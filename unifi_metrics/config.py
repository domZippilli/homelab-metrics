from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _bool_env(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Config:
    unifi_host: str
    username: str
    password: str
    site: str = "default"
    verify_ssl: bool = False
    timeout_seconds: float = 15.0
    pdu_filter: str = r"pdu|usp-pdu|smartpower|power strip|outlet"
    exporter_addr: str = "0.0.0.0"
    exporter_port: int = 9130
    scrape_ttl_seconds: float = 20.0

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        missing = [
            name
            for name in ("UNIFI_HOST", "UNIFI_USERNAME", "UNIFI_PASSWORD")
            if not os.getenv(name)
        ]
        if missing:
            joined = ", ".join(missing)
            raise ValueError(f"missing required environment variables: {joined}")

        return cls(
            unifi_host=os.environ["UNIFI_HOST"].rstrip("/"),
            username=os.environ["UNIFI_USERNAME"],
            password=os.environ["UNIFI_PASSWORD"],
            site=os.getenv("UNIFI_SITE", "default"),
            verify_ssl=_bool_env("UNIFI_VERIFY_SSL", False),
            timeout_seconds=float(os.getenv("UNIFI_TIMEOUT_SECONDS", "15")),
            pdu_filter=os.getenv(
                "UNIFI_PDU_FILTER", r"pdu|usp-pdu|smartpower|power strip|outlet"
            ),
            exporter_addr=os.getenv("EXPORTER_ADDR", "0.0.0.0"),
            exporter_port=int(os.getenv("EXPORTER_PORT", "9130")),
            scrape_ttl_seconds=float(os.getenv("SCRAPE_TTL_SECONDS", "20")),
        )


def load_dotenv(path: str = ".env") -> None:
    dotenv = Path(path)
    if not dotenv.exists():
        return
    for raw_line in dotenv.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)
