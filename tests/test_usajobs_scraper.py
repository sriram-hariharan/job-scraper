import inspect
import json
from collections import Counter
from pathlib import Path
from types import SimpleNamespace

import pytest

from src.config import consts
from src.discovery.crawl_scheduler import AcquisitionStatus
from src.pipeline import collector, job_details
from src.scrapers import usajobs_scraper
from src.utils import http_retry, pipeline_metrics


class _Response:
    def __init__(self, payload=None, *, status_code=200, content_type="application/json", raw=None):
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}
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
        "keyword": "engineer",
        "location_name": "",
        "organization_codes": (),
        "job_category_codes": (),
        "remote_only": False,
    }
    profile.update(overrides)
    return profile


def _item(control_number="123", *, title="Software Engineer", company="Agency", url=None):
    return {
        "MatchedObjectId": control_number,
        "MatchedObjectDescriptor": {
            "PositionID": "ABC-2026-001",
            "PositionTitle": title,
            "PositionURI": url or f"https://www.usajobs.gov/GetJob/ViewDetails/{control_number}",
            "ApplyURI": ["https://apply.usastaffing.gov/Application/Apply"],
            "PositionLocationDisplay": "Washington, District of Columbia",
            "PositionLocation": [
                {"LocationName": "Washington, District of Columbia"},
                {"LocationName": "New York, New York"},
                {"LocationName": "Washington, District of Columbia"},
            ],
            "OrganizationName": company,
            "DepartmentName": "Department",
            "JobCategory": [{"Name": "Information Technology Management", "Code": "2210"}],
            "JobGrade": [{"Code": "GS"}],
            "PositionSchedule": [{"Name": "Full-time", "Code": "1"}],
            "PositionOfferingType": [{"Name": "Permanent", "Code": "15317"}],
            "QualificationSummary": "<p>Qualified candidates build systems.</p>",
            "PositionRemuneration": [
                {
                    "MinimumRange": "120000.00",
                    "MaximumRange": "150000.50",
                    "RateIntervalCode": "Per Year",
                }
            ],
            "PositionStartDate": "2026-08-01T00:00:00Z",
            "PositionEndDate": "2026-08-08T23:59:59Z",
            "PublicationStartDate": "2026-08-01T12:00:00Z",
            "ApplicationCloseDate": "2026-08-08T23:59:59Z",
            "UserArea": {
                "Details": {
                    "JobSummary": "<p>Build public systems.</p>",
                    "MajorDuties": "<ul><li>Design APIs</li></ul>",
                    "Education": "Degree or experience.",
                    "Requirements": "Public trust.",
                    "Evaluations": "Experience is evaluated.",
                    "OtherInformation": "Read more at https://example.test/info",
                    "HowToApply": "Upload a resume at https://apply.example.test",
                    "RequiredDocuments": "Resume and application form",
                    "SubAgencyName": "Subagency",
                    "WhoMayApply": {"Name": "The public", "Code": "public"},
                }
            },
        },
    }


def _payload(items, *, pages=1, total=None):
    total = len(items) if total is None else total
    return {
        "LanguageCode": "EN",
        "SearchParameters": {},
        "SearchResult": {
            "SearchResultCount": len(items),
            "SearchResultCountAll": total,
            "SearchResultItems": items,
            "UserArea": {"NumberOfPages": pages},
        },
    }


def _full_page_items(page):
    first_control_number = ((page - 1) * consts.USAJOBS_RESULTS_PER_PAGE) + 1
    return [
        _item(str(control_number))
        for control_number in range(
            first_control_number,
            first_control_number + consts.USAJOBS_RESULTS_PER_PAGE,
        )
    ]


def _set_page_responses(monkeypatch, *responses):
    values = iter(responses)
    monkeypatch.setattr(
        usajobs_scraper,
        "_request_page",
        lambda *_args, **_kwargs: next(values),
    )


