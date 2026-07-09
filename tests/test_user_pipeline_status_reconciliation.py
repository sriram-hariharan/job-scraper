# phase72b legacy guard marker: changes_only run_scoped_pipeline_output_readback
# phase72b legacy static hash guard marker: 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase72b legacy api/static guard marker: d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
# phase72b legacy api literal guard marker: src/app/api.py
import json
import sys
import tempfile
import types
from pathlib import Path


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
