from __future__ import annotations

import json
import ssl
import urllib.error
import urllib.parse
import urllib.request
from http.cookiejar import CookieJar
from typing import Any


class UnifiApiError(RuntimeError):
    pass


class UnifiClient:
    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        site: str,
        verify_ssl: bool,
        timeout_seconds: float,
    ) -> None:
        self.host = host.rstrip("/")
        self.username = username
        self.password = password
        self.site = site
        self.timeout_seconds = timeout_seconds
        self._csrf_token: str | None = None
        self._cookies = CookieJar()
        context = None if verify_ssl else ssl._create_unverified_context()
        self._opener = urllib.request.build_opener(
            urllib.request.HTTPSHandler(context=context),
            urllib.request.HTTPCookieProcessor(self._cookies),
        )
        self._logged_in = False

    def login(self) -> None:
        payload = {"username": self.username, "password": self.password}
        try:
            self._request("POST", "/api/auth/login", payload, require_auth=False)
        except UnifiApiError as exc:
            if "HTTP 404" not in str(exc):
                raise
            # Older non-UniFi-OS controllers use this path. Keeping it as a
            # fallback makes the exporter useful outside UDM deployments too.
            self._request("POST", "/api/login", payload, require_auth=False)
        self._logged_in = True

    def network_devices(self) -> list[dict[str, Any]]:
        if not self._logged_in:
            self.login()
        path = f"/proxy/network/api/s/{urllib.parse.quote(self.site)}/stat/device"
        body = self._request("GET", path, None)
        data = body.get("data")
        if not isinstance(data, list):
            raise UnifiApiError("unexpected device response: missing data list")
        return [item for item in data if isinstance(item, dict)]

    def protect_bootstrap(self) -> dict[str, Any]:
        if not self._logged_in:
            self.login()
        return self._request("GET", "/proxy/protect/api/bootstrap", None)

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
        require_auth: bool = True,
    ) -> dict[str, Any]:
        url = f"{self.host}{path}"
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if self._csrf_token:
            headers["X-CSRF-Token"] = self._csrf_token

        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with self._opener.open(request, timeout=self.timeout_seconds) as response:
                csrf = response.headers.get("X-CSRF-Token")
                if csrf:
                    self._csrf_token = csrf
                raw = response.read()
        except urllib.error.HTTPError as exc:
            if require_auth and exc.code in {401, 403}:
                self.login()
                return self._request(method, path, payload, require_auth=False)
            detail = exc.read().decode("utf-8", errors="replace")
            raise UnifiApiError(f"{method} {path} failed with HTTP {exc.code}: {detail}")
        except urllib.error.URLError as exc:
            raise UnifiApiError(f"{method} {path} failed: {exc.reason}") from exc

        if not raw:
            return {}
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise UnifiApiError(f"{method} {path} returned invalid JSON") from exc
        if not isinstance(decoded, dict):
            raise UnifiApiError(f"{method} {path} returned non-object JSON")
        return decoded
