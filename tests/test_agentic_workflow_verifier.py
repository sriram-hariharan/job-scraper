import csv
import json

from src.agents.workflow_verifier import (
    main,
    verify_agentic_workflow_artifacts,
    write_agentic_workflow_verification_artifact,
)
from src.agents.read_only_chain_artifact_generator import generate_read_only_chain_artifacts
from src.agents.read_only_adapter_chain import write_read_only_adapter_chain_artifacts
from src.agents.orchestrator_adapter_harness import write_read_only_adapter_preflight_artifacts
from src.agents.workflow_planner import write_agentic_workflow_execution_plan_artifacts
from src.agents.workflow_registry import write_agentic_workflow_manifest_artifacts
from src.agents.workflow_runner import write_agentic_workflow_dry_run_artifacts
from src.evaluation.rag_evaluation import write_rag_evaluation_artifacts


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
    write_agentic_workflow_manifest_artifacts(output_dir=root)
    write_agentic_workflow_execution_plan_artifacts(output_dir=root)
    write_agentic_workflow_dry_run_artifacts(output_dir=root)
    write_read_only_adapter_preflight_artifacts(output_dir=root)
    write_read_only_adapter_chain_artifacts(
        output_dir=root,
        queue_rows=queue_rows,
        pipeline_run_id="run_test",
        owner_user_id="user_test",
    )
    generator_output_dir = root / "explicit_generator_output"
    generate_read_only_chain_artifacts(
        queue_input_artifact_path=root / "application_execution_queue.csv",
        output_dir=generator_output_dir,
        pipeline_run_id="run_test",
        owner_user_id="user_test",
    )
    for artifact_name in [
        "read_only_chain_artifact_generation_result.json",
        "read_only_chain_artifact_generation_report.md",
    ]:
        (root / artifact_name).write_text(
            (generator_output_dir / artifact_name).read_text(encoding="utf-8"),
            encoding="utf-8",
        )
    write_rag_evaluation_artifacts(
        output_dir=root,
        rows=[
            {
                "query_id": "q1",
                "query_text": "backend engineer",
                "retrieved_doc_id": "job_1",
                "retrieval_score": 0.8,
                "rank": 1,
            }
        ],
        pipeline_run_id="run_test",
        owner_user_id="user_test",
    )
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
    (root / "rag_evaluation_summary.json").unlink()
    (root / "rag_evaluation_report.md").unlink()

    payload = verify_agentic_workflow_artifacts(output_dir=root, strict=False)

    assert payload["validation_status"] == "warning"
    assert "best_resume_variant_by_job.csv" in payload["missing_artifacts"]
    assert "source_health_report.csv" in payload["missing_artifacts"]
    assert "rag_evaluation_summary.json" in payload["missing_artifacts"]
    assert "missing_optional_artifacts" in payload["reason_codes"]


