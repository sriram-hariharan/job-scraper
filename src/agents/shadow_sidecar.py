from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable


SCHEMA_VERSION = "phase5_shadow_sidecar_trace_v1"

GLOBAL_SIDECAR_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
JD_INTELLIGENCE_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED"
TAILORING_SUGGESTION_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED"
CRITIC_GUARDRAIL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED"
KILL_SWITCH_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"
THREE_AGENT_SHADOW_WORKFLOW_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_THREE_AGENT_SHADOW_WORKFLOW_ENABLED"
)

STATUS_NOT_ENABLED = "not_enabled"
STATUS_SKIPPED_BY_CONFIG = "skipped_by_config"
STATUS_COMPLETED_SHADOW = "completed_shadow"
STATUS_COMPLETED_WITH_FALLBACK = "completed_with_fallback"
STATUS_BLOCKED_BY_KILL_SWITCH = "blocked_by_kill_switch"
STATUS_FAILED_NON_BLOCKING = "failed_non_blocking"
CHAIN_STATUS_COMPLETED_SHADOW_CHAIN = "completed_shadow_chain"

OBSERVED_STATUS_NOT_ENABLED = "observed_not_enabled"
OBSERVED_STATUS_SKIPPED_BY_CONFIG = "observed_skipped_by_config"
OBSERVED_STATUS_BLOCKED_BY_KILL_SWITCH = "observed_blocked_by_kill_switch"
OBSERVED_STATUS_COMPLETED_SHADOW_CHAIN = "observed_completed_shadow_chain"
OBSERVED_STATUS_COMPLETED_WITH_FALLBACK = "observed_completed_with_fallback"
OBSERVED_STATUS_FAILED_NON_BLOCKING = "observed_failed_non_blocking"
OBSERVED_STATUS_MISSING_SOURCE = "observed_missing_source"
OBSERVED_STATUS_INVALID_SOURCE = "observed_invalid_source"

HOOK_STATUS_NOT_ENABLED = "hook_not_enabled"
HOOK_STATUS_BLOCKED_BY_KILL_SWITCH = "hook_blocked_by_kill_switch"
HOOK_STATUS_BLOCKED_MISSING_CONTEXT = "hook_blocked_missing_context"
HOOK_STATUS_BLOCKED_UNSUPPORTED_STAGE = "hook_blocked_unsupported_stage"
HOOK_STATUS_SKIPPED_NO_ENABLED_AGENTS = "hook_skipped_no_enabled_agents"
HOOK_STATUS_READY_FOR_SHADOW_SIDECAR = "hook_ready_for_shadow_sidecar"
HOOK_STATUS_FAILED_NON_BLOCKING = "hook_failed_non_blocking"

SIDECAR_STATUS_ENUM = (
    STATUS_NOT_ENABLED,
    STATUS_SKIPPED_BY_CONFIG,
    STATUS_COMPLETED_SHADOW,
    STATUS_COMPLETED_WITH_FALLBACK,
    STATUS_BLOCKED_BY_KILL_SWITCH,
    STATUS_FAILED_NON_BLOCKING,
)

CHAIN_AGENT_ORDER = (
    "jd_intelligence",
    "tailoring_suggestion",
    "critic_guardrail",
)

SUPPORTED_PIPELINE_HOOK_STAGES = (
    "post_filter_evaluation",
    "post_final_scoring",
    "pre_human_review",
)

OBSERVABILITY_STATUS_BY_CHAIN_STATUS = {
    STATUS_NOT_ENABLED: OBSERVED_STATUS_NOT_ENABLED,
    STATUS_SKIPPED_BY_CONFIG: OBSERVED_STATUS_SKIPPED_BY_CONFIG,
    STATUS_BLOCKED_BY_KILL_SWITCH: OBSERVED_STATUS_BLOCKED_BY_KILL_SWITCH,
    CHAIN_STATUS_COMPLETED_SHADOW_CHAIN: OBSERVED_STATUS_COMPLETED_SHADOW_CHAIN,
    STATUS_COMPLETED_WITH_FALLBACK: OBSERVED_STATUS_COMPLETED_WITH_FALLBACK,
    STATUS_FAILED_NON_BLOCKING: OBSERVED_STATUS_FAILED_NON_BLOCKING,
}

AGENT_FLAG_NAMES = {
    "jd_intelligence": JD_INTELLIGENCE_FLAG,
    "jd_intelligence_agent": JD_INTELLIGENCE_FLAG,
    "JD Intelligence Agent": JD_INTELLIGENCE_FLAG,
    "tailoring_suggestion": TAILORING_SUGGESTION_FLAG,
    "tailoring_suggestion_agent": TAILORING_SUGGESTION_FLAG,
    "Tailoring Suggestion Agent": TAILORING_SUGGESTION_FLAG,
    "critic_guardrail": CRITIC_GUARDRAIL_FLAG,
    "critic_guardrail_agent": CRITIC_GUARDRAIL_FLAG,
    "Critic / Guardrail Agent": CRITIC_GUARDRAIL_FLAG,
}

JD_AGENT_NAMES = {
    "jd_intelligence",
    "jd_intelligence_agent",
    "JD Intelligence Agent",
}

TAILORING_AGENT_NAMES = {
    "tailoring_suggestion",
    "tailoring_suggestion_agent",
    "Tailoring Suggestion Agent",
}

CRITIC_AGENT_NAMES = {
    "critic_guardrail",
    "critic_guardrail_agent",
    "Critic / Guardrail Agent",
}

JD_SIGNAL_FIELDS = (
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
    "seniority_indicators",
    "risk_flags",
)

TAILORING_SIGNAL_FIELDS = (
    "patch_ready_suggestions",
    "guidance_only_suggestions",
    "rejected_suggestions",
    "missing_evidence",
    "unsupported_claim_risks",
    "source_fields_used",
    "risk_flags",
)

CRITIC_SIGNAL_FIELDS = (
    "approved_suggestions",
    "downgraded_suggestions",
    "rejected_suggestions",
    "reason_codes",
    "unsupported_claim_risks",
    "ats_risks",
    "readability_risks",
    "evidence_gaps",
    "risk_flags",
)


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _snapshot(value: Any) -> Any:
    return deepcopy(value)


def _text_list(value: Any) -> list[str]:
    if not isinstance(value, (list, tuple)):
        return []
    return [_clean_text(item) for item in value if _clean_text(item)]


def _merged_text_list(*values: Any) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for value in values:
        for item in _text_list(value):
            if item not in seen:
                merged.append(item)
                seen.add(item)
    return merged


