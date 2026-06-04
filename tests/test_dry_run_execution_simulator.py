import json
from pathlib import Path

from src.agents import (
    dry_run_execution_simulator,
    orchestrator_adapter_harness,
    read_only_adapter_chain,
    read_only_chain_artifact_generator,
    workflow_runner,
)


SMOKE_FIXTURE_PATH = Path("tests/fixtures/agentic_read_only_chain_smoke/application_execution_queue.csv")
PRODUCTION_ROOT_NAMES = {
    "application_execution_queue.csv",
    "job_prioritization_recommendations.csv",
    "tailoring_decision_recommendations.csv",
    "operator_review_recommendations.csv",
}


def _make_existing_artifacts(tmp_path):
    input_dir = tmp_path / "chain"
    result = read_only_chain_artifact_generator.generate_read_only_chain_artifacts(
        queue_input_artifact_path=SMOKE_FIXTURE_PATH,
        output_dir=input_dir,
        pipeline_run_id="simulator_fixture",
        owner_user_id="simulator_user",
    )
    assert result["validation"]["validation_status"] == "passed"
    return input_dir


def _fail_if_called(*args, **kwargs):
    raise AssertionError("simulator must not run chain or generator")


def test_missing_input_dir_does_not_simulate(tmp_path):
    result = dry_run_execution_simulator.simulate_dry_run_execution(output_dir=tmp_path)

    assert result["did_simulate"] is False
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["validation"]["validation_status"] == "failed"
    assert "missing_explicit_input_artifact_dir" in result["validation"]["reason_codes"]
    assert not (tmp_path / "dry_run_execution_simulation_result.json").exists()


def test_missing_output_dir_does_not_simulate(tmp_path):
    result = dry_run_execution_simulator.simulate_dry_run_execution(input_artifact_dir=tmp_path)

    assert result["did_simulate"] is False
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["validation"]["validation_status"] == "failed"
    assert "missing_explicit_output_dir" in result["validation"]["reason_codes"]


def test_nonexistent_input_dir_does_not_simulate(tmp_path):
    result = dry_run_execution_simulator.simulate_dry_run_execution(
        input_artifact_dir=tmp_path / "missing",
        output_dir=tmp_path / "out",
    )

    assert result["did_simulate"] is False
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert "input_artifact_dir_not_found" in result["validation"]["reason_codes"]
    assert not (tmp_path / "out" / "dry_run_execution_simulation_result.json").exists()


def test_missing_source_artifacts_fail_safely(tmp_path):
    input_dir = tmp_path / "input"
    input_dir.mkdir()

    result = dry_run_execution_simulator.simulate_dry_run_execution(
        input_artifact_dir=input_dir,
        output_dir=tmp_path / "out",
    )

    assert result["did_simulate"] is False
    assert "missing_read_only_adapter_chain_result" in result["validation"]["reason_codes"]
    assert "missing_read_only_chain_artifact_generation_result" in result["validation"]["reason_codes"]
    assert not (tmp_path / "out" / "dry_run_execution_simulation_result.json").exists()


def test_simulator_does_not_run_chain_or_generator(monkeypatch, tmp_path):
    input_dir = _make_existing_artifacts(tmp_path)
    output_dir = tmp_path / "sim"
    monkeypatch.setattr(read_only_adapter_chain, "run_read_only_adapter_chain", _fail_if_called)
    monkeypatch.setattr(
        read_only_chain_artifact_generator,
        "generate_read_only_chain_artifacts",
        _fail_if_called,
    )

    result = dry_run_execution_simulator.simulate_dry_run_execution(
        input_artifact_dir=input_dir,
        output_dir=output_dir,
    )

    assert result["did_simulate"] is True
    assert result["validation"]["validation_status"] == "passed"
    assert (output_dir / "dry_run_execution_simulation_result.json").exists()
    assert (output_dir / "dry_run_execution_simulation_report.md").exists()


