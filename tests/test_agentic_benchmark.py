import json
import tempfile
from pathlib import Path

from src.evaluation import agentic_benchmark


def test_agentic_benchmark_fixture_loads_sanitized_cases():
    fixture = agentic_benchmark.load_benchmark_fixture()

    assert fixture["benchmark_name"] == "agentic_phase_4a_sanitized_v1"
    assert len(fixture["cases"]) == 6
    assert len(fixture["source_health_rows"]) == 5
    assert len(fixture["selector_rows"]) == 3
    assert len(fixture["critic_cases"]) == 4
    assert len(fixture["job_priority_rows"]) == 6
    assert len(fixture["tailoring_decision_rows"]) == 6
    assert len(fixture["operator_review_rows"]) == 6
    serialized = json.dumps(fixture).lower()
    assert "sriram" not in serialized
    assert "swatika" not in serialized
    assert "profile_resumes" not in serialized


def test_agentic_benchmark_metrics_compute_expected_values():
    result = agentic_benchmark.run_benchmark()

    assert result["benchmark_case_count"] == 6
    assert result["source_health_recommendation_accuracy"] == 1.0
    assert result["fallback_only_block_rate"] == 1.0
    assert result["deterministic_match_allow_rate"] == 1.0
    assert result["low_confidence_block_rate"] == 1.0
    assert result["critic_unsupported_claim_rejection_rate"] == 1.0
    assert result["critic_safe_suggestion_approval_rate"] == 1.0
    assert result["critic_downgrade_rate"] == 1.0
    assert result["job_priority_accuracy"] == 1.0
    assert result["fallback_only_skip_rate"] == 1.0
    assert result["high_score_apply_rate"] == 1.0
    assert result["packet_block_skip_rate"] == 1.0
    assert result["tailoring_decision_accuracy"] == 1.0
    assert result["fallback_only_do_not_tailor_rate"] == 1.0
    assert result["critic_reject_do_not_tailor_rate"] == 1.0
    assert result["high_score_light_tailoring_rate"] == 1.0
    assert result["operator_review_accuracy"] == 1.0
    assert result["ready_to_apply_precision"] == 1.0
    assert result["hold_or_skip_block_rate"] == 1.0
    assert result["critic_reject_hold_rate"] == 1.0
    assert result["llmops_metadata_schema_present"] == 1.0
    assert result["llmops_required_keys_present"] == 1.0
    assert result["validation_pass_rate"] == 1.0
    assert result["failed_case_ids"] == []
    assert "generated_at_utc" in result["summary_json"]
    assert set(result["summary_json"]["metrics"]) == {
        "benchmark_case_count",
        "source_health_recommendation_accuracy",
        "fallback_only_block_rate",
        "deterministic_match_allow_rate",
        "low_confidence_block_rate",
        "critic_unsupported_claim_rejection_rate",
        "critic_safe_suggestion_approval_rate",
        "critic_downgrade_rate",
        "job_priority_accuracy",
        "fallback_only_skip_rate",
        "high_score_apply_rate",
        "packet_block_skip_rate",
        "tailoring_decision_accuracy",
        "fallback_only_do_not_tailor_rate",
        "critic_reject_do_not_tailor_rate",
        "high_score_light_tailoring_rate",
        "operator_review_accuracy",
        "ready_to_apply_precision",
        "hold_or_skip_block_rate",
        "critic_reject_hold_rate",
        "llmops_metadata_schema_present",
        "llmops_required_keys_present",
        "validation_pass_rate",
        "failed_case_ids",
    }


