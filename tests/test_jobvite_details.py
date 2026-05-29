from src.details.jobvite_details import fetch_jobvite_details
from src.intelligence.job_intelligence import (
    SKIPPED_NO_DESCRIPTION,
    filter_jobs_for_ai_evaluation,
)
from src.pipeline import job_details


class FakeResponse:
    def __init__(self, status_code=200, text=""):
        self.status_code = status_code
        self.text = text


def test_jobvite_jsonld_description_extracts_description_text(monkeypatch):
    page = """
    <html><head>
      <script type="application/ld+json">
        {
          "@context": "https://schema.org",
          "@type": "JobPosting",
          "description": "<p>Build risk APIs.</p><p>Own platform quality.</p>"
        }
      </script>
    </head><body>Other content</body></html>
    """
    monkeypatch.setattr(
        "src.details.jobvite_details.http_get",
        lambda *args, **kwargs: FakeResponse(text=page),
    )

    job = {
        "company": "acme",
        "title": "Backend Engineer",
        "source": "jobvite",
        "job_id": "jv_123",
        "url": "https://jobs.jobvite.com/acme/job/abc123",
    }

    enriched = fetch_jobvite_details(job)

    assert enriched["_details_fetched"] == "jobvite_html"
    assert enriched["description_text"] == "Build risk APIs. Own platform quality."
    assert "Build risk APIs." in enriched["description_html"]


def test_jobvite_html_only_description_extracts_description_text(monkeypatch):
    page = """
    <html><body>
      <div class="jv-job-description">
        <h2>About the role</h2>
        <p>Design secure backend services.</p>
      </div>
    </body></html>
    """
    monkeypatch.setattr(
        "src.details.jobvite_details.http_get",
        lambda *args, **kwargs: FakeResponse(text=page),
    )

    job = {
        "company": "acme",
        "title": "Security Engineer",
        "source": "jobvite",
        "job_id": "jv_456",
        "url": "https://jobs.jobvite.com/acme/job/def456",
    }

    enriched = fetch_jobvite_details(job)

    assert enriched["_details_fetched"] == "jobvite_html"
    assert "About the role Design secure backend services." in enriched["description_text"]


def test_process_job_treats_jobvite_as_enrichable(monkeypatch):
    def fake_fetch_jobvite_details(job):
        job["description_html"] = "<p>Jobvite description.</p>"
        job["description_text"] = "Jobvite description."
        job["_details_fetched"] = "jobvite_html"
        return job

    monkeypatch.setattr(job_details, "get_description", lambda cache_key: None)
    monkeypatch.setattr(job_details, "save_description", lambda description: None)
    monkeypatch.setattr(job_details, "fetch_jobvite_details", fake_fetch_jobvite_details)

    job = {
        "source": "jobvite",
        "job_id": "jv_123",
        "company": "acme",
        "title": "Backend Engineer",
        "url": "https://jobs.jobvite.com/acme/job/abc123",
    }

    enriched = job_details.process_job(job)

    assert "jobvite" in job_details.ENRICHABLE_SOURCES
    assert enriched["_details_fetched"] == "jobvite_html"
    assert enriched["description_text"] == "Jobvite description."


def test_failed_jobvite_response_does_not_crash_and_remains_skipped(monkeypatch):
    monkeypatch.setattr(
        "src.details.jobvite_details.http_get",
        lambda *args, **kwargs: FakeResponse(status_code=500, text=""),
    )

    job = {
        "company": "acme",
        "title": "Backend Engineer",
        "source": "jobvite",
        "job_id": "jv_123",
        "url": "https://jobs.jobvite.com/acme/job/abc123",
    }

    enriched = fetch_jobvite_details(job)
    evaluable = filter_jobs_for_ai_evaluation([enriched])

    assert enriched["_details_fetched"] == "jobvite_request_failed"
    assert evaluable == []
    assert enriched["ai_evaluation_skip_reason"] == SKIPPED_NO_DESCRIPTION


def test_jobvite_job_with_description_becomes_evaluable(monkeypatch):
    page = """
    <html><body>
      <section class="job-description">
        <p>Build reliable APIs for customer systems.</p>
      </section>
    </body></html>
    """
    monkeypatch.setattr(
        "src.details.jobvite_details.http_get",
        lambda *args, **kwargs: FakeResponse(text=page),
    )

    job = {
        "company": "acme",
        "title": "Backend Engineer",
        "source": "jobvite",
        "job_id": "jv_123",
        "url": "https://jobs.jobvite.com/acme/job/abc123",
    }

    enriched = fetch_jobvite_details(job)
    evaluable = filter_jobs_for_ai_evaluation([enriched])

    assert enriched["_details_fetched"] == "jobvite_html"
    assert evaluable == [enriched]
    assert "ai_evaluation_skip_reason" not in enriched
