"""Default-off Phase 15G wrap review for live JD intelligence."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PHASE_WRAP_VERSION = "phase-15g-live-jd-intelligence-wrap-v1"
STATUS_SKIPPED = "phase15_wrap_skipped_default_off"
STATUS_READY = "phase15_wrap_ready_for_review_no_runtime"


def live_jd_intelligence_phase_wrap_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "phase_wrap_review_only": True,
        "approval_gate_closed": True,
        "jd_intelligence_only": True,
        "future_runtime_requires_separate_explicit_phase": True,
        "provider_execution_added": False,
        "provider_client_constructed": False,
        "provider_sdk_imported": False,
        "environment_secrets_read": False,
        "network_calls_made": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_read_files": False,
        "did_write_files": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_mutate_resume": False,
        "did_execute_application": False,
        "did_submit_application": False,
    }


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _text(value: Any) -> str:
    return str(value or "").strip()


def _phase_summary(
    payload: dict[str, Any],
    *,
    status_key: str,
    review_only_key: str,
) -> dict[str, Any]:
    return {
        "supplied": bool(payload),
        "status": _text(payload.get(status_key)),
        "review_only": payload.get(review_only_key) is True,
        "execution_authorized": (
            payload.get("execution_authorized") is True
        ),
        "rollout_authorized": (
            payload.get("rollout_authorized") is True
        ),
        "mutation_authorized": (
            payload.get("mutation_authorized") is True
        ),
        "source_payload": payload,
    }


def build_live_jd_intelligence_phase_wrap(
    *,
    enabled: bool = False,
    phase15a_expansion_plan: dict[str, Any] | None = None,
    phase15b_review_readiness: dict[str, Any] | None = None,
    phase15c_evidence_review: dict[str, Any] | None = None,
    phase15d_operator_decision: dict[str, Any] | None = None,
    phase15e_approval_gate: dict[str, Any] | None = None,
    phase15f_rollout_handoff: dict[str, Any] | None = None,
    phase_wrap_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize Phase 15 without authorizing approval or runtime."""

    phase15a = _plain_dict(phase15a_expansion_plan)
    phase15b = _plain_dict(phase15b_review_readiness)
    phase15c = _plain_dict(phase15c_evidence_review)
    phase15d = _plain_dict(phase15d_operator_decision)
    phase15e = _plain_dict(phase15e_approval_gate)
    phase15f = _plain_dict(phase15f_rollout_handoff)
    context = _plain_dict(phase_wrap_context)
    phase15f_boundaries = _plain_dict(
        phase15f.get("decision_boundaries")
    )
    phases = (phase15a, phase15b, phase15c, phase15d, phase15e, phase15f)
    summaries = {
        "phase15a": _phase_summary(
            phase15a,
            status_key="plan_status",
            review_only_key="planning_only",
        ),
        "phase15b": _phase_summary(
            phase15b,
            status_key="readiness_status",
            review_only_key="review_readiness_only",
        ),
        "phase15c": _phase_summary(
            phase15c,
            status_key="review_outcome",
            review_only_key="evidence_review_only",
        ),
        "phase15d": _phase_summary(
            phase15d,
            status_key="operator_decision_status",
            review_only_key="operator_decision_review_only",
        ),
        "phase15e": _phase_summary(
            phase15e,
            status_key="approval_gate_status",
            review_only_key="approval_gate_review_only",
        ),
        "phase15f": _phase_summary(
            phase15f,
            status_key="rollout_handoff_status",
            review_only_key="rollout_handoff_review_only",
        ),
    }
    checks = {
        "phase15a_supplied": bool(phase15a),
        "phase15b_supplied": bool(phase15b),
        "phase15c_supplied": bool(phase15c),
        "phase15d_supplied": bool(phase15d),
        "phase15e_supplied": bool(phase15e),
        "phase15f_supplied": bool(phase15f),
        "phase15a_planning_only": (
            phase15a.get("planning_only") is True
        ),
        "phase15b_review_only": (
            phase15b.get("review_readiness_only") is True
        ),
        "phase15c_evidence_review_only": (
            phase15c.get("evidence_review_only") is True
        ),
        "phase15d_operator_decision_review_only": (
            phase15d.get("operator_decision_review_only") is True
        ),
        "phase15e_approval_gate_review_only": (
            phase15e.get("approval_gate_review_only") is True
        ),
        "phase15f_rollout_handoff_review_only": (
            phase15f.get("rollout_handoff_review_only") is True
        ),
        "phase15e_approval_gate_closed": (
            bool(phase15e)
            and phase15e.get("approval_gate_open") is False
        ),
        "phase15f_approval_gate_closed": (
            bool(phase15f)
            and phase15f.get("approval_gate_open") is False
        ),
        "no_phase_authorized_execution": (
            all(item.get("execution_authorized") is not True for item in phases)
        ),
        "no_phase_authorized_rollout": (
            all(item.get("rollout_authorized") is not True for item in phases)
        ),
        "no_phase_authorized_mutation": (
            all(item.get("mutation_authorized") is not True for item in phases)
        ),
        "no_phase_recorded_approval": (
            phase15d.get("operator_approval_recorded") is False
            and phase15e.get("approval_recorded") is False
            and phase15e.get("operator_approval_recorded") is False
            and phase15f.get("approval_recorded") is False
            and phase15f.get("operator_approval_recorded") is False
        ),
        "future_runtime_requires_separate_explicit_phase": (
            phase15f.get(
                "future_runtime_requires_separate_explicit_phase"
            )
            is True
        ),
        "prefilter_relevance_separation_preserved": (
            phase15f_boundaries.get(
                "prefilter_relevance_is_separate"
            )
            is True
        ),
        "jd_intelligence_evaluation_separation_preserved": (
            phase15f_boundaries.get(
                "jd_intelligence_evaluation_is_separate"
            )
            is True
        ),
        "final_application_scoring_separation_preserved": (
            phase15f_boundaries.get(
                "final_application_scoring_is_separate"
            )
            is True
        ),
        "phase_wrap_context_supplied": bool(context),
    }
    return {
        "phase_wrap_version": PHASE_WRAP_VERSION,
        "phase_wrap_enabled": enabled is True,
        "phase_wrap_status": (
            STATUS_READY if enabled is True else STATUS_SKIPPED
        ),
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "phase_wrap_review_only": True,
        "approval_gate_closed": True,
        "jd_intelligence_only": True,
        "approval_gate_open": False,
        "approval_recorded": False,
        "operator_approval_recorded": False,
        "execution_authorized": False,
        "rollout_authorized": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "future_runtime_requires_separate_explicit_phase": True,
        "phase15a_to_phase15f_summaries": summaries,
        "phase15g_wrap_review": {
            "scope": "live_jd_intelligence_phase_wrap_review",
            "phase_wrap_checks": checks,
            "wrap_state": {
                "approval_gate_open": False,
                "approval_recorded": False,
                "operator_approval_recorded": False,
                "execution_authorized": False,
                "rollout_authorized": False,
                "mutation_authorized": False,
                "future_runtime_authorized": False,
            },
        },
        "decision_boundaries": {
            "prefilter_relevance_is_separate": True,
            "jd_intelligence_evaluation_is_separate": True,
            "final_application_scoring_is_separate": True,
            "prefilter_output_modified": False,
            "jd_evaluation_execution_added": False,
            "final_scoring_input_modified": False,
        },
        "forbidden_mutation_and_application_paths": {
            "broader_provider_expansion_allowed": False,
            "tailoring_expansion_allowed": False,
            "critic_expansion_allowed": False,
            "scoring_influence_allowed": False,
            "ranking_influence_allowed": False,
            "queue_influence_allowed": False,
            "approval_mutation_allowed": False,
            "resume_mutation_allowed": False,
            "execution_request_allowed": False,
            "application_execution_allowed": False,
            "application_submission_allowed": False,
        },
        "phase_wrap_context": context,
        "next_safe_step": (
            "review_phase15g_wrap_without_runtime"
            if enabled is True
            else "enable_phase15g_wrap_review_only"
        ),
        "safety_metadata": (
            live_jd_intelligence_phase_wrap_safety_metadata()
        ),
    }
