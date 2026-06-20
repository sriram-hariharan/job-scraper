"""Default-off safety plan for a future JD provider canary."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PLAN_VERSION = "phase-13a-provider-live-activation-safety-plan-v1"
STATUS_SKIPPED = "live_activation_plan_skipped_default_off"
STATUS_READY = "live_activation_plan_ready_for_review"
FIRST_CANARY_AGENT = "jd_intelligence"
BLOCKED_LIVE_AGENTS = ("tailoring_suggestion", "critic_guardrail")


def provider_live_activation_safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "planning_only": True,
        "shadow_only": True,
        "live_provider_execution_enabled": False,
        "provider_calls_made": False,
        "network_calls_made": False,
        "environment_secrets_read": False,
        "embeddings_created": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_write_files": False,
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
        "service_behavior_added": False,
        "pipeline_stage_added": False,
        "mutation_authorized": False,
    }


def build_provider_live_activation_safety_plan(
    *,
    enabled: bool = False,
    planning_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Describe future canary gates without enabling or calling a provider."""

    context = (
        deepcopy(planning_context)
        if isinstance(planning_context, dict)
        else {}
    )
    status = STATUS_READY if enabled is True else STATUS_SKIPPED
    next_safe_step = (
        "review_phase_13b_jd_canary_scaffold_requirements"
        if enabled is True
        else "enable_live_activation_safety_plan_review_only"
    )
    return {
        "plan_version": PLAN_VERSION,
        "live_activation_safety_plan_enabled": enabled is True,
        "plan_status": status,
        "default_off": True,
        "planning_only": True,
        "live_provider_execution_enabled": False,
        "first_real_canary_agent": FIRST_CANARY_AGENT,
        "first_real_canary_mode": "shadow_only",
        "blocked_real_execution_agent_names": list(BLOCKED_LIVE_AGENTS),
        "blocked_real_execution_reasons": {
            "tailoring_suggestion": (
                "deferred_until_jd_live_canary_safety_is_proven"
            ),
            "critic_guardrail": (
                "deferred_until_jd_live_canary_and_handoffs_are_proven"
            ),
        },
        "explicit_enable_flag_required": True,
        "explicit_configuration_required": True,
        "provider_name_allowlist_required": True,
        "model_name_allowlist_required": True,
        "provider_allowlist_default": [],
        "model_allowlist_default": [],
        "injected_provider_adapter_required": True,
        "injected_provider_client_required": True,
        "later_approved_provider_adapter_allowed": True,
        "provider_client_constructed_internally": False,
        "environment_secrets_read_by_plan": False,
        "shadow_only_required": True,
        "canary_constraints": {
            "single_agent_only": True,
            "single_agent_name": FIRST_CANARY_AGENT,
            "final_decision_influence_allowed": False,
            "database_writes_allowed": False,
            "resume_or_cover_letter_writes_allowed": False,
            "application_actions_allowed": False,
        },
        "execution_limits": {
            "strict_timeout_required": True,
            "timeout_must_be_explicit": True,
            "retry_limit_required": True,
            "retry_limit_must_be_explicit": True,
            "token_budget_required": True,
            "token_budget_must_be_explicit": True,
            "cost_budget_required": True,
            "cost_budget_must_be_explicit": True,
            "unbounded_retries_allowed": False,
            "unbounded_tokens_allowed": False,
            "unbounded_cost_allowed": False,
        },
        "validation_and_fallback": {
            "structured_output_schema_validation_required": True,
            "invalid_output_must_fallback": True,
            "provider_exception_must_fallback": True,
            "timeout_must_fallback": True,
            "budget_exceeded_must_block_or_fallback": True,
            "deterministic_fallback_required": True,
            "fallback_target": "existing_deterministic_jd_shadow_output",
        },
        "observability_requirements": {
            "llmops_metadata_required": True,
            "prompt_version_required": True,
            "agent_version_required": True,
            "provider_name_required": True,
            "model_name_required": True,
            "latency_required": True,
            "token_usage_required": True,
            "estimated_cost_required": True,
            "retry_count_required": True,
            "fallback_status_required": True,
            "schema_validation_status_required": True,
            "provider_error_classification_required": True,
        },
        "provider_error_classifications": [
            "configuration_error",
            "authentication_error",
            "rate_limit_error",
            "timeout_error",
            "provider_response_error",
            "schema_validation_error",
            "budget_limit_error",
            "unknown_provider_error",
        ],
        "no_influence_requirements": {
            "final_scoring_influence_allowed": False,
            "ranking_influence_allowed": False,
            "queue_influence_allowed": False,
            "approval_influence_allowed": False,
            "resume_mutation_allowed": False,
            "cover_letter_mutation_allowed": False,
            "execution_allowed": False,
            "submission_allowed": False,
        },
        "rollback": {
            "off_switch_required": True,
            "primary_off_switch": "jd_live_canary_enabled_false",
            "secondary_off_switch": "provider_runtime_adapter_enabled_false",
            "rollback_on_provider_error": True,
            "rollback_on_schema_validation_failure": True,
            "rollback_on_timeout": True,
            "rollback_on_retry_limit": True,
            "rollback_on_token_budget_limit": True,
            "rollback_on_cost_budget_limit": True,
            "fallback_behavior": "existing_deterministic_jd_shadow_output",
            "normal_behavior_unchanged_when_off": True,
        },
        "pre_live_smoke_test_plan": {
            "injected_fake_client_only": True,
            "live_network_allowed": False,
            "assert_allowlist_enforcement": True,
            "assert_timeout_enforcement": True,
            "assert_retry_limit_enforcement": True,
            "assert_token_budget_enforcement": True,
            "assert_cost_budget_enforcement": True,
            "assert_structured_output_validation": True,
            "assert_error_classification": True,
            "assert_llmops_metadata": True,
            "assert_deterministic_fallback": True,
            "assert_readback_visibility": True,
            "assert_zero_mutation_authority": True,
        },
        "audit_readback_expectations": {
            "existing_trace_readback_required": True,
            "existing_review_packet_readback_required": True,
            "existing_service_readback_required": True,
            "existing_api_readback_required": True,
            "existing_ui_readback_required": True,
            "ui_remains_manual_only": True,
            "audit_payload_must_not_trigger_execution": True,
        },
        "phase_13b_go_no_go_checks": [
            "jd_only_canary_scope_confirmed",
            "shadow_only_mode_confirmed",
            "explicit_enable_gate_defined",
            "provider_and_model_allowlists_defined",
            "injected_or_approved_adapter_boundary_confirmed",
            "timeout_and_retry_limits_defined",
            "token_and_cost_budgets_defined",
            "structured_output_validation_confirmed",
            "deterministic_fallback_confirmed",
            "llmops_and_prompt_version_metadata_confirmed",
            "error_classification_confirmed",
            "rollback_switches_confirmed",
            "readback_audit_visibility_confirmed",
            "zero_mutation_authority_confirmed",
        ],
        "go_decision_authorized": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "planning_context": context,
        "next_safe_step": next_safe_step,
        "safety_metadata": provider_live_activation_safety_metadata(),
    }
