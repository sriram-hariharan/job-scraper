"""Default-off Phase 15C evidence review for live JD intelligence."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


EVIDENCE_REVIEW_VERSION = (
    "phase-15c-live-jd-intelligence-evidence-review-v1"
)
OUTCOME_SKIPPED = "evidence_review_skipped_default_off"
OUTCOME_READY = "evidence_review_ready_for_operator_review"


def live_jd_intelligence_evidence_review_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "evidence_review_only": True,
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


def _phase14_summary(evidence: dict[str, Any]) -> dict[str, Any]:
    llmops = _plain_dict(evidence.get("llmops_metadata"))
    readback = _plain_dict(evidence.get("readback"))
    provider_name = _text(
        evidence.get("provider_name")
        or llmops.get("model_provider")
        or readback.get("provider_name")
    )
    model_name = _text(
        evidence.get("model_name")
        or llmops.get("model_name")
        or readback.get("model_name")
    )
    token_usage = _plain_dict(evidence.get("token_usage"))
    token_usage_recorded = bool(token_usage) or any(
        llmops.get(key) is not None
        for key in ("input_tokens", "output_tokens", "total_tokens")
    )
    return {
        "evidence_supplied": bool(evidence),
        "provider_call_attempted": (
            evidence.get("provider_call_attempted") is True
            or llmops.get("provider_call_attempted") is True
            or readback.get("provider_call_attempted") is True
        ),
        "provider_call_succeeded": (
            evidence.get("provider_call_succeeded") is True
            or llmops.get("provider_call_succeeded") is True
            or readback.get("provider_call_succeeded") is True
        ),
        "fallback_not_used": (
            bool(evidence)
            and evidence.get("fallback_used") is False
        ),
        "structured_output_validated": (
            evidence.get("structured_output_validated") is True
            or readback.get("structured_output_validated") is True
        ),
        "schema_validation_valid": (
            _text(llmops.get("schema_validation_status")) == "valid"
            or _text(readback.get("source_validation_status")) == "valid"
        ),
        "mutation_authority_remained_false": (
            bool(evidence)
            and evidence.get("mutation_authorized") is False
        ),
        "mutation_authorized_agent_count_zero": (
            bool(evidence)
            and evidence.get("mutation_authorized_agent_count") == 0
        ),
        "jd_source_was_manual_single_job": (
            evidence.get("one_job_only") is True
            and evidence.get("jd_only") is True
            and evidence.get("manual_command_enabled") is True
        ),
        "provider_model_recorded": bool(provider_name and model_name),
        "token_usage_recorded": token_usage_recorded,
        "provider_name": provider_name,
        "model_name": model_name,
        "llmops_metadata": llmops,
        "readback": readback,
        "source_evidence": evidence,
    }


def build_live_jd_intelligence_evidence_review(
    *,
    enabled: bool = False,
    phase15a_expansion_plan: dict[str, Any] | None = None,
    phase15b_review_readiness: dict[str, Any] | None = None,
    phase14_manual_canary_evidence: dict[str, Any] | None = None,
    evidence_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Review supplied evidence without reading files or enabling runtime."""

    phase14 = _plain_dict(phase14_manual_canary_evidence)
    phase15a = _plain_dict(phase15a_expansion_plan)
    phase15b = _plain_dict(phase15b_review_readiness)
    context = _plain_dict(evidence_context)
    phase14_summary = _phase14_summary(phase14)
    phase15a_planning = _plain_dict(
        phase15a.get("phase15a_expansion_planning")
    )
    phase15b_review = _plain_dict(
        phase15b.get("phase15b_review_readiness")
    )
    phase15b_forbidden = _plain_dict(
        phase15b.get("forbidden_mutation_and_application_paths")
    )
    checks = {
        "phase14_evidence_supplied": bool(phase14),
        "provider_call_attempted": (
            phase14_summary["provider_call_attempted"]
        ),
        "provider_call_succeeded": (
            phase14_summary["provider_call_succeeded"]
        ),
        "fallback_not_used": phase14_summary["fallback_not_used"],
        "structured_output_validated": (
            phase14_summary["structured_output_validated"]
        ),
        "schema_validation_valid": (
            phase14_summary["schema_validation_valid"]
        ),
        "mutation_authority_remained_false": (
            phase14_summary["mutation_authority_remained_false"]
        ),
        "mutation_authorized_agent_count_zero": (
            phase14_summary["mutation_authorized_agent_count_zero"]
        ),
        "jd_source_was_manual_single_job": (
            phase14_summary["jd_source_was_manual_single_job"]
        ),
        "provider_model_recorded": (
            phase14_summary["provider_model_recorded"]
        ),
        "token_usage_recorded": (
            phase14_summary["token_usage_recorded"]
        ),
        "phase15a_plan_supplied": bool(phase15a),
        "phase15a_planning_only": (
            phase15a.get("planning_only") is True
        ),
        "phase15a_execution_not_authorized": (
            bool(phase15a)
            and phase15a.get("execution_authorized") is False
        ),
        "phase15b_review_readiness_supplied": bool(phase15b),
        "phase15b_review_only": (
            phase15b.get("review_readiness_only") is True
        ),
        "phase15b_rollout_not_authorized": (
            bool(phase15b)
            and phase15b.get("rollout_authorized") is False
        ),
        "scoring_influence_blocked": (
            phase15b_forbidden.get("scoring_influence_allowed") is False
        ),
        "ranking_influence_blocked": (
            phase15b_forbidden.get("ranking_influence_allowed") is False
        ),
        "queue_influence_blocked": (
            phase15b_forbidden.get("queue_influence_allowed") is False
        ),
        "resume_mutation_blocked": (
            phase15b_forbidden.get("resume_mutation_allowed") is False
        ),
        "application_execution_blocked": (
            phase15b_forbidden.get("application_execution_allowed")
            is False
        ),
        "application_submission_blocked": (
            phase15b_forbidden.get("application_submission_allowed")
            is False
        ),
    }
    return {
        "evidence_review_version": EVIDENCE_REVIEW_VERSION,
        "evidence_review_enabled": enabled is True,
        "review_outcome": (
            OUTCOME_READY if enabled is True else OUTCOME_SKIPPED
        ),
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "evidence_review_only": True,
        "jd_intelligence_only": True,
        "execution_authorized": False,
        "rollout_authorized": False,
        "phase14_manual_canary_evidence_summary": phase14_summary,
        "phase15a_expansion_plan_summary": {
            "plan_supplied": bool(phase15a),
            "plan_status": _text(phase15a.get("plan_status")),
            "planning_only": phase15a.get("planning_only") is True,
            "execution_authorized": (
                phase15a.get("execution_authorized") is True
            ),
            "phase15a_expansion_planning": phase15a_planning,
            "source_plan": phase15a,
        },
        "phase15b_review_readiness_summary": {
            "review_readiness_supplied": bool(phase15b),
            "readiness_status": _text(
                phase15b.get("readiness_status")
            ),
            "review_readiness_only": (
                phase15b.get("review_readiness_only") is True
            ),
            "rollout_authorized": (
                phase15b.get("rollout_authorized") is True
            ),
            "phase15b_review_readiness": phase15b_review,
            "source_readiness": phase15b,
        },
        "evidence_review_checks": checks,
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
        "evidence_context": context,
        "next_safe_step": (
            "operator_review_phase15c_evidence_without_execution"
            if enabled is True
            else "enable_phase15c_evidence_review_only"
        ),
        "safety_metadata": (
            live_jd_intelligence_evidence_review_safety_metadata()
        ),
    }
