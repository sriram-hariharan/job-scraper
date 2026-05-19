from src.details.workable_details import fetch_workable_details, workable_shortcode
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


def test_workable_shortcode_supports_all_known_sources():
    assert workable_shortcode({"_shortcode": "TOPLEVEL"}) == "TOPLEVEL"
    assert workable_shortcode({"meta": {"_shortcode": "META"}}) == "META"
    assert workable_shortcode({"job_id": "wb_JOBID"}) == "JOBID"
    assert workable_shortcode({"url": "https://apply.workable.com/acme/j/FALLBACK/"}) == "FALLBACK"


def test_workable_detail_fetcher_extracts_description_text(monkeypatch):
    captured_url = {}

    def fake_http_get(url, **kwargs):
        captured_url["url"] = url
        return FakeResponse(
            payload={
                "description": "<p>Build production services.</p>",
            }
        )

    monkeypatch.setattr("src.details.workable_details.http_get", fake_http_get)

    job = {
        "company": "acme",
        "title": "Backend Engineer",
        "source": "workable",
        "job_id": "wb_BACKEND123",
        "url": "https://apply.workable.com/acme/j/BACKEND123/",
    }

    enriched = fetch_workable_details(job)

    assert captured_url["url"] == "https://apply.workable.com/api/v2/accounts/acme/jobs/BACKEND123"
    assert enriched["_details_fetched"] == "workable_api"
    assert enriched["description_text"] == "Build production services."
    assert "Build production services." in enriched["description_html"]


def test_workable_detail_fetcher_includes_requirements_and_benefits(monkeypatch):
    monkeypatch.setattr(
        "src.details.workable_details.http_get",
        lambda *args, **kwargs: FakeResponse(
            payload={
                "description": "Own APIs.",
                "requirements": "<ul><li>Python</li><li>Distributed systems</li></ul>",
                "benefits": ["Remote work", "Health coverage"],
            }
        ),
    )

    job = {
        "company": "acme",
        "title": "Software Engineer",
        "source": "workable",
        "job_id": "wb_JOB456",
        "url": "https://apply.workable.com/acme/j/JOB456/",
    }

    enriched = fetch_workable_details(job)

    assert enriched["_details_fetched"] == "workable_api"
    assert "Own APIs." in enriched["description_text"]
    assert "Python Distributed systems" in enriched["description_text"]
    assert "Remote work Health coverage" in enriched["description_text"]


def test_process_job_treats_workable_as_enrichable(monkeypatch):
    def fake_fetch_workable_details(job):
        job["description_html"] = "<p>Workable description.</p>"
        job["description_text"] = "Workable description."
        job["_details_fetched"] = "workable_api"
        return job

    monkeypatch.setattr(job_details, "get_description", lambda cache_key: None)
    monkeypatch.setattr(job_details, "save_description", lambda description: None)
    monkeypatch.setattr(job_details, "fetch_workable_details", fake_fetch_workable_details)

    job = {
        "source": "workable",
        "job_id": "wb_123",
        "company": "acme",
        "title": "Backend Engineer",
        "url": "https://apply.workable.com/acme/j/123/",
    }

    enriched = job_details.process_job(job)

    assert "workable" in job_details.ENRICHABLE_SOURCES
    assert enriched["_details_fetched"] == "workable_api"
    assert enriched["description_text"] == "Workable description."


def test_failed_workable_response_does_not_crash_and_remains_skipped(monkeypatch):
    monkeypatch.setattr(
        "src.details.workable_details.http_get",
        lambda *args, **kwargs: FakeResponse(status_code=500),
    )

    job = {
        "company": "acme",
        "title": "Backend Engineer",
        "source": "workable",
        "job_id": "wb_BACKEND123",
        "url": "https://apply.workable.com/acme/j/BACKEND123/",
    }

    enriched = fetch_workable_details(job)
    evaluable = filter_jobs_for_ai_evaluation([enriched])

    assert enriched["_details_fetched"] == "workable_request_failed"
    assert evaluable == []
    assert enriched["ai_evaluation_skip_reason"] == SKIPPED_NO_DESCRIPTION


def test_successful_workable_response_without_body_sets_no_description(monkeypatch):
    monkeypatch.setattr(
        "src.details.workable_details.http_get",
        lambda *args, **kwargs: FakeResponse(payload={"description": "", "requirements": ""}),
    )

    job = {
        "company": "acme",
        "title": "Backend Engineer",
        "source": "workable",
        "job_id": "wb_BACKEND123",
        "url": "https://apply.workable.com/acme/j/BACKEND123/",
    }

    enriched = fetch_workable_details(job)
    evaluable = filter_jobs_for_ai_evaluation([enriched])

    assert enriched["_details_fetched"] == "workable_no_description"
    assert evaluable == []
    assert enriched["ai_evaluation_skip_reason"] == SKIPPED_NO_DESCRIPTION


def test_workable_job_with_fetched_description_becomes_evaluable(monkeypatch):
    monkeypatch.setattr(
        "src.details.workable_details.http_get",
        lambda *args, **kwargs: FakeResponse(
            payload={
                "description": "<p>Build reliable services.</p>",
                "requirements": "<p>Python and APIs.</p>",
            }
        ),
    )

    job = {
        "company": "acme",
        "title": "Backend Engineer",
        "source": "workable",
        "job_id": "wb_BACKEND123",
        "url": "https://apply.workable.com/acme/j/BACKEND123/",
    }

    enriched = fetch_workable_details(job)
    evaluable = filter_jobs_for_ai_evaluation([enriched])

    assert enriched["_details_fetched"] == "workable_api"
    assert evaluable == [enriched]
    assert "ai_evaluation_skip_reason" not in enriched
