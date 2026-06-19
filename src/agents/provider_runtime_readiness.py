"""Default-off readiness contract for future shadow provider runtime use."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


CONTRACT_VERSION = "phase-11a-provider-runtime-readiness-v1"
STATUS_SKIPPED = "skipped_default_off"
STATUS_READY = "ready_shadow_provider_runtime"
STATUS_MISSING = "missing_provider_configuration"
STATUS_BLOCKED = "provider_runtime_blocked"
REQUIRED_CONFIGURATION_KEYS = (
    "provider_name",
    "model_name",
    "configured_agent_names",
)


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _clean_agent_names(value: Any) -> list[str]:
    values = value if isinstance(value, (list, tuple)) else []
    names: list[str] = []
    for item in values:
        name = _clean_text(item)
        if name and name not in names:
            names.append(name)
    return names


def provider_runtime_readiness_safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "provider_calls_made": False,
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


def build_provider_runtime_readiness_payload(
    *,
    enabled: bool = False,
    config: dict[str, Any] | None = None,
    provider_calls_allowed: bool = False,
) -> dict[str, Any]:
    """Report explicit provider readiness without reading secrets or executing."""

    source = _plain_dict(config)
    provider_name = _clean_text(source.get("provider_name"))
    model_name = _clean_text(source.get("model_name"))
    configured_agent_names = _clean_agent_names(
        source.get("configured_agent_names")
    )
    shadow_only_requested = source.get("shadow_only", True) is True
    mutation_requested = source.get("mutation_authorized") is True
    missing_configuration_keys = [
        key
        for key, configured in (
            ("provider_name", bool(provider_name)),
            ("model_name", bool(model_name)),
            ("configured_agent_names", bool(configured_agent_names)),
        )
        if not configured
    ]

    status = STATUS_SKIPPED
    next_safe_step = "enable_provider_runtime_readiness_check"
    if enabled is True:
        if not shadow_only_requested or mutation_requested:
            status = STATUS_BLOCKED
            next_safe_step = (
                "restore_shadow_only_mode_and_zero_mutation_authority"
            )
        elif missing_configuration_keys:
            status = STATUS_MISSING
            next_safe_step = (
                "supply_missing_provider_configuration_without_secrets"
            )
        else:
            status = STATUS_READY
            next_safe_step = (
                "keep_provider_calls_disabled_until_explicit_shadow_test"
                if provider_calls_allowed is not True
                else "inject_provider_callable_for_explicit_shadow_test"
            )

    return {
        "contract_version": CONTRACT_VERSION,
        "provider_runtime_readiness_enabled": enabled is True,
        "readiness_status": status,
        "provider_name": provider_name,
        "model_name": model_name,
        "provider_runtime_configured": not missing_configuration_keys,
        "provider_calls_allowed": (
            enabled is True
            and status == STATUS_READY
            and provider_calls_allowed is True
        ),
        "provider_runtime_default_off": enabled is not True,
        "shadow_only": True,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "missing_configuration_keys": missing_configuration_keys,
        "required_configuration_keys": list(REQUIRED_CONFIGURATION_KEYS),
        "configured_agent_names": configured_agent_names,
        "provider_backed_agent_count": len(configured_agent_names),
        "next_safe_step": next_safe_step,
        "safety_metadata": provider_runtime_readiness_safety_metadata(),
    }
