import json
from pathlib import Path

from src.agents import (
    dry_run_execution_simulator,
    orchestrator_adapter_harness,
    proposal_only_mutation_planner,
    read_only_chain_artifact_generator,
    workflow_runner,
)


SMOKE_FIXTURE_PATH = Path("tests/fixtures/agentic_read_only_chain_smoke/application_execution_queue.csv")
PRODUCTION_ROOT_NAMES = {
    "application_execution_queue.csv",
    "job_prioritization_recommendations.csv",
    "tailoring_decision_recommendations.csv",
    "operator_review_recommendations.csv",
    "dry_run_execution_simulation_result.json",
}


def _make_simulation_artifact(tmp_path):
    chain_dir = tmp_path / "chain"
    sim_dir = tmp_path / "sim"
    generation = read_only_chain_artifact_generator.generate_read_only_chain_artifacts(
        queue_input_artifact_path=SMOKE_FIXTURE_PATH,
        output_dir=chain_dir,
        pipeline_run_id="proposal_fixture",
        owner_user_id="proposal_user",
    )
    assert generation["validation"]["validation_status"] == "passed"
    simulation = dry_run_execution_simulator.simulate_dry_run_execution(
        input_artifact_dir=chain_dir,
        output_dir=sim_dir,
        pipeline_run_id="proposal_fixture",
        owner_user_id="proposal_user",
    )
    assert simulation["validation"]["validation_status"] == "passed"
    return sim_dir / "dry_run_execution_simulation_result.json"


def test_missing_simulation_result_path_does_not_plan(tmp_path):
    result = proposal_only_mutation_planner.build_proposal_only_mutation_plan(
        output_dir=tmp_path,
    )

    assert result["did_plan"] is False
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_approve"] is False
    assert result["did_store_approval"] is False
    assert result["did_write_db"] is False
    assert result["validation"]["validation_status"] == "failed"
    assert "missing_explicit_simulation_result_path" in result["validation"]["reason_codes"]
    assert not (tmp_path / "proposal_only_mutation_plan_result.json").exists()


def test_missing_output_dir_does_not_plan(tmp_path):
    simulation_path = _make_simulation_artifact(tmp_path)

    result = proposal_only_mutation_planner.build_proposal_only_mutation_plan(
        simulation_result_path=simulation_path,
    )

    assert result["did_plan"] is False
    assert result["validation"]["validation_status"] == "failed"
    assert "missing_explicit_output_dir" in result["validation"]["reason_codes"]


def test_nonexistent_simulation_path_does_not_plan(tmp_path):
    result = proposal_only_mutation_planner.build_proposal_only_mutation_plan(
        simulation_result_path=tmp_path / "missing.json",
        output_dir=tmp_path / "plan",
    )

    assert result["did_plan"] is False
    assert result["validation"]["validation_status"] == "failed"
    assert "simulation_result_path_not_found" in result["validation"]["reason_codes"]
    assert not (tmp_path / "plan" / "proposal_only_mutation_plan_result.json").exists()


def test_invalid_simulation_artifact_does_not_plan(tmp_path):
    simulation_path = tmp_path / "bad_simulation.json"
    simulation_path.write_text(json.dumps({"execution_mode": "unsafe"}), encoding="utf-8")

    result = proposal_only_mutation_planner.build_proposal_only_mutation_plan(
        simulation_result_path=simulation_path,
        output_dir=tmp_path / "plan",
    )

    assert result["did_plan"] is False
    assert result["validation"]["validation_status"] == "failed"
    assert "simulation_result_validation_failed" in result["validation"]["reason_codes"]
    assert not (tmp_path / "plan" / "proposal_only_mutation_plan_result.json").exists()


def test_planner_source_does_not_import_or_run_execution_helpers():
    source = Path("src/agents/proposal_only_mutation_planner.py").read_text(encoding="utf-8")

    for forbidden in [
        "workflow_runner",
        "run_application_planning",
        "from src.application_execution_queue",
        "import src.application_execution_queue",
        "read_only_adapter_chain",
        "read_only_chain_artifact_generator",
        "simulate_dry_run_execution",
        "generate_read_only_chain_artifacts",
        "run_read_only_adapter_chain",
        "from src.storage",
        "import src.storage",
        "src.storage.",
        "FastAPI",
    ]:
        assert forbidden not in source


