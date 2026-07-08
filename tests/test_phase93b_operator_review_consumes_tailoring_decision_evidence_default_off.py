import ast
from copy import deepcopy
from pathlib import Path

from src.agents import operator_review_agent


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FALSE_SAFETY_FLAGS = [
    "provider_call_performed",
    "live_llm_call_performed",
    "jd_extraction_performed",
    "resume_match_execution_performed",
    "critic_execution_performed",
    "job_prioritization_execution_performed",
    "tailoring_decision_execution_performed",
    "trace_persistence_performed",
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
    "tailoring_provider_call_performed",
    "workflow_runner_executed",
    "application_status_changed",
    "auto_apply_performed",
    "ats_submission_performed",
    "apply_click_performed",
    "recruiter_message_sent",
    "mark_applied_performed",
]


def _tailoring_evidence(**overrides):
    payload = {
        "artifact_type": "tailoring_decision_priority_evidence",
        "job_id": "job-93b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "tailoring_decision": "no_tailoring_needed",
        "tailoring_intensity": "none",
        "tailoring_readiness": "ready_for_operator_review",
        "operator_review_required": False,
        "operator_review_input_summary": {
            "job_id": "job-93b",
            "selected_resume_id": "resume-main",
            "tailoring_decision": "no_tailoring_needed",
            "tailoring_intensity": "none",
            "tailoring_readiness": "ready_for_operator_review",
            "operator_review_required": False,
            "priority_recommendation": "prioritize",
            "priority_band": "high",
            "confidence": 0.9,
            "reason_codes": [],
        },
        "reason_codes": [],
        "validation_summary": {"validation_status": "passed"},
        "confidence": 0.9,
    }
    payload.update(overrides)
    return payload


def _priority_evidence(**overrides):
    payload = {
        "artifact_type": "job_prioritization_critic_evidence",
        "job_id": "job-93b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "priority_recommendation": "prioritize",
        "priority_band": "high",
        "readiness_level": "ready_for_tailoring_review",
        "manual_review_required": False,
        "validation_summary": {"validation_status": "passed"},
        "confidence": 0.88,
    }
    payload.update(overrides)
    return payload


