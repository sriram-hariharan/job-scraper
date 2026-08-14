import inspect
import json
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
import requests

from src.config import consts
from src.discovery.crawl_scheduler import AcquisitionStatus
from src.pipeline import collector
from src.pipeline.dedupe import dedupe_jobs
from src.scrapers import himalayas_scraper
from src.utils import http_retry, pipeline_metrics


NOW = datetime(2026, 8, 3, 12, 0, tzinfo=timezone.utc)
PUBLISHED_MS = 1_754_049_600_000
EXPIRES_MS = 1_788_259_200_000


class _Response:
    def __init__(
        self,
        payload=None,
        *,
        status_code=200,
        content_type="application/json",
        raw=None,
        headers=None,
    ):
        self.status_code = status_code
        self.headers = {"Content-Type": content_type, **(headers or {})}
        self.content = (
            raw
            if raw is not None
            else json.dumps(payload if payload is not None else {}).encode("utf-8")
        )


@pytest.fixture(autouse=True)
def _reset_metrics():
    pipeline_metrics.reset_acquisition_metrics()
    yield
    pipeline_metrics.reset_acquisition_metrics()


def _profile(profile_id="engineering", **overrides):
    profile = {
        "profile_id": profile_id,
        "query": "engineer",
        "country": "",
        "worldwide": False,
        "exclude_worldwide": False,
        "seniority": (),
        "employment_type": (),
        "company_slugs": (),
        "timezone": "",
        "sort": "",
    }
    profile.update(overrides)
    return profile


def _item(
    guid="job-123",
    *,
    title="Software Engineer",
    company="Acme",
    application_link=None,
    publication=PUBLISHED_MS,
    expiry=EXPIRES_MS,
):
    suffix = str(guid).lower().replace("_", "-") or "missing"
    return {
        "guid": guid,
        "title": title,
        "excerpt": "Short summary",
        "companyName": company,
        "companySlug": "acme",
        "companyLogo": "https://cdn.example.test/acme.png",
        "employmentType": "Full Time",
        "minSalary": "120000.00",
        "maxSalary": Decimal("150000.50"),
        "salaryPeriod": "annual",
        "seniority": ["Senior", "Senior"],
        "currency": "USD",
        "locationRestrictions": [
            {"alpha2": "US", "name": "United States", "slug": "united-states"},
            {"alpha2": "CA", "name": "Canada", "slug": "canada"},
            {"alpha2": "US", "name": "United States", "slug": "united-states"},
        ],
        "timezoneRestrictions": ["UTC-5", "UTC-8", "UTC-5"],
        "categories": ["Software Development", "Engineering"],
        "parentCategories": ["Technology"],
        "description": (
            "<h2>Role</h2><p>Build reliable systems.</p>"
            "<script>secret()</script><style>.hidden{}</style>"
            "<form>Upload resume</form><iframe>candidate</iframe>"
            "<p>Apply now at https://apply.example.test/form</p>"
            "<p>Collaborate with the team.</p>"
        ),
        "pubDate": publication,
        "expiryDate": expiry,
        "applicationLink": application_link
        or f"https://himalayas.app/companies/acme/jobs/software-engineer-{suffix}/",
    }


def _json_safe(value):
    if isinstance(value, Decimal):
        return str(value)
    raise TypeError


def _payload(items, *, page=1, total=None, limit=20, **overrides):
    payload = {
        "updatedAt": PUBLISHED_MS,
        "offset": (page - 1) * 20,
        "limit": limit,
        "totalCount": len(items) if total is None else total,
        "jobs": items,
    }
    payload.update(overrides)
    return payload


def _response(payload, **kwargs):
    return _Response(raw=json.dumps(payload, default=_json_safe).encode(), **kwargs)


def _set_page_responses(monkeypatch, *responses):
    values = iter(responses)
    monkeypatch.setattr(
        himalayas_scraper,
        "_request_page",
        lambda *_args, **_kwargs: next(values),
    )


def _contains_prohibited_application_data(value):
    prohibited_keys = {
        "applicationlink",
        "applicationurl",
        "candidateurl",
        "applicationform",
        "recruitercontact",
        "resumeuploadurl",
        "trackingtoken",
    }
    prohibited_values = (
        "apply.example.test",
        "boards.greenhouse.io",
        "upload resume",
        "application form",
    )
    if isinstance(value, dict):
        return any(
            str(key).replace("_", "").lower() in prohibited_keys
            or _contains_prohibited_application_data(item)
            for key, item in value.items()
        )
    if isinstance(value, (list, tuple)):
        return any(_contains_prohibited_application_data(item) for item in value)
    text = str(value or "").lower()
    return any(marker in text for marker in prohibited_values)


