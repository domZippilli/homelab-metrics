# homelab-metrics

A small Prometheus exporter for homelab devices, currently supporting:

- UniFi OS / Network device metrics, initially aimed at UDM Pro setups with
  UniFi SmartPower / PDU devices.
- UniFi Protect camera/NVR/sensor status metrics.
- EcoFlow cloud API device quota metrics.
- ZFS pool status and scrub metrics from `zpool status`.

UniFi's local API is not formally stable. This exporter uses the local UniFi OS
login flow and the Network application proxy endpoints, then exports numeric PDU
and outlet fields it finds in the device payload.

## Why local credentials

For a UDM Pro, the useful Network application data is usually available through
the local console API rather than a cloud API key. Create a local admin account
with the least privileges that can read Network devices.

## Configuration

Set environment variables for at least one source.

### UniFi

| Variable | Default | Description |
| --- | --- | --- |
| `UNIFI_HOST` | optional | UDM/UniFi OS host, for example `https://192.168.1.1` |
| `UNIFI_USERNAME` | optional | Local UniFi OS username |
| `UNIFI_PASSWORD` | optional | Local UniFi OS password |
| `UNIFI_SITE` | `default` | Network site id |
| `UNIFI_VERIFY_SSL` | `false` | Verify TLS certificates |
| `UNIFI_TIMEOUT_SECONDS` | `15` | API timeout |
| `UNIFI_PDU_FILTER` | `pdu|usp-pdu|smartpower|power strip|outlet` | Regex used against model/name/type |
| `UNIFI_PROTECT_ENABLED` | `false` | Enable UniFi Protect scraping with the same local UniFi OS account |

The local UniFi OS account must have Protect permissions, such as Protect Viewer
access. Without that, Protect endpoints return HTTP 403 while Network metrics
continue to work.

### EcoFlow

| Variable | Default | Description |
| --- | --- | --- |
| `ECOFLOW_ACCESS_KEY` | optional | EcoFlow developer access key |
| `ECOFLOW_SECRET_KEY` | optional | EcoFlow developer secret key |
| `ECOFLOW_HOST` | `https://api.ecoflow.com` | EcoFlow API host |
| `ECOFLOW_DEVICE_SNS` | all devices | Optional comma-separated serial numbers to scrape |
| `ECOFLOW_TIMEOUT_SECONDS` | `15` | API timeout |

For this setup, the Delta Pro 3 serial is `MR51ZAS5PGCA0561`. Set:

```sh
ECOFLOW_DEVICE_SNS=MR51ZAS5PGCA0561
```

Delta Pro 3 quota fields are exported with curated names for the documented
fields, for example `ecoflow_delta_pro_3_battery_soc_percent`,
`ecoflow_delta_pro_3_input_power_watts`, and
`ecoflow_delta_pro_3_output_power_watts`. Unknown quota fields still use the
generic `ecoflow_quota_*` fallback.

### Exporter

### ZFS

| Variable | Default | Description |
| --- | --- | --- |
| `ZFS_ENABLED` | `false` | Enable ZFS status scraping with `zpool` |
| `ZFS_POOLS` | all pools | Optional comma-separated pool names |

The exporter shells out to `zpool list` and `zpool status -p`. If running in a
container, the container needs access to ZFS tooling and host ZFS state.

| Variable | Default | Description |
| --- | --- | --- |
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
- `GET /debug/ecoflow` for a redacted JSON view of EcoFlow devices and quotas.
- `GET /debug/protect` for a redacted JSON view of UniFi Protect bootstrap data.

## Prometheus scrape config

```yaml
scrape_configs:
  - job_name: homelab_metrics
    static_configs:
      - targets: ["localhost:9130"]
```

## Docker

```sh
docker build -t homelab-metrics .
docker run --rm --env-file .env -p 9130:9130 homelab-metrics
```

## Test

```sh
python3 -m unittest discover -v
```
