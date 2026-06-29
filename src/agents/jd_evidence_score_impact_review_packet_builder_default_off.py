"""Default-off review packet builder for JD evidence score impacts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PHASE = "40A"
DEFAULT_GROUP_ORDER = (
    "manual_review",
    "positive_review",
    "negative_review",
    "neutral_review",
    "unmatched",
    "unknown",
)
NEXT_ACTION_BY_RECOMMENDATION = {
    "manual_review": "review_before_scoring",
    "positive_review": "review_positive_impact",
    "negative_review": "review_negative_impact",
    "neutral_review": "review_neutral_impact",
    "unmatched": "match_or_ignore_unmatched",
    "unknown": "inspect_unknown_recommendation",
}
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


def _string(value: Any) -> str:
    return str(value or "").strip()


def _policy(value: dict[str, Any] | None) -> dict[str, Any]:
    supplied = value if isinstance(value, dict) else {}
    raw_order = supplied.get("group_order", DEFAULT_GROUP_ORDER)
    group_order: list[str] = []
    if isinstance(raw_order, list | tuple):
        for item in raw_order:
            recommendation = _recommendation(item)
            if recommendation not in group_order:
                group_order.append(recommendation)
    for recommendation in DEFAULT_GROUP_ORDER:
        if recommendation not in group_order:
            group_order.append(recommendation)
    max_missing = _number_or_none(supplied.get("max_missing_reason_items"))
    if not isinstance(max_missing, int) or max_missing < 0:
        max_missing = 10
    return {
        "include_full_annotated_row": _bool(
            supplied.get("include_full_annotated_row", False)
        ),
        "include_score_impact_preview_result": _bool(
            supplied.get("include_score_impact_preview_result", True)
        ),
        "max_missing_reason_items": max_missing,
        "group_order": group_order,
    }


def _recommendation(value: Any) -> str:
    text = _string(value)
    if text in NEXT_ACTION_BY_RECOMMENDATION and text != "unknown":
        return text
    if text == "unknown":
        return "unknown"
    return "unknown"


def _rows_from_annotator_result(
    annotator_result: dict[str, Any] | None,
) -> tuple[list[Any], str]:
    if not isinstance(annotator_result, dict):
        return [], "missing"
    if isinstance(annotator_result.get("annotated_rows"), list):
        return list(annotator_result["annotated_rows"]), "annotator_result.annotated_rows"
    nested = annotator_result.get("annotator_result")
    if isinstance(nested, dict):
        if isinstance(nested.get("annotated_rows"), list):
            return list(nested["annotated_rows"]), "annotator_result.annotator_result.annotated_rows"
        summary = nested.get("annotation_summary")
        if isinstance(summary, dict) and isinstance(summary.get("annotated_rows"), list):
            return (
                list(summary["annotated_rows"]),
                "annotator_result.annotator_result.annotation_summary.annotated_rows",
            )
    return [], "missing"


def _resolve_rows(
    annotated_rows: list[Any] | None,
    annotator_result: dict[str, Any] | None,
) -> tuple[list[Any], str, list[str]]:
    if isinstance(annotated_rows, list):
        return list(annotated_rows), "annotated_rows", []
    rows, source = _rows_from_annotator_result(annotator_result)
    if rows:
        return rows, source, []
    return [], source, ["annotated_rows"]


def _preview(row: dict[str, Any]) -> dict[str, Any]:
    value = row.get("score_impact_preview")
    if isinstance(value, dict):
        return value
    value = row.get("score_impact_preview_result")
    if isinstance(value, dict):
        return value
    return {}


def _existing_score(row: dict[str, Any], row_key: str) -> dict[str, Any] | None:
    if _bool(row.get("existing_score_present")) is True:
        field = _string(row.get("existing_score_field")) or "existing_score_value"
        return {
            "row_key": row_key,
            "field": field,
            "value": deepcopy(row.get("existing_score_value")),
        }
    for field in (
        "existing_score_value",
        "final_score",
        "score",
        "fit_score",
        "application_score",
    ):
        if field in row and row.get(field) not in (None, ""):
            return {
                "row_key": row_key,
                "field": field,
                "value": deepcopy(row.get(field)),
            }
    return None


def _row_key(row: dict[str, Any], index: int) -> str:
    for field in ("item_id", "job_id", "id"):
        value = _string(row.get(field))
        if value:
            return value
    return str(index)


def _review_reason(
    *,
    recommendation: str,
    score_preview_available: bool,
    blocked_reason: str,
    requires_red_flag_review: bool,
    impact_band: str,
    score_preview_delta: Any,
) -> str:
    if score_preview_available is not True:
        reason = blocked_reason or "score preview unavailable"
        return f"score_preview_blocked:{reason}"
    if requires_red_flag_review is True:
        return "red_flag_review_required"
    delta = _number_or_none(score_preview_delta)
    delta_text = "unknown" if delta is None else str(delta)
    band = impact_band or "unknown"
    if recommendation == "positive_review":
        return f"positive_impact:{band}:delta={delta_text}"
    if recommendation == "negative_review":
        return f"negative_impact:{band}:delta={delta_text}"
    if recommendation == "neutral_review":
        return f"neutral_impact:{band}:delta={delta_text}"
    if recommendation == "unmatched":
        return "unmatched_annotation"
    if recommendation == "manual_review":
        return f"manual_review:{band}:delta={delta_text}"
    return "unknown_recommendation"


def _packet(
    row: dict[str, Any],
    *,
    index: int,
    policy: dict[str, Any],
) -> dict[str, Any]:
    preview = _preview(row)
    recommendation = _recommendation(row.get("score_impact_review_recommendation"))
    blocked_reason = _string(preview.get("score_preview_blocked_reason"))
    available = _bool(preview.get("score_preview_available"))
    red_flag = _bool(preview.get("requires_red_flag_review"))
    impact_band = _string(preview.get("impact_band"))
    delta = deepcopy(preview.get("score_preview_delta"))
    packet = {
        "item_id": deepcopy(row.get("item_id")),
        "job_id": deepcopy(row.get("job_id")),
        "row_id": deepcopy(row.get("id")),
        "title": deepcopy(row.get("title")),
        "company": deepcopy(row.get("company")),
        "location": deepcopy(row.get("location")),
        "source_url": deepcopy(row.get("source_url")),
        "score_impact_review_recommendation": recommendation,
        "score_impact_annotation_ready": _bool(
            row.get("score_impact_annotation_ready")
        ),
        "score_impact_annotation_source": _string(
            row.get("score_impact_annotation_source")
        ),
        "score_preview_available": available,
        "score_preview_blocked_reason": blocked_reason,
        "existing_score_present": _bool(row.get("existing_score_present")),
        "existing_score_field": deepcopy(row.get("existing_score_field")),
        "existing_score_value": deepcopy(row.get("existing_score_value")),
        "hypothetical_score_preview": deepcopy(
            preview.get("hypothetical_score_preview")
        ),
        "score_preview_delta": delta,
        "impact_band": impact_band,
        "requires_red_flag_review": red_flag,
        "review_reason": _review_reason(
            recommendation=recommendation,
            score_preview_available=available,
            blocked_reason=blocked_reason,
            requires_red_flag_review=red_flag,
            impact_band=impact_band,
            score_preview_delta=delta,
        ),
        "operator_next_action": NEXT_ACTION_BY_RECOMMENDATION[recommendation],
        "final_score_produced": False,
        "existing_score_changed": False,
    }
    if policy["include_score_impact_preview_result"]:
        packet["score_impact_preview_result"] = deepcopy(
            row.get("score_impact_preview_result")
        )
    if policy["include_full_annotated_row"]:
        packet["annotated_row"] = deepcopy(row)
    packet["packet_row_key"] = _row_key(row, index)
    return packet


def _empty_grouped(policy: dict[str, Any]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for recommendation in policy["group_order"]:
        grouped[recommendation] = []
    return grouped


def _payload(
    *,
    rows_present: bool,
    row_count: int,
    valid_count: int,
    invalid_count: int,
    policy: dict[str, Any],
    review_packets: list[dict[str, Any]],
    grouped: dict[str, list[dict[str, Any]]],
    existing_scores: list[dict[str, Any]],
    findings: dict[str, Any],
    missing_inputs: list[str],
) -> dict[str, Any]:
    packet_count = len(review_packets)
    summary = {
        "review_packet_count": packet_count,
        "manual_review_count": len(grouped.get("manual_review", [])),
        "positive_review_count": len(grouped.get("positive_review", [])),
        "negative_review_count": len(grouped.get("negative_review", [])),
        "neutral_review_count": len(grouped.get("neutral_review", [])),
        "unmatched_count": len(grouped.get("unmatched", [])),
        "unknown_review_count": len(grouped.get("unknown", [])),
        "final_score_produced": False,
        "existing_score_changed": False,
    }
    available_count = len(
        [
            packet
            for packet in review_packets
            if packet.get("score_preview_available") is True
        ]
    )
    blocked_count = len(
        [
            packet
            for packet in review_packets
            if packet.get("score_preview_available") is not True
        ]
    )
    red_flag_count = len(
        [
            packet
            for packet in review_packets
            if packet.get("requires_red_flag_review") is True
        ]
    )
    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_evidence_score_impact_review_packet_builder": True,
        "read_only": True,
        "advisory_only": True,
        "preview_only": True,
        "deterministic_review_packet_building": True,
        "manual_review_packet_only": True,
        "requires_manual_user_control": True,
        "annotated_rows_present": rows_present,
        "annotated_row_count": row_count,
        "valid_annotated_row_count": valid_count,
        "invalid_annotated_row_count": invalid_count,
        "review_policy": deepcopy(policy),
        "review_packets": deepcopy(review_packets),
        "review_packets_by_recommendation": deepcopy(grouped),
        "review_packet_summary": summary,
        "manual_review_count": summary["manual_review_count"],
        "positive_review_count": summary["positive_review_count"],
        "negative_review_count": summary["negative_review_count"],
        "neutral_review_count": summary["neutral_review_count"],
        "unmatched_count": summary["unmatched_count"],
        "unknown_review_count": summary["unknown_review_count"],
        "score_preview_available_count": available_count,
        "score_preview_blocked_count": blocked_count,
        "red_flag_review_count": red_flag_count,
        "existing_score_fields_detected": deepcopy(existing_scores),
        "existing_scores_preserved": True,
        "packet_findings": deepcopy(findings),
        "missing_inputs": list(missing_inputs),
        "packet_key": "|".join(
            (
                f"phase={PHASE}",
                f"rows={row_count}",
                f"valid={valid_count}",
                f"invalid={invalid_count}",
                f"packets={packet_count}",
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


def build_jd_evidence_score_impact_review_packet_builder_default_off(
    annotated_rows: list[Any] | None = None,
    annotator_result: dict[str, Any] | None = None,
    review_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic manual-review packets from Phase 39 annotated rows."""

    policy = _policy(review_policy)
    rows, source, missing_inputs = _resolve_rows(annotated_rows, annotator_result)
    grouped = _empty_grouped(policy)
    invalid_rows: list[dict[str, Any]] = []
    packets_by_recommendation: dict[str, list[dict[str, Any]]] = _empty_grouped(policy)
    existing_scores: list[dict[str, Any]] = []

    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            invalid_rows.append(
                {
                    "input_index": index,
                    "reason": "annotated row must be a dictionary",
                }
            )
            continue
        copied = deepcopy(row)
        packet = _packet(copied, index=index, policy=policy)
        recommendation = packet["score_impact_review_recommendation"]
        if recommendation not in packets_by_recommendation:
            packets_by_recommendation[recommendation] = []
        packets_by_recommendation[recommendation].append(packet)
        score = _existing_score(copied, packet["packet_row_key"])
        if score is not None:
            existing_scores.append(score)

    review_packets: list[dict[str, Any]] = []
    for recommendation in policy["group_order"]:
        if recommendation not in grouped:
            grouped[recommendation] = []
        for packet in packets_by_recommendation.get(recommendation, []):
            grouped[recommendation].append(deepcopy(packet))
            review_packets.append(deepcopy(packet))

    if rows and not review_packets and "annotated_rows" not in missing_inputs:
        missing_inputs.append("valid_annotated_rows")

    findings = {
        "annotated_rows_source": source,
        "copied_annotated_rows_only": True,
        "invalid_annotated_rows": invalid_rows[: policy["max_missing_reason_items"]],
        "invalid_annotated_row_count": len(invalid_rows),
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
        review_packets=review_packets,
        grouped=grouped,
        existing_scores=existing_scores,
        findings=findings,
        missing_inputs=missing_inputs,
    )
