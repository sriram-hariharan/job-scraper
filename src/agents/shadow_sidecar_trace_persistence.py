from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from src.agents import shadow_sidecar
from src.storage.agent_trace.store import build_agent_trace_summary_payload


TRACE_PERSISTENCE_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_PERSISTENCE_ENABLED"
)
GLOBAL_SIDECAR_FLAG = shadow_sidecar.GLOBAL_SIDECAR_FLAG
KILL_SWITCH_FLAG = shadow_sidecar.KILL_SWITCH_FLAG

STATUS_NOT_ENABLED = "trace_persistence_not_enabled"
STATUS_BLOCKED_BY_KILL_SWITCH = "trace_persistence_blocked_by_kill_switch"
STATUS_BLOCKED_MISSING_TRACE = "trace_persistence_blocked_missing_trace"
STATUS_BLOCKED_INVALID_TRACE = "trace_persistence_blocked_invalid_trace"
STATUS_READY = "trace_persistence_ready"
STATUS_SKIPPED_NO_SAFE_SINK = "trace_persistence_skipped_no_safe_sink"
STATUS_FAILED_NON_BLOCKING = "trace_persistence_failed_non_blocking"


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


def evaluate_shadow_sidecar_trace_persistence_safety(
    *, called_by_hook: bool = False
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "trace_persistence_only": True,
        "trace_persistence_called_by_hook": bool(called_by_hook),
        "pipeline_hook_called_by_pipeline": False,
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


def _trace_capture_valid(trace_capture_payload: dict[str, Any]) -> bool:
    if not isinstance(trace_capture_payload, dict):
        return False
    if trace_capture_payload.get("trace_capture_only") is not True:
        return False
    if not _clean_text(trace_capture_payload.get("trace_capture_status")):
        return False
    if not _clean_text(trace_capture_payload.get("hook_status")):
        return False
    return True


def _status_from_config(
    *,
    trace_capture_payload: dict[str, Any] | None,
    sidecar_config: dict[str, Any],
) -> str:
    config = deepcopy(sidecar_config or {})
    if _config_bool(config, KILL_SWITCH_FLAG, "kill_switch_enabled", default=False):
        return STATUS_BLOCKED_BY_KILL_SWITCH
    if not _config_bool(config, GLOBAL_SIDECAR_FLAG, "sidecar_enabled", default=False):
        return STATUS_NOT_ENABLED
    if not _config_bool(
        config,
        TRACE_PERSISTENCE_FLAG,
        "trace_persistence_enabled",
        default=False,
    ):
        return STATUS_NOT_ENABLED
    if trace_capture_payload is None:
        return STATUS_BLOCKED_MISSING_TRACE
    if not _trace_capture_valid(trace_capture_payload):
        return STATUS_BLOCKED_INVALID_TRACE
    return STATUS_READY


def build_shadow_sidecar_trace_persistence_records(
    *,
    trace_capture_payload: dict[str, Any],
    owner_user_id: str = "shadow_sidecar",
    pipeline_run_id: str = "",
    context_id: str = "",
    called_by_hook: bool = False,
) -> dict[str, Any]:
    trace_capture = _snapshot(trace_capture_payload)
    trace_status = _clean_text(trace_capture.get("trace_capture_status"))
    hook_status = _clean_text(trace_capture.get("hook_status"))
    pipeline_id = _clean_text(pipeline_run_id) or _clean_text(
        trace_capture.get("source_deterministic_stage")
    )
    context = _clean_text(context_id) or _clean_text(
        trace_capture.get("source_deterministic_decision")
    )
    owner = _clean_text(owner_user_id) or "shadow_sidecar"
    run_id = "shadow_sidecar_trace_persistence"
    step_id = "shadow_sidecar_trace_persistence_step"
    run_record = {
        "agent_run_id": run_id,
        "owner_user_id": owner,
        "pipeline_run_id": pipeline_id,
        "context_id": context,
        "status": "ready",
        "started_at": "in_memory",
        "completed_at": "in_memory",
        "summary_json": {
            "trace_persistence_status": STATUS_READY,
            "trace_capture_status": trace_status,
            "hook_status": hook_status,
            "source_deterministic_stage": _clean_text(
                trace_capture.get("source_deterministic_stage")
            ),
            "source_deterministic_decision": _clean_text(
                trace_capture.get("source_deterministic_decision")
            ),
        },
        "error": "",
    }
    step_record = {
        "agent_step_id": step_id,
        "agent_run_id": run_id,
        "owner_user_id": owner,
        "pipeline_run_id": pipeline_id,
        "context_id": context,
        "agent_name": "Shadow Sidecar Trace Persistence",
        "agent_version": shadow_sidecar.SCHEMA_VERSION,
        "input_json": {
            "trace_capture_status": trace_status,
            "hook_status": hook_status,
        },
        "output_json": {
            "trace_capture": trace_capture,
            "trace_bundle": _snapshot(trace_capture.get("trace_bundle") or {}),
            "evidence_pack": _snapshot(trace_capture.get("evidence_pack") or {}),
        },
        "validation_json": {
            "trace_capture_valid": True,
            "persistence_flag_required": TRACE_PERSISTENCE_FLAG,
        },
        "status": "ready",
        "started_at": "in_memory",
        "completed_at": "in_memory",
        "latency_ms": 0,
        "model_provider": "",
        "model_name": "",
        "token_usage_json": {},
        "cost_json": {},
        "error": "",
    }
    trace_summary = build_agent_trace_summary_payload(
        agent_runs=[run_record],
        agent_steps=[step_record],
    )
    return {
        "record_type": "shadow_sidecar_trace_persistence_records",
        "agent_run_record": run_record,
        "agent_step_record": step_record,
        "trace_summary": trace_summary,
        "safety_metadata": evaluate_shadow_sidecar_trace_persistence_safety(
            called_by_hook=called_by_hook
        ),
    }


def build_shadow_sidecar_trace_persistence_payload(
    *,
    trace_capture_payload: dict[str, Any] | None = None,
    sidecar_config: dict[str, Any] | None = None,
    owner_user_id: str = "shadow_sidecar",
    pipeline_run_id: str = "",
    context_id: str = "",
    persistence_writer: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    called_by_hook: bool = False,
) -> dict[str, Any]:
    trace_capture = (
        _snapshot(trace_capture_payload)
        if isinstance(trace_capture_payload, dict)
        else None
    )
    config = _snapshot(sidecar_config or {})
    status = _status_from_config(
        trace_capture_payload=trace_capture,
        sidecar_config=config,
    )
    records: dict[str, Any] = {}
    writer_result: dict[str, Any] = {}
    if status == STATUS_READY and trace_capture is not None:
        records = build_shadow_sidecar_trace_persistence_records(
            trace_capture_payload=trace_capture,
            owner_user_id=owner_user_id,
            pipeline_run_id=pipeline_run_id,
            context_id=context_id,
            called_by_hook=called_by_hook,
        )
        if persistence_writer is None:
            status = STATUS_SKIPPED_NO_SAFE_SINK
        else:
            try:
                writer_result = _snapshot(persistence_writer(_snapshot(records)))
            except Exception as exc:
                status = STATUS_FAILED_NON_BLOCKING
                writer_result = {"error_type": exc.__class__.__name__}

    return {
        "schema_version": shadow_sidecar.SCHEMA_VERSION,
        "trace_persistence_status": status,
        "trace_persistence_only": True,
        "persistence_flag_name": TRACE_PERSISTENCE_FLAG,
        "persistence_enabled": status
        in {STATUS_READY, STATUS_SKIPPED_NO_SAFE_SINK, STATUS_FAILED_NON_BLOCKING},
        "persistence_attempted": bool(persistence_writer is not None and records),
        "persistence_records": records,
        "writer_result": writer_result,
        "source_trace_context": {
            "trace_capture_status": _clean_text(
                (trace_capture or {}).get("trace_capture_status")
            ),
            "hook_status": _clean_text((trace_capture or {}).get("hook_status")),
            "source_deterministic_stage": _clean_text(
                (trace_capture or {}).get("source_deterministic_stage")
            ),
            "source_deterministic_decision": _clean_text(
                (trace_capture or {}).get("source_deterministic_decision")
            ),
        },
        "provider_calls_disabled_in_tests": True,
        "requires_live_database": False,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "safety_metadata": evaluate_shadow_sidecar_trace_persistence_safety(
            called_by_hook=called_by_hook
        ),
    }


def build_shadow_sidecar_trace_persistence_helper_payload(**kwargs: Any) -> dict[str, Any]:
    return build_shadow_sidecar_trace_persistence_payload(**kwargs)