def test_fixture_roundtrip_simulator_reads_existing_artifacts(tmp_path):
    input_dir = _make_existing_artifacts(tmp_path)
    output_dir = tmp_path / "sim"

    result = dry_run_execution_simulator.simulate_dry_run_execution(
        input_artifact_dir=input_dir,
        output_dir=output_dir,
        pipeline_run_id="sim_run",
        owner_user_id="sim_owner",
    )

    assert result["execution_mode"] == "explicit_dry_run_execution_simulation"
    assert result["did_simulate"] is True
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["context"]["allow_db_write"] is False
    assert result["context"]["allow_scheduler_execution"] is False
    assert result["validation"]["validation_status"] == "passed"
    assert result["chain_artifact_summary"]["input_row_count"] == 4
    assert result["chain_artifact_summary"]["adapters_executed_count"] == 3
    assert result["simulated_execution_plan"]["can_execute_live"] is False
    assert result["simulated_execution_plan"]["requires_operator_approval"] is True
    assert result["simulated_execution_plan"]["requires_audit_ledger"] is True
    assert result["simulated_execution_plan"]["requires_idempotency_key"] is True
    assert result["simulated_execution_plan"]["requires_execution_lock"] is True
    assert result["simulated_execution_plan"]["requires_rollback_plan"] is True
    assert "queue_mutation_blocked" in result["blocked_live_execution_reasons"]
    assert "application_submission_blocked" in result["blocked_live_execution_reasons"]

    proposals = result["simulated_mutation_proposals"]
    assert proposals
    for proposal in proposals:
        assert proposal["proposal_mode"] == "simulated_non_executable"
        assert proposal["mutation_type"] in dry_run_execution_simulator.SIMULATED_MUTATION_TYPES
        assert proposal["can_execute_live"] is False
        assert proposal["requires_approval"] is True
        assert proposal["blocked_by_default"] is True

    root_files = {path.name for path in output_dir.iterdir() if path.is_file()}
    assert root_files == {
        "dry_run_execution_simulation_result.json",
        "dry_run_execution_simulation_report.md",
    }
    assert not root_files.intersection(PRODUCTION_ROOT_NAMES)


def test_validation_catches_production_root_artifact_name(tmp_path):
    input_dir = _make_existing_artifacts(tmp_path)
    output_dir = tmp_path / "sim"
    result = dry_run_execution_simulator.simulate_dry_run_execution(
        input_artifact_dir=input_dir,
        output_dir=output_dir,
    )
    (output_dir / "application_execution_queue.csv").write_text("unsafe\n", encoding="utf-8")

    validation = dry_run_execution_simulator.validate_dry_run_execution_simulation_result(result)

    assert validation["validation_status"] == "failed"
    assert "production_artifact_name_written_at_output_root" in validation["reason_codes"]


def test_cli_missing_args_fails_safely(capsys):
    exit_code = dry_run_execution_simulator.main(["--json"])
    output = capsys.readouterr().out

    assert exit_code == 1
    payload = json.loads(output)
    assert payload["did_simulate"] is False
    assert payload["did_execute_live"] is False
    assert payload["did_mutate_production"] is False
    assert payload["validation"]["validation_status"] == "failed"
    assert "missing_explicit_input_artifact_dir" in payload["validation"]["reason_codes"]
    assert "missing_explicit_output_dir" in payload["validation"]["reason_codes"]


def test_cli_fixture_run_succeeds(tmp_path, capsys):
    input_dir = _make_existing_artifacts(tmp_path)
    output_dir = tmp_path / "sim"

    exit_code = dry_run_execution_simulator.main(
        [
            "--input-artifact-dir",
            str(input_dir),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    payload = json.loads(output)
    assert payload["did_simulate"] is True
    assert payload["did_execute_live"] is False
    assert payload["did_mutate_production"] is False
    assert payload["validation"]["validation_status"] == "passed"
    assert (output_dir / "dry_run_execution_simulation_result.json").exists()
    assert (output_dir / "dry_run_execution_simulation_report.md").exists()


def test_preflight_executable_adapter_count_remains_zero():
    plan = orchestrator_adapter_harness.build_read_only_adapter_preflight_plan()

    assert plan["executable_adapter_count"] == 0
    assert plan["summary"]["execution_enabled_count"] == 0
    assert all(result["did_execute"] is False for result in plan["adapter_preflight_results"])


def test_workflow_runner_remains_dry_run_only():
    result = workflow_runner.run_agentic_workflow_dry_run()

    assert result["execution_mode"] == "dry_run"
    assert result["executed_step_count"] == 0
    assert all(step["did_execute"] is False for step in result["ordered_step_results"])
