from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping, TypedDict

from src.agents.critic_agent import build_critic_resume_match_jd_evidence_artifact
from src.agents.evidence_chain_composition import (
    ORDERED_AGENT_KEYS,
    build_agent_evidence_chain_bundle,
    build_agent_evidence_chain_trace_payload,
)
from src.agents.evidence_chain_execution import (
    DEFAULT_SAMPLE_LIMIT,
    FALSE_SAFETY_FLAGS,
)
from src.agents.jd_intelligence import describe_existing_job_intelligence_result
from src.agents.job_prioritization_agent import (
    build_job_prioritization_critic_evidence_artifact,
)
from src.agents.operator_review_agent import (
    build_operator_review_tailoring_evidence_artifact,
)
from src.agents.resume_match_agent import build_resume_match_jd_evidence_artifact
from src.agents.tailoring_decision_agent import (
    build_tailoring_decision_priority_evidence_artifact,
)


LANGGRAPH_EVIDENCE_CHAIN_GATE_NAME = (
    "APPLYLENS_AGENTIC_LANGGRAPH_EVIDENCE_CHAIN_ENABLED"
)
LANGGRAPH_EVIDENCE_CHAIN_VERSION = "langgraph-evidence-chain-harness-v1"
ARTIFACT_KEYS_BY_AGENT = {
    "jd_intelligence": "jd_intelligence",
    "resume_match": "resume_match_jd_evidence",
    "critic": "critic_resume_match_jd_evidence",
    "job_prioritization": "job_prioritization_critic_evidence",
    "tailoring_decision": "tailoring_decision_priority_evidence",
    "operator_review": "operator_review_tailoring_evidence",
}


class EvidenceChainGraphState(TypedDict, total=False):
    job: Dict[str, Any]
    job_index: int
    job_identity: Dict[str, str]
    resume_rows: List[Dict[str, Any]]
    selected_resume_id: str
    pipeline_run_id: str
    owner_user_id: str
    context_id: str
    include_trace_payload: bool
    artifacts: Dict[str, Any]
    ordered_node_keys: List[str]
    node_statuses: List[Dict[str, Any]]
    warnings: List[str]
    evidence_chain_bundle: Dict[str, Any]
    trace_payload: Dict[str, Any]


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _safe_sample_limit(value: Any) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = DEFAULT_SAMPLE_LIMIT
    if parsed < 0:
        return 0
    return min(parsed, DEFAULT_SAMPLE_LIMIT)


def _jobs_list(jobs: Any) -> List[Dict[str, Any]]:
    if jobs is None:
        return []
    if isinstance(jobs, Mapping):
        return [deepcopy(dict(jobs))]
    if isinstance(jobs, (list, tuple)):
        return [
            deepcopy(dict(job))
            for job in jobs
            if isinstance(job, Mapping)
        ]
    return []


def _resume_rows_and_selection(
    resume_context: Any,
) -> tuple[List[Dict[str, Any]], str]:
    if resume_context is None:
        return [], ""
    if isinstance(resume_context, list):
        return [
            deepcopy(dict(row))
            for row in resume_context
            if isinstance(row, Mapping)
        ], ""
    if not isinstance(resume_context, Mapping):
        return [], ""

    context = dict(resume_context)
    raw_rows = (
        context.get("resume_variants")
        if context.get("resume_variants") is not None
        else context.get("resume_evidence_rows")
    )
    if raw_rows is None and any(
        key in context
        for key in ("resume_id", "skills", "raw_text", "bullets", "tools")
    ):
        raw_rows = [context]
    rows = [
        deepcopy(dict(row))
        for row in list(raw_rows or [])
        if isinstance(row, Mapping)
    ]
    return rows, _clean_text(context.get("selected_resume_id"))


def _job_identity(job: Mapping[str, Any], index: int) -> Dict[str, str]:
    return {
        "job_id": _clean_text(
            job.get("job_id")
            or job.get("id")
            or job.get("job_key")
            or f"sampled-job-{index + 1}"
        ),
        "title": _clean_text(job.get("title") or job.get("job_title")),
        "company": _clean_text(job.get("company")),
    }