def test_checked_in_query_profiles_are_exactly_the_two_approved_us_queries():
    path = Path(consts.HIMALAYAS_QUERY_PROFILES_PATH)
    assert json.loads(path.read_text(encoding="utf-8")) == [
        {
            "profile_id": "data-us",
            "query": "data",
            "country": "US",
            "exclude_worldwide": True,
            "sort": "recent",
        },
        {
            "profile_id": "software-us",
            "query": "software",
            "country": "US",
            "exclude_worldwide": True,
            "sort": "recent",
        },
    ]
    assert himalayas_scraper._load_query_profiles(path) == [
        {
            "profile_id": "data-us",
            "query": "data",
            "country": "US",
            "worldwide": False,
            "exclude_worldwide": True,
            "timezone": "",
            "seniority": (),
            "employment_type": (),
            "company_slugs": (),
            "sort": "recent",
        },
        {
            "profile_id": "software-us",
            "query": "software",
            "country": "US",
            "worldwide": False,
            "exclude_worldwide": True,
            "timezone": "",
            "seniority": (),
            "employment_type": (),
            "company_slugs": (),
            "sort": "recent",
        },
    ]
    assert not any(profile["query"] == "engineer" for profile in himalayas_scraper._load_query_profiles(path))
    assert all(profile["query"] for profile in himalayas_scraper._load_query_profiles(path))


def test_empty_profiles_exit_before_http_metrics_workers_or_schedule(monkeypatch):
    monkeypatch.setattr(himalayas_scraper, "_load_query_profiles", lambda: [])
    for owner in ("_request_page", "observe_acquisition"):
        monkeypatch.setattr(
            himalayas_scraper,
            owner,
            lambda *args, _owner=owner, **kwargs: pytest.fail(f"{_owner} must not run"),
        )
    assert himalayas_scraper.scrape_all_himalayas() == []
    assert pipeline_metrics.acquisition_metrics_snapshot() == ()


def test_profile_loader_accepts_four_sorts_and_deduplicates_lists(tmp_path):
    profiles = [
        {"profile_id": "zeta", "worldwide": True},
        {
            "profile_id": "alpha",
            "seniority": ["Senior", "Manager", "Senior"],
            "employment_type": ["Full Time", "Contractor", "Full Time"],
            "company_slugs": ["linear", "vercel", "linear"],
        },
        {"profile_id": "two", "country": "US", "exclude_worldwide": True},
        {"profile_id": "three", "timezone": "UTC+05:30"},
    ]
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps(profiles), encoding="utf-8")

    loaded = himalayas_scraper._load_query_profiles(path)

    assert [profile["profile_id"] for profile in loaded] == [
        "alpha",
        "three",
        "two",
        "zeta",
    ]
    assert loaded[0]["seniority"] == ("Senior", "Manager")
    assert loaded[0]["employment_type"] == ("Full Time", "Contractor")
    assert loaded[0]["company_slugs"] == ("linear", "vercel")


@pytest.mark.parametrize(
    "profiles",
    [
        [{"profile_id": str(index), "query": "x"} for index in range(5)],
        [{"profile_id": "dup", "query": "x"}, {"profile_id": "dup", "query": "y"}],
        [{"profile_id": "UPPER", "query": "x"}],
        [{"profile_id": "bad profile", "query": "x"}],
        [{"profile_id": "x" * 65, "query": "x"}],
        [{"profile_id": "empty"}],
        [{"profile_id": "sort-only", "sort": "recent"}],
        [{"profile_id": "conflict", "worldwide": True, "exclude_worldwide": True}],
        [{"profile_id": "exclude-only", "exclude_worldwide": True}],
        [{"profile_id": "unknown", "query": "x", "limit": 20}],
        [{"profile_id": "bad-seniority", "seniority": ["Staff"]}],
        [{"profile_id": "bad-employment", "employment_type": ["Permanent"]}],
        [{"profile_id": "bad-sort", "query": "x", "sort": "newest"}],
        [{"profile_id": "bad-slug", "company_slugs": ["Not Canonical"]}],
        [{"profile_id": "bad-list", "seniority": "Senior"}],
        [{"profile_id": "bad-timezone", "timezone": "Eastern"}],
        [{"profile_id": "bad-boolean", "worldwide": "true"}],
        [{"profile_id": 123, "query": "x"}],
        [{"profile_id": "long-query", "query": "x" * 201}],
        [{"profile_id": "long-country", "country": "x" * 101}],
        [{"profile_id": "too-many", "company_slugs": [f"co-{i}" for i in range(21)]}],
    ],
)
def test_invalid_profiles_reject_safely_without_request(tmp_path, monkeypatch, profiles):
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps(profiles), encoding="utf-8")
    monkeypatch.setattr(himalayas_scraper, "HIMALAYAS_QUERY_PROFILES_PATH", str(path))
    monkeypatch.setattr(
        himalayas_scraper,
        "_request_page",
        lambda *args, **kwargs: pytest.fail("HTTP must not run"),
    )
    monkeypatch.setattr(
        himalayas_scraper,
        "observe_acquisition",
        lambda *args, **kwargs: pytest.fail("metrics must not run"),
    )
    assert himalayas_scraper.scrape_all_himalayas() == []


