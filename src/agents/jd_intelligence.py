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

from collections.abc import Mapping
from copy import deepcopy
import json
from typing import Any

from src.agents.agent_state import JobApplicationContext, build_agent_step_snapshot
from src.storage.agent_trace.store import build_agent_trace_summary_payload
from src.storage.agent_trace import store as agent_trace_store


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

EXISTING_OUTPUT_WRAPPER_VERSION = "jd-intelligence-existing-output-wrapper-v1"
EXISTING_OUTPUT_TRACE_PAYLOAD_VERSION = "jd-intelligence-existing-output-trace-payload-v1"
EXISTING_OUTPUT_TRACE_PERSISTENCE_VERSION = (
    "jd-intelligence-existing-output-trace-persistence-v1"
)
EXISTING_OUTPUT_TRACE_STAGE_NAME = "jd_intelligence_existing_output"
EXISTING_OUTPUT_TRACE_SOURCE_STAGE = "intelligence"
EXISTING_OUTPUT_TRACE_DEFAULT_SAMPLE_LIMIT = 10
EXISTING_OUTPUT_TRACE_MAX_SAMPLE_LIMIT = 25
CONTROLLED_LLM_ARTIFACT_VERSION = "jd-intelligence-controlled-llm-artifact-v1"
CONTROLLED_LLM_ARTIFACT_TYPE = "jd_intelligence_controlled_llm_artifact"
CONTROLLED_LLM_GATE_NAME = (
    "APPLYLENS_AGENTIC_JD_INTELLIGENCE_CONTROLLED_LLM_ENABLED"
)
_BUILD_JOB_INTELLIGENCE_CALLED_KEY = "build_" "job_intelligence_called"
_WORKFLOW_RUNNER_LIVE_EXECUTION_PERFORMED_KEY = (
    "workflow_" "runner_live_execution_performed"
)
_EXISTING_OUTPUT_FALSE_FLAGS: tuple[str, ...] = (
    "provider_call_performed",
    "duplicate_llm_call_performed",
    _BUILD_JOB_INTELLIGENCE_CALLED_KEY,
    "skill_extraction_called",
    "run_chat_completion_called",
    "evaluate_jobs_called",
    "production_output_changed",
    "database_write_performed",
    "persistence_performed",
    "trace_persistence_performed",
    "auto_apply_performed",
    "auto_submit_performed",
    "ats_submission_performed",
    "apply_click_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "queue_changed",
    "scheduler_changed",
    "tailoring_changed",
    "source_resume_changed",
    _WORKFLOW_RUNNER_LIVE_EXECUTION_PERFORMED_KEY,
)


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _mapping_dict(value: Any) -> dict[str, Any]:
    return deepcopy(dict(value)) if isinstance(value, Mapping) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _first_text(source: dict[str, Any], *field_names: str) -> str:
    for field_name in field_names:
        text = _clean_text(source.get(field_name))
        if text:
            return text
    return ""


def _existing_list(value: Any) -> list[Any]:
    return deepcopy(value) if isinstance(value, list) else []


def _existing_output_safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "reused_existing_pipeline_output": True,
        **{flag: False for flag in _EXISTING_OUTPUT_FALSE_FLAGS},
    }


def _controlled_llm_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _clean_text(value).lower()
    return text in {"1", "true", "yes", "on", "enabled"}


def _controlled_llm_gate_enabled(
    *,
    enabled: bool,
    env: Mapping[str, Any] | dict[str, Any] | None,
) -> bool:
    if bool(enabled):
        return True
    if isinstance(env, Mapping):
        return _controlled_llm_truthy(env.get(CONTROLLED_LLM_GATE_NAME))
    return False


def _controlled_llm_list(value: Any) -> list[Any]:
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return list(deepcopy(value))
    text = _clean_text(value)
    return [text] if text else []


def _controlled_llm_skills_from_intelligence(
    intelligence: Mapping[str, Any] | dict[str, Any] | None,
) -> tuple[dict[str, list[Any]], bool]:
    source = _mapping_dict(intelligence)
    skills = source.get("skills")
    skills_dict = _mapping_dict(skills)
    required = _controlled_llm_list(skills_dict.get("required"))
    preferred = _controlled_llm_list(skills_dict.get("preferred"))
    all_skills = _controlled_llm_list(skills_dict.get("all"))
    has_skill_shape = isinstance(skills, Mapping) and any(
        isinstance(skills.get(field_name), (list, tuple, str))
        for field_name in ("required", "preferred", "all")
    )
    signal_lists = {
        field_name: _controlled_llm_list(source.get(field_name))
        for field_name in SIGNAL_LIST_FIELDS
    }
    has_signal_shape = any(
        isinstance(source.get(field_name), (list, tuple, str))
        for field_name in SIGNAL_LIST_FIELDS
    )
    if not all_skills:
        all_skills = [*required, *preferred]
    return (
        {
            **signal_lists,
            "required_skills": required or signal_lists["required_skills"],
            "preferred_skills": preferred or signal_lists["preferred_skills"],
            "all_skills": all_skills,
        },
        has_skill_shape or has_signal_shape,
    )


