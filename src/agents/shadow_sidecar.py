from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable


SCHEMA_VERSION = "phase5_shadow_sidecar_trace_v1"

GLOBAL_SIDECAR_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
JD_INTELLIGENCE_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED"
TAILORING_SUGGESTION_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED"
CRITIC_GUARDRAIL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED"
KILL_SWITCH_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"

STATUS_NOT_ENABLED = "not_enabled"
STATUS_SKIPPED_BY_CONFIG = "skipped_by_config"
STATUS_COMPLETED_SHADOW = "completed_shadow"
STATUS_COMPLETED_WITH_FALLBACK = "completed_with_fallback"
STATUS_BLOCKED_BY_KILL_SWITCH = "blocked_by_kill_switch"
STATUS_FAILED_NON_BLOCKING = "failed_non_blocking"

SIDECAR_STATUS_ENUM = (
    STATUS_NOT_ENABLED,
    STATUS_SKIPPED_BY_CONFIG,
    STATUS_COMPLETED_SHADOW,
    STATUS_COMPLETED_WITH_FALLBACK,
    STATUS_BLOCKED_BY_KILL_SWITCH,
    STATUS_FAILED_NON_BLOCKING,
)

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


def _agent_enabled(config: dict[str, Any], agent_name: str) -> bool:
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
    return {
        **source,
        "global_flag_name": GLOBAL_SIDECAR_FLAG,
        "jd_intelligence_flag_name": JD_INTELLIGENCE_FLAG,
        "tailoring_suggestion_flag_name": TAILORING_SUGGESTION_FLAG,
        "critic_guardrail_flag_name": CRITIC_GUARDRAIL_FLAG,
        "kill_switch_flag_name": KILL_SWITCH_FLAG,
        "provider_calls_disabled_in_tests": True,
        "pipeline_wiring_added": False,
    }


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


def evaluate_shadow_sidecar_safety() -> dict[str, bool]:
    return {
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
    }


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
    return {
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
        "existing_trace_context": _snapshot(existing_trace_context or {}),
        "sidecar_config": _sidecar_config(sidecar_config),
        "agent_name": _clean_text(agent_name) or "JD Intelligence Agent",
        "started_at_utc": _clean_text(started_at_utc),
        "completed_at_utc": _clean_text(completed_at_utc),
        "duration_ms": int(duration_ms or 0),
    }


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
    return {
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
        "safety_metadata": evaluate_shadow_sidecar_safety(),
    }


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
