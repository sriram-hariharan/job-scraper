"""Default-off hypothetical score impact preview for JD evidence contributions."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PHASE = "38A"
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


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _optional_number(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _policy(value: dict[str, Any] | None) -> dict[str, Any]:
    supplied = value if isinstance(value, dict) else {}
    return {
        "score_floor": _number(supplied.get("score_floor", 0), 0),
        "score_ceiling": _number(supplied.get("score_ceiling", 100), 100),
        "default_base_score": _optional_number(supplied.get("default_base_score")),
        "require_existing_score_for_preview": _bool(
            supplied.get("require_existing_score_for_preview", False)
        ),
        "red_flag_review_blocks_preview_score": _bool(
            supplied.get("red_flag_review_blocks_preview_score", True)
        ),
        "round_digits": max(0, _int(supplied.get("round_digits", 4), 4)),
    }


def _rows_from_inputs(
    contribution_packet: dict[str, Any] | None,
    contribution_rows: list[Any] | None,
) -> tuple[list[Any], str]:
    if isinstance(contribution_rows, list):
        return list(contribution_rows), "contribution_rows"
    if isinstance(contribution_packet, dict):
        if isinstance(contribution_packet.get("contribution_rows"), list):
            return list(contribution_packet["contribution_rows"]), "contribution_packet"
        preview_result = contribution_packet.get("preview_result")
        if isinstance(preview_result, dict):
            if isinstance(preview_result.get("contribution_rows"), list):
                return list(preview_result["contribution_rows"]), "preview_result"
            packet = preview_result.get("contribution_packet")
            if isinstance(packet, dict) and isinstance(
                packet.get("contribution_rows"),
                list,
            ):
                return list(packet["contribution_rows"]), "preview_result_packet"
    return [], "missing"


def _row_key(row: dict[str, Any], index: int) -> str:
    for name in ("row_key", "item_id", "job_id", "id"):
        value = row.get(name)
        if value not in (None, "", [], {}):
            return str(value)
    return str(index)


def _bounded(value: float, *, policy: dict[str, Any]) -> float:
    lower = min(policy["score_floor"], policy["score_ceiling"])
    upper = max(policy["score_floor"], policy["score_ceiling"])
    return max(lower, min(upper, value))


def _round(value: float | None, *, policy: dict[str, Any]) -> float | None:
    if value is None:
        return None
    return round(value, policy["round_digits"])


def _base_score(row: dict[str, Any], *, policy: dict[str, Any]) -> tuple[float | None, str]:
    if _bool(row.get("existing_score_present")) is True:
        score = _optional_number(row.get("existing_score_value"))
        if score is not None:
            return score, ""
        if policy["require_existing_score_for_preview"] is True:
            return None, "existing score value is not numeric"
    default_score = policy["default_base_score"]
    if default_score is not None:
        return default_score, ""
    if policy["require_existing_score_for_preview"] is True:
        return None, "existing score required for preview"
    return 0.0, ""


def _impact_band(
    *,
    available: bool,
    blocked_reason: str,
    delta: float | None,
    requires_review: bool,
) -> str:
    if not available:
        if requires_review and blocked_reason == "red flag review required":
            return "review"
        return "blocked"
    if delta is None or delta == 0:
        return "neutral"
    if delta > 0:
        return "positive"
    return "negative"


def _impact_row(
    row: dict[str, Any],
    *,
    index: int,
    policy: dict[str, Any],
) -> dict[str, Any]:
    requires_review = _bool(row.get("requires_red_flag_review"))
    contribution = _number(row.get("bounded_advisory_contribution_points"), 0.0)
    existing_score_present = _bool(row.get("existing_score_present"))
    base_score, blocked_reason = _base_score(row, policy=policy)
    if (
        policy["red_flag_review_blocks_preview_score"] is True
        and requires_review is True
    ):
        blocked_reason = "red flag review required"
        base_score = base_score if base_score is not None else None
    available = blocked_reason == "" and base_score is not None
    hypothetical = None
    delta = None
    if available:
        hypothetical = _bounded(base_score + contribution, policy=policy)
        delta = hypothetical - base_score
    band = _impact_band(
        available=available,
        blocked_reason=blocked_reason,
        delta=delta,
        requires_review=requires_review,
    )
    return {
        "item_id": str(row.get("item_id", "") or ""),
        "job_id": str(row.get("job_id", "") or ""),
        "title": str(row.get("title", "") or ""),
        "company": str(row.get("company", "") or ""),
        "existing_score_present": existing_score_present,
        "existing_score_field": str(row.get("existing_score_field", "") or ""),
        "existing_score_value": deepcopy(row.get("existing_score_value")),
        "base_score_for_preview": _round(base_score, policy=policy),
        "bounded_advisory_contribution_points": _round(contribution, policy=policy),
        "hypothetical_score_preview": _round(hypothetical, policy=policy),
        "score_preview_delta": _round(delta, policy=policy),
        "score_preview_available": available,
        "score_preview_blocked_reason": blocked_reason,
        "impact_band": band,
        "requires_red_flag_review": requires_review,
        "hypothetical_score_preview_produced": available,
        "final_score_produced": False,
        "existing_score_changed": False,
        "row_key": _row_key(row, index),
    }


def _payload(
    *,
    source: str,
    raw_count: int,
    impact_rows: list[dict[str, Any]],
    unmapped_rows: list[dict[str, Any]],
    policy: dict[str, Any],
    missing_inputs: list[str],
) -> dict[str, Any]:
    valid_count = len(impact_rows)
    invalid_count = len(unmapped_rows)
    available_rows = [row for row in impact_rows if row["score_preview_available"]]
    blocked_rows = [row for row in impact_rows if not row["score_preview_available"]]
    positive_rows = [row for row in impact_rows if row["impact_band"] == "positive"]
    negative_rows = [row for row in impact_rows if row["impact_band"] == "negative"]
    neutral_rows = [row for row in impact_rows if row["impact_band"] == "neutral"]
    red_review_rows = [
        row for row in impact_rows if row["requires_red_flag_review"] is True
    ]
    existing_scores = [
        {
            "row_key": row["row_key"],
            "field": row["existing_score_field"],
            "value": deepcopy(row["existing_score_value"]),
        }
        for row in impact_rows
        if row["existing_score_present"] is True
    ]
    score_values = [
        {
            "row_key": row["row_key"],
            "base_score_for_preview": row["base_score_for_preview"],
            "hypothetical_score_preview": row["hypothetical_score_preview"],
            "score_preview_delta": row["score_preview_delta"],
        }
        for row in available_rows
    ]
    packet_rows = [
        {
            "row_key": row["row_key"],
            "item_id": row["item_id"],
            "job_id": row["job_id"],
            "hypothetical_score_preview": row["hypothetical_score_preview"],
            "score_preview_delta": row["score_preview_delta"],
            "score_preview_available": row["score_preview_available"],
            "impact_band": row["impact_band"],
            "final_score_produced": False,
        }
        for row in impact_rows
    ]
    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_evidence_score_impact_preview": True,
        "read_only": True,
        "advisory_only": True,
        "preview_only": True,
        "deterministic_score_impact_preview": True,
        "requires_manual_user_control": True,
        "contribution_rows_present": raw_count > 0,
        "contribution_row_count": raw_count,
        "valid_contribution_row_count": valid_count,
        "invalid_contribution_row_count": invalid_count,
        "impact_policy": deepcopy(policy),
        "impact_rows": deepcopy(impact_rows),
        "unmapped_rows": deepcopy(unmapped_rows),
        "impact_packet": {
            "phase": PHASE,
            "packet_type": "jd_evidence_score_impact_preview",
            "source": source,
            "impact_row_count": valid_count,
            "impact_rows": deepcopy(packet_rows),
            "final_score_included": False,
        },
        "impact_summary": {
            "contribution_row_count": raw_count,
            "valid_contribution_row_count": valid_count,
            "invalid_contribution_row_count": invalid_count,
            "preview_score_available_count": len(available_rows),
            "preview_score_blocked_count": len(blocked_rows),
            "positive_impact_count": len(positive_rows),
            "negative_impact_count": len(negative_rows),
            "neutral_impact_count": len(neutral_rows),
            "red_flag_review_count": len(red_review_rows),
            "final_score_produced": False,
            "existing_score_changed": False,
        },
        "preview_score_available_count": len(available_rows),
        "preview_score_blocked_count": len(blocked_rows),
        "positive_impact_count": len(positive_rows),
        "negative_impact_count": len(negative_rows),
        "neutral_impact_count": len(neutral_rows),
        "red_flag_review_count": len(red_review_rows),
        "existing_score_fields_detected": deepcopy(existing_scores),
        "existing_scores_preserved": True,
        "score_preview_values": score_values,
        "impact_findings": {
            "source": source,
            "score_impact_preview_only": True,
            "hypothetical_score_preview_values": True,
            "existing_scores_preserved": True,
            "final_score_produced": False,
            "matching_scoring_module_called": False,
        },
        "missing_inputs": list(missing_inputs),
        "impact_key": "|".join(
            (
                f"phase={PHASE}",
                f"source={source}",
                f"rows={raw_count}",
                f"valid={valid_count}",
                f"invalid={invalid_count}",
                f"available={len(available_rows)}",
                f"blocked={len(blocked_rows)}",
                f"positive={len(positive_rows)}",
                f"negative={len(negative_rows)}",
                f"red_review={len(red_review_rows)}",
            )
        ),
        "hypothetical_score_preview_produced": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def build_jd_evidence_score_impact_preview_default_off(
    contribution_packet: dict[str, Any] | None = None,
    contribution_rows: list[Any] | None = None,
    impact_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic hypothetical score impact previews."""

    policy = _policy(impact_policy)
    rows, source = _rows_from_inputs(contribution_packet, contribution_rows)
    if not rows:
        return _payload(
            source=source,
            raw_count=0,
            impact_rows=[],
            unmapped_rows=[],
            policy=policy,
            missing_inputs=["contribution_rows"],
        )

    impact_rows: list[dict[str, Any]] = []
    unmapped_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            unmapped_rows.append(
                {
                    "input_index": index,
                    "reason": "contribution row must be a dictionary",
                }
            )
            continue
        impact_rows.append(_impact_row(row, index=index, policy=policy))

    return _payload(
        source=source,
        raw_count=len(rows),
        impact_rows=impact_rows,
        unmapped_rows=unmapped_rows,
        policy=policy,
        missing_inputs=[],
    )
