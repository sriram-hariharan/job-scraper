"""Default-off provider request-envelope contract for manual tailoring preview."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


PHASE = "27A"
CONTRACT_VERSION = (
    "phase-27a-manual-generate-ai-tailoring-preview-provider-request-envelope-v1"
)
STATUS_BLOCKED = (
    "manual_generate_ai_tailoring_preview_provider_request_envelope_blocked"
)
STATUS_READY = (
    "manual_generate_ai_tailoring_preview_provider_request_envelope_ready"
)


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
        or metadata.get("provider_request_envelope_confirmed") is True
    )


def _dispatch_boundary_accepted(payload: dict[str, Any]) -> bool:
    if not payload:
        return False

    return (
        (
            payload.get("dispatch_allowed") is True
            or payload.get("dispatch_ready") is True
        )
        and payload.get("provider_call_performed") is not True
        and payload.get("network_call_performed") is not True
        and payload.get("tailoring_runtime_call_performed") is not True
        and payload.get("ai_tailoring_generation_performed") is not True
        and payload.get("execution_performed") is not True
        and payload.get("submission_performed") is not True
    )


def _provider_configuration_present(metadata: dict[str, Any]) -> bool:
    if not metadata:
        return False
    return (
        metadata.get("provider_configured") is True
        or metadata.get("provider_configuration_present") is True
        or metadata.get("provider_name") is not None
        or metadata.get("model") is not None
    )


def _deterministic_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return "manual-generate-ai-tailoring-preview-provider-envelope-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract(
    *,
    phase26_dispatch_boundary_payload: dict[str, Any] | None = None,
    phase25_request_packet_payload: dict[str, Any] | None = None,
    phase24_preview_contract_payload: dict[str, Any] | None = None,
    user_trigger_metadata: dict[str, Any] | None = None,
    operator_confirmation_metadata: dict[str, Any] | None = None,
    provider_configuration_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a safe provider request-envelope description without dispatch."""

    safe_dispatch_boundary = _plain_dict(phase26_dispatch_boundary_payload)
    safe_request_packet = _plain_dict(phase25_request_packet_payload)
    safe_preview_contract = _plain_dict(phase24_preview_contract_payload)
    safe_user_trigger = _plain_dict(user_trigger_metadata)
    safe_operator_confirmation = _plain_dict(operator_confirmation_metadata)
    safe_provider_configuration = _plain_dict(provider_configuration_metadata)

    user_trigger_present = _user_trigger_present(safe_user_trigger)
    operator_confirmation_present = _operator_confirmation_present(
        safe_operator_confirmation
    )
    dispatch_boundary_accepted = _dispatch_boundary_accepted(
        safe_dispatch_boundary
    )
    provider_configuration_present = _provider_configuration_present(
        safe_provider_configuration
    )

    missing_inputs: list[str] = []
    if not user_trigger_present:
        missing_inputs.append("user_trigger_metadata")
    if not operator_confirmation_present:
        missing_inputs.append("operator_confirmation_metadata")
    if not safe_dispatch_boundary:
        missing_inputs.append("phase26_dispatch_boundary_payload")
    if not safe_request_packet:
        missing_inputs.append("phase25_request_packet_payload")
    if not safe_preview_contract:
        missing_inputs.append("phase24_preview_contract_payload")
    if not provider_configuration_present:
        missing_inputs.append("provider_configuration_metadata")

    blocked_reasons: list[str] = []
    if not user_trigger_present:
        blocked_reasons.append("explicit user trigger required")
    if not operator_confirmation_present:
        blocked_reasons.append("operator confirmation required")
    if not safe_dispatch_boundary:
        blocked_reasons.append("phase26 dispatch-boundary payload required")
    elif not dispatch_boundary_accepted:
        blocked_reasons.append(
            "dispatch boundary must be accepted before provider request-envelope"
        )
    if not safe_request_packet:
        blocked_reasons.append("phase25 request-packet payload required")
    if not safe_preview_contract:
        blocked_reasons.append("phase24 preview contract payload required")
    if not provider_configuration_present:
        blocked_reasons.append("provider configuration metadata required")

    provider_request_envelope_ready = (
        user_trigger_present
        and operator_confirmation_present
        and dispatch_boundary_accepted
        and bool(safe_request_packet)
        and bool(safe_preview_contract)
        and provider_configuration_present
    )
    provider_request_allowed = provider_request_envelope_ready
    contract_status = (
        STATUS_READY if provider_request_envelope_ready else STATUS_BLOCKED
    )

    if not user_trigger_present:
        next_safe_step = "require_explicit_user_trigger"
    elif not operator_confirmation_present:
        next_safe_step = "require_operator_confirmation"
    elif not safe_dispatch_boundary or not dispatch_boundary_accepted:
        next_safe_step = "provide_accepted_dispatch_boundary"
    elif not safe_request_packet:
        next_safe_step = "provide_phase25_request_packet_payload"
    elif not safe_preview_contract:
        next_safe_step = "provide_phase24_preview_contract_payload"
    elif not provider_configuration_present:
        next_safe_step = "provide_provider_configuration_metadata"
    else:
        next_safe_step = (
            "manual_review_provider_request_envelope_without_dispatching"
        )

    envelope_inputs = {
        "phase26_dispatch_boundary_payload": safe_dispatch_boundary,
        "phase25_request_packet_payload": safe_request_packet,
        "phase24_preview_contract_payload": safe_preview_contract,
        "user_trigger_metadata": safe_user_trigger,
        "operator_confirmation_metadata": safe_operator_confirmation,
        "provider_configuration_metadata": safe_provider_configuration,
        "dispatch_boundary_accepted": dispatch_boundary_accepted,
        "provider_configuration_present": provider_configuration_present,
        "provider_request_envelope_ready": provider_request_envelope_ready,
    }
    deterministic_envelope_key = _deterministic_key(envelope_inputs)

    request_envelope = {
        "request_envelope_status": contract_status,
        "deterministic_envelope_key": deterministic_envelope_key,
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "provider_request_envelope_contract_only": True,
        "requires_user_trigger": True,
        "operator_confirmation_required": True,
        "manual_acceptance_required": True,
        "dispatch_boundary_required": True,
        "dispatch_boundary_accepted": dispatch_boundary_accepted,
        "provider_configuration_required": True,
        "provider_configuration_present": provider_configuration_present,
        "provider_request_envelope_ready": provider_request_envelope_ready,
        "provider_request_allowed": provider_request_allowed,
        "contains_generated_tailoring_output": False,
        "creates_real_tailoring_output": False,
        "dispatch_performed": False,
        "provider_call_performed": False,
        "network_call_performed": False,
        "source_inputs": deepcopy(envelope_inputs),
    }

    return {
        "phase": PHASE,
        "contract_version": CONTRACT_VERSION,
        "contract_status": contract_status,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "provider_request_envelope_contract_only": True,
        "requires_user_trigger": True,
        "user_trigger_present": user_trigger_present,
        "operator_confirmation_required": True,
        "operator_confirmation_present": operator_confirmation_present,
        "manual_acceptance_required": True,
        "dispatch_boundary_required": True,
        "dispatch_boundary_accepted": dispatch_boundary_accepted,
        "provider_configuration_required": True,
        "provider_configuration_present": provider_configuration_present,
        "provider_request_envelope_ready": provider_request_envelope_ready,
        "provider_request_allowed": provider_request_allowed,
        "blocked_reasons": blocked_reasons,
        "missing_inputs": missing_inputs,
        "request_envelope": request_envelope,
        "deterministic_envelope_key": deterministic_envelope_key,
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
