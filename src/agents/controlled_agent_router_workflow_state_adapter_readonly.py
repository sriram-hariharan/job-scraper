"""Read-only workflow-state adapter for the controlled agent router."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents.controlled_agent_router_readonly import (
    build_controlled_agent_router_readonly_decision,
)


PHASE = "33B"

JOB_IDENTIFIER_FIELDS = (
    "job_id",
    "id",
    "merge_key",
    "title",
    "company",
    "location",
)

GENERATED_TAILORING_FIELDS = (
    "generated_text",
    "generated_tailoring_text",
    "tailored_resume_text",
    "real_tailoring_output",
    "resume_rewrite",
    "rewritten_resume",
    "draft_resume",
    "tailored_bullets",
    "generated_bullets",
    "suggestions",
)

REQUIRED_INPUTS_BY_STEP = {
    "run_relevance_prefilter": ("job_record",),
    "run_jd_intelligence": ("job_record", "relevance_result"),
    "run_final_application_scoring": (
        "job_record",
        "relevance_result",
        "jd_intelligence_result",
    ),
    "check_tailoring_opportunity": (
        "job_record",
        "relevance_result",
        "jd_intelligence_result",
        "final_score_result",
    ),
    "prepare_manual_tailoring_preview": (
        "job_record",
        "relevance_result",
        "jd_intelligence_result",
        "final_score_result",
        "tailoring_opportunity_result",
    ),
    "await_manual_review": (),
}


def _safe_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _is_present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _first_present(source: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in source:
            return source[name]
    return None


def _truth_marker(source: Any, names: tuple[str, ...]) -> bool | None:
    if isinstance(source, bool):
        return source
    if not isinstance(source, dict):
        return None
    for name in names:
        value = source.get(name)
        if isinstance(value, bool):
            return value
    return None


def _numeric_score(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if not isinstance(value, dict):
        return None
    for name in (
        "final_score",
        "score",
        "final_application_score",
        "application_score",
        "overall_score",
    ):
        score = value.get(name)
        if isinstance(score, (int, float)) and not isinstance(score, bool):
            return float(score)
    return None


def _job_summary(job_record: dict[str, Any]) -> dict[str, Any]:
    return {
        field: deepcopy(job_record[field])
        for field in JOB_IDENTIFIER_FIELDS
        if field in job_record and _is_present(job_record[field])
    }


def _normalize_relevance(value: dict[str, Any]) -> dict[str, Any]:
    rejected = _truth_marker(
        value,
        (
            "rejected",
            "not_relevant",
            "filtered_out",
            "prefilter_rejected",
        ),
    )
    if rejected is True:
        relevant = False
    else:
        relevant = _truth_marker(
            value,
            (
                "is_relevant",
                "relevant",
                "passes_prefilter",
                "prefilter_passed",
                "matched",
            ),
        )
    normalized = _safe_dict(value)
    if relevant is not None:
        normalized["is_relevant"] = relevant
    return normalized


def _normalize_jd_intelligence(value: dict[str, Any]) -> dict[str, Any]:
    normalized = _safe_dict(value)
    signals = _first_present(
        normalized,
        (
            "signals",
            "jd_signals",
            "job_signals",
            "requirements",
            "responsibilities",
            "skills",
        ),
    )
    if _is_present(signals):
        normalized["signals_present"] = True
    return normalized


def _normalize_tailoring_opportunity(value: dict[str, Any]) -> dict[str, Any]:
    helpful = _truth_marker(
        value,
        (
            "tailoring_may_help",
            "may_help",
            "helpful",
            "tailoring_recommended",
            "has_opportunity",
            "opportunity_found",
        ),
    )
    if helpful is None:
        not_helpful = _truth_marker(
            value,
            (
                "tailoring_does_not_help",
                "not_helpful",
                "no_tailoring_needed",
            ),
        )
        if not_helpful is True:
            helpful = False
    normalized = _safe_dict(value)
    if helpful is not None:
        normalized["tailoring_may_help"] = helpful
    return normalized


def _manual_preview_metadata(value: dict[str, Any]) -> dict[str, Any]:
    metadata: dict[str, Any] = {"manual_tailoring_preview_present": True}
    for key, item in value.items():
        lowered = str(key).lower()
        if key in GENERATED_TAILORING_FIELDS:
            continue
        if any(marker in lowered for marker in ("generated", "rewrite")):
            continue
        if isinstance(item, (str, int, float, bool)) or item is None:
            metadata[key] = deepcopy(item)
    return metadata


def _available_inputs(
    *,
    job_present: bool,
    relevance_result_present: bool,
    jd_intelligence_present: bool,
    final_score_present: bool,
    tailoring_opportunity_present: bool,
    manual_tailoring_preview_present: bool,
) -> list[str]:
    pairs = (
        ("job_record", job_present),
        ("relevance_result", relevance_result_present),
        ("jd_intelligence_result", jd_intelligence_present),
        ("final_score_result", final_score_present),
        ("tailoring_opportunity_result", tailoring_opportunity_present),
        (
            "manual_tailoring_preview_result",
            manual_tailoring_preview_present,
        ),
    )
    return [name for name, present in pairs if present]


def _adapter_key(
    *,
    next_allowed_step: str,
    available_inputs: list[str],
    missing_inputs: list[str],
) -> str:
    return "|".join(
        (
            f"phase={PHASE}",
            f"step={next_allowed_step}",
            "available=" + ",".join(available_inputs),
            "missing=" + ",".join(missing_inputs),
        )
    )


def build_controlled_agent_router_workflow_state_adapter_readonly(
    *,
    job_record: dict[str, Any] | None = None,
    relevance_result: dict[str, Any] | None = None,
    jd_intelligence_result: dict[str, Any] | None = None,
    final_score_result: dict[str, Any] | None = None,
    tailoring_opportunity_result: dict[str, Any] | None = None,
    manual_tailoring_preview_result: dict[str, Any] | None = None,
    router_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize supplied artifacts and return a router handoff packet."""

    safe_job = _safe_dict(job_record)
    safe_relevance = _safe_dict(relevance_result)
    safe_jd = _safe_dict(jd_intelligence_result)
    safe_score = _safe_dict(final_score_result)
    safe_tailoring = _safe_dict(tailoring_opportunity_result)
    safe_preview = _safe_dict(manual_tailoring_preview_result)

    job_present = bool(safe_job)
    relevance_result_present = bool(safe_relevance)
    jd_intelligence_present = bool(safe_jd)
    final_score = _numeric_score(safe_score)
    final_score_present = final_score is not None
    tailoring_opportunity_present = bool(safe_tailoring)
    manual_tailoring_preview_present = bool(safe_preview)

    current_state: dict[str, Any] = {}
    if job_present:
        current_state["job"] = _job_summary(safe_job)
    if relevance_result_present:
        current_state["relevance_result"] = _normalize_relevance(
            safe_relevance
        )
    if jd_intelligence_present:
        current_state["jd_intelligence"] = _normalize_jd_intelligence(
            safe_jd
        )
    if final_score_present:
        current_state["final_score"] = final_score
    if tailoring_opportunity_present:
        current_state["tailoring_opportunity"] = (
            _normalize_tailoring_opportunity(safe_tailoring)
        )
    if manual_tailoring_preview_present:
        current_state["manual_tailoring_preview"] = _manual_preview_metadata(
            safe_preview
        )

    any_input_present = any(
        (
            job_present,
            relevance_result_present,
            jd_intelligence_present,
            final_score_present,
            tailoring_opportunity_present,
            manual_tailoring_preview_present,
        )
    )
    router_decision = build_controlled_agent_router_readonly_decision(
        current_state=current_state if any_input_present else None,
        router_policy=router_policy,
    )
    next_allowed_step = router_decision["next_allowed_step"]
    required_inputs = list(
        REQUIRED_INPUTS_BY_STEP.get(next_allowed_step, ())
    )
    available_inputs = _available_inputs(
        job_present=job_present,
        relevance_result_present=relevance_result_present,
        jd_intelligence_present=jd_intelligence_present,
        final_score_present=final_score_present,
        tailoring_opportunity_present=tailoring_opportunity_present,
        manual_tailoring_preview_present=manual_tailoring_preview_present,
    )
    missing_inputs = [
        name for name in required_inputs if name not in available_inputs
    ]
    state_adapter_missing_inputs = [
        name
        for name, present in (
            ("job_record", job_present),
            ("relevance_result", relevance_result_present),
            ("jd_intelligence_result", jd_intelligence_present),
            ("final_score_result", final_score_present),
            ("tailoring_opportunity_result", tailoring_opportunity_present),
        )
        if not present
    ]
    handoff_reason = router_decision["routing_reason"]
    adapter_key = _adapter_key(
        next_allowed_step=next_allowed_step,
        available_inputs=available_inputs,
        missing_inputs=missing_inputs,
    )
    agent_handoff_packet = {
        "phase": PHASE,
        "non_executable": True,
        "read_only": True,
        "advisory_only": True,
        "next_allowed_step": next_allowed_step,
        "handoff_reason": handoff_reason,
        "required_inputs_for_next_step": required_inputs,
        "available_inputs_for_next_step": available_inputs,
        "missing_inputs_for_next_step": missing_inputs,
        "allowed_agent_steps": deepcopy(
            router_decision["allowed_agent_steps"]
        ),
        "blocked_agent_steps": deepcopy(
            router_decision["blocked_agent_steps"]
        ),
        "router_decision_key": router_decision["decision_key"],
        "no_executable_callback": True,
        "no_provider_request": True,
        "no_network_request": True,
        "no_mutation_command": True,
        "no_database_write_command": True,
        "no_application_submission_command": True,
    }

    return {
        "phase": PHASE,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "workflow_state_adapter_only": True,
        "controlled_agent_router_adapter": True,
        "allowlisted_routing_only": True,
        "requires_manual_user_control": True,
        "job_present": job_present,
        "relevance_result_present": relevance_result_present,
        "jd_intelligence_present": jd_intelligence_present,
        "final_score_present": final_score_present,
        "tailoring_opportunity_present": tailoring_opportunity_present,
        "manual_tailoring_preview_present": manual_tailoring_preview_present,
        "current_state": deepcopy(current_state),
        "state_adapter_findings": {
            "job_identifiers": _job_summary(safe_job),
            "final_score": final_score,
            "manual_tailoring_preview_metadata_only": (
                manual_tailoring_preview_present
            ),
            "router_called": True,
            "stage_execution_performed": False,
        },
        "state_adapter_missing_inputs": state_adapter_missing_inputs,
        "router_decision": deepcopy(router_decision),
        "agent_handoff_packet": agent_handoff_packet,
        "next_allowed_step": next_allowed_step,
        "handoff_reason": handoff_reason,
        "required_inputs_for_next_step": required_inputs,
        "available_inputs_for_next_step": available_inputs,
        "missing_inputs_for_next_step": missing_inputs,
        "adapter_key": adapter_key,
        "no_llm_calls": True,
        "llm_call_performed": False,
        "no_provider_calls": True,
        "provider_call_performed": False,
        "no_network_calls": True,
        "network_call_performed": False,
        "dispatch_performed": False,
        "stage_execution_performed": False,
        "tailoring_runtime_call_performed": False,
        "ai_tailoring_generation_performed": False,
        "real_tailoring_output_created": False,
        "resume_rewrite_performed": False,
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
        "database_write_performed": False,
        "persistence_performed": False,
        "execution_performed": False,
        "submission_performed": False,
        "auto_apply_performed": False,
        "auto_submit_performed": False,
    }
