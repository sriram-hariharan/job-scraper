import ast
from copy import deepcopy
from pathlib import Path

from src.agents import tailoring_decision_agent


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FALSE_SAFETY_FLAGS = [
    "provider_call_performed",
    "live_llm_call_performed",
    "jd_extraction_performed",
    "resume_match_execution_performed",
    "critic_execution_performed",
    "job_prioritization_execution_performed",
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
    "generated_resume_mutation_performed",
    "tailoring_provider_call_performed",
    "workflow_runner_executed",
    "auto_apply_performed",
    "ats_submission_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
]


def _priority_evidence(**overrides):
    payload = {
        "artifact_type": "job_prioritization_critic_evidence",
        "job_id": "job-92b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "priority_recommendation": "prioritize",
        "priority_band": "high",
        "readiness_level": "ready_for_tailoring_review",
        "manual_review_required": False,
        "tailoring_decision_input_summary": {
            "job_id": "job-92b",
            "selected_resume_id": "resume-main",
            "priority_recommendation": "prioritize",
            "priority_band": "high",
            "readiness_level": "ready_for_tailoring_review",
            "manual_review_required": False,
            "critic_status": "approved",
            "evidence_quality": "strong",
            "confidence": 0.88,
            "risk_flag_count": 0,
            "contradiction_count": 0,
            "missing_required_skill_count": 0,
            "reason_codes": [],
        },
        "reason_codes": [],
        "validation_summary": {"validation_status": "passed"},
        "confidence": 0.88,
    }
    payload.update(overrides)
    return payload


def _critic_evidence(**overrides):
    payload = {
        "artifact_type": "critic_resume_match_jd_evidence",
        "job_id": "job-92b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "critic_status": "approved",
        "evidence_quality": "strong",
        "risk_flags": [],
        "contradiction_flags": [],
        "validation_summary": {"validation_status": "passed"},
        "confidence": 0.86,
    }
    payload.update(overrides)
    return payload


def _resume_match_evidence(**overrides):
    payload = {
        "artifact_type": "resume_match_jd_evidence",
        "job_id": "job-92b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "missing_required_skills": [],
        "missing_preferred_skills": [],
        "validation_summary": {"validation_status": "passed"},
        "confidence": 0.84,
    }
    payload.update(overrides)
    return payload


