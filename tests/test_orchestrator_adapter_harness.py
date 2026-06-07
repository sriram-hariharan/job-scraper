import json

from src.agents import orchestrator_adapter_harness, workflow_registry, workflow_runner


EXPECTED_AGENT_KEYS = [
    "source_health",
    "resume_match",
    "critic",
    "job_prioritization",
    "tailoring_decision",
    "operator_review",
]


def test_preflight_plan_includes_all_agents_in_registry_order():
    plan = orchestrator_adapter_harness.build_read_only_adapter_preflight_plan(
        pipeline_run_id="run_preflight",
        owner_user_id="owner_preflight",
    )
    results = plan["adapter_preflight_results"]

    assert plan["harness_version"] == "read_only_adapter_harness_v1"
    assert plan["execution_mode"] == "read_only_preflight"
    assert plan["pipeline_run_id"] == "run_preflight"
    assert plan["owner_user_id"] == "owner_preflight"
    assert plan["planned_adapter_count"] == 6
    assert [result["agent_key"] for result in results] == EXPECTED_AGENT_KEYS
    assert [result["agent_key"] for result in results] == workflow_registry.ORDERED_AGENT_KEYS


def test_preflight_plan_never_enables_or_executes_adapters():
    plan = orchestrator_adapter_harness.build_read_only_adapter_preflight_plan()

    assert plan["allow_agent_execution"] is False
    assert plan["executable_adapter_count"] == 0
    assert plan["did_execute_live"] is False
    assert plan["did_mutate_production"] is False
    assert plan["did_write_db"] is False
    assert plan["summary"]["execution_enabled_count"] == 0
    assert plan["summary"]["did_execute_count"] == 0
    for result in plan["adapter_preflight_results"]:
        assert result["execution_enabled"] is False
        assert result["did_execute"] is False
        assert result["mutates_production_decisions"] is False
        assert result["llm_call_expected"] is False
        assert result["allowed_execution_mode"] in {"dry_run_only", "future_read_only"}
        assert "agent_execution_disabled" in result["reason_codes"]
        assert "read_only_preflight" in result["reason_codes"]


def test_preflight_plan_includes_read_only_fixture_validation_summary():
    plan = orchestrator_adapter_harness.build_read_only_adapter_preflight_plan()

    assert plan["fixture_validation_enabled"] is True
    assert plan["fixture_validation_passed"] is True
    assert plan["fixture_validation_status"] == "passed"
    assert plan["fixture_validation_expected_fixture_count"] == 3
    assert plan["fixture_validation_checked_count"] == 3
    assert plan["fixture_validation_failed_fixture_ids"] == []
    assert "db_write_not_allowed" in plan["fixture_validation_reason_codes"]
    assert "application_submission_not_allowed" in plan["fixture_validation_reason_codes"]

    result_by_filename = {
        result["fixture_filename"]: result
        for result in plan["fixture_validation_results"]
    }
    assert sorted(result_by_filename) == [
        "blocked_application_submission_request_minimal.json",
        "blocked_db_write_request_minimal.json",
        "safe_execution_request_minimal.json",
    ]
    assert result_by_filename["safe_execution_request_minimal.json"][
        "actual_validation_status"
    ] == "passed"
    assert result_by_filename["blocked_db_write_request_minimal.json"][
        "actual_validation_status"
    ] == "failed"
    assert result_by_filename["blocked_application_submission_request_minimal.json"][
        "actual_validation_status"
    ] == "failed"
    assert "db_write_not_allowed" in result_by_filename[
        "blocked_db_write_request_minimal.json"
    ]["actual_reason_codes"]
    assert "application_submission_not_allowed" in result_by_filename[
        "blocked_application_submission_request_minimal.json"
    ]["actual_reason_codes"]
    assert all(
        result["expected_matches_actual"]
        for result in plan["fixture_validation_results"]
    )
    assert all(
        result["did_execute_fixture"] is False
        and result["did_mutate_production"] is False
        and result["did_write_db"] is False
        for result in plan["fixture_validation_results"]
    )
    assert plan["allow_agent_execution"] is False
    assert plan["executable_adapter_count"] == 0
    assert plan["summary"]["did_execute_count"] == 0
    assert plan["did_execute_live"] is False
    assert plan["did_mutate_production"] is False
    assert plan["did_write_db"] is False