def _bool_value(value: Any, *, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    normalized = _clean_text(value).lower()
    if normalized in {"1", "true", "yes", "on", "enabled"}:
        return True
    if normalized in {"0", "false", "no", "off", "disabled"}:
        return False
    return default


def _config_bool(config: dict[str, Any], *keys: str, default: bool = False) -> bool:
    if not isinstance(config, dict):
        config = {}
    for key in keys:
        if key in config:
            return _bool_value(config.get(key), default=default)
    return default


def _agent_flag_name(agent_name: str) -> str:
    cleaned = _clean_text(agent_name)
    return AGENT_FLAG_NAMES.get(cleaned) or AGENT_FLAG_NAMES.get(cleaned.lower(), "")


def _is_jd_intelligence_agent(agent_name: str) -> bool:
    cleaned = _clean_text(agent_name)
    return cleaned in JD_AGENT_NAMES or cleaned.lower() in JD_AGENT_NAMES


def _is_tailoring_suggestion_agent(agent_name: str) -> bool:
    cleaned = _clean_text(agent_name)
    return cleaned in TAILORING_AGENT_NAMES or cleaned.lower() in TAILORING_AGENT_NAMES


def _is_critic_guardrail_agent(agent_name: str) -> bool:
    cleaned = _clean_text(agent_name)
    return cleaned in CRITIC_AGENT_NAMES or cleaned.lower() in CRITIC_AGENT_NAMES


def _agent_enabled(config: dict[str, Any], agent_name: str) -> bool:
    if not isinstance(config, dict):
        config = {}
    agent_flag_name = _agent_flag_name(agent_name)
    explicit = config.get("per_agent_enabled")
    if isinstance(explicit, dict):
        for key in {agent_name, _clean_text(agent_name).lower(), agent_flag_name}:
            if key in explicit:
                return _bool_value(explicit.get(key), default=False)
    if agent_flag_name:
        return _config_bool(config, agent_flag_name, default=False)
    return _config_bool(config, "agent_enabled", default=False)


def _sidecar_config(config: dict[str, Any] | None) -> dict[str, Any]:
    source = deepcopy(config) if isinstance(config, dict) else {}
    payload = {
        **source,
        "global_flag_name": GLOBAL_SIDECAR_FLAG,
        "jd_intelligence_flag_name": JD_INTELLIGENCE_FLAG,
        "tailoring_suggestion_flag_name": TAILORING_SUGGESTION_FLAG,
        "critic_guardrail_flag_name": CRITIC_GUARDRAIL_FLAG,
        "kill_switch_flag_name": KILL_SWITCH_FLAG,
        "provider_calls_disabled_in_tests": True,
        "pipeline_wiring_added": False,
    }
    return payload


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _jd_signal_refs(source: dict[str, Any]) -> list[str]:
    job_payload = _plain_dict(source.get("job_payload"))
    trace_context = _plain_dict(source.get("existing_trace_context"))
    explicit_refs = _merged_text_list(
        job_payload.get("jd_evidence_refs"),
        job_payload.get("evidence_refs"),
        trace_context.get("jd_evidence_refs"),
        trace_context.get("evidence_refs"),
    )
    if explicit_refs:
        return explicit_refs

    refs: list[str] = []
    for field_name in JD_SIGNAL_FIELDS:
        if _text_list(job_payload.get(field_name)) or _text_list(
            trace_context.get(field_name)
        ):
            refs.append(f"job_payload.{field_name}")
    if _clean_text(job_payload.get("description")) or _clean_text(
        job_payload.get("job_description")
    ):
        refs.append("job_payload.job_description")
    return refs


def _jd_reason_codes(source: dict[str, Any], fallback_reason_codes: Any) -> list[str]:
    job_payload = _plain_dict(source.get("job_payload"))
    trace_context = _plain_dict(source.get("existing_trace_context"))
    reason_codes = _merged_text_list(
        fallback_reason_codes,
        job_payload.get("jd_reason_codes"),
        job_payload.get("reason_codes"),
        trace_context.get("jd_reason_codes"),
        trace_context.get("reason_codes"),
    )
    if _jd_signal_refs(source):
        reason_codes.append("jd_shadow_signals_observed")
    if not reason_codes:
        reason_codes.append("jd_shadow_deterministic_fallback")
    return _merged_text_list(reason_codes)


def _jd_risk_flags(source: dict[str, Any]) -> list[str]:
    job_payload = _plain_dict(source.get("job_payload"))
    trace_context = _plain_dict(source.get("existing_trace_context"))
    return _merged_text_list(
        job_payload.get("jd_risk_flags"),
        job_payload.get("risk_flags"),
        trace_context.get("jd_risk_flags"),
        trace_context.get("risk_flags"),
    )


def _tailoring_signal_refs(source: dict[str, Any]) -> list[str]:
    job_payload = _plain_dict(source.get("job_payload"))
    resume_profile = _plain_dict(source.get("resume_profile_payload"))
    trace_context = _plain_dict(source.get("existing_trace_context"))
    explicit_refs = _merged_text_list(
        job_payload.get("tailoring_evidence_refs"),
        resume_profile.get("tailoring_evidence_refs"),
        trace_context.get("tailoring_evidence_refs"),
        job_payload.get("evidence_refs"),
        resume_profile.get("evidence_refs"),
        trace_context.get("evidence_refs"),
    )
    if explicit_refs:
        return explicit_refs

    refs: list[str] = []
    for field_name in TAILORING_SIGNAL_FIELDS:
        if (
            _text_list(job_payload.get(field_name))
            or _text_list(resume_profile.get(field_name))
            or _text_list(trace_context.get(field_name))
        ):
            refs.append(f"existing_trace_context.{field_name}")
    if _clean_text(resume_profile.get("resume_id")):
        refs.append("resume_profile_payload.resume_id")
    return refs


def _tailoring_reason_codes(
    source: dict[str, Any],
    fallback_reason_codes: Any,
) -> list[str]:
    job_payload = _plain_dict(source.get("job_payload"))
    resume_profile = _plain_dict(source.get("resume_profile_payload"))
    trace_context = _plain_dict(source.get("existing_trace_context"))
    reason_codes = _merged_text_list(
        fallback_reason_codes,
        job_payload.get("tailoring_reason_codes"),
        resume_profile.get("tailoring_reason_codes"),
        trace_context.get("tailoring_reason_codes"),
        job_payload.get("reason_codes"),
        trace_context.get("reason_codes"),
    )
    if _tailoring_signal_refs(source):
        reason_codes.append("tailoring_shadow_signals_observed")
    if not reason_codes:
        reason_codes.append("tailoring_shadow_deterministic_fallback")
    return _merged_text_list(reason_codes)


def _tailoring_risk_flags(source: dict[str, Any]) -> list[str]:
    job_payload = _plain_dict(source.get("job_payload"))
    resume_profile = _plain_dict(source.get("resume_profile_payload"))
    trace_context = _plain_dict(source.get("existing_trace_context"))
    return _merged_text_list(
        job_payload.get("tailoring_risk_flags"),
        resume_profile.get("tailoring_risk_flags"),
        trace_context.get("tailoring_risk_flags"),
        job_payload.get("unsupported_claim_risks"),
        trace_context.get("unsupported_claim_risks"),
        job_payload.get("risk_flags"),
        trace_context.get("risk_flags"),
    )


def _critic_signal_refs(source: dict[str, Any]) -> list[str]:
    job_payload = _plain_dict(source.get("job_payload"))
    resume_profile = _plain_dict(source.get("resume_profile_payload"))
    trace_context = _plain_dict(source.get("existing_trace_context"))
    explicit_refs = _merged_text_list(
        job_payload.get("critic_evidence_refs"),
        resume_profile.get("critic_evidence_refs"),
        trace_context.get("critic_evidence_refs"),
        job_payload.get("evidence_refs"),
        resume_profile.get("evidence_refs"),
        trace_context.get("evidence_refs"),
    )
    if explicit_refs:
        return explicit_refs

    refs: list[str] = []
    for field_name in CRITIC_SIGNAL_FIELDS:
        if (
            _text_list(job_payload.get(field_name))
            or _text_list(resume_profile.get(field_name))
            or _text_list(trace_context.get(field_name))
        ):
            refs.append(f"existing_trace_context.{field_name}")
    if _clean_text(resume_profile.get("resume_id")):
        refs.append("resume_profile_payload.resume_id")
    return refs


def _critic_reason_codes(
    source: dict[str, Any],
    fallback_reason_codes: Any,
) -> list[str]:
    job_payload = _plain_dict(source.get("job_payload"))
    resume_profile = _plain_dict(source.get("resume_profile_payload"))
    trace_context = _plain_dict(source.get("existing_trace_context"))
    reason_codes = _merged_text_list(
        fallback_reason_codes,
        job_payload.get("critic_reason_codes"),
        resume_profile.get("critic_reason_codes"),
        trace_context.get("critic_reason_codes"),
        job_payload.get("reason_codes"),
        trace_context.get("reason_codes"),
    )
    if _critic_signal_refs(source):
        reason_codes.append("critic_shadow_signals_observed")
    if not reason_codes:
        reason_codes.append("critic_shadow_deterministic_fallback")
    return _merged_text_list(reason_codes)


def _critic_risk_flags(source: dict[str, Any]) -> list[str]:
    job_payload = _plain_dict(source.get("job_payload"))
    resume_profile = _plain_dict(source.get("resume_profile_payload"))
    trace_context = _plain_dict(source.get("existing_trace_context"))
    return _merged_text_list(
        job_payload.get("critic_risk_flags"),
        resume_profile.get("critic_risk_flags"),
        trace_context.get("critic_risk_flags"),
        job_payload.get("unsupported_claim_risks"),
        trace_context.get("unsupported_claim_risks"),
        job_payload.get("ats_risks"),
        trace_context.get("ats_risks"),
        job_payload.get("readability_risks"),
        trace_context.get("readability_risks"),
        job_payload.get("risk_flags"),
        trace_context.get("risk_flags"),
    )


def _critic_blocking_findings(source: dict[str, Any]) -> list[str]:
    job_payload = _plain_dict(source.get("job_payload"))
    resume_profile = _plain_dict(source.get("resume_profile_payload"))
    trace_context = _plain_dict(source.get("existing_trace_context"))
    return _merged_text_list(
        job_payload.get("critic_blocking_findings"),
        resume_profile.get("critic_blocking_findings"),
        trace_context.get("critic_blocking_findings"),
        job_payload.get("evidence_gaps"),
        trace_context.get("evidence_gaps"),
        job_payload.get("blocking_findings"),
        trace_context.get("blocking_findings"),
    )


def evaluate_shadow_sidecar_safety(
    *,
    vector_evidence_input_available: bool = False,
    vector_evidence_input_attached: bool = False,
    semantic_evidence_input_available: bool = False,
    semantic_evidence_input_attached: bool = False,
    provider_calls_made: bool = False,
    embeddings_created: bool = False,
) -> dict[str, bool]:
    payload = {
        "read_only": True,
        "shadow_only": True,
        "manual_review_required": True,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_create_approval": False,
        "did_mutate_approval": False,
        "did_mutate_resume": False,
        "did_create_execution_request": False,
        "did_create_execution_launch_request": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "pipeline_wiring_added": False,
        "auto_apply_enabled": False,
        "vector_evidence_input_available": bool(
            vector_evidence_input_available
        ),
        "vector_evidence_input_attached": bool(
            vector_evidence_input_attached
        ),
        "vector_evidence_input_shadow_only": True,
        "vector_evidence_used_for_scoring": False,
        "vector_evidence_used_for_ranking": False,
        "vector_evidence_used_for_queue": False,
        "vector_evidence_used_for_application": False,
        "semantic_evidence_input_available": bool(
            semantic_evidence_input_available
        ),
        "semantic_evidence_input_attached": bool(
            semantic_evidence_input_attached
        ),
        "semantic_evidence_input_shadow_only": True,
        "semantic_evidence_used_for_scoring": False,
        "semantic_evidence_used_for_ranking": False,
        "semantic_evidence_used_for_queue": False,
        "semantic_evidence_used_for_application": False,
        "did_write_database": False,
        "provider_calls_made": bool(provider_calls_made),
        "embeddings_created": bool(embeddings_created),
    }
    return payload


def evaluate_shadow_sidecar_chain_safety() -> dict[str, bool]:
    return evaluate_shadow_sidecar_safety()


def evaluate_shadow_sidecar_chain_observability_safety() -> dict[str, bool]:
    safety = evaluate_shadow_sidecar_safety()
    safety["observability_only"] = True
    return safety


def evaluate_shadow_sidecar_pipeline_hook_safety() -> dict[str, bool]:
    safety = evaluate_shadow_sidecar_safety()
    safety["hook_preview_only"] = True
    return safety


def _vector_evidence_input(
    existing_trace_context: dict[str, Any] | None,
) -> dict[str, Any]:
    trace_context = _plain_dict(existing_trace_context)
    context = _plain_dict(trace_context.get("vector_evidence_context"))
    safety = _plain_dict(context.get("safety_metadata"))
    if not context or safety.get("vector_evidence_context_attached") is not True:
        return {}
    semantic_input = _plain_dict(context.get("semantic_evidence_context"))
    payload = {
        "status": _clean_text(context.get("status")),
        "hook_surface": _clean_text(context.get("hook_surface")),
        "run_id": _clean_text(context.get("run_id")),
        "job_id": _clean_text(context.get("job_id")),
        "stage_name": _clean_text(context.get("stage_name")),
        "evidence_context": _plain_dict(context.get("evidence_context")),
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "vector_evidence_input_available": True,
        "vector_evidence_input_attached": True,
        "vector_evidence_input_shadow_only": True,
        "vector_evidence_used_for_scoring": False,
        "vector_evidence_used_for_ranking": False,
        "vector_evidence_used_for_queue": False,
        "vector_evidence_used_for_application": False,
        "provider_calls_made": bool(context.get("provider_calls_made")),
        "embeddings_created": bool(context.get("embeddings_created")),
    }
    if semantic_input:
        payload["semantic_evidence_input"] = semantic_input
    return payload


def build_shadow_sidecar_input_payload(
    *,
    run_id: str = "",
    batch_id: str = "",
    job_id: str = "",
    stage_name: str = "",
    source_deterministic_stage: str = "",
    source_deterministic_status: str = "",
    source_deterministic_score: Any = None,
    source_deterministic_decision: str = "",
    source_deterministic_reason_codes: list[str] | tuple[str, ...] | None = None,
    job_payload: dict[str, Any] | None = None,
    resume_profile_payload: dict[str, Any] | None = None,
    existing_trace_context: dict[str, Any] | None = None,
    sidecar_config: dict[str, Any] | None = None,
    agent_name: str = "JD Intelligence Agent",
    started_at_utc: str = "",
    completed_at_utc: str = "",
    duration_ms: int = 0,
) -> dict[str, Any]:
    trace_context = _snapshot(existing_trace_context or {})
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": _clean_text(run_id),
        "batch_id": _clean_text(batch_id),
        "job_id": _clean_text(job_id),
        "stage_name": _clean_text(stage_name),
        "source_deterministic_stage": _clean_text(source_deterministic_stage),
        "source_deterministic_status": _clean_text(source_deterministic_status),
        "source_deterministic_score": source_deterministic_score,
        "source_deterministic_decision": _clean_text(source_deterministic_decision),
        "source_deterministic_reason_codes": _text_list(
            source_deterministic_reason_codes
        ),
        "job_payload": _snapshot(job_payload or {}),
        "resume_profile_payload": _snapshot(resume_profile_payload or {}),
        "existing_trace_context": trace_context,
        "sidecar_config": _sidecar_config(sidecar_config),
        "agent_name": _clean_text(agent_name) or "JD Intelligence Agent",
        "started_at_utc": _clean_text(started_at_utc),
        "completed_at_utc": _clean_text(completed_at_utc),
        "duration_ms": int(duration_ms or 0),
    }
    vector_input = _vector_evidence_input(trace_context)
    if vector_input:
        payload["vector_evidence_input"] = vector_input
    return payload