def test_agentic_benchmark_source_health_recommendation_rules_score_correctly():
    fixture = agentic_benchmark.load_benchmark_fixture()
    evaluation = agentic_benchmark.evaluate_source_health_rows(fixture["source_health_rows"])
    recommendations = {
        item["company"]: item["recommendation"]
        for item in evaluation["payload"]["output"]["recommendations"]
    }

    assert recommendations["example-scale"] == "promote"
    assert recommendations["field-example"] == "keep"
    assert recommendations["detail-needed-example"] == "needs_detail_enrichment"
    assert recommendations["timestamp-example"] == "needs_timestamp_fix"
    assert recommendations["stale-example"] == "demote"
    assert evaluation["accuracy"] == 1.0


def test_agentic_benchmark_resume_credibility_guards():
    fixture = agentic_benchmark.load_benchmark_fixture()
    evaluation = agentic_benchmark.evaluate_resume_selector_rows(fixture["selector_rows"])

    assert evaluation["fallback_only_block_rate"] == 1.0
    assert evaluation["deterministic_match_allow_rate"] == 1.0
    assert evaluation["low_confidence_block_rate"] == 1.0
    assert evaluation["validation"]["validation_status"] == "passed"


def test_agentic_benchmark_critic_metrics_are_included():
    fixture = agentic_benchmark.load_benchmark_fixture()
    evaluation = agentic_benchmark.evaluate_critic_cases(fixture["critic_cases"])
    decisions = {
        output["suggestion_id"]: output["decision"]
        for output in evaluation["outputs"]
    }

    assert decisions["critic_supported_patch"] == "approve"
    assert decisions["critic_unsupported_tool"] == "reject"
    assert decisions["critic_unsupported_metric"] == "reject"
    assert decisions["critic_guidance_only"] == "downgrade_to_guidance"
    assert evaluation["critic_unsupported_claim_rejection_rate"] == 1.0
    assert evaluation["critic_safe_suggestion_approval_rate"] == 1.0
    assert evaluation["critic_downgrade_rate"] == 1.0
    assert evaluation["summary"]["agent_name"] == "Critic Agent"


def test_agentic_benchmark_job_prioritization_metrics_are_included():
    fixture = agentic_benchmark.load_benchmark_fixture()
    evaluation = agentic_benchmark.evaluate_job_priority_rows(fixture["job_priority_rows"])
    priorities = {
        item["job_id"]: item["advisory_priority"]
        for item in evaluation["payload"]["output"]["recommendations"]
    }

    assert priorities["priority_fallback_only"] == "skip_for_now"
    assert priorities["priority_packet_blocked"] == "skip_for_now"
    assert priorities["priority_manual_review"] == "manual_review"
    assert priorities["priority_tailor_first"] == "tailor_first"
    assert priorities["priority_apply_now"] == "apply_now"
    assert priorities["priority_watch_source"] == "watch_source"
    assert evaluation["accuracy"] == 1.0
    assert evaluation["fallback_only_skip_rate"] == 1.0
    assert evaluation["high_score_apply_rate"] == 1.0
    assert evaluation["packet_block_skip_rate"] == 1.0
    assert evaluation["payload"]["summary"]["agent_name"] == "Job Prioritization Agent"


def test_agentic_benchmark_tailoring_decision_metrics_are_included():
    fixture = agentic_benchmark.load_benchmark_fixture()
    evaluation = agentic_benchmark.evaluate_tailoring_decision_rows(
        fixture["tailoring_decision_rows"]
    )
    decisions = {
        item["job_id"]: item["tailoring_decision"]
        for item in evaluation["payload"]["output"]["decisions"]
    }

    assert decisions["tailoring_fallback_only"] == "do_not_tailor"
    assert decisions["tailoring_critic_reject"] == "do_not_tailor"
    assert decisions["tailoring_manual_review"] == "manual_review_before_tailoring"
    assert decisions["tailoring_tailor_first"] == "tailor_before_apply"
    assert decisions["tailoring_light"] == "light_tailoring"
    assert decisions["tailoring_no_needed"] == "no_tailoring_needed"
    assert evaluation["accuracy"] == 1.0
    assert evaluation["fallback_only_do_not_tailor_rate"] == 1.0
    assert evaluation["critic_reject_do_not_tailor_rate"] == 1.0
    assert evaluation["high_score_light_tailoring_rate"] == 1.0
    assert evaluation["payload"]["summary"]["agent_name"] == "Tailoring Decision Agent"


