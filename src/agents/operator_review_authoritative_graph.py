from __future__ import annotations

from copy import deepcopy
import time
from typing import Any, Dict, List, Mapping, TypedDict

from src.agents import operator_review_agent


AUTHORITATIVE_OPERATOR_REVIEW_GRAPH_VERSION = (
    "authoritative-operator-review-graph-v1"
)
AUTHORITATIVE_OPERATOR_REVIEW_STATE_VERSION = (
    "authoritative-operator-review-state-v1"
)
AUTHORITATIVE_OPERATOR_REVIEW_NODE = "build_operator_review_shared_result"
AUTHORITATIVE_OPERATOR_REVIEW_PRODUCTION_NODE_COUNT = 1
MAX_NODE_LATENCY_MS = 300_000


class AuthoritativeOperatorReviewState(TypedDict, total=False):
    graph_version: str
    state_version: str
    execution_mode: str
    pipeline_run_id: str
    owner_user_id: str
    context_id: str
    tailoring_overlay_rows: List[Dict[str, Any]]
    shared_result: Dict[str, Any]
    current_node: str
    completed_nodes: List[str]
    pending_node: str
    status: str
    failure_classification: str
    invocation_count: int
    node_latency_ms: int
    deterministic: bool
    read_only: bool
    provider_calls_allowed: bool
    mutation_authority: bool
    application_authority: bool
    ats_authority: bool


def _bounded_latency_ms(started_ns: int) -> int:
    elapsed_ms = int((time.perf_counter_ns() - started_ns) / 1_000_000)
    return max(0, min(elapsed_ms, MAX_NODE_LATENCY_MS))


def _copy_tailoring_overlay_rows(rows: Any) -> List[Dict[str, Any]]:
    if not isinstance(rows, list):
        raise TypeError(
            "authoritative_operator_review_tailoring_overlay_rows_"
            "must_be_list"
        )
    copied_rows: List[Dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise TypeError(
                "authoritative_operator_review_tailoring_overlay_rows_"
                f"{index}_must_be_mapping"
            )
        copied_rows.append(deepcopy(dict(row)))
    return copied_rows


def build_authoritative_operator_review_graph(
    *,
    source_artifact_path: str = "",
) -> Any:
    from langgraph.graph import END, START, StateGraph

    source_reference = str(source_artifact_path or "").strip()

    def build_operator_review_shared_result_node(
        state: AuthoritativeOperatorReviewState,
    ) -> AuthoritativeOperatorReviewState:
        tailoring_overlay_rows = _copy_tailoring_overlay_rows(
            state.get("tailoring_overlay_rows")
        )
        started_ns = time.perf_counter_ns()
        shared_result = (
            operator_review_agent.build_operator_review_shared_result(
                rows=deepcopy(tailoring_overlay_rows),
                pipeline_run_id=str(state.get("pipeline_run_id") or ""),
                owner_user_id=str(state.get("owner_user_id") or ""),
                source_artifact_path=source_reference,
            )
        )
        validated = (
            operator_review_agent.validate_operator_review_shared_result(
                shared_result,
                expected_rows=tailoring_overlay_rows,
                pipeline_run_id=str(state.get("pipeline_run_id") or ""),
                owner_user_id=str(state.get("owner_user_id") or ""),
                source_artifact_path=source_reference,
            )
        )
        next_state = deepcopy(state)
        next_state.update(
            {
                "shared_result": deepcopy(validated),
                "current_node": AUTHORITATIVE_OPERATOR_REVIEW_NODE,
                "completed_nodes": [AUTHORITATIVE_OPERATOR_REVIEW_NODE],
                "pending_node": "",
                "status": "completed",
                "failure_classification": "",
                "invocation_count": 1,
                "node_latency_ms": _bounded_latency_ms(started_ns),
            }
        )
        return next_state

    graph = StateGraph(AuthoritativeOperatorReviewState)
    graph.add_node(
        AUTHORITATIVE_OPERATOR_REVIEW_NODE,
        build_operator_review_shared_result_node,
    )
    graph.add_edge(START, AUTHORITATIVE_OPERATOR_REVIEW_NODE)
    graph.add_edge(AUTHORITATIVE_OPERATOR_REVIEW_NODE, END)
    return graph


def execute_authoritative_operator_review_graph(
    *,
    rows: List[Mapping[str, Any]],
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    context_id: str = "",
    source_artifact_path: str = "",
) -> Dict[str, Any]:
    caller_rows_before = deepcopy(rows)
    copied_rows = _copy_tailoring_overlay_rows(rows)
    initial_state: AuthoritativeOperatorReviewState = {
        "graph_version": AUTHORITATIVE_OPERATOR_REVIEW_GRAPH_VERSION,
        "state_version": AUTHORITATIVE_OPERATOR_REVIEW_STATE_VERSION,
        "execution_mode": "langgraph",
        "pipeline_run_id": str(pipeline_run_id or "").strip(),
        "owner_user_id": str(owner_user_id or "").strip(),
        "context_id": str(context_id or "").strip(),
        "tailoring_overlay_rows": copied_rows,
        "shared_result": {},
        "current_node": "",
        "completed_nodes": [],
        "pending_node": AUTHORITATIVE_OPERATOR_REVIEW_NODE,
        "status": "pending",
        "failure_classification": "",
        "invocation_count": 0,
        "node_latency_ms": 0,
        "deterministic": True,
        "read_only": True,
        "provider_calls_allowed": False,
        "mutation_authority": False,
        "application_authority": False,
        "ats_authority": False,
    }
    final_state = (
        build_authoritative_operator_review_graph(
            source_artifact_path=source_artifact_path,
        )
        .compile()
        .invoke(initial_state)
    )
    if (
        rows != caller_rows_before
        or final_state.get("tailoring_overlay_rows") != copied_rows
    ):
        raise RuntimeError(
            "authoritative_operator_review_input_mutation_detected"
        )
    if (
        final_state.get("status") != "completed"
        or final_state.get("invocation_count") != 1
        or final_state.get("completed_nodes")
        != [AUTHORITATIVE_OPERATOR_REVIEW_NODE]
        or final_state.get("pending_node")
    ):
        raise RuntimeError(
            "authoritative_operator_review_graph_contract_failed"
        )
    shared_result = (
        operator_review_agent.validate_operator_review_shared_result(
            final_state.get("shared_result", {}),
            expected_rows=copied_rows,
            pipeline_run_id=str(pipeline_run_id or "").strip(),
            owner_user_id=str(owner_user_id or "").strip(),
            source_artifact_path=str(source_artifact_path or "").strip(),
        )
    )
    execution_metadata = {
        "graph_version": AUTHORITATIVE_OPERATOR_REVIEW_GRAPH_VERSION,
        "state_version": AUTHORITATIVE_OPERATOR_REVIEW_STATE_VERSION,
        "execution_mode": "langgraph",
        "node_name": AUTHORITATIVE_OPERATOR_REVIEW_NODE,
        "production_node_count": (
            AUTHORITATIVE_OPERATOR_REVIEW_PRODUCTION_NODE_COUNT
        ),
        "invocation_count": 1,
        "node_latency_ms": max(
            0,
            min(
                int(final_state.get("node_latency_ms") or 0),
                MAX_NODE_LATENCY_MS,
            ),
        ),
        "status": "completed",
        "failure_classification": "",
        "deterministic": True,
        "read_only": True,
        "provider_calls_allowed": False,
        "mutation_authority": False,
        "application_authority": False,
        "ats_authority": False,
    }
    return {
        "shared_result": deepcopy(shared_result),
        "execution_metadata": execution_metadata,
    }
