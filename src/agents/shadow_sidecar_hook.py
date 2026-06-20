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
    semantic_evidence_input_available: bool = False,
    semantic_evidence_input_attached: bool = False,
    provider_calls_made: bool = False,
    embeddings_created: bool = False,
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
        "semantic_evidence_input_available": bool(
            semantic_evidence_input_available
        ),
        "semantic_evidence_input_attached": bool(
            semantic_evidence_input_attached
        ),
        "semantic_evidence_input_shadow_only": True,
        "semantic_evidence_used_for_scoring": False,
        "semantic_evidence_used_for_ranking": False,
        "semantic_evidence_used_for_queue": False,
        "semantic_evidence_used_for_application": False,
        "did_write_database": False,
        "provider_calls_made": bool(provider_calls_made),
        "embeddings_created": bool(embeddings_created),
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
    *,
    semantic_evidence_quality_gate_enabled: bool = False,
    semantic_evidence_minimum_similarity_score: float = 0.75,
    semantic_evidence_minimum_count: int = 1,
    semantic_evidence_max_count: int = 5,
    semantic_evidence_quality_gate_helper: Any = None,
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
    semantic_source = _plain_dict(evidence_context.get("semantic_retrieval"))
    semantic_attached = bool(
        semantic_source
        and source_safety.get("semantic_evidence_attached") is True
    )
    quality_gate_payload: dict[str, Any] = {}
    if semantic_attached and semantic_evidence_quality_gate_enabled is True:
        quality_gate = semantic_evidence_quality_gate_helper
        if quality_gate is None:
            from src.agents.semantic_evidence_quality_gate import (
                run_semantic_evidence_quality_gate,
            )

            quality_gate = run_semantic_evidence_quality_gate
        quality_result = quality_gate(
            enabled=True,
            evidence_items=deepcopy(
                semantic_source.get("retrieval_candidates", []) or []
            ),
            minimum_similarity_score=(
                semantic_evidence_minimum_similarity_score
            ),
            minimum_evidence_count=semantic_evidence_minimum_count,
            max_evidence_count=semantic_evidence_max_count,
        )
        quality_gate_payload = (
            deepcopy(quality_result)
            if isinstance(quality_result, dict)
            else {}
        )
        semantic_attached = bool(
            quality_gate_payload.get("status") == "evidence_quality_passed"
            and quality_gate_payload.get(
                "semantic_evidence_quality_passed"
            )
        )
        if semantic_attached:
            semantic_source["retrieval_candidates"] = deepcopy(
                quality_gate_payload.get("quality_evidence", []) or []
            )
            semantic_source["result_count"] = len(
                semantic_source["retrieval_candidates"]
            )
            evidence_context["semantic_retrieval"] = deepcopy(
                semantic_source
            )
        else:
            evidence_context.pop("semantic_retrieval", None)
    provider_calls_made = bool(
        source_safety.get("provider_calls_made")
    ) if semantic_attached else False
    embeddings_created = bool(
        source_safety.get("embeddings_created")
    ) if semantic_attached else False
    context = {
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
        "semantic_evidence_input_available": semantic_attached,
        "semantic_evidence_input_attached": semantic_attached,
        "semantic_evidence_input_shadow_only": True,
        "semantic_evidence_used_for_scoring": False,
        "semantic_evidence_used_for_ranking": False,
        "semantic_evidence_used_for_queue": False,
        "semantic_evidence_used_for_application": False,
        "did_write_database": False,
        "provider_calls_made": provider_calls_made,
        "embeddings_created": embeddings_created,
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
            "semantic_evidence_input_available": semantic_attached,
            "semantic_evidence_input_attached": semantic_attached,
            "semantic_evidence_input_shadow_only": True,
            "semantic_evidence_used_for_scoring": False,
            "semantic_evidence_used_for_ranking": False,
            "semantic_evidence_used_for_queue": False,
            "semantic_evidence_used_for_application": False,
            "did_write_database": False,
            "provider_calls_made": provider_calls_made,
            "embeddings_created": embeddings_created,
        },
    }
    if semantic_evidence_quality_gate_enabled is True:
        context["semantic_evidence_quality_gate"] = quality_gate_payload
        context["safety_metadata"].update(
            {
                "semantic_evidence_quality_gate_enabled": True,
                "semantic_evidence_quality_passed": semantic_attached,
            }
        )
    if semantic_attached:
        context["semantic_evidence_context"] = {
            "status": _clean_text(semantic_source.get("status")),
            "result_count": int(semantic_source.get("result_count") or 0),
            "retrieval_candidates": [
                {
                    key: deepcopy(candidate.get(key))
                    for key in (
                        "chunk_id",
                        "chunk_type",
                        "source_type",
                        "source_id",
                        "retrieval_score",
                        "distance",
                    )
                    if candidate.get(key) is not None
                }
                for candidate in semantic_source.get("retrieval_candidates", [])
                if isinstance(candidate, dict)
            ],
            "read_only": True,
            "advisory_only": True,
            "shadow_only": True,
            "semantic_evidence_input_available": True,
            "semantic_evidence_input_attached": True,
            "semantic_evidence_input_shadow_only": True,
            "semantic_evidence_used_for_scoring": False,
            "semantic_evidence_used_for_ranking": False,
            "semantic_evidence_used_for_queue": False,
            "semantic_evidence_used_for_application": False,
            "did_write_database": False,
            "provider_calls_made": provider_calls_made,
            "embeddings_created": embeddings_created,
        }
        if semantic_evidence_quality_gate_enabled is True:
            context["semantic_evidence_context"][
                "semantic_evidence_quality_gate"
            ] = deepcopy(quality_gate_payload)
    return context


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
        "provider_backed_automated_agents": int(
            chain.get("provider_backed_automated_agents", 0) or 0
        ),
        "live_provider_backed_automated_agents": int(
            chain.get("live_provider_backed_automated_agents", 0) or 0
        ),
        "mutation_authorized_agents": 0,
        "mutation_authorized_scoring_agents": 0,
        "mutation_authorized_ranking_agents": 0,
        "mutation_authorized_application_agents": 0,
        "live_production_pipeline_connected_agents": 0,
        "live_agents_allowed_to_automate_mutations": 0,
    }
    vector_context = _plain_dict(
        payload["existing_trace_context"].get("vector_evidence_context")
    )
    semantic_context = _plain_dict(
        vector_context.get("semantic_evidence_context")
    )
    payload["safety_metadata"] = evaluate_shadow_sidecar_pipeline_hook_safety(
        called_by_pipeline=called_by_pipeline,
        vector_evidence_context_available=bool(vector_context),
        vector_evidence_context_attached=bool(vector_context),
        semantic_evidence_input_available=bool(semantic_context),
        semantic_evidence_input_attached=bool(semantic_context),
        provider_calls_made=bool(
            semantic_context.get("provider_calls_made")
            or chain.get("provider_backed_automated_agents")
        ),
        embeddings_created=bool(
            semantic_context.get("embeddings_created")
        ),
    )
    jd_result = next(
        (
            result
            for result in chain.get("ordered_agent_results", [])
            if isinstance(result, dict)
            and _clean_text(result.get("agent_name")) == "jd_intelligence"
        ),
        {},
    )
    jd_safety = _plain_dict(jd_result.get("safety_metadata"))
    tailoring_result = next(
        (
            result
            for result in chain.get("ordered_agent_results", [])
            if isinstance(result, dict)
            and _clean_text(result.get("agent_name"))
            == "tailoring_suggestion"
        ),
        {},
    )
    tailoring_safety = _plain_dict(
        tailoring_result.get("safety_metadata")
    )
    critic_result = next(
        (
            result
            for result in chain.get("ordered_agent_results", [])
            if isinstance(result, dict)
            and _clean_text(result.get("agent_name"))
            == "critic_guardrail"
        ),
        {},
    )
    critic_safety = _plain_dict(critic_result.get("safety_metadata"))
    payload["safety_metadata"].update(
        {
            "jd_intelligence_provider_enabled": bool(
                jd_safety.get("jd_intelligence_provider_enabled")
            ),
            "jd_intelligence_provider_attempted": bool(
                jd_safety.get("jd_intelligence_provider_attempted")
            ),
            "jd_intelligence_provider_succeeded": bool(
                jd_safety.get("jd_intelligence_provider_succeeded")
            ),
            "jd_intelligence_schema_validated": bool(
                jd_safety.get("jd_intelligence_schema_validated")
            ),
            "tailoring_provider_enabled": bool(
                tailoring_safety.get("tailoring_provider_enabled")
            ),
            "tailoring_provider_attempted": bool(
                tailoring_safety.get("tailoring_provider_attempted")
            ),
            "tailoring_provider_succeeded": bool(
                tailoring_safety.get("tailoring_provider_succeeded")
            ),
            "tailoring_schema_validated": bool(
                tailoring_safety.get("tailoring_schema_validated")
            ),
            "critic_provider_enabled": bool(
                critic_safety.get("critic_provider_enabled")
            ),
            "critic_provider_attempted": bool(
                critic_safety.get("critic_provider_attempted")
            ),
            "critic_provider_succeeded": bool(
                critic_safety.get("critic_provider_succeeded")
            ),
            "critic_schema_validated": bool(
                critic_safety.get("critic_schema_validated")
            ),
        }
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
    semantic_evidence_quality_gate_enabled: bool = False,
    semantic_evidence_minimum_similarity_score: float = 0.75,
    semantic_evidence_minimum_count: int = 1,
    semantic_evidence_max_count: int = 5,
    semantic_evidence_quality_gate_helper: Any = None,
    three_agent_shadow_workflow_enabled: bool = False,
    llmops_trace_contract_enabled: bool = False,
    llmops_trace_metadata_by_agent: dict[str, dict[str, Any]] | None = None,
    llmops_trace_contract_helper: Any = None,
    llmops_aggregate_enabled: bool = False,
    llmops_aggregate_helper: Any = None,
    workflow_readiness_enabled: bool = False,
    workflow_readiness_helper: Any = None,
    jd_intelligence_provider_enabled: bool = False,
    jd_intelligence_provider: Any = None,
    jd_intelligence_provider_metadata: dict[str, Any] | None = None,
    tailoring_provider_enabled: bool = False,
    tailoring_provider: Any = None,
    tailoring_provider_metadata: dict[str, Any] | None = None,
    critic_provider_enabled: bool = False,
    critic_provider: Any = None,
    critic_provider_metadata: dict[str, Any] | None = None,
    provider_handoff_enabled: bool = False,
    provider_runtime_adapter_enabled: bool = False,
    provider_runtime_adapter_client: Any = None,
    provider_runtime_adapter_helper: Any = None,
    provider_runtime_provider_name: str = "",
    provider_runtime_model_name: str = "",
    jd_provider_runtime_activation_enabled: bool = False,
    jd_provider_runtime_activation_client: Any = None,
    jd_provider_runtime_activation_provider: Any = None,
    jd_provider_runtime_activation_helper: Any = None,
    jd_provider_runtime_activation_adapter_runner: Any = None,
    called_by_pipeline: bool = False,
    trace_persistence_writer: Any = None,
) -> dict[str, Any]:
    trace_context = _snapshot(existing_trace_context or {})
    vector_evidence_context = _advisory_vector_evidence_context(
        vector_evidence_hook_payload,
        semantic_evidence_quality_gate_enabled=(
            semantic_evidence_quality_gate_enabled
        ),
        semantic_evidence_minimum_similarity_score=(
            semantic_evidence_minimum_similarity_score
        ),
        semantic_evidence_minimum_count=semantic_evidence_minimum_count,
        semantic_evidence_max_count=semantic_evidence_max_count,
        semantic_evidence_quality_gate_helper=(
            semantic_evidence_quality_gate_helper
        ),
    )
    if vector_evidence_context:
        trace_context["vector_evidence_context"] = vector_evidence_context

    effective_sidecar_config = _snapshot(sidecar_config or {})
    if three_agent_shadow_workflow_enabled is True:
        effective_sidecar_config.update(
            {
                shadow_sidecar.GLOBAL_SIDECAR_FLAG: True,
                shadow_sidecar.JD_INTELLIGENCE_FLAG: True,
                shadow_sidecar.TAILORING_SUGGESTION_FLAG: True,
                shadow_sidecar.CRITIC_GUARDRAIL_FLAG: True,
                shadow_sidecar.THREE_AGENT_SHADOW_WORKFLOW_FLAG: True,
                "provider_execution_allowed": False,
            }
        )
    if (
        three_agent_shadow_workflow_enabled is True
        and (
            jd_intelligence_provider_enabled is True
            or tailoring_provider_enabled is True
            or critic_provider_enabled is True
            or jd_provider_runtime_activation_enabled is True
        )
    ):
        effective_sidecar_config["provider_execution_allowed"] = True

    runtime_adapter_metadata_by_agent: dict[str, dict[str, Any]] = {}

    def runtime_adapter_provider(
        *,
        agent_name: str,
        direct_provider: Any,
    ) -> Any:
        if provider_runtime_adapter_enabled is not True:
            return direct_provider

        def call_provider_runtime_adapter(
            provider_request: dict[str, Any],
        ) -> dict[str, Any]:
            adapter = provider_runtime_adapter_helper
            if adapter is None:
                from src.agents.provider_runtime_adapter import (
                    run_provider_runtime_adapter,
                )

                adapter = run_provider_runtime_adapter
            adapter_result = adapter(
                enabled=True,
                request_payload={
                    "agent_name": agent_name,
                    "provider_request": deepcopy(provider_request),
                },
                provider_name=provider_runtime_provider_name,
                model_name=provider_runtime_model_name,
                provider_callable=(
                    direct_provider if callable(direct_provider) else None
                ),
                **{"provider_" + "client": provider_runtime_adapter_client},
            )
            adapter_result = _plain_dict(adapter_result)
            attempted = bool(
                adapter_result.get("provider_call_attempted")
            )
            succeeded = bool(
                adapter_result.get("provider_call_succeeded")
            )
            blocked = bool(adapter_result.get("provider_call_blocked"))
            runtime_adapter_metadata_by_agent[agent_name] = {
                "provider_runtime_adapter_enabled": True,
                "provider_runtime_adapter_attempted": attempted,
                "provider_runtime_adapter_succeeded": succeeded,
                "provider_runtime_adapter_blocked": blocked,
                "provider_calls_made": attempted,
                "embeddings_created": False,
                "did_write_database": False,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
                "did_mutate_queue": False,
                "did_create_approval": False,
                "did_mutate_resume": False,
                "did_create_execution_request": False,
                "did_execute_application": False,
                "did_submit_application": False,
            }
            if not succeeded:
                error_type = _clean_text(
                    adapter_result.get("error_type")
                ) or _clean_text(adapter_result.get("status"))
                raise RuntimeError(error_type or "provider_runtime_blocked")
            output = _plain_dict(adapter_result.get("output"))
            return {
                **output,
                "model_provider": _clean_text(
                    adapter_result.get("provider_name")
                ),
                "model_name": _clean_text(
                    adapter_result.get("model_name")
                ),
                "latency_ms": int(
                    adapter_result.get("latency_ms") or 0
                ),
                "token_usage": {
                    "input_token_count": int(
                        adapter_result.get("input_tokens") or 0
                    ),
                    "output_token_count": int(
                        adapter_result.get("output_tokens") or 0
                    ),
                    "total_token_count": int(
                        adapter_result.get("total_tokens") or 0
                    ),
                },
                "cost": {
                    "estimated_cost": float(
                        adapter_result.get("estimated_cost") or 0
                    )
                },
            }

        return call_provider_runtime_adapter

    jd_activation_bridge_metadata: dict[str, Any] = {}
    jd_shadow_agent = None
    if (
        three_agent_shadow_workflow_enabled is True
        and jd_provider_runtime_activation_enabled is True
    ):
        activation_helper = jd_provider_runtime_activation_helper
        if activation_helper is None:
            from src.agents.jd_provider_runtime_activation import (
                run_jd_provider_runtime_activation,
            )

            activation_helper = run_jd_provider_runtime_activation

        def jd_shadow_agent(sidecar_input: dict[str, Any]) -> dict[str, Any]:
            activation = activation_helper(
                enabled=True,
                job_payload=_plain_dict(
                    sidecar_input.get("job_payload")
                ),
                context_id=_clean_text(sidecar_input.get("run_id")),
                job_id=_clean_text(sidecar_input.get("job_id")),
                provider_name=provider_runtime_provider_name,
                model_name=provider_runtime_model_name,
                provider_callable=jd_provider_runtime_activation_provider,
                **{"provider_" + "client": jd_provider_runtime_activation_client},
                adapter_runner=(
                    jd_provider_runtime_activation_adapter_runner
                ),
            )
            activation = _plain_dict(activation)
            provider_payload = _plain_dict(
                activation.get("jd_intelligence_output")
            )
            metadata = _plain_dict(
                activation.get("llmops_trace_metadata")
            )
            safety = _plain_dict(activation.get("safety_metadata"))
            validation_status = _clean_text(
                provider_payload.get("validation_status")
            )
            succeeded = validation_status == "valid"
            provider_called = bool(
                metadata.get("provider_call_attempted")
            )
            jd_activation_bridge_metadata.update(
                {
                    "activation_status": _clean_text(
                        activation.get("status")
                    ),
                    "llmops_trace_metadata": deepcopy(metadata),
                    "safety_metadata": deepcopy(safety),
                    "provider_called": provider_called,
                    "succeeded": succeeded,
                    "fallback_used": bool(
                        activation.get("fallback_used")
                    ),
                }
            )
            provider_payload["provider_metadata"] = {
                **metadata,
                "jd_provider_runtime_activation_enabled": True,
                "jd_provider_runtime_activation_status": _clean_text(
                    activation.get("status")
                ),
                "shadow_only": True,
            }
            provider_payload["safety_metadata"] = {
                **_plain_dict(
                    provider_payload.get("safety_metadata")
                ),
                **safety,
                "jd_intelligence_provider_enabled": True,
                "jd_intelligence_provider_attempted": provider_called,
                "jd_intelligence_provider_succeeded": succeeded,
                "jd_intelligence_schema_validated": succeeded,
                "jd_provider_runtime_activation_enabled": True,
                "jd_provider_runtime_activation_attempted": provider_called,
                "jd_provider_runtime_activation_succeeded": succeeded,
                "jd_provider_runtime_activation_fallback": bool(
                    activation.get("fallback_used")
                ),
                "provider_calls_made": provider_called,
                "did_write_database": False,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
                "did_mutate_queue": False,
                "did_create_approval": False,
                "did_mutate_resume": False,
                "did_execute_application": False,
                "did_submit_application": False,
            }
            return {
                "agent_output_status": (
                    "completed_shadow"
                    if succeeded
                    else "completed_with_fallback"
                ),
                "agent_recommendation": (
                    "preserve_source_deterministic_decision"
                ),
                "agent_confidence": float(
                    provider_payload.get("extraction_confidence") or 0
                ),
                "agent_reason_codes": list(
                    provider_payload.get("validation_errors") or []
                ),
                "agent_evidence_refs": [
                    f"jd_provider_runtime.{field}"
                    for field in (
                        "required_skills",
                        "preferred_skills",
                        "required_tools",
                        "preferred_tools",
                        "workflows",
                        "methods",
                        "business_contexts",
                        "stakeholder_contexts",
                        "ownership_signals",
                        "seniority_signals",
                    )
                    if provider_payload.get(field)
                ],
                "agent_risk_flags": list(
                    provider_payload.get("risk_flags") or []
                ),
                "agent_output_payload": provider_payload,
            }
    elif (
        three_agent_shadow_workflow_enabled is True
        and jd_intelligence_provider_enabled is True
    ):
        from src.agents.jd_intelligence import (
            build_live_jd_intelligence_dry_run_payload,
        )

        def jd_shadow_agent(sidecar_input: dict[str, Any]) -> dict[str, Any]:
            job = _plain_dict(sidecar_input.get("job_payload"))
            provider_payload = build_live_jd_intelligence_dry_run_payload(
                job_title=job.get("title"),
                company=job.get("company"),
                location=job.get("location"),
                job_description=(
                    job.get("job_description") or job.get("description")
                ),
                source_metadata=_plain_dict(job.get("source_metadata")),
                context_id=sidecar_input.get("run_id"),
                job_id=sidecar_input.get("job_id"),
                adapter=runtime_adapter_provider(
                    agent_name="jd_intelligence",
                    direct_provider=jd_intelligence_provider,
                ),
                feature_enabled=True,
            )
            validation_status = _clean_text(
                provider_payload.get("validation_status")
            )
            provider_called = bool(
                _plain_dict(
                    provider_payload.get("safety_metadata")
                ).get("did_call_llm")
            )
            succeeded = validation_status == "valid"
            supplied_metadata = _plain_dict(
                jd_intelligence_provider_metadata
            )
            metadata = {
                "model_provider": _clean_text(
                    provider_payload.get("model_provider")
                ),
                "model_name": _clean_text(
                    provider_payload.get("model_name")
                ),
                "prompt_version": _clean_text(
                    provider_payload.get("prompt_version")
                ),
                "latency_ms": int(
                    provider_payload.get("latency_ms") or 0
                ),
                "fallback_used": bool(
                    provider_payload.get("fallback_used")
                    or not succeeded
                ),
                "schema_validation_status": validation_status,
                "error_type": (
                    _clean_text(
                        (provider_payload.get("validation_errors") or [""])[0]
                    )
                    if validation_status not in {"valid", ""}
                    else ""
                ),
                "provider_call_made": provider_called,
            }
            metadata.update(supplied_metadata)
            token_usage = _plain_dict(
                provider_payload.get("token_usage")
            )
            cost = _plain_dict(provider_payload.get("cost"))
            metadata.update(
                {
                    "input_tokens": int(
                        metadata.get("input_tokens")
                        or token_usage.get("input_token_count")
                        or token_usage.get("prompt_tokens")
                        or 0
                    ),
                    "output_tokens": int(
                        metadata.get("output_tokens")
                        or token_usage.get("output_token_count")
                        or token_usage.get("completion_tokens")
                        or 0
                    ),
                    "estimated_cost": float(
                        metadata.get("estimated_cost")
                        or cost.get("estimated_cost")
                        or cost.get("usd")
                        or 0
                    ),
                    "retry_count": int(
                        metadata.get("retry_count") or 0
                    ),
                }
            )
            provider_payload["provider_metadata"] = metadata
            provider_payload["fallback_used"] = bool(
                provider_payload.get("fallback_used") or not succeeded
            )
            provider_payload["safety_metadata"] = {
                **_plain_dict(provider_payload.get("safety_metadata")),
                "jd_intelligence_provider_enabled": True,
                "jd_intelligence_provider_attempted": provider_called,
                "jd_intelligence_provider_succeeded": succeeded,
                "jd_intelligence_schema_validated": succeeded,
                "provider_calls_made": provider_called,
                "did_write_database": False,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
                "did_mutate_queue": False,
                "did_create_approval": False,
                "did_mutate_resume": False,
                "did_execute_application": False,
                "did_submit_application": False,
            }
            return {
                "agent_output_status": (
                    "completed_shadow"
                    if succeeded
                    else "completed_with_fallback"
                ),
                "agent_recommendation": (
                    "preserve_source_deterministic_decision"
                ),
                "agent_confidence": float(
                    provider_payload.get("extraction_confidence") or 0
                ),
                "agent_reason_codes": list(
                    provider_payload.get("validation_errors") or []
                ),
                "agent_evidence_refs": [
                    f"jd_provider.{field}"
                    for field in (
                        "required_skills",
                        "preferred_skills",
                        "required_tools",
                        "preferred_tools",
                        "workflows",
                        "methods",
                        "business_contexts",
                        "stakeholder_contexts",
                        "ownership_signals",
                        "seniority_signals",
                    )
                    if provider_payload.get(field)
                ],
                "agent_risk_flags": list(
                    provider_payload.get("risk_flags") or []
                ),
                "agent_output_payload": provider_payload,
            }

    tailoring_shadow_agent = None
    if (
        three_agent_shadow_workflow_enabled is True
        and tailoring_provider_enabled is True
    ):
        from src.agents.tailoring_decision_agent import (
            build_live_tailoring_suggestion_shadow_payload,
        )

        def tailoring_shadow_agent(
            sidecar_input: dict[str, Any],
        ) -> dict[str, Any]:
            job = _plain_dict(sidecar_input.get("job_payload"))
            trace = _plain_dict(
                sidecar_input.get("existing_trace_context")
            )
            trusted_jd_output = _plain_dict(
                trace.get("jd_intelligence_provider_output")
            )
            resume = _plain_dict(
                sidecar_input.get("resume_profile_payload")
            )
            provider_payload = (
                build_live_tailoring_suggestion_shadow_payload(
                    jd_intelligence=trusted_jd_output
                    if provider_handoff_enabled is True
                    else {
                        key: deepcopy(job.get(key))
                        for key in (
                            "required_skills",
                            "preferred_skills",
                            "required_tools",
                            "preferred_tools",
                            "workflows",
                            "methods",
                            "business_contexts",
                            "stakeholder_contexts",
                            "ownership_signals",
                            "seniority_signals",
                        )
                    },
                    resume_profile=resume,
                    context_id=sidecar_input.get("run_id"),
                    job_id=sidecar_input.get("job_id"),
                    adapter=runtime_adapter_provider(
                        agent_name="tailoring_suggestion",
                        direct_provider=tailoring_provider,
                    ),
                    feature_enabled=True,
                )
            )
            validation_status = _clean_text(
                provider_payload.get("validation_status")
            )
            provider_called = bool(
                _plain_dict(
                    provider_payload.get("safety_metadata")
                ).get("did_call_llm")
            )
            succeeded = validation_status == "valid"
            supplied_metadata = _plain_dict(
                tailoring_provider_metadata
            )
            token_usage = _plain_dict(
                provider_payload.get("token_usage")
            )
            cost = _plain_dict(provider_payload.get("cost"))
            metadata = {
                "model_provider": _clean_text(
                    provider_payload.get("model_provider")
                ),
                "model_name": _clean_text(
                    provider_payload.get("model_name")
                ),
                "prompt_version": _clean_text(
                    provider_payload.get("prompt_version")
                ),
                "latency_ms": int(
                    provider_payload.get("latency_ms") or 0
                ),
                "fallback_used": bool(
                    provider_payload.get("fallback_used")
                    or not succeeded
                ),
                "schema_validation_status": validation_status,
                "error_type": (
                    _clean_text(
                        (provider_payload.get("validation_errors") or [""])[0]
                    )
                    if validation_status not in {"valid", ""}
                    else ""
                ),
                "provider_call_made": provider_called,
            }
            metadata.update(supplied_metadata)
            metadata.update(
                {
                    "input_tokens": int(
                        metadata.get("input_tokens")
                        or token_usage.get("input_token_count")
                        or token_usage.get("prompt_tokens")
                        or 0
                    ),
                    "output_tokens": int(
                        metadata.get("output_tokens")
                        or token_usage.get("output_token_count")
                        or token_usage.get("completion_tokens")
                        or 0
                    ),
                    "estimated_cost": float(
                        metadata.get("estimated_cost")
                        or cost.get("estimated_cost")
                        or cost.get("usd")
                        or 0
                    ),
                    "retry_count": int(
                        metadata.get("retry_count") or 0
                    ),
                }
            )
            provider_payload["provider_metadata"] = metadata
            provider_payload["fallback_used"] = bool(
                provider_payload.get("fallback_used") or not succeeded
            )
            provider_payload["safety_metadata"] = {
                **_plain_dict(provider_payload.get("safety_metadata")),
                "tailoring_provider_enabled": True,
                "tailoring_provider_attempted": provider_called,
                "tailoring_provider_succeeded": succeeded,
                "tailoring_schema_validated": succeeded,
                "provider_calls_made": provider_called,
                "did_write_database": False,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
                "did_mutate_queue": False,
                "did_create_approval": False,
                "did_mutate_resume": False,
                "did_execute_application": False,
                "did_submit_application": False,
            }
            suggestion_count = sum(
                len(provider_payload.get(field, []) or [])
                for field in (
                    "patch_ready_suggestions",
                    "guidance_only_suggestions",
                    "rejected_suggestions",
                )
            )
            return {
                "agent_output_status": (
                    "completed_shadow"
                    if succeeded
                    else "completed_with_fallback"
                ),
                "agent_recommendation": (
                    "preserve_source_deterministic_decision"
                ),
                "agent_confidence": 1.0 if succeeded else 0.0,
                "agent_reason_codes": list(
                    provider_payload.get("validation_errors") or []
                ),
                "agent_evidence_refs": [
                    f"tailoring_provider.suggestion_{index + 1}"
                    for index in range(suggestion_count)
                ],
                "agent_risk_flags": [
                    _clean_text(item)
                    for suggestion in (
                        provider_payload.get("rejected_suggestions") or []
                    )
                    if isinstance(suggestion, dict)
                    for item in suggestion.get("risk_flags", [])
                    if _clean_text(item)
                ],
                "agent_output_payload": provider_payload,
            }

    critic_shadow_agent = None
    if (
        three_agent_shadow_workflow_enabled is True
        and critic_provider_enabled is True
    ):
        from src.agents.critic_agent import (
            build_live_critic_guardrail_shadow_payload,
        )

        def critic_shadow_agent(
            sidecar_input: dict[str, Any],
        ) -> dict[str, Any]:
            job = _plain_dict(sidecar_input.get("job_payload"))
            resume = _plain_dict(
                sidecar_input.get("resume_profile_payload")
            )
            tailoring_context = _plain_dict(
                _plain_dict(
                    sidecar_input.get("existing_trace_context")
                ).get("tailoring_suggestion_payload")
            )
            if provider_handoff_enabled is True:
                tailoring_context = _plain_dict(
                    _plain_dict(
                        sidecar_input.get("existing_trace_context")
                    ).get("tailoring_suggestion_provider_output")
                )
            provider_payload = build_live_critic_guardrail_shadow_payload(
                tailoring_suggestion_payload=tailoring_context,
                jd_intelligence={
                    key: deepcopy(job.get(key))
                    for key in (
                        "required_skills",
                        "preferred_skills",
                        "required_tools",
                        "preferred_tools",
                        "workflows",
                        "methods",
                        "business_contexts",
                        "stakeholder_contexts",
                        "ownership_signals",
                        "seniority_signals",
                    )
                },
                resume_profile=resume,
                context_id=sidecar_input.get("run_id"),
                job_id=sidecar_input.get("job_id"),
                adapter=runtime_adapter_provider(
                    agent_name="critic_guardrail",
                    direct_provider=critic_provider,
                ),
                feature_enabled=True,
            )
            validation_status = _clean_text(
                provider_payload.get("validation_status")
            )
            provider_called = bool(
                _plain_dict(
                    provider_payload.get("safety_metadata")
                ).get("did_call_llm")
            )
            succeeded = validation_status == "valid"
            supplied_metadata = _plain_dict(critic_provider_metadata)
            token_usage = _plain_dict(
                provider_payload.get("token_usage")
            )
            cost = _plain_dict(provider_payload.get("cost"))
            metadata = {
                "model_provider": _clean_text(
                    provider_payload.get("model_provider")
                ),
                "model_name": _clean_text(
                    provider_payload.get("model_name")
                ),
                "prompt_version": _clean_text(
                    provider_payload.get("prompt_version")
                ),
                "latency_ms": int(
                    provider_payload.get("latency_ms") or 0
                ),
                "fallback_used": bool(
                    provider_payload.get("fallback_used")
                    or not succeeded
                ),
                "schema_validation_status": validation_status,
                "error_type": (
                    _clean_text(
                        (provider_payload.get("validation_errors") or [""])[0]
                    )
                    if validation_status not in {"valid", ""}
                    else ""
                ),
                "provider_call_made": provider_called,
            }
            metadata.update(supplied_metadata)
            metadata.update(
                {
                    "input_tokens": int(
                        metadata.get("input_tokens")
                        or token_usage.get("input_token_count")
                        or token_usage.get("prompt_tokens")
                        or 0
                    ),
                    "output_tokens": int(
                        metadata.get("output_tokens")
                        or token_usage.get("output_token_count")
                        or token_usage.get("completion_tokens")
                        or 0
                    ),
                    "estimated_cost": float(
                        metadata.get("estimated_cost")
                        or cost.get("estimated_cost")
                        or cost.get("usd")
                        or 0
                    ),
                    "retry_count": int(
                        metadata.get("retry_count") or 0
                    ),
                }
            )
            provider_payload["provider_metadata"] = metadata
            provider_payload["fallback_used"] = bool(
                provider_payload.get("fallback_used") or not succeeded
            )
            provider_payload["safety_metadata"] = {
                **_plain_dict(provider_payload.get("safety_metadata")),
                "critic_provider_enabled": True,
                "critic_provider_attempted": provider_called,
                "critic_provider_succeeded": succeeded,
                "critic_schema_validated": succeeded,
                "provider_calls_made": provider_called,
                "did_write_database": False,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
                "did_mutate_queue": False,
                "did_create_approval": False,
                "did_mutate_resume": False,
                "did_execute_application": False,
                "did_submit_application": False,
            }
            return {
                "agent_output_status": (
                    "completed_shadow"
                    if succeeded
                    else "completed_with_fallback"
                ),
                "agent_recommendation": (
                    "preserve_source_deterministic_decision"
                ),
                "agent_confidence": float(
                    provider_payload.get("confidence") or 0
                ),
                "agent_reason_codes": list(
                    provider_payload.get("reason_codes") or []
                )
                + list(provider_payload.get("validation_errors") or []),
                "agent_evidence_refs": [
                    f"critic_provider.decision_{index + 1}"
                    for index in range(
                        sum(
                            len(provider_payload.get(field, []) or [])
                            for field in (
                                "approved_suggestions",
                                "downgraded_suggestions",
                                "rejected_suggestions",
                            )
                        )
                    )
                ],
                "agent_risk_flags": list(
                    provider_payload.get("unsupported_claim_risks") or []
                )
                + list(provider_payload.get("ats_risks") or [])
                + list(provider_payload.get("readability_risks") or []),
                "agent_blocking_findings": list(
                    provider_payload.get("evidence_gaps") or []
                ),
                "agent_output_payload": provider_payload,
            }

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
        sidecar_config=effective_sidecar_config,
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
            sidecar_config=effective_sidecar_config,
            agent_name="shadow_sidecar_chain",
        )
        chain_payload = shadow_sidecar.run_shadow_sidecar_chain(
            sidecar_input=sidecar_input,
            jd_intelligence_shadow_agent=jd_shadow_agent,
            tailoring_shadow_agent=tailoring_shadow_agent,
            critic_shadow_agent=critic_shadow_agent,
            provider_handoff_enabled=provider_handoff_enabled is True,
        )
        if (
            llmops_trace_contract_enabled is True
            or llmops_aggregate_enabled is True
            or jd_intelligence_provider_enabled is True
            or tailoring_provider_enabled is True
            or critic_provider_enabled is True
            or jd_provider_runtime_activation_enabled is True
        ):
            trace_contract = llmops_trace_contract_helper
            if trace_contract is None:
                from src.agents.agent_llmops_trace_contract import (
                    attach_three_agent_llmops_trace_contract,
                )

                trace_contract = attach_three_agent_llmops_trace_contract
            chain_payload = trace_contract(
                chain_payload=chain_payload,
                enabled=True,
                metadata_by_agent=deepcopy(
                    llmops_trace_metadata_by_agent or {}
                ),
            )
        if jd_provider_runtime_activation_enabled is True:
            results = [
                deepcopy(result)
                for result in (
                    chain_payload.get("ordered_agent_results") or []
                )
                if isinstance(result, dict)
            ]
            for result in results:
                if _clean_text(result.get("agent_name")) != (
                    "jd_intelligence"
                ):
                    continue
                activation_trace = _plain_dict(
                    jd_activation_bridge_metadata.get(
                        "llmops_trace_metadata"
                    )
                )
                trace_metadata = _plain_dict(
                    result.get("llmops_trace_metadata")
                )
                trace_metadata.update(activation_trace)
                trace_metadata.update(
                    {
                        "jd_provider_runtime_activation_enabled": True,
                        "jd_provider_runtime_activation_status": (
                            _clean_text(
                                jd_activation_bridge_metadata.get(
                                    "activation_status"
                                )
                            )
                        ),
                    }
                )
                result["llmops_trace_metadata"] = trace_metadata
                result_safety = _plain_dict(
                    result.get("safety_metadata")
                )
                result_safety.update(
                    _plain_dict(
                        jd_activation_bridge_metadata.get(
                            "safety_metadata"
                        )
                    )
                )
                result_safety.update(
                    {
                        "jd_provider_runtime_activation_enabled": True,
                        "jd_provider_runtime_activation_attempted": bool(
                            jd_activation_bridge_metadata.get(
                                "provider_called"
                            )
                        ),
                        "jd_provider_runtime_activation_succeeded": bool(
                            jd_activation_bridge_metadata.get("succeeded")
                        ),
                        "jd_provider_runtime_activation_fallback": bool(
                            jd_activation_bridge_metadata.get(
                                "fallback_used"
                            )
                        ),
                    }
                )
                result["safety_metadata"] = result_safety
            chain_payload["ordered_agent_results"] = results
            chain_payload["agent_results"] = deepcopy(results)
        if provider_runtime_adapter_enabled is True:
            results = [
                deepcopy(result)
                for result in (
                    chain_payload.get("ordered_agent_results") or []
                )
                if isinstance(result, dict)
            ]
            for result in results:
                agent_name = _clean_text(result.get("agent_name"))
                adapter_metadata = _plain_dict(
                    runtime_adapter_metadata_by_agent.get(agent_name)
                )
                if not adapter_metadata:
                    adapter_metadata = {
                        "provider_runtime_adapter_enabled": True,
                        "provider_runtime_adapter_attempted": False,
                        "provider_runtime_adapter_succeeded": False,
                        "provider_runtime_adapter_blocked": True,
                        "provider_calls_made": False,
                        "embeddings_created": False,
                        "did_write_database": False,
                        "did_mutate_scoring": False,
                        "did_change_ranking": False,
                        "did_mutate_queue": False,
                        "did_create_approval": False,
                        "did_mutate_resume": False,
                        "did_create_execution_request": False,
                        "did_execute_application": False,
                        "did_submit_application": False,
                    }
                trace_metadata = _plain_dict(
                    result.get("llmops_trace_metadata")
                )
                trace_metadata.update(
                    {
                        key: adapter_metadata[key]
                        for key in (
                            "provider_runtime_adapter_enabled",
                            "provider_runtime_adapter_attempted",
                            "provider_runtime_adapter_succeeded",
                            "provider_runtime_adapter_blocked",
                        )
                    }
                )
                trace_metadata["provider_call_made"] = bool(
                    adapter_metadata.get("provider_calls_made")
                )
                result["llmops_trace_metadata"] = trace_metadata
                result_safety = _plain_dict(
                    result.get("safety_metadata")
                )
                result_safety.update(adapter_metadata)
                result["safety_metadata"] = result_safety
            chain_payload["ordered_agent_results"] = results
            chain_payload["agent_results"] = deepcopy(results)
            provider_backed_names = [
                _clean_text(result.get("agent_name"))
                for result in results
                if _plain_dict(
                    result.get("llmops_trace_metadata")
                ).get("provider_call_made")
                is True
            ]
            trace_contract_payload = _plain_dict(
                chain_payload.get("three_agent_llmops_trace_contract")
            )
            if trace_contract_payload:
                trace_contract_payload["agent_traces"] = [
                    deepcopy(
                        _plain_dict(
                            result.get("llmops_trace_metadata")
                        )
                    )
                    for result in results
                ]
                trace_contract_payload["provider_calls_made"] = bool(
                    provider_backed_names
                )
                trace_contract_payload[
                    "provider_backed_agent_count"
                ] = len(provider_backed_names)
                trace_contract_payload[
                    "provider_backed_agent_names"
                ] = provider_backed_names
                chain_payload[
                    "three_agent_llmops_trace_contract"
                ] = trace_contract_payload
            chain_payload["provider_backed_automated_agents"] = len(
                provider_backed_names
            )
            chain_payload[
                "live_provider_backed_automated_agents"
            ] = len(provider_backed_names)
        if llmops_aggregate_enabled is True:
            aggregate_helper = llmops_aggregate_helper
            if aggregate_helper is None:
                from src.agents.three_agent_llmops_aggregate import (
                    attach_three_agent_llmops_aggregate,
                )

                aggregate_helper = attach_three_agent_llmops_aggregate
            chain_payload = aggregate_helper(
                chain_payload=chain_payload,
                enabled=True,
            )
        if workflow_readiness_enabled is True:
            readiness_helper = workflow_readiness_helper
            if readiness_helper is None:
                from src.agents.three_agent_workflow_readiness import (
                    attach_three_agent_workflow_readiness,
                )

                readiness_helper = attach_three_agent_workflow_readiness
            chain_payload = readiness_helper(
                chain_payload=chain_payload,
                enabled=True,
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
