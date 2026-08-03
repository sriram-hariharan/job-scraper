from collections import Counter
import inspect

import pytest
import requests

from src.discovery.crawl_scheduler import AcquisitionOutcome, AcquisitionStatus
from src.pipeline import collector
from src.scrapers import personio_scraper
from src.utils import http_retry, pipeline_metrics


class _Response:
    def __init__(
        self,
        content=b"<workzag-jobs />",
        *,
        status_code=200,
        content_type="text/xml; charset=utf-8",
    ):
        self.content = content
        self.status_code = status_code
        self.headers = {"Content-Type": content_type}


@pytest.fixture(autouse=True)
def _reset_metrics():
    pipeline_metrics.reset_acquisition_metrics()
    yield
    pipeline_metrics.reset_acquisition_metrics()


def _position(position_id="123", title="Software Engineer", extra=""):
    return f"""
    <position>
      <id>{position_id}</id>
      <subcompany>Acme GmbH</subcompany>
      <office>Berlin</office>
      <additionalOffices><office>Munich</office><office>Berlin</office></additionalOffices>
      <department>Engineering</department>
      <recruitingCategory>Technology</recruitingCategory>
      <name>{title}</name>
      <jobDescriptions>
        <jobDescription>
          <name>Responsibilities</name>
          <value><![CDATA[<p>Build <strong>safe APIs</strong>. https://acme.jobs.personio.de/job/123/apply</p><script>secret()</script><style>.x{{}}</style><form>Apply now<input value="secret"></form>]]></value>
        </jobDescription>
        <jobDescription><name>Profile</name><value><![CDATA[<ul><li>Careful</li><li>Kind</li></ul>]]></value></jobDescription>
      </jobDescriptions>
      <employmentType>permanent</employmentType>
      <seniority>experienced</seniority>
      <schedule>full-time</schedule>
      <yearsOfExperience>2-5</yearsOfExperience>
      <keywords>python, APIs</keywords>
      <occupation>software_engineering</occupation>
      <occupationCategory>technology</occupationCategory>
      <createdAt>2026-08-01T12:00:00+0200</createdAt>
      {extra}
    </position>
    """


def _feed(*positions, root="workzag-jobs"):
    return (f"<?xml version='1.0' encoding='UTF-8'?><{root}>" + "".join(positions) + f"</{root}>").encode()


def _set_response(monkeypatch, response):
    monkeypatch.setattr(personio_scraper, "_request_feed", lambda _host: response)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("acme.jobs.personio.de", "acme.jobs.personio.de"),
        ("Acme-Co.Jobs.Personio.Com", "acme-co.jobs.personio.com"),
        ("a.jobs.personio.de", "a.jobs.personio.de"),
        ("https://acme.jobs.personio.de", ""),
        ("acme.jobs.personio.de/xml", ""),
        ("acme.jobs.personio.de?language=en", ""),
        ("acme.jobs.personio.de:443", ""),
        ("user@acme.jobs.personio.de", ""),
        (" acme.jobs.personio.de", ""),
        ("acme jobs.personio.de", ""),
        ("-acme.jobs.personio.de", ""),
        ("acme-.jobs.personio.de", ""),
        (f"{'a' * 64}.jobs.personio.de", ""),
        ("jobs.personio.de", ""),
        ("localhost.jobs.personio.invalid", ""),
        ("127.0.0.1", ""),
        ("acme.personio.de", ""),
        ("jobs.personio.com", ""),
        ("careers.acme.com", ""),
    ],
)
def test_host_normalization_is_strict(value, expected):
    assert personio_scraper._normalize_host(value) == expected


def test_company_validation_canonicalizes_deduplicates_and_checks_xml(monkeypatch):
    calls = []
    monkeypatch.setattr(
        personio_scraper,
        "_request_feed",
        lambda host: calls.append(host) or _Response(),
    )

    valid = personio_scraper.validate_personio_companies(
        [
            "ACME.jobs.personio.de",
            "acme.jobs.personio.de",
            "beta.jobs.personio.com",
            "https://bad.jobs.personio.de",
        ]
    )

    assert valid == {"acme.jobs.personio.de", "beta.jobs.personio.com"}
    assert Counter(calls) == Counter(
        ["acme.jobs.personio.de", "acme.jobs.personio.de", "beta.jobs.personio.com"]
    )


