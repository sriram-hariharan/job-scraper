from __future__ import annotations

from copy import deepcopy
import hashlib
import json
import math
from typing import Any, Dict, List, Mapping, TypedDict

from src.agents.job_prioritization_agent import (
    render_job_prioritization_recommendation_rows,
)


CONTRACT_VERSION = "job-prioritization-graph-verification-v1"
GRAPH_RUNTIME = "langgraph"
NODE_KEY = "job_prioritization"
MAX_ROW_COUNT = 10

SAFETY_METADATA = {
    "authoritative_output_changed": False,
    "queue_mutation_performed": False,
    "ranking_changed": False,
    "selected_resume_changed": False,
    "production_trace_written": False,
    "advisory_artifact_written": False,
    "database_write_performed": False,
    "file_write_performed": False,
    "live_llm_call_performed": False,
    "durable_connection_performed": False,
    "checkpoint_persisted": False,
    "finalize_executed": False,
    "application_action_created": False,
    "application_status_changed": False,
    "ats_submission_performed": False,
    "apply_click_performed": False,
    "recruiter_message_sent": False,
    "resume_mutation_performed": False,
    "tailoring_mutation_performed": False,
    "scheduler_mutation_performed": False,
}


class JobPrioritizationVerificationState(TypedDict, total=False):
    rows: List[Dict[str, Any]]
    pipeline_run_id: str
    owner_user_id: str
    context_id: str
    source_artifact_reference: str
    input_digest: str
    invocation_identity: str
    rendered_recommendation_rows: List[Dict[str, str]]
    output_digest: str
    ordered_node_keys: List[str]


def _clean_required_identity(value: Any, field_name: str) -> str:
    clean_value = str(value or "").strip()
    if not clean_value:
        raise ValueError(f"{field_name}_required")
    return clean_value


def _canonicalize(value: Any, *, location: str = "value") -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"{location}_must_be_finite")
        return value
    if isinstance(value, list):
        return [
            _canonicalize(item, location=f"{location}[{index}]")
            for index, item in enumerate(value)
        ]
    if isinstance(value, Mapping):
        if any(not isinstance(key, str) for key in value):
            raise TypeError(f"{location}_mapping_keys_must_be_strings")
        canonical: Dict[str, Any] = {}
        for key in sorted(value):
            canonical[key] = _canonicalize(
                value[key],
                location=f"{location}.{key}",
            )
        return canonical
    raise TypeError(f"{location}_contains_unsupported_value")


def _canonical_json_bytes(value: Any) -> bytes:
    canonical = _canonicalize(value)
    return json.dumps(
        canonical,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json_bytes(value)).hexdigest()


def _validate_and_copy_rows(rows: Any) -> List[Dict[str, Any]]:
    if not isinstance(rows, list):
        raise TypeError("rows_must_be_a_list")
    if not rows:
        raise ValueError("rows_must_not_be_empty")
    if len(rows) > MAX_ROW_COUNT:
        raise ValueError("row_count_exceeds_maximum")

    copied_rows: List[Dict[str, Any]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, Mapping):
            raise TypeError(f"rows[{index}]_must_be_a_mapping")
        copied_row = deepcopy(dict(row))
        _canonicalize(copied_row, location=f"rows[{index}]")
        copied_rows.append(copied_row)
    return copied_rows


def _prepare_verification_identity(
    *,
    rows: Any,
    pipeline_run_id: Any,
    owner_user_id: Any,
    context_id: Any,
) -> tuple[List[Dict[str, Any]], str, str, str, str, str]:
    clean_owner_user_id = _clean_required_identity(owner_user_id, "owner_user_id")
    clean_pipeline_run_id = _clean_required_identity(
        pipeline_run_id,
        "pipeline_run_id",
    )
    clean_context_id = _clean_required_identity(context_id, "context_id")
    copied_rows = _validate_and_copy_rows(rows)
    input_digest = _digest(copied_rows)
    invocation_identity = _digest(
        {
            "contract_version": CONTRACT_VERSION,
            "owner_user_id": clean_owner_user_id,
            "pipeline_run_id": clean_pipeline_run_id,
            "context_id": clean_context_id,
            "rows": copied_rows,
        }
    )
    return (
        copied_rows,
        clean_pipeline_run_id,
        clean_owner_user_id,
        clean_context_id,
        input_digest,
        invocation_identity,
    )


def build_job_prioritization_graph_verification_identity(
    *,
    rows: List[Mapping[str, Any]],
    pipeline_run_id: str,
    owner_user_id: str,
    context_id: str,
) -> Dict[str, Any]:
    """Return the contract-owned bounded identity without executing the graph."""

    (
        copied_rows,
        _,
        _,
        _,
        input_digest,
        invocation_identity,
    ) = _prepare_verification_identity(
        rows=rows,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        context_id=context_id,
    )
    return {
        "contract_version": CONTRACT_VERSION,
        "input_row_count": len(copied_rows),
        "input_digest": input_digest,
        "invocation_identity": invocation_identity,
    }


def _job_prioritization_node(
    state: JobPrioritizationVerificationState,
) -> JobPrioritizationVerificationState:
    rendered_rows = render_job_prioritization_recommendation_rows(
        deepcopy(state["rows"])
    )
    if not isinstance(rendered_rows, list):
        raise TypeError("renderer_output_must_be_a_list")

    copied_output: List[Dict[str, str]] = []
    for index, row in enumerate(rendered_rows):
        if not isinstance(row, Mapping):
            raise TypeError(f"renderer_output[{index}]_must_be_a_mapping")
        copied_row = deepcopy(dict(row))
        _canonicalize(copied_row, location=f"renderer_output[{index}]")
        copied_output.append(copied_row)

    next_state = deepcopy(state)
    next_state["rendered_recommendation_rows"] = copied_output
    next_state["output_digest"] = _digest(copied_output)
    next_state["ordered_node_keys"] = [NODE_KEY]
    return next_state


def _build_graph() -> Any:
    from langgraph.graph import END, START, StateGraph

    graph = StateGraph(JobPrioritizationVerificationState)
    graph.add_node(NODE_KEY, _job_prioritization_node)
    graph.add_edge(START, NODE_KEY)
    graph.add_edge(NODE_KEY, END)
    return graph


def execute_job_prioritization_graph_verification(
    *,
    rows: List[Mapping[str, Any]],
    pipeline_run_id: str,
    owner_user_id: str,
    context_id: str,
    source_artifact_reference: str,
) -> Dict[str, Any]:
    """Run the explicit, read-only production-row renderer verification graph."""

    (
        copied_rows,
        clean_pipeline_run_id,
        clean_owner_user_id,
        clean_context_id,
        input_digest,
        invocation_identity,
    ) = _prepare_verification_identity(
        rows=rows,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        context_id=context_id,
    )
    clean_source_reference = str(source_artifact_reference or "").strip()

    caller_rows_snapshot = deepcopy(rows)

    initial_state: JobPrioritizationVerificationState = {
        "rows": copied_rows,
        "pipeline_run_id": clean_pipeline_run_id,
        "owner_user_id": clean_owner_user_id,
        "context_id": clean_context_id,
        "source_artifact_reference": clean_source_reference,
        "input_digest": input_digest,
        "invocation_identity": invocation_identity,
        "rendered_recommendation_rows": [],
        "output_digest": "",
        "ordered_node_keys": [],
    }
    final_state = _build_graph().compile().invoke(initial_state)

    input_unchanged = (
        rows == caller_rows_snapshot
        and _digest(final_state["rows"]) == input_digest
    )
    return {
        "contract_version": CONTRACT_VERSION,
        "graph_runtime": GRAPH_RUNTIME,
        "node_key": NODE_KEY,
        "ordered_node_keys": list(final_state["ordered_node_keys"]),
        "attempted": True,
        "completed": True,
        "input_row_count": len(copied_rows),
        "output_row_count": len(final_state["rendered_recommendation_rows"]),
        "input_digest": input_digest,
        "output_digest": final_state["output_digest"],
        "invocation_identity": invocation_identity,
        "rendered_recommendation_rows": deepcopy(
            final_state["rendered_recommendation_rows"]
        ),
        "input_unchanged": input_unchanged,
        "deterministic": True,
        "read_only": True,
        "non_authoritative": True,
        "non_persistent": True,
        "explicit_call_only": True,
        "safety_metadata": dict(SAFETY_METADATA),
    }
