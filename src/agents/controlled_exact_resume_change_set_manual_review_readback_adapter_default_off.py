from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


PHASE = "48A"

DEFAULT_READBACK_POLICY: dict[str, Any] = {
    "max_readback_items": 12,
    "include_before_after_text": True,
    "include_risk_flags": True,
    "include_evidence": True,
    "include_action_labels": True,
    "group_by_change_type": True,
    "group_by_operator_action": True,
    "sort_by_display_order": True,
}

FALSE_ACTION_FLAGS = (
    "ui_route_added",
    "api_route_added",
    "ui_readback_performed",
    "api_readback_performed",
    "user_acceptance_performed",
    "resume_change_applied",
    "manual_review_packets_created",
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

ITEM_FALSE_ACTION_FLAGS = (
    "ui_route_added",
    "api_route_added",
    "ui_readback_performed",
    "api_readback_performed",
    "user_acceptance_performed",
    "resume_change_applied",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "application_submission_performed",
)

ALLOWED_USER_ACTIONS = ("preview", "inspect", "defer")
BLOCKED_USER_ACTIONS = (
    "apply",
    "overwrite_resume",
    "mutate_resume",
    "submit_application",
    "auto_apply",
    "auto_submit",
)

ACTION_LABELS = {
    "review_risk": "Review risk before accepting",
    "review_change": "Review exact change",
    "reject_invalid": "Reject invalid proposal",
    "inspect_unknown": "Inspect unknown proposal",
    "unknown": "Inspect proposal",
}


def _coerce_policy(readback_policy: dict[str, Any] | None) -> dict[str, Any]:
    policy = dict(DEFAULT_READBACK_POLICY)
    if isinstance(readback_policy, dict):
        for key in DEFAULT_READBACK_POLICY:
            if key == "max_readback_items":
                policy[key] = _safe_positive_int(readback_policy.get(key), policy[key])
            elif key in readback_policy:
                policy[key] = bool(readback_policy.get(key))
    return policy


def _safe_positive_int(value: Any, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback
    if parsed < 0:
        return fallback
    return parsed


def _as_list(value: Any) -> list[Any] | None:
    if isinstance(value, list):
        return deepcopy(value)
    return None


def _flatten_grouped(value: Any) -> list[Any] | None:
    if not isinstance(value, dict):
        return None
    rows: list[Any] = []
    for key in sorted(value):
        group = value.get(key)
        if isinstance(group, list):
            rows.extend(deepcopy(group))
    return rows


def _resolve_packets(
    manual_review_packets: list[dict[str, Any]] | None,
    review_packet_result: dict[str, Any] | None,
) -> tuple[list[Any], str | None]:
    explicit_packets = _as_list(manual_review_packets)
    if explicit_packets is not None:
        return explicit_packets, "manual_review_packets"

    if not isinstance(review_packet_result, dict):
        return [], None

    direct_packets = _as_list(review_packet_result.get("manual_review_packets"))
    if direct_packets is not None:
        return direct_packets, "review_packet_result.manual_review_packets"

    nested_result = review_packet_result.get("review_packet_result")
    if isinstance(nested_result, dict):
        nested_packets = _as_list(nested_result.get("manual_review_packets"))
        if nested_packets is not None:
            return nested_packets, "review_packet_result.review_packet_result.manual_review_packets"

        nested_grouped = _flatten_grouped(nested_result.get("manual_review_packets_by_type"))
        if nested_grouped is not None:
            return nested_grouped, "review_packet_result.review_packet_result.manual_review_packets_by_type"

    grouped_packets = _flatten_grouped(review_packet_result.get("manual_review_packets_by_type"))
    if grouped_packets is not None:
        return grouped_packets, "review_packet_result.manual_review_packets_by_type"

    return [], None


def _text_value(packet: dict[str, Any], keys: tuple[str, ...]) -> str:
    for key in keys:
        value = packet.get(key)
        if value is None:
            continue
        return str(value)
    return ""


def _list_value(packet: dict[str, Any], key: str) -> list[Any]:
    value = packet.get(key)
    if isinstance(value, list):
        return deepcopy(value)
    if value in (None, ""):
        return []
    return [value]


def _operator_action(packet: dict[str, Any]) -> str:
    action = str(packet.get("recommended_operator_action") or packet.get("operator_action") or "")
    if action in ACTION_LABELS:
        return action
    if action:
        return "inspect_unknown"
    return "unknown"


def _readback_item_key(packet: dict[str, Any], ordinal: int) -> str:
    source = {
        "ordinal": ordinal,
        "review_packet_id": packet.get("review_packet_id"),
        "proposal_id": packet.get("proposal_id"),
        "recommended_operator_action": packet.get("recommended_operator_action"),
        "display_order": packet.get("display_order"),
    }
    return sha256(json.dumps(source, sort_keys=True, default=str).encode("utf-8")).hexdigest()[:16]


def _display_order(packet: dict[str, Any], ordinal: int) -> int:
    return _safe_positive_int(packet.get("display_order"), ordinal)


def _build_readback_item(
    packet: dict[str, Any],
    ordinal: int,
    policy: dict[str, Any],
    readback_context: dict[str, Any] | None,
) -> dict[str, Any]:
    operator_action = _operator_action(packet)
    include_before_after_text = bool(policy["include_before_after_text"])
    include_risk_flags = bool(policy["include_risk_flags"])
    include_evidence = bool(policy["include_evidence"])
    include_action_labels = bool(policy["include_action_labels"])

    item = {
        "readback_item_id": f"phase48a-readback-{_readback_item_key(packet, ordinal)}",
        "review_packet_id": _text_value(packet, ("review_packet_id", "packet_id", "manual_review_packet_id")),
        "proposal_id": _text_value(packet, ("proposal_id", "change_proposal_id", "change_id")),
        "change_type": _text_value(packet, ("change_type", "proposal_type", "type")) or "unknown",
        "target_section": _text_value(packet, ("target_section", "section")),
        "target_identifier": _text_value(packet, ("target_identifier", "target_id", "field_path")),
        "current_text": _text_value(packet, ("current_text", "before_text", "existing_text"))
        if include_before_after_text
        else "",
        "proposed_text": _text_value(packet, ("proposed_text", "after_text", "replacement_text"))
        if include_before_after_text
        else "",
        "change_reason": _text_value(packet, ("change_reason", "reason", "rationale")),
        "jd_terms_supported": _list_value(packet, "jd_terms_supported") if include_evidence else [],
        "resume_evidence_used": _list_value(packet, "resume_evidence_used") if include_evidence else [],
        "risk_flags": _list_value(packet, "risk_flags") if include_risk_flags else [],
        "source_validation_status": _text_value(packet, ("source_validation_status", "validation_status")),
        "normalization_notes": _list_value(packet, "normalization_notes"),
        "manual_review_required": True,
        "requires_user_acceptance": True,
        "recommended_operator_action": operator_action,
        "operator_action_label": ACTION_LABELS[operator_action] if include_action_labels else "",
        "review_reason": _text_value(packet, ("review_reason", "manual_review_reason")),
        "display_order": _display_order(packet, ordinal),
        "readback_context": deepcopy(readback_context) if isinstance(readback_context, dict) else {},
    }
    for flag in ITEM_FALSE_ACTION_FLAGS:
        item[flag] = False
    return item


def _sort_items(items: list[dict[str, Any]], policy: dict[str, Any]) -> list[dict[str, Any]]:
    if not policy["sort_by_display_order"]:
        return list(items)
    return sorted(items, key=lambda item: (item["display_order"], item["readback_item_id"]))


def _group_by(items: list[dict[str, Any]], key: str) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in items:
        group_key = str(item.get(key) or "unknown")
        existing = grouped.get(group_key)
        if existing is None:
            grouped[group_key] = [deepcopy(item)]
        else:
            existing.append(deepcopy(item))
    return {key_name: grouped[key_name] for key_name in sorted(grouped)}


def build_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off(
    manual_review_packets: list[dict[str, Any]] | None = None,
    review_packet_result: dict[str, Any] | None = None,
    readback_context: dict[str, Any] | None = None,
    readback_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    policy = _coerce_policy(readback_policy)
    resolved_packets, packet_source = _resolve_packets(manual_review_packets, review_packet_result)

    valid_packets: list[dict[str, Any]] = []
    invalid_packet_count = 0
    for packet in resolved_packets:
        if isinstance(packet, dict):
            valid_packets.append(deepcopy(packet))
        else:
            invalid_packet_count += 1

    missing_inputs: list[str] = []
    if not resolved_packets:
        missing_inputs.append("manual_review_packets")

    readback_items = [
        _build_readback_item(packet, ordinal, policy, readback_context)
        for ordinal, packet in enumerate(valid_packets)
    ]
    readback_items = _sort_items(readback_items, policy)

    max_readback_items = int(policy["max_readback_items"])
    truncated_item_count = max(0, len(readback_items) - max_readback_items)
    readback_items = readback_items[:max_readback_items]

    readback_items_by_type = (
        _group_by(readback_items, "change_type") if policy["group_by_change_type"] else {}
    )
    readback_items_by_action = (
        _group_by(readback_items, "recommended_operator_action")
        if policy["group_by_operator_action"]
        else {}
    )

    readback_summary = {
        "packet_source": packet_source,
        "input_packet_count": len(resolved_packets),
        "valid_packet_count": len(valid_packets),
        "invalid_packet_count": invalid_packet_count,
        "readback_item_count": len(readback_items),
        "truncated_item_count": truncated_item_count,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "read_only": True,
        "advisory_only": True,
        "ui_api_readback_payload_only": True,
        "resume_change_applied": False,
        "resume_mutation_performed": False,
        "provider_call_performed": False,
        "network_call_performed": False,
        "application_submission_performed": False,
    }

    readback_findings = {
        "blocked": bool(missing_inputs),
        "missing_inputs": list(missing_inputs),
        "invalid_packet_count": invalid_packet_count,
        "excluded_invalid_packets": invalid_packet_count,
        "truncated_item_count": truncated_item_count,
        "notes": [
            "manual_review_packets are required for readback"
        ]
        if missing_inputs
        else [
            "manual review readback payload created without provider calls, mutation, persistence, or submission"
        ],
    }

    readback_payload = {
        "payload_type": "exact_resume_change_set_manual_review_readback",
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "readback_items": deepcopy(readback_items),
        "readback_summary": deepcopy(readback_summary),
        "allowed_user_actions": list(ALLOWED_USER_ACTIONS),
        "blocked_user_actions": list(BLOCKED_USER_ACTIONS),
    }

    output = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_manual_review_readback_adapter": True,
        "read_only": True,
        "advisory_only": True,
        "manual_review_readback_only": True,
        "ui_api_readback_payload_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "manual_review_packets_present": bool(manual_review_packets),
        "review_packet_result_present": isinstance(review_packet_result, dict),
        "readback_context_present": isinstance(readback_context, dict) and bool(readback_context),
        "readback_policy": deepcopy(policy),
        "readback_items": deepcopy(readback_items),
        "readback_items_by_type": readback_items_by_type,
        "readback_items_by_action": readback_items_by_action,
        "readback_payload": readback_payload,
        "readback_summary": readback_summary,
        "readback_findings": readback_findings,
        "missing_inputs": missing_inputs,
        "readback_key": sha256(
            json.dumps(readback_payload, sort_keys=True, default=str).encode("utf-8")
        ).hexdigest(),
        "manual_review_readback_payload_created": True,
    }
    for flag in FALSE_ACTION_FLAGS:
        output[flag] = False
    return output
