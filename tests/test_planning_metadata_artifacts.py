import csv
import sys
import tempfile
from pathlib import Path

import application_execution_queue
import application_shortlist_from_batch_selector
import run_application_planning


def _read_rows(path: Path):
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _write_selector_fixture(path: Path) -> None:
    row = {
        "job_doc_id": "https://jobs.example.com/1",
        "job_company": "Acme",
        "job_title": "Backend Engineer",
        "job_location": "New York, NY",
        "posted_at": "",
        "freshness_status": "unknown_timestamp_allowed",
        "ashby_timestamp_status": "ashby_timestamp_request_failed",
        "resume_variants_considered": "2",
        "passed_prefilter": "1",
        "filtered_out": "0",
        "winner_resume": "resume.pdf",
        "winner_score": "0.910000",
        "winner_bucket": "strong",
        "winner_top_dims": "skills=0.90",
        "winner_missing_requirements": "",
        "winner_matched_terms": "python",
        "recommendation_summary": "Strong match.",
        "resolved_resume": "resume.pdf",
        "resolved_score": "0.910000",
        "resolved_bucket": "strong",
        "resolved_top_dims": "skills=0.90",
        "resolved_missing_requirements": "",
        "resolved_matched_terms": "python",
        "resolved_resume_source": "deterministic_winner",
        "resolved_selection_status": "resolved",
        "variant_review_required": "False",
        "resolved_best_available_imperfect_match": "False",
        "selection_signal": "deterministic_winner",
        "requires_manual_review": "False",
        "manual_review_gap_epsilon": "0.020000",
        "is_tie": "False",
        "tie_epsilon": "0.010000",
        "runner_up_resume": "",
        "runner_up_score": "",
        "score_gap": "",
        "llm_adjudication_resume": "",
        "llm_adjudication_confidence": "",
        "llm_adjudication_reason": "",
        "llm_adjudication_status": "disabled",
        "llm_adjudication_parse_ok": "",
        "llm_adjudication_provider": "",
        "llm_adjudication_model": "",
        "llm_adjudication_cache_hit": "",
        "llm_adjudication_differs_from_deterministic": "False",
        "llm_adjudication_error_type": "",
        "llm_fallback_best_resume": "",
        "llm_fallback_best_score": "",
        "llm_fallback_backup_resume": "",
        "llm_fallback_backup_score": "",
        "llm_fallback_confidence": "",
        "llm_fallback_reason": "",
        "llm_fallback_status": "disabled",
        "llm_fallback_parse_ok": "",
        "llm_fallback_provider": "",
        "llm_fallback_model": "",
        "llm_fallback_cache_hit": "",
        "llm_fallback_error_type": "",
    }
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(row))
        writer.writeheader()
        writer.writerow(row)


def test_selector_source_writes_location_and_unknown_timestamp_metadata():
    source = Path("batch_select_best_resume_variant.py").read_text(encoding="utf-8")

    assert '"job_location": str(record.get("location", "")' in source
    assert '"freshness_status": str(record.get("freshness_status", "")' in source
    assert '"ashby_timestamp_status": str(record.get("ashby_timestamp_status", "")' in source
    assert '"job_location",' in source


def test_job_packet_manifest_includes_location_and_timestamp_metadata():
    source = Path("run_application_planning.py").read_text(encoding="utf-8")

    assert '"job_location": row.get("job_location", "")' in source
    assert '"freshness_status": row.get("freshness_status", "")' in source
    assert '"ashby_timestamp_status": row.get("ashby_timestamp_status", "")' in source
    assert '"job_location",' in source


