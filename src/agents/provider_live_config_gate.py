"""Fail-closed configuration gate for a future JD live provider canary."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


GATE_VERSION = "phase-13b-provider-live-config-gate-v1"
STATUS_SKIPPED = "live_config_gate_skipped_default_off"
STATUS_BLOCKED = "live_config_gate_blocked"
STATUS_ALLOWED = "live_config_gate_allowed_for_future_canary"
ALLOWED_AGENT_NAME = "jd_intelligence"
POLICY_LIMITS = {
    "max_timeout_seconds": 30.0,
    "max_retry_limit": 2,
    "max_input_tokens": 20_000,
    "max_output_tokens": 4_000,
    "max_estimated_cost": 1.0,
}
INFLUENCE_KEYS = (
    "final_scoring_influence_enabled",
    "ranking_influence_enabled",
    "queue_influence_enabled",
    "resume_mutation_enabled",
    "execution_enabled",
    "submission_enabled",
)


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _clean_allowlist(value: Any) -> list[str]:
    values = value if isinstance(value, (list, tuple, set)) else []
    cleaned: list[str] = []
    for item in values:
        text = _clean_text(item)
        if text and text not in cleaned:
            cleaned.append(text)
    return cleaned


def _number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number >= 0 else None


def _integer(value: Any) -> int | None:
    number = _number(value)
    if number is None or not number.is_integer():
        return None
    return int(number)


def provider_live_config_gate_safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "config_gate_only": True,
        "shadow_only": True,
        "live_provider_execution_enabled": False,
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
        "service_behavior_added": False,
        "pipeline_stage_added": False,
        "mutation_authorized": False,
    }


def evaluate_provider_live_config_gate(
    *,
    enabled: bool = False,
    config: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Validate explicit canary config without executing provider runtime."""

    source = _plain_dict(config)
    provider_name = _clean_text(source.get("provider_name"))
    model_name = _clean_text(source.get("model_name"))
    agent_name = _clean_text(source.get("agent_name"))
    provider_allowlist = _clean_allowlist(
        source.get("allowed_provider_names")
        or source.get("provider_allowlist")
    )
    model_allowlist = _clean_allowlist(
        source.get("allowed_model_names")
        or source.get("model_allowlist")
    )
    timeout_seconds = _number(source.get("timeout_seconds"))
    retry_limit = _integer(source.get("retry_limit"))
    max_input_tokens = _integer(source.get("max_input_tokens"))
    max_output_tokens = _integer(source.get("max_output_tokens"))
    max_estimated_cost = _number(source.get("max_estimated_cost"))

    reasons: list[str] = []
    if enabled is not True:
        reasons.append("live_config_gate_not_enabled")
    if source.get("live_canary_enabled") is not True:
        reasons.append("live_canary_not_explicitly_enabled")
    if agent_name != ALLOWED_AGENT_NAME:
        reasons.append(
            "agent_name_must_be_jd_intelligence"
            if agent_name
            else "agent_name_missing"
        )
    if source.get("shadow_only") is not True:
        reasons.append("shadow_only_must_be_true")
    if not provider_allowlist:
        reasons.append("provider_allowlist_missing")
    elif not provider_name:
        reasons.append("provider_name_missing")
    elif provider_name not in provider_allowlist:
        reasons.append("provider_name_not_allowlisted")
    if not model_allowlist:
        reasons.append("model_allowlist_missing")
    elif not model_name:
        reasons.append("model_name_missing")
    elif model_name not in model_allowlist:
        reasons.append("model_name_not_allowlisted")

    if timeout_seconds is None or timeout_seconds <= 0:
        reasons.append("timeout_seconds_missing_or_invalid")
    elif timeout_seconds > POLICY_LIMITS["max_timeout_seconds"]:
        reasons.append("timeout_seconds_exceeds_policy_limit")
    if retry_limit is None:
        reasons.append("retry_limit_missing_or_invalid")
    elif retry_limit > POLICY_LIMITS["max_retry_limit"]:
        reasons.append("retry_limit_exceeds_policy_limit")
    if max_input_tokens is None or max_input_tokens <= 0:
        reasons.append("max_input_tokens_missing_or_invalid")
    elif max_input_tokens > POLICY_LIMITS["max_input_tokens"]:
        reasons.append("max_input_tokens_exceeds_policy_limit")
    if max_output_tokens is None or max_output_tokens <= 0:
        reasons.append("max_output_tokens_missing_or_invalid")
    elif max_output_tokens > POLICY_LIMITS["max_output_tokens"]:
        reasons.append("max_output_tokens_exceeds_policy_limit")
    if max_estimated_cost is None or max_estimated_cost <= 0:
        reasons.append("max_estimated_cost_missing_or_invalid")
    elif max_estimated_cost > POLICY_LIMITS["max_estimated_cost"]:
        reasons.append("max_estimated_cost_exceeds_policy_limit")

    for key, reason in (
        (
            "structured_output_validation_required",
            "structured_output_validation_must_be_required",
        ),
        (
            "deterministic_fallback_required",
            "deterministic_fallback_must_be_required",
        ),
        (
            "llmops_metadata_required",
            "llmops_metadata_must_be_required",
        ),
    ):
        if source.get(key) is not True:
            reasons.append(reason)
    if not _clean_text(source.get("prompt_version")):
        reasons.append("prompt_version_missing")
    if not _clean_text(source.get("runtime_version")):
        reasons.append("runtime_version_missing")
    if source.get("no_mutation_authority") is not True:
        reasons.append("no_mutation_authority_must_be_true")
    if source.get("mutation_authorized") is not False:
        reasons.append("mutation_authorized_must_be_false")
    for key in INFLUENCE_KEYS:
        if source.get(key) is not False:
            reasons.append(f"{key}_must_be_false")

    canary_allowed = not reasons
    gate_status = STATUS_ALLOWED if canary_allowed else STATUS_BLOCKED
    if enabled is not True:
        gate_status = STATUS_SKIPPED
    next_safe_step = (
        "phase_13c_may_consume_gate_result_without_bypassing_safety"
        if canary_allowed
        else (
            "enable_live_config_gate_with_explicit_safe_configuration"
            if enabled is not True
            else "resolve_all_blocked_reasons_before_phase_13c"
        )
    )
    return {
        "gate_version": GATE_VERSION,
        "live_config_gate_enabled": enabled is True,
        "gate_status": gate_status,
        "default_off": enabled is not True,
        "canary_allowed": canary_allowed,
        "blocked_reasons": reasons,
        "allowed_agent_name": ALLOWED_AGENT_NAME,
        "agent_name": agent_name,
        "provider_name": provider_name,
        "model_name": model_name,
        "provider_allowlist": provider_allowlist,
        "model_allowlist": model_allowlist,
        "shadow_only": source.get("shadow_only") is True,
        "provider_calls_allowed": canary_allowed,
        "provider_calls_made": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "budget_limits": {
            "max_input_tokens": max_input_tokens,
            "max_output_tokens": max_output_tokens,
            "max_estimated_cost": max_estimated_cost,
            "policy_max_input_tokens": POLICY_LIMITS[
                "max_input_tokens"
            ],
            "policy_max_output_tokens": POLICY_LIMITS[
                "max_output_tokens"
            ],
            "policy_max_estimated_cost": POLICY_LIMITS[
                "max_estimated_cost"
            ],
        },
        "runtime_limits": {
            "timeout_seconds": timeout_seconds,
            "retry_limit": retry_limit,
            "policy_max_timeout_seconds": POLICY_LIMITS[
                "max_timeout_seconds"
            ],
            "policy_max_retry_limit": POLICY_LIMITS["max_retry_limit"],
        },
        "validation_required": (
            source.get("structured_output_validation_required") is True
        ),
        "fallback_required": (
            source.get("deterministic_fallback_required") is True
        ),
        "llmops_required": (
            source.get("llmops_metadata_required") is True
        ),
        "prompt_version": _clean_text(source.get("prompt_version")),
        "runtime_version": _clean_text(source.get("runtime_version")),
        "influence_disabled": {
            key: source.get(key) is False for key in INFLUENCE_KEYS
        },
        "config_snapshot": source,
        "next_safe_step": next_safe_step,
        "safety_metadata": provider_live_config_gate_safety_metadata(),
    }


def build_provider_live_config_gate_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    """Compatibility name for callers that use payload-builder style."""

    return evaluate_provider_live_config_gate(**kwargs)
