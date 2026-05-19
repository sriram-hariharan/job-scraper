from src.details.ashby_details import fetch_ashby_details
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


def test_ashby_detail_fetcher_extracts_description_text(monkeypatch):
    captured_payload = {}

    def fake_http_post(url, **kwargs):
        captured_payload.update(kwargs.get("json") or {})
        return FakeResponse(
            payload={
                "data": {
                    "jobPosting": {
                        "id": "675be915-3aed-4fe2-8f8b-f56dde88cf8a",
                        "title": "Software Engineer - Security",
                        "descriptionHtml": "<div><p>Build secure APIs.</p><p>Own platform security.</p></div>",
                    }
                }
            }
        )

    monkeypatch.setattr("src.details.ashby_details.http_post", fake_http_post)

    job = {
        "company": "plaid",
        "title": "Software Engineer - Security",
        "source": "ashby",
        "job_id": "as_675be915-3aed-4fe2-8f8b-f56dde88cf8a",
        "url": "https://jobs.ashbyhq.com/plaid/675be915-3aed-4fe2-8f8b-f56dde88cf8a",
    }

    enriched = fetch_ashby_details(job)

    assert captured_payload["operationName"] == "ApiJobPosting"
    assert captured_payload["variables"] == {
        "organizationHostedJobsPageName": "plaid",
        "jobPostingId": "675be915-3aed-4fe2-8f8b-f56dde88cf8a",
    }
    assert enriched["_details_fetched"] == "ashby_api"
    assert "Build secure APIs." in enriched["description_html"]
    assert enriched["description_text"] == "Build secure APIs. Own platform security."


def test_process_job_treats_ashby_as_enrichable(monkeypatch):
    def fake_fetch_ashby_details(job):
        job["description_html"] = "<p>Ashby description.</p>"
        job["description_text"] = "Ashby description."
        job["_details_fetched"] = "ashby_api"
        return job

    monkeypatch.setattr(job_details, "get_description", lambda cache_key: None)
    monkeypatch.setattr(job_details, "save_description", lambda description: None)
    monkeypatch.setattr(job_details, "fetch_ashby_details", fake_fetch_ashby_details)

    job = {
        "source": "ashby",
        "job_id": "as_123",
        "company": "acme",
        "title": "Backend Engineer",
        "url": "https://jobs.ashbyhq.com/acme/123",
    }

    enriched = job_details.process_job(job)

    assert "ashby" in job_details.ENRICHABLE_SOURCES
    assert enriched["_details_fetched"] == "ashby_api"
    assert enriched["description_text"] == "Ashby description."


def test_ashby_job_with_fetched_description_becomes_evaluable(monkeypatch):
    monkeypatch.setattr(
        "src.details.ashby_details.http_post",
        lambda *args, **kwargs: FakeResponse(
            payload={
                "data": {
                    "jobPosting": {
                        "descriptionHtml": "<p>Build distributed systems for security products.</p>",
                    }
                }
            }
        ),
    )

    job = {
        "company": "plaid",
        "title": "Software Engineer - Security",
        "source": "ashby",
        "job_id": "as_675be915-3aed-4fe2-8f8b-f56dde88cf8a",
        "url": "https://jobs.ashbyhq.com/plaid/675be915-3aed-4fe2-8f8b-f56dde88cf8a",
    }

    enriched = fetch_ashby_details(job)
    evaluable = filter_jobs_for_ai_evaluation([enriched])

    assert enriched["_details_fetched"] == "ashby_api"
    assert evaluable == [enriched]
    assert "ai_evaluation_skip_reason" not in enriched


def test_failed_ashby_response_does_not_crash_and_remains_skipped(monkeypatch):
    monkeypatch.setattr(
        "src.details.ashby_details.http_post",
        lambda *args, **kwargs: FakeResponse(status_code=500),
    )

    job = {
        "company": "plaid",
        "title": "Software Engineer - Security",
        "source": "ashby",
        "job_id": "as_675be915-3aed-4fe2-8f8b-f56dde88cf8a",
        "url": "https://jobs.ashbyhq.com/plaid/675be915-3aed-4fe2-8f8b-f56dde88cf8a",
    }

    enriched = fetch_ashby_details(job)
    evaluable = filter_jobs_for_ai_evaluation([enriched])

    assert enriched["_details_fetched"] == "failed"
    assert evaluable == []
    assert enriched["ai_evaluation_skip_reason"] == SKIPPED_NO_DESCRIPTION