def test_profile_parameter_mapping_is_exact():
    profile = _profile(
        query="python engineer",
        country="US",
        worldwide=False,
        exclude_worldwide=True,
        seniority=("Senior", "Manager"),
        employment_type=("Full Time", "Contractor"),
        company_slugs=("linear", "vercel"),
        timezone="UTC-5",
        sort="recent",
    )
    assert himalayas_scraper._profile_params(profile, 2) == {
        "page": 2,
        "q": "python engineer",
        "country": "US",
        "timezone": "UTC-5",
        "sort": "recent",
        "exclude_worldwide": "true",
        "seniority": "Senior,Manager",
        "employment_type": "Full Time,Contractor",
        "company": "linear,vercel",
    }


def test_request_uses_official_unauthenticated_get_timeout_and_no_redirects(monkeypatch):
    captured = {}

    def get(url, **kwargs):
        captured.update(url=url, kwargs=kwargs)
        return _response(_payload([]))

    monkeypatch.setattr(himalayas_scraper, "_himalayas_get", get)
    himalayas_scraper._request_page(_profile(), 1)
    assert captured == {
        "url": "https://himalayas.app/jobs/api/search",
        "kwargs": {
            "params": {"page": 1, "q": "engineer"},
            "timeout": 10,
            "allow_redirects": False,
        },
    }
    assert "headers" not in captured["kwargs"]


@pytest.mark.parametrize(
    ("status", "expected_calls"),
    [(429, 1), (500, 2), (502, 2), (503, 2), (504, 2), (400, 1), (404, 1)],
)
def test_private_get_retry_contract_excludes_429(monkeypatch, status, expected_calls):
    calls = []
    monkeypatch.setattr(http_retry.time, "sleep", lambda _delay: None)
    monkeypatch.setattr(
        himalayas_scraper.requests,
        "get",
        lambda *args, **kwargs: calls.append((args, kwargs))
        or _Response(status_code=status),
    )
    response = himalayas_scraper._request_page(_profile(), 1)
    assert response.status_code == status
    assert len(calls) == expected_calls


@pytest.mark.parametrize("exception_type", [requests.Timeout, requests.ConnectionError])
def test_private_get_retries_transport_exceptions_once(monkeypatch, exception_type):
    calls = []
    monkeypatch.setattr(http_retry.time, "sleep", lambda _delay: None)

    def get(*args, **kwargs):
        calls.append((args, kwargs))
        if len(calls) == 1:
            raise exception_type("bounded fixture")
        return _response(_payload([]))

    monkeypatch.setattr(himalayas_scraper.requests, "get", get)
    assert himalayas_scraper._request_page(_profile(), 1).status_code == 200
    assert len(calls) == 2


def test_http_request_retry_metrics_are_captured_without_schedule_advancement(monkeypatch):
    calls = []
    monkeypatch.setattr(http_retry.time, "sleep", lambda _delay: None)
    monkeypatch.setattr(
        himalayas_scraper.requests,
        "get",
        lambda *args, **kwargs: calls.append((args, kwargs))
        or (_Response(status_code=503) if len(calls) == 1 else _response(_payload([]))),
    )
    outcome = pipeline_metrics.observe_acquisition(
        "himalayas",
        lambda: himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW),
        schedule_on_success=False,
        company="himalayas:engineering",
    )
    metric = pipeline_metrics.acquisition_metrics_snapshot()[0]
    assert outcome.status is AcquisitionStatus.EMPTY
    assert (metric.request_count, metric.retry_count) == (2, 1)
    assert metric.response_status_counts == ((200, 1), (503, 1))
    assert metric.schedule_advanced is False


