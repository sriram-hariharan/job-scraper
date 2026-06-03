import csv
import json

from src.agents import orchestrator_adapter_harness, read_only_adapter_chain, workflow_runner


def _queue_row(**overrides):
    row = {
        "job_doc_id": "job_1",
        "job_company": "Example Co",
        "job_title": "Backend Software Engineer",
        "source": "greenhouse",
        "action": "APPLY",
        "deterministic_winner_available": "true",
        "deterministic_winner_score": "0.850000",
        "winner_score": "0.850000",
        "winner_resume": "backend_resume.pdf",
        "fallback_only_no_deterministic_match": "false",
        "packet_generation_allowed": "true",
        "packet_generation_block_reason": "",
        "critic_decision": "",
        "missing_requirement_count": "0",
    }
    row.update(overrides)
    return row


def _all_adapter_flags_false(result):
    for flag in [
        "allow_production_mutation",
        "allow_queue_action_update",
        "allow_packet_update",
        "allow_tailoring_update",
        "allow_tailoring_generation_update",
        "allow_scoring_update",
        "allow_ranking_update",
        "allow_application_submission",
    ]:
        if flag in result:
            assert result[flag] is False


def test_empty_input_returns_warning_safely():
    result = read_only_adapter_chain.run_read_only_adapter_chain()

    assert result["execution_mode"] == "manual_read_only_adapter_chain"
    assert result["did_execute_chain"] is False
    assert result["did_mutate_production"] is False
    assert result["summary"]["input_row_count"] == 0
    assert result["summary"]["adapters_executed_count"] == 0
    assert result["validation"]["validation_status"] == "warning"
    assert "chain_not_executed" in result["validation"]["warning_codes"]
    assert "no_queue_rows_or_path" in result["reason_codes"]


def test_queue_rows_input_runs_chain_without_mutating_original_rows():
    rows = [
        _queue_row(),
        _queue_row(job_doc_id="job_2", deterministic_winner_score="0.000000", winner_score="0.000000", fallback_only_no_deterministic_match="true"),
    ]
    original_rows = [dict(row) for row in rows]

    result = read_only_adapter_chain.run_read_only_adapter_chain(
        queue_rows=rows,
        pipeline_run_id="chain_run",
        owner_user_id="chain_owner",
    )

    assert rows == original_rows
    assert result["did_execute_chain"] is True
    assert result["did_mutate_production"] is False
    assert result["adapter_execution_order"] == ["job_prioritization", "tailoring_decision", "operator_review"]
    assert result["summary"]["input_row_count"] == 2
    assert result["summary"]["job_prioritization_recommendation_count"] == 2
    assert result["summary"]["tailoring_decision_count"] == 2
    assert result["summary"]["operator_review_lane_count"] == 2
    assert result["summary"]["adapters_executed_count"] == 3
    assert result["validation"]["validation_status"] == "passed"


def test_queue_input_artifact_path_loads_explicit_csv(tmp_path):
    input_path = tmp_path / "queue.csv"
    with input_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(_queue_row().keys()))
        writer.writeheader()
        writer.writerow(_queue_row(job_doc_id="job_csv"))

    result = read_only_adapter_chain.run_read_only_adapter_chain(
        queue_input_artifact_path=input_path,
    )

    assert result["did_execute_chain"] is True
    assert result["summary"]["input_row_count"] == 1
    assert result["context"]["queue_input_artifact_path"] == str(input_path)


def test_adapter_result_safety_flags_remain_false():
    result = read_only_adapter_chain.run_read_only_adapter_chain(queue_rows=[_queue_row()])

    for adapter_key in result["adapter_execution_order"]:
        adapter_result = result["adapter_results"][adapter_key]
        assert adapter_result["did_mutate_production"] is False
        _all_adapter_flags_false(adapter_result)


def test_validation_passes_for_normal_chain_result():
    result = read_only_adapter_chain.run_read_only_adapter_chain(queue_rows=[_queue_row()])
    validation = read_only_adapter_chain.validate_read_only_adapter_chain_result(result)

    assert validation["validation_status"] == "passed"
    assert validation["reason_codes"] == []


def test_validation_catches_did_mutate_production_true():
    result = read_only_adapter_chain.run_read_only_adapter_chain(queue_rows=[_queue_row()])
    result["did_mutate_production"] = True

    validation = read_only_adapter_chain.validate_read_only_adapter_chain_result(result)

    assert validation["validation_status"] == "failed"
    assert "did_mutate_production" in validation["reason_codes"]


def test_validation_catches_wrong_execution_mode():
    result = read_only_adapter_chain.run_read_only_adapter_chain(queue_rows=[_queue_row()])
    result["execution_mode"] = "live"

    validation = read_only_adapter_chain.validate_read_only_adapter_chain_result(result)

    assert validation["validation_status"] == "failed"
    assert "execution_mode_not_manual_read_only_adapter_chain" in validation["reason_codes"]


def test_validation_catches_unsafe_adapter_result_mutation():
    result = read_only_adapter_chain.run_read_only_adapter_chain(queue_rows=[_queue_row()])
    result["adapter_results"]["operator_review"]["allow_application_submission"] = True

    validation = read_only_adapter_chain.validate_read_only_adapter_chain_result(result)

    assert validation["validation_status"] == "failed"
    assert "operator_review:unsafe_flag_true" in validation["reason_codes"]


def test_validation_catches_allow_application_submission_true():
    result = read_only_adapter_chain.run_read_only_adapter_chain(queue_rows=[_queue_row()])
    result["allow_application_submission"] = True

    validation = read_only_adapter_chain.validate_read_only_adapter_chain_result(result)

    assert validation["validation_status"] == "failed"
    assert "allow_application_submission_true" in validation["reason_codes"]


def test_artifact_writer_writes_chain_root_and_adapter_subdirectory_files_only(tmp_path):
    result = read_only_adapter_chain.run_read_only_adapter_chain(
        queue_rows=[_queue_row()],
        output_dir=tmp_path,
    )
    artifact_names = {path.split("/")[-1] for path in result["artifacts_written"]}

    assert "read_only_adapter_chain_result.json" in artifact_names
    assert "read_only_adapter_chain_report.md" in artifact_names
    assert "job_prioritization_read_only_adapter_result.json" in artifact_names
    assert "tailoring_decision_read_only_adapter_result.json" in artifact_names
    assert "operator_review_read_only_adapter_result.json" in artifact_names
    assert (tmp_path / "job_prioritization" / "job_prioritization_read_only_adapter_recommendations.csv").exists()
    assert (tmp_path / "tailoring_decision" / "tailoring_decision_read_only_adapter_decisions.csv").exists()
    assert (tmp_path / "operator_review" / "operator_review_read_only_adapter_reviews.csv").exists()
    assert not (tmp_path / "application_execution_queue.csv").exists()
    assert not (tmp_path / "job_prioritization_recommendations.csv").exists()
    assert not (tmp_path / "tailoring_decision_recommendations.csv").exists()
    assert not (tmp_path / "operator_review_recommendations.csv").exists()
    payload = json.loads((tmp_path / "read_only_adapter_chain_result.json").read_text(encoding="utf-8"))
    assert payload["execution_mode"] == "manual_read_only_adapter_chain"


def test_cli_json_no_input_returns_safe_warning(capsys):
    exit_code = read_only_adapter_chain.main(["--json"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"execution_mode": "manual_read_only_adapter_chain"' in output
    assert '"did_execute_chain": false' in output
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
