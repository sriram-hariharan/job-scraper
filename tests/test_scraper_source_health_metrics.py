import asyncio
from datetime import datetime, timezone

import pytest

from src.discovery.crawl_scheduler import AcquisitionOutcome, AcquisitionStatus
from src.storage import metrics_store
from src.utils import ats_health, http_retry, pipeline_metrics


def _job(source="greenhouse", company="acme", suffix="1", **overrides):
    job = {
        "source": source,
        "company": company,
        "job_id": f"job-{suffix}",
        "title": f"Engineer {suffix}",
        "url": f"https://jobs.example/{suffix}",
        "posted_at": "2026-08-02T00:00:00+00:00",
        "description": "Role description",
    }
    job.update(overrides)
    return job


@pytest.fixture(autouse=True)
def _reset_metrics():
    pipeline_metrics.reset_acquisition_metrics()
    yield
    pipeline_metrics.reset_acquisition_metrics()


def test_observed_success_records_transport_counts_completeness_and_schedule(monkeypatch):
    monkeypatch.setattr(http_retry.time, "sleep", lambda _delay: None)
    responses = iter([
        type("Response", (), {"status_code": 503, "headers": {}})(),
        type("Response", (), {"status_code": 200, "headers": {}})(),
    ])

    @http_retry.retry_request(retries=2, delay=0)
    def request():
        return next(responses)

    def acquire():
        assert request().status_code == 200
        return AcquisitionOutcome(
            "acme",
            AcquisitionStatus.SUCCESS,
            (_job(),),
            page_count=1,
            raw_job_count=2,
        )

    outcome = pipeline_metrics.observe_acquisition(
        "greenhouse", acquire, schedule_on_success=True
    )
    metric = pipeline_metrics.acquisition_metrics_snapshot()[0]

    assert list(outcome.jobs) == [_job()]
    assert metric.request_count == 2
    assert metric.response_status_counts == ((200, 1), (503, 1))
    assert metric.retry_count == 1
    assert metric.page_count == 1
    assert metric.raw_job_count == 2
    assert metric.normalized_job_count == 1
    assert metric.canonical_url_present_count == 1
    assert metric.timestamp_present_count == 1
    assert metric.description_present_count == 1
    assert metric.schedule_advanced is True
    assert metric.health == pipeline_metrics.DEGRADED


def test_retry_exhaustion_records_failed_transport_health(monkeypatch):
    monkeypatch.setattr(http_retry.time, "sleep", lambda _delay: None)

    @http_retry.retry_request(retries=2, delay=0)
    def request():
        raise http_retry.requests.Timeout("secret timeout detail")

    with pytest.raises(http_retry.requests.Timeout):
        pipeline_metrics.observe_acquisition(
            "workable",
            request,
            schedule_on_success=True,
            company="acme",
        )

    metric = pipeline_metrics.acquisition_metrics_snapshot()[0]
    assert metric.acquisition_status == "FAILED"
    assert metric.reason_code == "transport_error"
    assert metric.request_count == 2
    assert metric.retry_count == 1
    assert metric.health == "unhealthy"
    assert metric.schedule_advanced is False
    assert "secret timeout detail" not in repr(metric)


@pytest.mark.parametrize(
    ("status", "health"),
    [
        ("SUCCESS", "healthy"),
        ("EMPTY", "healthy"),
        ("PARTIAL", "degraded"),
        ("FAILED", "unhealthy"),
        ("", "unknown"),
    ],
)
def test_health_status_policy(status, health):
    assert pipeline_metrics.classify_source_health(status) == health


def test_completeness_thresholds_are_deterministic_and_nonfatal_for_one_optional_gap():
    assert pipeline_metrics.classify_source_health(
        "SUCCESS",
        normalized_job_count=10,
        timestamp_missing_count=1,
        description_missing_count=1,
    ) == "healthy"
    assert pipeline_metrics.classify_source_health(
        "SUCCESS",
        normalized_job_count=4,
        canonical_url_missing_count=2,
    ) == "unhealthy"
    assert pipeline_metrics.classify_source_health(
        "SUCCESS",
        normalized_job_count=4,
        timestamp_missing_count=4,
    ) == "degraded"


@pytest.mark.parametrize(
    ("status", "reason", "jobs", "advance"),
    [
        (AcquisitionStatus.SUCCESS, "", (_job(),), True),
        (AcquisitionStatus.EMPTY, "", (), True),
        (AcquisitionStatus.PARTIAL, "pagination_interrupted", (_job(),), False),
        (AcquisitionStatus.FAILED, "transport_error", (), False),
    ],
)
def test_outcomes_preserve_scheduler_matrix(status, reason, jobs, advance):
    outcome = AcquisitionOutcome("acme", status, jobs, reason=reason)
    pipeline_metrics.observe_acquisition(
        "workday", lambda: outcome, schedule_on_success=True
    )
    metric = pipeline_metrics.acquisition_metrics_snapshot()[0]
    assert metric.schedule_advanced is advance
    if status is AcquisitionStatus.PARTIAL:
        assert metric.partial_result_count == 1


