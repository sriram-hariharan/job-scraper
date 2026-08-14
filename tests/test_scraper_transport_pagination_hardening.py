import asyncio
from datetime import datetime, timezone
from email.utils import format_datetime
from pathlib import Path

import pytest
import requests

from src.config import consts
from src.discovery.crawl_scheduler import AcquisitionStatus
from src.scrapers import (
    builtin_scraper,
    greenhouse_scraper,
    lever_scraper,
    workable_scraper,
    workday_scraper,
)
from src.utils import http_retry


class _Response:
    def __init__(self, payload=None, *, status_code=200, headers=None):
        self.status_code = status_code
        self.headers = headers or {}
        self._payload = payload

    def json(self):
        return self._payload


class _AsyncResponse:
    def __init__(self, payload=None, *, status=200, headers=None):
        self.status = status
        self.headers = headers or {}
        self._payload = payload

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def json(self):
        return self._payload


class _AsyncSequenceSession:
    def __init__(self, responses):
        self.responses = iter(responses)
        self.calls = 0

    def get(self, *args, **kwargs):
        self.calls += 1
        value = next(self.responses)
        if isinstance(value, BaseException):
            raise value
        return value


def _job(company, suffix="1"):
    return {
        "company": company,
        "job_id": f"{company}-{suffix}",
        "title": "Software Engineer",
    }


def _workday_posting(index):
    return {
        "externalPath": f"/job/{index}",
        "title": "Software Engineer",
        "location": "New York, NY",
        "postedDate": "2026-08-02",
    }


def _workable_posting(index):
    return {
        "id": f"job-{index}",
        "shortcode": f"JOB{index}",
        "title": "Software Engineer",
        "city": "New York",
        "state": "NY",
        "country": "US",
        "url": f"https://apply.workable.com/acme/j/JOB{index}/",
        "published": "2026-08-02",
    }


def _prepare_workday(monkeypatch):
    monkeypatch.setattr(workday_scraper, "normalize_workday_url", lambda url: url)
    monkeypatch.setattr(workday_scraper, "learn_from_job_url", lambda url: None)
    monkeypatch.setattr(workday_scraper.time, "sleep", lambda seconds: None)


def _prepare_workable(monkeypatch):
    monkeypatch.setattr(workable_scraper, "learn_from_job_url", lambda url: None)
    monkeypatch.setattr(
        workable_scraper,
        "workable_get",
        lambda *args, **kwargs: _Response({"jobs": []}),
    )


@pytest.mark.parametrize("module", [greenhouse_scraper, lever_scraper])
def test_async_sessions_use_finite_total_timeout(monkeypatch, module):
    captured = {}

    class _SessionContext:
        async def __aenter__(self):
            return object()

        async def __aexit__(self, exc_type, exc, tb):
            return None

    def client_session(*args, **kwargs):
        captured.update(kwargs)
        return _SessionContext()

    monkeypatch.setattr(module, "load_lines", lambda path: [])
    monkeypatch.setattr(module, "load_schedule", lambda: {})
    monkeypatch.setattr(module, "save_schedule", lambda schedule: None)
    monkeypatch.setattr(module.aiohttp, "TCPConnector", lambda *args, **kwargs: None)
    monkeypatch.setattr(module.aiohttp, "ClientSession", client_session)

    if module is greenhouse_scraper:
        asyncio.run(module.scrape_all_greenhouse_async())
    else:
        asyncio.run(module.scrape_all_lever_async())

    timeout = captured["timeout"]
    assert timeout.total == consts.SCRAPER_ASYNC_TOTAL_TIMEOUT_SECONDS
    assert 0 < timeout.total < float("inf")


