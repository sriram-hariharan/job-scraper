from __future__ import annotations

from copy import deepcopy
import time
from typing import Any, Dict, List, Mapping, TypedDict

from src.pipeline import application_scorer


AUTHORITATIVE_FINAL_SCORING_GRAPH_VERSION = (
    "authoritative-final-scoring-graph-v1"
)
AUTHORITATIVE_FINAL_SCORING_STATE_VERSION = (
    "authoritative-final-scoring-state-v1"
)
AUTHORITATIVE_FINAL_SCORING_NODE = "score_jobs"
AUTHORITATIVE_FINAL_SCORING_PRODUCTION_NODE_COUNT = 1
MAX_NODE_LATENCY_MS = 300_000


class AuthoritativeFinalScoringState(TypedDict, total=False):
    graph_version: str
    state_version: str
    execution_mode: str
    pipeline_run_id: str
    owner_user_id: str
    context_id: str
    ai_jobs: List[Dict[str, Any]]
    scored_jobs: List[Dict[str, Any]]
    input_count: int
    scored_count: int
    current_node: str
    completed_nodes: List[str]
    pending_node: str
    status: str
    failure_classification: str
    invocation_count: int
    node_latency_ms: int
    deterministic: bool
    caller_input_immutable: bool
    provider_calls_allowed: bool
    persistent_mutation_authority: bool
    application_authority: bool
    ats_authority: bool


def _bounded_latency_ms(started_ns: int) -> int:
    elapsed_ms = int((time.perf_counter_ns() - started_ns) / 1_000_000)
    return max(0, min(elapsed_ms, MAX_NODE_LATENCY_MS))


def _copy_jobs(
    rows: Any,
    *,
    field_name: str,
) -> List[Dict[str, Any]]:
    if not isinstance(rows, list):
        raise TypeError(f"{field_name}_must_be_list")
    copied_rows: List[Dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise TypeError(f"{field_name}_{index}_must_be_mapping")
        copied_rows.append(deepcopy(dict(row)))
    return copied_rows


def build_authoritative_final_scoring_graph() -> Any:
    from langgraph.graph import END, START, StateGraph

    def score_jobs_node(
        state: AuthoritativeFinalScoringState,
    ) -> AuthoritativeFinalScoringState:
        ai_jobs = _copy_jobs(
            state.get("ai_jobs"),
            field_name="authoritative_final_scoring_ai_jobs",
        )
        started_ns = time.perf_counter_ns()
        scored_jobs = _copy_jobs(
            application_scorer.score_jobs(deepcopy(ai_jobs)),
            field_name="authoritative_final_scoring_scored_jobs",
        )
        if len(scored_jobs) != len(ai_jobs):
            raise RuntimeError(
                "authoritative_final_scoring_output_count_mismatch"
            )

        next_state = deepcopy(state)
        next_state.update(
            {
                "scored_jobs": scored_jobs,
                "scored_count": len(scored_jobs),
                "current_node": AUTHORITATIVE_FINAL_SCORING_NODE,
                "completed_nodes": [AUTHORITATIVE_FINAL_SCORING_NODE],
                "pending_node": "",
                "status": "completed",
                "failure_classification": "",
                "invocation_count": 1,
                "node_latency_ms": _bounded_latency_ms(started_ns),
            }
        )
        return next_state

    graph = StateGraph(AuthoritativeFinalScoringState)
    graph.add_node(AUTHORITATIVE_FINAL_SCORING_NODE, score_jobs_node)
    graph.add_edge(START, AUTHORITATIVE_FINAL_SCORING_NODE)
    graph.add_edge(AUTHORITATIVE_FINAL_SCORING_NODE, END)
    return graph


def execute_authoritative_final_scoring_graph(
    *,
    jobs: List[Mapping[str, Any]],
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    context_id: str = "",
) -> Dict[str, Any]:
    caller_jobs_before = deepcopy(jobs)
    copied_jobs = _copy_jobs(
        jobs,
        field_name="authoritative_final_scoring_ai_jobs",
    )
    initial_state: AuthoritativeFinalScoringState = {
        "graph_version": AUTHORITATIVE_FINAL_SCORING_GRAPH_VERSION,
        "state_version": AUTHORITATIVE_FINAL_SCORING_STATE_VERSION,
        "execution_mode": "langgraph",
        "pipeline_run_id": str(pipeline_run_id or "").strip(),
        "owner_user_id": str(owner_user_id or "").strip(),
        "context_id": str(context_id or "").strip(),
        "ai_jobs": copied_jobs,
        "scored_jobs": [],
        "input_count": len(copied_jobs),
        "scored_count": 0,
        "current_node": "",
        "completed_nodes": [],
        "pending_node": AUTHORITATIVE_FINAL_SCORING_NODE,
        "status": "pending",
        "failure_classification": "",
        "invocation_count": 0,
        "node_latency_ms": 0,
        "deterministic": True,
        "caller_input_immutable": True,
        "provider_calls_allowed": False,
        "persistent_mutation_authority": False,
        "application_authority": False,
        "ats_authority": False,
    }
    final_state = (
        build_authoritative_final_scoring_graph()
        .compile()
        .invoke(initial_state)
    )
    if jobs != caller_jobs_before or final_state.get("ai_jobs") != copied_jobs:
        raise RuntimeError(
            "authoritative_final_scoring_input_mutation_detected"
        )
    if (
        final_state.get("status") != "completed"
        or final_state.get("invocation_count") != 1
        or final_state.get("completed_nodes")
        != [AUTHORITATIVE_FINAL_SCORING_NODE]
        or final_state.get("pending_node")
    ):
        raise RuntimeError(
            "authoritative_final_scoring_graph_contract_failed"
        )

    scored_jobs = _copy_jobs(
        final_state.get("scored_jobs"),
        field_name="authoritative_final_scoring_scored_jobs",
    )
    metadata = {
        "graph_version": AUTHORITATIVE_FINAL_SCORING_GRAPH_VERSION,
        "state_version": AUTHORITATIVE_FINAL_SCORING_STATE_VERSION,
        "execution_mode": "langgraph",
        "node_name": AUTHORITATIVE_FINAL_SCORING_NODE,
        "production_node_count": (
            AUTHORITATIVE_FINAL_SCORING_PRODUCTION_NODE_COUNT
        ),
        "invocation_count": 1,
        "input_count": len(copied_jobs),
        "scored_count": len(scored_jobs),
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
        "caller_input_immutable": True,
        "provider_calls_allowed": False,
        "persistent_mutation_authority": False,
        "application_authority": False,
        "ats_authority": False,
    }
    return {
        "scored_jobs": scored_jobs,
        "execution_metadata": metadata,
    }