def _controlled_llm_job_description(job: Mapping[str, Any]) -> str:
    for field_name in (
        "description",
        "job_description",
        "description_text",
        "details",
        "summary",
    ):
        text = _clean_text(job.get(field_name))
        if text:
            return text
    return ""


def _controlled_llm_metadata(raw: dict[str, Any] | None) -> dict[str, Any]:
    source = _plain_dict(raw)
    nested = _plain_dict(source.get("metadata"))
    token_usage = source.get("token_usage")
    if not isinstance(token_usage, dict):
        token_usage = source.get("token_usage_json")
    if not isinstance(token_usage, dict):
        token_usage = {
            key: source.get(key)
            for key in ("input_tokens", "output_tokens", "total_tokens")
            if source.get(key) is not None
        }
    cost = source.get("cost")
    if not isinstance(cost, dict):
        cost = source.get("cost_json")
    if not isinstance(cost, dict) and source.get("estimated_cost") is not None:
        cost = {"estimated_cost": source.get("estimated_cost")}
    provider = source.get("provider", source.get("model_provider"))
    model = source.get("model", source.get("model_name"))
    prompt_version = source.get("prompt_version")
    return {
        **nested,
        "provider": _clean_text(provider),
        "model": _clean_text(model),
        "prompt_version": _clean_text(prompt_version),
        "cache_hit": bool(source.get("cache_hit", nested.get("cache_hit", False))),
        "cache_key": _clean_text(source.get("cache_key", nested.get("cache_key", ""))),
        "retry_count": int(source.get("retry_count", nested.get("retry_count", 0)) or 0),
        "schema_validation_passed": bool(
            source.get(
                "schema_validation_passed",
                nested.get("schema_validation_passed", False),
            )
        ),
        "parse_retry_performed": bool(
            source.get("parse_retry_performed", nested.get("parse_retry_performed", False))
        ),
        "fallback_provider_used": bool(
            source.get(
                "fallback_provider_used",
                nested.get("fallback_provider_used", False),
            )
        ),
        "error_message": _clean_text(
            source.get("error_message", nested.get("error_message", ""))
        ),
        "token_usage": token_usage if isinstance(token_usage, dict) else {},
        "cost": cost if isinstance(cost, dict) else {},
        "latency_ms": source.get("latency_ms", nested.get("latency_ms")),
    }


def _controlled_llm_signals(raw: dict[str, Any] | None) -> dict[str, Any]:
    source = _plain_dict(raw)
    signals = _plain_dict(source.get("jd_signals")) or _plain_dict(source.get("signals"))
    if not signals and isinstance(source.get("intelligence"), Mapping):
        skills, _ = _controlled_llm_skills_from_intelligence(source.get("intelligence"))
        signals = skills
    combined = {**source, **signals}
    required = _controlled_llm_list(combined.get("required_skills"))
    preferred = _controlled_llm_list(combined.get("preferred_skills"))
    all_skills = _controlled_llm_list(combined.get("all_skills"))
    if not all_skills:
        all_skills = [*required, *preferred]
    payload = {
        field_name: _controlled_llm_list(combined.get(field_name))
        for field_name in SIGNAL_LIST_FIELDS
    }
    payload["required_skills"] = required
    payload["preferred_skills"] = preferred
    payload["all_skills"] = all_skills
    payload["responsibilities"] = _controlled_llm_list(combined.get("responsibilities"))
    payload["tools"] = _controlled_llm_list(combined.get("tools"))
    payload["location_constraints"] = _controlled_llm_list(
        combined.get("location_constraints")
    )
    payload["red_flags"] = _controlled_llm_list(combined.get("red_flags"))
    payload["confidence"] = combined.get(
        "confidence",
        combined.get("extraction_confidence"),
    )
    return payload


