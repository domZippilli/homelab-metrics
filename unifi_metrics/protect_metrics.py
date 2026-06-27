from __future__ import annotations

from typing import Any

from .metrics import Sample, numeric_value


def collect_protect_samples(bootstrap: dict[str, Any]) -> list[Sample]:
    samples: list[Sample] = []
    samples.extend(nvr_samples(bootstrap))
    samples.extend(camera_samples(list_value(bootstrap, "cameras")))
    samples.extend(light_samples(list_value(bootstrap, "lights")))
    samples.extend(sensor_samples(list_value(bootstrap, "sensors")))
    samples.extend(viewer_samples(list_value(bootstrap, "viewers")))
    return samples


def nvr_samples(bootstrap: dict[str, Any]) -> list[Sample]:
    nvr = bootstrap.get("nvr")
    if not isinstance(nvr, dict):
        return []
    labels = {
        "id": str(nvr.get("id", "")),
        "name": str(nvr.get("name") or nvr.get("host") or "nvr"),
        "model": str(nvr.get("modelKey") or nvr.get("model") or ""),
        "version": str(nvr.get("version") or nvr.get("firmwareVersion") or ""),
    }
    samples = [Sample("unifi_protect_nvr_info", labels, 1.0)]
    add(
        samples,
        "unifi_protect_nvr_up_since_timestamp_seconds",
        labels,
        timestamp_value(nvr.get("upSince")),
    )
    add(
        samples,
        "unifi_protect_nvr_last_seen_timestamp_seconds",
        labels,
        timestamp_value(nvr.get("lastSeen")),
    )
    add(samples, "unifi_protect_nvr_uptime_seconds", labels, numeric_value(nvr.get("uptime")))
    add(samples, "unifi_protect_nvr_is_recording", labels, bool_value(nvr.get("isRecording")))
    add(
        samples,
        "unifi_protect_nvr_recording_disabled",
        labels,
        bool_value(nvr.get("isRecordingDisabled")),
    )
    add(
        samples,
        "unifi_protect_nvr_recording_motion_only",
        labels,
        bool_value(nvr.get("isRecordingMotionOnly")),
    )
    add(
        samples,
        "unifi_protect_nvr_disk_used_bytes",
        labels,
        first_nested_number(
            nvr,
            ("storageStats", "recordingSpace", "used"),
            ("systemInfo", "storage", "used"),
            ("diskUsed",),
            ("storageUsed",),
        ),
    )
    add(
        samples,
        "unifi_protect_nvr_disk_available_bytes",
        labels,
        first_nested_number(
            nvr,
            ("storageStats", "recordingSpace", "available"),
            ("systemInfo", "storage", "available"),
        ),
    )
    add(
        samples,
        "unifi_protect_nvr_disk_total_bytes",
        labels,
        first_nested_number(
            nvr,
            ("storageStats", "recordingSpace", "total"),
            ("systemInfo", "storage", "size"),
            ("diskSize",),
            ("storageSize",),
        ),
    )
    add(
        samples,
        "unifi_protect_nvr_cpu_load_percent",
        labels,
        first_nested_number(nvr, ("systemInfo", "cpu", "averageLoad")),
    )
    add(
        samples,
        "unifi_protect_nvr_cpu_temperature_celsius",
        labels,
        first_nested_number(nvr, ("systemInfo", "cpu", "temperature")),
    )
    add(
        samples,
        "unifi_protect_nvr_memory_available_kilobytes",
        labels,
        first_nested_number(nvr, ("systemInfo", "memory", "available")),
    )
    add(
        samples,
        "unifi_protect_nvr_memory_free_kilobytes",
        labels,
        first_nested_number(nvr, ("systemInfo", "memory", "free")),
    )
    add(
        samples,
        "unifi_protect_nvr_memory_total_kilobytes",
        labels,
        first_nested_number(nvr, ("systemInfo", "memory", "total")),
    )
    add(samples, "unifi_protect_nvr_camera_count", labels, numeric_value(nvr.get("cameraCount")))
    add(
        samples,
        "unifi_protect_nvr_camera_utilization_percent",
        labels,
        numeric_value(nvr.get("cameraUtilization")),
    )
    return samples


