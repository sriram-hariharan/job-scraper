import json
from pathlib import Path

from src.agents.workflow_summary import (
    build_agentic_workflow_summary,
    render_agentic_workflow_summary_markdown,
    write_agentic_workflow_summary_artifacts,
)


def test_workflow_summary_handles_all_artifacts_present(tmp_path):
    summary = build_agentic_workflow_summary(
        queue_rows=[
            {
                "job_doc_id": "job_1",
                "job_company": "Acme",
                "job_title": "Backend Engineer",
                "fallback_only_no_deterministic_match": "false",
                "packet_generation_allowed": "true",
            },
            {
                "job_doc_id": "job_2",
                "job_company": "Beta",
                "job_title": "ML Engineer",
                "fallback_only_no_deterministic_match": "true",
                "packet_generation_allowed": "false",
                "packet_generation_block_reason": "fallback_only_no_deterministic_match",
            },
        ],
        job_prioritization_rows=[
            {"job_id": "job_1", "advisory_priority": "apply_now"},
            {"job_id": "job_2", "advisory_priority": "skip_for_now"},
        ],
        tailoring_decision_rows=[
            {"job_id": "job_1", "tailoring_decision": "no_tailoring_needed"},
            {"job_id": "job_2", "tailoring_decision": "do_not_tailor"},
        ],
        operator_review_rows=[
            {
                "job_id": "job_1",
                "company": "Acme",
                "title": "Backend Engineer",
                "operator_review_lane": "ready_to_apply",
                "deterministic_winner_score": "0.82",
            },
            {
                "job_id": "job_2",
                "company": "Beta",
                "title": "ML Engineer",
                "operator_review_lane": "hold_or_skip",
                "deterministic_winner_score": "0.00",
            },
        ],
        source_health_rows=[
            {
                "source": "greenhouse",
                "company": "scaleai",
                "scraped_jobs": "10",
                "title_pass_jobs": "8",
                "location_pass_jobs": "7",
                "freshness_pass_jobs": "6",
                "missing_timestamp_jobs": "0",
                "not_recent_jobs": "0",
                "final_corpus_jobs": "6",
            }
        ],
        best_resume_rows=[{"job_id": "job_1"}],
        packet_manifest_rows=[
            {"job_doc_id": "job_1", "packet_status": "generated"},
            {"job_doc_id": "job_2", "packet_status": "unresolved_no_credible_match"},
        ],
        generated_at_utc="2026-01-01T00:00:00+00:00",
    )

    assert summary["total_queue_jobs"] == 2
    assert summary["total_packet_jobs"] == 1
    assert summary["advisory_priority_counts"] == {"apply_now": 1, "skip_for_now": 1}
    assert summary["tailoring_decision_counts"] == {"do_not_tailor": 1, "no_tailoring_needed": 1}
    assert summary["operator_review_lane_counts"] == {"hold_or_skip": 1, "ready_to_apply": 1}
    assert summary["fallback_only_count"] == 1
    assert summary["packet_blocked_count"] == 1
    assert summary["ready_to_apply_count"] == 1
    assert summary["hold_or_skip_count"] == 1
    assert summary["source_recommendation_counts"] == {"promote": 1}
    assert summary["top_ready_to_apply_jobs"][0]["company"] == "Acme"
    assert summary["top_hold_or_skip_jobs"][0]["company"] == "Beta"


def test_workflow_summary_handles_missing_optional_artifacts_safely(tmp_path):
    output_dir = tmp_path / "outputs"
    output_dir.mkdir()
    (output_dir / "application_execution_queue.csv").write_text(
        "job_doc_id,job_company,job_title\njob_1,Acme,Backend Engineer\n",
        encoding="utf-8",
    )

    result = write_agentic_workflow_summary_artifacts(
        output_dir=output_dir,
        generated_at_utc="2026-01-01T00:00:00+00:00",
    )

    summary = json.loads(Path(result["summary_json_path"]).read_text(encoding="utf-8"))
    markdown = Path(result["summary_md_path"]).read_text(encoding="utf-8")

    assert summary["total_queue_jobs"] == 1
    assert "operator_review_recommendations.csv" in summary["missing_artifacts"]
    assert "## Overview" in markdown
    assert "## Resume Match Safety" in markdown
    assert "## Source Health" in markdown
    assert "## Job Prioritization" in markdown
    assert "## Tailoring Decision" in markdown
    assert "## Operator Review" in markdown
    assert "## Top Ready Jobs" in markdown
    assert "## Hold / Skip Jobs" in markdown
    assert "## Missing Artifacts" in markdown


def test_workflow_summary_markdown_contains_stable_sections():
    markdown = render_agentic_workflow_summary_markdown(
        {
            "generated_at_utc": "2026-01-01T00:00:00+00:00",
            "total_queue_jobs": 0,
            "total_packet_jobs": 0,
            "fallback_only_count": 0,
            "packet_blocked_count": 0,
            "missing_artifacts": [],
        }
    )

    assert markdown.startswith("# Agentic Workflow Summary")
    assert "## Overview" in markdown
    assert "## Missing Artifacts" in markdown
