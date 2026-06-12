"""Pure deduplication agent trace wrapper.

This module describes caller-supplied deduplication summaries as deterministic
agent trace output. It does not call live deduplication, seen-jobs storage,
filtering, ranking, scoring, LLM evaluation, execution, submission, API, UI,
scheduler, reporting, export, or emitter behavior.
"""
# Contract note:
# This wrapper represents deduplication only.
# It does not perform prefilter relevance, LLM evaluation, or final application scoring.

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents.agent_state import JobApplicationContext, build_agent_step_snapshot


AGENT_NAME = "deduplication_agent"
DEFAULT_AGENT_VERSION = "deduplication-wrapper-v1"

SAFETY_FLAGS: dict[str, bool] = {
    "did_call_live_deduplication": False,
    "did_call_prefilter_relevance": False,
    "did_call_llm_evaluation": False,
    "did_call_final_application_scoring": False,
    "did_create_connection": False,
    "did_commit_transaction": False,
    "did_run_migration": False,
    "did_schedule_background_work": False,
    "did_execute_scheduler": False,
    "did_execute_reporting_job": False,
    "did_export_files": False,
    "did_execute_application": False,
    "did_submit_application": False,
    "api_route_added": False,
    "ui_action_added": False,
    "pipeline_wiring_added": False,
}


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_int(value: Any, *, default: int = -1) -> int:
    if value is None:
        return default
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return -1
    return parsed


def _optional_count(summary: dict[str, Any], key: str) -> int | None:
    if key not in summary:
        return None
    return _safe_int(summary.get(key))


def _sorted_reason_counts(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, int] = {}
    for key, count in value.items():
        reason = _clean_text(key)
        if not reason:
            continue
        normalized[reason] = _safe_int(count)
    return {key: normalized[key] for key in sorted(normalized)}


def _validation(
    *,
    input_count: int,
    unique_count: int,
    seen_count: int,
    new_count: int,
    same_run_duplicate_count: int,
    filtered_count: int | None,
    cross_run_duplicate_count: int | None,
) -> dict[str, Any]:
    errors: list[str] = []
    required_counts = {
        "input_count": input_count,
        "unique_count": unique_count,
        "seen_count": seen_count,
        "new_count": new_count,
        "same_run_duplicate_count": same_run_duplicate_count,
    }
    for key, value in required_counts.items():
        if value < 0:
            errors.append(f"{key}_invalid")
    if filtered_count is not None and filtered_count < 0:
        errors.append("filtered_count_invalid")
    if cross_run_duplicate_count is not None and cross_run_duplicate_count < 0:
        errors.append("cross_run_duplicate_count_invalid")

    if not errors:
        if seen_count + new_count != unique_count:
            errors.append("seen_new_unique_count_mismatch")
        if unique_count + same_run_duplicate_count != input_count:
            errors.append("unique_duplicate_input_count_mismatch")
        if filtered_count is not None and filtered_count > input_count:
            errors.append("filtered_count_exceeds_input_count")
        if cross_run_duplicate_count is not None and cross_run_duplicate_count > seen_count:
            errors.append("cross_run_duplicate_count_exceeds_seen_count")

    return {
        "is_valid": not errors,
        "errors": errors,
        "preserves_deduplication": True,
        "did_call_live_deduplication": False,
        "did_call_prefilter_relevance": False,
        "did_call_llm_evaluation": False,
        "did_call_final_application_scoring": False,
    }


def describe_deduplication_result(
    deduplication_summary: dict[str, Any],
    *,
    agent_version: str = DEFAULT_AGENT_VERSION,
) -> dict[str, Any]:
    """Describe caller-supplied deduplication output without deduplicating."""

    summary = _plain_dict(deduplication_summary)
    input_count = _safe_int(summary.get("input_count"))
    unique_count = _safe_int(summary.get("unique_count"))
    seen_count = _safe_int(summary.get("seen_count"))
    new_count = _safe_int(summary.get("new_count"))
    same_run_duplicate_count = _safe_int(summary.get("same_run_duplicate_count"))
    filtered_count = _optional_count(summary, "filtered_count")
    cross_run_duplicate_count = _optional_count(summary, "cross_run_duplicate_count")
    reason_counts = _sorted_reason_counts(summary.get("reason_counts"))
    validation_json = _validation(
        input_count=input_count,
        unique_count=unique_count,
        seen_count=seen_count,
        new_count=new_count,
        same_run_duplicate_count=same_run_duplicate_count,
        filtered_count=filtered_count,
        cross_run_duplicate_count=cross_run_duplicate_count,
    )
    status = "completed" if validation_json["is_valid"] else "invalid"

    output_json: dict[str, Any] = {
        "agent_name": AGENT_NAME,
        "agent_version": _clean_text(agent_version) or DEFAULT_AGENT_VERSION,
        "status": status,
        "input_count": input_count,
        "unique_count": unique_count,
        "seen_count": seen_count,
        "new_count": new_count,
        "same_run_duplicate_count": same_run_duplicate_count,
        "reason_counts": reason_counts,
        "validation_json": validation_json,
        "separation": {
            "deduplication": "described_only",
            "prefilter_relevance": "not_called",
            "llm_evaluation": "not_called",
            "final_application_scoring": "not_called",
        },
    }
    if filtered_count is not None:
        output_json["filtered_count"] = filtered_count
    if cross_run_duplicate_count is not None:
        output_json["cross_run_duplicate_count"] = cross_run_duplicate_count

    return {
        "agent_name": AGENT_NAME,
        "agent_version": output_json["agent_version"],
        "status": status,
        "input_count": input_count,
        "filtered_count": filtered_count,
        "unique_count": unique_count,
        "seen_count": seen_count,
        "new_count": new_count,
        "same_run_duplicate_count": same_run_duplicate_count,
        "cross_run_duplicate_count": cross_run_duplicate_count,
        "reason_counts": reason_counts,
        "validation_json": validation_json,
        "output_json": output_json,
        **safety_flags(),
    }


def build_deduplication_step_snapshot(
    *,
    context: JobApplicationContext | dict[str, Any],
    deduplication_summary: dict[str, Any],
    observed_at_utc: str,
    agent_run_id: str,
    step_index: int = 1,
    agent_version: str = DEFAULT_AGENT_VERSION,
) -> dict[str, Any]:
    description = describe_deduplication_result(
        deduplication_summary,
        agent_version=agent_version,
    )
    return build_agent_step_snapshot(
        context=context,
        agent_name=AGENT_NAME,
        step_name="deduplication_trace_wrapper",
        step_index=step_index,
        observed_at_utc=observed_at_utc,
        step_status=description["status"],
        agent_run_id=agent_run_id,
        input_summary={
            "input_count": description["input_count"],
            "filtered_count": description["filtered_count"],
        },
        output_summary=description["output_json"],
        reason_codes=description["validation_json"]["errors"],
        metadata={
            "agent_version": description["agent_version"],
            "wrapper_only": True,
            "did_call_live_deduplication": False,
        },
    )
