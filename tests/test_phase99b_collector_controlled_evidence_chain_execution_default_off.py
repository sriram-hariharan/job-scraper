from copy import deepcopy
from pathlib import Path
import ast

from src.pipeline import collector


ROOT = Path(__file__).resolve().parents[1]
GATE = "APPLYLENS_AGENTIC_PIPELINE_EVIDENCE_CHAIN_EXECUTION_ENABLED"
SAMPLE_LIMIT_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_EVIDENCE_CHAIN_EXECUTION_SAMPLE_LIMIT"
)
FALSE_SAFETY_FLAGS = [
    "provider_call_performed",
    "live_llm_call_performed",
    "trace_persistence_performed",
    "trace_store_write_performed",
    "database_write_performed",
    "collector_output_changed",
    "production_output_changed",
    "evaluable_jobs_changed",
    "scored_jobs_changed",
    "scoring_changed",
    "ranking_changed",
    "filtering_changed",
    "cache_behavior_changed",
    "retry_behavior_changed",
    "dedupe_behavior_changed",
    "source_health_behavior_changed",
    "ats_health_behavior_changed",
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


def _env(**overrides):
    base = {
        GATE: "",
        SAMPLE_LIMIT_FLAG: "",
        "JOB_APP_PIPELINE_RUN_ID": "phase99b_pipeline",
        "JOB_STACK_OWNER_USER_ID": "phase99b_owner",
        "APPLYLENS_AGENT_CONTEXT_ID": "",
        "APPLYLENS_AGENT_TRACE_ENABLED": "",
        "APPLYLENS_AGENT_TRACE_STRICT": "1",
    }
    base.update(overrides)
    return base


def _jobs():
    return [
        {
            "job_id": "job-99b-1",
            "title": "Machine Learning Engineer",
            "company": "Example AI",
            "intelligence": {
                "skills": {
                    "required": ["Python", "SQL"],
                    "preferred": ["RAG"],
                    "all": ["Python", "SQL", "RAG"],
                }
            },
            "ai_fit_score": 8,
            "priority_score": 12.5,
        },
        {
            "job_id": "job-99b-2",
            "title": "Backend Engineer",
            "company": "Example Cloud",
            "intelligence": {
                "skills": {
                    "required": ["Python"],
                    "preferred": ["Postgres"],
                    "all": ["Python", "Postgres"],
                }
            },
            "ai_fit_score": 7,
            "priority_score": 10.5,
        },
    ]


def _execution_result(**overrides):
    payload = {
        "artifact_type": "controlled_evidence_chain_execution_result",
        "executed": True,
        "attempted": True,
        "reason": "evidence_chain_execution_completed",
        "automatic_internal_decisioning_performed": True,
        "trace_persistence_performed": False,
        "database_write_performed": False,
        "provider_call_performed": False,
        "live_llm_call_performed": False,
    }
    payload.update(overrides)
    return payload


def _assert_safety(payload, *, internal_decisioning):
    assert payload["default_off"] is True
    assert payload["read_only"] is True
    assert payload["diagnostic_only"] is True
    assert payload["sidecar_only"] is True
    assert payload["trace_persistence_requested"] is False
    assert payload["trace_persistence_performed"] is False
    for flag in FALSE_SAFETY_FLAGS:
        assert payload[flag] is False
        assert payload["safety_metadata"][flag] is False
    assert (
        payload["automatic_internal_decisioning_performed"] is internal_decisioning
    )
    assert (
        payload["safety_metadata"]["automatic_internal_decisioning_performed"]
        is internal_decisioning
    )


def _collector_source() -> str:
    return (ROOT / "src/pipeline/collector.py").read_text(encoding="utf-8")


def _wrapper_source() -> str:
    source = _collector_source()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name
            == "_maybe_run_controlled_evidence_chain_execution_after_application_priority"
        ):
            return ast.get_source_segment(source, node) or ""
    raise AssertionError("Phase 99B collector execution wrapper missing")


def _call_names(source: str) -> set[str]:
    tree = ast.parse(source)
    names: set[str] = set()

    def call_name(node: ast.AST) -> str:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Attribute):
            parent = call_name(node.value)
            return f"{parent}.{node.attr}" if parent else node.attr
        return ""

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            names.add(call_name(node.func))
    return names


