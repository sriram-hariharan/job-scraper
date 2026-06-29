"""Default-off advisory contribution preview for JD evidence scoring features."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PHASE = "37A"
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


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _policy(value: dict[str, Any] | None) -> dict[str, Any]:
    supplied = value if isinstance(value, dict) else {}
    return {
        "max_positive_contribution_points": _number(
            supplied.get("max_positive_contribution_points", 12),
            12,
        ),
        "max_negative_contribution_points": _number(
            supplied.get("max_negative_contribution_points", -12),
            -12,
        ),
        "required_skill_weight": _number(supplied.get("required_skill_weight", 6), 6),
        "preferred_skill_weight": _number(
            supplied.get("preferred_skill_weight", 2),
            2,
        ),
        "tool_weight": _number(supplied.get("tool_weight", 2), 2),
        "responsibility_weight": _number(
            supplied.get("responsibility_weight", 2),
            2,
        ),
        "missing_required_skill_penalty": _number(
            supplied.get("missing_required_skill_penalty", -1),
            -1,
        ),
        "missing_tool_penalty": _number(supplied.get("missing_tool_penalty", -0.5), -0.5),
        "red_flag_penalty": _number(supplied.get("red_flag_penalty", -3), -3),
        "red_flag_review_threshold": max(
            0,
            _int(supplied.get("red_flag_review_threshold", 1), 1),
        ),
    }


def _rows_from_inputs(
    feature_packet: dict[str, Any] | None,
    scoring_feature_rows: list[Any] | None,
) -> tuple[list[Any], str]:
    if isinstance(scoring_feature_rows, list):
        return list(scoring_feature_rows), "scoring_feature_rows"
    if isinstance(feature_packet, dict) and isinstance(
        feature_packet.get("scoring_feature_rows"),
        list,
    ):
        return list(feature_packet["scoring_feature_rows"]), "feature_packet"
    return [], "missing"


def _row_key(row: dict[str, Any], index: int) -> str:
    for name in ("row_key", "item_id", "job_id", "id"):
        value = row.get(name)
        if _present(value):
            return str(value)
    return str(index)


def _count_from_row(row: dict[str, Any], count_key: str, list_key: str) -> int:
    value = row.get(count_key)
    if _present(value):
        return max(0, _int(value, 0))
    listed = row.get(list_key)
    if isinstance(listed, list):
        return len(listed)
    return 0


def _list_from_row(row: dict[str, Any], list_key: str) -> list[Any]:
    value = row.get(list_key)
    return deepcopy(value) if isinstance(value, list) else []


def _bounded(value: float, *, policy: dict[str, Any]) -> float:
    lower = min(
        policy["max_negative_contribution_points"],
        policy["max_positive_contribution_points"],
    )
    upper = max(
        policy["max_negative_contribution_points"],
        policy["max_positive_contribution_points"],
    )
    return max(lower, min(upper, value))


def _contribution_band(value: float, *, requires_review: bool) -> str:
    if requires_review:
        return "review"
    if value >= 8:
        return "strong_positive"
    if value > 1:
        return "positive"
    if value < 0:
        return "negative"
    return "neutral"


def _contribution_row(
    row: dict[str, Any],
    *,
    index: int,
    policy: dict[str, Any],
) -> dict[str, Any]:
    required_ratio = _number(row.get("required_skill_coverage_ratio"), 0.0)
    preferred_ratio = _number(row.get("preferred_skill_coverage_ratio"), 0.0)
    tool_ratio = _number(row.get("tool_coverage_ratio"), 0.0)
    responsibility_ratio = _number(row.get("responsibility_coverage_ratio"), 0.0)
    missing_required_count = _count_from_row(
        row,
        "missing_required_skill_count",
        "missing_required_skills",
    )
    missing_tool_count = _count_from_row(row, "missing_tool_count", "missing_tools")
    red_flag_count = _count_from_row(row, "red_flag_count", "red_flag_findings")
    positive_points = (
        required_ratio * policy["required_skill_weight"]
        + preferred_ratio * policy["preferred_skill_weight"]
        + tool_ratio * policy["tool_weight"]
        + responsibility_ratio * policy["responsibility_weight"]
    )
    missing_required_penalty = (
        missing_required_count * policy["missing_required_skill_penalty"]
    )
    missing_tool_penalty = missing_tool_count * policy["missing_tool_penalty"]
    red_flag_penalty = red_flag_count * policy["red_flag_penalty"]
    advisory_points = (
        positive_points
        + missing_required_penalty
        + missing_tool_penalty
        + red_flag_penalty
    )
    bounded_points = _bounded(advisory_points, policy=policy)
    requires_review = (
        red_flag_count >= policy["red_flag_review_threshold"]
        or _bool(row.get("requires_red_flag_review")) is True
    )
    scoring_inputs_ready = _bool(row.get("scoring_inputs_ready"))
    evidence_ready = _bool(row.get("evidence_ready"))
    band = _contribution_band(bounded_points, requires_review=requires_review)
    return {
        "item_id": str(row.get("item_id", "") or ""),
        "job_id": str(row.get("job_id", "") or ""),
        "title": str(row.get("title", "") or ""),
        "company": str(row.get("company", "") or ""),
        "existing_score_present": _bool(row.get("existing_score_present")),
        "existing_score_field": str(row.get("existing_score_field", "") or ""),
        "existing_score_value": deepcopy(row.get("existing_score_value")),
        "evidence_ready": evidence_ready,
        "scoring_inputs_ready": scoring_inputs_ready,
        "required_skill_coverage_ratio": required_ratio,
        "preferred_skill_coverage_ratio": preferred_ratio,
        "tool_coverage_ratio": tool_ratio,
        "responsibility_coverage_ratio": responsibility_ratio,
        "positive_evidence_contribution_points": round(positive_points, 6),
        "missing_required_skill_penalty_points": round(missing_required_penalty, 6),
        "missing_tool_penalty_points": round(missing_tool_penalty, 6),
        "red_flag_penalty_points": round(red_flag_penalty, 6),
        "advisory_evidence_contribution_points": round(advisory_points, 6),
        "bounded_advisory_contribution_points": round(bounded_points, 6),
        "contribution_band": band,
        "requires_red_flag_review": requires_review,
        "final_score_produced": False,
        "existing_score_changed": False,
        "row_key": _row_key(row, index),
        "missing_required_skill_count": missing_required_count,
        "missing_tool_count": missing_tool_count,
        "red_flag_count": red_flag_count,
        "missing_required_skills": _list_from_row(row, "missing_required_skills"),
        "missing_tools": _list_from_row(row, "missing_tools"),
        "red_flag_findings": _list_from_row(row, "red_flag_findings"),
    }


def _payload(
    *,
    source: str,
    raw_count: int,
    contribution_rows: list[dict[str, Any]],
    unmapped_rows: list[dict[str, Any]],
    policy: dict[str, Any],
    missing_inputs: list[str],
) -> dict[str, Any]:
    valid_count = len(contribution_rows)
    invalid_count = len(unmapped_rows)
    positives = [
        row
        for row in contribution_rows
        if row["bounded_advisory_contribution_points"] > 0
    ]
    negatives = [
        row
        for row in contribution_rows
        if row["bounded_advisory_contribution_points"] < 0
    ]
    high_positive = [
        row
        for row in contribution_rows
        if row["contribution_band"] == "strong_positive"
    ]
    red_review = [
        row for row in contribution_rows if row["requires_red_flag_review"] is True
    ]
    preview_ready = [
        row
        for row in contribution_rows
        if row["evidence_ready"] is True and row["scoring_inputs_ready"] is True
    ]
    existing_scores = [
        {
            "row_key": row["row_key"],
            "field": row["existing_score_field"],
            "value": deepcopy(row["existing_score_value"]),
        }
        for row in contribution_rows
        if row["existing_score_present"] is True
    ]
    missing_required_by_row = {
        row["row_key"]: deepcopy(row["missing_required_skills"])
        for row in contribution_rows
    }
    missing_tools_by_row = {
        row["row_key"]: deepcopy(row["missing_tools"]) for row in contribution_rows
    }
    red_flags_by_row = {
        row["row_key"]: deepcopy(row["red_flag_findings"])
        for row in contribution_rows
    }
    positive_total = sum(
        row["positive_evidence_contribution_points"] for row in contribution_rows
    )
    negative_total = sum(
        row["missing_required_skill_penalty_points"]
        + row["missing_tool_penalty_points"]
        + row["red_flag_penalty_points"]
        for row in contribution_rows
    )
    bounded_total = sum(
        row["bounded_advisory_contribution_points"] for row in contribution_rows
    )
    packet_rows = [
        {
            "row_key": row["row_key"],
            "item_id": row["item_id"],
            "job_id": row["job_id"],
            "bounded_advisory_contribution_points": row[
                "bounded_advisory_contribution_points"
            ],
            "contribution_band": row["contribution_band"],
            "requires_red_flag_review": row["requires_red_flag_review"],
            "final_score_produced": False,
        }
        for row in contribution_rows
    ]
    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_evidence_scoring_contribution_preview": True,
        "read_only": True,
        "advisory_only": True,
        "deterministic_contribution_preview": True,
        "requires_manual_user_control": True,
        "feature_rows_present": raw_count > 0,
        "feature_row_count": raw_count,
        "valid_feature_row_count": valid_count,
        "invalid_feature_row_count": invalid_count,
        "contribution_policy": deepcopy(policy),
        "contribution_rows": deepcopy(contribution_rows),
        "unmapped_rows": deepcopy(unmapped_rows),
        "contribution_packet": {
            "phase": PHASE,
            "packet_type": "jd_evidence_scoring_contribution_preview",
            "source": source,
            "contribution_row_count": valid_count,
            "contribution_rows": deepcopy(packet_rows),
            "final_score_included": False,
        },
        "contribution_summary": {
            "feature_row_count": raw_count,
            "valid_feature_row_count": valid_count,
            "invalid_feature_row_count": invalid_count,
            "preview_ready_count": len(preview_ready),
            "preview_blocked_count": valid_count - len(preview_ready),
            "positive_contribution_points_total": round(positive_total, 6),
            "negative_contribution_points_total": round(negative_total, 6),
            "bounded_contribution_points_total": round(bounded_total, 6),
            "high_positive_contribution_count": len(high_positive),
            "negative_contribution_count": len(negatives),
            "red_flag_review_count": len(red_review),
            "final_score_produced": False,
            "existing_score_changed": False,
        },
        "positive_contribution_points_total": round(positive_total, 6),
        "negative_contribution_points_total": round(negative_total, 6),
        "bounded_contribution_points_total": round(bounded_total, 6),
        "high_positive_contribution_count": len(high_positive),
        "negative_contribution_count": len(negatives),
        "red_flag_review_count": len(red_review),
        "missing_required_skills_by_row": missing_required_by_row,
        "missing_tools_by_row": missing_tools_by_row,
        "red_flag_findings_by_row": red_flags_by_row,
        "existing_score_fields_detected": deepcopy(existing_scores),
        "existing_scores_preserved": True,
        "preview_ready_count": len(preview_ready),
        "preview_blocked_count": valid_count - len(preview_ready),
        "preview_findings": {
            "source": source,
            "contribution_preview_only": True,
            "bounded_advisory_contributions": True,
            "existing_scores_preserved": True,
            "final_score_produced": False,
            "matching_scoring_module_called": False,
        },
        "missing_inputs": list(missing_inputs),
        "preview_key": "|".join(
            (
                f"phase={PHASE}",
                f"source={source}",
                f"rows={raw_count}",
                f"valid={valid_count}",
                f"invalid={invalid_count}",
                f"ready={len(preview_ready)}",
                f"red_review={len(red_review)}",
                f"bounded={round(bounded_total, 6)}",
            )
        ),
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def build_jd_evidence_scoring_contribution_preview_default_off(
    feature_packet: dict[str, Any] | None = None,
    scoring_feature_rows: list[Any] | None = None,
    contribution_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build deterministic advisory contribution previews from scoring features."""

    policy = _policy(contribution_policy)
    rows, source = _rows_from_inputs(feature_packet, scoring_feature_rows)
    if not rows:
        return _payload(
            source=source,
            raw_count=0,
            contribution_rows=[],
            unmapped_rows=[],
            policy=policy,
            missing_inputs=["scoring_feature_rows"],
        )

    contribution_rows: list[dict[str, Any]] = []
    unmapped_rows: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            unmapped_rows.append(
                {
                    "input_index": index,
                    "reason": "scoring feature row must be a dictionary",
                }
            )
            continue
        contribution_rows.append(_contribution_row(row, index=index, policy=policy))

    return _payload(
        source=source,
        raw_count=len(rows),
        contribution_rows=contribution_rows,
        unmapped_rows=unmapped_rows,
        policy=policy,
        missing_inputs=[],
    )
