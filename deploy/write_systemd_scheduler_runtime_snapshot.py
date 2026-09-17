#!/usr/bin/env python3
"""Write the bounded host systemd scheduler observation consumed by web."""

from __future__ import annotations

import json
import os
import selectors
import stat
import subprocess
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "applylens.scheduler-runtime-observation.v1"
SYSTEMCTL = "/usr/bin/systemctl"
OUTPUT_PATH = Path("/var/lib/applylens-scheduler-runtime/status.json")
COMMAND_TIMEOUT_SECONDS = 5
MAX_COMMAND_OUTPUT_BYTES = 16 * 1024
PROCESS_CLEANUP_TIMEOUT_SECONDS = 1
MAX_SNAPSHOT_BYTES = 64 * 1024

JOBS = (
    (
        "agent_discovery",
        "applylens-agent-discovery.timer",
        "applylens-agent-discovery.service",
    ),
    (
        "live_pipeline",
        "applylens-live-pipeline.timer",
        "applylens-live-pipeline.service",
    ),
)
TIMER_PROPERTIES = (
    "LoadState",
    "ActiveState",
    "SubState",
    "UnitFileState",
    "NextElapseUSecRealtime",
)
SERVICE_PROPERTIES = (
    "ActiveState",
    "SubState",
    "Result",
    "ExecMainStatus",
)


def _systemctl_environment() -> dict[str, str]:
    return {
        "LANG": "C",
        "LC_ALL": "C",
        "PATH": "/usr/bin:/bin",
        "SYSTEMD_COLORS": "0",
        "SYSTEMD_PAGER": "cat",
        "TZ": "UTC",
    }


def _run_bounded_systemctl(command: list[str]) -> tuple[int, str]:
    """Cap combined stdout + stderr bytes during capture, before decoding.

    Retain at most MAX_COMMAND_OUTPUT_BYTES; read at most one extra byte to
    detect overflow. Pipes provide backpressure without disk capture files.
    """
    process = subprocess.Popen(
        command, env=_systemctl_environment(), shell=False,
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        bufsize=0,
    )
    deadline = time.monotonic() + COMMAND_TIMEOUT_SECONDS
    streams = (process.stdout, process.stderr)
    captured = [bytearray(), bytearray()]
    total = 0
    try:
        with selectors.DefaultSelector() as selector:
            for index, stream in enumerate(streams):
                os.set_blocking(stream.fileno(), False)
                selector.register(stream, selectors.EVENT_READ, index)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired(command, COMMAND_TIMEOUT_SECONDS)
                for key, _events in selector.select(remaining):
                    chunk = os.read(
                        key.fd, min(4096, MAX_COMMAND_OUTPUT_BYTES - total + 1)
                    )
                    if not chunk:
                        selector.unregister(key.fileobj)
                        continue
                    total += len(chunk)
                    if total > MAX_COMMAND_OUTPUT_BYTES:
                        raise RuntimeError("systemctl output exceeded the bounded limit")
                    captured[key.data].extend(chunk)
            returncode = process.wait(timeout=max(0, deadline - time.monotonic()))
        stdout = captured[0].decode("utf-8", errors="strict")
        captured[1].decode("utf-8", errors="strict")
        return returncode, stdout
    finally:
        # Do not communicate()/drain: that could accumulate additional output.
        for stream in streams:
            stream.close()
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=PROCESS_CLEANUP_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=PROCESS_CLEANUP_TIMEOUT_SECONDS)


