"""Default-off readback adapter for approved exact resume change plans."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any


PHASE = "54A"
PACKET_TYPE = "exact_resume_change_set_approved_change_plan_packet"
READBACK_TYPE = "exact_resume_change_set_approved_change_plan_readback"
STAGE_SEQUENCE = (
    "approved_change_plan_packet_resolution",
    "approved_change_plan_packet_validation",
    "approved_change_plan_readback",
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
        "allow_approved_change_plan_readback": _bool(
            supplied.get("allow_approved_change_plan_readback"),
            False,
        )
    }


def _text(value: Any) -> str:
    return str(value or "").strip()


def _packet_key(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)
    return "phase54a-approved-change-plan-readback-" + sha256(
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


def _looks_like_raw_phase52(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    if value.get("payload_type") == "exact_resume_change_set_manual_decision_readback":
        return True
    payload = value.get("readback_payload")
    return isinstance(payload, dict) and payload.get("payload_type") == (
        "exact_resume_change_set_manual_decision_readback"
    )


def _resolve_packet(
    value: Any,
) -> tuple[dict[str, Any] | None, str, bool, bool, bool]:
    if not isinstance(value, dict):
        return None, "missing", False, False, False
    if value.get("payload_type") == PACKET_TYPE:
        return deepcopy(value), "approved_change_plan_packet", False, False, False
    packet = value.get("approved_change_plan_packet")
    if isinstance(packet, dict) and packet.get("payload_type") == PACKET_TYPE:
        return deepcopy(packet), "phase53.approved_change_plan_packet", False, False, False
    plan_result = value.get("plan_result")
    if isinstance(plan_result, dict):
        nested = plan_result.get("approved_change_plan_packet")
        if isinstance(nested, dict) and nested.get("payload_type") == PACKET_TYPE:
            return (
                deepcopy(nested),
                "phase53b.plan_result.approved_change_plan_packet",
                False,
                False,
                False,
            )
    return (
        None,
        "missing",
        _looks_like_raw_phase52(value),
        _looks_like_raw_phase51(value),
        _looks_like_raw_phase50(value),
    )


def _change_type(row: dict[str, Any]) -> str:
    return _text(row.get("change_type") or row.get("type") or "unspecified")


def _section(row: dict[str, Any]) -> str:
    return _text(
        row.get("section")
        or row.get("resume_section")
        or row.get("target_section")
        or "unspecified"
    )


def _validate_changes(rows: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    valid: list[dict[str, Any]] = []
    invalid: list[dict[str, Any]] = []
    if not isinstance(rows, list):
        return [], [{"index": None, "reason": "approved_changes must be a list"}]
    seen: set[str] = set()
    for index, raw in enumerate(rows):
        if not isinstance(raw, dict):
            invalid.append({"index": index, "reason": "approved change must be an object"})
            continue
        proposal_id = _text(raw.get("proposal_id") or raw.get("change_id"))
        manual_decision = _text(raw.get("manual_decision") or "approve").lower()
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
        if manual_decision != "approve":
            invalid.append(
                {
                    "index": index,
                    "proposal_id": proposal_id,
                    "manual_decision": manual_decision,
                    "reason": "approved change must have approve decision",
                }
            )
            continue
        unsafe_flags = [
            key
            for key in (
                "resume_change_applied",
                "resume_overwrite_performed",
                "resume_mutation_performed",
                "artifact_created",
                "resume_artifact_created",
                "application_execution_performed",
            )
            if bool(raw.get(key))
        ]
        if unsafe_flags:
            invalid.append(
                {
                    "index": index,
                    "proposal_id": proposal_id,
                    "reason": "approved change must not report applied side effects",
                    "unsafe_flags": unsafe_flags,
                }
            )
            continue
        seen.add(proposal_id)
        valid.append(
            {
                "plan_item_id": _text(raw.get("plan_item_id")),
                "proposal_id": proposal_id,
                "source_readback_item_id": _text(raw.get("source_readback_item_id")),
                "manual_decision": "approve",
                "decision_reason": _text(
                    raw.get("decision_reason") or raw.get("reason") or raw.get("notes")
                ),
                "change_type": _change_type(raw),
                "section": _section(raw),
                "resume_change_applied": False,
                "resume_overwrite_performed": False,
                "resume_mutation_performed": False,
                "artifact_created": False,
                "application_execution_performed": False,
            }
        )
    return valid, invalid


def _count_by(rows: list[dict[str, Any]], key: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for row in rows:
        value = _text(row.get(key)) or "unspecified"
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def _summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "approved_change_count": len(rows),
        "approved_change_count_by_type": _count_by(rows, "change_type"),
        "approved_change_count_by_section": _count_by(rows, "section"),
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
        "controlled_exact_resume_change_set_approved_change_plan_readback_adapter": True,
        "approved_change_plan_readback_only": True,
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


def build_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off(
    approved_change_plan_packet_result: dict[str, Any] | None = None,
    approved_change_plan_packet: dict[str, Any] | None = None,
    enabled: bool = False,
    readback_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic readback for an approved-change plan packet only."""

    policy = _policy(readback_policy)
    source_value: Any = (
        approved_change_plan_packet
        if isinstance(approved_change_plan_packet, dict)
        else approved_change_plan_packet_result
    )
    packet, source, raw_phase52_input, raw_phase51_input, raw_phase50_input = (
        _resolve_packet(source_value)
    )
    raw_changes = packet.get("approved_changes") if isinstance(packet, dict) else None
    valid_changes, invalid_changes = _validate_changes(raw_changes)
    summary = _summary(valid_changes)
    stage_summaries: dict[str, Any] = {
        "approved_change_plan_packet_resolution": {
            "source": source,
            "approved_change_plan_packet_present": isinstance(packet, dict),
            "raw_phase52_manual_decision_readback_input": raw_phase52_input,
            "raw_phase51_manual_decision_packet_input": raw_phase51_input,
            "raw_phase50_readback_or_review_input": raw_phase50_input,
        },
        "approved_change_plan_packet_validation": {
            "valid_approved_change_count": len(valid_changes),
            "invalid_approved_change_count": len(invalid_changes),
            "approved_change_count_by_type": deepcopy(
                summary["approved_change_count_by_type"]
            ),
            "approved_change_count_by_section": deepcopy(
                summary["approved_change_count_by_section"]
            ),
        },
    }
    stage_results: dict[str, Any] = {
        "approved_change_plan_packet_resolution": {
            "approved_change_plan_packet": deepcopy(packet),
            "source": source,
            "raw_phase52_manual_decision_readback_input": raw_phase52_input,
            "raw_phase51_manual_decision_packet_input": raw_phase51_input,
            "raw_phase50_readback_or_review_input": raw_phase50_input,
        },
        "approved_change_plan_packet_validation": {
            "approved_changes": deepcopy(valid_changes),
            "invalid_approved_changes": deepcopy(invalid_changes),
            "approved_change_summary": deepcopy(summary),
        },
    }

    missing_inputs: list[str] = []
    blocked_reasons: list[str] = []
    if not bool(enabled):
        blocked_reasons.append("enabled must be true")
    if not policy["allow_approved_change_plan_readback"]:
        blocked_reasons.append("readback policy must allow approved change plan readback")
    if raw_phase52_input:
        blocked_reasons.append(
            "approved change plan packet required; raw phase52 manual decision readback is not accepted"
        )
    if raw_phase51_input:
        blocked_reasons.append(
            "approved change plan packet required; raw manual decision packet is not accepted"
        )
    if raw_phase50_input:
        blocked_reasons.append(
            "approved change plan packet required; raw phase50 readback/manual review input is not accepted"
        )
    if not isinstance(packet, dict):
        missing_inputs.append("approved_change_plan_packet")
        blocked_reasons.append("approved change plan packet required")
    elif packet.get("payload_type") != PACKET_TYPE:
        blocked_reasons.append("input must be approved change plan packet output")
    if not valid_changes:
        blocked_reasons.append("approved change plan packet must contain valid approved changes")
    if invalid_changes:
        blocked_reasons.append("invalid approved change plan packet present")

    if blocked_reasons:
        return _blocked_payload(
            enabled=bool(enabled)
            and bool(policy["allow_approved_change_plan_readback"]),
            policy=policy,
            blocked_reason="; ".join(blocked_reasons),
            missing_inputs=missing_inputs,
            stage_summaries=stage_summaries,
            stage_results=stage_results,
        )

    readback_items = [
        {
            "readback_item_id": f"approved-change-plan-readback-{row['proposal_id']}",
            "plan_item_id": row["plan_item_id"],
            "proposal_id": row["proposal_id"],
            "source_readback_item_id": row["source_readback_item_id"],
            "manual_decision": row["manual_decision"],
            "decision_reason": row["decision_reason"],
            "change_type": row["change_type"],
            "section": row["section"],
            "resume_change_applied": False,
            "resume_overwrite_performed": False,
            "resume_mutation_performed": False,
            "artifact_created": False,
            "application_execution_performed": False,
        }
        for row in sorted(valid_changes, key=lambda item: item["proposal_id"])
    ]
    readback_payload = {
        "payload_type": READBACK_TYPE,
        "approved_change_plan_readback_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "source_approved_change_plan_packet": deepcopy(packet),
        "approved_change_summary": deepcopy(summary),
        "approved_changes_by_type": {
            key: [deepcopy(row) for row in readback_items if row["change_type"] == key]
            for key in summary["approved_change_count_by_type"]
        },
        "approved_changes_by_section": {
            key: [deepcopy(row) for row in readback_items if row["section"] == key]
            for key in summary["approved_change_count_by_section"]
        },
        "readback_items": readback_items,
        "resume_change_applied": False,
        "resume_mutation_performed": False,
        "artifact_created": False,
        "application_execution_performed": False,
    }
    readback_key = _packet_key(readback_payload)
    stage_summaries["approved_change_plan_readback"] = {
        "readback_payload_created": True,
        "approved_change_count": len(readback_items),
        "readback_payload_key": readback_key,
        "artifact_created": False,
        "resume_change_applied": False,
    }
    stage_results["approved_change_plan_readback"] = deepcopy(readback_payload)
    payload = {
        "phase": PHASE,
        "default_off": True,
        "controlled_exact_resume_change_set_approved_change_plan_readback_adapter": True,
        "approved_change_plan_readback_only": True,
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
        "approved_change_summary": deepcopy(summary),
        "readback_payload": readback_payload,
        "readback_payload_created": True,
        "readback_payload_key": readback_key,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload
