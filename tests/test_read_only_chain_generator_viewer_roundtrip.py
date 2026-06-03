import json
from pathlib import Path

from src.agents import (
    orchestrator_adapter_harness,
    read_only_chain_artifact_generator,
    workflow_runner,
)
from src.agents.workflow_verifier import verify_agentic_workflow_artifacts
from src.app import services


SMOKE_FIXTURE_PATH = Path("tests/fixtures/agentic_read_only_chain_smoke/application_execution_queue.csv")
PRODUCTION_ROOT_NAMES = {
    "application_execution_queue.csv",
    "job_prioritization_recommendations.csv",
    "tailoring_decision_recommendations.csv",
    "operator_review_recommendations.csv",
}


def _artifact_row(path: Path, artifact_name: str | None = None) -> dict:
    name = artifact_name or path.name
    text = path.read_text(encoding="utf-8")
    content_json = {}
    if name.endswith(".json"):
        content_json = json.loads(text)
    return {
        "artifact_name": name,
        "artifact_kind": services._pipeline_artifact_kind(output_dir=path.parent, path=path),
        "content_text": text,
        "content_json": content_json,
    }


def _text_artifact_row(artifact_name: str, content_text: str, content_json: dict | None = None) -> dict:
    return {
        "artifact_name": artifact_name,
        "artifact_kind": artifact_name.rsplit(".", 1)[0],
        "content_text": content_text,
        "content_json": dict(content_json or {}),
    }


def _required_verifier_artifact_rows() -> list[dict]:
    return [
        _text_artifact_row(
            "application_execution_queue.csv",
            "\n".join(
                [
                    "job_id,company,title,action,fallback_only_no_deterministic_match,packet_generation_allowed,packet_generation_block_reason",
                    "fake_job_001,Example Systems Lab,Backend Platform Engineer,APPLY,false,true,",
                    "",
                ]
            ),
        ),
        _text_artifact_row(
            "job_prioritization_recommendations.csv",
            "\n".join(
                [
                    "job_id,company,title,existing_action,advisory_priority",
                    "fake_job_001,Example Systems Lab,Backend Platform Engineer,APPLY,apply_now",
                    "",
                ]
            ),
        ),
        _text_artifact_row(
            "tailoring_decision_recommendations.csv",
            "\n".join(
                [
                    "job_id,company,title,existing_action,tailoring_decision",
                    "fake_job_001,Example Systems Lab,Backend Platform Engineer,APPLY,no_tailoring_needed",
                    "",
                ]
            ),
        ),
        _text_artifact_row(
            "tailoring_decision_summary.json",
            json.dumps({"row_count": 1}),
            {"row_count": 1},
        ),
        _text_artifact_row(
            "operator_review_recommendations.csv",
            "\n".join(
                [
                    "job_id,company,title,existing_action,operator_review_lane,fallback_only_no_deterministic_match,packet_generation_allowed,packet_generation_block_reason",
                    "fake_job_001,Example Systems Lab,Backend Platform Engineer,APPLY,ready_to_apply,false,true,",
                    "",
                ]
            ),
        ),
        _text_artifact_row(
            "operator_review_summary.json",
            json.dumps({"row_count": 1}),
            {"row_count": 1},
        ),
        _text_artifact_row(
            "agentic_workflow_summary.json",
            json.dumps({"operator_review_lane_counts": {"ready_to_apply": 1}, "total_queue_jobs": 1}),
            {"operator_review_lane_counts": {"ready_to_apply": 1}, "total_queue_jobs": 1},
        ),
        _text_artifact_row(
            "agentic_workflow_summary.md",
            "# Agentic Workflow Summary\n",
        ),
    ]


def test_explicit_generator_artifacts_roundtrip_to_verifier_and_agentic_review_read_models(tmp_path):
    result = read_only_chain_artifact_generator.generate_read_only_chain_artifacts(
        queue_input_artifact_path=SMOKE_FIXTURE_PATH,
        output_dir=tmp_path,
        pipeline_run_id="roundtrip_smoke",
        owner_user_id="roundtrip_user",
    )

    assert result["execution_mode"] == "explicit_operator_read_only_chain_artifact_generation"
    assert result["did_run_chain"] is True
    assert result["did_mutate_production"] is False
    assert result["require_explicit_input"] is True
    assert result["require_explicit_output_dir"] is True
    assert result["allow_live_pipeline_wiring"] is False
    assert result["allow_application_submission"] is False
    assert result["validation"]["validation_status"] == "passed"

    root_files = {path.name for path in tmp_path.iterdir() if path.is_file()}
    assert "read_only_adapter_chain_result.json" in root_files
    assert "read_only_adapter_chain_report.md" in root_files
    assert "read_only_chain_artifact_generation_result.json" in root_files
    assert "read_only_chain_artifact_generation_report.md" in root_files
    assert not root_files.intersection(PRODUCTION_ROOT_NAMES)

    generated_rows = [
        _artifact_row(tmp_path / "read_only_adapter_chain_result.json"),
        _artifact_row(tmp_path / "read_only_adapter_chain_report.md"),
        _artifact_row(tmp_path / "read_only_chain_artifact_generation_result.json"),
        _artifact_row(tmp_path / "read_only_chain_artifact_generation_report.md"),
    ]
    artifact_rows = _required_verifier_artifact_rows() + generated_rows

    verification = verify_agentic_workflow_artifacts(artifact_rows=artifact_rows, strict=False)
    check_names = {check["name"] for check in verification["consistency_checks"]}
    failed_checks = {
        check["name"]
        for check in verification["consistency_checks"]
        if not check["passed"]
    }
    assert verification["validation_status"] == "warning"
    assert "missing_optional_artifacts" in verification["reason_codes"]
    assert "read_only_chain_artifact_generation_validation_failed" not in verification["reason_codes"]
    assert "read_only_adapter_chain_validation_failed" not in verification["reason_codes"]
    assert failed_checks == set()
    assert "read_only_chain_artifact_generation_validation_passed_or_warning" in check_names
    assert "read_only_chain_artifact_generation_explicit_operator_mode" in check_names
    assert "read_only_chain_artifact_generation_did_not_mutate_production" in check_names
    assert "read_only_chain_artifact_generation_no_production_root_artifact_names" in check_names

    chain_read_model = services._manual_read_only_adapter_chain_from_artifacts(generated_rows)
    generator_read_model = services._explicit_read_only_chain_artifact_generation_from_artifacts(generated_rows)
    assert chain_read_model["present"] is True
    assert chain_read_model["summary"]["adapters_executed_count"] == 3
    assert generator_read_model["present"] is True
    assert generator_read_model["did_run_chain"] is True
    assert generator_read_model["did_mutate_production"] is False
    assert generator_read_model["chain_result_summary"]["adapters_executed_count"] == 3

    review_js = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    assert "Manual Read-Only Adapter Chain" in review_js
    assert "Explicit Read-Only Chain Generator" in review_js

    preflight = orchestrator_adapter_harness.build_read_only_adapter_preflight_plan()
    assert preflight["executable_adapter_count"] == 0
    assert all(result["did_execute"] is False for result in preflight["adapter_preflight_results"])

    dry_run = workflow_runner.run_agentic_workflow_dry_run()
    assert dry_run["execution_mode"] == "dry_run"
    assert dry_run["executed_step_count"] == 0
    assert all(step["did_execute"] is False for step in dry_run["ordered_step_results"])
