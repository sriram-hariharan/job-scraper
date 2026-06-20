"""Default-off JD Intelligence activation scaffold for injected providers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Callable

from src.agents.jd_intelligence import (
    build_live_jd_intelligence_dry_run_payload,
)
from src.agents.provider_runtime_adapter import run_provider_runtime_adapter


SCAFFOLD_VERSION = "phase-12b-jd-provider-runtime-activation-v1"
STATUS_SKIPPED = "jd_provider_runtime_activation_skipped_default_off"
STATUS_BLOCKED = "jd_provider_runtime_activation_blocked"
STATUS_READY = "jd_provider_runtime_activation_ready_shadow"
STATUS_FALLBACK = "jd_provider_runtime_activation_fallback"


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _safety_metadata(*, provider_calls_made: bool = False) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "jd_intelligence_only": True,
        "provider_calls_made": bool(provider_calls_made),
        "network_calls_made_by_scaffold": False,
        "embeddings_created": False,
        "did_read_database": False,
        "did_write_database": False,
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
        "service_bridge_added": False,
        "pipeline_stage_added": False,
        "mutation_authorized": False,
    }


def _fallback_jd_payload(*, enabled: bool) -> dict[str, Any]:
    return build_live_jd_intelligence_dry_run_payload(
        feature_enabled=enabled,
    )


def _llmops_metadata(
    adapter_result: dict[str, Any],
    *,
    schema_validation_status: str,
    fallback_used: bool,
) -> dict[str, Any]:
    attempted = adapter_result.get("provider_call_attempted") is True
    return {
        "agent_name": "jd_intelligence",
        "model_provider": _clean_text(
            adapter_result.get("provider_name")
        ),
        "model_name": _clean_text(adapter_result.get("model_name")),
        "provider_call_attempted": attempted,
        "provider_call_made": attempted,
        "provider_call_succeeded": (
            adapter_result.get("provider_call_succeeded") is True
            and schema_validation_status == "valid"
        ),
        "provider_call_blocked": (
            adapter_result.get("provider_call_blocked") is True
        ),
        "fallback_used": bool(fallback_used),
        "schema_validation_status": schema_validation_status,
        "error_type": _clean_text(adapter_result.get("error_type")),
        "latency_ms": int(adapter_result.get("latency_ms") or 0),
        "input_tokens": int(adapter_result.get("input_tokens") or 0),
        "output_tokens": int(adapter_result.get("output_tokens") or 0),
        "total_tokens": int(adapter_result.get("total_tokens") or 0),
        "estimated_cost": float(
            adapter_result.get("estimated_cost") or 0
        ),
    }


def run_jd_provider_runtime_activation(
    *,
    enabled: bool = False,
    job_payload: dict[str, Any] | None = None,
    context_id: str = "",
    job_id: str = "",
    provider_name: str = "",
    model_name: str = "",
    provider_callable: Callable[[dict[str, Any]], Any] | None = None,
    provider_client: Any = None,
    adapter_runner: Any = None,
) -> dict[str, Any]:
    """Run one injected JD provider path in shadow-only scaffold mode."""

    job = _plain_dict(job_payload)
    if enabled is not True:
        jd_payload = _fallback_jd_payload(enabled=False)
        adapter_result = {
            "status": "provider_runtime_adapter_skipped_default_off",
            "provider_call_attempted": False,
            "provider_call_succeeded": False,
            "provider_call_blocked": True,
            "provider_name": _clean_text(provider_name),
            "model_name": _clean_text(model_name),
        }
        return {
            "scaffold_version": SCAFFOLD_VERSION,
            "status": STATUS_SKIPPED,
            "activation_enabled": False,
            "default_off": True,
            "shadow_only": True,
            "activated_agent_name": "jd_intelligence",
            "deferred_agent_names": [
                "tailoring_suggestion",
                "critic_guardrail",
            ],
            "jd_intelligence_output": jd_payload,
            "provider_runtime_metadata": adapter_result,
            "llmops_trace_metadata": _llmops_metadata(
                adapter_result,
                schema_validation_status="disabled",
                fallback_used=True,
            ),
            "fallback_used": True,
            "mutation_authorized": False,
            "mutation_authorized_agent_count": 0,
            "safety_metadata": _safety_metadata(),
        }

    runner = adapter_runner or run_provider_runtime_adapter
    adapter_result = runner(
        enabled=True,
        request_payload={
            "agent_name": "jd_intelligence",
            "job_payload": deepcopy(job),
            "context_id": _clean_text(context_id),
            "job_id": _clean_text(job_id),
            "shadow_only": True,
        },
        provider_name=_clean_text(provider_name),
        model_name=_clean_text(model_name),
        provider_callable=provider_callable,
        provider_client=provider_client,
    )
    adapter_result = _plain_dict(adapter_result)
    attempted = adapter_result.get("provider_call_attempted") is True
    adapter_succeeded = (
        adapter_result.get("provider_call_succeeded") is True
    )

    if adapter_succeeded:
        output = _plain_dict(adapter_result.get("output"))
        validated_input = {
            **output,
            "model_provider": adapter_result.get("provider_name"),
            "model_name": adapter_result.get("model_name"),
            "latency_ms": adapter_result.get("latency_ms", 0),
            "token_usage": {
                "input_token_count": adapter_result.get(
                    "input_tokens",
                    0,
                ),
                "output_token_count": adapter_result.get(
                    "output_tokens",
                    0,
                ),
                "total_token_count": adapter_result.get(
                    "total_tokens",
                    0,
                ),
            },
            "cost": {
                "estimated_cost": adapter_result.get(
                    "estimated_cost",
                    0,
                )
            },
        }
        jd_payload = build_live_jd_intelligence_dry_run_payload(
            job_title=job.get("title"),
            company=job.get("company"),
            location=job.get("location"),
            job_description=(
                job.get("job_description") or job.get("description")
            ),
            source_metadata=_plain_dict(job.get("source_metadata")),
            context_id=context_id,
            job_id=job_id,
            adapter=lambda _request: deepcopy(validated_input),
            feature_enabled=True,
        )
    else:
        jd_payload = _fallback_jd_payload(enabled=True)

    validation_status = _clean_text(
        jd_payload.get("validation_status")
    ) or "fallback"
    validated = validation_status == "valid"
    fallback_used = not validated
    status = STATUS_READY if validated else STATUS_FALLBACK
    if not attempted and adapter_result.get("provider_call_blocked") is True:
        status = STATUS_BLOCKED
    llmops = _llmops_metadata(
        adapter_result,
        schema_validation_status=validation_status,
        fallback_used=fallback_used,
    )
    if not validated and not llmops["error_type"]:
        errors = jd_payload.get("validation_errors")
        llmops["error_type"] = _clean_text(
            errors[0] if isinstance(errors, list) and errors else ""
        )

    return {
        "scaffold_version": SCAFFOLD_VERSION,
        "status": status,
        "activation_enabled": True,
        "default_off": False,
        "shadow_only": True,
        "activated_agent_name": "jd_intelligence",
        "deferred_agent_names": [
            "tailoring_suggestion",
            "critic_guardrail",
        ],
        "jd_intelligence_output": jd_payload,
        "provider_runtime_metadata": adapter_result,
        "llmops_trace_metadata": llmops,
        "fallback_used": fallback_used,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "safety_metadata": _safety_metadata(
            provider_calls_made=attempted
        ),
    }
