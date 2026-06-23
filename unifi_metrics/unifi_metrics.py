from __future__ import annotations

from typing import Any

from .metrics import Sample, numeric_value


def collect_unifi_device_samples(devices: list[dict[str, Any]]) -> list[Sample]:
    samples: list[Sample] = []
    for device in devices:
        labels = device_labels(device)
        samples.append(Sample("unifi_device_info", labels, 1.0))
        add(samples, "unifi_device_up", labels, state_value(device.get("state")))
        add(samples, "unifi_device_uptime_seconds", labels, numeric_value(device.get("uptime")))
        add(samples, "unifi_device_rx_bytes", labels, numeric_value(device.get("rx_bytes")))
        add(samples, "unifi_device_tx_bytes", labels, numeric_value(device.get("tx_bytes")))
        add(samples, "unifi_device_clients", labels, numeric_value(device.get("num_sta")))
        add(samples, "unifi_device_guest_clients", labels, numeric_value(device.get("guest-num_sta")))
        add(samples, "unifi_device_lan_clients", labels, numeric_value(device.get("lan-num_sta")))
        add(samples, "unifi_device_wlan_clients", labels, numeric_value(device.get("wlan-num_sta")))
        add(samples, "unifi_device_satisfaction", labels, numeric_value(device.get("satisfaction")))
        add(samples, "unifi_device_upgrade_available", labels, bool_value(device.get("upgradable")))
        add(samples, "unifi_device_overheating", labels, bool_value(device.get("overheating")))
        samples.extend(system_samples(device, labels))
        samples.extend(gateway_samples(device, labels))
        samples.extend(port_samples(device, labels))
        samples.extend(ap_samples(device, labels))
    return samples


def device_labels(device: dict[str, Any]) -> dict[str, str]:
    return {
        "mac": str(device.get("mac", "")),
        "name": str(device.get("name") or device.get("display_name") or device.get("mac", "")),
        "model": str(device.get("model", "")),
        "type": str(device.get("type", "")),
        "version": str(device.get("displayable_version") or device.get("version") or ""),
    }


def system_samples(device: dict[str, Any], labels: dict[str, str]) -> list[Sample]:
    samples: list[Sample] = []
    system_stats = device.get("system-stats")
    if isinstance(system_stats, dict):
        add(samples, "unifi_device_cpu_usage_percent", labels, numeric_value(system_stats.get("cpu")))
        add(samples, "unifi_device_memory_usage_percent", labels, numeric_value(system_stats.get("mem")))
    sys_stats = device.get("sys_stats")
    if isinstance(sys_stats, dict):
        add(samples, "unifi_device_load_1", labels, numeric_value(sys_stats.get("loadavg_1")))
        add(samples, "unifi_device_load_5", labels, numeric_value(sys_stats.get("loadavg_5")))
        add(samples, "unifi_device_load_15", labels, numeric_value(sys_stats.get("loadavg_15")))
        add(samples, "unifi_device_memory_total_bytes", labels, numeric_value(sys_stats.get("mem_total")))
        add(samples, "unifi_device_memory_used_bytes", labels, numeric_value(sys_stats.get("mem_used")))
    return samples


def gateway_samples(device: dict[str, Any], labels: dict[str, str]) -> list[Sample]:
    if device.get("type") != "udm":
        return []
    uplink = device.get("uplink")
    if not isinstance(uplink, dict):
        return []
    samples: list[Sample] = []
    wan_labels = {
        **labels,
        "interface": str(uplink.get("name", "")),
        "network": str(uplink.get("network_name") or uplink.get("comment") or "wan"),
        "ip": str(uplink.get("ip", "")),
    }
    add(samples, "unifi_gateway_wan_up", wan_labels, bool_value(uplink.get("up")))
    add(samples, "unifi_gateway_wan_latency_ms", wan_labels, numeric_value(uplink.get("latency")))
    add(samples, "unifi_gateway_wan_uptime_seconds", wan_labels, numeric_value(uplink.get("uptime")))
    add(samples, "unifi_gateway_wan_rx_bytes", wan_labels, numeric_value(uplink.get("rx_bytes")))
    add(samples, "unifi_gateway_wan_tx_bytes", wan_labels, numeric_value(uplink.get("tx_bytes")))
    add(samples, "unifi_gateway_wan_rx_rate_bps", wan_labels, numeric_value(uplink.get("rx_rate")))
    add(samples, "unifi_gateway_wan_tx_rate_bps", wan_labels, numeric_value(uplink.get("tx_rate")))
    add(samples, "unifi_gateway_wan_rx_errors", wan_labels, numeric_value(uplink.get("rx_errors")))
    add(samples, "unifi_gateway_wan_tx_errors", wan_labels, numeric_value(uplink.get("tx_errors")))
    add(samples, "unifi_gateway_wan_rx_dropped", wan_labels, numeric_value(uplink.get("rx_dropped")))
    add(samples, "unifi_gateway_wan_tx_dropped", wan_labels, numeric_value(uplink.get("tx_dropped")))
    add(samples, "unifi_gateway_wan_speed_mbps", wan_labels, numeric_value(uplink.get("speed")))
    return samples


