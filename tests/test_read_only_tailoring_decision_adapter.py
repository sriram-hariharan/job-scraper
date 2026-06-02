import csv
import json

from src.agents import orchestrator_adapter_harness, read_only_tailoring_decision_adapter, workflow_runner


def _queue_row(**overrides):
    row = {
        "job_doc_id": "job_1",
        "job_company": "Example Co",
        "job_title": "Backend Software Engineer",
        "source": "greenhouse",
        "action": "APPLY",
        "advisory_priority": "apply_now",
        "deterministic_winner_available": "true",
        "deterministic_winner_score": "0.750000",
        "winner_score": "0.750000",
        "winner_resume": "backend_resume.pdf",
        "fallback_only_no_deterministic_match": "false",
        "packet_generation_allowed": "true",
        "packet_generation_block_reason": "",
        "critic_decision": "",
        "missing_requirement_count": "1",
    }
    row.update(overrides)
    return row


def _prioritization_row(**overrides):
    row = {
        "job_id": "job_1",
        "company": "Example Co",
        "title": "Backend Software Engineer",
        "advisory_priority": "tailor_first",
        "deterministic_winner_score": "0.650000",
        "fallback_only_no_deterministic_match": "false",
        "packet_generation_allowed": "true",
        "packet_generation_block_reason": "",
    }
    row.update(overrides)
    return row


def test_empty_input_returns_warning_safely():
    result = read_only_tailoring_decision_adapter.run_tailoring_decision_read_only_adapter()

    assert result["execution_mode"] == "read_only_adapter"
    assert result["did_execute_agent"] is False
    assert result["did_mutate_production"] is False
    assert result["row_count"] == 0
    assert result["decision_count"] == 0
    assert result["validation"]["validation_status"] == "warning"
    assert "no_queue_rows" in result["validation"]["warning_codes"]


def test_queue_rows_input_produces_decisions_without_mutating_original_rows():
    rows = [
        _queue_row(),
        _queue_row(job_doc_id="job_2", deterministic_winner_score="0.550000", winner_score="0.550000"),
    ]
    original_rows = [dict(row) for row in rows]

    result = read_only_tailoring_decision_adapter.run_tailoring_decision_read_only_adapter(
        queue_rows=rows,
        pipeline_run_id="run_adapter",
        owner_user_id="owner_adapter",
    )

    assert rows == original_rows
    assert result["did_execute_agent"] is True
    assert result["did_mutate_production"] is False
    assert result["row_count"] == 2
    assert result["decision_count"] == 2
    assert result["decisions"][0]["tailoring_decision"] == "light_tailoring"
    assert result["decisions"][0]["existing_action"] == "APPLY"
    assert result["validation"]["validation_status"] == "passed"


def test_optional_prioritization_rows_can_supply_advisory_priority():
    result = read_only_tailoring_decision_adapter.run_tailoring_decision_read_only_adapter(
        queue_rows=[
            _queue_row(
                advisory_priority="",
                deterministic_winner_score="",
                winner_score="",
            )
        ],
        prioritization_rows=[_prioritization_row()],
    )

    assert result["did_execute_agent"] is True
    assert result["decision_count"] == 1
    assert result["decisions"][0]["advisory_priority"] == "tailor_first"
    assert result["decisions"][0]["tailoring_decision"] == "tailor_before_apply"


def test_queue_input_artifact_path_loads_explicit_csv(tmp_path):
    input_path = tmp_path / "queue.csv"
    with input_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_queue_row().keys()))
        writer.writeheader()
        writer.writerow(_queue_row(job_doc_id="job_csv"))

    result = read_only_tailoring_decision_adapter.run_tailoring_decision_read_only_adapter(
        queue_input_artifact_path=input_path,
    )

    assert result["did_execute_agent"] is True
    assert result["row_count"] == 1
    assert result["decision_count"] == 1
    assert result["context"]["queue_input_artifact_path"] == str(input_path)


def test_validation_passes_for_normal_adapter_result():
    result = read_only_tailoring_decision_adapter.run_tailoring_decision_read_only_adapter(
        queue_rows=[_queue_row()]
    )
    validation = read_only_tailoring_decision_adapter.validate_tailoring_decision_adapter_result(result)

    assert validation["validation_status"] == "passed"
    assert validation["reason_codes"] == []