@pytest.mark.parametrize(
    "response",
    [
        _Response(raw=b"<html></html>", content_type="text/html"),
        _Response(raw=b"<jobs />", content_type="application/xml"),
        _Response(raw=b"{", content_type="application/json"),
        _Response([], content_type="application/json"),
        _response({"jobs": []}),
        _response({**_payload([]), "updatedAt": True}),
        _response(_payload({}, total=0)),
        _response(_payload([_item(str(i)) for i in range(21)], total=21)),
        _response(_payload([_item("excess")], total=0)),
        _response(_payload([], page=1, total=0, limit=21)),
        _response(_payload([], page=1, total=0, offset=20)),
    ],
)
def test_malformed_content_schema_and_pagination_fail_safely(monkeypatch, response):
    _set_page_responses(monkeypatch, response)
    outcome = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)
    assert outcome.status is AcquisitionStatus.FAILED
    assert outcome.reason == "malformed_payload"
    assert outcome.jobs == ()


def test_response_byte_bound_is_enforced(monkeypatch):
    response = _Response(
        raw=b" " * (himalayas_scraper.HIMALAYAS_MAX_RESPONSE_BYTES + 1),
        content_type="application/json",
    )
    _set_page_responses(monkeypatch, response)
    outcome = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)
    assert outcome.reason == "malformed_payload"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (PUBLISHED_MS // 1_000, "2025-08-01T12:00:00Z"),
        (PUBLISHED_MS, "2025-08-01T12:00:00Z"),
        ("2025-08-01T05:30:00+05:30", "2025-08-01T00:00:00Z"),
    ],
)
def test_timestamp_parser_accepts_seconds_milliseconds_and_iso(value, expected):
    normalized, parsed = himalayas_scraper._timestamp(value, now=NOW)
    assert normalized == expected
    assert parsed.tzinfo is timezone.utc


@pytest.mark.parametrize(
    "value",
    [True, False, -1, 1, 100_000_000_000, float("nan"), float("inf"), "", "2026-08-01"],
)
def test_timestamp_parser_rejects_ambiguous_nonfinite_or_implausible_values(value):
    assert himalayas_scraper._timestamp(value, now=NOW) is None


def test_success_normalizes_active_job_and_discards_application_data(monkeypatch):
    _set_page_responses(monkeypatch, _response(_payload([_item()])))
    outcome = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)
    job = outcome.jobs[0]

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert (outcome.page_count, outcome.raw_job_count) == (1, 1)
    assert job["job_id"] == "himalayas_job-123"
    assert job["source"] == "himalayas"
    assert job["company"] == "Acme"
    assert job["title"] == "Software Engineer"
    assert job["posted_at"] == "2025-08-01T12:00:00Z"
    assert job["expiry_date"] == "2026-09-01T10:40:00Z"
    assert job["location"] == ["Remote, United States", "Remote, Canada"]
    assert job["country_restrictions"] == ["United States", "Canada"]
    assert job["timezone_restrictions"] == ["UTC-5", "UTC-8"]
    assert job["remote"] is True
    assert job["worldwide"] is False
    assert job["salary_minimum"] == "120000"
    assert job["salary_maximum"] == "150000.5"
    assert job["salary_period"] == "annual"
    assert job["provider_attribution_required"] is True
    assert job["provider_attribution_label"] == "Himalayas"
    assert job["provider_attribution_url"] == job["url"]
    assert "Build reliable systems" in job["description"]
    assert "Collaborate with the team" in job["description"]
    for suppressed in ("secret()", ".hidden", "Upload resume", "candidate", "Apply now"):
        assert suppressed not in job["description"]
    assert "<" not in job["description"]
    assert len(job["description"]) <= consts.HIMALAYAS_MAX_DESCRIPTION_CHARS
    assert _contains_prohibited_application_data(job) is False


def test_remote_fallback_and_worldwide_require_empty_country_and_timezone():
    item = _item()
    item["locationRestrictions"] = []
    item["timezoneRestrictions"] = []
    state, worldwide = himalayas_scraper._normalize_result(item, now=NOW)
    assert state == "usable"
    assert worldwide["location"] == ["Remote"]
    assert worldwide["worldwide"] is True

    item["timezoneRestrictions"] = ["UTC+2"]
    state, timezone_restricted = himalayas_scraper._normalize_result(item, now=NOW)
    assert state == "usable"
    assert timezone_restricted["location"] == ["Remote"]
    assert timezone_restricted["worldwide"] is False