@pytest.mark.parametrize(
    "response",
    [
        _Response(status_code=302),
        _Response(b"<html />", content_type="text/html"),
        _Response(b"{}", content_type="application/json"),
        _Response(_feed(root="jobs")),
        _Response(b"<workzag-jobs>"),
    ],
)
def test_company_validation_rejects_redirect_non_xml_and_malformed(monkeypatch, response):
    _set_response(monkeypatch, response)
    assert personio_scraper.validate_personio_company("acme.jobs.personio.de") is False


def test_request_uses_exact_public_feed_shared_get_timeout_and_no_redirects(monkeypatch):
    captured = {}

    def get(url, **kwargs):
        captured.update(url=url, kwargs=kwargs)
        return _Response()

    monkeypatch.setattr(personio_scraper, "http_get", get)
    personio_scraper._request_feed("acme.jobs.personio.com")

    assert captured == {
        "url": "https://acme.jobs.personio.com/xml?language=en",
        "kwargs": {
            "headers": {"User-Agent": "Mozilla/5.0"},
            "timeout": 10,
            "allow_redirects": False,
        },
    }


@pytest.mark.parametrize(
    ("status", "expected_calls"),
    [(429, 2), (500, 2), (502, 2), (503, 2), (504, 2), (400, 1), (401, 1), (403, 1), (404, 1), (422, 1)],
)
def test_shared_get_retry_contract_is_unchanged(monkeypatch, status, expected_calls):
    calls = []
    monkeypatch.setattr(http_retry.time, "sleep", lambda _delay: None)
    monkeypatch.setattr(
        http_retry.requests,
        "get",
        lambda *args, **kwargs: calls.append((args, kwargs)) or _Response(status_code=status),
    )

    response = personio_scraper._request_feed("acme.jobs.personio.de")

    assert response.status_code == status
    assert len(calls) == expected_calls


def test_success_normalizes_public_vacancy_without_application_data(monkeypatch):
    _set_response(monkeypatch, _Response(_feed(_position())))

    outcome = personio_scraper._fetch_company_outcome("ACME.jobs.personio.de")

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.company == "acme.jobs.personio.de"
    assert outcome.page_count == 1
    assert outcome.raw_job_count == 1
    assert list(outcome.jobs) == [
        {
            "company": "Acme GmbH",
            "title": "Software Engineer",
            "location": ["Berlin", "Munich"],
            "url": "https://acme.jobs.personio.de/job/123?language=en",
            "source": "personio",
            "posted_at": None,
            "job_id": "personio_acme.jobs.personio.de_123",
            "description": "Responsibilities\nBuild safe APIs.\n\nProfile\nCareful\nKind",
            "personio_created_at": "2026-08-01T12:00:00+0200",
            "department": "Engineering",
            "recruiting_category": "Technology",
            "employment_type": "permanent",
            "seniority": "experienced",
            "schedule": "full-time",
            "years_of_experience": "2-5",
            "keywords": "python, APIs",
            "occupation": "software_engineering",
            "occupation_category": "technology",
        }
    ]
    serialized = repr(outcome.jobs[0]).lower()
    for forbidden in ("application", "/apply", "apply now", "secret()", "<script", "<style", "<form", "<input"):
        assert forbidden not in serialized


def test_company_falls_back_and_invalid_optional_fields_do_not_crash(monkeypatch):
    position = """
    <position>
      <id>9</id><name>Engineer</name><createdAt>not-a-timestamp</createdAt>
      <jobDescriptions><jobDescription><name /><value><b>Text</b></value></jobDescription></jobDescriptions>
      <additionalOffices><office /><unknown /></additionalOffices>
    </position>
    """
    _set_response(monkeypatch, _Response(_feed(position)))

    outcome = personio_scraper._fetch_company_outcome("acme.jobs.personio.com")

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.jobs[0]["company"] == "acme.jobs.personio.com"
    assert outcome.jobs[0]["location"] == []
    assert outcome.jobs[0]["posted_at"] is None
    assert "personio_created_at" not in outcome.jobs[0]


