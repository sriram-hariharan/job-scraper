"""Default-off provider response validation for exact resume change sets."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


PHASE = "45A"
REQUIRED_PROPOSAL_FIELDS = (
    "proposal_id",
    "change_type",
    "target_section",
    "target_identifier",
    "current_text",
    "proposed_text",
    "change_reason",
    "jd_terms_supported",
    "resume_evidence_used",
    "risk_flags",
    "manual_review_required",
    "requires_user_acceptance",
)
REQUIRED_SAFETY_FLAGS = (
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "application_submission_performed",
)
TEXT_FIELDS = (
    "proposal_id",
    "change_type",
    "target_section",
    "target_identifier",
    "current_text",
    "proposed_text",
    "change_reason",
)
LIST_FIELDS = (
    "jd_terms_supported",
    "resume_evidence_used",
    "risk_flags",
)
FALSE_ACTION_KEYS = (
    "provider_response_normalization_performed",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "application_submission_performed",
    "submission_performed",
    "auto_apply_performed",
    "auto_submit_performed",
)


def _bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y"}:
            return True
        if text in {"0", "false", "no", "n"}:
            return False
    return default if value is None else bool(value)


def _int_at_least(value: Any, default: int, minimum: int) -> int:
    if isinstance(value, bool):
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return parsed if parsed >= minimum else default


def _policy(value: dict[str, Any] | None) -> dict[str, Any]:
    supplied = value if isinstance(value, dict) else {}
    return {
        "require_refined_change_proposals": _bool(
            supplied.get("require_refined_change_proposals"),
            True,
        ),
        "require_known_proposal_ids": _bool(
            supplied.get("require_known_proposal_ids"),
            False,
        ),
        "allow_extra_top_level_keys": _bool(
            supplied.get("allow_extra_top_level_keys"),
            True,
        ),
        "allow_empty_refined_change_proposals": _bool(
            supplied.get("allow_empty_refined_change_proposals"),
            False,
        ),
        "max_refined_change_proposals": _int_at_least(
            supplied.get("max_refined_change_proposals"),
            12,
            0,
        ),
        "max_text_length": _int_at_least(
            supplied.get("max_text_length"),
            3000,
            1,
        ),
        "required_boolean_safety_flags": _bool(
            supplied.get("required_boolean_safety_flags"),
            True,
        ),
    }


def _resolve_provider_response(
    provider_response: Any,
    provider_call_result: Any,
) -> tuple[Any, str]:
    if provider_response is not None:
        return deepcopy(provider_response), "provider_response"
    if not isinstance(provider_call_result, dict):
        return None, "missing"
    direct = provider_call_result.get("provider_response")
    if direct is not None:
        return deepcopy(direct), "provider_call_result.provider_response"
    nested = provider_call_result.get("provider_call_result")
    if isinstance(nested, dict) and nested.get("provider_response") is not None:
        return (
            deepcopy(nested.get("provider_response")),
            "provider_call_result.provider_call_result.provider_response",
        )
    return None, "missing"


def _parse_provider_response(value: Any) -> tuple[Any, str, str]:
    if value is None:
        return None, "missing", "provider response missing"
    if isinstance(value, dict):
        return deepcopy(value), "dict", ""
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None, "invalid_raw_string", "provider response string is empty"
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            return None, "invalid_json", f"provider response is not valid JSON: {exc.msg}"
        if isinstance(parsed, dict):
            return deepcopy(parsed), "json_string_dict", ""
        return deepcopy(parsed), "json_string_non_dict", "parsed provider response must be a dictionary"
    return deepcopy(value), "non_dict", "provider response must be a dictionary or JSON object string"


def _known_proposal_ids(original_request_packet: Any) -> list[str]:
    if not isinstance(original_request_packet, dict):
        return []
    rows = original_request_packet.get("included_change_proposals")
    if not isinstance(rows, list):
        request_packet = original_request_packet.get("request_packet")
        if isinstance(request_packet, dict):
            rows = request_packet.get("included_change_proposals")
    ids: list[str] = []
    seen: set[str] = set()
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            proposal_id = str(row.get("proposal_id") or "").strip()
            if proposal_id and proposal_id not in seen:
                seen.add(proposal_id)
                ids.append(proposal_id)
    return ids


def _proposal_label(index: int, proposal: Any) -> str:
    if isinstance(proposal, dict):
        proposal_id = str(proposal.get("proposal_id") or "").strip()
        if proposal_id:
            return proposal_id
    return f"index:{index}"


def _extra_top_level_keys(parsed: dict[str, Any]) -> list[str]:
    allowed = set(REQUIRED_SAFETY_FLAGS)
    allowed.add("refined_change_proposals")
    extras: list[str] = []
    for key in sorted(str(key) for key in parsed.keys()):
        if key not in allowed:
            extras.append(key)
    return extras


def _stable_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase45a-provider-response-validation-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_controlled_exact_resume_change_set_provider_response_validation_default_off(
    provider_response: Any = None,
    provider_call_result: dict[str, Any] | None = None,
    original_request_packet: dict[str, Any] | None = None,
    validation_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate refined exact resume change proposals without side effects."""

    policy = _policy(validation_policy)
    response_value, response_source = _resolve_provider_response(
        provider_response,
        provider_call_result,
    )
    parsed_response, parse_status, parse_error = _parse_provider_response(response_value)
    provider_response_present = response_value is not None
    provider_call_result_present = isinstance(provider_call_result, dict)
    original_request_packet_present = isinstance(original_request_packet, dict)
    known_ids = _known_proposal_ids(original_request_packet)
    known_id_set = set(known_ids)
    errors: list[str] = []
    warnings: list[str] = []
    findings: list[dict[str, Any]] = []
    missing_inputs: list[str] = []
    missing_required_fields_by_proposal: dict[str, list[str]] = {}
    invalid_safety_flags: dict[str, Any] = {}
    unknown_proposal_ids: list[str] = []
    refined_change_proposals: list[dict[str, Any]] = []
    invalid_refined_change_proposal_count = 0

    if not provider_response_present:
        missing_inputs.append("provider_response")
        errors.append("provider response required")
    if parse_error:
        errors.append(parse_error)

    if isinstance(parsed_response, dict):
        extra_keys = _extra_top_level_keys(parsed_response)
        if extra_keys and not policy["allow_extra_top_level_keys"]:
            errors.append("extra top-level keys are not allowed")
        if extra_keys and policy["allow_extra_top_level_keys"]:
            warnings.append("extra top-level keys ignored for validation")

        if policy["required_boolean_safety_flags"]:
            for key in REQUIRED_SAFETY_FLAGS:
                if parsed_response.get(key) is not False:
                    invalid_safety_flags[key] = deepcopy(parsed_response.get(key))
            if invalid_safety_flags:
                errors.append("required safety flags must be false")

        proposals = parsed_response.get("refined_change_proposals")
        if proposals is None:
            if policy["require_refined_change_proposals"]:
                errors.append("refined_change_proposals required")
        elif not isinstance(proposals, list):
            errors.append("refined_change_proposals must be a list")
        else:
            if not proposals and not policy["allow_empty_refined_change_proposals"]:
                errors.append("refined_change_proposals must not be empty")
            if len(proposals) > policy["max_refined_change_proposals"]:
                errors.append("too many refined_change_proposals")

            for index, proposal in enumerate(proposals):
                label = _proposal_label(index, proposal)
                if not isinstance(proposal, dict):
                    invalid_refined_change_proposal_count += 1
                    missing_required_fields_by_proposal[label] = list(
                        REQUIRED_PROPOSAL_FIELDS
                    )
                    continue

                missing_fields: list[str] = []
                for field in REQUIRED_PROPOSAL_FIELDS:
                    if field not in proposal:
                        missing_fields.append(field)
                for field in TEXT_FIELDS:
                    if field in proposal and not isinstance(proposal.get(field), str):
                        missing_fields.append(f"{field}:string")
                    if (
                        field in proposal
                        and len(str(proposal.get(field) or ""))
                        > policy["max_text_length"]
                    ):
                        missing_fields.append(f"{field}:max_text_length")
                for field in LIST_FIELDS:
                    if field in proposal and not isinstance(proposal.get(field), list):
                        missing_fields.append(f"{field}:list")
                for field in ("manual_review_required", "requires_user_acceptance"):
                    if field in proposal and proposal.get(field) is not True:
                        missing_fields.append(f"{field}:true")

                proposal_id = str(proposal.get("proposal_id") or "").strip()
                if (
                    policy["require_known_proposal_ids"]
                    and proposal_id
                    and known_id_set
                    and proposal_id not in known_id_set
                ):
                    unknown_proposal_ids.append(proposal_id)
                if policy["require_known_proposal_ids"] and proposal_id and not known_id_set:
                    unknown_proposal_ids.append(proposal_id)

                if missing_fields:
                    invalid_refined_change_proposal_count += 1
                    missing_required_fields_by_proposal[label] = list(missing_fields)
                else:
                    refined_change_proposals.append(deepcopy(proposal))
    elif provider_response_present:
        errors.append("parsed provider response must be a dictionary")

    if invalid_refined_change_proposal_count:
        errors.append("invalid refined change proposals present")
    if unknown_proposal_ids and policy["require_known_proposal_ids"]:
        errors.append("unknown proposal ids present")

    valid_refined_change_proposal_count = len(refined_change_proposals)
    provider_response_valid = not errors
    validation_summary = {
        "provider_response_source": response_source,
        "provider_response_valid": provider_response_valid,
        "valid_refined_change_proposal_count": valid_refined_change_proposal_count,
        "invalid_refined_change_proposal_count": invalid_refined_change_proposal_count,
        "unknown_proposal_id_count": len(unknown_proposal_ids),
        "missing_input_count": len(missing_inputs),
        "error_count": len(errors),
        "warning_count": len(warnings),
    }
    findings.append(
        {
            "finding": "provider_response_present",
            "accepted": provider_response_present,
            "read_only": True,
        }
    )
    findings.append(
        {
            "finding": "refined_change_proposals_schema_valid",
            "accepted": provider_response_valid,
            "read_only": True,
        }
    )
    findings.append(
        {
            "finding": "manual_user_control_required",
            "accepted": True,
            "read_only": True,
        }
    )
    key_payload = {
        "parse_status": parse_status,
        "policy": policy,
        "known_proposal_ids": known_ids,
        "validation_summary": validation_summary,
        "validation_errors": errors,
        "validation_warnings": warnings,
    }
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_provider_response_validation": True,
        "read_only": True,
        "advisory_only": True,
        "validation_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "provider_response_present": provider_response_present,
        "provider_call_result_present": provider_call_result_present,
        "original_request_packet_present": original_request_packet_present,
        "validation_policy": deepcopy(policy),
        "parsed_provider_response": deepcopy(parsed_response),
        "provider_response_parse_status": parse_status,
        "provider_response_valid": provider_response_valid,
        "validation_errors": list(errors),
        "validation_warnings": list(warnings),
        "refined_change_proposals": deepcopy(refined_change_proposals),
        "valid_refined_change_proposal_count": valid_refined_change_proposal_count,
        "invalid_refined_change_proposal_count": invalid_refined_change_proposal_count,
        "known_proposal_ids": list(known_ids),
        "unknown_proposal_ids": list(unknown_proposal_ids),
        "missing_required_fields_by_proposal": deepcopy(
            missing_required_fields_by_proposal
        ),
        "invalid_safety_flags": deepcopy(invalid_safety_flags),
        "validation_summary": validation_summary,
        "validation_findings": findings,
        "missing_inputs": list(missing_inputs),
        "validation_key": _stable_key(key_payload),
        "provider_response_validation_performed": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload
