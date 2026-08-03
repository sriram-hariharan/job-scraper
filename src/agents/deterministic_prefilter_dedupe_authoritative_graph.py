from __future__ import annotations

from copy import deepcopy
import time
from typing import Any, Callable, Dict, List, Mapping, TypedDict

from src.pipeline import dedupe, job_filter
from src.config.seniority_policy import normalize_seniority_filter_preferences


AUTHORITATIVE_PREFILTER_DEDUPE_GRAPH_VERSION = (
    "authoritative-prefilter-dedupe-graph-v1"
)
AUTHORITATIVE_PREFILTER_DEDUPE_STATE_VERSION = (
    "authoritative-prefilter-dedupe-state-v1"
)
AUTHORITATIVE_PREFILTER_NODE = "filter_jobs"
AUTHORITATIVE_DEDUPE_NODE = "dedupe_jobs"
AUTHORITATIVE_PREFILTER_DEDUPE_NODE_ORDER = (
    AUTHORITATIVE_PREFILTER_NODE,
    AUTHORITATIVE_DEDUPE_NODE,
)
AUTHORITATIVE_PREFILTER_DEDUPE_PRODUCTION_NODE_COUNT = 2
MAX_NODE_LATENCY_MS = 300_000


class AuthoritativePrefilterDedupeState(TypedDict, total=False):
    graph_version: str
    state_version: str
    execution_mode: str
    pipeline_run_id: str
    owner_user_id: str
    context_id: str
    input_jobs: List[Dict[str, Any]]
    selected_role_families: List[str] | None
    target_seniority: List[str]
    seniority_strict_match: bool
    filter_mode: str
    excluded_keywords: List[str]
    role_title_audit_enabled: bool
    role_title_audit_rows: List[Dict[str, Any]]
    filtered_jobs: List[Dict[str, Any]]
    filter_diagnostics: Dict[str, int]
    deduplicated_jobs: List[Dict[str, Any]]
    input_count: int
    prefilter_output_count: int
    dedupe_output_count: int
    current_node: str
    completed_nodes: List[str]
    pending_node: str
    status: str
    failure_classification: str
    prefilter_invocation_count: int
    dedupe_invocation_count: int
    prefilter_latency_ms: int
    dedupe_latency_ms: int
    deterministic: bool
    read_only: bool
    provider_calls_allowed: bool
    mutation_authority: bool
    application_authority: bool
    ats_authority: bool


def _bounded_latency_ms(started_ns: int) -> int:
    elapsed_ms = int((time.perf_counter_ns() - started_ns) / 1_000_000)
    return max(0, min(elapsed_ms, MAX_NODE_LATENCY_MS))


