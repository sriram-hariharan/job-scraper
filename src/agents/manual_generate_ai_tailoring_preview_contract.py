"""Default-off contract for a future manual Generate AI Tailoring preview."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PHASE = "24A"
CONTRACT_VERSION = (
    "phase-24a-manual-generate-ai-tailoring-preview-contract-v1"
)
STATUS_BLOCKED = "manual_generate_ai_tailoring_preview_blocked"
STATUS_INCOMPLETE = "manual_generate_ai_tailoring_preview_incomplete"
STATUS_READY = "manual_generate_ai_tailoring_preview_ready"


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _has_payload(value: dict[str, Any]) -> bool:
    return bool(value)


def _user_trigger_present(metadata: dict[str, Any]) -> bool:
    if not metadata:
        return False
    return (
        metadata.get("user_triggered") is True
        or metadata.get("explicit_user_trigger") is True
        or metadata.get("generate_ai_tailoring_requested") is True
    )


def build_manual_generate_ai_tailoring_preview_contract(
    *,
    tailoring_opportunity_payload: dict[str, Any] | None = None,
    generate_ai_tailoring_action_boundary_payload: dict[str, Any] | None = None,
    selected_resume_metadata: dict[str, Any] | None = None,
    job_metadata: dict[str, Any] | None = None,
    user_trigger_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return preview-readiness metadata without generating or mutating."""

    safe_tailoring_opportunity = _plain_dict(tailoring_opportunity_payload)
    safe_action_boundary = _plain_dict(
        generate_ai_tailoring_action_boundary_payload
    )
    safe_resume = _plain_dict(selected_resume_metadata)
    safe_job = _plain_dict(job_metadata)
    safe_user_trigger = _plain_dict(user_trigger_metadata)

    user_trigger_present = _user_trigger_present(safe_user_trigger)
    missing_inputs: list[str] = []
    if not _has_payload(safe_tailoring_opportunity):
        missing_inputs.append("tailoring_opportunity_payload")
    if not _has_payload(safe_action_boundary):
        missing_inputs.append("generate_ai_tailoring_action_boundary_payload")
    if not _has_payload(safe_resume):
        missing_inputs.append("selected_resume_metadata")
    if not _has_payload(safe_job):
        missing_inputs.append("job_metadata")
    if not user_trigger_present:
        missing_inputs.append("user_trigger_metadata")

    blocked_reasons: list[str] = []
    if not user_trigger_present:
        blocked_reasons.append("explicit user trigger required")
    if missing_inputs:
        blocked_reasons.append("required preview inputs missing")

    can_prepare_preview = user_trigger_present and not missing_inputs
    if not user_trigger_present:
        contract_status = STATUS_BLOCKED
        next_safe_step = "require_explicit_user_trigger"
    elif missing_inputs:
        contract_status = STATUS_INCOMPLETE
        next_safe_step = "supply_missing_preview_inputs"
    else:
        contract_status = STATUS_READY
        next_safe_step = (
            "review_preview_readiness_without_generating_ai_tailoring"
        )

    return {
        "phase": PHASE,
        "contract_version": CONTRACT_VERSION,
        "contract_status": contract_status,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "preview_contract_only": True,
        "requires_user_trigger": True,
        "user_trigger_present": user_trigger_present,
        "manual_acceptance_required": True,
        "can_prepare_preview": can_prepare_preview,
        "blocked_reasons": blocked_reasons,
        "missing_inputs": missing_inputs,
        "no_provider_calls": True,
        "provider_call_performed": False,
        "no_network_calls": True,
        "tailoring_runtime_call_performed": False,
        "ai_tailoring_generation_performed": False,
        "resume_rewrite_performed": False,
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
        "database_write_performed": False,
        "persistence_performed": False,
        "execution_performed": False,
        "submission_performed": False,
        "auto_apply_performed": False,
        "auto_submit_performed": False,
        "next_safe_step": next_safe_step,
        "preview_inputs": {
            "tailoring_opportunity_payload": safe_tailoring_opportunity,
            "generate_ai_tailoring_action_boundary_payload": (
                safe_action_boundary
            ),
            "selected_resume_metadata": safe_resume,
            "job_metadata": safe_job,
            "user_trigger_metadata": safe_user_trigger,
        },
    }
