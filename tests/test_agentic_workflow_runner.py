import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.agents import orchestrator_adapter_harness, workflow_runner


EXPECTED_AGENT_KEYS = [
    "source_health",
    "resume_match",
    "critic",
    "job_prioritization",
    "tailoring_decision",
    "operator_review",
]
FIXTURE_DIR = Path("tests/fixtures/agentic_storage_transaction_failure_modes")


def _healthy_preflight_plan():
    healthy = workflow_runner.run_agentic_workflow_dry_run()
    return {
        "fixture_validation": deepcopy(healthy["fixture_validation"]),
        "executable_adapter_count": 0,
        "allow_agent_execution": False,
        "did_execute_live": False,
        "did_mutate_production": False,
        "did_write_db": False,
        "summary": {"did_execute_count": 0},
    }


def _run_with_fixture_validation(fixture_validation):
    preflight_plan = {
        "fixture_validation": fixture_validation,
        "executable_adapter_count": 0,
        "allow_agent_execution": False,
        "did_execute_live": False,
        "did_mutate_production": False,
        "did_write_db": False,
        "summary": {"did_execute_count": 0},
    }
    return workflow_runner.run_agentic_workflow_dry_run(preflight_plan=preflight_plan)


def _copy_fixture_dir(tmp_path):
    fixture_dir = (
        tmp_path
        / "repo"
        / "tests"
        / "fixtures"
        / "agentic_storage_transaction_failure_modes"
    )
    fixture_dir.mkdir(parents=True)
    for fixture_path in FIXTURE_DIR.iterdir():
        if fixture_path.is_file():
            (fixture_dir / fixture_path.name).write_text(
                fixture_path.read_text(encoding="utf-8"),
                encoding="utf-8",
            )
    return fixture_dir


def _assert_blocked_without_execution(result, expected_reason_code):
    assert result["execution_mode"] == "dry_run"
    assert result["blocked_by_fixture_validation_gate"] is True
    assert result["fixture_validation_gate_passed"] is False
    assert result["fixture_validation_gate_status"] == "failed"
    assert expected_reason_code in result["fixture_validation_gate_reason_codes"]
    assert result["validation"]["validation_status"] == "failed"
    assert "fixture_validation_gate_failed" in result["validation"]["reason_codes"]
    assert result["executed_step_count"] == 0
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False
    assert all(step["did_execute"] is False for step in result["ordered_step_results"])
    assert all(
        step["execution_enabled"] is False for step in result["ordered_step_results"]
    )
    assert all(
        step["execution_status"] == "skipped_dry_run"
        for step in result["ordered_step_results"]
    )


def _assert_blocked_dry_run_steps(result, expected_reason_code):
    assert result["execution_mode"] == "dry_run"
    assert result["blocked_by_fixture_validation_gate"] is True
    assert result["fixture_validation_gate_passed"] is False
    assert expected_reason_code in result["fixture_validation_gate_reason_codes"]
    assert result["executed_step_count"] == 0
    assert all(step["did_execute"] is False for step in result["ordered_step_results"])
    assert all(
        step["execution_enabled"] is False for step in result["ordered_step_results"]
    )


def _fixture_validation_with_result_mutation(filename, mutation):
    fixture_validation = deepcopy(_healthy_preflight_plan()["fixture_validation"])
    for item in fixture_validation["fixture_validation_results"]:
        if item["fixture_filename"] == filename:
            mutation(item)
            return fixture_validation
    raise AssertionError(f"Missing fixture result for {filename}")


def test_workflow_runner_dry_run_includes_all_planned_agents():
    result = workflow_runner.run_agentic_workflow_dry_run(
        pipeline_run_id="run_dry",
        owner_user_id="owner_dry",
    )
    steps = result["ordered_step_results"]

    assert result["runner_version"] == "agentic_workflow_runner_v1"
    assert result["execution_mode"] == "dry_run"
    assert result["pipeline_run_id"] == "run_dry"
    assert result["owner_user_id"] == "owner_dry"
    assert result["planned_step_count"] == 6
    assert [step["agent_key"] for step in steps] == EXPECTED_AGENT_KEYS