def test_gate_off_returns_none_without_importing_or_calling_execution_helper():
    jobs = _jobs()
    before = deepcopy(jobs)
    calls = []

    def fail_if_called(**_kwargs):
        calls.append("called")
        raise AssertionError("gate off must not call execution helper")

    result = collector._maybe_run_controlled_evidence_chain_execution_after_application_priority(
        jobs,
        env=_env(**{GATE: ""}),
        execution_helper=fail_if_called,
    )

    assert result is None
    assert calls == []
    assert jobs == before


def test_gate_on_calls_execution_helper_with_bounded_defensive_copy_and_context():
    jobs = _jobs()
    before = deepcopy(jobs)
    captured = {}

    def helper(received_jobs, **kwargs):
        captured["jobs"] = received_jobs
        captured["kwargs"] = kwargs
        received_jobs[0]["title"] = "mutated inside helper"
        return _execution_result()

    result = collector._maybe_run_controlled_evidence_chain_execution_after_application_priority(
        jobs,
        env=_env(**{GATE: "1"}),
        execution_helper=helper,
    )

    assert result["artifact_type"] == (
        "collector_controlled_evidence_chain_execution_result"
    )
    assert result["artifact_version"] == (
        "collector-controlled-evidence-chain-execution-v1"
    )
    assert result["collector_stage"] == "post_score_jobs"
    assert result["gate_name"] == GATE
    assert result["attempted"] is True
    assert result["executed"] is True
    assert result["reason"] == "evidence_chain_execution_completed"
    assert result["execution_result"]["artifact_type"] == (
        "controlled_evidence_chain_execution_result"
    )
    assert result["sample_limit"] == 10
    assert result["jobs_received_count"] == 2
    assert result["jobs_sampled_count"] == 2
    assert captured["jobs"] is not jobs
    assert captured["jobs"][0] is not jobs[0]
    assert captured["kwargs"] == {
        "resume_context": None,
        "pipeline_run_id": "phase99b_pipeline",
        "owner_user_id": "phase99b_owner",
        "context_id": "evidence_chain_execution:phase99b_pipeline",
        "execution_gate_enabled": True,
        "include_trace_payload": True,
        "sample_limit": 10,
    }
    assert result["pipeline_run_id"] == "phase99b_pipeline"
    assert result["owner_user_id"] == "phase99b_owner"
    assert result["context_id"] == "evidence_chain_execution:phase99b_pipeline"
    assert jobs == before
    _assert_safety(result, internal_decisioning=True)


def test_sample_limit_env_bounds_copied_jobs_and_invalid_env_falls_back_to_default():
    jobs = _jobs() + [_jobs()[0] | {"job_id": "job-99b-3"}]
    captured_limits = []

    def helper(received_jobs, **kwargs):
        captured_limits.append((len(received_jobs), kwargs["sample_limit"]))
        return _execution_result()

    limited = collector._maybe_run_controlled_evidence_chain_execution_after_application_priority(
        jobs,
        env=_env(**{GATE: "1", SAMPLE_LIMIT_FLAG: "1"}),
        execution_helper=helper,
    )
    invalid = collector._maybe_run_controlled_evidence_chain_execution_after_application_priority(
        jobs,
        env=_env(**{GATE: "1", SAMPLE_LIMIT_FLAG: "not-a-number"}),
        execution_helper=helper,
    )

    assert limited["sample_limit"] == 1
    assert limited["jobs_sampled_count"] == 1
    assert invalid["sample_limit"] == 10
    assert invalid["jobs_sampled_count"] == 3
    assert captured_limits == [(1, 1), (3, 10)]


def test_explicit_sample_limit_overrides_env_value():
    calls = []

    def helper(received_jobs, **kwargs):
        calls.append((len(received_jobs), kwargs["sample_limit"]))
        return _execution_result()

    result = collector._maybe_run_controlled_evidence_chain_execution_after_application_priority(
        _jobs(),
        env=_env(**{GATE: "1", SAMPLE_LIMIT_FLAG: "1"}),
        execution_helper=helper,
        sample_limit=2,
    )

    assert result["sample_limit"] == 2
    assert calls == [(2, 2)]


def test_helper_failure_is_non_blocking_and_preserves_jobs_even_with_trace_strict():
    jobs = _jobs()
    before = deepcopy(jobs)

    def fail_helper(*_args, **_kwargs):
        raise RuntimeError("phase99b executor unavailable")

    result = collector._maybe_run_controlled_evidence_chain_execution_after_application_priority(
        jobs,
        env=_env(**{GATE: "1", "APPLYLENS_AGENT_TRACE_STRICT": "1"}),
        execution_helper=fail_helper,
    )

    assert result["attempted"] is True
    assert result["executed"] is False
    assert result["reason"] == "evidence_chain_execution_failed"
    assert "phase99b executor unavailable" in result["warning"]
    assert "phase99b executor unavailable" in result["error_message"]
    assert jobs == before
    _assert_safety(result, internal_decisioning=False)