def build_shadow_sidecar_trace_payload(
    *,
    sidecar_input: dict[str, Any],
    sidecar_stage_status: str,
    agent_output_status: str = "",
    agent_recommendation: str = "",
    agent_confidence: float = 0.0,
    agent_reason_codes: list[str] | tuple[str, ...] | None = None,
    agent_evidence_refs: list[str] | tuple[str, ...] | None = None,
    agent_risk_flags: list[str] | tuple[str, ...] | None = None,
    agent_blocking_findings: list[str] | tuple[str, ...] | None = None,
    fallback_used: bool = False,
    error_type: str = "",
    error_message: str = "",
) -> dict[str, Any]:
    source = deepcopy(sidecar_input or {})
    config = _sidecar_config(source.get("sidecar_config"))
    status = _clean_text(sidecar_stage_status) or STATUS_NOT_ENABLED
    if status not in SIDECAR_STATUS_ENUM:
        status = STATUS_FAILED_NON_BLOCKING
        error_type = _clean_text(error_type) or "invalid_sidecar_stage_status"
    reason_codes = _text_list(agent_reason_codes)
    blocking_findings = _text_list(agent_blocking_findings)
    vector_input = _plain_dict(source.get("vector_evidence_input"))
    semantic_input = _plain_dict(
        vector_input.get("semantic_evidence_input")
    )
    health_status = "healthy" if status == STATUS_COMPLETED_SHADOW else "warning"
    readiness_status = "ready" if status == STATUS_COMPLETED_SHADOW else "blocked"
    trace_bundle = {
        "bundle_type": "shadow_sidecar_trace_bundle",
        "schema_version": SCHEMA_VERSION,
        "stage_name": _clean_text(source.get("stage_name")),
        "agent_name": _clean_text(source.get("agent_name")),
        "sidecar_stage_status": status,
        "source_deterministic_decision": _clean_text(
            source.get("source_deterministic_decision")
        ),
        "fallback_used": bool(fallback_used),
    }
    readiness_decision = {
        "readiness_status": readiness_status,
        "decision_reason_codes": reason_codes,
        "blocking_findings": blocking_findings,
        "warning_findings": [] if readiness_status == "ready" else reason_codes,
    }
    evidence_pack = {
        "evidence_pack_type": "shadow_sidecar_evidence_pack",
        "schema_version": SCHEMA_VERSION,
        "stage_name": _clean_text(source.get("stage_name")),
        "agent_name": _clean_text(source.get("agent_name")),
        "sidecar_stage_status": status,
        "source_deterministic_decision": _clean_text(
            source.get("source_deterministic_decision")
        ),
        "agent_evidence_refs": _text_list(agent_evidence_refs),
        "agent_risk_flags": _text_list(agent_risk_flags),
        "fallback_used": bool(fallback_used),
    }
    payload = {
        "schema_version": SCHEMA_VERSION,
        "run_id": _clean_text(source.get("run_id")),
        "batch_id": _clean_text(source.get("batch_id")),
        "job_id": _clean_text(source.get("job_id")),
        "stage_name": _clean_text(source.get("stage_name")),
        "agent_name": _clean_text(source.get("agent_name")),
        "agent_mode": "shadow_sidecar",
        "provider_mode": "disabled",
        "sidecar_enabled": status
        in {STATUS_COMPLETED_SHADOW, STATUS_COMPLETED_WITH_FALLBACK},
        "sidecar_stage_status": status,
        "started_at_utc": _clean_text(source.get("started_at_utc")),
        "completed_at_utc": _clean_text(source.get("completed_at_utc")),
        "duration_ms": int(source.get("duration_ms") or 0),
        "source_deterministic_stage": _clean_text(
            source.get("source_deterministic_stage")
        ),
        "source_deterministic_status": _clean_text(
            source.get("source_deterministic_status")
        ),
        "source_deterministic_score": source.get("source_deterministic_score"),
        "source_deterministic_decision": _clean_text(
            source.get("source_deterministic_decision")
        ),
        "source_deterministic_reason_codes": _text_list(
            source.get("source_deterministic_reason_codes")
        ),
        "agent_output_status": _clean_text(agent_output_status) or status,
        "agent_recommendation": _clean_text(agent_recommendation),
        "agent_confidence": float(agent_confidence or 0.0),
        "agent_reason_codes": reason_codes,
        "agent_evidence_refs": _text_list(agent_evidence_refs),
        "agent_risk_flags": _text_list(agent_risk_flags),
        "agent_blocking_findings": blocking_findings,
        "trace_bundle": trace_bundle,
        "evidence_pack": evidence_pack,
        "readiness_decision": readiness_decision,
        "health_status": health_status,
        "fallback_used": bool(fallback_used),
        "error_type": _clean_text(error_type),
        "error_message": _clean_text(error_message),
        "sidecar_config": config,
        "safety_metadata": evaluate_shadow_sidecar_safety(
            vector_evidence_input_available=bool(vector_input),
            vector_evidence_input_attached=bool(vector_input),
            semantic_evidence_input_available=bool(semantic_input),
            semantic_evidence_input_attached=bool(semantic_input),
            provider_calls_made=bool(
                semantic_input.get("provider_calls_made")
            ),
            embeddings_created=bool(
                semantic_input.get("embeddings_created")
            ),
        ),
    }
    if vector_input:
        payload["vector_evidence_input"] = vector_input
    if semantic_input:
        payload["semantic_evidence_input"] = semantic_input
    return payload


