"""Manual one-job harness for the config-gated JD live canary."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from src.agents.jd_live_provider_canary import (
    run_jd_live_provider_canary,
)
from src.agents.jd_live_provider_canary_readback import (
    build_jd_live_provider_canary_readback,
)
from src.agents.jd_live_provider_external_adapter import (
    build_jd_live_provider_external_adapter,
)
from src.agents.provider_live_config_gate import (
    evaluate_provider_live_config_gate,
)


COMMAND_VERSION = "phase-14a-jd-live-provider-canary-command-v1"
STATUS_SKIPPED = "manual_jd_live_canary_command_skipped_default_off"
STATUS_BLOCKED = "manual_jd_live_canary_command_blocked"
STATUS_COMPLETED = "manual_jd_live_canary_command_completed"
ALLOWED_AGENT_NAME = "jd_intelligence"


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _one_job(
    *,
    job_payload: Any,
    job_payloads: Any,
) -> tuple[dict[str, Any], bool, str]:
    direct = _plain_dict(job_payload)
    batch = job_payloads if isinstance(job_payloads, (list, tuple)) else []
    batch_jobs = [
        deepcopy(item) for item in batch if isinstance(item, dict)
    ]
    if direct and batch_jobs:
        return {}, False, "multiple_job_inputs_not_allowed"
    if direct:
        return direct, True, ""
    if len(batch_jobs) == 1 and len(batch) == 1:
        return batch_jobs[0], True, ""
    if len(batch) > 1:
        return {}, False, "multiple_jobs_not_allowed"
    if batch and not batch_jobs:
        return {}, False, "job_payload_invalid"
    return {}, False, "one_job_payload_required"


def manual_jd_live_canary_command_safety_metadata() -> dict[str, bool]:
    return {
        "manual_only": True,
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "one_job_only": True,
        "jd_intelligence_only": True,
        "config_gate_required": True,
        "provider_calls_made": False,
        "network_implemented_by_repository": False,
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


def run_manual_jd_live_provider_canary_command(
    *,
    enabled: bool = False,
    job_payload: dict[str, Any] | None = None,
    job_payloads: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
    live_config: dict[str, Any] | None = None,
    provider_adapter: Callable[[dict[str, Any]], Any] | None = None,
    external_adapter: Callable[[dict[str, Any]], Any] | None = None,
    deterministic_fallback_input: dict[str, Any] | None = None,
    canary_runner: Callable[..., dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Run at most one explicitly enabled JD canary through injection."""

    config = _plain_dict(live_config)
    job, one_job_only, job_block_reason = _one_job(
        job_payload=job_payload,
        job_payloads=job_payloads,
    )
    gate = _plain_dict(
        evaluate_provider_live_config_gate(
            enabled=enabled is True,
            config=deepcopy(config),
        )
    )
    gate_allowed = gate.get("canary_allowed") is True
    base = {
        "command_version": COMMAND_VERSION,
        "command_status": (
            STATUS_SKIPPED if enabled is not True else STATUS_BLOCKED
        ),
        "manual_command_enabled": enabled is True,
        "one_job_only": one_job_only,
        "jd_only": config.get("agent_name") == ALLOWED_AGENT_NAME,
        "shadow_only": config.get("shadow_only") is True,
        "config_gate_allowed": gate_allowed,
        "config_gate": gate,
        "canary_attempted": False,
        "provider_call_attempted": False,
        "provider_call_succeeded": False,
        "fallback_used": True,
        "fallback_reason": "",
        "structured_output_validated": False,
        "llmops_metadata": {},
        "external_adapter_bridge": {},
        "readback": {},
        "canary_result": {},
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "scoring_influence_disabled": True,
        "ranking_influence_disabled": True,
        "queue_influence_disabled": True,
        "resume_mutation_disabled": True,
        "execution_submission_disabled": True,
        "next_safe_step": "",
        "safety_metadata": (
            manual_jd_live_canary_command_safety_metadata()
        ),
    }

    adapter = provider_adapter
    external_bridge = None
    block_reason = ""
    if enabled is not True:
        block_reason = "manual_command_not_enabled"
    elif callable(provider_adapter) and callable(external_adapter):
        block_reason = "multiple_adapter_inputs_not_allowed"
    elif not one_job_only:
        block_reason = job_block_reason
    elif not gate_allowed:
        reasons = gate.get("blocked_reasons")
        block_reason = (
            str(reasons[0]).strip()
            if isinstance(reasons, list) and reasons
            else "live_config_gate_blocked"
        )
    elif callable(external_adapter):
        external_bridge = build_jd_live_provider_external_adapter(
            enabled=True,
            live_config=deepcopy(config),
            external_adapter=external_adapter,
        )
        adapter = external_bridge
    elif not callable(adapter):
        block_reason = "missing_injected_provider_adapter"

    if block_reason:
        return {
            **base,
            "fallback_reason": block_reason,
            "readback": build_jd_live_provider_canary_readback(
                enabled=False,
            ),
            "next_safe_step": (
                gate.get("next_safe_step")
                if not gate_allowed
                else "resolve_manual_command_blocker_before_retry"
            ),
        }

    runner = canary_runner or run_jd_live_provider_canary
    canary = runner(
        enabled=True,
        job_payload=deepcopy(job),
        live_config=deepcopy(config),
        provider_adapter=adapter,
        deterministic_fallback_input=deepcopy(
            deterministic_fallback_input
        ),
    )
    canary = _plain_dict(canary)
    readback = build_jd_live_provider_canary_readback(
        enabled=True,
        payload=deepcopy(canary),
    )
    call_attempted = canary.get("provider_call_attempted") is True
    call_succeeded = canary.get("provider_call_succeeded") is True
    fallback_used = canary.get("fallback_used") is True
    validated = canary.get("structured_output_validated") is True
    safety = manual_jd_live_canary_command_safety_metadata()
    safety["provider_calls_made"] = call_attempted
    return {
        **base,
        "command_status": STATUS_COMPLETED,
        "canary_attempted": canary.get("canary_attempted") is True,
        "provider_call_attempted": call_attempted,
        "provider_call_succeeded": call_succeeded,
        "fallback_used": fallback_used,
        "fallback_reason": str(
            canary.get("fallback_reason") or ""
        ).strip(),
        "structured_output_validated": validated,
        "llmops_metadata": _plain_dict(
            canary.get("llmops_metadata")
        ),
        "external_adapter_bridge": (
            _plain_dict(external_bridge.last_result)
            if external_bridge is not None
            else {}
        ),
        "readback": readback,
        "canary_result": canary,
        "next_safe_step": str(
            canary.get("next_safe_step")
            or "audit_manual_canary_result"
        ).strip(),
        "safety_metadata": safety,
    }


def build_manual_jd_live_provider_canary_command_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    return run_manual_jd_live_provider_canary_command(**kwargs)
