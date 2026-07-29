from __future__ import annotations

from copy import deepcopy
import time
from typing import Any, Callable, Dict, List, Mapping, TypedDict


AUTHORITATIVE_TAILORING_GENERATION_GRAPH_VERSION = (
    "authoritative-tailoring-generation-graph-v1"
)
AUTHORITATIVE_TAILORING_GENERATION_STATE_VERSION = (
    "authoritative-tailoring-generation-state-v1"
)
AUTHORITATIVE_TAILORING_GENERATION_NODE = "tailoring_generation"
AUTHORITATIVE_TAILORING_GENERATION_PRODUCTION_NODE_COUNT = 1
MAX_NODE_LATENCY_MS = 300_000
MAX_METADATA_TEXT_LENGTH = 128


class AuthoritativeTailoringGenerationState(TypedDict, total=False):
    graph_version: str
    state_version: str
    execution_mode: str
    pipeline_run_id: str
    owner_user_id: str
    context_id: str
    tailoring_packet: Dict[str, Any]
    tailoring_payload: Dict[str, Any]
    current_node: str
    completed_nodes: List[str]
    pending_node: str
    status: str
    failure_classification: str
    node_invocation_count: int
    tailoring_owner_invocation_count: int
    exact_change_owner_invocation_count: int
    critic_invocation_count: int
    node_latency_ms: int
    cache_hit: bool
    retry_used: bool
    parse_ok: bool
    requested_provider: str
    requested_model: str
    resolved_provider: str
    resolved_model: str
    exact_change_embedded_in_tailoring_stage: bool
    caller_input_immutable: bool
    owner_managed_cache_first: bool
    provider_calls_conditionally_allowed: bool
    graph_persistence_authority: bool
    mutation_authority: bool
    application_authority: bool
    ats_authority: bool
    generated_content_retained_in_state: bool
    raw_provider_response_retained_in_state: bool


def _bounded_latency_ms(started_ns: int) -> int:
    elapsed_ms = int((time.perf_counter_ns() - started_ns) / 1_000_000)
    return max(0, min(elapsed_ms, MAX_NODE_LATENCY_MS))


def _copy_mapping(value: Any, *, field_name: str) -> Dict[str, Any]:
    if not isinstance(value, Mapping):
        raise TypeError(f"{field_name}_must_be_mapping")
    return deepcopy(dict(value))


def _bounded_metadata_text(value: Any) -> str:
    return " ".join(str(value or "").split())[:MAX_METADATA_TEXT_LENGTH]


def _failure_classification(result: Mapping[str, Any]) -> str:
    if result.get("parse_ok") is True:
        return ""
    parse_error = str(result.get("parse_error") or "").lower()
    if "call failed" in parse_error:
        return "provider_failure"
    return "structured_validation_failure"