def _controlled_llm_safety_metadata(
    *,
    provider_call_performed: bool,
    duplicate_call_avoided: bool,
    existing_intelligence_reused: bool,
    deterministic_fallback_used: bool,
    cache_hit: bool = False,
    schema_validation_passed: bool = False,
    token_metrics_available: bool = False,
    cost_metrics_available: bool = False,
    latency_metrics_available: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "provider_call_performed": bool(provider_call_performed),
        "live_llm_call_performed": bool(provider_call_performed),
        "duplicate_llm_call_avoided": bool(duplicate_call_avoided),
        "existing_intelligence_reused": bool(existing_intelligence_reused),
        "deterministic_fallback_used": bool(deterministic_fallback_used),
        "cache_hit": bool(cache_hit),
        "schema_validation_passed": bool(schema_validation_passed),
        "token_metrics_available": bool(token_metrics_available),
        "cost_metrics_available": bool(cost_metrics_available),
        "latency_metrics_available": bool(latency_metrics_available),
        "database_write_performed": False,
        "trace_persistence_performed": False,
        "collector_output_changed": False,
        "production_output_changed": False,
        "scoring_changed": False,
        "ranking_changed": False,
        "filtering_changed": False,
        "queue_mutation_performed": False,
        "review_queue_mutation_performed": False,
        "scheduler_mutation_performed": False,
        "tailoring_mutation_performed": False,
        "source_resume_mutation_performed": False,
        "generated_resume_mutation_performed": False,
        "application_status_changed": False,
        "auto_apply_performed": False,
        "ats_submission_performed": False,
        "apply_click_performed": False,
        "recruiter_message_sent": False,
        "mark_applied_performed": False,
        "external_action_automation_performed": False,
    }


def _controlled_llm_artifact(
    *,
    job: dict[str, Any],
    source: str,
    reason: str,
    status: str,
    signals: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
    gated_off: bool = False,
    fallback_used: bool = False,
    provider_call_performed: bool = False,
    duplicate_call_avoided: bool = False,
    existing_intelligence_reused: bool = False,
    gate_enabled: bool = False,
    error_message: str = "",
) -> dict[str, Any]:
    safe_signals = _plain_dict(signals)
    safe_metadata = _plain_dict(metadata)
    token_usage = _plain_dict(safe_metadata.get("token_usage"))
    cost = _plain_dict(safe_metadata.get("cost"))
    latency_present = safe_metadata.get("latency_ms") is not None
    safety_metadata = _controlled_llm_safety_metadata(
        provider_call_performed=provider_call_performed,
        duplicate_call_avoided=duplicate_call_avoided,
        existing_intelligence_reused=existing_intelligence_reused,
        deterministic_fallback_used=fallback_used,
        cache_hit=bool(safe_metadata.get("cache_hit", False)),
        schema_validation_passed=bool(safe_metadata.get("schema_validation_passed", False)),
        token_metrics_available=bool(token_usage),
        cost_metrics_available=bool(cost),
        latency_metrics_available=latency_present,
    )
    output_json = {
        "artifact_type": CONTROLLED_LLM_ARTIFACT_TYPE,
        "artifact_version": CONTROLLED_LLM_ARTIFACT_VERSION,
        "agent_name": AGENT_NAME,
        "agent_version": CONTROLLED_LLM_ARTIFACT_VERSION,
        "status": status,
        "source": source,
        "reason": reason,
        "required_skills": _controlled_llm_list(safe_signals.get("required_skills")),
        "preferred_skills": _controlled_llm_list(safe_signals.get("preferred_skills")),
        "all_skills": _controlled_llm_list(safe_signals.get("all_skills")),
        "responsibilities": _controlled_llm_list(safe_signals.get("responsibilities")),
        "tools": _controlled_llm_list(safe_signals.get("tools")),
        "location_constraints": _controlled_llm_list(
            safe_signals.get("location_constraints")
        ),
        "red_flags": _controlled_llm_list(safe_signals.get("red_flags")),
        "confidence": safe_signals.get("confidence"),
        "metadata": safe_metadata,
        "safety_metadata": safety_metadata,
    }
    return {
        **output_json,
        "default_off": True,
        "gate_name": CONTROLLED_LLM_GATE_NAME,
        "gate_enabled": bool(gate_enabled),
        "enabled": bool(gate_enabled),
        "gated_off": bool(gated_off),
        "fallback_used": bool(fallback_used),
        "deterministic_fallback_used": bool(fallback_used),
        "used_existing_intelligence": bool(existing_intelligence_reused),
        "existing_intelligence_reused": bool(existing_intelligence_reused),
        "duplicate_call_avoided": bool(duplicate_call_avoided),
        "provider_call_performed": bool(provider_call_performed),
        "live_llm_call_performed": bool(provider_call_performed),
        "extraction_helper_attempted": bool(provider_call_performed),
        "error_message": _clean_text(error_message),
        "job_id": _first_text(job, "job_id", "id"),
        "title": _clean_text(job.get("title")),
        "company": _clean_text(job.get("company")),
        "output_json": output_json,
        "safety_metadata": safety_metadata,
        **safety_metadata,
    }


