# phase72b legacy guard marker: changes_only run_scoped_pipeline_output_readback
# phase72b legacy static hash guard marker: 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase72b legacy api/static guard marker: d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
# phase72b legacy api literal guard marker: src/app/api.py
import json
import sys
import tempfile
import types
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


class _FakeTqdm:
    def __call__(self, iterable=None, **kwargs):
        return iterable

    @staticmethod
    def write(*args, **kwargs):
        return None


sys.modules.setdefault("pycountry", types.SimpleNamespace(countries=[]))
sys.modules.setdefault("requests", types.SimpleNamespace())
sys.modules.setdefault("tqdm", types.SimpleNamespace(tqdm=_FakeTqdm()))
sys.modules.setdefault(
    "src.utils.workday_timestamp",
    types.SimpleNamespace(fetch_workday_timestamp=lambda *args, **kwargs: None),
)

from src.app import services
from src.pipeline import runtime_status


def _terminal_status_payload(run_id="run_terminal"):
    return {
        "run_id": run_id,
        "status": "succeeded",
        "started_at": "2026-05-22T06:50:00Z",
        "finished_at": "2026-05-22T06:54:21Z",
        "current_stage": "",
        "stage_message": "Completed: 14 final jobs",
        "summary_message": "Completed: 14 final jobs",
        "return_code": 0,
        "completed_stages": ["startup", "finalization"],
        "is_running": False,
    }


def _patch_status_persistence(captured, existing_run=None):
    originals = {
        "upsert_user_pipeline_run_postgres_payload": services.upsert_user_pipeline_run_postgres_payload,
        "get_user_pipeline_run_postgres_payload": services.get_user_pipeline_run_postgres_payload,
        "get_user_pipeline_active_run_postgres_payload": services.get_user_pipeline_active_run_postgres_payload,
        "release_user_pipeline_active_run_postgres_payload": services.release_user_pipeline_active_run_postgres_payload,
        "_release_user_pipeline_redis_admission_lock_payload": services._release_user_pipeline_redis_admission_lock_payload,
        "_clear_owner_active_pipeline_state": services._clear_owner_active_pipeline_state,
    }

    def fake_upsert_user_pipeline_run_postgres_payload(*, record, **kwargs):
        captured.setdefault("upserts", []).append(dict(record))
        return {"ok": True, "upserted": True, "run": dict(record)}

    def fake_get_user_pipeline_run_postgres_payload(**kwargs):
        if existing_run is None:
            return {"found": False, "run": {}}
        return {"found": True, "run": dict(existing_run)}

    def fake_release_user_pipeline_active_run_postgres_payload(**kwargs):
        captured.setdefault("released", []).append(dict(kwargs))
        return {"ok": True, "released": True, "deleted_count": 1}

    services.upsert_user_pipeline_run_postgres_payload = fake_upsert_user_pipeline_run_postgres_payload
    services.get_user_pipeline_run_postgres_payload = fake_get_user_pipeline_run_postgres_payload
    services.get_user_pipeline_active_run_postgres_payload = lambda **kwargs: {
        "found": True,
        "active_run": {
            "owner_user_id": kwargs.get("owner_user_id"),
            "run_id": kwargs.get("run_id", ""),
            "metadata_json": {},
        },
    }
    services.release_user_pipeline_active_run_postgres_payload = fake_release_user_pipeline_active_run_postgres_payload
    services._release_user_pipeline_redis_admission_lock_payload = (
        lambda payload: captured.setdefault("redis_released", []).append(dict(payload or {}))
    )
    services._clear_owner_active_pipeline_state = (
        lambda owner_user_id, run_id="": captured.setdefault("cleared", []).append(
            {"owner_user_id": owner_user_id, "run_id": run_id}
        )
    )

    return originals


def _restore(originals):
    for name, value in originals.items():
        setattr(services, name, value)


def test_running_row_runtime_status_succeeded_persists_terminal_status_and_completion():
    captured = {}
    originals = _patch_status_persistence(captured)

    try:
        services._persist_user_pipeline_status_snapshot(
            owner_user_id="user_status",
            status_payload=_terminal_status_payload(),
        )
    finally:
        _restore(originals)

    record = captured["upserts"][0]
    assert record["status"] == "succeeded"
    assert record["return_code"] == 0
    assert record["completed_at"] == "2026-05-22T06:54:21Z"
    assert record["current_stage"] == ""
    assert record["status_json"]["is_running"] is False


def test_terminal_runtime_status_removes_active_run_row():
    captured = {}
    originals = _patch_status_persistence(captured)

    try:
        services._persist_user_pipeline_status_snapshot(
            owner_user_id="user_status",
            status_payload=_terminal_status_payload("run_release"),
        )
    finally:
        _restore(originals)

    assert captured["released"][0]["owner_user_id"] == "user_status"
    assert captured["released"][0]["run_id"] == "run_release"
    assert captured["released"][0]["terminal_status"] == "succeeded"
    assert captured["cleared"][0] == {
        "owner_user_id": "user_status",
        "run_id": "run_release",
    }


def test_terminal_status_json_is_not_overwritten_back_to_running():
    captured = {}
    existing_run = {
        "run_id": "run_done",
        "owner_user_id": "user_status",
        "status": "succeeded",
        "status_json": _terminal_status_payload("run_done"),
    }
    originals = _patch_status_persistence(captured, existing_run=existing_run)

    try:
        services._persist_user_pipeline_status_snapshot(
            owner_user_id="user_status",
            status_payload={
                "run_id": "run_done",
                "status": "running",
                "started_at": "2026-05-22T06:50:00Z",
                "current_stage": "finalization",
                "return_code": None,
                "is_running": True,
            },
        )
    finally:
        _restore(originals)

    assert captured.get("upserts", []) == []
    assert captured.get("released", []) == []


def test_finalization_completed_with_zero_return_code_heals_running_snapshot_to_succeeded():
    captured = {}
    originals = _patch_status_persistence(captured)

    try:
        services._persist_user_pipeline_status_snapshot(
            owner_user_id="user_status",
            status_payload={
                "run_id": "run_healed",
                "status": "running",
                "started_at": "2026-05-22T06:50:00Z",
                "finished_at": "2026-05-22T06:54:21Z",
                "current_stage": "",
                "summary_message": "Completed: 14 final jobs",
                "return_code": 0,
                "completed_stages": ["startup", "filtering", "finalization"],
                "is_running": True,
            },
        )
    finally:
        _restore(originals)

    record = captured["upserts"][0]
    assert record["status"] == "succeeded"
    assert record["completed_at"] == "2026-05-22T06:54:21Z"
    assert record["status_json"]["status"] == "succeeded"
    assert record["status_json"]["is_running"] is False
    assert captured["released"][0]["run_id"] == "run_healed"


def test_status_polling_reconciles_terminal_runtime_status_file_over_running_snapshot():
    original_gate = services.user_pipeline_gate_payload
    services.user_pipeline_gate_payload = lambda owner_user_id: {"ok": True}

    with tempfile.TemporaryDirectory() as tmp_dir:
        status_path = Path(tmp_dir) / "live_pipeline_status.json"
        status_path.write_text(json.dumps(_terminal_status_payload("run_poll")), encoding="utf-8")

        try:
            payload = services.pipeline_status_payload(
                owner_user_id="user_status",
                state={
                    "status": "running",
                    "started_at": "2026-05-22T06:50:00Z",
                    "finished_at": "",
                    "return_code": None,
                    "status_path": str(status_path),
                    "run_id": "run_poll",
                    "output_dir": tmp_dir,
                    "config": {},
                },
            )
        finally:
            services.user_pipeline_gate_payload = original_gate

    pipeline = payload["pipeline"]
    assert pipeline["status"] == "succeeded"
    assert pipeline["return_code"] == 0
    assert pipeline["finished_at"] == "2026-05-22T06:54:21Z"
    assert pipeline["is_running"] is False


def test_latest_owner_status_heals_stale_running_row_from_terminal_status_json():
    captured = {}
    terminal_json = _terminal_status_payload("run_status_json")
    originals = {
        "get_latest_user_pipeline_run_postgres_payload": services.get_latest_user_pipeline_run_postgres_payload,
        "update_user_pipeline_run_status_postgres_payload": services.update_user_pipeline_run_status_postgres_payload,
        "get_user_pipeline_active_run_postgres_payload": services.get_user_pipeline_active_run_postgres_payload,
        "release_user_pipeline_active_run_postgres_payload": services.release_user_pipeline_active_run_postgres_payload,
        "_release_user_pipeline_redis_admission_lock_payload": services._release_user_pipeline_redis_admission_lock_payload,
        "_clear_owner_active_pipeline_state": services._clear_owner_active_pipeline_state,
        "user_pipeline_gate_payload": services.user_pipeline_gate_payload,
    }

    services.get_latest_user_pipeline_run_postgres_payload = lambda **kwargs: {
        "found": True,
        "run": {
            "run_id": "run_status_json",
            "owner_user_id": "user_status",
            "status": "running",
            "current_stage": "finalization",
            "stage_message": "Completed: 14 final jobs",
            "summary_message": "Completed: 14 final jobs",
            "return_code": None,
            "started_at": "2026-05-22T06:50:00Z",
            "completed_at": "",
            "status_json": terminal_json,
            "error": "",
        },
    }
    services.update_user_pipeline_run_status_postgres_payload = lambda **kwargs: captured.setdefault(
        "updated",
        dict(kwargs),
    )
    services.get_user_pipeline_active_run_postgres_payload = lambda **kwargs: {
        "found": True,
        "active_run": {"metadata_json": {}},
    }
    services.release_user_pipeline_active_run_postgres_payload = (
        lambda **kwargs: captured.setdefault("released", dict(kwargs))
    )
    services._release_user_pipeline_redis_admission_lock_payload = lambda payload: None
    services._clear_owner_active_pipeline_state = (
        lambda owner_user_id, run_id="": captured.setdefault(
            "cleared",
            {"owner_user_id": owner_user_id, "run_id": run_id},
        )
    )
    services.user_pipeline_gate_payload = lambda owner_user_id: {"ok": True}

    try:
        payload = services._latest_owner_pipeline_status_payload(owner_user_id="user_status")
    finally:
        _restore(originals)

    assert payload["status"] == "succeeded"
    assert payload["finished_at"] == "2026-05-22T06:54:21Z"
    assert captured["updated"]["status"] == "succeeded"
    assert captured["updated"]["completed_at"] == "2026-05-22T06:54:21Z"
    assert captured["updated"]["status_json"]["is_running"] is False
    assert captured["released"]["run_id"] == "run_status_json"


