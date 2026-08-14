from datetime import datetime, timezone

from src.discovery.crawl_scheduler import AcquisitionOutcome, AcquisitionStatus
from src.scrapers import builtin_scraper
from src.scrapers.builtin_scraper import extract_builtin_jobs_from_html


def _job_card(company, title, posted, location, job_slug="software-engineer", job_id="12345"):
    posted_html = f"<span>{posted}</span>" if posted is not None else ""
    return f"""
    <a href="/company/{company.lower().replace(' ', '-')}" target="_blank"><span>{company}</span></a>
    <h2><a href="/job/{job_slug}/{job_id}" target="_blank" data-id="job-card-title">{title}</a></h2>
    {posted_html}
    <span>Hybrid</span>
    <span>{location}</span>
    <span>150K-200K Annually</span>
    <p>Build useful software.</p>
    """


def test_extract_builtin_recent_engineering_job():
    now = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    jobs = extract_builtin_jobs_from_html(
        _job_card("Acme AI", "Software Engineer", "48 Minutes Ago", "New York, NY, USA"),
        now=now,
    )

    assert len(jobs) == 1
    assert jobs[0]["source"] == "builtin"
    assert jobs[0]["company"] == "Acme AI"
    assert jobs[0]["title"] == "Software Engineer"
    assert jobs[0]["location"] == "New York, NY, USA"
    assert jobs[0]["posted_at"] == "2026-05-27T11:12:00+00:00"
    assert jobs[0]["url"] == "https://builtin.com/job/software-engineer/12345"


def test_extract_builtin_stale_job_with_reliable_timestamp():
    now = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    jobs = extract_builtin_jobs_from_html(
        _job_card("Old Co", "Backend Engineer", "Reposted 3 Days Ago", "Austin, TX, USA"),
        now=now,
    )

    assert len(jobs) == 1
    assert jobs[0]["posted_at"] == "2026-05-24T12:00:00+00:00"


def test_extract_builtin_non_engineering_job_with_reliable_timestamp():
    now = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    jobs = extract_builtin_jobs_from_html(
        _job_card("Ops Co", "Customer Success Manager", "6 Hours Ago", "Remote, USA"),
        now=now,
    )

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Customer Success Manager"
    assert jobs[0]["posted_at"] == "2026-05-27T06:00:00+00:00"


def test_extract_builtin_missing_timestamp_is_not_emitted():
    jobs = extract_builtin_jobs_from_html(
        _job_card("No Time Co", "Software Engineer", None, "Boston, MA, USA"),
        now=datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc),
    )

    assert jobs == []


def test_extract_builtin_augments_title_when_url_slug_contains_staff():
    now = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    jobs = extract_builtin_jobs_from_html(
        _job_card(
            "Agent Co",
            "Software Engineer, Agent",
            "2 Hours Ago",
            "San Francisco, CA, USA",
            job_slug="staff-software-engineer-agent",
            job_id="8967348",
        ),
        now=now,
    )

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Staff Software Engineer, Agent"
    assert jobs[0]["url"] == "https://builtin.com/job/staff-software-engineer-agent/8967348"


def test_extract_builtin_normal_title_remains_unchanged():
    now = datetime(2026, 5, 27, 12, 0, tzinfo=timezone.utc)
    jobs = extract_builtin_jobs_from_html(
        _job_card(
            "Normal Co",
            "Software Engineer, Agent",
            "2 Hours Ago",
            "San Francisco, CA, USA",
            job_slug="software-engineer-agent",
            job_id="8967349",
        ),
        now=now,
    )

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Software Engineer, Agent"


def test_fixed_routes_are_exact_and_ordered():
    assert builtin_scraper.BUILTIN_JOBS_URLS == (
        "https://builtin.com/jobs/dev-engineering",
        "https://builtin.com/jobs/data-analytics/data-science",
        "https://builtin.com/jobs/data-analytics/machine-learning",
    )


def test_three_routes_are_fetched_sequentially_and_aggregated(monkeypatch):
    route_html = {
        builtin_scraper.BUILTIN_JOBS_URLS[0]: _job_card(
            "First Co",
            "First Route Title",
            "1 Hour Ago",
            "Austin, TX, USA",
            job_id="1",
        ),
        builtin_scraper.BUILTIN_JOBS_URLS[1]: (
            _job_card(
                "Second Co",
                "Duplicate Route Title",
                "2 Hours Ago",
                "Boston, MA, USA",
                job_id="1",
            )
            + _job_card(
                "Second Co",
                "Second Route Title",
                "3 Hours Ago",
                "Boston, MA, USA",
                job_id="2",
            )
        ),
        builtin_scraper.BUILTIN_JOBS_URLS[2]: _job_card(
            "Third Co",
            "Third Route Title",
            "4 Hours Ago",
            "Seattle, WA, USA",
            job_id="3",
        ),
    }
    calls = []

    class Response:
        status = 200

        def __init__(self, body):
            self.body = body

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return None

        def read(self):
            return self.body.encode("utf-8")

    def urlopen(request, *, timeout):
        calls.append((request.full_url, timeout))
        return Response(route_html[request.full_url])

    monkeypatch.setattr(builtin_scraper, "urlopen", urlopen)
    outcome = builtin_scraper._fetch_builtin_outcome()

    assert calls == [
        (url, builtin_scraper.BUILTIN_HTTP_TIMEOUT_SECONDS)
        for url in builtin_scraper.BUILTIN_JOBS_URLS
    ]
    assert outcome.status is AcquisitionStatus.SUCCESS
    assert outcome.reason == ""
    assert outcome.page_count == 3
    assert outcome.raw_job_count == 3
    assert len(outcome.jobs) == 3
    assert [job["job_id"] for job in outcome.jobs] == [
        "builtin_1",
        "builtin_2",
        "builtin_3",
    ]
    assert outcome.jobs[0]["title"] == "First Route Title"


