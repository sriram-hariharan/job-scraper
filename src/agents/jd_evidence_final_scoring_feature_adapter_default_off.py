"""Default-off adapter from JD evidence results to scoring feature packets."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


PHASE = "36A"
SCORE_FIELDS = ("final_score", "score", "fit_score", "application_score")
EVIDENCE_ROW_FIELDS = (
    "evidence_matrix_result",
    "evidence_matrix",
    "evidence_coverage_summary",
    "coverage_summary",
)
FALSE_ACTION_KEYS = (
    "final_score_produced",
    "existing_score_changed",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
    "evidence_matching_performed",
    "final_scoring_performed",
    "matching_scoring_module_called",
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


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


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


def _policy(value: dict[str, Any] | None) -> dict[str, Any]:
    supplied = value if isinstance(value, dict) else {}
    return {
        "high_required_skill_coverage_threshold": _number(
            supplied.get("high_required_skill_coverage_threshold", 0.8),
            0.8,
        ),
        "low_required_skill_coverage_threshold": _number(
            supplied.get("low_required_skill_coverage_threshold", 0.5),
            0.5,
        ),
        "high_tool_coverage_threshold": _number(
            supplied.get("high_tool_coverage_threshold", 0.8),
            0.8,
        ),
        "red_flag_review_threshold": max(
            0,
            _int(supplied.get("red_flag_review_threshold", 1), 1),
        ),
    }


def _row_key(row: dict[str, Any], index: int) -> str:
    for name in ("item_id", "job_id", "id"):
        value = row.get(name)
        if _present(value):
            return str(value)
    return str(index)


def _score_snapshot(row: dict[str, Any]) -> dict[str, Any]:
    for field in SCORE_FIELDS:
        if field in row and _present(row.get(field)):
            return {
                "existing_score_present": True,
                "existing_score_field": field,
                "existing_score_value": deepcopy(row.get(field)),
            }
    return {
        "existing_score_present": False,
        "existing_score_field": "",
        "existing_score_value": None,
    }


def _row_evidence(row: dict[str, Any]) -> dict[str, Any] | None:
    if isinstance(row.get("evidence_matrix_result"), dict):
        return deepcopy(row["evidence_matrix_result"])
    if isinstance(row.get("evidence_matrix"), dict) or isinstance(
        row.get("evidence_coverage_summary"), dict
    ):
        evidence: dict[str, Any] = {
            "evidence_ready": bool(row.get("evidence_matrix")),
            "evidence_matrix": deepcopy(row.get("evidence_matrix", {})),
            "coverage_summary": deepcopy(row.get("evidence_coverage_summary", {})),
        }
        if isinstance(row.get("coverage_summary"), dict):
            evidence["coverage_summary"] = deepcopy(row["coverage_summary"])
        return evidence
    if isinstance(row.get("coverage_summary"), dict):
        return {
            "evidence_ready": True,
            "coverage_summary": deepcopy(row["coverage_summary"]),
        }
    return None


def _external_evidence(
    evidence_results: Any,
    *,
    row: dict[str, Any],
    index: int,
) -> dict[str, Any] | None:
    if isinstance(evidence_results, list):
        if index < len(evidence_results) and isinstance(evidence_results[index], dict):
            return deepcopy(evidence_results[index])
        return None
    if isinstance(evidence_results, dict):
        keys = [_row_key(row, index), str(index)]
        for name in ("item_id", "job_id", "id"):
            value = row.get(name)
            if _present(value):
                keys.append(str(value))
        seen: set[str] = set()
        for key in keys:
            if key in seen:
                continue
            seen.add(key)
            if isinstance(evidence_results.get(key), dict):
                return deepcopy(evidence_results[key])
    return None


def _resolved_evidence(
    row: dict[str, Any],
    *,
    index: int,
    evidence_results: Any,
) -> dict[str, Any] | None:
    row_level = _row_evidence(row)
    if isinstance(row_level, dict):
        return row_level
    return _external_evidence(evidence_results, row=row, index=index)


def _list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _matrix_missing(evidence: dict[str, Any], field: str) -> list[Any]:
    matrix = evidence.get("evidence_matrix")
    if not isinstance(matrix, dict):
        return []
    rows = matrix.get(field)
    if not isinstance(rows, list):
        return []
    return [
        row.get("signal")
        for row in rows
        if isinstance(row, dict)
        and row.get("status") == "missing"
        and _present(row.get("signal"))
    ]


def _red_flags(evidence: dict[str, Any]) -> list[Any]:
    if isinstance(evidence.get("red_flag_findings"), list):
        return deepcopy(evidence["red_flag_findings"])
    matrix = evidence.get("evidence_matrix")
    if isinstance(matrix, dict) and isinstance(matrix.get("red_flags"), list):
        return deepcopy(matrix["red_flags"])
    return []


def _coverage_ratio(evidence: dict[str, Any], key: str) -> float:
    if key in evidence:
        return _number(evidence.get(key), 0.0)
    return 0.0


def _coverage_band(required_ratio: float, *, policy: dict[str, Any], ready: bool) -> str:
    if not ready:
        return "unknown"
    if required_ratio >= policy["high_required_skill_coverage_threshold"]:
        return "high"
    if required_ratio < policy["low_required_skill_coverage_threshold"]:
        return "low"
    return "medium"


def _feature_row(
    row: dict[str, Any],
    *,
    index: int,
    evidence: dict[str, Any] | None,
    policy: dict[str, Any],
) -> dict[str, Any]:
    row_key = _row_key(row, index)
    score = _score_snapshot(row)
    ready = isinstance(evidence, dict) and evidence.get("evidence_ready") is True
    evidence_payload = evidence if isinstance(evidence, dict) else {}
    missing_required = _list(evidence_payload.get("missing_required_skills"))
    if not missing_required:
        missing_required = _matrix_missing(evidence_payload, "required_skills")
    missing_tools = _list(evidence_payload.get("missing_tools"))
    if not missing_tools:
        missing_tools = _matrix_missing(evidence_payload, "tools")
    red_flags = _red_flags(evidence_payload)
    required_ratio = _coverage_ratio(
        evidence_payload,
        "required_skill_coverage_ratio",
    )
    preferred_ratio = _coverage_ratio(
        evidence_payload,
        "preferred_skill_coverage_ratio",
    )
    tool_ratio = _coverage_ratio(evidence_payload, "tool_coverage_ratio")
    responsibility_ratio = _coverage_ratio(
        evidence_payload,
        "responsibility_coverage_ratio",
    )
    red_flag_count = len(red_flags)
    band = _coverage_band(required_ratio, policy=policy, ready=ready)
    return {
        "item_id": str(row.get("item_id", "") or ""),
        "job_id": str(row.get("job_id", "") or row.get("id", "") or row_key),
        "title": str(row.get("title", "") or ""),
        "company": str(row.get("company", "") or ""),
        "existing_score_present": score["existing_score_present"],
        "existing_score_field": score["existing_score_field"],
        "existing_score_value": deepcopy(score["existing_score_value"]),
        "evidence_ready": ready,
        "required_skill_coverage_ratio": required_ratio,
        "preferred_skill_coverage_ratio": preferred_ratio,
        "tool_coverage_ratio": tool_ratio,
        "responsibility_coverage_ratio": responsibility_ratio,
        "missing_required_skill_count": len(missing_required),
        "missing_tool_count": len(missing_tools),
        "red_flag_count": red_flag_count,
        "coverage_band": band,
        "requires_red_flag_review": red_flag_count
        >= policy["red_flag_review_threshold"],
        "scoring_inputs_ready": ready and band != "unknown",
        "row_key": row_key,
        "missing_required_skills": deepcopy(missing_required),
        "missing_tools": deepcopy(missing_tools),
        "red_flag_findings": deepcopy(red_flags),
    }


def _payload(
    *,
    planning_row_count: int,
    valid_planning_row_count: int,
    invalid_planning_row_count: int,
    feature_rows: list[dict[str, Any]],
    unmapped_rows: list[dict[str, Any]],
    policy: dict[str, Any],
    missing_inputs: list[str],
) -> dict[str, Any]:
    ready = [row for row in feature_rows if row["evidence_ready"] is True]
    missing = [row for row in feature_rows if row["evidence_ready"] is not True]
    high = [row for row in feature_rows if row["coverage_band"] == "high"]
    low = [row for row in feature_rows if row["coverage_band"] == "low"]
    red_review = [
        row for row in feature_rows if row["requires_red_flag_review"] is True
    ]
    existing_scores = [
        {
            "row_key": row["row_key"],
            "field": row["existing_score_field"],
            "value": deepcopy(row["existing_score_value"]),
        }
        for row in feature_rows
        if row["existing_score_present"] is True
    ]
    missing_required_by_row = {
        row["row_key"]: deepcopy(row["missing_required_skills"])
        for row in feature_rows
    }
    missing_tools_by_row = {
        row["row_key"]: deepcopy(row["missing_tools"]) for row in feature_rows
    }
    red_flags_by_row = {
        row["row_key"]: deepcopy(row["red_flag_findings"]) for row in feature_rows
    }
    packet_rows = [
        {
            "row_key": row["row_key"],
            "item_id": row["item_id"],
            "job_id": row["job_id"],
            "evidence_ready": row["evidence_ready"],
            "required_skill_coverage_ratio": row[
                "required_skill_coverage_ratio"
            ],
            "preferred_skill_coverage_ratio": row[
                "preferred_skill_coverage_ratio"
            ],
            "tool_coverage_ratio": row["tool_coverage_ratio"],
            "responsibility_coverage_ratio": row[
                "responsibility_coverage_ratio"
            ],
            "missing_required_skill_count": row[
                "missing_required_skill_count"
            ],
            "missing_tool_count": row["missing_tool_count"],
            "red_flag_count": row["red_flag_count"],
            "coverage_band": row["coverage_band"],
            "requires_red_flag_review": row["requires_red_flag_review"],
            "scoring_inputs_ready": row["scoring_inputs_ready"],
        }
        for row in feature_rows
    ]
    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_evidence_final_scoring_feature_adapter": True,
        "read_only": True,
        "advisory_only": True,
        "deterministic_scoring_feature_preparation": True,
        "requires_manual_user_control": True,
        "planning_row_count": planning_row_count,
        "valid_planning_row_count": valid_planning_row_count,
        "invalid_planning_row_count": invalid_planning_row_count,
        "feature_rows": deepcopy(feature_rows),
        "unmapped_rows": deepcopy(unmapped_rows),
        "feature_policy": deepcopy(policy),
        "feature_packet": {
            "phase": PHASE,
            "packet_type": "jd_evidence_final_scoring_features",
            "feature_row_count": len(feature_rows),
            "scoring_feature_rows": deepcopy(packet_rows),
            "final_score_included": False,
        },
        "scoring_feature_rows": deepcopy(packet_rows),
        "scoring_feature_summary": {
            "feature_row_count": len(feature_rows),
            "evidence_ready_count": len(ready),
            "evidence_missing_count": len(missing),
            "high_coverage_count": len(high),
            "low_coverage_count": len(low),
            "red_flag_review_count": len(red_review),
            "final_score_produced": False,
            "existing_score_changed": False,
        },
        "existing_score_fields_detected": deepcopy(existing_scores),
        "existing_scores_preserved": True,
        "evidence_ready_count": len(ready),
        "evidence_missing_count": len(missing),
        "high_coverage_count": len(high),
        "low_coverage_count": len(low),
        "red_flag_review_count": len(red_review),
        "missing_required_skills_by_row": missing_required_by_row,
        "missing_tools_by_row": missing_tools_by_row,
        "red_flag_findings_by_row": red_flags_by_row,
        "adapter_findings": {
            "feature_preparation_only": True,
            "existing_scores_preserved": True,
            "final_score_produced": False,
            "matching_scoring_module_called": False,
        },
        "missing_inputs": list(missing_inputs),
        "adapter_key": "|".join(
            (
                f"phase={PHASE}",
                f"rows={planning_row_count}",
                f"valid={valid_planning_row_count}",
                f"invalid={invalid_planning_row_count}",
                f"ready={len(ready)}",
                f"missing={len(missing)}",
                f"high={len(high)}",
                f"low={len(low)}",
                f"red_review={len(red_review)}",
            )
        ),
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def build_jd_evidence_final_scoring_feature_adapter_default_off(
    planning_rows: list[dict[str, Any]] | None = None,
    evidence_results: Any = None,
    feature_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convert supplied JD evidence results into final-scoring-ready features."""

    policy = _policy(feature_policy)
    if not isinstance(planning_rows, list):
        return _payload(
            planning_row_count=0,
            valid_planning_row_count=0,
            invalid_planning_row_count=0,
            feature_rows=[],
            unmapped_rows=[
                {
                    "input_index": None,
                    "reason": "planning_rows must be supplied as a list",
                }
            ],
            policy=policy,
            missing_inputs=["planning_rows"],
        )

    feature_rows: list[dict[str, Any]] = []
    unmapped_rows: list[dict[str, Any]] = []
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
        evidence = _resolved_evidence(
            copied,
            index=index,
            evidence_results=evidence_results,
        )
        feature_rows.append(
            _feature_row(
                copied,
                index=index,
                evidence=evidence,
                policy=policy,
            )
        )

    return _payload(
        planning_row_count=len(planning_rows),
        valid_planning_row_count=len(feature_rows),
        invalid_planning_row_count=len(unmapped_rows),
        feature_rows=feature_rows,
        unmapped_rows=unmapped_rows,
        policy=policy,
        missing_inputs=[],
    )