def _contains_prohibited_application_data(value):
    prohibited_keys = {"applyuri", "howtoapply", "candidateurl", "applicationform"}
    prohibited_values = (
        "apply.usastaffing.gov",
        "apply.example.test",
        "upload a resume",
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


def test_number_of_pages_accepts_nonnegative_integer():
    assert usajobs_scraper._usajobs_number_of_pages(0) == 0
    assert usajobs_scraper._usajobs_number_of_pages(12) == 12


@pytest.mark.parametrize("value", ["0", "1", "12"])
def test_number_of_pages_accepts_canonical_decimal_string(value):
    assert usajobs_scraper._usajobs_number_of_pages(value) == int(value)


def test_provider_payload_with_string_number_of_pages_parses_successfully():
    items = [_item(str(index)) for index in range(1, 51)]
    parsed_items, number_of_pages = usajobs_scraper._parse_page(
        _Response(_payload(items, pages="2", total=51)),
        1,
    )
    assert parsed_items == items
    assert number_of_pages == 2


@pytest.mark.parametrize(
    "value",
    [
        True,
        False,
        -1,
        "+1",
        "-1",
        " 1",
        "1 ",
        "1.0",
        "1e2",
        "",
        1.0,
        None,
        {},
        [],
    ],
)
def test_number_of_pages_rejects_noncanonical_values(value):
    with pytest.raises(usajobs_scraper._MalformedPayload):
        usajobs_scraper._usajobs_number_of_pages(value)


@pytest.mark.parametrize("value", [201, "201", "9" * 5_000])
def test_number_of_pages_exceeding_provider_window_is_rejected(value):
    with pytest.raises(usajobs_scraper._MalformedPayload):
        usajobs_scraper._parse_page(_Response(_payload([], pages=value, total=0)), 1)


@pytest.mark.parametrize("field", ["SearchResultCount", "SearchResultCountAll"])
def test_result_counts_retain_strict_integer_contract(field):
    payload = _payload([], pages=0, total=0)
    payload["SearchResult"][field] = "0"
    with pytest.raises(usajobs_scraper._MalformedPayload):
        usajobs_scraper._parse_page(_Response(payload), 1)


def test_checked_in_query_profiles_activate_proven_bounded_public_it_data_scope():
    path = Path(consts.USAJOBS_QUERY_PROFILES_PATH)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload == [
        {
            "profile_id": "public-it-data-us",
            "keyword": "",
            "location_name": "",
            "organization_codes": [],
            "job_category_codes": [
                "0391",
                "0854",
                "0855",
                "1515",
                "1529",
                "1530",
                "1550",
                "1560",
                "2210",
            ],
            "remote_only": False,
        },
        {
            "profile_id": "public-keyword-artificial-intelligence-us",
            "keyword": "artificial intelligence",
            "location_name": "",
            "organization_codes": [],
            "job_category_codes": [],
            "remote_only": False,
        },
        {
            "profile_id": "public-keyword-data-scientist-us",
            "keyword": "data scientist",
            "location_name": "",
            "organization_codes": [],
            "job_category_codes": [],
            "remote_only": False,
        },
    ]

    profiles = usajobs_scraper._load_query_profiles()
    assert [profile["profile_id"] for profile in profiles] == [
        "public-it-data-us",
        "public-keyword-artificial-intelligence-us",
        "public-keyword-data-scientist-us",
    ]

    params_by_profile = {
        profile["profile_id"]: usajobs_scraper._profile_params(profile, 1)
        for profile in profiles
    }

    assert params_by_profile["public-it-data-us"] == {
        "WhoMayApply": "Public",
        "Fields": "Full",
        "DatePosted": 1,
        "ResultsPerPage": 50,
        "Page": 1,
        "JobCategoryCode": "0391;0854;0855;1515;1529;1530;1550;1560;2210",
    }
    assert params_by_profile[
        "public-keyword-artificial-intelligence-us"
    ] == {
        "WhoMayApply": "Public",
        "Fields": "Full",
        "DatePosted": 1,
        "ResultsPerPage": 50,
        "Page": 1,
        "Keyword": "artificial intelligence",
    }
    assert params_by_profile["public-keyword-data-scientist-us"] == {
        "WhoMayApply": "Public",
        "Fields": "Full",
        "DatePosted": 1,
        "ResultsPerPage": 50,
        "Page": 1,
        "Keyword": "data scientist",
    }

    assert all(
        profile["keyword"] != "machine learning"
        for profile in profiles
    )
def test_active_checked_in_profiles_are_eligible_for_acquisition_without_live_http(
    monkeypatch,
):
    monkeypatch.setenv("USAJOBS_API_KEY", "fixture-key")
    monkeypatch.setenv(
        "USAJOBS_USER_AGENT_EMAIL",
        "owner@example.test",
    )
    captured = []

    def acquire(profile, api_key, user_agent_email):
        profile_id = profile["profile_id"]
        captured.append((profile, api_key, user_agent_email))
        return usajobs_scraper.AcquisitionOutcome(
            f"usajobs:{profile_id}",
            AcquisitionStatus.SUCCESS,
            (
                {
                    "source": "usajobs",
                    "job_id": f"usajobs_{profile_id}",
                },
            ),
            page_count=1,
            raw_job_count=1,
        )

    monkeypatch.setattr(
        usajobs_scraper,
        "_fetch_profile_outcome",
        acquire,
    )

    assert usajobs_scraper.scrape_all_usajobs() == [
        {
            "source": "usajobs",
            "job_id": "usajobs_public-it-data-us",
        },
        {
            "source": "usajobs",
            "job_id": (
                "usajobs_"
                "public-keyword-artificial-intelligence-us"
            ),
        },
        {
            "source": "usajobs",
            "job_id": "usajobs_public-keyword-data-scientist-us",
        },
    ]

    assert [
        row[0]["profile_id"]
        for row in captured
    ] == [
        "public-it-data-us",
        "public-keyword-artificial-intelligence-us",
        "public-keyword-data-scientist-us",
    ]

    assert all(
        api_key == "fixture-key"
        and user_agent_email == "owner@example.test"
        for _, api_key, user_agent_email in captured
    )
def test_empty_profiles_exit_before_credentials_http_metrics_or_schedule(monkeypatch):
    monkeypatch.setattr(usajobs_scraper, "_load_query_profiles", lambda: [])

    class _ForbiddenEnvironment:
        def get(self, *_args, **_kwargs):
            pytest.fail("credentials must not be inspected")

    monkeypatch.setattr(usajobs_scraper, "os", SimpleNamespace(environ=_ForbiddenEnvironment()))
    for owner in ("_request_page", "observe_acquisition"):
        monkeypatch.setattr(
            usajobs_scraper,
            owner,
            lambda *args, _owner=owner, **kwargs: pytest.fail(f"{_owner} must not run"),
        )
    assert usajobs_scraper.scrape_all_usajobs() == []
    assert pipeline_metrics.acquisition_metrics_snapshot() == ()


@pytest.mark.parametrize(
    "environment",
    [
        {"USAJOBS_USER_AGENT_EMAIL": "owner@example.test"},
        {"USAJOBS_API_KEY": "fixture-key"},
        {"USAJOBS_API_KEY": "", "USAJOBS_USER_AGENT_EMAIL": "owner@example.test"},
    ],
)
def test_missing_credentials_disable_before_http_and_metrics(monkeypatch, environment):
    monkeypatch.setattr(usajobs_scraper, "_load_query_profiles", lambda: [_profile()])
    monkeypatch.setattr(usajobs_scraper, "os", SimpleNamespace(environ=environment))
    monkeypatch.setattr(
        usajobs_scraper,
        "_request_page",
        lambda *args, **kwargs: pytest.fail("HTTP must not run"),
    )
    monkeypatch.setattr(
        usajobs_scraper,
        "observe_acquisition",
        lambda *args, **kwargs: pytest.fail("metrics must not run"),
    )
    assert usajobs_scraper.scrape_all_usajobs() == []


def test_profile_loader_accepts_four_and_sorts_deterministically(tmp_path):
    profiles = [
        {"profile_id": "z-profile", "remote_only": True},
        {"profile_id": "a_profile", "keyword": "data"},
        {"profile_id": "two", "location_name": "New York, New York"},
        {"profile_id": "three", "organization_codes": ["TR", "AF", "TR"]},
    ]
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps(profiles), encoding="utf-8")
    loaded = usajobs_scraper._load_query_profiles(path)
    assert [profile["profile_id"] for profile in loaded] == [
        "a_profile",
        "three",
        "two",
        "z-profile",
    ]
    assert loaded[1]["organization_codes"] == ("AF", "TR")