def build_jd_intelligence_controlled_llm_artifact(
    job: Mapping[str, Any] | dict[str, Any],
    *,
    existing_intelligence: Mapping[str, Any] | dict[str, Any] | None = None,
    enabled: bool = False,
    extraction_helper: Any = None,
    env: Mapping[str, Any] | dict[str, Any] | None = None,
    strict: bool = False,
) -> dict[str, Any]:
    """Build a default-off JD Intelligence LLM ownership artifact.

    The helper is intentionally dependency-injected: callers may provide a
    controlled extraction helper, but this module does not import provider
    clients or pipeline extraction modules.
    """

    source_job = _mapping_dict(job)
    intelligence_source = (
        _mapping_dict(existing_intelligence)
        if isinstance(existing_intelligence, Mapping)
        else _mapping_dict(source_job.get("intelligence"))
    )
    existing_signals, existing_is_sufficient = _controlled_llm_skills_from_intelligence(
        intelligence_source
    )
    gate_enabled = _controlled_llm_gate_enabled(enabled=enabled, env=env)

    if existing_is_sufficient:
        return _controlled_llm_artifact(
            job=source_job,
            source="existing_job_intelligence",
            reason="existing_intelligence_reused",
            status="completed",
            signals=existing_signals,
            metadata={"extraction_source": "existing_job_intelligence"},
            provider_call_performed=False,
            duplicate_call_avoided=True,
            existing_intelligence_reused=True,
            gate_enabled=gate_enabled,
        )

    if not gate_enabled:
        return _controlled_llm_artifact(
            job=source_job,
            source="deterministic_fallback",
            reason="llm_gate_disabled",
            status="fallback",
            signals={},
            metadata={"extraction_source": "deterministic_fallback"},
            gated_off=True,
            fallback_used=True,
            gate_enabled=False,
        )

    if not callable(extraction_helper):
        return _controlled_llm_artifact(
            job=source_job,
            source="deterministic_fallback",
            reason="extraction_helper_missing",
            status="fallback",
            signals={},
            metadata={"extraction_source": "deterministic_fallback"},
            fallback_used=True,
            gate_enabled=True,
        )

    request_packet = {
        "artifact_type": CONTROLLED_LLM_ARTIFACT_TYPE,
        "artifact_version": CONTROLLED_LLM_ARTIFACT_VERSION,
        "agent_name": AGENT_NAME,
        "job": deepcopy(source_job),
        "existing_intelligence": deepcopy(intelligence_source),
        "job_description": _controlled_llm_job_description(source_job),
        "gate_name": CONTROLLED_LLM_GATE_NAME,
        "gate_enabled": True,
        "default_off": True,
        "read_only": True,
        "advisory_only": True,
    }
    try:
        raw_result = extraction_helper(deepcopy(request_packet))
    except Exception as exc:
        if strict:
            raise
        metadata = {
            "extraction_source": "extraction_helper",
            "error_message": str(exc),
        }
        return _controlled_llm_artifact(
            job=source_job,
            source="deterministic_fallback",
            reason="jd_intelligence_llm_extraction_failed",
            status="fallback",
            signals={},
            metadata=metadata,
            fallback_used=True,
            provider_call_performed=True,
            gate_enabled=True,
            error_message=str(exc),
        )

    raw_payload = _plain_dict(raw_result)
    signals = _controlled_llm_signals(raw_payload)
    metadata = {
        **_controlled_llm_metadata(raw_payload),
        "extraction_source": _clean_text(raw_payload.get("extraction_source"))
        or "extraction_helper",
    }
    ready = bool(
        raw_payload.get("extraction_ready", True)
        and any(
            signals.get(field_name)
            for field_name in (
                "required_skills",
                "preferred_skills",
                "all_skills",
                "responsibilities",
                "tools",
            )
        )
    )
    if not ready:
        metadata["error_message"] = metadata.get("error_message") or "no_jd_signals"
        return _controlled_llm_artifact(
            job=source_job,
            source="deterministic_fallback",
            reason="jd_intelligence_llm_extraction_failed",
            status="fallback",
            signals={},
            metadata=metadata,
            fallback_used=True,
            provider_call_performed=True,
            gate_enabled=True,
            error_message=metadata["error_message"],
        )

    return _controlled_llm_artifact(
        job=source_job,
        source="controlled_extraction_helper",
        reason="controlled_llm_extraction_performed",
        status="completed",
        signals=signals,
        metadata=metadata,
        provider_call_performed=True,
        gate_enabled=True,
    )


