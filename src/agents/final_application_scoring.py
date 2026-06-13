"""Pure final application scoring agent trace wrapper.

This module describes caller-supplied final application scoring summaries as
deterministic agent trace output. It does not call live scoring, ranking,
matching, filtering, deduplication, JD intelligence, LLM providers, execution,
submission, storage, API, UI, scheduler, reporting, export, or emitter behavior.
"""
# Contract note:
# This wrapper represents final application scoring only.
# It does not perform prefilter relevance, deduplication, JD intelligence, LLM evaluation,
# application execution, or application submission.
# Contract note:
# This wrapper represents final application scoring only.
# It does not perform prefilter relevance, deduplication, JD intelligence, or LLM evaluation.

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents.agent_state import JobApplicationContext, build_agent_step_snapshot
from src.storage.agent_trace.store import build_agent_trace_summary_payload


AGENT_NAME = "final_application_scoring_agent"
DEFAULT_AGENT_VERSION = "final-application-scoring-wrapper-v1"

SAFETY_FLAGS: dict[str, bool] = {
    "did_call_live_final_application_scoring": False,
    "did_call_prefilter_relevance": False,
    "did_call_deduplication": False,
    "did_call_jd_intelligence": False,
    "did_call_llm_provider": False,
    "did_execute_application": False,
    "did_submit_application": False,
    "did_create_connection": False,
    "did_commit_transaction": False,
    "did_run_migration": False,
    "did_schedule_background_work": False,
    "did_execute_scheduler": False,
    "did_execute_reporting_job": False,
    "did_export_files": False,
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


def _safe_int(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return -1
    return parsed


def _sorted_counts(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, int] = {}
    for key, count in value.items():
        label = _clean_text(key)
        if not label:
            continue
        normalized[label] = _safe_int(count)
    return {key: normalized[key] for key in sorted(normalized)}


def _supplied_score(summary: dict[str, Any], key: str) -> Any:
    return deepcopy(summary.get(key)) if key in summary else None


def _validation(
    *,
    input_count: int,
    scored_count: int,
    qualified_count: int,
    disqualified_count: int,
) -> dict[str, Any]:
    errors: list[str] = []
    counts = {
        "input_count": input_count,
        "scored_count": scored_count,
        "qualified_count": qualified_count,
        "disqualified_count": disqualified_count,
    }
    for key, value in counts.items():
        if value < 0:
            errors.append(f"{key}_invalid")

    if not errors:
        if scored_count > input_count:
            errors.append("scored_count_exceeds_input_count")
        if qualified_count + disqualified_count != scored_count:
            errors.append("qualified_disqualified_scored_count_mismatch")

    return {
        "is_valid": not errors,
        "errors": errors,
        "preserves_final_application_scoring": True,
        "did_call_live_final_application_scoring": False,
        "did_call_prefilter_relevance": False,
        "did_call_deduplication": False,
        "did_call_jd_intelligence": False,
        "did_call_llm_provider": False,
    }


def _build_trace_summary(description: dict[str, Any]) -> dict[str, Any]:
    payload = _plain_dict(description)
    step_row = {
        "agent_step_id": "in_memory:final_application_scoring_trace_wrapper",
        "agent_run_id": "in_memory:final_application_scoring_agent",
        "owner_user_id": "read_only_final_application_scoring_wrapper",
        "agent_name": AGENT_NAME,
        "agent_version": payload.get("agent_version", DEFAULT_AGENT_VERSION),
        "input_json": {
            "input_count": payload.get("input_count", -1),
            "scored_count": payload.get("scored_count", -1),
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


def describe_final_application_scoring_result(
    scoring_summary: dict[str, Any],
    *,
    agent_version: str = DEFAULT_AGENT_VERSION,
    include_trace_summary: bool = False,
) -> dict[str, Any]:
    """Describe caller-supplied final scoring output without scoring jobs."""

    summary = _plain_dict(scoring_summary)
    input_count = _safe_int(summary.get("input_count"))
    scored_count = _safe_int(summary.get("scored_count"))
    qualified_count = _safe_int(summary.get("qualified_count"))
    disqualified_count = _safe_int(summary.get("disqualified_count"))
    score_summary = _plain_dict(summary.get("score_summary"))
    threshold_summary = _plain_dict(summary.get("threshold_summary"))
    decision_counts = _sorted_counts(summary.get("decision_counts"))
    top_score = _supplied_score(summary, "top_score")
    bottom_score = _supplied_score(summary, "bottom_score")
    average_score = _supplied_score(summary, "average_score")
    validation_json = _validation(
        input_count=input_count,
        scored_count=scored_count,
        qualified_count=qualified_count,
        disqualified_count=disqualified_count,
    )
    status = "completed" if validation_json["is_valid"] else "invalid"

    output_json: dict[str, Any] = {
        "agent_name": AGENT_NAME,
        "agent_version": _clean_text(agent_version) or DEFAULT_AGENT_VERSION,
        "status": status,
        "input_count": input_count,
        "scored_count": scored_count,
        "qualified_count": qualified_count,
        "disqualified_count": disqualified_count,
        "score_summary": score_summary,
        "threshold_summary": threshold_summary,
        "decision_counts": decision_counts,
        "top_score": top_score,
        "bottom_score": bottom_score,
        "average_score": average_score,
        "validation_json": validation_json,
        "separation": {
            "final_application_scoring": "described_only",
            "prefilter_relevance": "not_called",
            "deduplication": "not_called",
            "jd_intelligence": "not_called",
            "llm_evaluation_live_extraction": "not_called",
            "application_execution": "not_called",
            "application_submission": "not_called",
        },
    }

    payload = {
        "agent_name": AGENT_NAME,
        "agent_version": output_json["agent_version"],
        "status": status,
        "input_count": input_count,
        "scored_count": scored_count,
        "qualified_count": qualified_count,
        "disqualified_count": disqualified_count,
        "score_summary": score_summary,
        "threshold_summary": threshold_summary,
        "decision_counts": decision_counts,
        "top_score": top_score,
        "bottom_score": bottom_score,
        "average_score": average_score,
        "validation_json": validation_json,
        "output_json": output_json,
        **safety_flags(),
    }
    if include_trace_summary:
        payload["trace_summary"] = _build_trace_summary(payload)
    return payload


def build_final_application_scoring_step_snapshot(
    *,
    context: JobApplicationContext | dict[str, Any],
    scoring_summary: dict[str, Any],
    observed_at_utc: str,
    agent_run_id: str,
    step_index: int = 1,
    agent_version: str = DEFAULT_AGENT_VERSION,
    include_trace_summary: bool = False,
) -> dict[str, Any]:
    description = describe_final_application_scoring_result(
        scoring_summary,
        agent_version=agent_version,
        include_trace_summary=include_trace_summary,
    )
    metadata = {
        "agent_version": description["agent_version"],
        "wrapper_only": True,
        "did_call_live_final_application_scoring": False,
    }
    if include_trace_summary:
        metadata["trace_summary"] = _plain_dict(description.get("trace_summary"))
    return build_agent_step_snapshot(
        context=context,
        agent_name=AGENT_NAME,
        step_name="final_application_scoring_trace_wrapper",
        step_index=step_index,
        observed_at_utc=observed_at_utc,
        step_status=description["status"],
        agent_run_id=agent_run_id,
        input_summary={
            "input_count": description["input_count"],
            "scored_count": description["scored_count"],
        },
        output_summary=description["output_json"],
        reason_codes=description["validation_json"]["errors"],
        metadata=metadata,
    )