def build_shadow_sidecar_fallback_payload(
    *,
    sidecar_input: dict[str, Any],
    sidecar_stage_status: str = STATUS_COMPLETED_WITH_FALLBACK,
    reason_codes: list[str] | tuple[str, ...] | None = None,
    error_type: str = "",
    error_message: str = "",
) -> dict[str, Any]:
    source = deepcopy(sidecar_input or {})
    agent_name = _clean_text(source.get("agent_name"))
    if _is_jd_intelligence_agent(agent_name):
        return build_shadow_sidecar_trace_payload(
            sidecar_input=source,
            sidecar_stage_status=sidecar_stage_status,
            agent_output_status="fallback",
            agent_recommendation="preserve_source_deterministic_decision",
            agent_confidence=0.0,
            agent_reason_codes=_jd_reason_codes(source, reason_codes),
            agent_evidence_refs=_jd_signal_refs(source),
            agent_risk_flags=_jd_risk_flags(source),
            agent_blocking_findings=[],
            fallback_used=True,
            error_type=error_type,
            error_message=error_message,
        )
    if _is_tailoring_suggestion_agent(agent_name):
        return build_shadow_sidecar_trace_payload(
            sidecar_input=source,
            sidecar_stage_status=sidecar_stage_status,
            agent_output_status="fallback",
            agent_recommendation="preserve_source_deterministic_decision",
            agent_confidence=0.0,
            agent_reason_codes=_tailoring_reason_codes(source, reason_codes),
            agent_evidence_refs=_tailoring_signal_refs(source),
            agent_risk_flags=_tailoring_risk_flags(source),
            agent_blocking_findings=[],
            fallback_used=True,
            error_type=error_type,
            error_message=error_message,
        )
    if _is_critic_guardrail_agent(agent_name):
        return build_shadow_sidecar_trace_payload(
            sidecar_input=source,
            sidecar_stage_status=sidecar_stage_status,
            agent_output_status="fallback",
            agent_recommendation="preserve_source_deterministic_decision",
            agent_confidence=0.0,
            agent_reason_codes=_critic_reason_codes(source, reason_codes),
            agent_evidence_refs=_critic_signal_refs(source),
            agent_risk_flags=_critic_risk_flags(source),
            agent_blocking_findings=_critic_blocking_findings(source),
            fallback_used=True,
            error_type=error_type,
            error_message=error_message,
        )
    return build_shadow_sidecar_trace_payload(
        sidecar_input=source,
        sidecar_stage_status=sidecar_stage_status,
        agent_output_status="fallback",
        agent_recommendation="preserve_source_deterministic_decision",
        agent_confidence=0.0,
        agent_reason_codes=reason_codes or ["deterministic_fallback"],
        agent_evidence_refs=[],
        agent_risk_flags=[],
        agent_blocking_findings=[],
        fallback_used=True,
        error_type=error_type,
        error_message=error_message,
    )