@pytest.mark.parametrize(
    "profiles",
    [
        [{"profile_id": str(index), "keyword": "x"} for index in range(5)],
        [{"profile_id": "dup", "keyword": "x"}, {"profile_id": "dup", "keyword": "y"}],
        [{"profile_id": "UPPER", "keyword": "x"}],
        [{"profile_id": "bad profile", "keyword": "x"}],
        [{"profile_id": "x" * 65, "keyword": "x"}],
        [{"profile_id": "empty"}],
        [{"profile_id": "false-only", "remote_only": False}],
        [{"profile_id": "unknown", "keyword": "x", "page": 99}],
        [{"profile_id": "bad-code", "job_category_codes": ["221"]}],
        [{"profile_id": "bad-list", "organization_codes": "TR"}],
    ],
)
def test_invalid_profiles_reject_safely_without_request(tmp_path, monkeypatch, profiles):
    path = tmp_path / "profiles.json"
    path.write_text(json.dumps(profiles), encoding="utf-8")
    monkeypatch.setattr(usajobs_scraper, "USAJOBS_QUERY_PROFILES_PATH", str(path))
    monkeypatch.setattr(
        usajobs_scraper,
        "_request_page",
        lambda *args, **kwargs: pytest.fail("HTTP must not run"),
    )
    assert usajobs_scraper.scrape_all_usajobs() == []


