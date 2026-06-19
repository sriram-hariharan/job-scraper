"""Deterministic aggregate metrics for three-agent shadow LLMOps traces."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


AGGREGATE_VERSION = "phase-9p-three-agent-llmops-aggregate-v1"
ORDERED_AGENT_NAMES = (
    "jd_intelligence",
    "tailoring_suggestion",
    "critic_guardrail",
)


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


def three_agent_llmops_aggregate_safety_metadata(
    *,
    enabled: bool = False,
    recorded: bool = False,
    provider_calls_made: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "llmops_aggregate_enabled": bool(enabled),
        "llmops_aggregate_recorded": bool(recorded),
        "provider_calls_made": bool(provider_calls_made),
        "embeddings_created": False,
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


def attach_three_agent_llmops_aggregate(
    *,
    chain_payload: dict[str, Any] | None,
    enabled: bool = False,
) -> dict[str, Any]:
    """Attach run-level metrics derived only from existing agent traces."""

    chain = _plain_dict(chain_payload)
    if enabled is not True:
        return chain

    source_results = chain.get("ordered_agent_results")
    results = source_results if isinstance(source_results, list) else []
    traces = [
        _plain_dict(_plain_dict(result).get("llmops_trace_metadata"))
        for result in results
    ]
    agent_names = [
        _clean_text(_plain_dict(result).get("agent_name"))
        for result in results
    ]
    input_tokens = sum(
        _non_negative_int(
            trace.get("input_tokens", trace.get("input_token_count", 0))
        )
        for trace in traces
    )
    output_tokens = sum(
        _non_negative_int(
            trace.get("output_tokens", trace.get("output_token_count", 0))
        )
        for trace in traces
    )
    latencies = [
        _non_negative_int(trace.get("latency_ms", 0)) for trace in traces
    ]
    provider_call_count = sum(
        1 for trace in traces if trace.get("provider_call_made") is True
    )
    fallback_count = sum(
        1 for trace in traces if trace.get("fallback_used") is True
    )
    schema_statuses = [
        _clean_text(trace.get("schema_validation_status")).lower()
        for trace in traces
    ]
    schema_valid_count = sum(
        1 for status in schema_statuses if status == "valid"
    )
    schema_invalid_count = sum(
        1
        for status in schema_statuses
        if status in {"invalid", "fallback", "failed", "error"}
    )
    ordered_three_agents = (
        len(agent_names) == len(ORDERED_AGENT_NAMES)
        and tuple(agent_names) == ORDERED_AGENT_NAMES
    )
    aggregate_status = (
        "aggregate_complete"
        if ordered_three_agents
        and schema_valid_count + schema_invalid_count == len(agent_names)
        else "aggregate_partial"
    )
    aggregate = {
        "aggregate_version": AGGREGATE_VERSION,
        "llmops_aggregate_enabled": True,
        "llmops_aggregate_recorded": True,
        "total_input_tokens": input_tokens,
        "total_output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "total_estimated_cost": round(
            sum(
                _non_negative_float(trace.get("estimated_cost", 0))
                for trace in traces
            ),
            8,
        ),
        "total_latency_ms": sum(latencies),
        "max_agent_latency_ms": max(latencies, default=0),
        "provider_call_count": provider_call_count,
        "fallback_count": fallback_count,
        "schema_valid_count": schema_valid_count,
        "schema_invalid_count": schema_invalid_count,
        "agent_count": len(agent_names),
        "agent_names": agent_names,
        "aggregate_status": aggregate_status,
        "provider_calls_made": provider_call_count > 0,
        "safety_metadata": three_agent_llmops_aggregate_safety_metadata(
            enabled=True,
            recorded=True,
            provider_calls_made=provider_call_count > 0,
        ),
    }
    chain["three_agent_llmops_aggregate"] = aggregate
    chain_safety = _plain_dict(chain.get("safety_metadata"))
    chain_safety.update(aggregate["safety_metadata"])
    chain["safety_metadata"] = chain_safety
    return chain