def _critic_evidence(**overrides):
    payload = {
        "artifact_type": "critic_resume_match_jd_evidence",
        "job_id": "job-93b",
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
        "job_id": "job-93b",
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
        "job_id": "job-93b",
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


def _artifact(**overrides):
    kwargs = {
        "tailoring_decision_priority_evidence": _tailoring_evidence(),
        "job_prioritization_critic_evidence": _priority_evidence(),
        "critic_resume_match_jd_evidence": _critic_evidence(),
        "resume_match_jd_evidence": _resume_match_evidence(),
        "jd_intelligence": _jd_wrapper(),
    }
    kwargs.update(overrides)
    return operator_review_agent.build_operator_review_tailoring_evidence_artifact(
        **kwargs
    )


def _assert_safety(payload):
    assert payload["default_off"] is True
    assert payload["read_only"] is True
    assert payload["diagnostic_only"] is True
    safety = payload["safety_metadata"]
    for flag in REQUIRED_FALSE_SAFETY_FLAGS:
        assert payload[flag] is False
        assert safety[flag] is False


def test_valid_tailoring_evidence_builds_operator_review_artifact():
    payload = _artifact()

    assert payload["artifact_type"] == "operator_review_tailoring_evidence"
    assert payload["source_agent"] == "operator_review"
    assert payload["upstream_agents"] == [
        "tailoring_decision",
        "job_prioritization",
        "critic",
        "resume_match",
        "jd_intelligence",
    ]
    assert payload["gate_name"] == (
        "APPLYLENS_AGENTIC_OPERATOR_REVIEW_CONSUMES_TAILORING_DECISION_EVIDENCE_ENABLED"
    )
    assert payload["operator_review_lane"] == "ready_to_apply"
    assert payload["operator_review_readiness"] == "ready_without_tailoring"
    assert payload["recommended_next_step"] == "review_and_apply_manually"
    assert payload["human_review_required"] is False
    assert payload["review_packet_summary"]["tailoring_decision"] == "no_tailoring_needed"
    assert payload["validation_summary"]["validation_status"] == "passed"
    _assert_safety(payload)


def test_missing_tailoring_decision_evidence_returns_collect_more_evidence_artifact():
    payload = operator_review_agent.build_operator_review_tailoring_evidence_artifact(
        tailoring_decision_priority_evidence=None,
        job_prioritization_critic_evidence=_priority_evidence(),
        critic_resume_match_jd_evidence=_critic_evidence(),
        resume_match_jd_evidence=_resume_match_evidence(),
        jd_intelligence=_jd_wrapper(),
    )

    assert payload["operator_review_lane"] == "review_before_action"
    assert payload["operator_review_readiness"] == "insufficient_evidence"
    assert payload["recommended_next_step"] == "collect_more_evidence"
    assert payload["human_review_required"] is True
    assert "tailoring_decision_evidence_missing" in payload["reason_codes"]
    assert payload["validation_summary"]["validation_status"] == "failed"
    _assert_safety(payload)


def test_missing_optional_context_uses_tailoring_decision_as_primary_evidence():
    payload = operator_review_agent.build_operator_review_tailoring_evidence_artifact(
        tailoring_decision_priority_evidence=_tailoring_evidence(
            tailoring_decision="light_tailoring",
            tailoring_intensity="light",
            operator_review_required=False,
        ),
        job_prioritization_critic_evidence=None,
        critic_resume_match_jd_evidence=None,
        resume_match_jd_evidence=None,
        jd_intelligence=None,
    )

    assert payload["operator_review_lane"] == "tailor_then_apply"
    assert payload["operator_review_readiness"] == "needs_tailoring_review"
    assert payload["recommended_next_step"] == "review_tailoring_plan"
    assert "job_prioritization_context_missing" in payload["reason_codes"]
    assert "critic_context_missing" in payload["reason_codes"]
    assert "resume_match_context_missing" in payload["reason_codes"]
    assert "jd_intelligence_context_missing" in payload["reason_codes"]
    _assert_safety(payload)


def test_malformed_tailoring_decision_evidence_does_not_fallback_to_upstream_helpers():
    payload = _artifact(
        tailoring_decision_priority_evidence={
            "artifact_type": "wrong_artifact",
            "tailoring_decision": "no_tailoring_needed",
            "tailoring_readiness": "ready_for_operator_review",
            "confidence": 1.0,
        },
    )

    assert payload["operator_review_lane"] == "review_before_action"
    assert payload["operator_review_readiness"] == "insufficient_evidence"
    assert payload["human_review_required"] is True
    assert "tailoring_decision_evidence_malformed" in payload["reason_codes"]
    assert payload["validation_summary"]["validation_status"] == "failed"
    _assert_safety(payload)


def test_deterministic_lane_rules_cover_expected_operator_review_outcomes():
    light = _artifact(
        tailoring_decision_priority_evidence=_tailoring_evidence(
            tailoring_decision="light_tailoring",
            tailoring_intensity="light",
            operator_review_required=False,
        )
    )
    standard = _artifact(
        tailoring_decision_priority_evidence=_tailoring_evidence(
            tailoring_decision="tailor_before_apply",
            tailoring_intensity="standard",
            operator_review_required=False,
        )
    )
    manual = _artifact(
        tailoring_decision_priority_evidence=_tailoring_evidence(
            tailoring_decision="manual_review_before_tailoring",
            tailoring_readiness="needs_manual_review",
            operator_review_required=True,
        )
    )
    blocked = _artifact(
        tailoring_decision_priority_evidence=_tailoring_evidence(
            tailoring_decision="do_not_tailor",
            tailoring_readiness="blocked_by_risk",
            operator_review_required=True,
        )
    )
    source_watch = _artifact(
        tailoring_decision_priority_evidence=_tailoring_evidence(
            job_id="",
            title="",
            company="",
            tailoring_decision="no_tailoring_needed",
            confidence=0.8,
            operator_review_required=False,
        ),
        job_prioritization_critic_evidence={},
        critic_resume_match_jd_evidence={},
        resume_match_jd_evidence={},
        jd_intelligence={},
    )

    assert light["operator_review_lane"] == "tailor_then_apply"
    assert light["recommended_next_step"] == "review_tailoring_plan"
    assert standard["operator_review_lane"] == "tailor_then_apply"
    assert manual["operator_review_lane"] == "review_before_action"
    assert manual["operator_review_readiness"] == "needs_manual_review"
    assert blocked["operator_review_lane"] == "hold_or_skip"
    assert blocked["operator_review_readiness"] == "blocked_by_risk"
    assert source_watch["operator_review_lane"] == "source_watch"
    assert source_watch["recommended_next_step"] == "watch_source"


def test_consistency_checks_force_human_review_for_contradictory_evidence():
    payload = _artifact(
        tailoring_decision_priority_evidence=_tailoring_evidence(
            operator_review_required=True,
            confidence=0.95,
        ),
        critic_resume_match_jd_evidence=_critic_evidence(
            risk_flags=["required_skill_coverage_low"],
            contradiction_flags=["jd_title_conflict"],
        ),
        resume_match_jd_evidence=_resume_match_evidence(company="Different Co"),
    )

    assert payload["operator_review_lane"] == "review_before_action"
    assert payload["operator_review_readiness"] == "needs_manual_review"
    assert payload["human_review_required"] is True
    assert "no_tailoring_needed_with_operator_review_required" in payload["reason_codes"]
    assert "no_tailoring_needed_with_critic_risk_flags" in payload["reason_codes"]
    assert "no_tailoring_needed_with_critic_contradiction_flags" in payload["reason_codes"]
    assert "resume_match_context_company_conflict" in payload["reason_codes"]
    assert payload["validation_summary"]["validation_status"] == "degraded"


def test_operator_review_tailoring_evidence_is_deterministic_and_does_not_mutate_inputs():
    tailoring = _tailoring_evidence()
    priority = _priority_evidence()
    critic = _critic_evidence()
    resume = _resume_match_evidence()
    jd = _jd_wrapper()
    before = deepcopy((tailoring, priority, critic, resume, jd))

    first = operator_review_agent.build_operator_review_tailoring_evidence_artifact(
        tailoring_decision_priority_evidence=tailoring,
        job_prioritization_critic_evidence=priority,
        critic_resume_match_jd_evidence=critic,
        resume_match_jd_evidence=resume,
        jd_intelligence=jd,
    )
    second = operator_review_agent.build_operator_review_tailoring_evidence_artifact(
        tailoring_decision_priority_evidence=tailoring,
        job_prioritization_critic_evidence=priority,
        critic_resume_match_jd_evidence=critic,
        resume_match_jd_evidence=resume,
        jd_intelligence=jd,
    )

    assert first == second
    assert (tailoring, priority, critic, resume, jd) == before


def test_helper_source_does_not_call_upstream_or_mutating_runtime_paths():
    source = (ROOT / "src/agents/operator_review_agent.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    helper = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "build_operator_review_tailoring_evidence_artifact"
    )
    forbidden_calls = {
        "build_tailoring_decision_priority_evidence_artifact",
        "build_job_prioritization_critic_evidence_artifact",
        "build_critic_resume_match_jd_evidence_artifact",
        "build_resume_match_jd_evidence_artifact",
        "describe_existing_job_intelligence_result",
        "build_existing_job_intelligence_trace_payload",
        "persist_existing_job_intelligence_trace_payload",
        "build_job_intelligence",
        "run_chat_completion",
        "provider_callable",
        "score_jobs",
        "record_agent_step",
        "create_agent_run",
        "submit_application",
        "click_apply",
        "mark_applied",
    }

    call_names = set()
    for node in ast.walk(helper):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                call_names.add(func.id)
            elif isinstance(func, ast.Attribute):
                call_names.add(func.attr)

    assert not (call_names & forbidden_calls)
