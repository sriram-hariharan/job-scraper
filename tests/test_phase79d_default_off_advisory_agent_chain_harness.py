from src.agents import orchestrator_adapter_harness, workflow_registry, workflow_runner


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
    "source_resume_mutation_allowed",
    "llm_provider_call_allowed",
    "scheduler_mutation_allowed",
    "workflow_runner_live_execution_allowed",
]


def test_advisory_chain_harness_is_default_off_and_read_only():
    result = orchestrator_adapter_harness.build_default_off_advisory_agent_chain_harness()

    assert result["harness_version"] == "default_off_advisory_agent_chain_harness_v1"
    assert result["execution_mode"] == "default_off_read_only_advisory_chain"
    assert result["default_off"] is True
    assert result["enabled"] is False
    assert result["explicit_invocation_required"] is True
    assert result["read_only"] is True
    assert result["advisory_only"] is True
    assert result["validation"]["validation_status"] == "passed"
    for flag in UNSAFE_FLAGS:
        assert result[flag] is False


def test_advisory_chain_represents_registry_order_without_execution():
    result = orchestrator_adapter_harness.build_default_off_advisory_agent_chain_harness(
        enabled=True,
        pipeline_run_id="phase79d_run",
        owner_user_id="phase79d_owner",
    )

    assert result["enabled"] is True
    assert result["pipeline_run_id"] == "phase79d_run"
    assert result["owner_user_id"] == "phase79d_owner"
    assert result["ordered_agent_keys"] == workflow_registry.ORDERED_AGENT_KEYS
    assert [agent["agent_key"] for agent in result["chain_agents"]] == workflow_registry.ORDERED_AGENT_KEYS
    assert [agent["chain_index"] for agent in result["chain_agents"]] == [1, 2, 3, 4, 5, 6]
    assert result["summary"]["agent_count"] == 6
    assert result["summary"]["execution_enabled_count"] == 0
    assert result["summary"]["did_execute_count"] == 0
    assert result["summary"]["mutation_allowed_count"] == 0
    assert result["summary"]["production_mutating_agent_count"] == 0
    assert result["validation"]["validation_status"] == "passed"


def test_advisory_chain_agent_statuses_are_advisory_and_non_mutating():
    result = orchestrator_adapter_harness.build_default_off_advisory_agent_chain_harness(enabled=True)

    for agent in result["chain_agents"]:
        assert agent["advisory_only"] is True
        assert agent["read_only"] is True
        assert agent["execution_enabled"] is False
        assert agent["did_execute"] is False
        assert agent["mutation_allowed"] is False
        assert agent["mutates_production_decisions"] is False
        assert agent["llm_call_expected"] is False
        assert agent["allowed_execution_mode"] in {"dry_run_only", "future_read_only"}
        assert "default_off_advisory_chain" in agent["reason_codes"]
        assert "agent_execution_disabled" in agent["reason_codes"]
        assert "auto_apply_disabled" in agent["reason_codes"]
        assert "ats_submission_disabled" in agent["reason_codes"]
        for flag in UNSAFE_FLAGS:
            if flag in agent:
                assert agent[flag] is False


def test_advisory_chain_validation_catches_auto_apply_or_mutation_capability():
    result = orchestrator_adapter_harness.build_default_off_advisory_agent_chain_harness()
    result["auto_apply_allowed"] = True
    result["chain_agents"][0]["mutation_allowed"] = True

    validation = orchestrator_adapter_harness.validate_default_off_advisory_agent_chain_harness(result)

    assert validation["validation_status"] == "failed"
    assert "auto_apply_allowed_not_false" in validation["reason_codes"]
    assert "source_health:mutation_allowed_not_false" in validation["reason_codes"]


def test_workflow_runner_remains_dry_run_only_for_phase79d():
    result = workflow_runner.run_agentic_workflow_dry_run()

    assert result["execution_mode"] == "dry_run"
    assert result["executed_step_count"] == 0
    assert result["summary"]["did_execute_any_step"] is False
    assert all(step["did_execute"] is False for step in result["ordered_step_results"])
    assert all(step["execution_enabled"] is False for step in result["ordered_step_results"])