def camera_samples(cameras: list[dict[str, Any]]) -> list[Sample]:
    samples: list[Sample] = []
    for camera in cameras:
        labels = device_labels(camera)
        samples.append(Sample("unifi_protect_camera_info", labels, 1.0))
        add(
            samples,
            "unifi_protect_camera_connected",
            labels,
            bool_value(camera.get("isConnected")),
        )
        add(
            samples,
            "unifi_protect_camera_recording_enabled",
            labels,
            bool_value(camera.get("isRecording")),
        )
        add(
            samples,
            "unifi_protect_camera_motion_detected",
            labels,
            bool_value(camera.get("isMotionDetected")),
        )
        add(
            samples,
            "unifi_protect_camera_smart_detected",
            labels,
            bool_value(camera.get("isSmartDetected")),
        )
        add(
            samples,
            "unifi_protect_camera_up_since_timestamp_seconds",
            labels,
            timestamp_value(camera.get("upSince")),
        )
        add(
            samples,
            "unifi_protect_camera_last_seen_timestamp_seconds",
            labels,
            timestamp_value(camera.get("lastSeen")),
        )
        add(
            samples,
            "unifi_protect_camera_connected_since_timestamp_seconds",
            labels,
            timestamp_value(camera.get("connectedSince")),
        )
        add(
            samples,
            "unifi_protect_camera_last_motion_timestamp_seconds",
            labels,
            first_timestamp(
                camera,
                ("lastMotion",),
                ("lastMotionEvent", "start"),
                ("lastMotionEvent", "end"),
            ),
        )
        add(samples, "unifi_protect_camera_rx_bytes", labels, first_number(camera, "rxBytes", "bytesRx"))
        add(samples, "unifi_protect_camera_tx_bytes", labels, first_number(camera, "txBytes", "bytesTx"))
        add(
            samples,
            "unifi_protect_camera_wifi_signal_quality",
            labels,
            first_nested_number(
                camera,
                ("wifiConnectionState", "signalQuality"),
                ("wirelessConnectionState", "signalState", "signalQuality"),
                ("stats", "wifiQuality"),
            ),
        )
        add(
            samples,
            "unifi_protect_camera_wifi_signal_strength_dbm",
            labels,
            first_nested_number(
                camera,
                ("wirelessConnectionState", "signalState", "signalStrength"),
                ("wifiConnectionState", "signalStrength"),
            ),
        )
        add(
            samples,
            "unifi_protect_camera_battery_percent",
            labels,
            first_nested_number(
                camera,
                ("batteryStatus", "percentage"),
                ("wirelessConnectionState", "batteryStatus", "percentage"),
                ("batteryPercentage",),
                ("batteryPercent",),
            ),
        )
    return samples


def light_samples(lights: list[dict[str, Any]]) -> list[Sample]:
    samples: list[Sample] = []
    for light in lights:
        labels = device_labels(light)
        samples.append(Sample("unifi_protect_light_info", labels, 1.0))
        add(samples, "unifi_protect_light_connected", labels, bool_value(light.get("isConnected")))
        add(samples, "unifi_protect_light_on", labels, bool_value(light.get("isLightOn")))
        settings = light.get("lightDeviceSettings")
        add(
            samples,
            "unifi_protect_light_brightness_percent",
            labels,
            numeric_value(settings.get("ledLevel") if isinstance(settings, dict) else None),
        )
    return samples


