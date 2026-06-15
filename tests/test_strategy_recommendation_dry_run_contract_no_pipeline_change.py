from __future__ import annotations

from copy import deepcopy

from src.agents import job_prioritization_agent


def _jd(**overrides):
    payload = {
        "required_skills": ["Python", "SQL"],
        "required_tools": ["Airflow"],
        "workflows": ["production data pipelines"],
        "business_contexts": ["finance partners"],
    }
    payload.update(overrides)
    return payload


def _resume_match(**overrides):
    payload = {
        "match_status": "strong_match",
        "recommendation_label": "strong_match",
        "selected_resume_id": "resume-a",
        "confidence": 0.86,
        "missing_evidence": [],
        "risk_flags": [],
    }
    payload.update(overrides)
    return payload


def _tailoring(**overrides):
    payload = {
        "suggestion_status": "patch_ready_available",
        "selected_resume_id": "resume-a",
        "patch_ready_suggestions": [{"suggestion_id": "tailoring_dry_run_001"}],
        "guidance_only_suggestions": [],
        "rejected_suggestions": [],
        "missing_evidence": [],
        "projected_score_delta": 0.03,
    }
    payload.update(overrides)
    return payload


def _critic(**overrides):
    payload = {
        "critic_status": "approved",
        "approved_suggestions": [{"suggestion_id": "tailoring_dry_run_001"}],
        "downgraded_suggestions": [],
        "rejected_suggestions": [],
        "reason_codes": [],
        "evidence_gaps": [],
        "confidence": 0.88,
    }
    payload.update(overrides)
    return payload


def _build(**overrides):
    kwargs = {
        "jd_intelligence": _jd(),
        "resume_match_payload": _resume_match(),
        "tailoring_suggestion_payload": _tailoring(),
        "critic_guardrail_payload": _critic(),
        "context_id": "ctx-1",
        "job_id": "job-1",
    }
    kwargs.update(overrides)
    return job_prioritization_agent.build_strategy_recommendation_dry_run_payload(**kwargs)


def test_strong_match_with_approved_critic_recommends_apply_or_tailor_first():
    payload = _build()

    assert payload["recommendation_action"] in {"apply_now", "tailor_first"}
    assert payload["recommendation_action"] == "tailor_first"
    assert payload["recommendation_label"] == "strong_match_with_approved_tailoring"
    assert payload["priority_hint"] == "high"
    assert payload["readiness_level"] == "ready_after_tailoring"
    assert "strong_resume_match" in payload["decision_reasons"]
    assert "critic_guardrail_approved" in payload["decision_reasons"]
    assert payload["confidence"] >= 0.86


def test_missing_evidence_recommends_improve_resume_evidence():
    payload = _build(
        resume_match_payload=_resume_match(
            match_status="partial_match",
            recommendation_label="partial_match",
            confidence=0.55,
            missing_evidence=["tools:no_matching_resume_evidence"],
        ),
        tailoring_suggestion_payload=_tailoring(
            patch_ready_suggestions=[],
            suggestion_status="guidance_only",
            missing_evidence=["required_tools:Airflow:resume_evidence_missing"],
        ),
        critic_guardrail_payload=_critic(
            critic_status="needs_guidance",
            approved_suggestions=[],
            downgraded_suggestions=[{"suggestion_id": "tailoring_dry_run_002"}],
            evidence_gaps=["required_tools:Airflow:resume_evidence_missing"],
        ),
    )

    assert payload["recommendation_action"] == "improve_resume_evidence"
    assert payload["recommendation_label"] == "missing_evidence"
    assert "missing_evidence_before_apply" in payload["decision_reasons"]
    assert payload["required_human_review"] is True


def test_rejected_critic_output_blocks_apply_now():
    payload = _build(
        critic_guardrail_payload=_critic(
            critic_status="rejected",
            approved_suggestions=[],
            rejected_suggestions=[{"suggestion_id": "tailoring_dry_run_bad"}],
            reason_codes=["unsupported_claim"],
            confidence=0.91,
        )
    )

    assert payload["recommendation_action"] != "apply_now"
    assert payload["recommendation_action"] == "improve_resume_evidence"
    assert payload["readiness_level"] == "blocked"
    assert "critic_guardrail_rejected_suggestions" in payload["decision_reasons"]
    assert "unsupported_claim" in payload["blocking_risks"]


def test_weak_match_recommends_save_for_later_or_skip():
    payload = _build(
        resume_match_payload=_resume_match(
            match_status="weak_match",
            recommendation_label="weak_match",
            confidence=0.28,
        ),
        tailoring_suggestion_payload=_tailoring(patch_ready_suggestions=[], suggestion_status="guidance_only"),
        critic_guardrail_payload=_critic(approved_suggestions=[], downgraded_suggestions=[]),
    )

    assert payload["recommendation_action"] in {"save_for_later", "skip"}
    assert payload["recommendation_action"] == "save_for_later"
    assert payload["recommendation_label"] == "weak_resume_match"
    assert payload["readiness_level"] == "not_ready"


def test_missing_inputs_return_insufficient_information():
    payload = job_prioritization_agent.build_strategy_recommendation_dry_run_payload(
        jd_intelligence={},
        resume_match_payload={},
        tailoring_suggestion_payload={},
        critic_guardrail_payload={},
    )

    assert payload["recommendation_action"] == "insufficient_information"
    assert payload["recommendation_label"] == "insufficient_information"
    assert payload["strategy_status"] == "ready"
    assert "missing_required_dry_run_inputs" in payload["decision_reasons"]
    assert "resume_match_payload_missing" in payload["blocking_risks"]
    assert "critic_guardrail_payload_missing" in payload["blocking_risks"]


def test_strategy_recommendation_dry_run_does_not_mutate_inputs_and_is_deterministic():
    jd = _jd()
    resume = _resume_match()
    tailoring = _tailoring()
    critic = _critic()
    preferences = {"risk_tolerance": "conservative"}
    original_jd = deepcopy(jd)
    original_resume = deepcopy(resume)
    original_tailoring = deepcopy(tailoring)
    original_critic = deepcopy(critic)
    original_preferences = deepcopy(preferences)

    first = job_prioritization_agent.build_strategy_recommendation_dry_run_payload(
        jd_intelligence=jd,
        resume_match_payload=resume,
        tailoring_suggestion_payload=tailoring,
        critic_guardrail_payload=critic,
        user_preferences=preferences,
    )
    second = job_prioritization_agent.build_strategy_recommendation_dry_run_payload(
        jd_intelligence=jd,
        resume_match_payload=resume,
        tailoring_suggestion_payload=tailoring,
        critic_guardrail_payload=critic,
        user_preferences=preferences,
    )

    assert first == second
    assert jd == original_jd
    assert resume == original_resume
    assert tailoring == original_tailoring
    assert critic == original_critic
    assert preferences == original_preferences


def test_strategy_recommendation_dry_run_safety_metadata_has_no_runtime_mutation():
    payload = _build()

    safety = payload["safety_metadata"]
    assert safety["dry_run_only"] is True
    assert safety["deterministic_only"] is True
    assert safety["did_call_llm"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["advisory_only"] is True


def test_strategy_recommendation_dry_run_helper_has_no_pipeline_or_storage_calls():
    source_names = set(job_prioritization_agent.build_strategy_recommendation_dry_run_payload.__code__.co_names)

    forbidden = {
        "create_agent_run",
        "record_agent_step",
        "complete_agent_run",
        "complete_agent_step",
        "score_resume_job_match",
        "run_agentic_workflow_dry_run",
        "execute_application",
        "submit_application",
    }
    assert forbidden.isdisjoint(source_names)
