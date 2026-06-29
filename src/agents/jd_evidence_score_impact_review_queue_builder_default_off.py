"""Default-off review queue builder for JD evidence score impacts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PHASE = "41A"
RECOMMENDATIONS = (
    "manual_review",
    "positive_review",
    "negative_review",
    "neutral_review",
    "unmatched",
    "unknown",
)
FALSE_ACTION_KEYS = (
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
    "evidence_matching_performed",
    "scoring_feature_preparation_performed",
    "contribution_preview_performed",
    "score_impact_preview_performed",
    "planning_annotation_performed",
    "review_packet_building_performed",
    "final_scoring_performed",
    "tailoring_opportunity_check_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "application_submission_performed",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "submission_performed",
    "auto_apply_performed",
    "auto_submit_performed",
)


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _string(value: Any) -> str:
    return str(value or "").strip()


def _number_or_none(value: Any) -> float | int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = float(text)
        except ValueError:
            return None
        if parsed.is_integer():
            return int(parsed)
        return parsed
    return None


def _int_policy(supplied: dict[str, Any], key: str, default: int) -> int:
    value = _number_or_none(supplied.get(key))
    if isinstance(value, int):
        return value
    return default


def _policy(value: dict[str, Any] | None) -> dict[str, Any]:
    supplied = value if isinstance(value, dict) else {}
    max_items = _number_or_none(supplied.get("max_queue_items"))
    if not isinstance(max_items, int) or max_items < 0:
        max_items = None
    return {
        "urgent_red_flag_priority": _int_policy(
            supplied,
            "urgent_red_flag_priority",
            100,
        ),
        "blocked_preview_priority": _int_policy(
            supplied,
            "blocked_preview_priority",
            90,
        ),
        "manual_review_priority": _int_policy(
            supplied,
            "manual_review_priority",
            80,
        ),
        "negative_review_priority": _int_policy(
            supplied,
            "negative_review_priority",
            70,
        ),
        "positive_review_priority": _int_policy(
            supplied,
            "positive_review_priority",
            60,
        ),
        "neutral_review_priority": _int_policy(
            supplied,
            "neutral_review_priority",
            40,
        ),
        "unmatched_priority": _int_policy(
            supplied,
            "unmatched_priority",
            30,
        ),
        "unknown_priority": _int_policy(
            supplied,
            "unknown_priority",
            20,
        ),
        "sort_by_absolute_delta_within_priority": _bool(
            supplied.get("sort_by_absolute_delta_within_priority", True)
        ),
        "max_queue_items": max_items,
    }


def _recommendation(value: Any) -> str:
    text = _string(value)
    if text in RECOMMENDATIONS and text != "unknown":
        return text
    if text == "unknown":
        return "unknown"
    return "unknown"


def _flatten_grouped(value: Any) -> list[Any]:
    if not isinstance(value, dict):
        return []
    rows: list[Any] = []
    for recommendation in RECOMMENDATIONS:
        grouped = value.get(recommendation)
        if isinstance(grouped, list):
            rows.extend(grouped)
    for key in sorted(str(key) for key in value.keys()):
        if key in RECOMMENDATIONS:
            continue
        grouped = value.get(key)
        if isinstance(grouped, list):
            rows.extend(grouped)
    return rows


def _rows_from_builder_result(
    builder_result: dict[str, Any] | None,
) -> tuple[list[Any], str]:
    if not isinstance(builder_result, dict):
        return [], "missing"
    if isinstance(builder_result.get("review_packets"), list):
        return list(builder_result["review_packets"]), "builder_result.review_packets"
    nested = builder_result.get("builder_result")
    if isinstance(nested, dict) and isinstance(nested.get("review_packets"), list):
        return (
            list(nested["review_packets"]),
            "builder_result.builder_result.review_packets",
        )
    grouped = _flatten_grouped(builder_result.get("review_packets_by_recommendation"))
    if grouped:
        return grouped, "builder_result.review_packets_by_recommendation"
    if isinstance(nested, dict):
        grouped = _flatten_grouped(nested.get("review_packets_by_recommendation"))
        if grouped:
            return (
                grouped,
                "builder_result.builder_result.review_packets_by_recommendation",
            )
    return [], "missing"


def _resolve_rows(
    review_packets: list[Any] | None,
    builder_result: dict[str, Any] | None,
) -> tuple[list[Any], str, list[str]]:
    if isinstance(review_packets, list):
        return list(review_packets), "review_packets", []
    rows, source = _rows_from_builder_result(builder_result)
    if rows:
        return rows, source, []
    return [], source, ["review_packets"]


def _priority(packet: dict[str, Any], *, policy: dict[str, Any]) -> tuple[int, str]:
    recommendation = _recommendation(packet.get("score_impact_review_recommendation"))
    if _bool(packet.get("requires_red_flag_review")):
        return policy["urgent_red_flag_priority"], "red_flag_review"
    if _bool(packet.get("score_preview_available")) is not True:
        return policy["blocked_preview_priority"], "blocked_score_preview"
    if recommendation == "manual_review":
        return policy["manual_review_priority"], "manual_review"
    if recommendation == "negative_review":
        return policy["negative_review_priority"], "negative_review"
    if recommendation == "positive_review":
        return policy["positive_review_priority"], "positive_review"
    if recommendation == "neutral_review":
        return policy["neutral_review_priority"], "neutral_review"
    if recommendation == "unmatched":
        return policy["unmatched_priority"], "unmatched"
    return policy["unknown_priority"], "unknown"


def _priority_band(priority: int, *, policy: dict[str, Any], reason: str) -> str:
    if reason in {"red_flag_review", "blocked_score_preview"}:
        return "urgent"
    if priority >= policy["manual_review_priority"]:
        return "high"
    if priority >= policy["positive_review_priority"]:
        return "medium"
    if priority >= policy["unmatched_priority"]:
        return "low"
    return "backlog"


def _queue_reason(
    packet: dict[str, Any],
    *,
    recommendation: str,
    priority_reason: str,
) -> str:
    if priority_reason == "red_flag_review":
        return "urgent:red_flag_review_required"
    if priority_reason == "blocked_score_preview":
        blocked = _string(packet.get("score_preview_blocked_reason")) or "score preview unavailable"
        return f"urgent:score_preview_blocked:{blocked}"
    band = _string(packet.get("impact_band")) or "unknown"
    delta = _number_or_none(packet.get("score_preview_delta"))
    delta_text = "unknown" if delta is None else str(delta)
    action = _string(packet.get("operator_next_action")) or "manual_review"
    return f"{recommendation}:{band}:delta={delta_text}:next={action}"


def _existing_score(packet: dict[str, Any], row_key: str) -> dict[str, Any] | None:
    if _bool(packet.get("existing_score_present")) is True:
        field = _string(packet.get("existing_score_field")) or "existing_score_value"
        return {
            "row_key": row_key,
            "field": field,
            "value": deepcopy(packet.get("existing_score_value")),
        }
    if packet.get("existing_score_value") not in (None, ""):
        return {
            "row_key": row_key,
            "field": "existing_score_value",
            "value": deepcopy(packet.get("existing_score_value")),
        }
    return None


def _row_key(packet: dict[str, Any], index: int) -> str:
    for field in ("item_id", "job_id", "row_id"):
        value = _string(packet.get(field))
        if value:
            return value
    return str(index)


def _queue_item(
    packet: dict[str, Any],
    *,
    index: int,
    policy: dict[str, Any],
) -> dict[str, Any]:
    priority, priority_reason = _priority(packet, policy=policy)
    recommendation = _recommendation(packet.get("score_impact_review_recommendation"))
    return {
        "queue_position": 0,
        "priority_rank": priority,
        "priority_band": _priority_band(
            priority,
            policy=policy,
            reason=priority_reason,
        ),
        "item_id": deepcopy(packet.get("item_id")),
        "job_id": deepcopy(packet.get("job_id")),
        "row_id": deepcopy(packet.get("row_id")),
        "title": deepcopy(packet.get("title")),
        "company": deepcopy(packet.get("company")),
        "location": deepcopy(packet.get("location")),
        "source_url": deepcopy(packet.get("source_url")),
        "score_impact_review_recommendation": recommendation,
        "score_preview_available": _bool(packet.get("score_preview_available")),
        "score_preview_blocked_reason": _string(
            packet.get("score_preview_blocked_reason")
        ),
        "existing_score_present": _bool(packet.get("existing_score_present")),
        "existing_score_field": deepcopy(packet.get("existing_score_field")),
        "existing_score_value": deepcopy(packet.get("existing_score_value")),
        "hypothetical_score_preview": deepcopy(
            packet.get("hypothetical_score_preview")
        ),
        "score_preview_delta": deepcopy(packet.get("score_preview_delta")),
        "impact_band": _string(packet.get("impact_band")),
        "requires_red_flag_review": _bool(packet.get("requires_red_flag_review")),
        "review_reason": _string(packet.get("review_reason")),
        "operator_next_action": _string(packet.get("operator_next_action")),
        "queue_reason": _queue_reason(
            packet,
            recommendation=recommendation,
            priority_reason=priority_reason,
        ),
        "final_score_produced": False,
        "existing_score_changed": False,
        "_input_index": index,
    }


def _sort_key(item: dict[str, Any], *, sort_delta: bool) -> tuple[Any, ...]:
    delta = _number_or_none(item.get("score_preview_delta"))
    absolute_delta = abs(float(delta)) if delta is not None else -1.0
    delta_key = -absolute_delta if sort_delta else 0
    return (-int(item["priority_rank"]), delta_key, int(item["_input_index"]))


def _without_internal(item: dict[str, Any], position: int) -> dict[str, Any]:
    copied: dict[str, Any] = {}
    for key, value in item.items():
        if key == "_input_index":
            continue
        copied[key] = deepcopy(value)
    copied["queue_position"] = position
    return copied


def _group_by_priority(queue: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for item in queue:
        key = str(item["priority_rank"])
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(deepcopy(item))
    return grouped


def _payload(
    *,
    rows_present: bool,
    row_count: int,
    valid_count: int,
    invalid_count: int,
    policy: dict[str, Any],
    queue: list[dict[str, Any]],
    existing_scores: list[dict[str, Any]],
    findings: dict[str, Any],
    missing_inputs: list[str],
) -> dict[str, Any]:
    urgent_count = len([item for item in queue if item["priority_band"] == "urgent"])
    summary = {
        "review_queue_count": len(queue),
        "urgent_review_count": urgent_count,
        "manual_review_count": len(
            [
                item
                for item in queue
                if item["score_impact_review_recommendation"] == "manual_review"
            ]
        ),
        "positive_review_count": len(
            [
                item
                for item in queue
                if item["score_impact_review_recommendation"] == "positive_review"
            ]
        ),
        "negative_review_count": len(
            [
                item
                for item in queue
                if item["score_impact_review_recommendation"] == "negative_review"
            ]
        ),
        "neutral_review_count": len(
            [
                item
                for item in queue
                if item["score_impact_review_recommendation"] == "neutral_review"
            ]
        ),
        "unmatched_count": len(
            [
                item
                for item in queue
                if item["score_impact_review_recommendation"] == "unmatched"
            ]
        ),
        "unknown_review_count": len(
            [
                item
                for item in queue
                if item["score_impact_review_recommendation"] == "unknown"
            ]
        ),
        "final_score_produced": False,
        "existing_score_changed": False,
    }
    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_evidence_score_impact_review_queue_builder": True,
        "read_only": True,
        "advisory_only": True,
        "preview_only": True,
        "deterministic_review_queue_building": True,
        "manual_review_queue_only": True,
        "requires_manual_user_control": True,
        "review_packets_present": rows_present,
        "review_packet_count": row_count,
        "valid_review_packet_count": valid_count,
        "invalid_review_packet_count": invalid_count,
        "queue_policy": deepcopy(policy),
        "review_queue": deepcopy(queue),
        "review_queue_by_priority": _group_by_priority(queue),
        "review_queue_summary": summary,
        "urgent_review_count": summary["urgent_review_count"],
        "manual_review_count": summary["manual_review_count"],
        "positive_review_count": summary["positive_review_count"],
        "negative_review_count": summary["negative_review_count"],
        "neutral_review_count": summary["neutral_review_count"],
        "unmatched_count": summary["unmatched_count"],
        "unknown_review_count": summary["unknown_review_count"],
        "score_preview_available_count": len(
            [item for item in queue if item["score_preview_available"] is True]
        ),
        "score_preview_blocked_count": len(
            [item for item in queue if item["score_preview_available"] is not True]
        ),
        "red_flag_review_count": len(
            [item for item in queue if item["requires_red_flag_review"] is True]
        ),
        "existing_score_fields_detected": deepcopy(existing_scores),
        "existing_scores_preserved": True,
        "queue_findings": deepcopy(findings),
        "missing_inputs": list(missing_inputs),
        "queue_key": "|".join(
            (
                f"phase={PHASE}",
                f"packets={row_count}",
                f"valid={valid_count}",
                f"invalid={invalid_count}",
                f"queue={len(queue)}",
                f"urgent={summary['urgent_review_count']}",
                f"manual={summary['manual_review_count']}",
                f"positive={summary['positive_review_count']}",
                f"negative={summary['negative_review_count']}",
                f"neutral={summary['neutral_review_count']}",
                f"unmatched={summary['unmatched_count']}",
                f"unknown={summary['unknown_review_count']}",
            )
        ),
        "hypothetical_score_preview_produced": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def build_jd_evidence_score_impact_review_queue_builder_default_off(
    review_packets: list[Any] | None = None,
    builder_result: dict[str, Any] | None = None,
    queue_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic manual review queue from Phase 40 review packets."""

    policy = _policy(queue_policy)
    rows, source, missing_inputs = _resolve_rows(review_packets, builder_result)
    invalid_rows: list[dict[str, Any]] = []
    items: list[dict[str, Any]] = []
    existing_scores: list[dict[str, Any]] = []

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            invalid_rows.append(
                {
                    "input_index": index,
                    "reason": "review packet must be a dictionary",
                }
            )
            continue
        copied = deepcopy(row)
        item = _queue_item(copied, index=index, policy=policy)
        items.append(item)
        score = _existing_score(copied, _row_key(copied, index))
        if score is not None:
            existing_scores.append(score)

    sorted_items = sorted(
        items,
        key=lambda item: _sort_key(
            item,
            sort_delta=policy["sort_by_absolute_delta_within_priority"],
        ),
    )
    before_truncation = len(sorted_items)
    max_items = policy["max_queue_items"]
    truncated = False
    if isinstance(max_items, int):
        sorted_items = sorted_items[:max_items]
        truncated = len(sorted_items) < before_truncation
    queue = [
        _without_internal(item, position)
        for position, item in enumerate(sorted_items, start=1)
    ]
    if rows and not queue and "review_packets" not in missing_inputs:
        missing_inputs.append("valid_review_packets")

    findings = {
        "review_packets_source": source,
        "copied_review_packets_only": True,
        "invalid_review_packets": deepcopy(invalid_rows),
        "invalid_review_packet_count": len(invalid_rows),
        "queue_truncated": truncated,
        "queue_items_before_truncation": before_truncation,
        "queue_items_after_truncation": len(queue),
        "review_packet_building_performed": False,
        "score_impact_preview_performed": False,
        "planning_annotation_performed": False,
        "final_scoring_performed": False,
        "existing_score_changed": False,
        "executable_callbacks_included": False,
        "provider_request_payloads_included": False,
        "network_request_payloads_included": False,
        "mutation_commands_included": False,
        "db_write_commands_included": False,
        "application_submission_commands_included": False,
    }

    return _payload(
        rows_present=bool(rows),
        row_count=len(rows),
        valid_count=len(rows) - len(invalid_rows),
        invalid_count=len(invalid_rows),
        policy=policy,
        queue=queue,
        existing_scores=existing_scores,
        findings=findings,
        missing_inputs=missing_inputs,
    )