def test_latest_owner_status_exposes_run_scoped_output_status_and_log_paths():
    output_dir = "tmp/pipeline_runs/user_status/run_paths/application_planning"
    log_path = f"{output_dir}/live_pipeline_run.log"
    status_path = f"{output_dir}/live_pipeline_status.json"
    terminal_json = {
        **_terminal_status_payload("run_paths"),
        "output_dir": output_dir,
        "log_path": log_path,
        "status_path": status_path,
        "config": {
            "storage_mode": "run_scoped_scratch",
            "launch_config_path": f"{output_dir}/live_pipeline_launch_config.json",
            "job_corpus_path": f"{output_dir}/current_run_job_corpus.jsonl",
        },
    }
    originals = {
        "get_latest_user_pipeline_run_postgres_payload": services.get_latest_user_pipeline_run_postgres_payload,
        "update_user_pipeline_run_status_postgres_payload": services.update_user_pipeline_run_status_postgres_payload,
        "get_user_pipeline_active_run_postgres_payload": services.get_user_pipeline_active_run_postgres_payload,
        "release_user_pipeline_active_run_postgres_payload": services.release_user_pipeline_active_run_postgres_payload,
        "_release_user_pipeline_redis_admission_lock_payload": services._release_user_pipeline_redis_admission_lock_payload,
        "_clear_owner_active_pipeline_state": services._clear_owner_active_pipeline_state,
        "user_pipeline_gate_payload": services.user_pipeline_gate_payload,
    }

    services.get_latest_user_pipeline_run_postgres_payload = lambda **kwargs: {
        "found": True,
        "run": {
            "run_id": "run_paths",
            "owner_user_id": "user_status",
            "status": "succeeded",
            "current_stage": "",
            "stage_message": "Completed: 4 final jobs",
            "summary_message": "Completed: 4 final jobs",
            "return_code": 0,
            "started_at": "2026-07-02T08:35:16Z",
            "completed_at": "2026-07-02T08:36:16Z",
            "config_json": {
                "output_dir": output_dir,
                "log_path": log_path,
                "status_path": status_path,
                "config": {"storage_mode": "run_scoped_scratch"},
            },
            "status_json": terminal_json,
            "error": "",
        },
    }
    services.update_user_pipeline_run_status_postgres_payload = lambda **kwargs: {}
    services.get_user_pipeline_active_run_postgres_payload = lambda **kwargs: {
        "found": False,
        "active_run": {},
    }
    services.release_user_pipeline_active_run_postgres_payload = lambda **kwargs: {}
    services._release_user_pipeline_redis_admission_lock_payload = lambda payload: None
    services._clear_owner_active_pipeline_state = lambda owner_user_id, run_id="": None
    services.user_pipeline_gate_payload = lambda owner_user_id: {"ok": True}

    try:
        payload = services._latest_owner_pipeline_status_payload(owner_user_id="user_status")
    finally:
        _restore(originals)

    assert payload["status"] == "succeeded"
    assert payload["output_dir"] == output_dir
    assert payload["log_path"] == log_path
    assert payload["status_path"] == status_path
    assert payload["status_json"]["config"]["storage_mode"] == "run_scoped_scratch"


def _interrupted_running_payload(run_id="run_interrupted"):
    return {
        "run_id": run_id,
        "child_pid": 424242,
        "status": "running",
        "started_at": "2026-07-18T10:00:00Z",
        "updated_at_utc": "2026-07-18T10:01:00Z",
        "current_stage": "resume_matching",
        "completed_stages": ["startup", "scraping", "filtering"],
        "stage_started_at": "2026-07-18T10:00:50Z",
        "stage_message": "Matching resumes",
        "counts": {"scraped_jobs": 32, "filtered_jobs": 11},
        "summary_message": "",
        "return_code": None,
        "error": "",
    }


def _seconds_ago(seconds):
    return (datetime.now(timezone.utc) - timedelta(seconds=seconds)).isoformat().replace("+00:00", "Z")


def test_live_child_pid_keeps_stale_persisted_run_running(monkeypatch):
    payload = _interrupted_running_payload("run_alive")
    payload["child_process_identity"] = "child-start"
    monkeypatch.setattr(services, "_pid_exists", lambda pid: int(pid) == 424242)
    monkeypatch.setattr(services, "_process_start_identity", lambda pid: "child-start")

    reconciled = services._heal_stale_running_runtime_status(
        {"process_is_running": False, "run_id": "run_alive"},
        payload,
    )

    assert reconciled == payload
    assert reconciled["status"] == "running"


def test_authoritative_worker_identity_alive_keeps_run_running(monkeypatch):
    payload = _interrupted_running_payload("run_worker_alive")
    payload.pop("child_pid")
    monkeypatch.setattr(services, "_pid_exists", lambda pid: int(pid) == 8181)
    monkeypatch.setattr(services, "_process_start_identity", lambda pid: "a1b2c3d4")

    reconciled = services._heal_stale_running_runtime_status(
        {
            "process_is_running": False,
            "run_id": payload["run_id"],
            "worker_id": "pid:8181;start:a1b2c3d4",
        },
        payload,
    )

    assert reconciled == payload
    assert reconciled["status"] == "running"


def test_dead_authoritative_worker_with_verified_live_child_keeps_run_running(monkeypatch):
    payload = _interrupted_running_payload("run_child_survived")
    payload["child_process_identity"] = "child-start"
    monkeypatch.setattr(services, "_pid_exists", lambda pid: int(pid) == 424242)
    monkeypatch.setattr(services, "_process_start_identity", lambda pid: "child-start")

    reconciled = services._heal_stale_running_runtime_status(
        {
            "process_is_running": False,
            "run_id": payload["run_id"],
            "worker_id": "pid:8181;start:a1b2c3d4",
        },
        payload,
    )

    assert reconciled == payload
    assert reconciled["status"] == "running"


def test_dead_stale_child_reconciles_without_losing_run_progress(monkeypatch, tmp_path):
    status_path = tmp_path / "live_pipeline_status.json"
    payload = _interrupted_running_payload()
    payload["status_path"] = str(status_path)
    status_path.write_text(json.dumps(payload), encoding="utf-8")
    monkeypatch.setattr(services, "_pid_exists", lambda pid: False)

    reconciled = services._heal_stale_running_runtime_status(
        {
            "process_is_running": False,
            "run_id": payload["run_id"],
            "status_path": str(status_path),
        },
        payload,
    )

    assert reconciled["status"] == "failed"
    assert reconciled["is_running"] is False
    assert reconciled["run_id"] == "run_interrupted"
    assert reconciled["current_stage"] == "resume_matching"
    assert reconciled["completed_stages"] == ["startup", "scraping", "filtering"]
    assert reconciled["counts"] == {"scraped_jobs": 32, "filtered_jobs": 11}
    assert reconciled["started_at"] == "2026-07-18T10:00:00Z"
    assert reconciled["error"] == (
        "Pipeline run was interrupted because its owning process stopped before completion."
    )
    assert json.loads(status_path.read_text(encoding="utf-8"))["status"] == "failed"
    assert services._heal_stale_running_runtime_status({}, reconciled) == reconciled


def test_uncertain_fresh_liveness_is_not_falsely_terminal(monkeypatch):
    payload = _interrupted_running_payload("run_uncertain")
    payload.pop("child_pid")
    payload["updated_at_utc"] = services._utc_now()
    monkeypatch.setattr(services, "_pid_exists", lambda pid: False)

    reconciled = services._heal_stale_running_runtime_status(
        {"process_is_running": False, "run_id": "run_uncertain", "worker_id": "pid:8181"},
        payload,
    )

    assert reconciled["status"] == "running"
    assert "finished_at" not in reconciled


def test_dead_authoritative_worker_with_missing_child_uses_short_grace(monkeypatch):
    payload = _interrupted_running_payload("run_dead_worker_missing_child")
    payload.pop("child_pid")
    payload["current_stage"] = "scraping"
    payload["stage_message"] = "Collecting jobs"
    payload["updated_at_utc"] = _seconds_ago(31)
    monkeypatch.setattr(services, "_pid_exists", lambda pid: False)

    reconciled = services._heal_stale_running_runtime_status(
        {
            "process_is_running": False,
            "run_id": payload["run_id"],
            "worker_id": "pid:26860",
        },
        payload,
    )

    assert reconciled["status"] == "failed"
    assert reconciled["run_id"] == payload["run_id"]
    assert reconciled["current_stage"] == "scraping"
    assert reconciled["completed_stages"] == payload["completed_stages"]
    assert reconciled["counts"] == payload["counts"]
    assert reconciled["started_at"] == payload["started_at"]
    assert reconciled["updated_at_utc"] == payload["updated_at_utc"]
    assert reconciled["error"] == (
        "Pipeline run was interrupted because its owning process stopped before completion."
    )
    evidence = reconciled["interruption_reconciliation"]
    assert evidence["liveness_evidence"] == "worker_pid_not_running:26860;child_pid_missing"
    assert evidence["last_update_age_seconds"] < 60


def test_dead_authoritative_worker_with_dead_child_uses_short_grace(monkeypatch):
    payload = _interrupted_running_payload("run_dead_worker_dead_child")
    payload["updated_at_utc"] = _seconds_ago(31)
    payload["child_process_identity"] = "dead-child-start"
    monkeypatch.setattr(services, "_pid_exists", lambda pid: False)

    reconciled = services._heal_stale_running_runtime_status(
        {
            "process_is_running": False,
            "run_id": payload["run_id"],
            "worker_id": "pid:26860;start:a1b2c3d4",
        },
        payload,
    )

    assert reconciled["status"] == "failed"
    assert reconciled["interruption_reconciliation"]["last_update_age_seconds"] < 60
    assert "child_pid_not_running:424242" in reconciled["interruption_reconciliation"]["liveness_evidence"]


def test_dead_authoritative_worker_with_malformed_child_uses_short_grace(monkeypatch):
    payload = _interrupted_running_payload("run_dead_worker_malformed_child")
    payload["child_pid"] = "not-a-pid"
    payload["updated_at_utc"] = _seconds_ago(31)
    monkeypatch.setattr(services, "_pid_exists", lambda pid: False)

    reconciled = services._heal_stale_running_runtime_status(
        {"run_id": payload["run_id"], "worker_id": "pid:26860"},
        payload,
    )

    assert reconciled["status"] == "failed"
    assert reconciled["interruption_reconciliation"]["liveness_evidence"] == (
        "worker_pid_not_running:26860;child_pid_malformed"
    )


def test_fresh_dead_authoritative_worker_is_protected_by_short_grace(monkeypatch):
    payload = _interrupted_running_payload("run_dead_worker_fresh")
    payload.pop("child_pid")
    payload["updated_at_utc"] = _seconds_ago(10)
    monkeypatch.setattr(services, "_pid_exists", lambda pid: False)

    reconciled = services._heal_stale_running_runtime_status(
        {"run_id": payload["run_id"], "worker_id": "pid:26860"},
        payload,
    )

    assert reconciled == payload
    assert reconciled["status"] == "running"


def test_legacy_run_without_owner_evidence_retains_long_uncertainty_policy(monkeypatch):
    payload = _interrupted_running_payload("run_legacy_uncertain")
    payload.pop("child_pid")
    payload["updated_at_utc"] = _seconds_ago(60)
    monkeypatch.setattr(services, "_pid_exists", lambda pid: False)

    reconciled = services._heal_stale_running_runtime_status(
        {"run_id": payload["run_id"]},
        payload,
    )

    assert reconciled == payload
    assert reconciled["status"] == "running"


def test_worker_pid_reuse_identity_mismatch_reconciles_after_short_grace(monkeypatch):
    payload = _interrupted_running_payload("run_worker_pid_reused")
    payload.pop("child_pid")
    payload["updated_at_utc"] = _seconds_ago(31)
    monkeypatch.setattr(services, "_pid_exists", lambda pid: True)
    monkeypatch.setattr(services, "_process_start_identity", lambda pid: "different1")

    reconciled = services._heal_stale_running_runtime_status(
        {
            "run_id": payload["run_id"],
            "worker_id": "pid:26860;start:a1b2c3d4",
        },
        payload,
    )

    assert reconciled["status"] == "failed"
    assert reconciled["interruption_reconciliation"]["liveness_evidence"] == (
        "worker_identity_mismatch:26860;child_pid_missing"
    )


def test_legacy_worker_pid_reuse_is_not_claimed_alive_or_dead(monkeypatch):
    payload = _interrupted_running_payload("run_worker_pid_unverified")
    payload.pop("child_pid")
    payload["updated_at_utc"] = _seconds_ago(60)
    monkeypatch.setattr(services, "_pid_exists", lambda pid: True)

    reconciled = services._heal_stale_running_runtime_status(
        {"run_id": payload["run_id"], "worker_id": "pid:26860"},
        payload,
    )

    assert reconciled == payload
    assert reconciled["status"] == "running"


def test_unchanged_deferred_reconciliation_is_logged_only_once(monkeypatch):
    payload = _interrupted_running_payload("run_deferred_log_throttle")
    payload.pop("child_pid")
    payload["updated_at_utc"] = _seconds_ago(10)
    info_logs = []
    warning_logs = []
    monkeypatch.setattr(services, "_pid_exists", lambda pid: False)
    monkeypatch.setattr(services.logger, "info", lambda *args, **kwargs: info_logs.append(args))
    monkeypatch.setattr(services.logger, "warning", lambda *args, **kwargs: warning_logs.append(args))

    snapshot = {"run_id": payload["run_id"], "worker_id": "pid:26860"}
    assert services._heal_stale_running_runtime_status(snapshot, payload) == payload
    assert services._heal_stale_running_runtime_status(snapshot, payload) == payload

    assert len(info_logs) == 1
    assert len(warning_logs) == 1
    assert "deferred" in warning_logs[0][0]


