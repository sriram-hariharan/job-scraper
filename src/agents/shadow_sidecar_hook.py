from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents import shadow_sidecar
from src.storage.agent_trace.store import build_agent_trace_summary_payload


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _snapshot(value: Any) -> Any:
    return deepcopy(value)


def evaluate_shadow_sidecar_pipeline_hook_safety(
    *, called_by_pipeline: bool = False
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "pipeline_hook_available": True,
        "pipeline_hook_called_by_pipeline": bool(called_by_pipeline),
        "manual_review_required": True,
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
        "auto_apply_enabled": False,
    }


def evaluate_shadow_sidecar_hook_trace_capture_safety(
    *, called_by_pipeline: bool = False
) -> dict[str, bool]:
    safety = evaluate_shadow_sidecar_pipeline_hook_safety(
        called_by_pipeline=called_by_pipeline
    )
    safety["trace_capture_only"] = True
    safety["did_read_database"] = False
    safety["did_write_database"] = False
    safety["did_write_agent_trace_run"] = False
    safety["did_write_agent_trace_step"] = False
    safety["did_update_agent_trace_run"] = False
    safety["did_update_agent_trace_step"] = False
    return safety


def _hook_status_from_chain(chain_payload: dict[str, Any]) -> str:
    chain_status = _clean_text(
        chain_payload.get("chain_status") or chain_payload.get("sidecar_chain_status")
    )
    if chain_status == shadow_sidecar.CHAIN_STATUS_COMPLETED_SHADOW_CHAIN:
        return "hook_completed_shadow_sidecar"
    if chain_status == shadow_sidecar.STATUS_FAILED_NON_BLOCKING:
        return "hook_failed_non_blocking"
    return "hook_completed_with_fallback"


def _trace_capture_status(hook_status: str) -> str:
    status = _clean_text(hook_status)
    if status == "hook_not_enabled":
        return "trace_capture_not_enabled"
    if status in {
        "hook_blocked_by_kill_switch",
        "hook_blocked_missing_context",
        "hook_blocked_unsupported_stage",
        "hook_skipped_no_enabled_agents",
    }:
        return "trace_capture_skipped"
    if status == "hook_failed_non_blocking":
        return "trace_capture_failed_non_blocking"
    return "trace_capture_captured"


def build_shadow_sidecar_hook_trace_capture_payload(
    hook_payload: dict[str, Any],
) -> dict[str, Any]:
    """Build a deterministic in-memory trace capture for a sidecar hook payload."""

    hook = deepcopy(hook_payload or {})
    chain = deepcopy(hook.get("chain_payload")) if isinstance(hook.get("chain_payload"), dict) else {}
    observability = (
        deepcopy(hook.get("observability_payload"))
        if isinstance(hook.get("observability_payload"), dict)
        else {}
    )
    safety = hook.get("safety_metadata") if isinstance(hook.get("safety_metadata"), dict) else {}
    called_by_pipeline = bool(safety.get("pipeline_hook_called_by_pipeline"))
    hook_status = _clean_text(hook.get("hook_status"))
    trace_status = _trace_capture_status(hook_status)
    chain_summary = {
        "chain_status": _clean_text(
            chain.get("chain_status") or chain.get("sidecar_chain_status")
        ),
        "stage_order": list(chain.get("stage_order") or []),
        "stage_statuses": deepcopy(chain.get("stage_statuses") or {}),
        "fallback_used": bool(chain.get("fallback_used")),
        "readiness_status": _clean_text(
            (chain.get("readiness_decision") or {}).get("readiness_status")
            if isinstance(chain.get("readiness_decision"), dict)
            else ""
        )
        or _clean_text(
            (observability.get("readiness_decision") or {}).get("readiness_status")
            if isinstance(observability.get("readiness_decision"), dict)
            else ""
        ),
    }
    step_status = "completed"
    if trace_status in {"trace_capture_not_enabled", "trace_capture_skipped"}:
        step_status = "skipped"
    elif trace_status == "trace_capture_failed_non_blocking":
        step_status = "warning"

    trace_summary = build_agent_trace_summary_payload(
        agent_runs=[],
        agent_steps=[
            {
                "agent_step_id": "shadow_sidecar_hook_trace_capture",
                "agent_run_id": "shadow_sidecar_hook_trace_capture",
                "owner_user_id": "shadow_sidecar",
                "agent_name": "Shadow Sidecar Hook Trace Capture",
                "status": step_status,
                "started_at": "in_memory",
                "completed_at": "in_memory",
                "metadata_json": {
                    "trace_capture_status": trace_status,
                    "hook_status": hook_status,
                    "chain_attempted": bool(hook.get("chain_attempted")),
                },
                "safety_metadata_json": evaluate_shadow_sidecar_hook_trace_capture_safety(
                    called_by_pipeline=called_by_pipeline
                ),
            }
        ],
    )
    trace_bundle = deepcopy(chain.get("trace_bundle") or {})
    if not trace_bundle:
        trace_bundle = {
            "bundle_type": "shadow_sidecar_hook_trace_capture_bundle",
            "schema_version": shadow_sidecar.SCHEMA_VERSION,
            "hook_status": hook_status,
            "stage_name": _clean_text(hook.get("stage_name")),
            "source_deterministic_decision": _clean_text(
                hook.get("source_deterministic_decision")
            ),
        }
    evidence_pack = deepcopy(chain.get("evidence_pack") or {})
    if not evidence_pack:
        evidence_pack = {
            "evidence_pack_type": "shadow_sidecar_hook_trace_capture_evidence_pack",
            "schema_version": shadow_sidecar.SCHEMA_VERSION,
            "hook_status": hook_status,
            "source_deterministic_reason_codes": list(
                hook.get("source_deterministic_reason_codes") or []
            ),
            "fallback_used": trace_status != "trace_capture_captured",
        }

    return {
        "schema_version": shadow_sidecar.SCHEMA_VERSION,
        "trace_capture_status": trace_status,
        "trace_capture_only": True,
        "persistence_deferred": True,
        "persistence_deferred_reason": (
            "no_existing_safe_persistent_shadow_sidecar_trace_sink"
        ),
        "hook_status": hook_status,
        "hook_preview_status": _clean_text(hook.get("hook_preview_status")),
        "chain_attempted": bool(hook.get("chain_attempted")),
        "chain_summary": chain_summary,
        "source_deterministic_stage": _clean_text(
            hook.get("source_deterministic_stage")
        ),
        "source_deterministic_status": _clean_text(
            hook.get("source_deterministic_status")
        ),
        "source_deterministic_score": hook.get("source_deterministic_score"),
        "source_deterministic_decision": _clean_text(
            hook.get("source_deterministic_decision")
        ),
        "source_deterministic_reason_codes": list(
            hook.get("source_deterministic_reason_codes") or []
        ),
        "trace_bundle": trace_bundle,
        "evidence_pack": evidence_pack,
        "trace_summary": trace_summary,
        "provider_calls_disabled_in_tests": True,
        "safety_metadata": evaluate_shadow_sidecar_hook_trace_capture_safety(
            called_by_pipeline=called_by_pipeline
        ),
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
    }


