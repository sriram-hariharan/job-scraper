from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents import agent_recommendation_overlay
from src.agents import shadow_sidecar
from src.agents.shadow_sidecar_trace_persistence import (
    build_shadow_sidecar_trace_persistence_payload,
)
from src.storage.agent_trace.store import build_agent_trace_summary_payload


AGENT_RECOMMENDATION_OVERLAY_AUTO_GENERATE_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_AGENT_RECOMMENDATION_OVERLAY_AUTO_GENERATE_ENABLED"
)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _snapshot(value: Any) -> Any:
    return deepcopy(value)


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


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


def evaluate_shadow_sidecar_pipeline_hook_safety(
    *,
    called_by_pipeline: bool = False,
    vector_evidence_context_available: bool = False,
    vector_evidence_context_attached: bool = False,
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
        "vector_evidence_context_available": bool(
            vector_evidence_context_available
        ),
        "vector_evidence_context_attached": bool(
            vector_evidence_context_attached
        ),
        "vector_evidence_context_shadow_only": True,
        "vector_evidence_used_for_scoring": False,
        "vector_evidence_used_for_ranking": False,
        "vector_evidence_used_for_queue": False,
        "vector_evidence_used_for_application": False,
        "provider_calls_made": False,
        "embeddings_created": False,
    }


def evaluate_agent_recommendation_overlay_auto_generation_safety(
    *, automatic_generation: bool
) -> dict[str, bool]:
    safety = agent_recommendation_overlay.evaluate_agent_recommendation_overlay_safety()
    safety.update(
        {
            "automatic_generation": bool(automatic_generation),
            "pipeline_shadow_only": True,
            "manual_review_required": True,
            "approval_gate_required_for_influence": True,
            "did_create_approval": False,
            "did_mutate_approval": False,
            "did_create_execution_request": False,
            "did_create_execution_launch_request": False,
            "auto_apply_enabled": False,
            "mutation_authorized": False,
        }
    )
    return safety


def evaluate_agent_recommendation_overlay_trace_context_safety() -> dict[str, bool]:
    safety = evaluate_agent_recommendation_overlay_auto_generation_safety(
        automatic_generation=False
    )
    safety.update(
        {
            "trace_context_only": True,
            "pipeline_generated_overlay_context_propagation": True,
            "read_only": True,
            "advisory_only": True,
        }
    )
    return safety


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
        "agent_recommendation_overlay_auto_generation": deepcopy(
            hook.get("agent_recommendation_overlay_auto_generation") or {}
        ),
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


def _safe_shadow_sidecar_trace_persistence_payload(
    hook_payload: dict[str, Any],
    *,
    persistence_writer: Any = None,
) -> dict[str, Any]:
    try:
        return build_shadow_sidecar_trace_persistence_payload(
            trace_capture_payload=_snapshot(hook_payload.get("trace_capture") or {}),
            sidecar_config=_snapshot(hook_payload.get("sidecar_config") or {}),
            owner_user_id="shadow_sidecar",
            pipeline_run_id=_clean_text(hook_payload.get("source_deterministic_stage")),
            context_id=_clean_text(hook_payload.get("source_deterministic_decision")),
            persistence_writer=persistence_writer,
            called_by_hook=True,
        )
    except Exception as exc:
        return {
            "schema_version": shadow_sidecar.SCHEMA_VERSION,
            "trace_persistence_status": "trace_persistence_failed_non_blocking",
            "trace_persistence_only": True,
            "persistence_attempted": False,
            "error_type": exc.__class__.__name__,
            "provider_calls_disabled_in_tests": True,
            "requires_live_database": False,
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
            "safety_metadata": {
                "read_only": True,
                "shadow_only": True,
                "trace_persistence_only": True,
                "trace_persistence_called_by_hook": True,
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
                "auto_apply_enabled": False,
            },
        }


def _overlay_not_generated_payload(
    *,
    status: str,
    reason: str,
    automatic_generation: bool,
) -> dict[str, Any]:
    return {
        "schema_version": shadow_sidecar.SCHEMA_VERSION,
        "auto_generation_status": _clean_text(status),
        "overlay_generated": False,
        "blocked_reason": _clean_text(reason),
        "agent_recommendation_overlay": {},
        "provider_calls_disabled_in_tests": True,
        "requires_live_database": False,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "safety_metadata": evaluate_agent_recommendation_overlay_auto_generation_safety(
            automatic_generation=automatic_generation
        ),
    }


def _deterministic_context_from_hook_payload(
    hook_payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "deterministic_score": hook_payload.get("source_deterministic_score"),
        "deterministic_decision": _clean_text(
            hook_payload.get("source_deterministic_decision")
        ),
        "status": _clean_text(hook_payload.get("source_deterministic_status")),
        "source_deterministic_stage": _clean_text(
            hook_payload.get("source_deterministic_stage")
        ),
        "reason_codes": list(hook_payload.get("source_deterministic_reason_codes") or []),
    }


def _shadow_comparison_context_from_hook_payload(
    hook_payload: dict[str, Any],
) -> dict[str, Any]:
    trace_context = _plain_dict(hook_payload.get("existing_trace_context"))
    explicit = _plain_dict(
        trace_context.get("shadow_sidecar_score_comparison_result")
        or trace_context.get("shadow_score_comparison_context")
    )
    if explicit:
        return explicit

    chain = _plain_dict(hook_payload.get("chain_payload"))
    observability = _plain_dict(hook_payload.get("observability_payload"))
    readiness = _plain_dict(
        observability.get("readiness_decision") or hook_payload.get("readiness_decision")
    )
    chain_status = _clean_text(chain.get("chain_status") or chain.get("sidecar_chain_status"))
    if not chain_status:
        return {}

    blocking_findings = list(readiness.get("blocking_findings") or [])
    warning_findings = list(readiness.get("warning_findings") or [])
    stage_order = list(chain.get("stage_order") or [])
    if blocking_findings:
        agreement = "blocked_by_shadow_findings"
    elif warning_findings or bool(chain.get("fallback_used")):
        agreement = "needs_operator_review"
    else:
        agreement = "aligned"
    comparison_status = (
        "comparison_ready_with_fallback"
        if bool(chain.get("fallback_used")) or chain_status == shadow_sidecar.STATUS_COMPLETED_WITH_FALLBACK
        else "comparison_ready"
    )
    return {
        "comparison_status": comparison_status,
        "comparison_type": "shadow_sidecar_vs_deterministic_score",
        "agreement_level": agreement,
        "shadow_snapshot_status": chain_status,
        "shadow_agent_names": stage_order,
        "shadow_risk_flag_count": len(warning_findings),
        "shadow_blocking_finding_count": len(blocking_findings),
        "operator_review_summary": {
            "summary_type": "shadow_sidecar_hook_auto_overlay_source",
            "operator_review_only": True,
            "recommended_review_focus": list(
                readiness.get("decision_reason_codes") or []
            ),
        },
    }


def _influence_preview_context_from_hook_payload(
    hook_payload: dict[str, Any],
) -> dict[str, Any]:
    trace_context = _plain_dict(hook_payload.get("existing_trace_context"))
    return _plain_dict(
        trace_context.get("human_reviewed_influence_preview_result")
        or trace_context.get("human_reviewed_influence_preview_payload")
    )


def _approval_request_context_from_hook_payload(
    hook_payload: dict[str, Any],
) -> dict[str, Any]:
    trace_context = _plain_dict(hook_payload.get("existing_trace_context"))
    return _plain_dict(
        trace_context.get("human_reviewed_influence_approval_request_result")
        or trace_context.get("influence_approval_request_payload")
    )