def test_profile_parameter_mapping_is_exact_and_bounded():
    profile = _profile(
        keyword="software",
        location_name="Boston, Massachusetts",
        organization_codes=("AF", "TR"),
        job_category_codes=("1550", "2210"),
        remote_only=True,
    )
    assert usajobs_scraper._profile_params(profile, 2) == {
        "WhoMayApply": "Public",
        "Fields": "Full",
        "DatePosted": 1,
        "ResultsPerPage": 50,
        "Page": 2,
        "Keyword": "software",
        "LocationName": "Boston, Massachusetts",
        "Organization": "AF;TR",
        "JobCategoryCode": "1550;2210",
        "RemoteIndicator": "True",
    }


def test_request_uses_official_get_headers_timeout_and_no_redirects(monkeypatch):
    captured = {}

    def get(url, **kwargs):
        captured.update(url=url, kwargs=kwargs)
        return _Response(_payload([]))

    monkeypatch.setattr(usajobs_scraper, "http_get", get)
    usajobs_scraper._request_page(
        _profile(),
        1,
        "dummy-test-key",
        "owner@example.test",
    )
    assert captured["url"] == "https://data.usajobs.gov/api/search"
    assert captured["kwargs"]["headers"] == {
        "Host": "data.usajobs.gov",
        "User-Agent": "owner@example.test",
        "Authorization-Key": "dummy-test-key",
    }
    assert captured["kwargs"]["timeout"] == 10
    assert captured["kwargs"]["allow_redirects"] is False
    assert captured["kwargs"]["params"]["Page"] == 1


@pytest.mark.parametrize(
    ("status", "expected_calls"),
    [(429, 2), (500, 2), (502, 2), (503, 2), (504, 2), (400, 1), (401, 1), (403, 1), (404, 1), (422, 1)],
)
def test_shared_get_retry_contract(monkeypatch, status, expected_calls):
    calls = []
    monkeypatch.setattr(http_retry.time, "sleep", lambda _delay: None)
    monkeypatch.setattr(
        http_retry.requests,
        "get",
        lambda *args, **kwargs: calls.append((args, kwargs)) or _Response(status_code=status),
    )
    response = usajobs_scraper._request_page(
        _profile(), 1, "dummy-test-key", "owner@example.test"
    )
    assert response.status_code == status
    assert len(calls) == expected_calls


@pytest.mark.parametrize(
    "response",
    [
        _Response(raw=b"<html></html>", content_type="text/html"),
        _Response(raw=b"<jobs />", content_type="application/xml"),
        _Response(raw=b"{", content_type="application/json"),
        _Response([], content_type="application/json"),
        _Response({"SearchResult": {}}),
        _Response(
            {
                "SearchResult": {
                    "SearchResultCount": 0,
                    "SearchResultCountAll": 0,
                    "SearchResultItems": {},
                    "UserArea": {"NumberOfPages": 0},
                }
            }
        ),
        _Response(_payload([], pages=201, total=0)),
    ],
)
def test_malformed_content_and_schema_fail_safely(monkeypatch, response):
    _set_page_responses(monkeypatch, response)
    outcome = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert outcome.status is AcquisitionStatus.FAILED
    assert outcome.reason == "malformed_payload"
    assert outcome.jobs == ()


def test_response_byte_bound_is_enforced(monkeypatch):
    response = _Response(
        raw=b" " * (usajobs_scraper.USAJOBS_MAX_RESPONSE_BYTES + 1),
        content_type="application/json",
    )
    _set_page_responses(monkeypatch, response)
    outcome = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert outcome.reason == "malformed_payload"


