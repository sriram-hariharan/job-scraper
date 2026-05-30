import csv
import tempfile
from pathlib import Path

from src.pipeline.job_filter import (
    build_source_health_report_rows,
    write_source_health_report_csv,
)


def _audit_row(
    source,
    company,
    *,
    title_decision="pass",
    location_decision="pass",
    freshness_decision="pass",
    freshness_reason="fresh",
    ashby_fetch_decision="",
):
    return {
        "source": source,
        "job_company": company,
        "title_filter_decision": title_decision,
        "location_filter_decision": location_decision,
        "freshness_filter_decision": freshness_decision,
        "freshness_filter_reason": freshness_reason,
        "ashby_timestamp_fetch_decision": ashby_fetch_decision,
    }


def _rows_by_company(rows):
    return {row["company"]: row for row in rows}


def test_source_health_report_counts_company_funnels_and_final_jobs():
    audit_rows = [
        _audit_row("greenhouse", "scaleai"),
        _audit_row("greenhouse", "scaleai"),
        _audit_row(
            "greenhouse",
            "databricks",
            title_decision="reject",
            location_decision="",
            freshness_decision="reject",
            freshness_reason="title_mismatch",
        ),
        _audit_row(
            "greenhouse",
            "databricks",
            title_decision="pass",
            location_decision="pass",
            freshness_decision="reject",
            freshness_reason="not_recent",
        ),
        _audit_row(
            "ashby",
            "exampleco",
            title_decision="pass",
            location_decision="pass",
            freshness_decision="reject",
            freshness_reason="missing_timestamp",
            ashby_fetch_decision="429",
        ),
    ]
    final_jobs = [
        {"source": "greenhouse", "company": "scaleai"},
        {"source": "greenhouse", "company": "scaleai"},
    ]

    rows = _rows_by_company(build_source_health_report_rows(audit_rows, final_jobs))

    assert rows["scaleai"]["scraped_jobs"] == 2
    assert rows["scaleai"]["title_pass_jobs"] == 2
    assert rows["scaleai"]["location_pass_jobs"] == 2
    assert rows["scaleai"]["freshness_pass_jobs"] == 2
    assert rows["scaleai"]["final_corpus_jobs"] == 2
    assert rows["scaleai"]["final_display_jobs"] == 2

    assert rows["databricks"]["scraped_jobs"] == 2
    assert rows["databricks"]["title_pass_jobs"] == 1
    assert rows["databricks"]["title_reject_jobs"] == 1
    assert rows["databricks"]["not_recent_jobs"] == 1
    assert rows["databricks"]["final_corpus_jobs"] == 0

    assert rows["exampleco"]["scraped_jobs"] == 1
    assert rows["exampleco"]["missing_timestamp_jobs"] == 1
    assert rows["exampleco"]["ashby_timestamp_fetch_429"] == 1
    assert rows["exampleco"]["final_corpus_jobs"] == 0


def test_source_health_report_csv_is_written():
    audit_rows = [_audit_row("greenhouse", "scaleai")]

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "source_health_report.csv"
        write_source_health_report_csv(
            audit_rows,
            [{"source": "greenhouse", "company": "scaleai"}],
            output_path,
        )
        rows = list(csv.DictReader(output_path.read_text(encoding="utf-8").splitlines()))

    assert output_path.name == "source_health_report.csv"
    assert rows[0]["source"] == "greenhouse"
    assert rows[0]["company"] == "scaleai"
    assert rows[0]["final_corpus_jobs"] == "1"
