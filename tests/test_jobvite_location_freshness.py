import json
from datetime import datetime, timedelta, timezone

import pytest

from src.discovery.crawl_scheduler import AcquisitionStatus
from src.pipeline import job_filter
from src.scrapers import jobvite_scraper
from src.utils.html_timestamp_extractor import (
    extract_jsonld_dateposted,
    extract_jsonld_jobposting_metadata,
)


class _Response:
    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code


def _jsonld(payload):
    return (
        '<script type="application/ld+json">'
        + json.dumps(payload)
        + "</script>"
    )


def _posting(**overrides):
    posting = {
        "@type": "JobPosting",
        "datePosted": "2026-08-05",
        "jobLocation": {
            "@type": "Place",
            "address": {
                "addressLocality": "Kirkland",
                "addressRegion": "Washington",
                "addressCountry": "United States",
            },
        },
    }
    posting.update(overrides)
    return posting


@pytest.mark.parametrize(
    "payload",
    [
        _posting(),
        [_posting()],
        {"@graph": [_posting()]},
        {"nested": {"payload": _posting(**{"@type": ["Thing", "JobPosting"]})}},
    ],
)
def test_jobposting_metadata_supports_jsonld_shapes_and_type_lists(payload):
    metadata = extract_jsonld_jobposting_metadata(_jsonld(payload))

    assert metadata["posted_at"] == "2026-08-05"
    assert metadata["locations"] == ["Kirkland, Washington, United States"]
    assert extract_jsonld_dateposted(_jsonld(payload)) == "2026-08-05"


def test_jobposting_metadata_supports_multiple_locations():
    payload = _posting(
        jobLocation=[
            {"address": {"addressLocality": "Seattle", "addressRegion": "WA", "addressCountry": "US"}},
            {"address": {"addressLocality": "Portland", "addressRegion": "OR", "addressCountry": "US"}},
        ]
    )

    assert extract_jsonld_jobposting_metadata(_jsonld(payload))["locations"] == [
        "Seattle, WA, US",
        "Portland, OR, US",
    ]


@pytest.mark.parametrize(
    ("requirement", "expected"),
    [
        ({"@type": "Country", "name": "United States"}, ["Remote, United States"]),
        ({"@type": "Country", "name": "India"}, ["Remote, India"]),
        (None, ["Remote"]),
    ],
)
def test_jobposting_metadata_preserves_remote_country_semantics(requirement, expected):
    payload = _posting(jobLocation=None, jobLocationType="TELECOMMUTE")
    if requirement is not None:
        payload["applicantLocationRequirements"] = requirement

    metadata = extract_jsonld_jobposting_metadata(_jsonld(payload))

    assert metadata["locations"] == expected
    assert metadata["job_location_type"] == "TELECOMMUTE"


def test_jobposting_metadata_tolerates_malformed_or_absent_jsonld():
    expected = {
        "posted_at": None,
        "locations": [],
        "job_location_type": "",
        "applicant_location_requirements": [],
    }

    assert extract_jsonld_jobposting_metadata('<script type="application/ld+json">{</script>') == expected
    assert extract_jsonld_jobposting_metadata("<html></html>") == expected
    assert extract_jsonld_dateposted("<html></html>") is None


def test_dateposted_backward_compatibility_checks_later_jsonld_blocks():
    first = _jsonld(_posting(datePosted=None, datePublished=None))
    second = _jsonld(_posting(datePosted="2026-08-04"))

    assert extract_jsonld_dateposted(first + second) == "2026-08-04"