def _safety_metadata(*, automatic_internal_decisioning_performed: bool) -> Dict[str, bool]:
    return {
        **{flag: False for flag in FALSE_SAFETY_FLAGS},
        "automatic_internal_decisioning_performed": bool(
            automatic_internal_decisioning_performed
        ),
    }


def _reason_codes_from_artifacts(artifacts: Mapping[str, Any]) -> List[str]:
    reason_codes: List[str] = []
    for artifact in artifacts.values():
        if isinstance(artifact, Mapping):
            reason_codes.extend(
                _clean_text(code)
                for code in list(artifact.get("reason_codes") or [])
                if _clean_text(code)
            )
            reason_codes.extend(
                _clean_text(code)
                for code in list(artifact.get("chain_reason_codes") or [])
                if _clean_text(code)
            )
    return list(dict.fromkeys(reason_codes))


def _node_summary(agent_key: str, artifact: Any) -> Dict[str, Any]:
    artifact_type = artifact.get("artifact_type", "") if isinstance(artifact, Mapping) else ""
    reason_codes = artifact.get("reason_codes", []) if isinstance(artifact, Mapping) else []
    return {
        "agent_key": agent_key,
        "node_key": agent_key,
        "status": "completed",
        "artifact_key": ARTIFACT_KEYS_BY_AGENT[agent_key],
        "artifact_type": _clean_text(artifact_type),
        "reason_codes": [
            _clean_text(code)
            for code in list(reason_codes or [])
            if _clean_text(code)
        ],
    }


def _state_with_artifact(
    state: EvidenceChainGraphState,
    *,
    agent_key: str,
    artifact_key: str,
    artifact: Dict[str, Any],
) -> EvidenceChainGraphState:
    next_state: EvidenceChainGraphState = dict(state)
    artifacts = dict(next_state.get("artifacts") or {})
    artifacts[artifact_key] = artifact
    next_state["artifacts"] = artifacts
    next_state["ordered_node_keys"] = [
        *list(next_state.get("ordered_node_keys") or []),
        agent_key,
    ]
    next_state["node_statuses"] = [
        *list(next_state.get("node_statuses") or []),
        _node_summary(agent_key, artifact),
    ]
    return next_state


