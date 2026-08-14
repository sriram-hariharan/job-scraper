import inspect
import json
from collections import Counter

import pytest
import requests

from src.discovery.crawl_scheduler import AcquisitionOutcome, AcquisitionStatus
from src.pipeline.job_filter import us_location
from src.scrapers import recruitee_scraper
from src.utils import http_retry, pipeline_metrics


class _Response:
    def __init__(self, payload=None, status_code=200, json_error=False):
        self.status_code = status_code
        self.headers = {}
        self._payload = payload
        self._json_error = json_error

    def json(self):
        if self._json_error:
            raise ValueError("fixture malformed JSON")
        return self._payload


@pytest.fixture(autouse=True)
def _reset_metrics():
    pipeline_metrics.reset_acquisition_metrics()
    yield
    pipeline_metrics.reset_acquisition_metrics()


def _offer(suffix="1", **overrides):
    offer = {
        "id": suffix,
        "title": "Software Engineer",
        "careers_url": f"https://acme.recruitee.com/o/software-engineer-{suffix}",
        "careers_apply_url": f"https://acme.recruitee.com/o/software-engineer-{suffix}/c/new",
        "published_at": "2026-08-03T00:00:00Z",
        "location": "New York, NY, United States",
        "description": "Public role description",
        "requirements": "Public role requirements",
    }
    offer.update(overrides)
    return offer


def _outcome(monkeypatch, offers):
    monkeypatch.setattr(
        recruitee_scraper,
        "_request_offers",
        lambda tenant: _Response({"offers": offers}),
    )
    return recruitee_scraper._fetch_company_outcome("acme")


def _location_is_us(location):
    locations = location if isinstance(location, list) else [location]
    return any(us_location(value, "recruitee") for value in locations)


def test_valid_success_uses_stable_id_canonical_url_and_public_fields(monkeypatch):
    payload = {"offers": [_offer()]}
    monkeypatch.setattr(
        recruitee_scraper,
        "_request_offers",
        lambda tenant: _Response(payload),
    )

    outcome = recruitee_scraper._fetch_company_outcome("Acme")

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.company == "acme"
    assert outcome.page_count == 1
    assert outcome.raw_job_count == 1
    assert list(outcome.jobs) == [
        {
            "company": "acme",
            "title": "Software Engineer",
            "location": "New York, NY, United States",
            "url": "https://acme.recruitee.com/o/software-engineer-1",
            "source": "recruitee",
            "posted_at": "2026-08-03T00:00:00Z",
            "job_id": "rq_acme_1",
            "description": "Public role description",
            "requirements": "Public role requirements",
        }
    ]
    assert "careers_apply_url" not in outcome.jobs[0]


def test_unusable_secondary_locations_preserve_primary_string(monkeypatch):
    outcome = _outcome(
        monkeypatch,
        [
            _offer(
                locations={"city": "Boston", "country": "United States"},
            )
        ],
    )

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.jobs[0]["location"] == "New York, NY, United States"


def test_complete_secondary_us_location_is_retained_for_central_filter(monkeypatch):
    outcome = _outcome(
        monkeypatch,
        [
            _offer(
                location="Remote job",
                locations=[
                    {
                        "city": "Boston",
                        "state": "Massachusetts",
                        "state_code": "MA",
                        "country": "United States",
                        "country_code": "US",
                    }
                ],
            )
        ],
    )

    location = outcome.jobs[0]["location"]
    assert location == [
        "Remote job",
        "Boston, Massachusetts, United States",
    ]
    assert _location_is_us(location) is True


def test_us_country_code_fills_missing_country_name(monkeypatch):
    outcome = _outcome(
        monkeypatch,
        [
            _offer(
                location="",
                locations=[
                    {
                        "city": "Boston",
                        "state": "Massachusetts",
                        "country_code": "US",
                    }
                ],
            )
        ],
    )

    assert outcome.jobs[0]["location"] == "Boston, Massachusetts, United States"


@pytest.mark.parametrize(
    ("group", "expected"),
    [
        (
            {"city": "Berlin", "country": "Germany", "country_code": "DE"},
            "Berlin, Germany",
        ),
        (
            {
                "city": "Toronto",
                "state": "Ontario",
                "country": "Canada",
                "country_code": "CA",
            },
            "Toronto, Ontario, Canada",
        ),
        (
            {
                "city": "Bangalore",
                "state": "Karnataka",
                "country": "India",
                "country_code": "IN",
            },
            "Bangalore, Karnataka, India",
        ),
    ],
)
def test_foreign_country_codes_are_not_flattened_as_us_states(
    monkeypatch, group, expected
):
    outcome = _outcome(
        monkeypatch,
        [_offer(location="", locations=[group])],
    )

    location = outcome.jobs[0]["location"]
    assert location == expected
    assert _location_is_us(location) is False


