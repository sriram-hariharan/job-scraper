from copy import deepcopy
import inspect

from src.agents import orchestrator_adapter_harness, workflow_registry, workflow_runner


UNSAFE_FLAGS = [
    "auto_apply_allowed",
    "ats_submission_allowed",
    "apply_click_allowed",
    "queue_mutation_allowed",
    "ranking_mutation_allowed",
    "scoring_mutation_allowed",
    "filtering_mutation_allowed",
    "tailoring_mutation_allowed",
    "source_resume_mutation_allowed",
    "scheduler_mutation_allowed",
    "live_provider_allowed",
    "workflow_runner_live_execution_allowed",
]


def test_pipeline_boundary_helper_returns_existing_advisory_result_with_boundary_metadata():
    result = orchestrator_adapter_harness.invoke_read_only_advisory_chain_from_pipeline_boundary(
        pipeline_run_id="phase81b_run",
        owner_user_id="phase81b_owner",
        context_id="phase81b_context",
        input_summary={"scored_jobs": 3, "boundary": "post_application_priority"},
        env={"APPLYLENS_AGENT_TRACE_ENABLED": "1"},
        created_at_utc="2026-07-07T00:00:00+00:00",
    )

    assert result["adapter_version"] == "controlled_pipeline_boundary_advisory_chain_invocation_v1"
    assert result["invocation_mode"] == "controlled_pipeline_boundary_read_only_advisory_chain_invocation"
    assert result["explicitly_invoked"] is True
    assert result["default_off"] is True
    assert result["read_only"] is True
    assert result["diagnostic_only"] is True
    assert result["pipeline_run_id"] == "phase81b_run"
    assert result["owner_user_id"] == "phase81b_owner"
    assert result["context_id"] == "phase81b_context"
    assert result["advisory_result"]["invocation_mode"] == "explicit_read_only_advisory_chain_invocation"
    assert result["trace_ready_advisory_result"]["trace_ready"] is True
    assert result["ordered_agent_keys"] == workflow_registry.ORDERED_AGENT_KEYS
    assert result["validation"]["validation_status"] == "passed"
    assert result["pipeline_boundary"]["env_snapshot"]["APPLYLENS_AGENT_TRACE_ENABLED"] is True


def test_pipeline_boundary_helper_does_not_mutate_input_summary():
    input_summary = {
        "scored_jobs": 2,
        "sample": [{"job_id": "job-1", "score": 91}],
    }
    original = deepcopy(input_summary)

    result = orchestrator_adapter_harness.invoke_read_only_advisory_chain_from_pipeline_boundary(
        pipeline_run_id="phase81b_run",
        owner_user_id="phase81b_owner",
        context_id="phase81b_context",
        input_summary=input_summary,
    )
    result["pipeline_boundary"]["input_summary"]["sample"][0]["score"] = 0

    assert input_summary == original


def test_pipeline_boundary_helper_is_not_collector_api_ui_or_scheduler_wired():
    result = orchestrator_adapter_harness.invoke_read_only_advisory_chain_from_pipeline_boundary()

    for flag in [
        "collector_wired",
        "api_changed",
        "ui_changed",
        "scheduler_changed",
        "production_output_changed",
        "did_change_pipeline",
    ]:
        assert result[flag] is False
    assert result["pipeline_boundary"]["collector_wired"] is False
    assert result["pipeline_boundary"]["production_output_changed"] is False
    assert result["summary"]["collector_wired"] is False
    assert result["summary"]["production_output_changed"] is False


def test_pipeline_boundary_helper_does_not_persist_trace_or_write_database(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("pipeline-boundary helper must not persist trace")

    monkeypatch.setattr(orchestrator_adapter_harness, "persist_read_only_advisory_chain_trace", fail_if_called)
    monkeypatch.setattr(orchestrator_adapter_harness.trace, "execute_agent_trace_recording", fail_if_called)

    result = orchestrator_adapter_harness.invoke_read_only_advisory_chain_from_pipeline_boundary(
        env={"APPLYLENS_AGENT_TRACE_ENABLED": "1"},
    )

    assert result["trace_persisted"] is False
    assert result["would_persist_trace"] is False
    assert result["trace_persistence_enabled"] is False
    assert result["trace_store_write_enabled"] is False
    assert result["did_call_trace_execution_helper"] is False


def test_pipeline_boundary_helper_safety_flags_remain_false():
    result = orchestrator_adapter_harness.invoke_read_only_advisory_chain_from_pipeline_boundary()

    for flag in UNSAFE_FLAGS:
        assert result[flag] is False
        assert result["advisory_result"][flag] is False
    for flag in [
        "did_call_llm",
        "did_call_live_provider",
        "did_change_queue",
        "did_change_scoring",
        "did_change_ranking",
        "did_change_filtering",
        "did_change_tailoring",
        "did_mutate_source_resume",
        "did_execute_scheduler",
        "did_click_apply",
        "did_execute_application",
        "did_submit_application",
        "did_send_recruiter_message",
        "did_mark_applied",
    ]:
        assert result[flag] is False


def test_pipeline_boundary_validation_catches_unsafe_pipeline_or_apply_flags():
    result = orchestrator_adapter_harness.invoke_read_only_advisory_chain_from_pipeline_boundary()
    result["production_output_changed"] = True
    result["auto_apply_allowed"] = True

    validation = orchestrator_adapter_harness.validate_pipeline_boundary_advisory_chain_invocation(result)

    assert validation["validation_status"] == "failed"
    assert "production_output_changed_not_false" in validation["reason_codes"]
    assert "auto_apply_allowed_not_false" in validation["reason_codes"]


def test_pipeline_boundary_helper_does_not_call_workflow_runner(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("pipeline-boundary helper must not call workflow runner")

    monkeypatch.setattr(workflow_runner, "run_agentic_workflow_dry_run", fail_if_called)

    result = orchestrator_adapter_harness.invoke_read_only_advisory_chain_from_pipeline_boundary()

    assert result["did_call_workflow_runner"] is False
    assert result["did_call_live_workflow_runner"] is False
    assert result["workflow_runner_live_execution_allowed"] is False


def test_existing_workflow_runner_remains_dry_run_only_after_pipeline_boundary_helper():
    boundary = orchestrator_adapter_harness.invoke_read_only_advisory_chain_from_pipeline_boundary()
    dry_run = workflow_runner.run_agentic_workflow_dry_run()

    assert boundary["validation"]["validation_status"] == "passed"
    assert dry_run["execution_mode"] == "dry_run"
    assert dry_run["executed_step_count"] == 0
    assert dry_run["summary"]["did_execute_any_step"] is False
    assert all(step["did_execute"] is False for step in dry_run["ordered_step_results"])


def test_pipeline_boundary_helper_source_stays_helper_only():
    source = inspect.getsource(
        orchestrator_adapter_harness.invoke_read_only_advisory_chain_from_pipeline_boundary
    )

    for forbidden in [
        "import collector",
        "from src.pipeline",
        "collect_all_jobs_async",
        "persist_read_only_advisory_chain_trace(",
        "execute(",
        "agent_trace_payload(",
        "workflow_runner.",
        "run_agentic_workflow",
        "run_chat_completion",
        "submit_application(",
        "click_apply(",
        "mark_applied(",
        "LangGraph",
    ]:
        assert forbidden not in source
