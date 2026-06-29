"""Default-off planning artifact annotator for JD evidence score impacts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PHASE = "39A"
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
SCORE_FIELDS = (
    "existing_score_value",
    "final_score",
    "score",
    "fit_score",
    "application_score",
)


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _number(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
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
        "positive_delta_threshold": _number(
            supplied.get("positive_delta_threshold", 1),
            1,
        ),
        "negative_delta_threshold": _number(
            supplied.get("negative_delta_threshold", -1),
            -1,
        ),
        "include_full_impact_row": _bool(
            supplied.get("include_full_impact_row", True)
        ),
        "annotate_unmatched_rows": _bool(
            supplied.get("annotate_unmatched_rows", True)
        ),
    }


def _row_key(row: dict[str, Any], index: int) -> str:
    for name in ("item_id", "job_id", "id"):
        value = row.get(name)
        if _present(value):
            return str(value)
    return str(index)


def _candidate_keys(row: dict[str, Any], index: int) -> list[str]:
    keys: list[str] = []
    for name in ("item_id", "job_id", "id"):
        value = row.get(name)
        if _present(value):
            keys.append(str(value))
    keys.append(str(index))
    seen: set[str] = set()
    unique: list[str] = []
    for key in keys:
        if key in seen:
            continue
        seen.add(key)
        unique.append(key)
    return unique


def _impact_rows_from_result(impact_result: dict[str, Any] | None) -> list[Any]:
    if not isinstance(impact_result, dict):
        return []
    if isinstance(impact_result.get("impact_rows"), list):
        return list(impact_result["impact_rows"])
    packet = impact_result.get("impact_packet")
    if isinstance(packet, dict) and isinstance(packet.get("impact_rows"), list):
        return list(packet["impact_rows"])
    nested = impact_result.get("impact_result")
    if isinstance(nested, dict):
        if isinstance(nested.get("impact_rows"), list):
            return list(nested["impact_rows"])
        nested_packet = nested.get("impact_packet")
        if isinstance(nested_packet, dict) and isinstance(
            nested_packet.get("impact_rows"),
            list,
        ):
            return list(nested_packet["impact_rows"])
    return []


def _impact_rows_from_inputs(
    impact_result: dict[str, Any] | None,
    impact_rows: list[Any] | None,
) -> tuple[list[Any], str]:
    if isinstance(impact_rows, list):
        return list(impact_rows), "impact_rows"
    rows = _impact_rows_from_result(impact_result)
    if rows:
        return rows, "impact_result"
    return [], "missing"


def _impact_index(rows: list[Any]) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]]]:
    indexed: dict[str, dict[str, Any]] = {}
    invalid: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            invalid.append(
                {
                    "input_index": index,
                    "reason": "impact row must be a dictionary",
                }
            )
            continue
        copied = deepcopy(row)
        for key in _candidate_keys(copied, index):
            if key not in indexed:
                indexed[key] = copied
    return indexed, invalid


def _existing_score(row: dict[str, Any], row_key: str) -> dict[str, Any] | None:
    if _bool(row.get("existing_score_present")) is True:
        field = str(row.get("existing_score_field") or "existing_score_value")
        return {
            "row_key": row_key,
            "field": field,
            "value": deepcopy(row.get("existing_score_value")),
        }
    for field in SCORE_FIELDS:
        if field in row and _present(row.get(field)):
            return {
                "row_key": row_key,
                "field": field,
                "value": deepcopy(row.get(field)),
            }
    return None


def _recommendation(
    impact_row: dict[str, Any] | None,
    *,
    policy: dict[str, Any],
) -> str:
    if impact_row is None:
        return "unmatched"
    if _bool(impact_row.get("requires_red_flag_review")) is True:
        return "manual_review"
    if _bool(impact_row.get("score_preview_available")) is not True:
        return "manual_review"
    delta = _number(impact_row.get("score_preview_delta"), 0.0)
    if delta >= policy["positive_delta_threshold"]:
        return "positive_review"
    if delta <= policy["negative_delta_threshold"]:
        return "negative_review"
    return "neutral_review"


def _review_summary(
    *,
    row_key: str,
    impact_row: dict[str, Any] | None,
    recommendation: str,
) -> dict[str, Any]:
    if impact_row is None:
        return {
            "row_key": row_key,
            "matched": False,
            "reason": "no matching score impact preview row",
            "recommendation": recommendation,
            "final_score_produced": False,
            "existing_score_changed": False,
        }
    return {
        "row_key": row_key,
        "matched": True,
        "score_preview_available": _bool(impact_row.get("score_preview_available")),
        "score_preview_blocked_reason": str(
            impact_row.get("score_preview_blocked_reason", "") or ""
        ),
        "impact_band": str(impact_row.get("impact_band", "") or ""),
        "requires_red_flag_review": _bool(impact_row.get("requires_red_flag_review")),
        "recommendation": recommendation,
        "final_score_produced": False,
        "existing_score_changed": False,
    }


def _preview(
    impact_row: dict[str, Any] | None,
    *,
    include_full_impact_row: bool,
) -> dict[str, Any]:
    if impact_row is None:
        return {
            "matched": False,
            "score_preview_available": False,
            "score_preview_blocked_reason": "unmatched",
            "final_score_produced": False,
            "existing_score_changed": False,
        }
    preview = {
        "matched": True,
        "base_score_for_preview": deepcopy(impact_row.get("base_score_for_preview")),
        "bounded_advisory_contribution_points": deepcopy(
            impact_row.get("bounded_advisory_contribution_points")
        ),
        "hypothetical_score_preview": deepcopy(
            impact_row.get("hypothetical_score_preview")
        ),
        "score_preview_delta": deepcopy(impact_row.get("score_preview_delta")),
        "score_preview_available": _bool(impact_row.get("score_preview_available")),
        "score_preview_blocked_reason": str(
            impact_row.get("score_preview_blocked_reason", "") or ""
        ),
        "impact_band": str(impact_row.get("impact_band", "") or ""),
        "requires_red_flag_review": _bool(impact_row.get("requires_red_flag_review")),
        "hypothetical_score_preview_produced": _bool(
            impact_row.get("hypothetical_score_preview_produced")
        ),
        "final_score_produced": False,
        "existing_score_changed": False,
    }
    if include_full_impact_row:
        preview["impact_row"] = deepcopy(impact_row)
    return preview


def _annotated_row(
    row: dict[str, Any],
    *,
    row_key: str,
    impact_row: dict[str, Any] | None,
    source: str,
    policy: dict[str, Any],
) -> dict[str, Any]:
    recommendation = _recommendation(impact_row, policy=policy)
    copied = deepcopy(row)
    copied["score_impact_preview_result"] = (
        deepcopy(impact_row)
        if impact_row is not None
        else {
            "matched": False,
            "reason": "no matching score impact preview row",
        }
    )
    copied["score_impact_preview"] = _preview(
        impact_row,
        include_full_impact_row=policy["include_full_impact_row"],
    )
    copied["score_impact_review_summary"] = _review_summary(
        row_key=row_key,
        impact_row=impact_row,
        recommendation=recommendation,
    )
    copied["score_impact_review_recommendation"] = recommendation
    copied["score_impact_annotation_ready"] = impact_row is not None
    copied["score_impact_annotation_source"] = source if impact_row is not None else "unmatched"
    copied["final_score_produced"] = False
    copied["existing_score_changed"] = False
    return copied


def _payload(
    *,
    planning_row_count: int,
    valid_planning_row_count: int,
    invalid_planning_row_count: int,
    impact_row_count: int,
    policy: dict[str, Any],
    annotated_rows: list[dict[str, Any]],
    unannotated_rows: list[dict[str, Any]],
    unmapped_rows: list[dict[str, Any]],
    impact_rows_by_key: dict[str, dict[str, Any]],
    invalid_impact_rows: list[dict[str, Any]],
    missing_inputs: list[str],
) -> dict[str, Any]:
    matched_rows = [
        row
        for row in annotated_rows
        if row.get("score_impact_review_recommendation") != "unmatched"
    ]
    blocked_rows = [
        row
        for row in matched_rows
        if row.get("score_impact_preview", {}).get("score_preview_available") is not True
    ]
    positive_rows = [
        row
        for row in annotated_rows
        if row.get("score_impact_review_recommendation") == "positive_review"
    ]
    negative_rows = [
        row
        for row in annotated_rows
        if row.get("score_impact_review_recommendation") == "negative_review"
    ]
    neutral_rows = [
        row
        for row in annotated_rows
        if row.get("score_impact_review_recommendation") == "neutral_review"
    ]
    red_review_rows = [
        row
        for row in annotated_rows
        if row.get("score_impact_preview", {}).get("requires_red_flag_review") is True
    ]
    existing_scores: list[dict[str, Any]] = []
    for index, row in enumerate(annotated_rows + unannotated_rows):
        score = _existing_score(row, _row_key(row, index))
        if score is not None:
            existing_scores.append(score)

    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_evidence_score_impact_planning_artifact_annotator": True,
        "read_only": True,
        "advisory_only": True,
        "preview_only": True,
        "deterministic_score_impact_annotation": True,
        "requires_manual_user_control": True,
        "planning_row_count": planning_row_count,
        "valid_planning_row_count": valid_planning_row_count,
        "invalid_planning_row_count": invalid_planning_row_count,
        "impact_rows_present": impact_row_count > 0,
        "impact_row_count": impact_row_count,
        "annotation_policy": deepcopy(policy),
        "annotated_rows": deepcopy(annotated_rows),
        "unannotated_rows": deepcopy(unannotated_rows),
        "unmapped_rows": deepcopy(unmapped_rows),
        "impact_rows_by_key": deepcopy(impact_rows_by_key),
        "annotation_summary": {
            "planning_row_count": planning_row_count,
            "valid_planning_row_count": valid_planning_row_count,
            "invalid_planning_row_count": invalid_planning_row_count,
            "annotated_row_count": len(annotated_rows),
            "unannotated_row_count": len(unannotated_rows),
            "matched_impact_row_count": len(matched_rows),
            "unmatched_annotation_count": len(annotated_rows) - len(matched_rows),
            "invalid_impact_row_count": len(invalid_impact_rows),
            "final_score_produced": False,
            "existing_score_changed": False,
        },
        "score_preview_available_count": len(matched_rows) - len(blocked_rows),
        "score_preview_blocked_count": len(blocked_rows),
        "positive_impact_count": len(positive_rows),
        "negative_impact_count": len(negative_rows),
        "neutral_impact_count": len(neutral_rows),
        "red_flag_review_count": len(red_review_rows),
        "existing_score_fields_detected": deepcopy(existing_scores),
        "existing_scores_preserved": True,
        "annotation_findings": {
            "copied_planning_rows_only": True,
            "invalid_impact_rows": deepcopy(invalid_impact_rows),
            "score_impact_preview_performed": False,
            "final_scoring_performed": False,
            "existing_score_changed": False,
        },
        "missing_inputs": list(missing_inputs),
        "annotator_key": "|".join(
            (
                f"phase={PHASE}",
                f"rows={planning_row_count}",
                f"valid={valid_planning_row_count}",
                f"invalid={invalid_planning_row_count}",
                f"impact={impact_row_count}",
                f"annotated={len(annotated_rows)}",
                f"unannotated={len(unannotated_rows)}",
                f"available={len(matched_rows) - len(blocked_rows)}",
                f"blocked={len(blocked_rows)}",
            )
        ),
        "hypothetical_score_preview_produced": True,
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def build_jd_evidence_score_impact_planning_artifact_annotator_default_off(
    planning_rows: list[Any] | None = None,
    impact_result: dict[str, Any] | None = None,
    impact_rows: list[Any] | None = None,
    annotation_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Annotate copied planning-like rows with score impact preview metadata."""

    policy = _policy(annotation_policy)
    rows, impact_source = _impact_rows_from_inputs(impact_result, impact_rows)
    impact_rows_by_key, invalid_impact_rows = _impact_index(rows)
    impact_count = len([row for row in rows if isinstance(row, dict)])

    if not isinstance(planning_rows, list):
        return _payload(
            planning_row_count=0,
            valid_planning_row_count=0,
            invalid_planning_row_count=0,
            impact_row_count=impact_count,
            policy=policy,
            annotated_rows=[],
            unannotated_rows=[],
            unmapped_rows=[
                {
                    "input_index": None,
                    "reason": "planning_rows must be supplied as a list",
                }
            ],
            impact_rows_by_key=impact_rows_by_key,
            invalid_impact_rows=invalid_impact_rows,
            missing_inputs=["planning_rows"],
        )

    annotated_rows: list[dict[str, Any]] = []
    unannotated_rows: list[dict[str, Any]] = []
    unmapped_rows: list[dict[str, Any]] = []
    missing_inputs: list[str] = []
    if impact_count == 0:
        missing_inputs.append("impact_rows")

    for index, row in enumerate(planning_rows):
        if not isinstance(row, dict):
            unmapped_rows.append(
                {
                    "input_index": index,
                    "reason": "planning row must be a dictionary",
                }
            )
            continue

        copied = deepcopy(row)
        row_key = _row_key(copied, index)
        match = None
        for key in _candidate_keys(copied, index):
            if key in impact_rows_by_key:
                match = impact_rows_by_key[key]
                break
        if match is None and impact_count == 0:
            unannotated = deepcopy(copied)
            unannotated["score_impact_annotation_ready"] = False
            unannotated["score_impact_annotation_source"] = "missing_impact_rows"
            unannotated["score_impact_review_recommendation"] = "unmatched"
            unannotated["final_score_produced"] = False
            unannotated["existing_score_changed"] = False
            unannotated_rows.append(unannotated)
            continue
        if match is None and policy["annotate_unmatched_rows"] is not True:
            unannotated = deepcopy(copied)
            unannotated["score_impact_annotation_ready"] = False
            unannotated["score_impact_annotation_source"] = "unmatched"
            unannotated["score_impact_review_recommendation"] = "unmatched"
            unannotated["final_score_produced"] = False
            unannotated["existing_score_changed"] = False
            unannotated_rows.append(unannotated)
            continue
        annotated_rows.append(
            _annotated_row(
                copied,
                row_key=row_key,
                impact_row=match,
                source=impact_source,
                policy=policy,
            )
        )

    return _payload(
        planning_row_count=len(planning_rows),
        valid_planning_row_count=len(planning_rows) - len(unmapped_rows),
        invalid_planning_row_count=len(unmapped_rows),
        impact_row_count=impact_count,
        policy=policy,
        annotated_rows=annotated_rows,
        unannotated_rows=unannotated_rows,
        unmapped_rows=unmapped_rows,
        impact_rows_by_key=impact_rows_by_key,
        invalid_impact_rows=invalid_impact_rows,
        missing_inputs=missing_inputs,
    )
