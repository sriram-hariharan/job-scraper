import csv
import sys
import tempfile
import types
from datetime import datetime, timezone
from pathlib import Path


class _FakeTqdm:
    def __call__(self, iterable=None, **kwargs):
        return iterable

    @staticmethod
    def write(*args, **kwargs):
        return None


sys.modules.setdefault("pycountry", types.SimpleNamespace(countries=[]))
sys.modules.setdefault("requests", types.SimpleNamespace())
sys.modules.setdefault("tqdm", types.SimpleNamespace(tqdm=_FakeTqdm()))
sys.modules.setdefault(
    "src.utils.workday_timestamp",
    types.SimpleNamespace(fetch_workday_timestamp=lambda *args, **kwargs: None),
)

from src.pipeline.job_filter import (
    filter_jobs,
    role_title_filter_audit_counts,
    write_role_title_filter_audit_csv,
)


def _job(title, **overrides):
    job = {
        "company": "Acme",
        "title": title,
        "location": "United States",
        "source": "jobvite",
        "posted_at": datetime.now(timezone.utc).isoformat(),
        "url": f"https://example.com/{title.lower().replace(' ', '-')}",
    }
    job.update(overrides)
    return job


def test_role_title_audit_records_pass_with_matched_family_and_pattern():
    audit_rows = []
    jobs = [_job("Backend Engineer")]

    filtered = filter_jobs(
        jobs,
        selected_role_families=["backend_engineering"],
        role_title_audit_rows=audit_rows,
    )

    assert filtered == jobs
    assert len(audit_rows) == 1
    row = audit_rows[0]
    assert row["title_filter_decision"] == "pass"
    assert row["title_filter_reason"] == "include_pattern_match"
    assert row["matched_role_family"] == "backend_engineering"
    assert row["matched_pattern"]


def test_role_title_audit_records_reject_with_no_matched_family():
    audit_rows = []

    filtered = filter_jobs(
        [_job("Product Manager")],
        selected_role_families=["backend_engineering"],
        role_title_audit_rows=audit_rows,
    )

    assert filtered == []
    assert len(audit_rows) == 1
    row = audit_rows[0]
    assert row["title_filter_decision"] == "reject"
    assert row["title_filter_reason"] == "no_include_pattern_match"
    assert row["matched_role_family"] == ""
    assert row["matched_pattern"] == ""


def test_role_title_audit_mode_does_not_change_filtered_results():
    jobs = [_job("Backend Engineer"), _job("Product Manager")]

    baseline = filter_jobs(jobs, selected_role_families=["backend_engineering"])
    audit_rows = []
    audited = filter_jobs(
        jobs,
        selected_role_families=["backend_engineering"],
        role_title_audit_rows=audit_rows,
    )

    assert audited == baseline
    assert [row["title_filter_decision"] for row in audit_rows] == ["pass", "reject"]


def test_role_title_audit_csv_is_written_with_summary_counts():
    audit_rows = []
    filter_jobs(
        [_job("Backend Engineer"), _job("Product Manager")],
        selected_role_families=["backend_engineering", "fullstack_engineering"],
        role_title_audit_rows=audit_rows,
    )

    with tempfile.TemporaryDirectory() as tmp_dir:
        output_path = Path(tmp_dir) / "role_title_filter_audit.csv"
        write_role_title_filter_audit_csv(audit_rows, output_path)
        rows = list(csv.DictReader(output_path.read_text(encoding="utf-8").splitlines()))

    counts = role_title_filter_audit_counts(audit_rows)
    assert output_path.name == "role_title_filter_audit.csv"
    assert len(rows) == 2
    assert counts["role_title_audit_total"] == 2
    assert counts["role_title_audit_pass"] == 1
    assert counts["role_title_audit_reject"] == 1
    assert counts["role_title_audit_suspected_false_negative"] == 0