def test_parse_jobvite_listing_handles_proven_layouts_and_deduplicates():
    page = """
    <div class="jv-featured-job">
      <a href="/acme/job/featured123"><span>Backend Engineer</span><span>Remote, United States</span></a>
      <span class="jv-tag-new">New</span>
    </div>
    <div class="jv-job-list"><ul>
      <li class="row"><a href="/acme/job/foreign456"><span>Data Engineer</span><span>Remote, India | Job Type: Full-Time |</span></a></li>
      <li class="row"><a href="/acme/job/hybrid789"><span>Platform Engineer</span><span>Hybrid Remote, San Diego, California</span></a></li>
      <li class="row"><a href="/acme/job/remote111"><span>Software Engineer</span><span>Remote</span></a></li>
      <li class="row"><a href="/acme/job/multi222"><span>QA Engineer</span><span>2 Locations</span></a></li>
      <li class="row"><a href="/acme/job/featured123"><span>Duplicate</span><span>Kirkland, Washington</span></a></li>
    </ul></div>
    """

    records = jobvite_scraper.parse_jobvite_listing(page)

    assert [(row["title"], row["location"], row["jobvite_id"]) for row in records] == [
        ("Backend Engineer", "Remote, United States", "featured123"),
        ("Data Engineer", "Remote, India", "foreign456"),
        ("Platform Engineer", "Hybrid Remote, San Diego, California", "hybrid789"),
        ("Software Engineer", "Remote", "remote111"),
        ("QA Engineer", "2 Locations", "multi222"),
    ]
    assert records[0]["is_new"] is True


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("acme", "acme"),
        ("Acme", "acme"),
        ("acme-data", "acme-data"),
        ("acme_data", "acme_data"),
        ("company2", "company2"),
        ("company-2026", "company-2026"),
    ],
)
def test_jobvite_company_normalization_preserves_valid_identity(value, expected):
    assert jobvite_scraper._normalize_jobvite_company(value) == expected


@pytest.mark.parametrize(
    "value",
    [
        "",
        "   ",
        "jobs",
        "job",
        "careers",
        "apply",
        "www",
        "acme corp",
        "acme/jobs",
        "acme?x=1",
        "acme#section",
        "-acme",
        "acme-",
        "_acme",
        "acme_",
    ],
)
def test_jobvite_company_normalization_rejects_invalid_identity(value):
    assert jobvite_scraper._normalize_jobvite_company(value) is None


def test_validate_jobvite_company_uses_existing_transport_and_listing_parser(
    monkeypatch,
):
    calls = []
    parser_calls = []
    html = '<a href="/acme/job/abc123">Software Engineer</a>'

    monkeypatch.setattr(
        jobvite_scraper,
        "jobvite_get",
        lambda url, **kwargs: calls.append((url, kwargs)) or _Response(html),
    )
    monkeypatch.setattr(
        jobvite_scraper,
        "parse_jobvite_listing",
        lambda value: parser_calls.append(value) or [{"jobvite_id": "abc123"}],
    )

    assert jobvite_scraper.validate_jobvite_company(" Acme ") is True
    assert calls == [
        (
            jobvite_scraper.JOBVITE_URL_PATTERNS[0].format(company="acme"),
            {"timeout": 10},
        ),
    ]
    assert parser_calls == [html]


def test_validate_jobvite_company_falls_back_in_pattern_order(monkeypatch):
    calls = []
    valid_html = '<a href="/acme/job/abc123">Software Engineer</a>'

    def get(url, **kwargs):
        calls.append((url, kwargs))
        if len(calls) == 1:
            return _Response(status_code=404)
        return _Response(valid_html)

    monkeypatch.setattr(jobvite_scraper, "jobvite_get", get)

    assert jobvite_scraper.validate_jobvite_company("acme") is True
    assert calls == [
        (pattern.format(company="acme"), {"timeout": 10})
        for pattern in jobvite_scraper.JOBVITE_URL_PATTERNS
    ]


@pytest.mark.parametrize(
    "responses",
    [
        [_Response(status_code=404), _Response(status_code=500)],
        [OSError("offline"), OSError("offline")],
        [_Response(""), _Response("")],
        [_Response("<html>arbitrary</html>"), _Response("<html>no listings</html>")],
        [_Response('<a href="/not-a-job">Malformed</a>')] * 2,
    ],
)
def test_validate_jobvite_company_rejects_unproven_boards(monkeypatch, responses):
    values = iter(responses)

    def get(*_args, **_kwargs):
        value = next(values)
        if isinstance(value, Exception):
            raise value
        return value

    monkeypatch.setattr(jobvite_scraper, "jobvite_get", get)

    assert jobvite_scraper.validate_jobvite_company("acme") is False


