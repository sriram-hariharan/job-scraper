import ast
from copy import deepcopy
from pathlib import Path

from src.agents import job_prioritization_agent


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FALSE_SAFETY_FLAGS = [
    "provider_call_performed",
    "live_llm_call_performed",
    "jd_extraction_performed",
    "resume_match_execution_performed",
    "critic_execution_performed",
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


def _critic_evidence(**overrides):
    payload = {
        "artifact_type": "critic_resume_match_jd_evidence",
        "job_id": "job-91b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "critic_status": "approved",
        "evidence_quality": "strong",
        "gap_analysis": {
            "missing_required_skills": [],
            "missing_required_skill_ratio": 0.0,
        },
        "risk_flags": [],
        "contradiction_flags": [],
        "missing_required_skills": [],
        "review_guidance": "Resume Match evidence is strong.",
        "job_prioritization_input_summary": {
            "job_id": "job-91b",
            "selected_resume_id": "resume-main",
            "critic_status": "approved",
            "evidence_quality": "strong",
            "confidence": 0.86,
            "missing_required_skill_count": 0,
            "risk_flag_count": 0,
            "contradiction_count": 0,
            "reason_codes": [],
        },
        "reason_codes": [],
        "validation_summary": {"validation_status": "passed"},
        "confidence": 0.86,
    }
    payload.update(overrides)
    return payload


def _resume_match_evidence(**overrides):
    payload = {
        "artifact_type": "resume_match_jd_evidence",
        "job_id": "job-91b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "confidence": 0.84,
        "validation_summary": {"validation_status": "passed"},
    }
    payload.update(overrides)
    return payload


def _jd_wrapper(**overrides):
    payload = {
        "status": "completed",
        "job_id": "job-91b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "required_skills": ["Python", "SQL", "RAG"],
        "preferred_skills": ["Airflow"],
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


def test_valid_critic_evidence_builds_priority_artifact_for_tailoring_decision():
    payload = job_prioritization_agent.build_job_prioritization_critic_evidence_artifact(
        critic_resume_match_jd_evidence=_critic_evidence(),
        resume_match_jd_evidence=_resume_match_evidence(),
        jd_intelligence=_jd_wrapper(),
    )

    assert payload["artifact_type"] == "job_prioritization_critic_evidence"
    assert payload["source_agent"] == "job_prioritization"
    assert payload["upstream_agents"] == ["critic", "resume_match", "jd_intelligence"]
    assert payload["gate_name"] == (
        "APPLYLENS_AGENTIC_JOB_PRIORITIZATION_CONSUMES_CRITIC_EVIDENCE_ENABLED"
    )
    assert payload["enabled"] is False
    assert payload["job_id"] == "job-91b"
    assert payload["title"] == "AI Platform Engineer"
    assert payload["company"] == "Example AI"
    assert payload["selected_resume_id"] == "resume-main"
    assert payload["priority_recommendation"] == "prioritize"
    assert payload["priority_band"] == "high"
    assert payload["readiness_level"] == "ready_for_tailoring_review"
    assert payload["manual_review_required"] is False
    summary = payload["tailoring_decision_input_summary"]
    assert summary["priority_recommendation"] == "prioritize"
    assert summary["critic_status"] == "approved"
    assert payload["validation_summary"]["validation_status"] == "passed"
    _assert_safety(payload)


def test_missing_critic_evidence_returns_manual_review_artifact_without_crashing():
    payload = job_prioritization_agent.build_job_prioritization_critic_evidence_artifact(
        critic_resume_match_jd_evidence=None,
        resume_match_jd_evidence=_resume_match_evidence(),
        jd_intelligence=_jd_wrapper(),
    )

    assert payload["priority_recommendation"] == "manual_review"
    assert payload["priority_band"] == "manual_review"
    assert payload["readiness_level"] == "insufficient_evidence"
    assert payload["manual_review_required"] is True
    assert "critic_evidence_missing" in payload["reason_codes"]
    assert payload["validation_summary"]["critic_evidence_present"] is False
    _assert_safety(payload)


def test_missing_optional_context_uses_critic_as_primary_evidence():
    payload = job_prioritization_agent.build_job_prioritization_critic_evidence_artifact(
        critic_resume_match_jd_evidence=_critic_evidence(),
        resume_match_jd_evidence=None,
        jd_intelligence=None,
    )

    assert payload["priority_recommendation"] == "prioritize"
    assert payload["priority_band"] == "high"
    assert "resume_match_context_missing" in payload["reason_codes"]
    assert "jd_intelligence_context_missing" in payload["reason_codes"]
    assert payload["validation_summary"]["critic_evidence_valid"] is True
    _assert_safety(payload)


def test_malformed_critic_evidence_returns_manual_review_without_fallback_helpers():
    payload = job_prioritization_agent.build_job_prioritization_critic_evidence_artifact(
        critic_resume_match_jd_evidence={
            "artifact_type": "wrong_artifact",
            "critic_status": "approved",
            "evidence_quality": "strong",
            "confidence": 0.9,
        },
        resume_match_jd_evidence=_resume_match_evidence(),
        jd_intelligence=_jd_wrapper(),
    )

    assert payload["priority_recommendation"] == "manual_review"
    assert payload["manual_review_required"] is True
    assert "critic_evidence_malformed" in payload["reason_codes"]
    assert payload["validation_summary"]["validation_status"] == "failed"
    assert payload["critic_execution_performed"] is False
    assert payload["resume_match_execution_performed"] is False
    assert payload["jd_extraction_performed"] is False
    _assert_safety(payload)


def test_deterministic_priority_rules_cover_medium_low_and_manual_review():
    medium = job_prioritization_agent.build_job_prioritization_critic_evidence_artifact(
        critic_resume_match_jd_evidence=_critic_evidence(
            evidence_quality="partial",
            confidence=0.58,
        ),
        resume_match_jd_evidence=_resume_match_evidence(),
        jd_intelligence=_jd_wrapper(),
    )
    low = job_prioritization_agent.build_job_prioritization_critic_evidence_artifact(
        critic_resume_match_jd_evidence=_critic_evidence(
            critic_status="needs_review",
            evidence_quality="weak",
            confidence=0.31,
            gap_analysis={
                "missing_required_skills": ["RAG", "SQL"],
                "missing_required_skill_ratio": 0.67,
            },
        ),
        resume_match_jd_evidence=_resume_match_evidence(),
        jd_intelligence=_jd_wrapper(),
    )
    manual = job_prioritization_agent.build_job_prioritization_critic_evidence_artifact(
        critic_resume_match_jd_evidence=_critic_evidence(
            evidence_quality="partial",
            confidence=0.72,
            risk_flags=["required_skill_coverage_low"],
            contradiction_flags=["jd_required_skills_conflict"],
        ),
        resume_match_jd_evidence=_resume_match_evidence(),
        jd_intelligence=_jd_wrapper(),
    )

    assert medium["priority_recommendation"] == "standard_review"
    assert medium["priority_band"] == "medium"
    assert medium["readiness_level"] == "needs_human_review"
    assert low["priority_recommendation"] == "deprioritize"
    assert low["priority_band"] == "low"
    assert low["readiness_level"] == "insufficient_evidence"
    assert manual["priority_recommendation"] == "manual_review"
    assert manual["priority_band"] == "manual_review"
    assert manual["readiness_level"] == "blocked_by_risk"


def test_consistency_checks_force_manual_review_for_conflicting_approved_evidence():
    payload = job_prioritization_agent.build_job_prioritization_critic_evidence_artifact(
        critic_resume_match_jd_evidence=_critic_evidence(
            critic_status="approved",
            evidence_quality="weak",
            contradiction_flags=["matched_required_skill_not_in_resume_match_jd:Kubernetes"],
        ),
        resume_match_jd_evidence=_resume_match_evidence(company="Different Co"),
        jd_intelligence=_jd_wrapper(title="Different Title"),
    )

    assert payload["priority_recommendation"] == "manual_review"
    assert payload["manual_review_required"] is True
    assert "approved_critic_with_weak_or_missing_evidence" in payload["reason_codes"]
    assert "approved_critic_with_contradiction_flags" in payload["reason_codes"]
    assert "resume_match_context_company_conflict" in payload["reason_codes"]
    assert "jd_intelligence_context_title_conflict" in payload["reason_codes"]


def test_helper_is_deterministic_and_does_not_mutate_inputs():
    critic = _critic_evidence()
    resume = _resume_match_evidence()
    jd = _jd_wrapper()
    original_critic = deepcopy(critic)
    original_resume = deepcopy(resume)
    original_jd = deepcopy(jd)

    first = job_prioritization_agent.build_job_prioritization_critic_evidence_artifact(
        critic_resume_match_jd_evidence=critic,
        resume_match_jd_evidence=resume,
        jd_intelligence=jd,
    )
    second = job_prioritization_agent.build_job_prioritization_critic_evidence_artifact(
        critic_resume_match_jd_evidence=critic,
        resume_match_jd_evidence=resume,
        jd_intelligence=jd,
    )

    assert first == second
    assert critic == original_critic
    assert resume == original_resume
    assert jd == original_jd
    _assert_safety(first)


def test_helper_source_does_not_call_upstream_runtime_or_mutation_paths():
    source = (ROOT / "src/agents/job_prioritization_agent.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    helper = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "build_job_prioritization_critic_evidence_artifact"
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
        "build_critic_resume_match_jd_evidence_artifact",
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
        "src.agents.critic_agent",
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
