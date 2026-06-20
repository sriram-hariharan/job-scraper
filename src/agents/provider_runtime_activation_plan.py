"""Default-off activation plan for the first real shadow provider path."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PLAN_VERSION = "phase-12a-provider-runtime-activation-plan-v1"
STATUS_SKIPPED = "activation_plan_skipped_default_off"
STATUS_READY = "activation_plan_ready_for_review"
FIRST_ACTIVATION_AGENT = "jd_intelligence"
DEFERRED_AGENTS = ("tailoring_suggestion", "critic_guardrail")


def provider_runtime_activation_plan_safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "planning_only": True,
        "shadow_only": True,
        "provider_calls_made": False,
        "network_calls_made": False,
        "embeddings_created": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_create_approval": False,
        "did_mutate_approval": False,
        "did_mutate_resume": False,
        "did_write_resume_draft": False,
        "did_write_cover_letter_draft": False,
        "did_create_execution_request": False,
        "did_create_execution_launch_request": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "api_route_added": False,
        "ui_action_added": False,
        "pipeline_stage_added": False,
        "mutation_authorized": False,
    }


def build_provider_runtime_activation_plan(
    *,
    enabled: bool = False,
    planning_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return the reviewed activation sequence without executing providers."""

    context = (
        deepcopy(planning_context)
        if isinstance(planning_context, dict)
        else {}
    )
    status = STATUS_READY if enabled is True else STATUS_SKIPPED
    next_safe_step = (
        "review_jd_intelligence_shadow_smoke_plan"
        if enabled is True
        else "enable_activation_plan_review_only"
    )
    return {
        "plan_version": PLAN_VERSION,
        "activation_plan_enabled": enabled is True,
        "activation_status": status,
        "default_off": True,
        "live_provider_execution_enabled": False,
        "first_activation_agent": FIRST_ACTIVATION_AGENT,
        "first_activation_mode": "shadow_only",
        "first_activation_reason": (
            "read_only_job_description_analysis_with_no_resume_scoring_"
            "ranking_queue_or_application_mutation"
        ),
        "deferred_agent_names": list(DEFERRED_AGENTS),
        "deferred_agent_reasons": {
            "tailoring_suggestion": (
                "defer_until_jd_intelligence_shadow_runtime_is_validated"
            ),
            "critic_guardrail": (
                "defer_until_upstream_structured_handoffs_are_validated"
            ),
        },
        "explicit_configuration_required": True,
        "injected_provider_adapter_required": True,
        "injected_provider_client_required": True,
        "provider_client_constructed_internally": False,
        "shadow_only_required": True,
        "structured_output_validation_required": True,
        "deterministic_fallback_required": True,
        "llmops_metadata_required": True,
        "required_llmops_fields": [
            "provider_call_attempted",
            "provider_call_succeeded",
            "provider_call_blocked",
            "fallback_used",
            "schema_validation_status",
            "latency_ms",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "estimated_cost",
            "error_type",
        ],
        "provider_state_logging_required": [
            "attempted",
            "succeeded",
            "failed",
            "fallback",
        ],
        "rollback": {
            "off_switch_required": True,
            "off_switch": "provider_runtime_adapter_enabled_false",
            "fallback_behavior": "deterministic_existing_shadow_output",
            "normal_behavior_unchanged_when_off": True,
        },
        "smoke_test_plan": {
            "automated_test_client": "injected_fake_client_only",
            "live_network_allowed": False,
            "assert_structured_output_validation": True,
            "assert_llmops_metadata": True,
            "assert_deterministic_fallback": True,
            "assert_zero_mutation_authority": True,
        },
        "planning_context": context,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "next_safe_step": next_safe_step,
        "safety_metadata": (
            provider_runtime_activation_plan_safety_metadata()
        ),
    }
