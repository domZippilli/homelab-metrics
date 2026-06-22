import unittest

from unifi_metrics.exporter import Handler, redact
from unifi_metrics.metrics import collect_pdu_samples, render_prometheus


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
        self.assertIn("unifi_device_info", names)
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


if __name__ == "__main__":
    unittest.main()