def _jd_intelligence_node(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    artifact = describe_existing_job_intelligence_result(dict(state.get("job") or {}))
    return _state_with_artifact(
        state,
        agent_key="jd_intelligence",
        artifact_key="jd_intelligence",
        artifact=artifact,
    )


def _resume_match_node(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    identity = dict(state.get("job_identity") or {})
    artifacts = dict(state.get("artifacts") or {})
    artifact = build_resume_match_jd_evidence_artifact(
        jd_intelligence=dict(artifacts.get("jd_intelligence") or {}),
        resume_variants=list(state.get("resume_rows") or []),
        selected_resume_id=_clean_text(state.get("selected_resume_id")),
        job_id=_clean_text(identity.get("job_id")),
        title=_clean_text(identity.get("title")),
        company=_clean_text(identity.get("company")),
        enabled=True,
    )
    return _state_with_artifact(
        state,
        agent_key="resume_match",
        artifact_key="resume_match_jd_evidence",
        artifact=artifact,
    )


def _critic_node(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    artifacts = dict(state.get("artifacts") or {})
    artifact = build_critic_resume_match_jd_evidence_artifact(
        resume_match_jd_evidence=dict(artifacts.get("resume_match_jd_evidence") or {}),
        jd_intelligence=dict(artifacts.get("jd_intelligence") or {}),
        enabled=True,
    )
    return _state_with_artifact(
        state,
        agent_key="critic",
        artifact_key="critic_resume_match_jd_evidence",
        artifact=artifact,
    )


def _job_prioritization_node(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    artifacts = dict(state.get("artifacts") or {})
    artifact = build_job_prioritization_critic_evidence_artifact(
        critic_resume_match_jd_evidence=dict(
            artifacts.get("critic_resume_match_jd_evidence") or {}
        ),
        resume_match_jd_evidence=dict(artifacts.get("resume_match_jd_evidence") or {}),
        jd_intelligence=dict(artifacts.get("jd_intelligence") or {}),
        enabled=True,
    )
    return _state_with_artifact(
        state,
        agent_key="job_prioritization",
        artifact_key="job_prioritization_critic_evidence",
        artifact=artifact,
    )


def _tailoring_decision_node(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    artifacts = dict(state.get("artifacts") or {})
    artifact = build_tailoring_decision_priority_evidence_artifact(
        job_prioritization_critic_evidence=dict(
            artifacts.get("job_prioritization_critic_evidence") or {}
        ),
        critic_resume_match_jd_evidence=dict(
            artifacts.get("critic_resume_match_jd_evidence") or {}
        ),
        resume_match_jd_evidence=dict(artifacts.get("resume_match_jd_evidence") or {}),
        jd_intelligence=dict(artifacts.get("jd_intelligence") or {}),
        enabled=True,
    )
    return _state_with_artifact(
        state,
        agent_key="tailoring_decision",
        artifact_key="tailoring_decision_priority_evidence",
        artifact=artifact,
    )


def _operator_review_node(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    artifacts = dict(state.get("artifacts") or {})
    artifact = build_operator_review_tailoring_evidence_artifact(
        tailoring_decision_priority_evidence=dict(
            artifacts.get("tailoring_decision_priority_evidence") or {}
        ),
        job_prioritization_critic_evidence=dict(
            artifacts.get("job_prioritization_critic_evidence") or {}
        ),
        critic_resume_match_jd_evidence=dict(
            artifacts.get("critic_resume_match_jd_evidence") or {}
        ),
        resume_match_jd_evidence=dict(artifacts.get("resume_match_jd_evidence") or {}),
        jd_intelligence=dict(artifacts.get("jd_intelligence") or {}),
        enabled=True,
    )
    return _state_with_artifact(
        state,
        agent_key="operator_review",
        artifact_key="operator_review_tailoring_evidence",
        artifact=artifact,
    )


def _finalize_node(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    artifacts = dict(state.get("artifacts") or {})
    identity = dict(state.get("job_identity") or {})
    chain_id = ":".join(
        part
        for part in (
            _clean_text(state.get("pipeline_run_id")),
            _clean_text(identity.get("job_id")),
            "langgraph-evidence-chain",
        )
        if part
    )
    bundle = build_agent_evidence_chain_bundle(
        jd_intelligence=dict(artifacts.get("jd_intelligence") or {}),
        resume_match_jd_evidence=dict(artifacts.get("resume_match_jd_evidence") or {}),
        critic_resume_match_jd_evidence=dict(
            artifacts.get("critic_resume_match_jd_evidence") or {}
        ),
        job_prioritization_critic_evidence=dict(
            artifacts.get("job_prioritization_critic_evidence") or {}
        ),
        tailoring_decision_priority_evidence=dict(
            artifacts.get("tailoring_decision_priority_evidence") or {}
        ),
        operator_review_tailoring_evidence=dict(
            artifacts.get("operator_review_tailoring_evidence") or {}
        ),
        enabled=True,
        chain_id=chain_id,
        pipeline_run_id=_clean_text(state.get("pipeline_run_id")),
        owner_user_id=_clean_text(state.get("owner_user_id")),
        context_id=_clean_text(state.get("context_id")),
    )
    next_state: EvidenceChainGraphState = dict(state)
    artifacts["agent_evidence_chain_bundle"] = bundle
    next_state["evidence_chain_bundle"] = bundle
    if bool(state.get("include_trace_payload")):
        trace_payload = build_agent_evidence_chain_trace_payload(bundle, enabled=True)
        artifacts["agent_evidence_chain_trace_payload"] = trace_payload
        next_state["trace_payload"] = trace_payload
    next_state["artifacts"] = artifacts
    return next_state


def _compile_graph() -> Any:
    from langgraph.graph import END, StateGraph

    graph = StateGraph(EvidenceChainGraphState)
    graph.add_node("jd_intelligence", _jd_intelligence_node)
    graph.add_node("resume_match", _resume_match_node)
    graph.add_node("critic", _critic_node)
    graph.add_node("job_prioritization", _job_prioritization_node)
    graph.add_node("tailoring_decision", _tailoring_decision_node)
    graph.add_node("operator_review", _operator_review_node)
    graph.add_node("finalize", _finalize_node)
    graph.set_entry_point("jd_intelligence")
    graph.add_edge("jd_intelligence", "resume_match")
    graph.add_edge("resume_match", "critic")
    graph.add_edge("critic", "job_prioritization")
    graph.add_edge("job_prioritization", "tailoring_decision")
    graph.add_edge("tailoring_decision", "operator_review")
    graph.add_edge("operator_review", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


def _execute_graph_state(state: EvidenceChainGraphState) -> EvidenceChainGraphState:
    compiled_graph = _compile_graph()
    return compiled_graph.invoke(state)


def _per_job_result_from_state(state: EvidenceChainGraphState) -> Dict[str, Any]:
    identity = dict(state.get("job_identity") or {})
    artifacts = dict(state.get("artifacts") or {})
    reason_codes = _reason_codes_from_artifacts(artifacts)
    ordered_node_keys = list(state.get("ordered_node_keys") or [])
    node_statuses = list(state.get("node_statuses") or [])
    return {
        **identity,
        "status": "degraded" if reason_codes else "succeeded",
        "reason_codes": reason_codes,
        "graph_runtime": "langgraph",
        "ordered_node_keys": ordered_node_keys,
        "ordered_agent_keys": list(ORDERED_AGENT_KEYS),
        "node_statuses": node_statuses,
        "artifacts": artifacts,
        "evidence_chain_bundle": artifacts.get("agent_evidence_chain_bundle", {}),
        "trace_payload": artifacts.get("agent_evidence_chain_trace_payload", {}),
        "safety_metadata": _safety_metadata(
            automatic_internal_decisioning_performed=True
        ),
    }


def _base_result(
    *,
    enabled: bool,
    jobs_received_count: int,
    jobs_sampled_count: int,
    sample_limit: int,
    pipeline_run_id: str,
    owner_user_id: str,
    context_id: str,
    include_trace_payload: bool,
    attempted: bool,
    executed: bool,
    reason: str,
    per_job_results: List[Dict[str, Any]] | None = None,
    warnings: List[str] | None = None,
) -> Dict[str, Any]:
    per_job_results = list(per_job_results or [])
    succeeded_count = sum(
        1 for result in per_job_results if result.get("status") in {"succeeded", "degraded"}
    )
    failed_count = sum(1 for result in per_job_results if result.get("status") == "failed")
    safety_metadata = _safety_metadata(
        automatic_internal_decisioning_performed=succeeded_count > 0
    )
    return {
        "artifact_type": "langgraph_evidence_chain_execution",
        "artifact_version": LANGGRAPH_EVIDENCE_CHAIN_VERSION,
        "gate_name": LANGGRAPH_EVIDENCE_CHAIN_GATE_NAME,
        "enabled": bool(enabled),
        "execution_gate_enabled": bool(enabled),
        "graph_runtime": "langgraph",
        "default_off": True,
        "explicit_call_only": True,
        "read_only": True,
        "diagnostic_only": True,
        "attempted": bool(attempted),
        "executed": bool(executed),
        "reason": reason,
        "job_count": jobs_received_count,
        "jobs_received_count": jobs_received_count,
        "jobs_sampled_count": jobs_sampled_count,
        "processed_count": len(per_job_results),
        "jobs_executed_count": len(per_job_results),
        "jobs_succeeded_count": succeeded_count,
        "jobs_failed_count": failed_count,
        "sample_limit": sample_limit,
        "pipeline_run_id": pipeline_run_id,
        "owner_user_id": owner_user_id,
        "context_id": context_id,
        "include_trace_payload": bool(include_trace_payload),
        "ordered_agent_keys": list(ORDERED_AGENT_KEYS),
        "per_job_results": per_job_results,
        "warnings": list(warnings or []),
        "safety_metadata": safety_metadata,
        **safety_metadata,
    }


def execute_langgraph_evidence_chain(
    jobs: Any,
    *,
    pipeline_run_id: str | None = None,
    owner_user_id: str | None = None,
    context_id: str | None = None,
    resume_context: Any = None,
    sample_limit: Any = DEFAULT_SAMPLE_LIMIT,
    include_trace_payload: bool = True,
    enabled: bool = False,
    strict: bool = False,
) -> Dict[str, Any]:
    """Run the existing evidence chain through an explicit default-off LangGraph harness."""

    normalized_jobs = _jobs_list(jobs)
    safe_sample_limit = _safe_sample_limit(sample_limit)
    sampled_jobs = normalized_jobs[:safe_sample_limit]
    pipeline_run = _clean_text(pipeline_run_id)
    owner_user = _clean_text(owner_user_id)
    context = _clean_text(context_id)

    if not enabled:
        return _base_result(
            enabled=False,
            jobs_received_count=len(normalized_jobs),
            jobs_sampled_count=0,
            sample_limit=safe_sample_limit,
            pipeline_run_id=pipeline_run,
            owner_user_id=owner_user,
            context_id=context,
            include_trace_payload=include_trace_payload,
            attempted=False,
            executed=False,
            reason="langgraph_evidence_chain_disabled",
        )

    if not sampled_jobs:
        return _base_result(
            enabled=True,
            jobs_received_count=len(normalized_jobs),
            jobs_sampled_count=0,
            sample_limit=safe_sample_limit,
            pipeline_run_id=pipeline_run,
            owner_user_id=owner_user,
            context_id=context,
            include_trace_payload=include_trace_payload,
            attempted=True,
            executed=False,
            reason="no_jobs_sampled",
        )

    resume_rows, selected_resume_id = _resume_rows_and_selection(resume_context)
    per_job_results: List[Dict[str, Any]] = []
    warnings: List[str] = []
    for index, job in enumerate(sampled_jobs):
        identity = _job_identity(job, index)
        initial_state: EvidenceChainGraphState = {
            "job": deepcopy(job),
            "job_index": index,
            "job_identity": identity,
            "resume_rows": deepcopy(resume_rows),
            "selected_resume_id": selected_resume_id,
            "pipeline_run_id": pipeline_run,
            "owner_user_id": owner_user,
            "context_id": context,
            "include_trace_payload": bool(include_trace_payload),
            "artifacts": {},
            "ordered_node_keys": [],
            "node_statuses": [],
            "warnings": [],
        }
        try:
            final_state = _execute_graph_state(initial_state)
            per_job_results.append(_per_job_result_from_state(final_state))
        except Exception as exc:
            if strict:
                raise
            warnings.append("langgraph_evidence_chain_job_failed")
            per_job_results.append(
                {
                    **identity,
                    "status": "failed",
                    "reason_codes": ["langgraph_evidence_chain_job_failed"],
                    "graph_runtime": "langgraph",
                    "ordered_node_keys": [],
                    "ordered_agent_keys": list(ORDERED_AGENT_KEYS),
                    "node_statuses": [],
                    "artifacts": {},
                    "error_message": str(exc),
                    "safety_metadata": _safety_metadata(
                        automatic_internal_decisioning_performed=False
                    ),
                }
            )

    failed_count = sum(1 for result in per_job_results if result.get("status") == "failed")
    reason = (
        "langgraph_evidence_chain_completed_with_failures"
        if failed_count
        else "langgraph_evidence_chain_completed"
    )
    return _base_result(
        enabled=True,
        jobs_received_count=len(normalized_jobs),
        jobs_sampled_count=len(sampled_jobs),
        sample_limit=safe_sample_limit,
        pipeline_run_id=pipeline_run,
        owner_user_id=owner_user,
        context_id=context,
        include_trace_payload=include_trace_payload,
        attempted=True,
        executed=True,
        reason=reason,
        per_job_results=per_job_results,
        warnings=warnings,
    )
