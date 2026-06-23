from __future__ import annotations

import json
import logging
import re
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from .client import UnifiClient
from .config import Config
from .ecoflow_client import EcoFlowClient
from .ecoflow_metrics import collect_ecoflow_samples, serial_from_device
from .metrics import Sample, collect_pdu_samples, pdu_devices, render_samples
from .unifi_metrics import collect_unifi_device_samples
from .zfs_status import collect_zfs_status_samples


LOG = logging.getLogger("unifi_metrics")
SENSITIVE_KEY_RE = re.compile(r"password|token|secret|credential|key", re.IGNORECASE)


class ScrapeCache:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.unifi_client = None
        if config.unifi_enabled:
            assert config.unifi_host and config.username and config.password
            self.unifi_client = UnifiClient(
                host=config.unifi_host,
                username=config.username,
                password=config.password,
                site=config.site,
                verify_ssl=config.verify_ssl,
                timeout_seconds=config.timeout_seconds,
            )
        self.ecoflow_client = None
        if config.ecoflow_enabled:
            assert config.ecoflow_access_key and config.ecoflow_secret_key
            self.ecoflow_client = EcoFlowClient(
                host=config.ecoflow_host,
                access_key=config.ecoflow_access_key,
                secret_key=config.ecoflow_secret_key,
                timeout_seconds=config.ecoflow_timeout_seconds,
            )
        self._expires_at = 0.0
        self._unifi_devices: list[dict[str, Any]] = []
        self._ecoflow_devices: list[dict[str, Any]] = []
        self._ecoflow_quotas: dict[str, dict[str, Any]] = {}
        self._errors: dict[str, Exception] = {}
        self._duration = 0.0
        self._samples: list[Sample] = []

    def scrape(self) -> tuple[list[Sample], float, dict[str, Exception]]:
        now = time.monotonic()
        if now < self._expires_at:
            return self._samples, self._duration, self._errors

        started = time.monotonic()
        samples: list[Sample] = []
        errors: dict[str, Exception] = {}
        if self.unifi_client:
            samples.extend(self._scrape_unifi(errors))
        if self.ecoflow_client:
            samples.extend(self._scrape_ecoflow(errors))
        if self.config.zfs_enabled:
            samples.extend(self._scrape_zfs(errors))
        self._duration = time.monotonic() - started
        samples.append(Sample("homelab_scrape_duration_seconds", {}, self._duration))
        self._samples = samples
        self._errors = errors
        self._expires_at = time.monotonic() + self.config.scrape_ttl_seconds
        return self._samples, self._duration, self._errors

    def _scrape_unifi(self, errors: dict[str, Exception]) -> list[Sample]:
        started = time.monotonic()
        try:
            assert self.unifi_client
            self._unifi_devices = self.unifi_client.network_devices()
            samples = collect_unifi_device_samples(self._unifi_devices)
            samples.extend(collect_pdu_samples(self._unifi_devices, self.config.pdu_filter))
            samples.append(Sample("unifi_up", {}, 1.0))
            samples.append(Sample("unifi_scrape_duration_seconds", {}, time.monotonic() - started))
            return samples
        except Exception as exc:
            LOG.warning("UniFi scrape failed: %s", exc)
            errors["unifi"] = exc
            return [
                Sample("unifi_up", {}, 0.0),
                Sample("unifi_scrape_duration_seconds", {}, time.monotonic() - started),
                Sample(
                    "unifi_scrape_error",
                    {"type": exc.__class__.__name__, "message": str(exc)[:160]},
                    1.0,
                ),
            ]

    def _scrape_ecoflow(self, errors: dict[str, Exception]) -> list[Sample]:
        started = time.monotonic()
        try:
            assert self.ecoflow_client
            devices = self.ecoflow_client.devices()
            allowed = set(self.config.ecoflow_device_sns)
            if allowed:
                devices = [device for device in devices if serial_from_device(device) in allowed]
            quotas = {
                serial_number: self.ecoflow_client.quota(serial_number)
                for serial_number in (serial_from_device(device) for device in devices)
                if serial_number
            }
            self._ecoflow_devices = devices
            self._ecoflow_quotas = quotas
            samples = collect_ecoflow_samples(devices, quotas)
            samples.append(Sample("ecoflow_up", {}, 1.0))
            samples.append(
                Sample("ecoflow_scrape_duration_seconds", {}, time.monotonic() - started)
            )
            return samples
        except Exception as exc:
            LOG.warning("EcoFlow scrape failed: %s", exc)
            errors["ecoflow"] = exc
            return [
                Sample("ecoflow_up", {}, 0.0),
                Sample("ecoflow_scrape_duration_seconds", {}, time.monotonic() - started),
                Sample(
                    "ecoflow_scrape_error",
                    {"type": exc.__class__.__name__, "message": str(exc)[:160]},
                    1.0,
                ),
            ]

    def _scrape_zfs(self, errors: dict[str, Exception]) -> list[Sample]:
        started = time.monotonic()
        try:
            samples = collect_zfs_status_samples(self.config.zfs_pools)
            samples.append(Sample("homelab_zfs_up", {}, 1.0))
            samples.append(Sample("homelab_zfs_scrape_duration_seconds", {}, time.monotonic() - started))
            return samples
        except Exception as exc:
            LOG.warning("ZFS status scrape failed: %s", exc)
            errors["zfs"] = exc
            return [
                Sample("homelab_zfs_up", {}, 0.0),
                Sample("homelab_zfs_scrape_duration_seconds", {}, time.monotonic() - started),
                Sample(
                    "homelab_zfs_scrape_error",
                    {"type": exc.__class__.__name__, "message": str(exc)[:160]},
                    1.0,
                ),
            ]

    def unifi_devices(self) -> tuple[list[dict[str, Any]], Exception | None]:
        self.scrape()
        return self._unifi_devices, self._errors.get("unifi")

    def ecoflow_debug(self) -> tuple[dict[str, Any], Exception | None]:
        self.scrape()
        body = {"devices": self._ecoflow_devices, "quotas": self._ecoflow_quotas}
        return body, self._errors.get("ecoflow")


