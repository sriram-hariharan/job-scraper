from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

from src.pipeline import collector


ROOT = Path(__file__).resolve().parents[1]
GATE = "APPLYLENS_AGENTIC_PIPELINE_EVIDENCE_CHAIN_DIAGNOSTICS_ENABLED"
REQUIRED_ARTIFACTS = [
    "resume_match_jd_evidence",
    "critic_resume_match_jd_evidence",
    "job_prioritization_critic_evidence",
    "tailoring_decision_priority_evidence",
    "operator_review_tailoring_evidence",
]
FALSE_SAFETY_FLAGS = [
    "provider_call_performed",
    "live_llm_call_performed",
    "evidence_chain_bundle_execution_performed",
    "evidence_chain_trace_payload_execution_performed",
    "evidence_chain_trace_persistence_performed",
    "jd_extraction_performed",
    "jd_wrapper_execution_performed",
    "resume_match_execution_performed",
    "critic_execution_performed",
    "job_prioritization_execution_performed",
    "tailoring_decision_execution_performed",
    "operator_review_execution_performed",
    "trace_store_write_performed",
    "database_write_performed",
    "collector_output_changed",
    "production_output_changed",
    "evaluable_jobs_changed",
    "scored_jobs_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "cache_behavior_changed",
    "retry_behavior_changed",
    "dedupe_behavior_changed",
    "source_health_behavior_changed",
    "ats_health_behavior_changed",
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
]


def _collector_source() -> str:
    return (ROOT / "src/pipeline/collector.py").read_text(encoding="utf-8")


def _collector_helper_source() -> str:
    source = _collector_source()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name == "_maybe_build_evidence_chain_collector_diagnostics"
        ):
            return ast.get_source_segment(source, node) or ""
    raise AssertionError("collector evidence-chain diagnostics helper not found")


def _call_names(source: str) -> set[str]:
    names: set[str] = set()
    tree = ast.parse(source)

    def call_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = call_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            names.add(call_name(node.func))
    return names


def _job(**overrides):
    payload = {
        "job_id": "job-97b",
        "title": "Machine Learning Engineer",
        "company": "Example AI",
        "intelligence": {
            "skills": {
                "required": ["python", "sql"],
                "preferred": ["rag"],
                "all": ["python", "sql", "rag"],
            },
            "visa_sponsorship": "unknown",
        },
        "ai_fit": "8/10 | AI 8, Skill 8, Seniority 7, Learning 9",
        "ai_fit_score": 8,
        "ai_relevance": 8,
        "skill_match": 8,
        "seniority_match": 7,
        "learning_opportunity": 9,
        "ai_signal_score": 8.0,
        "priority_score": 12.5,
    }
    payload.update(overrides)
    return payload


def _artifact(name: str) -> dict:
    return {
        "artifact_type": name,
        "source_agent": name.replace("_evidence", ""),
        "validation_summary": {"validation_status": "passed"},
        "safety_metadata": {"provider_call_performed": False},
    }


def _job_with_all_artifacts(**overrides):
    payload = _job(
        resume_match_jd_evidence=_artifact("resume_match_jd_evidence"),
        critic_resume_match_jd_evidence=_artifact("critic_resume_match_jd_evidence"),
        job_prioritization_critic_evidence=_artifact(
            "job_prioritization_critic_evidence"
        ),
        tailoring_decision_priority_evidence=_artifact(
            "tailoring_decision_priority_evidence"
        ),
        operator_review_tailoring_evidence=_artifact(
            "operator_review_tailoring_evidence"
        ),
    )
    payload.update(overrides)
    return payload


def test_gate_off_returns_none_and_does_not_mutate_jobs():
    jobs = [_job()]
    before = deepcopy(jobs)

    result = collector._maybe_build_evidence_chain_collector_diagnostics(
        jobs,
        env={GATE: ""},
    )

    assert result is None
    assert jobs == before


def test_gate_on_with_no_jobs_reports_unavailable():
    payload = collector._maybe_build_evidence_chain_collector_diagnostics(
        [],
        env={GATE: "1"},
    )

    assert payload["artifact_type"] == "agent_evidence_chain_collector_diagnostics"
    assert payload["enabled"] is True
    assert payload["collector_stage"] == "post_score_jobs"
    assert payload["jobs_inspected_count"] == 0
    assert payload["evidence_chain_readiness"] == "unavailable"
    assert payload["readiness_reason_codes"] == ["no_jobs_available"]
    assert payload["evidence_chain_missing_artifacts"] == REQUIRED_ARTIFACTS


def test_jobs_with_intelligence_but_no_phase89_to_93_artifacts_report_inputs_missing():
    jobs = [_job(), _job(job_id="job-97b-2")]
    before = deepcopy(jobs)

    payload = collector._maybe_build_evidence_chain_collector_diagnostics(
        jobs,
        env={GATE: "true"},
    )

    assert payload["jobs_inspected_count"] == 2
    assert payload["jd_intelligence_present_count"] == 2
    assert payload["ai_evaluation_present_count"] == 2
    assert payload["scoring_present_count"] == 2
    for key in REQUIRED_ARTIFACTS:
        assert payload[f"{key}_present_count"] == 0
    assert payload["evidence_chain_readiness"] == "inputs_missing"
    assert "downstream_evidence_artifacts_missing" in payload["readiness_reason_codes"]
    assert payload["evidence_chain_missing_artifacts"] == REQUIRED_ARTIFACTS
    assert "controlled evidence-chain execution path" in payload[
        "next_recommended_engineering_step"
    ]
    assert jobs == before