def test_stage_aggregation_uses_source_owned_counts_without_overwriting_boards():
    for company, suffix in (("alpha", "1"), ("beta", "2")):
        pipeline_metrics.observe_acquisition(
            "lever",
            lambda company=company, suffix=suffix: AcquisitionOutcome(
                company,
                AcquisitionStatus.SUCCESS,
                (_job("lever", company, suffix),),
                raw_job_count=1,
            ),
            schedule_on_success=True,
        )
    acquisitions = pipeline_metrics.acquisition_metrics_snapshot()
    combined = pipeline_metrics.combine_source_stage_metrics(
        acquisitions,
        filtered_jobs=[_job("lever", "alpha", "1")],
        deduped_jobs=[_job("lever", "alpha", "1")],
        final_jobs=[_job("lever", "alpha", "1")],
    )
    summary = next(metric for metric in combined if metric.company == "")
    boards = [metric for metric in combined if metric.company]
    assert summary.normalized_job_count == 2
    assert summary.filter_drop_count == 1
    assert summary.duplicate_drop_count == 0
    assert summary.final_retained_job_count == 1
    assert [(row.company, row.filter_drop_count) for row in boards] == [
        ("alpha", 0),
        ("beta", 0),
    ]


def test_ats_health_enforces_failed_and_partial_truth():
    rows = (
        pipeline_metrics.SourceHealthMetrics(
            source="ashby",
            company="alpha",
            acquisition_status="FAILED",
            health="healthy",
        ),
        pipeline_metrics.SourceHealthMetrics(
            source="lever",
            company="beta",
            acquisition_status="PARTIAL",
            health="healthy",
        ),
    )
    assert ats_health.enforce_source_health(rows) == {
        "ashby": "unhealthy",
        "lever": "degraded",
    }


def test_persistence_is_idempotent_ordered_bounded_and_payload_safe(monkeypatch):
    statements = []
    monkeypatch.setattr(metrics_store, "init_metrics_db", lambda: None)
    monkeypatch.setattr(
        metrics_store, "_run_psql_statement", statements.append
    )
    now = datetime(2026, 8, 2, tzinfo=timezone.utc)
    rows = [
        {
            "source": "workday",
            "company": "https://tenant.myworkdayjobs.com/site?token=secret",
            "acquisition_status": "FAILED",
            "reason_code": "transport_error",
            "response_status_counts": ((503, 2),),
            "started_at": now,
            "completed_at": now,
            "health": "unhealthy",
            "provider_payload": "never-persist-this-secret",
            "exception": "never-persist-this-exception",
        },
        pipeline_metrics.SourceHealthMetrics(
            source="ashby",
            company="alpha",
            acquisition_status="EMPTY",
            health="healthy",
        ),
    ]

    assert metrics_store.record_source_health_metrics(17, rows) == 2
    assert metrics_store.record_source_health_metrics(17, rows) == 2
    assert statements[0] == statements[1]
    sql = statements[0]
    assert "ON CONFLICT (run_id, source, company) DO UPDATE" in sql
    assert sql.index("'ashby'") < sql.index("'workday'")
    assert "tenant.myworkdayjobs.com/site" in sql
    assert "token=secret" not in sql
    assert "never-persist-this-secret" not in sql
    assert "never-persist-this-exception" not in sql


def test_persistence_keeps_runs_and_companies_distinct(monkeypatch):
    statements = []
    monkeypatch.setattr(metrics_store, "init_metrics_db", lambda: None)
    monkeypatch.setattr(metrics_store, "_run_psql_statement", statements.append)
    rows = [
        pipeline_metrics.SourceHealthMetrics(source="lever", company="alpha"),
        pipeline_metrics.SourceHealthMetrics(source="lever", company="beta"),
    ]
    metrics_store.record_source_health_metrics(41, rows)
    metrics_store.record_source_health_metrics(42, rows)
    assert "(41, 'lever', 'alpha'" in statements[0]
    assert "(41, 'lever', 'beta'" in statements[0]
    assert "(42, 'lever', 'alpha'" in statements[1]


def test_collector_persistence_failure_preserves_truthful_metrics():
    from src.pipeline import collector

    failed_metric = pipeline_metrics.SourceHealthMetrics(
        source="workday",
        company="acme",
        acquisition_status="FAILED",
        reason_code="transport_error",
        health="unhealthy",
    )

    def unavailable_writer(_run_id, _metrics):
        raise RuntimeError("secret database response")

    assert collector._persist_source_health_safely(
        12,
        (failed_metric,),
        unavailable_writer,
    ) == 0
    assert failed_metric.acquisition_status == "FAILED"
    assert failed_metric.health == "unhealthy"
    assert "secret database response" not in repr(failed_metric)


