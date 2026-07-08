from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, List, Mapping

from src.agents.critic_agent import build_critic_resume_match_jd_evidence_artifact
from src.agents.evidence_chain_composition import (
    build_agent_evidence_chain_bundle,
    build_agent_evidence_chain_trace_payload,
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


EVIDENCE_CHAIN_EXECUTION_GATE_NAME = (
    "APPLYLENS_AGENTIC_EVIDENCE_CHAIN_EXECUTION_ENABLED"
)
EVIDENCE_CHAIN_EXECUTION_VERSION = "controlled-evidence-chain-execution-v1"
DEFAULT_SAMPLE_LIMIT = 10


FALSE_SAFETY_FLAGS = (
    "provider_call_performed",
    "live_llm_call_performed",
    "trace_persistence_performed",
    "trace_store_write_performed",
    "database_write_performed",
    "collector_output_changed",
    "production_output_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "review_queue_mutation_performed",
    "queue_mutation_performed",
    "scheduler_mutation_performed",
    "tailoring_mutation_performed",
    "source_resume_mutation_performed",
    "generated_resume_mutation_performed",
    "workflow_runner_executed",
    "application_status_changed",
    "auto_apply_performed",
    "ats_submission_performed",
    "apply_click_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
    "external_action_automation_performed",
)


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
    if isinstance(jobs, list):
        return [
            deepcopy(dict(job))
            for job in jobs
            if isinstance(job, Mapping)
        ]
    if isinstance(jobs, tuple):
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


def _base_result(
    *,
    execution_gate_enabled: bool,
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
) -> Dict[str, Any]:
    per_job_results = list(per_job_results or [])
    jobs_succeeded_count = sum(
        1 for result in per_job_results if result.get("status") in {"succeeded", "degraded"}
    )
    jobs_failed_count = sum(
        1 for result in per_job_results if result.get("status") == "failed"
    )
    aggregate_reason_codes = list(
        dict.fromkeys(
            _clean_text(code)
            for result in per_job_results
            for code in list(result.get("reason_codes") or [])
            if _clean_text(code)
        )
    )
    safety_metadata = _safety_metadata(
        automatic_internal_decisioning_performed=jobs_succeeded_count > 0
    )
    return {
        "artifact_type": "controlled_evidence_chain_execution_result",
        "artifact_version": EVIDENCE_CHAIN_EXECUTION_VERSION,
        "gate_name": EVIDENCE_CHAIN_EXECUTION_GATE_NAME,
        "execution_gate_enabled": bool(execution_gate_enabled),
        "default_off": True,
        "read_only": True,
        "diagnostic_only": True,
        "attempted": bool(attempted),
        "executed": bool(executed),
        "reason": reason,
        "jobs_received_count": jobs_received_count,
        "jobs_sampled_count": jobs_sampled_count,
        "jobs_executed_count": len(per_job_results),
        "jobs_succeeded_count": jobs_succeeded_count,
        "jobs_failed_count": jobs_failed_count,
        "sample_limit": sample_limit,
        "pipeline_run_id": pipeline_run_id,
        "owner_user_id": owner_user_id,
        "context_id": context_id,
        "include_trace_payload": bool(include_trace_payload),
        "per_job_results": per_job_results,
        "aggregate_reason_codes": aggregate_reason_codes,
        "safety_metadata": safety_metadata,
        **safety_metadata,
    }


def _execute_job(
    *,
    job: Dict[str, Any],
    index: int,
    resume_rows: List[Dict[str, Any]],
    selected_resume_id: str,
    pipeline_run_id: str,
    owner_user_id: str,
    context_id: str,
    include_trace_payload: bool,
) -> Dict[str, Any]:
    identity = _job_identity(job, index)
    jd_intelligence = describe_existing_job_intelligence_result(job)
    resume_match = build_resume_match_jd_evidence_artifact(
        jd_intelligence=jd_intelligence,
        resume_variants=resume_rows,
        selected_resume_id=selected_resume_id,
        job_id=identity["job_id"],
        title=identity["title"],
        company=identity["company"],
        enabled=True,
    )
    critic = build_critic_resume_match_jd_evidence_artifact(
        resume_match_jd_evidence=resume_match,
        jd_intelligence=jd_intelligence,
        enabled=True,
    )
    priority = build_job_prioritization_critic_evidence_artifact(
        critic_resume_match_jd_evidence=critic,
        resume_match_jd_evidence=resume_match,
        jd_intelligence=jd_intelligence,
        enabled=True,
    )
    tailoring = build_tailoring_decision_priority_evidence_artifact(
        job_prioritization_critic_evidence=priority,
        critic_resume_match_jd_evidence=critic,
        resume_match_jd_evidence=resume_match,
        jd_intelligence=jd_intelligence,
        enabled=True,
    )
    operator_review = build_operator_review_tailoring_evidence_artifact(
        tailoring_decision_priority_evidence=tailoring,
        job_prioritization_critic_evidence=priority,
        critic_resume_match_jd_evidence=critic,
        resume_match_jd_evidence=resume_match,
        jd_intelligence=jd_intelligence,
        enabled=True,
    )
    chain_id = ":".join(
        part
        for part in (
            _clean_text(pipeline_run_id),
            identity["job_id"],
            "evidence-chain",
        )
        if part
    )
    bundle = build_agent_evidence_chain_bundle(
        jd_intelligence=jd_intelligence,
        resume_match_jd_evidence=resume_match,
        critic_resume_match_jd_evidence=critic,
        job_prioritization_critic_evidence=priority,
        tailoring_decision_priority_evidence=tailoring,
        operator_review_tailoring_evidence=operator_review,
        enabled=True,
        chain_id=chain_id,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        context_id=context_id,
    )
    artifacts = {
        "jd_intelligence": jd_intelligence,
        "resume_match_jd_evidence": resume_match,
        "critic_resume_match_jd_evidence": critic,
        "job_prioritization_critic_evidence": priority,
        "tailoring_decision_priority_evidence": tailoring,
        "operator_review_tailoring_evidence": operator_review,
        "agent_evidence_chain_bundle": bundle,
    }
    if include_trace_payload:
        artifacts["agent_evidence_chain_trace_payload"] = (
            build_agent_evidence_chain_trace_payload(bundle, enabled=True)
        )

    reason_codes = _reason_codes_from_artifacts(artifacts)
    return {
        **identity,
        "status": "degraded" if reason_codes else "succeeded",
        "reason_codes": reason_codes,
        "artifacts": artifacts,
    }


def execute_controlled_evidence_chain(
    jobs: Any,
    *,
    resume_context: Any = None,
    pipeline_run_id: str | None = None,
    owner_user_id: str | None = None,
    context_id: str | None = None,
    execution_gate_enabled: bool = False,
    include_trace_payload: bool = True,
    sample_limit: Any = DEFAULT_SAMPLE_LIMIT,
    strict: bool = False,
) -> Dict[str, Any]:
    """Execute the existing evidence-chain helpers as a controlled read-only sidecar."""

    normalized_jobs = _jobs_list(jobs)
    safe_sample_limit = _safe_sample_limit(sample_limit)
    sampled_jobs = normalized_jobs[:safe_sample_limit]
    pipeline_run = _clean_text(pipeline_run_id)
    owner_user = _clean_text(owner_user_id)
    context = _clean_text(context_id)

    if not execution_gate_enabled:
        return _base_result(
            execution_gate_enabled=False,
            jobs_received_count=len(normalized_jobs),
            jobs_sampled_count=0,
            sample_limit=safe_sample_limit,
            pipeline_run_id=pipeline_run,
            owner_user_id=owner_user,
            context_id=context,
            include_trace_payload=include_trace_payload,
            attempted=False,
            executed=False,
            reason="evidence_chain_execution_disabled",
        )

    if not sampled_jobs:
        return _base_result(
            execution_gate_enabled=True,
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
    for index, job in enumerate(sampled_jobs):
        try:
            per_job_results.append(
                _execute_job(
                    job=job,
                    index=index,
                    resume_rows=resume_rows,
                    selected_resume_id=selected_resume_id,
                    pipeline_run_id=pipeline_run,
                    owner_user_id=owner_user,
                    context_id=context,
                    include_trace_payload=include_trace_payload,
                )
            )
        except Exception as exc:
            if strict:
                raise
            identity = _job_identity(job, index)
            per_job_results.append(
                {
                    **identity,
                    "status": "failed",
                    "reason_codes": ["evidence_chain_helper_failed"],
                    "artifacts": {},
                    "error_message": str(exc),
                }
            )

    failed_count = sum(1 for result in per_job_results if result.get("status") == "failed")
    reason = (
        "evidence_chain_execution_completed_with_failures"
        if failed_count
        else "evidence_chain_execution_completed"
    )
    return _base_result(
        execution_gate_enabled=True,
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
    )
