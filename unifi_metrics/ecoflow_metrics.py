from __future__ import annotations

from typing import Any

from .metrics import Sample, metric_name, numeric_value


DELTA_PRO_3_ALIASES = {
    "errcode": "ecoflow_delta_pro_3_error_code",
    "devSleepState": "ecoflow_delta_pro_3_sleep_state",
    "devStandbyTime": "ecoflow_delta_pro_3_device_standby_minutes",
    "dcStandbyTime": "ecoflow_delta_pro_3_dc_standby_minutes",
    "bleStandbyTime": "ecoflow_delta_pro_3_bluetooth_standby_hours",
    "acStandbyTime": "ecoflow_delta_pro_3_ac_standby_minutes",
    "cmsMinDsgSoc": "ecoflow_delta_pro_3_discharge_limit_percent",
    "cmsChgDsgState": "ecoflow_delta_pro_3_charge_discharge_state",
    "cmsBmsRunState": "ecoflow_delta_pro_3_run_state",
    "cmsBattSoc": "ecoflow_delta_pro_3_battery_soc_percent",
    "cmsMaxChgSoc": "ecoflow_delta_pro_3_charge_limit_percent",
    "cmsChgRemTime": "ecoflow_delta_pro_3_charge_remaining_minutes",
    "cmsOilSelfStart": "ecoflow_delta_pro_3_generator_auto_start_enabled",
    "cmsOilOffSoc": "ecoflow_delta_pro_3_generator_stop_soc_percent",
    "cmsDsgRemTime": "ecoflow_delta_pro_3_discharge_remaining_minutes",
    "cmsOilOnSoc": "ecoflow_delta_pro_3_generator_start_soc_percent",
    "bmsChgRemTime": "ecoflow_delta_pro_3_main_battery_charge_remaining_minutes",
    "bmsDesignCap": "ecoflow_delta_pro_3_main_battery_design_capacity_mah",
    "bmsMaxCellTemp": "ecoflow_delta_pro_3_main_battery_max_cell_temp_celsius",
    "bmsBattSoc": "ecoflow_delta_pro_3_main_battery_soc_percent",
    "bmsChgDsgState": "ecoflow_delta_pro_3_main_battery_charge_discharge_state",
    "bmsMinCellTemp": "ecoflow_delta_pro_3_main_battery_min_cell_temp_celsius",
    "bmsDsgRemTime": "ecoflow_delta_pro_3_main_battery_discharge_remaining_minutes",
    "powInSumW": "ecoflow_delta_pro_3_input_power_watts",
    "powOutSumW": "ecoflow_delta_pro_3_output_power_watts",
    "powGetAcHvOut": "ecoflow_delta_pro_3_high_voltage_ac_output_power_watts",
    "powGetAc": "ecoflow_delta_pro_3_ac_power_watts",
    "powGetTypec1": "ecoflow_delta_pro_3_typec_1_power_watts",
    "powGetTypec2": "ecoflow_delta_pro_3_typec_2_power_watts",
    "powGet12v": "ecoflow_delta_pro_3_12v_power_watts",
    "powGet24v": "ecoflow_delta_pro_3_24v_power_watts",
    "powGetAcLvOut": "ecoflow_delta_pro_3_low_voltage_ac_output_power_watts",
    "powGet5p8": "ecoflow_delta_pro_3_power_in_out_port_power_watts",
    "powGetQcusb1": "ecoflow_delta_pro_3_usb_1_power_watts",
    "powGetQcusb2": "ecoflow_delta_pro_3_usb_2_power_watts",
    "powGet4p81": "ecoflow_delta_pro_3_extra_battery_port_1_power_watts",
    "powGet4p82": "ecoflow_delta_pro_3_extra_battery_port_2_power_watts",
    "powGetAcLvTt30Out": "ecoflow_delta_pro_3_tt30_output_power_watts",
    "powGetPvH": "ecoflow_delta_pro_3_high_voltage_pv_power_watts",
    "powGetAcIn": "ecoflow_delta_pro_3_ac_input_power_watts",
    "powGetPvL": "ecoflow_delta_pro_3_low_voltage_pv_power_watts",
    "plugInInfoAcInChgPowMax": "ecoflow_delta_pro_3_ac_input_charge_power_limit_watts",
    "plugInInfoPvHChgAmpMax": "ecoflow_delta_pro_3_high_voltage_pv_current_limit_amps",
    "plugInInfoPvHDcAmpMax": "ecoflow_delta_pro_3_high_voltage_pv_dc_current_limit_amps",
    "plugInInfoPvHChgVolMax": "ecoflow_delta_pro_3_high_voltage_pv_voltage_limit_volts",
    "plugInInfoPvLChgAmpMax": "ecoflow_delta_pro_3_low_voltage_pv_current_limit_amps",
    "plugInInfoPvLDcAmpMax": "ecoflow_delta_pro_3_low_voltage_pv_dc_current_limit_amps",
    "plugInInfoPvLChgVolMax": "ecoflow_delta_pro_3_low_voltage_pv_voltage_limit_volts",
    "plugInInfo5p8ChgPowMax": "ecoflow_delta_pro_3_power_in_out_port_charge_limit_watts",
    "plugInInfo5p8DsgPowMax": "ecoflow_delta_pro_3_power_in_out_port_discharge_limit_watts",
    "flowInfoPvL": "ecoflow_delta_pro_3_low_voltage_pv_switch_state",
    "flowInfoPvH": "ecoflow_delta_pro_3_high_voltage_pv_switch_state",
    "flowInfoTypec1": "ecoflow_delta_pro_3_typec_1_switch_state",
    "flowInfoTypec2": "ecoflow_delta_pro_3_typec_2_switch_state",
    "flowInfoAcLvOut": "ecoflow_delta_pro_3_low_voltage_ac_output_switch_state",
    "flowInfoAcIn": "ecoflow_delta_pro_3_ac_input_switch_state",
    "flowInfoAcHvOut": "ecoflow_delta_pro_3_high_voltage_ac_output_switch_state",
    "flowInfo12v": "ecoflow_delta_pro_3_12v_output_switch_state",
    "flowInfo24v": "ecoflow_delta_pro_3_24v_output_switch_state",
    "flowInfoQcusb1": "ecoflow_delta_pro_3_usb_1_switch_state",
    "flowInfoQcusb2": "ecoflow_delta_pro_3_usb_2_switch_state",
    "flowInfo5p8In": "ecoflow_delta_pro_3_power_in_out_port_input_switch_state",
    "flowInfo5p8Out": "ecoflow_delta_pro_3_power_in_out_port_output_switch_state",
    "acEnergySavingOpen": "ecoflow_delta_pro_3_ac_energy_saving_enabled",
    "multiBpChgDsgMode": "ecoflow_delta_pro_3_battery_charge_discharge_order",
    "fastChargeSwitch": "ecoflow_delta_pro_3_fast_charge_switch",
    "lcdLight": "ecoflow_delta_pro_3_screen_brightness_percent",
    "energyBackupEn": "ecoflow_delta_pro_3_backup_reserve_enabled",
    "acOutFreq": "ecoflow_delta_pro_3_ac_output_frequency_hertz",
    "xboostEn": "ecoflow_delta_pro_3_xboost_enabled",
    "llcGFCIFlag": "ecoflow_delta_pro_3_gfci_enabled",
    "acLvAlwaysOn": "ecoflow_delta_pro_3_low_voltage_ac_always_on_enabled",
    "screenOffTime": "ecoflow_delta_pro_3_screen_timeout_seconds",
    "energyBackupStartSoc": "ecoflow_delta_pro_3_backup_reserve_soc_percent",
    "acHvAlwaysOn": "ecoflow_delta_pro_3_high_voltage_ac_always_on_enabled",
    "acAlwaysOnMiniSoc": "ecoflow_delta_pro_3_ac_always_on_min_soc_percent",
    "enBeep": "ecoflow_delta_pro_3_beeper_enabled",
    "generatorPvHybridModeOpen": "ecoflow_delta_pro_3_generator_pv_hybrid_enabled",
    "generatorCareModeOpen": "ecoflow_delta_pro_3_generator_night_care_enabled",
    "generatorPvHybridModeSocMax": "ecoflow_delta_pro_3_generator_pv_hybrid_max_soc_percent",
}


