import asyncio
import inspect

import pytest

from src.discovery.crawl_scheduler import AcquisitionStatus
from src.pipeline.job_filter import filter_jobs
from src.scrapers import (
    greenhouse_scraper,
    lever_scraper,
    recruitee_scraper,
    workday_scraper,
)
from src.utils import pipeline_metrics


@pytest.fixture(autouse=True)
def _reset_acquisition_metrics():
    pipeline_metrics.reset_acquisition_metrics()
    yield
    pipeline_metrics.reset_acquisition_metrics()


class _AsyncResponse:
    def __init__(self, payload):
        self.status = 200
        self.headers = {}
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def json(self):
        return self._payload


class _AsyncSession:
    def __init__(self, payload):
        self._payload = payload

    def get(self, *args, **kwargs):
        return _AsyncResponse(self._payload)


class _SyncResponse:
    def __init__(self, payload):
        self.status_code = 200
        self.headers = {}
        self._payload = payload

    def json(self):
        return self._payload


def _greenhouse_outcome(monkeypatch):
    monkeypatch.setattr(greenhouse_scraper, "learn_from_job_url", lambda _url: None)
    payload = {
        "jobs": [
            {
                "id": "gh-1",
                "title": "Backend Engineer",
                "location": {"name": "London, UK"},
                "absolute_url": "https://boards.greenhouse.io/acme/jobs/gh-1",
                "updated_at": "2000-01-01T00:00:00Z",
            }
        ]
    }
    return asyncio.run(
        greenhouse_scraper._fetch_company_outcome(_AsyncSession(payload), "acme")
    )


def _lever_outcome(monkeypatch):
    monkeypatch.setattr(lever_scraper, "learn_from_job_url", lambda _url: None)
    payload = [
        {
            "id": "lv-1",
            "text": "Backend Engineer",
            "categories": {"location": "London, UK"},
            "hostedUrl": "https://jobs.lever.co/acme/lv-1",
            "createdAt": 946684800000,
        }
    ]
    return asyncio.run(
        lever_scraper._fetch_company_outcome(_AsyncSession(payload), "acme")
    )


def _workday_outcome(monkeypatch):
    captured_payloads = []
    payload = {
        "total": 1,
        "jobPostings": [
            {
                "externalPath": "/job/backend-engineer",
                "title": "Backend Engineer",
                "location": "London, UK",
                "postedDate": "2000-01-01",
            }
        ],
    }

    def post(*args, **kwargs):
        captured_payloads.append(dict(kwargs["json"]))
        return _SyncResponse(payload)

    monkeypatch.setattr(workday_scraper, "workday_post", post)
    monkeypatch.setattr(workday_scraper, "normalize_workday_url", lambda url: url)
    monkeypatch.setattr(workday_scraper, "learn_from_job_url", lambda _url: None)
    monkeypatch.setattr(workday_scraper.time, "sleep", lambda _seconds: None)
    outcome = workday_scraper._scrape_company_outcome(
        "https://acme.myworkdayjobs.com/jobs"
    )
    assert captured_payloads == [{"limit": 20, "offset": 0, "searchText": ""}]
    return outcome


def _recruitee_outcome(monkeypatch):
    payload = {
        "offers": [
            {
                "id": "rq-1",
                "title": "Backend Engineer",
                "location": "London, UK",
                "published_at": "2000-01-01T00:00:00Z",
                "careers_url": "https://acme.recruitee.com/o/backend-engineer",
            }
        ]
    }
    monkeypatch.setattr(
        recruitee_scraper,
        "_request_offers",
        lambda _tenant: _SyncResponse(payload),
    )
    return recruitee_scraper._fetch_company_outcome("acme")


@pytest.mark.parametrize(
    "outcome_factory",
    [
        _greenhouse_outcome,
        _lever_outcome,
        _workday_outcome,
        _recruitee_outcome,
    ],
    ids=["greenhouse", "lever", "workday", "recruitee"],
)
def test_acquisition_retains_nonmatching_non_us_and_old_jobs(
    monkeypatch, outcome_factory
):
    outcome = outcome_factory(monkeypatch)

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.raw_job_count == 1
    assert len(outcome.jobs) == 1
    assert outcome.jobs[0]["title"] == "Backend Engineer"
    assert outcome.jobs[0]["location"] in ("London, UK", ["London, UK"])