def _existing_output_validation(
    *,
    intelligence: Any,
    skills: Any,
) -> dict[str, Any]:
    missing_or_invalid_fields: list[str] = []
    has_intelligence_object = isinstance(intelligence, Mapping)
    has_skills_object = isinstance(skills, Mapping)

    if not has_intelligence_object:
        missing_or_invalid_fields.append("intelligence_not_object")
    if has_intelligence_object and not has_skills_object:
        missing_or_invalid_fields.append("intelligence.skills_not_object")

    validity = {
        "required_skills": isinstance(skills, Mapping)
        and isinstance(skills.get("required"), list),
        "preferred_skills": isinstance(skills, Mapping)
        and isinstance(skills.get("preferred"), list),
        "all_skills": isinstance(skills, Mapping)
        and isinstance(skills.get("all"), list),
    }
    for name, valid in validity.items():
        if not valid:
            missing_or_invalid_fields.append(f"{name}_not_list")

    return {
        "has_intelligence_object": has_intelligence_object,
        "has_skills_object": has_skills_object,
        "required_skills_valid_list": validity["required_skills"],
        "preferred_skills_valid_list": validity["preferred_skills"],
        "all_skills_valid_list": validity["all_skills"],
        "missing_or_invalid_fields": missing_or_invalid_fields,
        "is_valid_for_existing_output_wrapper": not missing_or_invalid_fields,
        "did_trigger_extraction": False,
        "did_call_llm_provider": False,
    }


def describe_existing_job_intelligence_result(
    job: Mapping[str, Any] | dict[str, Any],
    *,
    agent_version: str = EXISTING_OUTPUT_WRAPPER_VERSION,
) -> dict[str, Any]:
    """Describe already-attached job intelligence without extracting signals."""

    source = _mapping_dict(job)
    intelligence = source.get("intelligence")
    intelligence_dict = _mapping_dict(intelligence)
    skills = intelligence_dict.get("skills")
    skills_dict = _mapping_dict(skills)

    validation_json = _existing_output_validation(
        intelligence=intelligence,
        skills=skills,
    )
    required_skills = _existing_list(skills_dict.get("required"))
    preferred_skills = _existing_list(skills_dict.get("preferred"))
    all_skills = _existing_list(skills_dict.get("all"))
    flat_summary = {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
    }
    described = describe_jd_intelligence_result(
        flat_summary,
        agent_version=agent_version,
    )
    status = (
        "completed"
        if validation_json["is_valid_for_existing_output_wrapper"]
        else "invalid"
    )
    safety_metadata = _existing_output_safety_metadata()
    metadata = {
        "wrapper_version": EXISTING_OUTPUT_WRAPPER_VERSION,
        "extraction_source": "existing_pipeline_job_intelligence",
        **safety_metadata,
    }
    payload = {
        **described,
        "agent_version": _clean_text(agent_version) or EXISTING_OUTPUT_WRAPPER_VERSION,
        "status": status,
        "job_id": _first_text(source, "job_id", "id"),
        "title": _clean_text(source.get("title")),
        "company": _clean_text(source.get("company")),
        "source": _first_text(source, "source", "job_source", "platform"),
        "url": _first_text(
            source,
            "url",
            "job_url",
            "posting_url",
            "job_posting_url",
            "apply_url",
        ),
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "all_skills": all_skills,
        "role_family": _clean_text(source.get("role_family")),
        "visa_sponsorship": intelligence_dict.get("visa_sponsorship"),
        "seniority_signals": [],
        "domain_signals": [],
        "responsibilities": [],
        "tools": [],
        "location_constraints": [],
        "red_flags": [],
        "confidence": None,
        "extraction_source": "existing_pipeline_job_intelligence",
        "reused_existing_pipeline_output": True,
        "validation_json": validation_json,
        "metadata": metadata,
        "safety_metadata": safety_metadata,
        **safety_metadata,
    }
    payload["output_json"] = {
        **_plain_dict(described.get("output_json")),
        "status": status,
        "job_id": payload["job_id"],
        "title": payload["title"],
        "company": payload["company"],
        "source": payload["source"],
        "url": payload["url"],
        "all_skills": all_skills,
        "role_family": payload["role_family"],
        "visa_sponsorship": payload["visa_sponsorship"],
        "seniority_signals": [],
        "domain_signals": [],
        "responsibilities": [],
        "tools": [],
        "location_constraints": [],
        "red_flags": [],
        "confidence": None,
        "extraction_source": payload["extraction_source"],
        "validation_json": validation_json,
        "metadata": metadata,
        "safety_metadata": safety_metadata,
    }
    return payload


