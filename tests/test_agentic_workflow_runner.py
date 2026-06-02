import json

from src.agents import workflow_runner


EXPECTED_AGENT_KEYS = [
    "source_health",
    "resume_match",
    "critic",
    "job_prioritization",
    "tailoring_decision",
    "operator_review",
]


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