def _advisory_vector_evidence_context(
    vector_evidence_hook_payload: Any,
) -> dict[str, Any]:
    source = _plain_dict(vector_evidence_hook_payload)
    source_safety = _plain_dict(source.get("safety_metadata"))
    evidence_context = _plain_dict(source.get("evidence_context"))
    context_available = bool(
        evidence_context
        and source_safety.get("vector_evidence_context_attached") is True
    )
    if not context_available:
        return {}
    return {
        "status": _clean_text(source.get("status")),
        "hook_surface": _clean_text(source.get("hook_surface")),
        "run_id": _clean_text(source.get("run_id")),
        "job_id": _clean_text(source.get("job_id")),
        "stage_name": _clean_text(source.get("stage_name")),
        "evidence_context": evidence_context,
        "vector_evidence_context_shadow_only": True,
        "vector_evidence_used_for_scoring": False,
        "vector_evidence_used_for_ranking": False,
        "vector_evidence_used_for_queue": False,
        "vector_evidence_used_for_application": False,
        "provider_calls_made": False,
        "embeddings_created": False,
        "safety_metadata": {
            "read_only": True,
            "advisory_only": True,
            "shadow_only": True,
            "vector_evidence_context_available": True,
            "vector_evidence_context_attached": True,
            "vector_evidence_context_shadow_only": True,
            "vector_evidence_used_for_scoring": False,
            "vector_evidence_used_for_ranking": False,
            "vector_evidence_used_for_queue": False,
            "vector_evidence_used_for_application": False,
            "provider_calls_made": False,
            "embeddings_created": False,
        },
    }