def _jd_wrapper(**overrides):
    payload = {
        "status": "completed",
        "job_id": "job-92b",
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


def test_valid_priority_evidence_builds_tailoring_decision_artifact_for_operator_review():
    payload = tailoring_decision_agent.build_tailoring_decision_priority_evidence_artifact(
        job_prioritization_critic_evidence=_priority_evidence(),
        critic_resume_match_jd_evidence=_critic_evidence(),
        resume_match_jd_evidence=_resume_match_evidence(),
        jd_intelligence=_jd_wrapper(),
    )

    assert payload["artifact_type"] == "tailoring_decision_priority_evidence"
    assert payload["source_agent"] == "tailoring_decision"
    assert payload["upstream_agents"] == [
        "job_prioritization",
        "critic",
        "resume_match",
        "jd_intelligence",
    ]
    assert payload["gate_name"] == (
        "APPLYLENS_AGENTIC_TAILORING_DECISION_CONSUMES_JOB_PRIORITIZATION_EVIDENCE_ENABLED"
    )
    assert payload["enabled"] is False
    assert payload["job_id"] == "job-92b"
    assert payload["title"] == "AI Platform Engineer"
    assert payload["company"] == "Example AI"
    assert payload["selected_resume_id"] == "resume-main"
    assert payload["tailoring_decision"] == "no_tailoring_needed"
    assert payload["tailoring_intensity"] == "none"
    assert payload["tailoring_readiness"] == "ready_for_operator_review"
    assert payload["operator_review_required"] is False
    summary = payload["operator_review_input_summary"]
    assert summary["tailoring_decision"] == "no_tailoring_needed"
    assert summary["priority_recommendation"] == "prioritize"
    assert payload["validation_summary"]["validation_status"] == "passed"
    _assert_safety(payload)


def test_missing_job_prioritization_evidence_returns_manual_review_artifact():
    payload = tailoring_decision_agent.build_tailoring_decision_priority_evidence_artifact(
        job_prioritization_critic_evidence=None,
        critic_resume_match_jd_evidence=_critic_evidence(),
        resume_match_jd_evidence=_resume_match_evidence(),
        jd_intelligence=_jd_wrapper(),
    )

    assert payload["tailoring_decision"] == "manual_review_before_tailoring"
    assert payload["tailoring_intensity"] == "manual_review"
    assert payload["tailoring_readiness"] == "insufficient_evidence"
    assert payload["operator_review_required"] is True
    assert "job_prioritization_evidence_missing" in payload["reason_codes"]
    assert payload["validation_summary"]["job_prioritization_evidence_present"] is False
    _assert_safety(payload)


def test_missing_optional_context_uses_job_prioritization_as_primary_evidence():
    payload = tailoring_decision_agent.build_tailoring_decision_priority_evidence_artifact(
        job_prioritization_critic_evidence=_priority_evidence(),
        critic_resume_match_jd_evidence=None,
        resume_match_jd_evidence=None,
        jd_intelligence=None,
    )

    assert payload["tailoring_decision"] == "no_tailoring_needed"
    assert payload["tailoring_intensity"] == "none"
    assert "critic_context_missing" in payload["reason_codes"]
    assert "resume_match_context_missing" in payload["reason_codes"]
    assert "jd_intelligence_context_missing" in payload["reason_codes"]
    assert payload["validation_summary"]["job_prioritization_evidence_valid"] is True
    _assert_safety(payload)


def test_malformed_job_prioritization_evidence_returns_review_without_fallback_helpers():
    payload = tailoring_decision_agent.build_tailoring_decision_priority_evidence_artifact(
        job_prioritization_critic_evidence={
            "artifact_type": "wrong_artifact",
            "priority_recommendation": "prioritize",
            "priority_band": "high",
            "readiness_level": "ready_for_tailoring_review",
            "confidence": 0.9,
        },
        critic_resume_match_jd_evidence=_critic_evidence(),
        resume_match_jd_evidence=_resume_match_evidence(),
        jd_intelligence=_jd_wrapper(),
    )

    assert payload["tailoring_decision"] == "manual_review_before_tailoring"
    assert payload["tailoring_readiness"] == "insufficient_evidence"
    assert payload["operator_review_required"] is True
    assert "job_prioritization_evidence_malformed" in payload["reason_codes"]
    assert payload["validation_summary"]["validation_status"] == "failed"
    assert payload["job_prioritization_execution_performed"] is False
    assert payload["tailoring_provider_call_performed"] is False
    _assert_safety(payload)


def test_deterministic_decision_rules_cover_light_standard_manual_and_blocked():
    light = tailoring_decision_agent.build_tailoring_decision_priority_evidence_artifact(
        job_prioritization_critic_evidence=_priority_evidence(),
        critic_resume_match_jd_evidence=_critic_evidence(),
        resume_match_jd_evidence=_resume_match_evidence(missing_preferred_skills=["Airflow"]),
        jd_intelligence=_jd_wrapper(),
    )
    standard = tailoring_decision_agent.build_tailoring_decision_priority_evidence_artifact(
        job_prioritization_critic_evidence=_priority_evidence(
            tailoring_decision_input_summary={
                "missing_required_skill_count": 1,
                "risk_flag_count": 0,
                "contradiction_count": 0,
            }
        ),
        critic_resume_match_jd_evidence=_critic_evidence(),
        resume_match_jd_evidence=_resume_match_evidence(missing_required_skills=["RAG"]),
        jd_intelligence=_jd_wrapper(),
    )
    manual = tailoring_decision_agent.build_tailoring_decision_priority_evidence_artifact(
        job_prioritization_critic_evidence=_priority_evidence(
            manual_review_required=True,
            validation_summary={"validation_status": "degraded"},
        ),
        critic_resume_match_jd_evidence=_critic_evidence(),
        resume_match_jd_evidence=_resume_match_evidence(),
        jd_intelligence=_jd_wrapper(),
    )
    blocked = tailoring_decision_agent.build_tailoring_decision_priority_evidence_artifact(
        job_prioritization_critic_evidence=_priority_evidence(
            priority_recommendation="deprioritize",
            priority_band="low",
            readiness_level="blocked_by_risk",
            confidence=0.2,
        ),
        critic_resume_match_jd_evidence=_critic_evidence(risk_flags=["required_skill_coverage_low"]),
        resume_match_jd_evidence=_resume_match_evidence(),
        jd_intelligence=_jd_wrapper(),
    )

    assert light["tailoring_decision"] == "light_tailoring"
    assert light["tailoring_intensity"] == "light"
    assert light["tailoring_readiness"] == "ready_for_light_tailoring_review"
    assert standard["tailoring_decision"] == "tailor_before_apply"
    assert standard["tailoring_intensity"] == "standard"
    assert manual["tailoring_decision"] == "manual_review_before_tailoring"
    assert manual["tailoring_intensity"] == "manual_review"
    assert blocked["tailoring_decision"] == "do_not_tailor"
    assert blocked["tailoring_intensity"] == "blocked"


def test_consistency_checks_flag_conflicting_priority_and_upstream_risk():
    payload = tailoring_decision_agent.build_tailoring_decision_priority_evidence_artifact(
        job_prioritization_critic_evidence=_priority_evidence(
            readiness_level="blocked_by_risk",
            manual_review_required=True,
        ),
        critic_resume_match_jd_evidence=_critic_evidence(
            risk_flags=["required_skill_coverage_low"],
            contradiction_flags=["jd_required_skills_conflict"],
        ),
        resume_match_jd_evidence=_resume_match_evidence(company="Different Co"),
        jd_intelligence=_jd_wrapper(title="Different Title"),
    )

    assert payload["tailoring_decision"] == "do_not_tailor"
    assert payload["operator_review_required"] is True
    assert "priority_high_with_blocked_or_insufficient_readiness" in payload["reason_codes"]
    assert "priority_high_with_critic_risk_flags" in payload["reason_codes"]
    assert "priority_high_with_critic_contradiction_flags" in payload["reason_codes"]
    assert "resume_match_context_company_conflict" in payload["reason_codes"]
    assert "jd_intelligence_context_title_conflict" in payload["reason_codes"]


def test_helper_is_deterministic_and_does_not_mutate_inputs():
    priority = _priority_evidence()
    critic = _critic_evidence()
    resume = _resume_match_evidence()
    jd = _jd_wrapper()
    original_priority = deepcopy(priority)
    original_critic = deepcopy(critic)
    original_resume = deepcopy(resume)
    original_jd = deepcopy(jd)

    first = tailoring_decision_agent.build_tailoring_decision_priority_evidence_artifact(
        job_prioritization_critic_evidence=priority,
        critic_resume_match_jd_evidence=critic,
        resume_match_jd_evidence=resume,
        jd_intelligence=jd,
    )
    second = tailoring_decision_agent.build_tailoring_decision_priority_evidence_artifact(
        job_prioritization_critic_evidence=priority,
        critic_resume_match_jd_evidence=critic,
        resume_match_jd_evidence=resume,
        jd_intelligence=jd,
    )

    assert first == second
    assert priority == original_priority
    assert critic == original_critic
    assert resume == original_resume
    assert jd == original_jd
    _assert_safety(first)


def test_helper_source_does_not_call_upstream_runtime_or_mutation_paths():
    source = (ROOT / "src/agents/tailoring_decision_agent.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    helper = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "build_tailoring_decision_priority_evidence_artifact"
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
        "build_job_prioritization_critic_evidence_artifact",
        "build_critic_resume_match_jd_evidence_artifact",
        "build_resume_match_jd_evidence_artifact",
        "describe_existing_job_intelligence_result",
        "build_existing_job_intelligence_trace_payload",
        "persist_existing_job_intelligence_trace_payload",
        "build_job_intelligence",
        "build_tailoring_suggestion_dry_run_payload",
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
        "src.agents.job_prioritization_agent",
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
        "source_resume",
        "generated_resume",
    ]
    for marker in forbidden_markers:
        assert marker not in helper_source