def test_description_output_is_bounded(monkeypatch):
    long_text = "x" * (personio_scraper.PERSONIO_MAX_DESCRIPTION_CHARS + 100)
    position = f"<position><id>1</id><name>Engineer</name><jobDescriptions><jobDescription><value>{long_text}</value></jobDescription></jobDescriptions></position>"
    _set_response(monkeypatch, _Response(_feed(position)))

    outcome = personio_scraper._fetch_company_outcome("acme.jobs.personio.de")

    assert len(outcome.jobs[0]["description"]) == personio_scraper.PERSONIO_MAX_DESCRIPTION_CHARS


@pytest.mark.parametrize(
    "content",
    [
        b"<html />",
        b"{}",
        _feed(root="jobs"),
        b"<workzag-jobs>",
        b"<!DOCTYPE workzag-jobs><workzag-jobs />",
        b"<!entity secret 'value'><workzag-jobs />",
    ],
)
def test_malformed_payloads_are_failed(monkeypatch, content):
    content_type = "text/xml" if not content.startswith(b"{") else "application/json"
    _set_response(monkeypatch, _Response(content, content_type=content_type))

    outcome = personio_scraper._fetch_company_outcome("acme.jobs.personio.de")

    assert outcome.status is AcquisitionStatus.FAILED
    assert outcome.reason == "malformed_payload"
    assert outcome.jobs == ()


def test_xml_byte_and_position_count_bounds(monkeypatch):
    oversized = b"<workzag-jobs>" + b" " * personio_scraper.PERSONIO_MAX_XML_BYTES + b"</workzag-jobs>"
    _set_response(monkeypatch, _Response(oversized))
    assert personio_scraper._fetch_company_outcome("acme.jobs.personio.de").reason == "malformed_payload"

    positions = "<position><id>1</id><name>Engineer</name></position>" * (personio_scraper.PERSONIO_MAX_POSITIONS + 1)
    _set_response(monkeypatch, _Response(_feed(positions)))
    assert personio_scraper._fetch_company_outcome("acme.jobs.personio.de").reason == "malformed_payload"


def test_empty_mixed_and_all_malformed_outcomes(monkeypatch):
    _set_response(monkeypatch, _Response(_feed()))
    empty = personio_scraper._fetch_company_outcome("acme.jobs.personio.de")
    assert (empty.status, empty.jobs, empty.page_count, empty.raw_job_count) == (
        AcquisitionStatus.EMPTY,
        (),
        1,
        0,
    )

    malformed = "<position><id>bad</id><name>Bad</name></position><position><id>2</id></position>"
    _set_response(monkeypatch, _Response(_feed(_position(), malformed)))
    partial = personio_scraper._fetch_company_outcome("acme.jobs.personio.de")
    assert partial.status is AcquisitionStatus.PARTIAL
    assert partial.reason == "parse_error"
    assert len(partial.jobs) == 1
    assert partial.raw_job_count == 3
    assert partial.should_mark_scraped is False

    _set_response(monkeypatch, _Response(_feed(malformed)))
    failed = personio_scraper._fetch_company_outcome("acme.jobs.personio.de")
    assert failed.status is AcquisitionStatus.FAILED
    assert failed.reason == "parse_error"
    assert failed.jobs == ()
    assert failed.page_count == 1
    assert failed.raw_job_count == 2


def test_transport_redirect_and_non_200_outcomes(monkeypatch):
    monkeypatch.setattr(
        personio_scraper,
        "_request_feed",
        lambda _host: (_ for _ in ()).throw(requests.Timeout("fixture secret")),
    )
    transport = personio_scraper._fetch_company_outcome("acme.jobs.personio.de")
    assert transport.status is AcquisitionStatus.FAILED
    assert transport.reason == "transport_error"
    assert "fixture secret" not in repr(transport)

    for status_code in (301, 302, 307, 308, 404, 500):
        _set_response(monkeypatch, _Response(status_code=status_code))
        outcome = personio_scraper._fetch_company_outcome("acme.jobs.personio.de")
        assert outcome.status is AcquisitionStatus.FAILED
        assert outcome.reason == "non_200_response"
        assert outcome.jobs == ()


def test_adapter_does_not_prefilter_trustworthy_jobs(monkeypatch):
    old_irrelevant_foreign_role = _position(
        "77",
        "Chief Poetry Officer",
        extra="<createdAt>2000-01-01T00:00:00Z</createdAt><seniority>executive</seniority>",
    ).replace("<office>Berlin</office>", "<office>London, UK</office>")
    _set_response(monkeypatch, _Response(_feed(old_irrelevant_foreign_role)))

    outcome = personio_scraper._fetch_company_outcome("acme.jobs.personio.de")

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert [job["title"] for job in outcome.jobs] == ["Chief Poetry Officer"]
    assert outcome.jobs[0]["location"][0] == "London, UK"
    assert outcome.jobs[0]["posted_at"] is None


def test_empty_config_exits_before_schedule_workers_http_and_metrics(monkeypatch):
    monkeypatch.setattr(personio_scraper, "load_lines", lambda path: [])
    for owner in ("load_schedule", "run_parallel", "_request_feed", "observe_acquisition"):
        monkeypatch.setattr(
            personio_scraper,
            owner,
            lambda *args, _owner=owner, **kwargs: pytest.fail(f"{_owner} must not run"),
        )

    assert personio_scraper.scrape_all_personio() == []
    assert pipeline_metrics.acquisition_metrics_snapshot() == ()


def test_schedule_advances_only_success_and_empty_and_keeps_partial_jobs(monkeypatch):
    hosts = [f"{name}.jobs.personio.de" for name in ("success", "empty", "partial", "failed")]
    schedule = {}
    marked = []
    saved = []

    outcomes = {
        hosts[0]: AcquisitionOutcome(hosts[0], AcquisitionStatus.SUCCESS, ({"job_id": "success"},)),
        hosts[1]: AcquisitionOutcome(hosts[1], AcquisitionStatus.EMPTY),
        hosts[2]: AcquisitionOutcome(hosts[2], AcquisitionStatus.PARTIAL, ({"job_id": "partial"},), reason="parse_error"),
        hosts[3]: AcquisitionOutcome(hosts[3], AcquisitionStatus.FAILED, reason="transport_error"),
    }
    monkeypatch.setattr(personio_scraper, "load_lines", lambda path: list(reversed(hosts)))
    monkeypatch.setattr(personio_scraper, "load_schedule", lambda: schedule)
    monkeypatch.setattr(personio_scraper, "should_scrape", lambda host, value: True)
    monkeypatch.setattr(personio_scraper, "_fetch_company_result", lambda host: [outcomes[host]])
    monkeypatch.setattr(
        personio_scraper,
        "run_parallel",
        lambda items, worker, max_workers, desc: [worker(item)[0] for item in items],
    )
    monkeypatch.setattr(personio_scraper, "mark_scraped", lambda host, value: marked.append(host))
    monkeypatch.setattr(personio_scraper, "save_schedule", lambda value: saved.append(value))

    jobs = personio_scraper.scrape_all_personio()

    assert jobs == [{"job_id": "partial"}, {"job_id": "success"}]
    assert marked == [hosts[1], hosts[0]]
    assert saved == [schedule]


def test_observation_uses_existing_http_and_source_health_metrics(monkeypatch):
    _set_response(monkeypatch, _Response(_feed(_position())))

    observed = personio_scraper._fetch_company_result("acme.jobs.personio.de")
    metrics = pipeline_metrics.acquisition_metrics_snapshot()

    assert observed[0].status is AcquisitionStatus.SUCCESS
    assert len(metrics) == 1
    assert metrics[0].source == "personio"
    assert metrics[0].company == "acme.jobs.personio.de"
    assert metrics[0].normalized_job_count == 1
    assert metrics[0].schedule_advanced is True


def test_collector_registers_personio_once_before_central_filter_and_dedupe():
    source = inspect.getsource(collector.collect_all_jobs_async)

    assert source.count('(\"personio\", scrape_all_personio)') == 1
    registry_position = source.index('(\"personio\", scrape_all_personio)')
    filter_position = source.index("filter_jobs(", registry_position)
    dedupe_position = source.index("dedupe_jobs(", filter_position)
    assert registry_position < filter_position < dedupe_position
