from __future__ import annotations

import ast
import builtins
from copy import deepcopy
from pathlib import Path

import pytest

from src.pipeline import collector


ROOT = Path(__file__).resolve().parents[1]
GATE = "APPLYLENS_AGENTIC_PIPELINE_JD_INTELLIGENCE_EXISTING_OUTPUT_DIAGNOSTICS_ENABLED"
SAMPLE_LIMIT = (
    "APPLYLENS_AGENTIC_PIPELINE_JD_INTELLIGENCE_EXISTING_OUTPUT_DIAGNOSTICS_SAMPLE_LIMIT"
)


def _already_intelligent_job(index: int = 1) -> dict:
    return {
        "job_id": f"job-87b-{index}",
        "title": f"Analytics Engineer {index}",
        "company": "Example Data",
        "intelligence": {
            "skills": {
                "required": ["python", "sql"],
                "preferred": ["airflow"],
                "all": ["python", "sql", "airflow"],
            },
            "visa_sponsorship": "unknown",
        },
    }


def _collector_source() -> str:
    return (ROOT / "src/pipeline/collector.py").read_text(encoding="utf-8")


def _collector_helper_source() -> str:
    source = _collector_source()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.FunctionDef)
            and node.name
            == "_maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence"
        ):
            return ast.get_source_segment(source, node) or ""
    raise AssertionError("collector diagnostics helper not found")


def _call_names(source: str) -> set[str]:
    names: set[str] = set()
    tree = ast.parse(source)

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


def test_gate_off_returns_none_does_not_import_or_call_builder(monkeypatch):
    jobs = [_already_intelligent_job()]
    original = deepcopy(jobs)
    imported_modules: list[str] = []
    real_import = builtins.__import__

    def tracking_import(name, *args, **kwargs):
        imported_modules.append(name)
        if name == "src.agents.jd_intelligence":
            raise AssertionError("JD trace payload helper should not be imported")
        return real_import(name, *args, **kwargs)

    def builder(*args, **kwargs):
        raise AssertionError("payload builder should not be called when gate is off")

    monkeypatch.setattr(builtins, "__import__", tracking_import)

    payload = collector._maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence(
        jobs,
        env={},
        payload_builder=builder,
    )

    assert payload is None
    assert jobs == original
    assert "src.agents.jd_intelligence" not in imported_modules


def test_gate_on_calls_phase86_builder_with_already_intelligent_jobs_and_sample_limit():
    jobs = [_already_intelligent_job(1), _already_intelligent_job(2)]
    original = deepcopy(jobs)
    calls: list[dict] = []

    def builder(received_jobs, *, sample_limit):
        calls.append({"jobs": received_jobs, "sample_limit": sample_limit})
        return {
            "stage_name": "jd_intelligence_existing_output",
            "source_stage": "intelligence",
            "job_count_seen": len(received_jobs),
            "job_count_sampled": 1,
            "validation_summary": {"invalid_wrapper_outputs": 0},
            "trace_persistence_requested": False,
            "trace_persistence_performed": False,
            "production_output_changed": False,
        }

    payload = collector._maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence(
        jobs,
        env={GATE: "1", SAMPLE_LIMIT: "3"},
        payload_builder=builder,
    )

    assert calls == [{"jobs": jobs, "sample_limit": "3"}]
    assert payload["attempted"] is True
    assert payload["enabled"] is True
    assert payload["job_count_seen"] == 2
    assert payload["trace_persistence_requested"] is False
    assert payload["trace_persistence_performed"] is False
    assert payload["production_output_changed"] is False
    assert jobs == original


def test_gate_on_real_payload_is_not_persistent_and_does_not_mutate_jobs():
    jobs = [_already_intelligent_job(1), _already_intelligent_job(2)]
    original = deepcopy(jobs)

    payload = collector._maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence(
        jobs,
        env={GATE: "true", SAMPLE_LIMIT: "1"},
    )

    assert payload["stage_name"] == "jd_intelligence_existing_output"
    assert payload["job_count_seen"] == 2
    assert payload["job_count_sampled"] == 1
    assert payload["omitted_job_count"] == 1
    assert payload["sample_limit"] == 1
    assert payload["trace_persistence_requested"] is False
    assert payload["trace_persistence_performed"] is False
    assert payload["production_output_changed"] is False
    assert jobs == original