def test_shared_sync_requests_have_default_timeout_and_preserve_explicit_timeout(
    monkeypatch,
):
    calls = []

    def request(url, **kwargs):
        calls.append((url, kwargs["timeout"]))
        return _Response()

    monkeypatch.setattr(http_retry.requests, "get", request)
    monkeypatch.setattr(http_retry.requests, "post", request)

    http_retry.http_get("https://fixture.invalid/get")
    http_retry.http_post("https://fixture.invalid/post", timeout=17)

    assert calls == [
        ("https://fixture.invalid/get", consts.SCRAPER_HTTP_TIMEOUT_SECONDS),
        ("https://fixture.invalid/post", 17),
    ]


def test_builtin_preserves_existing_timeout(monkeypatch):
    captured = []

    class _BuiltinResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self):
            return b"fixture"

    def urlopen(request, *, timeout):
        captured.append(timeout)
        return _BuiltinResponse()

    monkeypatch.setattr(builtin_scraper, "urlopen", urlopen)

    assert builtin_scraper.fetch_builtin_jobs_html() == "fixture"
    assert captured == [consts.BUILTIN_HTTP_TIMEOUT_SECONDS]
    assert consts.BUILTIN_HTTP_TIMEOUT_SECONDS == 15


@pytest.mark.parametrize("status", [429, 500, 502, 503, 504])
def test_transient_statuses_retry_once(monkeypatch, status):
    responses = iter([_Response(status_code=status), _Response(status_code=200)])
    calls = []
    sleeps = []

    def request(url, **kwargs):
        calls.append(True)
        return next(responses)

    monkeypatch.setattr(http_retry.requests, "get", request)
    monkeypatch.setattr(http_retry.time, "sleep", sleeps.append)

    assert http_retry.http_get("https://fixture.invalid/read").status_code == 200
    assert len(calls) == 2
    assert sleeps == [consts.SCRAPER_RETRY_DELAY_SECONDS]


@pytest.mark.parametrize("status", [400, 401, 403, 404, 422])
def test_non_transient_statuses_do_not_retry(monkeypatch, status):
    calls = []
    monkeypatch.setattr(
        http_retry.time,
        "sleep",
        lambda seconds: (_ for _ in ()).throw(AssertionError("unexpected sleep")),
    )

    def request(url, **kwargs):
        calls.append(True)
        return _Response(status_code=status)

    monkeypatch.setattr(http_retry.requests, "get", request)

    assert http_retry.http_get("https://fixture.invalid/read").status_code == status
    assert len(calls) == 1


@pytest.mark.parametrize(
    ("headers", "expected"),
    [
        ({"Retry-After": "7"}, 7.0),
        ({"Retry-After": "malformed"}, consts.SCRAPER_RETRY_DELAY_SECONDS),
        ({}, consts.SCRAPER_RETRY_DELAY_SECONDS),
        ({"Retry-After": "-4"}, 0.0),
        ({"Retry-After": "9999"}, consts.SCRAPER_RETRY_MAX_DELAY_SECONDS),
    ],
)
def test_retry_after_numeric_fallback_negative_and_cap(headers, expected):
    assert http_retry.retry_delay_seconds(headers) == expected


def test_retry_after_http_date_uses_injected_clock_and_handles_expired_date():
    now = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc).timestamp()
    future = format_datetime(datetime(2026, 8, 2, 12, 0, 12, tzinfo=timezone.utc))
    expired = format_datetime(datetime(2026, 8, 2, 11, 59, tzinfo=timezone.utc))

    assert http_retry.retry_delay_seconds({"Retry-After": future}, now=now) == 12.0
    assert http_retry.retry_delay_seconds({"Retry-After": expired}, now=now) == 0.0


def test_retry_delay_is_deterministic_and_has_no_jitter(monkeypatch):
    responses = iter([
        _Response(status_code=429, headers={"Retry-After": "3"}),
        _Response(status_code=200),
    ])
    sleeps = []

    def request(url, **kwargs):
        return next(responses)

    monkeypatch.setattr(http_retry.requests, "get", request)
    monkeypatch.setattr(http_retry.time, "sleep", sleeps.append)
    http_retry.http_get("https://fixture.invalid/read")

    assert sleeps == [3.0]
    assert "random" not in http_retry.__dict__


@pytest.mark.parametrize(
    "error",
    [requests.Timeout("fixture"), requests.ConnectionError("fixture")],
)
def test_supported_transport_exceptions_retry(monkeypatch, error):
    responses = iter([error, _Response()])
    calls = []
    monkeypatch.setattr(http_retry.time, "sleep", lambda seconds: None)

    def request(url, **kwargs):
        calls.append(True)
        value = next(responses)
        if isinstance(value, BaseException):
            raise value
        return value

    monkeypatch.setattr(http_retry.requests, "get", request)

    assert http_retry.http_get("https://fixture.invalid/read").status_code == 200
    assert len(calls) == 2


def test_unsupported_exception_propagates_without_retry_or_success(monkeypatch):
    calls = []
    monkeypatch.setattr(
        http_retry.time,
        "sleep",
        lambda seconds: (_ for _ in ()).throw(AssertionError("unexpected sleep")),
    )

    def request(url, **kwargs):
        calls.append(True)
        raise ValueError("fixture parser failure")

    monkeypatch.setattr(http_retry.requests, "get", request)

    with pytest.raises(ValueError, match="fixture parser failure"):
        http_retry.http_get("https://fixture.invalid/read")
    assert len(calls) == 1


def test_builtin_transient_status_retries_without_real_sleep(monkeypatch):
    from urllib.error import HTTPError

    calls = []
    sleeps = []

    class _BuiltinResponse:
        status = 200

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self):
            return b"fixture"

    def urlopen(request, *, timeout):
        calls.append(timeout)
        if len(calls) == 1:
            raise HTTPError(
                request.full_url,
                503,
                "fixture",
                {"Retry-After": "2"},
                None,
            )
        return _BuiltinResponse()

    monkeypatch.setattr(builtin_scraper, "urlopen", urlopen)
    monkeypatch.setattr(builtin_scraper.time, "sleep", sleeps.append)

    assert builtin_scraper.fetch_builtin_jobs_html() == "fixture"
    assert calls == [15, 15]
    assert sleeps == [2.0]


def test_sync_retry_exhaustion_translates_to_failed(monkeypatch):
    _prepare_workday(monkeypatch)
    calls = []

    def timeout(*args, **kwargs):
        calls.append(kwargs["timeout"])
        raise requests.Timeout("fixture")

    monkeypatch.setattr(workday_scraper.session, "post", timeout)
    outcome = workday_scraper._scrape_company_outcome(
        "https://acme.myworkdayjobs.com/jobs"
    )

    assert outcome.status is AcquisitionStatus.FAILED
    assert outcome.reason == "transport_error"
    assert calls == [10, 10]


def test_sync_retry_exhaustion_after_first_page_is_partial(monkeypatch):
    _prepare_workday(monkeypatch)
    first = _Response(
        {
            "total": 40,
            "jobPostings": [_workday_posting(index) for index in range(20)],
        }
    )
    responses = iter([first, requests.ConnectionError("fixture"), requests.ConnectionError("fixture")])

    def post(*args, **kwargs):
        value = next(responses)
        if isinstance(value, BaseException):
            raise value
        return value

    monkeypatch.setattr(workday_scraper.session, "post", post)
    outcome = workday_scraper._scrape_company_outcome(
        "https://acme.myworkdayjobs.com/jobs"
    )

    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "pagination_interrupted"
    assert len(outcome.jobs) == 20


@pytest.mark.parametrize("module", [greenhouse_scraper, lever_scraper])
def test_async_retry_exhaustion_is_failed_without_real_sleep(monkeypatch, module):
    sleeps = []

    async def no_sleep(seconds):
        sleeps.append(seconds)

    monkeypatch.setattr(module.asyncio, "sleep", no_sleep)
    session = _AsyncSequenceSession([
        module.aiohttp.ClientConnectionError("fixture"),
        module.aiohttp.ClientConnectionError("fixture"),
    ])
    outcome = asyncio.run(module._fetch_company_outcome(session, "acme"))

    assert outcome.status is AcquisitionStatus.FAILED
    assert outcome.reason == "transport_error"
    assert session.calls == consts.SCRAPER_RETRY_ATTEMPTS
    assert sleeps == [consts.SCRAPER_RETRY_DELAY_SECONDS]


@pytest.mark.parametrize("module", [greenhouse_scraper, lever_scraper])
def test_async_transient_status_retries_with_retry_after(monkeypatch, module):
    sleeps = []

    async def no_sleep(seconds):
        sleeps.append(seconds)

    payload = {"jobs": []} if module is greenhouse_scraper else []
    session = _AsyncSequenceSession([
        _AsyncResponse(status=429, headers={"Retry-After": "4"}),
        _AsyncResponse(payload),
    ])
    monkeypatch.setattr(module.asyncio, "sleep", no_sleep)
    outcome = asyncio.run(module._fetch_company_outcome(session, "acme"))

    assert outcome.status is AcquisitionStatus.EMPTY
    assert session.calls == 2
    assert sleeps == [4.0]


def test_workday_verified_empty_and_normal_short_page(monkeypatch):
    _prepare_workday(monkeypatch)
    board = "https://acme.myworkdayjobs.com/jobs"

    monkeypatch.setattr(
        workday_scraper,
        "workday_post",
        lambda *args, **kwargs: _Response({"total": 0, "jobPostings": []}),
    )
    empty = workday_scraper._scrape_company_outcome(board)

    monkeypatch.setattr(
        workday_scraper,
        "workday_post",
        lambda *args, **kwargs: _Response(
            {"jobPostings": [_workday_posting(index) for index in range(3)]}
        ),
    )
    success = workday_scraper._scrape_company_outcome(board)

    assert empty.status is AcquisitionStatus.EMPTY
    assert empty.page_count == 1
    assert success.status is AcquisitionStatus.SUCCESS
    assert len(success.jobs) == 3
    assert success.company == board
    assert {job["company"] for job in success.jobs} == {"acme"}


@pytest.mark.parametrize("mode", ["repeated", "no_progress"])
def test_workday_repeated_and_no_progress_pages_are_partial(monkeypatch, mode):
    _prepare_workday(monkeypatch)
    board = "https://acme.myworkdayjobs.com/jobs"
    first_jobs = [_workday_posting(index) for index in range(20)]
    second_jobs = list(first_jobs)
    if mode == "no_progress":
        second_jobs = list(reversed(second_jobs))
    responses = iter([
        _Response({"total": 60, "jobPostings": first_jobs}),
        _Response({"total": 60, "jobPostings": second_jobs}),
    ])
    monkeypatch.setattr(
        workday_scraper,
        "workday_post",
        lambda *args, **kwargs: next(responses),
    )

    outcome = workday_scraper._scrape_company_outcome(board)

    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "pagination_no_progress"
    assert len(outcome.jobs) == 20
    assert outcome.should_mark_scraped is False


def test_workday_page_cap_is_finite_and_partial(monkeypatch):
    _prepare_workday(monkeypatch)
    calls = []
    monkeypatch.setattr(workday_scraper, "WORKDAY_MAX_PAGES", 1)

    def post(*args, **kwargs):
        calls.append(kwargs["json"]["offset"])
        return _Response(
            {
                "total": 40,
                "jobPostings": [_workday_posting(index) for index in range(20)],
            }
        )

    monkeypatch.setattr(workday_scraper, "workday_post", post)
    outcome = workday_scraper._scrape_company_outcome(
        "https://acme.myworkdayjobs.com/jobs"
    )

    assert calls == [0]
    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "pagination_limit_reached"
    assert outcome.page_count == 1
    assert outcome.should_mark_scraped is False


