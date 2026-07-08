import ast
from copy import deepcopy
from pathlib import Path

import pytest

from src.agents import evidence_chain_execution


ROOT = Path(__file__).resolve().parents[1]
GATE = "APPLYLENS_AGENTIC_EVIDENCE_CHAIN_EXECUTION_ENABLED"
FALSE_SAFETY_FLAGS = [
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
]


def _job(job_id="job-98b", **overrides):
    payload = {
        "job_id": job_id,
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "url": "https://example.test/jobs/98b",
        "intelligence": {
            "skills": {
                "required": ["Python", "SQL"],
                "preferred": ["RAG"],
                "all": ["Python", "SQL", "RAG"],
            },
            "visa_sponsorship": "unknown",
        },
        "ai_fit_score": 8,
        "priority_score": 12.5,
    }
    payload.update(overrides)
    return payload


def _resume_context():
    return {
        "selected_resume_id": "resume-main",
        "resume_variants": [
            {
                "resume_id": "resume-main",
                "skills": ["Python", "SQL", "RAG"],
                "raw_text": "Built Python, SQL, and RAG systems.",
            }
        ],
    }


def _assert_safe(payload, *, internal_decisioning):
    assert payload["default_off"] is True
    assert payload["read_only"] is True
    assert payload["diagnostic_only"] is True
    assert payload["gate_name"] == GATE
    for flag in FALSE_SAFETY_FLAGS:
        assert payload[flag] is False
        assert payload["safety_metadata"][flag] is False
    assert (
        payload["automatic_internal_decisioning_performed"] is internal_decisioning
    )
    assert (
        payload["safety_metadata"]["automatic_internal_decisioning_performed"]
        is internal_decisioning
    )


def _patch_success_chain(monkeypatch, calls):
    def jd(job):
        calls.append("jd_intelligence")
        return {
            "status": "completed",
            "job_id": job["job_id"],
            "title": job["title"],
            "company": job["company"],
            "required_skills": ["Python"],
            "preferred_skills": ["SQL"],
            "validation_json": {
                "is_valid_for_existing_output_wrapper": True,
                "missing_or_invalid_fields": [],
            },
            "reason_codes": [],
        }

    def resume_match(**kwargs):
        calls.append("resume_match")
        return {
            "artifact_type": "resume_match_jd_evidence",
            "job_id": kwargs["job_id"],
            "title": kwargs["title"],
            "company": kwargs["company"],
            "reason_codes": [],
        }

    def critic(**kwargs):
        calls.append("critic")
        return {
            "artifact_type": "critic_resume_match_jd_evidence",
            "job_id": kwargs["resume_match_jd_evidence"]["job_id"],
            "reason_codes": [],
        }

    def priority(**kwargs):
        calls.append("job_prioritization")
        return {
            "artifact_type": "job_prioritization_critic_evidence",
            "job_id": kwargs["critic_resume_match_jd_evidence"]["job_id"],
            "reason_codes": [],
        }

    def tailoring(**kwargs):
        calls.append("tailoring_decision")
        return {
            "artifact_type": "tailoring_decision_priority_evidence",
            "job_id": kwargs["job_prioritization_critic_evidence"]["job_id"],
            "reason_codes": [],
        }

    def operator_review(**kwargs):
        calls.append("operator_review")
        return {
            "artifact_type": "operator_review_tailoring_evidence",
            "job_id": kwargs["tailoring_decision_priority_evidence"]["job_id"],
            "reason_codes": [],
        }

    def bundle(**kwargs):
        calls.append("bundle")
        return {
            "artifact_type": "agent_evidence_chain_bundle",
            "chain_id": kwargs["chain_id"],
            "chain_reason_codes": [],
        }

    def trace_payload(bundle, **kwargs):
        calls.append("trace_payload")
        return {
            "artifact_type": "agent_evidence_chain_trace_payload",
            "chain_id": bundle["chain_id"],
            "reason_codes": [],
        }

    monkeypatch.setattr(
        evidence_chain_execution,
        "describe_existing_job_intelligence_result",
        jd,
    )
    monkeypatch.setattr(
        evidence_chain_execution,
        "build_resume_match_jd_evidence_artifact",
        resume_match,
    )
    monkeypatch.setattr(
        evidence_chain_execution,
        "build_critic_resume_match_jd_evidence_artifact",
        critic,
    )
    monkeypatch.setattr(
        evidence_chain_execution,
        "build_job_prioritization_critic_evidence_artifact",
        priority,
    )
    monkeypatch.setattr(
        evidence_chain_execution,
        "build_tailoring_decision_priority_evidence_artifact",
        tailoring,
    )
    monkeypatch.setattr(
        evidence_chain_execution,
        "build_operator_review_tailoring_evidence_artifact",
        operator_review,
    )
    monkeypatch.setattr(
        evidence_chain_execution,
        "build_agent_evidence_chain_bundle",
        bundle,
    )
    monkeypatch.setattr(
        evidence_chain_execution,
        "build_agent_evidence_chain_trace_payload",
        trace_payload,
    )


