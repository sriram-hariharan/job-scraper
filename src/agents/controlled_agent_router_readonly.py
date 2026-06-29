"""Deterministic read-only router for controlled agent handoffs."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PHASE = "33A"
DEFAULT_SCORE_THRESHOLD = 70

ALLOWED_AGENT_STEPS = (
    "run_relevance_prefilter",
    "run_jd_intelligence",
    "run_final_application_scoring",
    "check_tailoring_opportunity",
    "prepare_manual_tailoring_preview",
    "await_manual_review",
)

BLOCKED_AGENT_STEPS = (
    "call_llm",
    "call_provider",
    "call_network",
    "dispatch_provider_request",
    "generate_ai_tailoring",
    "rewrite_resume",
    "overwrite_resume",
    "mutate_resume",
    "persist_snapshot",
    "write_database",
    "execute_application",
    "submit_application",
    "auto_apply",
    "auto_submit",
)


def _safe_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _first_present(source: dict[str, Any], names: tuple[str, ...]) -> Any:
    for name in names:
        if name in source:
            return source[name]
    return None


def _has_payload(value: Any) -> bool:
    return value not in (None, "", [], {})


def _truth_marker(value: Any, names: tuple[str, ...]) -> bool | None:
    if isinstance(value, bool):
        return value
    if not isinstance(value, dict):
        return None
    for name in names:
        marker = value.get(name)
        if isinstance(marker, bool):
            return marker
    return None


def _relevance_state(current_state: dict[str, Any]) -> tuple[bool, bool | None]:
    value = _first_present(
        current_state,
        (
            "relevance_result",
            "relevance_prefilter_result",
            "prefilter_result",
            "relevance",
            "is_relevant",
            "relevant",
        ),
    )
    if value is None:
        return False, None
    if isinstance(value, bool):
        return True, value
    if isinstance(value, dict):
        marker = _truth_marker(
            value,
            (
                "is_relevant",
                "relevant",
                "passes_prefilter",
                "prefilter_passed",
                "matched",
            ),
        )
        if marker is not None:
            return True, marker
    return True, bool(value)


def _has_jd_intelligence(current_state: dict[str, Any]) -> bool:
    value = _first_present(
        current_state,
        (
            "jd_intelligence",
            "jd_signals",
            "jd_understanding",
            "job_description_intelligence",
            "job_signals",
        ),
    )
    return _has_payload(value)


def _coerce_score(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    if isinstance(value, dict):
        for name in (
            "final_score",
            "final_application_score",
            "score",
            "application_score",
            "overall_score",
        ):
            score = value.get(name)
            if isinstance(score, (int, float)) and not isinstance(score, bool):
                return float(score)
    return None


def _final_score(current_state: dict[str, Any]) -> float | None:
    value = _first_present(
        current_state,
        (
            "final_score",
            "final_application_score",
            "application_score",
            "final_application_scoring",
            "score",
        ),
    )
    return _coerce_score(value)


def _policy_threshold(router_policy: Any) -> float:
    policy = router_policy if isinstance(router_policy, dict) else {}
    threshold = _coerce_score(
        {
            "score": policy.get(
                "final_score_threshold",
                policy.get("minimum_final_score", policy.get("threshold")),
            )
        }
    )
    return threshold if threshold is not None else float(DEFAULT_SCORE_THRESHOLD)


def _tailoring_opportunity(
    current_state: dict[str, Any],
) -> tuple[bool, bool | None]:
    value = _first_present(
        current_state,
        (
            "tailoring_opportunity",
            "tailoring_opportunity_result",
            "tailoring_agent_opportunity",
            "tailoring_opportunities",
        ),
    )
    if value is None:
        return False, None
    if isinstance(value, bool):
        return True, value
    if isinstance(value, list):
        return True, bool(value)
    if isinstance(value, dict):
        marker = _truth_marker(
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
        if marker is not None:
            return True, marker
        opportunities = value.get("opportunities")
        if isinstance(opportunities, list):
            return True, bool(opportunities)
    return True, None


def _decision_key(
    *,
    next_allowed_step: str,
    threshold: float,
    relevant: bool | None,
    final_score: float | None,
    tailoring_may_help: bool | None,
) -> str:
    return "|".join(
        (
            f"phase={PHASE}",
            f"step={next_allowed_step}",
            f"threshold={threshold:g}",
            f"relevant={relevant}",
            f"final_score={final_score}",
            f"tailoring_may_help={tailoring_may_help}",
        )
    )


def _base_payload(
    *,
    current_state: dict[str, Any],
    next_allowed_step: str,
    routing_reason: str,
    routing_inputs: dict[str, Any],
    routing_findings: dict[str, Any],
    missing_inputs: list[str],
    blocked_reasons: list[str],
    decision_key: str,
) -> dict[str, Any]:
    return {
        "phase": PHASE,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "router_only": True,
        "controlled_agent_router": True,
        "allowlisted_routing_only": True,
        "requires_manual_user_control": True,
        "current_state": deepcopy(current_state),
        "allowed_agent_steps": list(ALLOWED_AGENT_STEPS),
        "blocked_agent_steps": list(BLOCKED_AGENT_STEPS),
        "next_allowed_step": next_allowed_step,
        "routing_reason": routing_reason,
        "routing_inputs": deepcopy(routing_inputs),
        "routing_findings": deepcopy(routing_findings),
        "missing_inputs": list(missing_inputs),
        "blocked_reasons": list(blocked_reasons),
        "decision_key": decision_key,
        "no_llm_calls": True,
        "llm_call_performed": False,
        "no_provider_calls": True,
        "provider_call_performed": False,
        "no_network_calls": True,
        "network_call_performed": False,
        "dispatch_performed": False,
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


def build_controlled_agent_router_readonly_decision(
    current_state: dict[str, Any] | None = None,
    router_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Choose the next allowed agent step from a closed allowlist."""

    threshold = _policy_threshold(router_policy)
    if not isinstance(current_state, dict):
        next_allowed_step = "await_manual_review"
        routing_findings = {
            "current_state_is_dict": False,
            "threshold": threshold,
        }
        decision_key = _decision_key(
            next_allowed_step=next_allowed_step,
            threshold=threshold,
            relevant=None,
            final_score=None,
            tailoring_may_help=None,
        )
        return _base_payload(
            current_state={},
            next_allowed_step=next_allowed_step,
            routing_reason="current_state must be supplied as a dictionary",
            routing_inputs={
                "router_policy": _safe_dict(router_policy),
                "score_threshold": threshold,
            },
            routing_findings=routing_findings,
            missing_inputs=["current_state"],
            blocked_reasons=["missing or invalid current_state"],
            decision_key=decision_key,
        )

    safe_state = _safe_dict(current_state)
    relevance_present, relevant = _relevance_state(safe_state)
    has_jd_intelligence = _has_jd_intelligence(safe_state)
    final_score = _final_score(safe_state)
    opportunity_present, tailoring_may_help = _tailoring_opportunity(
        safe_state
    )

    missing_inputs: list[str] = []
    blocked_reasons: list[str] = []

    if not relevance_present:
        next_allowed_step = "run_relevance_prefilter"
        routing_reason = "no relevance prefilter result is present"
        missing_inputs.append("relevance_result")
    elif relevant is False:
        next_allowed_step = "await_manual_review"
        routing_reason = "relevance prefilter indicates the job is not relevant"
        blocked_reasons.append("job is not relevant")
    elif not has_jd_intelligence:
        next_allowed_step = "run_jd_intelligence"
        routing_reason = "job is relevant but JD intelligence is missing"
        missing_inputs.append("jd_intelligence")
    elif final_score is None:
        next_allowed_step = "run_final_application_scoring"
        routing_reason = "JD intelligence exists but final score is missing"
        missing_inputs.append("final_score")
    elif final_score < threshold:
        next_allowed_step = "await_manual_review"
        routing_reason = "final application score is below policy threshold"
        blocked_reasons.append("final score below threshold")
    elif not opportunity_present:
        next_allowed_step = "check_tailoring_opportunity"
        routing_reason = (
            "final score meets threshold but tailoring opportunity is missing"
        )
        missing_inputs.append("tailoring_opportunity")
    elif tailoring_may_help is True:
        next_allowed_step = "prepare_manual_tailoring_preview"
        routing_reason = "tailoring opportunity indicates tailoring may help"
    else:
        next_allowed_step = "await_manual_review"
        routing_reason = (
            "safe analysis is complete and no helpful tailoring action is "
            "available"
        )
        if tailoring_may_help is False:
            blocked_reasons.append("tailoring opportunity does not help")

    routing_findings = {
        "current_state_is_dict": True,
        "relevance_result_present": relevance_present,
        "relevance_indicates_relevant": relevant,
        "jd_intelligence_present": has_jd_intelligence,
        "final_score": final_score,
        "score_threshold": threshold,
        "final_score_meets_threshold": (
            final_score is not None and final_score >= threshold
        ),
        "tailoring_opportunity_present": opportunity_present,
        "tailoring_may_help": tailoring_may_help,
    }
    decision_key = _decision_key(
        next_allowed_step=next_allowed_step,
        threshold=threshold,
        relevant=relevant,
        final_score=final_score,
        tailoring_may_help=tailoring_may_help,
    )
    return _base_payload(
        current_state=safe_state,
        next_allowed_step=next_allowed_step,
        routing_reason=routing_reason,
        routing_inputs={
            "router_policy": _safe_dict(router_policy),
            "score_threshold": threshold,
            "recognized_state_fields": sorted(safe_state.keys()),
        },
        routing_findings=routing_findings,
        missing_inputs=missing_inputs,
        blocked_reasons=blocked_reasons,
        decision_key=decision_key,
    )
