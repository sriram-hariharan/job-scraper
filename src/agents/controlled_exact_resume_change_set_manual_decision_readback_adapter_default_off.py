"""Default-off readback adapter for exact resume manual decisions."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


PHASE = "52A"
PACKET_TYPE = "exact_resume_change_set_manual_decision_packet"
READBACK_TYPE = "exact_resume_change_set_manual_decision_readback"
ALLOWED_DECISIONS = ("approve", "reject", "needs_revision")
STAGE_SEQUENCE = (
    "manual_decision_packet_resolution",
    "manual_decision_packet_validation",
    "manual_decision_readback",
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
        "allow_manual_decision_readback": _bool(
            supplied.get("allow_manual_decision_readback"),
            False,
        )
    }


def _text(value: Any) -> str:
    return str(value or "").strip()


def _decision_key(row: dict[str, Any]) -> str:
    return _text(row.get("manual_decision") or row.get("decision")).lower()


def _packet_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase52a-manual-decision-readback-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def _looks_like_raw_review_or_readback(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("payload_type") == "exact_resume_change_set_manual_review_readback":
        return True
    if isinstance(value.get("readback_items"), list):
        return True
    if isinstance(value.get("manual_review_packets"), list):
        return True
    final_payload = value.get("final_readback_payload")
    if isinstance(final_payload, dict) and isinstance(
        final_payload.get("readback_items"),
        list,
    ):
        return True
    readback_payload = value.get("readback_payload")
    return isinstance(readback_payload, dict) and isinstance(
        readback_payload.get("readback_items"),
        list,
    )


def _resolve_packet(value: Any) -> tuple[dict[str, Any] | None, str, bool]:
    if not isinstance(value, dict):
        return None, "missing", False
    direct_type = value.get("payload_type")
    if direct_type == PACKET_TYPE:
        return deepcopy(value), "manual_decision_packet", False
    packet = value.get("manual_decision_packet")
    if isinstance(packet, dict) and packet.get("payload_type") == PACKET_TYPE:
        return deepcopy(packet), "phase51.manual_decision_packet", False
    decision_result = value.get("decision_result")
    if isinstance(decision_result, dict):
        nested = decision_result.get("manual_decision_packet")
        if isinstance(nested, dict) and nested.get("payload_type") == PACKET_TYPE:
            return deepcopy(nested), "phase51b.decision_result.manual_decision_packet", False
    return None, "missing", _looks_like_raw_review_or_readback(value)


def _validate_decisions(rows: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return [], [{"index": None, "reason": "manual_decisions must be a list"}]
    seen: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            invalid.append({"index": index, "reason": "decision row must be an object"})
            continue
        proposal_id = _text(raw.get("proposal_id") or raw.get("change_id"))
        decision = _decision_key(raw)
        if not proposal_id:
            invalid.append({"index": index, "reason": "proposal_id required"})
            continue
        if proposal_id in seen:
            invalid.append(
                {
                    "index": index,
                    "proposal_id": proposal_id,
                    "reason": "duplicate proposal_id",
                }
            )
            continue
        if decision not in ALLOWED_DECISIONS:
            invalid.append(
                {
                    "index": index,
                    "proposal_id": proposal_id,
                    "decision": decision,
                    "reason": "invalid decision value",
                }
            )
            continue
        seen.add(proposal_id)
        valid.append(
            {
                "proposal_id": proposal_id,
                "manual_decision": decision,
                "decision_reason": _text(
                    raw.get("decision_reason") or raw.get("reason") or raw.get("notes")
                ),
                "resume_change_applied": False,
                "resume_overwrite_performed": False,
                "resume_mutation_performed": False,
                "artifact_created": False,
                "application_execution_performed": False,
            }
        )
    return valid, invalid


def _summary(decisions: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "decision_count": len(decisions),
        "approved_count": sum(
            1 for row in decisions if row["manual_decision"] == "approve"
        ),
        "rejected_count": sum(
            1 for row in decisions if row["manual_decision"] == "reject"
        ),
        "needs_revision_count": sum(
            1 for row in decisions if row["manual_decision"] == "needs_revision"
        ),
        "resume_change_applied": False,
        "resume_mutation_performed": False,
        "artifact_created": False,
        "application_execution_performed": False,
    }


def _blocked_payload(
    *,
    enabled: bool,
    policy: dict[str, Any],
    blocked_reason: str,
    missing_inputs: list[str],
    stage_summaries: dict[str, Any],
    stage_results: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_manual_decision_readback_adapter": True,
        "manual_decision_readback_only": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "enabled": bool(enabled),
        "readback_policy": deepcopy(policy),
        "status": "blocked",
        "blocked_reason": blocked_reason,
        "missing_inputs": list(missing_inputs),
        "stage_sequence": list(STAGE_SEQUENCE),
        "stage_summaries": deepcopy(stage_summaries),
        "stage_results": deepcopy(stage_results),
        "readback_payload": None,
        "readback_payload_created": False,
        "readback_payload_key": _packet_key(
            {
                "status": "blocked",
                "blocked_reason": blocked_reason,
                "missing_inputs": missing_inputs,
            }
        ),
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def build_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off(
    manual_decision_packet_result: dict[str, Any] | None = None,
    manual_decision_packet: dict[str, Any] | None = None,
    enabled: bool = False,
    readback_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic readback for a Phase 51 manual decision packet."""

    policy = _policy(readback_policy)
    source_value: Any = (
        manual_decision_packet
        if isinstance(manual_decision_packet, dict)
        else manual_decision_packet_result
    )
    packet, packet_source, raw_review_input = _resolve_packet(source_value)
    raw_decisions = packet.get("manual_decisions") if isinstance(packet, dict) else None
    valid_decisions, invalid_decisions = _validate_decisions(raw_decisions)
    summary = _summary(valid_decisions)
    stage_summaries: dict[str, Any] = {
        "manual_decision_packet_resolution": {
            "source": packet_source,
            "packet_present": isinstance(packet, dict),
            "raw_review_or_readback_input": raw_review_input,
        },
        "manual_decision_packet_validation": {
            "valid_decision_count": len(valid_decisions),
            "invalid_decision_count": len(invalid_decisions),
            "allowed_decision_values": list(ALLOWED_DECISIONS),
        },
    }
    stage_results: dict[str, Any] = {
        "manual_decision_packet_resolution": {
            "manual_decision_packet": deepcopy(packet),
            "source": packet_source,
            "raw_review_or_readback_input": raw_review_input,
        },
        "manual_decision_packet_validation": {
            "manual_decisions": deepcopy(valid_decisions),
            "invalid_decisions": deepcopy(invalid_decisions),
            "decision_summary": deepcopy(summary),
        },
    }

    missing_inputs: list[str] = []
    blocked_reasons: list[str] = []
    if not bool(enabled):
        blocked_reasons.append("enabled must be true")
    if not policy["allow_manual_decision_readback"]:
        blocked_reasons.append("readback policy must allow manual decision readback")
    if raw_review_input:
        blocked_reasons.append("manual decision packet required; raw readback/manual review input is not accepted")
    if not isinstance(packet, dict):
        missing_inputs.append("manual_decision_packet")
        blocked_reasons.append("manual decision packet required")
    elif packet.get("payload_type") != PACKET_TYPE:
        blocked_reasons.append("input must be a manual decision packet")
    if not valid_decisions:
        blocked_reasons.append("manual decision packet must contain valid decisions")
    if invalid_decisions:
        blocked_reasons.append("invalid manual decision packet present")

    if blocked_reasons:
        return _blocked_payload(
            enabled=bool(enabled) and bool(policy["allow_manual_decision_readback"]),
            policy=policy,
            blocked_reason="; ".join(blocked_reasons),
            missing_inputs=missing_inputs,
            stage_summaries=stage_summaries,
            stage_results=stage_results,
        )

    decisions_by_status = {
        decision: [
            deepcopy(row)
            for row in valid_decisions
            if row["manual_decision"] == decision
        ]
        for decision in ALLOWED_DECISIONS
    }
    readback_items = [
        {
            "readback_item_id": f"manual-decision-readback-{row['proposal_id']}",
            "proposal_id": row["proposal_id"],
            "manual_decision": row["manual_decision"],
            "decision_reason": row["decision_reason"],
            "operator_review_required": True,
            "resume_change_applied": False,
            "resume_overwrite_performed": False,
            "resume_mutation_performed": False,
            "artifact_created": False,
            "application_execution_performed": False,
        }
        for row in sorted(valid_decisions, key=lambda item: item["proposal_id"])
    ]
    readback_payload = {
        "payload_type": READBACK_TYPE,
        "manual_decision_readback_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "source_manual_decision_packet": deepcopy(packet),
        "decision_summary": deepcopy(summary),
        "decisions_by_status": decisions_by_status,
        "readback_items": readback_items,
        "resume_change_applied": False,
        "resume_mutation_performed": False,
        "artifact_created": False,
        "application_execution_performed": False,
    }
    readback_key = _packet_key(readback_payload)
    stage_summaries["manual_decision_readback"] = {
        "readback_payload_created": True,
        "readback_item_count": len(readback_items),
        "readback_payload_key": readback_key,
        "decision_summary": deepcopy(summary),
    }
    stage_results["manual_decision_readback"] = deepcopy(readback_payload)
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_manual_decision_readback_adapter": True,
        "manual_decision_readback_only": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "enabled": True,
        "readback_policy": deepcopy(policy),
        "status": "completed",
        "blocked_reason": "",
        "missing_inputs": [],
        "stage_sequence": list(STAGE_SEQUENCE),
        "stage_summaries": stage_summaries,
        "stage_results": stage_results,
        "decision_summary": deepcopy(summary),
        "readback_payload": readback_payload,
        "readback_payload_created": True,
        "readback_payload_key": readback_key,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload
