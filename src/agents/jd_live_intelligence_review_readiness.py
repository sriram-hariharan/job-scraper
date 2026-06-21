"""Default-off Phase 15B review readiness for live JD intelligence."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


READINESS_VERSION = (
    "phase-15b-live-jd-intelligence-review-readiness-v1"
)
STATUS_SKIPPED = "live_jd_review_readiness_skipped_default_off"
STATUS_READY = "live_jd_review_readiness_ready_for_review"


def live_jd_intelligence_review_readiness_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "review_readiness_only": True,
        "jd_intelligence_only": True,
        "provider_execution_added": False,
        "provider_client_constructed": False,
        "provider_sdk_imported": False,
        "environment_secrets_read": False,
        "network_calls_made": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_mutate_resume": False,
        "did_execute_application": False,
        "did_submit_application": False,
    }


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def build_live_jd_intelligence_review_readiness(
    *,
    enabled: bool = False,
    phase15a_expansion_plan: dict[str, Any] | None = None,
    review_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Summarize Phase 15A for review without enabling execution."""

    plan = _plain_dict(phase15a_expansion_plan)
    context = _plain_dict(review_context)
    phase14 = _plain_dict(plan.get("phase14_manual_canary_evidence"))
    phase15a = _plain_dict(plan.get("phase15a_expansion_planning"))
    forbidden15a = _plain_dict(
        plan.get("forbidden_mutation_and_application_paths")
    )
    phase15a_summary = {
        "plan_supplied": bool(plan),
        "plan_enabled": plan.get("plan_enabled") is True,
        "plan_status": str(plan.get("plan_status") or ""),
        "planning_only": plan.get("planning_only") is True,
        "execution_authorized": plan.get("execution_authorized") is True,
        "jd_intelligence_only": (
            phase15a.get("agent_name") == "jd_intelligence"
        ),
        "shadow_only": phase15a.get("shadow_only") is True,
        "advisory_only": phase15a.get("advisory_only") is True,
        "provider_execution_added": (
            phase15a.get("provider_execution_added") is True
        ),
        "phase14_manual_canary_evidence": phase14,
        "phase15a_expansion_planning": phase15a,
        "forbidden_paths": forbidden15a,
        "source_plan": plan,
    }
    review_checks = {
        "phase15a_plan_reviewed": bool(plan),
        "phase14_canary_evidence_reviewed": bool(phase14),
        "jd_only_scope_preserved": (
            phase15a.get("agent_name") == "jd_intelligence"
        ),
        "shadow_only_scope_preserved": (
            phase15a.get("shadow_only") is True
        ),
        "one_job_manual_evidence_boundary_preserved": (
            phase14.get("source_phase")
            == "phase_14_manual_one_job_canary"
        ),
        "structured_output_validation_preserved": (
            phase14.get("structured_output_validated") is True
        ),
        "deterministic_fallback_preserved": (
            phase15a.get(
                "existing_deterministic_fallback_required"
            )
            is True
        ),
        "llmops_readback_fields_preserved": (
            phase15a.get("existing_llmops_readback_required") is True
        ),
        "runtime_cost_limits_preserved": (
            "runtime_and_cost_limits_confirmed"
            in phase15a.get("go_no_go_requirements", [])
        ),
        "rollback_off_switch_requirements_preserved": (
            "rollback_and_off_switch_validation"
            in phase15a.get("expansion_candidates", [])
        ),
        "zero_mutation_authority_preserved": (
            plan.get("mutation_authorized") is False
            and plan.get("mutation_authorized_agent_count") == 0
        ),
    }
    return {
        "readiness_version": READINESS_VERSION,
        "review_readiness_enabled": enabled is True,
        "readiness_status": (
            STATUS_READY if enabled is True else STATUS_SKIPPED
        ),
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "review_readiness_only": True,
        "jd_intelligence_only": True,
        "execution_authorized": False,
        "rollout_authorized": False,
        "phase15a_plan_summary": phase15a_summary,
        "phase15b_review_readiness": {
            "scope": "live_jd_intelligence_review_readiness",
            "review_checks": review_checks,
            "decision_boundaries": {
                "prefilter_relevance_is_separate": True,
                "jd_intelligence_evaluation_is_separate": True,
                "final_application_scoring_is_separate": True,
                "prefilter_output_modified": False,
                "jd_evaluation_execution_added": False,
                "final_scoring_input_modified": False,
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
        "review_context": context,
        "next_safe_step": (
            "review_phase15b_jd_readiness_without_execution"
            if enabled is True
            else "enable_phase15b_review_only"
        ),
        "safety_metadata": (
            live_jd_intelligence_review_readiness_safety_metadata()
        ),
    }
