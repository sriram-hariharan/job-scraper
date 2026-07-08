import ast
from copy import deepcopy
from pathlib import Path

import pytest

from src.agents.evidence_chain_composition import (
    build_agent_evidence_chain_bundle,
    build_agent_evidence_chain_trace_payload,
    persist_agent_evidence_chain_trace_payload,
)


ROOT = Path(__file__).resolve().parents[1]


REQUIRED_FALSE_SAFETY_FLAGS = [
    "provider_call_performed",
    "live_llm_call_performed",
    "evidence_chain_bundle_execution_performed",
    "evidence_chain_trace_payload_execution_performed",
    "jd_extraction_performed",
    "jd_wrapper_execution_performed",
    "resume_match_execution_performed",
    "critic_execution_performed",
    "job_prioritization_execution_performed",
    "tailoring_decision_execution_performed",
    "operator_review_execution_performed",
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
        "job_id": "job-96b",
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


def _artifact(agent_key, artifact_type, **overrides):
    payload = {
        "artifact_type": artifact_type,
        "source_agent": agent_key,
        "job_id": "job-96b",
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "selected_resume_id": "resume-main",
        "reason_codes": [],
        "validation_summary": {"validation_status": "passed"},
        "confidence": 0.86,
        "safety_metadata": {"provider_call_performed": False},
    }
    payload.update(overrides)
    return payload


def _trace_payload(**bundle_overrides):
    bundle = build_agent_evidence_chain_bundle(
        jd_intelligence=_jd_wrapper(),
        resume_match_jd_evidence=_artifact(
            "resume_match",
            "resume_match_jd_evidence",
            missing_required_skills=[],
            large_nested_detail={"must_not": "persist"},
        ),
        critic_resume_match_jd_evidence=_artifact(
            "critic",
            "critic_resume_match_jd_evidence",
            critic_status="approved",
            evidence_quality="strong",
            risk_flags=[],
            contradiction_flags=[],
        ),
        job_prioritization_critic_evidence=_artifact(
            "job_prioritization",
            "job_prioritization_critic_evidence",
            priority_recommendation="prioritize",
            priority_band="high",
            readiness_level="ready_for_tailoring_review",
        ),
        tailoring_decision_priority_evidence=_artifact(
            "tailoring_decision",
            "tailoring_decision_priority_evidence",
            tailoring_decision="no_tailoring_needed",
            tailoring_readiness="ready_for_operator_review",
        ),
        operator_review_tailoring_evidence=_artifact(
            "operator_review",
            "operator_review_tailoring_evidence",
            operator_review_lane="ready_to_apply",
            operator_review_readiness="ready_without_tailoring",
            recommended_next_step="review_and_apply_manually",
            human_review_required=False,
        ),
        pipeline_run_id="run-96b",
        owner_user_id="owner-96b",
        context_id="ctx-96b",
        **bundle_overrides,
    )
    return build_agent_evidence_chain_trace_payload(bundle)


def _persist(payload=None, **overrides):
    kwargs = {
        "trace_payload": payload if payload is not None else _trace_payload(),
        "owner_user_id": "owner-96b",
        "pipeline_run_id": "run-96b",
        "context_id": "ctx-96b",
    }
    kwargs.update(overrides)
    return persist_agent_evidence_chain_trace_payload(**kwargs)


def _assert_no_non_trace_mutations(result):
    for flag in REQUIRED_FALSE_SAFETY_FLAGS:
        assert result[flag] is False
        assert result["safety_metadata"][flag] is False


def test_gate_disabled_skips_without_executor_call_even_when_strict():
    calls = []
    result = _persist(
        execute_callback=lambda operation: calls.append(operation),
        persistence_gate_enabled=False,
        strict=True,
    )

    assert result["attempted"] is False
    assert result["recorded"] is False
    assert result["reason"] == "trace_persistence_disabled"
    assert result["trace_persistence_enabled"] is False
    assert result["trace_store_write_enabled"] is False
    assert calls == []
    assert result["trace_persistence_requested"] is False
    assert result["trace_persistence_performed"] is False
    assert result["trace_store_write_performed"] is False
    _assert_no_non_trace_mutations(result)


def test_missing_context_is_non_blocking_even_when_strict_enabled():
    calls = []
    result = _persist(
        owner_user_id="",
        persistence_gate_enabled=True,
        execute_callback=lambda operation: calls.append(operation),
        strict=True,
    )

    assert result["attempted"] is False
    assert result["recorded"] is False
    assert result["reason"] == "missing_trace_context"
    assert calls == []
    assert result["trace_persistence_requested"] is True
    assert result["trace_persistence_performed"] is False
    _assert_no_non_trace_mutations(result)


def test_missing_executor_is_non_blocking_even_when_strict_enabled():
    result = _persist(persistence_gate_enabled=True, strict=True)

    assert result["attempted"] is False
    assert result["recorded"] is False
    assert result["reason"] == "write_executor_missing"
    assert result["trace_persistence_requested"] is True
    assert result["trace_persistence_performed"] is False
    _assert_no_non_trace_mutations(result)


def test_multiple_executors_returns_validation_failure_without_choosing_one():
    calls = []

    class FakeCursor:
        def execute(self, sql, params):
            calls.append(("cursor", sql, params))

    result = _persist(
        persistence_gate_enabled=True,
        cursor=FakeCursor(),
        execute_callback=lambda operation: calls.append(("callback", operation)),
    )

    assert result["attempted"] is False
    assert result["recorded"] is False
    assert result["reason"] == "multiple_write_executors"
    assert calls == []


def test_missing_and_malformed_payloads_skip_without_raise_even_when_strict():
    missing = _persist(
        payload=None,
        trace_payload=None,
        persistence_gate_enabled=True,
        execute_callback=lambda operation: operation,
        strict=True,
    )
    malformed = _persist(
        payload=["bad"],
        persistence_gate_enabled=True,
        execute_callback=lambda operation: operation,
        strict=True,
    )

    assert missing["reason"] == "trace_payload_missing_or_malformed"
    assert malformed["reason"] == "trace_payload_missing_or_malformed"
    assert missing["attempted"] is False
    assert malformed["recorded"] is False


def test_wrong_artifact_type_skips_without_raise():
    result = _persist(
        payload={"artifact_type": "wrong"},
        persistence_gate_enabled=True,
        execute_callback=lambda operation: operation,
        strict=True,
    )

    assert result["attempted"] is False
    assert result["recorded"] is False
    assert result["reason"] == "trace_payload_wrong_artifact_type"


def test_execute_callback_path_records_one_run_and_ordered_compact_steps():
    operations = []
    payload = _trace_payload()
    before = deepcopy(payload)

    result = _persist(
        payload=payload,
        persistence_gate_enabled=True,
        execute_callback=lambda operation: operations.append(operation),
    )

    assert result["attempted"] is True
    assert result["recorded"] is True
    assert result["reason"] == ""
    assert result["run_count"] == 1
    assert result["step_count"] == 6
    assert result["record_count"] == 7
    assert result["trace_persistence_enabled"] is True
    assert result["trace_store_write_enabled"] is True
    assert result["trace_persistence_requested"] is True
    assert result["trace_persistence_performed"] is True
    assert result["trace_store_write_performed"] is True
    assert [operation["table"] for operation in operations] == [
        "agent_runs",
        *["agent_steps"] * 6,
    ]
    records = result["recording_payload"]["records"]
    assert [record["snapshot"]["agent_name"] for record in records[1:]] == [
        "jd_intelligence",
        "resume_match",
        "critic",
        "job_prioritization",
        "tailoring_decision",
        "operator_review",
    ]
    assert "artifacts" not in records[0]["snapshot"]["summary_json"]
    assert all("large_nested_detail" not in record["snapshot"]["output_json"] for record in records[1:])
    assert payload == before
    _assert_no_non_trace_mutations(result)


def test_cursor_path_records_one_run_and_steps():
    class FakeCursor:
        def __init__(self):
            self.calls = []

        def execute(self, sql, params):
            self.calls.append((sql, params))

    cursor = FakeCursor()
    result = _persist(persistence_gate_enabled=True, cursor=cursor)

    assert result["attempted"] is True
    assert result["recorded"] is True
    assert len(cursor.calls) == 7
    assert result["record_count"] == 7


def test_non_strict_execution_failure_returns_warning_result():
    def fail(_operation):
        raise RuntimeError("phase96b executor unavailable")

    result = _persist(persistence_gate_enabled=True, execute_callback=fail, strict=False)

    assert result["attempted"] is True
    assert result["recorded"] is False
    assert result["reason"] == "trace_persistence_failed"
    assert "phase96b executor unavailable" in result["error_message"]
    assert result["trace_persistence_performed"] is False
    assert result["trace_store_write_performed"] is False


def test_strict_execution_failure_reraises_after_attempt():
    def fail(_operation):
        raise RuntimeError("phase96b strict executor unavailable")

    with pytest.raises(RuntimeError, match="phase96b strict executor unavailable"):
        _persist(persistence_gate_enabled=True, execute_callback=fail, strict=True)


def test_repeated_calls_have_same_stable_result_shape():
    payload = _trace_payload()

    first = _persist(
        payload=payload,
        persistence_gate_enabled=True,
        execute_callback=lambda operation: operation,
    )
    second = _persist(
        payload=payload,
        persistence_gate_enabled=True,
        execute_callback=lambda operation: operation,
    )

    stable_keys = [
        "persistence_version",
        "artifact_type",
        "source_artifact_type",
        "gate_name",
        "attempted",
        "recorded",
        "record_count",
        "run_count",
        "step_count",
        "agent_run_id",
        "chain_id",
    ]
    assert {key: first[key] for key in stable_keys} == {
        key: second[key] for key in stable_keys
    }


def test_source_safety_for_persistence_helper_only():
    path = ROOT / "src/agents/evidence_chain_composition.py"
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    helper = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef)
        and node.name == "persist_agent_evidence_chain_trace_payload"
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
        "build_agent_evidence_chain_trace_payload",
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
    assert "ensure_schema=True" not in source
