from __future__ import annotations

from pathlib import Path

from .metrics import Sample


GT_FREQ_FILES = {
    "media_RP0_freq_mhz": "homelab_gpu_media_rp0_frequency_mhz",
    "media_RPn_freq_mhz": "homelab_gpu_media_rpn_frequency_mhz",
    "punit_req_freq_mhz": "homelab_gpu_punit_requested_frequency_mhz",
    "rps_RP0_freq_mhz": "homelab_gpu_rps_rp0_frequency_mhz",
    "rps_RP1_freq_mhz": "homelab_gpu_rps_rp1_frequency_mhz",
    "rps_RPn_freq_mhz": "homelab_gpu_rps_rpn_frequency_mhz",
    "rps_act_freq_mhz": "homelab_gpu_rps_actual_frequency_mhz",
    "rps_cur_freq_mhz": "homelab_gpu_rps_current_frequency_mhz",
    "rps_boost_freq_mhz": "homelab_gpu_rps_boost_frequency_mhz",
    "rps_max_freq_mhz": "homelab_gpu_rps_max_frequency_mhz",
    "rps_min_freq_mhz": "homelab_gpu_rps_min_frequency_mhz",
}

GT_COUNTER_FILES = {
    "media_freq_factor": "homelab_gpu_media_frequency_factor",
    "rc6_enable": "homelab_gpu_rc6_enabled",
    "rc6_residency_ms": "homelab_gpu_rc6_residency_seconds_total",
}

THROTTLE_REASON_FILES = {
    "throttle_reason_pl1",
    "throttle_reason_pl2",
    "throttle_reason_pl4",
    "throttle_reason_prochot",
    "throttle_reason_ratl",
    "throttle_reason_status",
    "throttle_reason_thermal",
    "throttle_reason_vr_tdc",
    "throttle_reason_vr_thermalert",
}


def collect_gpu_samples(sysfs_path: str) -> list[Sample]:
    drm = Path(sysfs_path)
    device = drm / "device"
    card = drm.name
    if not device.exists():
        raise FileNotFoundError(f"{device} does not exist")

    labels = {
        "card": card,
        "vendor": read_text(device / "vendor"),
        "device": read_text(device / "device"),
        "subsystem_device": read_text(device / "subsystem_device"),
        "revision": read_text(device / "revision"),
    }
    samples = [Sample("homelab_gpu_info", labels, 1.0)]
    samples.extend(collect_hwmon_samples(device, card))
    samples.extend(collect_gt_samples(device, card))
    return samples


def collect_hwmon_samples(device: Path, card: str) -> list[Sample]:
    samples: list[Sample] = []
    for hwmon in sorted((device / "hwmon").glob("hwmon*")):
        name = read_text(hwmon / "name") or hwmon.name
        labels = {"card": card, "hwmon": hwmon.name, "name": name}
        samples.extend(
            [
                *scaled_sample(
                    "homelab_gpu_energy_joules_total",
                    hwmon / "energy1_input",
                    labels,
                    scale=1_000_000,
                ),
                *scaled_sample(
                    "homelab_gpu_voltage_volts",
                    hwmon / "in0_input",
                    labels,
                    scale=1_000,
                ),
                *scaled_sample(
                    "homelab_gpu_power_limit_watts",
                    hwmon / "power1_max",
                    labels,
                    scale=1_000_000,
                ),
                *scaled_sample(
                    "homelab_gpu_power_limit_interval_seconds",
                    hwmon / "power1_max_interval",
                    labels,
                    scale=1_000,
                ),
                *scaled_sample(
                    "homelab_gpu_power_rated_max_watts",
                    hwmon / "power1_rated_max",
                    labels,
                    scale=1_000_000,
                ),
            ]
        )
    return samples


def collect_gt_samples(device: Path, card: str) -> list[Sample]:
    samples: list[Sample] = []
    gt_root = device / "drm" / card / "gt"
    for gt in sorted(gt_root.glob("gt*")):
        if not gt.is_dir():
            continue
        labels = {"card": card, "gt": gt.name, "gt_id": read_text(gt / "id")}
        for filename, metric in GT_FREQ_FILES.items():
            samples.extend(scaled_sample(metric, gt / filename, labels))
        for filename, metric in GT_COUNTER_FILES.items():
            scale = 1_000 if filename.endswith("_ms") else 1
            samples.extend(scaled_sample(metric, gt / filename, labels, scale=scale))
        samples.extend(media_freq_factor_scaled(gt, labels))
        for filename in THROTTLE_REASON_FILES:
            samples.extend(
                scaled_sample(
                    "homelab_gpu_throttle_reason",
                    gt / filename,
                    {**labels, "reason": filename.removeprefix("throttle_reason_")},
                )
            )
    return samples


def media_freq_factor_scaled(gt: Path, labels: dict[str, str]) -> list[Sample]:
    raw = read_float(gt / "media_freq_factor")
    scale = read_float(gt / "media_freq_factor.scale")
    if raw is None or scale is None:
        return []
    return [Sample("homelab_gpu_media_frequency_factor_scaled", labels, raw * scale)]


def scaled_sample(
    name: str, path: Path, labels: dict[str, str], scale: float = 1
) -> list[Sample]:
    value = read_float(path)
    if value is None:
        return []
    return [Sample(name, labels, value / scale)]


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def read_float(path: Path) -> float | None:
    value = read_text(path)
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None