def test_preflight_result_contract_fields_are_present():
    plan = orchestrator_adapter_harness.build_read_only_adapter_preflight_plan()
    result = plan["adapter_preflight_results"][0]

    for field in [
        "step_index",
        "agent_key",
        "agent_name",
        "owner_module",
        "adapter_status",
        "allowed_execution_mode",
        "would_call_entrypoints",
        "required_artifacts",
        "produced_artifacts",
        "input_loader_required",
        "output_validator_required",
        "artifact_writer_available",
        "trace_supported",
        "db_access_required",
        "env_context_required",
        "llm_call_expected",
        "mutates_production_decisions",
        "preflight_status",
        "execution_enabled",
        "did_execute",
        "reason_codes",
    ]:
        assert field in result
    assert all(isinstance(item, str) and item for item in result["would_call_entrypoints"])


def test_preflight_validation_passes_for_default_plan():
    plan = orchestrator_adapter_harness.build_read_only_adapter_preflight_plan()
    validation = orchestrator_adapter_harness.validate_read_only_adapter_preflight_plan(plan)

    assert plan["validation"]["validation_status"] == "passed"
    assert validation["validation_status"] == "passed"
    assert validation["reason_codes"] == []
    assert validation["warning_codes"] == []
    assert validation["expected_order"] == EXPECTED_AGENT_KEYS
    assert validation["actual_order"] == EXPECTED_AGENT_KEYS


def test_preflight_validation_catches_execution_enabled():
    plan = orchestrator_adapter_harness.build_read_only_adapter_preflight_plan()
    plan["adapter_preflight_results"][0]["execution_enabled"] = True

    validation = orchestrator_adapter_harness.validate_read_only_adapter_preflight_plan(plan)

    assert validation["validation_status"] == "failed"
    assert "source_health:execution_enabled" in validation["reason_codes"]


def test_preflight_validation_catches_did_execute():
    plan = orchestrator_adapter_harness.build_read_only_adapter_preflight_plan()
    plan["adapter_preflight_results"][0]["did_execute"] = True

    validation = orchestrator_adapter_harness.validate_read_only_adapter_preflight_plan(plan)

    assert validation["validation_status"] == "failed"
    assert "source_health:did_execute" in validation["reason_codes"]


def test_preflight_validation_catches_live_execution_mode():
    plan = orchestrator_adapter_harness.build_read_only_adapter_preflight_plan()
    plan["adapter_preflight_results"][0]["allowed_execution_mode"] = "autonomous"

    validation = orchestrator_adapter_harness.validate_read_only_adapter_preflight_plan(plan)

    assert validation["validation_status"] == "failed"
    assert "source_health:live_execution_mode" in validation["reason_codes"]


def test_preflight_artifact_presence_is_warning_only(tmp_path):
    plan = orchestrator_adapter_harness.build_read_only_adapter_preflight_plan(artifact_root=tmp_path)
    validation = plan["validation"]

    assert "artifact_presence" in plan["adapter_preflight_results"][0]
    assert validation["validation_status"] == "warning"
    assert "source_health:missing_required_artifacts" in validation["warning_codes"]


def test_preflight_markdown_includes_preflight_only_warning():
    markdown = orchestrator_adapter_harness.render_read_only_adapter_preflight_markdown()

    assert "# Read-Only Adapter Preflight" in markdown
    assert "Preflight-only warning" in markdown
    assert "does not execute agents" in markdown
    assert "enable autonomous execution" in markdown
    assert "Executable adapter count: `0`" in markdown


def test_preflight_artifact_writer_writes_reports(tmp_path):
    result = orchestrator_adapter_harness.write_read_only_adapter_preflight_artifacts(output_dir=tmp_path)

    json_path = tmp_path / "read_only_adapter_preflight.json"
    md_path = tmp_path / "read_only_adapter_preflight.md"
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert result["validation_status"] == "passed"
    assert payload["execution_mode"] == "read_only_preflight"
    assert payload["executable_adapter_count"] == 0
    assert json_path.exists()
    assert md_path.exists()
    assert "# Read-Only Adapter Preflight" in md_path.read_text(encoding="utf-8")


def test_preflight_cli_json_returns_success(capsys):
    exit_code = orchestrator_adapter_harness.main(["--preflight", "--json"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"execution_mode": "read_only_preflight"' in output
    assert '"executable_adapter_count": 0' in output


def test_workflow_runner_remains_dry_run_only():
    result = workflow_runner.run_agentic_workflow_dry_run()

    assert result["execution_mode"] == "dry_run"
    assert result["executed_step_count"] == 0
    for step in result["ordered_step_results"]:
        assert step["did_execute"] is False
        assert step["execution_enabled"] is False
