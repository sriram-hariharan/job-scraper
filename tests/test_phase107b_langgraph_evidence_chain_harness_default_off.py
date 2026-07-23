# phase107b legacy guard marker: changes_only requirements_hash_old 96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 src/app/api.py
import ast
from copy import deepcopy
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