@pytest.mark.parametrize(
    "payload",
    [
        {"jobPostings": [_workday_posting(index) for index in range(3)]},
        {
            "total": 3,
            "jobPostings": [_workday_posting(index) for index in range(3)],
        },
    ],
)
def test_workday_proven_completion_precedes_page_cap(monkeypatch, payload):
    _prepare_workday(monkeypatch)
    monkeypatch.setattr(workday_scraper, "WORKDAY_MAX_PAGES", 1)
    monkeypatch.setattr(
        workday_scraper,
        "workday_post",
        lambda *args, **kwargs: _Response(payload),
    )

    outcome = workday_scraper._scrape_company_outcome(
        "https://acme.myworkdayjobs.com/jobs"
    )

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.page_count == 1
    assert outcome.raw_job_count == 3


@pytest.mark.parametrize("total", [True, False, -1, "40", 40.0])
def test_workday_rejects_malformed_total_metadata(monkeypatch, total):
    _prepare_workday(monkeypatch)
    monkeypatch.setattr(
        workday_scraper,
        "workday_post",
        lambda *args, **kwargs: _Response(
            {"total": total, "jobPostings": [_workday_posting(1)]}
        ),
    )

    outcome = workday_scraper._scrape_company_outcome(
        "https://acme.myworkdayjobs.com/jobs"
    )

    assert outcome.status is AcquisitionStatus.FAILED
    assert outcome.reason == "malformed_payload"
    assert outcome.page_count == 0


def test_workday_advances_by_returned_rows_and_retains_first_total(monkeypatch):
    _prepare_workday(monkeypatch)
    calls = []

    def post(*args, **kwargs):
        offset = kwargs["json"]["offset"]
        calls.append(offset)
        if offset == 0:
            return _Response(
                {
                    "total": 5,
                    "jobPostings": [_workday_posting(index) for index in range(3)],
                }
            )
        return _Response(
            {
                "total": 0,
                "jobPostings": [_workday_posting(index) for index in range(3, 5)],
            }
        )

    monkeypatch.setattr(workday_scraper, "workday_post", post)
    outcome = workday_scraper._scrape_company_outcome(
        "https://acme.myworkdayjobs.com/jobs"
    )

    assert calls == [0, 3]
    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.page_count == 2
    assert outcome.raw_job_count == 5
    assert len(outcome.jobs) == 5


def test_workday_empty_page_with_remaining_total_is_no_progress(monkeypatch):
    _prepare_workday(monkeypatch)
    responses = iter(
        [
            _Response(
                {
                    "total": 40,
                    "jobPostings": [_workday_posting(index) for index in range(20)],
                }
            ),
            _Response({"total": 40, "jobPostings": []}),
        ]
    )
    monkeypatch.setattr(
        workday_scraper,
        "workday_post",
        lambda *args, **kwargs: next(responses),
    )

    outcome = workday_scraper._scrape_company_outcome(
        "https://acme.myworkdayjobs.com/jobs"
    )

    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "pagination_no_progress"
    assert outcome.page_count == 2
    assert outcome.raw_job_count == 20


def test_workday_exact_provider_boundary_is_partial_without_offset_2000(monkeypatch):
    _prepare_workday(monkeypatch)
    calls = []

    def post(*args, **kwargs):
        offset = kwargs["json"]["offset"]
        calls.append(offset)
        return _Response(
            {
                "total": 2000 if offset != 1980 else 0,
                "jobPostings": [
                    _workday_posting(index)
                    for index in range(offset, offset + consts.WORKDAY_PAGE_SIZE)
                ],
            }
        )

    monkeypatch.setattr(workday_scraper, "workday_post", post)
    outcome = workday_scraper._scrape_company_outcome(
        "https://acme.myworkdayjobs.com/jobs"
    )

    assert calls == list(range(0, 2000, 20))
    assert 2000 not in calls
    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "pagination_limit_reached"
    assert outcome.page_count == 100
    assert outcome.raw_job_count == 2000
    assert len(outcome.jobs) == 2000


