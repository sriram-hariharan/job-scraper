"""Read-only trace summary for JD provider runtime activation metadata."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


STATUS_SKIPPED = "jd_provider_runtime_readback_skipped_default_off"
STATUS_NO_DATA = "jd_provider_runtime_readback_no_data"
STATUS_NOT_ATTEMPTED = "jd_provider_runtime_readback_not_attempted"
STATUS_BLOCKED = "jd_provider_runtime_readback_blocked"
STATUS_SUCCEEDED = "jd_provider_runtime_readback_succeeded"
STATUS_VALIDATION_FAILED = (
    "jd_provider_runtime_readback_validation_failed"
)
STATUS_FAILED = "jd_provider_runtime_readback_failed"


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "readback_only": True,
        "shadow_only": True,
        "provider_calls_made": False,
        "network_calls_made": False,
        "embeddings_created": False,
        "did_read_database": False,
        "did_write_database": False,
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


def _jd_result_from_payload(
    payload: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    chain = _plain_dict(payload.get("chain_payload"))
    if not chain and "ordered_agent_results" in payload:
        chain = payload
    results = chain.get("ordered_agent_results")
    if not isinstance(results, list):
        results = chain.get("agent_results")
    if isinstance(results, list):
        for result_value in results:
            result = _plain_dict(result_value)
            if _clean_text(result.get("agent_name")) == "jd_intelligence":
                return result, chain
    if _clean_text(payload.get("agent_name")) == "jd_intelligence":
        return payload, {}
    return {}, chain


def _source_metadata(
    payload: dict[str, Any],
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    if (
        "jd_intelligence_output" in payload
        or "provider_runtime_metadata" in payload
    ):
        return (
            payload,
            _plain_dict(payload.get("llmops_trace_metadata")),
            _plain_dict(payload.get("safety_metadata")),
            _plain_dict(payload.get("jd_intelligence_output")),
        )

    result, _chain = _jd_result_from_payload(payload)
    output = _plain_dict(result.get("agent_output_payload"))
    trace = _plain_dict(result.get("llmops_trace_metadata"))
    safety = _plain_dict(result.get("safety_metadata"))
    provider_metadata = _plain_dict(result.get("provider_metadata"))
    if not trace:
        trace = _plain_dict(output.get("provider_metadata"))
    if not provider_metadata:
        provider_metadata = _plain_dict(output.get("provider_metadata"))
    activation = {
        "status": (
            trace.get("jd_provider_runtime_activation_status")
            or provider_metadata.get(
                "jd_provider_runtime_activation_status"
            )
        ),
        "activation_enabled": (
            safety.get("jd_provider_runtime_activation_enabled") is True
            or trace.get("jd_provider_runtime_activation_enabled") is True
        ),
        "shadow_only": safety.get("shadow_only", True) is True,
        "fallback_used": (
            trace.get("fallback_used") is True
            or result.get("fallback_used") is True
        ),
    }
    return activation, trace, safety, output


def _fallback_reason(
    activation: dict[str, Any],
    trace: dict[str, Any],
    output: dict[str, Any],
) -> str:
    error_type = _clean_text(trace.get("error_type"))
    if error_type:
        return error_type
    errors = output.get("validation_errors")
    if isinstance(errors, list) and errors:
        return _clean_text(errors[0])
    return _clean_text(activation.get("status"))


def build_jd_provider_runtime_trace_readback(
    *,
    payload: dict[str, Any] | None = None,
    enabled: bool = False,
) -> dict[str, Any]:
    """Summarize existing JD activation metadata without executing anything."""

    source = _plain_dict(payload)
    base = {
        "readback_enabled": enabled is True,
        "readback_status": STATUS_SKIPPED,
        "jd_provider_runtime_enabled": False,
        "jd_provider_runtime_attempted": False,
        "jd_provider_runtime_succeeded": False,
        "jd_provider_runtime_failed": False,
        "fallback_used": False,
        "fallback_reason": "",
        "shadow_only": True,
        "provider_calls_allowed": False,
        "configured_provider_name": "",
        "configured_model_name": "",
        "llmops_metadata_present": False,
        "structured_output_validated": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "next_safe_step": "enable_jd_provider_runtime_readback_only",
        "safety_metadata": _safety_metadata(),
    }
    if enabled is not True:
        return base
    if not source:
        return {
            **base,
            "readback_enabled": True,
            "readback_status": STATUS_NO_DATA,
            "next_safe_step": "supply_existing_jd_shadow_metadata",
        }

    activation, trace, source_safety, output = _source_metadata(source)
    activation_enabled = (
        activation.get("activation_enabled") is True
        or source_safety.get(
            "jd_provider_runtime_activation_enabled"
        )
        is True
        or trace.get("jd_provider_runtime_activation_enabled") is True
    )
    attempted = (
        trace.get("provider_call_attempted") is True
        or source_safety.get(
            "jd_provider_runtime_activation_attempted"
        )
        is True
    )
    succeeded = (
        trace.get("provider_call_succeeded") is True
        or source_safety.get(
            "jd_provider_runtime_activation_succeeded"
        )
        is True
    )
    blocked = trace.get("provider_call_blocked") is True
    validation_status = _clean_text(
        trace.get("schema_validation_status")
        or output.get("validation_status")
    )
    validated = validation_status == "valid"
    fallback_used = (
        activation.get("fallback_used") is True
        or trace.get("fallback_used") is True
        or output.get("fallback_used") is True
        or source_safety.get(
            "jd_provider_runtime_activation_fallback"
        )
        is True
    )
    failed = attempted and not succeeded

    status = STATUS_NOT_ATTEMPTED
    next_safe_step = "keep_jd_provider_runtime_default_off"
    if blocked and not attempted:
        status = STATUS_BLOCKED
        next_safe_step = "inject_test_runtime_client_for_shadow_smoke"
    elif succeeded and validated:
        status = STATUS_SUCCEEDED
        next_safe_step = "review_shadow_output_and_llmops_metadata"
    elif attempted and validation_status == "invalid":
        status = STATUS_VALIDATION_FAILED
        next_safe_step = "fix_structured_output_before_retry"
    elif failed:
        status = STATUS_FAILED
        next_safe_step = "inspect_failure_and_keep_fallback_enabled"

    provider_name = _clean_text(
        trace.get("model_provider")
        or output.get("model_provider")
    )
    model_name = _clean_text(
        trace.get("model_name") or output.get("model_name")
    )
    return {
        **base,
        "readback_enabled": True,
        "readback_status": status,
        "jd_provider_runtime_enabled": activation_enabled,
        "jd_provider_runtime_attempted": attempted,
        "jd_provider_runtime_succeeded": succeeded and validated,
        "jd_provider_runtime_failed": failed or (
            attempted and not validated
        ),
        "fallback_used": fallback_used,
        "fallback_reason": (
            _fallback_reason(activation, trace, output)
            if fallback_used
            else ""
        ),
        "shadow_only": (
            activation.get("shadow_only", True) is True
            and source_safety.get("shadow_only", True) is True
        ),
        "provider_calls_allowed": activation_enabled,
        "configured_provider_name": provider_name,
        "configured_model_name": model_name,
        "llmops_metadata_present": bool(trace),
        "structured_output_validated": validated,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "next_safe_step": next_safe_step,
        "source_llmops_metadata": trace,
        "source_validation_status": validation_status,
        "safety_metadata": _safety_metadata(),
    }


def build_jd_provider_runtime_trace_readback_helper_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    return build_jd_provider_runtime_trace_readback(**kwargs)
