"""Default-off request-packet contract for manual Generate AI Tailoring preview."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


PHASE = "25A"
CONTRACT_VERSION = (
    "phase-25a-manual-generate-ai-tailoring-preview-request-packet-v1"
)
STATUS_BLOCKED = "manual_generate_ai_tailoring_preview_request_packet_blocked"
STATUS_INCOMPLETE = (
    "manual_generate_ai_tailoring_preview_request_packet_incomplete"
)
STATUS_READY = "manual_generate_ai_tailoring_preview_request_packet_ready"


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


def _deterministic_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return "manual-generate-ai-tailoring-preview-request-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_manual_generate_ai_tailoring_preview_request_packet_contract(
    *,
    phase24_preview_contract_payload: dict[str, Any] | None = None,
    job_metadata: dict[str, Any] | None = None,
    selected_resume_metadata: dict[str, Any] | None = None,
    tailoring_opportunity_payload: dict[str, Any] | None = None,
    user_trigger_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a future request-packet description without generating output."""

    safe_phase24 = _plain_dict(phase24_preview_contract_payload)
    safe_job = _plain_dict(job_metadata)
    safe_resume = _plain_dict(selected_resume_metadata)
    safe_tailoring_opportunity = _plain_dict(tailoring_opportunity_payload)
    safe_user_trigger = _plain_dict(user_trigger_metadata)

    user_trigger_present = _user_trigger_present(safe_user_trigger)
    missing_inputs: list[str] = []
    if not _has_payload(safe_phase24):
        missing_inputs.append("phase24_preview_contract_payload")
    if not _has_payload(safe_job):
        missing_inputs.append("job_metadata")
    if not _has_payload(safe_resume):
        missing_inputs.append("selected_resume_metadata")
    if not _has_payload(safe_tailoring_opportunity):
        missing_inputs.append("tailoring_opportunity_payload")
    if not user_trigger_present:
        missing_inputs.append("user_trigger_metadata")

    blocked_reasons: list[str] = []
    if not user_trigger_present:
        blocked_reasons.append("explicit user trigger required")
    if missing_inputs:
        blocked_reasons.append("required request-packet inputs missing")

    can_prepare_request_packet = user_trigger_present and not missing_inputs
    preview_request_allowed = can_prepare_request_packet
    if not user_trigger_present:
        contract_status = STATUS_BLOCKED
        next_safe_step = "require_explicit_user_trigger"
    elif missing_inputs:
        contract_status = STATUS_INCOMPLETE
        next_safe_step = "supply_missing_request_packet_inputs"
    else:
        contract_status = STATUS_READY
        next_safe_step = (
            "review_request_packet_without_generating_ai_tailoring"
        )

    request_key_inputs = {
        "phase24_preview_contract_payload": safe_phase24,
        "job_metadata": safe_job,
        "selected_resume_metadata": safe_resume,
        "tailoring_opportunity_payload": safe_tailoring_opportunity,
        "user_trigger_metadata": safe_user_trigger,
    }
    deterministic_request_key = _deterministic_key(request_key_inputs)

    request_packet = {
        "request_packet_status": contract_status,
        "deterministic_request_key": deterministic_request_key,
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "request_packet_contract_only": True,
        "requires_user_trigger": True,
        "manual_acceptance_required": True,
        "can_prepare_request_packet": can_prepare_request_packet,
        "preview_request_allowed": preview_request_allowed,
        "contains_generated_tailoring_output": False,
        "tailoring_generation_requested_from_runtime": False,
        "source_inputs": deepcopy(request_key_inputs),
    }

    return {
        "phase": PHASE,
        "contract_version": CONTRACT_VERSION,
        "contract_status": contract_status,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "request_packet_contract_only": True,
        "requires_user_trigger": True,
        "user_trigger_present": user_trigger_present,
        "manual_acceptance_required": True,
        "can_prepare_request_packet": can_prepare_request_packet,
        "preview_request_allowed": preview_request_allowed,
        "blocked_reasons": blocked_reasons,
        "missing_inputs": missing_inputs,
        "request_packet": request_packet,
        "deterministic_request_key": deterministic_request_key,
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
    }
