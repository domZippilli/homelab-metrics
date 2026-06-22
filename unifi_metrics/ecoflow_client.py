from __future__ import annotations

import hashlib
import hmac
import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


class EcoFlowApiError(RuntimeError):
    pass


class EcoFlowClient:
    def __init__(
        self,
        host: str,
        access_key: str,
        secret_key: str,
        timeout_seconds: float,
    ) -> None:
        self.host = host.rstrip("/")
        self.access_key = access_key
        self.secret_key = secret_key
        self.timeout_seconds = timeout_seconds

    def devices(self) -> list[dict[str, Any]]:
        body = self._request("GET", "/iot-open/sign/device/list")
        data = body.get("data", body)
        if isinstance(data, list):
            return [item for item in data if isinstance(item, dict)]
        if isinstance(data, dict):
            for key in ("devices", "list", "deviceList"):
                value = data.get(key)
                if isinstance(value, list):
                    return [item for item in value if isinstance(item, dict)]
        raise EcoFlowApiError("unexpected device list response")

    def quota(self, serial_number: str) -> dict[str, Any]:
        body = self._request("GET", "/iot-open/sign/device/quota/all", {"sn": serial_number})
        data = body.get("data", body)
        if not isinstance(data, dict):
            raise EcoFlowApiError(f"unexpected quota response for {serial_number}")
        return data

    def _request(
        self,
        method: str,
        path: str,
        query: dict[str, Any] | None = None,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        query = query or {}
        encoded_query = urllib.parse.urlencode(query)
        url = f"{self.host}{path}"
        if encoded_query:
            url = f"{url}?{encoded_query}"

        raw_payload = None
        if payload is not None:
            raw_payload = json.dumps(payload, separators=(",", ":")).encode("utf-8")

        headers = self._headers(query, payload)
        if payload is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=raw_payload, headers=headers, method=method)

        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise EcoFlowApiError(f"{method} {path} failed with HTTP {exc.code}: {detail}")
        except urllib.error.URLError as exc:
            raise EcoFlowApiError(f"{method} {path} failed: {exc.reason}") from exc

        try:
            decoded = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise EcoFlowApiError(f"{method} {path} returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise EcoFlowApiError(f"{method} {path} returned non-object JSON")
        code = decoded.get("code")
        if code not in (None, 0, "0"):
            message = decoded.get("message") or decoded.get("msg") or decoded
            raise EcoFlowApiError(f"{method} {path} returned API error {code}: {message}")
        return decoded

    def _headers(
        self, query: dict[str, Any], payload: dict[str, Any] | None
    ) -> dict[str, str]:
        nonce = str(random.randint(100000, 999999))
        timestamp = str(int(time.time() * 1000))
        sign_params = flatten(query)
        if payload:
            sign_params.update(flatten(payload))
        sign_text = signature_text(sign_params, self.access_key, nonce, timestamp)
        signature = hmac.new(
            self.secret_key.encode("utf-8"),
            sign_text.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return {
            "accessKey": self.access_key,
            "nonce": nonce,
            "timestamp": timestamp,
            "sign": signature,
            "Accept": "application/json",
            "User-Agent": "homelab-metrics/0.1",
        }


def signature_text(
    params: dict[str, str], access_key: str, nonce: str, timestamp: str
) -> str:
    request_parts = [f"{key}={params[key]}" for key in sorted(params)]
    auth_parts = [
        f"accessKey={access_key}",
        f"nonce={nonce}",
        f"timestamp={timestamp}",
    ]
    return "&".join([*request_parts, *auth_parts])


def sign_text(text: str, secret_key: str) -> str:
    return hmac.new(
        secret_key.encode("utf-8"),
        text.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def flatten(value: Any, prefix: str = "") -> dict[str, str]:
    if isinstance(value, dict):
        result: dict[str, str] = {}
        for key, item in value.items():
            child_key = f"{prefix}.{key}" if prefix else str(key)
            result.update(flatten(item, child_key))
        return result
    if isinstance(value, list):
        result = {}
        for index, item in enumerate(value):
            child_key = f"{prefix}[{index}]"
            result.update(flatten(item, child_key))
        return result
    return {prefix: str(value)}
