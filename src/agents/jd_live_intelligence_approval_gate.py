"""Default-off Phase 15E closed approval gate for live JD."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


APPROVAL_GATE_VERSION = (
    "phase-15e-live-jd-intelligence-approval-gate-v1"
)
STATUS_SKIPPED = "approval_gate_skipped_default_off"
STATUS_READY_CLOSED = "approval_gate_ready_for_review_closed"


def live_jd_intelligence_approval_gate_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "approval_gate_review_only": True,
        "approval_gate_closed": True,
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


def build_live_jd_intelligence_approval_gate(
    *,
    enabled: bool = False,
    phase15d_operator_decision: dict[str, Any] | None = None,
    approval_gate_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe a closed gate without recording or persisting approval."""

    operator_decision = _plain_dict(phase15d_operator_decision)
    context = _plain_dict(approval_gate_context)
    phase15d_review = _plain_dict(
        operator_decision.get("phase15d_operator_decision_review")
    )
    phase15d_checks = _plain_dict(
        phase15d_review.get("operator_decision_checks")
    )
    decision_recording = _plain_dict(
        phase15d_review.get("decision_recording")
    )
    phase15d_forbidden = _plain_dict(
        operator_decision.get(
            "forbidden_mutation_and_application_paths"
        )
    )
    successful_evidence_keys = (
        "phase15c_provider_call_succeeded",
        "phase15c_structured_output_validated",
        "phase15c_schema_validation_valid",
        "phase15c_fallback_not_used",
        "phase15c_zero_mutation_authority_preserved",
    )
    checks = {
        "phase15d_operator_decision_supplied": bool(operator_decision),
        "phase15d_operator_decision_review_only": (
            operator_decision.get("operator_decision_review_only")
            is True
        ),
        "phase15d_execution_not_authorized": (
            bool(operator_decision)
            and operator_decision.get("execution_authorized") is False
        ),
        "phase15d_rollout_not_authorized": (
            bool(operator_decision)
            and operator_decision.get("rollout_authorized") is False
        ),
        "phase15d_mutation_not_authorized": (
            bool(operator_decision)
            and operator_decision.get("mutation_authorized") is False
        ),
        "phase15d_operator_approval_not_recorded": (
            bool(operator_decision)
            and operator_decision.get("operator_approval_recorded")
            is False
        ),
        "phase15d_human_review_required": (
            decision_recording.get("human_review_required") is True
        ),
        "phase15d_execution_not_triggered": (
            decision_recording.get("execution_triggered") is False
        ),
        "phase15d_rollout_not_triggered": (
            decision_recording.get("rollout_triggered") is False
        ),
        "phase15d_successful_evidence_chain_present": all(
            phase15d_checks.get(key) is True
            for key in successful_evidence_keys
        ),
        "scoring_influence_blocked": (
            phase15d_forbidden.get("scoring_influence_allowed")
            is False
        ),
        "ranking_influence_blocked": (
            phase15d_forbidden.get("ranking_influence_allowed")
            is False
        ),
        "queue_influence_blocked": (
            phase15d_forbidden.get("queue_influence_allowed") is False
        ),
        "resume_mutation_blocked": (
            phase15d_forbidden.get("resume_mutation_allowed") is False
        ),
        "application_execution_blocked": (
            phase15d_forbidden.get("application_execution_allowed")
            is False
        ),
        "application_submission_blocked": (
            phase15d_forbidden.get("application_submission_allowed")
            is False
        ),
        "approval_gate_context_supplied": bool(context),
        "approval_gate_remains_closed": True,
        "future_runtime_requires_separate_explicit_phase": True,
    }
    return {
        "approval_gate_version": APPROVAL_GATE_VERSION,
        "approval_gate_enabled": enabled is True,
        "approval_gate_status": (
            STATUS_READY_CLOSED if enabled is True else STATUS_SKIPPED
        ),
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "approval_gate_review_only": True,
        "approval_gate_open": False,
        "jd_intelligence_only": True,
        "execution_authorized": False,
        "rollout_authorized": False,
        "approval_recorded": False,
        "operator_approval_recorded": False,
        "operator_approval_required_before_any_future_runtime": True,
        "phase15d_operator_decision_summary": {
            "operator_decision_supplied": bool(operator_decision),
            "operator_decision_status": _text(
                operator_decision.get("operator_decision_status")
            ),
            "operator_decision_review_only": (
                operator_decision.get("operator_decision_review_only")
                is True
            ),
            "execution_authorized": (
                operator_decision.get("execution_authorized") is True
            ),
            "rollout_authorized": (
                operator_decision.get("rollout_authorized") is True
            ),
            "mutation_authorized": (
                operator_decision.get("mutation_authorized") is True
            ),
            "operator_approval_recorded": (
                operator_decision.get("operator_approval_recorded")
                is True
            ),
            "operator_decision_checks": phase15d_checks,
            "decision_recording": decision_recording,
            "source_operator_decision": operator_decision,
        },
        "phase15e_approval_gate_review": {
            "scope": "live_jd_intelligence_approval_gate_review",
            "approval_gate_checks": checks,
            "gate_state": {
                "gate_open": False,
                "approval_recorded": False,
                "operator_approval_recorded": False,
                "execution_triggered": False,
                "rollout_triggered": False,
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
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "approval_gate_context": context,
        "next_safe_step": (
            "review_phase15e_closed_approval_gate_without_execution"
            if enabled is True
            else "enable_phase15e_approval_gate_review_only"
        ),
        "safety_metadata": (
            live_jd_intelligence_approval_gate_safety_metadata()
        ),
    }
