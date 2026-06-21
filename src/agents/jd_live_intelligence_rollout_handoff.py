"""Default-off Phase 15F rollout handoff review for live JD."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


ROLLOUT_HANDOFF_VERSION = (
    "phase-15f-live-jd-intelligence-rollout-handoff-v1"
)
STATUS_SKIPPED = "rollout_handoff_skipped_default_off"
STATUS_READY = "rollout_handoff_ready_for_review_no_runtime"


def live_jd_intelligence_rollout_handoff_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "rollout_handoff_review_only": True,
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


def build_live_jd_intelligence_rollout_handoff(
    *,
    enabled: bool = False,
    phase15e_approval_gate: dict[str, Any] | None = None,
    rollout_handoff_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a review-only handoff without opening the approval gate."""

    approval_gate = _plain_dict(phase15e_approval_gate)
    context = _plain_dict(rollout_handoff_context)
    phase15e_review = _plain_dict(
        approval_gate.get("phase15e_approval_gate_review")
    )
    phase15e_checks = _plain_dict(
        phase15e_review.get("approval_gate_checks")
    )
    gate_state = _plain_dict(phase15e_review.get("gate_state"))
    phase15e_forbidden = _plain_dict(
        approval_gate.get("forbidden_mutation_and_application_paths")
    )
    boundaries = _plain_dict(
        approval_gate.get("decision_boundaries")
    )
    checks = {
        "phase15e_approval_gate_supplied": bool(approval_gate),
        "phase15e_approval_gate_review_only": (
            approval_gate.get("approval_gate_review_only") is True
        ),
        "phase15e_approval_gate_closed": (
            bool(approval_gate)
            and approval_gate.get("approval_gate_open") is False
            and gate_state.get("gate_open") is False
        ),
        "phase15e_execution_not_authorized": (
            bool(approval_gate)
            and approval_gate.get("execution_authorized") is False
        ),
        "phase15e_rollout_not_authorized": (
            bool(approval_gate)
            and approval_gate.get("rollout_authorized") is False
        ),
        "phase15e_mutation_not_authorized": (
            bool(approval_gate)
            and approval_gate.get("mutation_authorized") is False
        ),
        "phase15e_approval_not_recorded": (
            bool(approval_gate)
            and approval_gate.get("approval_recorded") is False
        ),
        "phase15e_operator_approval_not_recorded": (
            bool(approval_gate)
            and approval_gate.get("operator_approval_recorded") is False
        ),
        "phase15e_future_runtime_requires_explicit_phase": (
            phase15e_checks.get(
                "future_runtime_requires_separate_explicit_phase"
            )
            is True
        ),
        "successful_review_chain_present": (
            phase15e_checks.get(
                "phase15d_successful_evidence_chain_present"
            )
            is True
        ),
        "scoring_influence_blocked": (
            phase15e_forbidden.get("scoring_influence_allowed")
            is False
        ),
        "ranking_influence_blocked": (
            phase15e_forbidden.get("ranking_influence_allowed")
            is False
        ),
        "queue_influence_blocked": (
            phase15e_forbidden.get("queue_influence_allowed") is False
        ),
        "resume_mutation_blocked": (
            phase15e_forbidden.get("resume_mutation_allowed") is False
        ),
        "application_execution_blocked": (
            phase15e_forbidden.get("application_execution_allowed")
            is False
        ),
        "application_submission_blocked": (
            phase15e_forbidden.get("application_submission_allowed")
            is False
        ),
        "prefilter_relevance_separation_preserved": (
            boundaries.get("prefilter_relevance_is_separate") is True
        ),
        "jd_intelligence_evaluation_separation_preserved": (
            boundaries.get(
                "jd_intelligence_evaluation_is_separate"
            )
            is True
        ),
        "final_application_scoring_separation_preserved": (
            boundaries.get(
                "final_application_scoring_is_separate"
            )
            is True
        ),
        "rollout_handoff_context_supplied": bool(context),
    }
    return {
        "rollout_handoff_version": ROLLOUT_HANDOFF_VERSION,
        "rollout_handoff_enabled": enabled is True,
        "rollout_handoff_status": (
            STATUS_READY if enabled is True else STATUS_SKIPPED
        ),
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "rollout_handoff_review_only": True,
        "jd_intelligence_only": True,
        "approval_gate_open": False,
        "approval_recorded": False,
        "operator_approval_recorded": False,
        "execution_authorized": False,
        "rollout_authorized": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "future_runtime_requires_separate_explicit_phase": True,
        "phase15e_approval_gate_summary": {
            "approval_gate_supplied": bool(approval_gate),
            "approval_gate_status": _text(
                approval_gate.get("approval_gate_status")
            ),
            "approval_gate_review_only": (
                approval_gate.get("approval_gate_review_only") is True
            ),
            "approval_gate_open": (
                approval_gate.get("approval_gate_open") is True
            ),
            "execution_authorized": (
                approval_gate.get("execution_authorized") is True
            ),
            "rollout_authorized": (
                approval_gate.get("rollout_authorized") is True
            ),
            "mutation_authorized": (
                approval_gate.get("mutation_authorized") is True
            ),
            "approval_recorded": (
                approval_gate.get("approval_recorded") is True
            ),
            "operator_approval_recorded": (
                approval_gate.get("operator_approval_recorded") is True
            ),
            "approval_gate_checks": phase15e_checks,
            "gate_state": gate_state,
            "source_approval_gate": approval_gate,
        },
        "phase15f_rollout_handoff_review": {
            "scope": "live_jd_intelligence_rollout_handoff_review",
            "rollout_handoff_checks": checks,
            "handoff_state": {
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
        "rollout_handoff_context": context,
        "next_safe_step": (
            "review_phase15f_rollout_handoff_without_runtime"
            if enabled is True
            else "enable_phase15f_rollout_handoff_review_only"
        ),
        "safety_metadata": (
            live_jd_intelligence_rollout_handoff_safety_metadata()
        ),
    }