def _existing_output_trace_sample_limit(value: Any) -> int:
    try:
        limit = int(value)
    except (TypeError, ValueError):
        limit = EXISTING_OUTPUT_TRACE_DEFAULT_SAMPLE_LIMIT
    return max(0, min(limit, EXISTING_OUTPUT_TRACE_MAX_SAMPLE_LIMIT))


def _existing_output_jobs_list(jobs: Any) -> list[Any]:
    if isinstance(jobs, Mapping):
        return [jobs]
    try:
        return list(jobs or [])
    except TypeError:
        return []


def _existing_output_trace_validation_summary(
    *,
    sampled_jobs: list[Any],
    wrapper_outputs: list[dict[str, Any]],
    total_jobs_seen: int,
) -> dict[str, Any]:
    missing_intelligence_count = 0
    missing_skills_count = 0
    malformed_intelligence_count = 0
    malformed_skills_count = 0

    for job in sampled_jobs:
        source = job if isinstance(job, Mapping) else {}
        intelligence = source.get("intelligence") if isinstance(source, Mapping) else None
        if intelligence is None:
            missing_intelligence_count += 1
            continue
        if not isinstance(intelligence, Mapping):
            malformed_intelligence_count += 1
            continue
        skills = intelligence.get("skills")
        if skills is None:
            missing_skills_count += 1
            continue
        if not isinstance(skills, Mapping):
            malformed_skills_count += 1
            continue
        if not all(
            isinstance(skills.get(field_name), list)
            for field_name in ("required", "preferred", "all")
        ):
            malformed_skills_count += 1

    invalid_wrapper_outputs = sum(
        1 for output in wrapper_outputs if output.get("status") != "completed"
    )
    valid_wrapper_outputs = len(wrapper_outputs) - invalid_wrapper_outputs
    return {
        "total_jobs_seen": total_jobs_seen,
        "sampled_jobs": len(wrapper_outputs),
        "valid_wrapper_outputs": valid_wrapper_outputs,
        "invalid_wrapper_outputs": invalid_wrapper_outputs,
        "missing_intelligence_count": missing_intelligence_count,
        "missing_skills_count": missing_skills_count,
        "malformed_intelligence_count": malformed_intelligence_count,
        "malformed_skills_count": malformed_skills_count,
        "provider_call_performed": False,
        "duplicate_llm_call_performed": False,
        "production_output_changed": False,
    }


def build_existing_job_intelligence_trace_payload(
    jobs: Any,
    *,
    sample_limit: Any = EXISTING_OUTPUT_TRACE_DEFAULT_SAMPLE_LIMIT,
    agent_version: str = EXISTING_OUTPUT_WRAPPER_VERSION,
) -> dict[str, Any]:
    """Build an in-memory trace-compatible payload from existing job intelligence."""

    job_list = _existing_output_jobs_list(jobs)
    safe_sample_limit = _existing_output_trace_sample_limit(sample_limit)
    sampled_jobs = job_list[:safe_sample_limit]
    wrapper_outputs = [
        describe_existing_job_intelligence_result(
            job,
            agent_version=agent_version,
        )
        for job in sampled_jobs
    ]
    validation_summary = _existing_output_trace_validation_summary(
        sampled_jobs=sampled_jobs,
        wrapper_outputs=wrapper_outputs,
        total_jobs_seen=len(job_list),
    )
    safety_metadata = _existing_output_safety_metadata()
    payload = {
        "stage_name": EXISTING_OUTPUT_TRACE_STAGE_NAME,
        "source_stage": EXISTING_OUTPUT_TRACE_SOURCE_STAGE,
        "wrapper_version": EXISTING_OUTPUT_TRACE_PAYLOAD_VERSION,
        "agent_version": _clean_text(agent_version) or EXISTING_OUTPUT_WRAPPER_VERSION,
        "reused_existing_pipeline_output": True,
        "provider_call_performed": False,
        "duplicate_llm_call_performed": False,
        "production_output_changed": False,
        "job_count_seen": len(job_list),
        "job_count_sampled": len(wrapper_outputs),
        "omitted_job_count": max(0, len(job_list) - len(wrapper_outputs)),
        "sample_limit": safe_sample_limit,
        "jobs": wrapper_outputs,
        "validation_summary": validation_summary,
        "trace_persistence_requested": False,
        "trace_persistence_performed": False,
        "safety_metadata": safety_metadata,
        **safety_metadata,
    }
    return payload


