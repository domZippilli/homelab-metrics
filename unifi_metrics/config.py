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
    unifi_host: str | None = None
    username: str | None = None
    password: str | None = None
    site: str = "default"
    verify_ssl: bool = False
    timeout_seconds: float = 15.0
    pdu_filter: str = r"pdu|usp-pdu|smartpower|power strip|outlet"
    protect_enabled: bool = False
    ecoflow_host: str = "https://api.ecoflow.com"
    ecoflow_access_key: str | None = None
    ecoflow_secret_key: str | None = None
    ecoflow_device_sns: tuple[str, ...] = ()
    ecoflow_timeout_seconds: float = 15.0
    zfs_enabled: bool = False
    zfs_pools: tuple[str, ...] = ()
    intel_gpu_enabled: bool = False
    gpu_sysfs_path: str = "/sys/class/drm/card1"
    exporter_addr: str = "0.0.0.0"
    exporter_port: int = 9130
    scrape_ttl_seconds: float = 20.0

    @property
    def unifi_enabled(self) -> bool:
        return bool(self.unifi_host and self.username and self.password)

    @property
    def ecoflow_enabled(self) -> bool:
        return bool(self.ecoflow_access_key and self.ecoflow_secret_key)

    @classmethod
    def from_env(cls) -> "Config":
        load_dotenv()
        config = cls(
            unifi_host=os.getenv("UNIFI_HOST", "").rstrip("/") or None,
            username=os.getenv("UNIFI_USERNAME") or None,
            password=os.getenv("UNIFI_PASSWORD") or None,
            site=os.getenv("UNIFI_SITE", "default"),
            verify_ssl=_bool_env("UNIFI_VERIFY_SSL", False),
            timeout_seconds=float(os.getenv("UNIFI_TIMEOUT_SECONDS", "15")),
            pdu_filter=os.getenv(
                "UNIFI_PDU_FILTER", r"pdu|usp-pdu|smartpower|power strip|outlet"
            ),
            protect_enabled=_bool_env("UNIFI_PROTECT_ENABLED", False),
            ecoflow_host=os.getenv("ECOFLOW_HOST", "https://api.ecoflow.com").rstrip("/"),
            ecoflow_access_key=os.getenv("ECOFLOW_ACCESS_KEY")
            or os.getenv("ECOFLOW_API_KEY")
            or None,
            ecoflow_secret_key=os.getenv("ECOFLOW_SECRET_KEY")
            or os.getenv("ECOFLOW_API_SECRET")
            or None,
            ecoflow_device_sns=_csv_env("ECOFLOW_DEVICE_SNS"),
            ecoflow_timeout_seconds=float(os.getenv("ECOFLOW_TIMEOUT_SECONDS", "15")),
            zfs_enabled=_bool_env("ZFS_ENABLED", False),
            zfs_pools=_csv_env("ZFS_POOLS"),
            intel_gpu_enabled=_bool_env("INTEL_GPU_ENABLED", False),
            gpu_sysfs_path=os.getenv("GPU_SYSFS_PATH", "/sys/class/drm/card1"),
            exporter_addr=os.getenv("EXPORTER_ADDR", "0.0.0.0"),
            exporter_port=int(os.getenv("EXPORTER_PORT", "9130")),
            scrape_ttl_seconds=float(os.getenv("SCRAPE_TTL_SECONDS", "20")),
        )
        if (
            not config.unifi_enabled
            and not config.ecoflow_enabled
            and not config.zfs_enabled
            and not config.intel_gpu_enabled
        ):
            raise ValueError("configure at least one source: UniFi, EcoFlow, ZFS, or GPU")
        return config


def _csv_env(name: str) -> tuple[str, ...]:
    value = os.getenv(name, "")
    return tuple(item.strip() for item in value.split(",") if item.strip())


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
