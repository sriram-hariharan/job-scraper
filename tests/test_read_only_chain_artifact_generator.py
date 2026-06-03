import json
from pathlib import Path

from src.agents import (
    orchestrator_adapter_harness,
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


def _fail_if_chain_runs(*args, **kwargs):
    raise AssertionError("chain should not run without explicit valid input and output")


def test_missing_queue_input_does_not_run_chain(monkeypatch, tmp_path):
    monkeypatch.setattr(
        read_only_chain_artifact_generator.read_only_adapter_chain,
        "run_read_only_adapter_chain",
        _fail_if_chain_runs,
    )

    result = read_only_chain_artifact_generator.generate_read_only_chain_artifacts(
        output_dir=tmp_path,
    )

    assert result["did_run_chain"] is False
    assert result["did_mutate_production"] is False
    assert "missing_explicit_queue_input" in result["reason_codes"]
    assert result["validation"]["validation_status"] == "failed"
    assert not (tmp_path / "read_only_adapter_chain_result.json").exists()


def test_missing_output_dir_does_not_run_chain(monkeypatch):
    monkeypatch.setattr(
        read_only_chain_artifact_generator.read_only_adapter_chain,
        "run_read_only_adapter_chain",
        _fail_if_chain_runs,
    )

    result = read_only_chain_artifact_generator.generate_read_only_chain_artifacts(
        queue_input_artifact_path=SMOKE_FIXTURE_PATH,
    )

    assert result["did_run_chain"] is False
    assert result["did_mutate_production"] is False
    assert "missing_explicit_output_dir" in result["reason_codes"]
    assert result["validation"]["validation_status"] == "failed"
    assert result["generator_artifacts"] == []


def test_nonexistent_queue_input_does_not_run_chain(monkeypatch, tmp_path):
    monkeypatch.setattr(
        read_only_chain_artifact_generator.read_only_adapter_chain,
        "run_read_only_adapter_chain",
        _fail_if_chain_runs,
    )

    result = read_only_chain_artifact_generator.generate_read_only_chain_artifacts(
        queue_input_artifact_path=tmp_path / "missing.csv",
        output_dir=tmp_path / "out",
    )

    assert result["did_run_chain"] is False
    assert result["did_mutate_production"] is False
    assert "queue_input_artifact_not_found" in result["reason_codes"]
    assert result["validation"]["validation_status"] == "failed"
    assert not (tmp_path / "out" / "read_only_adapter_chain_result.json").exists()


def test_fixture_run_succeeds_and_writes_only_diagnostics(tmp_path):
    result = read_only_chain_artifact_generator.generate_read_only_chain_artifacts(
        queue_input_artifact_path=SMOKE_FIXTURE_PATH,
        output_dir=tmp_path,
        pipeline_run_id="generator_smoke",
        owner_user_id="generator_user",
    )

    assert result["execution_mode"] == "explicit_operator_read_only_chain_artifact_generation"
    assert result["did_run_chain"] is True
    assert result["did_mutate_production"] is False
    assert result["allow_live_pipeline_wiring"] is False
    assert result["allow_application_submission"] is False
    assert result["validation"]["validation_status"] == "passed"
    assert result["chain_result"]["execution_mode"] == "manual_read_only_adapter_chain"
    assert result["chain_result"]["did_mutate_production"] is False
    assert result["chain_result"]["allow_live_pipeline_wiring"] is False
    assert result["chain_result"]["allow_application_submission"] is False
    assert result["chain_result"]["adapter_execution_order"] == [
        "job_prioritization",
        "tailoring_decision",
        "operator_review",
    ]
    assert result["chain_result_summary"]["input_row_count"] == 4
    assert result["chain_result_summary"]["adapters_executed_count"] == 3

    root_files = {path.name for path in tmp_path.iterdir() if path.is_file()}
    assert "read_only_adapter_chain_result.json" in root_files
    assert "read_only_adapter_chain_report.md" in root_files
    assert "read_only_chain_artifact_generation_result.json" in root_files
    assert "read_only_chain_artifact_generation_report.md" in root_files
    assert not root_files.intersection(PRODUCTION_ROOT_NAMES)

    generator_artifact_names = {Path(path).name for path in result["generator_artifacts"]}
    assert generator_artifact_names == {
        "read_only_chain_artifact_generation_result.json",
        "read_only_chain_artifact_generation_report.md",
    }
    assert (tmp_path / "job_prioritization" / "job_prioritization_read_only_adapter_recommendations.csv").exists()
    assert (tmp_path / "tailoring_decision" / "tailoring_decision_read_only_adapter_decisions.csv").exists()
    assert (tmp_path / "operator_review" / "operator_review_read_only_adapter_reviews.csv").exists()


def test_validation_catches_production_root_artifact_name(tmp_path):
    result = read_only_chain_artifact_generator.generate_read_only_chain_artifacts(
        queue_input_artifact_path=SMOKE_FIXTURE_PATH,
        output_dir=tmp_path,
    )
    (tmp_path / "application_execution_queue.csv").write_text("unsafe\n", encoding="utf-8")

    validation = read_only_chain_artifact_generator.validate_chain_artifact_generation_result(result)

    assert validation["validation_status"] == "failed"
    assert "production_artifact_name_written_at_output_root" in validation["reason_codes"]


def test_cli_missing_args_fails_safely(capsys):
    exit_code = read_only_chain_artifact_generator.main(["--json"])
    output = capsys.readouterr().out

    assert exit_code == 1
    payload = json.loads(output)
    assert payload["did_run_chain"] is False
    assert payload["did_mutate_production"] is False
    assert payload["validation"]["validation_status"] == "failed"
    assert "missing_explicit_queue_input" in payload["validation"]["reason_codes"]
    assert "missing_explicit_output_dir" in payload["validation"]["reason_codes"]


def test_cli_fixture_run_succeeds(tmp_path, capsys):
    exit_code = read_only_chain_artifact_generator.main(
        [
            "--queue-input",
            str(SMOKE_FIXTURE_PATH),
            "--output-dir",
            str(tmp_path),
            "--json",
        ]
    )
    output = capsys.readouterr().out

    assert exit_code == 0
    payload = json.loads(output)
    assert payload["did_run_chain"] is True
    assert payload["did_mutate_production"] is False
    assert payload["validation"]["validation_status"] == "passed"
    assert (tmp_path / "read_only_adapter_chain_result.json").exists()
    assert (tmp_path / "read_only_adapter_chain_report.md").exists()


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
