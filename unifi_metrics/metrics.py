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
    "unifi_protect_up": "Whether the last UniFi Protect scrape succeeded.",
    "unifi_protect_scrape_duration_seconds": "Duration of the last UniFi Protect API scrape.",
    "unifi_protect_scrape_error": "UniFi Protect scrape error information, labeled by error type.",
    "unifi_protect_nvr_info": "UniFi Protect NVR information.",
    "unifi_protect_nvr_up_since_timestamp_seconds": "Unix timestamp when the UniFi Protect NVR came online.",
    "unifi_protect_nvr_last_seen_timestamp_seconds": "Unix timestamp when the UniFi Protect NVR was last seen.",
    "unifi_protect_nvr_is_recording": "Whether the UniFi Protect NVR is recording.",
    "unifi_protect_nvr_recording_disabled": "Whether UniFi Protect recording is disabled.",
    "unifi_protect_nvr_recording_motion_only": "Whether UniFi Protect records motion only.",
    "unifi_protect_nvr_disk_used_bytes": "UniFi Protect recording storage used.",
    "unifi_protect_nvr_disk_available_bytes": "UniFi Protect recording storage available.",
    "unifi_protect_nvr_disk_total_bytes": "UniFi Protect recording storage total.",
    "unifi_protect_nvr_cpu_load_percent": "UniFi Protect NVR CPU load.",
    "unifi_protect_nvr_cpu_temperature_celsius": "UniFi Protect NVR CPU temperature.",
    "unifi_protect_nvr_memory_available_kilobytes": "UniFi Protect NVR available memory.",
    "unifi_protect_nvr_memory_free_kilobytes": "UniFi Protect NVR free memory.",
    "unifi_protect_nvr_memory_total_kilobytes": "UniFi Protect NVR total memory.",
    "unifi_protect_nvr_camera_count": "Number of configured UniFi Protect cameras.",
    "unifi_protect_nvr_camera_utilization_percent": "UniFi Protect camera utilization.",
    "unifi_protect_camera_info": "UniFi Protect camera information.",
    "unifi_protect_camera_connected": "Whether the UniFi Protect camera is connected.",
    "unifi_protect_camera_recording_enabled": "Whether the UniFi Protect camera is recording.",
    "unifi_protect_camera_motion_detected": "Whether the UniFi Protect camera currently reports motion.",
    "unifi_protect_camera_smart_detected": "Whether the UniFi Protect camera currently reports smart detection.",
    "unifi_protect_camera_up_since_timestamp_seconds": "Unix timestamp when the UniFi Protect camera came online.",
    "unifi_protect_camera_last_seen_timestamp_seconds": "Unix timestamp when the UniFi Protect camera was last seen.",
    "unifi_protect_camera_connected_since_timestamp_seconds": "Unix timestamp when the UniFi Protect camera connected.",
    "unifi_protect_camera_last_motion_timestamp_seconds": "Unix timestamp of the last UniFi Protect camera motion event.",
    "unifi_protect_camera_rx_bytes": "Bytes received by the UniFi Protect camera.",
    "unifi_protect_camera_tx_bytes": "Bytes sent by the UniFi Protect camera.",
    "unifi_protect_camera_wifi_signal_quality": "UniFi Protect camera wireless signal quality.",
    "unifi_protect_camera_wifi_signal_strength_dbm": "UniFi Protect camera wireless signal strength.",
    "unifi_protect_camera_battery_percent": "UniFi Protect camera battery percentage.",
    "unifi_protect_light_info": "UniFi Protect light information.",
    "unifi_protect_light_connected": "Whether the UniFi Protect light is connected.",
    "unifi_protect_light_on": "Whether the UniFi Protect light is on.",
    "unifi_protect_light_brightness_percent": "UniFi Protect light brightness.",
    "unifi_protect_sensor_info": "UniFi Protect sensor information.",
    "unifi_protect_sensor_connected": "Whether the UniFi Protect sensor is connected.",
    "unifi_protect_sensor_updating": "Whether the UniFi Protect sensor is updating.",
    "unifi_protect_sensor_open": "Whether the UniFi Protect sensor reports open.",
    "unifi_protect_sensor_motion_detected": "Whether the UniFi Protect sensor currently reports motion.",
    "unifi_protect_sensor_up_since_timestamp_seconds": "Unix timestamp when the UniFi Protect sensor came online.",
    "unifi_protect_sensor_last_seen_timestamp_seconds": "Unix timestamp when the UniFi Protect sensor was last seen.",
    "unifi_protect_sensor_connected_since_timestamp_seconds": "Unix timestamp when the UniFi Protect sensor connected.",
    "unifi_protect_sensor_motion_detected_at_timestamp_seconds": "Unix timestamp of the last UniFi Protect sensor motion event.",
    "unifi_protect_sensor_temperature_celsius": "UniFi Protect sensor temperature.",
    "unifi_protect_sensor_humidity_percent": "UniFi Protect sensor humidity.",
    "unifi_protect_sensor_light_lux": "UniFi Protect sensor light level.",
    "unifi_protect_sensor_battery_percent": "UniFi Protect sensor battery percentage.",
    "unifi_protect_sensor_battery_low": "Whether the UniFi Protect sensor battery is low.",
    "unifi_protect_sensor_signal_quality": "UniFi Protect sensor wireless signal quality.",
    "unifi_protect_sensor_signal_strength_dbm": "UniFi Protect sensor wireless signal strength.",
    "unifi_protect_sensor_leak_detected_at_timestamp_seconds": "Unix timestamp of the last UniFi Protect sensor leak event.",
    "unifi_protect_sensor_tampering_detected_at_timestamp_seconds": "Unix timestamp of the last UniFi Protect sensor tamper event.",
    "unifi_protect_viewer_info": "UniFi Protect viewer information.",
    "unifi_protect_viewer_connected": "Whether the UniFi Protect viewer is connected.",
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
    "homelab_gpu_up": "Whether the last GPU sysfs scrape succeeded.",
    "homelab_gpu_scrape_duration_seconds": "Duration of the last GPU sysfs scrape.",
    "homelab_gpu_scrape_error": "GPU scrape error information, labeled by error type.",
    "homelab_gpu_info": "Intel GPU device information.",
    "homelab_gpu_energy_joules_total": "GPU energy counter from hwmon.",
    "homelab_gpu_voltage_volts": "GPU voltage from hwmon.",
    "homelab_gpu_power_limit_watts": "GPU configured power limit from hwmon.",
    "homelab_gpu_power_limit_interval_seconds": "GPU power limit interval from hwmon.",
    "homelab_gpu_power_rated_max_watts": "GPU rated maximum power from hwmon.",
    "homelab_gpu_media_rp0_frequency_mhz": "GPU media RP0 frequency.",
    "homelab_gpu_media_rpn_frequency_mhz": "GPU media RPn frequency.",
    "homelab_gpu_media_frequency_factor": "Raw GPU media frequency factor.",
    "homelab_gpu_media_frequency_factor_scaled": "Scaled GPU media frequency factor.",
    "homelab_gpu_punit_requested_frequency_mhz": "GPU punit requested frequency.",
    "homelab_gpu_rc6_enabled": "Whether GPU RC6 is enabled.",
    "homelab_gpu_rc6_residency_seconds_total": "GPU RC6 residency counter.",
    "homelab_gpu_rps_rp0_frequency_mhz": "GPU RPS RP0 frequency.",
    "homelab_gpu_rps_rp1_frequency_mhz": "GPU RPS RP1 frequency.",
    "homelab_gpu_rps_rpn_frequency_mhz": "GPU RPS RPn frequency.",
    "homelab_gpu_rps_actual_frequency_mhz": "GPU RPS actual frequency.",
    "homelab_gpu_rps_current_frequency_mhz": "GPU RPS current frequency.",
    "homelab_gpu_rps_boost_frequency_mhz": "GPU RPS boost frequency.",
    "homelab_gpu_rps_max_frequency_mhz": "GPU RPS maximum frequency.",
    "homelab_gpu_rps_min_frequency_mhz": "GPU RPS minimum frequency.",
    "homelab_gpu_throttle_reason": "GPU throttle reason status, labeled by reason.",
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
