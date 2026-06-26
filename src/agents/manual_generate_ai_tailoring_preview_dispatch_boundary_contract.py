"""Default-off dispatch-boundary contract for manual AI tailoring preview."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


PHASE = "26A"
CONTRACT_VERSION = (
    "phase-26a-manual-generate-ai-tailoring-preview-dispatch-boundary-v1"
)
STATUS_BLOCKED = (
    "manual_generate_ai_tailoring_preview_dispatch_boundary_blocked"
)
STATUS_READY = "manual_generate_ai_tailoring_preview_dispatch_boundary_ready"


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _user_trigger_present(metadata: dict[str, Any]) -> bool:
    if not metadata:
        return False
    return (
        metadata.get("user_triggered") is True
        or metadata.get("explicit_user_trigger") is True
        or metadata.get("generate_ai_tailoring_requested") is True
    )


def _operator_confirmation_present(metadata: dict[str, Any]) -> bool:
    if not metadata:
        return False
    return (
        metadata.get("operator_confirmed") is True
        or metadata.get("explicit_operator_confirmation") is True
        or metadata.get("dispatch_boundary_confirmed") is True
    )


def _request_packet_accepted(payload: dict[str, Any]) -> bool:
    if not payload:
        return False

    nested_packet = payload.get("request_packet")
    nested_packet = nested_packet if isinstance(nested_packet, dict) else {}
    packet_allowed = (
        payload.get("preview_request_allowed") is True
        or payload.get("can_prepare_request_packet") is True
        or nested_packet.get("preview_request_allowed") is True
        or nested_packet.get("can_prepare_request_packet") is True
    )
    no_prior_generation = (
        payload.get("provider_call_performed") is not True
        and payload.get("tailoring_runtime_call_performed") is not True
        and payload.get("ai_tailoring_generation_performed") is not True
    )
    return packet_allowed and no_prior_generation


def _deterministic_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return "manual-generate-ai-tailoring-preview-dispatch-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_manual_generate_ai_tailoring_preview_dispatch_boundary_contract(
    *,
    phase25_request_packet_payload: dict[str, Any] | None = None,
    phase24_preview_contract_payload: dict[str, Any] | None = None,
    user_trigger_metadata: dict[str, Any] | None = None,
    operator_confirmation_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return dispatch readiness metadata without dispatching anything."""

    safe_packet = _plain_dict(phase25_request_packet_payload)
    safe_phase24 = _plain_dict(phase24_preview_contract_payload)
    safe_user_trigger = _plain_dict(user_trigger_metadata)
    safe_operator_confirmation = _plain_dict(operator_confirmation_metadata)

    user_trigger_present = _user_trigger_present(safe_user_trigger)
    operator_confirmation_present = _operator_confirmation_present(
        safe_operator_confirmation
    )
    request_packet_accepted = _request_packet_accepted(safe_packet)

    missing_inputs: list[str] = []
    if not safe_packet:
        missing_inputs.append("phase25_request_packet_payload")
    if not safe_phase24:
        missing_inputs.append("phase24_preview_contract_payload")
    if not user_trigger_present:
        missing_inputs.append("user_trigger_metadata")
    if not operator_confirmation_present:
        missing_inputs.append("operator_confirmation_metadata")

    blocked_reasons: list[str] = []
    if not user_trigger_present:
        blocked_reasons.append("explicit user trigger required")
    if not operator_confirmation_present:
        blocked_reasons.append("operator confirmation required")
    if not safe_packet:
        blocked_reasons.append("phase25 request-packet payload required")
    elif not request_packet_accepted:
        blocked_reasons.append(
            "request packet must be preview-request allowed before dispatch "
            "readiness"
        )
    if not safe_phase24:
        blocked_reasons.append("phase24 preview contract payload required")

    dispatch_ready = (
        user_trigger_present
        and operator_confirmation_present
        and request_packet_accepted
        and bool(safe_phase24)
    )
    dispatch_allowed = dispatch_ready
    contract_status = STATUS_READY if dispatch_ready else STATUS_BLOCKED

    if not user_trigger_present:
        next_safe_step = "require_explicit_user_trigger"
    elif not operator_confirmation_present:
        next_safe_step = "require_operator_confirmation"
    elif not safe_packet or not request_packet_accepted:
        next_safe_step = "provide_preview_request_allowed_packet"
    elif not safe_phase24:
        next_safe_step = "provide_phase24_preview_contract_payload"
    else:
        next_safe_step = "manual_review_dispatch_boundary_without_dispatching"

    dispatch_key_inputs = {
        "phase25_request_packet_payload": safe_packet,
        "phase24_preview_contract_payload": safe_phase24,
        "user_trigger_metadata": safe_user_trigger,
        "operator_confirmation_metadata": safe_operator_confirmation,
        "request_packet_accepted": request_packet_accepted,
        "dispatch_ready": dispatch_ready,
    }
    deterministic_dispatch_key = _deterministic_key(dispatch_key_inputs)

    return {
        "phase": PHASE,
        "contract_version": CONTRACT_VERSION,
        "contract_status": contract_status,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "dispatch_boundary_contract_only": True,
        "requires_user_trigger": True,
        "user_trigger_present": user_trigger_present,
        "operator_confirmation_required": True,
        "operator_confirmation_present": operator_confirmation_present,
        "manual_acceptance_required": True,
        "dispatch_ready": dispatch_ready,
        "dispatch_allowed": dispatch_allowed,
        "blocked_reasons": blocked_reasons,
        "missing_inputs": missing_inputs,
        "request_packet_accepted": request_packet_accepted,
        "deterministic_dispatch_key": deterministic_dispatch_key,
        "no_provider_calls": True,
        "provider_call_performed": False,
        "no_network_calls": True,
        "network_call_performed": False,
        "tailoring_runtime_call_performed": False,
        "ai_tailoring_generation_performed": False,
        "real_tailoring_output_created": False,
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
