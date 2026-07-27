"""Artifact-only production shadow graph and bounded execution result."""

from __future__ import annotations

from copy import deepcopy
import time
from typing import Any, Dict, Mapping, Sequence

from src.agents.production_shadow_artifact_adapter import (
    ProductionShadowAdapterError,
    artifact_digests,
    project_completed_authoritative_artifacts,
)
from src.agents.production_shadow_state import (
    ProductionShadowState,
    build_initial_production_shadow_state,
    validate_production_shadow_state,
)
from src.agents.production_shadow_parity import (
    compare_production_shadow_parity,
)


PRODUCTION_SHADOW_EXECUTION_VERSION = "production-shadow-graph-execution-v2"
PRODUCTION_SHADOW_NODE_ORDER = (
    "load_authoritative_identity",
    "project_resume_selection",
    "project_queue_priority",
    "project_tailoring_decision",
    "project_operator_review",
    "compare_authoritative_parity",
    "finalize_shadow_observation",
)
MAX_PRODUCTION_SHADOW_JOBS = 25


def _projection(state: Mapping[str, Any]) -> Dict[str, Any]:
    validated = validate_production_shadow_state(state)
    return deepcopy(validated["authoritative_projection"])


def _complete_delta(
    state: Mapping[str, Any],
    node: str,
    started_ns: int,
    **values: Any,
) -> Dict[str, Any]:
    completed = list(state.get("completed_nodes") or [])
    expected = list(PRODUCTION_SHADOW_NODE_ORDER)[: len(completed)]
    if completed != expected or node != PRODUCTION_SHADOW_NODE_ORDER[len(completed)]:
        raise ValueError("production_shadow_node_order_invalid")
    statuses = deepcopy(dict(state.get("node_statuses") or {}))
    statuses[node] = "completed"
    latencies = deepcopy(dict(state.get("node_latencies_ms") or {}))
    latencies[node] = max(0, int((time.perf_counter_ns() - started_ns) / 1_000_000))
    return {
        **deepcopy(values),
        "current_node": node,
        "completed_nodes": [*completed, node],
        "node_statuses": statuses,
        "node_latencies_ms": latencies,
    }


def _load_authoritative_identity(
    state: ProductionShadowState,
) -> Dict[str, Any]:
    started = time.perf_counter_ns()
    projection = _projection(state)
    identity = dict(projection.get("identity_facts") or {})
    if identity.get("job_id") != state.get("job_id"):
        raise ValueError("production_shadow_identity_conflict")
    return _complete_delta(
        state,
        "load_authoritative_identity",
        started,
        reason_codes=["authoritative_identity_projected"],
    )


def _project_resume_selection(
    state: ProductionShadowState,
) -> Dict[str, Any]:
    started = time.perf_counter_ns()
    projection = _projection(state)
    facts = dict(projection.get("resume_selection_facts") or {})
    if facts.get("selected_resume_id") != state.get("selected_resume_id"):
        raise ValueError("production_shadow_resume_conflict")
    return _complete_delta(state, "project_resume_selection", started)


def _project_queue_priority(
    state: ProductionShadowState,
) -> Dict[str, Any]:
    started = time.perf_counter_ns()
    facts = dict(_projection(state).get("queue_priority_facts") or {})
    rank = facts.get("queue_rank")
    action = str(facts.get("queue_action") or "").strip()
    priority = str(facts.get("advisory_priority") or "").strip()
    if rank is not None and (
        isinstance(rank, bool) or not isinstance(rank, int) or rank < 0
    ):
        raise ValueError("production_shadow_queue_rank_invalid")
    advisory_facts: Dict[str, Any] = {}
    if priority:
        advisory_facts["advisory_priority"] = priority
    if facts.get("advisory_reason_codes"):
        advisory_facts["advisory_reason_codes"] = deepcopy(
            facts["advisory_reason_codes"]
        )
    if "requires_manual_review" in facts:
        advisory_facts["requires_manual_review"] = facts[
            "requires_manual_review"
        ]
    return _complete_delta(
        state,
        "project_queue_priority",
        started,
        queue_rank=rank,
        queue_action=action,
        advisory_priority_facts=advisory_facts,
    )


def _project_tailoring_decision(
    state: ProductionShadowState,
) -> Dict[str, Any]:
    started = time.perf_counter_ns()
    facts = dict(_projection(state).get("tailoring_decision_facts") or {})
    return _complete_delta(
        state,
        "project_tailoring_decision",
        started,
        tailoring_decision_facts=deepcopy(facts),
    )


def _project_operator_review(
    state: ProductionShadowState,
) -> Dict[str, Any]:
    started = time.perf_counter_ns()
    facts = dict(_projection(state).get("operator_review_facts") or {})
    if (
        facts.get("operator_decision_consumed") is not False
    ):
        raise ValueError("production_shadow_operator_review_invalid")
    return _complete_delta(
        state,
        "project_operator_review",
        started,
        operator_review_facts=deepcopy(facts),
        operator_review_required=True,
    )


def _compare_authoritative_parity(
    state: ProductionShadowState,
) -> Dict[str, Any]:
    started = time.perf_counter_ns()
    projection = _projection(state)
    resume_facts = dict(projection.get("resume_selection_facts") or {})
    advisory = dict(state.get("advisory_priority_facts") or {})
    tailoring = dict(state.get("tailoring_decision_facts") or {})
    operator = dict(state.get("operator_review_facts") or {})
    shadow_facts: Dict[str, Any] = {
        "job_id": state.get("job_id"),
        "selected_resume_id": state.get("selected_resume_id"),
    }
    for field, value in (
        ("packet_resume", resume_facts.get("packet_resume")),
        ("queue_rank", state.get("queue_rank")),
        ("action", state.get("queue_action")),
        ("advisory_priority", advisory.get("advisory_priority")),
        ("advisory_reason_codes", advisory.get("advisory_reason_codes")),
        ("requires_manual_review", advisory.get("requires_manual_review")),
        ("tailoring_decision", tailoring.get("tailoring_decision")),
        ("tailoring_reason_codes", tailoring.get("tailoring_reason_codes")),
        ("operator_review_lane", operator.get("operator_review_lane")),
        (
            "packet_generation_allowed",
            operator.get("packet_generation_allowed"),
        ),
    ):
        if value is not None and value != "" and value != []:
            shadow_facts[field] = deepcopy(value)
    parity = compare_production_shadow_parity(
        authoritative_facts=dict(
            projection.get("authoritative_parity_facts") or {}
        ),
        shadow_facts=shadow_facts,
    )
    return _complete_delta(
        state,
        "compare_authoritative_parity",
        started,
        parity=parity,
    )


def _finalize_shadow_observation(
    state: ProductionShadowState,
) -> Dict[str, Any]:
    started = time.perf_counter_ns()
    projection = _projection(state)
    return _complete_delta(
        state,
        "finalize_shadow_observation",
        started,
        provider_metadata=deepcopy(projection.get("provider_metadata") or {}),
        pending_node="operator_review",
        operator_review_required=True,
        failure_classification="",
    )


def build_production_shadow_graph() -> Any:
    """Build the real six-node LangGraph without a checkpointer or writer."""

    from langgraph.graph import END, StateGraph

    graph = StateGraph(ProductionShadowState)
    graph.add_node("load_authoritative_identity", _load_authoritative_identity)
    graph.add_node("project_resume_selection", _project_resume_selection)
    graph.add_node("project_queue_priority", _project_queue_priority)
    graph.add_node("project_tailoring_decision", _project_tailoring_decision)
    graph.add_node("project_operator_review", _project_operator_review)
    graph.add_node(
        "compare_authoritative_parity", _compare_authoritative_parity
    )
    graph.add_node("finalize_shadow_observation", _finalize_shadow_observation)
    graph.set_entry_point("load_authoritative_identity")
    for left, right in zip(
        PRODUCTION_SHADOW_NODE_ORDER, PRODUCTION_SHADOW_NODE_ORDER[1:]
    ):
        graph.add_edge(left, right)
    graph.add_edge("finalize_shadow_observation", END)
    return graph


def _bounded_result(state: Mapping[str, Any], graph_latency_ms: int) -> Dict[str, Any]:
    validated = validate_production_shadow_state(state)
    if tuple(validated["completed_nodes"]) != PRODUCTION_SHADOW_NODE_ORDER:
        raise ValueError("production_shadow_completed_nodes_invalid")
    return {
        "status": "completed_at_operator_review",
        "graph_invocation_id": validated["graph_invocation_id"],
        "job_id": validated["job_id"],
        "job_index": validated["job_index"],
        "selected_resume_id": validated["selected_resume_id"],
        "queue_rank": validated["queue_rank"],
        "queue_action": validated["queue_action"],
        "advisory_priority_facts": deepcopy(
            validated["advisory_priority_facts"]
        ),
        "tailoring_decision_facts": deepcopy(
            validated["tailoring_decision_facts"]
        ),
        "operator_review_facts": deepcopy(validated["operator_review_facts"]),
        "parity": deepcopy(validated["parity"]),
        "provider_metadata": deepcopy(validated["provider_metadata"]),
        "completed_node_order": list(validated["completed_nodes"]),
        "node_statuses": deepcopy(validated["node_statuses"]),
        "node_latencies_ms": deepcopy(validated["node_latencies_ms"]),
        "pending_node": validated["pending_node"],
        "operator_review_required": validated["operator_review_required"],
        "reason_codes": list(validated["reason_codes"]),
        "warnings": list(validated["warnings"]),
        "failure_classification": validated["failure_classification"],
        "authoritative_artifacts": deepcopy(
            validated["authoritative_artifacts"]
        ),
        "graph_latency_ms": max(0, int(graph_latency_ms)),
        "read_only": True,
        "authoritative": False,
        "provider_call_count": 0,
        "production_write_count": 0,
        "mutation_count": 0,
        "application_count": 0,
        "ats_count": 0,
    }


