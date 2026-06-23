"""Default-off operator canary for the completed three-core shadow workflow."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from src.agents.three_core_agent_shadow_runtime_readback import (
    build_three_core_agent_shadow_runtime_readback,
)


CANARY_VERSION = "phase-17h-three-core-shadow-operator-canary-v1"
STATUS_DISABLED = (
    "three_core_shadow_operator_canary_skipped_default_off"
)
STATUS_INCOMPLETE = "three_core_shadow_operator_canary_incomplete"
STATUS_COMPLETED = "three_core_shadow_operator_canary_completed"
STATUS_FAILED = "three_core_shadow_operator_canary_failed_closed"
READBACK_COMPLETED = "three_core_shadow_runtime_readback_completed"
READBACK_FAILED = (
    "three_core_shadow_runtime_readback_failed_closed"
)


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def three_core_shadow_operator_canary_safety_metadata(
) -> dict[str, bool]:
    return {
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "operator_canary_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "pipeline_stage_added": False,
        "provider_runtime_not_invoked": True,
        "provider_sdk_imported": False,
        "environment_secrets_read": False,
        "network_calls_made": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_read_files": False,
        "did_write_files": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_mutate_resume": False,
        "did_execute_application": False,
        "did_submit_application": False,
    }


def run_three_core_agent_shadow_operator_canary(
    *,
    enabled: bool = False,
    shadow_payload_provider: Callable[[], dict[str, Any]] | None = None,
    canary_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Call one injected payload provider and summarize it through readback."""

    context = _plain_dict(canary_context)
    provider_supplied = callable(shadow_payload_provider)
    provider_called = False
    source_payload: dict[str, Any] = {}
    runtime_readback: dict[str, Any] = {}
    failure_summary: dict[str, Any] = {}

    if enabled is not True:
        status = STATUS_DISABLED
        next_safe_step = (
            "enable_three_core_shadow_operator_canary_only"
        )
    elif not provider_supplied:
        status = STATUS_INCOMPLETE
        next_safe_step = "supply_three_core_shadow_payload_provider"
    else:
        provider_called = True
        try:
            source_payload = _plain_dict(shadow_payload_provider())
            runtime_readback = (
                build_three_core_agent_shadow_runtime_readback(
                    enabled=True,
                    shadow_sidecar_hook_payload=deepcopy(source_payload),
                    readback_context=deepcopy(context),
                )
            )
            readback_status = str(
                runtime_readback.get("readback_status") or ""
            ).strip()
            readback_summary = _plain_dict(
                runtime_readback.get("runtime_readback_summary")
            )
            if readback_status == READBACK_COMPLETED:
                status = STATUS_COMPLETED
                next_safe_step = (
                    "review_three_core_shadow_operator_canary_"
                    "before_api_or_ui_readback"
                )
            elif readback_status == READBACK_FAILED:
                status = STATUS_FAILED
                failure_summary = _plain_dict(
                    readback_summary.get("failure_summary")
                )
                next_safe_step = (
                    "fix_three_core_shadow_operator_canary_"
                    "failure_before_retry"
                )
            else:
                status = STATUS_INCOMPLETE
                next_safe_step = (
                    "supply_three_core_shadow_payload_provider"
                )
        except Exception as error:
            status = STATUS_FAILED
            failure_summary = {
                "error_type": type(error).__name__,
                "error_message": str(error),
                "failed_closed": True,
            }
            next_safe_step = (
                "fix_three_core_shadow_operator_canary_"
                "failure_before_retry"
            )

    readback_summary = _plain_dict(
        runtime_readback.get("runtime_readback_summary")
    )
    readback_status = str(
        runtime_readback.get("readback_status") or ""
    ).strip()
    return {
        "canary_version": CANARY_VERSION,
        "three_core_shadow_operator_canary_enabled": enabled is True,
        "canary_status": status,
        "default_off": True,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "operator_canary_only": True,
        "three_core_agent_only": True,
        "pipeline_not_connected": True,
        "pipeline_stage_added": False,
        "workflow_connection_authorized": False,
        "pipeline_connection_authorized": False,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "execution_authorized": False,
        "submission_authorized": False,
        "application_execution_authorized": False,
        "final_scoring_mutation_enabled": False,
        "ranking_mutation_enabled": False,
        "queue_mutation_enabled": False,
        "resume_mutation_enabled": False,
        "operator_canary_summary": {
            "provider_supplied": provider_supplied,
            "provider_called": provider_called,
            "readback_status": readback_status,
            "readback_completion": (
                readback_summary.get("completion") is True
            ),
            "ordered_agent_names_found": deepcopy(
                readback_summary.get("ordered_agent_names_found") or []
            ),
            "shadow_result_count": readback_summary.get(
                "shadow_result_count"
            ),
            "failure_summary": deepcopy(failure_summary),
        },
        "runtime_readback": deepcopy(runtime_readback),
        "source_shadow_payload_summary": {
            "source_payload_supplied": bool(source_payload),
            "source_hook_status": str(
                source_payload.get("hook_status") or ""
            ).strip(),
            "source_shadow_payload": deepcopy(source_payload),
        },
        "canary_context": context,
        "next_safe_step": next_safe_step,
        "safety_metadata": (
            three_core_shadow_operator_canary_safety_metadata()
        ),
    }
