import csv
import json

from src.agents.workflow_verifier import (
    main,
    verify_agentic_workflow_artifacts,
    write_agentic_workflow_verification_artifact,
)


def _write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fieldnames})


def _write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def _complete_artifact_dir(tmp_path, *, operator_rows=None, summary_counts=None):
    root = tmp_path / "run"
    queue_rows = [
        {
            "job_doc_id": "job_1",
            "job_company": "Acme",
            "job_title": "Backend Engineer",
            "action": "APPLY",
            "fallback_only_no_deterministic_match": "false",
            "packet_generation_allowed": "true",
        },
        {
            "job_doc_id": "job_2",
            "job_company": "Beta",
            "job_title": "ML Engineer",
            "action": "SKIP_FOR_NOW",
            "fallback_only_no_deterministic_match": "true",
            "packet_generation_allowed": "false",
            "packet_generation_block_reason": "fallback_only_no_deterministic_match",
        },
    ]
    operator_rows = operator_rows or [
        {
            "job_id": "job_1",
            "company": "Acme",
            "title": "Backend Engineer",
            "existing_action": "APPLY",
            "operator_review_lane": "ready_to_apply",
            "fallback_only_no_deterministic_match": "false",
            "packet_generation_allowed": "true",
        },
        {
            "job_id": "job_2",
            "company": "Beta",
            "title": "ML Engineer",
            "existing_action": "SKIP_FOR_NOW",
            "operator_review_lane": "hold_or_skip",
            "fallback_only_no_deterministic_match": "true",
            "packet_generation_allowed": "false",
            "packet_generation_block_reason": "fallback_only_no_deterministic_match",
        },
    ]
    summary_counts = summary_counts or {"hold_or_skip": 1, "ready_to_apply": 1}

    _write_csv(
        root / "application_execution_queue.csv",
        queue_rows,
        [
            "job_doc_id",
            "job_company",
            "job_title",
            "action",
            "fallback_only_no_deterministic_match",
            "packet_generation_allowed",
            "packet_generation_block_reason",
        ],
    )
    _write_csv(root / "best_resume_variant_by_job.csv", [{"job_id": "job_1"}], ["job_id"])
    _write_csv(
        root / "source_health_report.csv",
        [{"source": "greenhouse", "company": "scaleai", "scraped_jobs": "1"}],
        ["source", "company", "scraped_jobs"],
    )
    _write_csv(
        root / "job_prioritization_recommendations.csv",
        [
            {"job_id": "job_1", "company": "Acme", "title": "Backend Engineer", "existing_action": "APPLY", "advisory_priority": "apply_now"},
            {"job_id": "job_2", "company": "Beta", "title": "ML Engineer", "existing_action": "SKIP_FOR_NOW", "advisory_priority": "skip_for_now"},
        ],
        ["job_id", "company", "title", "existing_action", "advisory_priority"],
    )
    _write_csv(
        root / "tailoring_decision_recommendations.csv",
        [
            {"job_id": "job_1", "company": "Acme", "title": "Backend Engineer", "existing_action": "APPLY", "tailoring_decision": "light_tailoring"},
            {"job_id": "job_2", "company": "Beta", "title": "ML Engineer", "existing_action": "SKIP_FOR_NOW", "tailoring_decision": "do_not_tailor"},
        ],
        ["job_id", "company", "title", "existing_action", "tailoring_decision"],
    )
    _write_json(root / "tailoring_decision_summary.json", {"row_count": 2})
    _write_csv(
        root / "operator_review_recommendations.csv",
        operator_rows,
        [
            "job_id",
            "company",
            "title",
            "existing_action",
            "operator_review_lane",
            "fallback_only_no_deterministic_match",
            "packet_generation_allowed",
            "packet_generation_block_reason",
        ],
    )
    _write_json(root / "operator_review_summary.json", {"row_count": 2})
    _write_json(
        root / "agentic_workflow_summary.json",
        {"operator_review_lane_counts": summary_counts, "total_queue_jobs": 2},
    )
    (root / "agentic_workflow_summary.md").write_text("# Agentic Workflow Summary\n", encoding="utf-8")
    return root


def test_workflow_verifier_passes_with_complete_fake_artifact_folder(tmp_path):
    root = _complete_artifact_dir(tmp_path)

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    assert payload["validation_status"] == "passed"
    assert payload["missing_artifacts"] == []
    assert payload["row_counts"]["operator_review_recommendations"] == 2


def test_workflow_verifier_warns_with_missing_optional_artifacts_non_strict(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    (root / "best_resume_variant_by_job.csv").unlink()
    (root / "source_health_report.csv").unlink()

    payload = verify_agentic_workflow_artifacts(output_dir=root, strict=False)

    assert payload["validation_status"] == "warning"
    assert "best_resume_variant_by_job.csv" in payload["missing_artifacts"]
    assert "source_health_report.csv" in payload["missing_artifacts"]
    assert "missing_optional_artifacts" in payload["reason_codes"]


def test_workflow_verifier_fails_missing_required_artifacts_in_strict_mode(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    (root / "operator_review_recommendations.csv").unlink()

    payload = verify_agentic_workflow_artifacts(output_dir=root, strict=True)

    assert payload["validation_status"] == "failed"
    assert "operator_review_recommendations.csv" in payload["missing_artifacts"]
    assert "missing_required_artifacts" in payload["reason_codes"]


def test_workflow_verifier_detects_summary_count_mismatch(tmp_path):
    root = _complete_artifact_dir(tmp_path, summary_counts={"ready_to_apply": 2})

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    assert payload["validation_status"] == "failed"
    assert "workflow_summary_operator_count_mismatch" in payload["reason_codes"]


def test_workflow_verifier_detects_ready_to_apply_fallback_only_bug(tmp_path):
    root = _complete_artifact_dir(
        tmp_path,
        operator_rows=[
            {
                "job_id": "job_2",
                "company": "Beta",
                "title": "ML Engineer",
                "existing_action": "SKIP_FOR_NOW",
                "operator_review_lane": "ready_to_apply",
                "fallback_only_no_deterministic_match": "true",
                "packet_generation_allowed": "false",
                "packet_generation_block_reason": "fallback_only_no_deterministic_match",
            }
        ],
        summary_counts={"ready_to_apply": 1},
    )

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    assert payload["validation_status"] == "failed"
    assert "fallback_only_ready_to_apply" in payload["reason_codes"]
    assert "packet_blocked_ready_to_apply" in payload["reason_codes"]


def test_workflow_verifier_cli_non_strict_returns_success_on_temp_fixture(tmp_path):
    root = _complete_artifact_dir(tmp_path)

    assert main(["--output-dir", str(root), "--json"]) == 0


def test_workflow_verifier_writes_warning_artifact_for_missing_optional_files(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    (root / "best_resume_variant_by_job.csv").unlink()

    result = write_agentic_workflow_verification_artifact(output_dir=root)
    payload = json.loads((root / "agentic_workflow_verification.json").read_text(encoding="utf-8"))

    assert result["validation_status"] == "warning"
    assert payload["validation_status"] == "warning"
    assert "best_resume_variant_by_job.csv" in payload["missing_artifacts"]
