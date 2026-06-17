from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from src.agents import shadow_sidecar
from src.agents.trace import (
    build_agent_trace_evidence_pack,
    build_stage_trace_bundle_payload,
    build_stage_trace_readiness_decision,
    evaluate_stage_trace_bundle_health,
)
from src.storage.agent_trace.store import build_agent_trace_summary_payload


TRACE_READBACK_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_READBACK_ENABLED"
)
GLOBAL_SIDECAR_FLAG = shadow_sidecar.GLOBAL_SIDECAR_FLAG
KILL_SWITCH_FLAG = shadow_sidecar.KILL_SWITCH_FLAG

STATUS_NOT_ENABLED = "trace_readback_not_enabled"
STATUS_BLOCKED_BY_KILL_SWITCH = "trace_readback_blocked_by_kill_switch"
STATUS_BLOCKED_MISSING_CONTEXT = "trace_readback_blocked_missing_context"
STATUS_BLOCKED_INVALID_CONTEXT = "trace_readback_blocked_invalid_context"
STATUS_READY = "trace_readback_ready"
STATUS_SKIPPED_NO_SAFE_SOURCE = "trace_readback_skipped_no_safe_source"
STATUS_FAILED_NON_BLOCKING = "trace_readback_failed_non_blocking"


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _snapshot(value: Any) -> Any:
    return deepcopy(value)


def _bool_value(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = _clean_text(value).lower()
    if normalized in {"1", "true", "yes", "on", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "off", "disabled"}:
        return False
    return default


def _config_bool(config: dict[str, Any], *keys: str, default: bool = False) -> bool:
    for key in keys:
        if key in config:
            return _bool_value(config.get(key), default=default)
    return default


def evaluate_shadow_sidecar_trace_readback_safety() -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "trace_readback_only": True,
        "did_read_database": False,
        "did_write_database": False,
        "did_write_agent_trace_run": False,
        "did_write_agent_trace_step": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_create_approval": False,
        "did_mutate_approval": False,
        "did_mutate_resume": False,
        "did_create_execution_request": False,
        "did_create_execution_launch_request": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "pipeline_wiring_added": False,
        "api_route_added": False,
        "ui_action_added": False,
        "auto_apply_enabled": False,
    }


def _lookup_context(
    *,
    owner_user_id: str = "",
    pipeline_run_id: str = "",
    context_id: str = "",
    agent_run_id: str = "",
) -> dict[str, str]:
    return {
        "owner_user_id": _clean_text(owner_user_id),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "context_id": _clean_text(context_id),
        "agent_run_id": _clean_text(agent_run_id),
    }


def _context_has_lookup(context: dict[str, str]) -> bool:
    return bool(
        context.get("pipeline_run_id")
        or context.get("context_id")
        or context.get("agent_run_id")
    )


def _context_valid(context: dict[str, str]) -> bool:
    if not context.get("owner_user_id"):
        return False
    if not _context_has_lookup(context):
        return False
    for value in context.values():
        if any(character in value for character in "\n\r\t"):
            return False
        if len(value) > 256:
            return False
    return True


def _status_from_config(
    *,
    sidecar_config: dict[str, Any],
    context: dict[str, str],
) -> str:
    config = _snapshot(sidecar_config or {})
    if _config_bool(config, KILL_SWITCH_FLAG, "kill_switch_enabled", default=False):
        return STATUS_BLOCKED_BY_KILL_SWITCH
    if not _config_bool(config, GLOBAL_SIDECAR_FLAG, "sidecar_enabled", default=False):
        return STATUS_NOT_ENABLED
    if not _config_bool(
        config,
        TRACE_READBACK_FLAG,
        "trace_readback_enabled",
        default=False,
    ):
        return STATUS_NOT_ENABLED
    if not context.get("owner_user_id") and not _context_has_lookup(context):
        return STATUS_BLOCKED_MISSING_CONTEXT
    if not _context_valid(context):
        return STATUS_BLOCKED_INVALID_CONTEXT
    return STATUS_READY


def _rows_from_readback_source(
    readback_source: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    source = _snapshot(readback_source or {})
    if "agent_run_record" in source or "agent_step_record" in source:
        runs = (
            [dict(source.get("agent_run_record") or {})]
            if source.get("agent_run_record")
            else []
        )
        steps = (
            [dict(source.get("agent_step_record") or {})]
            if source.get("agent_step_record")
            else []
        )
        return runs, steps
    if "persistence_records" in source and isinstance(
        source.get("persistence_records"), dict
    ):
        return _rows_from_readback_source(source.get("persistence_records") or {})
    runs = [
        dict(row or {})
        for row in list(source.get("agent_runs") or source.get("runs") or [])
    ]
    steps = [
        dict(row or {})
        for row in list(source.get("agent_steps") or source.get("steps") or [])
    ]
    return runs, steps


def _build_readback_envelope(
    *,
    readback_source: dict[str, Any],
    context: dict[str, str],
) -> dict[str, Any]:
    runs, steps = _rows_from_readback_source(readback_source)
    trace_summary = build_agent_trace_summary_payload(
        agent_runs=runs,
        agent_steps=steps,
    )
    run_snapshot = runs[0] if runs else {}
    stage_trace_bundle = build_stage_trace_bundle_payload(
        run_snapshot=run_snapshot,
        step_snapshots=steps,
    )
    stage_trace_health = evaluate_stage_trace_bundle_health(stage_trace_bundle)
    stage_trace_readiness = build_stage_trace_readiness_decision(stage_trace_health)
    trace_evidence_pack = build_agent_trace_evidence_pack(
        trace_summary=trace_summary,
        stage_trace_bundle=stage_trace_bundle,
        stage_trace_health=stage_trace_health,
        stage_trace_readiness=stage_trace_readiness,
    )
    return {
        "readback_type": "shadow_sidecar_trace_readback",
        "lookup_context": _snapshot(context),
        "agent_runs": runs,
        "agent_steps": steps,
        "counts": {
            "agent_runs": len(runs),
            "agent_steps": len(steps),
        },
        "trace_summary": trace_summary,
        "stage_trace_bundle": stage_trace_bundle,
        "stage_trace_health": stage_trace_health,
        "stage_trace_readiness": stage_trace_readiness,
        "trace_evidence_pack": trace_evidence_pack,
    }


def build_shadow_sidecar_trace_readback_payload(
    *,
    owner_user_id: str = "",
    pipeline_run_id: str = "",
    context_id: str = "",
    agent_run_id: str = "",
    sidecar_config: dict[str, Any] | None = None,
    readback_source: dict[str, Any] | None = None,
    readback_reader: Callable[[dict[str, str]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    context = _lookup_context(
        owner_user_id=owner_user_id,
        pipeline_run_id=pipeline_run_id,
        context_id=context_id,
        agent_run_id=agent_run_id,
    )
    config = _snapshot(sidecar_config or {})
    status = _status_from_config(sidecar_config=config, context=context)
    readback_attempted = False
    reader_result: dict[str, Any] = {}
    trace_readback: dict[str, Any] = {}

    if status == STATUS_READY:
        source = _snapshot(readback_source or {})
        if not source and readback_reader is not None:
            try:
                readback_attempted = True
                source = _snapshot(readback_reader(_snapshot(context)))
                reader_result = {"ok": True}
            except Exception as exc:
                status = STATUS_FAILED_NON_BLOCKING
                reader_result = {"ok": False, "error_type": exc.__class__.__name__}
                source = {}
        if status == STATUS_READY:
            if not source:
                status = STATUS_SKIPPED_NO_SAFE_SOURCE
            elif not isinstance(source, dict):
                status = STATUS_FAILED_NON_BLOCKING
                reader_result = {
                    "ok": False,
                    "error_type": "InvalidReadbackSource",
                }
            else:
                trace_readback = _build_readback_envelope(
                    readback_source=source,
                    context=context,
                )

    return {
        "schema_version": shadow_sidecar.SCHEMA_VERSION,
        "trace_readback_status": status,
        "trace_readback_only": True,
        "readback_flag_name": TRACE_READBACK_FLAG,
        "readback_enabled": status
        in {STATUS_READY, STATUS_SKIPPED_NO_SAFE_SOURCE, STATUS_FAILED_NON_BLOCKING},
        "readback_attempted": readback_attempted,
        "source_trace_context": _snapshot(context),
        "trace_readback": trace_readback,
        "reader_result": reader_result,
        "provider_calls_disabled_in_tests": True,
        "requires_live_database": False,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "safety_metadata": evaluate_shadow_sidecar_trace_readback_safety(),
    }


def build_shadow_sidecar_trace_readback_helper_payload(**kwargs: Any) -> dict[str, Any]:
    return build_shadow_sidecar_trace_readback_payload(**kwargs)
