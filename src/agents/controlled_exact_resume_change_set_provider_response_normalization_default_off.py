"""Default-off provider response normalization for exact resume change sets."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


PHASE = "46A"
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
    "provider_response_validation_performed",
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
        "require_valid_provider_response": _bool(
            supplied.get("require_valid_provider_response"),
            True,
        ),
        "include_invalid_proposals": _bool(
            supplied.get("include_invalid_proposals"),
            False,
        ),
        "max_normalized_change_proposals": _int_at_least(
            supplied.get("max_normalized_change_proposals"),
            12,
            0,
        ),
        "trim_text": _bool(supplied.get("trim_text"), True),
        "max_text_length": _int_at_least(
            supplied.get("max_text_length"),
            3000,
            1,
        ),
        "preserve_before_after_text": _bool(
            supplied.get("preserve_before_after_text"),
            True,
        ),
        "preserve_risk_flags": _bool(supplied.get("preserve_risk_flags"), True),
        "default_manual_review_required": _bool(
            supplied.get("default_manual_review_required"),
            True,
        ),
        "default_requires_user_acceptance": _bool(
            supplied.get("default_requires_user_acceptance"),
            True,
        ),
    }


def _resolve_validation_result(value: Any) -> tuple[dict[str, Any] | None, str]:
    if not isinstance(value, dict):
        return None, "missing"
    nested = value.get("validation_result")
    if isinstance(nested, dict):
        return deepcopy(nested), "validation_result.validation_result"
    return deepcopy(value), "validation_result"


def _resolve_provider_response(
    *,
    validation_result: dict[str, Any] | None,
    provider_response: Any,
) -> tuple[Any, str]:
    if provider_response is not None:
        return deepcopy(provider_response), "provider_response"
    if isinstance(validation_result, dict):
        parsed = validation_result.get("parsed_provider_response")
        if parsed is not None:
            return deepcopy(parsed), "validation_result.parsed_provider_response"
        nested = validation_result.get("validation_result")
        if isinstance(nested, dict) and nested.get("parsed_provider_response") is not None:
            return (
                deepcopy(nested.get("parsed_provider_response")),
                "validation_result.validation_result.parsed_provider_response",
            )
    return None, "missing"


def _proposal_rows(
    *,
    validation_result: dict[str, Any] | None,
    provider_response: Any,
) -> tuple[list[Any], str]:
    if isinstance(validation_result, dict) and isinstance(
        validation_result.get("refined_change_proposals"),
        list,
    ):
        return list(validation_result["refined_change_proposals"]), (
            "validation_result.refined_change_proposals"
        )
    if isinstance(provider_response, dict) and isinstance(
        provider_response.get("refined_change_proposals"),
        list,
    ):
        return list(provider_response["refined_change_proposals"]), (
            "provider_response.refined_change_proposals"
        )
    return [], "missing"


def _original_proposal_ids(value: Any) -> list[str]:
    if isinstance(value, dict):
        rows = value.get("change_proposals")
    else:
        rows = value
    ids: list[str] = []
    seen: set[str] = set()
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            proposal_id = _clean_text(row.get("proposal_id"), trim=True)
            if proposal_id and proposal_id not in seen:
                seen.add(proposal_id)
                ids.append(proposal_id)
    return ids


def _clean_text(value: Any, *, trim: bool) -> str:
    text = "" if value is None else str(value)
    return text.strip() if trim else text


def _bounded_text(
    value: Any,
    *,
    field: str,
    proposal_id: str,
    policy: dict[str, Any],
    warnings: list[str],
) -> str:
    text = _clean_text(value, trim=policy["trim_text"])
    max_length = policy["max_text_length"]
    if len(text) > max_length:
        warnings.append(f"{proposal_id or 'unknown'}:{field}:truncated_to_max_text_length")
        return text[:max_length]
    return text


def _text_values(value: Any, *, trim: bool) -> list[str]:
    values: list[str] = []
    if isinstance(value, dict):
        for key in sorted(value.keys()):
            values.extend(_text_values(value.get(key), trim=trim))
        return values
    if isinstance(value, list | tuple | set):
        items = list(value)
    else:
        items = [value]
    for item in items:
        if isinstance(item, dict):
            values.extend(_text_values(item, trim=trim))
            continue
        text = _clean_text(item, trim=trim)
        if text:
            values.append(text)
    return values


def _normalized_list(value: Any, *, trim: bool) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for text in _text_values(value, trim=trim):
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _proposal_missing_fields(proposal: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    for field in REQUIRED_PROPOSAL_FIELDS:
        if field not in proposal:
            missing.append(field)
    return missing


def _source_status(validation_result: dict[str, Any] | None) -> str:
    if not isinstance(validation_result, dict):
        return "unvalidated"
    return "valid" if validation_result.get("provider_response_valid") is True else "invalid"


def _normalized_proposal(
    proposal: dict[str, Any],
    *,
    index: int,
    source_validation_status: str,
    policy: dict[str, Any],
    warnings: list[str],
    invalid_notes: list[str],
) -> dict[str, Any]:
    proposal_id = _bounded_text(
        proposal.get("proposal_id") or f"index:{index}",
        field="proposal_id",
        proposal_id=str(proposal.get("proposal_id") or f"index:{index}"),
        policy=policy,
        warnings=warnings,
    )
    notes: list[str] = []
    if invalid_notes:
        notes.extend(invalid_notes)
    if source_validation_status == "unvalidated":
        notes.append("source provider response was not validated")
    if source_validation_status == "invalid":
        notes.append("source provider response was invalid")
    current_text = (
        _bounded_text(
            proposal.get("current_text"),
            field="current_text",
            proposal_id=proposal_id,
            policy=policy,
            warnings=warnings,
        )
        if policy["preserve_before_after_text"]
        else ""
    )
    proposed_text = (
        _bounded_text(
            proposal.get("proposed_text"),
            field="proposed_text",
            proposal_id=proposal_id,
            policy=policy,
            warnings=warnings,
        )
        if policy["preserve_before_after_text"]
        else ""
    )
    return {
        "proposal_id": proposal_id,
        "change_type": _bounded_text(
            proposal.get("change_type"),
            field="change_type",
            proposal_id=proposal_id,
            policy=policy,
            warnings=warnings,
        ),
        "target_section": _bounded_text(
            proposal.get("target_section"),
            field="target_section",
            proposal_id=proposal_id,
            policy=policy,
            warnings=warnings,
        ),
        "target_identifier": _bounded_text(
            proposal.get("target_identifier"),
            field="target_identifier",
            proposal_id=proposal_id,
            policy=policy,
            warnings=warnings,
        ),
        "current_text": current_text,
        "proposed_text": proposed_text,
        "change_reason": _bounded_text(
            proposal.get("change_reason"),
            field="change_reason",
            proposal_id=proposal_id,
            policy=policy,
            warnings=warnings,
        ),
        "jd_terms_supported": _normalized_list(
            proposal.get("jd_terms_supported"),
            trim=policy["trim_text"],
        ),
        "resume_evidence_used": _normalized_list(
            proposal.get("resume_evidence_used"),
            trim=policy["trim_text"],
        ),
        "risk_flags": (
            _normalized_list(proposal.get("risk_flags"), trim=policy["trim_text"])
            if policy["preserve_risk_flags"]
            else []
        ),
        "manual_review_required": (
            proposal.get("manual_review_required") is True
            or policy["default_manual_review_required"] is True
        ),
        "requires_user_acceptance": (
            proposal.get("requires_user_acceptance") is True
            or policy["default_requires_user_acceptance"] is True
        ),
        "source_validation_status": source_validation_status,
        "normalization_notes": list(notes),
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
    }


def _group_by_type(proposals: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for proposal in proposals:
        change_type = proposal.get("change_type") or "unknown"
        if change_type not in grouped:
            grouped[change_type] = []
        grouped[change_type].append(deepcopy(proposal))
    return grouped


def _counts_by_type(proposals: list[dict[str, Any]]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for proposal in proposals:
        change_type = proposal.get("change_type") or "unknown"
        counts[change_type] = counts.get(change_type, 0) + 1
    return counts


def _stable_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase46a-provider-response-normalization-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
    validation_result: dict[str, Any] | None = None,
    provider_response: dict[str, Any] | None = None,
    original_change_proposals: list[dict[str, Any]] | dict[str, Any] | None = None,
    normalization_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize validated refined change proposals without side effects."""

    policy = _policy(normalization_policy)
    resolved_validation, validation_source = _resolve_validation_result(validation_result)
    response_value, response_source = _resolve_provider_response(
        validation_result=resolved_validation,
        provider_response=provider_response,
    )
    validation_result_present = isinstance(resolved_validation, dict)
    provider_response_present = response_value is not None
    original_change_proposals_present = isinstance(
        original_change_proposals,
        (dict, list),
    )
    provider_response_valid = (
        bool(resolved_validation.get("provider_response_valid"))
        if validation_result_present
        else False
    )
    source_validation_status = _source_status(resolved_validation)
    missing_inputs: list[str] = []
    errors: list[str] = []
    warnings: list[str] = []
    findings: list[dict[str, Any]] = []

    if not validation_result_present and not provider_response_present:
        missing_inputs.append("validation_result_or_provider_response")
        errors.append("validation result or provider response required")
    if policy["require_valid_provider_response"] and not provider_response_valid:
        if validation_result_present:
            errors.append("valid provider response required before normalization")
        elif provider_response_present:
            errors.append("validated provider response required before normalization")

    proposal_rows, proposal_source = _proposal_rows(
        validation_result=resolved_validation,
        provider_response=response_value,
    )
    if not proposal_rows and not errors:
        warnings.append("no refined change proposals available to normalize")

    normalized: list[dict[str, Any]] = []
    invalid_proposal_count = 0
    excluded_invalid_proposal_count = 0
    original_ids = _original_proposal_ids(original_change_proposals)
    limit = policy["max_normalized_change_proposals"]
    truncated_by_limit = len(proposal_rows) > limit
    if truncated_by_limit:
        warnings.append("normalized refined change proposals truncated to policy limit")

    if not errors:
        for index, row in enumerate(proposal_rows[:limit]):
            invalid_notes: list[str] = []
            if not isinstance(row, dict):
                invalid_proposal_count += 1
                invalid_notes.append("proposal item was not a dictionary")
                if not policy["include_invalid_proposals"]:
                    excluded_invalid_proposal_count += 1
                    continue
                row = {"proposal_id": f"index:{index}"}
            missing = _proposal_missing_fields(row)
            if missing:
                invalid_proposal_count += 1
                invalid_notes.append("missing fields: " + ", ".join(missing))
                if not policy["include_invalid_proposals"]:
                    excluded_invalid_proposal_count += 1
                    continue
            normalized.append(
                _normalized_proposal(
                    row,
                    index=index,
                    source_validation_status=source_validation_status,
                    policy=policy,
                    warnings=warnings,
                    invalid_notes=invalid_notes,
                )
            )

    grouped = _group_by_type(normalized)
    counts_by_type = _counts_by_type(normalized)
    summary = {
        "normalized_refined_change_proposal_count": len(normalized),
        "input_refined_change_proposal_count": len(proposal_rows),
        "invalid_refined_change_proposal_count": invalid_proposal_count,
        "excluded_invalid_refined_change_proposal_count": (
            excluded_invalid_proposal_count
        ),
        "truncated_by_policy_limit": truncated_by_limit,
        "counts_by_type": counts_by_type,
        "known_original_change_proposal_ids": list(original_ids),
        "all_manual_review_required": all(
            proposal.get("manual_review_required") is True for proposal in normalized
        )
        if normalized
        else True,
        "all_require_user_acceptance": all(
            proposal.get("requires_user_acceptance") is True for proposal in normalized
        )
        if normalized
        else True,
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
    }
    findings.append(
        {
            "finding": "validation_result_present",
            "accepted": validation_result_present,
            "read_only": True,
        }
    )
    findings.append(
        {
            "finding": "provider_response_normalized",
            "accepted": bool(normalized),
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
        "validation_source": validation_source,
        "response_source": response_source,
        "proposal_source": proposal_source,
        "provider_response_valid": provider_response_valid,
        "policy": policy,
        "summary": summary,
        "errors": errors,
        "warnings": warnings,
    }
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_provider_response_normalization": True,
        "read_only": True,
        "advisory_only": True,
        "normalization_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "validation_result_present": validation_result_present,
        "provider_response_present": provider_response_present,
        "original_change_proposals_present": original_change_proposals_present,
        "normalization_policy": deepcopy(policy),
        "provider_response_valid": provider_response_valid,
        "normalized_refined_change_proposals": deepcopy(normalized),
        "normalized_change_proposals_by_type": grouped,
        "normalized_change_set_summary": summary,
        "normalization_errors": list(errors),
        "normalization_warnings": list(warnings),
        "normalization_findings": findings,
        "missing_inputs": list(missing_inputs),
        "normalization_key": _stable_key(key_payload),
        "provider_response_normalization_performed": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload
