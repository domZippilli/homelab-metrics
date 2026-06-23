from __future__ import annotations

import math
import re
import time
from dataclasses import dataclass
from typing import Any, Iterable


HELP = {
    "homelab_scrape_duration_seconds": "Duration of the last combined homelab metrics scrape.",
    "unifi_up": "Whether the last UniFi API scrape succeeded.",
    "unifi_scrape_duration_seconds": "Duration of the last UniFi API scrape.",
    "unifi_scrape_error": "Scrape error information, labeled by error type.",
    "unifi_device_info": "UniFi device information.",
    "unifi_device_up": "Whether the UniFi device is connected.",
    "unifi_device_uptime_seconds": "UniFi device uptime.",
    "unifi_device_cpu_usage_percent": "UniFi device CPU usage.",
    "unifi_device_memory_usage_percent": "UniFi device memory usage.",
    "unifi_gateway_wan_up": "Whether the UniFi gateway WAN uplink is up.",
    "unifi_switch_port_up": "Whether the UniFi switch port link is up.",
    "unifi_switch_port_poe_power_watts": "UniFi switch port PoE power draw.",
    "unifi_ap_vap_clients": "Connected clients on a UniFi AP virtual access point.",
    "unifi_pdu_outlet_relay_state": "Whether the UniFi PDU outlet relay is on.",
    "unifi_pdu_outlet_ac_power_consumption_watts": "Total UniFi PDU outlet AC power consumption.",
    "unifi_pdu_outlet_ac_power_budget_watts": "Total UniFi PDU outlet AC power budget.",
    "unifi_pdu_outlet_power_watts": "UniFi PDU outlet power draw.",
    "unifi_pdu_outlet_current_amps": "UniFi PDU outlet current draw.",
    "unifi_pdu_outlet_voltage_volts": "UniFi PDU outlet voltage.",
    "unifi_pdu_outlet_power_factor": "UniFi PDU outlet power factor.",
    "ecoflow_up": "Whether the last EcoFlow API scrape succeeded.",
    "ecoflow_scrape_duration_seconds": "Duration of the last EcoFlow API scrape.",
    "ecoflow_scrape_error": "EcoFlow scrape error information, labeled by error type.",
    "ecoflow_device_info": "EcoFlow device information.",
    "ecoflow_device_online": "Whether the EcoFlow device is online.",
    "homelab_zfs_up": "Whether the last ZFS status scrape succeeded.",
    "homelab_zfs_scrape_duration_seconds": "Duration of the last ZFS status scrape.",
    "homelab_zfs_scrape_error": "ZFS status scrape error information, labeled by error type.",
    "homelab_zfs_scrub_repaired_bytes": "Bytes repaired during the most recent ZFS scrub.",
    "homelab_zfs_scrub_errors": "Errors reported by the most recent ZFS scrub.",
    "homelab_zfs_scrub_duration_seconds": "Duration of the most recent ZFS scrub.",
    "homelab_zfs_scrub_end_timestamp_seconds": "Unix timestamp when the most recent ZFS scrub finished.",
    "homelab_zfs_scrub_status": "Most recent ZFS scan status, labeled by status text.",
    "homelab_zfs_data_errors": "Whether zpool status reports known data errors.",
    "homelab_zfs_vdev_read_errors": "Read errors reported by zpool status for a pool or vdev.",
    "homelab_zfs_vdev_write_errors": "Write errors reported by zpool status for a pool or vdev.",
    "homelab_zfs_vdev_checksum_errors": "Checksum errors reported by zpool status for a pool or vdev.",
}

DEVICE_FIELD_ALIASES = {
    "outlet_ac_power_consumption": "unifi_pdu_outlet_ac_power_consumption_watts",
    "outlet_ac_power_budget": "unifi_pdu_outlet_ac_power_budget_watts",
}

OUTLET_FIELD_ALIASES = {
    "outlet_power": "unifi_pdu_outlet_power_watts",
    "outlet_current": "unifi_pdu_outlet_current_amps",
    "outlet_voltage": "unifi_pdu_outlet_voltage_volts",
    "outlet_power_factor": "unifi_pdu_outlet_power_factor",
}


@dataclass(frozen=True)
class Sample:
    name: str
    labels: dict[str, str]
    value: float


def numeric_value(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)) and math.isfinite(value):
        return float(value)
    if isinstance(value, str):
        try:
            parsed = float(value)
        except ValueError:
            return None
        if math.isfinite(parsed):
            return parsed
    return None


def metric_name(prefix: str, field: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9_]", "_", field).strip("_").lower()
    cleaned = re.sub(r"_+", "_", cleaned)
    if not cleaned:
        cleaned = "value"
    if cleaned[0].isdigit():
        cleaned = f"field_{cleaned}"
    return f"{prefix}_{cleaned}"