def execute_production_shadow_graph(
    *,
    job_ids: Sequence[str],
    owner_user_id: str,
    pipeline_run_id: str,
    context_id: str,
    artifact_paths: Mapping[str, Any],
    _compiled_graph: Any = None,
) -> Dict[str, Any]:
    """Execute bounded artifact projection and verify source bytes are unchanged."""

    if not job_ids or len(job_ids) > MAX_PRODUCTION_SHADOW_JOBS:
        raise ValueError("production_shadow_job_count_invalid")
    detached_job_ids = deepcopy(list(job_ids))
    detached_paths = deepcopy(dict(artifact_paths))
    try:
        before = artifact_digests(detached_paths)
        adapted = project_completed_authoritative_artifacts(
            job_ids=detached_job_ids,
            owner_user_id=owner_user_id,
            pipeline_run_id=pipeline_run_id,
            context_id=context_id,
            artifact_paths=detached_paths,
        )
    except ProductionShadowAdapterError as exc:
        return {
            "execution_version": PRODUCTION_SHADOW_EXECUTION_VERSION,
            "status": "input_rejected",
            "owner_id": str(owner_user_id or "").strip(),
            "pipeline_run_id": str(pipeline_run_id or "").strip(),
            "context_id": str(context_id or "").strip(),
            "job_count": len(detached_job_ids),
            "failure_classification": str(exc)[:120],
            "artifacts_unchanged": True,
            "provider_call_count": 0,
            "production_write_count": 0,
            "mutation_count": 0,
            "application_count": 0,
            "ats_count": 0,
            "results": [
                {
                    "job_id": str(job_id or "").strip(),
                    "status": "input_rejected",
                    "failure_classification": str(exc)[:120],
                }
                for job_id in detached_job_ids
            ],
        }

    graph = _compiled_graph or build_production_shadow_graph().compile()
    indexed_results: list[tuple[int, Dict[str, Any]]] = [
        (int(row["request_index"]), dict(row))
        for row in adapted.get("rejections", [])
    ]
    for projection in adapted["projections"]:
        initial = build_initial_production_shadow_state(projection)
        started = time.perf_counter_ns()
        try:
            final = graph.invoke(deepcopy(initial))
            latency_ms = int(
                (time.perf_counter_ns() - started) / 1_000_000
            )
            bounded = _bounded_result(final, latency_ms)
            parity_status = dict(bounded.get("parity") or {}).get(
                "parity_status"
            )
            bounded["status"] = {
                "passed": "parity_completed",
                "mismatch": "parity_mismatch",
                "incomplete": "parity_incomplete",
                "incomparable": "parity_completed",
                "failed": "parity_failed",
            }.get(parity_status, "parity_failed")
            indexed_results.append(
                (int(projection["request_index"]), bounded)
            )
        except (TypeError, ValueError, RuntimeError):
            indexed_results.append(
                (
                    int(projection["request_index"]),
                    {
                    "status": "graph_execution_failed",
                    "job_id": projection["job_id"],
                    "failure_classification": "bounded_graph_failure",
                    },
                )
            )
    results = [row for _index, row in sorted(indexed_results)]
    try:
        after = artifact_digests(detached_paths)
    except ProductionShadowAdapterError:
        after = {}
    unchanged = before == after
    if not unchanged:
        for result in results:
            result["status"] = "write_suppression_violation"
            result["failure_classification"] = "authoritative_artifact_changed"
    return {
        "execution_version": PRODUCTION_SHADOW_EXECUTION_VERSION,
        "status": "completed" if unchanged else "write_suppression_violation",
        "owner_id": str(owner_user_id or "").strip(),
        "pipeline_run_id": str(pipeline_run_id or "").strip(),
        "context_id": str(context_id or "").strip(),
        "job_count": len(detached_job_ids),
        "artifact_digests_before": before,
        "artifact_digests_after": after,
        "artifacts_unchanged": unchanged,
        "provider_call_count": 0,
        "production_write_count": 0,
        "mutation_count": 0,
        "application_count": 0,
        "ats_count": 0,
        "results": results,
    }
