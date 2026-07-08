import ast
from copy import deepcopy
from pathlib import Path

from src.agents import critic_agent


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FALSE_SAFETY_FLAGS = [
    "provider_call_performed",
    "live_llm_call_performed",
    "jd_extraction_performed",
    "resume_match_execution_performed",
    "trace_persistence_performed",
    "collector_output_changed",
    "production_output_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "queue_mutation_performed",
    "scheduler_mutation_performed",
    "tailoring_mutation_performed",
    "source_resume_mutation_performed",
    "workflow_runner_executed",
    "auto_apply_performed",
    "ats_submission_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
]


def _resume_match_evidence(**overrides):
    payload = {
        "artifact_type": "resume_match_jd_evidence",
        "job_id": "job-90b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "jd_required_skills": ["Python", "SQL", "RAG"],
        "jd_preferred_skills": ["Airflow"],
        "jd_all_skills": ["Python", "SQL", "RAG", "Airflow"],
        "matched_required_skills": ["Python", "SQL", "RAG"],
        "missing_required_skills": [],
        "matched_preferred_skills": ["Airflow"],
        "missing_preferred_skills": [],
        "match_status": "strong_match",
        "recommendation_label": "strong_match",
        "confidence": 0.84,
        "critic_input_summary": {
            "job_id": "job-90b",
            "selected_resume_id": "resume-main",
            "matched_required_skill_count": 3,
            "missing_required_skill_count": 0,
        },
        "reason_codes": [],
        "validation_summary": {"validation_status": "passed"},
    }
    payload.update(overrides)
    return payload


def _jd_wrapper(**overrides):
    payload = {
        "status": "completed",
        "job_id": "job-90b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "required_skills": ["Python", "SQL", "RAG"],
        "preferred_skills": ["Airflow"],
        "all_skills": ["Python", "SQL", "RAG", "Airflow"],
        "extraction_source": "existing_pipeline_job_intelligence",
        "validation_json": {
            "is_valid_for_existing_output_wrapper": True,
            "missing_or_invalid_fields": [],
        },
    }
    payload.update(overrides)
    return payload


def _assert_safety(payload):
    assert payload["default_off"] is True
    assert payload["read_only"] is True
    assert payload["diagnostic_only"] is True
    safety = payload["safety_metadata"]
    for flag in REQUIRED_FALSE_SAFETY_FLAGS:
        assert payload[flag] is False
        assert safety[flag] is False


def test_valid_resume_match_and_jd_evidence_builds_critic_artifact():
    payload = critic_agent.build_critic_resume_match_jd_evidence_artifact(
        resume_match_jd_evidence=_resume_match_evidence(),
        jd_intelligence=_jd_wrapper(),
    )

    assert payload["artifact_type"] == "critic_resume_match_jd_evidence"
    assert payload["source_agent"] == "critic"
    assert payload["upstream_agents"] == ["resume_match", "jd_intelligence"]
    assert payload["job_id"] == "job-90b"
    assert payload["title"] == "AI Platform Engineer"
    assert payload["company"] == "Example AI"
    assert payload["selected_resume_id"] == "resume-main"
    assert payload["critic_status"] == "approved"
    assert payload["evidence_quality"] == "strong"
    assert payload["gap_analysis"]["missing_required_skills"] == []
    assert payload["risk_flags"] == []
    assert payload["contradiction_flags"] == []
    assert payload["unsupported_match_claims"] == []
    assert "downstream prioritization" in payload["review_guidance"]
    assert payload["job_prioritization_input_summary"]["critic_status"] == "approved"
    assert payload["validation_summary"]["validation_status"] == "passed"
    assert payload["confidence"] == 0.84
    _assert_safety(payload)


def test_missing_resume_match_evidence_returns_insufficient_artifact():
    payload = critic_agent.build_critic_resume_match_jd_evidence_artifact(
        resume_match_jd_evidence=None,
        jd_intelligence=_jd_wrapper(),
    )

    assert payload["critic_status"] == "insufficient_evidence"
    assert payload["evidence_quality"] == "missing"
    assert "resume_match_evidence_missing" in payload["reason_codes"]
    assert payload["validation_summary"]["resume_match_evidence_present"] is False
    assert payload["validation_summary"]["validation_status"] == "degraded"
    _assert_safety(payload)


