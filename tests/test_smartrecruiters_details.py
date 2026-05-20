from src.details.smartrecruiters_details import (
    fetch_smartrecruiters_details,
    smartrecruiters_identifiers,
)
from src.intelligence.job_intelligence import (
    SKIPPED_NO_DESCRIPTION,
    filter_jobs_for_ai_evaluation,
)
from src.pipeline import job_details


class FakeResponse:
    def __init__(self, status_code=200, payload=None, text=""):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


def test_smartrecruiters_identifier_helper_supports_job_id_and_url():
    assert smartrecruiters_identifiers(
        {"company": "Acme", "job_id": "sr_abc123"}
    ) == ("Acme", "abc123")
    assert smartrecruiters_identifiers(
        {"url": "https://jobs.smartrecruiters.com/Nvidia/12345-ml-engineer"}
    ) == ("Nvidia", "12345-ml-engineer")


def test_smartrecruiters_api_response_extracts_description_text(monkeypatch):
    captured_url = {}

    def fake_http_get(url, **kwargs):
        captured_url["url"] = url
        return FakeResponse(
            payload={
                "jobAd": {
                    "sections": {
                        "jobDescription": {"text": "<p>Build analytics services.</p>"},
                    }
                }
            }
        )

    monkeypatch.setattr("src.details.smartrecruiters_details.http_get", fake_http_get)

    job = {
        "company": "Acme",
        "title": "Backend Engineer",
        "source": "smartrecruiters",
        "job_id": "sr_abc123",
        "url": "https://jobs.smartrecruiters.com/Acme/abc123",
    }

    enriched = fetch_smartrecruiters_details(job)

    assert captured_url["url"] == "https://api.smartrecruiters.com/v1/companies/Acme/postings/abc123"
    assert enriched["_details_fetched"] == "smartrecruiters_api"
    assert enriched["description_text"] == "Build analytics services."


def test_smartrecruiters_multiple_section_fields_are_included(monkeypatch):
    monkeypatch.setattr(
        "src.details.smartrecruiters_details.http_get",
        lambda *args, **kwargs: FakeResponse(
            payload={
                "jobAd": {
                    "sections": {
                        "jobDescription": {"text": "Own platform systems."},
                        "qualifications": {"text": "<p>Python and APIs.</p>"},
                        "additionalInformation": {"text": "Remote friendly."},
                    }
                },
                "responsibilities": "Improve reliability.",
                "qualifications": "Distributed systems.",
            }
        ),
    )

    job = {
        "company": "Acme",
        "title": "Software Engineer",
        "source": "smartrecruiters",
        "job_id": "sr_job456",
        "url": "https://jobs.smartrecruiters.com/Acme/job456",
    }

    enriched = fetch_smartrecruiters_details(job)

    assert enriched["_details_fetched"] == "smartrecruiters_api"
    assert "Own platform systems." in enriched["description_text"]
    assert "Python and APIs." in enriched["description_text"]
    assert "Remote friendly." in enriched["description_text"]
    assert "Improve reliability." in enriched["description_text"]
    assert "Distributed systems." in enriched["description_text"]


def test_process_job_treats_smartrecruiters_as_enrichable(monkeypatch):
    def fake_fetch_smartrecruiters_details(job):
        job["description_html"] = "<p>SmartRecruiters description.</p>"
        job["description_text"] = "SmartRecruiters description."
        job["_details_fetched"] = "smartrecruiters_api"
        return job

    monkeypatch.setattr(job_details, "get_description", lambda cache_key: None)
    monkeypatch.setattr(job_details, "save_description", lambda description: None)
    monkeypatch.setattr(
        job_details,
        "fetch_smartrecruiters_details",
        fake_fetch_smartrecruiters_details,
    )

    job = {
        "source": "smartrecruiters",
        "job_id": "sr_123",
        "company": "Acme",
        "title": "Backend Engineer",
        "url": "https://jobs.smartrecruiters.com/Acme/123",
    }

    enriched = job_details.process_job(job)

    assert "smartrecruiters" in job_details.ENRICHABLE_SOURCES
    assert enriched["_details_fetched"] == "smartrecruiters_api"
    assert enriched["description_text"] == "SmartRecruiters description."


def test_failed_smartrecruiters_response_does_not_crash_and_remains_skipped(monkeypatch):
    monkeypatch.setattr(
        "src.details.smartrecruiters_details.http_get",
        lambda *args, **kwargs: FakeResponse(status_code=500),
    )

    job = {
        "company": "Acme",
        "title": "Backend Engineer",
        "source": "smartrecruiters",
        "job_id": "sr_123",
        "url": "https://jobs.smartrecruiters.com/Acme/123",
    }

    enriched = fetch_smartrecruiters_details(job)
    evaluable = filter_jobs_for_ai_evaluation([enriched])

    assert enriched["_details_fetched"] == "smartrecruiters_request_failed"
    assert evaluable == []
    assert enriched["ai_evaluation_skip_reason"] == SKIPPED_NO_DESCRIPTION


def test_smartrecruiters_job_with_description_becomes_evaluable(monkeypatch):
    monkeypatch.setattr(
        "src.details.smartrecruiters_details.http_get",
        lambda *args, **kwargs: FakeResponse(
            payload={
                "jobAd": {
                    "sections": {
                        "jobDescription": {"text": "<p>Build reliable APIs.</p>"},
                    }
                }
            }
        ),
    )

    job = {
        "company": "Acme",
        "title": "Backend Engineer",
        "source": "smartrecruiters",
        "job_id": "sr_123",
        "url": "https://jobs.smartrecruiters.com/Acme/123",
    }

    enriched = fetch_smartrecruiters_details(job)
    evaluable = filter_jobs_for_ai_evaluation([enriched])

    assert enriched["_details_fetched"] == "smartrecruiters_api"
    assert evaluable == [enriched]
    assert "ai_evaluation_skip_reason" not in enriched