def test_mixed_locations_remain_complete_and_recover_explicit_us(monkeypatch):
    outcome = _outcome(
        monkeypatch,
        [
            _offer(
                location="Remote job",
                locations=[
                    {
                        "city": "Boston",
                        "state": "Massachusetts",
                        "state_code": "MA",
                        "country": "United States",
                        "country_code": "US",
                    },
                    {
                        "city": "Berlin",
                        "country": "Germany",
                        "country_code": "DE",
                    },
                ],
            )
        ],
    )

    location = outcome.jobs[0]["location"]
    assert location == [
        "Remote job",
        "Boston, Massachusetts, United States",
        "Berlin, Germany",
    ]
    assert all(value not in location for value in ("MA", "US", "DE"))
    assert _location_is_us(location) is True
    assert _location_is_us("Berlin, Germany") is False


def test_location_deduplication_preserves_primary_and_api_order(monkeypatch):
    duplicate = {
        "name": "Remote - US",
        "city": "Remote",
        "state": "New York",
        "country": "United States",
        "country_code": "US",
    }
    outcome = _outcome(
        monkeypatch,
        [
            _offer(
                location="Remote - US, Remote, New York, United States",
                locations=[
                    duplicate,
                    dict(duplicate),
                    {
                        "name": "Boston",
                        "city": "Boston",
                        "state": "Massachusetts",
                        "country": "United States",
                    },
                ],
            )
        ],
    )

    assert outcome.jobs[0]["location"] == [
        "Remote - US, Remote, New York, United States",
        "Boston, Massachusetts, United States",
    ]


@pytest.mark.parametrize(
    "locations",
    [
        {"city": "Boston", "country": "United States"},
        [None, "invalid", 7, {}, {"city": "Berlin", "country_code": "DE"}],
    ],
)
def test_malformed_optional_locations_do_not_degrade_valid_offer(
    monkeypatch, locations
):
    outcome = _outcome(monkeypatch, [_offer(locations=locations)])

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.reason == ""
    assert outcome.raw_job_count == 1
    assert len(outcome.jobs) == 1
    assert outcome.jobs[0]["location"] == "New York, NY, United States"


def test_secondary_locations_preserve_authoritative_job_contract(monkeypatch):
    offer = _offer(
        location="Remote job",
        locations=[
            {
                "city": "Boston",
                "state": "Massachusetts",
                "country": "United States",
                "country_code": "US",
            }
        ],
    )
    outcome = _outcome(monkeypatch, [offer])
    job = outcome.jobs[0]

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.raw_job_count == 1
    assert len(outcome.jobs) == 1
    assert job["company"] == "acme"
    assert job["job_id"] == "rq_acme_1"
    assert job["url"] == offer["careers_url"]
    assert job["posted_at"] == offer["published_at"]
    assert job["description"] == offer["description"]
    assert job["requirements"] == offer["requirements"]


def test_valid_empty_board_is_empty(monkeypatch):
    monkeypatch.setattr(
        recruitee_scraper,
        "_request_offers",
        lambda tenant: _Response({"offers": []}),
    )

    outcome = recruitee_scraper._fetch_company_outcome("acme")

    assert outcome.status is AcquisitionStatus.EMPTY
    assert outcome.jobs == ()
    assert outcome.page_count == 1
    assert outcome.raw_job_count == 0


def test_populated_board_is_success_before_central_filter(monkeypatch):
    monkeypatch.setattr(
        recruitee_scraper,
        "_request_offers",
        lambda tenant: _Response(
            {
                "offers": [
                    _offer(
                        title="Backend Engineer",
                        location="London, UK",
                        published_at="2000-01-01T00:00:00Z",
                    )
                ]
            }
        ),
    )

    outcome = recruitee_scraper._fetch_company_outcome("acme")

    assert outcome.status is AcquisitionStatus.SUCCESS
    assert [job["title"] for job in outcome.jobs] == ["Backend Engineer"]
    assert outcome.raw_job_count == 1


@pytest.mark.parametrize(
    ("response", "expected_reason"),
    [
        (_Response(status_code=404), "non_200_response"),
        (_Response(json_error=True), "malformed_payload"),
        (_Response([]), "malformed_payload"),
        (_Response({}), "malformed_payload"),
        (_Response({"offers": {}}), "malformed_payload"),
    ],
)
def test_non_200_malformed_json_and_malformed_envelopes(
    monkeypatch, response, expected_reason
):
    monkeypatch.setattr(
        recruitee_scraper,
        "_request_offers",
        lambda tenant: response,
    )

    outcome = recruitee_scraper._fetch_company_outcome("acme")

    assert outcome.status is AcquisitionStatus.FAILED
    assert outcome.reason == expected_reason
    assert outcome.jobs == ()


