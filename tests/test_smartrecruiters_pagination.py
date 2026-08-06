import inspect

import pytest

from src.config import consts
from src.discovery.crawl_scheduler import AcquisitionStatus
from src.scrapers import smartrecruiters_scraper as scraper


class _Response:
    def __init__(self, payload=None, *, status_code=200, error=None):
        self.payload = payload
        self.status_code = status_code
        self.error = error

    def json(self):
        if self.error:
            raise self.error
        return self.payload


def _posting(identifier="acme", job_id="1", **overrides):
    row = {
        "id": job_id,
        "name": "Software Engineer",
        "releasedDate": "2026-08-05T12:00:00Z",
        "company": {"identifier": identifier},
        "location": {"city": "New York", "region": "NY", "country": "US"},
        "applyUrl": f"https://jobs.smartrecruiters.com/{identifier}/{job_id}",
    }
    row.update(overrides)
    return row


def _payload(rows, *, offset=0, total=None, limit=100):
    return {
        "content": rows,
        "offset": offset,
        "limit": limit,
        "totalFound": len(rows) if total is None else total,
    }


def _outcome():
    return scraper._thread_outcome.value


@pytest.fixture(autouse=True)
def _no_discovery_writes(monkeypatch):
    learned = []
    monkeypatch.setattr(scraper, "learn_from_job_url", learned.append)
    yield learned


def test_global_complete_success_and_single_request(monkeypatch):
    calls = []
    monkeypatch.setattr(
        scraper,
        "http_get",
        lambda url, **kwargs: calls.append((url, kwargs))
        or _Response(_payload([_posting()], total=1)),
    )

    jobs = scraper.fetch_company_jobs(None)
    outcome = _outcome()

    assert len(calls) == 1
    assert calls[0][1]["params"] == {"limit": 100}
    assert outcome.status is AcquisitionStatus.SUCCESS
    assert (outcome.page_count, outcome.raw_job_count, len(jobs)) == (1, 1, 1)


def test_global_empty_is_complete(monkeypatch):
    monkeypatch.setattr(
        scraper, "http_get", lambda *_args, **_kwargs: _Response(_payload([], total=0))
    )

    assert scraper.fetch_company_jobs(None) == []
    assert _outcome().status is AcquisitionStatus.EMPTY
    assert (_outcome().page_count, _outcome().raw_job_count) == (1, 0)


def test_global_truncation_is_partial_without_second_request(monkeypatch):
    calls = []
    monkeypatch.setattr(
        scraper,
        "http_get",
        lambda *_args, **_kwargs: calls.append(1)
        or _Response(_payload([_posting()], total=2)),
    )

    jobs = scraper.fetch_company_jobs(None)

    assert len(calls) == 1
    assert len(jobs) == 1
    assert (_outcome().status, _outcome().reason) == (
        AcquisitionStatus.PARTIAL,
        "pagination_limit_reached",
    )


@pytest.mark.parametrize(
    "payload",
    [
        [],
        {"content": "bad", "offset": 0, "limit": 100, "totalFound": 0},
        _payload([], offset=True),
        _payload([], limit=0),
        _payload([], limit=True),
        _payload([], total=True),
        _payload([], total=-1),
        _payload([_posting()], total=0),
    ],
)
def test_global_malformed_metadata_fails(payload, monkeypatch):
    monkeypatch.setattr(
        scraper, "http_get", lambda *_args, **_kwargs: _Response(payload)
    )

    assert scraper.fetch_company_jobs(None) == []
    assert (_outcome().status, _outcome().reason, _outcome().page_count) == (
        AcquisitionStatus.FAILED,
        "malformed_payload",
        1,
    )


def test_company_one_page_completion_preserves_fields(monkeypatch, _no_discovery_writes):
    row = _posting(identifier="payload-co", job_id="abc")
    monkeypatch.setattr(
        scraper,
        "http_get",
        lambda *_args, **_kwargs: _Response(_payload([row], total=1)),
    )

    jobs = scraper.fetch_company_board("requested-co")
    job = jobs[0]

    assert _outcome().status is AcquisitionStatus.SUCCESS
    assert (_outcome().page_count, _outcome().raw_job_count) == (1, 1)
    assert job == {
        "company": "requested-co",
        "title": "Software Engineer",
        "location": "New York",
        "url": "https://jobs.smartrecruiters.com/payload-co/abc",
        "source": "smartrecruiters",
        "posted_at": "2026-08-05T12:00:00Z",
        "job_id": "sr_abc",
    }
    assert _no_discovery_writes == [job["url"]]


def test_company_two_page_completion_advances_by_returned_rows(monkeypatch):
    calls = []
    responses = iter(
        [
            _Response(_payload([_posting(job_id="1")], offset=0, total=2)),
            _Response(_payload([_posting(job_id="2")], offset=1, total=2)),
        ]
    )

    def get(_url, **kwargs):
        calls.append(kwargs["params"]["offset"])
        return next(responses)

    monkeypatch.setattr(scraper, "http_get", get)

    jobs = scraper.fetch_company_board("acme")

    assert calls == [0, 1]
    assert [job["job_id"] for job in jobs] == ["sr_1", "sr_2"]
    assert (_outcome().status, _outcome().page_count, _outcome().raw_job_count) == (
        AcquisitionStatus.SUCCESS,
        2,
        2,
    )


def test_six_page_style_progression_is_sequential(monkeypatch):
    calls = []

    def get(_url, **kwargs):
        offset = kwargs["params"]["offset"]
        calls.append(offset)
        return _Response(_payload([_posting(job_id=str(offset))], offset=offset, total=6))

    monkeypatch.setattr(scraper, "http_get", get)

    jobs = scraper.fetch_company_board("acme")

    assert calls == [0, 1, 2, 3, 4, 5]
    assert len(jobs) == 6
    assert _outcome().status is AcquisitionStatus.SUCCESS


def test_short_nonterminal_page_continues(monkeypatch):
    calls = []
    responses = iter(
        [
            _Response(_payload([_posting(job_id="1")], offset=0, total=2)),
            _Response(_payload([_posting(job_id="2")], offset=1, total=2)),
        ]
    )
    monkeypatch.setattr(
        scraper,
        "http_get",
        lambda _url, **kwargs: calls.append(kwargs["params"]["offset"])
        or next(responses),
    )

    assert len(scraper.fetch_company_board("acme")) == 2
    assert calls == [0, 1]


def test_empty_nonterminal_page_is_no_progress(monkeypatch):
    monkeypatch.setattr(
        scraper,
        "http_get",
        lambda *_args, **_kwargs: _Response(_payload([], offset=0, total=2)),
    )

    assert scraper.fetch_company_board("acme") == []
    assert (_outcome().status, _outcome().reason) == (
        AcquisitionStatus.FAILED,
        "pagination_no_progress",
    )


@pytest.mark.parametrize("reverse", [False, True])
def test_repeated_or_zero_new_id_page_is_partial(monkeypatch, reverse):
    first = [_posting(job_id="1"), _posting(job_id="2")]
    second = list(reversed(first)) if reverse else list(first)
    responses = iter(
        [
            _Response(_payload(first, offset=0, total=5)),
            _Response(_payload(second, offset=2, total=5)),
        ]
    )
    monkeypatch.setattr(
        scraper, "http_get", lambda *_args, **_kwargs: next(responses)
    )

    jobs = scraper.fetch_company_board("acme")

    assert len(jobs) == 2
    assert (_outcome().status, _outcome().reason) == (
        AcquisitionStatus.PARTIAL,
        "pagination_no_progress",
    )
    assert (_outcome().page_count, _outcome().raw_job_count) == (2, 4)


@pytest.mark.parametrize(
    ("total", "status", "reason"),
    [
        (2, AcquisitionStatus.SUCCESS, ""),
        (3, AcquisitionStatus.PARTIAL, "pagination_limit_reached"),
    ],
)
def test_configured_ceiling_exact_or_truncated(monkeypatch, total, status, reason):
    monkeypatch.setattr(scraper, "SMARTRECRUITERS_MAX_COMPANY_PAGES", 2)
    calls = []

    def get(_url, **kwargs):
        offset = kwargs["params"]["offset"]
        calls.append(offset)
        return _Response(
            _payload([_posting(job_id=str(offset))], offset=offset, total=total)
        )

    monkeypatch.setattr(scraper, "http_get", get)

    jobs = scraper.fetch_company_board("acme")

    assert len(jobs) == 2
    assert (_outcome().status, _outcome().reason) == (status, reason)
    assert calls == [0, 1]


@pytest.mark.parametrize(
    ("total", "status", "reason"),
    [
        (10, AcquisitionStatus.SUCCESS, ""),
        (11, AcquisitionStatus.PARTIAL, "pagination_limit_reached"),
    ],
)
def test_page_ten_exact_or_truncated_never_requests_page_eleven(
    monkeypatch, total, status, reason
):
    calls = []

    def get(_url, **kwargs):
        offset = kwargs["params"]["offset"]
        calls.append(offset)
        return _Response(
            _payload([_posting(job_id=str(offset))], offset=offset, total=total)
        )

    monkeypatch.setattr(scraper, "http_get", get)

    jobs = scraper.fetch_company_board("acme")

    assert len(jobs) == 10
    assert (_outcome().status, _outcome().reason) == (status, reason)
    assert (_outcome().page_count, _outcome().raw_job_count) == (10, 10)
    assert calls == list(range(10))


@pytest.mark.parametrize("failure", [RuntimeError("offline"), _Response(status_code=503)])
def test_later_request_failure_retains_safe_jobs(monkeypatch, failure):
    responses = iter(
        [_Response(_payload([_posting()], total=2)), failure]
    )

    def get(*_args, **_kwargs):
        value = next(responses)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(scraper, "http_get", get)

    assert len(scraper.fetch_company_board("acme")) == 1
    assert (_outcome().status, _outcome().reason, _outcome().page_count) == (
        AcquisitionStatus.PARTIAL,
        "pagination_interrupted",
        1,
    )


@pytest.mark.parametrize("failure", [RuntimeError("offline"), _Response(status_code=503)])
def test_first_request_failure_is_failed(monkeypatch, failure):
    def get(*_args, **_kwargs):
        if isinstance(failure, Exception):
            raise failure
        return failure

    monkeypatch.setattr(scraper, "http_get", get)

    assert scraper.fetch_company_board("acme") == []
    assert _outcome().status is AcquisitionStatus.FAILED
    assert _outcome().reason in {"transport_error", "non_200_response"}


def test_later_malformed_metadata_is_partial(monkeypatch):
    responses = iter(
        [
            _Response(_payload([_posting()], total=2)),
            _Response(_payload([_posting(job_id="2")], offset=0, total=2)),
        ]
    )
    monkeypatch.setattr(
        scraper, "http_get", lambda *_args, **_kwargs: next(responses)
    )

    assert len(scraper.fetch_company_board("acme")) == 1
    assert (_outcome().status, _outcome().reason, _outcome().page_count) == (
        AcquisitionStatus.PARTIAL,
        "pagination_interrupted",
        1,
    )


def test_first_company_malformed_metadata_is_failed(monkeypatch):
    monkeypatch.setattr(
        scraper,
        "http_get",
        lambda *_args, **_kwargs: _Response(
            _payload([_posting()], offset=1, total=1)
        ),
    )

    assert scraper.fetch_company_board("acme") == []
    assert (_outcome().status, _outcome().reason) == (
        AcquisitionStatus.FAILED,
        "malformed_payload",
    )


@pytest.mark.parametrize(
    "bad_row",
    [
        "not-an-object",
        _posting(job_id=None),
        _posting(company=None),
        _posting(location="malformed"),
    ],
)
def test_malformed_row_does_not_stop_page(bad_row, monkeypatch):
    rows = [bad_row, _posting(job_id="safe")]
    monkeypatch.setattr(
        scraper,
        "http_get",
        lambda *_args, **_kwargs: _Response(_payload(rows, total=2)),
    )

    jobs = scraper.fetch_company_board("acme")

    assert [job["job_id"] for job in jobs] == ["sr_safe"]
    assert (_outcome().status, _outcome().raw_job_count) == (
        AcquisitionStatus.SUCCESS,
        2,
    )


def test_global_requires_apply_url_while_board_constructs_url(monkeypatch):
    missing_apply = _posting(applyUrl=None)
    monkeypatch.setattr(
        scraper,
        "http_get",
        lambda *_args, **_kwargs: _Response(_payload([missing_apply], total=1)),
    )
    assert scraper.fetch_company_jobs(None) == []
    assert _outcome().reason == "parse_error"

    assert len(scraper.fetch_company_board("acme")) == 1
    assert _outcome().status is AcquisitionStatus.SUCCESS


def test_duplicates_count_raw_but_emit_and_learn_once(monkeypatch, _no_discovery_writes):
    rows = [_posting(job_id="same"), _posting(job_id="same"), _posting(job_id="new")]
    monkeypatch.setattr(
        scraper,
        "http_get",
        lambda *_args, **_kwargs: _Response(_payload(rows, total=3)),
    )

    jobs = scraper.fetch_company_board("acme")

    assert [job["job_id"] for job in jobs] == ["sr_same", "sr_new"]
    assert _outcome().raw_job_count == 3
    assert len(_no_discovery_writes) == 2


def test_cross_target_duplicate_is_emitted_and_learned_per_target(
    monkeypatch, _no_discovery_writes
):
    monkeypatch.setattr(
        scraper,
        "http_get",
        lambda *_args, **_kwargs: _Response(_payload([_posting(job_id="shared")], total=1)),
    )

    first = scraper.fetch_company_board("one")
    second = scraper.fetch_company_board("two")

    assert first[0]["job_id"] == second[0]["job_id"] == "sr_shared"
    assert len(_no_discovery_writes) == 2


def test_global_and_company_overlap_remains_emitted(monkeypatch, _no_discovery_writes):
    responses = iter(
        [
            _Response(_payload([_posting(job_id="shared")], total=1)),
            _Response(_payload([_posting(job_id="shared")], total=1)),
        ]
    )
    monkeypatch.setattr(
        scraper, "http_get", lambda *_args, **_kwargs: next(responses)
    )

    global_jobs = scraper.fetch_company_jobs(None)
    company_jobs = scraper.fetch_company_board("acme")

    assert global_jobs[0]["job_id"] == company_jobs[0]["job_id"] == "sr_shared"
    assert len(_no_discovery_writes) == 2


def test_thread_local_parallel_and_finite_bounds_are_preserved(monkeypatch):
    fallback_job = _posting()
    outcome = scraper._capture_public_outcome("fallback", lambda: [fallback_job])
    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.raw_job_count == 1

    source = inspect.getsource(scraper.scrape_all_smartrecruiters)
    assert "max_workers=20" in source
    assert consts.SMARTRECRUITERS_PAGE_SIZE == 100
    assert consts.SMARTRECRUITERS_MAX_COMPANY_PAGES == 10
    assert 1 + 747 * consts.SMARTRECRUITERS_MAX_COMPANY_PAGES == 7_471


def test_company_result_shape_remains_flat(monkeypatch):
    expected = {"source": "smartrecruiters", "job_id": "sr_1"}
    monkeypatch.setattr(
        scraper,
        "fetch_company_board",
        lambda _company: scraper._return_jobs(
            "acme", AcquisitionStatus.SUCCESS, [expected], raw_job_count=1, page_count=1
        ),
    )
    monkeypatch.setattr(
        scraper,
        "observe_acquisition",
        lambda _source, acquire, **_kwargs: acquire(),
    )

    assert scraper._fetch_company_board_result("acme") == [("acme", [expected])]
