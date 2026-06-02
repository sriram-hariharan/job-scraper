from src.agents import orchestrator_adapters, workflow_runner


EXPECTED_AGENT_KEYS = [
    "source_health",
    "resume_match",
    "critic",
    "job_prioritization",
    "tailoring_decision",
    "operator_review",
]


def test_orchestrator_adapter_contract_lists_all_implemented_agents():
    contract = orchestrator_adapters.get_orchestrator_adapter_contract()
    specs = orchestrator_adapters.list_orchestrator_adapter_specs()

    assert contract["contract_version"] == "orchestrator_adapter_contract_v1"
    assert contract["contract_only"] is True
    assert contract["execution_enabled"] is False
    assert contract["autonomous_execution_enabled"] is False
    assert contract["ordered_agent_keys"] == EXPECTED_AGENT_KEYS
    assert [spec["agent_key"] for spec in specs] == EXPECTED_AGENT_KEYS


def test_orchestrator_adapter_specs_are_static_safe_metadata():
    for spec in orchestrator_adapters.list_orchestrator_adapter_specs():
        assert spec["owner_module"].startswith("src.agents.")
        assert spec["adapter_status"] in {
            "ready_for_read_only_adapter",
            "needs_input_adapter",
            "needs_policy_adapter",
            "blocked",
        }
        assert spec["mutates_production_decisions"] is False
        assert spec["llm_call_expected"] is False
        assert spec["allowed_execution_mode"] in {"dry_run_only", "future_read_only"}
        assert spec["allowed_execution_mode"] not in {"live", "autonomous", "production"}
        assert spec["reason_codes"]
        assert all(isinstance(item, str) and item for item in spec["callable_entrypoint_names"])


def test_orchestrator_adapter_validation_passes():
    validation = orchestrator_adapters.validate_orchestrator_adapter_contract()

    assert validation["validation_status"] == "passed"
    assert validation["reason_codes"] == []
    assert validation["warning_codes"] == []
    assert validation["adapter_count"] == 6
    assert validation["registry_agent_keys"] == EXPECTED_AGENT_KEYS
    assert validation["adapter_agent_keys"] == EXPECTED_AGENT_KEYS


def test_orchestrator_adapter_validation_rejects_mutation_and_live_execution():
    contract = orchestrator_adapters.get_orchestrator_adapter_contract()
    contract["adapter_specs"]["source_health"]["mutates_production_decisions"] = True
    contract["adapter_specs"]["resume_match"]["allowed_execution_mode"] = "live"
    contract["adapter_specs"]["critic"]["callable_entrypoint_names"] = ["ok", 123]

    validation = orchestrator_adapters.validate_orchestrator_adapter_contract(contract)

    assert validation["validation_status"] == "failed"
    assert "source_health:mutates_production_decisions" in validation["reason_codes"]
    assert "resume_match:live_execution_mode" in validation["reason_codes"]
    assert "critic:non_string_callable_entrypoint_name" in validation["reason_codes"]


def test_orchestrator_adapter_markdown_warns_contract_only_and_dry_run():
    markdown = orchestrator_adapters.render_orchestrator_adapter_contract_markdown()

    assert "# Orchestrator Adapter Contract" in markdown
    assert "Contract-only warning" in markdown
    assert "dry-run only" in markdown
    assert "does not execute agents" in markdown
    assert "workflow runner mode: `dry_run_only`".lower() in markdown.lower()
    for agent_key in EXPECTED_AGENT_KEYS:
        assert f"### `{agent_key}`" in markdown


def test_workflow_runner_remains_dry_run_only():
    result = workflow_runner.run_agentic_workflow_dry_run()

    assert result["execution_mode"] == "dry_run"
    assert result["executed_step_count"] == 0
    for step in result["ordered_step_results"]:
        assert step["did_execute"] is False
        assert step["execution_enabled"] is False
        assert step["execution_status"] == "skipped_dry_run"