def test_partial_artifacts_report_degraded_with_deterministic_missing_list():
    jobs = [
        _job(
            resume_match_jd_evidence=_artifact("resume_match_jd_evidence"),
            critic_resume_match_jd_evidence=_artifact(
                "critic_resume_match_jd_evidence"
            ),
        )
    ]

    payload = collector._maybe_build_evidence_chain_collector_diagnostics(
        jobs,
        env={GATE: "1"},
    )

    assert payload["evidence_chain_readiness"] == "degraded"
    assert payload["readiness_reason_codes"] == ["partial_evidence_artifacts_present"]
    assert payload["resume_match_jd_evidence_present_count"] == 1
    assert payload["critic_resume_match_jd_evidence_present_count"] == 1
    assert payload["evidence_chain_missing_artifacts"] == [
        "job_prioritization_critic_evidence",
        "tailoring_decision_priority_evidence",
        "operator_review_tailoring_evidence",
    ]


def test_all_phase89_to_93_artifacts_report_ready_from_existing_artifacts():
    jobs = [_job_with_all_artifacts(), _job_with_all_artifacts(job_id="job-97b-2")]

    payload = collector._maybe_build_evidence_chain_collector_diagnostics(
        jobs,
        env={GATE: "1"},
    )

    assert payload["evidence_chain_readiness"] == "ready_from_existing_artifacts"
    assert payload["readiness_reason_codes"] == [
        "all_required_evidence_artifacts_present"
    ]
    assert payload["evidence_chain_missing_artifacts"] == []
    for key in REQUIRED_ARTIFACTS:
        assert payload[f"{key}_present_count"] == 2


def test_diagnostics_are_sidecar_only_and_do_not_insert_into_job_records():
    jobs = [_job_with_all_artifacts()]
    before = deepcopy(jobs)

    payload = collector._maybe_build_evidence_chain_collector_diagnostics(
        jobs,
        env={GATE: "on"},
    )

    assert payload["production_output_changed"] is False
    assert payload["collector_output_changed"] is False
    assert payload["scored_jobs_changed"] is False
    assert "agent_evidence_chain_collector_diagnostics" not in jobs[0]
    assert jobs == before


def test_safety_flags_and_product_direction_metadata_are_explicit():
    payload = collector._maybe_build_evidence_chain_collector_diagnostics(
        [_job()],
        env={GATE: "1"},
    )

    for flag in FALSE_SAFETY_FLAGS:
        assert payload[flag] is False
        assert payload["safety_metadata"][flag] is False
    assert payload["automatic_internal_decisioning_goal"] is True
    assert payload["external_action_automation_goal"] is False
    assert payload["next_phase_should_execute_controlled_chain"] is True
    assert payload["trace_persistence_requested"] is False
    assert payload["trace_persistence_performed"] is False


def test_call_site_is_after_advisory_sidecar_before_source_health():
    source = _collector_source()
    complete_marker = (
        'complete_stage("application_priority", counts={"scored_jobs": len(scored_jobs)})'
    )
    advisory_marker = (
        "_maybe_invoke_advisory_chain_diagnostics_after_application_priority(scored_jobs)"
    )
    evidence_marker = "_maybe_build_evidence_chain_collector_diagnostics(scored_jobs)"
    source_health_marker = "if role_title_audit_rows is not None:"

    assert source.count(evidence_marker) == 1
    assert (
        source.index(complete_marker)
        < source.index(advisory_marker, source.index(complete_marker))
        < source.index(evidence_marker, source.index(advisory_marker))
        < source.index(source_health_marker, source.index(evidence_marker))
    )


def test_collector_evidence_chain_diagnostics_source_has_no_execution_persistence_or_external_actions():
    helper_source = _collector_helper_source()
    forbidden_tokens = [
        "build_resume_match_jd_evidence_artifact",
        "build_critic_resume_match_jd_evidence_artifact",
        "build_job_prioritization_critic_evidence_artifact",
        "build_tailoring_decision_priority_evidence_artifact",
        "build_operator_review_tailoring_evidence_artifact",
        "build_agent_evidence_chain_bundle",
        "build_agent_evidence_chain_trace_payload",
        "persist_agent_evidence_chain_trace_payload",
        "record_agent_step_postgres_payload",
        "create_agent_run_postgres_payload",
        "cursor.execute",
        "commit(",
        "workflow_runner",
        "run_chat_completion",
        "run_chat_completion_with_metadata",
        "submit_application",
        "click_apply",
        "mark_applied",
        "send_recruiter",
        "src.app.api",
        "src.app.services",
        "LangGraph",
    ]
    for token in forbidden_tokens:
        assert token not in helper_source

    calls = _call_names(helper_source)
    for name in [
        "build_resume_match_jd_evidence_artifact",
        "build_critic_resume_match_jd_evidence_artifact",
        "build_job_prioritization_critic_evidence_artifact",
        "build_tailoring_decision_priority_evidence_artifact",
        "build_operator_review_tailoring_evidence_artifact",
        "build_agent_evidence_chain_bundle",
        "build_agent_evidence_chain_trace_payload",
        "persist_agent_evidence_chain_trace_payload",
        "record_agent_step_postgres_payload",
        "create_agent_run_postgres_payload",
        "run_chat_completion",
        "run_chat_completion_with_metadata",
    ]:
        assert name not in calls


def test_phase97b_gate_and_artifact_contract_are_declared_in_collector_source():
    source = _collector_source()

    assert "APPLYLENS_AGENTIC_PIPELINE_EVIDENCE_CHAIN_DIAGNOSTICS_ENABLED" in source
    assert "agent_evidence_chain_collector_diagnostics" in source
    assert "agent-evidence-chain-collector-diagnostics-v1" in source