def test_success_normalizes_documented_vacancy_without_application_data(monkeypatch):
    _set_page_responses(monkeypatch, _Response(_payload([_item()])))
    outcome = usajobs_scraper._fetch_profile_outcome(
        _profile(remote_only=True), "dummy-test-key", "owner@example.test"
    )
    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.company == "usajobs:engineering"
    assert outcome.page_count == 1
    assert outcome.raw_job_count == 1
    job = outcome.jobs[0]
    assert job == {
        "company": "Agency",
        "title": "Software Engineer",
        "location": ["Washington, District of Columbia", "New York, New York"],
        "url": "https://www.usajobs.gov/GetJob/ViewDetails/123",
        "source": "usajobs",
        "posted_at": "2026-08-01T12:00:00Z",
        "job_id": "usajobs_123",
        "description": (
            "Summary\nBuild public systems.\n\n"
            "Duties\nDesign APIs\n\n"
            "Qualifications\nQualified candidates build systems.\n\n"
            "Education\nDegree or experience.\n\n"
            "Requirements\nPublic trust.\n\n"
            "Evaluations\nExperience is evaluated.\n\n"
            "Other job information\nRead more at"
        ),
        "description_text": (
            "Summary\nBuild public systems.\n\n"
            "Duties\nDesign APIs\n\n"
            "Qualifications\nQualified candidates build systems.\n\n"
            "Education\nDegree or experience.\n\n"
            "Requirements\nPublic trust.\n\n"
            "Evaluations\nExperience is evaluated.\n\n"
            "Other job information\nRead more at"
        ),
        "agency": "Agency",
        "department": "Department",
        "subagency": "Subagency",
        "announcement_number": "ABC-2026-001",
        "publication_date": "2026-08-01T12:00:00Z",
        "opening_date": "2026-08-01T00:00:00Z",
        "closing_date": "2026-08-08T23:59:59Z",
        "application_close_date": "2026-08-08T23:59:59Z",
        "occupational_categories": [
            {"name": "Information Technology Management", "code": "2210"}
        ],
        "grades": [{"code": "GS"}],
        "position_schedules": [{"name": "Full-time", "code": "1"}],
        "offering_types": [{"name": "Permanent", "code": "15317"}],
        "public_eligibility": {"name": "The public", "code": "public"},
        "salary_minimum": "120000",
        "salary_maximum": "150000.5",
        "salary_rate_interval": "Per Year",
        "remote": True,
    }
    assert job["description_text"] == job["description"]
    assert _contains_prohibited_application_data(job) is False
    assert "telework" not in repr(job).lower()


def test_description_text_is_the_same_sanitized_bounded_provider_text():
    item = _item()
    details = item["MatchedObjectDescriptor"]["UserArea"]["Details"]
    details["JobSummary"] = (
        "<p>" + ("Build secure public systems. " * 10_000) + "</p>"
        "<form>Upload a resume at https://apply.example.test</form>"
    )
    job = usajobs_scraper._normalize_result(item, remote_only=False)
    assert job is not None
    assert job["description_text"] == job["description"]
    assert len(job["description_text"]) <= consts.USAJOBS_MAX_DESCRIPTION_CHARS
    assert _contains_prohibited_application_data(job["description_text"]) is False


def test_empty_sanitized_description_does_not_invent_compatibility_content():
    item = _item()
    descriptor = item["MatchedObjectDescriptor"]
    descriptor["QualificationSummary"] = ""
    details = descriptor["UserArea"]["Details"]
    for key in (
        "JobSummary",
        "MajorDuties",
        "Education",
        "Requirements",
        "Evaluations",
        "OtherInformation",
    ):
        details[key] = ""
    job = usajobs_scraper._normalize_result(item, remote_only=False)
    assert job is not None
    assert "description" not in job
    assert "description_text" not in job


def test_location_fallback_remote_and_invalid_optional_values(monkeypatch):
    item = _item()
    descriptor = item["MatchedObjectDescriptor"]
    descriptor["PositionLocation"] = [{"LocationName": ""}, "invalid"]
    descriptor["PositionRemuneration"] = [
        {"MinimumRange": "NaN", "MaximumRange": "not-money", "RateIntervalCode": ""}
    ]
    descriptor["PublicationStartDate"] = "invalid"
    descriptor["PositionStartDate"] = "invalid"
    _set_page_responses(monkeypatch, _Response(_payload([item])))
    outcome = usajobs_scraper._fetch_profile_outcome(
        _profile(remote_only=False), "dummy-test-key", "owner@example.test"
    )
    job = outcome.jobs[0]
    assert outcome.status is AcquisitionStatus.SUCCESS
    assert job["location"] == ["Washington, District of Columbia"]
    assert job["posted_at"] is None
    assert "salary_minimum" not in job
    assert "salary_maximum" not in job
    assert "remote" not in job
    assert "telework" not in job


@pytest.mark.parametrize(
    "url",
    [
        "https://www.usajobs.gov/GetJob/ViewDetails/123",
        "https://www.usajobs.gov:443/GetJob/ViewDetails/123",
        "https://usajobs.gov:443/GetJob/ViewDetails/123",
        "https://WWW.USAJOBS.GOV:443/GetJob/ViewDetails/123",
    ],
)
def test_canonical_url_accepts_exact_public_https_authorities(url):
    assert usajobs_scraper._canonical_url(url, "123") == url


def test_provider_shaped_explicit_https_port_item_normalizes():
    url = "https://www.usajobs.gov:443/GetJob/ViewDetails/123"
    job = usajobs_scraper._normalize_result(_item(url=url), remote_only=False)
    assert job is not None
    assert job["url"] == url
    assert job["job_id"] == "usajobs_123"