def test_builder_exception_returns_non_blocking_diagnostic_metadata():
    jobs = [_already_intelligent_job()]
    original = deepcopy(jobs)

    def builder(*args, **kwargs):
        raise RuntimeError("diagnostic payload failed")

    payload = collector._maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence(
        jobs,
        env={GATE: "1"},
        payload_builder=builder,
    )

    assert payload["attempted"] is True
    assert payload["enabled"] is True
    assert payload["reason"] == "jd_intelligence_existing_output_diagnostics_failed"
    assert "diagnostic payload failed" in payload["warning"]
    assert payload["trace_persistence_requested"] is False
    assert payload["trace_persistence_performed"] is False
    assert payload["production_output_changed"] is False
    for key in (
        "auto_apply_performed",
        "auto_submit_performed",
        "ats_submission_performed",
        "apply_click_performed",
        "recruiter_message_sent",
        "mark_applied_performed",
        "provider_call_performed",
        "duplicate_llm_call_performed",
        "database_write_performed",
        "scoring_changed",
        "ranking_changed",
        "filtering_changed",
        "queue_changed",
        "scheduler_changed",
        "tailoring_changed",
        "source_resume_changed",
        "workflow_runner_live_execution_performed",
    ):
        assert payload[key] is False
    assert jobs == original


def test_collector_source_places_diagnostics_after_intelligence_before_later_stages():
    source = _collector_source()
    intelligence_complete = source.index(
        'complete_stage("intelligence", counts={"intelligent_jobs": len(intelligent_jobs)})'
    )
    diagnostics_call = source.index(
        "_maybe_build_jd_intelligence_existing_output_diagnostics_after_intelligence(\n"
        "        intelligent_jobs\n"
        "    )"
    )
    skill_store = source.index("store_job_skills(skill_run_id, intelligent_jobs)")
    evaluation_filter = source.index("filter_jobs_for_ai_evaluation(intelligent_jobs)")
    evaluation = source.index("evaluate_jobs(evaluable_jobs)")
    scoring = source.index("score_jobs(ai_jobs)")

    assert intelligence_complete < diagnostics_call < skill_store
    assert diagnostics_call < evaluation_filter < evaluation < scoring


def test_collector_diagnostics_helper_has_no_duplicate_provider_persistence_or_scoring_calls():
    helper_source = _collector_helper_source()
    forbidden_tokens = [
        "build_job_intelligence(",
        "enrich_skills_with_llm(",
        "run_chat_completion(",
        "run_chat_completion_with_metadata(",
        "evaluate_jobs(",
        "score_jobs(",
        "record_agent_step_postgres_payload(",
        "create_agent_run_postgres_payload(",
        "agent_trace_payload(",
        "cursor.execute(",
        "commit(",
        "src.app.services",
        "src.app.api",
        "workflow_runner",
    ]
    for token in forbidden_tokens:
        assert token not in helper_source

    calls = _call_names(helper_source)
    assert "build_job_intelligence" not in calls
    assert "enrich_skills_with_llm" not in calls
    assert "run_chat_completion" not in calls
    assert "run_chat_completion_with_metadata" not in calls
    assert "evaluate_jobs" not in calls
    assert "score_jobs" not in calls
    assert "record_agent_step_postgres_payload" not in calls
    assert "create_agent_run_postgres_payload" not in calls
    assert "agent_trace_payload" not in calls


def test_phase87b_expected_gate_names_are_present():
    source = _collector_source()

    assert "APPLYLENS_AGENTIC_PIPELINE_JD_INTELLIGENCE_EXISTING_OUTPUT_DIAGNOSTICS_ENABLED" in source
    assert "APPLYLENS_AGENTIC_PIPELINE_JD_INTELLIGENCE_EXISTING_OUTPUT_DIAGNOSTICS_SAMPLE_LIMIT" in source
    assert "APPLYLENS_AGENTIC_PIPELINE_JD_INTELLIGENCE_EXISTING_OUTPUT_TRACE_PERSISTENCE_ENABLED" not in source
