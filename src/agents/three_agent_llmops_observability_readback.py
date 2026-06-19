"""Read-only LLMOps observability readback for the three-agent workflow."""

from __future__ import annotations

from copy import deepcopy
from typing import Any


STATUS_SKIPPED = "skipped_default_off"
STATUS_READY = "ready"
STATUS_MISSING_CHAIN = "missing_three_agent_chain"
STATUS_MISSING_METADATA = "missing_llmops_metadata"


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


def _safety_metadata() -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "readback_only": True,
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


def _empty_aggregate() -> dict[str, Any]:
    return {
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_tokens": 0,
        "total_estimated_cost": 0.0,
        "total_latency_ms": 0,
        "max_agent_latency_ms": 0,
        "provider_call_count": 0,
        "fallback_count": 0,
        "schema_valid_count": 0,
        "schema_invalid_count": 0,
        "agent_count": 0,
        "agent_names": [],
        "aggregate_status": "",
        "provider_calls_made": False,
    }


def _extract_source(
    payload: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    source = _plain_dict(payload)
    chain = _plain_dict(source.get("chain_payload"))
    if chain:
        return chain, source
    if (
        "ordered_agent_results" in source
        or "three_agent_llmops_trace_contract" in source
    ):
        return source, {}
    return {}, source


def _agent_rows(
    chain: dict[str, Any],
    container: dict[str, Any],
) -> list[dict[str, Any]]:
    results = chain.get("ordered_agent_results")
    results = results if isinstance(results, list) else []
    rows: list[dict[str, Any]] = []
    for result_value in results:
        result = _plain_dict(result_value)
        trace = _plain_dict(result.get("llmops_trace_metadata"))
        input_tokens = _non_negative_int(
            trace.get("input_tokens", trace.get("input_token_count", 0))
        )
        output_tokens = _non_negative_int(
            trace.get(
                "output_tokens",
                trace.get("output_token_count", 0),
            )
        )
        rows.append(
            {
                "agent_name": _clean_text(result.get("agent_name")),
                "provider_call_made": (
                    trace.get("provider_call_made") is True
                ),
                "model_provider": _clean_text(
                    trace.get("model_provider")
                ),
                "model_name": _clean_text(trace.get("model_name")),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": _non_negative_int(
                    trace.get(
                        "total_token_count",
                        input_tokens + output_tokens,
                    )
                ),
                "estimated_cost": _non_negative_float(
                    trace.get("estimated_cost")
                ),
                "latency_ms": _non_negative_int(
                    trace.get("latency_ms")
                ),
                "fallback_used": trace.get("fallback_used") is True,
                "schema_validation_status": _clean_text(
                    trace.get("schema_validation_status")
                ),
                "error_type": _clean_text(trace.get("error_type")),
            }
        )
    if rows:
        return rows

    trace_contract = _plain_dict(
        container.get("three_agent_llmops_trace_contract")
    )
    traces = trace_contract.get("agent_traces")
    traces = traces if isinstance(traces, list) else []
    for trace_value in traces:
        trace = _plain_dict(trace_value)
        input_tokens = _non_negative_int(
            trace.get("input_tokens", trace.get("input_token_count", 0))
        )
        output_tokens = _non_negative_int(
            trace.get(
                "output_tokens",
                trace.get("output_token_count", 0),
            )
        )
        rows.append(
            {
                "agent_name": _clean_text(trace.get("agent_name")),
                "provider_call_made": (
                    trace.get("provider_call_made") is True
                ),
                "model_provider": _clean_text(
                    trace.get("model_provider")
                ),
                "model_name": _clean_text(trace.get("model_name")),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "total_tokens": _non_negative_int(
                    trace.get(
                        "total_token_count",
                        input_tokens + output_tokens,
                    )
                ),
                "estimated_cost": _non_negative_float(
                    trace.get("estimated_cost")
                ),
                "latency_ms": _non_negative_int(
                    trace.get("latency_ms")
                ),
                "fallback_used": trace.get("fallback_used") is True,
                "schema_validation_status": _clean_text(
                    trace.get("schema_validation_status")
                ),
                "error_type": _clean_text(trace.get("error_type")),
            }
        )
    return rows


def build_three_agent_llmops_observability_readback_payload(
    *,
    payload: dict[str, Any] | None = None,
    enabled: bool = False,
) -> dict[str, Any]:
    """Normalize existing workflow observability without executing anything."""

    safety = _safety_metadata()
    empty = {
        "observability_readback_enabled": enabled is True,
        "readback_status": STATUS_SKIPPED,
        "agent_count": 0,
        "provider_backed_agent_count": 0,
        "provider_backed_agent_names": [],
        "agents": [],
        "aggregate": _empty_aggregate(),
        "workflow_readiness": {},
        "safety_metadata": safety,
    }
    if enabled is not True:
        return empty

    chain, container = _extract_source(payload)
    if not chain and not container:
        empty["readback_status"] = STATUS_MISSING_CHAIN
        return empty

    source = chain or container
    rows = _agent_rows(chain, source)
    if not rows:
        empty["readback_status"] = (
            STATUS_MISSING_METADATA if source else STATUS_MISSING_CHAIN
        )
        return empty

    aggregate = _plain_dict(
        source.get("three_agent_llmops_aggregate")
    )
    if not aggregate:
        aggregate = _empty_aggregate()
    readiness = _plain_dict(
        source.get("three_agent_workflow_readiness")
    )
    provider_names = [
        row["agent_name"]
        for row in rows
        if row["provider_call_made"] and row["agent_name"]
    ]
    return {
        "observability_readback_enabled": True,
        "readback_status": STATUS_READY,
        "agent_count": len(rows),
        "provider_backed_agent_count": len(provider_names),
        "provider_backed_agent_names": provider_names,
        "agents": rows,
        "aggregate": aggregate,
        "workflow_readiness": readiness,
        "safety_metadata": safety,
    }


def build_three_agent_llmops_observability_readback_helper_payload(
    **kwargs: Any,
) -> dict[str, Any]:
    return build_three_agent_llmops_observability_readback_payload(**kwargs)