def _safe_shadow_sidecar_hook_trace_capture_payload(
    hook_payload: dict[str, Any],
) -> dict[str, Any]:
    try:
        return build_shadow_sidecar_hook_trace_capture_payload(hook_payload)
    except Exception as exc:
        safety = hook_payload.get("safety_metadata") if isinstance(hook_payload, dict) else {}
        return {
            "schema_version": shadow_sidecar.SCHEMA_VERSION,
            "trace_capture_status": "trace_capture_failed_non_blocking",
            "trace_capture_only": True,
            "persistence_deferred": True,
            "persistence_deferred_reason": (
                "no_existing_safe_persistent_shadow_sidecar_trace_sink"
            ),
            "hook_status": _clean_text(
                hook_payload.get("hook_status") if isinstance(hook_payload, dict) else ""
            ),
            "chain_attempted": bool(
                hook_payload.get("chain_attempted") if isinstance(hook_payload, dict) else False
            ),
            "error_type": exc.__class__.__name__,
            "provider_calls_disabled_in_tests": True,
            "safety_metadata": evaluate_shadow_sidecar_hook_trace_capture_safety(
                called_by_pipeline=bool(safety.get("pipeline_hook_called_by_pipeline"))
            ),
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
        }


def _base_hook_payload(
    *,
    preview_payload: dict[str, Any],
    hook_status: str,
    chain_attempted: bool,
    called_by_pipeline: bool = False,
    chain_payload: dict[str, Any] | None = None,
    observability_payload: dict[str, Any] | None = None,
    next_safe_step: str = "",
) -> dict[str, Any]:
    preview = deepcopy(preview_payload or {})
    chain = deepcopy(chain_payload) if isinstance(chain_payload, dict) else {}
    observability = (
        deepcopy(observability_payload) if isinstance(observability_payload, dict) else {}
    )
    payload = {
        "schema_version": shadow_sidecar.SCHEMA_VERSION,
        "hook_status": _clean_text(hook_status) or "hook_failed_non_blocking",
        "hook_preview_status": _clean_text(preview.get("hook_preview_status")),
        "hook_called": True,
        "chain_attempted": bool(chain_attempted),
        "stage_name": _clean_text(preview.get("stage_name")),
        "supported_stage": bool(preview.get("supported_stage")),
        "enabled_agent_names": list(preview.get("enabled_agent_names") or []),
        "disabled_agent_names": list(preview.get("disabled_agent_names") or []),
        "source_deterministic_stage": _clean_text(
            preview.get("source_deterministic_stage")
        ),
        "source_deterministic_status": _clean_text(
            preview.get("source_deterministic_status")
        ),
        "source_deterministic_score": preview.get("source_deterministic_score"),
        "source_deterministic_decision": _clean_text(
            preview.get("source_deterministic_decision")
        ),
        "source_deterministic_reason_codes": list(
            preview.get("source_deterministic_reason_codes") or []
        ),
        "chain_payload": chain,
        "observability_payload": observability,
        "readiness_decision": deepcopy(
            observability.get("readiness_decision")
            or preview.get("readiness_decision")
            or {}
        ),
        "next_safe_step": _clean_text(next_safe_step)
        or _clean_text(preview.get("next_safe_step")),
        "provider_calls_disabled_in_tests": True,
        "safety_metadata": evaluate_shadow_sidecar_pipeline_hook_safety(
            called_by_pipeline=called_by_pipeline
        ),
        "default_off_pipeline_hook_call_sites": 1 if called_by_pipeline else 0,
        "live_production_pipeline_connected_agents": 0,
        "live_agents_allowed_to_automate_mutations": 0,
    }
    payload["trace_capture"] = _safe_shadow_sidecar_hook_trace_capture_payload(payload)
    return payload