def test_changed_liveness_evidence_is_logged_again(monkeypatch):
    payload = _interrupted_running_payload("run_evidence_changed")
    payload.pop("child_pid")
    payload["updated_at_utc"] = _seconds_ago(10)
    pid_exists = {26860: False}
    info_logs = []
    warning_logs = []
    monkeypatch.setattr(services, "_pid_exists", lambda pid: pid_exists.get(int(pid), False))
    monkeypatch.setattr(services.logger, "info", lambda *args, **kwargs: info_logs.append(args))
    monkeypatch.setattr(services.logger, "warning", lambda *args, **kwargs: warning_logs.append(args))

    snapshot = {"run_id": payload["run_id"], "worker_id": "pid:26860"}
    services._heal_stale_running_runtime_status(snapshot, payload)
    pid_exists[26860] = True
    services._heal_stale_running_runtime_status(snapshot, payload)
    services._heal_stale_running_runtime_status(snapshot, payload)

    assert len(info_logs) == 2
    assert len(warning_logs) == 2


def test_terminal_reconciliation_logs_and_writes_only_once(monkeypatch, tmp_path):
    payload = _interrupted_running_payload("run_terminal_log_once")
    payload.pop("child_pid")
    payload["updated_at_utc"] = _seconds_ago(31)
    status_path = tmp_path / "live_pipeline_status.json"
    writes = []
    warning_logs = []
    monkeypatch.setattr(services, "_pid_exists", lambda pid: False)
    monkeypatch.setattr(
        services,
        "_write_runtime_status_file",
        lambda path, value: writes.append((path, dict(value))),
    )
    monkeypatch.setattr(services.logger, "info", lambda *args, **kwargs: None)
    monkeypatch.setattr(services.logger, "warning", lambda *args, **kwargs: warning_logs.append(args))

    snapshot = {
        "run_id": payload["run_id"],
        "worker_id": "pid:26860",
        "status_path": str(status_path),
    }
    first = services._heal_stale_running_runtime_status(snapshot, payload)
    second = services._heal_stale_running_runtime_status(snapshot, payload)

    assert first == second
    assert first["status"] == "failed"
    assert len(writes) == 1
    assert len(warning_logs) == 1
    assert "completed" in warning_logs[0][0]


@pytest.mark.parametrize("terminal_status", ["succeeded", "failed"])
def test_interruption_reconciliation_never_modifies_terminal_run(terminal_status):
    payload = {
        **_interrupted_running_payload(f"run_{terminal_status}"),
        "status": terminal_status,
        "finished_at": "2026-07-18T10:03:00Z",
    }

    assert services._heal_stale_running_runtime_status({}, payload) == payload


def test_stale_db_run_reconciliation_releases_launch_and_is_idempotent(monkeypatch):
    captured = {"updates": [], "releases": [], "clears": []}
    payload = _interrupted_running_payload("run_db_interrupted")
    row = {
        "run_id": "run_db_interrupted",
        "owner_user_id": "owner-7",
        "status": "running",
        "started_at": payload["started_at"],
        "updated_at": payload["updated_at_utc"],
        "current_stage": payload["current_stage"],
        "status_json": payload,
        "config_json": {"child_pid": payload["child_pid"]},
    }
    monkeypatch.setattr(services, "_pid_exists", lambda pid: False)
    monkeypatch.setattr(
        services,
        "update_user_pipeline_run_status_postgres_payload",
        lambda **kwargs: captured["updates"].append(dict(kwargs)) or {"ok": True},
    )
    monkeypatch.setattr(
        services,
        "get_user_pipeline_active_run_postgres_payload",
        lambda **kwargs: {"found": True, "active_run": {"metadata_json": {}}},
    )
    monkeypatch.setattr(
        services,
        "release_user_pipeline_active_run_postgres_payload",
        lambda **kwargs: captured["releases"].append(dict(kwargs)) or {"ok": True},
    )
    monkeypatch.setattr(services, "_release_user_pipeline_redis_admission_lock_payload", lambda payload: {})
    monkeypatch.setattr(
        services,
        "_clear_owner_active_pipeline_state",
        lambda owner_user_id, run_id="": captured["clears"].append((owner_user_id, run_id)),
    )

    reconciled = services._reconciled_user_pipeline_run_record("owner-7", row)

    assert reconciled["status"] == "failed"
    assert reconciled["current_stage"] == "resume_matching"
    assert reconciled["status_json"]["counts"] == payload["counts"]
    assert captured["updates"][0]["run_id"] == "run_db_interrupted"
    assert captured["releases"][0]["terminal_status"] == "failed"
    assert captured["clears"] == [("owner-7", "run_db_interrupted")]

    terminal_row = {**reconciled, "status": "failed"}
    assert services._reconciled_user_pipeline_run_record("owner-7", terminal_row) == terminal_row
    assert len(captured["updates"]) == 1