def test_central_filter_owns_role_location_and_freshness_rejections():
    jobs = [
        {
            "job_id": "title-drop",
            "title": "Backend Engineer",
            "company": "Acme",
            "location": "New York, NY, United States",
            "source": "greenhouse",
            "posted_at": "2099-01-01T00:00:00Z",
            "url": "https://example.test/title-drop",
        },
        {
            "job_id": "location-drop",
            "title": "Data Scientist",
            "company": "Acme",
            "location": "London, UK",
            "source": "lever",
            "posted_at": "2099-01-01T00:00:00Z",
            "url": "https://example.test/location-drop",
        },
        {
            "job_id": "freshness-drop",
            "title": "Data Scientist",
            "company": "Acme",
            "location": "United States",
            "source": "recruitee",
            "posted_at": "2000-01-01T00:00:00Z",
            "url": "https://example.test/freshness-drop",
        },
    ]

    filtered, diagnostics = filter_jobs(
        jobs,
        selected_role_families=["data_science"],
        return_diagnostics=True,
    )

    assert filtered == []
    assert diagnostics["title_mismatch"] == 1
    assert diagnostics["location_not_us"] == 1
    assert diagnostics["not_recent"] == 1

    selected = filter_jobs(
        [jobs[0]],
        selected_role_families=["backend_engineering"],
    )
    assert [job["job_id"] for job in selected] == ["title-drop"]


def test_source_health_counts_normalized_job_before_central_drop(monkeypatch):
    outcome = _recruitee_outcome(monkeypatch)
    observed = pipeline_metrics.observe_acquisition(
        "recruitee",
        lambda: outcome,
        schedule_on_success=True,
    )
    filtered, diagnostics = filter_jobs(
        list(observed.jobs),
        selected_role_families=["data_science"],
        return_diagnostics=True,
    )
    metric = pipeline_metrics.acquisition_metrics_snapshot()[0]

    assert observed.status is AcquisitionStatus.SUCCESS
    assert metric.raw_job_count == 1
    assert metric.normalized_job_count == 1
    assert metric.schedule_advanced is True
    assert filtered == []
    assert diagnostics["title_mismatch"] == 1


@pytest.mark.parametrize(
    ("module", "owner"),
    [
        (greenhouse_scraper, greenhouse_scraper._fetch_company_outcome),
        (lever_scraper, lever_scraper._fetch_company_outcome),
        (workday_scraper, workday_scraper._scrape_company_outcome),
        (recruitee_scraper, recruitee_scraper._fetch_company_outcome),
    ],
)
def test_acquisition_owners_have_no_relevance_predicates(module, owner):
    source = inspect.getsource(owner)
    for predicate in (
        "title_matches",
        "us_location",
        "posted_within_24h",
        "appliedFacets",
        "JOB_STACK_SELECTED_ROLE_FAMILIES",
    ):
        assert predicate not in source

    assert not hasattr(module, "title_matches")
    assert not hasattr(module, "us_location")
    assert not hasattr(module, "posted_within_24h")


def test_genuinely_empty_provider_boards_remain_empty(monkeypatch):
    greenhouse = asyncio.run(
        greenhouse_scraper._fetch_company_outcome(
            _AsyncSession({"jobs": []}), "greenhouse-empty"
        )
    )
    lever = asyncio.run(
        lever_scraper._fetch_company_outcome(_AsyncSession([]), "lever-empty")
    )
    monkeypatch.setattr(
        workday_scraper,
        "workday_post",
        lambda *args, **kwargs: _SyncResponse({"total": 0, "jobPostings": []}),
    )
    workday = workday_scraper._scrape_company_outcome(
        "https://empty.myworkdayjobs.com/jobs"
    )
    monkeypatch.setattr(
        recruitee_scraper,
        "_request_offers",
        lambda _tenant: _SyncResponse({"offers": []}),
    )
    recruitee = recruitee_scraper._fetch_company_outcome("recruitee-empty")

    assert [greenhouse.status, lever.status, workday.status, recruitee.status] == [
        AcquisitionStatus.EMPTY,
        AcquisitionStatus.EMPTY,
        AcquisitionStatus.EMPTY,
        AcquisitionStatus.EMPTY,
    ]