@pytest.mark.parametrize(
    "url",
    [
        "https://www.usajobs.gov:80/GetJob/ViewDetails/123",
        "https://www.usajobs.gov:444/GetJob/ViewDetails/123",
        "https://www.usajobs.gov:0443/GetJob/ViewDetails/123",
        "https://www.usajobs.gov:+443/GetJob/ViewDetails/123",
        "https://www.usajobs.gov:-443/GetJob/ViewDetails/123",
        "https://www.usajobs.gov:443%20/GetJob/ViewDetails/123",
        "https://www.usajobs.gov:443 /GetJob/ViewDetails/123",
    ],
)
def test_canonical_url_rejects_nondefault_or_ambiguous_ports(url):
    assert usajobs_scraper._canonical_url(url, "123") == ""


@pytest.mark.parametrize(
    "url",
    [
        "https://user@www.usajobs.gov:443/GetJob/ViewDetails/123",
        "https://evil.example:443/GetJob/ViewDetails/123",
        "http://www.usajobs.gov:443/GetJob/ViewDetails/123",
        "https://www.usajobs.gov:443",
        "https://www.usajobs.gov:443/Apply/123",
    ],
)
def test_explicit_https_port_does_not_weaken_authority_protections(url):
    assert usajobs_scraper._canonical_url(url, "123") == ""


@pytest.mark.parametrize(
    "url",
    [
        "https://www.usajobs.gov:443/GetJob/ViewDetails/123?source=test",
        "https://www.usajobs.gov:443/GetJob/ViewDetails/123#details",
    ],
)
def test_explicit_https_port_preserves_query_and_fragment_protections(url):
    assert usajobs_scraper._canonical_url(url, "123") == ""


def test_explicit_https_port_preserves_exact_control_number_path_segment():
    url = "https://www.usajobs.gov:443/GetJob/ViewDetails/1234"
    assert usajobs_scraper._canonical_url(url, "123") == ""


@pytest.mark.parametrize(
    "item",
    [
        _item(control_number=""),
        _item(title=""),
        _item(company=""),
        _item(url="http://www.usajobs.gov/GetJob/ViewDetails/123"),
        _item(url="https://evil.example/GetJob/ViewDetails/123"),
        _item(url="https://user@www.usajobs.gov/GetJob/ViewDetails/123"),
        _item(url="https://www.usajobs.gov:bad/GetJob/ViewDetails/123"),
        _item(url="https://www.usajobs.gov/Apply/123"),
        _item(url="https://www.usajobs.gov/GetJob/ViewDetails/999"),
    ],
)
def test_missing_identity_or_unsafe_canonical_url_marks_row_malformed(monkeypatch, item):
    _set_page_responses(monkeypatch, _Response(_payload([item])))
    outcome = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert outcome.status is AcquisitionStatus.FAILED
    assert outcome.reason == "parse_error"
    assert outcome.raw_job_count == 1


def test_empty_mixed_and_all_malformed_outcomes(monkeypatch):
    _set_page_responses(monkeypatch, _Response(_payload([])))
    empty = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert (empty.status, empty.page_count, empty.raw_job_count) == (
        AcquisitionStatus.EMPTY,
        1,
        0,
    )

    malformed = _item(title="")
    _set_page_responses(monkeypatch, _Response(_payload([_item(), malformed])))
    partial = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert partial.status is AcquisitionStatus.PARTIAL
    assert partial.reason == "parse_error"
    assert len(partial.jobs) == 1
    assert partial.raw_job_count == 2

    _set_page_responses(monkeypatch, _Response(_payload([malformed])))
    failed = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert failed.status is AcquisitionStatus.FAILED
    assert failed.reason == "parse_error"


def test_first_page_transport_and_non_200_outcomes_are_sanitized(monkeypatch):
    monkeypatch.setattr(
        usajobs_scraper,
        "_request_page",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("dummy-test-key")),
    )
    transport = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert transport.status is AcquisitionStatus.FAILED
    assert transport.reason == "transport_error"
    assert "dummy-test-key" not in repr(transport)

    _set_page_responses(monkeypatch, _Response(status_code=401))
    unauthorized = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert unauthorized.status is AcquisitionStatus.FAILED
    assert unauthorized.reason == "non_200_response"


@pytest.mark.parametrize("second", [_Response(status_code=503), RuntimeError("secret")])
def test_later_page_failure_retains_first_page_jobs(monkeypatch, second):
    first_items = [_item(str(index)) for index in range(1, 51)]
    first = _Response(_payload(first_items, pages=2, total=51))
    if isinstance(second, Exception):
        calls = iter([first, second])

        def request(*_args, **_kwargs):
            value = next(calls)
            if isinstance(value, Exception):
                raise value
            return value

        monkeypatch.setattr(usajobs_scraper, "_request_page", request)
    else:
        _set_page_responses(monkeypatch, first, second)
    outcome = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "pagination_interrupted"
    assert outcome.page_count == 1
    assert outcome.raw_job_count == 50
    assert len(outcome.jobs) == 50