def test_workflow_runner_includes_fixture_validation_gate_fields():
    result = workflow_runner.run_agentic_workflow_dry_run()

    assert result["fixture_validation_gate_enabled"] is True
    assert result["fixture_validation_gate_status"] == "passed"
    assert result["fixture_validation_gate_passed"] is True
    assert result["fixture_validation_gate_reason_codes"] == []
    assert result["blocked_by_fixture_validation_gate"] is False
    assert result["fixture_validation"]["fixture_validation_passed"] is True
    assert result["fixture_validation"]["fixture_validation_checked_count"] == 3
    assert result["executable_adapter_count"] == 0
    assert result["allow_agent_execution"] is False
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False


def test_workflow_runner_expected_blocked_fixture_failures_do_not_block_gate():
    result = workflow_runner.run_agentic_workflow_dry_run()
    results_by_filename = {
        item["fixture_filename"]: item
        for item in result["fixture_validation"]["fixture_validation_results"]
    }

    assert result["fixture_validation_gate_passed"] is True
    assert result["blocked_by_fixture_validation_gate"] is False
    assert results_by_filename["safe_execution_request_minimal.json"][
        "actual_validation_status"
    ] == "passed"
    assert results_by_filename["safe_execution_request_minimal.json"][
        "expected_validation_status"
    ] == "passed"
    assert results_by_filename["blocked_db_write_request_minimal.json"][
        "actual_validation_status"
    ] == "failed"
    assert results_by_filename["blocked_db_write_request_minimal.json"][
        "expected_validation_status"
    ] == "failed"
    assert results_by_filename["blocked_application_submission_request_minimal.json"][
        "actual_validation_status"
    ] == "failed"
    assert results_by_filename["blocked_application_submission_request_minimal.json"][
        "expected_validation_status"
    ] == "failed"
    assert all(item["expected_matches_actual"] for item in results_by_filename.values())


@pytest.mark.parametrize(
    ("missing_filename", "expected_missing"),
    [
        (
            "safe_execution_request_minimal.json",
            ["safe_execution_request_minimal.json"],
        ),
        (
            "blocked_db_write_request_minimal.json",
            ["blocked_db_write_request_minimal.json"],
        ),
        (
            "blocked_application_submission_request_minimal.json",
            ["blocked_application_submission_request_minimal.json"],
        ),
    ],
)
def test_workflow_runner_blocks_missing_approved_fixture_with_temp_dir(
    tmp_path,
    monkeypatch,
    missing_filename,
    expected_missing,
):
    fixture_dir = _copy_fixture_dir(tmp_path)
    monkeypatch.setattr(orchestrator_adapter_harness, "REPO_ROOT", tmp_path / "repo")
    (fixture_dir / missing_filename).unlink()

    fixture_validation = (
        orchestrator_adapter_harness._build_fixture_validation_preflight_summary(
            fixture_dir=fixture_dir
        )
    )
    result = _run_with_fixture_validation(fixture_validation)

    assert fixture_validation["fixture_validation_missing_fixture_filenames"] == (
        expected_missing
    )
    _assert_blocked_without_execution(result, "fixture_validation_not_passed")


def test_workflow_runner_blocks_malformed_fixture_json_with_temp_dir(
    tmp_path,
    monkeypatch,
):
    fixture_dir = _copy_fixture_dir(tmp_path)
    monkeypatch.setattr(orchestrator_adapter_harness, "REPO_ROOT", tmp_path / "repo")
    (fixture_dir / "safe_execution_request_minimal.json").write_text(
        "{ malformed fixture json",
        encoding="utf-8",
    )

    fixture_validation = (
        orchestrator_adapter_harness._build_fixture_validation_preflight_summary(
            fixture_dir=fixture_dir
        )
    )
    result = _run_with_fixture_validation(fixture_validation)

    assert fixture_validation["fixture_validation_status"] == "failed"
    assert "invalid_json" in fixture_validation["fixture_validation_reason_codes"]
    _assert_blocked_without_execution(result, "fixture_validation_not_passed")