def pdu_devices(devices: Iterable[dict[str, Any]], pattern: re.Pattern[str]) -> list[dict[str, Any]]:
    matches = []
    for device in devices:
        haystack = " ".join(
            str(device.get(key, ""))
            for key in ("model", "name", "display_name", "type", "model_in_eol")
        )
        if pattern.search(haystack):
            matches.append(device)
    return matches


def device_labels(device: dict[str, Any]) -> dict[str, str]:
    return {
        "mac": str(device.get("mac", "")),
        "name": str(device.get("name") or device.get("display_name") or device.get("mac", "")),
        "model": str(device.get("model", "")),
        "type": str(device.get("type", "")),
    }


def collect_pdu_samples(devices: Iterable[dict[str, Any]], filter_regex: str) -> list[Sample]:
    pattern = re.compile(filter_regex, re.IGNORECASE)
    samples: list[Sample] = []
    for device in pdu_devices(devices, pattern):
        labels = device_labels(device)
        for key, value in sorted(device.items()):
            number = numeric_value(value)
            if number is not None:
                name = DEVICE_FIELD_ALIASES.get(key, metric_name("unifi_pdu", key))
                samples.append(Sample(name, labels, number))
        samples.extend(_outlet_samples(labels, _merged_outlets(device)))
    return samples


def _merged_outlets(device: dict[str, Any]) -> list[dict[str, Any]]:
    merged: dict[str, dict[str, Any]] = {}
    for key in ("outlet_overrides", "outlets", "outlet_table"):
        outlets = device.get(key)
        if not isinstance(outlets, list):
            continue
        for index, outlet in enumerate(outlets):
            if not isinstance(outlet, dict):
                continue
            outlet_index = str(outlet.get("index", outlet.get("port_idx", index)))
            existing = merged.setdefault(outlet_index, {})
            existing.update(outlet)
    return [merged[key] for key in sorted(merged, key=lambda item: int(item) if item.isdigit() else item)]


def _outlet_samples(device: dict[str, str], outlets: list[dict[str, Any]]) -> list[Sample]:
    samples: list[Sample] = []
    for index, outlet in enumerate(outlets):
        outlet_index = str(outlet.get("index", outlet.get("port_idx", index)))
        labels = {
            **device,
            "outlet_index": outlet_index,
            "outlet_name": str(outlet.get("name", outlet.get("label", ""))),
            "relay_state": str(outlet.get("relay_state", outlet.get("state", ""))),
        }
        relay_state = _relay_state_value(outlet)
        if relay_state is not None:
            samples.append(Sample("unifi_pdu_outlet_relay_state", labels, relay_state))
        for key, value in sorted(outlet.items()):
            if key in {"index", "port_idx"}:
                continue
            number = numeric_value(value)
            if number is not None:
                name = OUTLET_FIELD_ALIASES.get(key, metric_name("unifi_pdu_outlet", key))
                samples.append(Sample(name, labels, number))
    return samples


def _relay_state_value(outlet: dict[str, Any]) -> float | None:
    value = outlet.get("relay_state", outlet.get("state"))
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"on", "true", "1", "enabled"}:
            return 1.0
        if normalized in {"off", "false", "0", "disabled"}:
            return 0.0
    return None


def render_prometheus(
    samples: Iterable[Sample],
    up: bool,
    duration_seconds: float,
    error: Exception | None = None,
) -> str:
    base_samples = [
        Sample("unifi_up", {}, 1.0 if up else 0.0),
        Sample("unifi_scrape_duration_seconds", {}, duration_seconds),
    ]
    if error is not None:
        base_samples.append(
            Sample(
                "unifi_scrape_error",
                {"type": error.__class__.__name__, "message": str(error)[:160]},
                1.0,
            )
        )

    return render_samples([*base_samples, *samples])


def render_samples(samples: Iterable[Sample]) -> str:
    lines: list[str] = []
    seen: set[str] = set()
    seen_series: set[tuple[str, tuple[tuple[str, str], ...]]] = set()

    for sample in samples:
        series_key = (sample.name, tuple(sorted(sample.labels.items())))
        if series_key in seen_series:
            continue
        seen_series.add(series_key)
        if sample.name not in seen:
            help_text = HELP.get(sample.name, f"Metric derived from source field {sample.name}.")
            lines.append(f"# HELP {sample.name} {help_text}")
            lines.append(f"# TYPE {sample.name} gauge")
            seen.add(sample.name)
        lines.append(_render_sample(sample))

    lines.append("")
    return "\n".join(lines)


def _render_sample(sample: Sample) -> str:
    if sample.labels:
        labels = ",".join(
            f'{key}="{_escape_label(value)}"' for key, value in sorted(sample.labels.items())
        )
        return f"{sample.name}{{{labels}}} {sample.value:g}"
    return f"{sample.name} {sample.value:g}"


def _escape_label(value: str) -> str:
    return value.replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def timed_collect(devices: list[dict[str, Any]], filter_regex: str) -> tuple[list[Sample], float]:
    started = time.monotonic()
    samples = collect_pdu_samples(devices, filter_regex)
    return samples, time.monotonic() - started
