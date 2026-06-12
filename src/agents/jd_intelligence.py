"""Pure JD intelligence agent trace wrapper.

This module describes caller-supplied job-description intelligence summaries as
deterministic agent trace output. It does not call live extraction, model
providers, filtering, deduplication, ranking, scoring, execution, submission,
storage, API, UI, scheduler, reporting, export, or emitter behavior.
"""
# Contract note:
# This wrapper represents JD intelligence only.
# It does not perform prefilter relevance, deduplication, LLM evaluation, or final application scoring.

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents.agent_state import JobApplicationContext, build_agent_step_snapshot


AGENT_NAME = "jd_intelligence_agent"
DEFAULT_AGENT_VERSION = "jd-intelligence-wrapper-v1"

SIGNAL_LIST_FIELDS: tuple[str, ...] = (
    "required_skills",
    "preferred_skills",
    "required_tools",
    "preferred_tools",
    "methods",
    "workflows",
    "business_contexts",
    "stakeholder_contexts",
    "ownership_signals",
    "seniority_indicators",
)

SAFETY_FLAGS: dict[str, bool] = {
    "did_call_live_jd_extraction": False,
    "did_call_llm_provider": False,
    "did_call_prefilter_relevance": False,
    "did_call_deduplication": False,
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


def _signal_list(summary: dict[str, Any], field_name: str) -> list[Any]:
    value = summary.get(field_name, [])
    if not isinstance(value, list):
        return []
    return deepcopy(value)


def _validation(summary: dict[str, Any]) -> dict[str, Any]:
    errors: list[str] = []
    for field_name in SIGNAL_LIST_FIELDS:
        if field_name in summary and not isinstance(summary.get(field_name), list):
            errors.append(f"{field_name}_not_list")
    return {
        "is_valid": not errors,
        "errors": errors,
        "preserves_jd_intelligence": True,
        "did_call_live_jd_extraction": False,
        "did_call_llm_provider": False,
        "did_call_prefilter_relevance": False,
        "did_call_deduplication": False,
        "did_call_final_application_scoring": False,
    }


def _signal_counts(signals: dict[str, list[Any]]) -> dict[str, int]:
    return {field_name: len(signals[field_name]) for field_name in SIGNAL_LIST_FIELDS}


def describe_jd_intelligence_result(
    jd_intelligence_summary: dict[str, Any],
    *,
    agent_version: str = DEFAULT_AGENT_VERSION,
) -> dict[str, Any]:
    """Describe caller-supplied JD intelligence without extracting signals."""

    summary = _plain_dict(jd_intelligence_summary)
    signals = {
        field_name: _signal_list(summary, field_name)
        for field_name in SIGNAL_LIST_FIELDS
    }
    validation_json = _validation(summary)
    status = "completed" if validation_json["is_valid"] else "invalid"
    signal_counts = _signal_counts(signals)
    output_json: dict[str, Any] = {
        "agent_name": AGENT_NAME,
        "agent_version": _clean_text(agent_version) or DEFAULT_AGENT_VERSION,
        "status": status,
        **signals,
        "signal_counts": signal_counts,
        "required_skill_count": signal_counts["required_skills"],
        "preferred_skill_count": signal_counts["preferred_skills"],
        "workflow_count": signal_counts["workflows"],
        "business_context_count": signal_counts["business_contexts"],
        "validation_json": validation_json,
        "separation": {
            "jd_intelligence": "described_only",
            "prefilter_relevance": "not_called",
            "deduplication": "not_called",
            "llm_evaluation_live_extraction": "not_called",
            "final_application_scoring": "not_called",
        },
    }
    return {
        "agent_name": AGENT_NAME,
        "agent_version": output_json["agent_version"],
        "status": status,
        **signals,
        "signal_counts": signal_counts,
        "required_skill_count": signal_counts["required_skills"],
        "preferred_skill_count": signal_counts["preferred_skills"],
        "workflow_count": signal_counts["workflows"],
        "business_context_count": signal_counts["business_contexts"],
        "validation_json": validation_json,
        "output_json": output_json,
        **safety_flags(),
    }


def build_jd_intelligence_step_snapshot(
    *,
    context: JobApplicationContext | dict[str, Any],
    jd_intelligence_summary: dict[str, Any],
    observed_at_utc: str,
    agent_run_id: str,
    step_index: int = 1,
    agent_version: str = DEFAULT_AGENT_VERSION,
) -> dict[str, Any]:
    description = describe_jd_intelligence_result(
        jd_intelligence_summary,
        agent_version=agent_version,
    )
    return build_agent_step_snapshot(
        context=context,
        agent_name=AGENT_NAME,
        step_name="jd_intelligence_trace_wrapper",
        step_index=step_index,
        observed_at_utc=observed_at_utc,
        step_status=description["status"],
        agent_run_id=agent_run_id,
        input_summary={
            "required_skill_count": description["required_skill_count"],
            "preferred_skill_count": description["preferred_skill_count"],
            "workflow_count": description["workflow_count"],
            "business_context_count": description["business_context_count"],
        },
        output_summary=description["output_json"],
        reason_codes=description["validation_json"]["errors"],
        metadata={
            "agent_version": description["agent_version"],
            "wrapper_only": True,
            "did_call_live_jd_extraction": False,
            "did_call_llm_provider": False,
        },
    )
