import requests
import time
from src.config.consts import ASHBY_URL, ASHBY_QUERY, ASHBY_TIMESTAMP_QUERY
from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.parallel import run_parallel
from src.utils.logging import get_logger
from src.discovery.learned_companies import learn_from_job_url
from src.utils.http_retry import http_post
from src.discovery.crawl_scheduler import (
    load_schedule,
    save_schedule,
    should_scrape,
    mark_scraped
)

logger = get_logger("ashby")

ASHBY_TIMESTAMP_RETRIES = 3
ASHBY_TIMESTAMP_THROTTLE_SECONDS = 0.4
ASHBY_TIMESTAMP_BACKOFF_SECONDS = 0.5

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "apollographql-client-name": "frontend_non_user",
    "apollographql-client-version": "0.1.0",
    "Origin": "https://jobs.ashbyhq.com",
    "Referer": "https://jobs.ashbyhq.com"
}

def _ashby_timestamp_result(posted_at=None, marker="", status_code=None):
    return {
        "posted_at": posted_at,
        "marker": marker,
        "status_code": status_code,
    }


def _log_ashby_timestamp_failure(company, job_id, marker, status_code=None):
    logger.warning(
        "Ashby timestamp fetch failed | company=%s | job_id=%s | status=%s | reason=%s",
        company or "",
        job_id or "",
        status_code if status_code is not None else "",
        marker,
    )


def fetch_ashby_timestamp_result(company, job_id):
    payload = {
        "operationName": "ApiJobPosting",
        "query": ASHBY_TIMESTAMP_QUERY,
        "variables": {
            "organizationHostedJobsPageName": company,
            "jobPostingId": job_id
        }
    }

    last_response = None

    for attempt in range(ASHBY_TIMESTAMP_RETRIES):
        if ASHBY_TIMESTAMP_THROTTLE_SECONDS > 0:
            time.sleep(ASHBY_TIMESTAMP_THROTTLE_SECONDS)

        try:
            last_response = http_post(
                ASHBY_URL,
                json=payload,
                headers=HEADERS,
                timeout=10
            )
        except Exception:
            last_response = None

        status_code = getattr(last_response, "status_code", None)
        if last_response is not None and status_code == 200:
            break

        if attempt < ASHBY_TIMESTAMP_RETRIES - 1:
            logger.info(
                "Retrying Ashby timestamp fetch | company=%s | job_id=%s | status=%s | attempt=%s",
                company or "",
                job_id or "",
                status_code if status_code is not None else "",
                attempt + 1,
            )
            time.sleep(ASHBY_TIMESTAMP_BACKOFF_SECONDS * (attempt + 1))

    status_code = getattr(last_response, "status_code", None)
    if last_response is None or status_code != 200:
        marker = "ashby_timestamp_request_failed"
        _log_ashby_timestamp_failure(company, job_id, marker, status_code=status_code)
        return _ashby_timestamp_result(marker=marker, status_code=status_code)

    try:
        data = last_response.json()
    except Exception:
        marker = "ashby_timestamp_parse_failed"
        _log_ashby_timestamp_failure(company, job_id, marker, status_code=status_code)
        return _ashby_timestamp_result(marker=marker, status_code=status_code)

    if not isinstance(data, dict):
        marker = "ashby_timestamp_parse_failed"
        _log_ashby_timestamp_failure(company, job_id, marker, status_code=status_code)
        return _ashby_timestamp_result(marker=marker, status_code=status_code)

    if data.get("errors"):
        marker = "ashby_timestamp_request_failed"
        _log_ashby_timestamp_failure(company, job_id, marker, status_code=status_code)
        return _ashby_timestamp_result(marker=marker, status_code=status_code)

    root = data.get("data")
    job = root.get("jobPosting") if isinstance(root, dict) else None
    if not isinstance(job, dict):
        marker = "ashby_timestamp_parse_failed"
        _log_ashby_timestamp_failure(company, job_id, marker, status_code=status_code)
        return _ashby_timestamp_result(marker=marker, status_code=status_code)

    published_date = str(job.get("publishedDate") or "").strip()
    if not published_date:
        marker = "ashby_timestamp_no_published_date"
        _log_ashby_timestamp_failure(company, job_id, marker, status_code=status_code)
        return _ashby_timestamp_result(marker=marker, status_code=status_code)

    return _ashby_timestamp_result(posted_at=published_date, marker="")


def fetch_ashby_timestamp(company, job_id):
    result = fetch_ashby_timestamp_result(company, job_id)
    return result.get("posted_at")

def fetch_company_jobs(company):

    payload = {
        "operationName": "ApiJobBoardWithTeams",
        "query": ASHBY_QUERY,
        "variables": {"organizationHostedJobsPageName": company}
    }
    try:
        r = http_post(
            ASHBY_URL,
            json=payload,
            headers=HEADERS,
            timeout=10
        )
    except Exception:
        return []

    if r is None or r.status_code != 200:
        return []

    data = r.json()
    data_root = data.get("data")
    if not data_root:
        return []

    job_board = data_root.get("jobBoard")

    if not job_board:
        return []

    jobs_data = job_board.get("jobPostings", [])

    jobs = []

    for job in jobs_data:
        
        title = job.get("title", "")
        job_id = job.get("id")

        job_url = f"https://jobs.ashbyhq.com/{company}/{job_id}"

        learn_from_job_url(job_url)

        jobs.append(
            Job(
                company=company,
                title=title,
                location=job.get("locationName") or "",
                url=job_url,
                source="ashby",
                posted_at=None,
                meta={"_job_id": job_id},
                job_id=f"as_{job_id}",
            ).to_dict()
        )

    return jobs


def scrape_all_ashby():
    companies = load_lines("discovery://ats/ashby")
    schedule = load_schedule()

    companies = [
    c for c in companies
    if should_scrape(c, schedule)
    ]

    # remove duplicates
    companies = list(set(companies))


    results = run_parallel(
    companies,
    fetch_company_jobs,
    max_workers=20,
    desc="Ashby scraping"   
    )

    for company in companies:
        mark_scraped(company, schedule)

    all_jobs = []
    for r in results:
        if isinstance(r, list):
            all_jobs.extend(r)
        elif isinstance(r, dict):
            all_jobs.append(r)

    save_schedule(schedule)
    
    return all_jobs