def test_validate_jobvite_company_rejects_malformed_identity_without_request(
    monkeypatch,
):
    monkeypatch.setattr(
        jobvite_scraper,
        "jobvite_get",
        lambda *args, **kwargs: pytest.fail("malformed identity must not fetch"),
    )

    assert jobvite_scraper.validate_jobvite_company("bad/path") is False


def test_validate_jobvite_company_contains_parser_failures(monkeypatch):
    monkeypatch.setattr(
        jobvite_scraper,
        "jobvite_get",
        lambda *args, **kwargs: _Response("<html>candidate board</html>"),
    )
    monkeypatch.setattr(
        jobvite_scraper,
        "parse_jobvite_listing",
        lambda _html: (_ for _ in ()).throw(ValueError("bad fixture")),
    )

    assert jobvite_scraper.validate_jobvite_company("acme") is False


def test_validate_jobvite_companies_is_deterministic(monkeypatch):
    calls = []

    def validate(company):
        calls.append(company)
        return company in {"alpha", "zulu2"}

    monkeypatch.setattr(jobvite_scraper, "validate_jobvite_company", validate)

    assert jobvite_scraper.validate_jobvite_companies(
        ["Zulu2", "alpha", "zulu2", "Beta_Co", "bad/path"]
    ) == ["alpha", "zulu2"]
    assert calls == ["alpha", "beta_co", "zulu2"]


def test_acquisition_fetches_detail_only_for_ambiguous_listing_locations(monkeypatch):
    page = """
    <div class="jv-job-list"><ul>
      <li class="row"><a href="/acme/job/us1"><span>Backend Engineer</span><span>Kirkland, Washington</span></a></li>
      <li class="row"><a href="/acme/job/foreign2"><span>Data Engineer</span><span>Remote, India</span></a></li>
      <li class="row"><a href="/acme/job/remote3"><span>Software Engineer</span><span>Remote</span></a></li>
      <li class="row"><a href="/acme/job/multi4"><span>QA Engineer</span><span>2 Locations</span></a></li>
    </ul></div>
    """
    calls = []

    def get(url, **_kwargs):
        calls.append(url)
        if url.endswith("/jobs/alljobs"):
            return _Response(page)
        if url.endswith("/remote3"):
            return _Response(_jsonld(_posting(jobLocationType="TELECOMMUTE", applicantLocationRequirements={"name": "United States"})))
        if url.endswith("/multi4"):
            return _Response(_jsonld(_posting(jobLocation=[{"address": {"addressLocality": "Seattle", "addressRegion": "WA", "addressCountry": "US"}}, {"address": {"addressLocality": "Portland", "addressRegion": "OR", "addressCountry": "US"}}])))
        raise AssertionError(f"unexpected request {url}")

    monkeypatch.setattr(jobvite_scraper, "JOBVITE_URL_PATTERNS", ["https://jobs.jobvite.com/{company}/jobs/alljobs"])
    monkeypatch.setattr(jobvite_scraper, "jobvite_get", get)
    monkeypatch.setattr(jobvite_scraper, "learn_from_job_url", lambda _url: None)

    outcome = jobvite_scraper._fetch_company_outcome("acme")

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert len(outcome.jobs) == 4
    assert len(calls) == 3
    assert [job["_jobvite_metadata_source"] for job in outcome.jobs] == [
        "listing", "listing", "detail_fallback", "detail_fallback"
    ]
    assert outcome.jobs[0]["posted_at"] is None
    assert outcome.jobs[1]["location"] == "Remote, India"
    assert outcome.jobs[2]["location"] == "Remote, United States"
    assert outcome.jobs[2]["posted_at"] == "2026-08-05"
    assert outcome.jobs[3]["location"] == ["Seattle, WA, US", "Portland, OR, US"]


def test_failed_optional_acquisition_metadata_retains_job(monkeypatch):
    page = '<div class="jv-job-list"><li class="row"><a href="/acme/job/remote1"><span>Backend Engineer</span><span>Remote</span></a></li></div>'
    responses = iter([_Response(page), _Response(status_code=500)])
    monkeypatch.setattr(jobvite_scraper, "JOBVITE_URL_PATTERNS", ["https://jobs.jobvite.com/{company}/jobs/alljobs"])
    monkeypatch.setattr(jobvite_scraper, "jobvite_get", lambda *_args, **_kwargs: next(responses))
    monkeypatch.setattr(jobvite_scraper, "learn_from_job_url", lambda _url: None)

    outcome = jobvite_scraper._fetch_company_outcome("acme")

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert len(outcome.jobs) == 1
    assert outcome.jobs[0]["location"] == "Remote"
    assert outcome.jobs[0]["posted_at"] is None
    assert outcome.jobs[0]["_jobvite_metadata_source"] == "unresolved"