def test_success_payload_does_not_attach_execution_artifacts_to_scored_jobs():
    jobs = _jobs()
    before = deepcopy(jobs)

    def helper(received_jobs, **_kwargs):
        received_jobs[0]["agent_evidence_chain_bundle"] = {"mutated": True}
        return _execution_result()

    result = collector._maybe_run_controlled_evidence_chain_execution_after_application_priority(
        jobs,
        env=_env(**{GATE: "1"}),
        execution_helper=helper,
    )

    assert result["sidecar_only"] is True
    assert "agent_evidence_chain_bundle" not in jobs[0]
    assert "controlled_evidence_chain_execution_result" not in jobs[0]
    assert jobs == before


def test_call_site_is_after_phase97_diagnostics_before_source_health():
    source = _collector_source()
    complete_marker = (
        'complete_stage("application_priority", counts={"scored_jobs": len(scored_jobs)})'
    )
    advisory_marker = (
        "_maybe_invoke_advisory_chain_diagnostics_after_application_priority(scored_jobs)"
    )
    diagnostics_marker = "_maybe_build_evidence_chain_collector_diagnostics(scored_jobs)"
    execution_marker = (
        "_maybe_run_controlled_evidence_chain_execution_after_application_priority(scored_jobs)"
    )
    source_health_marker = "if role_title_audit_rows is not None:"

    assert source.count(execution_marker) == 1
    assert (
        source.index(complete_marker)
        < source.index(advisory_marker, source.index(complete_marker))
        < source.index(diagnostics_marker, source.index(advisory_marker))
        < source.index(execution_marker, source.index(diagnostics_marker))
        < source.index(source_health_marker, source.index(execution_marker))
    )


def test_wrapper_source_calls_only_phase98_executor_and_no_forbidden_paths():
    helper_source = _wrapper_source()
    assert "execute_controlled_evidence_chain" in helper_source
    assert "persist_agent_evidence_chain_trace_payload" not in helper_source

    forbidden_tokens = [
        "build_resume_match_jd_evidence_artifact",
        "build_critic_resume_match_jd_evidence_artifact",
        "build_job_prioritization_critic_evidence_artifact",
        "build_tailoring_decision_priority_evidence_artifact",
        "build_operator_review_tailoring_evidence_artifact",
        "build_agent_evidence_chain_bundle",
        "build_agent_evidence_chain_trace_payload",
        "persist_agent_evidence_chain_trace_payload",
        "record_agent_step_postgres_payload",
        "create_agent_run_postgres_payload",
        "cursor.execute",
        "commit(",
        "workflow_runner",
        "run_chat_completion",
        "run_chat_completion_with_metadata",
        "submit_application",
        "click_apply",
        "mark_applied",
        "send_recruiter",
        "src.app.api",
        "src.app.services",
        "LangGraph",
    ]
    for token in forbidden_tokens:
        assert token not in helper_source

    calls = _call_names(helper_source)
    forbidden_calls = {
        "build_resume_match_jd_evidence_artifact",
        "build_critic_resume_match_jd_evidence_artifact",
        "build_job_prioritization_critic_evidence_artifact",
        "build_tailoring_decision_priority_evidence_artifact",
        "build_operator_review_tailoring_evidence_artifact",
        "build_agent_evidence_chain_bundle",
        "build_agent_evidence_chain_trace_payload",
        "persist_agent_evidence_chain_trace_payload",
        "run_chat_completion",
        "run_chat_completion_with_metadata",
    }
    assert forbidden_calls.isdisjoint(calls)


def test_phase99b_gate_and_contract_are_declared_in_collector_source():
    source = _collector_source()

    assert "APPLYLENS_AGENTIC_PIPELINE_EVIDENCE_CHAIN_EXECUTION_ENABLED" in source
    assert "APPLYLENS_AGENTIC_PIPELINE_EVIDENCE_CHAIN_EXECUTION_SAMPLE_LIMIT" in source
    assert "collector_controlled_evidence_chain_execution_result" in source
    assert "collector-controlled-evidence-chain-execution-v1" in source
