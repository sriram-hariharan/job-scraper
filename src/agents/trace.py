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
    build_agent_trace_summary_payload,
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

DEFAULT_STAGE_TRACE_ORDER: tuple[str, ...] = (
    "relevance_prefilter_trace_wrapper",
    "deduplication_trace_wrapper",
    "jd_intelligence_trace_wrapper",
    "final_application_scoring_trace_wrapper",
)


def trace_recorder_safety_flags() -> dict[str, bool]:
    return dict(TRACE_RECORDER_SAFETY_FLAGS)


def _snapshot(value: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _snapshots(values: list[dict[str, Any]] | tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    if not isinstance(values, (list, tuple)):
        raise TypeError("step_snapshots must be a list or tuple.")
    return [_snapshot(value) for value in values]


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _stage_name(step_snapshot: dict[str, Any]) -> str:
    return _clean_text(step_snapshot.get("step_name")) or _clean_text(
        step_snapshot.get("agent_name")
    )


def _stage_counts(stage_names: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for stage_name in stage_names:
        if not stage_name:
            continue
        counts[stage_name] = int(counts.get(stage_name, 0)) + 1
    return dict(sorted(counts.items()))


def _duplicate_stages(stage_names: list[str]) -> list[dict[str, Any]]:
    return [
        {"stage_name": stage_name, "count": count}
        for stage_name, count in _stage_counts(stage_names).items()
        if count > 1
    ]


def stage_trace_bundle_safety_metadata() -> dict[str, bool]:
    return {
        "did_read_database": False,
        "did_write_database": False,
        "did_create_agent_run": False,
        "did_create_agent_step": False,
        "did_update_agent_run": False,
        "did_update_agent_step": False,
        "did_prepare_statement": False,
        "did_call_live_stage": False,
        "did_call_prefilter_relevance": False,
        "did_call_deduplication": False,
        "did_call_jd_intelligence": False,
        "did_call_final_application_scoring": False,
        "did_call_llm": False,
        "did_change_pipeline": False,
        "did_change_scoring": False,
        "did_change_ranking": False,
        "did_change_approval": False,
        "did_execute_application": False,
        "did_submit_application": False,
    }


def build_stage_trace_bundle_payload(
    *,
    run_snapshot: dict[str, Any],
    step_snapshots: list[dict[str, Any]] | tuple[dict[str, Any], ...],
    expected_stage_order: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    run = _snapshot(run_snapshot)
    steps = _snapshots(step_snapshots)
    expected_order = [
        _clean_text(stage_name)
        for stage_name in (expected_stage_order or DEFAULT_STAGE_TRACE_ORDER)
        if _clean_text(stage_name)
    ]
    stage_names = [_stage_name(step) for step in steps]
    agent_names = [_clean_text(step.get("agent_name")) for step in steps]
    missing_expected_stages = [
        stage_name for stage_name in expected_order if stage_name not in stage_names
    ]
    unexpected_stages = [
        stage_name
        for stage_name in stage_names
        if stage_name and stage_name not in expected_order
    ]
    duplicate_stages = _duplicate_stages(stage_names)
    stage_order_validation = {
        "is_valid": (
            stage_names == expected_order
            and not missing_expected_stages
            and not unexpected_stages
            and not duplicate_stages
        ),
        "expected_stage_order": expected_order,
        "observed_stage_order": stage_names,
        "missing_expected_stages": missing_expected_stages,
        "unexpected_stages": unexpected_stages,
        "duplicate_stages": duplicate_stages,
    }
    return {
        "operation": "build_stage_trace_bundle_payload",
        "bundle_type": "stage_trace_bundle",
        "run_snapshot": run,
        "step_snapshots": steps,
        "step_count": len(steps),
        "agent_names": agent_names,
        "stage_names": stage_names,
        "stage_order_validation": stage_order_validation,
        "missing_expected_stages": missing_expected_stages,
        "unexpected_stages": unexpected_stages,
        "duplicate_stages": duplicate_stages,
        "trace_summary": build_agent_trace_summary_payload(
            agent_runs=[run],
            agent_steps=steps,
        ),
        "safety_metadata": stage_trace_bundle_safety_metadata(),
        **trace_recorder_safety_flags(),
    }


def evaluate_stage_trace_bundle_health(
    stage_trace_bundle: dict[str, Any],
) -> dict[str, Any]:
    bundle = _snapshot(stage_trace_bundle)
    validation = _snapshot(bundle.get("stage_order_validation"))
    trace_summary = _snapshot(bundle.get("trace_summary"))
    missing_expected_stages = [
        _clean_text(stage_name)
        for stage_name in bundle.get("missing_expected_stages", [])
        if _clean_text(stage_name)
    ] if isinstance(bundle.get("missing_expected_stages"), list) else []
    unexpected_stages = [
        _clean_text(stage_name)
        for stage_name in bundle.get("unexpected_stages", [])
        if _clean_text(stage_name)
    ] if isinstance(bundle.get("unexpected_stages"), list) else []
    duplicate_stages = deepcopy(bundle.get("duplicate_stages", [])) if isinstance(
        bundle.get("duplicate_stages"), list
    ) else []
    stage_order_valid = validation.get("is_valid") is True
    all_required_fields_present = trace_summary.get("all_required_fields_present") is True

    findings: list[str] = []
    warnings: list[str] = []
    if not stage_order_valid:
        findings.append("stage_order_invalid")
        warnings.append("stage_order_validation_failed")
    if missing_expected_stages:
        findings.append("missing_expected_stages")
        warnings.append("one_or_more_expected_stages_missing")
    if unexpected_stages:
        findings.append("unexpected_stages")
        warnings.append("one_or_more_unexpected_stages_present")
    if duplicate_stages:
        findings.append("duplicate_stages")
        warnings.append("one_or_more_stage_names_duplicated")
    if not all_required_fields_present:
        findings.append("required_trace_fields_missing")
        warnings.append("one_or_more_trace_rows_missing_required_fields")

    ok = not findings and not warnings
    return {
        "ok": ok,
        "health_status": "healthy" if ok else "warning",
        "findings": findings,
        "warnings": warnings,
        "stage_order_valid": stage_order_valid,
        "missing_expected_stages": missing_expected_stages,
        "unexpected_stages": unexpected_stages,
        "duplicate_stages": duplicate_stages,
        "all_required_fields_present": all_required_fields_present,
        "safety_metadata": stage_trace_bundle_safety_metadata(),
    }


def _clean_text_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_clean_text(item) for item in value if _clean_text(item)]


def build_stage_trace_readiness_decision(
    stage_trace_health: dict[str, Any],
) -> dict[str, Any]:
    health = _snapshot(stage_trace_health)
    findings = _clean_text_list(health.get("findings"))
    warnings = _clean_text_list(health.get("warnings"))
    missing_expected_stages = _clean_text_list(health.get("missing_expected_stages"))
    unexpected_stages = _clean_text_list(health.get("unexpected_stages"))
    duplicate_stages = deepcopy(health.get("duplicate_stages", [])) if isinstance(
        health.get("duplicate_stages"), list
    ) else []
    stage_order_valid = health.get("stage_order_valid") is True
    all_required_fields_present = health.get("all_required_fields_present") is True

    decision_reason_codes: list[str] = []
    blocking_findings: list[str] = []
    warning_findings: list[str] = []

    if not health:
        decision_reason_codes.append("stage_trace_health_missing")
        blocking_findings.append("stage_trace_health_missing")
    if not stage_order_valid:
        decision_reason_codes.append("stage_order_invalid")
        blocking_findings.append("stage_order_invalid")
    if not all_required_fields_present:
        decision_reason_codes.append("required_trace_fields_missing")
        blocking_findings.append("required_trace_fields_missing")
    if missing_expected_stages:
        decision_reason_codes.append("missing_expected_stages")
        blocking_findings.append("missing_expected_stages")
    if unexpected_stages:
        decision_reason_codes.append("unexpected_stages")
        blocking_findings.append("unexpected_stages")
    if duplicate_stages:
        decision_reason_codes.append("duplicate_stages")
        blocking_findings.append("duplicate_stages")

    for finding in findings + warnings:
        if finding and finding not in blocking_findings and finding not in warning_findings:
            warning_findings.append(finding)

    if blocking_findings:
        readiness_status = "blocked"
    elif warning_findings or health.get("ok") is not True:
        readiness_status = "warning"
        if not warning_findings:
            warning_findings.append("stage_trace_health_not_ok")
        if "stage_trace_health_warning" not in decision_reason_codes:
            decision_reason_codes.append("stage_trace_health_warning")
    else:
        readiness_status = "ready"

    return {
        "ok": readiness_status == "ready",
        "readiness_status": readiness_status,
        "decision_reason_codes": decision_reason_codes,
        "blocking_findings": blocking_findings,
        "warning_findings": warning_findings,
        "stage_order_valid": stage_order_valid,
        "all_required_fields_present": all_required_fields_present,
        "safety_metadata": stage_trace_bundle_safety_metadata(),
    }


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