def test_runtime_initialize_preserves_launcher_pid_and_writes_heartbeat(monkeypatch, tmp_path):
    status_path = tmp_path / "live_pipeline_status.json"
    status_path.write_text(
        json.dumps(
            {
                "child_pid": 7331,
                "child_process_identity": "child-process-start",
                "worker_id": "pid:8181;start:a1b2c3d4",
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(runtime_status.ENV_STATUS_PATH, str(status_path))
    monkeypatch.setenv(runtime_status.ENV_RUN_ID, "run_pid_preserved")

    runtime_status.initialize_run(
        output_dir=str(tmp_path),
        log_path=str(tmp_path / "run.log"),
        status_path=str(status_path),
        planning_only=False,
        job_limit=10,
        job_packet_limit=3,
        llm_actions=["APPLY"],
        generate_tailoring=False,
        generate_llm_tailoring=False,
        refresh_llm_tailoring=False,
        generate_llm_fallback=False,
        generate_llm_adjudication=False,
        delete_seen_data="no",
    )

    persisted = json.loads(status_path.read_text(encoding="utf-8"))
    assert persisted["child_pid"] == 7331
    assert persisted["child_process_identity"] == "child-process-start"
    assert persisted["worker_id"] == "pid:8181;start:a1b2c3d4"
    assert persisted["updated_at_utc"]


def test_server_shutdown_stops_owner_scoped_run_and_preserves_runtime_progress(monkeypatch, tmp_path):
    class FakeProcess:
        def __init__(self):
            self.terminated = False

        def poll(self):
            return None

        def terminate(self):
            self.terminated = True

        def wait(self, timeout=None):
            assert timeout == 5
            return -15

    status_path = tmp_path / "live_pipeline_status.json"
    runtime_payload = _interrupted_running_payload("run_shutdown")
    status_path.write_text(json.dumps(runtime_payload), encoding="utf-8")
    process = FakeProcess()
    owner_state = {
        "run_id": "run_shutdown",
        "status": "running",
        "process": process,
        "child_pid": runtime_payload["child_pid"],
        "status_path": str(status_path),
        "log_handle": None,
    }
    monkeypatch.setattr(services, "_PIPELINE_ACTIVE_RUNS", {"owner-shutdown": owner_state})
    monkeypatch.setattr(
        services,
        "_PIPELINE_RUN_STATE",
        {"status": "idle", "process": None, "log_handle": None},
    )

    result = services.stop_live_pipeline_for_server_shutdown()

    persisted = json.loads(status_path.read_text(encoding="utf-8"))
    assert result["stopped"] is True
    assert result["stopped_count"] == 1
    assert process.terminated is True
    assert owner_state["status"] == "failed"
    assert owner_state["process"] is None
    assert persisted["status"] == "failed"
    assert persisted["run_id"] == "run_shutdown"
    assert persisted["current_stage"] == runtime_payload["current_stage"]
    assert persisted["completed_stages"] == runtime_payload["completed_stages"]
    assert persisted["counts"] == runtime_payload["counts"]
    assert persisted["error"] == "Pipeline run was interrupted before completion."