def test_planning_writes_agentic_workflow_summary_artifacts():
    source = Path("run_application_planning.py").read_text(encoding="utf-8")

    assert "agentic_workflow_summary.json" in source
    assert "agentic_workflow_summary.md" in source
    assert "write_agentic_workflow_summary_artifacts" in source
    assert "agentic_workflow_manifest.json" in source
    assert "agentic_workflow_manifest.md" in source
    assert "write_agentic_workflow_manifest_artifacts" in source
    assert "agentic_workflow_execution_plan.json" in source
    assert "agentic_workflow_execution_plan.md" in source
    assert "write_agentic_workflow_execution_plan_artifacts" in source
    assert "agentic_workflow_dry_run_result.json" in source
    assert "agentic_workflow_dry_run_report.md" in source
    assert "write_agentic_workflow_dry_run_artifacts" in source
    assert "read_only_adapter_preflight.json" in source
    assert "read_only_adapter_preflight.md" in source
    assert "write_read_only_adapter_preflight_artifacts" in source
    assert "agentic_workflow_verification.json" in source
    assert "write_agentic_workflow_verification_artifact" in source
    assert "rag_evaluation_summary.json" in source
    assert "rag_evaluation_report.md" in source
    assert "write_rag_evaluation_artifacts" in source
    assert "APPLYLENS_WORKFLOW_VERIFIER_STRICT" in source


def test_shortlist_and_execution_queue_preserve_job_location_and_freshness_metadata():
    original_argv = sys.argv[:]

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        selector_csv = root / "best_resume_variant_by_job.csv"
        shortlist_csv = root / "application_shortlist_by_job.csv"
        queue_csv = root / "application_execution_queue.csv"
        priority_csv = root / "job_prioritization_recommendations.csv"
        priority_summary = root / "job_prioritization_summary.json"
        tailoring_decision_csv = root / "tailoring_decision_recommendations.csv"
        tailoring_decision_summary = root / "tailoring_decision_summary.json"
        operator_review_csv = root / "operator_review_recommendations.csv"
        operator_review_summary = root / "operator_review_summary.json"
        _write_selector_fixture(selector_csv)

        try:
            sys.argv = [
                "application_shortlist_from_batch_selector.py",
                "--input-csv",
                str(selector_csv),
                "--output-csv",
                str(shortlist_csv),
                "--top-k-console",
                "0",
            ]
            application_shortlist_from_batch_selector.main()

            sys.argv = [
                "application_execution_queue.py",
                "--input-csv",
                str(shortlist_csv),
                "--output-csv",
                str(queue_csv),
                "--priority-output-csv",
                str(priority_csv),
                "--priority-summary-json",
                str(priority_summary),
                "--tailoring-decision-output-csv",
                str(tailoring_decision_csv),
                "--tailoring-decision-summary-json",
                str(tailoring_decision_summary),
                "--operator-review-output-csv",
                str(operator_review_csv),
                "--operator-review-summary-json",
                str(operator_review_summary),
                "--top-k-console",
                "0",
            ]
            application_execution_queue.main()
        finally:
            sys.argv = original_argv

        shortlist_row = _read_rows(shortlist_csv)[0]
        queue_row = _read_rows(queue_csv)[0]
        priority_row = _read_rows(priority_csv)[0]
        tailoring_decision_row = _read_rows(tailoring_decision_csv)[0]
        operator_review_row = _read_rows(operator_review_csv)[0]
        priority_summary_exists = priority_summary.exists()
        tailoring_decision_summary_exists = tailoring_decision_summary.exists()
        operator_review_summary_exists = operator_review_summary.exists()

    for row in (shortlist_row, queue_row):
        assert row["job_location"] == "New York, NY"
        assert row["freshness_status"] == "unknown_timestamp_allowed"
        assert row["ashby_timestamp_status"] == "ashby_timestamp_request_failed"
        assert row["posted_at"] == ""
        assert row["deterministic_winner_available"] == "true"
        assert row["deterministic_winner_score"] == "0.910000"
        assert row["packet_generation_allowed"] == "true"
    assert priority_row["existing_action"] == queue_row["action"]
    assert priority_row["advisory_priority"] == "apply_now"
    assert priority_row["deterministic_winner_score"] == "0.910000"
    assert priority_summary_exists
    assert tailoring_decision_row["existing_action"] == queue_row["action"]
    assert tailoring_decision_row["advisory_priority"] == "apply_now"
    assert tailoring_decision_row["tailoring_decision"] == "no_tailoring_needed"
    assert tailoring_decision_row["deterministic_winner_score"] == "0.910000"
    assert tailoring_decision_summary_exists
    assert operator_review_row["existing_action"] == queue_row["action"]
    assert operator_review_row["advisory_priority"] == "apply_now"
    assert operator_review_row["tailoring_decision"] == "no_tailoring_needed"
    assert operator_review_row["operator_review_lane"] == "ready_to_apply"
    assert operator_review_row["deterministic_winner_score"] == "0.910000"
    assert operator_review_summary_exists