def test_missing_jd_intelligence_context_uses_resume_match_as_primary():
    payload = critic_agent.build_critic_resume_match_jd_evidence_artifact(
        resume_match_jd_evidence=_resume_match_evidence(),
        jd_intelligence=None,
    )

    assert payload["critic_status"] == "approved"
    assert payload["evidence_quality"] == "strong"
    assert "jd_intelligence_context_missing" in payload["reason_codes"]
    assert "jd_context_unavailable" in payload["risk_flags"]
    assert payload["validation_summary"]["jd_intelligence_context_present"] is False
    _assert_safety(payload)


def test_malformed_resume_match_evidence_does_not_call_fallback_helpers():
    payload = critic_agent.build_critic_resume_match_jd_evidence_artifact(
        resume_match_jd_evidence={
            "artifact_type": "wrong_artifact",
            "confidence": 0.1,
            "validation_summary": {"validation_status": "failed"},
        },
        jd_intelligence=_jd_wrapper(),
    )

    assert payload["critic_status"] in {"insufficient_evidence", "rejected"}
    assert payload["evidence_quality"] in {"missing", "weak"}
    assert "resume_match_evidence_malformed" in payload["reason_codes"]
    assert "resume_match_validation_degraded" in payload["reason_codes"]
    assert payload["provider_call_performed"] is False
    assert payload["jd_extraction_performed"] is False
    assert payload["resume_match_execution_performed"] is False
    _assert_safety(payload)


def test_contradiction_flags_are_deterministic_for_jd_mismatch():
    resume_match = _resume_match_evidence(
        jd_required_skills=["Python", "SQL"],
        jd_all_skills=["Python", "SQL"],
        matched_required_skills=["Python", "Kubernetes"],
    )
    jd = _jd_wrapper(
        required_skills=["Python", "RAG"],
        all_skills=["Python", "RAG", "Airflow"],
    )

    payload = critic_agent.build_critic_resume_match_jd_evidence_artifact(
        resume_match_jd_evidence=resume_match,
        jd_intelligence=jd,
    )

    assert "matched_required_skill_not_in_resume_match_jd:Kubernetes" in payload["contradiction_flags"]
    assert "jd_required_skills_conflict" in payload["contradiction_flags"]
    assert "upstream_evidence_contradiction" in payload["reason_codes"]
    assert payload["critic_status"] == "needs_review"
    assert payload["evidence_quality"] == "partial"
    _assert_safety(payload)


def test_helper_is_deterministic_and_does_not_mutate_inputs():
    resume_match = _resume_match_evidence()
    jd = _jd_wrapper()
    original_resume_match = deepcopy(resume_match)
    original_jd = deepcopy(jd)

    first = critic_agent.build_critic_resume_match_jd_evidence_artifact(
        resume_match_jd_evidence=resume_match,
        jd_intelligence=jd,
    )
    second = critic_agent.build_critic_resume_match_jd_evidence_artifact(
        resume_match_jd_evidence=resume_match,
        jd_intelligence=jd,
    )

    assert first == second
    assert resume_match == original_resume_match
    assert jd == original_jd
    _assert_safety(first)


def test_helper_source_does_not_call_upstream_provider_trace_or_runtime_paths():
    source = (ROOT / "src/agents/critic_agent.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    helper = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "build_critic_resume_match_jd_evidence_artifact"
    )
    called_names = {
        node.func.id
        for node in ast.walk(helper)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    called_attrs = {
        node.func.attr
        for node in ast.walk(helper)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }
    forbidden_calls = {
        "build_resume_match_jd_evidence_artifact",
        "describe_existing_job_intelligence_result",
        "build_existing_job_intelligence_trace_payload",
        "persist_existing_job_intelligence_trace_payload",
        "build_job_intelligence",
        "enrich_skills_with_llm",
        "run_chat_completion",
        "run_chat_completion_with_metadata",
        "evaluate_jobs",
        "score_jobs",
        "create_agent_run",
        "record_agent_step",
        "complete_agent_run",
        "execute_application",
        "submit_application",
    }

    assert forbidden_calls.isdisjoint(called_names)
    assert forbidden_calls.isdisjoint(called_attrs)

    helper_source = ast.get_source_segment(source, helper)
    forbidden_markers = [
        "src.pipeline.collector",
        "src.agents.resume_match_agent",
        "src.agents.jd_intelligence",
        "src.app.api",
        "src.app.services",
        "workflow_runner.",
        "OpenAI",
        "Groq",
        "genai",
        "cursor.execute",
        ".commit(",
        "application_execution_queue",
    ]
    for marker in forbidden_markers:
        assert marker not in helper_source