class Handler(BaseHTTPRequestHandler):
    cache: ScrapeCache

    def do_GET(self) -> None:
        path = self._route(self.path)
        if path == "/":
            self._index()
            return
        if path == "/healthz":
            self._send_text("ok\n")
            return
        if path == "/metrics":
            self._metrics()
            return
        if path == "/debug/devices":
            self._debug_devices()
            return
        if path == "/debug/ecoflow":
            self._debug_ecoflow()
            return
        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, fmt: str, *args: Any) -> None:
        LOG.info("%s - %s", self.address_string(), fmt % args)

    def _metrics(self) -> None:
        samples, _, _ = self.cache.scrape()
        body = render_samples(samples)
        self._send_text(body, "text/plain; version=0.0.4; charset=utf-8")

    def _index(self) -> None:
        body = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>unifi-metrics</title>
</head>
<body>
  <h1>unifi-metrics</h1>
  <ul>
    <li><a href="/metrics">/metrics</a></li>
    <li><a href="/healthz">/healthz</a></li>
    <li><a href="/debug/devices">/debug/devices</a></li>
    <li><a href="/debug/ecoflow">/debug/ecoflow</a></li>
  </ul>
</body>
</html>
"""
        self._send_text(body, "text/html; charset=utf-8")

    def _debug_devices(self) -> None:
        devices, error = self.cache.unifi_devices()
        if error:
            self.send_error(HTTPStatus.BAD_GATEWAY, str(error))
            return
        pattern = re.compile(self.cache.config.pdu_filter, re.IGNORECASE)
        body = json.dumps(redact(pdu_devices(devices, pattern)), indent=2, sort_keys=True)
        self._send_text(f"{body}\n", "application/json")

    def _debug_ecoflow(self) -> None:
        body, error = self.cache.ecoflow_debug()
        if error:
            self.send_error(HTTPStatus.BAD_GATEWAY, str(error))
            return
        self._send_text(f"{json.dumps(redact(body), indent=2, sort_keys=True)}\n", "application/json")

    def _send_text(self, body: str, content_type: str = "text/plain; charset=utf-8") -> None:
        raw = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    @staticmethod
    def _route(path: str) -> str:
        return path.split("?", 1)[0]


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        redacted = {}
        for key, item in value.items():
            if SENSITIVE_KEY_RE.search(str(key)):
                redacted[key] = "[redacted]"
            else:
                redacted[key] = redact(item)
        return redacted
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    config = Config.from_env()
    Handler.cache = ScrapeCache(config)
    server = ThreadingHTTPServer((config.exporter_addr, config.exporter_port), Handler)
    LOG.info("listening on http://%s:%s", config.exporter_addr, config.exporter_port)
    server.serve_forever()