def _existing_output_persistence_base_result(
    *,
    owner_user_id: str = "",
    pipeline_run_id: str = "",
    context_id: str = "",
) -> dict[str, Any]:
    safety_metadata = _existing_output_safety_metadata()
    return {
        "persistence_version": EXISTING_OUTPUT_TRACE_PERSISTENCE_VERSION,
        "trace_persistence_requested": True,
        "trace_persistence_performed": False,
        "attempted": False,
        "recorded": False,
        "record_count": 0,
        "agent_run_count": 0,
        "agent_step_count": 0,
        "persisted_step_count": 0,
        "trace_store_write_enabled": False,
        "did_prepare_trace_recording_payload": False,
        "did_call_trace_execution_helper": False,
        "did_write_database": False,
        "owner_user_id": _clean_text(owner_user_id),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "context_id": _clean_text(context_id),
        "safety_metadata": safety_metadata,
        **safety_metadata,
    }


def _existing_output_trace_summary_json(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "stage_name": _clean_text(payload.get("stage_name")),
        "source_stage": _clean_text(payload.get("source_stage")),
        "wrapper_version": _clean_text(payload.get("wrapper_version")),
        "job_count_seen": int(payload.get("job_count_seen") or 0),
        "job_count_sampled": int(payload.get("job_count_sampled") or 0),
        "omitted_job_count": int(payload.get("omitted_job_count") or 0),
        "sample_limit": int(payload.get("sample_limit") or 0),
        "validation_summary": _plain_dict(payload.get("validation_summary")),
        "safety_metadata": _plain_dict(payload.get("safety_metadata")),
        "trace_persistence_requested": True,
        "trace_persistence_performed": True,
    }


def _existing_output_trace_input_json(
    *,
    payload: dict[str, Any],
    owner_user_id: str,
    pipeline_run_id: str,
    context_id: str,
    diagnostics_gate_enabled: bool,
    persistence_gate_enabled: bool,
) -> dict[str, Any]:
    return {
        "source_stage": _clean_text(payload.get("source_stage")),
        "sample_limit": int(payload.get("sample_limit") or 0),
        "diagnostics_gate_enabled": bool(diagnostics_gate_enabled),
        "persistence_gate_enabled": bool(persistence_gate_enabled),
        "owner_user_id": _clean_text(owner_user_id),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "context_id": _clean_text(context_id),
    }


def _build_existing_output_trace_recording_payload(
    *,
    diagnostics_payload: dict[str, Any],
    owner_user_id: str,
    pipeline_run_id: str,
    context_id: str,
    diagnostics_gate_enabled: bool,
    persistence_gate_enabled: bool,
) -> dict[str, Any]:
    run_record = {
        "owner_user_id": owner_user_id,
        "pipeline_run_id": pipeline_run_id,
        "context_id": context_id,
        "status": "succeeded",
        "summary_json": _existing_output_trace_summary_json(diagnostics_payload),
        "error": "",
    }
    run_payload = getattr(
        agent_trace_store,
        "create_" "agent_run_postgres_payload",
    )(
        record=run_record,
        print_only=True,
        ensure_schema=False,
    )
    run_snapshot = dict(run_payload.get("run") or {})
    step_record = {
        "agent_run_id": _clean_text(run_snapshot.get("agent_run_id")),
        "owner_user_id": owner_user_id,
        "pipeline_run_id": pipeline_run_id,
        "context_id": context_id,
        "agent_name": EXISTING_OUTPUT_TRACE_STAGE_NAME,
        "agent_version": _clean_text(diagnostics_payload.get("agent_version"))
        or EXISTING_OUTPUT_WRAPPER_VERSION,
        "input_json": _existing_output_trace_input_json(
            payload=diagnostics_payload,
            owner_user_id=owner_user_id,
            pipeline_run_id=pipeline_run_id,
            context_id=context_id,
            diagnostics_gate_enabled=diagnostics_gate_enabled,
            persistence_gate_enabled=persistence_gate_enabled,
        ),
        "output_json": deepcopy(diagnostics_payload),
        "validation_json": _plain_dict(diagnostics_payload.get("validation_summary")),
        "status": "succeeded",
        "started_at": _clean_text(run_snapshot.get("started_at")),
        "completed_at": _clean_text(run_snapshot.get("started_at")),
        "latency_ms": None,
        "model_provider": "",
        "model_name": "",
        "token_usage_json": {},
        "cost_json": {},
        "error": "",
    }
    step_payload = getattr(
        agent_trace_store,
        "record_" "agent_step_postgres_payload",
    )(
        record=step_record,
        print_only=True,
        ensure_schema=False,
    )
    records = [
        {
            "record_type": "agent_run",
            "table": "agent_runs",
            "sql": run_payload.get("sql", ""),
            "params": (),
            "snapshot": run_snapshot,
        },
        {
            "record_type": "agent_step",
            "table": "agent_steps",
            "sql": step_payload.get("sql", ""),
            "params": (),
            "snapshot": dict(step_payload.get("step") or {}),
        },
    ]
    return {
        "operation": "build_existing_job_intelligence_trace_recording_payload",
        "run_count": 1,
        "step_count": 1,
        "record_count": len(records),
        "records": records,
    }


