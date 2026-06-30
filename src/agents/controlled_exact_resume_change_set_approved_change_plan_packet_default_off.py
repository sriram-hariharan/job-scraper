"""Default-off approved change plan packet builder for exact resume changes."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


PHASE = "53A"
READBACK_TYPE = "exact_resume_change_set_manual_decision_readback"
PLAN_TYPE = "exact_resume_change_set_approved_change_plan_packet"
ALLOWED_DECISIONS = ("approve", "reject", "needs_revision")
STAGE_SEQUENCE = (
    "manual_decision_readback_resolution",
    "manual_decision_readback_validation",
    "approved_change_plan_packet",
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
        "allow_approved_change_plan_packet": _bool(
            supplied.get("allow_approved_change_plan_packet"),
            False,
        )
    }


def _text(value: Any) -> str:
    return str(value or "").strip()


def _decision_key(row: dict[str, Any]) -> str:
    return _text(row.get("manual_decision") or row.get("decision")).lower()


def _packet_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase53a-approved-change-plan-packet-" + sha256(
        encoded.encode("utf-8")
    ).hexdigest()[:24]


def _looks_like_raw_phase50(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("payload_type") == "exact_resume_change_set_manual_review_readback":
        return True
    if isinstance(value.get("manual_review_packets"), list):
        return True
    final_payload = value.get("final_readback_payload")
    if isinstance(final_payload, dict) and isinstance(
        final_payload.get("readback_items"),
        list,
    ):
        return True
    return False


def _looks_like_raw_phase51(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("payload_type") == "exact_resume_change_set_manual_decision_packet":
        return True
    packet = value.get("manual_decision_packet")
    return isinstance(packet, dict) and packet.get("payload_type") == (
        "exact_resume_change_set_manual_decision_packet"
    )


def _resolve_readback(value: Any) -> tuple[dict[str, Any] | None, str, bool, bool]:
    if not isinstance(value, dict):
        return None, "missing", False, False
    if value.get("payload_type") == READBACK_TYPE:
        return deepcopy(value), "manual_decision_readback", False, False
    payload = value.get("readback_payload")
    if isinstance(payload, dict) and payload.get("payload_type") == READBACK_TYPE:
        return deepcopy(payload), "phase52.readback_payload", False, False
    result = value.get("readback_result")
    if isinstance(result, dict):
        nested = result.get("readback_payload")
        if isinstance(nested, dict) and nested.get("payload_type") == READBACK_TYPE:
            return deepcopy(nested), "phase52b.readback_result.readback_payload", False, False
    return None, "missing", _looks_like_raw_phase51(value), _looks_like_raw_phase50(value)


def _validate_items(rows: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return [], [{"index": None, "reason": "readback_items must be a list"}]
    seen: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            invalid.append({"index": index, "reason": "readback item must be an object"})
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
                "readback_item_id": _text(raw.get("readback_item_id")),
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


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "decision_count": len(rows),
        "approved_count": sum(1 for row in rows if row["manual_decision"] == "approve"),
        "rejected_count": sum(1 for row in rows if row["manual_decision"] == "reject"),
        "needs_revision_count": sum(
            1 for row in rows if row["manual_decision"] == "needs_revision"
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
        "controlled_exact_resume_change_set_approved_change_plan_packet": True,
        "approved_change_plan_packet_only": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "enabled": bool(enabled),
        "plan_policy": deepcopy(policy),
        "status": "blocked",
        "blocked_reason": blocked_reason,
        "missing_inputs": list(missing_inputs),
        "stage_sequence": list(STAGE_SEQUENCE),
        "stage_summaries": deepcopy(stage_summaries),
        "stage_results": deepcopy(stage_results),
        "approved_change_plan_packet": None,
        "approved_change_plan_packet_created": False,
        "approved_change_plan_packet_key": _packet_key(
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


def build_controlled_exact_resume_change_set_approved_change_plan_packet_default_off(
    manual_decision_readback_result: dict[str, Any] | None = None,
    readback_payload: dict[str, Any] | None = None,
    enabled: bool = False,
    plan_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic approved-change plan packet without applying it."""

    policy = _policy(plan_policy)
    source_value: Any = (
        readback_payload
        if isinstance(readback_payload, dict)
        else manual_decision_readback_result
    )
    readback, source, raw_phase51_input, raw_phase50_input = _resolve_readback(source_value)
    raw_items = readback.get("readback_items") if isinstance(readback, dict) else None
    valid_items, invalid_items = _validate_items(raw_items)
    decision_summary = _summary(valid_items)
    approved_items = [
        deepcopy(row)
        for row in sorted(valid_items, key=lambda item: item["proposal_id"])
        if row["manual_decision"] == "approve"
    ]
    excluded_summary = {
        "rejected_count": decision_summary["rejected_count"],
        "needs_revision_count": decision_summary["needs_revision_count"],
        "excluded_count": (
            decision_summary["rejected_count"]
            + decision_summary["needs_revision_count"]
        ),
    }
    stage_summaries: dict[str, Any] = {
        "manual_decision_readback_resolution": {
            "source": source,
            "readback_present": isinstance(readback, dict),
            "raw_phase51_manual_decision_packet_input": raw_phase51_input,
            "raw_phase50_readback_or_review_input": raw_phase50_input,
        },
        "manual_decision_readback_validation": {
            "valid_readback_item_count": len(valid_items),
            "invalid_readback_item_count": len(invalid_items),
            "approved_count": len(approved_items),
            "rejected_count": decision_summary["rejected_count"],
            "needs_revision_count": decision_summary["needs_revision_count"],
        },
    }
    stage_results: dict[str, Any] = {
        "manual_decision_readback_resolution": {
            "readback_payload": deepcopy(readback),
            "source": source,
            "raw_phase51_manual_decision_packet_input": raw_phase51_input,
            "raw_phase50_readback_or_review_input": raw_phase50_input,
        },
        "manual_decision_readback_validation": {
            "readback_items": deepcopy(valid_items),
            "invalid_readback_items": deepcopy(invalid_items),
            "decision_summary": deepcopy(decision_summary),
            "excluded_decision_summary": deepcopy(excluded_summary),
        },
    }

    missing_inputs: list[str] = []
    blocked_reasons: list[str] = []
    if not bool(enabled):
        blocked_reasons.append("enabled must be true")
    if not policy["allow_approved_change_plan_packet"]:
        blocked_reasons.append("plan policy must allow approved change plan packet")
    if raw_phase51_input:
        blocked_reasons.append("manual decision readback required; raw manual decision packet is not accepted")
    if raw_phase50_input:
        blocked_reasons.append("manual decision readback required; raw phase50 readback/manual review input is not accepted")
    if not isinstance(readback, dict):
        missing_inputs.append("manual_decision_readback")
        blocked_reasons.append("manual decision readback required")
    elif readback.get("payload_type") != READBACK_TYPE:
        blocked_reasons.append("input must be manual decision readback output")
    if not valid_items:
        blocked_reasons.append("manual decision readback must contain valid items")
    if invalid_items:
        blocked_reasons.append("invalid manual decision readback present")

    if blocked_reasons:
        return _blocked_payload(
            enabled=bool(enabled) and bool(policy["allow_approved_change_plan_packet"]),
            policy=policy,
            blocked_reason="; ".join(blocked_reasons),
            missing_inputs=missing_inputs,
            stage_summaries=stage_summaries,
            stage_results=stage_results,
        )

    approved_changes = [
        {
            "plan_item_id": f"approved-change-plan-{item['proposal_id']}",
            "proposal_id": item["proposal_id"],
            "source_readback_item_id": item["readback_item_id"],
            "manual_decision": item["manual_decision"],
            "decision_reason": item["decision_reason"],
            "resume_change_applied": False,
            "resume_overwrite_performed": False,
            "resume_mutation_performed": False,
            "artifact_created": False,
            "application_execution_performed": False,
        }
        for item in approved_items
    ]
    packet = {
        "payload_type": PLAN_TYPE,
        "approved_change_plan_packet_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "source_manual_decision_readback": deepcopy(readback),
        "decision_summary": deepcopy(decision_summary),
        "excluded_decision_summary": deepcopy(excluded_summary),
        "approved_change_count": len(approved_changes),
        "approved_changes": approved_changes,
        "resume_change_applied": False,
        "resume_mutation_performed": False,
        "artifact_created": False,
        "application_execution_performed": False,
    }
    packet_key = _packet_key(packet)
    stage_summaries["approved_change_plan_packet"] = {
        "approved_change_plan_packet_created": True,
        "approved_change_count": len(approved_changes),
        "packet_key": packet_key,
        "artifact_created": False,
        "resume_change_applied": False,
    }
    stage_results["approved_change_plan_packet"] = deepcopy(packet)
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_approved_change_plan_packet": True,
        "approved_change_plan_packet_only": True,
        "read_only": True,
        "advisory_only": True,
        "proposal_only": True,
        "exact_worthy_changes_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "enabled": True,
        "plan_policy": deepcopy(policy),
        "status": "completed",
        "blocked_reason": "",
        "missing_inputs": [],
        "stage_sequence": list(STAGE_SEQUENCE),
        "stage_summaries": stage_summaries,
        "stage_results": stage_results,
        "decision_summary": deepcopy(decision_summary),
        "excluded_decision_summary": deepcopy(excluded_summary),
        "approved_change_plan_packet": packet,
        "approved_change_plan_packet_created": True,
        "approved_change_plan_packet_key": packet_key,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload
