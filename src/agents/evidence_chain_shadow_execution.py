"""Explicit, process-local execution through the Operator Review pause."""

from __future__ import annotations

from copy import deepcopy
import hashlib
from pathlib import Path
import time
from types import SimpleNamespace
from typing import Any, Dict, Mapping, Sequence

from src.agents.evidence_chain_shadow_adapter import (
    adapt_completed_planning_artifacts,
)
from src.agents.evidence_chain_shadow_parity import (
    canonical_artifact_digest,
    compare_shadow_parity,
)


SHADOW_EXECUTION_VERSION = "evidence-chain-shadow-execution-v1"
EXPECTED_NODE_ORDER = (
    "jd_intelligence",
    "resume_match",
    "critic",
    "job_prioritization",
    "tailoring_decision",
    "operator_review",
)
MAX_SHADOW_JOBS = 25
MAX_COMPARISONS_PER_JOB = 100


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _file_digest(path: str | Path | None) -> str:
    if path is None:
        return ""
    resolved = Path(path)
    if not resolved.is_file():
        return ""
    digest = hashlib.sha256()
    with resolved.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _artifact_path_digests(paths: Mapping[str, str | Path | None]) -> Dict[str, str]:
    return {key: _file_digest(value) for key, value in sorted(paths.items())}


def _bounded_codes(values: Any) -> list[str]:
    if not isinstance(values, list):
        return []
    result = []
    for value in values:
        text = _clean_text(value)
        if text and text.replace("_", "").replace("-", "").replace(".", "").isalnum():
            result.append(text[:120])
    return sorted(set(result))[:50]


def _shadow_facts(session: Any, pause_result: Mapping[str, Any], latency_ms: int) -> Dict[str, Any]:
    state = getattr(session, "_paused_state", None)
    if not isinstance(state, Mapping):
        raise ValueError("shadow_paused_state_malformed")
    ordered = list(state.get("ordered_node_keys") or [])
    if ordered != list(EXPECTED_NODE_ORDER):
        raise ValueError("shadow_completed_node_order_malformed")
    if list(pause_result.get("completed_node_keys") or []) != ordered:
        raise ValueError("shadow_completed_node_result_mismatch")
    if _clean_text(pause_result.get("safe_next_node")) != "finalize":
        raise ValueError("shadow_unexpected_pending_node")

    artifacts = state.get("artifacts")
    if not isinstance(artifacts, Mapping):
        raise ValueError("shadow_artifacts_malformed")
    if (
        "evidence_chain_bundle" in state
        or "trace_payload" in state
        or "agent_evidence_chain_bundle" in artifacts
        or "agent_evidence_chain_trace_payload" in artifacts
    ):
        raise ValueError("shadow_finalize_executed")
    node_statuses = list(state.get("node_statuses") or [])
    if len(node_statuses) != len(EXPECTED_NODE_ORDER):
        raise ValueError("shadow_node_statuses_malformed")
    bounded_statuses: Dict[str, str] = {}
    reason_codes: list[str] = []
    for expected, summary in zip(EXPECTED_NODE_ORDER, node_statuses):
        if not isinstance(summary, Mapping) or _clean_text(summary.get("node_key")) != expected:
            raise ValueError("shadow_node_statuses_malformed")
        bounded_statuses[expected] = _clean_text(summary.get("status"))[:40]
        reason_codes.extend(_bounded_codes(summary.get("reason_codes")))
    artifact_digests = {
        key: canonical_artifact_digest(value)
        for key, value in sorted(artifacts.items())
        if isinstance(value, Mapping)
    }
    operator_artifact = artifacts.get("operator_review_tailoring_evidence")
    recommendation = ""
    if isinstance(operator_artifact, Mapping):
        recommendation = _clean_text(
            operator_artifact.get("operator_review_lane")
            or operator_artifact.get("operator_review_readiness")
        )[:80]
    return {
        "pipeline_run_id": _clean_text(state.get("pipeline_run_id")),
        "job_id": _clean_text(dict(state.get("job_identity") or {}).get("job_id")),
        "selected_resume_id": _clean_text(state.get("selected_resume_id")),
        "completed_node_order": ordered,
        "node_statuses": bounded_statuses,
        "pending_node": "finalize",
        "finalization_executed": False,
        "final_bundle_present": False,
        "final_trace_present": False,
        "recommendation": recommendation,
        "warnings": _bounded_codes(state.get("warnings")),
        "reason_codes": sorted(set(reason_codes)),
        "artifact_digests": artifact_digests,
        "graph_failure_classification": "",
        "graph_latency_ms": max(0, int(latency_ms)),
    }


def _parity_specs(
    authoritative_specs: Sequence[Mapping[str, Any]],
    shadow_facts: Mapping[str, Any],
) -> list[Dict[str, Any]]:
    if len(authoritative_specs) > MAX_COMPARISONS_PER_JOB:
        raise ValueError("authoritative_comparison_limit_exceeded")
    specs: list[Dict[str, Any]] = []
    for raw in authoritative_specs:
        if not isinstance(raw, Mapping):
            raise ValueError("authoritative_comparison_malformed")
        spec = deepcopy(dict(raw))
        field = _clean_text(spec.get("field"))
        shadow_field = _clean_text(spec.pop("shadow_field", "")) or field
        if spec.get("mode") != "incomparable":
            if shadow_field in shadow_facts:
                spec["shadow_value"] = deepcopy(shadow_facts[shadow_field])
            else:
                spec["shadow_present"] = False
        specs.append(spec)
    specs.append(
        {
            "field": "human_finalization_outcome",
            "mode": "incomparable",
            "reason": "shadow_stops_at_operator_review",
        }
    )
    return specs


def _start_readonly_pause(initial_state: Mapping[str, Any]) -> tuple[Any, Dict[str, Any]]:
    from copy import deepcopy
    from langgraph.checkpoint.memory import InMemorySaver
    from src.agents.evidence_chain_langgraph_harness import (
        _compile_operator_review_pause_resume_graph,
        _experimental_state_lookup_config,
        _validate_paused_operator_review_state,
    )

    checkpointer = InMemorySaver()
    graph = _compile_operator_review_pause_resume_graph(checkpointer)
    graph_invocation_id = _clean_text(
        initial_state.get("graph_invocation_id")
        or dict(initial_state.get("job_identity") or {}).get("job_id")
    )
    config = {
        "configurable": {
            "thread_id": graph_invocation_id,
            "checkpoint_ns": "",
        }
    }
    graph.invoke(deepcopy(dict(initial_state)), deepcopy(config))
    snapshot = graph.get_state(
        _experimental_state_lookup_config(config, checkpointer)
    )
    paused_state = deepcopy(dict(snapshot.values or {}))
    _validate_paused_operator_review_state(paused_state)
    return (
        SimpleNamespace(
            _paused_state=paused_state,
            _checkpointer=checkpointer,
            _compiled_graph=graph,
        ),
        {
            "completed_node_keys": list(paused_state.get("ordered_node_keys") or []),
            "safe_next_node": (
                tuple(snapshot.next)[0] if len(tuple(snapshot.next)) == 1 else ""
            ),
        },
    )


def execute_readonly_shadow(
    *,
    job_ids: Sequence[str],
    owner_id: str,
    pipeline_run_id: str,
    context_id: str,
    resume_evidence_by_id: Mapping[str, Sequence[Mapping[str, Any]]],
    authoritative_comparisons_by_job: Mapping[str, Sequence[Mapping[str, Any]]],
    include_trace_payload: bool,
    job_corpus_rows: Sequence[Mapping[str, Any]] | None = None,
    best_resume_rows: Sequence[Mapping[str, Any]] | None = None,
    execution_queue_rows: Sequence[Mapping[str, Any]] | None = None,
    packet_manifest_rows: Sequence[Mapping[str, Any]] | None = None,
    job_corpus_path: str | Path | None = None,
    best_resume_path: str | Path | None = None,
    execution_queue_path: str | Path | None = None,
    packet_manifest_path: str | Path | None = None,
    _session_starter: Any = None,
) -> Dict[str, Any]:
    """Execute isolated jobs through Operator Review without resuming."""

    normalized_jobs = [_clean_text(job_id) for job_id in job_ids if _clean_text(job_id)]
    if not normalized_jobs or len(normalized_jobs) > MAX_SHADOW_JOBS:
        raise ValueError("shadow_job_count_invalid")
    if len(normalized_jobs) != len(set(normalized_jobs)):
        raise ValueError("shadow_job_identity_duplicate")
    artifact_paths = {
        "best_resume": best_resume_path,
        "execution_queue": execution_queue_path,
        "job_corpus": job_corpus_path,
        "packet_manifest": packet_manifest_path,
    }
    before_digests = _artifact_path_digests(artifact_paths)
    results: list[Dict[str, Any]] = []

    for job_id in normalized_jobs:
        adapted = adapt_completed_planning_artifacts(
            owner_id=owner_id,
            pipeline_run_id=pipeline_run_id,
            context_id=context_id,
            job_id=job_id,
            resume_evidence_by_id=resume_evidence_by_id,
            include_trace_payload=include_trace_payload,
            job_corpus_rows=job_corpus_rows,
            best_resume_rows=best_resume_rows,
            execution_queue_rows=execution_queue_rows,
            packet_manifest_rows=packet_manifest_rows,
            job_corpus_path=job_corpus_path,
            best_resume_path=best_resume_path,
            execution_queue_path=execution_queue_path,
            packet_manifest_path=packet_manifest_path,
        )
        if adapted.get("status") != "success":
            results.append(
                {
                    "job_id": job_id,
                    "status": "input_rejected",
                    "failure_code": _clean_text(adapted.get("failure_code")),
                }
            )
            continue
        graph_input = dict(adapted["graph_input"])
        initial_state = dict(graph_input["initial_state"])
        try:
            if _session_starter is None:
                starter = _start_readonly_pause
            else:
                starter = _session_starter
            started = time.perf_counter()
            session, pause_result = starter(
                {
                    **initial_state,
                    "graph_invocation_id": graph_input["graph_invocation_id"],
                }
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
        except ImportError:
            results.append(
                {"job_id": job_id, "status": "graph_construction_failed"}
            )
            continue
        except (RuntimeError, ValueError) as exc:
            code = _clean_text(exc)
            status = (
                "graph_output_malformed"
                if any(token in code for token in ("pause", "pending", "malformed", "finalize"))
                else "graph_execution_failed"
            )
            results.append({"job_id": job_id, "status": status})
            continue
        if session is None or not isinstance(pause_result, Mapping):
            results.append({"job_id": job_id, "status": "graph_output_malformed"})
            continue
        try:
            facts = _shadow_facts(session, pause_result, latency_ms)
        except (TypeError, ValueError):
            results.append({"job_id": job_id, "status": "graph_output_malformed"})
            continue
        try:
            specs = _parity_specs(
                authoritative_comparisons_by_job.get(job_id, ()),
                facts,
            )
            parity = compare_shadow_parity(
                pipeline_run_id=pipeline_run_id,
                job_id=job_id,
                selected_resume_id=graph_input["selected_resume_id"],
                fields=specs,
                warnings=facts["warnings"],
            )
        except (TypeError, ValueError):
            results.append({"job_id": job_id, "status": "parity_failed"})
            continue
        results.append(
            {
                "job_id": job_id,
                "status": "parity_completed",
                "execution_status": "completed_at_operator_review",
                "graph_invocation_id": graph_input["graph_invocation_id"],
                "shadow_facts": facts,
                "parity": parity,
            }
        )

    after_digests = _artifact_path_digests(artifact_paths)
    artifacts_unchanged = before_digests == after_digests
    if not artifacts_unchanged:
        for result in results:
            result["status"] = "write_suppression_violation"
            result.pop("parity", None)
    return {
        "execution_version": SHADOW_EXECUTION_VERSION,
        "status": (
            "write_suppression_violation"
            if not artifacts_unchanged
            else "completed"
        ),
        "owner_id": _clean_text(owner_id),
        "pipeline_run_id": _clean_text(pipeline_run_id),
        "context_id": _clean_text(context_id),
        "job_count": len(normalized_jobs),
        "artifacts_unchanged": artifacts_unchanged,
        "results": results,
    }
