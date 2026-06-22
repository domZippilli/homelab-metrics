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
from .metrics import collect_pdu_samples, pdu_devices, render_prometheus


LOG = logging.getLogger("unifi_metrics")
SENSITIVE_KEY_RE = re.compile(r"password|token|secret|credential|key", re.IGNORECASE)


class ScrapeCache:
    def __init__(self, config: Config) -> None:
        self.config = config
        self.client = UnifiClient(
            host=config.unifi_host,
            username=config.username,
            password=config.password,
            site=config.site,
            verify_ssl=config.verify_ssl,
            timeout_seconds=config.timeout_seconds,
        )
        self._expires_at = 0.0
        self._devices: list[dict[str, Any]] = []
        self._error: Exception | None = None
        self._duration = 0.0

    def scrape(self) -> tuple[list[dict[str, Any]], float, Exception | None]:
        now = time.monotonic()
        if now < self._expires_at:
            return self._devices, self._duration, self._error

        started = time.monotonic()
        try:
            devices = self.client.network_devices()
            self._devices = devices
            self._error = None
        except Exception as exc:
            LOG.warning("UniFi scrape failed: %s", exc)
            self._error = exc
        self._duration = time.monotonic() - started
        self._expires_at = time.monotonic() + self.config.scrape_ttl_seconds
        return self._devices, self._duration, self._error


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
        self.send_error(HTTPStatus.NOT_FOUND)

    def log_message(self, fmt: str, *args: Any) -> None:
        LOG.info("%s - %s", self.address_string(), fmt % args)

    def _metrics(self) -> None:
        devices, duration, error = self.cache.scrape()
        samples = [] if error else collect_pdu_samples(devices, self.cache.config.pdu_filter)
        body = render_prometheus(samples, error is None, duration, error)
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
  </ul>
</body>
</html>
"""
        self._send_text(body, "text/html; charset=utf-8")

    def _debug_devices(self) -> None:
        devices, _, error = self.cache.scrape()
        if error:
            self.send_error(HTTPStatus.BAD_GATEWAY, str(error))
            return
        pattern = re.compile(self.cache.config.pdu_filter, re.IGNORECASE)
        body = json.dumps(redact(pdu_devices(devices, pattern)), indent=2, sort_keys=True)
        self._send_text(f"{body}\n", "application/json")

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