def _systemctl_show(unit_name: str, properties: tuple[str, ...]) -> dict[str, str]:
    allowed_units = {
        unit for _job, timer, service in JOBS for unit in (timer, service)
    }
    if unit_name not in allowed_units:
        raise ValueError("unsupported systemd unit")

    command = [
        SYSTEMCTL,
        "show",
        unit_name,
        "--no-pager",
        f"--property={','.join(properties)}",
    ]
    returncode, stdout = _run_bounded_systemctl(command)
    if returncode != 0:
        raise RuntimeError("systemctl show failed")

    expected = set(properties)
    parsed: dict[str, str] = {}
    for line in stdout.splitlines():
        if not line or "=" not in line:
            raise ValueError("malformed systemctl show output")
        key, value = line.split("=", 1)
        if key not in expected or key in parsed:
            raise ValueError("unexpected systemctl show property")
        parsed[key] = value.strip()
    if set(parsed) != expected:
        raise ValueError("incomplete systemctl show output")
    return parsed


def _systemd_timestamp_to_utc(value: str) -> str | None:
    raw = str(value or "").strip()
    if raw in {"", "n/a"}:
        return None
    parts = raw.split()
    if (
        len(parts) != 4
        or parts[0] not in {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}
        or parts[3] != "UTC"
    ):
        raise ValueError("invalid systemd timestamp")
    parsed = datetime.fromisoformat(f"{parts[1]}T{parts[2]}")
    return parsed.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")


def _collect_job(job_name: str, timer_unit: str, service_unit: str) -> dict[str, Any]:
    timer = _systemctl_show(timer_unit, TIMER_PROPERTIES)
    service = _systemctl_show(service_unit, SERVICE_PROPERTIES)
    try:
        exec_main_status = int(service["ExecMainStatus"])
    except ValueError as exc:
        raise ValueError("invalid ExecMainStatus") from exc
    if exec_main_status < 0:
        raise ValueError("invalid ExecMainStatus")
    return {
        "job_name": job_name,
        "timer": {
            "unit_name": timer_unit,
            "load_state": timer["LoadState"],
            "active_state": timer["ActiveState"],
            "sub_state": timer["SubState"],
            "unit_file_state": timer["UnitFileState"],
            "expected_next_run_at": _systemd_timestamp_to_utc(
                timer["NextElapseUSecRealtime"]
            ),
        },
        "service": {
            "unit_name": service_unit,
            "active_state": service["ActiveState"],
            "sub_state": service["SubState"],
            "result": service["Result"],
            "exec_main_status": exec_main_status,
        },
    }


def collect_snapshot() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        ),
        "runtime_provider": "systemd",
        "collection_ok": True,
        "jobs": [_collect_job(*definition) for definition in JOBS],
    }


def failed_snapshot() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace(
            "+00:00", "Z"
        ),
        "runtime_provider": "systemd",
        "collection_ok": False,
        "jobs": [
            {
                "job_name": job_name,
                "timer": {
                    "unit_name": timer_unit,
                    "load_state": None,
                    "active_state": None,
                    "sub_state": None,
                    "unit_file_state": None,
                    "expected_next_run_at": None,
                },
                "service": {
                    "unit_name": service_unit,
                    "active_state": None,
                    "sub_state": None,
                    "result": None,
                    "exec_main_status": None,
                },
            }
            for job_name, timer_unit, service_unit in JOBS
        ],
    }


def write_snapshot_atomic(payload: dict[str, Any], output_path: Path = OUTPUT_PATH) -> None:
    encoded = (
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    if len(encoded) > MAX_SNAPSHOT_BYTES:
        raise ValueError("scheduler runtime snapshot exceeded the bounded limit")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}.",
        suffix=".tmp",
        dir=str(output_path.parent),
    )
    temporary_path = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o644)
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_path, output_path)
        directory_flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
        directory_descriptor = os.open(output_path.parent, directory_flags)
        try:
            os.fsync(directory_descriptor)
        finally:
            os.close(directory_descriptor)
        mode = stat.S_IMODE(output_path.stat().st_mode)
        if mode != 0o644:
            os.chmod(output_path, 0o644)
    finally:
        temporary_path.unlink(missing_ok=True)


def main() -> int:
    try:
        payload = collect_snapshot()
    except Exception:
        write_snapshot_atomic(failed_snapshot())
        return 1
    write_snapshot_atomic(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
