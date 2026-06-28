"""Default-off provider response validation contract for manual tailoring preview."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


PHASE = "30A"
CONTRACT_VERSION = (
    "phase-30a-manual-generate-ai-tailoring-preview-provider-response-validation-v1"
)
STATUS_BLOCKED = (
    "manual_generate_ai_tailoring_preview_provider_response_validation_blocked"
)
STATUS_READY = (
    "manual_generate_ai_tailoring_preview_provider_response_validation_ready"
)

_GENERATED_OUTPUT_KEYS = {
    "generated_tailoring_text",
    "generated_tailoring_suggestions",
    "real_tailoring_output",
    "resume_rewrite",
    "rewritten_resume",
    "tailored_resume",
}


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
        or metadata.get("provider_response_validation_confirmed") is True
    )


def _provider_call_dry_run_packet_accepted(payload: dict[str, Any]) -> bool:
    if not payload:
        return False

    nested_packet = payload.get("dry_run_packet")
    nested_packet = nested_packet if isinstance(nested_packet, dict) else {}
    packet_ready = (
        payload.get("dry_run_packet_ready") is True
        or payload.get("provider_call_allowed_for_future_manual_preview") is True
        or nested_packet.get("dry_run_packet_ready") is True
        or nested_packet.get("provider_call_allowed_for_future_manual_preview")
        is True
    )
    no_prior_activity = (
        payload.get("provider_call_performed") is not True
        and payload.get("network_call_performed") is not True
        and payload.get("dispatch_performed") is not True
        and payload.get("tailoring_runtime_call_performed") is not True
        and payload.get("ai_tailoring_generation_performed") is not True
        and payload.get("real_tailoring_output_created") is not True
        and payload.get("execution_performed") is not True
        and payload.get("submission_performed") is not True
    )
    return packet_ready and no_prior_activity


def _provider_request_envelope_accepted(payload: dict[str, Any]) -> bool:
    if not payload:
        return False

    nested_envelope = payload.get("request_envelope")
    nested_envelope = nested_envelope if isinstance(nested_envelope, dict) else {}
    envelope_allowed = (
        payload.get("provider_request_allowed") is True
        or payload.get("provider_request_envelope_ready") is True
        or nested_envelope.get("provider_request_allowed") is True
        or nested_envelope.get("provider_request_envelope_ready") is True
    )
    no_prior_activity = (
        payload.get("provider_call_performed") is not True
        and payload.get("network_call_performed") is not True
        and payload.get("tailoring_runtime_call_performed") is not True
        and payload.get("ai_tailoring_generation_performed") is not True
        and payload.get("real_tailoring_output_created") is not True
        and payload.get("execution_performed") is not True
        and payload.get("submission_performed") is not True
    )
    return envelope_allowed and no_prior_activity


def _provider_configuration_present(metadata: dict[str, Any]) -> bool:
    if not metadata:
        return False
    return (
        metadata.get("provider_configured") is True
        or metadata.get("provider_configuration_present") is True
        or metadata.get("provider_name") is not None
        or metadata.get("model") is not None
    )


def _response_validation_policy_present(metadata: dict[str, Any]) -> bool:
    if not metadata:
        return False
    return (
        metadata.get("response_validation_policy_present") is True
        or metadata.get("manual_response_validation_policy_present") is True
        or metadata.get("response_validation_policy_id") is not None
        or metadata.get("policy_name") is not None
    )


def _candidate_contains_generated_output(payload: dict[str, Any]) -> bool:
    return any(key in payload for key in _GENERATED_OUTPUT_KEYS)


def _deterministic_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return "manual-generate-ai-tailoring-preview-provider-response-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_manual_generate_ai_tailoring_preview_provider_response_validation_contract(
    *,
    provider_response_candidate_payload: dict[str, Any] | None = None,
    phase29_provider_call_dry_run_packet_payload: dict[str, Any] | None = None,
    phase28_provider_call_boundary_payload: dict[str, Any] | None = None,
    phase27_provider_request_envelope_payload: dict[str, Any] | None = None,
    user_trigger_metadata: dict[str, Any] | None = None,
    operator_confirmation_metadata: dict[str, Any] | None = None,
    response_validation_policy_metadata: dict[str, Any] | None = None,
    provider_configuration_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return provider response validation readiness without side effects."""

    safe_provider_response_candidate = _plain_dict(
        provider_response_candidate_payload
    )
    safe_provider_call_dry_run_packet = _plain_dict(
        phase29_provider_call_dry_run_packet_payload
    )
    safe_provider_call_boundary = _plain_dict(
        phase28_provider_call_boundary_payload
    )
    safe_provider_request_envelope = _plain_dict(
        phase27_provider_request_envelope_payload
    )
    safe_user_trigger = _plain_dict(user_trigger_metadata)
    safe_operator_confirmation = _plain_dict(operator_confirmation_metadata)
    safe_response_validation_policy = _plain_dict(
        response_validation_policy_metadata
    )
    safe_provider_configuration = _plain_dict(provider_configuration_metadata)

    user_trigger_present = _user_trigger_present(safe_user_trigger)
    operator_confirmation_present = _operator_confirmation_present(
        safe_operator_confirmation
    )
    provider_call_dry_run_packet_accepted = (
        _provider_call_dry_run_packet_accepted(
            safe_provider_call_dry_run_packet
        )
    )
    provider_request_envelope_accepted = _provider_request_envelope_accepted(
        safe_provider_request_envelope
    )
    provider_response_candidate_present = bool(safe_provider_response_candidate)
    response_validation_policy_present = _response_validation_policy_present(
        safe_response_validation_policy
    )
    provider_configuration_present = _provider_configuration_present(
        safe_provider_configuration
    )
    candidate_contains_generated_output = _candidate_contains_generated_output(
        safe_provider_response_candidate
    )

    missing_inputs: list[str] = []
    if not user_trigger_present:
        missing_inputs.append("user_trigger_metadata")
    if not operator_confirmation_present:
        missing_inputs.append("operator_confirmation_metadata")
    if not safe_provider_call_dry_run_packet:
        missing_inputs.append("phase29_provider_call_dry_run_packet_payload")
    if not safe_provider_request_envelope:
        missing_inputs.append("phase27_provider_request_envelope_payload")
    if not provider_response_candidate_present:
        missing_inputs.append("provider_response_candidate_payload")
    if not response_validation_policy_present:
        missing_inputs.append("response_validation_policy_metadata")
    if not provider_configuration_present:
        missing_inputs.append("provider_configuration_metadata")

    blocked_reasons: list[str] = []
    if not user_trigger_present:
        blocked_reasons.append("explicit user trigger required")
    if not operator_confirmation_present:
        blocked_reasons.append("operator confirmation required")
    if not safe_provider_call_dry_run_packet:
        blocked_reasons.append("phase29 provider-call dry-run packet required")
    elif not provider_call_dry_run_packet_accepted:
        blocked_reasons.append(
            "provider-call dry-run packet must be accepted before response validation"
        )
    if not safe_provider_request_envelope:
        blocked_reasons.append("phase27 provider request-envelope payload required")
    elif not provider_request_envelope_accepted:
        blocked_reasons.append(
            "provider request-envelope must be accepted before response validation"
        )
    if not provider_response_candidate_present:
        blocked_reasons.append("provider response candidate payload required")
    if candidate_contains_generated_output:
        blocked_reasons.append(
            "provider response candidate must not include generated tailoring output"
        )
    if not response_validation_policy_present:
        blocked_reasons.append("response validation policy metadata required")
    if not provider_configuration_present:
        blocked_reasons.append("provider configuration metadata required")

    response_validation_ready = (
        user_trigger_present
        and operator_confirmation_present
        and provider_call_dry_run_packet_accepted
        and provider_request_envelope_accepted
        and provider_response_candidate_present
        and not candidate_contains_generated_output
        and response_validation_policy_present
        and provider_configuration_present
    )
    provider_response_accepted_for_future_manual_preview = (
        response_validation_ready
    )
    contract_status = (
        STATUS_READY if response_validation_ready else STATUS_BLOCKED
    )

    if not user_trigger_present:
        next_safe_step = "require_explicit_user_trigger"
    elif not operator_confirmation_present:
        next_safe_step = "require_operator_confirmation"
    elif (
        not safe_provider_call_dry_run_packet
        or not provider_call_dry_run_packet_accepted
    ):
        next_safe_step = "provide_accepted_provider_call_dry_run_packet"
    elif (
        not safe_provider_request_envelope
        or not provider_request_envelope_accepted
    ):
        next_safe_step = "provide_accepted_provider_request_envelope"
    elif not provider_response_candidate_present:
        next_safe_step = "provide_provider_response_candidate_payload"
    elif candidate_contains_generated_output:
        next_safe_step = "provide_response_candidate_without_tailoring_output"
    elif not response_validation_policy_present:
        next_safe_step = "provide_response_validation_policy_metadata"
    elif not provider_configuration_present:
        next_safe_step = "provide_provider_configuration_metadata"
    else:
        next_safe_step = (
            "manual_review_provider_response_validation_without_live_call"
        )

    validation_inputs = {
        "provider_response_candidate_keys": sorted(
            safe_provider_response_candidate.keys()
        ),
        "phase29_provider_call_dry_run_packet_payload": (
            safe_provider_call_dry_run_packet
        ),
        "phase28_provider_call_boundary_payload": safe_provider_call_boundary,
        "phase27_provider_request_envelope_payload": (
            safe_provider_request_envelope
        ),
        "user_trigger_metadata": safe_user_trigger,
        "operator_confirmation_metadata": safe_operator_confirmation,
        "response_validation_policy_metadata": safe_response_validation_policy,
        "provider_configuration_metadata": safe_provider_configuration,
        "provider_call_dry_run_packet_accepted": (
            provider_call_dry_run_packet_accepted
        ),
        "provider_request_envelope_accepted": (
            provider_request_envelope_accepted
        ),
        "provider_response_candidate_present": (
            provider_response_candidate_present
        ),
        "response_validation_policy_present": (
            response_validation_policy_present
        ),
        "provider_configuration_present": provider_configuration_present,
        "response_validation_ready": response_validation_ready,
    }
    deterministic_response_validation_key = _deterministic_key(
        validation_inputs
    )

    validation_findings = [
        {
            "finding": "provider_response_candidate_present",
            "accepted": provider_response_candidate_present,
            "read_only": True,
        },
        {
            "finding": "no_generated_tailoring_output_in_candidate",
            "accepted": not candidate_contains_generated_output,
            "read_only": True,
        },
        {
            "finding": "provider_response_validation_ready",
            "accepted": response_validation_ready,
            "read_only": True,
        },
    ]

    provider_response_contract = {
        "provider_response_contract_status": contract_status,
        "deterministic_response_validation_key": (
            deterministic_response_validation_key
        ),
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "provider_response_validation_contract_only": True,
        "response_validation_only": True,
        "requires_user_trigger": True,
        "operator_confirmation_required": True,
        "manual_acceptance_required": True,
        "provider_call_dry_run_packet_required": True,
        "provider_call_dry_run_packet_accepted": (
            provider_call_dry_run_packet_accepted
        ),
        "provider_request_envelope_required": True,
        "provider_request_envelope_accepted": (
            provider_request_envelope_accepted
        ),
        "provider_response_candidate_required": True,
        "provider_response_candidate_present": (
            provider_response_candidate_present
        ),
        "response_validation_policy_required": True,
        "response_validation_policy_present": (
            response_validation_policy_present
        ),
        "provider_configuration_required": True,
        "provider_configuration_present": provider_configuration_present,
        "response_validation_ready": response_validation_ready,
        "provider_response_accepted_for_future_manual_preview": (
            provider_response_accepted_for_future_manual_preview
        ),
        "candidate_key_inventory": sorted(
            safe_provider_response_candidate.keys()
        ),
        "contains_generated_tailoring_text": (
            candidate_contains_generated_output
        ),
        "contains_real_tailoring_output": candidate_contains_generated_output,
        "provider_call_performed": False,
        "network_call_performed": False,
        "dispatch_performed": False,
        "tailoring_runtime_call_performed": False,
        "ai_tailoring_generation_performed": False,
        "real_tailoring_output_created": False,
        "source_inputs": deepcopy(validation_inputs),
    }

    return {
        "phase": PHASE,
        "contract_version": CONTRACT_VERSION,
        "contract_status": contract_status,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "provider_response_validation_contract_only": True,
        "response_validation_only": True,
        "requires_user_trigger": True,
        "user_trigger_present": user_trigger_present,
        "operator_confirmation_required": True,
        "operator_confirmation_present": operator_confirmation_present,
        "manual_acceptance_required": True,
        "provider_call_dry_run_packet_required": True,
        "provider_call_dry_run_packet_accepted": (
            provider_call_dry_run_packet_accepted
        ),
        "provider_request_envelope_required": True,
        "provider_request_envelope_accepted": (
            provider_request_envelope_accepted
        ),
        "provider_response_candidate_required": True,
        "provider_response_candidate_present": (
            provider_response_candidate_present
        ),
        "response_validation_policy_required": True,
        "response_validation_policy_present": (
            response_validation_policy_present
        ),
        "provider_configuration_required": True,
        "provider_configuration_present": provider_configuration_present,
        "response_validation_ready": response_validation_ready,
        "provider_response_accepted_for_future_manual_preview": (
            provider_response_accepted_for_future_manual_preview
        ),
        "blocked_reasons": blocked_reasons,
        "missing_inputs": missing_inputs,
        "validation_findings": validation_findings,
        "provider_response_contract": provider_response_contract,
        "deterministic_response_validation_key": (
            deterministic_response_validation_key
        ),
        "no_provider_calls": True,
        "provider_call_performed": False,
        "no_network_calls": True,
        "network_call_performed": False,
        "dispatch_performed": False,
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
