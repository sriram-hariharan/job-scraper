from src.app import services


def _scan_request() -> dict:
    return {
        "company": "ExampleCo",
        "role": "Analytics Engineer",
        "job_description_text": "Build reliable Python and SQL data pipelines.",
        "job_url": "https://example.test/jobs/analytics-engineer",
        "resume_text": "Built reliable Python and SQL data pipelines.",
    }


def test_scan_does_not_report_ready_when_persistence_is_unavailable(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)

    payload = services.create_saved_scan_payload(**_scan_request())

    assert payload["ok"] is False
    assert payload["postgres_write"]["skipped"] == "missing_database_url"
    assert payload["scan_status"] == "failed"
    assert payload["scan"]["scan_status"] == "failed"
    assert "persistence was not confirmed" in payload["scan"]["note"]
    assert payload["scan_review_payload"]["jd_llm_extraction"]["llm_call_attempted"] is False


def test_scan_reports_ready_only_after_confirmed_persistence(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://unit-test.invalid/applylens")
    monkeypatch.setattr(
        services,
        "_dual_write_saved_scan_postgres",
        lambda row: {
            "attempted": True,
            "ok": True,
            "table_name": "saved_scans",
            "scan_id": row["scan_id"],
        },
    )

    payload = services.create_saved_scan_payload(**_scan_request())

    assert payload["ok"] is True
    assert payload["scan_status"] == "ready"
    assert payload["scan"]["scan_status"] == "ready"
    assert payload["postgres_write"]["scan_id"] == payload["scan"]["scan_id"]
    assert payload["scan_review_payload"]["jd_llm_extraction"]["llm_call_attempted"] is False
