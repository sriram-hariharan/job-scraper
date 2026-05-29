from datetime import datetime, timezone
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