def test_workflow_verifier_warns_when_rag_evaluation_missing_non_strict(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    (root / "rag_evaluation_summary.json").unlink()
    (root / "rag_evaluation_report.md").unlink()

    payload = verify_agentic_workflow_artifacts(output_dir=root, strict=False)

    assert payload["validation_status"] == "warning"
    assert "rag_evaluation_summary.json" in payload["missing_artifacts"]
    assert "missing_optional_artifacts" in payload["reason_codes"]


def test_workflow_verifier_validates_read_only_adapter_preflight_when_present(tmp_path):
    root = _complete_artifact_dir(tmp_path)

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    check_names = {check["name"] for check in payload["consistency_checks"]}
    assert payload["validation_status"] == "passed"
    assert "read_only_adapter_preflight_validation_passed_or_warning" in check_names
    assert "read_only_adapter_preflight_mode" in check_names
    assert "read_only_adapter_preflight_agent_execution_disallowed" in check_names
    assert "read_only_adapter_preflight_executable_count_zero" in check_names
    assert "read_only_adapter_preflight_adapters_disabled" in check_names
    assert "read_only_adapter_preflight_adapters_not_executed" in check_names
    assert payload["row_counts"]["read_only_adapter_preflight_results"] == 6


def test_workflow_verifier_validates_read_only_adapter_chain_when_present(tmp_path):
    root = _complete_artifact_dir(tmp_path)

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    check_names = {check["name"] for check in payload["consistency_checks"]}
    assert payload["validation_status"] == "passed"
    assert "read_only_adapter_chain_validation_passed_or_warning" in check_names
    assert "read_only_adapter_chain_manual_mode" in check_names
    assert "read_only_adapter_chain_did_not_mutate_production" in check_names
    assert "read_only_adapter_chain_allow_application_submission_false" in check_names
    assert "read_only_adapter_chain_allow_live_pipeline_wiring_false" in check_names
    assert "read_only_adapter_chain_order_matches_expected" in check_names
    assert payload["row_counts"]["read_only_adapter_chain_adapters"] == 3


def test_workflow_verifier_warns_when_read_only_adapter_chain_missing_non_strict(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    (root / "read_only_adapter_chain_result.json").unlink()
    (root / "read_only_adapter_chain_report.md").unlink()

    payload = verify_agentic_workflow_artifacts(output_dir=root, strict=False)

    assert payload["validation_status"] == "warning"
    assert "read_only_adapter_chain_result.json" in payload["missing_artifacts"]
    assert "missing_optional_artifacts" in payload["reason_codes"]


def test_workflow_verifier_fails_unsafe_read_only_adapter_chain(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    chain_path = root / "read_only_adapter_chain_result.json"
    chain = json.loads(chain_path.read_text(encoding="utf-8"))
    chain["allow_application_submission"] = True
    _write_json(chain_path, chain)

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    assert payload["validation_status"] == "failed"
    assert "read_only_adapter_chain_validation_failed" in payload["reason_codes"]
    assert "read_only_adapter_chain_allow_application_submission_true" in payload["reason_codes"]


def test_workflow_verifier_validates_read_only_chain_artifact_generation_when_present(tmp_path):
    root = _complete_artifact_dir(tmp_path)

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    check_names = {check["name"] for check in payload["consistency_checks"]}
    assert payload["validation_status"] == "passed"
    assert "read_only_chain_artifact_generation_validation_passed_or_warning" in check_names
    assert "read_only_chain_artifact_generation_explicit_operator_mode" in check_names
    assert "read_only_chain_artifact_generation_did_not_mutate_production" in check_names
    assert "read_only_chain_artifact_generation_require_explicit_input_true" in check_names
    assert "read_only_chain_artifact_generation_require_explicit_output_dir_true" in check_names
    assert "read_only_chain_artifact_generation_allow_live_pipeline_wiring_false" in check_names
    assert "read_only_chain_artifact_generation_allow_application_submission_false" in check_names
    assert "read_only_chain_artifact_generation_no_production_root_artifact_names" in check_names
    assert payload["row_counts"]["read_only_chain_artifact_generation_did_run_chain"] == 1


def test_workflow_verifier_warns_when_read_only_chain_artifact_generation_missing_non_strict(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    (root / "read_only_chain_artifact_generation_result.json").unlink()
    (root / "read_only_chain_artifact_generation_report.md").unlink()

    payload = verify_agentic_workflow_artifacts(output_dir=root, strict=False)

    assert payload["validation_status"] == "warning"
    assert "read_only_chain_artifact_generation_result.json" in payload["missing_artifacts"]
    assert "missing_optional_artifacts" in payload["reason_codes"]


def test_workflow_verifier_fails_unsafe_read_only_chain_artifact_generation(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    generation_path = root / "read_only_chain_artifact_generation_result.json"
    generation = json.loads(generation_path.read_text(encoding="utf-8"))
    generation["allow_application_submission"] = True
    generation["require_explicit_input"] = False
    _write_json(generation_path, generation)

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    assert payload["validation_status"] == "failed"
    assert "read_only_chain_artifact_generation_validation_failed" in payload["reason_codes"]
    assert "read_only_chain_artifact_generation_allow_application_submission_true" in payload["reason_codes"]
    assert "read_only_chain_artifact_generation_require_explicit_input_false" in payload["reason_codes"]


def test_workflow_verifier_warns_when_read_only_adapter_preflight_missing_non_strict(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    (root / "read_only_adapter_preflight.json").unlink()
    (root / "read_only_adapter_preflight.md").unlink()

    payload = verify_agentic_workflow_artifacts(output_dir=root, strict=False)

    assert payload["validation_status"] == "warning"
    assert "read_only_adapter_preflight.json" in payload["missing_artifacts"]
    assert "missing_optional_artifacts" in payload["reason_codes"]


def test_workflow_verifier_fails_invalid_read_only_adapter_preflight(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    preflight_path = root / "read_only_adapter_preflight.json"
    preflight = json.loads(preflight_path.read_text(encoding="utf-8"))
    preflight["adapter_preflight_results"][0]["execution_enabled"] = True
    _write_json(preflight_path, preflight)

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    assert payload["validation_status"] == "failed"
    assert "read_only_adapter_preflight_validation_failed" in payload["reason_codes"]
    assert "read_only_adapter_preflight_adapter_enabled" in payload["reason_codes"]


def test_workflow_verifier_validates_rag_evaluation_artifact_when_present(tmp_path):
    root = _complete_artifact_dir(tmp_path)

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    check_names = {check["name"] for check in payload["consistency_checks"]}
    assert payload["validation_status"] == "passed"
    assert "rag_evaluation_validation_passed_or_warning" in check_names
    assert payload["row_counts"]["rag_evaluation_rows"] == 1


def test_workflow_verifier_fails_invalid_rag_evaluation_artifact(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    _write_json(
        root / "rag_evaluation_summary.json",
        {
            "evaluation_version": "rag_evaluation_v1",
            "validation_status": "failed",
            "rows": [{"retrieval_score": 3.0, "rank": -1}],
        },
    )

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    assert payload["validation_status"] == "failed"
    assert "rag_evaluation_validation_failed" in payload["reason_codes"]


def test_workflow_verifier_warns_when_manifest_missing_non_strict(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    (root / "agentic_workflow_manifest.json").unlink()
    (root / "agentic_workflow_manifest.md").unlink()

    payload = verify_agentic_workflow_artifacts(output_dir=root, strict=False)

    assert payload["validation_status"] == "warning"
    assert "agentic_workflow_manifest.json" in payload["missing_artifacts"]
    assert "missing_workflow_manifest" in payload["reason_codes"]


def test_workflow_verifier_fails_missing_required_artifacts_in_strict_mode(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    (root / "operator_review_recommendations.csv").unlink()

    payload = verify_agentic_workflow_artifacts(output_dir=root, strict=True)

    assert payload["validation_status"] == "failed"
    assert "operator_review_recommendations.csv" in payload["missing_artifacts"]
    assert "missing_required_artifacts" in payload["reason_codes"]


def test_workflow_verifier_strict_fails_when_manifest_missing(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    (root / "agentic_workflow_manifest.json").unlink()

    payload = verify_agentic_workflow_artifacts(output_dir=root, strict=True)

    assert payload["validation_status"] == "failed"
    assert "agentic_workflow_manifest.json" in payload["missing_artifacts"]
    assert "missing_workflow_manifest" in payload["reason_codes"]


def test_workflow_verifier_reads_manifest_and_validates_expected_artifacts(tmp_path):
    root = _complete_artifact_dir(tmp_path)

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    check_names = {check["name"] for check in payload["consistency_checks"]}
    assert payload["validation_status"] == "passed"
    assert "workflow_manifest_validation_passed" in check_names
    assert "workflow_manifest_ordered_agents_known" in check_names
    assert "workflow_manifest_required_artifacts_present" in check_names


def test_workflow_verifier_reads_execution_plan_and_validates_dry_run(tmp_path):
    root = _complete_artifact_dir(tmp_path)

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    check_names = {check["name"] for check in payload["consistency_checks"]}
    assert payload["validation_status"] == "passed"
    assert "workflow_execution_plan_validation_passed" in check_names
    assert "workflow_execution_plan_dry_run_mode" in check_names
    assert "workflow_execution_plan_steps_disabled" in check_names
    assert "workflow_execution_plan_steps_planned" in check_names
    assert "workflow_execution_plan_order_matches_registry" in check_names


def test_workflow_verifier_warns_when_execution_plan_missing_non_strict(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    (root / "agentic_workflow_execution_plan.json").unlink()
    (root / "agentic_workflow_execution_plan.md").unlink()

    payload = verify_agentic_workflow_artifacts(output_dir=root, strict=False)

    assert payload["validation_status"] == "warning"
    assert "agentic_workflow_execution_plan.json" in payload["missing_artifacts"]
    assert "missing_workflow_execution_plan" in payload["reason_codes"]


def test_workflow_verifier_detects_enabled_execution_plan_step(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    plan_path = root / "agentic_workflow_execution_plan.json"
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    plan["ordered_steps"][0]["execution_enabled"] = True
    _write_json(plan_path, plan)

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    assert payload["validation_status"] == "failed"
    assert "workflow_execution_plan_step_enabled" in payload["reason_codes"]
    assert "workflow_execution_plan_validation_failed" in payload["reason_codes"]


def test_workflow_verifier_reads_dry_run_result_and_validates_no_execution(tmp_path):
    root = _complete_artifact_dir(tmp_path)

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    check_names = {check["name"] for check in payload["consistency_checks"]}
    assert payload["validation_status"] == "passed"
    assert "workflow_dry_run_validation_passed" in check_names
    assert "workflow_dry_run_mode" in check_names
    assert "workflow_dry_run_executed_step_count_zero" in check_names
    assert "workflow_dry_run_steps_not_executed" in check_names
    assert "workflow_dry_run_steps_disabled" in check_names
    assert "workflow_dry_run_steps_skipped" in check_names
    assert "workflow_dry_run_planned_step_count_matches_registry" in check_names


def test_workflow_verifier_warns_when_dry_run_result_missing_non_strict(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    (root / "agentic_workflow_dry_run_result.json").unlink()
    (root / "agentic_workflow_dry_run_report.md").unlink()

    payload = verify_agentic_workflow_artifacts(output_dir=root, strict=False)

    assert payload["validation_status"] == "warning"
    assert "agentic_workflow_dry_run_result.json" in payload["missing_artifacts"]
    assert "missing_workflow_dry_run_result" in payload["reason_codes"]


def test_workflow_verifier_detects_dry_run_step_execution_bug(tmp_path):
    root = _complete_artifact_dir(tmp_path)
    result_path = root / "agentic_workflow_dry_run_result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    result["executed_step_count"] = 1
    result["ordered_step_results"][0]["did_execute"] = True
    _write_json(result_path, result)

    payload = verify_agentic_workflow_artifacts(output_dir=root)

    assert payload["validation_status"] == "failed"
    assert "workflow_dry_run_step_executed" in payload["reason_codes"]
    assert "workflow_dry_run_executed_step_count_nonzero" in payload["reason_codes"]
    assert "workflow_dry_run_validation_failed" in payload["reason_codes"]


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