def _copy_mapping_rows(
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


def _copy_string_list(
    values: Any,
    *,
    field_name: str,
    allow_none: bool = False,
) -> List[str] | None:
    if values is None and allow_none:
        return None
    if not isinstance(values, list):
        raise TypeError(f"{field_name}_must_be_list")
    return [str(value or "").strip() for value in values]


def _validate_filter_result(
    result: Any,
) -> tuple[List[Dict[str, Any]], Dict[str, int]]:
    if not isinstance(result, tuple) or len(result) != 2:
        raise RuntimeError("authoritative_prefilter_result_invalid")
    filtered_jobs = _copy_mapping_rows(
        result[0],
        field_name="authoritative_prefilter_filtered_jobs",
    )
    if not isinstance(result[1], Mapping):
        raise RuntimeError("authoritative_prefilter_diagnostics_invalid")
    diagnostics: Dict[str, int] = {}
    for key, value in result[1].items():
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise RuntimeError(
                "authoritative_prefilter_diagnostics_invalid"
            )
        diagnostics[str(key)] = value
    return filtered_jobs, diagnostics


def build_authoritative_prefilter_dedupe_graph(
    *,
    on_prefilter_completed: Callable[
        [
            List[Dict[str, Any]],
            Dict[str, int],
            List[Dict[str, Any]],
        ],
        None,
    ]
    | None = None,
    on_dedupe_completed: Callable[[List[Dict[str, Any]]], None]
    | None = None,
) -> Any:
    from langgraph.graph import END, START, StateGraph

    def filter_jobs_node(
        state: AuthoritativePrefilterDedupeState,
    ) -> AuthoritativePrefilterDedupeState:
        input_jobs = _copy_mapping_rows(
            state.get("input_jobs"),
            field_name="authoritative_prefilter_input_jobs",
        )
        selected_role_families = _copy_string_list(
            state.get("selected_role_families"),
            field_name="authoritative_prefilter_selected_role_families",
            allow_none=True,
        )
        target_seniority = _copy_string_list(
            state.get("target_seniority"),
            field_name="authoritative_prefilter_target_seniority",
        )
        seniority_strict_match = state.get("seniority_strict_match")
        if not isinstance(seniority_strict_match, bool):
            raise TypeError("authoritative_prefilter_seniority_strict_match_must_be_boolean")
        excluded_keywords = _copy_string_list(
            state.get("excluded_keywords"),
            field_name="authoritative_prefilter_excluded_keywords",
        )
        audit_enabled = bool(state.get("role_title_audit_enabled"))
        audit_rows = _copy_mapping_rows(
            state.get("role_title_audit_rows"),
            field_name="authoritative_prefilter_audit_rows",
        )
        working_audit_rows = deepcopy(audit_rows) if audit_enabled else None

        started_ns = time.perf_counter_ns()
        result = job_filter.filter_jobs(
            deepcopy(input_jobs),
            selected_role_families=selected_role_families,
            target_seniority=target_seniority,
            seniority_strict_match=seniority_strict_match,
            filter_mode=str(state.get("filter_mode") or "strict_live"),
            return_diagnostics=True,
            role_title_audit_rows=working_audit_rows,
            excluded_keywords=excluded_keywords,
        )
        filtered_jobs, diagnostics = _validate_filter_result(result)
        completed_audit_rows = (
            _copy_mapping_rows(
                working_audit_rows,
                field_name="authoritative_prefilter_audit_rows",
            )
            if audit_enabled
            else []
        )
        if on_prefilter_completed is not None:
            on_prefilter_completed(
                deepcopy(filtered_jobs),
                deepcopy(diagnostics),
                deepcopy(completed_audit_rows),
            )

        next_state = deepcopy(state)
        next_state.update(
            {
                "filtered_jobs": filtered_jobs,
                "filter_diagnostics": diagnostics,
                "role_title_audit_rows": completed_audit_rows,
                "prefilter_output_count": len(filtered_jobs),
                "current_node": AUTHORITATIVE_PREFILTER_NODE,
                "completed_nodes": [AUTHORITATIVE_PREFILTER_NODE],
                "pending_node": AUTHORITATIVE_DEDUPE_NODE,
                "status": "running",
                "prefilter_invocation_count": 1,
                "prefilter_latency_ms": _bounded_latency_ms(started_ns),
            }
        )
        return next_state

    def dedupe_jobs_node(
        state: AuthoritativePrefilterDedupeState,
    ) -> AuthoritativePrefilterDedupeState:
        filtered_jobs = _copy_mapping_rows(
            state.get("filtered_jobs"),
            field_name="authoritative_dedupe_filtered_jobs",
        )
        started_ns = time.perf_counter_ns()
        deduplicated_jobs = _copy_mapping_rows(
            dedupe.dedupe_jobs(deepcopy(filtered_jobs)),
            field_name="authoritative_deduplicated_jobs",
        )
        if on_dedupe_completed is not None:
            on_dedupe_completed(deepcopy(deduplicated_jobs))

        next_state = deepcopy(state)
        next_state.update(
            {
                "deduplicated_jobs": deduplicated_jobs,
                "dedupe_output_count": len(deduplicated_jobs),
                "current_node": AUTHORITATIVE_DEDUPE_NODE,
                "completed_nodes": list(
                    AUTHORITATIVE_PREFILTER_DEDUPE_NODE_ORDER
                ),
                "pending_node": "",
                "status": "completed",
                "dedupe_invocation_count": 1,
                "dedupe_latency_ms": _bounded_latency_ms(started_ns),
            }
        )
        return next_state

    graph = StateGraph(AuthoritativePrefilterDedupeState)
    graph.add_node(AUTHORITATIVE_PREFILTER_NODE, filter_jobs_node)
    graph.add_node(AUTHORITATIVE_DEDUPE_NODE, dedupe_jobs_node)
    graph.add_edge(START, AUTHORITATIVE_PREFILTER_NODE)
    graph.add_edge(
        AUTHORITATIVE_PREFILTER_NODE,
        AUTHORITATIVE_DEDUPE_NODE,
    )
    graph.add_edge(AUTHORITATIVE_DEDUPE_NODE, END)
    return graph


def execute_authoritative_prefilter_dedupe_graph(
    *,
    jobs: List[Mapping[str, Any]],
    selected_role_families: List[str] | None = None,
    target_seniority: List[str] | None = None,
    seniority_strict_match: bool = False,
    filter_mode: str = "strict_live",
    role_title_audit_rows: List[Mapping[str, Any]] | None = None,
    excluded_keywords: List[str] | None = None,
    pipeline_run_id: str = "",
    owner_user_id: str = "",
    context_id: str = "",
    on_prefilter_completed: Callable[
        [
            List[Dict[str, Any]],
            Dict[str, int],
            List[Dict[str, Any]],
        ],
        None,
    ]
    | None = None,
    on_dedupe_completed: Callable[[List[Dict[str, Any]]], None]
    | None = None,
) -> Dict[str, Any]:
    caller_jobs_before = deepcopy(jobs)
    caller_audit_before = deepcopy(role_title_audit_rows)
    copied_jobs = _copy_mapping_rows(
        jobs,
        field_name="authoritative_prefilter_input_jobs",
    )
    copied_audit_rows = _copy_mapping_rows(
        list(role_title_audit_rows or []),
        field_name="authoritative_prefilter_audit_rows",
    )
    selected_roles = _copy_string_list(
        selected_role_families,
        field_name="authoritative_prefilter_selected_role_families",
        allow_none=True,
    )
    excluded = _copy_string_list(
        list(excluded_keywords or []),
        field_name="authoritative_prefilter_excluded_keywords",
    )
    canonical_targets, strict_match = normalize_seniority_filter_preferences(
        target_seniority,
        seniority_strict_match,
    )
    initial_state: AuthoritativePrefilterDedupeState = {
        "graph_version": AUTHORITATIVE_PREFILTER_DEDUPE_GRAPH_VERSION,
        "state_version": AUTHORITATIVE_PREFILTER_DEDUPE_STATE_VERSION,
        "execution_mode": "langgraph",
        "pipeline_run_id": str(pipeline_run_id or "").strip(),
        "owner_user_id": str(owner_user_id or "").strip(),
        "context_id": str(context_id or "").strip(),
        "input_jobs": copied_jobs,
        "selected_role_families": selected_roles,
        "target_seniority": canonical_targets,
        "seniority_strict_match": strict_match,
        "filter_mode": str(filter_mode or "strict_live"),
        "excluded_keywords": excluded or [],
        "role_title_audit_enabled": role_title_audit_rows is not None,
        "role_title_audit_rows": copied_audit_rows,
        "filtered_jobs": [],
        "filter_diagnostics": {},
        "deduplicated_jobs": [],
        "input_count": len(copied_jobs),
        "prefilter_output_count": 0,
        "dedupe_output_count": 0,
        "current_node": "",
        "completed_nodes": [],
        "pending_node": AUTHORITATIVE_PREFILTER_NODE,
        "status": "pending",
        "failure_classification": "",
        "prefilter_invocation_count": 0,
        "dedupe_invocation_count": 0,
        "prefilter_latency_ms": 0,
        "dedupe_latency_ms": 0,
        "deterministic": True,
        "read_only": True,
        "provider_calls_allowed": False,
        "mutation_authority": False,
        "application_authority": False,
        "ats_authority": False,
    }
    final_state = (
        build_authoritative_prefilter_dedupe_graph(
            on_prefilter_completed=on_prefilter_completed,
            on_dedupe_completed=on_dedupe_completed,
        )
        .compile()
        .invoke(initial_state)
    )
    if jobs != caller_jobs_before or role_title_audit_rows != caller_audit_before:
        raise RuntimeError(
            "authoritative_prefilter_dedupe_input_mutation_detected"
        )
    if (
        final_state.get("input_jobs") != copied_jobs
        or final_state.get("status") != "completed"
        or final_state.get("completed_nodes")
        != list(AUTHORITATIVE_PREFILTER_DEDUPE_NODE_ORDER)
        or final_state.get("pending_node")
        or final_state.get("prefilter_invocation_count") != 1
        or final_state.get("dedupe_invocation_count") != 1
    ):
        raise RuntimeError(
            "authoritative_prefilter_dedupe_graph_contract_failed"
        )

    filtered_jobs = _copy_mapping_rows(
        final_state.get("filtered_jobs"),
        field_name="authoritative_prefilter_filtered_jobs",
    )
    deduplicated_jobs = _copy_mapping_rows(
        final_state.get("deduplicated_jobs"),
        field_name="authoritative_deduplicated_jobs",
    )
    diagnostics = dict(final_state.get("filter_diagnostics") or {})
    audit_rows = _copy_mapping_rows(
        final_state.get("role_title_audit_rows"),
        field_name="authoritative_prefilter_audit_rows",
    )
    metadata = {
        "graph_version": AUTHORITATIVE_PREFILTER_DEDUPE_GRAPH_VERSION,
        "state_version": AUTHORITATIVE_PREFILTER_DEDUPE_STATE_VERSION,
        "execution_mode": "langgraph",
        "node_order": list(AUTHORITATIVE_PREFILTER_DEDUPE_NODE_ORDER),
        "production_node_count": (
            AUTHORITATIVE_PREFILTER_DEDUPE_PRODUCTION_NODE_COUNT
        ),
        "prefilter_invocation_count": 1,
        "dedupe_invocation_count": 1,
        "input_count": len(copied_jobs),
        "prefilter_output_count": len(filtered_jobs),
        "dedupe_output_count": len(deduplicated_jobs),
        "prefilter_latency_ms": max(
            0,
            min(
                int(final_state.get("prefilter_latency_ms") or 0),
                MAX_NODE_LATENCY_MS,
            ),
        ),
        "dedupe_latency_ms": max(
            0,
            min(
                int(final_state.get("dedupe_latency_ms") or 0),
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
        "filtered_jobs": filtered_jobs,
        "filter_diagnostics": diagnostics,
        "role_title_audit_rows": audit_rows,
        "deduplicated_jobs": deduplicated_jobs,
        "execution_metadata": metadata,
    }
