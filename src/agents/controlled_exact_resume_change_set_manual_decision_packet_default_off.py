"""Default-off manual decision packet builder for exact resume changes."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


PHASE = "51A"
ALLOWED_DECISIONS = ("approve", "reject", "needs_revision")
STAGE_SEQUENCE = (
    "readback_resolution",
    "decision_validation",
    "manual_decision_packet",
)
FALSE_ACTION_KEYS = (
    "provider_call_performed",
    "real_provider_call_performed",
    "llm_call_performed",
    "network_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
    "resume_change_applied",
    "resume_artifact_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "database_" + "write_performed",
    "persistence_performed",
    "execution_performed",
    "application_execution_performed",
    "application_submission_performed",
    "submission_performed",
    "auto_" + "apply_performed",
    "auto_" + "submit_performed",
    "ui_route_added",
    "api_route_added",
    "ui_readback_performed",
    "api_readback_performed",
    "user_decision_applied",
    "user_acceptance_performed",
)


def _bool(value: Any, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"1", "true", "yes", "y"}:
            return True
        if lowered in {"0", "false", "no", "n"}:
            return False
    return default if value is None else bool(value)


def _policy(value: dict[str, Any] | None) -> dict[str, Any]:
    supplied = value if isinstance(value, dict) else {}
    return {
        "allow_manual_decision_packet": _bool(
            supplied.get("allow_manual_decision_packet"),
            False,
        ),
        "require_all_readback_items_decided": _bool(
            supplied.get("require_all_readback_items_decided"),
            False,
        ),
    }


def _text(value: Any) -> str:
    return str(value or "").strip()


def _as_list(value: Any) -> list[Any] | None:
    return deepcopy(value) if isinstance(value, list) else None


def _flatten_grouped(value: Any) -> list[Any]:
    if not isinstance(value, dict):
        return []
    rows: list[Any] = []
    for key in sorted(value):
        group = value.get(key)
        if isinstance(group, list):
            rows.extend(deepcopy(group))
    return rows


def _readback_items_from_result(value: Any) -> tuple[list[Any], str]:
    if not isinstance(value, dict):
        return [], "missing"

    payload = value.get("final_readback_payload")
    if isinstance(payload, dict) and isinstance(payload.get("readback_items"), list):
        return deepcopy(payload["readback_items"]), "phase50.final_readback_payload"

    pipeline = value.get("pipeline_result")
    if isinstance(pipeline, dict):
        nested_payload = pipeline.get("final_readback_payload")
        if isinstance(nested_payload, dict) and isinstance(
            nested_payload.get("readback_items"),
            list,
        ):
            return (
                deepcopy(nested_payload["readback_items"]),
                "phase50b.pipeline_result.final_readback_payload",
            )

    readback_payload = value.get("readback_payload")
    if isinstance(readback_payload, dict) and isinstance(
        readback_payload.get("readback_items"),
        list,
    ):
        return deepcopy(readback_payload["readback_items"]), "readback_payload"

    direct_items = _as_list(value.get("readback_items"))
    if direct_items is not None:
        return direct_items, "readback_items"

    grouped_items = _flatten_grouped(value.get("readback_items_by_type"))
    if grouped_items:
        return grouped_items, "readback_items_by_type"

    review_packets = _as_list(value.get("manual_review_packets"))
    if review_packets is not None:
        return review_packets, "manual_review_packets"

    review_result = value.get("manual_review_packet_result")
    if isinstance(review_result, dict):
        packets = _as_list(review_result.get("manual_review_packets"))
        if packets is not None:
            return packets, "manual_review_packet_result.manual_review_packets"

    return [], "missing"


def _item_identifier(item: dict[str, Any]) -> str:
    for key in ("proposal_id", "change_id", "change_proposal_id"):
        text = _text(item.get(key))
        if text:
            return text
    return ""


def _decision_identifier(decision: dict[str, Any]) -> str:
    for key in ("proposal_id", "change_id", "change_proposal_id"):
        text = _text(decision.get(key))
        if text:
            return text
    return ""


def _alternate_ids(item: dict[str, Any]) -> list[str]:
    ids: list[str] = []
    for key in ("readback_item_id", "review_packet_id", "packet_id"):
        text = _text(item.get(key))
        if text:
            ids.append(text)
    return ids


def _resolve_readback_items(value: Any) -> tuple[list[dict[str, Any]], str, list[str], dict[str, str]]:
    raw_items, source = _readback_items_from_result(value)
    items: list[dict[str, Any]] = []
    duplicate_ids: list[str] = []
    id_map: dict[str, str] = {}
    seen: set[str] = set()
    for raw in raw_items:
        if not isinstance(raw, dict):
            continue
        item = deepcopy(raw)
        proposal_id = _item_identifier(item)
        if not proposal_id:
            continue
        if proposal_id in seen:
            duplicate_ids.append(proposal_id)
            continue
        seen.add(proposal_id)
        items.append(item)
        id_map[proposal_id] = proposal_id
        for alternate in _alternate_ids(item):
            id_map[alternate] = proposal_id
    return items, source, duplicate_ids, id_map


def _decision_rows(value: Any) -> tuple[list[Any], str]:
    if isinstance(value, list):
        return deepcopy(value), "manual_decisions"
    if not isinstance(value, dict):
        return [], "missing"
    for key in ("manual_decisions", "decisions", "operator_decisions"):
        rows = value.get(key)
        if isinstance(rows, list):
            return deepcopy(rows), key
    mapping = value.get("decisions_by_proposal_id")
    if isinstance(mapping, dict):
        rows = [
            {"proposal_id": proposal_id, "decision": decision}
            for proposal_id, decision in sorted(mapping.items())
        ]
        return rows, "decisions_by_proposal_id"
    return [], "missing"


def _decision_key(row: dict[str, Any]) -> str:
    return _text(row.get("decision") or row.get("manual_decision")).lower()


def _decision_reason(row: dict[str, Any]) -> str:
    for key in ("decision_reason", "reason", "notes"):
        text = _text(row.get(key))
        if text:
            return text
    return ""


def _packet_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase51a-manual-decision-packet-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def _blocked_payload(
    *,
    enabled: bool,
    policy: dict[str, Any],
    status: str,
    blocked_reason: str,
    missing_inputs: list[str],
    readback_items: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    stage_summaries: dict[str, Any],
    stage_results: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_manual_decision_packet": True,
        "manual_decision_packet_only": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "enabled": bool(enabled),
        "decision_policy": deepcopy(policy),
        "status": status,
        "blocked_reason": blocked_reason,
        "missing_inputs": list(missing_inputs),
        "allowed_decision_values": list(ALLOWED_DECISIONS),
        "readback_item_count": len(readback_items),
        "manual_decision_count": len(decisions),
        "stage_sequence": list(STAGE_SEQUENCE),
        "stage_summaries": deepcopy(stage_summaries),
        "stage_results": deepcopy(stage_results),
        "manual_decision_packet": None,
        "manual_decision_packet_created": False,
        "manual_decision_packet_key": _packet_key(
            {
                "status": status,
                "blocked_reason": blocked_reason,
                "missing_inputs": missing_inputs,
                "readback_item_count": len(readback_items),
                "manual_decision_count": len(decisions),
            }
        ),
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def build_controlled_exact_resume_change_set_manual_decision_packet_default_off(
    readback_result: dict[str, Any] | None = None,
    manual_review_output: dict[str, Any] | None = None,
    manual_decisions: list[dict[str, Any]] | dict[str, Any] | None = None,
    enabled: bool = False,
    decision_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic manual decision packet without applying decisions."""

    policy = _policy(decision_policy)
    source_value: Any = readback_result if isinstance(readback_result, dict) else manual_review_output
    readback_items, item_source, duplicate_ids, id_map = _resolve_readback_items(source_value)
    raw_decisions, decision_source = _decision_rows(manual_decisions)
    stage_summaries: dict[str, Any] = {
        "readback_resolution": {
            "source": item_source,
            "readback_item_count": len(readback_items),
            "known_identifier_count": len(id_map),
            "duplicate_proposal_ids": list(duplicate_ids),
        },
        "decision_validation": {
            "source": decision_source,
            "input_decision_count": len(raw_decisions),
            "allowed_decision_values": list(ALLOWED_DECISIONS),
        },
    }
    stage_results: dict[str, Any] = {
        "readback_resolution": {
            "readback_items": deepcopy(readback_items),
            "identifier_map": deepcopy(id_map),
            "duplicate_proposal_ids": list(duplicate_ids),
        }
    }

    missing_inputs: list[str] = []
    blocked_reasons: list[str] = []
    if not bool(enabled):
        blocked_reasons.append("enabled must be true")
    if not policy["allow_manual_decision_packet"]:
        blocked_reasons.append("decision policy must allow manual decision packet")
    if not readback_items:
        missing_inputs.append("readback_or_manual_review_output")
        blocked_reasons.append("readback/manual review output required")
    if not raw_decisions:
        missing_inputs.append("manual_decisions")
        blocked_reasons.append("manual decisions required")
    if duplicate_ids:
        blocked_reasons.append("duplicate readback proposal ids present")

    normalized_decisions: list[dict[str, Any]] = []
    invalid_decisions: list[dict[str, Any]] = []
    unknown_identifiers: list[str] = []
    duplicate_decision_ids: list[str] = []
    decided_ids: set[str] = set()
    for index, raw in enumerate(raw_decisions):
        if not isinstance(raw, dict):
            invalid_decisions.append(
                {"index": index, "reason": "decision row must be an object"}
            )
            continue
        supplied_identifier = _decision_identifier(raw)
        decision_value = _decision_key(raw)
        canonical_id = id_map.get(supplied_identifier, "")
        if not supplied_identifier:
            invalid_decisions.append(
                {"index": index, "reason": "proposal_id required"}
            )
            continue
        if not canonical_id:
            unknown_identifiers.append(supplied_identifier)
            continue
        if decision_value not in ALLOWED_DECISIONS:
            invalid_decisions.append(
                {
                    "index": index,
                    "proposal_id": canonical_id,
                    "decision": decision_value,
                    "reason": "invalid decision value",
                }
            )
            continue
        if canonical_id in decided_ids:
            duplicate_decision_ids.append(canonical_id)
            continue
        decided_ids.add(canonical_id)
        normalized_decisions.append(
            {
                "proposal_id": canonical_id,
                "input_identifier": supplied_identifier,
                "manual_decision": decision_value,
                "decision_reason": _decision_reason(raw),
                "manual_decision_required": True,
                "resume_change_applied": False,
                "resume_overwrite_performed": False,
                "resume_mutation_performed": False,
                "artifact_created": False,
                "application_execution_performed": False,
            }
        )

    undecided_ids = [
        _item_identifier(item)
        for item in readback_items
        if _item_identifier(item) and _item_identifier(item) not in decided_ids
    ]
    if invalid_decisions:
        blocked_reasons.append("invalid manual decisions present")
    if unknown_identifiers:
        blocked_reasons.append("unknown proposal identifiers present")
    if duplicate_decision_ids:
        blocked_reasons.append("duplicate manual decisions present")
    if policy["require_all_readback_items_decided"] and undecided_ids:
        blocked_reasons.append("all readback items must have manual decisions")

    stage_summaries["decision_validation"].update(
        {
            "valid_decision_count": len(normalized_decisions),
            "invalid_decision_count": len(invalid_decisions),
            "unknown_identifier_count": len(unknown_identifiers),
            "duplicate_decision_count": len(duplicate_decision_ids),
            "undecided_readback_item_count": len(undecided_ids),
        }
    )
    stage_results["decision_validation"] = {
        "manual_decisions": deepcopy(normalized_decisions),
        "invalid_decisions": deepcopy(invalid_decisions),
        "unknown_identifiers": list(unknown_identifiers),
        "duplicate_decision_ids": list(duplicate_decision_ids),
        "undecided_proposal_ids": list(undecided_ids),
    }

    if blocked_reasons:
        return _blocked_payload(
            enabled=bool(enabled) and bool(policy["allow_manual_decision_packet"]),
            policy=policy,
            status="blocked",
            blocked_reason="; ".join(blocked_reasons),
            missing_inputs=missing_inputs,
            readback_items=readback_items,
            decisions=normalized_decisions,
            stage_summaries=stage_summaries,
            stage_results=stage_results,
        )

    decisions_by_id = {
        decision["proposal_id"]: deepcopy(decision)
        for decision in sorted(normalized_decisions, key=lambda row: row["proposal_id"])
    }
    manual_decision_packet = {
        "payload_type": "exact_resume_change_set_manual_decision_packet",
        "manual_decision_packet_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "allowed_decision_values": list(ALLOWED_DECISIONS),
        "manual_decisions": [deepcopy(decisions_by_id[key]) for key in sorted(decisions_by_id)],
        "manual_decisions_by_proposal_id": decisions_by_id,
        "decision_summary": {
            "decision_count": len(decisions_by_id),
            "approved_count": sum(
                1
                for row in decisions_by_id.values()
                if row["manual_decision"] == "approve"
            ),
            "rejected_count": sum(
                1
                for row in decisions_by_id.values()
                if row["manual_decision"] == "reject"
            ),
            "needs_revision_count": sum(
                1
                for row in decisions_by_id.values()
                if row["manual_decision"] == "needs_revision"
            ),
            "resume_change_applied": False,
            "resume_mutation_performed": False,
            "artifact_created": False,
            "application_execution_performed": False,
        },
    }
    packet_key = _packet_key(manual_decision_packet)
    stage_summaries["manual_decision_packet"] = {
        "manual_decision_packet_created": True,
        "manual_decision_count": len(decisions_by_id),
        "packet_key": packet_key,
        "resume_change_applied": False,
        "artifact_created": False,
    }
    stage_results["manual_decision_packet"] = deepcopy(manual_decision_packet)
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_manual_decision_packet": True,
        "manual_decision_packet_only": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "enabled": True,
        "decision_policy": deepcopy(policy),
        "status": "completed",
        "blocked_reason": "",
        "missing_inputs": [],
        "allowed_decision_values": list(ALLOWED_DECISIONS),
        "readback_item_count": len(readback_items),
        "manual_decision_count": len(decisions_by_id),
        "stage_sequence": list(STAGE_SEQUENCE),
        "stage_summaries": stage_summaries,
        "stage_results": stage_results,
        "manual_decision_packet": manual_decision_packet,
        "manual_decision_packet_created": True,
        "manual_decision_packet_key": packet_key,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload
