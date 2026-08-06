import asyncio
from collections import Counter
from dataclasses import FrozenInstanceError

import pytest

from src.discovery import crawl_scheduler
from src.discovery.crawl_scheduler import AcquisitionOutcome, AcquisitionStatus
from src.scrapers import (
    ashby_scraper,
    greenhouse_scraper,
    jobvite_scraper,
    lever_scraper,
    recruitee_scraper,
    smartrecruiters_scraper,
    workable_scraper,
    workday_scraper,
)


def _job(company, suffix="job"):
    return {
        "company": company,
        "job_id": f"{company}-{suffix}",
        "title": f"{company} engineer",
    }


class _SyncResponse:
    def __init__(self, payload=None, status_code=200, text="", json_error=False):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("malformed fixture")
        return self._payload


class _AsyncResponse:
    def __init__(self, payload=None, status=200, json_error=False):
        self.status = status
        self._payload = payload
        self._json_error = json_error

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def json(self):
        if self._json_error:
            raise ValueError("malformed fixture")
        return self._payload


class _AsyncSession:
    def __init__(self, response=None, error=None):
        self._response = response
        self._error = error

    def get(self, *args, **kwargs):
        if self._error:
            raise self._error
        return self._response


class _AsyncSessionContext:
    async def __aenter__(self):
        return object()

    async def __aexit__(self, exc_type, exc, tb):
        return None


def test_outcome_vocabulary_validation_and_immutability():
    success = AcquisitionOutcome(
        "acme",
        AcquisitionStatus.SUCCESS,
        (_job("acme"),),
        page_count=1,
    )
    empty = AcquisitionOutcome("empty", AcquisitionStatus.EMPTY)
    partial = AcquisitionOutcome(
        "partial",
        AcquisitionStatus.PARTIAL,
        (_job("partial"),),
        reason="pagination_interrupted",
        page_count=1,
    )
    failed = AcquisitionOutcome(
        "failed",
        AcquisitionStatus.FAILED,
        reason="transport_error",
    )

    assert success.should_mark_scraped is True
    assert empty.should_mark_scraped is True
    assert partial.should_mark_scraped is False
    assert failed.should_mark_scraped is False

    with pytest.raises(FrozenInstanceError):
        success.status = AcquisitionStatus.FAILED
    with pytest.raises(ValueError):
        AcquisitionOutcome("acme", "SUCCESS", (_job("acme"),))
    with pytest.raises(ValueError):
        AcquisitionOutcome("acme", AcquisitionStatus.SUCCESS)
    with pytest.raises(ValueError):
        AcquisitionOutcome(
            "acme",
            AcquisitionStatus.FAILED,
            reason="raw exception text",
        )


def test_historical_schedule_records_remain_compatible(monkeypatch):
    monkeypatch.setattr(crawl_scheduler.time, "time", lambda: 10_000)

    assert crawl_scheduler.should_scrape("new", {}) is True
    assert crawl_scheduler.should_scrape(
        "recent",
        {"recent": {"last_scraped": 10_000}},
    ) is False
    assert crawl_scheduler.should_scrape(
        "old",
        {"old": {"last_scraped": 10_000 - crawl_scheduler.CRAWL_INTERVAL}},
    ) is True


def _fixture_parallel(completion_order):
    def run_parallel(items, worker_fn, max_workers=10, desc="Processing"):
        assert Counter(items) == Counter(completion_order)
        results = []
        for company in completion_order:
            try:
                value = worker_fn(company)
            except Exception:
                continue
            if value:
                results.extend(value)
        return results

    return run_parallel


@pytest.mark.parametrize(
    ("scraper", "entrypoint", "outcome_worker"),
    [
        (workday_scraper, "scrape_all_workday", "_scrape_company_outcome"),
        (workable_scraper, "scrape_all_workable", "_fetch_company_outcome"),
        (jobvite_scraper, "scrape_all_jobvite", "_fetch_company_outcome"),
        (ashby_scraper, "scrape_all_ashby", "_fetch_company_outcome"),
        (recruitee_scraper, "scrape_all_recruitee", "_fetch_company_outcome"),
    ],
    ids=["workday", "workable", "jobvite", "ashby", "recruitee"],
)
def test_threaded_schedule_matrix_and_completion_ownership(
    monkeypatch,
    scraper,
    entrypoint,
    outcome_worker,
):
    companies = ["success", "empty", "partial", "raised", "failed"]
    completion_order = ["partial", "failed", "empty", "raised", "success"]
    schedule = {"historical": {"last_scraped": 1}}
    marked = []
    saved = []

    def outcome_for(company):
        if company == "raised":
            raise RuntimeError("fixture worker exception")
        if company == "success":
            return AcquisitionOutcome(
                company,
                AcquisitionStatus.SUCCESS,
                (_job(company),),
            )
        if company == "empty":
            return AcquisitionOutcome(company, AcquisitionStatus.EMPTY)
        if company == "partial":
            return AcquisitionOutcome(
                company,
                AcquisitionStatus.PARTIAL,
                (_job(company),),
                reason="pagination_interrupted",
            )
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason="transport_error",
        )

    monkeypatch.setattr(scraper, "load_lines", lambda path: list(companies))
    monkeypatch.setattr(scraper, "load_schedule", lambda: schedule)
    monkeypatch.setattr(scraper, "should_scrape", lambda company, value: True)
    monkeypatch.setattr(scraper, "mark_scraped", lambda company, value: marked.append(company))
    monkeypatch.setattr(scraper, "save_schedule", lambda value: saved.append(value))
    monkeypatch.setattr(scraper, outcome_worker, outcome_for)
    monkeypatch.setattr(scraper, "run_parallel", _fixture_parallel(completion_order))

    jobs = getattr(scraper, entrypoint)()

    assert jobs == [_job("partial"), _job("success")]
    assert marked == ["empty", "success"]
    assert saved == [schedule]
    assert schedule == {"historical": {"last_scraped": 1}}
    assert all(isinstance(job, dict) for job in jobs)


@pytest.mark.parametrize("scraper", [greenhouse_scraper, lever_scraper])
def test_async_schedule_matrix_and_completion_ownership(monkeypatch, scraper):
    companies = ["success", "empty", "partial", "raised", "failed"]
    schedule = {}
    marked = []
    saved = []

    async def outcome_for(session, company, **kwargs):
        if company == "raised":
            raise RuntimeError("fixture worker exception")
        if company == "success":
            return AcquisitionOutcome(
                company,
                AcquisitionStatus.SUCCESS,
                (_job(company),),
            )
        if company == "empty":
            return AcquisitionOutcome(company, AcquisitionStatus.EMPTY)
        if company == "partial":
            return AcquisitionOutcome(
                company,
                AcquisitionStatus.PARTIAL,
                (_job(company),),
                reason="parse_error",
            )
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason="transport_error",
        )

    monkeypatch.setattr(scraper, "load_lines", lambda path: list(companies))
    monkeypatch.setattr(scraper, "load_schedule", lambda: schedule)
    monkeypatch.setattr(scraper, "should_scrape", lambda company, value: True)
    monkeypatch.setattr(scraper, "mark_scraped", lambda company, value: marked.append(company))
    monkeypatch.setattr(scraper, "save_schedule", lambda value: saved.append(value))
    monkeypatch.setattr(scraper, "_fetch_company_outcome", outcome_for)
    monkeypatch.setattr(scraper, "tqdm", lambda iterable, **kwargs: iterable)
    monkeypatch.setattr(scraper.aiohttp, "TCPConnector", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        scraper.aiohttp,
        "ClientSession",
        lambda *args, **kwargs: _AsyncSessionContext(),
    )

    if scraper is greenhouse_scraper:
        jobs = asyncio.run(scraper.scrape_all_greenhouse_async())
    else:
        jobs = asyncio.run(scraper.scrape_all_lever_async())

    assert Counter(job["company"] for job in jobs) == Counter({"success": 1, "partial": 1})
    assert Counter(marked) == Counter({"success": 1, "empty": 1})
    assert saved == [schedule]
    assert all(isinstance(job, dict) for job in jobs)


def _workday_posting(index):
    return {
        "externalPath": f"/job/{index}",
        "title": "Software Engineer",
        "location": "New York, NY",
        "postedDate": "2026-08-02",
    }


def test_workday_outcomes_include_partial_pagination(monkeypatch):
    board = "https://acme.myworkdayjobs.com/jobs"
    monkeypatch.setattr(workday_scraper, "normalize_workday_url", lambda url: url)
    monkeypatch.setattr(workday_scraper, "learn_from_job_url", lambda url: None)
    monkeypatch.setattr(workday_scraper.time, "sleep", lambda seconds: None)

    first_page = _SyncResponse(
        {"total": 40, "jobPostings": [_workday_posting(i) for i in range(20)]}
    )
    responses = iter([first_page, _SyncResponse(status_code=503)])
    monkeypatch.setattr(workday_scraper, "workday_post", lambda *args, **kwargs: next(responses))
    partial = workday_scraper._scrape_company_outcome(board)

    malformed_second_page = _workday_posting(20)
    malformed_second_page["jobPostingInfo"] = "invalid"
    responses = iter([
        first_page,
        _SyncResponse({"total": 21, "jobPostings": [malformed_second_page]}),
    ])
    monkeypatch.setattr(workday_scraper, "workday_post", lambda *args, **kwargs: next(responses))
    parse_partial = workday_scraper._scrape_company_outcome(board)

    monkeypatch.setattr(
        workday_scraper,
        "workday_post",
        lambda *args, **kwargs: _SyncResponse({"total": 0, "jobPostings": []}),
    )
    empty = workday_scraper._scrape_company_outcome(board)
    monkeypatch.setattr(
        workday_scraper,
        "workday_post",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("offline")),
    )
    failed = workday_scraper._scrape_company_outcome(board)
    monkeypatch.setattr(
        workday_scraper,
        "workday_post",
        lambda *args, **kwargs: _SyncResponse(status_code=503),
    )
    non_200 = workday_scraper._scrape_company_outcome(board)
    monkeypatch.setattr(
        workday_scraper,
        "workday_post",
        lambda *args, **kwargs: _SyncResponse(payload=[], status_code=200),
    )
    malformed = workday_scraper._scrape_company_outcome(board)

    assert partial.status is AcquisitionStatus.PARTIAL
    assert len(partial.jobs) == 20
    assert partial.reason == "pagination_interrupted"
    assert parse_partial.status is AcquisitionStatus.PARTIAL
    assert len(parse_partial.jobs) == 20
    assert parse_partial.reason == "parse_error"
    assert empty.status is AcquisitionStatus.EMPTY
    assert empty.should_mark_scraped is True
    assert failed.status is AcquisitionStatus.FAILED
    assert failed.reason == "transport_error"
    assert non_200.status is AcquisitionStatus.FAILED
    assert non_200.reason == "non_200_response"
    assert malformed.status is AcquisitionStatus.FAILED
    assert malformed.reason == "malformed_payload"


def _workable_posting(index):
    return {
        "id": f"job-{index}",
        "title": "Software Engineer",
        "city": "New York",
        "state": "NY",
        "country": "US",
        "url": f"https://apply.workable.com/acme/j/job-{index}/",
        "published": "2026-08-02",
    }


def test_workable_stable_id_precedence_and_fallbacks():
    assert workable_scraper._workable_stable_id(
        {
            "shortcode": "SHORTCODE",
            "url": "https://apply.workable.com/acme/j/URL-TOKEN/",
            "id": "PROVIDER-ID",
            "code": "PROVIDER-CODE",
        }
    ) == "SHORTCODE"
    assert workable_scraper._workable_stable_id(
        {
            "application_url": "https://apply.workable.com/acme/j/URL-TOKEN/?x=1",
            "id": "PROVIDER-ID",
            "code": "PROVIDER-CODE",
        }
    ) == "URL-TOKEN"
    assert workable_scraper._workable_stable_id(
        {"id": "PROVIDER-ID", "code": "PROVIDER-CODE"}
    ) == "PROVIDER-ID"
    assert workable_scraper._workable_stable_id(
        {"code": "PROVIDER-CODE"}
    ) == "PROVIDER-CODE"


@pytest.mark.parametrize(
    "field_name",
    ["shortcode", "url", "shortlink", "application_url", "id", "code"],
)
def test_workable_stable_id_rejects_unsupported_identifier_types(field_name):
    with pytest.raises(ValueError, match="unsupported Workable stable identifier"):
        workable_scraper._workable_stable_id({field_name: ["unsupported"]})


def test_workable_outcome_uses_stable_identity_without_source_dedupe(monkeypatch):
    rows = [
        {
            **_workable_posting(1),
            "id": "REUSED-ID",
            "shortcode": "FIRST-SHORTCODE",
            "url": "https://apply.workable.com/acme/j/FIRST-SHORTCODE/",
            "title": "First Posting",
            "city": "New York",
        },
        {
            **_workable_posting(2),
            "id": "REUSED-ID",
            "shortcode": "SECOND-SHORTCODE",
            "url": "https://apply.workable.com/acme/j/SECOND-SHORTCODE/",
            "title": "Second Posting",
            "city": "Boston",
        },
        {
            **_workable_posting(3),
            "id": "ANOTHER-ID",
            "shortcode": "FIRST-SHORTCODE",
            "url": "https://apply.workable.com/acme/j/FIRST-SHORTCODE/",
            "title": "First Posting",
            "city": "Chicago",
        },
    ]
    stable_id_calls = []
    real_stable_id = workable_scraper._workable_stable_id

    def stable_id(job):
        stable_id_calls.append(job)
        return real_stable_id(job)

    monkeypatch.setattr(workable_scraper, "_workable_stable_id", stable_id)
    monkeypatch.setattr(workable_scraper, "learn_from_job_url", lambda _url: None)
    monkeypatch.setattr(
        workable_scraper,
        "workable_get",
        lambda *args, **kwargs: _SyncResponse({"jobs": rows}),
    )

    outcome = workable_scraper._fetch_company_outcome("acme")

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert stable_id_calls == rows
    assert [job["job_id"] for job in outcome.jobs] == [
        "wb_FIRST-SHORTCODE",
        "wb_SECOND-SHORTCODE",
        "wb_FIRST-SHORTCODE",
    ]
    assert [job["url"] for job in outcome.jobs] == [row["url"] for row in rows]
    assert len(outcome.jobs) == 3


def test_workable_outcome_uses_url_token_when_shortcode_is_absent(monkeypatch):
    row = {
        **_workable_posting(1),
        "id": "PROVIDER-ID",
        "shortcode": "",
        "url": "https://apply.workable.com/acme/j/URL-OWNS-IDENTITY/",
    }
    monkeypatch.setattr(workable_scraper, "learn_from_job_url", lambda _url: None)
    monkeypatch.setattr(
        workable_scraper,
        "workable_get",
        lambda *args, **kwargs: _SyncResponse({"jobs": [row]}),
    )

    outcome = workable_scraper._fetch_company_outcome("acme")

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.jobs[0]["job_id"] == "wb_URL-OWNS-IDENTITY"
    assert outcome.jobs[0]["url"] == row["url"]


def test_workable_outcomes_include_success_empty_and_failures(monkeypatch):
    monkeypatch.setattr(
        workable_scraper,
        "learn_from_job_url",
        lambda url: None,
    )

    monkeypatch.setattr(
        workable_scraper,
        "workable_get",
        lambda *args, **kwargs: _SyncResponse(
            {
                "jobs": [
                    _workable_posting(index)
                    for index in range(3)
                ]
            }
        ),
    )
    success = workable_scraper._fetch_company_outcome("acme")

    monkeypatch.setattr(
        workable_scraper,
        "workable_get",
        lambda *args, **kwargs: _SyncResponse(
            {"jobs": []}
        ),
    )
    empty = workable_scraper._fetch_company_outcome("empty")

    monkeypatch.setattr(
        workable_scraper,
        "workable_get",
        lambda *args, **kwargs: (
            _ for _ in ()
        ).throw(OSError("offline")),
    )
    failed = workable_scraper._fetch_company_outcome("failed")

    monkeypatch.setattr(
        workable_scraper,
        "workable_get",
        lambda *args, **kwargs: _SyncResponse(
            status_code=503
        ),
    )
    non_200 = workable_scraper._fetch_company_outcome(
        "missing"
    )

    monkeypatch.setattr(
        workable_scraper,
        "workable_get",
        lambda *args, **kwargs: _SyncResponse(
            payload=[]
        ),
    )
    malformed = workable_scraper._fetch_company_outcome(
        "malformed"
    )

    assert success.status is AcquisitionStatus.SUCCESS
    assert len(success.jobs) == 3
    assert success.page_count == 1
    assert success.raw_job_count == 3

    assert empty.status is AcquisitionStatus.EMPTY
    assert empty.page_count == 1
    assert empty.should_mark_scraped is True

    assert failed.status is AcquisitionStatus.FAILED
    assert failed.reason == "transport_error"
    assert failed.should_mark_scraped is False

    assert non_200.status is AcquisitionStatus.FAILED
    assert non_200.reason == "non_200_response"

    assert malformed.status is AcquisitionStatus.FAILED
    assert malformed.reason == "malformed_payload"


def test_jobvite_success_empty_and_failure_outcomes(monkeypatch):
    real_beautiful_soup = jobvite_scraper.BeautifulSoup
    monkeypatch.setattr(jobvite_scraper, "learn_from_job_url", lambda url: None)
    monkeypatch.setattr(
        jobvite_scraper,
        "jobvite_get",
        lambda *args, **kwargs: _SyncResponse(
            text='<a href="/acme/job/abc123">Software Engineer</a>'
        ),
    )
    success = jobvite_scraper._fetch_company_outcome("acme")

    monkeypatch.setattr(
        jobvite_scraper,
        "jobvite_get",
        lambda *args, **kwargs: _SyncResponse(text="<html><body>No jobs</body></html>"),
    )
    empty = jobvite_scraper._fetch_company_outcome("empty")
    monkeypatch.setattr(
        jobvite_scraper,
        "jobvite_get",
        lambda *args, **kwargs: _SyncResponse(status_code=404),
    )
    non_200 = jobvite_scraper._fetch_company_outcome("missing")
    monkeypatch.setattr(
        jobvite_scraper,
        "jobvite_get",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("offline")),
    )
    transport = jobvite_scraper._fetch_company_outcome("failed")
    monkeypatch.setattr(
        jobvite_scraper,
        "jobvite_get",
        lambda *args, **kwargs: _SyncResponse(text="<html>malformed fixture</html>"),
    )
    monkeypatch.setattr(
        jobvite_scraper,
        "BeautifulSoup",
        lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("bad html")),
    )
    malformed = jobvite_scraper._fetch_company_outcome("malformed")
    monkeypatch.setattr(jobvite_scraper, "BeautifulSoup", real_beautiful_soup)

    assert success.status is AcquisitionStatus.SUCCESS
    assert len(success.jobs) == 1
    assert empty.status is AcquisitionStatus.EMPTY
    assert non_200.status is AcquisitionStatus.FAILED
    assert non_200.reason == "non_200_response"
    assert transport.status is AcquisitionStatus.FAILED
    assert transport.reason == "transport_error"
    assert malformed.status is AcquisitionStatus.FAILED
    assert malformed.reason == "parse_error"