def run_shadow_sidecar_agent(
    *,
    sidecar_input: dict[str, Any],
    shadow_agent: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
) -> dict[str, Any]:
    source = deepcopy(sidecar_input or {})
    config = _sidecar_config(source.get("sidecar_config"))
    agent_name = _clean_text(source.get("agent_name")) or "JD Intelligence Agent"
    kill_switch_enabled = _config_bool(
        config,
        KILL_SWITCH_FLAG,
        "kill_switch_enabled",
        default=False,
    )
    if kill_switch_enabled:
        return build_shadow_sidecar_fallback_payload(
            sidecar_input=source,
            sidecar_stage_status=STATUS_BLOCKED_BY_KILL_SWITCH,
            reason_codes=["blocked_by_kill_switch"],
        )

    global_enabled = _config_bool(
        config,
        GLOBAL_SIDECAR_FLAG,
        "sidecar_enabled",
        "global_enabled",
        default=False,
    )
    if not global_enabled:
        return build_shadow_sidecar_fallback_payload(
            sidecar_input=source,
            sidecar_stage_status=STATUS_NOT_ENABLED,
            reason_codes=["global_sidecar_flag_disabled"],
        )

    if not _agent_enabled(config, agent_name):
        return build_shadow_sidecar_fallback_payload(
            sidecar_input=source,
            sidecar_stage_status=STATUS_SKIPPED_BY_CONFIG,
            reason_codes=["per_agent_sidecar_flag_disabled"],
        )

    provider_execution_allowed = _config_bool(
        config,
        "provider_execution_allowed",
        "allow_provider_call",
        default=False,
    )
    if not provider_execution_allowed or shadow_agent is None:
        return build_shadow_sidecar_fallback_payload(
            sidecar_input=source,
            sidecar_stage_status=STATUS_COMPLETED_WITH_FALLBACK,
            reason_codes=["provider_execution_unavailable_or_disallowed"],
        )

    try:
        raw_result = shadow_agent(deepcopy(source))
    except Exception as exc:
        return build_shadow_sidecar_fallback_payload(
            sidecar_input=source,
            sidecar_stage_status=STATUS_FAILED_NON_BLOCKING,
            reason_codes=["shadow_agent_error"],
            error_type=exc.__class__.__name__,
            error_message=str(exc),
        )

    result = dict(raw_result or {}) if isinstance(raw_result, dict) else {}
    return build_shadow_sidecar_trace_payload(
        sidecar_input=source,
        sidecar_stage_status=STATUS_COMPLETED_SHADOW,
        agent_output_status=_clean_text(result.get("agent_output_status"))
        or STATUS_COMPLETED_SHADOW,
        agent_recommendation=_clean_text(result.get("agent_recommendation"))
        or "preserve_source_deterministic_decision",
        agent_confidence=float(result.get("agent_confidence") or 0.0),
        agent_reason_codes=_text_list(result.get("agent_reason_codes")),
        agent_evidence_refs=_text_list(result.get("agent_evidence_refs")),
        agent_risk_flags=_text_list(result.get("agent_risk_flags")),
        agent_blocking_findings=_text_list(result.get("agent_blocking_findings")),
        fallback_used=False,
    )


def _shadow_chain_agent_input(
    source: dict[str, Any],
    *,
    agent_name: str,
    config: dict[str, Any],
) -> dict[str, Any]:
    base_stage = _clean_text(source.get("stage_name")) or "shadow_sidecar_chain"
    return build_shadow_sidecar_input_payload(
        run_id=_clean_text(source.get("run_id")),
        batch_id=_clean_text(source.get("batch_id")),
        job_id=_clean_text(source.get("job_id")),
        stage_name=f"{base_stage}.{agent_name}",
        source_deterministic_stage=_clean_text(
            source.get("source_deterministic_stage")
        ),
        source_deterministic_status=_clean_text(
            source.get("source_deterministic_status")
        ),
        source_deterministic_score=source.get("source_deterministic_score"),
        source_deterministic_decision=_clean_text(
            source.get("source_deterministic_decision")
        ),
        source_deterministic_reason_codes=_text_list(
            source.get("source_deterministic_reason_codes")
        ),
        job_payload=_plain_dict(source.get("job_payload")),
        resume_profile_payload=_plain_dict(source.get("resume_profile_payload")),
        existing_trace_context=_plain_dict(source.get("existing_trace_context")),
        sidecar_config=config,
        agent_name=agent_name,
        started_at_utc=_clean_text(source.get("started_at_utc")),
        completed_at_utc=_clean_text(source.get("completed_at_utc")),
        duration_ms=int(source.get("duration_ms") or 0),
    )