def test_country_restrictions_accept_exact_live_strings_and_strict_object_priority():
    item = _item()
    item["locationRestrictions"] = [
        "US",
        "Canada",
        {"alpha2": "FR", "name": "Canada", "slug": "united-states"},
        {"name": "United States"},
        {"slug": "germany"},
    ]

    state, job = himalayas_scraper._normalize_result(item, now=NOW)

    assert state == "usable"
    assert job["location"] == [
        "Remote, United States",
        "Remote, Canada",
        "Remote, France",
        "Remote, Germany",
    ]
    assert job["country_restrictions"] == [
        "United States",
        "Canada",
        "France",
        "Germany",
    ]


@pytest.mark.parametrize(
    ("restrictions", "expected", "worldwide", "unresolved"),
    [
        (["US"], ["Remote, United States"], False, False),
        ([{"name": "France"}], ["Remote, France"], False, False),
        ([{"slug": "united-states"}], ["Remote, United States"], False, False),
        (["Worldwide"], ["Remote, Worldwide"], True, False),
        ([], ["Remote"], True, False),
        ([True, {"alpha2": "USA"}, {"name": {"nested": "US"}}], ["Remote"], False, True),
    ],
)
def test_country_restriction_boundaries(
    restrictions, expected, worldwide, unresolved
):
    item = _item()
    item["locationRestrictions"] = restrictions
    item["timezoneRestrictions"] = []

    state, job = himalayas_scraper._normalize_result(item, now=NOW)

    assert state == "usable"
    assert job["location"] == expected
    assert job["worldwide"] is worldwide
    assert bool(job.get("location_restrictions_unresolved")) is unresolved


@pytest.mark.parametrize(
    "application_link",
    [
        "http://himalayas.app/companies/acme/jobs/software-engineer/",
        "https://evil.example/jobs/software-engineer",
        "https://user@himalayas.app/companies/acme/jobs/software-engineer/",
        "https://himalayas.app:444/companies/acme/jobs/software-engineer/",
        "https://himalayas.app/companies/acme/jobs/software-engineer/?track=1",
        "https://himalayas.app/companies/acme/jobs/software-engineer/#apply",
        "https://himalayas.app/jobs/software-engineer",
        "https://himalayas.app/apply/software-engineer",
    ],
)
def test_external_or_unsafe_application_link_makes_row_malformed(application_link):
    state, job = himalayas_scraper._normalize_result(
        _item(application_link=application_link), now=NOW
    )
    assert (state, job) == ("malformed", None)


def test_invalid_application_link_diagnostic_is_bounded_and_payload_free(
    monkeypatch, capsys
):
    invalid = _item(application_link="https://evil.example/private-candidate-payload")
    _set_page_responses(monkeypatch, _response(_payload([_item(), invalid])))

    outcome = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)
    logged = capsys.readouterr().out

    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "parse_error"
    assert len(outcome.jobs) == 1
    assert "row_normalization_invalid_application_link_count=1" in logged
    assert "evil.example" not in logged
    assert "private-candidate-payload" not in logged


@pytest.mark.parametrize(
    "item",
    [
        _item(guid=""),
        _item(title=""),
        _item(company=""),
        _item(publication=True),
        _item(expiry=-1),
        "not-an-object",
    ],
)
def test_missing_required_fields_mark_active_row_malformed(item):
    assert himalayas_scraper._normalize_result(item, now=NOW) == ("malformed", None)


def test_invalid_optional_fields_do_not_invalidate_job():
    item = _item()
    item.update(
        minSalary="NaN",
        maxSalary="not-money",
        salaryPeriod="century",
        companyLogo="javascript:alert(1)",
        locationRestrictions="not-a-list",
        timezoneRestrictions=[None, "UTC-5"],
        categories=[None, "Engineering"],
    )
    state, job = himalayas_scraper._normalize_result(item, now=NOW)
    assert state == "usable"
    assert job["location"] == ["Remote"]
    assert job["timezone_restrictions"] == ["UTC-5"]
    assert "salary_minimum" not in job
    assert "salary_maximum" not in job
    assert "salary_period" not in job
    assert "company_logo_url" not in job


def test_expired_rows_are_omitted_without_parse_error(monkeypatch):
    expired = _item("expired", expiry="2026-08-03T11:59:59Z")
    active = _item("active")

    _set_page_responses(monkeypatch, _response(_payload([expired])))
    expired_only = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)
    assert expired_only.status is AcquisitionStatus.EMPTY
    assert expired_only.raw_job_count == 1

    _set_page_responses(monkeypatch, _response(_payload([expired, active])))
    mixed = himalayas_scraper._fetch_profile_outcome(_profile(), now=lambda: NOW)
    assert mixed.status is AcquisitionStatus.SUCCESS
    assert [job["job_id"] for job in mixed.jobs] == ["himalayas_active"]
    assert mixed.raw_job_count == 2


def test_empty_mixed_and_all_malformed_outcomes(monkeypatch):
    _set_page_responses(monkeypatch, _response(_payload([])))
    empty = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)
    assert (empty.status, empty.page_count, empty.raw_job_count) == (
        AcquisitionStatus.EMPTY,
        1,
        0,
    )

    malformed = _item(title="")
    _set_page_responses(monkeypatch, _response(_payload([_item(), malformed])))
    partial = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)
    assert partial.status is AcquisitionStatus.PARTIAL
    assert partial.reason == "parse_error"
    assert len(partial.jobs) == 1
    assert partial.raw_job_count == 2

    _set_page_responses(monkeypatch, _response(_payload([malformed])))
    failed = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)
    assert failed.status is AcquisitionStatus.FAILED
    assert failed.reason == "parse_error"


def test_first_page_transport_and_non_200_outcomes_are_sanitized(monkeypatch):
    monkeypatch.setattr(
        himalayas_scraper,
        "_request_page",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("private body")),
    )
    transport = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)
    assert (transport.status, transport.reason) == (
        AcquisitionStatus.FAILED,
        "transport_error",
    )
    assert "private body" not in repr(transport)

    _set_page_responses(monkeypatch, _Response(status_code=429))
    limited = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)
    assert (limited.status, limited.reason) == (
        AcquisitionStatus.FAILED,
        "non_200_response",
    )


@pytest.mark.parametrize(
    "second",
    [
        _Response(status_code=503),
        RuntimeError("private"),
        _response({"jobs": []}),
    ],
)
def test_later_page_failure_retains_short_first_page_jobs(monkeypatch, second):
    first_items = [_item(f"job-{index}") for index in range(18)]
    first = _response(_payload(first_items, page=1, total=41))
    if isinstance(second, Exception):
        values = iter([first, second])

        def request(*_args, **_kwargs):
            value = next(values)
            if isinstance(value, Exception):
                raise value
            return value

        monkeypatch.setattr(himalayas_scraper, "_request_page", request)
    else:
        _set_page_responses(monkeypatch, first, second)
    outcome = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)
    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "pagination_interrupted"
    assert (outcome.page_count, outcome.raw_job_count, len(outcome.jobs)) == (1, 18, 18)


def test_short_nonterminal_page_continues_with_exact_http_metrics(monkeypatch):
    first = [_item(f"first-{index}") for index in range(18)]
    second = [_item(f"second-{index}") for index in range(15)]
    responses = iter(
        [
            _response(_payload(first, page=1, total=35)),
            _response(_payload(second, page=2, total=35)),
        ]
    )
    calls = []

    def get(*args, **kwargs):
        calls.append((args, kwargs))
        return next(responses)

    monkeypatch.setattr(himalayas_scraper.requests, "get", get)
    outcome = pipeline_metrics.observe_acquisition(
        "himalayas",
        lambda: himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW),
        schedule_on_success=False,
        company="himalayas:engineering",
    )
    metric = pipeline_metrics.acquisition_metrics_snapshot()[0]

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert (outcome.page_count, outcome.raw_job_count, len(outcome.jobs)) == (2, 33, 33)
    assert len(calls) == 2
    assert (metric.request_count, metric.retry_count) == (2, 0)
    assert metric.response_status_counts == ((200, 2),)
    assert metric.schedule_advanced is False


def test_short_terminal_page_stops_without_requesting_page_two(monkeypatch):
    requests = []

    def request(_profile, page):
        requests.append(page)
        return _response(_payload([_item(str(index)) for index in range(18)], total=18))

    monkeypatch.setattr(himalayas_scraper, "_request_page", request)
    outcome = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert (outcome.page_count, outcome.raw_job_count, len(outcome.jobs)) == (1, 18, 18)
    assert requests == [1]


def test_zero_row_nonterminal_page_continues(monkeypatch):
    _set_page_responses(
        monkeypatch,
        _response(_payload([], page=1, total=21)),
        _response(_payload([_item("last")], page=2, total=21)),
    )
    outcome = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert (outcome.page_count, outcome.raw_job_count, len(outcome.jobs)) == (2, 1, 1)


