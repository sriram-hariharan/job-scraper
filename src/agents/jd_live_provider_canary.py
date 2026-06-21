"""Config-gated JD live-provider canary using injection only."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from src.agents.jd_intelligence import (
    build_live_jd_intelligence_dry_run_payload,
)
from src.agents.provider_live_config_gate import (
    evaluate_provider_live_config_gate,
)


CANARY_VERSION = "phase-13c-jd-live-provider-canary-v1"
STATUS_SKIPPED = "jd_live_canary_skipped_default_off"
STATUS_BLOCKED = "jd_live_canary_blocked"
STATUS_SUCCEEDED = "jd_live_canary_succeeded_shadow_only"
STATUS_FALLBACK = "jd_live_canary_fallback"
DEFERRED_AGENTS = ("tailoring_suggestion", "critic_guardrail")


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


def _fallback_output(
    *,
    fallback_input: dict[str, Any] | None,
    reason: str,
) -> dict[str, Any]:
    source = _plain_dict(fallback_input)
    if not source:
        payload = build_live_jd_intelligence_dry_run_payload(
            feature_enabled=False,
        )
    else:
        payload = build_live_jd_intelligence_dry_run_payload(
            adapter=lambda _request: deepcopy(source),
            feature_enabled=True,
        )
        payload["safety_metadata"]["did_call_llm"] = False
    payload["validation_status"] = "fallback"
    payload["validation_errors"] = [reason]
    payload["fallback_used"] = True
    payload["model_provider"] = "deterministic"
    payload["model_name"] = "jd_live_canary_fallback"
    payload["token_usage"] = {}
    payload["cost"] = {}
    payload["latency_ms"] = 0
    return payload


def _provider_output(raw_response: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    raw = _plain_dict(raw_response)
    output = raw.get("output")
    if not isinstance(output, dict):
        output = raw.get("content")
    if not isinstance(output, dict):
        output = raw.get("raw_response")
    if not isinstance(output, dict):
        output = {
            key: deepcopy(value)
            for key, value in raw.items()
            if key
            not in {
                "provider_name",
                "provider",
                "model_name",
                "model",
                "latency_ms",
                "token_usage",
                "token_usage_json",
                "cost",
                "cost_json",
                "estimated_cost",
                "error_type",
                "schema_validation_status",
                "validation_status",
                "fallback_used",
            }
        }
    token_usage = _plain_dict(
        raw.get("token_usage") or raw.get("token_usage_json")
    )
    cost = _plain_dict(raw.get("cost") or raw.get("cost_json"))
    input_tokens = _non_negative_int(
        token_usage.get(
            "input_tokens",
            token_usage.get("input_token_count", 0),
        )
    )
    output_tokens = _non_negative_int(
        token_usage.get(
            "output_tokens",
            token_usage.get("output_token_count", 0),
        )
    )
    metadata = {
        "latency_ms": _non_negative_int(raw.get("latency_ms")),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": _non_negative_int(
            token_usage.get(
                "total_tokens",
                token_usage.get(
                    "total_token_count",
                    input_tokens + output_tokens,
                ),
            )
        ),
        "estimated_cost": _non_negative_float(
            cost.get(
                "estimated_cost",
                cost.get("usd", raw.get("estimated_cost", 0)),
            )
        ),
        "error_type": _clean_text(raw.get("error_type")),
    }
    return deepcopy(output), metadata


def _llmops_metadata(
    *,
    config: dict[str, Any],
    provider_call_attempted: bool,
    provider_call_succeeded: bool,
    fallback_used: bool,
    validation_status: str,
    adapter_metadata: dict[str, Any] | None = None,
    error_type: str = "",
) -> dict[str, Any]:
    metadata = _plain_dict(adapter_metadata)
    return {
        "agent_name": "jd_intelligence",
        "agent_version": "jd-live-provider-canary-v1",
        "prompt_version": _clean_text(config.get("prompt_version")),
        "runtime_version": _clean_text(config.get("runtime_version")),
        "model_provider": _clean_text(config.get("provider_name")),
        "model_name": _clean_text(config.get("model_name")),
        "provider_call_attempted": provider_call_attempted,
        "provider_call_made": provider_call_attempted,
        "provider_call_succeeded": provider_call_succeeded,
        "fallback_used": fallback_used,
        "schema_validation_status": validation_status,
        "error_type": _clean_text(error_type or metadata.get("error_type")),
        "latency_ms": _non_negative_int(metadata.get("latency_ms")),
        "input_tokens": _non_negative_int(metadata.get("input_tokens")),
        "output_tokens": _non_negative_int(metadata.get("output_tokens")),
        "total_tokens": _non_negative_int(metadata.get("total_tokens")),
        "estimated_cost": _non_negative_float(
            metadata.get("estimated_cost")
        ),
        "retry_count": 0,
    }


def _limit_violation(
    *,
    gate: dict[str, Any],
    adapter_metadata: dict[str, Any],
) -> str:
    runtime = _plain_dict(gate.get("runtime_limits"))
    budget = _plain_dict(gate.get("budget_limits"))
    limits = (
        (
            "latency_ms",
            _non_negative_float(runtime.get("timeout_seconds")) * 1000,
            "provider_timeout_budget_exceeded",
        ),
        (
            "input_tokens",
            _non_negative_float(budget.get("max_input_tokens")),
            "provider_input_token_budget_exceeded",
        ),
        (
            "output_tokens",
            _non_negative_float(budget.get("max_output_tokens")),
            "provider_output_token_budget_exceeded",
        ),
        (
            "estimated_cost",
            _non_negative_float(budget.get("max_estimated_cost")),
            "provider_cost_budget_exceeded",
        ),
    )
    for metadata_key, configured_limit, reason in limits:
        actual = _non_negative_float(adapter_metadata.get(metadata_key))
        if configured_limit > 0 and actual > configured_limit:
            return reason
    return ""


def jd_live_provider_canary_safety_metadata(
    *,
    provider_calls_made: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "jd_intelligence_only": True,
        "config_gate_required": True,
        "provider_calls_made": bool(provider_calls_made),
        "network_calls_made_by_repository": False,
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
        "did_write_resume_draft": False,
        "did_write_cover_letter_draft": False,
        "did_create_execution_request": False,
        "did_create_execution_launch_request": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "api_route_added": False,
        "ui_action_added": False,
        "service_behavior_added": False,
        "pipeline_stage_added": False,
        "mutation_authorized": False,
    }


def run_jd_live_provider_canary(
    *,
    enabled: bool = False,
    job_payload: dict[str, Any] | None = None,
    live_config: dict[str, Any] | None = None,
    provider_adapter: Callable[[dict[str, Any]], Any] | None = None,
    deterministic_fallback_input: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run one injected JD canary only after the Phase 13B gate allows it."""

    job = _plain_dict(job_payload)
    config = _plain_dict(live_config)
    gate = _plain_dict(
        evaluate_provider_live_config_gate(
            enabled=enabled is True,
            config=deepcopy(config),
        )
    )
    allowed = (
        gate.get("canary_allowed") is True
        and gate.get("provider_calls_allowed") is True
        and gate.get("agent_name") == "jd_intelligence"
        and gate.get("shadow_only") is True
    )
    provider_name = _clean_text(gate.get("provider_name"))
    model_name = _clean_text(gate.get("model_name"))
    prompt_version = _clean_text(gate.get("prompt_version"))
    runtime_version = _clean_text(gate.get("runtime_version"))

    base = {
        "canary_version": CANARY_VERSION,
        "canary_status": (
            STATUS_SKIPPED if enabled is not True else STATUS_BLOCKED
        ),
        "canary_enabled": enabled is True,
        "canary_attempted": False,
        "canary_allowed": allowed,
        "config_gate": gate,
        "provider_call_attempted": False,
        "provider_call_succeeded": False,
        "provider_call_failed": False,
        "fallback_used": True,
        "fallback_reason": "",
        "structured_output_validated": False,
        "shadow_only": True,
        "activated_agent_name": "jd_intelligence",
        "deferred_agent_names": list(DEFERRED_AGENTS),
        "provider_name": provider_name,
        "model_name": model_name,
        "prompt_version": prompt_version,
        "runtime_version": runtime_version,
        "jd_intelligence_output": {},
        "llmops_metadata": {},
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "next_safe_step": "",
        "safety_metadata": jd_live_provider_canary_safety_metadata(),
    }

    if not allowed:
        reason = (
            _clean_text((gate.get("blocked_reasons") or [""])[0])
            or "live_config_gate_blocked"
        )
        output = _fallback_output(
            fallback_input=deterministic_fallback_input,
            reason=reason,
        )
        return {
            **base,
            "fallback_reason": reason,
            "jd_intelligence_output": output,
            "llmops_metadata": _llmops_metadata(
                config=config,
                provider_call_attempted=False,
                provider_call_succeeded=False,
                fallback_used=True,
                validation_status="not_executed_config_gate_blocked",
                error_type="LiveConfigGateBlocked",
            ),
            "next_safe_step": gate.get("next_safe_step")
            or "resolve_live_config_gate_before_canary",
        }

    if not callable(provider_adapter):
        reason = "missing_injected_provider_adapter"
        output = _fallback_output(
            fallback_input=deterministic_fallback_input,
            reason=reason,
        )
        return {
            **base,
            "canary_status": STATUS_BLOCKED,
            "fallback_reason": reason,
            "jd_intelligence_output": output,
            "llmops_metadata": _llmops_metadata(
                config=config,
                provider_call_attempted=False,
                provider_call_succeeded=False,
                fallback_used=True,
                validation_status="not_executed_missing_adapter",
                error_type="MissingInjectedProviderAdapter",
            ),
            "next_safe_step": "inject_approved_provider_adapter_for_canary",
        }

    request = {
        "agent_name": "jd_intelligence",
        "shadow_only": True,
        "job_payload": deepcopy(job),
        "provider_name": provider_name,
        "model_name": model_name,
        "prompt_version": prompt_version,
        "runtime_version": runtime_version,
        "runtime_limits": deepcopy(gate.get("runtime_limits") or {}),
        "budget_limits": deepcopy(gate.get("budget_limits") or {}),
    }
    try:
        raw_response = provider_adapter(deepcopy(request))
    except Exception as exc:
        reason = f"provider_adapter_error:{exc.__class__.__name__}"
        output = _fallback_output(
            fallback_input=deterministic_fallback_input,
            reason=reason,
        )
        return {
            **base,
            "canary_status": STATUS_FALLBACK,
            "canary_attempted": True,
            "provider_call_attempted": True,
            "provider_call_failed": True,
            "fallback_reason": reason,
            "jd_intelligence_output": output,
            "llmops_metadata": _llmops_metadata(
                config=config,
                provider_call_attempted=True,
                provider_call_succeeded=False,
                fallback_used=True,
                validation_status="fallback",
                error_type=exc.__class__.__name__,
            ),
            "next_safe_step": "review_provider_error_and_keep_canary_off",
            "safety_metadata": jd_live_provider_canary_safety_metadata(
                provider_calls_made=True
            ),
        }

    structured_output, adapter_metadata = _provider_output(raw_response)
    limit_violation = _limit_violation(
        gate=gate,
        adapter_metadata=adapter_metadata,
    )
    if limit_violation:
        output = _fallback_output(
            fallback_input=deterministic_fallback_input,
            reason=limit_violation,
        )
        return {
            **base,
            "canary_status": STATUS_FALLBACK,
            "canary_attempted": True,
            "provider_call_attempted": True,
            "provider_call_failed": True,
            "fallback_reason": limit_violation,
            "jd_intelligence_output": output,
            "llmops_metadata": _llmops_metadata(
                config=config,
                provider_call_attempted=True,
                provider_call_succeeded=False,
                fallback_used=True,
                validation_status="budget_limit_exceeded",
                adapter_metadata=adapter_metadata,
                error_type="BudgetLimitExceeded",
            ),
            "next_safe_step": "reduce_usage_and_keep_canary_off",
            "safety_metadata": jd_live_provider_canary_safety_metadata(
                provider_calls_made=True
            ),
        }
    validated_input = {
        **structured_output,
        "model_provider": provider_name,
        "model_name": model_name,
        "prompt_version": prompt_version,
        "latency_ms": adapter_metadata.get("latency_ms", 0),
        "token_usage": {
            "input_tokens": adapter_metadata.get("input_tokens", 0),
            "output_tokens": adapter_metadata.get("output_tokens", 0),
            "total_tokens": adapter_metadata.get("total_tokens", 0),
        },
        "cost": {
            "estimated_cost": adapter_metadata.get(
                "estimated_cost",
                0,
            )
        },
    }
    validated = build_live_jd_intelligence_dry_run_payload(
        job_title=job.get("title"),
        company=job.get("company"),
        location=job.get("location"),
        job_description=(
            job.get("job_description") or job.get("description")
        ),
        source_metadata=_plain_dict(job.get("source_metadata")),
        context_id=job.get("context_id"),
        job_id=job.get("job_id"),
        adapter=lambda _request: deepcopy(validated_input),
        feature_enabled=True,
    )
    is_valid = validated.get("validation_status") == "valid"
    if not is_valid:
        errors = validated.get("validation_errors")
        reason = _clean_text(
            errors[0] if isinstance(errors, list) and errors else ""
        ) or "structured_output_validation_failed"
        output = _fallback_output(
            fallback_input=deterministic_fallback_input,
            reason=reason,
        )
        return {
            **base,
            "canary_status": STATUS_FALLBACK,
            "canary_attempted": True,
            "provider_call_attempted": True,
            "provider_call_failed": True,
            "fallback_reason": reason,
            "jd_intelligence_output": output,
            "llmops_metadata": _llmops_metadata(
                config=config,
                provider_call_attempted=True,
                provider_call_succeeded=False,
                fallback_used=True,
                validation_status="invalid",
                adapter_metadata=adapter_metadata,
                error_type="StructuredOutputValidationError",
            ),
            "next_safe_step": (
                "review_invalid_provider_output_and_keep_canary_off"
            ),
            "safety_metadata": jd_live_provider_canary_safety_metadata(
                provider_calls_made=True
            ),
        }

    return {
        **base,
        "canary_status": STATUS_SUCCEEDED,
        "canary_attempted": True,
        "provider_call_attempted": True,
        "provider_call_succeeded": True,
        "fallback_used": False,
        "structured_output_validated": True,
        "jd_intelligence_output": validated,
        "llmops_metadata": _llmops_metadata(
            config=config,
            provider_call_attempted=True,
            provider_call_succeeded=True,
            fallback_used=False,
            validation_status="valid",
            adapter_metadata=adapter_metadata,
        ),
        "next_safe_step": "audit_canary_readback_before_any_expansion",
        "safety_metadata": jd_live_provider_canary_safety_metadata(
            provider_calls_made=True
        ),
    }
