from __future__ import annotations

import datetime as dt
import re
import subprocess

from .metrics import Sample


SCRUB_RE = re.compile(
    r"scrub repaired (?P<repaired>\S+) in (?P<duration>\S+) "
    r"with (?P<errors>\d+) errors on (?P<ended>.+)$"
)
VDEV_RE = re.compile(
    r"^\s+(?P<name>\S.*?)\s+(?P<state>[A-Z]+)\s+"
    r"(?P<read>\d+)\s+(?P<write>\d+)\s+(?P<cksum>\d+)\s*$"
)


def collect_zfs_status_samples(pools: tuple[str, ...], command: str = "zpool") -> list[Sample]:
    selected_pools = pools or tuple(_list_pools(command))
    samples: list[Sample] = []
    for pool in selected_pools:
        output = subprocess.check_output(
            [command, "status", "-p", pool],
            text=True,
            stderr=subprocess.STDOUT,
            timeout=15,
        )
        samples.extend(parse_zpool_status(output))
    return samples


def parse_zpool_status(output: str) -> list[Sample]:
    pool = ""
    samples: list[Sample] = []
    in_config = False
    for raw_line in output.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if stripped.startswith("pool:"):
            pool = stripped.split(":", 1)[1].strip()
            continue
        if stripped.startswith("scan:") and pool:
            samples.extend(_scan_samples(pool, stripped.split(":", 1)[1].strip()))
            continue
        if stripped == "config:":
            in_config = True
            continue
        if stripped.startswith("errors:") and pool:
            samples.append(
                Sample("homelab_zfs_data_errors", {"pool": pool}, _data_error_value(stripped))
            )
            in_config = False
            continue
        if in_config and pool:
            samples.extend(_vdev_error_sample(pool, line))
    return samples


def _scan_samples(pool: str, scan: str) -> list[Sample]:
    labels = {"pool": pool}
    match = SCRUB_RE.search(scan)
    if not match:
        return [Sample("homelab_zfs_scrub_status", {**labels, "status": scan[:120]}, 1.0)]

    ended_at = _parse_zpool_datetime(match.group("ended"))
    return [
        Sample("homelab_zfs_scrub_repaired_bytes", labels, _parse_size_bytes(match.group("repaired"))),
        Sample("homelab_zfs_scrub_errors", labels, float(match.group("errors"))),
        Sample(
            "homelab_zfs_scrub_duration_seconds",
            labels,
            _parse_duration_seconds(match.group("duration")),
        ),
        Sample("homelab_zfs_scrub_end_timestamp_seconds", labels, ended_at.timestamp()),
        Sample("homelab_zfs_scrub_status", {**labels, "status": "scrub"}, 1.0),
    ]


def _vdev_error_sample(pool: str, line: str) -> list[Sample]:
    match = VDEV_RE.match(line)
    if not match:
        return []
    name = match.group("name").strip()
    if name in {"NAME", pool} or name.startswith(("raidz", "mirror", "spare", "logs", "cache")):
        vdev_type = "aggregate"
    else:
        vdev_type = "device"
    labels = {"pool": pool, "vdev": name, "state": match.group("state"), "type": vdev_type}
    return [
        Sample("homelab_zfs_vdev_read_errors", labels, float(match.group("read"))),
        Sample("homelab_zfs_vdev_write_errors", labels, float(match.group("write"))),
        Sample("homelab_zfs_vdev_checksum_errors", labels, float(match.group("cksum"))),
    ]


def _data_error_value(line: str) -> float:
    return 0.0 if "No known data errors" in line else 1.0


def _parse_zpool_datetime(value: str) -> dt.datetime:
    try:
        parsed = dt.datetime.strptime(value, "%a %b %d %H:%M:%S %Y")
    except ValueError:
        current_year = dt.datetime.now().year
        parsed = dt.datetime.strptime(f"{value} {current_year}", "%a %b %d %H:%M:%S %Y")
    return parsed.replace(tzinfo=dt.datetime.now().astimezone().tzinfo)


def _parse_duration_seconds(value: str) -> float:
    parts = [int(part) for part in value.split(":")]
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return float(hours * 3600 + minutes * 60 + seconds)
    if len(parts) == 2:
        minutes, seconds = parts
        return float(minutes * 60 + seconds)
    return float(parts[0])


def _parse_size_bytes(value: str) -> float:
    if value == "0B":
        return 0.0
    match = re.fullmatch(r"(?P<number>\d+(?:\.\d+)?)(?P<unit>[KMGTPEZ]?)(?:B)?", value)
    if not match:
        return 0.0
    number = float(match.group("number"))
    unit = match.group("unit")
    scale = {"": 1, "K": 1024, "M": 1024**2, "G": 1024**3, "T": 1024**4, "P": 1024**5}
    return number * scale.get(unit, 1)


def _list_pools(command: str) -> list[str]:
    output = subprocess.check_output(
        [command, "list", "-H", "-o", "name"],
        text=True,
        stderr=subprocess.STDOUT,
        timeout=15,
    )
    return [line.strip() for line in output.splitlines() if line.strip()]
