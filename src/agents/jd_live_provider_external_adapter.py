"""Strict external-callable boundary for the manual JD live canary."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from src.agents.provider_live_config_gate import (
    evaluate_provider_live_config_gate,
)


ADAPTER_VERSION = "phase-14b-jd-live-provider-external-adapter-v1"
STATUS_BLOCKED = "jd_live_external_adapter_blocked"
STATUS_SUCCEEDED = "jd_live_external_adapter_succeeded"
STATUS_FAILED = "jd_live_external_adapter_failed"
ALLOWED_AGENT_NAME = "jd_intelligence"


class JDLiveProviderExternalAdapterError(RuntimeError):
    """Fail-closed signal consumed by the existing canary fallback."""


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _non_negative_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def jd_live_external_adapter_safety_metadata() -> dict[str, bool]:
    return {
        "manual_only": True,
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "one_job_only": True,
        "jd_intelligence_only": True,
        "config_gate_required": True,
        "provider_sdk_imported": False,
        "provider_client_constructed": False,
        "environment_secrets_read": False,
        "direct_provider_network_implemented": False,
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
        "did_execute_application": False,
        "did_submit_application": False,
        "api_route_added": False,
        "ui_action_added": False,
        "service_behavior_added": False,
        "pipeline_stage_added": False,
        "mutation_authorized": False,
    }


def _base_result(
    *,
    config: dict[str, Any],
    configured: bool,
) -> dict[str, Any]:
    return {
        "adapter_version": ADAPTER_VERSION,
        "adapter_status": STATUS_BLOCKED,
        "external_adapter_configured": configured,
        "external_adapter_invoked": False,
        "external_adapter_succeeded": False,
        "external_adapter_failed": False,
        "adapter_error_type": "",
        "adapter_error_message": "",
        "output_schema_validated": False,
        "provider_name": _clean_text(config.get("provider_name")),
        "model_name": _clean_text(config.get("model_name")),
        "prompt_version": _clean_text(config.get("prompt_version")),
        "runtime_version": _clean_text(config.get("runtime_version")),
        "token_usage": {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        },
        "estimated_cost": 0.0,
        "latency_ms": 0,
        "normalized_response": {},
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "scoring_influence_disabled": True,
        "ranking_influence_disabled": True,
        "queue_influence_disabled": True,
        "resume_mutation_disabled": True,
        "execution_submission_disabled": True,
        "safety_metadata": jd_live_external_adapter_safety_metadata(),
    }


def _request_error(request: dict[str, Any]) -> str:
    if request.get("agent_name") != ALLOWED_AGENT_NAME:
        return "adapter_request_agent_must_be_jd_intelligence"
    if request.get("shadow_only") is not True:
        return "adapter_request_shadow_only_must_be_true"
    if (
        not isinstance(request.get("job_payload"), dict)
        or not request.get("job_payload")
    ):
        return "adapter_request_one_job_payload_required"
    return ""


def _normalize_response(
    raw_response: Any,
    *,
    config: dict[str, Any],
) -> tuple[dict[str, Any], str]:
    response = _plain_dict(raw_response)
    output = response.get("output")
    if not isinstance(output, dict):
        return {}, "external_adapter_output_missing"

    token_usage = response.get("token_usage", {})
    if not isinstance(token_usage, dict):
        return {}, "external_adapter_token_usage_invalid"
    normalized_tokens: dict[str, int] = {}
    for key in ("input_tokens", "output_tokens", "total_tokens"):
        number = _non_negative_number(token_usage.get(key, 0))
        if number is None or not number.is_integer():
            return {}, f"external_adapter_{key}_invalid"
        normalized_tokens[key] = int(number)

    cost = response.get("cost", {})
    if not isinstance(cost, dict):
        return {}, "external_adapter_cost_invalid"
    estimated_cost = _non_negative_number(
        cost.get("estimated_cost", response.get("estimated_cost", 0))
    )
    if estimated_cost is None:
        return {}, "external_adapter_estimated_cost_invalid"
    latency_ms = _non_negative_number(response.get("latency_ms", 0))
    if latency_ms is None or not latency_ms.is_integer():
        return {}, "external_adapter_latency_ms_invalid"

    normalized = {
        "output": deepcopy(output),
        "provider_name": _clean_text(config.get("provider_name")),
        "model_name": _clean_text(config.get("model_name")),
        "prompt_version": _clean_text(config.get("prompt_version")),
        "runtime_version": _clean_text(config.get("runtime_version")),
        "token_usage": normalized_tokens,
        "cost": {"estimated_cost": estimated_cost},
        "latency_ms": int(latency_ms),
    }
    return normalized, ""


def invoke_jd_live_provider_external_adapter(
    *,
    enabled: bool = False,
    request_payload: dict[str, Any] | None = None,
    live_config: dict[str, Any] | None = None,
    external_adapter: Callable[[dict[str, Any]], Any] | None = None,
) -> dict[str, Any]:
    """Validate and invoke one explicitly supplied external callable."""

    request = _plain_dict(request_payload)
    config = _plain_dict(live_config)
    configured = callable(external_adapter)
    base = _base_result(config=config, configured=configured)
    gate = _plain_dict(
        evaluate_provider_live_config_gate(
            enabled=enabled is True,
            config=deepcopy(config),
        )
    )

    error_type = ""
    error_message = ""
    if enabled is not True:
        error_type = "ExternalAdapterDisabled"
        error_message = "external_adapter_not_enabled"
    elif gate.get("canary_allowed") is not True:
        error_type = "LiveConfigGateBlocked"
        reasons = gate.get("blocked_reasons")
        error_message = (
            _clean_text(reasons[0])
            if isinstance(reasons, list) and reasons
            else "live_config_gate_blocked"
        )
    elif not configured:
        error_type = "MissingExternalAdapter"
        error_message = "missing_external_adapter"
    else:
        error_message = _request_error(request)
        if error_message:
            error_type = "InvalidExternalAdapterRequest"

    if error_type:
        return {
            **base,
            "adapter_error_type": error_type,
            "adapter_error_message": error_message,
        }

    try:
        raw_response = external_adapter(deepcopy(request))
    except Exception as exc:
        return {
            **base,
            "adapter_status": STATUS_FAILED,
            "external_adapter_invoked": True,
            "external_adapter_failed": True,
            "adapter_error_type": exc.__class__.__name__,
            "adapter_error_message": _clean_text(exc),
        }

    normalized, validation_error = _normalize_response(
        raw_response,
        config=config,
    )
    if validation_error:
        return {
            **base,
            "adapter_status": STATUS_FAILED,
            "external_adapter_invoked": True,
            "external_adapter_failed": True,
            "adapter_error_type": "InvalidExternalAdapterOutput",
            "adapter_error_message": validation_error,
        }

    return {
        **base,
        "adapter_status": STATUS_SUCCEEDED,
        "external_adapter_invoked": True,
        "external_adapter_succeeded": True,
        "output_schema_validated": True,
        "token_usage": deepcopy(normalized["token_usage"]),
        "estimated_cost": normalized["cost"]["estimated_cost"],
        "latency_ms": normalized["latency_ms"],
        "normalized_response": normalized,
    }


class JDLiveProviderExternalAdapterBridge:
    """Callable adapter retaining read-only bridge metadata for auditing."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        live_config: dict[str, Any] | None = None,
        external_adapter: Callable[[dict[str, Any]], Any] | None = None,
    ) -> None:
        self.enabled = enabled is True
        self.live_config = _plain_dict(live_config)
        self.external_adapter = external_adapter
        self.last_result: dict[str, Any] = {}

    def __call__(self, request_payload: dict[str, Any]) -> dict[str, Any]:
        self.last_result = invoke_jd_live_provider_external_adapter(
            enabled=self.enabled,
            request_payload=deepcopy(request_payload),
            live_config=deepcopy(self.live_config),
            external_adapter=self.external_adapter,
        )
        if self.last_result.get("external_adapter_succeeded") is True:
            return _plain_dict(self.last_result.get("normalized_response"))
        error_type = _clean_text(
            self.last_result.get("adapter_error_type")
        )
        error_message = _clean_text(
            self.last_result.get("adapter_error_message")
        )
        raise JDLiveProviderExternalAdapterError(
            ":".join(
                value
                for value in (error_type, error_message)
                if value
            )
            or "external_adapter_bridge_failed"
        )


def build_jd_live_provider_external_adapter(
    *,
    enabled: bool = False,
    live_config: dict[str, Any] | None = None,
    external_adapter: Callable[[dict[str, Any]], Any] | None = None,
) -> JDLiveProviderExternalAdapterBridge:
    return JDLiveProviderExternalAdapterBridge(
        enabled=enabled,
        live_config=live_config,
        external_adapter=external_adapter,
    )