@pytest.mark.parametrize(
    ("module_name", "wrapper_name", "source"),
    [
        ("src.scrapers.ashby_scraper", "_fetch_company_result", "ashby"),
        ("src.scrapers.jobvite_scraper", "_fetch_company_result", "jobvite"),
        ("src.scrapers.workable_scraper", "_fetch_company_result", "workable"),
        ("src.scrapers.workday_scraper", "_scrape_company_result", "workday"),
    ],
)
def test_sync_production_company_wrappers_emit_metrics(
    monkeypatch, module_name, wrapper_name, source
):
    module = __import__(module_name, fromlist=["unused"])
    acquisition_name = (
        "_scrape_company_outcome" if source == "workday" else "_fetch_company_outcome"
    )
    monkeypatch.setattr(
        module,
        acquisition_name,
        lambda _company: AcquisitionOutcome(
            "acme",
            AcquisitionStatus.SUCCESS,
            (_job(source),),
            raw_job_count=1,
        ),
    )
    result = getattr(module, wrapper_name)("acme")
    assert list(result[0].jobs) == [_job(source)]
    assert pipeline_metrics.acquisition_metrics_snapshot()[0].source == source


def test_async_production_company_wrappers_emit_metrics(monkeypatch):
    from src.scrapers import greenhouse_scraper, lever_scraper

    async def greenhouse_outcome(_session, company):
        return AcquisitionOutcome(
            company, AcquisitionStatus.SUCCESS, (_job("greenhouse"),)
        )

    async def lever_outcome(_session, company, **_kwargs):
        return AcquisitionOutcome(
            company, AcquisitionStatus.SUCCESS, (_job("lever"),)
        )

    monkeypatch.setattr(greenhouse_scraper, "_fetch_company_outcome", greenhouse_outcome)
    monkeypatch.setattr(lever_scraper, "_fetch_company_outcome", lever_outcome)
    asyncio.run(greenhouse_scraper.run_company(object(), "acme"))
    asyncio.run(
        pipeline_metrics.observe_acquisition_async(
            "lever",
            lambda: lever_scraper._fetch_company_outcome(object(), "acme"),
            schedule_on_success=True,
        )
    )
    assert [row.source for row in pipeline_metrics.acquisition_metrics_snapshot()] == [
        "greenhouse",
        "lever",
    ]


def test_unexpected_worker_failure_is_sanitized_and_does_not_cancel_success():
    async def failed():
        raise RuntimeError("secret provider body")

    async def succeeded():
        return AcquisitionOutcome(
            "good-co",
            AcquisitionStatus.SUCCESS,
            (_job("greenhouse", "good-co"),),
        )

    async def run_workers():
        return await asyncio.gather(
            pipeline_metrics.observe_acquisition_async(
                "greenhouse",
                failed,
                schedule_on_success=True,
                company="bad-co",
            ),
            pipeline_metrics.observe_acquisition_async(
                "greenhouse",
                succeeded,
                schedule_on_success=True,
                company="good-co",
            ),
            return_exceptions=True,
        )

    results = asyncio.run(run_workers())
    assert isinstance(results[0], RuntimeError)
    assert list(results[1].jobs) == [_job("greenhouse", "good-co")]
    metrics = pipeline_metrics.acquisition_metrics_snapshot()
    assert [(row.company, row.acquisition_status) for row in metrics] == [
        ("bad-co", "FAILED"),
        ("good-co", "SUCCESS"),
    ]
    assert metrics[0].reason_code == "parse_error"
    assert "secret provider body" not in repr(metrics[0])


def test_smartrecruiters_global_and_company_paths_remain_flat_and_observed(monkeypatch):
    from src.scrapers import smartrecruiters_scraper

    global_job = _job("smartrecruiters", "global-co", "global")
    board_job = _job("smartrecruiters", "board-co", "board")
    monkeypatch.setattr(
        smartrecruiters_scraper,
        "fetch_company_jobs",
        lambda _company: [global_job],
    )
    monkeypatch.setattr(
        smartrecruiters_scraper,
        "fetch_company_board",
        lambda _company: [board_job],
    )
    monkeypatch.setattr(smartrecruiters_scraper, "load_lines", lambda _path: ["board-co"])
    jobs = smartrecruiters_scraper.scrape_all_smartrecruiters()
    assert jobs == [global_job, board_job]
    assert [row.company for row in pipeline_metrics.acquisition_metrics_snapshot()] == [
        "<global_feed>",
        "board-co",
    ]


def test_builtin_path_remains_flat_and_observed(monkeypatch):
    from src.scrapers import builtin_scraper

    expected = _job("builtin", "built-in", "1")
    monkeypatch.setattr(
        builtin_scraper,
        "_fetch_builtin_outcome",
        lambda: AcquisitionOutcome(
            "<global_feed>", AcquisitionStatus.SUCCESS, (expected,), raw_job_count=1
        ),
    )
    monkeypatch.setattr(builtin_scraper, "learn_from_job_url", lambda _url: None)
    assert builtin_scraper.scrape_all_builtin() == [expected]
    assert pipeline_metrics.acquisition_metrics_snapshot()[0].source == "builtin"