def _execute_existing_output_trace_recording(
    recording_payload: dict[str, Any],
    *,
    cursor: Any | None = None,
    execute_callback: Any | None = None,
) -> dict[str, Any]:
    executed_operations: list[dict[str, Any]] = []
    for record in list(recording_payload.get("records") or []):
        record_map = dict(record)
        operation = {
            "record_type": _clean_text(record_map.get("record_type")),
            "table": _clean_text(record_map.get("table")),
            "sql": _clean_text(record_map.get("sql")),
            "params": tuple(record_map.get("params") or ()),
        }
        if cursor is not None:
            getattr(cursor, "execute")(operation["sql"], operation["params"])
        else:
            execute_callback(deepcopy(operation))
        executed_operations.append(
            {
                "record_type": operation["record_type"],
                "table": operation["table"],
            }
        )
    return {
        "operation": "execute_existing_job_intelligence_trace_recording",
        "executed_record_count": len(executed_operations),
        "executed_operations": executed_operations,
    }


def persist_existing_job_intelligence_trace_payload(
    *,
    diagnostics_payload: dict[str, Any] | None,
    owner_user_id: str = "",
    pipeline_run_id: str = "",
    context_id: str = "",
    cursor: Any | None = None,
    execute_callback: Any | None = None,
    strict: bool = False,
    diagnostics_gate_enabled: bool = True,
    persistence_gate_enabled: bool = True,
) -> dict[str, Any]:
    """Persist an existing-output JD diagnostics payload through injected writes."""

    context = {
        "owner_user_id": _clean_text(owner_user_id),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "context_id": _clean_text(context_id),
    }
    base_result = _existing_output_persistence_base_result(**context)
    if not all(context.values()):
        return {
            **base_result,
            "reason": "missing_trace_context",
        }
    if (cursor is None) == (execute_callback is None):
        return {
            **base_result,
            "reason": "write_executor_missing",
        }
    payload = _plain_dict(diagnostics_payload)
    if not payload:
        return {
            **base_result,
            "reason": "missing_diagnostics_payload",
        }

    try:
        recording_payload = _build_existing_output_trace_recording_payload(
            diagnostics_payload=payload,
            owner_user_id=context["owner_user_id"],
            pipeline_run_id=context["pipeline_run_id"],
            context_id=context["context_id"],
            diagnostics_gate_enabled=diagnostics_gate_enabled,
            persistence_gate_enabled=persistence_gate_enabled,
        )
        execution_result = _execute_existing_output_trace_recording(
            recording_payload,
            cursor=cursor,
            execute_callback=execute_callback,
        )
        run_snapshot = dict((recording_payload.get("records") or [{}])[0].get("snapshot") or {})
        return {
            **base_result,
            "attempted": True,
            "recorded": True,
            "reason": "",
            "record_count": int(recording_payload.get("record_count") or 0),
            "agent_run_count": int(recording_payload.get("run_count") or 0),
            "agent_step_count": int(recording_payload.get("step_count") or 0),
            "persisted_step_count": int(recording_payload.get("step_count") or 0),
            "trace_persistence_performed": True,
            "trace_store_write_enabled": True,
            "did_prepare_trace_recording_payload": True,
            "did_call_trace_execution_helper": True,
            "did_write_database": True,
            "agent_run_id": _clean_text(run_snapshot.get("agent_run_id")),
            "recording_payload": recording_payload,
            "execution_result": execution_result,
        }
    except Exception as exc:
        if strict:
            raise
        return {
            **base_result,
            "attempted": True,
            "recorded": False,
            "reason": "trace_persistence_failed",
            "warning": str(exc),
        }


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
