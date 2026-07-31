from __future__ import annotations

import time
from typing import Any, Callable, Dict, List, Mapping, TypedDict


AUTHORITATIVE_SEMANTIC_EVALUATION_GRAPH_VERSION = (
    "authoritative-semantic-evaluation-graph-v1"
)
AUTHORITATIVE_SEMANTIC_EVALUATION_STATE_VERSION = (
    "authoritative-semantic-evaluation-state-v1"
)
AUTHORITATIVE_SEMANTIC_EVALUATION_NODE = (
    "semantic_job_fit_evaluation"
)
AUTHORITATIVE_SEMANTIC_EVALUATION_PRODUCTION_NODE_COUNT = 1
MAX_NODE_LATENCY_MS = 300_000


class AuthoritativeSemanticEvaluationState(TypedDict, total=False):
    graph_version: str
    state_version: str
    execution_mode: str
    pipeline_run_id: str
    owner_user_id: str
    context_id: str
    evaluator_input_jobs: List[Dict[str, Any]]
    evaluated_jobs: List[Dict[str, Any]]
    input_count: int
    output_count: int
    current_node: str
    completed_nodes: List[str]
    pending_node: str
    status: str
    failure_classification: str
    invocation_count: int
    node_latency_ms: int
    provider_calls_allowed: bool
    mutation_contract: str
    mutation_authority: bool
    application_authority: bool
    ats_authority: bool


def _bounded_latency_ms(started_ns: int) -> int:
    elapsed_ms = int((time.perf_counter_ns() - started_ns) / 1_000_000)
    return max(0, min(elapsed_ms, MAX_NODE_LATENCY_MS))


def _validate_jobs(
    rows: Any,
    *,
    field_name: str,
) -> List[Dict[str, Any]]:
    if not isinstance(rows, list):
        raise TypeError(f"{field_name}_must_be_list")
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise TypeError(f"{field_name}_{index}_must_be_mapping")
    return rows


def build_authoritative_semantic_evaluation_graph(
    *,
    evaluate_jobs_func: Callable[
        [List[Dict[str, Any]]],
        List[Dict[str, Any]],
    ],
) -> Any:
    from langgraph.graph import END, START, StateGraph

    if not callable(evaluate_jobs_func):
        raise TypeError("evaluate_jobs_func_must_be_callable")

    def semantic_job_fit_evaluation_node(
        state: AuthoritativeSemanticEvaluationState,
    ) -> AuthoritativeSemanticEvaluationState:
        evaluator_input_jobs = _validate_jobs(
            state.get("evaluator_input_jobs"),
            field_name="authoritative_semantic_evaluator_input_jobs",
        )
        started_ns = time.perf_counter_ns()
        evaluated_jobs = _validate_jobs(
            evaluate_jobs_func(evaluator_input_jobs),
            field_name="authoritative_semantic_evaluated_jobs",
        )

        next_state = dict(state)
        next_state.update(
            {
                "evaluated_jobs": evaluated_jobs,
                "output_count": len(evaluated_jobs),
                "current_node": AUTHORITATIVE_SEMANTIC_EVALUATION_NODE,
                "completed_nodes": [
                    AUTHORITATIVE_SEMANTIC_EVALUATION_NODE
                ],
                "pending_node": "",
                "status": "completed",
                "failure_classification": "",
                "invocation_count": 1,
                "node_latency_ms": _bounded_latency_ms(started_ns),
            }
        )
        return next_state

    graph = StateGraph(AuthoritativeSemanticEvaluationState)
    graph.add_node(
        AUTHORITATIVE_SEMANTIC_EVALUATION_NODE,
        semantic_job_fit_evaluation_node,
    )
    graph.add_edge(START, AUTHORITATIVE_SEMANTIC_EVALUATION_NODE)
    graph.add_edge(AUTHORITATIVE_SEMANTIC_EVALUATION_NODE, END)
    return graph


def execute_authoritative_semantic_evaluation_graph(
    *,
    jobs: List[Dict[str, Any]],
    evaluate_jobs_func: Callable[
        [List[Dict[str, Any]]],
        List[Dict[str, Any]],
    ],
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    context_id: str = "",
) -> Dict[str, Any]:
    validated_jobs = _validate_jobs(
        jobs,
        field_name="authoritative_semantic_evaluator_input_jobs",
    )
    initial_state: AuthoritativeSemanticEvaluationState = {
        "graph_version": AUTHORITATIVE_SEMANTIC_EVALUATION_GRAPH_VERSION,
        "state_version": AUTHORITATIVE_SEMANTIC_EVALUATION_STATE_VERSION,
        "execution_mode": "langgraph",
        "pipeline_run_id": str(pipeline_run_id or "").strip(),
        "owner_user_id": str(owner_user_id or "").strip(),
        "context_id": str(context_id or "").strip(),
        "evaluator_input_jobs": validated_jobs,
        "evaluated_jobs": [],
        "input_count": len(validated_jobs),
        "output_count": 0,
        "current_node": "",
        "completed_nodes": [],
        "pending_node": AUTHORITATIVE_SEMANTIC_EVALUATION_NODE,
        "status": "pending",
        "failure_classification": "",
        "invocation_count": 0,
        "node_latency_ms": 0,
        "provider_calls_allowed": True,
        "mutation_contract": "production_evaluator_mutates_input_jobs",
        "mutation_authority": False,
        "application_authority": False,
        "ats_authority": False,
    }
    final_state = (
        build_authoritative_semantic_evaluation_graph(
            evaluate_jobs_func=evaluate_jobs_func,
        )
        .compile()
        .invoke(initial_state)
    )
    if (
        final_state.get("status") != "completed"
        or final_state.get("invocation_count") != 1
        or final_state.get("completed_nodes")
        != [AUTHORITATIVE_SEMANTIC_EVALUATION_NODE]
        or final_state.get("pending_node")
    ):
        raise RuntimeError(
            "authoritative_semantic_evaluation_graph_contract_failed"
        )

    evaluated_jobs = _validate_jobs(
        final_state.get("evaluated_jobs"),
        field_name="authoritative_semantic_evaluated_jobs",
    )
    metadata = {
        "graph_version": AUTHORITATIVE_SEMANTIC_EVALUATION_GRAPH_VERSION,
        "state_version": AUTHORITATIVE_SEMANTIC_EVALUATION_STATE_VERSION,
        "execution_mode": "langgraph",
        "node_name": AUTHORITATIVE_SEMANTIC_EVALUATION_NODE,
        "production_node_count": (
            AUTHORITATIVE_SEMANTIC_EVALUATION_PRODUCTION_NODE_COUNT
        ),
        "invocation_count": 1,
        "input_count": len(validated_jobs),
        "output_count": len(evaluated_jobs),
        "node_latency_ms": max(
            0,
            min(
                int(final_state.get("node_latency_ms") or 0),
                MAX_NODE_LATENCY_MS,
            ),
        ),
        "status": "completed",
        "failure_classification": "",
        "provider_calls_allowed": True,
        "mutation_contract": "production_evaluator_mutates_input_jobs",
        "mutation_authority": False,
        "application_authority": False,
        "ats_authority": False,
    }
    return {
        "evaluated_jobs": evaluated_jobs,
        "execution_metadata": metadata,
    }
