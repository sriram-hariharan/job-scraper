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
    assert result["validation_pass_rate"] == 1.0
    assert result["failed_case_ids"] == []


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


def test_agentic_benchmark_report_rendering_and_output_paths_are_stable():
    result = agentic_benchmark.run_benchmark()
    report = agentic_benchmark.render_markdown_report(result)

    assert "# Agentic Benchmark Report" in report
    assert "source_health_recommendation_accuracy" in report
    assert "Resume Match Agent credibility benchmark" in report

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_files = agentic_benchmark.write_benchmark_outputs(result, tmp_dir)

        assert Path(output_files["summary_json"]).name == "agentic_benchmark_summary.json"
        assert Path(output_files["results_csv"]).name == "agentic_benchmark_results.csv"
        assert Path(output_files["report_md"]).name == "agentic_benchmark_report.md"
        assert Path(output_files["summary_json"]).exists()
        assert Path(output_files["results_csv"]).exists()
        assert Path(output_files["report_md"]).exists()
