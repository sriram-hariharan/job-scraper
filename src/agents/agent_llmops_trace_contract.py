"""Default-off LLMOps trace contract for the three-agent shadow workflow."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from src.agents import llmops


TRACE_CONTRACT_VERSION = "phase-9k-three-agent-llmops-trace-v1"
ORDERED_AGENT_NAMES = (
    "jd_intelligence",
    "tailoring_suggestion",
    "critic_guardrail",
)

DEFAULT_AGENT_METADATA = {
    "jd_intelligence": {
        "agent_version": "shadow-jd-intelligence-v1",
        "prompt_version": "shadow-jd-intelligence-prompt-not-executed",
    },
    "tailoring_suggestion": {
        "agent_version": "shadow-tailoring-suggestion-v1",
        "prompt_version": "shadow-tailoring-suggestion-prompt-not-executed",
    },
    "critic_guardrail": {
        "agent_version": "shadow-critic-guardrail-v1",
        "prompt_version": "shadow-critic-guardrail-prompt-not-executed",
    },
}


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _agent_trace_metadata(
    result: dict[str, Any],
    supplied: dict[str, Any],
) -> dict[str, Any]:
    agent_name = _clean_text(result.get("agent_name"))
    defaults = DEFAULT_AGENT_METADATA.get(agent_name, {})
    result_metadata = _plain_dict(result.get("provider_metadata"))
    supplied = {**result_metadata, **supplied}
    latency_ms = supplied.get("latency_ms", 0) or 0
    metadata = llmops.build_llmops_metadata(
        agent_name=agent_name,
        agent_version=supplied.get(
            "agent_version",
            defaults.get("agent_version", ""),
        ),
        prompt_version=supplied.get(
            "prompt_version",
            defaults.get("prompt_version", ""),
        ),
        model_provider=supplied.get("model_provider", ""),
        model_name=supplied.get("model_name", ""),
        input_token_count=supplied.get(
            "input_tokens",
            supplied.get("input_token_count", 0),
        ),
        output_token_count=supplied.get(
            "output_tokens",
            supplied.get("output_token_count", 0),
        ),
        estimated_cost=supplied.get("estimated_cost", 0),
        cost_currency=supplied.get("cost_currency", ""),
        latency_ms=latency_ms or 0,
        retry_count=supplied.get("retry_count", 0),
        fallback_used=supplied.get(
            "fallback_used",
            result.get("fallback_used", False),
        ),
        schema_validation_status=supplied.get(
            "schema_validation_status",
            "not_executed_provider_disabled",
        ),
        error_type=supplied.get(
            "error_type",
            result.get("error_type", ""),
        ),
        cost_reason=supplied.get(
            "cost_reason",
            "provider_not_called",
        ),
    )
    metadata.update(
        {
            "trace_contract_version": TRACE_CONTRACT_VERSION,
            "input_tokens": metadata["input_token_count"],
            "output_tokens": metadata["output_token_count"],
            "provider_call_made": bool(
                supplied.get("provider_call_made")
            ),
        }
    )
    return metadata


def three_agent_llmops_trace_safety_metadata(
    *,
    enabled: bool = False,
    token_usage_recorded: bool = False,
    cost_recorded: bool = False,
    latency_recorded: bool = False,
    provider_calls_made: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "shadow_only": True,
        "llmops_trace_contract_enabled": bool(enabled),
        "provider_calls_made": bool(provider_calls_made),
        "token_usage_recorded": bool(token_usage_recorded),
        "cost_recorded": bool(cost_recorded),
        "latency_recorded": bool(latency_recorded),
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


def attach_three_agent_llmops_trace_contract(
    *,
    chain_payload: dict[str, Any] | None,
    enabled: bool = False,
    metadata_by_agent: dict[str, dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Attach stable LLMOps metadata to copied ordered shadow results."""

    chain = _plain_dict(chain_payload)
    if enabled is not True:
        return chain

    supplied_by_agent = _plain_dict(metadata_by_agent)
    source_results = chain.get("ordered_agent_results")
    source_results = source_results if isinstance(source_results, list) else []
    results: list[dict[str, Any]] = []
    trace_rows: list[dict[str, Any]] = []
    provider_backed_agent_names: list[str] = []
    for source_result in source_results:
        result = _plain_dict(source_result)
        agent_name = _clean_text(result.get("agent_name"))
        supplied = _plain_dict(supplied_by_agent.get(agent_name))
        trace = _agent_trace_metadata(result, supplied)
        trace["latency_ms"] = trace.get("latency_ms") or 0
        result["llmops_trace_metadata"] = trace
        result_safety = _plain_dict(result.get("safety_metadata"))
        result_safety.update(
            three_agent_llmops_trace_safety_metadata(
                enabled=True,
                token_usage_recorded=True,
                cost_recorded=True,
                latency_recorded=True,
                provider_calls_made=bool(
                    trace.get("provider_call_made")
                ),
            )
        )
        result["safety_metadata"] = result_safety
        results.append(result)
        trace_rows.append(deepcopy(trace))
        if trace.get("provider_call_made") is True:
            provider_backed_agent_names.append(agent_name)

    chain["ordered_agent_results"] = results
    chain["agent_results"] = deepcopy(results)
    chain["three_agent_llmops_trace_contract"] = {
        "trace_contract_version": TRACE_CONTRACT_VERSION,
        "llmops_trace_contract_enabled": True,
        "ordered_agent_count": len(results),
        "ordered_agent_names": [
            _clean_text(result.get("agent_name")) for result in results
        ],
        "agent_traces": trace_rows,
        "provider_calls_made": bool(provider_backed_agent_names),
        "provider_backed_agent_count": len(provider_backed_agent_names),
        "provider_backed_agent_names": provider_backed_agent_names,
        "token_usage_recorded": True,
        "cost_recorded": True,
        "latency_recorded": True,
        "safety_metadata": three_agent_llmops_trace_safety_metadata(
            enabled=True,
            token_usage_recorded=True,
            cost_recorded=True,
            latency_recorded=True,
            provider_calls_made=bool(provider_backed_agent_names),
        ),
    }
    chain_safety = _plain_dict(chain.get("safety_metadata"))
    chain_safety.update(
        three_agent_llmops_trace_safety_metadata(
            enabled=True,
            token_usage_recorded=True,
            cost_recorded=True,
            latency_recorded=True,
            provider_calls_made=bool(provider_backed_agent_names),
        )
    )
    chain["safety_metadata"] = chain_safety
    chain["provider_backed_automated_agents"] = len(
        provider_backed_agent_names
    )
    chain["live_provider_backed_automated_agents"] = len(
        provider_backed_agent_names
    )
    chain["mutation_authorized_agents"] = 0
    chain["mutation_authorized_scoring_agents"] = 0
    chain["mutation_authorized_ranking_agents"] = 0
    chain["mutation_authorized_application_agents"] = 0
    return chain