def test_workday_larger_total_stops_at_page_cap(monkeypatch):
    _prepare_workday(monkeypatch)
    calls = []
    monkeypatch.setattr(workday_scraper, "WORKDAY_MAX_PAGES", 2)

    def post(*args, **kwargs):
        offset = kwargs["json"]["offset"]
        calls.append(offset)
        return _Response(
            {
                "total": 3000,
                "jobPostings": [
                    _workday_posting(index) for index in range(offset, offset + 20)
                ],
            }
        )

    monkeypatch.setattr(workday_scraper, "workday_post", post)
    outcome = workday_scraper._scrape_company_outcome(
        "https://acme.myworkdayjobs.com/jobs"
    )

    assert calls == [0, 20]
    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "pagination_limit_reached"
    assert outcome.page_count == 2
    assert outcome.raw_job_count == 40


def test_workday_later_malformed_total_retains_safe_jobs(monkeypatch):
    _prepare_workday(monkeypatch)
    responses = iter(
        [
            _Response(
                {
                    "total": 40,
                    "jobPostings": [_workday_posting(index) for index in range(20)],
                }
            ),
            _Response(
                {
                    "total": "40",
                    "jobPostings": [_workday_posting(index) for index in range(20, 40)],
                }
            ),
        ]
    )
    monkeypatch.setattr(
        workday_scraper,
        "workday_post",
        lambda *args, **kwargs: next(responses),
    )

    outcome = workday_scraper._scrape_company_outcome(
        "https://acme.myworkdayjobs.com/jobs"
    )

    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "pagination_interrupted"
    assert outcome.page_count == 1
    assert outcome.raw_job_count == 20
    assert len(outcome.jobs) == 20


@pytest.mark.parametrize(
    ("posting", "expected"),
    [
        ({"jobPostingInfo": {"startDate": "info-start"}}, "info-start"),
        ({"startDate": "row-start"}, "row-start"),
        ({"jobPostingInfo": {"postedOn": "info-posted"}}, "info-posted"),
        ({"postedOn": "row-posted"}, "row-posted"),
        ({"postedDate": "row-posted-date"}, "row-posted-date"),
        ({"postedAt": "row-posted-at"}, "row-posted-at"),
        ({"createdDate": "row-created-date"}, "row-created-date"),
        ({"createdAt": "row-created-at"}, "row-created-at"),
    ],
)
def test_workday_listing_timestamp_candidate_family(monkeypatch, posting, expected):
    _prepare_workday(monkeypatch)
    row = _workday_posting(1)
    row.pop("postedDate")
    row.update(posting)
    monkeypatch.setattr(
        workday_scraper,
        "workday_post",
        lambda *args, **kwargs: _Response({"total": 1, "jobPostings": [row]}),
    )

    outcome = workday_scraper._scrape_company_outcome(
        "https://acme.myworkdayjobs.com/jobs"
    )

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.jobs[0]["posted_at"] == expected


def test_workday_later_page_failure_retains_earlier_jobs(monkeypatch):
    _prepare_workday(monkeypatch)
    responses = iter([
        _Response(
            {
                "total": 40,
                "jobPostings": [_workday_posting(index) for index in range(20)],
            }
        ),
        _Response(status_code=503),
    ])
    monkeypatch.setattr(
        workday_scraper,
        "workday_post",
        lambda *args, **kwargs: next(responses),
    )
    outcome = workday_scraper._scrape_company_outcome(
        "https://acme.myworkdayjobs.com/jobs"
    )

    assert outcome.status is AcquisitionStatus.PARTIAL
    assert len(outcome.jobs) == 20
    assert outcome.should_mark_scraped is False


