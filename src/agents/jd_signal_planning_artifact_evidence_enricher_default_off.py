"""Default-off JD signal evidence enricher for planning-like artifacts."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents.jd_signal_resume_evidence_matrix_default_off import (
    build_jd_signal_resume_evidence_matrix_default_off,
)


PHASE = "35B"
JD_SIGNAL_FIELDS = ("jd_signals", "jd_intelligence", "jd_intelligence_result")
ROW_EVIDENCE_FIELDS = (
    "resume_evidence",
    "resume_text",
    "profile_evidence",
    "candidate_profile",
)
SHARED_EVIDENCE_FIELDS = (
    "resume_text",
    "summary",
    "skills",
    "projects",
    "experience",
    "tools",
    "domains",
    "certifications",
)
FALSE_ACTION_KEYS = (
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
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


def _present(value: Any) -> bool:
    return value not in (None, "", [], {})


def _row_key(row: dict[str, Any], index: int) -> str:
    for name in ("item_id", "job_id", "id"):
        value = row.get(name)
        if _present(value):
            return str(value)
    return str(index)


def _jd_signals(row: dict[str, Any]) -> Any:
    for name in JD_SIGNAL_FIELDS:
        value = row.get(name)
        if isinstance(value, dict):
            return deepcopy(value)
    return None


def _row_resume_evidence(row: dict[str, Any]) -> Any:
    for name in ROW_EVIDENCE_FIELDS:
        value = row.get(name)
        if _present(value):
            return deepcopy(value)
    return None


def _shared_dict_evidence(value: dict[str, Any]) -> bool:
    return any(field in value for field in SHARED_EVIDENCE_FIELDS)


def _top_level_resume_evidence(
    resume_evidence: Any,
    *,
    row: dict[str, Any],
    index: int,
) -> Any:
    if isinstance(resume_evidence, list):
        if index < len(resume_evidence):
            return deepcopy(resume_evidence[index])
        return None

    if isinstance(resume_evidence, dict):
        keys: list[str] = [_row_key(row, index), str(index)]
        for name in ("item_id", "job_id", "id"):
            value = row.get(name)
            if _present(value):
                keys.append(str(value))
        seen: set[str] = set()
        for key in keys:
            if key in seen:
                continue
            seen.add(key)
            if key in resume_evidence:
                return deepcopy(resume_evidence[key])
        if _shared_dict_evidence(resume_evidence):
            return deepcopy(resume_evidence)
        return None

    if _present(resume_evidence):
        return deepcopy(resume_evidence)
    return None


def _resume_evidence_for_row(
    row: dict[str, Any],
    *,
    index: int,
    resume_evidence: Any,
) -> Any:
    row_level = _row_resume_evidence(row)
    if _present(row_level):
        return row_level
    return _top_level_resume_evidence(resume_evidence, row=row, index=index)


def _ratio_average(values: list[float]) -> float:
    if not values:
        return 0.0
    return round(sum(values) / len(values), 6)


def _empty_payload(
    *,
    planning_row_count: int,
    valid_planning_row_count: int,
    invalid_planning_row_count: int,
    enriched_rows: list[dict[str, Any]],
    unmapped_rows: list[dict[str, Any]],
    evidence_results: list[dict[str, Any]],
    missing_inputs: list[str],
    resume_evidence_present: bool,
) -> dict[str, Any]:
    ready_results = [
        result for result in evidence_results if result.get("evidence_ready") is True
    ]
    blocked_results = [
        result for result in evidence_results if result.get("evidence_ready") is not True
    ]
    required_ratios = [
        float(result.get("required_skill_coverage_ratio", 0.0))
        for result in ready_results
    ]
    preferred_ratios = [
        float(result.get("preferred_skill_coverage_ratio", 0.0))
        for result in ready_results
    ]
    tool_ratios = [
        float(result.get("tool_coverage_ratio", 0.0)) for result in ready_results
    ]
    responsibility_ratios = [
        float(result.get("responsibility_coverage_ratio", 0.0))
        for result in ready_results
    ]
    missing_required = {
        str(result.get("row_key")): deepcopy(result.get("missing_required_skills", []))
        for result in evidence_results
    }
    missing_tools = {
        str(result.get("row_key")): deepcopy(result.get("missing_tools", []))
        for result in evidence_results
    }
    red_flags = {
        str(result.get("row_key")): deepcopy(result.get("red_flag_findings", []))
        for result in evidence_results
    }
    payload = {
        "phase": PHASE,
        "default_off": True,
        "jd_signal_planning_artifact_evidence_enricher": True,
        "read_only": True,
        "advisory_only": True,
        "deterministic_evidence_matching": True,
        "requires_manual_user_control": True,
        "planning_row_count": planning_row_count,
        "valid_planning_row_count": valid_planning_row_count,
        "invalid_planning_row_count": invalid_planning_row_count,
        "enriched_rows": deepcopy(enriched_rows),
        "unmapped_rows": deepcopy(unmapped_rows),
        "evidence_results": deepcopy(evidence_results),
        "evidence_ready_count": len(ready_results),
        "evidence_blocked_count": len(blocked_results),
        "resume_evidence_present": resume_evidence_present,
        "field_mapping_summary": {
            "jd_signal_fields": list(JD_SIGNAL_FIELDS),
            "row_resume_evidence_fields": list(ROW_EVIDENCE_FIELDS),
            "valid_rows_considered": valid_planning_row_count,
            "unmapped_rows": invalid_planning_row_count,
        },
        "coverage_summary": {
            "ready_row_count": len(ready_results),
            "blocked_row_count": len(blocked_results),
            "required_skill_ratio_values": required_ratios,
            "preferred_skill_ratio_values": preferred_ratios,
            "tool_ratio_values": tool_ratios,
            "responsibility_ratio_values": responsibility_ratios,
            "final_application_score_created": False,
            "existing_score_changed": False,
        },
        "average_required_skill_coverage_ratio": _ratio_average(required_ratios),
        "average_preferred_skill_coverage_ratio": _ratio_average(preferred_ratios),
        "average_tool_coverage_ratio": _ratio_average(tool_ratios),
        "average_responsibility_coverage_ratio": _ratio_average(responsibility_ratios),
        "missing_required_skills_by_row": missing_required,
        "missing_tools_by_row": missing_tools,
        "red_flag_findings_by_row": red_flags,
        "enricher_findings": {
            "phase35a_matrix_helper_called_per_valid_row": True,
            "copied_rows_only": True,
            "averages_use_evidence_ready_rows_only": True,
            "final_scoring_performed": False,
            "existing_score_changed": False,
        },
        "missing_inputs": list(missing_inputs),
        "enricher_key": "|".join(
            (
                f"phase={PHASE}",
                f"rows={planning_row_count}",
                f"valid={valid_planning_row_count}",
                f"invalid={invalid_planning_row_count}",
                f"ready={len(ready_results)}",
                f"blocked={len(blocked_results)}",
            )
        ),
    }
    for key in FALSE_ACTION_KEYS:
        payload[key] = False
    return payload


def build_jd_signal_planning_artifact_evidence_enricher_default_off(
    planning_rows: list[dict[str, Any]] | None = None,
    resume_evidence: Any = None,
    evidence_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Enrich copied planning-like rows with Phase 35A evidence matrices."""

    if not isinstance(planning_rows, list):
        return _empty_payload(
            planning_row_count=0,
            valid_planning_row_count=0,
            invalid_planning_row_count=0,
            enriched_rows=[],
            unmapped_rows=[
                {
                    "input_index": None,
                    "reason": "planning_rows must be supplied as a list",
                }
            ],
            evidence_results=[],
            missing_inputs=["planning_rows"],
            resume_evidence_present=_present(resume_evidence),
        )

    enriched_rows: list[dict[str, Any]] = []
    unmapped_rows: list[dict[str, Any]] = []
    evidence_results: list[dict[str, Any]] = []
    resolved_evidence_present = False

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
        signals = _jd_signals(copied)
        evidence = _resume_evidence_for_row(
            copied,
            index=index,
            resume_evidence=resume_evidence,
        )
        if _present(evidence):
            resolved_evidence_present = True
        matrix_result = build_jd_signal_resume_evidence_matrix_default_off(
            jd_signals=signals,
            resume_evidence=evidence,
            evidence_policy=evidence_policy,
        )
        result = {
            "input_index": index,
            "row_key": row_key,
            "evidence_ready": matrix_result.get("evidence_ready") is True,
            "missing_inputs": deepcopy(matrix_result.get("missing_inputs", [])),
            "blocked_reasons": deepcopy(matrix_result.get("blocked_reasons", [])),
            "required_skill_coverage_ratio": matrix_result.get(
                "required_skill_coverage_ratio", 0.0
            ),
            "preferred_skill_coverage_ratio": matrix_result.get(
                "preferred_skill_coverage_ratio", 0.0
            ),
            "tool_coverage_ratio": matrix_result.get("tool_coverage_ratio", 0.0),
            "responsibility_coverage_ratio": matrix_result.get(
                "responsibility_coverage_ratio", 0.0
            ),
            "missing_required_skills": deepcopy(
                matrix_result.get("missing_required_skills", [])
            ),
            "missing_tools": deepcopy(matrix_result.get("missing_tools", [])),
            "red_flag_findings": deepcopy(matrix_result.get("red_flag_findings", [])),
            "evidence_matrix_key": matrix_result.get("evidence_matrix_key", ""),
            "evidence_matrix_result": deepcopy(matrix_result),
        }
        evidence_results.append(result)

        if matrix_result.get("evidence_ready") is True:
            copied["evidence_matrix_result"] = deepcopy(matrix_result)
            copied["evidence_matrix"] = deepcopy(matrix_result.get("evidence_matrix", {}))
            copied["evidence_coverage_summary"] = deepcopy(
                matrix_result.get("coverage_summary", {})
            )
        enriched_rows.append(copied)

    return _empty_payload(
        planning_row_count=len(planning_rows),
        valid_planning_row_count=len(enriched_rows),
        invalid_planning_row_count=len(unmapped_rows),
        enriched_rows=enriched_rows,
        unmapped_rows=unmapped_rows,
        evidence_results=evidence_results,
        missing_inputs=[],
        resume_evidence_present=resolved_evidence_present,
    )
