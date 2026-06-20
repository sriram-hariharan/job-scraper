"""Default-off injected provider runtime adapter for shadow agent execution."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable


ADAPTER_VERSION = "phase-11b-provider-runtime-adapter-v1"
STATUS_SKIPPED = "provider_runtime_adapter_skipped_default_off"
STATUS_MISSING_CLIENT = "provider_runtime_adapter_missing_client"
STATUS_READY = "provider_runtime_adapter_ready"
STATUS_FAILED = "provider_runtime_adapter_failed_non_blocking"


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


def _provider_callable(
    provider_callable: Callable[[dict[str, Any]], Any] | None,
    provider_client: Any,
) -> tuple[Callable[[dict[str, Any]], Any] | None, str]:
    if callable(provider_callable):
        return provider_callable, "injected_provider_callable"
    if callable(provider_client):
        return provider_client, "injected_callable_client"
    invoke = getattr(provider_client, "invoke", None)
    if callable(invoke):
        return invoke, "injected_invoke_client"
    return None, "missing_injected_client"


def provider_runtime_adapter_safety_metadata(
    *,
    provider_calls_made: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "provider_calls_made": bool(provider_calls_made),
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
        "pipeline_stage_added": False,
        "mutation_authorized": False,
    }


def _base_payload(
    *,
    enabled: bool,
    provider_name: str,
    model_name: str,
    provider_mechanism: str,
) -> dict[str, Any]:
    return {
        "adapter_version": ADAPTER_VERSION,
        "status": STATUS_SKIPPED,
        "provider_runtime_adapter_enabled": enabled is True,
        "provider_runtime_default_off": enabled is not True,
        "provider_name": provider_name,
        "model_name": model_name,
        "provider_mechanism": provider_mechanism,
        "provider_call_attempted": False,
        "provider_call_succeeded": False,
        "provider_call_blocked": True,
        "shadow_only": True,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "output": {},
        "fallback_used": True,
        "error_type": "",
        "latency_ms": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "estimated_cost": 0.0,
        "schema_validation_status": "not_executed_provider_disabled",
        "safety_metadata": provider_runtime_adapter_safety_metadata(),
    }


def _normalized_response(
    raw_response: Any,
    *,
    provider_name: str,
    model_name: str,
) -> dict[str, Any]:
    raw = _plain_dict(raw_response)
    if raw:
        output = raw.get("output")
        if not isinstance(output, dict):
            output = raw.get("raw_response")
        if not isinstance(output, dict):
            output = raw.get("content")
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
                    "schema_validation_status",
                    "validation_status",
                    "fallback_used",
                    "error_type",
                }
            }
    else:
        output = {"content": deepcopy(raw_response)}

    token_usage = _plain_dict(
        raw.get("token_usage") or raw.get("token_usage_json")
    )
    cost = _plain_dict(raw.get("cost") or raw.get("cost_json"))
    input_tokens = _non_negative_int(
        token_usage.get(
            "input_tokens",
            token_usage.get(
                "input_token_count",
                token_usage.get("prompt_tokens", 0),
            ),
        )
    )
    output_tokens = _non_negative_int(
        token_usage.get(
            "output_tokens",
            token_usage.get(
                "output_token_count",
                token_usage.get("completion_tokens", 0),
            ),
        )
    )
    total_tokens = _non_negative_int(
        token_usage.get(
            "total_tokens",
            token_usage.get(
                "total_token_count",
                input_tokens + output_tokens,
            ),
        )
    )
    return {
        "provider_name": _clean_text(
            raw.get("provider_name") or raw.get("provider")
        )
        or provider_name,
        "model_name": _clean_text(
            raw.get("model_name") or raw.get("model")
        )
        or model_name,
        "output": deepcopy(output),
        "fallback_used": raw.get("fallback_used") is True,
        "error_type": _clean_text(raw.get("error_type")),
        "latency_ms": _non_negative_int(raw.get("latency_ms")),
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
        "estimated_cost": _non_negative_float(
            cost.get(
                "estimated_cost",
                cost.get("usd", raw.get("estimated_cost", 0)),
            )
        ),
        "schema_validation_status": _clean_text(
            raw.get("schema_validation_status")
            or raw.get("validation_status")
        )
        or "not_validated",
    }


def run_provider_runtime_adapter(
    *,
    enabled: bool = False,
    request_payload: dict[str, Any] | None = None,
    provider_name: str = "",
    model_name: str = "",
    provider_callable: Callable[[dict[str, Any]], Any] | None = None,
    provider_client: Any = None,
) -> dict[str, Any]:
    """Call one explicitly injected provider boundary in shadow-only mode."""

    provider, mechanism = _provider_callable(
        provider_callable,
        provider_client,
    )
    payload = _base_payload(
        enabled=enabled is True,
        provider_name=_clean_text(provider_name),
        model_name=_clean_text(model_name),
        provider_mechanism=mechanism,
    )
    if enabled is not True:
        return payload
    if provider is None:
        payload.update(
            {
                "status": STATUS_MISSING_CLIENT,
                "schema_validation_status": "not_executed_missing_client",
                "error_type": "MissingInjectedProviderClient",
            }
        )
        return payload

    try:
        raw_response = provider(deepcopy(request_payload or {}))
    except Exception as exc:
        payload.update(
            {
                "status": STATUS_FAILED,
                "provider_call_attempted": True,
                "provider_call_blocked": False,
                "fallback_used": True,
                "error_type": exc.__class__.__name__,
                "schema_validation_status": "fallback",
                "safety_metadata": provider_runtime_adapter_safety_metadata(
                    provider_calls_made=True
                ),
            }
        )
        return payload

    normalized = _normalized_response(
        raw_response,
        provider_name=_clean_text(provider_name),
        model_name=_clean_text(model_name),
    )
    payload.update(
        {
            "status": STATUS_READY,
            "provider_call_attempted": True,
            "provider_call_succeeded": True,
            "provider_call_blocked": False,
            **normalized,
            "safety_metadata": provider_runtime_adapter_safety_metadata(
                provider_calls_made=True
            ),
        }
    )
    return payload