def test_workable_verified_empty_and_normal_public_payload(monkeypatch):
    _prepare_workable(monkeypatch)
    calls = []
    responses = iter([
        _Response({"jobs": []}),
        _Response(
            {
                "jobs": [
                    _workable_posting(index)
                    for index in range(3)
                ]
            }
        ),
    ])

    def get(url, **kwargs):
        calls.append(
            (
                url,
                kwargs.get("params"),
                kwargs.get("timeout"),
            )
        )
        return next(responses)

    monkeypatch.setattr(
        workable_scraper,
        "workable_get",
        get,
    )

    empty = workable_scraper._fetch_company_outcome("empty")
    success = workable_scraper._fetch_company_outcome("acme")

    assert empty.status is AcquisitionStatus.EMPTY
    assert empty.page_count == 1
    assert success.status is AcquisitionStatus.SUCCESS
    assert success.page_count == 1
    assert len(success.jobs) == 3
    assert success.company == "acme"
    assert {
        job["company"]
        for job in success.jobs
    } == {"acme"}
    assert calls == [
        (
            "https://www.workable.com/api/accounts/empty",
            {"details": "true"},
            10,
        ),
        (
            "https://www.workable.com/api/accounts/acme",
            {"details": "true"},
            10,
        ),
    ]


@pytest.mark.parametrize(
    ("response", "reason"),
    [
        (_Response(status_code=503), "non_200_response"),
        (_Response(payload=[]), "malformed_payload"),
        (
            _Response(payload={"jobs": {}}),
            "malformed_payload",
        ),
    ],
)
def test_workable_public_request_failures_are_explicit(
    monkeypatch,
    response,
    reason,
):
    _prepare_workable(monkeypatch)
    monkeypatch.setattr(
        workable_scraper,
        "workable_get",
        lambda *args, **kwargs: response,
    )

    outcome = workable_scraper._fetch_company_outcome("acme")

    assert outcome.status is AcquisitionStatus.FAILED
    assert outcome.reason == reason
    assert outcome.should_mark_scraped is False


def test_workable_public_payload_is_not_locally_page_truncated(
    monkeypatch,
):
    _prepare_workable(monkeypatch)
    jobs = [
        _workable_posting(index)
        for index in range(75)
    ]

    monkeypatch.setattr(
        workable_scraper,
        "workable_get",
        lambda *args, **kwargs: _Response(
            {"jobs": jobs}
        ),
    )
    monkeypatch.setattr(
        workable_scraper,
        "workable_post",
        lambda *args, **kwargs: (
            _ for _ in ()
        ).throw(
            AssertionError(
                "obsolete Workable POST route was called"
            )
        ),
    )

    outcome = workable_scraper._fetch_company_outcome("acme")

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.page_count == 1
    assert outcome.raw_job_count == 75
    assert len(outcome.jobs) == 75


def test_source_retry_and_pagination_constants_are_bounded():
    assert consts.SCRAPER_RETRY_ATTEMPTS == 2
    assert 0 <= consts.SCRAPER_RETRY_DELAY_SECONDS <= consts.SCRAPER_RETRY_MAX_DELAY_SECONDS
    assert 0 < consts.WORKDAY_MAX_PAGES < 1000
    assert 0 < consts.WORKABLE_MAX_PAGES < 1000
    assert consts.WORKDAY_PAGE_SIZE == 20
    assert consts.WORKABLE_PAGE_SIZE == 50


def test_hardening_paths_add_no_persistence_or_application_authority():
    modules = (
        http_retry,
        greenhouse_scraper,
        lever_scraper,
        workday_scraper,
        workable_scraper,
        builtin_scraper,
    )
    forbidden = (
        "submit_application",
        "ats_submit",
        "message_recruiter",
        "source_resume_overwrite",
        "generated_resume",
        "llm_client",
        "write_corpus",
        "write_cache",
    )

    for module in modules:
        source = Path(module.__file__).read_text(encoding="utf-8").lower()
        for marker in forbidden:
            assert marker not in source
