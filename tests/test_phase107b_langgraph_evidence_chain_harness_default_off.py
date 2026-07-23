# phase107b legacy guard marker: changes_only requirements_hash_old 96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 src/app/api.py
import ast
from copy import deepcopy
from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from src.agents import evidence_chain_execution as deterministic
from src.agents import evidence_chain_langgraph_harness as harness


ROOT = Path(__file__).resolve().parents[1]
EXPECTED_AGENT_KEYS = [
    "jd_intelligence",
    "resume_match",
    "critic",
    "job_prioritization",
    "tailoring_decision",
    "operator_review",
]
ARTIFACT_KEYS_BY_AGENT = {
    "jd_intelligence": "jd_intelligence",
    "resume_match": "resume_match_jd_evidence",
    "critic": "critic_resume_match_jd_evidence",
    "job_prioritization": "job_prioritization_critic_evidence",
    "tailoring_decision": "tailoring_decision_priority_evidence",
    "operator_review": "operator_review_tailoring_evidence",
}
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


def _job(job_id="job-107b", **overrides):
    payload = {
        "job_id": job_id,
        "title": "AI Platform Engineer",
        "company": "Example AI",
        "url": "https://example.test/jobs/107b",
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
    assert payload["explicit_call_only"] is True
    for flag in FALSE_SAFETY_FLAGS:
        assert payload[flag] is False
        assert payload["safety_metadata"][flag] is False
    assert payload["automatic_internal_decisioning_performed"] is internal_decisioning
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

    monkeypatch.setattr(harness, "describe_existing_job_intelligence_result", jd)
    monkeypatch.setattr(
        harness,
        "build_resume_match_jd_evidence_artifact",
        resume_match,
    )
    monkeypatch.setattr(
        harness,
        "build_critic_resume_match_jd_evidence_artifact",
        critic,
    )
    monkeypatch.setattr(
        harness,
        "build_job_prioritization_critic_evidence_artifact",
        priority,
    )
    monkeypatch.setattr(
        harness,
        "build_tailoring_decision_priority_evidence_artifact",
        tailoring,
    )
    monkeypatch.setattr(
        harness,
        "build_operator_review_tailoring_evidence_artifact",
        operator_review,
    )


def _run_both(
    jobs,
    *,
    resume_context,
    include_trace_payload=True,
    sample_limit=10,
    strict=True,
):
    deterministic_jobs = deepcopy(jobs)
    langgraph_jobs = deepcopy(jobs)
    deterministic_resume = deepcopy(resume_context)
    langgraph_resume = deepcopy(resume_context)
    deterministic_before = deepcopy(deterministic_jobs)
    langgraph_before = deepcopy(langgraph_jobs)
    deterministic_resume_before = deepcopy(deterministic_resume)
    langgraph_resume_before = deepcopy(langgraph_resume)

    deterministic_payload = deterministic.execute_controlled_evidence_chain(
        deterministic_jobs,
        resume_context=deterministic_resume,
        pipeline_run_id="run-parity",
        owner_user_id="owner-parity",
        context_id="ctx-parity",
        execution_gate_enabled=True,
        include_trace_payload=include_trace_payload,
        sample_limit=sample_limit,
        strict=strict,
    )
    langgraph_payload = harness.execute_langgraph_evidence_chain(
        langgraph_jobs,
        resume_context=langgraph_resume,
        pipeline_run_id="run-parity",
        owner_user_id="owner-parity",
        context_id="ctx-parity",
        enabled=True,
        include_trace_payload=include_trace_payload,
        sample_limit=sample_limit,
        strict=strict,
    )

    assert deterministic_jobs == deterministic_before
    assert langgraph_jobs == langgraph_before
    assert deterministic_resume == deterministic_resume_before
    assert langgraph_resume == langgraph_resume_before
    return deterministic_payload, langgraph_payload


def _normalized_bundle_chain_id(bundle, *, expected_suffix):
    normalized = deepcopy(bundle)
    chain_id = normalized["chain_id"]
    assert chain_id.endswith(expected_suffix)
    normalized["chain_id"] = "<engine-specific-chain-id>"
    return normalized


def _normalized_trace_chain_id(trace_payload, *, expected_suffix):
    normalized = deepcopy(trace_payload)
    chain_id = normalized["chain_id"]
    summary_chain_id = normalized["agent_run_compatible_summary"]["chain_id"]
    assert chain_id.endswith(expected_suffix)
    assert summary_chain_id == chain_id
    normalized["chain_id"] = "<engine-specific-chain-id>"
    normalized["agent_run_compatible_summary"][
        "chain_id"
    ] = "<engine-specific-chain-id>"
    return normalized


def _assert_engine_presentation_contract(
    deterministic_payload,
    langgraph_payload,
    *,
    completed_with_failures=False,
):
    shared_top_level_fields = (
        "execution_gate_enabled",
        "default_off",
        "read_only",
        "diagnostic_only",
        "attempted",
        "executed",
        "jobs_received_count",
        "jobs_sampled_count",
        "jobs_executed_count",
        "jobs_succeeded_count",
        "jobs_failed_count",
        "sample_limit",
        "pipeline_run_id",
        "owner_user_id",
        "context_id",
        "include_trace_payload",
        "safety_metadata",
    )
    for field in shared_top_level_fields:
        assert deterministic_payload[field] == langgraph_payload[field]

    assert deterministic_payload["artifact_type"] == (
        "controlled_evidence_chain_execution_result"
    )
    assert langgraph_payload["artifact_type"] == "langgraph_evidence_chain_execution"
    assert deterministic_payload["gate_name"] == (
        "APPLYLENS_AGENTIC_EVIDENCE_CHAIN_EXECUTION_ENABLED"
    )
    assert langgraph_payload["gate_name"] == (
        "APPLYLENS_AGENTIC_LANGGRAPH_EVIDENCE_CHAIN_ENABLED"
    )
    reason_suffix = "_completed_with_failures" if completed_with_failures else "_completed"
    assert deterministic_payload["reason"] == f"evidence_chain_execution{reason_suffix}"
    assert langgraph_payload["reason"] == (
        f"langgraph_evidence_chain{reason_suffix}"
    )
    assert langgraph_payload["enabled"] is True
    assert langgraph_payload["graph_runtime"] == "langgraph"
    assert langgraph_payload["explicit_call_only"] is True
    assert langgraph_payload["job_count"] == deterministic_payload["jobs_received_count"]
    assert langgraph_payload["processed_count"] == deterministic_payload[
        "jobs_executed_count"
    ]
    assert langgraph_payload["ordered_agent_keys"] == EXPECTED_AGENT_KEYS

    expected_aggregate_reasons = list(
        dict.fromkeys(
            code
            for result in deterministic_payload["per_job_results"]
            for code in result["reason_codes"]
        )
    )
    assert deterministic_payload["aggregate_reason_codes"] == expected_aggregate_reasons
    expected_warning = (
        ["langgraph_evidence_chain_job_failed"] if completed_with_failures else []
    )
    assert langgraph_payload["warnings"] == expected_warning


def _assert_successful_per_job_parity(
    deterministic_result,
    langgraph_result,
    *,
    include_trace_payload,
):
    for field in ("job_id", "title", "company", "status", "reason_codes"):
        assert deterministic_result[field] == langgraph_result[field]

    deterministic_artifacts = deterministic_result["artifacts"]
    langgraph_artifacts = langgraph_result["artifacts"]
    for artifact_key in ARTIFACT_KEYS_BY_AGENT.values():
        assert deterministic_artifacts[artifact_key] == langgraph_artifacts[artifact_key]

    deterministic_bundle = deterministic_artifacts["agent_evidence_chain_bundle"]
    langgraph_bundle = langgraph_artifacts["agent_evidence_chain_bundle"]
    assert _normalized_bundle_chain_id(
        deterministic_bundle,
        expected_suffix=":evidence-chain",
    ) == _normalized_bundle_chain_id(
        langgraph_bundle,
        expected_suffix=":langgraph-evidence-chain",
    )
    assert langgraph_result["evidence_chain_bundle"] == langgraph_bundle

    if include_trace_payload:
        deterministic_trace = deterministic_artifacts[
            "agent_evidence_chain_trace_payload"
        ]
        langgraph_trace = langgraph_artifacts[
            "agent_evidence_chain_trace_payload"
        ]
        assert _normalized_trace_chain_id(
            deterministic_trace,
            expected_suffix=":evidence-chain",
        ) == _normalized_trace_chain_id(
            langgraph_trace,
            expected_suffix=":langgraph-evidence-chain",
        )
        assert langgraph_result["trace_payload"] == langgraph_trace
    else:
        assert "agent_evidence_chain_trace_payload" not in deterministic_artifacts
        assert "agent_evidence_chain_trace_payload" not in langgraph_artifacts
        assert langgraph_result["trace_payload"] == {}

    assert langgraph_result["graph_runtime"] == "langgraph"
    assert langgraph_result["ordered_node_keys"] == EXPECTED_AGENT_KEYS
    assert langgraph_result["ordered_agent_keys"] == EXPECTED_AGENT_KEYS
    assert [item["agent_key"] for item in langgraph_result["node_statuses"]] == (
        EXPECTED_AGENT_KEYS
    )
    assert all(
        item["status"] == "completed"
        for item in langgraph_result["node_statuses"]
    )


def test_langgraph_dependency_declared_and_harness_uses_state_graph():
    requirements = (ROOT / "requirements.txt").read_text()
    source = (ROOT / "src/agents/evidence_chain_langgraph_harness.py").read_text()
    assert "\nlanggraph\n" in f"\n{requirements}\n"
    assert "from langgraph.graph import END, StateGraph" in source
    assert "StateGraph(EvidenceChainGraphState)" in source
    assert "graph.add_node(\"jd_intelligence\"" in source


def test_gate_off_skips_graph_and_helpers_without_input_mutation(monkeypatch):
    def fail_helper(*args, **kwargs):
        raise AssertionError("helper should not run while disabled")

    monkeypatch.setattr(harness, "_compile_graph", fail_helper)
    monkeypatch.setattr(
        harness,
        "describe_existing_job_intelligence_result",
        fail_helper,
    )
    jobs = [_job()]
    before = deepcopy(jobs)

    payload = harness.execute_langgraph_evidence_chain(
        jobs,
        resume_context=_resume_context(),
        enabled=False,
        strict=True,
    )

    assert jobs == before
    assert payload["enabled"] is False
    assert payload["executed"] is False
    assert payload["reason"] == "langgraph_evidence_chain_disabled"
    assert payload["per_job_results"] == []
    _assert_safe(payload, internal_decisioning=False)


def test_gate_on_executes_six_node_langgraph_in_order(monkeypatch):
    calls = []
    _patch_success_chain(monkeypatch, calls)

    payload = harness.execute_langgraph_evidence_chain(
        [_job()],
        resume_context=_resume_context(),
        pipeline_run_id="run-107b",
        owner_user_id="owner-107b",
        context_id="ctx-107b",
        enabled=True,
        strict=True,
    )

    assert payload["enabled"] is True
    assert payload["executed"] is True
    assert calls == EXPECTED_AGENT_KEYS
    result = payload["per_job_results"][0]
    assert result["ordered_node_keys"] == EXPECTED_AGENT_KEYS
    assert [status["agent_key"] for status in result["node_statuses"]] == EXPECTED_AGENT_KEYS
    _assert_safe(payload, internal_decisioning=True)


def test_gate_on_returns_bundle_operator_review_and_optional_trace(monkeypatch):
    calls = []
    _patch_success_chain(monkeypatch, calls)

    with_trace = harness.execute_langgraph_evidence_chain(
        [_job()],
        resume_context=_resume_context(),
        include_trace_payload=True,
        enabled=True,
        strict=True,
    )
    result = with_trace["per_job_results"][0]
    artifacts = result["artifacts"]

    assert result["evidence_chain_bundle"]["artifact_type"] == "agent_evidence_chain_bundle"
    assert result["evidence_chain_bundle"]["ordered_agent_keys"] == EXPECTED_AGENT_KEYS
    assert artifacts["operator_review_tailoring_evidence"]["artifact_type"] == (
        "operator_review_tailoring_evidence"
    )
    assert result["trace_payload"]["artifact_type"] == "agent_evidence_chain_trace_payload"

    without_trace = harness.execute_langgraph_evidence_chain(
        [_job(job_id="job-107b-no-trace")],
        resume_context=_resume_context(),
        include_trace_payload=False,
        enabled=True,
        strict=True,
    )
    no_trace_result = without_trace["per_job_results"][0]
    assert "agent_evidence_chain_trace_payload" not in no_trace_result["artifacts"]
    assert no_trace_result["trace_payload"] == {}


def test_input_jobs_are_not_mutated_when_enabled(monkeypatch):
    calls = []
    _patch_success_chain(monkeypatch, calls)
    jobs = [_job()]
    before = deepcopy(jobs)

    harness.execute_langgraph_evidence_chain(
        jobs,
        resume_context=_resume_context(),
        enabled=True,
        strict=True,
    )

    assert jobs == before


def test_harness_source_has_no_provider_persistence_collector_api_or_ui_wiring():
    source_path = ROOT / "src/agents/evidence_chain_langgraph_harness.py"
    source = source_path.read_text()
    tree = ast.parse(source)
    forbidden_import_fragments = [
        "src.pipeline.collector",
        "src.app.api",
        "src.app.services",
        "src.ai.llm_client",
        "src.ai.job_fit_evaluator",
        "src.storage.agent_trace.store",
        "src.storage.agent_state.store",
    ]
    forbidden_calls = {
        "run_chat_completion",
        "run_chat_completion_with_metadata",
        "persist_agent_evidence_chain_trace_payload",
        "create_agent_run_postgres_payload",
        "record_agent_step_postgres_payload",
        "open",
    }

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported = (
                node.module
                if isinstance(node, ast.ImportFrom)
                else " ".join(alias.name for alias in node.names)
            )
            assert not any(fragment in imported for fragment in forbidden_import_fragments)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls


def test_compatibility_shape_matches_existing_controlled_execution(monkeypatch):
    calls = []
    _patch_success_chain(monkeypatch, calls)

    payload = harness.execute_langgraph_evidence_chain(
        [_job()],
        resume_context=_resume_context(),
        pipeline_run_id="run-compat",
        owner_user_id="owner-compat",
        context_id="ctx-compat",
        enabled=True,
        strict=True,
    )

    result = payload["per_job_results"][0]
    assert payload["artifact_type"] == "langgraph_evidence_chain_execution"
    assert payload["graph_runtime"] == "langgraph"
    assert payload["processed_count"] == 1
    assert result["artifacts"]["agent_evidence_chain_bundle"]["artifact_type"] == (
        "agent_evidence_chain_bundle"
    )
    assert set(EXPECTED_AGENT_KEYS).issubset(
        result["artifacts"]["agent_evidence_chain_bundle"]["artifacts"].keys()
    )
    assert result["artifacts"]["agent_evidence_chain_trace_payload"]["chain_id"]


def test_complete_evidence_has_exact_substantive_parity_and_explicit_identity_difference():
    jobs = [_job()]
    jobs_before = deepcopy(jobs)
    resume_context = _resume_context()
    resume_before = deepcopy(resume_context)

    deterministic_payload, langgraph_payload = _run_both(
        jobs,
        resume_context=resume_context,
    )

    assert jobs == jobs_before
    assert resume_context == resume_before
    _assert_engine_presentation_contract(deterministic_payload, langgraph_payload)
    deterministic_result = deterministic_payload["per_job_results"][0]
    langgraph_result = langgraph_payload["per_job_results"][0]
    _assert_successful_per_job_parity(
        deterministic_result,
        langgraph_result,
        include_trace_payload=True,
    )
    deterministic_bundle = deterministic_result["artifacts"][
        "agent_evidence_chain_bundle"
    ]
    langgraph_bundle = langgraph_result["artifacts"]["agent_evidence_chain_bundle"]
    assert deterministic_bundle["chain_status"] == langgraph_bundle["chain_status"]
    assert deterministic_bundle["chain_readiness"] == langgraph_bundle[
        "chain_readiness"
    ]
    assert deterministic_payload["safety_metadata"] == langgraph_payload[
        "safety_metadata"
    ]
    assert deterministic_payload["provider_call_performed"] is False
    assert langgraph_payload["provider_call_performed"] is False
    assert deterministic_payload["trace_persistence_performed"] is False
    assert langgraph_payload["trace_persistence_performed"] is False

    validation_by_agent = langgraph_bundle["per_agent_validation_summary"]
    for node_summary in langgraph_result["node_statuses"]:
        agent_key = node_summary["agent_key"]
        assert node_summary["status"] == "completed"
        assert node_summary["artifact_key"] == ARTIFACT_KEYS_BY_AGENT[agent_key]
        assert agent_key in validation_by_agent


def test_missing_resume_evidence_degrades_identically_without_skipping_nodes():
    jobs = [_job("job-missing-resume")]
    deterministic_payload, langgraph_payload = _run_both(
        jobs,
        resume_context=None,
    )

    _assert_engine_presentation_contract(deterministic_payload, langgraph_payload)
    deterministic_result = deterministic_payload["per_job_results"][0]
    langgraph_result = langgraph_payload["per_job_results"][0]
    _assert_successful_per_job_parity(
        deterministic_result,
        langgraph_result,
        include_trace_payload=True,
    )
    artifacts = deterministic_result["artifacts"]
    assert artifacts["critic_resume_match_jd_evidence"]["critic_status"] == "rejected"
    assert artifacts["critic_resume_match_jd_evidence"]["evidence_quality"] == "weak"
    assert artifacts["job_prioritization_critic_evidence"][
        "priority_recommendation"
    ] == "manual_review"
    assert artifacts["job_prioritization_critic_evidence"][
        "manual_review_required"
    ] is True
    assert artifacts["tailoring_decision_priority_evidence"][
        "tailoring_decision"
    ] == "do_not_tailor"
    assert artifacts["tailoring_decision_priority_evidence"][
        "operator_review_required"
    ] is True
    assert artifacts["operator_review_tailoring_evidence"][
        "operator_review_lane"
    ] == "hold_or_skip"
    assert artifacts["operator_review_tailoring_evidence"][
        "human_review_required"
    ] is True
    bundle = artifacts["agent_evidence_chain_bundle"]
    assert bundle["chain_status"] == "blocked_by_risk"
    assert bundle["chain_readiness"] == "blocked_by_risk"
    assert langgraph_result["ordered_node_keys"] == EXPECTED_AGENT_KEYS


def test_trace_disabled_preserves_evidence_and_requires_no_write_executor():
    deterministic_payload, langgraph_payload = _run_both(
        [_job("job-no-trace")],
        resume_context=_resume_context(),
        include_trace_payload=False,
    )

    _assert_engine_presentation_contract(deterministic_payload, langgraph_payload)
    _assert_successful_per_job_parity(
        deterministic_payload["per_job_results"][0],
        langgraph_payload["per_job_results"][0],
        include_trace_payload=False,
    )
    assert deterministic_payload["include_trace_payload"] is False
    assert langgraph_payload["include_trace_payload"] is False
    for payload in (deterministic_payload, langgraph_payload):
        assert payload["trace_persistence_performed"] is False
        assert payload["trace_store_write_performed"] is False
        assert payload["database_write_performed"] is False
        assert payload["provider_call_performed"] is False


def test_sampling_selects_same_jobs_in_order_without_mutating_unsampled_jobs():
    jobs = [
        _job(
            "job-sample-a",
            priority_score=12.5,
            queue_rank=1,
            tailoring_decision="no_tailoring_needed",
            application_status="not_applied",
        ),
        _job(
            "job-sample-b",
            priority_score=9.5,
            queue_rank=2,
            tailoring_decision="manual_review_before_tailoring",
            application_status="not_applied",
        ),
        _job(
            "job-unsampled",
            priority_score=99.0,
            queue_rank=3,
            tailoring_decision="do_not_tailor",
            application_status="not_applied",
        ),
    ]
    before = deepcopy(jobs)
    deterministic_payload, langgraph_payload = _run_both(
        jobs,
        resume_context=_resume_context(),
        include_trace_payload=False,
        sample_limit=2,
    )

    assert jobs == before
    _assert_engine_presentation_contract(deterministic_payload, langgraph_payload)
    assert [result["job_id"] for result in deterministic_payload["per_job_results"]] == [
        "job-sample-a",
        "job-sample-b",
    ]
    assert [result["job_id"] for result in langgraph_payload["per_job_results"]] == [
        "job-sample-a",
        "job-sample-b",
    ]
    assert deterministic_payload["jobs_sampled_count"] == 2
    assert langgraph_payload["jobs_sampled_count"] == 2
    for deterministic_result, langgraph_result in zip(
        deterministic_payload["per_job_results"],
        langgraph_payload["per_job_results"],
    ):
        _assert_successful_per_job_parity(
            deterministic_result,
            langgraph_result,
            include_trace_payload=False,
        )
    assert jobs[2] == before[2]
    assert jobs[2]["priority_score"] == 99.0
    assert jobs[2]["queue_rank"] == 3
    assert jobs[2]["tailoring_decision"] == "do_not_tailor"
    assert jobs[2]["application_status"] == "not_applied"


def test_non_strict_failure_preserves_engine_reasons_and_continues(monkeypatch):
    original_resume_match = deterministic.build_resume_match_jd_evidence_artifact

    def controlled_failure(**kwargs):
        if kwargs["job_id"] == "job-fails":
            raise RuntimeError("parity resume boundary failed")
        return original_resume_match(**kwargs)

    monkeypatch.setattr(
        deterministic,
        "build_resume_match_jd_evidence_artifact",
        controlled_failure,
    )
    monkeypatch.setattr(
        harness,
        "build_resume_match_jd_evidence_artifact",
        controlled_failure,
    )
    jobs = [_job("job-fails"), _job("job-continues")]
    before = deepcopy(jobs)

    deterministic_payload, langgraph_payload = _run_both(
        jobs,
        resume_context=_resume_context(),
        include_trace_payload=False,
        strict=False,
    )

    assert jobs == before
    _assert_engine_presentation_contract(
        deterministic_payload,
        langgraph_payload,
        completed_with_failures=True,
    )
    deterministic_failed, deterministic_succeeded = deterministic_payload[
        "per_job_results"
    ]
    langgraph_failed, langgraph_succeeded = langgraph_payload["per_job_results"]
    assert deterministic_failed["status"] == langgraph_failed["status"] == "failed"
    assert deterministic_failed["artifacts"] == {}
    assert langgraph_failed["artifacts"] == {}
    assert deterministic_failed["reason_codes"] == ["evidence_chain_helper_failed"]
    assert langgraph_failed["reason_codes"] == [
        "langgraph_evidence_chain_job_failed"
    ]
    assert "parity resume boundary failed" in deterministic_failed["error_message"]
    assert "parity resume boundary failed" in langgraph_failed["error_message"]
    assert langgraph_failed["ordered_node_keys"] == []
    assert langgraph_failed["node_statuses"] == []
    assert deterministic_payload["trace_persistence_performed"] is False
    assert langgraph_payload["trace_persistence_performed"] is False
    _assert_successful_per_job_parity(
        deterministic_succeeded,
        langgraph_succeeded,
        include_trace_payload=False,
    )


def test_strict_failure_reraises_same_exception_contract_without_mutation(monkeypatch):
    class ParityBoundaryFailure(RuntimeError):
        pass

    def controlled_failure(**_kwargs):
        raise ParityBoundaryFailure("strict parity boundary failed")

    monkeypatch.setattr(
        deterministic,
        "build_resume_match_jd_evidence_artifact",
        controlled_failure,
    )
    monkeypatch.setattr(
        harness,
        "build_resume_match_jd_evidence_artifact",
        controlled_failure,
    )
    deterministic_jobs = [_job("job-strict-deterministic")]
    langgraph_jobs = [_job("job-strict-langgraph")]
    deterministic_before = deepcopy(deterministic_jobs)
    langgraph_before = deepcopy(langgraph_jobs)

    with pytest.raises(ParityBoundaryFailure, match="strict parity boundary failed"):
        deterministic.execute_controlled_evidence_chain(
            deterministic_jobs,
            resume_context=_resume_context(),
            execution_gate_enabled=True,
            strict=True,
        )
    with pytest.raises(ParityBoundaryFailure, match="strict parity boundary failed"):
        harness.execute_langgraph_evidence_chain(
            langgraph_jobs,
            resume_context=_resume_context(),
            enabled=True,
            strict=True,
        )

    assert deterministic_jobs == deterministic_before
    assert langgraph_jobs == langgraph_before


def test_parity_contract_adds_no_routing_checkpoint_interrupt_or_action_paths():
    paths = (
        ROOT / "src/agents/evidence_chain_execution.py",
        ROOT / "src/agents/evidence_chain_langgraph_harness.py",
    )
    forbidden_import_fragments = {
        "langgraph.checkpoint",
        "langgraph.types",
        "pickle",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "src.storage.operator_decisions",
        "src.storage.agentic_approvals",
        "src.storage.application_actions",
        "src.storage.patch_selections",
    }
    forbidden_calls = {
        "add_conditional_edges",
        "interrupt",
        "persist_agent_evidence_chain_trace_payload",
        "run_chat_completion",
        "run_chat_completion_with_metadata",
        "score_jobs",
        "execute_application",
        "submit_application",
        "mark_applied",
        "insert_operator_decision_row_to_postgres",
        "insert_application_action_row_to_postgres",
        "write_text",
        "open",
        "__import__",
        "getenv",
    }

    for path in paths:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = set()
        calls = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.add(node.module or "")
            elif isinstance(node, ast.Call):
                calls.append(node)
        assert not any(
            fragment in imported
            for imported in imports
            for fragment in forbidden_import_fragments
        )
        called_names = {
            node.func.id
            for node in calls
            if isinstance(node.func, ast.Name)
        }
        called_attributes = {
            node.func.attr
            for node in calls
            if isinstance(node.func, ast.Attribute)
        }
        assert forbidden_calls.isdisjoint(called_names | called_attributes)
        for node in calls:
            if (
                isinstance(node.func, ast.Attribute)
                and node.func.attr == "compile"
            ):
                assert all(keyword.arg != "checkpointer" for keyword in node.keywords)


def test_initial_state_builder_has_exact_keys_types_and_deep_copies_inputs():
    job = _job(
        "job-initial-state",
        nested_metadata={"skills": ["Python"], "signals": {"rank": 2}},
    )
    resume_rows = deepcopy(_resume_context()["resume_variants"])
    identity = {
        "job_id": "job-initial-state",
        "title": "AI Platform Engineer",
        "company": "Example AI",
    }
    state = harness._build_initial_graph_state(
        job=job,
        job_index=3,
        job_identity=identity,
        resume_rows=resume_rows,
        selected_resume_id="resume-main",
        pipeline_run_id="run-state",
        owner_user_id="owner-state",
        context_id="ctx-state",
        include_trace_payload=True,
    )

    assert set(state) == {
        "job",
        "job_index",
        "job_identity",
        "resume_rows",
        "selected_resume_id",
        "pipeline_run_id",
        "owner_user_id",
        "context_id",
        "include_trace_payload",
        "artifacts",
        "ordered_node_keys",
        "node_statuses",
        "warnings",
    }
    assert isinstance(state["job"], dict)
    assert isinstance(state["job_index"], int)
    assert isinstance(state["job_identity"], dict)
    assert isinstance(state["resume_rows"], list)
    assert isinstance(state["selected_resume_id"], str)
    assert isinstance(state["pipeline_run_id"], str)
    assert isinstance(state["owner_user_id"], str)
    assert isinstance(state["context_id"], str)
    assert isinstance(state["include_trace_payload"], bool)
    assert isinstance(state["artifacts"], dict)
    assert isinstance(state["ordered_node_keys"], list)
    assert isinstance(state["node_statuses"], list)
    assert isinstance(state["warnings"], list)

    job["nested_metadata"]["skills"].append("SQL")
    job["nested_metadata"]["signals"]["rank"] = 99
    resume_rows[0]["skills"].append("Airflow")
    identity["title"] = "Mutated title"
    assert state["job"]["nested_metadata"] == {
        "skills": ["Python"],
        "signals": {"rank": 2},
    }
    assert state["resume_rows"][0]["skills"] == ["Python", "SQL", "RAG"]
    assert state["job_identity"]["title"] == "AI Platform Engineer"


def test_state_transition_isolates_all_owned_containers_and_summary_shape():
    initial_state = harness._build_initial_graph_state(
        job=_job("job-transition"),
        job_index=0,
        job_identity={
            "job_id": "job-transition",
            "title": "AI Platform Engineer",
            "company": "Example AI",
        },
        resume_rows=_resume_context()["resume_variants"],
        selected_resume_id="resume-main",
        pipeline_run_id="run-transition",
        owner_user_id="owner-transition",
        context_id="ctx-transition",
        include_trace_payload=True,
    )
    jd_artifact = {
        "status": "completed",
        "validation_json": {
            "is_valid_for_existing_output_wrapper": True,
            "missing_or_invalid_fields": [],
        },
        "reason_codes": [],
    }
    jd_state = harness._state_with_artifact(
        initial_state,
        agent_key="jd_intelligence",
        artifact_key="jd_intelligence",
        artifact=jd_artifact,
    )
    resume_state = harness._state_with_artifact(
        jd_state,
        agent_key="resume_match",
        artifact_key="resume_match_jd_evidence",
        artifact={
            "artifact_type": "resume_match_jd_evidence",
            "validation_summary": {"validation_status": "passed"},
            "reason_codes": [],
        },
    )

    for key in ("artifacts", "ordered_node_keys", "node_statuses", "warnings"):
        assert initial_state[key] is not jd_state[key]
        assert jd_state[key] is not resume_state[key]
    assert set(jd_state["node_statuses"][0]) == {
        "agent_key",
        "node_key",
        "status",
        "artifact_key",
        "artifact_type",
        "reason_codes",
    }
    assert jd_state["node_statuses"][0]["status"] == "completed"

    resume_state["artifacts"]["jd_intelligence"]["validation_json"][
        "missing_or_invalid_fields"
    ].append("mutated")
    resume_state["ordered_node_keys"].append("mutated")
    resume_state["node_statuses"][0]["status"] = "mutated"
    resume_state["warnings"].append("mutated")
    assert jd_state["artifacts"]["jd_intelligence"]["validation_json"][
        "missing_or_invalid_fields"
    ] == []
    assert jd_state["ordered_node_keys"] == ["jd_intelligence"]
    assert jd_state["node_statuses"][0]["status"] == "completed"
    assert jd_state["warnings"] == []
    assert initial_state["artifacts"] == {}
    assert initial_state["ordered_node_keys"] == []
    assert initial_state["node_statuses"] == []
    assert initial_state["warnings"] == []


def test_typed_state_normalization_adds_no_external_per_job_result_keys():
    payload = harness.execute_langgraph_evidence_chain(
        [_job("job-external-shape")],
        resume_context=_resume_context(),
        pipeline_run_id="run-external-shape",
        owner_user_id="owner-external-shape",
        context_id="ctx-external-shape",
        enabled=True,
        strict=True,
    )

    assert set(payload["per_job_results"][0]) == {
        "job_id",
        "title",
        "company",
        "status",
        "reason_codes",
        "graph_runtime",
        "ordered_node_keys",
        "ordered_agent_keys",
        "node_statuses",
        "artifacts",
        "evidence_chain_bundle",
        "trace_payload",
        "safety_metadata",
    }


def _checkpoint_initial_state(
    *,
    job_id="job-checkpoint",
    job_index=0,
    job=None,
    resume_rows=None,
    selected_resume_id="resume-main",
    pipeline_run_id="run-checkpoint",
    owner_user_id="owner-checkpoint",
    context_id="ctx-checkpoint",
):
    resolved_job = deepcopy(job) if job is not None else _job(job_id)
    return harness._build_initial_graph_state(
        job=resolved_job,
        job_index=job_index,
        job_identity={
            "job_id": job_id,
            "title": resolved_job["title"],
            "company": resolved_job["company"],
        },
        resume_rows=deepcopy(
            resume_rows
            if resume_rows is not None
            else _resume_context()["resume_variants"]
        ),
        selected_resume_id=selected_resume_id,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        context_id=context_id,
        include_trace_payload=True,
    )


def _operator_review_pause_state(
    *,
    job_id="job-interrupt-request",
    job_index=0,
    selected_resume_id="resume-main",
    pipeline_run_id="run-interrupt-request",
    owner_user_id="owner-interrupt-request",
    context_id="ctx-interrupt-request",
):
    resume_rows = deepcopy(_resume_context()["resume_variants"])
    resume_rows[0]["resume_id"] = selected_resume_id
    state = _checkpoint_initial_state(
        job_id=job_id,
        job_index=job_index,
        resume_rows=resume_rows,
        selected_resume_id=selected_resume_id,
        pipeline_run_id=pipeline_run_id,
        owner_user_id=owner_user_id,
        context_id=context_id,
    )
    for node in (
        harness._jd_intelligence_node,
        harness._resume_match_node,
        harness._critic_node,
        harness._job_prioritization_node,
        harness._tailoring_decision_node,
        harness._operator_review_node,
    ):
        state = node(state)
    return state


def test_checkpoint_identity_is_stable_and_independent_of_mapping_or_object_identity():
    job_a = _job(
        "job-checkpoint-stable",
        nested_metadata={"alpha": 1, "beta": {"first": True, "second": False}},
    )
    job_b = {
        "nested_metadata": {
            "beta": {"second": False, "first": True},
            "alpha": 1,
        },
        **{
            key: deepcopy(value)
            for key, value in job_a.items()
            if key != "nested_metadata"
        },
    }
    state_a = _checkpoint_initial_state(
        job_id="job-checkpoint-stable",
        job=job_a,
    )
    state_b = _checkpoint_initial_state(
        job_id="job-checkpoint-stable",
        job=job_b,
    )

    identity_a = harness._build_checkpoint_identity(state_a)
    identity_b = harness._build_checkpoint_identity(state_b)
    assert identity_a == identity_b
    assert identity_a is not identity_b
    assert identity_a.graph_invocation_id == identity_b.graph_invocation_id
    assert identity_a.checkpoint_id == identity_b.checkpoint_id
    with pytest.raises(FrozenInstanceError):
        identity_a.job_id = "mutated"


def test_checkpoint_identity_changes_for_different_job_or_selected_index():
    base = harness._build_checkpoint_identity(
        _checkpoint_initial_state(job_id="job-checkpoint-a", job_index=0)
    )
    different_job = harness._build_checkpoint_identity(
        _checkpoint_initial_state(job_id="job-checkpoint-b", job_index=0)
    )
    different_index = harness._build_checkpoint_identity(
        _checkpoint_initial_state(job_id="job-checkpoint-a", job_index=1)
    )

    assert base.graph_invocation_id != different_job.graph_invocation_id
    assert base.checkpoint_id != different_job.checkpoint_id
    assert base.graph_invocation_id != different_index.graph_invocation_id
    assert base.checkpoint_id != different_index.checkpoint_id


def test_complete_checkpoint_round_trip_is_deterministic_and_lossless():
    initial_state = _checkpoint_initial_state(job_id="job-checkpoint-complete")
    final_state = harness._execute_graph_state(initial_state)
    final_before = deepcopy(final_state)

    envelope = harness._build_checkpoint_envelope(final_state)
    first_serialized = harness._serialize_checkpoint_envelope(envelope)
    second_serialized = harness._serialize_checkpoint_envelope(
        harness._build_checkpoint_envelope(deepcopy(final_state))
    )
    restored = harness._deserialize_checkpoint_envelope(first_serialized)

    assert first_serialized == second_serialized
    assert restored == envelope
    assert restored["state"] == final_state
    assert restored["completed_node_keys"] == EXPECTED_AGENT_KEYS
    assert restored["next_node_key"] == ""
    assert restored["checkpoint_status"] == "diagnostic_snapshot"
    assert restored["diagnostic_only"] is True
    assert restored["read_only"] is True
    assert restored["durable"] is False
    assert restored["resumable"] is False
    assert restored["persistence_performed"] is False
    assert final_state == final_before


def test_initial_and_partial_checkpoint_states_round_trip_with_derived_next_node():
    initial_state = _checkpoint_initial_state(job_id="job-checkpoint-partial")
    partial_state = harness._jd_intelligence_node(initial_state)

    initial_restored = harness._deserialize_checkpoint_envelope(
        harness._serialize_checkpoint_envelope(
            harness._build_checkpoint_envelope(initial_state)
        )
    )
    partial_restored = harness._deserialize_checkpoint_envelope(
        harness._serialize_checkpoint_envelope(
            harness._build_checkpoint_envelope(partial_state)
        )
    )

    assert initial_restored["state"] == initial_state
    assert initial_restored["completed_node_keys"] == []
    assert initial_restored["next_node_key"] == "jd_intelligence"
    assert partial_restored["state"] == partial_state
    assert partial_restored["completed_node_keys"] == ["jd_intelligence"]
    assert partial_restored["next_node_key"] == "resume_match"


def test_checkpoint_round_trip_returns_fresh_mutable_containers():
    state = _checkpoint_initial_state(job_id="job-checkpoint-fresh")
    partial_state = harness._jd_intelligence_node(state)
    envelope = harness._build_checkpoint_envelope(partial_state)
    envelope_before = deepcopy(envelope)
    partial_before = deepcopy(partial_state)
    restored = harness._deserialize_checkpoint_envelope(
        harness._serialize_checkpoint_envelope(envelope)
    )

    restored["state"]["job"]["title"] = "Mutated restored title"
    restored["state"]["artifacts"]["jd_intelligence"]["required_skills"].append(
        "mutated"
    )
    restored["completed_node_keys"].append("mutated")
    restored["checkpoint_identity"]["job_id"] = "mutated"
    assert envelope == envelope_before
    assert partial_state == partial_before


def test_checkpoint_deserialization_fails_closed_for_malformed_or_unsupported_payloads():
    envelope = harness._build_checkpoint_envelope(
        _checkpoint_initial_state(job_id="job-checkpoint-invalid")
    )
    unsupported_checkpoint = deepcopy(envelope)
    unsupported_checkpoint["checkpoint_schema_version"] = "unsupported"
    unsupported_state = deepcopy(envelope)
    unsupported_state["graph_state_schema_version"] = "unsupported"

    for malformed in ("", "{", "[]", '{"unexpected":true}'):
        with pytest.raises(ValueError):
            harness._deserialize_checkpoint_envelope(malformed)
    with pytest.raises(ValueError, match="checkpoint_schema_version_unsupported"):
        harness._deserialize_checkpoint_envelope(
            harness._serialize_checkpoint_envelope(unsupported_checkpoint)
        )
    with pytest.raises(
        ValueError,
        match="checkpoint_graph_state_schema_version_unsupported",
    ):
        harness._deserialize_checkpoint_envelope(
            harness._serialize_checkpoint_envelope(unsupported_state)
        )


def test_checkpoint_deserialization_rejects_identity_mismatch_and_missing_fields():
    state = _checkpoint_initial_state(job_id="job-checkpoint-mismatch")
    envelope = harness._build_checkpoint_envelope(state)
    mismatch = deepcopy(envelope)
    mismatch["checkpoint_identity"]["job_id"] = "different-job"
    missing_identity = deepcopy(envelope)
    del missing_identity["checkpoint_identity"]["owner_user_id"]
    missing_state_identity = deepcopy(state)
    missing_state_identity["owner_user_id"] = ""

    with pytest.raises(ValueError, match="checkpoint_identity_mismatch"):
        harness._deserialize_checkpoint_envelope(
            harness._serialize_checkpoint_envelope(mismatch)
        )
    with pytest.raises(ValueError, match="checkpoint_identity_fields_invalid"):
        harness._deserialize_checkpoint_envelope(
            harness._serialize_checkpoint_envelope(missing_identity)
        )
    with pytest.raises(
        ValueError,
        match="checkpoint_identity_missing_required_field:owner_user_id",
    ):
        harness._build_checkpoint_envelope(missing_state_identity)


def test_checkpoint_serialization_does_not_mutate_state_or_caller_inputs():
    caller_job = _job(
        "job-checkpoint-immutable",
        nested_metadata={"skills": ["Python"], "rank": 1},
    )
    caller_resume_rows = deepcopy(_resume_context()["resume_variants"])
    caller_job_before = deepcopy(caller_job)
    caller_resume_before = deepcopy(caller_resume_rows)
    state = _checkpoint_initial_state(
        job_id="job-checkpoint-immutable",
        job=caller_job,
        resume_rows=caller_resume_rows,
    )
    state_before = deepcopy(state)

    envelope = harness._build_checkpoint_envelope(state)
    serialized = harness._serialize_checkpoint_envelope(envelope)
    harness._deserialize_checkpoint_envelope(serialized)

    assert caller_job == caller_job_before
    assert caller_resume_rows == caller_resume_before
    assert state == state_before
    assert "checkpoint_identity" not in state
    assert "checkpoint_id" not in state


def test_normal_execution_exposes_no_checkpoint_contract_fields():
    payload = harness.execute_langgraph_evidence_chain(
        [_job("job-no-checkpoint-output")],
        resume_context=_resume_context(),
        pipeline_run_id="run-no-checkpoint-output",
        owner_user_id="owner-no-checkpoint-output",
        context_id="ctx-no-checkpoint-output",
        enabled=True,
        strict=True,
    )

    assert "checkpoint" not in payload
    assert "checkpoint_identity" not in payload
    assert "checkpoint_id" not in payload
    assert "checkpoint" not in payload["per_job_results"][0]
    assert "checkpoint_identity" not in payload["per_job_results"][0]
    assert "checkpoint_id" not in payload["per_job_results"][0]


def test_interrupt_request_is_deterministic_and_artifact_order_independent():
    state = _operator_review_pause_state()
    reordered = deepcopy(state)
    artifact = reordered["artifacts"]["operator_review_tailoring_evidence"]
    reordered_artifact = {
        key: deepcopy(artifact[key])
        for key in reversed(list(artifact))
    }
    validation = reordered_artifact["validation_summary"]
    reordered_artifact["validation_summary"] = {
        key: deepcopy(validation[key])
        for key in reversed(list(validation))
    }
    reordered["artifacts"][
        "operator_review_tailoring_evidence"
    ] = reordered_artifact
    state_before = deepcopy(state)
    reordered_before = deepcopy(reordered)

    first = harness._build_operator_review_interrupt_request(state)
    second = harness._build_operator_review_interrupt_request(reordered)

    assert first == second
    assert first["interrupt_request_id"] == second["interrupt_request_id"]
    assert first["operator_review_artifact_digest"] == (
        second["operator_review_artifact_digest"]
    )
    assert state == state_before
    assert reordered == reordered_before


def test_operator_review_artifact_digest_rejects_noncanonical_values_and_tracks_content():
    artifact = {
        "artifact_type": "operator_review_tailoring_evidence",
        "nested": {"alpha": 1, "beta": ["value"]},
    }
    reordered = {
        "nested": {"beta": ["value"], "alpha": 1},
        "artifact_type": "operator_review_tailoring_evidence",
    }
    changed = deepcopy(artifact)
    changed["nested"]["beta"] = ["different"]

    assert harness._operator_review_artifact_digest(artifact) == (
        harness._operator_review_artifact_digest(reordered)
    )
    assert harness._operator_review_artifact_digest(artifact) != (
        harness._operator_review_artifact_digest(changed)
    )
    for malformed in (
        {1: "non-string-key"},
        {"unsupported": ("tuple",)},
        {"non_finite": float("inf")},
    ):
        with pytest.raises(ValueError):
            harness._operator_review_artifact_digest(malformed)


def test_interrupt_request_has_exact_identity_evidence_decisions_and_safety():
    state = _operator_review_pause_state()
    request = harness._build_operator_review_interrupt_request(state)
    artifact = state["artifacts"]["operator_review_tailoring_evidence"]
    checkpoint_identity = harness._build_checkpoint_identity(state)

    assert set(request) == set(
        harness.OperatorReviewInterruptRequest.__required_keys__
    )
    assert request["interrupt_request_schema_version"] == (
        "operator-review-interrupt-request-v1"
    )
    assert request["graph_engine"] == checkpoint_identity.graph_engine
    assert request["graph_invocation_id"] == (
        checkpoint_identity.graph_invocation_id
    )
    assert request["checkpoint_id"] == checkpoint_identity.checkpoint_id
    assert request["checkpoint_schema_version"] == (
        harness.CHECKPOINT_SCHEMA_VERSION
    )
    assert request["graph_state_schema_version"] == (
        harness.GRAPH_STATE_SCHEMA_VERSION
    )
    assert request["owner_user_id"] == "owner-interrupt-request"
    assert request["pipeline_run_id"] == "run-interrupt-request"
    assert request["context_id"] == "ctx-interrupt-request"
    assert request["job_id"] == "job-interrupt-request"
    assert request["job_index"] == 0
    assert request["selected_resume_id"] == "resume-main"
    assert request["node_key"] == "operator_review"
    assert request["completed_node_keys"] == EXPECTED_AGENT_KEYS
    assert request["safe_next_node_key"] == "finalize"
    assert request["operator_review_artifact_type"] == artifact["artifact_type"]
    assert request["operator_review_artifact_version"] == (
        artifact["artifact_version"]
    )
    assert request["operator_review_lane"] == artifact["operator_review_lane"]
    assert request["operator_review_readiness"] == (
        artifact["operator_review_readiness"]
    )
    assert request["human_review_required"] is artifact["human_review_required"]
    assert request["recommended_next_step"] == (
        artifact["recommended_next_step"]
    )
    assert request["reason_codes"] == artifact["reason_codes"]
    assert request["validation_status"] == (
        artifact["validation_summary"]["validation_status"]
    )
    assert request["allowed_decision_values"] == [
        "continue_read_only",
        "needs_revision",
        "cancel",
    ]
    assert request["read_only"] is True
    assert request["diagnostic_only"] is True
    assert request["persistent"] is False
    assert request["resumable"] is False
    assert request["application_authorization"] is False
    assert request["resume_authorization"] is False


def test_interrupt_request_identity_changes_across_bound_context_and_evidence():
    base_state = _operator_review_pause_state()
    base = harness._build_operator_review_interrupt_request(base_state)
    variants = [
        _operator_review_pause_state(job_id="job-interrupt-request-other"),
        _operator_review_pause_state(job_index=2),
        _operator_review_pause_state(selected_resume_id="resume-other"),
        _operator_review_pause_state(owner_user_id="owner-other"),
        _operator_review_pause_state(pipeline_run_id="run-other"),
        _operator_review_pause_state(context_id="ctx-other"),
    ]
    checkpoint_variant = deepcopy(base_state)
    checkpoint_variant["warnings"].append("diagnostic-state-changed")
    variants.append(checkpoint_variant)
    artifact_variant = deepcopy(base_state)
    artifact_variant["artifacts"]["operator_review_tailoring_evidence"][
        "recommended_next_step"
    ] = "collect_more_evidence"
    variants.append(artifact_variant)

    variant_requests = [
        harness._build_operator_review_interrupt_request(state)
        for state in variants
    ]
    assert all(
        request["interrupt_request_id"] != base["interrupt_request_id"]
        for request in variant_requests
    )
    assert len(
        {request["interrupt_request_id"] for request in variant_requests}
    ) == len(variant_requests)
    for state in variants:
        with pytest.raises(ValueError, match="interrupt_request_mismatch"):
            harness._validate_operator_review_interrupt_request(base, state)


def test_interrupt_request_missing_or_malformed_operator_review_fails_closed():
    state = _operator_review_pause_state()
    missing = deepcopy(state)
    del missing["artifacts"]["operator_review_tailoring_evidence"]
    malformed = deepcopy(state)
    malformed["artifacts"]["operator_review_tailoring_evidence"] = []
    wrong_type = deepcopy(state)
    wrong_type["artifacts"]["operator_review_tailoring_evidence"][
        "artifact_type"
    ] = "wrong"
    missing_lane = deepcopy(state)
    del missing_lane["artifacts"]["operator_review_tailoring_evidence"][
        "operator_review_lane"
    ]
    unsupported_value = deepcopy(state)
    unsupported_value["artifacts"]["operator_review_tailoring_evidence"][
        "confidence"
    ] = float("nan")
    wrong_job = deepcopy(state)
    wrong_job["artifacts"]["operator_review_tailoring_evidence"][
        "job_id"
    ] = "wrong-job"
    wrong_resume = deepcopy(state)
    wrong_resume["artifacts"]["operator_review_tailoring_evidence"][
        "selected_resume_id"
    ] = "wrong-resume"

    with pytest.raises(ValueError, match="operator_review_artifact_missing"):
        harness._build_operator_review_interrupt_request(missing)
    for invalid in (malformed, wrong_type, missing_lane):
        with pytest.raises(ValueError, match="operator_review_artifact_malformed"):
            harness._build_operator_review_interrupt_request(invalid)
    with pytest.raises(ValueError, match="artifact_job_identity_mismatch"):
        harness._build_operator_review_interrupt_request(wrong_job)
    with pytest.raises(ValueError, match="artifact_resume_identity_mismatch"):
        harness._build_operator_review_interrupt_request(wrong_resume)
    with pytest.raises(
        ValueError,
        match="checkpoint_value_not_json_compatible",
    ):
        harness._build_operator_review_interrupt_request(unsupported_value)


def test_interrupt_request_requires_complete_order_and_exact_pause_boundary():
    state = _operator_review_pause_state()
    incomplete = deepcopy(state)
    incomplete["ordered_node_keys"].pop()
    incorrect = deepcopy(state)
    incorrect["ordered_node_keys"][-2:] = [
        "operator_review",
        "tailoring_decision",
    ]
    finalized = harness._finalize_node(state)

    for invalid in (incomplete, incorrect):
        with pytest.raises(ValueError, match="completed_node_keys"):
            harness._build_operator_review_interrupt_request(invalid)
    with pytest.raises(ValueError, match="node_key_invalid"):
        harness._build_operator_review_interrupt_request(
            state,
            requested_node_key="tailoring_decision",
        )
    with pytest.raises(ValueError, match="safe_next_node_key_invalid"):
        harness._build_operator_review_interrupt_request(
            state,
            safe_next_node_key="application_action",
        )
    with pytest.raises(ValueError, match="state_already_finalized"):
        harness._build_operator_review_interrupt_request(finalized)


def test_interrupt_request_rejects_unsupported_or_mismatched_checkpoint_identity():
    state = _operator_review_pause_state()
    identity = harness._build_checkpoint_identity(state).to_payload()
    unsupported_checkpoint = deepcopy(identity)
    unsupported_checkpoint["checkpoint_schema_version"] = "unsupported"
    unsupported_state = deepcopy(identity)
    unsupported_state["graph_state_schema_version"] = "unsupported"
    stale_identity = deepcopy(identity)
    stale_identity["checkpoint_id"] = "stale-checkpoint"

    with pytest.raises(
        ValueError,
        match="checkpoint_schema_version_unsupported",
    ):
        harness._build_operator_review_interrupt_request(
            state,
            checkpoint_identity=unsupported_checkpoint,
        )
    with pytest.raises(
        ValueError,
        match="graph_state_schema_version_unsupported",
    ):
        harness._build_operator_review_interrupt_request(
            state,
            checkpoint_identity=unsupported_state,
        )
    with pytest.raises(ValueError, match="checkpoint_identity_mismatch"):
        harness._build_operator_review_interrupt_request(
            state,
            checkpoint_identity=stale_identity,
        )


def test_interrupt_request_validator_rejects_schema_identity_artifact_and_safety_changes():
    state = _operator_review_pause_state()
    request = harness._build_operator_review_interrupt_request(state)
    mutations = {
        "interrupt_request_schema_version": "unsupported",
        "graph_engine": "wrong-engine",
        "checkpoint_schema_version": "unsupported",
        "graph_state_schema_version": "unsupported",
        "graph_invocation_id": "wrong-invocation",
        "checkpoint_id": "stale-checkpoint",
        "owner_user_id": "wrong-owner",
        "pipeline_run_id": "wrong-run",
        "context_id": "wrong-context",
        "job_id": "wrong-job",
        "selected_resume_id": "wrong-resume",
        "node_key": "tailoring_decision",
        "safe_next_node_key": "application_action",
        "operator_review_artifact_digest": "altered",
        "human_review_required": 1,
        "persistent": True,
        "resumable": True,
        "application_authorization": True,
        "resume_authorization": True,
    }
    for field, value in mutations.items():
        altered = deepcopy(request)
        altered[field] = value
        with pytest.raises(ValueError):
            harness._validate_operator_review_interrupt_request(altered, state)

    malformed_decisions = deepcopy(request)
    malformed_decisions["allowed_decision_values"] = [
        "continue_read_only",
        "apply",
    ]
    with pytest.raises(ValueError, match="allowed_decision_values_invalid"):
        harness._validate_operator_review_interrupt_request(
            malformed_decisions,
            state,
        )


def test_interrupt_request_requires_all_bound_execution_identity():
    state = _operator_review_pause_state()
    missing_identity_states = []
    for field in ("owner_user_id", "pipeline_run_id", "context_id"):
        missing = deepcopy(state)
        missing[field] = ""
        missing_identity_states.append(missing)
    missing_job = deepcopy(state)
    missing_job["job_identity"]["job_id"] = ""
    missing_identity_states.append(missing_job)
    missing_resume = deepcopy(state)
    missing_resume["selected_resume_id"] = ""
    missing_identity_states.append(missing_resume)

    for missing in missing_identity_states:
        with pytest.raises(ValueError, match="missing_required_field"):
            harness._build_operator_review_interrupt_request(missing)


def test_interrupt_request_builder_and_validator_are_pure_and_return_fresh_data():
    state = _operator_review_pause_state()
    state_before = deepcopy(state)
    identity = harness._build_checkpoint_identity(state).to_payload()
    identity_before = deepcopy(identity)

    request = harness._build_operator_review_interrupt_request(
        state,
        checkpoint_identity=identity,
    )
    request_before = deepcopy(request)
    validated = harness._validate_operator_review_interrupt_request(
        request,
        state,
    )

    assert state == state_before
    assert identity == identity_before
    assert request == request_before
    assert validated == request
    assert validated is not request
    assert validated["completed_node_keys"] is not state["ordered_node_keys"]
    assert validated["reason_codes"] is not state["artifacts"][
        "operator_review_tailoring_evidence"
    ]["reason_codes"]

    validated["completed_node_keys"].append("mutated")
    validated["reason_codes"].append("mutated")
    validated["allowed_decision_values"].append("apply")
    request["completed_node_keys"].append("request-mutated")
    request["reason_codes"].append("request-mutated")
    assert state == state_before
    assert identity == identity_before


def test_initial_partial_and_final_states_are_not_interrupt_request_eligible():
    initial = _checkpoint_initial_state()
    partial = harness._jd_intelligence_node(initial)
    pause_ready = _operator_review_pause_state()
    finalized = harness._finalize_node(pause_ready)

    for state in (initial, partial, finalized):
        with pytest.raises(ValueError):
            harness._build_operator_review_interrupt_request(state)


def test_normal_execution_exposes_no_interrupt_request_contract_fields():
    payload = harness.execute_langgraph_evidence_chain(
        [_job("job-no-interrupt-output")],
        resume_context=_resume_context(),
        pipeline_run_id="run-no-interrupt-output",
        owner_user_id="owner-no-interrupt-output",
        context_id="ctx-no-interrupt-output",
        enabled=True,
        strict=True,
    )

    assert "interrupt_request" not in payload
    assert "interrupt_request_id" not in payload
    result = payload["per_job_results"][0]
    assert "interrupt_request" not in result
    assert "interrupt_request_id" not in result
    assert "allowed_decision_values" not in result


def test_interrupt_request_contract_adds_no_interrupt_persistence_resume_or_action_calls():
    path = ROOT / "src/agents/evidence_chain_langgraph_harness.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    forbidden_import_fragments = {
        "langgraph.checkpoint",
        "langgraph.types",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "src.storage",
        "src.app",
    }
    forbidden_calls = {
        "interrupt",
        "Command",
        "add_conditional_edges",
        "open",
        "write_text",
        "__import__",
        "run_chat_completion",
        "execute_application",
        "submit_application",
        "mark_applied",
        "insert_operator_decision_row_to_postgres",
        "insert_application_action_row_to_postgres",
    }
    imports = set()
    called_names = set()
    called_attributes = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            imports.add(node.module or "")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                called_names.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                called_attributes.add(node.func.attr)
    assert not any(
        fragment in imported
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert forbidden_calls.isdisjoint(called_names | called_attributes)
    assert not any(isinstance(node, ast.While) for node in ast.walk(tree))
