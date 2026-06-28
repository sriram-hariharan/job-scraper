"""Default-off normalized response preview packet contract for manual tailoring preview."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


PHASE = "32A"
CONTRACT_VERSION = (
    "phase-32a-manual-generate-ai-tailoring-preview-normalized-response-preview-packet-v1"
)
STATUS_BLOCKED = (
    "manual_generate_ai_tailoring_preview_normalized_response_preview_packet_blocked"
)
STATUS_READY = (
    "manual_generate_ai_tailoring_preview_normalized_response_preview_packet_ready"
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
        or metadata.get("normalized_response_preview_packet_confirmed") is True
    )


def _provider_response_normalization_accepted(payload: dict[str, Any]) -> bool:
    if not payload:
        return False

    nested_contract = payload.get("normalized_provider_response_contract")
    nested_contract = nested_contract if isinstance(nested_contract, dict) else {}
    normalization_ready = (
        payload.get("response_normalization_ready") is True
        or payload.get(
            "normalized_provider_response_accepted_for_future_manual_preview"
        )
        is True
        or nested_contract.get("response_normalization_ready") is True
        or nested_contract.get(
            "normalized_provider_response_accepted_for_future_manual_preview"
        )
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
    return normalization_ready and no_prior_activity


def _provider_response_validation_accepted(payload: dict[str, Any]) -> bool:
    if not payload:
        return False

    nested_contract = payload.get("provider_response_contract")
    nested_contract = nested_contract if isinstance(nested_contract, dict) else {}
    validation_ready = (
        payload.get("response_validation_ready") is True
        or payload.get("provider_response_accepted_for_future_manual_preview")
        is True
        or nested_contract.get("response_validation_ready") is True
        or nested_contract.get(
            "provider_response_accepted_for_future_manual_preview"
        )
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
    return validation_ready and no_prior_activity


def _preview_packet_policy_present(metadata: dict[str, Any]) -> bool:
    if not metadata:
        return False
    return (
        metadata.get("preview_packet_policy_present") is True
        or metadata.get("manual_preview_packet_policy_present") is True
        or metadata.get("preview_packet_policy_id") is not None
        or metadata.get("policy_name") is not None
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


def _contains_generated_output(payload: dict[str, Any]) -> bool:
    return any(key in payload for key in _GENERATED_OUTPUT_KEYS)


def _deterministic_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        default=str,
    )
    return "manual-generate-ai-tailoring-preview-normalized-packet-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_contract(
    *,
    provider_response_normalization_payload: dict[str, Any] | None = None,
    normalized_provider_response_contract_payload: dict[str, Any] | None = None,
    provider_response_validation_payload: dict[str, Any] | None = None,
    provider_response_candidate_payload: dict[str, Any] | None = None,
    phase29_provider_call_dry_run_packet_payload: dict[str, Any] | None = None,
    phase28_provider_call_boundary_payload: dict[str, Any] | None = None,
    phase27_provider_request_envelope_payload: dict[str, Any] | None = None,
    user_trigger_metadata: dict[str, Any] | None = None,
    operator_confirmation_metadata: dict[str, Any] | None = None,
    preview_packet_policy_metadata: dict[str, Any] | None = None,
    provider_configuration_metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return normalized response preview packet readiness without side effects."""

    safe_provider_response_normalization = _plain_dict(
        provider_response_normalization_payload
    )
    safe_normalized_provider_response_contract = _plain_dict(
        normalized_provider_response_contract_payload
    )
    safe_provider_response_validation = _plain_dict(
        provider_response_validation_payload
    )
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
    safe_preview_packet_policy = _plain_dict(preview_packet_policy_metadata)
    safe_provider_configuration = _plain_dict(provider_configuration_metadata)

    user_trigger_present = _user_trigger_present(safe_user_trigger)
    operator_confirmation_present = _operator_confirmation_present(
        safe_operator_confirmation
    )
    provider_response_normalization_accepted = (
        _provider_response_normalization_accepted(
            safe_provider_response_normalization
        )
    )
    normalized_provider_response_present = bool(
        safe_normalized_provider_response_contract
    )
    provider_response_validation_accepted = (
        _provider_response_validation_accepted(
            safe_provider_response_validation
        )
    )
    preview_packet_policy_present = _preview_packet_policy_present(
        safe_preview_packet_policy
    )
    provider_configuration_present = _provider_configuration_present(
        safe_provider_configuration
    )
    normalized_contract_contains_generated_output = _contains_generated_output(
        safe_normalized_provider_response_contract
    )
    candidate_contains_generated_output = _contains_generated_output(
        safe_provider_response_candidate
    )

    missing_inputs: list[str] = []
    if not user_trigger_present:
        missing_inputs.append("user_trigger_metadata")
    if not operator_confirmation_present:
        missing_inputs.append("operator_confirmation_metadata")
    if not safe_provider_response_normalization:
        missing_inputs.append("provider_response_normalization_payload")
    if not normalized_provider_response_present:
        missing_inputs.append("normalized_provider_response_contract_payload")
    if not safe_provider_response_validation:
        missing_inputs.append("provider_response_validation_payload")
    if not preview_packet_policy_present:
        missing_inputs.append("preview_packet_policy_metadata")
    if not provider_configuration_present:
        missing_inputs.append("provider_configuration_metadata")

    blocked_reasons: list[str] = []
    if not user_trigger_present:
        blocked_reasons.append("explicit user trigger required")
    if not operator_confirmation_present:
        blocked_reasons.append("operator confirmation required")
    if not safe_provider_response_normalization:
        blocked_reasons.append("provider response normalization payload required")
    elif not provider_response_normalization_accepted:
        blocked_reasons.append(
            "provider response normalization must be accepted before preview packet"
        )
    if not normalized_provider_response_present:
        blocked_reasons.append("normalized provider response contract payload required")
    if normalized_contract_contains_generated_output:
        blocked_reasons.append(
            "normalized provider response contract must not include generated tailoring output"
        )
    if not safe_provider_response_validation:
        blocked_reasons.append("provider response validation payload required")
    elif not provider_response_validation_accepted:
        blocked_reasons.append(
            "provider response validation must be accepted before preview packet"
        )
    if candidate_contains_generated_output:
        blocked_reasons.append(
            "provider response candidate must not include generated tailoring output"
        )
    if not preview_packet_policy_present:
        blocked_reasons.append("preview packet policy metadata required")
    if not provider_configuration_present:
        blocked_reasons.append("provider configuration metadata required")

    preview_packet_ready = (
        user_trigger_present
        and operator_confirmation_present
        and provider_response_normalization_accepted
        and normalized_provider_response_present
        and not normalized_contract_contains_generated_output
        and provider_response_validation_accepted
        and not candidate_contains_generated_output
        and preview_packet_policy_present
        and provider_configuration_present
    )
    preview_packet_accepted_for_future_manual_preview = preview_packet_ready
    contract_status = STATUS_READY if preview_packet_ready else STATUS_BLOCKED

    if not user_trigger_present:
        next_safe_step = "require_explicit_user_trigger"
    elif not operator_confirmation_present:
        next_safe_step = "require_operator_confirmation"
    elif (
        not safe_provider_response_normalization
        or not provider_response_normalization_accepted
    ):
        next_safe_step = "provide_accepted_provider_response_normalization_payload"
    elif not normalized_provider_response_present:
        next_safe_step = "provide_normalized_provider_response_contract_payload"
    elif normalized_contract_contains_generated_output:
        next_safe_step = "provide_normalized_response_without_tailoring_output"
    elif (
        not safe_provider_response_validation
        or not provider_response_validation_accepted
    ):
        next_safe_step = "provide_accepted_provider_response_validation_payload"
    elif candidate_contains_generated_output:
        next_safe_step = "provide_response_candidate_without_tailoring_output"
    elif not preview_packet_policy_present:
        next_safe_step = "provide_preview_packet_policy_metadata"
    elif not provider_configuration_present:
        next_safe_step = "provide_provider_configuration_metadata"
    else:
        next_safe_step = (
            "manual_review_normalized_response_preview_packet_without_live_call"
        )

    preview_packet_inputs = {
        "provider_response_normalization_accepted": (
            provider_response_normalization_accepted
        ),
        "provider_response_normalization_status": (
            safe_provider_response_normalization.get("contract_status", "")
        ),
        "normalized_provider_response_contract_keys": sorted(
            safe_normalized_provider_response_contract.keys()
        ),
        "provider_response_validation_accepted": (
            provider_response_validation_accepted
        ),
        "provider_response_validation_status": (
            safe_provider_response_validation.get("contract_status", "")
        ),
        "provider_response_candidate_keys": sorted(
            safe_provider_response_candidate.keys()
        ),
        "phase29_provider_call_dry_run_packet_keys": sorted(
            safe_provider_call_dry_run_packet.keys()
        ),
        "phase28_provider_call_boundary_keys": sorted(
            safe_provider_call_boundary.keys()
        ),
        "phase27_provider_request_envelope_keys": sorted(
            safe_provider_request_envelope.keys()
        ),
        "user_trigger_metadata": safe_user_trigger,
        "operator_confirmation_metadata": safe_operator_confirmation,
        "preview_packet_policy_metadata": safe_preview_packet_policy,
        "provider_configuration_metadata": safe_provider_configuration,
        "preview_packet_ready": preview_packet_ready,
    }
    deterministic_preview_packet_key = _deterministic_key(
        preview_packet_inputs
    )

    preview_packet_findings = [
        {
            "finding": "provider_response_normalization_accepted",
            "accepted": provider_response_normalization_accepted,
            "read_only": True,
        },
        {
            "finding": "normalized_provider_response_present",
            "accepted": normalized_provider_response_present,
            "read_only": True,
        },
        {
            "finding": "provider_response_validation_accepted",
            "accepted": provider_response_validation_accepted,
            "read_only": True,
        },
        {
            "finding": "no_generated_tailoring_output_in_preview_packet_inputs",
            "accepted": not (
                normalized_contract_contains_generated_output
                or candidate_contains_generated_output
            ),
            "read_only": True,
        },
        {
            "finding": "normalized_response_preview_packet_ready",
            "accepted": preview_packet_ready,
            "read_only": True,
        },
    ]

    normalized_response_preview_packet_contract = {
        "normalized_response_preview_packet_contract_status": contract_status,
        "deterministic_preview_packet_key": deterministic_preview_packet_key,
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "normalized_response_preview_packet_contract_only": True,
        "preview_packet_only": True,
        "requires_user_trigger": True,
        "operator_confirmation_required": True,
        "manual_acceptance_required": True,
        "provider_response_normalization_required": True,
        "provider_response_normalization_accepted": (
            provider_response_normalization_accepted
        ),
        "normalized_provider_response_required": True,
        "normalized_provider_response_present": (
            normalized_provider_response_present
        ),
        "provider_response_validation_required": True,
        "provider_response_validation_accepted": (
            provider_response_validation_accepted
        ),
        "preview_packet_policy_required": True,
        "preview_packet_policy_present": preview_packet_policy_present,
        "provider_configuration_required": True,
        "provider_configuration_present": provider_configuration_present,
        "preview_packet_ready": preview_packet_ready,
        "preview_packet_accepted_for_future_manual_preview": (
            preview_packet_accepted_for_future_manual_preview
        ),
        "normalized_response_key_inventory": sorted(
            safe_normalized_provider_response_contract.keys()
        ),
        "normalization_contract_status": (
            safe_provider_response_normalization.get("contract_status", "")
        ),
        "validation_contract_status": (
            safe_provider_response_validation.get("contract_status", "")
        ),
        "contains_generated_tailoring_text": (
            normalized_contract_contains_generated_output
            or candidate_contains_generated_output
        ),
        "contains_real_tailoring_output": (
            normalized_contract_contains_generated_output
            or candidate_contains_generated_output
        ),
        "provider_call_performed": False,
        "network_call_performed": False,
        "dispatch_performed": False,
        "tailoring_runtime_call_performed": False,
        "ai_tailoring_generation_performed": False,
        "real_tailoring_output_created": False,
    }

    return {
        "phase": PHASE,
        "contract_version": CONTRACT_VERSION,
        "contract_status": contract_status,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
        "manual_review_only": True,
        "normalized_response_preview_packet_contract_only": True,
        "preview_packet_only": True,
        "requires_user_trigger": True,
        "user_trigger_present": user_trigger_present,
        "operator_confirmation_required": True,
        "operator_confirmation_present": operator_confirmation_present,
        "manual_acceptance_required": True,
        "provider_response_normalization_required": True,
        "provider_response_normalization_accepted": (
            provider_response_normalization_accepted
        ),
        "normalized_provider_response_required": True,
        "normalized_provider_response_present": (
            normalized_provider_response_present
        ),
        "provider_response_validation_required": True,
        "provider_response_validation_accepted": (
            provider_response_validation_accepted
        ),
        "preview_packet_policy_required": True,
        "preview_packet_policy_present": preview_packet_policy_present,
        "provider_configuration_required": True,
        "provider_configuration_present": provider_configuration_present,
        "preview_packet_ready": preview_packet_ready,
        "preview_packet_accepted_for_future_manual_preview": (
            preview_packet_accepted_for_future_manual_preview
        ),
        "blocked_reasons": blocked_reasons,
        "missing_inputs": missing_inputs,
        "preview_packet_findings": preview_packet_findings,
        "normalized_response_preview_packet_contract": (
            normalized_response_preview_packet_contract
        ),
        "deterministic_preview_packet_key": deterministic_preview_packet_key,
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
