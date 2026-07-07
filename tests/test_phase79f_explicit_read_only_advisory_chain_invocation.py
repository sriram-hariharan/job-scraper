from src.agents import orchestrator_adapter_harness, trace, workflow_registry, workflow_runner


UNSAFE_FLAGS = [
    "allow_agent_execution",
    "did_execute",
    "did_execute_chain",
    "did_mutate_production",
    "did_write_db",
    "mutation_allowed",
    "auto_apply_allowed",
    "ats_submission_allowed",
    "application_submission_allowed",
    "apply_click_allowed",
    "queue_mutation_allowed",
    "scoring_mutation_allowed",
    "ranking_mutation_allowed",
    "filtering_mutation_allowed",
    "tailoring_generation_allowed",
    "tailoring_mutation_allowed",
    "source_resume_mutation_allowed",
    "llm_provider_call_allowed",
    "live_provider_allowed",
    "scheduler_mutation_allowed",
    "workflow_runner_live_execution_allowed",
]


def test_explicit_invocation_returns_trace_ready_advisory_chain_result():
    result = orchestrator_adapter_harness.invoke_read_only_advisory_chain(
        pipeline_run_id="phase79f_run",
        owner_user_id="phase79f_owner",
        created_at_utc="2026-07-07T00:00:00+00:00",
    )
    trace_ready = result["trace_ready_advisory_result"]

    assert result["adapter_version"] == "explicit_read_only_advisory_chain_invocation_adapter_v1"
    assert result["invocation_mode"] == "explicit_read_only_advisory_chain_invocation"
    assert result["explicitly_invoked"] is True
    assert result["default_off"] is True
    assert result["read_only"] is True
    assert result["dry_run"] is True
    assert result["validation"]["validation_status"] == "passed"
    assert trace_ready["trace_ready"] is True
    assert trace_ready["trace_store_write_enabled"] is False
    assert trace_ready["ordered_agent_keys"] == workflow_registry.ORDERED_AGENT_KEYS
    assert [step["step_name"] for step in trace_ready["step_summaries"]] == workflow_registry.ORDERED_AGENT_KEYS
    assert result["summary"]["agent_count"] == 6
    assert result["summary"]["step_count"] == 6
    assert result["summary"]["did_invoke_adapter"] is True
    assert result["summary"]["did_execute_agent_count"] == 0


def test_default_harness_behavior_remains_default_off_until_helper_is_called():
    default_harness = orchestrator_adapter_harness.build_default_off_advisory_agent_chain_harness()
    invoked = orchestrator_adapter_harness.invoke_read_only_advisory_chain()

    assert default_harness["enabled"] is False
    assert default_harness["did_execute"] is False
    assert default_harness["did_execute_chain"] is False
    assert "invocation_mode" not in default_harness
    assert invoked["explicitly_invoked"] is True
    assert invoked["harness_result"]["enabled"] is True
    assert invoked["harness_result"]["did_execute"] is False
    assert invoked["harness_result"]["did_execute_chain"] is False


def test_explicit_invocation_does_not_write_trace_store_by_default(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("trace store execution helper must not be called")

    monkeypatch.setattr(trace, "execute_agent_trace_recording", fail_if_called)

    result = orchestrator_adapter_harness.invoke_read_only_advisory_chain()

    assert result["trace_persistence_enabled"] is False
    assert result["trace_store_write_enabled"] is False
    assert result["did_call_trace_execution_helper"] is False
    assert result["trace_ready_advisory_result"]["trace_persistence_enabled"] is False
    assert result["trace_ready_advisory_result"]["trace_store_write_enabled"] is False


def test_explicit_invocation_does_not_call_workflow_runner(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("workflow runner must not be called by invocation adapter")

    monkeypatch.setattr(workflow_runner, "run_agentic_workflow_dry_run", fail_if_called)

    result = orchestrator_adapter_harness.invoke_read_only_advisory_chain()

    assert result["did_call_workflow_runner"] is False
    assert result["did_call_live_workflow_runner"] is False
    assert result["workflow_runner_live_execution_allowed"] is False


def test_explicit_invocation_safety_flags_remain_false():
    result = orchestrator_adapter_harness.invoke_read_only_advisory_chain()

    for flag in UNSAFE_FLAGS:
        assert result[flag] is False
        assert result["harness_result"][flag] is False
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
    assert result["summary"]["mutation_allowed_count"] == 0
    assert result["summary"]["production_mutating_agent_count"] == 0


def test_invocation_validation_catches_unsafe_apply_or_store_flag():
    result = orchestrator_adapter_harness.invoke_read_only_advisory_chain()
    result["auto_apply_allowed"] = True
    result["trace_store_write_enabled"] = True

    validation = orchestrator_adapter_harness.validate_read_only_advisory_chain_invocation(result)

    assert validation["validation_status"] == "failed"
    assert "auto_apply_allowed_not_false" in validation["reason_codes"]
    assert "trace_store_write_enabled_not_false" in validation["reason_codes"]


def test_existing_workflow_runner_remains_dry_run_only_after_invocation():
    invocation = orchestrator_adapter_harness.invoke_read_only_advisory_chain()
    dry_run = workflow_runner.run_agentic_workflow_dry_run()

    assert invocation["validation"]["validation_status"] == "passed"
    assert dry_run["execution_mode"] == "dry_run"
    assert dry_run["executed_step_count"] == 0
    assert dry_run["summary"]["did_execute_any_step"] is False
    assert all(step["did_execute"] is False for step in dry_run["ordered_step_results"])
