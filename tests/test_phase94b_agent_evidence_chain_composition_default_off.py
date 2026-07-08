import ast
from copy import deepcopy
from pathlib import Path

from src.agents.evidence_chain_composition import build_agent_evidence_chain_bundle


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FALSE_SAFETY_FLAGS = [
    "provider_call_performed",
    "live_llm_call_performed",
    "jd_extraction_performed",
    "jd_wrapper_execution_performed",
    "resume_match_execution_performed",
    "critic_execution_performed",
    "job_prioritization_execution_performed",
    "tailoring_decision_execution_performed",
    "operator_review_execution_performed",
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


def _jd_wrapper(**overrides):
    payload = {
        "status": "completed",
        "job_id": "job-94b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "required_skills": ["Python", "SQL", "RAG"],
        "preferred_skills": ["Airflow"],
        "validation_json": {
            "is_valid_for_existing_output_wrapper": True,
            "missing_or_invalid_fields": [],
        },
        "safety_metadata": {"provider_call_performed": False},
    }
    payload.update(overrides)
    return payload


def _resume_match(**overrides):
    payload = {
        "artifact_type": "resume_match_jd_evidence",
        "job_id": "job-94b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "missing_required_skills": [],
        "validation_summary": {"validation_status": "passed"},
        "confidence": 0.84,
        "safety_metadata": {"provider_call_performed": False},
    }
    payload.update(overrides)
    return payload


def _critic(**overrides):
    payload = {
        "artifact_type": "critic_resume_match_jd_evidence",
        "job_id": "job-94b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "critic_status": "approved",
        "evidence_quality": "strong",
        "risk_flags": [],
        "contradiction_flags": [],
        "reason_codes": [],
        "validation_summary": {"validation_status": "passed"},
        "confidence": 0.86,
        "safety_metadata": {"provider_call_performed": False},
    }
    payload.update(overrides)
    return payload


def _priority(**overrides):
    payload = {
        "artifact_type": "job_prioritization_critic_evidence",
        "job_id": "job-94b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "priority_recommendation": "prioritize",
        "priority_band": "high",
        "readiness_level": "ready_for_tailoring_review",
        "reason_codes": [],
        "validation_summary": {"validation_status": "passed"},
        "confidence": 0.88,
        "safety_metadata": {"provider_call_performed": False},
    }
    payload.update(overrides)
    return payload


def _tailoring(**overrides):
    payload = {
        "artifact_type": "tailoring_decision_priority_evidence",
        "job_id": "job-94b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "tailoring_decision": "no_tailoring_needed",
        "tailoring_readiness": "ready_for_operator_review",
        "reason_codes": [],
        "validation_summary": {"validation_status": "passed"},
        "confidence": 0.9,
        "safety_metadata": {"provider_call_performed": False},
    }
    payload.update(overrides)
    return payload


def _operator_review(**overrides):
    payload = {
        "artifact_type": "operator_review_tailoring_evidence",
        "job_id": "job-94b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "operator_review_lane": "ready_to_apply",
        "operator_review_readiness": "ready_without_tailoring",
        "human_review_required": False,
        "recommended_next_step": "review_and_apply_manually",
        "review_packet_summary": {
            "job_id": "job-94b",
            "title": "AI Platform Engineer",
            "company": "Example AI",
            "selected_resume_id": "resume-main",
            "tailoring_decision": "no_tailoring_needed",
        },
        "reason_codes": [],
        "validation_summary": {"validation_status": "passed"},
        "confidence": 0.91,
        "safety_metadata": {"provider_call_performed": False},
    }
    payload.update(overrides)
    return payload


def _bundle(**overrides):
    kwargs = {
        "jd_intelligence": _jd_wrapper(),
        "resume_match_jd_evidence": _resume_match(),
        "critic_resume_match_jd_evidence": _critic(),
        "job_prioritization_critic_evidence": _priority(),
        "tailoring_decision_priority_evidence": _tailoring(),
        "operator_review_tailoring_evidence": _operator_review(),
        "pipeline_run_id": "run-94b",
        "owner_user_id": "owner-94b",
        "context_id": "ctx-94b",
    }
    kwargs.update(overrides)
    return build_agent_evidence_chain_bundle(**kwargs)


def _assert_safety(payload):
    assert payload["default_off"] is True
    assert payload["read_only"] is True
    assert payload["diagnostic_only"] is True
    for flag in REQUIRED_FALSE_SAFETY_FLAGS:
        assert payload[flag] is False
        assert payload["safety_metadata"][flag] is False


def test_happy_path_bundles_valid_already_built_artifacts():
    resume = _resume_match()
    payload = _bundle(resume_match_jd_evidence=resume)

    assert payload["artifact_type"] == "agent_evidence_chain_bundle"
    assert payload["source_agent"] == "evidence_chain_composition"
    assert payload["ordered_agent_keys"] == [
        "jd_intelligence",
        "resume_match",
        "critic",
        "job_prioritization",
        "tailoring_decision",
        "operator_review",
    ]
    assert payload["gate_name"] == "APPLYLENS_AGENTIC_EVIDENCE_CHAIN_COMPOSITION_ENABLED"
    assert payload["chain_status"] == "complete"
    assert payload["chain_readiness"] == "ready_for_human_review"
    assert payload["artifacts"]["resume_match"] == resume
    assert payload["artifacts"]["resume_match"] is not resume
    assert payload["artifact_presence"]["operator_review"]["present"] is True
    assert payload["artifact_validity"]["operator_review"]["valid"] is True
    assert payload["terminal_operator_review_summary"]["operator_review_lane"] == "ready_to_apply"
    assert payload["confidence_summary"]["maximum_confidence"] == 0.91
    assert payload["safety_metadata_rollup"]["all_supplied_artifacts_safe"] is True
    _assert_safety(payload)


def test_missing_required_terminal_artifacts_degrades_without_crashing():
    payload = _bundle(
        tailoring_decision_priority_evidence=None,
        operator_review_tailoring_evidence=None,
    )

    assert payload["chain_status"] == "missing_required_artifacts"
    assert payload["chain_readiness"] == "insufficient_evidence"
    assert "tailoring_decision_artifact_missing" in payload["chain_reason_codes"]
    assert "operator_review_artifact_missing" in payload["chain_reason_codes"]
    assert payload["artifact_presence"]["operator_review"]["present"] is False
    _assert_safety(payload)


def test_missing_earlier_optional_artifacts_returns_partial_bundle():
    payload = _bundle(
        jd_intelligence=None,
        resume_match_jd_evidence=None,
        critic_resume_match_jd_evidence=None,
        job_prioritization_critic_evidence=None,
    )

    assert payload["chain_status"] == "partial"
    assert payload["chain_readiness"] == "needs_more_evidence"
    assert "jd_intelligence_artifact_missing" in payload["chain_reason_codes"]
    assert "resume_match_artifact_missing" in payload["chain_reason_codes"]
    assert "critic_artifact_missing" in payload["chain_reason_codes"]
    assert "job_prioritization_artifact_missing" in payload["chain_reason_codes"]
    assert payload["artifact_validity"]["tailoring_decision"]["valid"] is True
    assert payload["artifact_validity"]["operator_review"]["valid"] is True


def test_malformed_artifacts_are_reported_without_upstream_fallback():
    payload = _bundle(
        resume_match_jd_evidence=["not", "a", "mapping"],
        critic_resume_match_jd_evidence={"artifact_type": "wrong_artifact"},
    )

    assert payload["chain_status"] == "malformed_artifacts"
    assert payload["chain_readiness"] == "needs_manual_review"
    assert "resume_match_artifact_malformed" in payload["chain_reason_codes"]
    assert "critic_artifact_type_mismatch" in payload["chain_reason_codes"]
    assert payload["artifact_validity"]["resume_match"]["is_mapping"] is False
    assert payload["artifact_validity"]["critic"]["valid"] is False


def test_blocked_risk_propagates_to_chain_status_and_readiness():
    payload = _bundle(
        critic_resume_match_jd_evidence=_critic(
            risk_flags=["required_skill_coverage_low"],
            contradiction_flags=["jd_context_conflict"],
            reason_codes=["upstream_evidence_contradiction"],
        ),
        tailoring_decision_priority_evidence=_tailoring(
            tailoring_decision="do_not_tailor",
            tailoring_readiness="blocked_by_risk",
            reason_codes=["priority_high_with_critic_risk_flags"],
        ),
        operator_review_tailoring_evidence=_operator_review(
            operator_review_lane="hold_or_skip",
            operator_review_readiness="blocked_by_risk",
            reason_codes=["no_tailoring_needed_with_critic_risk_flags"],
        ),
    )

    assert payload["chain_status"] == "blocked_by_risk"
    assert payload["chain_readiness"] == "blocked_by_risk"
    assert "priority_high_with_critic_risk_flags" in payload["chain_reason_codes"]
    assert "upstream_evidence_contradiction" in payload["chain_reason_codes"]


def test_safety_rollup_surfaces_risky_claims_without_performing_actions():
    payload = _bundle(
        resume_match_jd_evidence=_resume_match(
            safety_metadata={"provider_call_performed": True}
        )
    )

    assert payload["chain_status"] == "partial"
    assert payload["chain_readiness"] == "needs_manual_review"
    assert payload["provider_call_performed"] is False
    assert payload["safety_metadata"]["provider_call_performed"] is False
    assert payload["safety_metadata_rollup"]["all_supplied_artifacts_safe"] is False
    assert payload["safety_metadata_rollup"]["risky_flags_by_agent"] == {
        "resume_match": ["provider_call_performed"]
    }
    assert "resume_match_risky_safety_flags" in payload["chain_reason_codes"]


def test_bundle_is_deterministic_and_does_not_mutate_inputs():
    inputs = {
        "jd_intelligence": _jd_wrapper(),
        "resume_match_jd_evidence": _resume_match(),
        "critic_resume_match_jd_evidence": _critic(),
        "job_prioritization_critic_evidence": _priority(),
        "tailoring_decision_priority_evidence": _tailoring(),
        "operator_review_tailoring_evidence": _operator_review(),
    }
    before = deepcopy(inputs)

    first = build_agent_evidence_chain_bundle(**inputs)
    second = build_agent_evidence_chain_bundle(**inputs)

    assert first == second
    assert inputs == before


def test_phase94b_safety_flags_are_false():
    payload = _bundle()
    _assert_safety(payload)


def test_module_source_does_not_call_or_import_forbidden_runtime_paths():
    path = ROOT / "src/agents/evidence_chain_composition.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_imports = {
        "src.pipeline.collector",
        "src.app.api",
        "src.app.services",
        "src.storage.agent_trace.store",
        "src.ai",
        "src.intelligence.job_intelligence",
        "src.agents.resume_match_agent",
        "src.agents.critic_agent",
        "src.agents.job_prioritization_agent",
        "src.agents.tailoring_decision_agent",
        "src.agents.operator_review_agent",
        "src.agents.workflow_runner",
        "src.agents.read_only_adapter_chain",
        "src.agents.orchestrator_adapter_harness",
    }
    forbidden_calls = {
        "describe_existing_job_intelligence_result",
        "build_resume_match_jd_evidence_artifact",
        "build_critic_resume_match_jd_evidence_artifact",
        "build_job_prioritization_critic_evidence_artifact",
        "build_tailoring_decision_priority_evidence_artifact",
        "build_operator_review_tailoring_evidence_artifact",
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
        "write_text",
        "open",
    }

    imports = set()
    call_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                call_names.add(func.id)
            elif isinstance(func, ast.Attribute):
                call_names.add(func.attr)

    assert not (imports & forbidden_imports)
    assert not (call_names & forbidden_calls)
