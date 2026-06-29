"""Default-off manual review packets for exact resume change sets."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


PHASE = "47A"
KNOWN_CHANGE_TYPES = {"summary", "skill", "bullet", "project", "evidence_note"}
PACKET_TEXT_FIELDS = (
    "proposal_id",
    "change_type",
    "target_section",
    "target_identifier",
    "current_text",
    "proposed_text",
    "change_reason",
    "source_validation_status",
)
FALSE_ACTION_KEYS = (
    "ui_readback_performed",
    "user_acceptance_performed",
    "resume_change_applied",
    "resume_change_proposals_created",
    "provider_response_validation_performed",
    "provider_response_normalization_performed",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
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
        "max_review_packets": _int_at_least(
            supplied.get("max_review_packets"),
            12,
            0,
        ),
        "include_before_after_text": _bool(
            supplied.get("include_before_after_text"),
            True,
        ),
        "include_risk_flags": _bool(supplied.get("include_risk_flags"), True),
        "include_evidence": _bool(supplied.get("include_evidence"), True),
        "require_manual_review": _bool(supplied.get("require_manual_review"), True),
        "require_user_acceptance": _bool(
            supplied.get("require_user_acceptance"),
            True,
        ),
        "group_by_change_type": _bool(supplied.get("group_by_change_type"), True),
        "sort_by_change_type": _bool(supplied.get("sort_by_change_type"), False),
        "include_invalid_proposals": _bool(
            supplied.get("include_invalid_proposals"),
            False,
        ),
    }


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _text_values(value: Any) -> list[str]:
    if isinstance(value, dict):
        values: list[str] = []
        for key in sorted(value.keys()):
            values.extend(_text_values(value.get(key)))
        return values
    if isinstance(value, list | tuple | set):
        items = list(value)
    else:
        items = [value]
    result: list[str] = []
    for item in items:
        if isinstance(item, dict):
            result.extend(_text_values(item))
            continue
        text = _clean_text(item)
        if text:
            result.append(text)
    return result


def _normalized_list(value: Any) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for text in _text_values(value):
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        result.append(text)
    return result


def _flatten_grouped(value: Any) -> list[Any]:
    rows: list[Any] = []
    if not isinstance(value, dict):
        return rows
    for key in sorted(value.keys()):
        group = value.get(key)
        if isinstance(group, list):
            rows.extend(deepcopy(group))
    return rows


def _resolve_rows(
    normalized_change_proposals: Any,
    normalization_result: Any,
) -> tuple[list[Any], str, bool, bool, list[str]]:
    if isinstance(normalized_change_proposals, list):
        return (
            deepcopy(normalized_change_proposals),
            "normalized_change_proposals",
            True,
            isinstance(normalization_result, dict),
            [],
        )
    result_present = isinstance(normalization_result, dict)
    if not result_present:
        return [], "missing", False, False, ["normalized_change_proposals"]
    direct = normalization_result.get("normalized_refined_change_proposals")
    if isinstance(direct, list):
        return deepcopy(direct), "normalization_result.normalized_refined_change_proposals", False, True, []
    nested = normalization_result.get("normalization_result")
    if isinstance(nested, dict):
        nested_rows = nested.get("normalized_refined_change_proposals")
        if isinstance(nested_rows, list):
            return (
                deepcopy(nested_rows),
                "normalization_result.normalization_result.normalized_refined_change_proposals",
                False,
                True,
                [],
            )
    grouped = normalization_result.get("normalized_change_proposals_by_type")
    grouped_rows = _flatten_grouped(grouped)
    if grouped_rows:
        return deepcopy(grouped_rows), "normalization_result.normalized_change_proposals_by_type", False, True, []
    if isinstance(nested, dict):
        nested_grouped_rows = _flatten_grouped(
            nested.get("normalized_change_proposals_by_type")
        )
        if nested_grouped_rows:
            return (
                deepcopy(nested_grouped_rows),
                "normalization_result.normalization_result.normalized_change_proposals_by_type",
                False,
                True,
                [],
            )
    return [], "missing", False, True, ["normalized_change_proposals"]


def _recommended_action(proposal: dict[str, Any], *, invalid: bool) -> tuple[str, str]:
    if invalid:
        return "reject_invalid", "proposal is invalid for manual review"
    change_type = _clean_text(proposal.get("change_type")).lower()
    if not change_type or change_type not in KNOWN_CHANGE_TYPES:
        return "inspect_unknown", "change type is missing or unknown"
    risk_flags = _normalized_list(proposal.get("risk_flags"))
    if risk_flags:
        return "review_risk", "risk flags require operator review"
    return "review_change", "valid normalized proposal requires manual review"


def _packet_id(index: int, proposal: dict[str, Any], action: str) -> str:
    payload = {
        "phase": PHASE,
        "index": index,
        "proposal_id": _clean_text(proposal.get("proposal_id")),
        "change_type": _clean_text(proposal.get("change_type")),
        "target_section": _clean_text(proposal.get("target_section")),
        "target_identifier": _clean_text(proposal.get("target_identifier")),
        "action": action,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase47a-review-packet-" + sha256(encoded.encode("utf-8")).hexdigest()[:16]


def _packet(
    proposal: dict[str, Any],
    *,
    index: int,
    display_order: int,
    policy: dict[str, Any],
    review_context: dict[str, Any],
    invalid: bool,
) -> dict[str, Any]:
    action, reason = _recommended_action(proposal, invalid=invalid)
    current_text = _clean_text(proposal.get("current_text")) if policy["include_before_after_text"] else ""
    proposed_text = _clean_text(proposal.get("proposed_text")) if policy["include_before_after_text"] else ""
    risk_flags = _normalized_list(proposal.get("risk_flags")) if policy["include_risk_flags"] else []
    evidence = (
        _normalized_list(proposal.get("resume_evidence_used"))
        if policy["include_evidence"]
        else []
    )
    packet = {
        "review_packet_id": _packet_id(index, proposal, action),
        "proposal_id": _clean_text(proposal.get("proposal_id")) or f"index:{index}",
        "change_type": _clean_text(proposal.get("change_type")),
        "target_section": _clean_text(proposal.get("target_section")),
        "target_identifier": _clean_text(proposal.get("target_identifier")),
        "current_text": current_text,
        "proposed_text": proposed_text,
        "change_reason": _clean_text(proposal.get("change_reason")),
        "jd_terms_supported": _normalized_list(proposal.get("jd_terms_supported")),
        "resume_evidence_used": evidence,
        "risk_flags": risk_flags,
        "source_validation_status": _clean_text(
            proposal.get("source_validation_status")
        ),
        "normalization_notes": _normalized_list(proposal.get("normalization_notes")),
        "manual_review_required": (
            proposal.get("manual_review_required") is True
            or policy["require_manual_review"] is True
        ),
        "requires_user_acceptance": (
            proposal.get("requires_user_acceptance") is True
            or policy["require_user_acceptance"] is True
        ),
        "recommended_operator_action": action,
        "review_reason": reason,
        "display_order": display_order,
        "review_context": deepcopy(review_context),
        "ui_readback_performed": False,
        "user_acceptance_performed": False,
        "resume_change_applied": False,
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
    }
    return packet


def _sortable_rows(rows: list[tuple[int, Any]], *, sort_by_change_type: bool) -> list[tuple[int, Any]]:
    if not sort_by_change_type:
        return list(rows)
    return sorted(
        rows,
        key=lambda item: (
            _clean_text(item[1].get("change_type") if isinstance(item[1], dict) else "").lower(),
            item[0],
        ),
    )


def _group_by_type(packets: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for packet in packets:
        change_type = packet.get("change_type") or "unknown"
        if change_type not in grouped:
            grouped[change_type] = []
        grouped[change_type].append(deepcopy(packet))
    return grouped


def _counts(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        key = value or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return counts


def _stable_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase47a-manual-review-packets-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def build_controlled_exact_resume_change_set_manual_review_packet_builder_default_off(
    normalized_change_proposals: list[dict[str, Any]] | None = None,
    normalization_result: dict[str, Any] | None = None,
    review_context: dict[str, Any] | None = None,
    review_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic manual review packets for normalized exact changes."""

    policy = _policy(review_policy)
    context = deepcopy(review_context) if isinstance(review_context, dict) else {}
    rows, source, explicit_present, result_present, missing_inputs = _resolve_rows(
        normalized_change_proposals,
        normalization_result,
    )
    indexed_rows = list(enumerate(rows))
    ordered_rows = _sortable_rows(indexed_rows, sort_by_change_type=policy["sort_by_change_type"])
    limit = policy["max_review_packets"]
    truncated = len(ordered_rows) > limit
    packets: list[dict[str, Any]] = []
    findings: list[dict[str, Any]] = []
    invalid_count = 0
    excluded_invalid_count = 0

    for display_index, (original_index, row) in enumerate(ordered_rows[:limit], start=1):
        invalid = not isinstance(row, dict)
        if invalid:
            invalid_count += 1
            findings.append(
                {
                    "finding": "invalid_normalized_change_proposal",
                    "index": original_index,
                    "included": policy["include_invalid_proposals"],
                    "reason": "proposal must be a dictionary",
                }
            )
            if not policy["include_invalid_proposals"]:
                excluded_invalid_count += 1
                continue
            row = {"proposal_id": f"index:{original_index}", "change_type": ""}
        packet = _packet(
            row,
            index=original_index,
            display_order=display_index,
            policy=policy,
            review_context=context,
            invalid=invalid,
        )
        packets.append(packet)

    if not rows and "normalized_change_proposals" not in missing_inputs:
        missing_inputs.append("normalized_change_proposals")
    if rows and not packets and "manual_review_packets" not in missing_inputs:
        missing_inputs.append("manual_review_packets")

    grouped = _group_by_type(packets) if policy["group_by_change_type"] else {}
    counts_by_type = _counts([_clean_text(packet.get("change_type")) for packet in packets])
    counts_by_action = _counts(
        [_clean_text(packet.get("recommended_operator_action")) for packet in packets]
    )
    summary = {
        "manual_review_packet_count": len(packets),
        "input_normalized_change_proposal_count": len(rows),
        "invalid_normalized_change_proposal_count": invalid_count,
        "excluded_invalid_normalized_change_proposal_count": excluded_invalid_count,
        "truncated_by_policy_limit": truncated,
        "counts_by_type": counts_by_type,
        "counts_by_action": counts_by_action,
        "all_manual_review_required": all(
            packet.get("manual_review_required") is True for packet in packets
        )
        if packets
        else True,
        "all_require_user_acceptance": all(
            packet.get("requires_user_acceptance") is True for packet in packets
        )
        if packets
        else True,
        "ui_readback_performed": False,
        "user_acceptance_performed": False,
        "resume_change_applied": False,
    }
    findings.append(
        {
            "finding": "normalized_change_proposals_source",
            "source": source,
            "accepted": bool(rows),
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
        "source": source,
        "policy": policy,
        "summary": summary,
        "missing_inputs": missing_inputs,
    }
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_manual_review_packet_builder": True,
        "read_only": True,
        "advisory_only": True,
        "manual_review_packet_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "normalized_change_proposals_present": explicit_present or bool(rows),
        "normalization_result_present": result_present,
        "review_context_present": isinstance(review_context, dict),
        "review_policy": deepcopy(policy),
        "manual_review_packets": deepcopy(packets),
        "manual_review_packets_by_type": grouped,
        "manual_review_packet_summary": summary,
        "review_packet_findings": findings,
        "missing_inputs": list(missing_inputs),
        "review_packet_key": _stable_key(key_payload),
        "manual_review_packets_created": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload
