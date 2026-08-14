from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from src.config import consts
from src.pipeline import job_filter
from src.utils import workday_timestamp
from src.utils.posted_at_utils import parse_posted_at


class _Response:
    def __init__(self, payload=None, status_code=200, json_error=False):
        self.status_code = status_code
        self._payload = payload
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("malformed fixture")
        return self._payload


def _fresh_timestamp():
    return datetime.now(timezone.utc).isoformat()


def _workday_job(**overrides):
    job = {
        "company": "acme",
        "title": "Data Scientist",
        "location": "New York, NY",
        "source": "workday",
        "posted_at": None,
        "url": "https://acme.myworkdayjobs.com/jobs/job/123",
        "_board_url": "https://acme.myworkdayjobs.com/jobs",
        "_externalPath": "/job/123",
    }
    job.update(overrides)
    return job


@pytest.mark.parametrize(
    "value",
    ["Posted Today", "Posted Yesterday", "Posted 2 Days Ago"],
)
def test_existing_workday_relative_age_values_remain_supported(value):
    assert parse_posted_at(value) is not None


def test_exact_workday_30_plus_literal_is_supported_and_stale():
    parsed = parse_posted_at("Posted 30+ Days Ago")

    assert parsed is not None
    assert timedelta(days=29, hours=23) < datetime.now(timezone.utc) - parsed
    assert job_filter.posted_within_24h("Posted 30+ Days Ago") is False


@pytest.mark.parametrize(
    "value",
    [
        "Posted 31+ Days Ago",
        "Posted 30 + Days Ago",
        "posted 30+ days ago",
        " Posted 30+ Days Ago",
        "Posted 30+ Days Ago ",
        "x Posted 30+ Days Ago",
        "Posted 30+ Weeks Ago",
        "30d ago",
    ],
)
def test_workday_30_plus_parser_does_not_broaden_to_unproven_variants(value):
    assert parse_posted_at(value) is None


@pytest.mark.parametrize(
    ("payload", "expected_timestamp"),
    [
        ({"jobPostingInfo": {"startDate": "2026-08-05"}}, "2026-08-05"),
        ({"jobPostingInfo": {"postedOn": "Posted Today"}}, "Posted Today"),
        (
            {
                "jobPostingInfo": {
                    "startDate": "2026-08-05",
                    "postedOn": "Posted Yesterday",
                }
            },
            "2026-08-05",
        ),
    ],
)
def test_workday_timestamp_result_extracts_bounded_metadata(
    monkeypatch, payload, expected_timestamp
):
    monkeypatch.setattr(
        workday_timestamp.session,
        "get",
        lambda *args, **kwargs: _Response(payload),
    )

    result = workday_timestamp.fetch_workday_timestamp_result(
        "https://acme.myworkdayjobs.com/jobs",
        "/job/123",
    )

    assert result == {
        "posted_at": expected_timestamp,
        "marker": "workday_timestamp_success",
        "status_code": 200,
    }


def test_workday_timestamp_result_does_not_return_description(monkeypatch):
    monkeypatch.setattr(
        workday_timestamp.session,
        "get",
        lambda *args, **kwargs: _Response(
            {
                "jobPostingInfo": {
                    "startDate": "2026-08-05",
                    "jobDescription": "must-not-escape",
                },
                "jobDescription": "must-not-escape",
            }
        ),
    )

    result = workday_timestamp.fetch_workday_timestamp_result(
        "https://acme.myworkdayjobs.com/jobs",
        "/job/123",
    )

    assert set(result) == {"posted_at", "marker", "status_code"}
    assert "description" not in repr(result).lower()
    assert "must-not-escape" not in repr(result)


@pytest.mark.parametrize(
    ("response", "marker", "status_code"),
    [
        (_Response({"jobPostingInfo": {}}, 200), "workday_timestamp_missing", 200),
        (_Response([], 200), "workday_timestamp_malformed_payload", 200),
        (
            _Response({"jobPostingInfo": []}, 200),
            "workday_timestamp_malformed_payload",
            200,
        ),
        (
            _Response(json_error=True),
            "workday_timestamp_malformed_payload",
            200,
        ),
        (_Response({}, 429), "workday_timestamp_non_200", 429),
        (_Response({}, 503), "workday_timestamp_non_200", 503),
    ],
)
def test_workday_timestamp_result_failure_markers(
    monkeypatch, response, marker, status_code
):
    monkeypatch.setattr(
        workday_timestamp.session,
        "get",
        lambda *args, **kwargs: response,
    )

    result = workday_timestamp.fetch_workday_timestamp_result(
        "https://acme.myworkdayjobs.com/jobs",
        "/job/123",
    )

    assert result == {
        "posted_at": None,
        "marker": marker,
        "status_code": status_code,
    }


def test_workday_timestamp_result_request_failure(monkeypatch):
    def fail(*args, **kwargs):
        raise RuntimeError("fixture")

    monkeypatch.setattr(workday_timestamp.session, "get", fail)

    assert workday_timestamp.fetch_workday_timestamp_result(
        "https://acme.myworkdayjobs.com/jobs",
        "/job/123",
    ) == {
        "posted_at": None,
        "marker": "workday_timestamp_request_failed",
        "status_code": None,
    }


