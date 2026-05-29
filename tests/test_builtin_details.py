import json

from src.details.builtin_details import (
    extract_builtin_description_from_html,
    fetch_builtin_details,
)
from src.pipeline import job_details


class FakeResponse:
    def __init__(self, text="", status_code=200):
        self.text = text
        self.status_code = status_code


def _sample_html(description):
    payload = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "JobPosting",
                "title": "Software Engineer II",
                "description": description,
            }
        ],
    }
    return f"""
    <html>
      <head>
        <script type="application/ld+json">
          {json.dumps(payload)}
        </script>
      </head>
      <body>Rendered page shell</body>
    </html>
    """


def test_builtin_description_parser_extracts_jsonld_job_description():
    description_html, description_text = extract_builtin_description_from_html(
        _sample_html("<p>Build backend systems.</p><ul><li>Own reliable APIs.</li></ul>")
    )

    assert "Build backend systems." in description_html
    assert description_text == "Build backend systems. Own reliable APIs."


def test_builtin_detail_fetcher_populates_description(monkeypatch):
    monkeypatch.setattr(
        "src.details.builtin_details.fetch_builtin_detail_html",
        lambda url: (_sample_html("<p>Build production services.</p>"), 200),
    )

    enriched = fetch_builtin_details(
        {
            "source": "builtin",
            "company": "Chewy",
            "title": "Software Engineer II",
            "url": "https://builtin.com/job/software-engineer-ii/8908325",
            "job_id": "builtin_8908325",
        }
    )

    assert enriched["_details_fetched"] == "builtin_page"
    assert enriched["description_text"] == "Build production services."
    assert "Build production services." in enriched["description_html"]


def test_builtin_no_description_does_not_crash(monkeypatch):
    monkeypatch.setattr(
        "src.details.builtin_details.fetch_builtin_detail_html",
        lambda url: ("<html><body>No json ld here.</body></html>", 200),
    )

    enriched = fetch_builtin_details(
        {
            "source": "builtin",
            "url": "https://builtin.com/job/no-description/1",
        }
    )

    assert enriched["_details_fetched"] == "builtin_no_description"
    assert "description_text" not in enriched


def test_builtin_failed_response_does_not_crash(monkeypatch):
    monkeypatch.setattr(
        "src.details.builtin_details.fetch_builtin_detail_html",
        lambda url: (None, 500),
    )

    enriched = fetch_builtin_details(
        {
            "source": "builtin",
            "url": "https://builtin.com/job/failure/1",
        }
    )

    assert enriched["_details_fetched"] == "builtin_request_failed"
    assert "description_text" not in enriched


def test_builtin_is_enriched_by_job_details(monkeypatch):
    def fake_fetch_builtin_details(job):
        job["description_html"] = "<p>Built In description.</p>"
        job["description_text"] = "Built In description."
        job["_details_fetched"] = "builtin_page"
        return job

    monkeypatch.setattr(job_details, "get_description", lambda cache_key: None)
    monkeypatch.setattr(job_details, "save_description", lambda description: None)
    monkeypatch.setattr(job_details, "fetch_builtin_details", fake_fetch_builtin_details)

    enriched = job_details.process_job(
        {
            "source": "builtin",
            "url": "https://builtin.com/job/software-engineer-ii/8908325",
            "job_id": "builtin_8908325",
        }
    )

    assert "builtin" in job_details.ENRICHABLE_SOURCES
    assert enriched["_details_fetched"] == "builtin_page"
    assert enriched["description_text"] == "Built In description."
