from copy import deepcopy

from src.agents import orchestrator_adapter_harness, workflow_runner


TRACE_ENABLED_ENV = {
    "APPLYLENS_AGENT_TRACE_ENABLED": "1",
    "APPLYLENS_AGENT_TRACE_STRICT": "",
}

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


def _invocation():
    return orchestrator_adapter_harness.invoke_read_only_advisory_chain(
        pipeline_run_id="phase80b_run",
        owner_user_id="phase80b_owner",
        created_at_utc="2026-07-07T00:00:00+00:00",
    )


def test_trace_persistence_disabled_by_default_returns_trace_disabled():
    result = orchestrator_adapter_harness.persist_read_only_advisory_chain_trace(
        advisory_result=_invocation(),
        execute_callback=lambda operation: operation,
    )

    assert result["attempted"] is False
    assert result["recorded"] is False
    assert result["reason"] == "trace_disabled"
    assert result["trace_persistence_enabled"] is False
    assert result["trace_store_write_enabled"] is False
    assert result["did_call_trace_execution_helper"] is False


def test_missing_owner_pipeline_or_context_blocks_persistence():
    bundle = deepcopy(_invocation()["trace_ready_advisory_result"])
    bundle["owner_user_id"] = ""
    bundle["pipeline_run_id"] = ""
    bundle["run_snapshot"]["owner_user_id"] = ""
    bundle["run_snapshot"]["pipeline_run_id"] = ""
    bundle["run_snapshot"]["context_id"] = ""
    for step in bundle["step_summaries"]:
        step["owner_user_id"] = ""
        step["pipeline_run_id"] = ""
        step["context_id"] = ""

    result = orchestrator_adapter_harness.persist_read_only_advisory_chain_trace(
        trace_ready_bundle=bundle,
        env=TRACE_ENABLED_ENV,
        execute_callback=lambda operation: operation,
    )

    assert result["attempted"] is False
    assert result["recorded"] is False
    assert result["reason"] == "missing_trace_context"
    assert result["owner_user_id"] == ""
    assert result["pipeline_run_id"] == ""
    assert result["context_id"] == ""


def test_explicit_enabled_invocation_with_injected_executor_records_run_and_ordered_steps():
    operations = []

    result = orchestrator_adapter_harness.persist_read_only_advisory_chain_trace(
        advisory_result=_invocation(),
        env=TRACE_ENABLED_ENV,
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
    assert result["did_prepare_trace_recording_payload"] is True
    assert result["did_call_trace_execution_helper"] is True
    assert [operation["table"] for operation in operations] == ["agent_runs"] + ["agent_steps"] * 6

    snapshots = [record["snapshot"] for record in result["recording_payload"]["records"]]
    assert snapshots[0]["agent_run_id"] == result["recording_payload"]["records"][1]["snapshot"]["agent_run_id"]
    assert [step["agent_name"] for step in snapshots[1:]] == [
        "Source Health Agent",
        "Resume Match Agent",
        "Critic Agent",
        "Job Prioritization Agent",
        "Tailoring Decision Agent",
        "Operator Review Agent",
    ]


def test_non_strict_executor_failure_returns_warning_without_raise():
    def fail(_operation):
        raise RuntimeError("trace executor unavailable")

    result = orchestrator_adapter_harness.persist_read_only_advisory_chain_trace(
        advisory_result=_invocation(),
        env=TRACE_ENABLED_ENV,
        execute_callback=fail,
    )

    assert result["attempted"] is True
    assert result["recorded"] is False
    assert result["reason"] == "trace_persistence_failed"
    assert "trace executor unavailable" in result["warning"]
    assert result["trace_store_write_enabled"] is False


def test_strict_executor_failure_reraises():
    def fail(_operation):
        raise RuntimeError("strict trace executor unavailable")

    try:
        orchestrator_adapter_harness.persist_read_only_advisory_chain_trace(
            advisory_result=_invocation(),
            env={
                "APPLYLENS_AGENT_TRACE_ENABLED": "1",
                "APPLYLENS_AGENT_TRACE_STRICT": "1",
            },
            execute_callback=fail,
        )
    except RuntimeError as exc:
        assert "strict trace executor unavailable" in str(exc)
    else:
        raise AssertionError("Expected strict trace persistence failure to be raised.")


def test_all_application_and_mutation_safety_flags_remain_false():
    result = orchestrator_adapter_harness.persist_read_only_advisory_chain_trace(
        advisory_result=_invocation(),
        env=TRACE_ENABLED_ENV,
        execute_callback=lambda operation: operation,
    )

    for flag in UNSAFE_FLAGS:
        assert result[flag] is False
    for flag in [
        "did_call_llm",
        "did_call_live_provider",
        "did_change_pipeline",
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


def test_workflow_runner_remains_dry_run_only_after_trace_persistence_helper():
    persistence = orchestrator_adapter_harness.persist_read_only_advisory_chain_trace(
        advisory_result=_invocation(),
        env=TRACE_ENABLED_ENV,
        execute_callback=lambda operation: operation,
    )
    dry_run = workflow_runner.run_agentic_workflow_dry_run()

    assert persistence["recorded"] is True
    assert dry_run["execution_mode"] == "dry_run"
    assert dry_run["executed_step_count"] == 0
    assert dry_run["summary"]["did_execute_any_step"] is False
    assert all(step["did_execute"] is False for step in dry_run["ordered_step_results"])