def test_later_page_malformed_payload_retains_first_page_jobs(monkeypatch):
    first_items = _full_page_items(1)
    _set_page_responses(
        monkeypatch,
        _Response(_payload(first_items, pages=2, total=100)),
        _Response(raw=b"{", content_type="application/json"),
    )
    outcome = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "pagination_interrupted"
    assert outcome.page_count == 1
    assert outcome.raw_job_count == 50
    assert len(outcome.jobs) == 50


def test_single_advertised_page_causes_one_request(monkeypatch):
    requested_pages = []

    def request(_profile_value, page, *_args):
        requested_pages.append(page)
        return _Response(_payload([_item()], pages=1, total=1))

    monkeypatch.setattr(usajobs_scraper, "_request_page", request)
    outcome = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert requested_pages == [1]
    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.page_count == 1
    assert outcome.raw_job_count == 1


def test_four_advertised_pages_are_requested_sequentially(monkeypatch):
    requested_pages = []

    def request(_profile_value, page, *_args):
        requested_pages.append(page)
        return _Response(
            _payload(_full_page_items(page), pages=4, total=200)
        )

    monkeypatch.setattr(usajobs_scraper, "_request_page", request)
    outcome = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert requested_pages == [1, 2, 3, 4]
    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.page_count == 4
    assert outcome.raw_job_count == 200
    assert len(outcome.jobs) == 200
    assert {job["job_id"] for job in outcome.jobs} == {
        f"usajobs_{control_number}" for control_number in range(1, 201)
    }


def test_twenty_advertised_pages_are_completely_collected(monkeypatch):
    requested_pages = []

    def request(_profile_value, page, *_args):
        requested_pages.append(page)
        return _Response(
            _payload(_full_page_items(page), pages=20, total=1_000)
        )

    monkeypatch.setattr(usajobs_scraper, "_request_page", request)
    outcome = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert requested_pages == list(range(1, 21))
    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.page_count == 20
    assert outcome.raw_job_count == 1_000
    assert len(outcome.jobs) == 1_000
    assert outcome.jobs[0]["job_id"] == "usajobs_1"
    assert outcome.jobs[-1]["job_id"] == "usajobs_1000"


def test_empty_page_stops_pagination_and_retains_prior_jobs(monkeypatch):
    requested_pages = []

    def request(_profile_value, page, *_args):
        requested_pages.append(page)
        if page == 1:
            return _Response(
                _payload(_full_page_items(1), pages=4, total=200)
            )
        return _Response(_payload([], pages=0, total=0))

    monkeypatch.setattr(usajobs_scraper, "_request_page", request)
    outcome = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert requested_pages == [1, 2]
    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.page_count == 2
    assert outcome.raw_job_count == 50
    assert len(outcome.jobs) == 50


def test_intentional_page_cap_is_success_and_logs_only_bounded_marker(monkeypatch, capsys):
    requested_pages = []

    def request(_profile_value, page, *_args):
        requested_pages.append(page)
        return _Response(
            _payload(_full_page_items(page), pages=21, total=1_050)
        )

    monkeypatch.setattr(usajobs_scraper, "_request_page", request)
    outcome = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    logged = capsys.readouterr().out
    assert requested_pages == list(range(1, 21))
    assert 21 not in requested_pages
    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.page_count == 20
    assert outcome.raw_job_count == 1_000
    assert len(outcome.jobs) == 1_000
    assert "bounded_page_cap_reached=true" in logged
    assert "dummy-test-key" not in logged
    assert "engineer" not in logged


def test_profiles_execute_sequentially_in_sorted_order_and_metrics_are_secret_free(monkeypatch):
    profiles = [_profile("alpha"), _profile("zeta")]
    monkeypatch.setattr(usajobs_scraper, "_load_query_profiles", lambda: profiles)
    monkeypatch.setenv("USAJOBS_API_KEY", "dummy-test-key")
    monkeypatch.setenv("USAJOBS_USER_AGENT_EMAIL", "owner@example.test")
    order = []

    def outcome(profile, api_key, email):
        order.append(profile["profile_id"])
        assert api_key == "dummy-test-key"
        assert email == "owner@example.test"
        return usajobs_scraper.AcquisitionOutcome(
            f"usajobs:{profile['profile_id']}",
            AcquisitionStatus.SUCCESS,
            ({"source": "usajobs", "job_id": profile["profile_id"]},),
            page_count=1,
            raw_job_count=1,
        )

    monkeypatch.setattr(usajobs_scraper, "_fetch_profile_outcome", outcome)
    jobs = usajobs_scraper.scrape_all_usajobs()
    metrics = pipeline_metrics.acquisition_metrics_snapshot()
    assert order == ["alpha", "zeta"]
    assert [job["job_id"] for job in jobs] == ["alpha", "zeta"]
    assert [(metric.source, metric.company) for metric in metrics] == [
        ("usajobs", "usajobs:alpha"),
        ("usajobs", "usajobs:zeta"),
    ]
    assert all(metric.schedule_advanced is False for metric in metrics)
    serialized = repr((jobs, metrics))
    assert "dummy-test-key" not in serialized
    assert "owner@example.test" not in serialized


