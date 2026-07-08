import ast
from copy import deepcopy
from pathlib import Path

from src.agents.evidence_chain_composition import (
    build_agent_evidence_chain_bundle,
    build_agent_evidence_chain_trace_payload,
)


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FALSE_SAFETY_FLAGS = [
    "provider_call_performed",
    "live_llm_call_performed",
    "evidence_chain_bundle_execution_performed",
    "jd_extraction_performed",
    "jd_wrapper_execution_performed",
    "resume_match_execution_performed",
    "critic_execution_performed",
    "job_prioritization_execution_performed",
    "tailoring_decision_execution_performed",
    "operator_review_execution_performed",
    "trace_persistence_requested",
    "trace_persistence_performed",
    "trace_store_write_performed",
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
        "job_id": "job-95b",
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
        "source_agent": "resume_match",
        "job_id": "job-95b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "missing_required_skills": [],
        "validation_summary": {"validation_status": "passed"},
        "confidence": 0.84,
        "reason_codes": [],
        "safety_metadata": {"provider_call_performed": False},
        "large_nested_detail": {"omit": ["this", "full", "artifact"]},
    }
    payload.update(overrides)
    return payload


def _critic(**overrides):
    payload = {
        "artifact_type": "critic_resume_match_jd_evidence",
        "source_agent": "critic",
        "job_id": "job-95b",
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
        "source_agent": "job_prioritization",
        "job_id": "job-95b",
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
        "source_agent": "tailoring_decision",
        "job_id": "job-95b",
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
        "source_agent": "operator_review",
        "job_id": "job-95b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "operator_review_lane": "ready_to_apply",
        "operator_review_readiness": "ready_without_tailoring",
        "human_review_required": False,
        "recommended_next_step": "review_and_apply_manually",
        "review_packet_summary": {
            "job_id": "job-95b",
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
        "pipeline_run_id": "run-95b",
        "owner_user_id": "owner-95b",
        "context_id": "ctx-95b",
    }
    kwargs.update(overrides)
    return build_agent_evidence_chain_bundle(**kwargs)


def _assert_safety(payload):
    assert payload["default_off"] is True
    assert payload["read_only"] is True
    assert payload["diagnostic_only"] is True
    assert payload["trace_persistence_requested"] is False
    assert payload["trace_persistence_performed"] is False
    for flag in REQUIRED_FALSE_SAFETY_FLAGS:
        assert payload[flag] is False
        assert payload["safety_metadata"][flag] is False


def test_happy_path_builds_trace_payload_from_existing_bundle_only():
    bundle = _bundle()

    payload = build_agent_evidence_chain_trace_payload(bundle)

    assert payload["artifact_type"] == "agent_evidence_chain_trace_payload"
    assert payload["payload_version"] == "agent-evidence-chain-trace-payload-v1"
    assert payload["source_artifact_type"] == "agent_evidence_chain_bundle"
    assert payload["source_agent"] == "evidence_chain_composition"
    assert payload["gate_name"] == "APPLYLENS_AGENTIC_EVIDENCE_CHAIN_TRACE_PAYLOAD_ENABLED"
    assert payload["chain_id"] == bundle["chain_id"]
    assert payload["pipeline_run_id"] == "run-95b"
    assert payload["owner_user_id"] == "owner-95b"
    assert payload["context_id"] == "ctx-95b"
    assert payload["chain_status"] == "complete"
    assert payload["chain_readiness"] == "ready_for_human_review"
    assert payload["agent_run_compatible_summary"]["ordered_agent_count"] == 6
    assert payload["agent_run_compatible_summary"]["included_agent_count"] == 6
    assert [step["agent_key"] for step in payload["agent_step_compatible_summaries"]] == [
        "jd_intelligence",
        "resume_match",
        "critic",
        "job_prioritization",
        "tailoring_decision",
        "operator_review",
    ]
    assert payload["agent_step_compatible_summaries"][-1]["status_fields"][
        "operator_review_lane"
    ] == "ready_to_apply"
    assert payload["confidence_summary"]["maximum_confidence"] == 0.91
    assert payload["safety_metadata_rollup"]["all_supplied_artifacts_safe"] is True
    _assert_safety(payload)


def test_trace_payload_uses_compact_summaries_without_full_nested_artifacts():
    payload = build_agent_evidence_chain_trace_payload(_bundle())

    assert "artifacts" not in payload
    assert payload["redaction_policy"] == (
        "compact_agent_summaries_only_no_full_nested_artifacts"
    )
    assert payload["sampling_summary"] == {
        "sample_limit": 6,
        "included_agent_count": 6,
        "omitted_agent_count": 0,
        "omitted_field_count": payload["sampling_summary"]["omitted_field_count"],
    }
    resume_step = payload["agent_step_compatible_summaries"][1]
    assert "large_nested_detail" not in resume_step
    assert resume_step["omitted_field_count"] >= 1


def test_missing_bundle_returns_degraded_payload_without_crashing():
    payload = build_agent_evidence_chain_trace_payload(None)

    assert payload["source_artifact_type"] == "unknown"
    assert payload["chain_status"] == "missing_bundle"
    assert payload["chain_readiness"] == "insufficient_evidence"
    assert payload["chain_reason_codes"] == ["agent_evidence_chain_bundle_missing"]
    assert payload["agent_run_compatible_summary"]["missing_agent_count"] == 6
    _assert_safety(payload)


def test_malformed_bundle_returns_deterministic_payload_without_builder_fallback():
    payload = build_agent_evidence_chain_trace_payload(["not", "a", "bundle"])
    wrong_type = build_agent_evidence_chain_trace_payload(
        {"artifact_type": "not_the_chain_bundle", "chain_id": "bad"}
    )

    assert payload["chain_status"] == "malformed_bundle"
    assert payload["chain_reason_codes"] == ["agent_evidence_chain_bundle_malformed"]
    assert wrong_type["source_artifact_type"] == "not_the_chain_bundle"
    assert wrong_type["chain_status"] == "malformed_bundle"
    assert wrong_type["chain_reason_codes"] == [
        "agent_evidence_chain_bundle_malformed"
    ]
    _assert_safety(payload)
    _assert_safety(wrong_type)


def test_missing_and_malformed_artifacts_inside_bundle_use_bundle_metadata():
    bundle = _bundle(
        resume_match_jd_evidence={"artifact_type": "wrong"},
        operator_review_tailoring_evidence=None,
    )

    payload = build_agent_evidence_chain_trace_payload(bundle)

    assert payload["chain_status"] == "malformed_artifacts"
    resume_step = payload["agent_step_compatible_summaries"][1]
    operator_step = payload["agent_step_compatible_summaries"][-1]
    assert resume_step["artifact_present"] is True
    assert resume_step["artifact_valid"] is False
    assert "resume_match_artifact_type_mismatch" in resume_step["reason_codes"]
    assert operator_step["artifact_present"] is False
    assert operator_step["artifact_valid"] is False
    assert "operator_review_artifact_missing" in operator_step["reason_codes"]


def test_trace_payload_is_deterministic_and_does_not_mutate_input():
    bundle = _bundle()
    before = deepcopy(bundle)

    first = build_agent_evidence_chain_trace_payload(bundle)
    second = build_agent_evidence_chain_trace_payload(bundle)

    assert first == second
    assert bundle == before


def test_sample_limit_is_deterministic_and_capped_to_six_agents():
    bundle = _bundle()

    small = build_agent_evidence_chain_trace_payload(bundle, sample_limit=3)
    capped = build_agent_evidence_chain_trace_payload(bundle, sample_limit=99)
    fallback = build_agent_evidence_chain_trace_payload(bundle, sample_limit="bad")

    assert [step["agent_key"] for step in small["agent_step_compatible_summaries"]] == [
        "jd_intelligence",
        "resume_match",
        "critic",
    ]
    assert small["sampling_summary"]["included_agent_count"] == 3
    assert small["sampling_summary"]["omitted_agent_count"] == 3
    assert capped["sampling_summary"]["included_agent_count"] == 6
    assert fallback["sampling_summary"]["sample_limit"] == 6


def test_phase95b_safety_flags_are_false():
    payload = build_agent_evidence_chain_trace_payload(_bundle())
    _assert_safety(payload)


def test_trace_payload_source_does_not_call_forbidden_runtime_paths():
    path = ROOT / "src/agents/evidence_chain_composition.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    helper = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "build_agent_evidence_chain_trace_payload"
    )
    call_names = set()
    for node in ast.walk(helper):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                call_names.add(func.id)
            elif isinstance(func, ast.Attribute):
                call_names.add(func.attr)

    forbidden_helper_calls = {
        "build_agent_evidence_chain_bundle",
        "describe_existing_job_intelligence_result",
        "build_resume_match_jd_evidence_artifact",
        "build_critic_resume_match_jd_evidence_artifact",
        "build_job_prioritization_critic_evidence_artifact",
        "build_tailoring_decision_priority_evidence_artifact",
        "build_operator_review_tailoring_evidence_artifact",
        "build_existing_job_intelligence_trace_payload",
        "persist_existing_job_intelligence_trace_payload",
        "persist_read_only_advisory_chain_trace",
        "build_job_intelligence",
        "record_agent_step_postgres_payload",
        "create_agent_run_postgres_payload",
        "score_jobs",
        "run_chat_completion",
        "provider_callable",
        "submit_application",
        "click_apply",
        "mark_applied",
        "write_text",
        "open",
    }
    assert not (call_names & forbidden_helper_calls)

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
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
    assert not (imports & forbidden_imports)
