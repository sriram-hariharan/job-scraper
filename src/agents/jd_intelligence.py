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

import json
from copy import deepcopy
from typing import Any

from src.agents.agent_state import JobApplicationContext, build_agent_step_snapshot
from src.storage.agent_trace.store import build_agent_trace_summary_payload


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


def _build_trace_summary(description: dict[str, Any]) -> dict[str, Any]:
    payload = _plain_dict(description)
    step_row = {
        "agent_step_id": "in_memory:jd_intelligence_trace_wrapper",
        "agent_run_id": "in_memory:jd_intelligence_agent",
        "owner_user_id": "read_only_jd_intelligence_wrapper",
        "agent_name": AGENT_NAME,
        "agent_version": payload.get("agent_version", DEFAULT_AGENT_VERSION),
        "input_json": {
            "required_skill_count": payload.get("required_skill_count", 0),
            "preferred_skill_count": payload.get("preferred_skill_count", 0),
            "workflow_count": payload.get("workflow_count", 0),
            "business_context_count": payload.get("business_context_count", 0),
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


def describe_jd_intelligence_result(
    jd_intelligence_summary: dict[str, Any],
    *,
    agent_version: str = DEFAULT_AGENT_VERSION,
    include_trace_summary: bool = False,
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
    payload = {
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
    if include_trace_summary:
        payload["trace_summary"] = _build_trace_summary(payload)
    return payload


def build_jd_intelligence_step_snapshot(
    *,
    context: JobApplicationContext | dict[str, Any],
    jd_intelligence_summary: dict[str, Any],
    observed_at_utc: str,
    agent_run_id: str,
    step_index: int = 1,
    agent_version: str = DEFAULT_AGENT_VERSION,
    include_trace_summary: bool = False,
) -> dict[str, Any]:
    description = describe_jd_intelligence_result(
        jd_intelligence_summary,
        agent_version=agent_version,
        include_trace_summary=include_trace_summary,
    )
    metadata = {
        "agent_version": description["agent_version"],
        "wrapper_only": True,
        "did_call_live_jd_extraction": False,
        "did_call_llm_provider": False,
    }
    if include_trace_summary:
        metadata["trace_summary"] = _plain_dict(description.get("trace_summary"))
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
        metadata=metadata,
    )


LIVE_DRY_RUN_PROMPT_VERSION = "live-jd-intelligence-dry-run-v1"
LIVE_DRY_RUN_LIST_FIELDS: tuple[str, ...] = (
    "required_skills",
    "preferred_skills",
    "required_tools",
    "preferred_tools",
    "workflows",
    "methods",
    "business_contexts",
    "stakeholder_contexts",
    "ownership_signals",
    "seniority_signals",
    "risk_flags",
)


def _dry_run_safety_metadata(*, did_call_llm: bool) -> dict[str, bool]:
    return {
        "dry_run_only": True,
        "feature_flag_required": True,
        "did_call_llm": bool(did_call_llm),
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_mutate_approval": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "pipeline_wiring_added": False,
    }


def _dry_run_enabled(config: dict[str, Any] | None, feature_enabled: bool) -> bool:
    if isinstance(config, dict):
        for key in ("enabled", "feature_enabled", "live_jd_intelligence_enabled"):
            if key in config:
                return bool(config.get(key))
    return bool(feature_enabled)


def _dry_run_list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [_clean_text(item) for item in value if _clean_text(item)]
    if isinstance(value, tuple):
        return [_clean_text(item) for item in value if _clean_text(item)]
    text = _clean_text(value)
    return [text] if text else []


def _dry_run_float(value: Any) -> float:
    try:
        number = float(str(value or "0").strip() or "0")
    except (TypeError, ValueError):
        return 0.0
    return max(0.0, min(1.0, number))


def _dry_run_int(value: Any) -> int:
    try:
        return max(0, int(float(str(value or "0").strip() or "0")))
    except (TypeError, ValueError):
        return 0


def _dry_run_payload(
    *,
    validation_status: str,
    validation_errors: list[str],
    fallback_used: bool,
    did_call_llm: bool,
    model_provider: str = "deterministic",
    model_name: str = "jd_intelligence_dry_run_fallback",
    prompt_version: str = LIVE_DRY_RUN_PROMPT_VERSION,
    token_usage: dict[str, Any] | None = None,
    cost: dict[str, Any] | None = None,
    latency_ms: Any = 0,
    normalized: dict[str, Any] | None = None,
) -> dict[str, Any]:
    values = deepcopy(normalized) if isinstance(normalized, dict) else {}
    payload = {
        field_name: _dry_run_list(values.get(field_name))
        for field_name in LIVE_DRY_RUN_LIST_FIELDS
    }
    payload.update(
        {
            "extraction_confidence": _dry_run_float(values.get("extraction_confidence")),
            "validation_status": _clean_text(validation_status),
            "validation_errors": list(validation_errors),
            "fallback_used": bool(fallback_used),
            "model_provider": _clean_text(model_provider),
            "model_name": _clean_text(model_name),
            "prompt_version": _clean_text(prompt_version) or LIVE_DRY_RUN_PROMPT_VERSION,
            "token_usage": _plain_dict(token_usage),
            "cost": _plain_dict(cost),
            "latency_ms": _dry_run_int(latency_ms),
            "safety_metadata": _dry_run_safety_metadata(did_call_llm=did_call_llm),
        }
    )
    return payload


def _dry_run_adapter_metadata(raw: dict[str, Any]) -> dict[str, Any]:
    token_usage = raw.get("token_usage")
    if not isinstance(token_usage, dict):
        token_usage = raw.get("token_usage_json")
    cost = raw.get("cost")
    if not isinstance(cost, dict):
        cost = raw.get("cost_json")
    return {
        "model_provider": raw.get("model_provider", raw.get("provider", "")),
        "model_name": raw.get("model_name", raw.get("model", "")),
        "prompt_version": raw.get("prompt_version", LIVE_DRY_RUN_PROMPT_VERSION),
        "token_usage": token_usage if isinstance(token_usage, dict) else {},
        "cost": cost if isinstance(cost, dict) else {},
        "latency_ms": raw.get("latency_ms", 0),
    }


def _dry_run_parse_adapter_response(raw_response: Any) -> tuple[dict[str, Any] | None, str]:
    if isinstance(raw_response, dict):
        raw_content = raw_response.get("raw_response", raw_response.get("content"))
        if isinstance(raw_content, str):
            try:
                parsed_content = json.loads(raw_content)
            except json.JSONDecodeError:
                return None, "invalid_json_response"
            if not isinstance(parsed_content, dict):
                return None, "json_response_not_object"
            merged = deepcopy(parsed_content)
            for key, value in raw_response.items():
                if key not in {"raw_response", "content"}:
                    merged[key] = deepcopy(value)
            return merged, ""
        return deepcopy(raw_response), ""
    if isinstance(raw_response, str):
        try:
            parsed = json.loads(raw_response)
        except json.JSONDecodeError:
            return None, "invalid_json_response"
        if isinstance(parsed, dict):
            return parsed, ""
        return None, "json_response_not_object"
    return None, "adapter_response_not_object"


def build_live_jd_intelligence_dry_run_payload(
    *,
    job_title: Any = "",
    company: Any = "",
    location: Any = "",
    job_description: Any = "",
    source_metadata: dict[str, Any] | None = None,
    context_id: Any = "",
    job_id: Any = "",
    adapter: Any = None,
    feature_enabled: bool = False,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a deterministic read-only live JD intelligence dry-run contract."""

    adapter_input = {
        "job_title": _clean_text(job_title),
        "company": _clean_text(company),
        "location": _clean_text(location),
        "job_description": _clean_text(job_description),
        "source_metadata": _plain_dict(source_metadata),
        "context_id": _clean_text(context_id),
        "job_id": _clean_text(job_id),
        "prompt_version": LIVE_DRY_RUN_PROMPT_VERSION,
    }

    if not _dry_run_enabled(config, feature_enabled):
        return _dry_run_payload(
            validation_status="disabled",
            validation_errors=["feature_flag_disabled"],
            fallback_used=True,
            did_call_llm=False,
        )

    if not callable(adapter):
        return _dry_run_payload(
            validation_status="fallback",
            validation_errors=["adapter_missing"],
            fallback_used=True,
            did_call_llm=False,
        )

    try:
        raw_response = adapter(deepcopy(adapter_input))
    except Exception as exc:
        return _dry_run_payload(
            validation_status="fallback",
            validation_errors=[f"adapter_error:{exc.__class__.__name__}"],
            fallback_used=True,
            did_call_llm=True,
        )

    parsed, parse_error = _dry_run_parse_adapter_response(raw_response)
    if parsed is None:
        return _dry_run_payload(
            validation_status="fallback",
            validation_errors=[parse_error],
            fallback_used=True,
            did_call_llm=True,
        )

    normalized = {
        field_name: _dry_run_list(parsed.get(field_name))
        for field_name in LIVE_DRY_RUN_LIST_FIELDS
    }
    if not normalized["seniority_signals"]:
        normalized["seniority_signals"] = _dry_run_list(parsed.get("seniority_indicators"))
    normalized["extraction_confidence"] = _dry_run_float(parsed.get("extraction_confidence"))
    validation_errors = [
        f"{field_name}_not_list"
        for field_name in LIVE_DRY_RUN_LIST_FIELDS
        if field_name in parsed and not isinstance(parsed.get(field_name), (list, tuple, str))
    ]
    if not any(normalized[field_name] for field_name in LIVE_DRY_RUN_LIST_FIELDS):
        validation_errors.append("no_jd_intelligence_signals")

    metadata = _dry_run_adapter_metadata(parsed)
    return _dry_run_payload(
        validation_status="valid" if not validation_errors else "invalid",
        validation_errors=validation_errors,
        fallback_used=False,
        did_call_llm=True,
        normalized=normalized,
        **metadata,
    )