def test_gate_off_skips_without_helper_calls_or_input_mutation(monkeypatch):
    calls = []
    _patch_success_chain(monkeypatch, calls)
    jobs = [_job()]
    before = deepcopy(jobs)

    payload = evidence_chain_execution.execute_controlled_evidence_chain(
        jobs,
        resume_context=_resume_context(),
        execution_gate_enabled=False,
        strict=True,
    )

    assert payload["artifact_type"] == "controlled_evidence_chain_execution_result"
    assert payload["artifact_version"] == "controlled-evidence-chain-execution-v1"
    assert payload["execution_gate_enabled"] is False
    assert payload["attempted"] is False
    assert payload["executed"] is False
    assert payload["reason"] == "evidence_chain_execution_disabled"
    assert payload["jobs_received_count"] == 1
    assert payload["jobs_sampled_count"] == 0
    assert payload["jobs_executed_count"] == 0
    assert payload["per_job_results"] == []
    assert calls == []
    assert jobs == before
    _assert_safe(payload, internal_decisioning=False)


def test_gate_on_single_job_executes_phase89_to_95_in_order(monkeypatch):
    calls = []
    _patch_success_chain(monkeypatch, calls)
    job = _job()
    before = deepcopy(job)

    payload = evidence_chain_execution.execute_controlled_evidence_chain(
        job,
        resume_context=_resume_context(),
        pipeline_run_id="run-98b",
        owner_user_id="owner-98b",
        context_id="ctx-98b",
        execution_gate_enabled=True,
    )

    assert calls == [
        "jd_intelligence",
        "resume_match",
        "critic",
        "job_prioritization",
        "tailoring_decision",
        "operator_review",
        "bundle",
        "trace_payload",
    ]
    assert payload["attempted"] is True
    assert payload["executed"] is True
    assert payload["reason"] == "evidence_chain_execution_completed"
    assert payload["jobs_received_count"] == 1
    assert payload["jobs_sampled_count"] == 1
    assert payload["jobs_executed_count"] == 1
    assert payload["jobs_succeeded_count"] == 1
    assert payload["jobs_failed_count"] == 0
    result = payload["per_job_results"][0]
    assert result["status"] == "succeeded"
    assert result["job_id"] == "job-98b"
    artifacts = result["artifacts"]
    assert set(artifacts) == {
        "jd_intelligence",
        "resume_match_jd_evidence",
        "critic_resume_match_jd_evidence",
        "job_prioritization_critic_evidence",
        "tailoring_decision_priority_evidence",
        "operator_review_tailoring_evidence",
        "agent_evidence_chain_bundle",
        "agent_evidence_chain_trace_payload",
    }
    assert artifacts["agent_evidence_chain_trace_payload"]["artifact_type"] == (
        "agent_evidence_chain_trace_payload"
    )
    assert job == before
    _assert_safe(payload, internal_decisioning=True)


def test_include_trace_payload_false_executes_phase89_to_94_only(monkeypatch):
    calls = []
    _patch_success_chain(monkeypatch, calls)

    payload = evidence_chain_execution.execute_controlled_evidence_chain(
        _job(),
        resume_context=_resume_context(),
        execution_gate_enabled=True,
        include_trace_payload=False,
    )

    assert calls == [
        "jd_intelligence",
        "resume_match",
        "critic",
        "job_prioritization",
        "tailoring_decision",
        "operator_review",
        "bundle",
    ]
    assert "agent_evidence_chain_trace_payload" not in payload["per_job_results"][0][
        "artifacts"
    ]
    assert payload["include_trace_payload"] is False


def test_batch_execution_respects_sample_limit(monkeypatch):
    calls = []
    _patch_success_chain(monkeypatch, calls)
    jobs = [_job("job-a"), _job("job-b"), _job("job-c")]

    payload = evidence_chain_execution.execute_controlled_evidence_chain(
        jobs,
        resume_context=_resume_context(),
        execution_gate_enabled=True,
        sample_limit=2,
        include_trace_payload=False,
    )

    assert payload["jobs_received_count"] == 3
    assert payload["jobs_sampled_count"] == 2
    assert payload["jobs_executed_count"] == 2
    assert [result["job_id"] for result in payload["per_job_results"]] == [
        "job-a",
        "job-b",
    ]
    assert calls.count("resume_match") == 2
    assert calls.count("bundle") == 2