def test_fixture_flow_builds_proposal_only_plan_from_existing_simulation(tmp_path):
    simulation_path = _make_simulation_artifact(tmp_path)
    output_dir = tmp_path / "plan"

    result = proposal_only_mutation_planner.build_proposal_only_mutation_plan(
        simulation_result_path=simulation_path,
        output_dir=output_dir,
        pipeline_run_id="proposal_plan",
        owner_user_id="proposal_owner",
    )

    assert result["execution_mode"] == "explicit_proposal_only_mutation_planning"
    assert result["did_plan"] is True
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_approve"] is False
    assert result["did_store_approval"] is False
    assert result["did_write_db"] is False
    assert result["validation"]["validation_status"] == "passed"
    assert result["proposal_plan"]["can_execute_live"] is False
    assert result["proposal_plan"]["can_mutate"] is False
    assert result["proposal_plan"]["can_approve"] is False
    assert result["proposal_plan"]["requires_operator_approval"] is True
    assert result["proposal_plan"]["requires_approval_api"] is True
    assert result["proposal_plan"]["requires_approval_storage"] is True
    assert result["proposal_plan"]["requires_audit_ledger"] is True
    assert result["proposal_plan"]["requires_idempotency_key"] is True
    assert result["proposal_plan"]["requires_execution_lock"] is True
    assert result["proposal_plan"]["requires_rollback_plan"] is True
    assert "block_live_execution" in result["proposal_plan"]["proposed_next_review_steps"]
    assert "block_application_submission" in result["proposal_plan"]["proposed_next_review_steps"]
    assert "block_queue_mutation" in result["proposal_plan"]["proposed_next_review_steps"]

    items = result["proposal_only_mutation_items"]
    assert items
    for item in items:
        assert item["proposal_mode"] == "proposal_only_non_executable"
        assert item["mutation_type"] in proposal_only_mutation_planner.ALLOWED_MUTATION_TYPES
        assert item["can_execute_live"] is False
        assert item["can_mutate"] is False
        assert item["can_approve"] is False
        assert item["blocked_by_default"] is True
        assert item["requires_operator_approval"] is True
        assert item["requires_audit_ledger"] is True
        assert item["requires_idempotency_key"] is True
        assert item["requires_execution_lock"] is True
        assert item["requires_rollback_plan"] is True
        assert item["evidence_refs"]

    root_files = {path.name for path in output_dir.iterdir() if path.is_file()}
    assert root_files == {
        "proposal_only_mutation_plan_result.json",
        "proposal_only_mutation_plan_report.md",
    }
    assert not root_files.intersection(PRODUCTION_ROOT_NAMES)


def test_zero_source_proposals_warns_but_stays_non_executable(tmp_path):
    simulation_path = _make_simulation_artifact(tmp_path)
    payload = json.loads(simulation_path.read_text(encoding="utf-8"))
    payload["simulated_mutation_proposals"] = []
    simulation_path.write_text(json.dumps(payload), encoding="utf-8")

    result = proposal_only_mutation_planner.build_proposal_only_mutation_plan(
        simulation_result_path=simulation_path,
        output_dir=tmp_path / "plan",
    )

    assert result["did_plan"] is True
    assert result["proposal_only_mutation_items"] == []
    assert result["validation"]["validation_status"] == "warning"
    assert "no_simulated_mutation_proposals" in result["validation"]["warning_codes"]
    assert result["did_mutate_production"] is False


def test_validation_catches_forbidden_mutation_type(tmp_path):
    simulation_path = _make_simulation_artifact(tmp_path)
    result = proposal_only_mutation_planner.build_proposal_only_mutation_plan(
        simulation_result_path=simulation_path,
        output_dir=tmp_path / "plan",
    )
    result["proposal_only_mutation_items"][0]["mutation_type"] = "application_submission"

    validation = proposal_only_mutation_planner.validate_proposal_only_mutation_plan_result(result)

    assert validation["validation_status"] == "failed"
    assert "proposal_item_forbidden_mutation_type" in validation["reason_codes"]


def test_validation_catches_production_root_artifact_name(tmp_path):
    simulation_path = _make_simulation_artifact(tmp_path)
    output_dir = tmp_path / "plan"
    result = proposal_only_mutation_planner.build_proposal_only_mutation_plan(
        simulation_result_path=simulation_path,
        output_dir=output_dir,
    )
    (output_dir / "application_execution_queue.csv").write_text("unsafe\n", encoding="utf-8")

    validation = proposal_only_mutation_planner.validate_proposal_only_mutation_plan_result(result)

    assert validation["validation_status"] == "failed"
    assert "production_artifact_name_written_at_output_root" in validation["reason_codes"]


def test_cli_missing_args_fails_safely(capsys):
    exit_code = proposal_only_mutation_planner.main(["--json"])
    output = capsys.readouterr().out

    assert exit_code == 1
    payload = json.loads(output)
    assert payload["did_plan"] is False
    assert payload["did_execute_live"] is False
    assert payload["did_mutate_production"] is False
    assert payload["did_approve"] is False
    assert payload["did_store_approval"] is False
    assert payload["did_write_db"] is False
    assert payload["validation"]["validation_status"] == "failed"
    assert "missing_explicit_simulation_result_path" in payload["validation"]["reason_codes"]
    assert "missing_explicit_output_dir" in payload["validation"]["reason_codes"]


def test_cli_fixture_run_succeeds(tmp_path, capsys):
    simulation_path = _make_simulation_artifact(tmp_path)
    output_dir = tmp_path / "plan"

    exit_code = proposal_only_mutation_planner.main(
        [
            "--simulation-result",
            str(simulation_path),
            "--output-dir",
            str(output_dir),
            "--json",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    payload = json.loads(output)
    assert payload["did_plan"] is True
    assert payload["did_execute_live"] is False
    assert payload["did_mutate_production"] is False
    assert payload["validation"]["validation_status"] == "passed"
    assert (output_dir / "proposal_only_mutation_plan_result.json").exists()
    assert (output_dir / "proposal_only_mutation_plan_report.md").exists()


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