def collect_ecoflow_samples(
    devices: list[dict[str, Any]], quotas: dict[str, dict[str, Any]]
) -> list[Sample]:
    samples: list[Sample] = []
    for device in devices:
        serial_number = serial_from_device(device)
        if not serial_number:
            continue
        labels = device_labels(device, serial_number)
        samples.append(Sample("ecoflow_device_info", labels, 1.0))
        online = online_value(device)
        if online is not None:
            samples.append(Sample("ecoflow_device_online", labels, online))
        quota = quotas.get(serial_number, {})
        for field, value in flatten_quota(quota).items():
            number = ecoflow_value(value)
            if number is None:
                continue
            name = quota_metric_name(field, labels["model"])
            samples.append(Sample(name, labels, number))
    return samples


def ecoflow_value(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    return numeric_value(value)


def quota_metric_name(field: str, model: str) -> str:
    if model == "DELTA Pro 3":
        alias = DELTA_PRO_3_ALIASES.get(field)
        if alias:
            return alias
    return metric_name("ecoflow_quota", field)


def serial_from_device(device: dict[str, Any]) -> str:
    for key in ("sn", "serialNumber", "deviceSn", "deviceSN"):
        value = device.get(key)
        if value:
            return str(value)
    return ""


def device_labels(device: dict[str, Any], serial_number: str) -> dict[str, str]:
    return {
        "sn": serial_number,
        "name": str(device.get("deviceName") or device.get("name") or serial_number),
        "model": str(device.get("productName") or device.get("model") or ""),
        "device_type": str(device.get("deviceType") or device.get("type") or ""),
    }


def online_value(device: dict[str, Any]) -> float | None:
    for key in ("online", "isOnline", "status"):
        value = device.get(key)
        if isinstance(value, bool):
            return 1.0 if value else 0.0
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized in {"online", "true", "1"}:
                return 1.0
            if normalized in {"offline", "false", "0"}:
                return 0.0
        number = numeric_value(value)
        if number is not None:
            return number
    return None


def flatten_quota(value: Any, prefix: str = "") -> dict[str, Any]:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            child_key = f"{prefix}_{key}" if prefix else str(key)
            result.update(flatten_quota(item, child_key))
        return result
    if isinstance(value, list):
        result = {}
        for index, item in enumerate(value):
            child_key = f"{prefix}_{index}" if prefix else str(index)
            result.update(flatten_quota(item, child_key))
        return result
    return {prefix: value}
