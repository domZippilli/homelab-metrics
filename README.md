# unifi-metrics

A small Prometheus exporter for UniFi OS devices, initially aimed at UDM Pro
setups with UniFi SmartPower / PDU devices.

UniFi's local API is not formally stable. This exporter uses the local UniFi OS
login flow and the Network application proxy endpoints, then exports numeric PDU
and outlet fields it finds in the device payload.

## Why local credentials

For a UDM Pro, the useful Network application data is usually available through
the local console API rather than a cloud API key. Create a local admin account
with the least privileges that can read Network devices.

## Configuration

Set these environment variables:

| Variable | Default | Description |
| --- | --- | --- |
| `UNIFI_HOST` | required | UDM/UniFi OS host, for example `https://192.168.1.1` |
| `UNIFI_USERNAME` | required | Local UniFi OS username |
| `UNIFI_PASSWORD` | required | Local UniFi OS password |
| `UNIFI_SITE` | `default` | Network site id |
| `UNIFI_VERIFY_SSL` | `false` | Verify TLS certificates |
| `UNIFI_TIMEOUT_SECONDS` | `15` | API timeout |
| `UNIFI_PDU_FILTER` | `pdu|usp-pdu|smartpower|power strip|outlet` | Regex used against model/name/type |
| `EXPORTER_ADDR` | `0.0.0.0` | HTTP bind address |
| `EXPORTER_PORT` | `9130` | HTTP port |
| `SCRAPE_TTL_SECONDS` | `20` | Cache UniFi API results for this many seconds |

## Run locally

```sh
cp .env.example .env
python3 -m venv .venv
. .venv/bin/activate
python -m unifi_metrics
```

The exporter serves:

- `GET /metrics` for Prometheus.
- `GET /healthz` for a simple health check.
- `GET /debug/devices` for a redacted JSON view of devices matched as PDUs.

## Prometheus scrape config

```yaml
scrape_configs:
  - job_name: unifi_metrics
    static_configs:
      - targets: ["localhost:9130"]
```

## Docker

```sh
docker build -t unifi-metrics .
docker run --rm --env-file .env -p 9130:9130 unifi-metrics
```

## Test

```sh
python3 -m unittest discover -v
```