def build_authoritative_tailoring_generation_graph(
    *,
    run_tailoring_func: Callable[..., Mapping[str, Any]],
    output_llm_json: str = "",
    refresh_llm_cache: bool = False,
    enable_safe_app_ready_rewrite_promotion: bool = False,
    result_holder: Dict[str, Any] | None = None,
) -> Any:
    from langgraph.graph import END, START, StateGraph

    if not callable(run_tailoring_func):
        raise TypeError("run_tailoring_func_must_be_callable")
    holder = result_holder if result_holder is not None else {}

    def tailoring_generation_node(
        state: AuthoritativeTailoringGenerationState,
    ) -> AuthoritativeTailoringGenerationState:
        packet = _copy_mapping(
            state.get("tailoring_packet"),
            field_name="authoritative_tailoring_packet",
        )
        payload = _copy_mapping(
            state.get("tailoring_payload"),
            field_name="authoritative_tailoring_payload",
        )
        started_ns = time.perf_counter_ns()
        result = run_tailoring_func(
            packet=deepcopy(packet),
            payload=deepcopy(payload),
            output_llm_json=output_llm_json,
            refresh_llm_cache=bool(refresh_llm_cache),
            enable_safe_app_ready_rewrite_promotion=bool(
                enable_safe_app_ready_rewrite_promotion
            ),
        )
        if not isinstance(result, Mapping):
            raise TypeError(
                "authoritative_tailoring_generation_owner_output_must_be_mapping"
            )
        if not isinstance(result.get("parse_ok"), bool):
            raise TypeError(
                "authoritative_tailoring_generation_parse_ok_must_be_bool"
            )

        copied_result = deepcopy(dict(result))
        holder["tailoring_result"] = copied_result
        next_state = deepcopy(state)
        next_state.update(
            {
                "current_node": AUTHORITATIVE_TAILORING_GENERATION_NODE,
                "completed_nodes": [AUTHORITATIVE_TAILORING_GENERATION_NODE],
                "pending_node": "",
                "status": "completed",
                "failure_classification": _failure_classification(result),
                "node_invocation_count": 1,
                "tailoring_owner_invocation_count": 1,
                "exact_change_owner_invocation_count": 0,
                "critic_invocation_count": 0,
                "node_latency_ms": _bounded_latency_ms(started_ns),
                "cache_hit": bool(result.get("cache_hit", False)),
                "retry_used": bool(result.get("retry_used", False)),
                "parse_ok": bool(result["parse_ok"]),
                "requested_provider": _bounded_metadata_text(
                    result.get("requested_provider")
                ),
                "requested_model": _bounded_metadata_text(
                    result.get("requested_model")
                ),
                "resolved_provider": _bounded_metadata_text(
                    result.get("resolved_provider")
                ),
                "resolved_model": _bounded_metadata_text(
                    result.get("resolved_model")
                ),
                "exact_change_embedded_in_tailoring_stage": bool(
                    result.get(
                        "concrete_replacement_candidates_requested",
                        False,
                    )
                ),
            }
        )
        return next_state

    graph = StateGraph(AuthoritativeTailoringGenerationState)
    graph.add_node(
        AUTHORITATIVE_TAILORING_GENERATION_NODE,
        tailoring_generation_node,
    )
    graph.add_edge(START, AUTHORITATIVE_TAILORING_GENERATION_NODE)
    graph.add_edge(AUTHORITATIVE_TAILORING_GENERATION_NODE, END)
    return graph