def _greenhouse_payload():
    return {
        "jobs": [
            {
                "id": "gh-1",
                "title": "Software Engineer",
                "location": {"name": "New York, NY"},
                "absolute_url": "https://boards.greenhouse.io/acme/jobs/gh-1",
                "updated_at": "2026-08-02",
            }
        ]
    }


def test_greenhouse_success_empty_and_failure_outcomes(monkeypatch):
    async def no_sleep(seconds):
        return None

    monkeypatch.setattr(greenhouse_scraper.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(greenhouse_scraper, "learn_from_job_url", lambda url: None)

    success = asyncio.run(
        greenhouse_scraper._fetch_company_outcome(
            _AsyncSession(_AsyncResponse(_greenhouse_payload())), "acme"
        )
    )
    empty = asyncio.run(
        greenhouse_scraper._fetch_company_outcome(
            _AsyncSession(_AsyncResponse({"jobs": []})), "empty"
        )
    )
    non_200 = asyncio.run(
        greenhouse_scraper._fetch_company_outcome(
            _AsyncSession(_AsyncResponse(status=503)), "missing"
        )
    )
    malformed = asyncio.run(
        greenhouse_scraper._fetch_company_outcome(
            _AsyncSession(_AsyncResponse(payload=[])), "malformed"
        )
    )
    transport = asyncio.run(
        greenhouse_scraper._fetch_company_outcome(
            _AsyncSession(error=OSError("offline")), "failed"
        )
    )
    monkeypatch.setattr(
        greenhouse_scraper,
        "Job",
        lambda **kwargs: (_ for _ in ()).throw(ValueError("bad posting")),
    )
    parse_error = asyncio.run(
        greenhouse_scraper._fetch_company_outcome(
            _AsyncSession(_AsyncResponse(_greenhouse_payload())), "parse"
        )
    )

    assert success.status is AcquisitionStatus.SUCCESS
    assert empty.status is AcquisitionStatus.EMPTY
    assert non_200.status is AcquisitionStatus.FAILED
    assert malformed.reason == "malformed_payload"
    assert transport.reason == "transport_error"
    assert parse_error.reason == "parse_error"


def _lever_payload():
    return [
        {
            "id": "lv-1",
            "text": "Software Engineer",
            "categories": {"location": "New York, NY"},
            "hostedUrl": "https://jobs.lever.co/acme/lv-1",
            "createdAt": 4102444800000,
        }
    ]


def test_lever_success_empty_and_failure_outcomes(monkeypatch):
    async def no_sleep(seconds):
        return None

    monkeypatch.setattr(lever_scraper.asyncio, "sleep", no_sleep)
    monkeypatch.setattr(lever_scraper, "learn_from_job_url", lambda url: None)

    success = asyncio.run(
        lever_scraper._fetch_company_outcome(
            _AsyncSession(_AsyncResponse(_lever_payload())), "acme"
        )
    )
    empty = asyncio.run(
        lever_scraper._fetch_company_outcome(
            _AsyncSession(_AsyncResponse([])), "empty"
        )
    )
    non_200 = asyncio.run(
        lever_scraper._fetch_company_outcome(
            _AsyncSession(_AsyncResponse(status=503)), "missing"
        )
    )
    malformed = asyncio.run(
        lever_scraper._fetch_company_outcome(
            _AsyncSession(_AsyncResponse({"jobs": []})), "malformed"
        )
    )
    transport = asyncio.run(
        lever_scraper._fetch_company_outcome(
            _AsyncSession(error=OSError("offline")), "failed"
        )
    )
    parse_error = asyncio.run(
        lever_scraper._fetch_company_outcome(
            _AsyncSession(
                _AsyncResponse([
                    {
                        "id": "bad",
                        "text": "Software Engineer",
                        "categories": "invalid",
                    }
                ])
            ),
            "parse",
        )
    )

    assert success.status is AcquisitionStatus.SUCCESS
    assert empty.status is AcquisitionStatus.EMPTY
    assert non_200.reason == "non_200_response"
    assert malformed.reason == "malformed_payload"
    assert transport.reason == "transport_error"
    assert parse_error.reason == "parse_error"


def _ashby_payload(postings):
    return {"data": {"jobBoard": {"jobPostings": postings}}}


def test_ashby_success_empty_and_failure_outcomes(monkeypatch):
    monkeypatch.setattr(ashby_scraper, "learn_from_job_url", lambda url: None)
    monkeypatch.setattr(
        ashby_scraper,
        "http_post",
        lambda *args, **kwargs: _SyncResponse(
            _ashby_payload([
                {"id": "as-1", "title": "Software Engineer", "locationName": "Remote"}
            ])
        ),
    )
    success = ashby_scraper._fetch_company_outcome("acme")
    monkeypatch.setattr(
        ashby_scraper,
        "http_post",
        lambda *args, **kwargs: _SyncResponse(_ashby_payload([])),
    )
    empty = ashby_scraper._fetch_company_outcome("empty")
    monkeypatch.setattr(
        ashby_scraper,
        "http_post",
        lambda *args, **kwargs: _SyncResponse(status_code=503),
    )
    non_200 = ashby_scraper._fetch_company_outcome("missing")
    monkeypatch.setattr(
        ashby_scraper,
        "http_post",
        lambda *args, **kwargs: _SyncResponse(payload=[], status_code=200),
    )
    malformed = ashby_scraper._fetch_company_outcome("malformed")
    monkeypatch.setattr(
        ashby_scraper,
        "http_post",
        lambda *args, **kwargs: (_ for _ in ()).throw(OSError("offline")),
    )
    transport = ashby_scraper._fetch_company_outcome("failed")
    monkeypatch.setattr(
        ashby_scraper,
        "http_post",
        lambda *args, **kwargs: _SyncResponse(
            _ashby_payload([
                {"id": "as-2", "title": "Engineer", "locationName": "Remote"}
            ])
        ),
    )
    monkeypatch.setattr(
        ashby_scraper,
        "learn_from_job_url",
        lambda url: (_ for _ in ()).throw(ValueError("bad posting")),
    )
    parse_error = ashby_scraper._fetch_company_outcome("parse")

    assert success.status is AcquisitionStatus.SUCCESS
    assert empty.status is AcquisitionStatus.EMPTY
    assert non_200.reason == "non_200_response"
    assert malformed.reason == "malformed_payload"
    assert transport.reason == "transport_error"
    assert parse_error.reason == "parse_error"


def test_smartrecruiters_remains_unscheduled(monkeypatch):
    monkeypatch.setattr(
        smartrecruiters_scraper,
        "fetch_company_jobs",
        lambda company: [_job("global")],
    )
    monkeypatch.setattr(
        smartrecruiters_scraper,
        "fetch_company_board",
        lambda company: [_job(company)],
    )
    monkeypatch.setattr(
        smartrecruiters_scraper,
        "load_lines",
        lambda path: ["acme"],
    )
    monkeypatch.setattr(
        smartrecruiters_scraper,
        "run_parallel",
        lambda items, worker_fn, **kwargs: [worker_fn(items[0])[0]],
    )

    jobs = smartrecruiters_scraper.scrape_all_smartrecruiters()

    assert jobs == [_job("global"), _job("acme")]
    assert not any(
        hasattr(smartrecruiters_scraper, name)
        for name in ("load_schedule", "save_schedule", "mark_scraped", "should_scrape")
    )