def _shadow_chain_status(agent_results: list[dict[str, Any]]) -> str:
    statuses = [_clean_text(result.get("sidecar_stage_status")) for result in agent_results]
    if not statuses:
        return STATUS_SKIPPED_BY_CONFIG
    if any(status == STATUS_FAILED_NON_BLOCKING for status in statuses):
        return STATUS_FAILED_NON_BLOCKING
    if any(status == STATUS_COMPLETED_WITH_FALLBACK for status in statuses):
        return STATUS_COMPLETED_WITH_FALLBACK
    if all(status == STATUS_COMPLETED_SHADOW for status in statuses):
        return CHAIN_STATUS_COMPLETED_SHADOW_CHAIN
    return STATUS_COMPLETED_WITH_FALLBACK


def build_shadow_sidecar_chain_payload(
    *,
    sidecar_input: dict[str, Any],
    chain_status: str,
    agent_results: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
    reason_codes: list[str] | tuple[str, ...] | None = None,
    error_type: str = "",
    error_message: str = "",
) -> dict[str, Any]:
    source = deepcopy(sidecar_input or {})
    config = _sidecar_config(source.get("sidecar_config"))
    results = [deepcopy(result) for result in (agent_results or [])]
    status = _clean_text(chain_status) or STATUS_NOT_ENABLED
    if status not in set(SIDECAR_STATUS_ENUM) | {CHAIN_STATUS_COMPLETED_SHADOW_CHAIN}:
        status = STATUS_FAILED_NON_BLOCKING
        error_type = _clean_text(error_type) or "invalid_shadow_chain_status"
    ordered_names = [_clean_text(result.get("agent_name")) for result in results]
    stage_statuses = {
        _clean_text(result.get("agent_name")): _clean_text(
            result.get("sidecar_stage_status")
        )
        for result in results
    }
    all_reason_codes = _merged_text_list(
        reason_codes,
        *(result.get("agent_reason_codes") for result in results),
    )
    all_evidence_refs = _merged_text_list(
        *(result.get("agent_evidence_refs") for result in results),
    )
    all_risk_flags = _merged_text_list(
        *(result.get("agent_risk_flags") for result in results),
    )
    all_blocking_findings = _merged_text_list(
        *(result.get("agent_blocking_findings") for result in results),
    )
    fallback_used = bool(status != CHAIN_STATUS_COMPLETED_SHADOW_CHAIN) or any(
        bool(result.get("fallback_used")) for result in results
    )
    readiness_status = (
        "ready" if status == CHAIN_STATUS_COMPLETED_SHADOW_CHAIN else "blocked"
    )
    trace_bundle = {
        "bundle_type": "shadow_sidecar_chain_trace_bundle",
        "schema_version": SCHEMA_VERSION,
        "chain_status": status,
        "stage_order": ordered_names,
        "stage_statuses": stage_statuses,
        "source_deterministic_decision": _clean_text(
            source.get("source_deterministic_decision")
        ),
        "fallback_used": fallback_used,
    }
    evidence_pack = {
        "evidence_pack_type": "shadow_sidecar_chain_evidence_pack",
        "schema_version": SCHEMA_VERSION,
        "chain_status": status,
        "agent_evidence_refs": all_evidence_refs,
        "agent_risk_flags": all_risk_flags,
        "fallback_used": fallback_used,
    }
    readiness_decision = {
        "readiness_status": readiness_status,
        "decision_reason_codes": all_reason_codes,
        "blocking_findings": all_blocking_findings,
        "warning_findings": [] if readiness_status == "ready" else all_reason_codes,
    }
    workflow_enabled = _config_bool(
        config,
        THREE_AGENT_SHADOW_WORKFLOW_FLAG,
        "three_agent_shadow_workflow_enabled",
        default=False,
    )
    trace_context = _plain_dict(source.get("existing_trace_context"))
    vector_context = _plain_dict(trace_context.get("vector_evidence_context"))
    quality_gate = _plain_dict(
        vector_context.get("semantic_evidence_quality_gate")
    )
    workflow_safety = {
        "three_agent_shadow_workflow_enabled": workflow_enabled,
        "ordered_agent_count": len(results),
        "ordered_agent_names": ordered_names,
        "semantic_evidence_quality_gate_status": _clean_text(
            quality_gate.get("status")
        )
        or "semantic_evidence_quality_gate_not_enabled",
        "did_call_provider": False,
        "did_create_embeddings": False,
        "did_write_database": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_create_approval": False,
        "did_mutate_resume": False,
        "did_execute_application": False,
        "did_submit_application": False,
    }
    safety = evaluate_shadow_sidecar_chain_safety()
    safety.update(workflow_safety)
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": _clean_text(source.get("run_id")),
        "batch_id": _clean_text(source.get("batch_id")),
        "job_id": _clean_text(source.get("job_id")),
        "stage_name": _clean_text(source.get("stage_name")),
        "chain_status": status,
        "sidecar_chain_status": status,
        "chain_enabled": status
        in {CHAIN_STATUS_COMPLETED_SHADOW_CHAIN, STATUS_COMPLETED_WITH_FALLBACK},
        "provider_mode": "disabled",
        "stage_order": ordered_names,
        "stage_statuses": stage_statuses,
        "ordered_agent_results": results,
        "agent_results": results,
        "three_agent_shadow_workflow": deepcopy(workflow_safety),
        "source_deterministic_stage": _clean_text(
            source.get("source_deterministic_stage")
        ),
        "source_deterministic_status": _clean_text(
            source.get("source_deterministic_status")
        ),
        "source_deterministic_score": source.get("source_deterministic_score"),
        "source_deterministic_decision": _clean_text(
            source.get("source_deterministic_decision")
        ),
        "source_deterministic_reason_codes": _text_list(
            source.get("source_deterministic_reason_codes")
        ),
        "trace_bundle": trace_bundle,
        "evidence_pack": evidence_pack,
        "readiness_decision": readiness_decision,
        "health_status": "healthy"
        if status == CHAIN_STATUS_COMPLETED_SHADOW_CHAIN
        else "warning",
        "fallback_used": fallback_used,
        "error_type": _clean_text(error_type),
        "error_message": _clean_text(error_message),
        "sidecar_config": config,
        "safety_metadata": safety,
        "live_production_pipeline_connected_agents": 0,
        "live_agents_allowed_to_automate_mutations": 0,
    }


