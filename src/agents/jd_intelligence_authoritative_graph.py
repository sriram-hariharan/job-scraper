from __future__ import annotations

from copy import deepcopy
import time
from typing import Any, Callable, Dict, List, Mapping, TypedDict


AUTHORITATIVE_JD_INTELLIGENCE_GRAPH_VERSION = (
    "authoritative-jd-intelligence-graph-v1"
)
AUTHORITATIVE_JD_INTELLIGENCE_STATE_VERSION = (
    "authoritative-jd-intelligence-state-v1"
)
AUTHORITATIVE_JD_INTELLIGENCE_NODE = "jd_intelligence"
AUTHORITATIVE_JD_INTELLIGENCE_PRODUCTION_NODE_COUNT = 1
MAX_NODE_LATENCY_MS = 300_000


class AuthoritativeJDIntelligenceState(TypedDict, total=False):
    graph_version: str
    state_version: str
    execution_mode: str
    pipeline_run_id: str
    owner_user_id: str
    context_id: str
    detailed_jobs: List[Dict[str, Any]]
    intelligent_jobs: List[Dict[str, Any]]
    input_count: int
    output_count: int
    current_node: str
    completed_nodes: List[str]
    pending_node: str
    status: str
    failure_classification: str
    node_invocation_count: int
    jd_owner_invocation_count: int
    node_latency_ms: int
    caller_input_immutable: bool
    owner_managed_cache_first: bool
    provider_calls_conditionally_allowed: bool
    graph_persistence_authority: bool
    mutation_authority: bool
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


def build_authoritative_jd_intelligence_graph(
    *,
    build_job_intelligence_func: Callable[
        [Dict[str, Any]],
        Mapping[str, Any],
    ],
) -> Any:
    from langgraph.graph import END, START, StateGraph

    if not callable(build_job_intelligence_func):
        raise TypeError("build_job_intelligence_func_must_be_callable")

    def jd_intelligence_node(
        state: AuthoritativeJDIntelligenceState,
    ) -> AuthoritativeJDIntelligenceState:
        detailed_jobs = _copy_jobs(
            state.get("detailed_jobs"),
            field_name="authoritative_jd_intelligence_detailed_jobs",
        )
        started_ns = time.perf_counter_ns()
        intelligent_jobs: List[Dict[str, Any]] = []
        owner_invocation_count = 0
        for detailed_job in detailed_jobs:
            owner_invocation_count += 1
            intelligent_job = build_job_intelligence_func(
                deepcopy(detailed_job)
            )
            if not isinstance(intelligent_job, Mapping):
                raise TypeError(
                    "authoritative_jd_intelligence_owner_output_"
                    f"{owner_invocation_count - 1}_must_be_mapping"
                )
            intelligent_jobs.append(deepcopy(dict(intelligent_job)))

        if len(intelligent_jobs) != len(detailed_jobs):
            raise RuntimeError(
                "authoritative_jd_intelligence_output_count_mismatch"
            )

        next_state = deepcopy(state)
        next_state.update(
            {
                "intelligent_jobs": intelligent_jobs,
                "output_count": len(intelligent_jobs),
                "current_node": AUTHORITATIVE_JD_INTELLIGENCE_NODE,
                "completed_nodes": [AUTHORITATIVE_JD_INTELLIGENCE_NODE],
                "pending_node": "",
                "status": "completed",
                "failure_classification": "",
                "node_invocation_count": 1,
                "jd_owner_invocation_count": owner_invocation_count,
                "node_latency_ms": _bounded_latency_ms(started_ns),
            }
        )
        return next_state

    graph = StateGraph(AuthoritativeJDIntelligenceState)
    graph.add_node(
        AUTHORITATIVE_JD_INTELLIGENCE_NODE,
        jd_intelligence_node,
    )
    graph.add_edge(START, AUTHORITATIVE_JD_INTELLIGENCE_NODE)
    graph.add_edge(AUTHORITATIVE_JD_INTELLIGENCE_NODE, END)
    return graph


def execute_authoritative_jd_intelligence_graph(
    *,
    jobs: List[Mapping[str, Any]],
    build_job_intelligence_func: Callable[
        [Dict[str, Any]],
        Mapping[str, Any],
    ],
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    context_id: str = "",
) -> Dict[str, Any]:
    caller_jobs_before = deepcopy(jobs)
    copied_jobs = _copy_jobs(
        jobs,
        field_name="authoritative_jd_intelligence_detailed_jobs",
    )
    initial_state: AuthoritativeJDIntelligenceState = {
        "graph_version": AUTHORITATIVE_JD_INTELLIGENCE_GRAPH_VERSION,
        "state_version": AUTHORITATIVE_JD_INTELLIGENCE_STATE_VERSION,
        "execution_mode": "langgraph",
        "pipeline_run_id": str(pipeline_run_id or "").strip(),
        "owner_user_id": str(owner_user_id or "").strip(),
        "context_id": str(context_id or "").strip(),
        "detailed_jobs": copied_jobs,
        "intelligent_jobs": [],
        "input_count": len(copied_jobs),
        "output_count": 0,
        "current_node": "",
        "completed_nodes": [],
        "pending_node": AUTHORITATIVE_JD_INTELLIGENCE_NODE,
        "status": "pending",
        "failure_classification": "",
        "node_invocation_count": 0,
        "jd_owner_invocation_count": 0,
        "node_latency_ms": 0,
        "caller_input_immutable": True,
        "owner_managed_cache_first": True,
        "provider_calls_conditionally_allowed": True,
        "graph_persistence_authority": False,
        "mutation_authority": False,
        "application_authority": False,
        "ats_authority": False,
    }
    final_state = (
        build_authoritative_jd_intelligence_graph(
            build_job_intelligence_func=build_job_intelligence_func,
        )
        .compile()
        .invoke(initial_state)
    )
    if jobs != caller_jobs_before or final_state.get("detailed_jobs") != copied_jobs:
        raise RuntimeError(
            "authoritative_jd_intelligence_input_mutation_detected"
        )
    if (
        final_state.get("status") != "completed"
        or final_state.get("node_invocation_count") != 1
        or final_state.get("jd_owner_invocation_count") != len(copied_jobs)
        or final_state.get("completed_nodes")
        != [AUTHORITATIVE_JD_INTELLIGENCE_NODE]
        or final_state.get("pending_node")
    ):
        raise RuntimeError(
            "authoritative_jd_intelligence_graph_contract_failed"
        )

    intelligent_jobs = _copy_jobs(
        final_state.get("intelligent_jobs"),
        field_name="authoritative_jd_intelligence_intelligent_jobs",
    )
    metadata = {
        "graph_version": AUTHORITATIVE_JD_INTELLIGENCE_GRAPH_VERSION,
        "state_version": AUTHORITATIVE_JD_INTELLIGENCE_STATE_VERSION,
        "execution_mode": "langgraph",
        "node_order": [AUTHORITATIVE_JD_INTELLIGENCE_NODE],
        "production_node_count": (
            AUTHORITATIVE_JD_INTELLIGENCE_PRODUCTION_NODE_COUNT
        ),
        "node_invocation_count": 1,
        "jd_owner_invocation_count": len(copied_jobs),
        "input_count": len(copied_jobs),
        "output_count": len(intelligent_jobs),
        "node_latency_ms": max(
            0,
            min(
                int(final_state.get("node_latency_ms") or 0),
                MAX_NODE_LATENCY_MS,
            ),
        ),
        "status": "completed",
        "failure_classification": "",
        "caller_input_immutable": True,
        "owner_managed_cache_first": True,
        "provider_calls_conditionally_allowed": True,
        "graph_persistence_authority": False,
        "mutation_authority": False,
        "application_authority": False,
        "ats_authority": False,
    }
    return {
        "intelligent_jobs": intelligent_jobs,
        "execution_metadata": metadata,
    }