def test_missing_resume_context_degrades_without_fake_resume_facts_or_provider_calls():
    job = _job()
    before = deepcopy(job)

    payload = evidence_chain_execution.execute_controlled_evidence_chain(
        job,
        resume_context=None,
        execution_gate_enabled=True,
        include_trace_payload=True,
    )

    result = payload["per_job_results"][0]
    assert result["status"] == "degraded"
    assert "resume_evidence_missing" in result["reason_codes"]
    resume_artifact = result["artifacts"]["resume_match_jd_evidence"]
    assert resume_artifact["selected_resume_id"] == ""
    assert resume_artifact["resume_evidence_fields_used"] == []
    assert resume_artifact["provider_call_performed"] is False
    assert job == before
    _assert_safe(payload, internal_decisioning=True)


def test_helper_failure_strict_false_captures_failure_and_continues(monkeypatch):
    calls = []
    _patch_success_chain(monkeypatch, calls)

    def failing_resume_match(**kwargs):
        calls.append("resume_match_failed")
        if kwargs["job_id"] == "job-a":
            raise RuntimeError("resume evidence exploded")
        return {
            "artifact_type": "resume_match_jd_evidence",
            "job_id": kwargs["job_id"],
            "reason_codes": [],
        }

    monkeypatch.setattr(
        evidence_chain_execution,
        "build_resume_match_jd_evidence_artifact",
        failing_resume_match,
    )

    payload = evidence_chain_execution.execute_controlled_evidence_chain(
        [_job("job-a"), _job("job-b")],
        resume_context=_resume_context(),
        execution_gate_enabled=True,
        include_trace_payload=False,
        strict=False,
    )

    assert payload["reason"] == "evidence_chain_execution_completed_with_failures"
    assert payload["jobs_failed_count"] == 1
    assert payload["jobs_succeeded_count"] == 1
    assert payload["per_job_results"][0]["status"] == "failed"
    assert payload["per_job_results"][0]["reason_codes"] == [
        "evidence_chain_helper_failed"
    ]
    assert "resume evidence exploded" in payload["per_job_results"][0]["error_message"]
    assert payload["per_job_results"][1]["status"] == "succeeded"
    assert "evidence_chain_helper_failed" in payload["aggregate_reason_codes"]


def test_helper_failure_strict_true_reraises_after_actual_helper_failure(monkeypatch):
    calls = []
    _patch_success_chain(monkeypatch, calls)

    def failing_critic(**kwargs):
        calls.append("critic_failed")
        raise RuntimeError("critic failed")

    monkeypatch.setattr(
        evidence_chain_execution,
        "build_critic_resume_match_jd_evidence_artifact",
        failing_critic,
    )

    with pytest.raises(RuntimeError, match="critic failed"):
        evidence_chain_execution.execute_controlled_evidence_chain(
            _job(),
            resume_context=_resume_context(),
            execution_gate_enabled=True,
            strict=True,
        )

    assert "jd_intelligence" in calls
    assert "resume_match" in calls
    assert "critic_failed" in calls


def test_zero_sample_limit_attempts_without_execution_or_raise():
    payload = evidence_chain_execution.execute_controlled_evidence_chain(
        [_job()],
        resume_context=_resume_context(),
        execution_gate_enabled=True,
        sample_limit=0,
        strict=True,
    )

    assert payload["attempted"] is True
    assert payload["executed"] is False
    assert payload["reason"] == "no_jobs_sampled"
    assert payload["jobs_received_count"] == 1
    assert payload["jobs_sampled_count"] == 0
    assert payload["jobs_executed_count"] == 0
    _assert_safe(payload, internal_decisioning=False)


def test_source_does_not_import_or_call_forbidden_runtime_paths():
    source = (ROOT / "src/agents/evidence_chain_execution.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(source)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_from = {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    }
    forbidden_modules = {
        "src.pipeline.collector",
        "src.agents.workflow_runner",
        "src.storage.agent_trace.store",
        "src.ai.llm_client",
        "src.ai.job_fit_evaluator",
        "src.tailoring.llm",
        "src.app.api",
        "src.app.services",
    }
    assert forbidden_modules.isdisjoint(imported_modules)
    assert forbidden_modules.isdisjoint(imported_from)

    called_names = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attrs = {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    forbidden_calls = {
        "persist_agent_evidence_chain_trace_payload",
        "run_agentic_workflow_dry_run",
        "run_chat_completion",
        "run_chat_completion_with_metadata",
        "evaluate_jobs",
        "score_jobs",
        "execute_application",
        "submit_application",
        "mark_applied",
        "send_recruiter_message",
    }
    assert forbidden_calls.isdisjoint(called_names)
    assert forbidden_calls.isdisjoint(called_attrs)

    required_calls = {
        "describe_existing_job_intelligence_result",
        "build_resume_match_jd_evidence_artifact",
        "build_critic_resume_match_jd_evidence_artifact",
        "build_job_prioritization_critic_evidence_artifact",
        "build_tailoring_decision_priority_evidence_artifact",
        "build_operator_review_tailoring_evidence_artifact",
        "build_agent_evidence_chain_bundle",
        "build_agent_evidence_chain_trace_payload",
    }
    assert required_calls.issubset(called_names)