def test_workflow_runner_blocks_unexpected_extra_fixture_file_with_temp_dir(
    tmp_path,
    monkeypatch,
):
    fixture_dir = _copy_fixture_dir(tmp_path)
    monkeypatch.setattr(orchestrator_adapter_harness, "REPO_ROOT", tmp_path / "repo")
    (fixture_dir / "unexpected_extra_fixture.json").write_text(
        "{}",
        encoding="utf-8",
    )

    fixture_validation = (
        orchestrator_adapter_harness._build_fixture_validation_preflight_summary(
            fixture_dir=fixture_dir
        )
    )
    result = _run_with_fixture_validation(fixture_validation)

    assert fixture_validation["fixture_validation_unexpected_fixture_filenames"] == [
        "unexpected_extra_fixture.json"
    ]
    _assert_blocked_without_execution(result, "unexpected_fixture_file")


@pytest.mark.parametrize(
    ("field", "value", "expected_reason_code"),
    [
        (
            "fixture_validation_expected_fixture_count",
            2,
            "fixture_validation_expected_count_mismatch",
        ),
        (
            "fixture_validation_checked_count",
            2,
            "fixture_validation_checked_count_mismatch",
        ),
        (
            "fixture_validation_failed_fixture_ids",
            ["synthetic_failure"],
            "fixture_validation_failed_fixture_ids_non_empty",
        ),
        (
            "fixture_validation_status",
            "failed",
            "fixture_validation_status_not_passed",
        ),
        (
            "fixture_validation_passed",
            False,
            "fixture_validation_not_passed",
        ),
    ],
)
def test_workflow_runner_blocks_fixture_validation_summary_failure_modes(
    field,
    value,
    expected_reason_code,
):
    fixture_validation = deepcopy(_healthy_preflight_plan()["fixture_validation"])
    fixture_validation[field] = value

    result = _run_with_fixture_validation(fixture_validation)

    _assert_blocked_dry_run_steps(result, expected_reason_code)


@pytest.mark.parametrize(
    "fixture_filename",
    [
        "blocked_db_write_request_minimal.json",
        "blocked_application_submission_request_minimal.json",
        "safe_execution_request_minimal.json",
    ],
)
def test_workflow_runner_blocks_fixture_expected_actual_mismatch(fixture_filename):
    fixture_validation = _fixture_validation_with_result_mutation(
        fixture_filename,
        lambda item: item.update({"expected_matches_actual": False}),
    )

    result = _run_with_fixture_validation(fixture_validation)

    _assert_blocked_without_execution(
        result,
        f"{fixture_filename}:fixture_expected_mismatch",
    )


@pytest.mark.parametrize(
    ("field", "value", "expected_reason_code"),
    [
        ("executable_adapter_count", 1, "executable_adapter_count_nonzero"),
        ("allow_agent_execution", True, "allow_agent_execution_true"),
        ("did_execute_live", True, "did_execute_live_true"),
        ("did_mutate_production", True, "did_mutate_production_true"),
        ("did_write_db", True, "did_write_db_true"),
    ],
)
def test_workflow_runner_blocks_unsafe_preflight_fields_individually(
    field,
    value,
    expected_reason_code,
):
    preflight_plan = _healthy_preflight_plan()
    preflight_plan[field] = value

    result = workflow_runner.run_agentic_workflow_dry_run(
        preflight_plan=preflight_plan
    )

    _assert_blocked_dry_run_steps(result, expected_reason_code)


def test_workflow_runner_blocks_did_execute_count_nonzero_individually():
    preflight_plan = _healthy_preflight_plan()
    preflight_plan["summary"]["did_execute_count"] = 1

    result = workflow_runner.run_agentic_workflow_dry_run(preflight_plan=preflight_plan)

    _assert_blocked_dry_run_steps(result, "did_execute_count_nonzero")


def test_workflow_runner_non_block_conditions_accept_current_fixture_contract():
    result = workflow_runner.run_agentic_workflow_dry_run()
    results_by_filename = {
        item["fixture_filename"]: item
        for item in result["fixture_validation"]["fixture_validation_results"]
    }

    assert result["fixture_validation_gate_passed"] is True
    assert result["blocked_by_fixture_validation_gate"] is False
    assert result["fixture_validation"]["fixture_validation_failed_fixture_ids"] == []
    assert result["executable_adapter_count"] == 0
    assert result["allow_agent_execution"] is False
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False
    assert results_by_filename["blocked_db_write_request_minimal.json"][
        "expected_matches_actual"
    ] is True
    assert results_by_filename["blocked_application_submission_request_minimal.json"][
        "expected_matches_actual"
    ] is True
    assert results_by_filename["safe_execution_request_minimal.json"][
        "expected_matches_actual"
    ] is True