def port_samples(device: dict[str, Any], labels: dict[str, str]) -> list[Sample]:
    ports = device.get("port_table")
    if not isinstance(ports, list):
        return []
    samples: list[Sample] = []
    for port in ports:
        if not isinstance(port, dict):
            continue
        port_labels = {
            **labels,
            "port": str(port.get("port_idx", "")),
            "port_name": str(port.get("name", "")),
            "media": str(port.get("media", "")),
            "network": str(port.get("network_name", "")),
        }
        add(samples, "unifi_switch_port_up", port_labels, bool_value(port.get("up")))
        add(samples, "unifi_switch_port_enabled", port_labels, bool_value(port.get("enable", port.get("enabled"))))
        add(samples, "unifi_switch_port_speed_mbps", port_labels, numeric_value(port.get("speed")))
        add(samples, "unifi_switch_port_rx_bytes", port_labels, numeric_value(port.get("rx_bytes")))
        add(samples, "unifi_switch_port_tx_bytes", port_labels, numeric_value(port.get("tx_bytes")))
        add(samples, "unifi_switch_port_rx_packets", port_labels, numeric_value(port.get("rx_packets")))
        add(samples, "unifi_switch_port_tx_packets", port_labels, numeric_value(port.get("tx_packets")))
        add(samples, "unifi_switch_port_rx_errors", port_labels, numeric_value(port.get("rx_errors")))
        add(samples, "unifi_switch_port_tx_errors", port_labels, numeric_value(port.get("tx_errors")))
        add(samples, "unifi_switch_port_rx_dropped", port_labels, numeric_value(port.get("rx_dropped")))
        add(samples, "unifi_switch_port_tx_dropped", port_labels, numeric_value(port.get("tx_dropped")))
        add(samples, "unifi_switch_port_rx_rate_bytes_per_second", port_labels, numeric_value(port.get("rx_bytes-r")))
        add(samples, "unifi_switch_port_tx_rate_bytes_per_second", port_labels, numeric_value(port.get("tx_bytes-r")))
        add(samples, "unifi_switch_port_link_down_count", port_labels, numeric_value(port.get("link_down_count")))
        add(samples, "unifi_switch_port_poe_enabled", port_labels, bool_value(port.get("poe_enable")))
        add(samples, "unifi_switch_port_poe_good", port_labels, bool_value(port.get("poe_good")))
        add(samples, "unifi_switch_port_poe_power_watts", port_labels, numeric_value(port.get("poe_power")))
        add(samples, "unifi_switch_port_poe_voltage_volts", port_labels, numeric_value(port.get("poe_voltage")))
        add(samples, "unifi_switch_port_poe_current_milliamps", port_labels, numeric_value(port.get("poe_current")))
    return samples


def ap_samples(device: dict[str, Any], labels: dict[str, str]) -> list[Sample]:
    if device.get("type") != "uap":
        return []
    samples: list[Sample] = []
    radios = device.get("radio_table")
    if isinstance(radios, list):
        for radio in radios:
            if not isinstance(radio, dict):
                continue
            radio_labels = {
                **labels,
                "radio": str(radio.get("radio", "")),
                "radio_name": str(radio.get("name", "")),
            }
            add(samples, "unifi_ap_radio_max_tx_power_dbm", radio_labels, numeric_value(radio.get("max_txpower")))
            add(samples, "unifi_ap_radio_min_tx_power_dbm", radio_labels, numeric_value(radio.get("min_txpower")))
            add(samples, "unifi_ap_radio_spatial_streams", radio_labels, numeric_value(radio.get("nss")))
            width = parse_channel_width(radio.get("ht"))
            add(samples, "unifi_ap_radio_channel_width_mhz", radio_labels, width)
    vaps = device.get("vap_table")
    if isinstance(vaps, list):
        for vap in vaps:
            if not isinstance(vap, dict):
                continue
            vap_labels = {
                **labels,
                "radio": str(vap.get("radio", "")),
                "radio_name": str(vap.get("radio_name", "")),
                "essid": str(vap.get("essid", "")),
                "usage": str(vap.get("usage", "")),
            }
            add(samples, "unifi_ap_vap_up", vap_labels, bool_value(vap.get("up")))
            add(samples, "unifi_ap_vap_clients", vap_labels, numeric_value(vap.get("num_sta")))
            add(samples, "unifi_ap_vap_channel", vap_labels, numeric_value(vap.get("channel")))
            add(samples, "unifi_ap_vap_channel_width_mhz", vap_labels, numeric_value(vap.get("bw")))
            add(samples, "unifi_ap_vap_tx_power_dbm", vap_labels, numeric_value(vap.get("tx_power")))
            add(samples, "unifi_ap_vap_rx_bytes", vap_labels, numeric_value(vap.get("rx_bytes")))
            add(samples, "unifi_ap_vap_tx_bytes", vap_labels, numeric_value(vap.get("tx_bytes")))
            add(samples, "unifi_ap_vap_rx_errors", vap_labels, numeric_value(vap.get("rx_errors")))
            add(samples, "unifi_ap_vap_tx_errors", vap_labels, numeric_value(vap.get("tx_errors")))
            add(samples, "unifi_ap_vap_tx_retries", vap_labels, numeric_value(vap.get("tx_retries")))
            add(samples, "unifi_ap_vap_tx_dropped", vap_labels, numeric_value(vap.get("tx_dropped")))
            add(samples, "unifi_ap_vap_wifi_tx_dropped", vap_labels, numeric_value(vap.get("wifi_tx_dropped")))
            add(samples, "unifi_ap_vap_avg_client_signal_dbm", vap_labels, numeric_value(vap.get("avg_client_signal")))
            add(samples, "unifi_ap_vap_satisfaction", vap_labels, numeric_value(vap.get("satisfaction")))
    return samples


def add(samples: list[Sample], name: str, labels: dict[str, str], value: float | None) -> None:
    if value is not None:
        samples.append(Sample(name, labels, value))


def bool_value(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    return numeric_value(value)


def state_value(value: Any) -> float | None:
    number = numeric_value(value)
    if number is None:
        return None
    return 1.0 if number == 1 else 0.0


def parse_channel_width(value: Any) -> float | None:
    if isinstance(value, str):
        digits = "".join(char for char in value if char.isdigit())
        if digits:
            return float(digits)
    return numeric_value(value)