def test_failed_route_with_safe_jobs_is_partial(monkeypatch):
    responses = iter(
        [
            (
                _job_card(
                    "Safe Co",
                    "Safe Title",
                    "1 Hour Ago",
                    "Austin, TX, USA",
                ),
                "",
            ),
            ("", "non_200_response"),
            ("", ""),
        ]
    )
    monkeypatch.setattr(
        builtin_scraper,
        "_fetch_builtin_jobs_html_result",
        lambda _url: next(responses),
    )

    outcome = builtin_scraper._fetch_builtin_outcome()

    assert outcome.status is AcquisitionStatus.PARTIAL
    assert outcome.reason == "non_200_response"
    assert len(outcome.jobs) == 1
    assert outcome.page_count == 2
    assert outcome.raw_job_count == 1


def test_all_routes_failing_is_failed_with_deterministic_reason(monkeypatch):
    responses = iter(
        [
            ("", "non_200_response"),
            ("", "transport_error"),
            ("", "non_200_response"),
        ]
    )
    monkeypatch.setattr(
        builtin_scraper,
        "_fetch_builtin_jobs_html_result",
        lambda _url: next(responses),
    )

    outcome = builtin_scraper._fetch_builtin_outcome()

    assert outcome.status is AcquisitionStatus.FAILED
    assert outcome.reason == "transport_error"
    assert outcome.jobs == ()
    assert outcome.page_count == 0
    assert outcome.raw_job_count == 0


def test_three_valid_empty_routes_are_empty(monkeypatch):
    monkeypatch.setattr(
        builtin_scraper,
        "_fetch_builtin_jobs_html_result",
        lambda _url: ("", ""),
    )

    outcome = builtin_scraper._fetch_builtin_outcome()

    assert outcome.status is AcquisitionStatus.EMPTY
    assert outcome.reason == ""
    assert outcome.page_count == 3
    assert outcome.raw_job_count == 0


def test_failed_and_empty_routes_are_failed(monkeypatch):
    responses = iter(
        [
            ("", ""),
            ("", "transport_error"),
            ("", ""),
        ]
    )
    monkeypatch.setattr(
        builtin_scraper,
        "_fetch_builtin_jobs_html_result",
        lambda _url: next(responses),
    )

    outcome = builtin_scraper._fetch_builtin_outcome()

    assert outcome.status is AcquisitionStatus.FAILED
    assert outcome.reason == "transport_error"
    assert outcome.jobs == ()
    assert outcome.page_count == 2
    assert outcome.raw_job_count == 0


def test_route_helpers_do_not_learn(monkeypatch):
    monkeypatch.setattr(
        builtin_scraper,
        "_fetch_builtin_jobs_html_result",
        lambda _url: ("", ""),
    )
    monkeypatch.setattr(
        builtin_scraper,
        "learn_from_job_url",
        lambda _url: (_ for _ in ()).throw(AssertionError("unexpected learning")),
    )

    outcome = builtin_scraper._fetch_builtin_outcome()

    assert outcome.status is AcquisitionStatus.EMPTY


def test_scrape_observes_once_caps_jobs_and_then_learns(monkeypatch):
    jobs = tuple(
        {
            "url": f"https://builtin.com/job/software-engineer/{index}",
            "job_id": f"builtin_{index}",
        }
        for index in range(10_001)
    )
    outcome = AcquisitionOutcome(
        "<global_feed>",
        AcquisitionStatus.SUCCESS,
        jobs,
        page_count=3,
        raw_job_count=len(jobs),
    )
    observations = []
    learned = []

    def observe(source, acquire, *, schedule_on_success, company):
        observations.append((source, acquire, schedule_on_success, company))
        return outcome

    monkeypatch.setattr(builtin_scraper, "observe_acquisition", observe)
    monkeypatch.setattr(builtin_scraper, "learn_from_job_url", learned.append)

    result = builtin_scraper.scrape_all_builtin()

    assert len(result) == 10_000
    assert learned == [job["url"] for job in jobs[:10_000]]
    assert observations == [
        (
            "builtin",
            builtin_scraper._fetch_builtin_outcome,
            False,
            "<global_feed>",
        )
    ]