def test_workflow_runner_bad_fixture_validation_summary_blocks_without_execution():
    result = workflow_runner.run_agentic_workflow_dry_run(
        preflight_plan={
            "fixture_validation": {
                "fixture_validation_passed": False,
                "fixture_validation_status": "failed",
                "fixture_validation_checked_count": 0,
                "fixture_validation_expected_fixture_count": 3,
                "fixture_validation_failed_fixture_ids": ["missing_fixture"],
                "fixture_validation_unexpected_fixture_filenames": [],
                "fixture_validation_results": [],
            },
            "executable_adapter_count": 0,
            "allow_agent_execution": False,
            "did_execute_live": False,
            "did_mutate_production": False,
            "did_write_db": False,
            "summary": {"did_execute_count": 0},
        }
    )

    assert result["blocked_by_fixture_validation_gate"] is True
    assert result["fixture_validation_gate_passed"] is False
    assert result["fixture_validation_gate_status"] == "failed"
    assert "fixture_validation_not_passed" in result["fixture_validation_gate_reason_codes"]
    assert "fixture_validation_failed_fixture_ids_non_empty" in result[
        "fixture_validation_gate_reason_codes"
    ]
    assert "approved_fixture_missing_from_results" in result[
        "fixture_validation_gate_reason_codes"
    ]
    assert result["validation"]["validation_status"] == "failed"
    assert "fixture_validation_gate_failed" in result["validation"]["reason_codes"]
    assert result["executed_step_count"] == 0
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False
    assert all(step["did_execute"] is False for step in result["ordered_step_results"])


def test_workflow_runner_missing_fixture_validation_summary_blocks_without_execution():
    result = workflow_runner.run_agentic_workflow_dry_run(
        preflight_plan={
            "executable_adapter_count": 0,
            "allow_agent_execution": False,
            "did_execute_live": False,
            "did_mutate_production": False,
            "did_write_db": False,
            "summary": {"did_execute_count": 0},
        }
    )

    assert result["blocked_by_fixture_validation_gate"] is True
    assert "missing_fixture_validation_summary" in result[
        "fixture_validation_gate_reason_codes"
    ]
    assert result["executed_step_count"] == 0
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False


def test_workflow_runner_unsafe_preflight_safety_fields_block_without_execution():
    healthy = workflow_runner.run_agentic_workflow_dry_run()
    preflight_plan = {
        "fixture_validation": healthy["fixture_validation"],
        "executable_adapter_count": 1,
        "allow_agent_execution": True,
        "did_execute_live": True,
        "did_mutate_production": True,
        "did_write_db": True,
        "summary": {"did_execute_count": 1},
    }

    result = workflow_runner.run_agentic_workflow_dry_run(preflight_plan=preflight_plan)

    assert result["blocked_by_fixture_validation_gate"] is True
    assert "executable_adapter_count_nonzero" in result[
        "fixture_validation_gate_reason_codes"
    ]
    assert "allow_agent_execution_true" in result["fixture_validation_gate_reason_codes"]
    assert "did_execute_count_nonzero" in result["fixture_validation_gate_reason_codes"]
    assert "did_execute_live_true" in result["fixture_validation_gate_reason_codes"]
    assert "did_mutate_production_true" in result["fixture_validation_gate_reason_codes"]
    assert "did_write_db_true" in result["fixture_validation_gate_reason_codes"]
    assert result["executed_step_count"] == 0
    assert all(step["did_execute"] is False for step in result["ordered_step_results"])


def test_workflow_runner_never_executes_steps_in_dry_run():
    result = workflow_runner.run_agentic_workflow_dry_run()

    assert result["executed_step_count"] == 0
    assert result["skipped_step_count"] == 6
    for step in result["ordered_step_results"]:
        assert step["did_execute"] is False
        assert step["execution_enabled"] is False
        assert step["execution_status"] == "skipped_dry_run"
        assert "dry_run_only" in step["reason_codes"]
        assert "agent_execution_disabled" in step["reason_codes"]