def test_two_short_nonterminal_pages_reach_cap_without_page_three(monkeypatch, capsys):
    monkeypatch.setattr(himalayas_scraper, "HIMALAYAS_MAX_PAGES_PER_PROFILE", 2)
    requests = []
    pages = {
        1: _response(
            _payload([_item(f"first-{index}") for index in range(18)], page=1, total=41)
        ),
        2: _response(
            _payload([_item(f"second-{index}") for index in range(18)], page=2, total=41)
        ),
    }

    def request(_profile, page):
        requests.append(page)
        return pages[page]

    monkeypatch.setattr(himalayas_scraper, "_request_page", request)
    outcome = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)
    logged = capsys.readouterr().out

    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "pagination_limit_reached"
    assert (outcome.page_count, outcome.raw_job_count, len(outcome.jobs)) == (2, 36, 36)
    assert requests == [1, 2]
    assert "bounded_page_cap_reached=true" in logged


def test_intentional_page_cap_retains_40_jobs_and_logs_bounded_marker(monkeypatch, capsys):
    monkeypatch.setattr(himalayas_scraper, "HIMALAYAS_MAX_PAGES_PER_PROFILE", 2)
    first = [_item(f"first-{index}") for index in range(20)]
    second = [_item(f"second-{index}") for index in range(20)]
    _set_page_responses(
        monkeypatch,
        _response(_payload(first, page=1, total=60)),
        _response(_payload(second, page=2, total=60)),
    )
    outcome = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)
    logged = capsys.readouterr().out
    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "pagination_limit_reached"
    assert (outcome.page_count, outcome.raw_job_count, len(outcome.jobs)) == (2, 40, 40)
    assert "bounded_page_cap_reached=true" in logged
    assert "engineer" not in logged


def test_repeated_page_is_partial_without_requesting_to_ceiling(monkeypatch):
    rows = [_item(f"same-{index}") for index in range(2)]
    repeated = _response(_payload(rows, total=50))
    requests = []

    def request(_profile, page):
        requests.append(page)
        payload = json.loads(repeated.content)
        payload["offset"] = (page - 1) * 20
        return _response(payload)

    monkeypatch.setattr(himalayas_scraper, "_request_page", request)

    outcome = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)

    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "pagination_no_progress"
    assert (outcome.page_count, outcome.raw_job_count, len(outcome.jobs)) == (2, 4, 2)
    assert requests == [1, 2]


def test_reordered_page_with_zero_new_guids_is_partial(monkeypatch):
    first = [_item("one"), _item("two")]
    second = [_item("two"), _item("one")]
    _set_page_responses(
        monkeypatch,
        _response(_payload(first, page=1, total=50)),
        _response(_payload(second, page=2, total=50)),
    )

    outcome = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)

    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "pagination_no_progress"
    assert (outcome.page_count, outcome.raw_job_count, len(outcome.jobs)) == (2, 4, 2)


def test_empty_nonterminal_page_can_continue_to_a_later_result(monkeypatch):
    _set_page_responses(
        monkeypatch,
        _response(_payload([], page=1, total=21)),
        _response(_payload([_item("last")], page=2, total=21)),
    )

    outcome = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert (outcome.page_count, outcome.raw_job_count, len(outcome.jobs)) == (2, 1, 1)


@pytest.mark.parametrize(("total", "status", "reason"), [
    (201, AcquisitionStatus.PARTIAL, "pagination_limit_reached"),
    (200, AcquisitionStatus.SUCCESS, ""),
])
def test_page_ten_ceiling_status_and_no_page_eleven(
    monkeypatch, total, status, reason
):
    requests = []

    def request(_profile, page):
        requests.append(page)
        rows = [_item(f"page-{page}-{index}") for index in range(20)]
        return _response(_payload(rows, page=page, total=total))

    monkeypatch.setattr(himalayas_scraper, "_request_page", request)

    outcome = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)

    assert outcome.status is status
    assert outcome.reason == reason
    assert (outcome.page_count, outcome.raw_job_count, len(outcome.jobs)) == (10, 200, 200)
    assert requests == list(range(1, 11))