def run_shadow_sidecar_chain(
    *,
    sidecar_input: dict[str, Any],
) -> dict[str, Any]:
    source = deepcopy(sidecar_input or {})
    config = _sidecar_config(source.get("sidecar_config"))
    kill_switch_enabled = _config_bool(
        config,
        KILL_SWITCH_FLAG,
        "kill_switch_enabled",
        default=False,
    )
    if kill_switch_enabled:
        return build_shadow_sidecar_chain_payload(
            sidecar_input=source,
            chain_status=STATUS_BLOCKED_BY_KILL_SWITCH,
            reason_codes=["blocked_by_kill_switch"],
        )

    global_enabled = _config_bool(
        config,
        GLOBAL_SIDECAR_FLAG,
        "sidecar_enabled",
        "global_enabled",
        default=False,
    )
    if not global_enabled:
        return build_shadow_sidecar_chain_payload(
            sidecar_input=source,
            chain_status=STATUS_NOT_ENABLED,
            reason_codes=["global_sidecar_flag_disabled"],
        )

    enabled_agents = [
        agent_name for agent_name in CHAIN_AGENT_ORDER if _agent_enabled(config, agent_name)
    ]
    if not enabled_agents:
        return build_shadow_sidecar_chain_payload(
            sidecar_input=source,
            chain_status=STATUS_SKIPPED_BY_CONFIG,
            reason_codes=["per_agent_sidecar_flags_disabled"],
        )

    agent_results: list[dict[str, Any]] = []
    for agent_name in enabled_agents:
        agent_input = _shadow_chain_agent_input(
            source,
            agent_name=agent_name,
            config=config,
        )
        try:
            agent_results.append(run_shadow_sidecar_agent(sidecar_input=agent_input))
        except Exception as exc:
            agent_results.append(
                build_shadow_sidecar_fallback_payload(
                    sidecar_input=agent_input,
                    sidecar_stage_status=STATUS_FAILED_NON_BLOCKING,
                    reason_codes=["shadow_chain_stage_error"],
                    error_type=exc.__class__.__name__,
                    error_message=str(exc),
                )
            )

    return build_shadow_sidecar_chain_payload(
        sidecar_input=source,
        chain_status=_shadow_chain_status(agent_results),
        agent_results=agent_results,
    )