def test_fallback_only_selector_row_is_visible_but_not_actionable():
    original_argv = sys.argv[:]

    with tempfile.TemporaryDirectory() as tmp_dir:
        root = Path(tmp_dir)
        selector_csv = root / "best_resume_variant_by_job.csv"
        shortlist_csv = root / "application_shortlist_by_job.csv"
        queue_csv = root / "application_execution_queue.csv"
        _write_selector_fixture(selector_csv)

        rows = _read_rows(selector_csv)
        row = rows[0]
        row.update(
            {
                "passed_prefilter": "0",
                "winner_resume": "",
                "winner_score": "0.000000",
                "winner_bucket": "filtered_out",
                "resolved_resume": "fallback.pdf",
                "resolved_score": "0.000000",
                "resolved_bucket": "filtered_out",
                "resolved_resume_source": "llm_fallback_generated",
                "resolved_selection_status": "fallback_only_no_deterministic_match",
                "resolved_best_available_imperfect_match": "True",
                "selection_signal": "no_credible_match",
                "llm_fallback_best_resume": "fallback.pdf",
                "llm_fallback_best_score": "0.420000",
                "llm_fallback_status": "generated",
            }
        )
        with selector_csv.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(row))
            writer.writeheader()
            writer.writerow(row)

        try:
            sys.argv = [
                "application_shortlist_from_batch_selector.py",
                "--input-csv",
                str(selector_csv),
                "--output-csv",
                str(shortlist_csv),
                "--top-k-console",
                "0",
            ]
            application_shortlist_from_batch_selector.main()

            sys.argv = [
                "application_execution_queue.py",
                "--input-csv",
                str(shortlist_csv),
                "--output-csv",
                str(queue_csv),
                "--top-k-console",
                "0",
            ]
            application_execution_queue.main()
        finally:
            sys.argv = original_argv

        shortlist_row = _read_rows(shortlist_csv)[0]
        queue_row = _read_rows(queue_csv)[0]

    assert shortlist_row["action"] == "SKIP_FOR_NOW"
    assert shortlist_row["winner_resume"] == ""
    assert shortlist_row["resolved_resume"] == "fallback.pdf"
    assert shortlist_row["selector_winner_resume"] == ""
    assert shortlist_row["fallback_only_no_deterministic_match"] == "true"
    assert shortlist_row["resolved_selection_status"] == "fallback_only_no_deterministic_match"
    assert shortlist_row["packet_generation_allowed"] == "false"
    assert shortlist_row["packet_generation_block_reason"] == "fallback_only_no_deterministic_match"
    assert (
        shortlist_row["resolved_resume_warning"]
        == "Fallback suggested a resume, but deterministic scorer found no credible match."
    )
    assert "Fallback resume suggestion only" in queue_row["queue_priority_reason"]