def _safe_agent_recommendation_overlay_auto_generation_payload(
    hook_payload: dict[str, Any],
) -> dict[str, Any]:
    config = _plain_dict(hook_payload.get("sidecar_config"))
    if not _config_bool(config, shadow_sidecar.GLOBAL_SIDECAR_FLAG, default=False):
        return _overlay_not_generated_payload(
            status="overlay_auto_generation_not_enabled",
            reason="global_shadow_sidecar_not_enabled",
            automatic_generation=False,
        )
    if not _config_bool(
        config,
        AGENT_RECOMMENDATION_OVERLAY_AUTO_GENERATE_FLAG,
        "agent_recommendation_overlay_auto_generate_enabled",
        default=False,
    ):
        return _overlay_not_generated_payload(
            status="overlay_auto_generation_not_enabled",
            reason="agent_recommendation_overlay_auto_generation_flag_disabled",
            automatic_generation=False,
        )
    if _config_bool(config, shadow_sidecar.KILL_SWITCH_FLAG, "kill_switch_enabled", default=False):
        return _overlay_not_generated_payload(
            status="overlay_auto_generation_blocked_by_kill_switch",
            reason="shadow_sidecar_kill_switch_enabled",
            automatic_generation=True,
        )

    try:
        overlay_config = {
            **config,
            agent_recommendation_overlay.AGENT_RECOMMENDATION_OVERLAY_FLAG: True,
        }
        overlay = agent_recommendation_overlay.build_agent_recommendation_overlay_payload(
            deterministic_score_context=_deterministic_context_from_hook_payload(
                hook_payload
            ),
            shadow_score_comparison_context=_shadow_comparison_context_from_hook_payload(
                hook_payload
            ),
            human_reviewed_influence_preview_payload=_influence_preview_context_from_hook_payload(
                hook_payload
            ),
            influence_approval_request_payload=_approval_request_context_from_hook_payload(
                hook_payload
            ),
            overlay_config=overlay_config,
        )
        safety = dict(overlay.get("safety_metadata") or {})
        safety.update(
            evaluate_agent_recommendation_overlay_auto_generation_safety(
                automatic_generation=True
            )
        )
        overlay["safety_metadata"] = safety
        return {
            "schema_version": shadow_sidecar.SCHEMA_VERSION,
            "auto_generation_status": (
                "overlay_auto_generated_partial"
                if overlay.get("overlay_status") == "overlay_partial_insufficient_context"
                else "overlay_auto_generated"
            ),
            "overlay_generated": True,
            "blocked_reason": "",
            "agent_recommendation_overlay": overlay,
            "provider_calls_disabled_in_tests": True,
            "requires_live_database": False,
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
            "safety_metadata": safety,
        }
    except Exception as exc:
        return {
            "schema_version": shadow_sidecar.SCHEMA_VERSION,
            "auto_generation_status": "overlay_auto_generation_failed_non_blocking",
            "overlay_generated": False,
            "blocked_reason": "overlay_generation_failed_non_blocking",
            "agent_recommendation_overlay": {},
            "error_type": exc.__class__.__name__,
            "provider_calls_disabled_in_tests": True,
            "requires_live_database": False,
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
            "safety_metadata": evaluate_agent_recommendation_overlay_auto_generation_safety(
                automatic_generation=True
            ),
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
    trace_persistence_writer: Any = None,
    existing_trace_context: dict[str, Any] | None = None,
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
        "existing_trace_context": deepcopy(existing_trace_context or {}),
        "chain_payload": chain,
        "observability_payload": observability,
        "sidecar_config": deepcopy(preview.get("sidecar_config") or {}),
        "readiness_decision": deepcopy(
            observability.get("readiness_decision")
            or preview.get("readiness_decision")
            or {}
        ),
        "next_safe_step": _clean_text(next_safe_step)
        or _clean_text(preview.get("next_safe_step")),
        "provider_calls_disabled_in_tests": True,
        "safety_metadata": {},
        "default_off_pipeline_hook_call_sites": 1 if called_by_pipeline else 0,
        "live_production_pipeline_connected_agents": 0,
        "live_agents_allowed_to_automate_mutations": 0,
    }
    vector_context = _plain_dict(
        payload["existing_trace_context"].get("vector_evidence_context")
    )
    payload["safety_metadata"] = evaluate_shadow_sidecar_pipeline_hook_safety(
        called_by_pipeline=called_by_pipeline,
        vector_evidence_context_available=bool(vector_context),
        vector_evidence_context_attached=bool(vector_context),
    )
    payload["agent_recommendation_overlay_auto_generation"] = (
        _safe_agent_recommendation_overlay_auto_generation_payload(payload)
    )
    overlay_context = deepcopy(
        payload["agent_recommendation_overlay_auto_generation"]
    )
    overlay_context_safety = dict(overlay_context.get("safety_metadata") or {})
    automatic_generation = bool(
        overlay_context_safety.get("automatic_generation")
    )
    overlay_context_safety.update(
        evaluate_agent_recommendation_overlay_trace_context_safety()
    )
    overlay_context_safety["automatic_generation"] = automatic_generation
    overlay_context["safety_metadata"] = overlay_context_safety
    payload["existing_trace_context"][
        "agent_recommendation_overlay_auto_generation"
    ] = overlay_context
    payload["trace_capture"] = _safe_shadow_sidecar_hook_trace_capture_payload(payload)
    payload["trace_persistence"] = _safe_shadow_sidecar_trace_persistence_payload(
        payload,
        persistence_writer=trace_persistence_writer,
    )
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
    vector_evidence_hook_payload: dict[str, Any] | None = None,
    called_by_pipeline: bool = False,
    trace_persistence_writer: Any = None,
) -> dict[str, Any]:
    trace_context = _snapshot(existing_trace_context or {})
    vector_evidence_context = _advisory_vector_evidence_context(
        vector_evidence_hook_payload
    )
    if vector_evidence_context:
        trace_context["vector_evidence_context"] = vector_evidence_context

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
        existing_trace_context=_snapshot(trace_context),
    )
    if preview.get("hook_preview_status") != "hook_ready_for_shadow_sidecar":
        return _base_hook_payload(
            preview_payload=preview,
            hook_status=_clean_text(preview.get("hook_preview_status")),
            chain_attempted=False,
            called_by_pipeline=called_by_pipeline,
            trace_persistence_writer=trace_persistence_writer,
            next_safe_step=_clean_text(preview.get("next_safe_step")),
            existing_trace_context=trace_context,
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
            existing_trace_context=_snapshot(trace_context),
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
            trace_persistence_writer=trace_persistence_writer,
            chain_payload=chain_payload,
            observability_payload=observability,
            next_safe_step="inspect_shadow_sidecar_observability",
            existing_trace_context=trace_context,
        )
    except Exception as exc:
        return _base_hook_payload(
            preview_payload=preview,
            hook_status="hook_failed_non_blocking",
            chain_attempted=True,
            called_by_pipeline=called_by_pipeline,
            trace_persistence_writer=trace_persistence_writer,
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
            existing_trace_context=trace_context,
        )


def build_shadow_sidecar_pipeline_hook_payload(**kwargs: Any) -> dict[str, Any]:
    return run_shadow_sidecar_pipeline_hook(**kwargs)