def test_workflow_runner_context_reports_input_artifact_presence():
    context = workflow_runner.build_agentic_workflow_run_context(
        input_artifacts_present=[
            "application_execution_queue.csv",
            "source_health_report.csv",
        ],
        feature_flags_snapshot={"APPLYLENS_AGENT_TRACE_ENABLED": True},
        created_at_utc="2026-01-01T00:00:00+00:00",
    )

    assert context["execution_mode"] == "dry_run"
    assert context["created_at_utc"] == "2026-01-01T00:00:00+00:00"
    assert "application_execution_queue.csv" in context["input_artifacts_present"]
    assert "best_resume_variant_by_job.csv" in context["input_artifacts_missing"]
    assert context["feature_flags_snapshot"]["APPLYLENS_AGENT_TRACE_ENABLED"] is True


def test_workflow_runner_would_trace_reflects_trace_flag_snapshot():
    result = workflow_runner.run_agentic_workflow_dry_run(
        env={"APPLYLENS_AGENT_TRACE_ENABLED": "1"},
    )

    assert result["summary"]["would_trace_step_count"] == 6
    assert all(step["would_trace"] is True for step in result["ordered_step_results"])


def test_workflow_runner_validation_passes_for_normal_dry_run():
    result = workflow_runner.run_agentic_workflow_dry_run()
    validation = workflow_runner.validate_agentic_workflow_dry_run_result(result)

    assert result["validation"]["validation_status"] == "passed"
    assert validation["validation_status"] == "passed"
    assert validation["reason_codes"] == []
    assert validation["expected_order"] == EXPECTED_AGENT_KEYS
    assert validation["actual_order"] == EXPECTED_AGENT_KEYS


def test_workflow_runner_validation_catches_accidental_executed_step():
    result = workflow_runner.run_agentic_workflow_dry_run()
    result["executed_step_count"] = 1
    result["ordered_step_results"][0]["did_execute"] = True

    validation = workflow_runner.validate_agentic_workflow_dry_run_result(result)

    assert validation["validation_status"] == "failed"
    assert "executed_step_count_nonzero" in validation["reason_codes"]
    assert "source_health:did_execute" in validation["reason_codes"]


def test_workflow_runner_validation_catches_execution_enabled_step():
    result = workflow_runner.run_agentic_workflow_dry_run()
    result["ordered_step_results"][0]["execution_enabled"] = True

    validation = workflow_runner.validate_agentic_workflow_dry_run_result(result)

    assert validation["validation_status"] == "failed"
    assert "source_health:execution_enabled" in validation["reason_codes"]


def test_workflow_runner_validation_catches_wrong_status():
    result = workflow_runner.run_agentic_workflow_dry_run()
    result["ordered_step_results"][0]["execution_status"] = "planned"

    validation = workflow_runner.validate_agentic_workflow_dry_run_result(result)

    assert validation["validation_status"] == "failed"
    assert "source_health:execution_status_not_skipped_dry_run" in validation["reason_codes"]


def test_workflow_runner_markdown_report_includes_all_agents():
    markdown = workflow_runner.render_agentic_workflow_dry_run_report_markdown()

    assert "# Agentic Workflow Dry-Run Report" in markdown
    assert "Executed step count: `0`" in markdown
    for agent_name in [
        "Resume Match Agent",
        "Source Health Agent",
        "Critic Agent",
        "Job Prioritization Agent",
        "Tailoring Decision Agent",
        "Operator Review Agent",
    ]:
        assert agent_name in markdown


def test_workflow_runner_writes_dry_run_artifacts(tmp_path):
    result = workflow_runner.write_agentic_workflow_dry_run_artifacts(output_dir=tmp_path)

    json_path = tmp_path / "agentic_workflow_dry_run_result.json"
    md_path = tmp_path / "agentic_workflow_dry_run_report.md"
    payload = json.loads(json_path.read_text(encoding="utf-8"))

    assert result["validation_status"] == "passed"
    assert payload["executed_step_count"] == 0
    assert json_path.exists()
    assert md_path.exists()
    assert "# Agentic Workflow Dry-Run Report" in md_path.read_text(encoding="utf-8")


def test_workflow_runner_cli_dry_run_json_returns_success(capsys):
    exit_code = workflow_runner.main(["--dry-run", "--json"])
    output = capsys.readouterr().out

    assert exit_code == 0
    assert '"execution_mode": "dry_run"' in output
    assert '"executed_step_count": 0' in output