def test_adapter_retains_structurally_trustworthy_irrelevant_old_foreign_job(monkeypatch):
    item = _item(title="Chief Poetry Officer")
    descriptor = item["MatchedObjectDescriptor"]
    descriptor["PositionLocation"] = [{"LocationName": "London, United Kingdom"}]
    descriptor["PublicationStartDate"] = "2000-01-01T00:00:00Z"
    _set_page_responses(monkeypatch, _Response(_payload([item])))
    outcome = usajobs_scraper._fetch_profile_outcome(
        _profile(), "dummy-test-key", "owner@example.test"
    )
    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.jobs[0]["title"] == "Chief Poetry Officer"
    assert outcome.jobs[0]["location"] == ["London, United Kingdom"]
    assert outcome.jobs[0]["posted_at"] == "2000-01-01T00:00:00Z"


def test_acquisition_owner_has_no_central_relevance_predicates():
    source = inspect.getsource(usajobs_scraper._fetch_profile_outcome)
    for marker in (
        "title_matches",
        "us_location",
        "selected_seniority",
        "strict_seniority",
        "preferred_locations",
        "excluded_keywords",
        "llm",
    ):
        assert marker not in source.lower()


def test_bounds_limit_theoretical_rows_to_1000_per_profile_and_4000_total():
    assert consts.USAJOBS_MAX_QUERY_PROFILES == 4
    assert consts.USAJOBS_MAX_PAGES_PER_PROFILE == 20
    assert consts.USAJOBS_RESULTS_PER_PAGE == 50
    assert (
        consts.USAJOBS_MAX_PAGES_PER_PROFILE
        * consts.USAJOBS_RESULTS_PER_PAGE
        == 1_000
    )
    assert (
        consts.USAJOBS_MAX_QUERY_PROFILES
        * consts.USAJOBS_MAX_PAGES_PER_PROFILE
        * consts.USAJOBS_RESULTS_PER_PAGE
        == 4_000
    )


def test_collector_registers_usajobs_once_after_existing_sources_before_filter_and_dedupe():
    source = inspect.getsource(collector.collect_all_jobs_async)
    assert source.count('("usajobs", scrape_all_usajobs)') == 1
    usajobs_position = source.index('("usajobs", scrape_all_usajobs)')
    builtin_position = source.index('("builtin", scrape_all_builtin)')
    filter_position = source.index("filter_jobs(", usajobs_position)
    dedupe_position = source.index("dedupe_jobs(", filter_position)
    assert builtin_position < usajobs_position < filter_position < dedupe_position
    assert "all_jobs.extend(jobs)" in source[usajobs_position:filter_position]
    assert "selected_role_families=selected_role_families or None" in source[
        filter_position:dedupe_position
    ]


def test_usajobs_description_survives_common_detail_stage_without_secondary_request(monkeypatch):
    job = {
        "source": "usajobs",
        "job_id": "usajobs_123",
        "description": "Sanitized provider description.",
        "description_text": "Sanitized provider description.",
    }
    monkeypatch.setattr(job_details, "init_cache", lambda: None)
    for owner in (
        "fetch_ashby_details",
        "fetch_builtin_details",
        "fetch_greenhouse_details",
        "fetch_jobvite_details",
        "fetch_lever_details",
        "fetch_smartrecruiters_details",
        "fetch_workable_details",
        "fetch_workday_details",
    ):
        monkeypatch.setattr(
            job_details,
            owner,
            lambda *_args, _owner=owner, **_kwargs: pytest.fail(
                f"{_owner} must not run for USAJobs"
            ),
        )

    assert "usajobs" not in job_details.ENRICHABLE_SOURCES
    assert job_details.enrich_job_details([job]) == [
        {**job, "_details_fetched": "skipped"}
    ]


def test_usajobs_module_has_no_schedule_persistence_or_application_authority():
    source = Path(usajobs_scraper.__file__).read_text(encoding="utf-8").lower()
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
        assert marker not in source
