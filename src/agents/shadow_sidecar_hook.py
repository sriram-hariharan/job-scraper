from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents import shadow_sidecar


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


def _hook_status_from_chain(chain_payload: dict[str, Any]) -> str:
    chain_status = _clean_text(
        chain_payload.get("chain_status") or chain_payload.get("sidecar_chain_status")
    )
    if chain_status == shadow_sidecar.CHAIN_STATUS_COMPLETED_SHADOW_CHAIN:
        return "hook_completed_shadow_sidecar"
    if chain_status == shadow_sidecar.STATUS_FAILED_NON_BLOCKING:
        return "hook_failed_non_blocking"
    return "hook_completed_with_fallback"


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
    return {
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