def test_transport_failure_is_failed(monkeypatch):
    def fail(_tenant):
        raise requests.Timeout("fixture secret")

    monkeypatch.setattr(recruitee_scraper, "_request_offers", fail)

    outcome = recruitee_scraper._fetch_company_outcome("acme")

    assert outcome.status is AcquisitionStatus.FAILED
    assert outcome.reason == "transport_error"
    assert "fixture secret" not in repr(outcome)


def test_every_record_malformed_is_failed(monkeypatch):
    monkeypatch.setattr(
        recruitee_scraper,
        "_request_offers",
        lambda tenant: _Response(
            {"offers": [None, {"id": "1"}, {"title": "Engineer"}]}
        ),
    )

    outcome = recruitee_scraper._fetch_company_outcome("acme")

    assert outcome.status is AcquisitionStatus.FAILED
    assert outcome.reason == "parse_error"
    assert outcome.raw_job_count == 3


def test_mixed_valid_and_malformed_records_are_partial(monkeypatch):
    monkeypatch.setattr(
        recruitee_scraper,
        "_request_offers",
        lambda tenant: _Response({"offers": [_offer(), {"id": "broken"}]}),
    )

    outcome = recruitee_scraper._fetch_company_outcome("acme")

    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "parse_error"
    assert [job["job_id"] for job in outcome.jobs] == ["rq_acme_1"]
    assert outcome.raw_job_count == 2


def test_request_uses_existing_finite_timeout_and_get_owner(monkeypatch):
    captured = {}

    def get(url, **kwargs):
        captured.update(url=url, kwargs=kwargs)
        return _Response({"offers": []})

    monkeypatch.setattr(recruitee_scraper, "http_get", get)

    response = recruitee_scraper._request_offers("acme")

    assert response.status_code == 200
    assert captured["url"] == "https://acme.recruitee.com/api/offers/"
    assert captured["kwargs"]["timeout"] == 10
    assert captured["kwargs"]["headers"] == {"User-Agent": "Mozilla/5.0"}


@pytest.mark.parametrize(
    ("tenant", "valid"),
    [
        ("acme", True),
        ("Acme-Co", True),
        ("a", True),
        ("", False),
        ("-acme", False),
        ("acme-", False),
        ("acme.example", False),
        ("acme/path", False),
        ("a" * 64, False),
    ],
)
def test_tenant_validation_is_strict_and_normalized(monkeypatch, tenant, valid):
    calls = []
    monkeypatch.setattr(
        recruitee_scraper,
        "_request_offers",
        lambda company: calls.append(company) or _Response({"offers": []}),
    )

    assert recruitee_scraper.validate_recruitee_company(tenant) is valid
    assert calls == ([_normalize_expected(tenant)] if valid else [])


def _normalize_expected(value):
    return str(value).strip().lower()


def test_company_validator_accepts_empty_board_and_rejects_bad_contract(monkeypatch):
    responses = {
        "empty": _Response({"offers": []}),
        "missing": _Response(status_code=404),
        "malformed": _Response({"jobs": []}),
    }
    monkeypatch.setattr(
        recruitee_scraper,
        "_request_offers",
        lambda tenant: responses[tenant],
    )
    monkeypatch.setattr(
        recruitee_scraper,
        "tqdm",
        lambda values, **kwargs: values,
    )

    assert recruitee_scraper.validate_recruitee_companies(
        ["empty", "missing", "malformed", "bad/path", "EMPTY"]
    ) == {"empty"}


def test_one_observed_outcome_captures_transport_and_completeness(monkeypatch):
    monkeypatch.setattr(
        http_retry.requests,
        "get",
        lambda *args, **kwargs: _Response({"offers": [_offer()]}),
    )

    results = recruitee_scraper._fetch_company_result("acme")
    metrics = pipeline_metrics.acquisition_metrics_snapshot()

    assert len(results) == 1
    assert results[0].status is AcquisitionStatus.SUCCESS
    assert len(metrics) == 1
    metric = metrics[0]
    assert metric.source == "recruitee"
    assert metric.company == "acme"
    assert metric.acquisition_status == "SUCCESS"
    assert metric.request_count == 1
    assert metric.response_status_counts == ((200, 1),)
    assert metric.retry_count == 0
    assert metric.page_count == 1
    assert metric.raw_job_count == 1
    assert metric.normalized_job_count == 1
    assert metric.canonical_url_present_count == 1
    assert metric.timestamp_present_count == 1
    assert metric.description_present_count == 1
    assert metric.schedule_advanced is True
    assert metric.duration_ms is not None