def execute_authoritative_tailoring_generation_graph(
    *,
    packet: Mapping[str, Any],
    payload: Mapping[str, Any],
    run_tailoring_func: Callable[..., Mapping[str, Any]],
    output_llm_json: str = "",
    refresh_llm_cache: bool = False,
    enable_safe_app_ready_rewrite_promotion: bool = False,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    context_id: str = "",
) -> Dict[str, Any]:
    caller_packet_before = deepcopy(packet)
    caller_payload_before = deepcopy(payload)
    copied_packet = _copy_mapping(
        packet,
        field_name="authoritative_tailoring_packet",
    )
    copied_payload = _copy_mapping(
        payload,
        field_name="authoritative_tailoring_payload",
    )
    result_holder: Dict[str, Any] = {}
    initial_state: AuthoritativeTailoringGenerationState = {
        "graph_version": AUTHORITATIVE_TAILORING_GENERATION_GRAPH_VERSION,
        "state_version": AUTHORITATIVE_TAILORING_GENERATION_STATE_VERSION,
        "execution_mode": "langgraph",
        "pipeline_run_id": _bounded_metadata_text(pipeline_run_id),
        "owner_user_id": _bounded_metadata_text(owner_user_id),
        "context_id": _bounded_metadata_text(context_id),
        "tailoring_packet": copied_packet,
        "tailoring_payload": copied_payload,
        "current_node": "",
        "completed_nodes": [],
        "pending_node": AUTHORITATIVE_TAILORING_GENERATION_NODE,
        "status": "pending",
        "failure_classification": "",
        "node_invocation_count": 0,
        "tailoring_owner_invocation_count": 0,
        "exact_change_owner_invocation_count": 0,
        "critic_invocation_count": 0,
        "node_latency_ms": 0,
        "cache_hit": False,
        "retry_used": False,
        "parse_ok": False,
        "requested_provider": "",
        "requested_model": "",
        "resolved_provider": "",
        "resolved_model": "",
        "exact_change_embedded_in_tailoring_stage": False,
        "caller_input_immutable": True,
        "owner_managed_cache_first": True,
        "provider_calls_conditionally_allowed": True,
        "graph_persistence_authority": False,
        "mutation_authority": False,
        "application_authority": False,
        "ats_authority": False,
        "generated_content_retained_in_state": False,
        "raw_provider_response_retained_in_state": False,
    }
    final_state = (
        build_authoritative_tailoring_generation_graph(
            run_tailoring_func=run_tailoring_func,
            output_llm_json=output_llm_json,
            refresh_llm_cache=refresh_llm_cache,
            enable_safe_app_ready_rewrite_promotion=(
                enable_safe_app_ready_rewrite_promotion
            ),
            result_holder=result_holder,
        )
        .compile()
        .invoke(initial_state)
    )
    if (
        packet != caller_packet_before
        or payload != caller_payload_before
        or final_state.get("tailoring_packet") != copied_packet
        or final_state.get("tailoring_payload") != copied_payload
    ):
        raise RuntimeError(
            "authoritative_tailoring_generation_input_mutation_detected"
        )
    if (
        final_state.get("status") != "completed"
        or final_state.get("node_invocation_count") != 1
        or final_state.get("tailoring_owner_invocation_count") != 1
        or final_state.get("exact_change_owner_invocation_count") != 0
        or final_state.get("critic_invocation_count") != 0
        or final_state.get("completed_nodes")
        != [AUTHORITATIVE_TAILORING_GENERATION_NODE]
        or final_state.get("pending_node")
        or "tailoring_result" not in result_holder
    ):
        raise RuntimeError(
            "authoritative_tailoring_generation_graph_contract_failed"
        )

    metadata = {
        "graph_version": AUTHORITATIVE_TAILORING_GENERATION_GRAPH_VERSION,
        "state_version": AUTHORITATIVE_TAILORING_GENERATION_STATE_VERSION,
        "execution_mode": "langgraph",
        "node_order": [AUTHORITATIVE_TAILORING_GENERATION_NODE],
        "production_node_count": (
            AUTHORITATIVE_TAILORING_GENERATION_PRODUCTION_NODE_COUNT
        ),
        "node_invocation_count": 1,
        "tailoring_owner_invocation_count": 1,
        "exact_change_owner_invocation_count": 0,
        "critic_invocation_count": 0,
        "node_latency_ms": max(
            0,
            min(
                int(final_state.get("node_latency_ms") or 0),
                MAX_NODE_LATENCY_MS,
            ),
        ),
        "status": "completed",
        "failure_classification": str(
            final_state.get("failure_classification") or ""
        ),
        "cache_hit": bool(final_state.get("cache_hit", False)),
        "retry_used": bool(final_state.get("retry_used", False)),
        "parse_ok": bool(final_state.get("parse_ok", False)),
        "requested_provider": str(
            final_state.get("requested_provider") or ""
        ),
        "requested_model": str(final_state.get("requested_model") or ""),
        "resolved_provider": str(
            final_state.get("resolved_provider") or ""
        ),
        "resolved_model": str(final_state.get("resolved_model") or ""),
        "exact_change_embedded_in_tailoring_stage": bool(
            final_state.get("exact_change_embedded_in_tailoring_stage", False)
        ),
        "caller_input_immutable": True,
        "owner_managed_cache_first": True,
        "provider_calls_conditionally_allowed": True,
        "graph_persistence_authority": False,
        "mutation_authority": False,
        "application_authority": False,
        "ats_authority": False,
        "generated_content_retained_in_state": False,
        "raw_provider_response_retained_in_state": False,
    }
    return {
        "tailoring_result": deepcopy(result_holder["tailoring_result"]),
        "execution_metadata": metadata,
    }
