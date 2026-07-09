# phase107b legacy guard marker: changes_only requirements_hash_old 96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 src/app/api.py
import ast
from copy import deepcopy
from pathlib import Path

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