def test_retry_exhaustion_records_failed_transport_metric(monkeypatch):
    monkeypatch.setattr(http_retry.time, "sleep", lambda _delay: None)

    def timeout(*args, **kwargs):
        raise requests.Timeout("fixture secret")

    monkeypatch.setattr(http_retry.requests, "get", timeout)

    outcome = recruitee_scraper._fetch_company_result("acme")[0]
    metric = pipeline_metrics.acquisition_metrics_snapshot()[0]

    assert outcome.status is AcquisitionStatus.FAILED
    assert outcome.reason == "transport_error"
    assert metric.request_count == 2
    assert metric.retry_count == 1
    assert metric.response_status_counts == ()
    assert metric.schedule_advanced is False
    assert metric.health == "unhealthy"
    assert "fixture secret" not in repr(metric)


def _fixture_parallel(completion_order):
    def run_parallel(items, worker_fn, max_workers=10, desc="Processing"):
        assert Counter(items) == Counter(completion_order)
        results = []
        for tenant in completion_order:
            try:
                results.extend(worker_fn(tenant))
            except RuntimeError:
                assert tenant == "raised"
        return results

    return run_parallel


def test_parallel_flat_output_worker_isolation_and_schedule_matrix(monkeypatch):
    companies = ["success", "empty", "partial", "failed", "raised", "success"]
    completion_order = ["partial", "raised", "failed", "empty", "success"]
    schedule = {}
    marked = []
    saved = []

    def result(tenant):
        if tenant == "raised":
            raise RuntimeError("fixture worker failure")
        if tenant == "success":
            outcome = AcquisitionOutcome(
                tenant,
                AcquisitionStatus.SUCCESS,
                ({"company": tenant, "job_id": "success"},),
            )
        elif tenant == "empty":
            outcome = AcquisitionOutcome(tenant, AcquisitionStatus.EMPTY)
        elif tenant == "partial":
            outcome = AcquisitionOutcome(
                tenant,
                AcquisitionStatus.PARTIAL,
                ({"company": tenant, "job_id": "partial"},),
                reason="parse_error",
            )
        else:
            outcome = AcquisitionOutcome(
                tenant,
                AcquisitionStatus.FAILED,
                reason="transport_error",
            )
        return [outcome]

    monkeypatch.setattr(recruitee_scraper, "load_lines", lambda path: companies)
    monkeypatch.setattr(recruitee_scraper, "load_schedule", lambda: schedule)
    monkeypatch.setattr(recruitee_scraper, "should_scrape", lambda company, value: True)
    monkeypatch.setattr(recruitee_scraper, "_fetch_company_result", result)
    monkeypatch.setattr(
        recruitee_scraper,
        "run_parallel",
        _fixture_parallel(completion_order),
    )
    monkeypatch.setattr(
        recruitee_scraper,
        "mark_scraped",
        lambda company, value: marked.append(company),
    )
    monkeypatch.setattr(
        recruitee_scraper,
        "save_schedule",
        lambda value: saved.append(value),
    )

    jobs = recruitee_scraper.scrape_all_recruitee()

    assert jobs == [
        {"company": "partial", "job_id": "partial"},
        {"company": "success", "job_id": "success"},
    ]
    assert marked == ["empty", "success"]
    assert saved == [schedule]


def test_empty_default_off_source_has_no_side_effects(monkeypatch):
    monkeypatch.setattr(recruitee_scraper, "load_lines", lambda path: [])
    monkeypatch.setattr(
        recruitee_scraper,
        "_request_offers",
        lambda tenant: pytest.fail("no Recruitee request expected"),
    )
    monkeypatch.setattr(
        recruitee_scraper,
        "load_schedule",
        lambda: pytest.fail("no schedule access expected"),
    )
    monkeypatch.setattr(
        recruitee_scraper,
        "save_schedule",
        lambda value: pytest.fail("no schedule write expected"),
    )

    assert recruitee_scraper.scrape_all_recruitee() == []
    assert pipeline_metrics.acquisition_metrics_snapshot() == ()


def test_adapter_has_no_mutation_capable_http_helper():
    source = inspect.getsource(recruitee_scraper)
    assert "http_post" not in source
    assert "requests.post" not in source
    assert "careers_apply_url" not in source
    assert "candidate" not in source.lower()


def test_checked_in_curated_configuration_contains_validated_tenants():
    with open("src/config/curated_ats_sources.json", encoding="utf-8") as handle:
        payload = json.load(handle)

    sources = payload["recruitee"]

    assert len(sources) == 24
    assert sources == sorted(set(sources))
    assert "aetherflux" in sources
    assert "basispathinc" in sources
    assert "hudsonmanpower" in sources
    assert "transperfect" in sources
    assert "careermentors" not in sources
    assert "firstfactory" not in sources