def test_agentic_benchmark_operator_review_metrics_are_included():
    fixture = agentic_benchmark.load_benchmark_fixture()
    evaluation = agentic_benchmark.evaluate_operator_review_rows(
        fixture["operator_review_rows"]
    )
    lanes = {
        item["job_id"]: item["operator_review_lane"]
        for item in evaluation["payload"]["output"]["reviews"]
    }

    assert lanes["operator_fallback_only"] == "hold_or_skip"
    assert lanes["operator_critic_reject"] == "hold_or_skip"
    assert lanes["operator_packet_review"] == "review_before_action"
    assert lanes["operator_ready"] == "ready_to_apply"
    assert lanes["operator_tailor"] == "tailor_then_apply"
    assert lanes["operator_source_watch"] == "source_watch"
    assert evaluation["accuracy"] == 1.0
    assert evaluation["ready_to_apply_precision"] == 1.0
    assert evaluation["hold_or_skip_block_rate"] == 1.0
    assert evaluation["critic_reject_hold_rate"] == 1.0
    assert evaluation["payload"]["summary"]["agent_name"] == "Operator Review Agent"


def test_agentic_benchmark_report_rendering_and_output_paths_are_stable():
    result = agentic_benchmark.run_benchmark()
    result["thresholds"] = agentic_benchmark.evaluate_thresholds(result)
    report = agentic_benchmark.render_markdown_report(result)

    assert "# Agentic Benchmark Report" in report
    assert "Generated at UTC" in report
    assert "source_health_recommendation_accuracy" in report
    assert "## Failed Case IDs" in report
    assert "## Interpretation" in report
    assert "All configured regression thresholds passed." in report
    assert "Resume Match Agent credibility benchmark" in report
    assert "Critic Agent suggestion validation benchmark" in report
    assert "Job Prioritization Agent advisory benchmark" in report
    assert "Tailoring Decision Agent advisory benchmark" in report
    assert "Operator Review Agent advisory benchmark" in report
    assert "LLMOps metadata schema readiness benchmark" in report

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_files = agentic_benchmark.write_benchmark_outputs(result, tmp_dir)

        assert Path(output_files["summary_json"]).name == "agentic_benchmark_summary.json"
        assert Path(output_files["results_csv"]).name == "agentic_benchmark_results.csv"
        assert Path(output_files["report_md"]).name == "agentic_benchmark_report.md"
        assert Path(output_files["summary_json"]).exists()
        assert Path(output_files["results_csv"]).exists()
        assert Path(output_files["report_md"]).exists()


def test_agentic_benchmark_cli_no_write_returns_success(capsys):
    exit_code = agentic_benchmark.main(["--no-write", "--print-summary"])

    captured = capsys.readouterr()
    assert exit_code == 0
    assert "agentic_phase_4a_sanitized_v1" in captured.out
    assert "source_health_recommendation_accuracy" in captured.out


def test_agentic_benchmark_cli_write_mode_writes_files(tmp_path):
    exit_code = agentic_benchmark.main(["--write", "--output-dir", str(tmp_path)])

    assert exit_code == 0
    assert (tmp_path / "agentic_benchmark_summary.json").exists()
    assert (tmp_path / "agentic_benchmark_results.csv").exists()
    assert (tmp_path / "agentic_benchmark_report.md").exists()


def test_agentic_benchmark_cli_threshold_failure_returns_nonzero(capsys):
    exit_code = agentic_benchmark.main([
        "--no-write",
        "--min-validation-pass-rate",
        "1.01",
    ])

    captured = capsys.readouterr()
    assert exit_code == 1
    assert "validation_pass_rate" in captured.err
