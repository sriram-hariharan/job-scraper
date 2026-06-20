"""Read-only normalization for existing JD live canary metadata."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


STATUS_SKIPPED = "jd_live_canary_readback_skipped_default_off"
STATUS_NO_DATA = "jd_live_canary_readback_no_data"
STATUS_NOT_ATTEMPTED = "jd_live_canary_readback_not_attempted"
STATUS_BLOCKED = "jd_live_canary_readback_blocked"
STATUS_SUCCEEDED = "jd_live_canary_readback_succeeded"
STATUS_FALLBACK = "jd_live_canary_readback_fallback"
STATUS_FAILED = "jd_live_canary_readback_failed"


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(float(str(value or "0").strip() or "0")))
    except (TypeError, ValueError):
        return 0


def _non_negative_float(value: Any) -> float:
    try:
        return max(0.0, float(str(value or "0").strip() or "0"))
    except (TypeError, ValueError):
        return 0.0


def jd_live_provider_canary_readback_safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "readback_only": True,
        "shadow_only": True,
        "provider_calls_made": False,
        "network_calls_made": False,
        "environment_secrets_read": False,
        "provider_client_constructed": False,
        "embeddings_created": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_write_files": False,
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
        "api_route_added": False,
        "ui_action_added": False,
        "service_bridge_added": False,
        "pipeline_stage_added": False,
        "mutation_authorized": False,
    }


def _jd_result(payload: dict[str, Any]) -> dict[str, Any]:
    chain = _plain_dict(payload.get("chain_payload"))
    if not chain and (
        "ordered_agent_results" in payload or "agent_results" in payload
    ):
        chain = payload
    results = chain.get("ordered_agent_results")
    if not isinstance(results, list):
        results = chain.get("agent_results")
    if isinstance(results, list):
        for result_value in results:
            result = _plain_dict(result_value)
            if _clean_text(result.get("agent_name")) == "jd_intelligence":
                return result
    if _clean_text(payload.get("agent_name")) == "jd_intelligence":
        return payload
    return {}


def _source_metadata(
    payload: dict[str, Any],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    if (
        "canary_status" in payload
        or "canary_enabled" in payload
        or "config_gate" in payload
    ):
        return (
            payload,
            _plain_dict(payload.get("llmops_metadata")),
            _plain_dict(payload.get("safety_metadata")),
            _plain_dict(payload.get("jd_intelligence_output")),
        )

    result = _jd_result(payload)
    output = _plain_dict(result.get("agent_output_payload"))
    trace = _plain_dict(result.get("llmops_trace_metadata"))
    safety = _plain_dict(result.get("safety_metadata"))
    output_metadata = _plain_dict(output.get("provider_metadata"))
    if not trace:
        trace = output_metadata
    canary = {
        "canary_status": (
            trace.get("jd_live_provider_canary_status")
            or output_metadata.get("jd_live_provider_canary_status")
        ),
        "canary_enabled": (
            trace.get("jd_live_provider_canary_enabled") is True
            or safety.get("jd_live_provider_canary_enabled") is True
        ),
        "canary_allowed": (
            trace.get("jd_live_provider_canary_allowed") is True
            or safety.get("jd_live_provider_canary_allowed") is True
        ),
        "canary_attempted": (
            trace.get("jd_live_provider_canary_attempted") is True
            or safety.get("jd_live_provider_canary_attempted") is True
        ),
        "provider_call_attempted": (
            trace.get("provider_call_attempted") is True
            or trace.get("provider_call_made") is True
        ),
        "provider_call_succeeded": (
            trace.get("provider_call_succeeded") is True
            or safety.get("jd_live_provider_canary_succeeded") is True
        ),
        "provider_call_failed": (
            safety.get("jd_live_provider_canary_attempted") is True
            and safety.get("jd_live_provider_canary_succeeded") is not True
        ),
        "fallback_used": (
            trace.get("fallback_used") is True
            or safety.get("jd_live_provider_canary_fallback") is True
            or output.get("fallback_used") is True
        ),
        "fallback_reason": (
            safety.get("jd_live_provider_canary_fallback_reason")
        ),
        "structured_output_validated": (
            trace.get("schema_validation_status") == "valid"
            or output.get("validation_status") == "valid"
        ),
        "shadow_only": safety.get("shadow_only", True) is True,
        "provider_name": (
            trace.get("model_provider")
            or output.get("model_provider")
        ),
        "model_name": (
            trace.get("model_name") or output.get("model_name")
        ),
        "prompt_version": (
            trace.get("prompt_version") or output.get("prompt_version")
        ),
        "runtime_version": trace.get("runtime_version"),
    }
    return canary, trace, safety, output


def build_jd_live_provider_canary_readback(
    *,
    payload: dict[str, Any] | None = None,
    enabled: bool = False,
) -> dict[str, Any]:
    """Summarize existing canary metadata without executing the canary."""

    source = _plain_dict(payload)
    base = {
        "readback_enabled": enabled is True,
        "readback_status": STATUS_SKIPPED,
        "canary_configured": False,
        "canary_allowed": False,
        "canary_attempted": False,
        "provider_call_attempted": False,
        "provider_call_succeeded": False,
        "provider_call_failed": False,
        "fallback_used": False,
        "fallback_reason": "",
        "structured_output_validated": False,
        "shadow_only": True,
        "provider_name": "",
        "model_name": "",
        "prompt_version": "",
        "runtime_version": "",
        "llmops_metadata_present": False,
        "latency_ms": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "estimated_cost": 0.0,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "influence_disabled": {
            "scoring": True,
            "ranking": True,
            "queue": True,
            "resume": True,
            "execution": True,
            "submission": True,
        },
        "next_safe_step": "enable_jd_live_canary_readback_only",
        "safety_metadata": (
            jd_live_provider_canary_readback_safety_metadata()
        ),
    }
    if enabled is not True:
        return base
    if not source:
        return {
            **base,
            "readback_enabled": True,
            "readback_status": STATUS_NO_DATA,
            "next_safe_step": "supply_existing_jd_canary_metadata",
        }

    canary, trace, source_safety, output = _source_metadata(source)
    configured = canary.get("canary_enabled") is True
    allowed = canary.get("canary_allowed") is True
    attempted = (
        canary.get("canary_attempted") is True
        or canary.get("provider_call_attempted") is True
    )
    call_attempted = (
        canary.get("provider_call_attempted") is True
        or trace.get("provider_call_attempted") is True
        or trace.get("provider_call_made") is True
    )
    call_succeeded = (
        canary.get("provider_call_succeeded") is True
        or trace.get("provider_call_succeeded") is True
    )
    validated = (
        canary.get("structured_output_validated") is True
        or trace.get("schema_validation_status") == "valid"
        or output.get("validation_status") == "valid"
    )
    fallback_used = (
        canary.get("fallback_used") is True
        or trace.get("fallback_used") is True
        or output.get("fallback_used") is True
        or source_safety.get("jd_live_provider_canary_fallback") is True
    )
    failed = (
        canary.get("provider_call_failed") is True
        or (call_attempted and not call_succeeded)
        or (call_attempted and not validated)
    )
    fallback_reason = _clean_text(canary.get("fallback_reason"))
    if not fallback_reason:
        fallback_reason = _clean_text(
            source_safety.get(
                "jd_live_provider_canary_fallback_reason"
            )
            or trace.get("error_type")
        )
    if not fallback_reason:
        errors = output.get("validation_errors")
        if isinstance(errors, list) and errors:
            fallback_reason = _clean_text(errors[0])

    status = STATUS_NOT_ATTEMPTED
    next_safe_step = "keep_jd_live_canary_default_off"
    canary_status = _clean_text(canary.get("canary_status"))
    if not configured and not canary_status:
        status = STATUS_NO_DATA
        next_safe_step = "supply_existing_jd_canary_metadata"
    elif not attempted and (fallback_used or "blocked" in canary_status):
        status = STATUS_BLOCKED
        next_safe_step = "resolve_canary_gate_or_adapter_blocker"
    elif call_succeeded and validated and not fallback_used:
        status = STATUS_SUCCEEDED
        next_safe_step = "audit_shadow_canary_before_any_expansion"
    elif fallback_used:
        status = STATUS_FALLBACK
        next_safe_step = "inspect_fallback_and_keep_canary_default_off"
    elif failed:
        status = STATUS_FAILED
        next_safe_step = "inspect_canary_failure_and_keep_canary_off"

    provider_name = _clean_text(
        canary.get("provider_name") or trace.get("model_provider")
    )
    model_name = _clean_text(
        canary.get("model_name") or trace.get("model_name")
    )
    prompt_version = _clean_text(
        canary.get("prompt_version") or trace.get("prompt_version")
    )
    runtime_version = _clean_text(
        canary.get("runtime_version") or trace.get("runtime_version")
    )
    shadow_only = (
        canary.get("shadow_only", True) is True
        and source_safety.get("shadow_only", True) is True
    )
    return {
        **base,
        "readback_enabled": True,
        "readback_status": status,
        "source_canary_status": canary_status,
        "canary_configured": configured,
        "canary_allowed": allowed,
        "canary_attempted": attempted,
        "provider_call_attempted": call_attempted,
        "provider_call_succeeded": (
            call_succeeded and validated and not fallback_used
        ),
        "provider_call_failed": failed,
        "fallback_used": fallback_used,
        "fallback_reason": fallback_reason if fallback_used else "",
        "structured_output_validated": validated,
        "shadow_only": shadow_only,
        "provider_name": provider_name,
        "model_name": model_name,
        "prompt_version": prompt_version,
        "runtime_version": runtime_version,
        "llmops_metadata_present": bool(trace),
        "latency_ms": _non_negative_int(trace.get("latency_ms")),
        "input_tokens": _non_negative_int(trace.get("input_tokens")),
        "output_tokens": _non_negative_int(trace.get("output_tokens")),
        "total_tokens": _non_negative_int(trace.get("total_tokens")),
        "estimated_cost": _non_negative_float(
            trace.get("estimated_cost")
        ),
        "source_llmops_metadata": trace,
        "source_validation_status": _clean_text(
            trace.get("schema_validation_status")
            or output.get("validation_status")
        ),
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "next_safe_step": next_safe_step,
    }


def build_jd_live_provider_canary_readback_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    return build_jd_live_provider_canary_readback(**kwargs)