def run_shadow_sidecar_pipeline_hook(
    *,
    run_id: str = "",
    batch_id: str = "",
    job_id: str = "",
    stage_name: str = "",
    source_deterministic_stage: str = "",
    source_deterministic_status: str = "",
    source_deterministic_score: Any = None,
    source_deterministic_decision: str = "",
    source_deterministic_reason_codes: list[str] | tuple[str, ...] | None = None,
    sidecar_config: dict[str, Any] | None = None,
    job_payload: dict[str, Any] | None = None,
    resume_profile_payload: dict[str, Any] | None = None,
    existing_trace_context: dict[str, Any] | None = None,
    called_by_pipeline: bool = False,
) -> dict[str, Any]:
    preview = shadow_sidecar.build_shadow_sidecar_pipeline_hook_preview_payload(
        run_id=run_id,
        batch_id=batch_id,
        job_id=job_id,
        stage_name=stage_name,
        source_deterministic_stage=source_deterministic_stage,
        source_deterministic_status=source_deterministic_status,
        source_deterministic_score=source_deterministic_score,
        source_deterministic_decision=source_deterministic_decision,
        source_deterministic_reason_codes=source_deterministic_reason_codes,
        sidecar_config=_snapshot(sidecar_config or {}),
        job_payload=_snapshot(job_payload or {}),
        resume_profile_payload=_snapshot(resume_profile_payload or {}),
        existing_trace_context=_snapshot(existing_trace_context or {}),
    )
    if preview.get("hook_preview_status") != "hook_ready_for_shadow_sidecar":
        return _base_hook_payload(
            preview_payload=preview,
            hook_status=_clean_text(preview.get("hook_preview_status")),
            chain_attempted=False,
            called_by_pipeline=called_by_pipeline,
            next_safe_step=_clean_text(preview.get("next_safe_step")),
        )

    try:
        sidecar_input = shadow_sidecar.build_shadow_sidecar_input_payload(
            run_id=run_id,
            batch_id=batch_id,
            job_id=job_id,
            stage_name=stage_name,
            source_deterministic_stage=source_deterministic_stage,
            source_deterministic_status=source_deterministic_status,
            source_deterministic_score=source_deterministic_score,
            source_deterministic_decision=source_deterministic_decision,
            source_deterministic_reason_codes=source_deterministic_reason_codes,
            job_payload=_snapshot(job_payload or {}),
            resume_profile_payload=_snapshot(resume_profile_payload or {}),
            existing_trace_context=_snapshot(existing_trace_context or {}),
            sidecar_config=_snapshot(sidecar_config or {}),
            agent_name="shadow_sidecar_chain",
        )
        chain_payload = shadow_sidecar.run_shadow_sidecar_chain(
            sidecar_input=sidecar_input
        )
        observability = shadow_sidecar.build_shadow_sidecar_chain_observability_payload(
            chain_payload
        )
        return _base_hook_payload(
            preview_payload=preview,
            hook_status=_hook_status_from_chain(chain_payload),
            chain_attempted=True,
            called_by_pipeline=called_by_pipeline,
            chain_payload=chain_payload,
            observability_payload=observability,
            next_safe_step="inspect_shadow_sidecar_observability",
        )
    except Exception as exc:
        return _base_hook_payload(
            preview_payload=preview,
            hook_status="hook_failed_non_blocking",
            chain_attempted=True,
            called_by_pipeline=called_by_pipeline,
            observability_payload={
                "observability_status": "observed_failed_non_blocking",
                "readiness_decision": {
                    "readiness_status": "blocked",
                    "decision_reason_codes": ["shadow_sidecar_hook_error"],
                    "blocking_findings": [exc.__class__.__name__],
                    "warning_findings": ["shadow_sidecar_hook_error"],
                },
            },
            next_safe_step="preserve_deterministic_pipeline_result",
        )


def build_shadow_sidecar_pipeline_hook_payload(**kwargs: Any) -> dict[str, Any]:
    return run_shadow_sidecar_pipeline_hook(**kwargs)
