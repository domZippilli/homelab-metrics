import unittest
from unittest.mock import patch

from unifi_metrics.config import Config
from unifi_metrics.ecoflow_client import flatten, sign_text, signature_text
from unifi_metrics.ecoflow_metrics import collect_ecoflow_samples
from unifi_metrics.exporter import Handler, redact
from unifi_metrics.metrics import collect_pdu_samples, render_prometheus
from unifi_metrics.unifi_metrics import collect_unifi_device_samples
from unifi_metrics.zfs_status import parse_zpool_status


class MetricsTest(unittest.TestCase):
    def test_collects_device_and_outlet_numbers(self) -> None:
        samples = collect_pdu_samples(
            [
                {
                    "mac": "aa:bb",
                    "name": "rack-pdu",
                    "model": "USP-PDU-Pro",
                    "type": "power",
                    "outlet_ac_power_consumption": "12.500",
                    "state": 1,
                    "outlet_overrides": [
                        {"index": 1, "name": "modem", "relay_state": True},
                    ],
                    "outlet_table": [
                        {
                            "index": 1,
                            "name": "modem",
                            "outlet_current": "0.100",
                            "outlet_power": "12.500",
                            "outlet_power_factor": "0.950",
                            "outlet_voltage": "119.700",
                            "relay_state": "on",
                        },
                        {"index": 2, "name": "unused", "power": 0, "relay_state": "off"},
                    ],
                }
            ],
            "pdu",
        )
        names = {sample.name for sample in samples}
        self.assertIn("unifi_pdu_state", names)
        self.assertIn("unifi_pdu_outlet_ac_power_consumption_watts", names)
        self.assertIn("unifi_pdu_outlet_power_watts", names)
        self.assertIn("unifi_pdu_outlet_current_amps", names)
        self.assertIn("unifi_pdu_outlet_voltage_volts", names)
        self.assertIn("unifi_pdu_outlet_relay_state", names)
        modem_power = [
            sample
            for sample in samples
            if sample.name == "unifi_pdu_outlet_power_watts"
            and sample.labels["outlet_index"] == "1"
        ]
        self.assertEqual(len(modem_power), 1)
        self.assertEqual(modem_power[0].value, 12.5)

    def test_does_not_match_non_pdu_devices_just_because_they_have_outlet_data(self) -> None:
        samples = collect_pdu_samples(
            [
                {
                    "mac": "aa:bb",
                    "name": "Dream Machine",
                    "model": "UDMPROMAX",
                    "type": "udm",
                    "outlet_table": [{"index": 1, "relay_state": True}],
                }
            ],
            "pdu|usp-pdu|smartpower|power strip|outlet",
        )
        self.assertEqual(samples, [])

    def test_renders_escaped_labels(self) -> None:
        body = render_prometheus(
            collect_pdu_samples(
                [{"mac": "aa", "name": 'rack "pdu"', "model": "PDU", "uptime": 10}],
                "pdu",
            ),
            up=True,
            duration_seconds=0.25,
        )
        self.assertIn('name="rack \\"pdu\\""', body)
        self.assertIn("unifi_up 1", body)

    def test_render_deduplicates_identical_series(self) -> None:
        body = render_prometheus(
            collect_pdu_samples(
                [{"mac": "aa", "name": "rack-pdu", "model": "PDU", "_uptime": 10, "uptime": 10}],
                "pdu",
            ),
            up=True,
            duration_seconds=0.25,
        )
        self.assertEqual(body.count('unifi_pdu_uptime{mac="aa"'), 1)

    def test_redacts_debug_payload(self) -> None:
        payload = {"name": "pdu", "api_key": "secret", "children": [{"token": "secret"}]}
        self.assertEqual(
            redact(payload),
            {"name": "pdu", "api_key": "[redacted]", "children": [{"token": "[redacted]"}]},
        )

    def test_known_routes_ignore_query_string(self) -> None:
        self.assertEqual(Handler._route("/metrics?x=1"), "/metrics")

    def test_collects_ecoflow_quota_numbers(self) -> None:
        samples = collect_ecoflow_samples(
            [
                {
                    "sn": "ABC123",
                    "deviceName": "Delta Pro",
                    "productName": "DELTA Pro",
                    "online": True,
                }
            ],
            {
                "ABC123": {
                    "soc": "87",
                    "wattsOutSum": 123.4,
                    "nested": {"temp": "31.5"},
                    "enBeep": True,
                }
            },
        )
        names = {sample.name for sample in samples}
        self.assertIn("ecoflow_device_info", names)
        self.assertIn("ecoflow_device_online", names)
        self.assertIn("ecoflow_quota_soc", names)
        self.assertIn("ecoflow_quota_wattsoutsum", names)
        self.assertIn("ecoflow_quota_nested_temp", names)
        self.assertIn("ecoflow_quota_enbeep", names)

    def test_collects_delta_pro_3_curated_metrics(self) -> None:
        samples = collect_ecoflow_samples(
            [
                {
                    "sn": "MR51ZAS5PGCA0561",
                    "productName": "DELTA Pro 3",
                    "online": 1,
                }
            ],
            {
                "MR51ZAS5PGCA0561": {
                    "cmsBattSoc": 98.5,
                    "powInSumW": 100,
                    "powOutSumW": 50,
                    "enBeep": False,
                }
            },
        )
        values = {sample.name: sample.value for sample in samples}
        self.assertEqual(values["ecoflow_delta_pro_3_battery_soc_percent"], 98.5)
        self.assertEqual(values["ecoflow_delta_pro_3_input_power_watts"], 100)
        self.assertEqual(values["ecoflow_delta_pro_3_output_power_watts"], 50)
        self.assertEqual(values["ecoflow_delta_pro_3_beeper_enabled"], 0)

    def test_ecoflow_flatten_uses_dotted_keys_for_signing(self) -> None:
        self.assertEqual(flatten({"a": {"b": 1}, "c": [True]}), {"a.b": "1", "c[0]": "True"})

    def test_ecoflow_signature_matches_documentation_example(self) -> None:
        text = signature_text(
            {
                "params.cmdSet": "11",
                "params.eps": "0",
                "params.id": "24",
                "sn": "123456789",
            },
            "Fp4SvIprYSDPXtYJidEtUAd1o",
            "345164",
            "1671171709428",
        )
        self.assertEqual(
            text,
            "params.cmdSet=11&params.eps=0&params.id=24&sn=123456789&"
            "accessKey=Fp4SvIprYSDPXtYJidEtUAd1o&nonce=345164&timestamp=1671171709428",
        )
        self.assertEqual(
            sign_text(text, "WIbFEKre0s6sLnh4ei7SPUeYnptHG6V"),
            "07c13b65e037faf3b153d51613638fa80003c4c38d2407379a7f52851af1473e",
        )

    def test_config_allows_ecoflow_without_unifi(self) -> None:
        env = {
            "ECOFLOW_ACCESS_KEY": "access",
            "ECOFLOW_SECRET_KEY": "secret",
            "ECOFLOW_DEVICE_SNS": "abc, def",
        }
        with patch("unifi_metrics.config.load_dotenv"), patch.dict("os.environ", env, clear=True):
            config = Config.from_env()
        self.assertFalse(config.unifi_enabled)
        self.assertTrue(config.ecoflow_enabled)
        self.assertEqual(config.ecoflow_device_sns, ("abc", "def"))

    def test_config_allows_zfs_without_unifi_or_ecoflow(self) -> None:
        with patch("unifi_metrics.config.load_dotenv"), patch.dict(
            "os.environ", {"ZFS_ENABLED": "true", "ZFS_POOLS": "tank, backup"}, clear=True
        ):
            config = Config.from_env()
        self.assertTrue(config.zfs_enabled)
        self.assertEqual(config.zfs_pools, ("tank", "backup"))

    def test_collects_curated_unifi_device_and_port_metrics(self) -> None:
        samples = collect_unifi_device_samples(
            [
                {
                    "mac": "aa",
                    "name": "Switch",
                    "model": "USW",
                    "type": "usw",
                    "version": "1.0",
                    "state": 1,
                    "uptime": 123,
                    "system-stats": {"cpu": "4.5", "mem": "33.0"},
                    "sys_stats": {"loadavg_1": "0.1", "mem_total": 1000, "mem_used": 500},
                    "port_table": [
                        {
                            "port_idx": 1,
                            "name": "Port 1",
                            "media": "GE",
                            "up": True,
                            "enable": True,
                            "speed": 1000,
                            "rx_bytes": 10,
                            "tx_bytes": 20,
                            "poe_enable": True,
                            "poe_good": True,
                            "poe_power": "12.5",
                            "poe_voltage": "54.1",
                            "poe_current": "231.0",
                        }
                    ],
                }
            ]
        )
        values = {sample.name: sample.value for sample in samples}
        self.assertEqual(values["unifi_device_up"], 1)
        self.assertEqual(values["unifi_device_cpu_usage_percent"], 4.5)
        self.assertEqual(values["unifi_switch_port_up"], 1)
        self.assertEqual(values["unifi_switch_port_poe_power_watts"], 12.5)

    def test_collects_curated_unifi_gateway_and_ap_metrics(self) -> None:
        samples = collect_unifi_device_samples(
            [
                {
                    "mac": "gw",
                    "name": "Gateway",
                    "model": "UDM",
                    "type": "udm",
                    "state": 1,
                    "uplink": {
                        "name": "eth9",
                        "comment": "WAN",
                        "ip": "192.0.2.10",
                        "up": True,
                        "latency": 4,
                        "rx_bytes": 100,
                        "tx_bytes": 200,
                        "speed": 10000,
                    },
                },
                {
                    "mac": "ap",
                    "name": "AP",
                    "model": "U7",
                    "type": "uap",
                    "state": 1,
                    "radio_table": [{"radio": "na", "name": "wifi1", "ht": "80", "nss": 4}],
                    "vap_table": [
                        {
                            "radio": "na",
                            "radio_name": "wifi1",
                            "essid": "wifi",
                            "usage": "user",
                            "up": True,
                            "num_sta": 7,
                            "channel": 36,
                            "bw": 80,
                            "tx_power": 21,
                            "rx_errors": 1,
                        }
                    ],
                },
            ]
        )
        values = {sample.name: sample.value for sample in samples}
        self.assertEqual(values["unifi_gateway_wan_up"], 1)
        self.assertEqual(values["unifi_gateway_wan_latency_ms"], 4)
        self.assertEqual(values["unifi_ap_radio_channel_width_mhz"], 80)
        self.assertEqual(values["unifi_ap_vap_clients"], 7)

    def test_parses_zpool_status_scrub_and_errors(self) -> None:
        samples = parse_zpool_status(
            """
  pool: plex-pool
 state: ONLINE
  scan: scrub repaired 0B in 03:05:44 with 0 errors on Sun Jun  7 06:05:45 2026
config:

        NAME                                          STATE     READ WRITE CKSUM
        plex-pool                                     ONLINE       0     0     0
          raidz1-0                                    ONLINE       0     0     0
            ata-WDC_WD30EFRX-68EUZN0_WD-WCC4N0NJJJHT  ONLINE       1     2     3

errors: No known data errors
"""
        )
        values = {(sample.name, sample.labels.get("vdev", "")): sample.value for sample in samples}
        self.assertEqual(values[("homelab_zfs_scrub_repaired_bytes", "")], 0)
        self.assertEqual(values[("homelab_zfs_scrub_errors", "")], 0)
        self.assertEqual(values[("homelab_zfs_scrub_duration_seconds", "")], 11144)
        self.assertEqual(values[("homelab_zfs_data_errors", "")], 0)
        self.assertEqual(
            values[("homelab_zfs_vdev_read_errors", "ata-WDC_WD30EFRX-68EUZN0_WD-WCC4N0NJJJHT")],
            1,
        )
        self.assertEqual(
            values[
                ("homelab_zfs_vdev_write_errors", "ata-WDC_WD30EFRX-68EUZN0_WD-WCC4N0NJJJHT")
            ],
            2,
        )
        self.assertEqual(
            values[
                (
                    "homelab_zfs_vdev_checksum_errors",
                    "ata-WDC_WD30EFRX-68EUZN0_WD-WCC4N0NJJJHT",
                )
            ],
            3,
        )


if __name__ == "__main__":
    unittest.main()