def test_workday_timestamp_compatibility_wrapper(monkeypatch):
    monkeypatch.setattr(
        workday_timestamp,
        "fetch_workday_timestamp_result",
        lambda *args, **kwargs: {
            "posted_at": "2026-08-05",
            "marker": "workday_timestamp_success",
            "status_code": 200,
        },
    )
    assert workday_timestamp.fetch_workday_timestamp("board", "/job/1") == "2026-08-05"

    monkeypatch.setattr(
        workday_timestamp,
        "fetch_workday_timestamp_result",
        lambda *args, **kwargs: {
            "posted_at": None,
            "marker": "workday_timestamp_missing",
            "status_code": 200,
        },
    )
    assert workday_timestamp.fetch_workday_timestamp("board", "/job/1") is None


def test_workday_listing_timestamp_avoids_fallback(monkeypatch):
    calls = []
    monkeypatch.setattr(
        job_filter,
        "fetch_workday_timestamp_result",
        lambda *args, **kwargs: calls.append(args),
    )
    job = _workday_job(posted_at=_fresh_timestamp())

    filtered, diagnostics = job_filter.filter_jobs([job], return_diagnostics=True)

    assert filtered == [job]
    assert calls == []
    assert diagnostics["workday_timestamp_listing_present"] == 1
    assert diagnostics.get("workday_timestamp_cache_miss", 0) == 0


def test_workday_hydration_runs_only_after_title_and_location_pass(monkeypatch):
    calls = []
    monkeypatch.setattr(
        job_filter,
        "fetch_workday_timestamp_result",
        lambda *args, **kwargs: calls.append(args),
    )
    jobs = [
        _workday_job(title="Registered Nurse", _externalPath="/job/title"),
        _workday_job(location="London, UK", _externalPath="/job/location"),
    ]

    filtered, diagnostics = job_filter.filter_jobs(jobs, return_diagnostics=True)

    assert filtered == []
    assert calls == []
    assert diagnostics.get("workday_timestamp_cache_miss", 0) == 0


def test_duplicate_workday_keys_share_one_request_and_result(monkeypatch):
    calls = []

    def fetch(board_url, external_path):
        calls.append((board_url, external_path))
        return {
            "posted_at": _fresh_timestamp(),
            "marker": "workday_timestamp_success",
            "status_code": 200,
        }

    monkeypatch.setattr(job_filter, "fetch_workday_timestamp_result", fetch)
    jobs = [
        _workday_job(),
        _workday_job(
            _board_url="HTTPS://ACME.MYWORKDAYJOBS.COM/jobs?ignored=1",
            url="https://acme.myworkdayjobs.com/jobs/job/123?duplicate=1",
        ),
    ]

    filtered, diagnostics = job_filter.filter_jobs(jobs, return_diagnostics=True)

    assert filtered == jobs
    assert len(calls) == 1
    assert diagnostics["workday_timestamp_cache_miss"] == 1
    assert diagnostics["workday_timestamp_cache_hit"] == 1
    assert diagnostics["workday_timestamp_fetch_success"] == 1
    assert diagnostics["workday_timestamp_fetch_429"] == 0
    assert diagnostics["workday_timestamp_fetch_failed"] == 0
    assert all(job["posted_at"] for job in jobs)


@pytest.mark.parametrize(
    ("result", "counter"),
    [
        (
            {
                "posted_at": None,
                "marker": "workday_timestamp_non_200",
                "status_code": 429,
            },
            "workday_timestamp_fetch_429",
        ),
        (
            {
                "posted_at": None,
                "marker": "workday_timestamp_missing",
                "status_code": 200,
            },
            "workday_timestamp_fetch_failed",
        ),
    ],
)
def test_workday_failed_fallback_is_rejected_with_mutually_exclusive_counter(
    monkeypatch, result, counter
):
    monkeypatch.setattr(
        job_filter,
        "fetch_workday_timestamp_result",
        lambda *args, **kwargs: result,
    )

    filtered, diagnostics = job_filter.filter_jobs(
        [_workday_job()],
        return_diagnostics=True,
    )

    assert filtered == []
    assert diagnostics[counter] == 1
    assert diagnostics["workday_timestamp_fetch_429"] + diagnostics[
        "workday_timestamp_fetch_failed"
    ] == 1
    assert diagnostics["missing_timestamp"] == 1


def test_workday_timestamp_cache_is_not_persistent_across_filter_runs(monkeypatch):
    calls = []

    def fetch(*args):
        calls.append(args)
        return {
            "posted_at": _fresh_timestamp(),
            "marker": "workday_timestamp_success",
            "status_code": 200,
        }

    monkeypatch.setattr(job_filter, "fetch_workday_timestamp_result", fetch)

    job_filter.filter_jobs([_workday_job()])
    job_filter.filter_jobs([_workday_job()])

    assert len(calls) == 2


def test_workday_timestamp_workers_and_collector_diagnostics_are_bounded():
    filter_source = Path("src/pipeline/job_filter.py").read_text(encoding="utf-8")
    collector_source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    counters = {
        "workday_timestamp_listing_present",
        "workday_timestamp_cache_hit",
        "workday_timestamp_cache_miss",
        "workday_timestamp_fetch_success",
        "workday_timestamp_fetch_429",
        "workday_timestamp_fetch_failed",
    }

    assert consts.TIMESTAMP_WORKERS == 10
    assert "ThreadPoolExecutor(max_workers=TIMESTAMP_WORKERS)" in filter_source
    assert all(counter in collector_source for counter in counters)
