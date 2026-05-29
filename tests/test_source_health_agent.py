import csv
import tempfile
from pathlib import Path

from src.agents import source_health_agent


def _row(
    source,
    company,
    *,
    scraped=1,
    title_pass=0,
    location_pass=0,
    freshness_pass=0,
    not_recent=0,
    missing_timestamp=0,
    final=0,
):
    return {
        "source": source,
        "company": company,
        "scraped_jobs": str(scraped),
        "title_pass_jobs": str(title_pass),
        "title_reject_jobs": "0",
        "location_pass_jobs": str(location_pass),
        "location_reject_jobs": "0",
        "freshness_pass_jobs": str(freshness_pass),
        "not_recent_jobs": str(not_recent),
        "missing_timestamp_jobs": str(missing_timestamp),
        "final_corpus_jobs": str(final),
        "final_display_jobs": str(final),
        "ashby_timestamp_fetch_success": "0",
        "ashby_timestamp_fetch_429": "0",
        "ashby_timestamp_fetch_failed": "0",
        "notes": "",
    }


def test_source_health_agent_parses_csv_rows():
    rows = [_row("greenhouse", "scaleai", scraped=10, freshness_pass=8, final=6)]
    with tempfile.TemporaryDirectory() as tmp_dir:
        path = Path(tmp_dir) / "source_health_report.csv"
        with path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

        parsed = source_health_agent.parse_source_health_report_csv(path)

    assert parsed == rows


def test_source_health_agent_recommendation_rules_and_aggregates():
    rows = [
        _row("greenhouse", "scaleai", scraped=20, title_pass=10, location_pass=8, freshness_pass=8, final=6),
        _row("lever", "field-ai", scraped=6, title_pass=3, location_pass=3, freshness_pass=2, final=2),
        _row("builtin", "example", scraped=4, title_pass=4, location_pass=4, freshness_pass=4, final=0),
        _row("ashby", "missingco", scraped=5, title_pass=3, location_pass=3, missing_timestamp=3),
        _row("greenhouse", "staleco", scraped=9, title_pass=3, location_pass=3, not_recent=3),
        _row("smartrecruiters", "quietco", scraped=0),
    ]

    payload = source_health_agent.render_source_health_recommendations(rows=rows)
    recommendations = {
        item["company"]: item["recommendation"]
        for item in payload["output"]["recommendations"]
    }

    assert recommendations["scaleai"] == "promote"
    assert recommendations["field-ai"] == "keep"
    assert recommendations["example"] == "needs_detail_enrichment"
    assert recommendations["missingco"] == "needs_timestamp_fix"
    assert recommendations["staleco"] == "demote"
    assert recommendations["quietco"] == "monitor"
    assert payload["output"]["final_jobs_by_source"]["greenhouse"] == 6
    assert payload["output"]["final_jobs_by_source"]["lever"] == 2
    assert payload["output"]["missing_timestamp_by_source"]["ashby"] == 3
    assert payload["output"]["top_companies_by_final_jobs"][0]["company"] == "scaleai"
    assert {"source": "builtin", "company": "example"} in payload["output"]["zero_final_but_fresh_companies"]
    assert {"source": "ashby", "company": "missingco"} in payload["output"]["missing_timestamp_companies"]
    assert payload["validation"]["validation_status"] == "passed"
    assert payload["validation"]["no_mutation_performed"] is True


def test_source_health_agent_validation_fails_when_required_columns_missing():
    rows = [{"source": "greenhouse", "company": "scaleai", "scraped_jobs": "1"}]
    payload = source_health_agent.render_source_health_recommendations(rows=rows)

    assert payload["validation"]["required_columns_present"] is False
    assert payload["validation"]["validation_status"] == "failed"
    assert "missing_required_columns" in payload["validation"]["reason_codes"]
    assert "final_corpus_jobs" in payload["validation"]["missing_required_columns"]


def test_source_health_agent_trace_disabled_by_default(monkeypatch):
    class TraceModule:
        def create_agent_run(self, **kwargs):
            raise AssertionError("trace should not run when disabled")

    monkeypatch.delenv(source_health_agent.TRACE_ENABLED_ENV, raising=False)
    result = source_health_agent.record_source_health_agent_trace(
        rows=[_row("greenhouse", "scaleai")],
        artifact_path="source_health_report.csv",
        trace_module=TraceModule(),
    )

    assert result == {"attempted": False, "reason": "trace_disabled"}


def test_source_health_agent_optional_trace_can_be_monkeypatched():
    calls = []

    class TraceModule:
        def create_agent_run(self, **kwargs):
            calls.append(("create_agent_run", kwargs))
            return {"run": {"agent_run_id": "agent_run_1"}}

        def record_agent_step(self, **kwargs):
            calls.append(("record_agent_step", kwargs))
            return {"step": {"agent_step_id": "agent_step_1"}}

        def complete_agent_step(self, **kwargs):
            calls.append(("complete_agent_step", kwargs))
            return {"ok": True}

        def complete_agent_run(self, **kwargs):
            calls.append(("complete_agent_run", kwargs))
            return {"ok": True}

    result = source_health_agent.record_source_health_agent_trace(
        rows=[_row("greenhouse", "scaleai", scraped=10, freshness_pass=6, final=6)],
        artifact_path="source_health_report.csv",
        env={
            source_health_agent.TRACE_ENABLED_ENV: "1",
            "JOB_STACK_OWNER_USER_ID": "user_1",
            "JOB_APP_PIPELINE_RUN_ID": "run_1",
        },
        trace_module=TraceModule(),
    )

    assert result["recorded"] is True
    assert result["agent_run_id"] == "agent_run_1"
    assert result["agent_step_id"] == "agent_step_1"
    assert [name for name, _payload in calls] == [
        "create_agent_run",
        "record_agent_step",
        "complete_agent_step",
        "complete_agent_run",
    ]
    step_record = calls[1][1]["record"]
    assert step_record["agent_name"] == source_health_agent.AGENT_NAME
    assert step_record["input_json"]["total_source_company_rows"] == 1


def test_source_health_agent_trace_failure_returns_warning_when_not_strict():
    class TraceModule:
        def create_agent_run(self, **kwargs):
            raise RuntimeError("db unavailable")

    result = source_health_agent.record_source_health_agent_trace(
        rows=[_row("greenhouse", "scaleai")],
        env={
            source_health_agent.TRACE_ENABLED_ENV: "1",
            "JOB_STACK_OWNER_USER_ID": "user_1",
            "JOB_APP_PIPELINE_RUN_ID": "run_1",
        },
        trace_module=TraceModule(),
    )

    assert result["attempted"] is True
    assert result["recorded"] is False
    assert "db unavailable" in result["warning"]
