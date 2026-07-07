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


def test_trace_ready_bundle_exists_and_preserves_registry_order():
    result = orchestrator_adapter_harness.build_default_off_advisory_agent_chain_harness(
        pipeline_run_id="phase79e_run",
        owner_user_id="phase79e_owner",
        created_at_utc="2026-07-07T00:00:00+00:00",
    )
    bundle = result["trace_ready_bundle"]

    assert result["validation"]["validation_status"] == "passed"
    assert bundle["bundle_version"] == "default_off_advisory_chain_trace_bundle_v1"
    assert bundle["bundle_type"] == "default_off_advisory_chain_trace_ready_bundle"
    assert bundle["trace_ready"] is True
    assert bundle["ordered_agent_keys"] == workflow_registry.ORDERED_AGENT_KEYS
    assert [step["step_name"] for step in bundle["step_summaries"]] == workflow_registry.ORDERED_AGENT_KEYS
    assert bundle["trace_summary"]["run_count"] == 1
    assert bundle["trace_summary"]["step_count"] == 6
    assert bundle["trace_summary"]["all_required_fields_present"] is True
    assert bundle["stage_trace_bundle"]["stage_order_validation"]["is_valid"] is True


def test_trace_ready_bundle_step_summaries_are_non_executing_advisory_agents():
    result = orchestrator_adapter_harness.build_default_off_advisory_agent_chain_harness(enabled=True)
    steps = result["trace_ready_bundle"]["step_summaries"]

    assert len(steps) == 6
    for index, step in enumerate(steps, start=1):
        assert step["step_index"] == index
        assert step["agent_run_id"] == result["chain_run_id"]
        assert step["agent_name"]
        assert step["agent_version"]
        assert step["did_execute"] is False
        assert step["mutation_allowed"] is False
        assert step["output_json"]["advisory_only"] is True
        assert step["output_json"]["read_only"] is True
        assert step["output_json"]["did_execute"] is False
        assert step["output_json"]["mutation_allowed"] is False
        for flag, value in step["validation_json"]["safety_flags"].items():
            assert flag in UNSAFE_FLAGS
            assert value is False


def test_trace_ready_bundle_all_mutation_apply_provider_flags_remain_false():
    result = orchestrator_adapter_harness.build_default_off_advisory_agent_chain_harness()
    bundle = result["trace_ready_bundle"]

    for flag in UNSAFE_FLAGS:
        assert result[flag] is False
    safety = bundle["validation_safety_summary"]
    for flag in [
        "trace_persistence_enabled",
        "trace_store_write_enabled",
        "did_prepare_trace_recording_payload",
        "did_call_trace_execution_helper",
        "did_read_database",
        "did_write_database",
        "did_create_agent_run",
        "did_create_agent_step",
        "did_update_agent_run",
        "did_update_agent_step",
        "did_call_llm",
        "did_call_live_provider",
        "did_change_pipeline",
        "did_change_scoring",
        "did_change_ranking",
        "did_change_filtering",
        "did_change_queue",
        "did_change_tailoring",
        "did_mutate_source_resume",
        "did_execute_scheduler",
        "did_click_apply",
        "did_execute_application",
        "did_submit_application",
        "did_send_recruiter_message",
        "did_mark_applied",
    ]:
        assert safety[flag] is False


def test_trace_ready_bundle_uses_deterministic_chain_run_id_without_external_id():
    first = orchestrator_adapter_harness.build_default_off_advisory_agent_chain_harness(
        created_at_utc="2026-07-07T00:00:00+00:00",
    )
    second = orchestrator_adapter_harness.build_default_off_advisory_agent_chain_harness(
        created_at_utc="2026-07-08T00:00:00+00:00",
    )
    explicit = orchestrator_adapter_harness.build_default_off_advisory_agent_chain_harness(
        chain_run_id="explicit_trace_ready_chain",
    )

    assert first["chain_run_id"] == second["chain_run_id"]
    assert first["trace_ready_bundle"]["agent_run_id"] == first["chain_run_id"]
    assert explicit["chain_run_id"] == "explicit_trace_ready_chain"
    assert explicit["trace_ready_bundle"]["chain_run_id"] == "explicit_trace_ready_chain"


def test_trace_ready_bundle_does_not_execute_trace_store_writes_by_default(monkeypatch):
    def fail_if_called(*args, **kwargs):
        raise AssertionError("trace execution helper must not be called")

    monkeypatch.setattr(trace, "execute_agent_trace_recording", fail_if_called)

    result = orchestrator_adapter_harness.build_default_off_advisory_agent_chain_harness()

    assert result["trace_ready_bundle"]["trace_persistence_enabled"] is False
    assert result["trace_ready_bundle"]["trace_store_write_enabled"] is False
    assert result["trace_ready_bundle"]["validation_safety_summary"]["did_call_trace_execution_helper"] is False


def test_phase79d_harness_and_workflow_runner_remain_compatible():
    harness = orchestrator_adapter_harness.build_default_off_advisory_agent_chain_harness(enabled=True)
    dry_run = workflow_runner.run_agentic_workflow_dry_run()

    assert harness["validation"]["validation_status"] == "passed"
    assert harness["summary"]["production_mutating_agent_count"] == 0
    assert dry_run["execution_mode"] == "dry_run"
    assert dry_run["executed_step_count"] == 0
    assert dry_run["summary"]["did_execute_any_step"] is False
