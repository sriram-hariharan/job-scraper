"""Default-off Phase 15A plan for read-only live JD expansion."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PLAN_VERSION = "phase-15a-live-jd-intelligence-expansion-plan-v1"
STATUS_SKIPPED = "live_jd_expansion_plan_skipped_default_off"
STATUS_READY = "live_jd_expansion_plan_ready_for_review"


def live_jd_intelligence_expansion_plan_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "jd_intelligence_only": True,
        "planning_only": True,
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


def build_live_jd_intelligence_expansion_plan(
    *,
    enabled: bool = False,
    phase14_manual_canary_evidence: dict[str, Any] | None = None,
    planning_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe expansion requirements without executing provider runtime."""

    evidence = _plain_dict(phase14_manual_canary_evidence)
    context = _plain_dict(planning_context)
    evidence_summary = {
        "evidence_supplied": bool(evidence),
        "manual_one_job_canary_succeeded": (
            evidence.get("provider_call_succeeded") is True
        ),
        "structured_output_validated": (
            evidence.get("structured_output_validated") is True
        ),
        "fallback_not_used": evidence.get("fallback_used") is False,
        "mutation_authority_remained_false": (
            evidence.get("mutation_authorized") is False
        ),
        "shadow_only_preserved": evidence.get("shadow_only") is True,
        "source_phase": "phase_14_manual_one_job_canary",
        "source_evidence": evidence,
    }
    return {
        "plan_version": PLAN_VERSION,
        "plan_enabled": enabled is True,
        "plan_status": (
            STATUS_READY if enabled is True else STATUS_SKIPPED
        ),
        "default_off": True,
        "planning_only": True,
        "execution_authorized": False,
        "phase14_manual_canary_evidence": evidence_summary,
        "phase15a_expansion_planning": {
            "scope": "read_only_live_jd_intelligence_expansion",
            "agent_name": "jd_intelligence",
            "shadow_only": True,
            "advisory_only": True,
            "provider_execution_added": False,
            "existing_external_adapter_path_unchanged": True,
            "existing_config_gate_required": True,
            "existing_structured_validation_required": True,
            "existing_deterministic_fallback_required": True,
            "existing_llmops_readback_required": True,
            "expansion_candidates": [
                "repeatable_manual_jd_only_canary_evidence",
                "bounded_read_only_jd_analysis_volume",
                "provider_quality_and_cost_observability",
                "rollback_and_off_switch_validation",
            ],
            "go_no_go_requirements": [
                "phase14_evidence_reviewed",
                "jd_only_scope_preserved",
                "shadow_only_scope_preserved",
                "zero_mutation_authority_confirmed",
                "structured_output_validation_confirmed",
                "deterministic_fallback_confirmed",
                "llmops_readback_confirmed",
                "runtime_and_cost_limits_confirmed",
            ],
        },
        "forbidden_mutation_and_application_paths": {
            "scoring_mutation_allowed": False,
            "ranking_mutation_allowed": False,
            "queue_mutation_allowed": False,
            "approval_mutation_allowed": False,
            "resume_mutation_allowed": False,
            "execution_request_allowed": False,
            "application_execution_allowed": False,
            "application_submission_allowed": False,
            "tailoring_provider_expansion_allowed": False,
            "critic_provider_expansion_allowed": False,
        },
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "planning_context": context,
        "next_safe_step": (
            "review_phase15a_read_only_jd_expansion_plan"
            if enabled is True
            else "enable_phase15a_plan_review_only"
        ),
        "safety_metadata": (
            live_jd_intelligence_expansion_plan_safety_metadata()
        ),
    }