def build_shadow_sidecar_chain_evidence_summary(
    chain_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    source = deepcopy(chain_payload) if isinstance(chain_payload, dict) else {}
    evidence_pack = _plain_dict(source.get("evidence_pack"))
    agent_results = [
        deepcopy(result)
        for result in source.get("ordered_agent_results", source.get("agent_results", []))
        if isinstance(result, dict)
    ]
    evidence_refs = _merged_text_list(
        evidence_pack.get("agent_evidence_refs"),
        *(result.get("agent_evidence_refs") for result in agent_results),
    )
    risk_flags = _merged_text_list(
        evidence_pack.get("agent_risk_flags"),
        *(result.get("agent_risk_flags") for result in agent_results),
    )
    blocking_findings = _merged_text_list(
        _plain_dict(source.get("readiness_decision")).get("blocking_findings"),
        *(result.get("agent_blocking_findings") for result in agent_results),
    )
    return {
        "evidence_summary_type": "shadow_sidecar_chain_evidence_summary",
        "source_chain_status": _clean_text(
            source.get("chain_status") or source.get("sidecar_chain_status")
        ),
        "evidence_ref_count": len(evidence_refs),
        "risk_flag_count": len(risk_flags),
        "blocking_finding_count": len(blocking_findings),
        "agent_evidence_refs": evidence_refs,
        "agent_risk_flags": risk_flags,
        "blocking_findings": blocking_findings,
    }


def evaluate_shadow_sidecar_chain_readiness(
    chain_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    source = deepcopy(chain_payload) if isinstance(chain_payload, dict) else {}
    source_status = _clean_text(
        source.get("chain_status") or source.get("sidecar_chain_status")
    )
    readiness = _plain_dict(source.get("readiness_decision"))
    evidence_summary = build_shadow_sidecar_chain_evidence_summary(source)
    if not source:
        readiness_status = "blocked"
        reason_codes = ["missing_chain_payload"]
    elif source_status not in set(SIDECAR_STATUS_ENUM) | {
        CHAIN_STATUS_COMPLETED_SHADOW_CHAIN,
    }:
        readiness_status = "blocked"
        reason_codes = ["invalid_chain_payload"]
    else:
        readiness_status = _clean_text(readiness.get("readiness_status")) or (
            "ready" if source_status == CHAIN_STATUS_COMPLETED_SHADOW_CHAIN else "blocked"
        )
        reason_codes = _merged_text_list(
            readiness.get("decision_reason_codes"),
            ["fallback_observed"] if bool(source.get("fallback_used")) else [],
        )
    blocking_findings = _merged_text_list(
        readiness.get("blocking_findings"),
        evidence_summary.get("blocking_findings"),
    )
    return {
        "readiness_status": readiness_status,
        "decision_reason_codes": reason_codes,
        "blocking_findings": blocking_findings,
        "warning_findings": []
        if readiness_status == "ready"
        else _merged_text_list(readiness.get("warning_findings"), reason_codes),
    }


def build_shadow_sidecar_chain_observability_payload(
    chain_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    source = deepcopy(chain_payload) if isinstance(chain_payload, dict) else {}
    source_status = _clean_text(
        source.get("chain_status") or source.get("sidecar_chain_status")
    )
    if not source:
        observability_status = OBSERVED_STATUS_MISSING_SOURCE
    elif source_status not in set(SIDECAR_STATUS_ENUM) | {
        CHAIN_STATUS_COMPLETED_SHADOW_CHAIN,
    }:
        observability_status = OBSERVED_STATUS_INVALID_SOURCE
    else:
        observability_status = OBSERVABILITY_STATUS_BY_CHAIN_STATUS.get(
            source_status,
            OBSERVED_STATUS_INVALID_SOURCE,
        )

    agent_results = [
        deepcopy(result)
        for result in source.get("ordered_agent_results", source.get("agent_results", []))
        if isinstance(result, dict)
    ]
    ordered_agent_names = _text_list(source.get("stage_order")) or [
        _clean_text(result.get("agent_name")) for result in agent_results
    ]
    fallback_count = sum(1 for result in agent_results if bool(result.get("fallback_used")))
    risk_flag_count = sum(len(_text_list(result.get("agent_risk_flags"))) for result in agent_results)
    blocking_finding_count = sum(
        len(_text_list(result.get("agent_blocking_findings")))
        for result in agent_results
    )
    evidence_summary = build_shadow_sidecar_chain_evidence_summary(source)
    readiness_decision = evaluate_shadow_sidecar_chain_readiness(source)
    return {
        "schema_version": SCHEMA_VERSION,
        "observability_status": observability_status,
        "source_chain_status": source_status,
        "enabled_agent_count": len(agent_results),
        "ordered_agent_names": ordered_agent_names,
        "fallback_count": fallback_count,
        "risk_flag_count": risk_flag_count,
        "blocking_finding_count": blocking_finding_count,
        "readiness_decision": readiness_decision,
        "health_status": _clean_text(source.get("health_status")) or "warning",
        "evidence_summary": evidence_summary,
        "trace_bundle": {
            "bundle_type": "shadow_sidecar_chain_observability_trace_bundle",
            "schema_version": SCHEMA_VERSION,
            "observability_status": observability_status,
            "source_chain_status": source_status,
            "ordered_agent_names": ordered_agent_names,
            "fallback_count": fallback_count,
        },
        "source_deterministic_decision": _clean_text(
            source.get("source_deterministic_decision")
        ),
        "safety_metadata": evaluate_shadow_sidecar_chain_observability_safety(),
        "live_production_pipeline_connected_agents": 0,
        "live_agents_allowed_to_automate_mutations": 0,
    }


def _missing_pipeline_context_fields(context: dict[str, Any]) -> list[str]:
    required_fields = (
        "run_id",
        "batch_id",
        "job_id",
        "stage_name",
        "source_deterministic_stage",
        "source_deterministic_status",
        "source_deterministic_decision",
    )
    return [field for field in required_fields if not _clean_text(context.get(field))]


def evaluate_shadow_sidecar_pipeline_hook_eligibility(
    *,
    stage_name: str = "",
    sidecar_config: dict[str, Any] | None = None,
    pipeline_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = deepcopy(pipeline_context) if isinstance(pipeline_context, dict) else {}
    if stage_name:
        context["stage_name"] = stage_name
    config = _sidecar_config(sidecar_config)
    normalized_stage = _clean_text(context.get("stage_name"))
    missing_fields = _missing_pipeline_context_fields(context)
    enabled_agent_names = [
        agent_name for agent_name in CHAIN_AGENT_ORDER if _agent_enabled(config, agent_name)
    ]
    disabled_agent_names = [
        agent_name for agent_name in CHAIN_AGENT_ORDER if agent_name not in enabled_agent_names
    ]

    if missing_fields:
        status = HOOK_STATUS_BLOCKED_MISSING_CONTEXT
        next_safe_step = "provide_required_pipeline_context"
    elif _config_bool(config, KILL_SWITCH_FLAG, "kill_switch_enabled", default=False):
        status = HOOK_STATUS_BLOCKED_BY_KILL_SWITCH
        next_safe_step = "keep_shadow_sidecar_disabled"
    elif not _config_bool(
        config,
        GLOBAL_SIDECAR_FLAG,
        "sidecar_enabled",
        "global_enabled",
        default=False,
    ):
        status = HOOK_STATUS_NOT_ENABLED
        next_safe_step = "enable_global_shadow_sidecar_flag_for_preview_only"
    elif normalized_stage not in SUPPORTED_PIPELINE_HOOK_STAGES:
        status = HOOK_STATUS_BLOCKED_UNSUPPORTED_STAGE
        next_safe_step = "choose_supported_shadow_sidecar_hook_stage"
    elif not enabled_agent_names:
        status = HOOK_STATUS_SKIPPED_NO_ENABLED_AGENTS
        next_safe_step = "enable_at_least_one_shadow_sidecar_agent_flag"
    else:
        status = HOOK_STATUS_READY_FOR_SHADOW_SIDECAR
        next_safe_step = "future_hook_may_run_shadow_sidecar_chain_when_wired"

    return {
        "hook_preview_status": status,
        "stage_name": normalized_stage,
        "supported_stage": normalized_stage in SUPPORTED_PIPELINE_HOOK_STAGES,
        "supported_stages": list(SUPPORTED_PIPELINE_HOOK_STAGES),
        "enabled_agent_names": enabled_agent_names,
        "disabled_agent_names": disabled_agent_names,
        "missing_context_fields": missing_fields,
        "next_safe_step": next_safe_step,
    }


def build_shadow_sidecar_pipeline_hook_preview_payload(
    *,
    run_id: str = "",
    batch_id: str = "",
    job_id: str = "",
    stage_name: str = "",
    source_deterministic_stage: str = "",
    source_deterministic_status: str = "",
    source_deterministic_score: Any = None,
    source_deterministic_decision: str = "",
    source_deterministic_reason_codes: list[str] | tuple[str, ...] | None = None,
    sidecar_config: dict[str, Any] | None = None,
    job_payload: dict[str, Any] | None = None,
    resume_profile_payload: dict[str, Any] | None = None,
    existing_trace_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context = {
        "run_id": _clean_text(run_id),
        "batch_id": _clean_text(batch_id),
        "job_id": _clean_text(job_id),
        "stage_name": _clean_text(stage_name),
        "source_deterministic_stage": _clean_text(source_deterministic_stage),
        "source_deterministic_status": _clean_text(source_deterministic_status),
        "source_deterministic_score": source_deterministic_score,
        "source_deterministic_decision": _clean_text(source_deterministic_decision),
        "source_deterministic_reason_codes": _text_list(
            source_deterministic_reason_codes
        ),
        "job_payload": _snapshot(job_payload or {}),
        "resume_profile_payload": _snapshot(resume_profile_payload or {}),
        "existing_trace_context": _snapshot(existing_trace_context or {}),
    }
    config = _sidecar_config(sidecar_config)
    eligibility = evaluate_shadow_sidecar_pipeline_hook_eligibility(
        stage_name=stage_name,
        sidecar_config=config,
        pipeline_context=context,
    )
    return {
        "schema_version": SCHEMA_VERSION,
        **eligibility,
        "run_id": context["run_id"],
        "batch_id": context["batch_id"],
        "job_id": context["job_id"],
        "source_deterministic_stage": context["source_deterministic_stage"],
        "source_deterministic_status": context["source_deterministic_status"],
        "source_deterministic_score": context["source_deterministic_score"],
        "source_deterministic_decision": context["source_deterministic_decision"],
        "source_deterministic_reason_codes": context[
            "source_deterministic_reason_codes"
        ],
        "sidecar_config": config,
        "provider_calls_disabled_in_tests": True,
        "trace_bundle": {
            "bundle_type": "shadow_sidecar_pipeline_hook_preview_trace_bundle",
            "schema_version": SCHEMA_VERSION,
            "hook_preview_status": eligibility["hook_preview_status"],
            "stage_name": eligibility["stage_name"],
            "enabled_agent_names": eligibility["enabled_agent_names"],
            "source_deterministic_decision": context[
                "source_deterministic_decision"
            ],
        },
        "readiness_decision": {
            "readiness_status": "ready"
            if eligibility["hook_preview_status"] == HOOK_STATUS_READY_FOR_SHADOW_SIDECAR
            else "blocked",
            "decision_reason_codes": [eligibility["hook_preview_status"]],
            "blocking_findings": []
            if eligibility["hook_preview_status"] == HOOK_STATUS_READY_FOR_SHADOW_SIDECAR
            else [eligibility["next_safe_step"]],
            "warning_findings": [],
        },
        "safety_metadata": evaluate_shadow_sidecar_pipeline_hook_safety(),
        "live_production_pipeline_connected_agents": 0,
        "live_agents_allowed_to_automate_mutations": 0,
    }
