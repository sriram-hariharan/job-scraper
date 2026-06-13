"""Pure relevance prefilter agent trace wrapper.

This module describes caller-supplied prefilter results as deterministic agent
trace output. It does not call live filtering, ranking, scoring, LLM evaluation,
execution, submission, storage, API, UI, scheduler, or reporting behavior.
"""
# Contract note:
# This wrapper represents prefilter relevance only.
# It does not perform LLM evaluation or final application scoring.

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents.agent_state import JobApplicationContext, build_agent_step_snapshot
from src.storage.agent_trace.store import build_agent_trace_summary_payload


AGENT_NAME = "relevance_prefilter_agent"
DEFAULT_AGENT_VERSION = "prefilter-wrapper-v1"

SAFETY_FLAGS: dict[str, bool] = {
    "did_call_live_filter": False,
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


def _optional_text(payload: dict[str, Any], key: str) -> str:
    return _clean_text(payload.get(key))


def _safe_int(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return -1
    return parsed


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


def _validation(input_count: int, kept_count: int, dropped_count: int) -> dict[str, Any]:
    errors: list[str] = []
    if input_count < 0:
        errors.append("input_count_invalid")
    if kept_count < 0:
        errors.append("kept_count_invalid")
    if dropped_count < 0:
        errors.append("dropped_count_invalid")
    if input_count >= 0 and kept_count >= 0 and dropped_count >= 0:
        if kept_count + dropped_count != input_count:
            errors.append("kept_dropped_count_mismatch")
    return {
        "is_valid": not errors,
        "errors": errors,
        "preserves_prefilter_relevance": True,
        "did_call_live_filter": False,
        "did_call_llm_evaluation": False,
        "did_call_final_application_scoring": False,
    }


def _build_trace_summary(description: dict[str, Any]) -> dict[str, Any]:
    payload = _plain_dict(description)
    step_row = {
        "agent_step_id": "in_memory:relevance_prefilter_trace_wrapper",
        "agent_run_id": "in_memory:relevance_prefilter_agent",
        "owner_user_id": "read_only_relevance_prefilter_wrapper",
        "agent_name": AGENT_NAME,
        "agent_version": payload.get("agent_version", DEFAULT_AGENT_VERSION),
        "input_json": {
            "input_count": payload.get("input_count", -1),
            "role_family": payload.get("role_family", ""),
            "seniority": payload.get("seniority", ""),
            "location_policy": payload.get("location_policy", ""),
        },
        "output_json": _plain_dict(payload.get("output_json")),
        "validation_json": _plain_dict(payload.get("validation_json")),
        "status": payload.get("status", "unknown"),
        "started_at": "in_memory",
        "completed_at": "in_memory",
        "latency_ms": 0,
        "model_provider": "",
        "model_name": "",
        "token_usage_json": {},
        "cost_json": {},
        "error": "",
    }
    return build_agent_trace_summary_payload(agent_runs=[], agent_steps=[step_row])


def describe_relevance_prefilter_result(
    prefilter_summary: dict[str, Any],
    *,
    agent_version: str = DEFAULT_AGENT_VERSION,
    include_trace_summary: bool = False,
) -> dict[str, Any]:
    """Describe caller-supplied prefilter output without running prefiltering."""

    summary = _plain_dict(prefilter_summary)
    input_count = _safe_int(summary.get("input_count"))
    kept_count = _safe_int(summary.get("kept_count"))
    dropped_count = _safe_int(summary.get("dropped_count"))
    reason_counts = _sorted_reason_counts(summary.get("reason_counts"))
    validation_json = _validation(input_count, kept_count, dropped_count)
    status = "completed" if validation_json["is_valid"] else "invalid"

    output_json: dict[str, Any] = {
        "agent_name": AGENT_NAME,
        "agent_version": _clean_text(agent_version) or DEFAULT_AGENT_VERSION,
        "status": status,
        "input_count": input_count,
        "kept_count": kept_count,
        "dropped_count": dropped_count,
        "reason_counts": reason_counts,
        "validation_json": validation_json,
        "separation": {
            "prefilter_relevance": "described_only",
            "llm_evaluation": "not_called",
            "final_application_scoring": "not_called",
        },
    }
    for optional_key in (
        "embedding_similarity_summary",
        "role_family",
        "seniority",
        "location_policy",
    ):
        if optional_key in summary:
            value = summary.get(optional_key)
            output_json[optional_key] = (
                _plain_dict(value) if isinstance(value, dict) else _clean_text(value)
            )

    payload = {
        "agent_name": AGENT_NAME,
        "agent_version": output_json["agent_version"],
        "status": status,
        "input_count": input_count,
        "kept_count": kept_count,
        "dropped_count": dropped_count,
        "reason_counts": reason_counts,
        "embedding_similarity_summary": output_json.get(
            "embedding_similarity_summary", {}
        ),
        "role_family": _optional_text(output_json, "role_family"),
        "seniority": _optional_text(output_json, "seniority"),
        "location_policy": _optional_text(output_json, "location_policy"),
        "validation_json": validation_json,
        "output_json": output_json,
        **safety_flags(),
    }
    if include_trace_summary:
        payload["trace_summary"] = _build_trace_summary(payload)
    return payload


def build_relevance_prefilter_step_snapshot(
    *,
    context: JobApplicationContext | dict[str, Any],
    prefilter_summary: dict[str, Any],
    observed_at_utc: str,
    agent_run_id: str,
    step_index: int = 1,
    agent_version: str = DEFAULT_AGENT_VERSION,
    include_trace_summary: bool = False,
) -> dict[str, Any]:
    description = describe_relevance_prefilter_result(
        prefilter_summary,
        agent_version=agent_version,
        include_trace_summary=include_trace_summary,
    )
    metadata = {
        "agent_version": description["agent_version"],
        "wrapper_only": True,
        "did_call_live_filter": False,
    }
    if include_trace_summary:
        metadata["trace_summary"] = _plain_dict(description.get("trace_summary"))
    return build_agent_step_snapshot(
        context=context,
        agent_name=AGENT_NAME,
        step_name="relevance_prefilter_trace_wrapper",
        step_index=step_index,
        observed_at_utc=observed_at_utc,
        step_status=description["status"],
        agent_run_id=agent_run_id,
        input_summary={
            "input_count": description["input_count"],
            "role_family": description["role_family"],
            "seniority": description["seniority"],
            "location_policy": description["location_policy"],
        },
        output_summary=description["output_json"],
        reason_codes=description["validation_json"]["errors"],
        metadata=metadata,
    )