def sensor_samples(sensors: list[dict[str, Any]]) -> list[Sample]:
    samples: list[Sample] = []
    for sensor in sensors:
        labels = device_labels(sensor)
        samples.append(Sample("unifi_protect_sensor_info", labels, 1.0))
        add(samples, "unifi_protect_sensor_connected", labels, bool_value(sensor.get("isConnected")))
        add(samples, "unifi_protect_sensor_updating", labels, bool_value(sensor.get("isUpdating")))
        add(samples, "unifi_protect_sensor_open", labels, bool_value(sensor.get("isOpened")))
        add(
            samples,
            "unifi_protect_sensor_motion_detected",
            labels,
            bool_value(sensor.get("isMotionDetected")),
        )
        add(
            samples,
            "unifi_protect_sensor_up_since_timestamp_seconds",
            labels,
            timestamp_value(sensor.get("upSince")),
        )
        add(
            samples,
            "unifi_protect_sensor_last_seen_timestamp_seconds",
            labels,
            timestamp_value(sensor.get("lastSeen")),
        )
        add(
            samples,
            "unifi_protect_sensor_connected_since_timestamp_seconds",
            labels,
            timestamp_value(sensor.get("connectedSince")),
        )
        add(
            samples,
            "unifi_protect_sensor_motion_detected_at_timestamp_seconds",
            labels,
            timestamp_value(sensor.get("motionDetectedAt")),
        )
        add(
            samples,
            "unifi_protect_sensor_temperature_celsius",
            labels,
            first_nested_number(sensor, ("stats", "temperature", "value"), ("temperature",)),
        )
        add(
            samples,
            "unifi_protect_sensor_humidity_percent",
            labels,
            first_nested_number(sensor, ("stats", "humidity", "value"), ("humidity",)),
        )
        add(
            samples,
            "unifi_protect_sensor_light_lux",
            labels,
            first_nested_number(sensor, ("stats", "light", "value"), ("light",)),
        )
        add(
            samples,
            "unifi_protect_sensor_battery_percent",
            labels,
            first_nested_number(
                sensor,
                ("batteryStatus", "percentage"),
                ("wirelessConnectionState", "batteryStatus", "percentage"),
                ("batteryPercentage",),
                ("batteryPercent",),
            ),
        )
        add(
            samples,
            "unifi_protect_sensor_battery_low",
            labels,
            first_bool(
                sensor,
                ("batteryStatus", "isLow"),
                ("wirelessConnectionState", "batteryStatus", "isLow"),
            ),
        )
        add(
            samples,
            "unifi_protect_sensor_signal_quality",
            labels,
            first_nested_number(
                sensor,
                ("wirelessConnectionState", "signalState", "signalQuality"),
                ("bluetoothConnectionState", "signalQuality"),
            ),
        )
        add(
            samples,
            "unifi_protect_sensor_signal_strength_dbm",
            labels,
            first_nested_number(
                sensor,
                ("wirelessConnectionState", "signalState", "signalStrength"),
                ("bluetoothConnectionState", "signalStrength"),
            ),
        )
        add(
            samples,
            "unifi_protect_sensor_leak_detected_at_timestamp_seconds",
            labels,
            first_timestamp(sensor, ("leakDetectedAt",), ("externalLeakDetectedAt",)),
        )
        add(
            samples,
            "unifi_protect_sensor_tampering_detected_at_timestamp_seconds",
            labels,
            timestamp_value(sensor.get("tamperingDetectedAt")),
        )
    return samples


def viewer_samples(viewers: list[dict[str, Any]]) -> list[Sample]:
    samples: list[Sample] = []
    for viewer in viewers:
        labels = device_labels(viewer)
        samples.append(Sample("unifi_protect_viewer_info", labels, 1.0))
        add(samples, "unifi_protect_viewer_connected", labels, bool_value(viewer.get("isConnected")))
    return samples


def device_labels(device: dict[str, Any]) -> dict[str, str]:
    return {
        "id": str(device.get("id", "")),
        "name": str(device.get("name") or device.get("displayName") or device.get("id", "")),
        "model": str(
            device.get("marketName")
            or device.get("type")
            or device.get("modelKey")
            or device.get("model")
            or ""
        ),
        "mac": str(device.get("mac") or device.get("macAddress") or ""),
        "host": str(device.get("host") or device.get("hostAddress") or ""),
    }


def list_value(data: dict[str, Any], key: str) -> list[dict[str, Any]]:
    value = data.get(key)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def add(samples: list[Sample], name: str, labels: dict[str, str], value: float | None) -> None:
    if value is not None:
        samples.append(Sample(name, labels, value))


def bool_value(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "yes", "on", "connected", "recording", "1"}:
            return 1.0
        if normalized in {"false", "no", "off", "disconnected", "0"}:
            return 0.0
    return numeric_value(value)


def timestamp_value(value: Any) -> float | None:
    number = numeric_value(value)
    if number is None:
        return None
    if number > 10_000_000_000:
        return number / 1000.0
    return number


def first_number(data: dict[str, Any], *keys: str) -> float | None:
    for key in keys:
        value = data.get(key)
        number = numeric_value(value)
        if number is not None:
            return number
    return None


def first_nested_number(data: dict[str, Any], *paths: tuple[str, ...]) -> float | None:
    for path in paths:
        number = numeric_value(nested_value(data, path))
        if number is not None:
            return number
    return None


def first_timestamp(data: dict[str, Any], *paths: tuple[str, ...]) -> float | None:
    for path in paths:
        timestamp = timestamp_value(nested_value(data, path))
        if timestamp is not None:
            return timestamp
    return None


def first_bool(data: dict[str, Any], *paths: tuple[str, ...]) -> float | None:
    for path in paths:
        value = bool_value(nested_value(data, path))
        if value is not None:
            return value
    return None


def nested_value(data: dict[str, Any], path: tuple[str, ...]) -> Any:
    value: Any = data
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value
