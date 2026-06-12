from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict

from src.agents.agent_state import (
    JobApplicationContext,
    build_agent_run_snapshot,
    build_agent_step_snapshot,
)
from src.storage.agent_state import store as agent_state_store
from src.storage.agent_trace.store import (
    complete_agent_run_postgres_payload,
    complete_agent_step_postgres_payload,
    create_agent_run_postgres_payload,
    fail_agent_run_postgres_payload,
    fail_agent_step_postgres_payload,
    get_agent_run_postgres_payload,
    list_agent_runs_postgres_payload,
    list_agent_steps_postgres_payload,
    record_agent_step_postgres_payload,
)


TRACE_RECORDER_SAFETY_FLAGS: dict[str, bool] = {
    "did_create_connection": False,
    "did_commit_transaction": False,
    "did_run_migration": False,
    "did_schedule_background_work": False,
    "did_execute_scheduler": False,
    "did_execute_reporting_job": False,
    "did_export_files": False,
    "did_execute_application": False,
    "did_submit_application": False,
    "api_route_added": False,
    "ui_action_added": False,
    "pipeline_wiring_added": False,
}


def trace_recorder_safety_flags() -> dict[str, bool]:
    return dict(TRACE_RECORDER_SAFETY_FLAGS)


def _snapshot(value: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _snapshots(values: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    if not isinstance(values, (list, tuple)):
        raise TypeError("step_snapshots must be a list or tuple.")
    return [_snapshot(value) for value in values]


def build_agent_run_record_payload(run_snapshot: dict[str, Any]) -> dict[str, Any]:
    snapshot = _snapshot(run_snapshot)
    prepared = agent_state_store.prepare_agent_run_upsert(snapshot)
    return {
        "operation": "record_agent_run_snapshot",
        "record_type": "agent_run",
        "table": "agent_runs",
        "prepared_statement": prepared,
        "snapshot": snapshot,
        **trace_recorder_safety_flags(),
    }


def build_agent_step_record_payload(step_snapshot: dict[str, Any]) -> dict[str, Any]:
    snapshot = _snapshot(step_snapshot)
    prepared = agent_state_store.prepare_agent_step_upsert(snapshot)
    return {
        "operation": "record_agent_step_snapshot",
        "record_type": "agent_step",
        "table": "agent_steps",
        "prepared_statement": prepared,
        "snapshot": snapshot,
        **trace_recorder_safety_flags(),
    }


def build_agent_trace_recording_payload(
    *,
    run_snapshot: dict[str, Any],
    step_snapshots: list[dict[str, Any]] | tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    run_record = build_agent_run_record_payload(run_snapshot)
    step_records = [
        build_agent_step_record_payload(step_snapshot)
        for step_snapshot in _snapshots(step_snapshots)
    ]
    operations = [run_record, *step_records]
    return {
        "operation": "build_agent_trace_recording_payload",
        "run_count": 1,
        "step_count": len(step_records),
        "record_count": len(operations),
        "records": operations,
        **trace_recorder_safety_flags(),
    }


def build_fake_smoke_trace_payload() -> dict[str, Any]:
    context = JobApplicationContext(
        approval_request_id="smoke_approval",
        job_id="smoke_job",
        candidate_key="smoke_candidate",
        role_family="smoke",
        run_mode="dry_run",
        observed_at_utc="2026-06-12T00:00:00Z",
        metadata={"source": "trace_recorder_smoke"},
    )
    run_snapshot = build_agent_run_snapshot(
        context=context,
        agent_name="smoke_agent",
        observed_at_utc="2026-06-12T00:01:00Z",
        run_status="ready",
        metadata={"trace": "smoke"},
    )
    step_snapshot = build_agent_step_snapshot(
        context=context,
        agent_name="smoke_agent",
        step_name="smoke_step",
        step_index=1,
        observed_at_utc="2026-06-12T00:02:00Z",
        step_status="ready",
        agent_run_id=run_snapshot["agent_run_id"],
        input_summary={"source": "smoke"},
        output_summary={"result": "not_executed"},
        reason_codes=["smoke_trace_only"],
        metadata={"trace": "smoke"},
    )
    return build_agent_trace_recording_payload(
        run_snapshot=run_snapshot,
        step_snapshots=[step_snapshot],
    )


def execute_agent_trace_recording(
    trace_payload: dict[str, Any],
    *,
    cursor: Any | None = None,
    execute_callback: Any | None = None,
) -> dict[str, Any]:
    if (cursor is None) == (execute_callback is None):
        raise ValueError("Provide exactly one injected cursor or execute_callback.")
    payload = _snapshot(trace_payload)
    records = payload.get("records")
    if not isinstance(records, list):
        raise ValueError("trace_payload records must be a list.")

    executed_operations: list[dict[str, Any]] = []
    for record in records:
        prepared = _snapshot(record).get("prepared_statement")
        if not isinstance(prepared, dict):
            raise ValueError("Each trace record must include a prepared_statement.")
        operation = {
            "record_type": _snapshot(record).get("record_type", ""),
            "table": prepared.get("table", ""),
            "sql": prepared.get("sql", ""),
            "params": tuple(prepared.get("params", ())),
        }
        if cursor is not None:
            cursor.execute(operation["sql"], operation["params"])
        else:
            execute_callback(deepcopy(operation))
        executed_operations.append(
            {
                "record_type": operation["record_type"],
                "table": operation["table"],
            }
        )

    return {
        "operation": "execute_agent_trace_recording",
        "executed_record_count": len(executed_operations),
        "executed_operations": executed_operations,
        **trace_recorder_safety_flags(),
    }


def create_agent_run(**kwargs: Any) -> Dict[str, Any]:
    return create_agent_run_postgres_payload(**kwargs)


def complete_agent_run(**kwargs: Any) -> Dict[str, Any]:
    return complete_agent_run_postgres_payload(**kwargs)


def fail_agent_run(**kwargs: Any) -> Dict[str, Any]:
    return fail_agent_run_postgres_payload(**kwargs)


def record_agent_step(**kwargs: Any) -> Dict[str, Any]:
    return record_agent_step_postgres_payload(**kwargs)


def complete_agent_step(**kwargs: Any) -> Dict[str, Any]:
    return complete_agent_step_postgres_payload(**kwargs)


def fail_agent_step(**kwargs: Any) -> Dict[str, Any]:
    return fail_agent_step_postgres_payload(**kwargs)


def get_agent_run(**kwargs: Any) -> Dict[str, Any]:
    return get_agent_run_postgres_payload(**kwargs)


def list_agent_runs(**kwargs: Any) -> Dict[str, Any]:
    return list_agent_runs_postgres_payload(**kwargs)


def list_agent_steps(**kwargs: Any) -> Dict[str, Any]:
    return list_agent_steps_postgres_payload(**kwargs)