def test_validation_catches_did_mutate_production_true():
    result = read_only_tailoring_decision_adapter.run_tailoring_decision_read_only_adapter(
        queue_rows=[_queue_row()]
    )
    result["did_mutate_production"] = True

    validation = read_only_tailoring_decision_adapter.validate_tailoring_decision_adapter_result(result)

    assert validation["validation_status"] == "failed"
    assert "did_mutate_production" in validation["reason_codes"]


def test_validation_catches_wrong_execution_mode():
    result = read_only_tailoring_decision_adapter.run_tailoring_decision_read_only_adapter(
        queue_rows=[_queue_row()]
    )
    result["execution_mode"] = "live"

    validation = read_only_tailoring_decision_adapter.validate_tailoring_decision_adapter_result(result)

    assert validation["validation_status"] == "failed"
    assert "execution_mode_not_read_only_adapter" in validation["reason_codes"]


def test_validation_catches_unsafe_update_flags():
    result = read_only_tailoring_decision_adapter.run_tailoring_decision_read_only_adapter(
        queue_rows=[_queue_row()]
    )
    result["allow_queue_action_update"] = True
    result["allow_tailoring_generation_update"] = True

    validation = read_only_tailoring_decision_adapter.validate_tailoring_decision_adapter_result(result)

    assert validation["validation_status"] == "failed"
    assert "allow_queue_action_update_true" in validation["reason_codes"]
    assert "allow_tailoring_generation_update_true" in validation["reason_codes"]


def test_validation_catches_changed_existing_action():
    result = read_only_tailoring_decision_adapter.run_tailoring_decision_read_only_adapter(
        queue_rows=[_queue_row()]
    )
    result["decisions"][0]["existing_action"] = "SKIP_FOR_NOW"

    validation = read_only_tailoring_decision_adapter.validate_tailoring_decision_adapter_result(result)

    assert validation["validation_status"] == "failed"
    assert "existing_action_changed" in validation["reason_codes"]


def test_validation_catches_tailoring_scoring_and_ranking_mutation_signals():
    result = read_only_tailoring_decision_adapter.run_tailoring_decision_read_only_adapter(
        queue_rows=[_queue_row(score="0.75", rank="1", tailoring_status="pending")]
    )
    result["decisions"][0]["score"] = "0.80"
    result["decisions"][0]["rank"] = "2"
    result["decisions"][0]["tailoring_status"] = "generated"

    validation = read_only_tailoring_decision_adapter.validate_tailoring_decision_adapter_result(result)

    assert validation["validation_status"] == "failed"
    assert "production_action_field_written" in validation["reason_codes"]


def test_artifact_writer_writes_adapter_specific_files_only(tmp_path):
    result = read_only_tailoring_decision_adapter.run_tailoring_decision_read_only_adapter(
        queue_rows=[_queue_row()],
        output_dir=tmp_path,
    )
    artifact_names = {path.split("/")[-1] for path in result["artifacts_written"]}

    assert artifact_names == {
        "tailoring_decision_read_only_adapter_result.json",
        "tailoring_decision_read_only_adapter_report.md",
        "tailoring_decision_read_only_adapter_decisions.csv",
    }
    assert not (tmp_path / "application_execution_queue.csv").exists()
    assert not (tmp_path / "tailoring_decision_recommendations.csv").exists()
    assert not (tmp_path / "tailoring_decision_summary.json").exists()
    assert not (tmp_path / "job_prioritization_recommendations.csv").exists()
    payload = json.loads((tmp_path / "tailoring_decision_read_only_adapter_result.json").read_text(encoding="utf-8"))
    assert payload["execution_mode"] == "read_only_adapter"


def test_cli_json_no_input_returns_safe_warning(capsys):
    exit_code = read_only_tailoring_decision_adapter.main(["--json"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"execution_mode": "read_only_adapter"' in output
    assert '"did_execute_agent": false' in output
    assert '"validation_status": "warning"' in output


def test_preflight_harness_executable_adapter_count_remains_zero():
    plan = orchestrator_adapter_harness.build_read_only_adapter_preflight_plan()

    assert plan["executable_adapter_count"] == 0
    assert plan["summary"]["execution_enabled_count"] == 0
    assert all(result["execution_enabled"] is False for result in plan["adapter_preflight_results"])


def test_workflow_runner_remains_dry_run_only():
    result = workflow_runner.run_agentic_workflow_dry_run()

    assert result["execution_mode"] == "dry_run"
    assert result["executed_step_count"] == 0
    assert all(step["did_execute"] is False for step in result["ordered_step_results"])