def _fresh_timestamp():
    return datetime.now(timezone.utc).isoformat()


def _filter_job(suffix, **overrides):
    job = {
        "company": "acme",
        "title": "Backend Engineer",
        "location": "Remote, United States",
        "source": "jobvite",
        "posted_at": None,
        "url": f"https://jobs.jobvite.com/acme/job/{suffix}",
    }
    job.update(overrides)
    return job


def test_timestamp_hydration_obeys_filter_order_cache_and_existing_values(monkeypatch):
    calls = []

    def fetch(url):
        calls.append(url)
        return {"posted_at": _fresh_timestamp(), "marker": "", "status_code": 200}

    monkeypatch.setattr(job_filter, "fetch_jobvite_metadata_result", fetch)
    populated = _filter_job("existing", posted_at=_fresh_timestamp())
    duplicate_url = "https://jobs.jobvite.com/acme/job/shared?tracking=1"
    jobs = [
        _filter_job("title-reject", title="Nurse"),
        _filter_job("foreign", location="Remote, India"),
        _filter_job("generic", location="Remote"),
        populated,
        _filter_job("shared"),
        _filter_job("shared-duplicate", url=duplicate_url),
    ]
    jobs[-1]["url"] = "https://jobs.jobvite.com/acme/job/shared?tracking=2"

    filtered, diagnostics = job_filter.filter_jobs(
        jobs,
        selected_role_families=["backend_engineering"],
        return_diagnostics=True,
    )

    assert calls == ["https://jobs.jobvite.com/acme/job/shared"]
    assert filtered == [populated, jobs[4], jobs[5]]
    assert diagnostics["jobvite_timestamp_cache_miss"] == 1
    assert diagnostics["jobvite_timestamp_cache_hit"] == 1
    assert diagnostics["jobvite_timestamp_fetch_success"] == 1


@pytest.mark.parametrize("status_code", [429, 500])
def test_failed_timestamp_hydration_uses_normal_missing_timestamp_rejection(monkeypatch, status_code):
    monkeypatch.setattr(
        job_filter,
        "fetch_jobvite_metadata_result",
        lambda _url: {
            "posted_at": None,
            "marker": "jobvite_metadata_request_failed",
            "status_code": status_code,
        },
    )
    audit_rows = []

    filtered, diagnostics = job_filter.filter_jobs(
        [_filter_job("missing")],
        selected_role_families=["backend_engineering"],
        role_title_audit_rows=audit_rows,
        return_diagnostics=True,
    )

    assert filtered == []
    assert diagnostics["missing_timestamp"] == 1
    expected_key = (
        "jobvite_timestamp_fetch_429"
        if status_code == 429
        else "jobvite_timestamp_fetch_failed"
    )
    assert diagnostics[expected_key] == 1
    assert audit_rows[0]["jobvite_timestamp_fetch_decision"] == (
        "429" if status_code == 429 else "failed"
    )
    assert audit_rows[0]["freshness_filter_reason"] == "missing_timestamp"


def test_stale_hydrated_timestamp_is_rejected_as_not_recent(monkeypatch):
    stale = (datetime.now(timezone.utc) - timedelta(days=3)).isoformat()
    monkeypatch.setattr(
        job_filter,
        "fetch_jobvite_metadata_result",
        lambda _url: {"posted_at": stale, "marker": "", "status_code": 200},
    )

    filtered, diagnostics = job_filter.filter_jobs(
        [_filter_job("stale")],
        selected_role_families=["backend_engineering"],
        return_diagnostics=True,
    )

    assert filtered == []
    assert diagnostics["not_recent"] == 1
    assert diagnostics["jobvite_timestamp_fetch_success"] == 1