def test_packet_selection_blocks_fallback_only_and_low_confidence_rows():
    fallback_only = {
        "winner_resume": "",
        "winner_score": "0.000000",
        "resolved_resume": "fallback.pdf",
        "resolved_selection_status": "fallback_only_no_deterministic_match",
        "resolved_resume_source": "llm_fallback_generated",
        "variant_review_required": "false",
        "selection_signal": "no_credible_match",
        "llm_fallback_best_resume": "fallback.pdf",
        "llm_fallback_status": "generated",
    }
    assert run_application_planning._resolve_packet_resume_selection(fallback_only) == {
        "packet_status": "unresolved_no_credible_match",
        "packet_resume": "",
        "packet_resume_source": "fallback_only_no_deterministic_match",
    }

    low_confidence = {
        "winner_resume": "weak.pdf",
        "winner_score": "0.490000",
        "resolved_resume": "weak.pdf",
        "resolved_selection_status": "resolved",
        "resolved_resume_source": "deterministic_winner",
        "variant_review_required": "false",
        "selection_signal": "deterministic_winner",
    }
    assert run_application_planning._resolve_packet_resume_selection(low_confidence) == {
        "packet_status": "blocked_low_confidence_match",
        "packet_resume": "",
        "packet_resume_source": "deterministic_score_below_credible_threshold",
    }

    swatika_style = {
        "winner_resume": "SWATIKA_test_1.pdf",
        "winner_score": "0.520000",
        "resolved_resume": "SWATIKA_test_1.pdf",
        "resolved_selection_status": "resolved",
        "resolved_resume_source": "deterministic_winner",
        "variant_review_required": "false",
        "selection_signal": "deterministic_winner",
    }
    assert run_application_planning._resolve_packet_resume_selection(swatika_style) == {
        "packet_status": "generated",
        "packet_resume": "SWATIKA_test_1.pdf",
        "packet_resume_source": "deterministic_winner",
    }


def _packet_selection_row(
    *,
    action: str,
    job_doc_id: str,
    winner_score: str = "0.720000",
    winner_resume: str = "resume.pdf",
    fallback_only_no_deterministic_match: str = "false",
    packet_generation_allowed: str = "true",
) -> dict:
    return {
        "job_doc_id": job_doc_id,
        "action": action,
        "winner_resume": winner_resume,
        "winner_score": winner_score,
        "resolved_resume": winner_resume,
        "resolved_resume_source": "deterministic_winner" if winner_resume else "",
        "resolved_selection_status": "resolved" if winner_resume else "",
        "variant_review_required": "false",
        "selection_signal": "deterministic_winner" if winner_resume else "no_credible_match",
        "fallback_only_no_deterministic_match": fallback_only_no_deterministic_match,
        "packet_generation_allowed": packet_generation_allowed,
    }


def test_selected_rows_preserves_default_skip_exclusion_when_not_requested():
    rows = [
        _packet_selection_row(action="APPLY", job_doc_id="apply"),
        _packet_selection_row(action="MAYBE_TAILOR", job_doc_id="maybe"),
        _packet_selection_row(action="SKIP_FOR_NOW", job_doc_id="safe_skip"),
    ]

    selected = run_application_planning._selected_rows(
        rows,
        include_actions={"APPLY", "MAYBE_TAILOR"},
        packet_limit=0,
    )

    assert [row["job_doc_id"] for row in selected] == ["apply", "maybe"]


def test_selected_rows_includes_only_safe_skip_rows_when_explicitly_requested():
    rows = [
        _packet_selection_row(action="APPLY", job_doc_id="apply"),
        _packet_selection_row(action="MAYBE_TAILOR", job_doc_id="maybe"),
        _packet_selection_row(action="SKIP_FOR_NOW", job_doc_id="safe_skip", winner_score="0.500000"),
        _packet_selection_row(
            action="SKIP_FOR_NOW",
            job_doc_id="fallback_skip",
            winner_score="0.000000",
            winner_resume="",
            fallback_only_no_deterministic_match="true",
            packet_generation_allowed="false",
        ),
        _packet_selection_row(
            action="SKIP_FOR_NOW",
            job_doc_id="packet_blocked_skip",
            winner_score="0.720000",
            packet_generation_allowed="false",
        ),
        _packet_selection_row(
            action="SKIP_FOR_NOW",
            job_doc_id="low_score_skip",
            winner_score="0.490000",
            packet_generation_allowed="false",
        ),
    ]

    selected = run_application_planning._selected_rows(
        rows,
        include_actions={"APPLY", "MAYBE_TAILOR", "SKIP_FOR_NOW"},
        packet_limit=0,
    )

    assert [row["job_doc_id"] for row in selected] == ["apply", "maybe", "safe_skip"]
    assert selected[-1]["action"] == "SKIP_FOR_NOW"
    assert run_application_planning._resolve_packet_resume_selection(selected[-1]) == {
        "packet_status": "generated",
        "packet_resume": "resume.pdf",
        "packet_resume_source": "deterministic_winner",
    }
