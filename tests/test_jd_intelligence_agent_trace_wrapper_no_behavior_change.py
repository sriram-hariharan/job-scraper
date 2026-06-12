from copy import deepcopy
import importlib
from pathlib import Path

from src.agents.agent_state import JobApplicationContext
from src.agents import jd_intelligence


def _summary():
    return {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": ["Airflow"],
        "required_tools": ["PostgreSQL"],
        "preferred_tools": ["dbt"],
        "methods": ["experimentation", "causal inference"],
        "workflows": ["batch pipelines", "metric reviews"],
        "business_contexts": ["marketplace growth"],
        "stakeholder_contexts": ["product managers", "data science"],
        "ownership_signals": ["owns data quality"],
        "seniority_indicators": ["technical leadership"],
    }


def _context():
    return JobApplicationContext(
        approval_request_id="approval_jd",
        job_id="job_jd",
        candidate_key="candidate_jd",
        role_family="data_engineering",
        run_mode="dry_run",
        observed_at_utc="2026-06-12T15:00:00Z",
        metadata={"source": "unit_test"},
    )


def _assert_safety_flags_false(payload):
    assert payload["did_call_live_jd_extraction"] is False
    assert payload["did_call_llm_provider"] is False
    assert payload["did_call_prefilter_relevance"] is False
    assert payload["did_call_deduplication"] is False
    assert payload["did_call_final_application_scoring"] is False
    assert payload["did_create_connection"] is False
    assert payload["did_commit_transaction"] is False
    assert payload["did_run_migration"] is False
    assert payload["did_schedule_background_work"] is False
    assert payload["did_execute_scheduler"] is False
    assert payload["did_execute_reporting_job"] is False
    assert payload["did_export_files"] is False
    assert payload["did_execute_application"] is False
    assert payload["did_submit_application"] is False
    assert payload["api_route_added"] is False
    assert payload["ui_action_added"] is False
    assert payload["pipeline_wiring_added"] is False


def test_import_has_no_side_effects():
    module = importlib.reload(jd_intelligence)

    _assert_safety_flags_false(module.safety_flags())


def test_jd_intelligence_wrapper_output_is_deterministic_and_preserves_input():
    summary = _summary()
    original = deepcopy(summary)

    first = jd_intelligence.describe_jd_intelligence_result(summary)
    second = jd_intelligence.describe_jd_intelligence_result(summary)

    assert summary == original
    assert first == second
    assert first["agent_name"] == "jd_intelligence_agent"
    assert first["agent_version"] == "jd-intelligence-wrapper-v1"
    assert first["status"] == "completed"
    assert first["required_skill_count"] == 2
    assert first["preferred_skill_count"] == 1
    assert first["workflow_count"] == 2
    assert first["business_context_count"] == 1
    _assert_safety_flags_false(first)


def test_supplied_signals_are_preserved():
    payload = jd_intelligence.describe_jd_intelligence_result(_summary())

    assert payload["required_skills"] == ["Python", "SQL"]
    assert payload["preferred_skills"] == ["Airflow"]
    assert payload["required_tools"] == ["PostgreSQL"]
    assert payload["preferred_tools"] == ["dbt"]
    assert payload["methods"] == ["experimentation", "causal inference"]
    assert payload["workflows"] == ["batch pipelines", "metric reviews"]
    assert payload["business_contexts"] == ["marketplace growth"]
    assert payload["stakeholder_contexts"] == ["product managers", "data science"]
    assert payload["ownership_signals"] == ["owns data quality"]
    assert payload["seniority_indicators"] == ["technical leadership"]
    assert payload["output_json"]["required_skills"] == payload["required_skills"]


def test_signal_counts_are_deterministic():
    payload = jd_intelligence.describe_jd_intelligence_result(_summary())

    assert payload["signal_counts"] == {
        "required_skills": 2,
        "preferred_skills": 1,
        "required_tools": 1,
        "preferred_tools": 1,
        "methods": 2,
        "workflows": 2,
        "business_contexts": 1,
        "stakeholder_contexts": 2,
        "ownership_signals": 1,
        "seniority_indicators": 1,
    }


def test_invalid_non_list_signal_fields_fail_validation_safely():
    summary = _summary()
    summary["required_skills"] = "Python"
    payload = jd_intelligence.describe_jd_intelligence_result(summary)

    assert payload["status"] == "invalid"
    assert payload["validation_json"]["is_valid"] is False
    assert payload["validation_json"]["errors"] == ["required_skills_not_list"]
    assert payload["required_skills"] == []
    assert payload["did_call_live_jd_extraction"] is False
    assert payload["did_call_llm_provider"] is False
    assert payload["did_execute_application"] is False
    assert payload["did_submit_application"] is False


def test_step_snapshot_uses_caller_supplied_context_ids_and_timestamp():
    summary = _summary()
    original = deepcopy(summary)

    step = jd_intelligence.build_jd_intelligence_step_snapshot(
        context=_context(),
        jd_intelligence_summary=summary,
        observed_at_utc="2026-06-12T15:01:00Z",
        agent_run_id="agent_run_jd",
        step_index=4,
        agent_version="jd-intelligence-wrapper-test",
    )

    assert summary == original
    assert step["agent_name"] == "jd_intelligence_agent"
    assert step["step_name"] == "jd_intelligence_trace_wrapper"
    assert step["step_status"] == "completed"
    assert step["agent_run_id"] == "agent_run_jd"
    assert step["observed_at_utc"] == "2026-06-12T15:01:00Z"
    assert step["output_summary"]["agent_version"] == "jd-intelligence-wrapper-test"
    assert step["output_summary"]["separation"] == {
        "jd_intelligence": "described_only",
        "prefilter_relevance": "not_called",
        "deduplication": "not_called",
        "llm_evaluation_live_extraction": "not_called",
        "final_application_scoring": "not_called",
    }


def test_wrapper_source_does_not_call_live_jd_llm_prefilter_dedup_or_scoring_paths():
    source = Path("src/agents/jd_intelligence.py").read_text()

    forbidden_tokens = [
        "src.intelligence",
        "build_job_intelligence",
        "extract_skills",
        "enrich_skills",
        "skill_llm",
        "hybrid_skill_extractor",
        "job_fit_evaluator",
        "score_first_scan",
        "src.pipeline.job_filter",
        "filter_jobs",
        "src.pipeline.dedupe",
        "dedupe_jobs",
        "relevance_prefilter",
        "src.agents.deduplication",
        "run_llm",
        "model_client",
        "open(",
        "connect(",
        ".commit(",
        "run_migration(",
        "FileResponse",
        "StreamingResponse",
        "write_text",
        "write_bytes",
        "send_file",
        "subprocess",
        "background_tasks.add_task",
        "Thread",
        "Process",
        "scheduler_execution(",
        "reporting_job_execution(",
        "application_execution(",
        "application_submission(",
        "export_writer",
        "metrics_emitter",
        "logging_emitter",
        "audit_writer",
        "datetime.",
        "utcnow",
        "now(",
        "uuid",
        "random",
        "src.app.api",
        "agentic_review.js",
        "workflow_runner",
        "application_execution_queue",
    ]
    for token in forbidden_tokens:
        assert token not in source
