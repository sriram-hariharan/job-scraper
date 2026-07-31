from __future__ import annotations

from copy import deepcopy
import time
from typing import Any, Dict, List, Mapping, TypedDict

from src.agents import job_prioritization_agent


AUTHORITATIVE_JOB_PRIORITIZATION_GRAPH_VERSION = (
    "authoritative-job-prioritization-graph-v1"
)
AUTHORITATIVE_JOB_PRIORITIZATION_STATE_VERSION = (
    "authoritative-job-prioritization-state-v1"
)
AUTHORITATIVE_JOB_PRIORITIZATION_NODE = (
    "build_job_prioritization_shared_result"
)
AUTHORITATIVE_JOB_PRIORITIZATION_PRODUCTION_NODE_COUNT = 1
MAX_NODE_LATENCY_MS = 300_000


class AuthoritativeJobPrioritizationState(TypedDict, total=False):
    state_version: str
    execution_mode: str
    pipeline_run_id: str
    owner_user_id: str
    context_id: str
    source_artifact_path: str
    queue_rows: List[Dict[str, Any]]
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


def _copy_queue_rows(rows: Any) -> List[Dict[str, Any]]:
    if not isinstance(rows, list):
        raise TypeError("authoritative_priority_queue_rows_must_be_list")
    copied_rows: List[Dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise TypeError(
                f"authoritative_priority_queue_rows_{index}_must_be_mapping"
            )
        copied_rows.append(deepcopy(dict(row)))
    return copied_rows


def _build_job_prioritization_shared_result_node(
    state: AuthoritativeJobPrioritizationState,
) -> AuthoritativeJobPrioritizationState:
    queue_rows = _copy_queue_rows(state.get("queue_rows"))
    started_ns = time.perf_counter_ns()
    shared_result = (
        job_prioritization_agent.build_job_prioritization_shared_result(
            rows=deepcopy(queue_rows),
            pipeline_run_id=str(state.get("pipeline_run_id") or ""),
            owner_user_id=str(state.get("owner_user_id") or ""),
            source_artifact_path=str(
                state.get("source_artifact_path") or ""
            ),
        )
    )
    validated = (
        job_prioritization_agent.validate_job_prioritization_shared_result(
            shared_result,
            expected_rows=queue_rows,
            pipeline_run_id=str(state.get("pipeline_run_id") or ""),
            owner_user_id=str(state.get("owner_user_id") or ""),
            source_artifact_path=str(
                state.get("source_artifact_path") or ""
            ),
        )
    )
    latency_ms = _bounded_latency_ms(started_ns)
    next_state = deepcopy(state)
    next_state.update(
        {
            "shared_result": deepcopy(validated),
            "current_node": AUTHORITATIVE_JOB_PRIORITIZATION_NODE,
            "completed_nodes": [
                AUTHORITATIVE_JOB_PRIORITIZATION_NODE
            ],
            "pending_node": "",
            "status": "completed",
            "failure_classification": "",
            "invocation_count": 1,
            "node_latency_ms": latency_ms,
        }
    )
    return next_state


def build_authoritative_job_prioritization_graph() -> Any:
    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(AuthoritativeJobPrioritizationState)
    graph.add_node(
        AUTHORITATIVE_JOB_PRIORITIZATION_NODE,
        _build_job_prioritization_shared_result_node,
    )
    graph.add_edge(START, AUTHORITATIVE_JOB_PRIORITIZATION_NODE)
    graph.add_edge(AUTHORITATIVE_JOB_PRIORITIZATION_NODE, END)
    return graph


def execute_authoritative_job_prioritization_graph(
    *,
    rows: List[Mapping[str, Any]],
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    context_id: str = "",
    source_artifact_path: str = "",
) -> Dict[str, Any]:
    caller_rows_before = deepcopy(rows)
    copied_rows = _copy_queue_rows(rows)
    initial_state: AuthoritativeJobPrioritizationState = {
        "state_version": AUTHORITATIVE_JOB_PRIORITIZATION_STATE_VERSION,
        "execution_mode": "langgraph",
        "pipeline_run_id": str(pipeline_run_id or "").strip(),
        "owner_user_id": str(owner_user_id or "").strip(),
        "context_id": str(context_id or "").strip(),
        "source_artifact_path": str(source_artifact_path or "").strip(),
        "queue_rows": copied_rows,
        "shared_result": {},
        "current_node": "",
        "completed_nodes": [],
        "pending_node": AUTHORITATIVE_JOB_PRIORITIZATION_NODE,
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
        build_authoritative_job_prioritization_graph()
        .compile()
        .invoke(initial_state)
    )
    if rows != caller_rows_before or final_state.get("queue_rows") != copied_rows:
        raise RuntimeError(
            "authoritative_job_prioritization_input_mutation_detected"
        )
    if (
        final_state.get("status") != "completed"
        or final_state.get("invocation_count") != 1
        or final_state.get("completed_nodes")
        != [AUTHORITATIVE_JOB_PRIORITIZATION_NODE]
        or final_state.get("pending_node")
    ):
        raise RuntimeError(
            "authoritative_job_prioritization_graph_contract_failed"
        )
    shared_result = (
        job_prioritization_agent.validate_job_prioritization_shared_result(
            final_state.get("shared_result", {}),
            expected_rows=copied_rows,
            pipeline_run_id=str(pipeline_run_id or "").strip(),
            owner_user_id=str(owner_user_id or "").strip(),
            source_artifact_path=str(source_artifact_path or "").strip(),
        )
    )
    execution_metadata = {
        "graph_version": AUTHORITATIVE_JOB_PRIORITIZATION_GRAPH_VERSION,
        "state_version": AUTHORITATIVE_JOB_PRIORITIZATION_STATE_VERSION,
        "execution_mode": "langgraph",
        "node_name": AUTHORITATIVE_JOB_PRIORITIZATION_NODE,
        "production_node_count": (
            AUTHORITATIVE_JOB_PRIORITIZATION_PRODUCTION_NODE_COUNT
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