def test_same_guid_in_separate_profiles_remains_for_centralized_dedupe(monkeypatch):
    responses = iter(
        [
            _response(_payload([_item("shared")])),
            _response(_payload([_item("shared")])),
        ]
    )
    monkeypatch.setattr(
        himalayas_scraper,
        "_request_page",
        lambda *_args, **_kwargs: next(responses),
    )

    data = himalayas_scraper._fetch_profile_outcome(_profile("data-us"), now=NOW)
    software = himalayas_scraper._fetch_profile_outcome(
        _profile("software-us"), now=NOW
    )

    assert len(data.jobs) == len(software.jobs) == 1
    assert data.jobs[0]["job_id"] == software.jobs[0]["job_id"]


def test_profiles_execute_sequentially_in_sorted_order_with_exact_metrics(monkeypatch):
    profiles = [_profile("alpha"), _profile("zeta")]
    monkeypatch.setattr(himalayas_scraper, "_load_query_profiles", lambda: profiles)
    order = []

    def outcome(profile):
        order.append(profile["profile_id"])
        return himalayas_scraper.AcquisitionOutcome(
            f"himalayas:{profile['profile_id']}",
            AcquisitionStatus.SUCCESS,
            ({"source": "himalayas", "job_id": profile["profile_id"]},),
            page_count=1,
            raw_job_count=1,
        )

    monkeypatch.setattr(himalayas_scraper, "_fetch_profile_outcome", outcome)
    jobs = himalayas_scraper.scrape_all_himalayas()
    metrics = pipeline_metrics.acquisition_metrics_snapshot()
    assert order == ["alpha", "zeta"]
    assert [job["job_id"] for job in jobs] == ["alpha", "zeta"]
    assert [(metric.source, metric.company) for metric in metrics] == [
        ("himalayas", "himalayas:alpha"),
        ("himalayas", "himalayas:zeta"),
    ]
    assert all(metric.schedule_advanced is False for metric in metrics)


def test_adapter_retains_structurally_trustworthy_irrelevant_job(monkeypatch):
    item = _item(title="Chief Poetry Officer")
    item["locationRestrictions"] = [{"name": "France"}]
    _set_page_responses(monkeypatch, _response(_payload([item])))
    outcome = himalayas_scraper._fetch_profile_outcome(_profile(), now=NOW)
    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.jobs[0]["title"] == "Chief Poetry Officer"
    assert outcome.jobs[0]["location"] == ["Remote, France"]


def test_bounds_limit_active_profile_requests_to_twenty():
    assert consts.HIMALAYAS_MAX_QUERY_PROFILES == 4
    assert consts.HIMALAYAS_MAX_PAGES_PER_PROFILE == 10
    assert consts.HIMALAYAS_RESULTS_PER_PAGE == 20
    assert (
        2
        * consts.HIMALAYAS_MAX_PAGES_PER_PROFILE
        == 20
    )


def test_collector_registers_himalayas_once_after_usajobs_before_filter_and_dedupe():
    source = inspect.getsource(collector.collect_all_jobs_async)
    assert source.count('(\"himalayas\", scrape_all_himalayas)') == 1
    himalayas_position = source.index('(\"himalayas\", scrape_all_himalayas)')
    usajobs_position = source.index('(\"usajobs\", scrape_all_usajobs)')
    filter_position = source.index("filter_jobs(", himalayas_position)
    dedupe_position = source.index("dedupe_jobs(", filter_position)
    assert usajobs_position < himalayas_position < filter_position < dedupe_position


def test_direct_duplicate_wins_without_himalayas_attribution():
    state, supplemental = himalayas_scraper._normalize_result(_item(), now=NOW)
    assert state == "usable"
    direct = {
        **supplemental,
        "source": "greenhouse",
        "job_id": "greenhouse_123",
    }
    for key in (
        "provider_attribution_required",
        "provider_attribution_label",
        "provider_attribution_url",
    ):
        direct.pop(key)
    assert dedupe_jobs([supplemental, direct]) == [direct]
    assert not any("provider_attribution" in key for key in direct)


def test_module_has_no_prefilter_schedule_application_or_detail_request_authority():
    acquisition_source = inspect.getsource(himalayas_scraper._fetch_profile_outcome).lower()
    for predicate in (
        "title_matches",
        "selected_seniority",
        "strict_seniority",
        "preferred_locations",
        "excluded_keywords",
        "llm",
    ):
        assert predicate not in acquisition_source

    module_source = Path(himalayas_scraper.__file__).read_text(encoding="utf-8").lower()
    for marker in (
        "load_schedule",
        "save_schedule",
        "mark_scraped",
        "run_parallel",
        "http_post",
        "requests.post",
        "submit_application",
        "ats_submit",
        "message_recruiter",
        "upload_resume",
    ):
        assert marker not in module_source
