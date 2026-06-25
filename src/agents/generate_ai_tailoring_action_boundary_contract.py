"""Pure default-off boundary for a future user-triggered tailoring action."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


CONTRACT_VERSION = "phase-23d-generate-ai-tailoring-action-boundary-v1"
STATUS_SKIPPED = "generate_ai_tailoring_action_boundary_skipped_default_off"
STATUS_BLOCKED = "generate_ai_tailoring_action_boundary_blocked_user_trigger_required"
STATUS_READY = "generate_ai_tailoring_action_boundary_ready_for_future_action"
FUTURE_ACTION_NAME = "Generate AI Tailoring"


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _plain_list(value: Any) -> list[Any]:
    return deepcopy(value) if isinstance(value, list) else []


def generate_ai_tailoring_action_boundary_safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "manual_user_control_required": True,
        "user_trigger_required": True,
        "preview_only": True,
        "manual_acceptance_required": True,
        "provider_call_attempted": False,
        "network_call_attempted": False,
        "file_read_attempted": False,
        "file_write_attempted": False,
        "environment_read_attempted": False,
        "database_read_attempted": False,
        "database_write_attempted": False,
        "persistence_attempted": False,
        "scoring_called": False,
        "prefilter_called": False,
        "matching_called": False,
        "tailoring_runtime_called": False,
        "llm_runtime_called": False,
        "ai_tailoring_generation_performed": False,
        "ranking_mutated": False,
        "queue_mutated": False,
        "resume_mutated": False,
        "application_mutated": False,
        "approval_mutated": False,
        "decision_mutated": False,
        "audit_mutated": False,
        "execution_authorized": False,
        "submission_authorized": False,
        "mutation_authorized": False,
    }


def build_generate_ai_tailoring_action_boundary_contract(
    *,
    enabled: bool = False,
    user_triggered: bool = False,
    tailoring_agent_opportunity_payload: dict[str, Any] | None = None,
    selected_opportunity_ids: list[Any] | None = None,
    generation_context: dict[str, Any] | None = None,
    operator_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return readiness metadata without generating or mutating anything."""

    enabled_exact = enabled is True
    user_triggered_exact = user_triggered is True
    action_inputs = {
        "tailoring_agent_opportunity_payload": _plain_dict(
            tailoring_agent_opportunity_payload
        ),
        "selected_opportunity_ids": _plain_list(
            selected_opportunity_ids
        ),
        "generation_context": _plain_dict(generation_context),
        "operator_context": _plain_dict(operator_context),
    }

    if not enabled_exact:
        status = STATUS_SKIPPED
        action_allowed = False
        blocked_reason = "action boundary is default-off"
        readiness_summary = (
            "Generate AI Tailoring action readiness is skipped by default."
        )
        next_safe_step = "explicitly_enable_action_boundary"
    elif not user_triggered_exact:
        status = STATUS_BLOCKED
        action_allowed = False
        blocked_reason = "explicit user trigger required"
        readiness_summary = (
            "Generate AI Tailoring remains blocked until an explicit user "
            "trigger is supplied."
        )
        next_safe_step = "require_explicit_user_trigger"
    else:
        status = STATUS_READY
        action_allowed = True
        blocked_reason = ""
        readiness_summary = (
            "Action-boundary readiness is confirmed for a later preview-only "
            "generation phase; no tailoring was generated."
        )
        next_safe_step = (
            "retain_preview_only_boundary_without_calling_tailoring_runtime"
        )

    return {
        "contract_version": CONTRACT_VERSION,
        "action_boundary_status": status,
        "generate_ai_tailoring_action_boundary_enabled": enabled_exact,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "manual_user_control_required": True,
        "user_trigger_required": True,
        "user_triggered": user_triggered_exact,
        "action_allowed": action_allowed,
        "action_blocked_reason": blocked_reason,
        "future_action_name": FUTURE_ACTION_NAME,
        "ai_tailoring_generation_performed": False,
        "tailoring_provider_call_performed": False,
        "tailoring_runtime_call_performed": False,
        "resume_rewrite_performed": False,
        "resume_overwrite_performed": False,
        "application_submission_performed": False,
        "preview_only": True,
        "manual_acceptance_required": True,
        "no_auto_apply": True,
        "no_auto_submit": True,
        "no_autonomous_application_execution": True,
        "no_automatic_job_application_submission": True,
        "no_provider_calls": True,
        "no_network_calls": True,
        "no_database_writes": True,
        "no_persistence": True,
        "no_mutation": True,
        "no_resume_mutation": True,
        "no_application_mutation": True,
        "no_execution": True,
        "no_submission": True,
        "action_inputs": action_inputs,
        "readiness_summary": readiness_summary,
        "next_safe_step": next_safe_step,
        "safety_metadata": (
            generate_ai_tailoring_action_boundary_safety_metadata()
        ),
    }
