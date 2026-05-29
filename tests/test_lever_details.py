from src.details.lever_details import fetch_lever_details
from src.intelligence.job_intelligence import (
    SKIPPED_NO_DESCRIPTION,
    filter_jobs_for_ai_evaluation,
)
from src.pipeline import job_details


class FakeResponse:
    def __init__(self, status_code=200, payload=None):
        self.status_code = status_code
        self._payload = payload or {}

    def json(self):
        return self._payload


def test_lever_detail_fetcher_extracts_description_text(monkeypatch):
    captured_url = {}

    def fake_http_get(url, **kwargs):
        captured_url["url"] = url
        return FakeResponse(
            payload={
                "description": "<p>Build APIs for payments.</p>",
                "descriptionPlain": "Build APIs for payments.",
            }
        )

    monkeypatch.setattr("src.details.lever_details.http_get", fake_http_get)

    job = {
        "company": "stripe",
        "title": "Backend Engineer",
        "source": "lever",
        "job_id": "lv_abc123",
        "url": "https://jobs.lever.co/stripe/abc123",
    }

    enriched = fetch_lever_details(job)

    assert captured_url["url"] == "https://api.lever.co/v0/postings/stripe/abc123"
    assert enriched["_details_fetched"] == "lever_api"
    assert enriched["description_text"] == "Build APIs for payments."
    assert "Build APIs for payments." in enriched["description_html"]


def test_lever_detail_fetcher_includes_lists_and_additional(monkeypatch):
    monkeypatch.setattr(
        "src.details.lever_details.http_get",
        lambda *args, **kwargs: FakeResponse(
            payload={
                "descriptionPlain": "Own backend services.",
                "lists": [
                    {
                        "text": "Responsibilities",
                        "content": "<ul><li>Design APIs.</li><li>Improve reliability.</li></ul>",
                    },
                    {
                        "text": "Requirements",
                        "content": "<p>Python and distributed systems.</p>",
                    },
                ],
                "additionalPlain": "Equal opportunity employer.",
            }
        ),
    )

    job = {
        "company": "acme",
        "title": "Software Engineer",
        "source": "lever",
        "job_id": "lv_job-456",
        "url": "https://jobs.lever.co/acme/job-456",
    }

    enriched = fetch_lever_details(job)

    assert enriched["_details_fetched"] == "lever_api"
    assert "Own backend services." in enriched["description_text"]
    assert "Responsibilities Design APIs. Improve reliability." in enriched["description_text"]
    assert "Requirements Python and distributed systems." in enriched["description_text"]
    assert "Equal opportunity employer." in enriched["description_text"]
    assert "<h3>Responsibilities</h3>" in enriched["description_html"]


def test_process_job_treats_lever_as_enrichable(monkeypatch):
    def fake_fetch_lever_details(job):
        job["description_html"] = "<p>Lever description.</p>"
        job["description_text"] = "Lever description."
        job["_details_fetched"] = "lever_api"
        return job

    monkeypatch.setattr(job_details, "get_description", lambda cache_key: None)
    monkeypatch.setattr(job_details, "save_description", lambda description: None)
    monkeypatch.setattr(job_details, "fetch_lever_details", fake_fetch_lever_details)

    job = {
        "source": "lever",
        "job_id": "lv_123",
        "company": "acme",
        "title": "Backend Engineer",
        "url": "https://jobs.lever.co/acme/123",
    }

    enriched = job_details.process_job(job)

    assert "lever" in job_details.ENRICHABLE_SOURCES
    assert enriched["_details_fetched"] == "lever_api"
    assert enriched["description_text"] == "Lever description."


def test_failed_lever_response_does_not_crash_and_remains_skipped(monkeypatch):
    monkeypatch.setattr(
        "src.details.lever_details.http_get",
        lambda *args, **kwargs: FakeResponse(status_code=500),
    )

    job = {
        "company": "stripe",
        "title": "Backend Engineer",
        "source": "lever",
        "job_id": "lv_abc123",
        "url": "https://jobs.lever.co/stripe/abc123",
    }

    enriched = fetch_lever_details(job)
    evaluable = filter_jobs_for_ai_evaluation([enriched])

    assert enriched["_details_fetched"] == "lever_request_failed"
    assert evaluable == []
    assert enriched["ai_evaluation_skip_reason"] == SKIPPED_NO_DESCRIPTION


def test_successful_lever_response_without_body_sets_no_description(monkeypatch):
    monkeypatch.setattr(
        "src.details.lever_details.http_get",
        lambda *args, **kwargs: FakeResponse(payload={"description": "", "lists": []}),
    )

    job = {
        "company": "stripe",
        "title": "Backend Engineer",
        "source": "lever",
        "job_id": "lv_abc123",
        "url": "https://jobs.lever.co/stripe/abc123",
    }

    enriched = fetch_lever_details(job)
    evaluable = filter_jobs_for_ai_evaluation([enriched])

    assert enriched["_details_fetched"] == "lever_no_description"
    assert evaluable == []
    assert enriched["ai_evaluation_skip_reason"] == SKIPPED_NO_DESCRIPTION


def test_lever_job_with_fetched_description_becomes_evaluable(monkeypatch):
    monkeypatch.setattr(
        "src.details.lever_details.http_get",
        lambda *args, **kwargs: FakeResponse(
            payload={
                "description": "<p>Build distributed backend systems.</p>",
                "lists": [
                    {"text": "Requirements", "content": "<p>Python and APIs.</p>"}
                ],
            }
        ),
    )

    job = {
        "company": "stripe",
        "title": "Backend Engineer",
        "source": "lever",
        "job_id": "lv_abc123",
        "url": "https://jobs.lever.co/stripe/abc123",
    }

    enriched = fetch_lever_details(job)
    evaluable = filter_jobs_for_ai_evaluation([enriched])

    assert enriched["_details_fetched"] == "lever_api"
    assert evaluable == [enriched]
    assert "ai_evaluation_skip_reason" not in enriched
