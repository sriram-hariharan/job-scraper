"""Default-off Phase 15D operator decision review for live JD."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


OPERATOR_DECISION_VERSION = (
    "phase-15d-live-jd-intelligence-operator-decision-v1"
)
STATUS_SKIPPED = "operator_decision_skipped_default_off"
STATUS_READY = "operator_decision_ready_for_human_review"


def live_jd_intelligence_operator_decision_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "operator_decision_review_only": True,
        "jd_intelligence_only": True,
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


def build_live_jd_intelligence_operator_decision(
    *,
    enabled: bool = False,
    phase15c_evidence_review: dict[str, Any] | None = None,
    operator_decision_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Prepare human review metadata without recording an approval."""

    evidence_review = _plain_dict(phase15c_evidence_review)
    context = _plain_dict(operator_decision_context)
    phase15c_checks = _plain_dict(
        evidence_review.get("evidence_review_checks")
    )
    phase15c_boundaries = _plain_dict(
        evidence_review.get("decision_boundaries")
    )
    phase15c_forbidden = _plain_dict(
        evidence_review.get(
            "forbidden_mutation_and_application_paths"
        )
    )
    checks = {
        "phase15c_evidence_review_supplied": bool(evidence_review),
        "phase15c_evidence_review_only": (
            evidence_review.get("evidence_review_only") is True
        ),
        "phase15c_execution_not_authorized": (
            bool(evidence_review)
            and evidence_review.get("execution_authorized") is False
        ),
        "phase15c_rollout_not_authorized": (
            bool(evidence_review)
            and evidence_review.get("rollout_authorized") is False
        ),
        "phase15c_mutation_not_authorized": (
            bool(evidence_review)
            and evidence_review.get("mutation_authorized") is False
        ),
        "phase15c_provider_call_succeeded": (
            phase15c_checks.get("provider_call_succeeded") is True
        ),
        "phase15c_structured_output_validated": (
            phase15c_checks.get("structured_output_validated") is True
        ),
        "phase15c_schema_validation_valid": (
            phase15c_checks.get("schema_validation_valid") is True
        ),
        "phase15c_fallback_not_used": (
            phase15c_checks.get("fallback_not_used") is True
        ),
        "phase15c_zero_mutation_authority_preserved": (
            phase15c_checks.get(
                "mutation_authority_remained_false"
            )
            is True
            and phase15c_checks.get(
                "mutation_authorized_agent_count_zero"
            )
            is True
        ),
        "scoring_influence_blocked": (
            phase15c_forbidden.get("scoring_influence_allowed")
            is False
        ),
        "ranking_influence_blocked": (
            phase15c_forbidden.get("ranking_influence_allowed")
            is False
        ),
        "queue_influence_blocked": (
            phase15c_forbidden.get("queue_influence_allowed") is False
        ),
        "resume_mutation_blocked": (
            phase15c_forbidden.get("resume_mutation_allowed") is False
        ),
        "application_execution_blocked": (
            phase15c_forbidden.get("application_execution_allowed")
            is False
        ),
        "application_submission_blocked": (
            phase15c_forbidden.get("application_submission_allowed")
            is False
        ),
        "prefilter_relevance_separation_preserved": (
            phase15c_boundaries.get(
                "prefilter_relevance_is_separate"
            )
            is True
        ),
        "jd_intelligence_evaluation_separation_preserved": (
            phase15c_boundaries.get(
                "jd_intelligence_evaluation_is_separate"
            )
            is True
        ),
        "final_application_scoring_separation_preserved": (
            phase15c_boundaries.get(
                "final_application_scoring_is_separate"
            )
            is True
        ),
        "operator_context_supplied": bool(context),
    }
    return {
        "operator_decision_version": OPERATOR_DECISION_VERSION,
        "operator_decision_enabled": enabled is True,
        "operator_decision_status": (
            STATUS_READY if enabled is True else STATUS_SKIPPED
        ),
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "operator_decision_review_only": True,
        "jd_intelligence_only": True,
        "execution_authorized": False,
        "rollout_authorized": False,
        "operator_approval_recorded": False,
        "operator_approval_required_before_any_future_runtime": True,
        "phase15c_evidence_review_summary": {
            "evidence_review_supplied": bool(evidence_review),
            "review_outcome": _text(
                evidence_review.get("review_outcome")
            ),
            "evidence_review_only": (
                evidence_review.get("evidence_review_only") is True
            ),
            "execution_authorized": (
                evidence_review.get("execution_authorized") is True
            ),
            "rollout_authorized": (
                evidence_review.get("rollout_authorized") is True
            ),
            "mutation_authorized": (
                evidence_review.get("mutation_authorized") is True
            ),
            "evidence_review_checks": phase15c_checks,
            "decision_boundaries": phase15c_boundaries,
            "source_evidence_review": evidence_review,
        },
        "phase15d_operator_decision_review": {
            "scope": "live_jd_intelligence_operator_decision_review",
            "operator_decision_checks": checks,
            "decision_recording": {
                "human_review_required": True,
                "approval_recorded": False,
                "rejection_recorded": False,
                "execution_triggered": False,
                "rollout_triggered": False,
            },
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
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "operator_decision_context": context,
        "next_safe_step": (
            "human_review_phase15d_operator_decision_without_execution"
            if enabled is True
            else "enable_phase15d_operator_decision_review_only"
        ),
        "safety_metadata": (
            live_jd_intelligence_operator_decision_safety_metadata()
        ),
    }
