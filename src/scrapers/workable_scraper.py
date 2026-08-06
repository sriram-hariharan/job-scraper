import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlsplit

import requests

from src.utils.http_retry import retry_request
from src.utils.pipeline_metrics import observe_acquisition
from src.config.consts import (
    WORKABLE_PUBLIC_ACCOUNT_API,
    WORKABLE_V2_DETAIL_API,
)
from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.parallel import run_parallel
from src.utils.logging import get_logger
from src.discovery.learned_companies import (
    learn_from_job_url,
    normalize_workable_slug,
)
from src.discovery.crawl_scheduler import (
    AcquisitionOutcome,
    AcquisitionStatus,
    load_schedule,
    save_schedule,
    should_scrape,
    mark_scraped
)

logger = get_logger("workable")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

@retry_request(retries=2)
def workable_get(url, **kwargs):
    return session.get(url, **kwargs)


@retry_request(retries=2)
def workable_post(url, **kwargs):
    return session.post(url, **kwargs)

def fetch_workable_timestamp(company, shortcode):

    if not shortcode:
        return None

    url = WORKABLE_V2_DETAIL_API.format(company, shortcode)

    try:
        r = workable_get(url, timeout=10)

        if r is None or r.status_code != 200:
            return None

        data = r.json()
        return data.get("published")

    except Exception:
        return None


def extract_v3_jobs(data):

    if not isinstance(data, dict):
        return []

    if "results" in data and isinstance(data["results"], list):
        return data["results"]

    values = [v for v in data.values() if isinstance(v, dict)]
    return values


def _workable_identifier_text(value):
    if value is None:
        return ""
    if not isinstance(value, (str, int)):
        raise ValueError("unsupported Workable stable identifier")
    return str(value).strip()


def _workable_posting_token(value):
    url = _workable_identifier_text(value)
    if not url or any(character.isspace() for character in url):
        return ""

    try:
        parsed = urlsplit(url)
    except ValueError:
        return ""

    if parsed.scheme and parsed.scheme.lower() not in {"http", "https"}:
        return ""
    match = re.search(r"(?:^|/)j/([^/]+)(?:/|$)", parsed.path)
    return match.group(1).strip() if match else ""


def _workable_stable_id(job):
    shortcode = _workable_identifier_text(job.get("shortcode"))
    if shortcode:
        return shortcode

    for field_name in ("url", "shortlink", "application_url"):
        posting_token = _workable_posting_token(job.get(field_name))
        if posting_token:
            return posting_token

    for field_name in ("id", "code"):
        fallback = _workable_identifier_text(job.get(field_name))
        if fallback:
            return fallback

    return ""


def _fetch_company_outcome(company):

    jobs_data = []
    page_count = 0
    url = WORKABLE_PUBLIC_ACCOUNT_API.format(company)

    try:
        r = workable_get(
            url,
            params={"details": "true"},
            headers={"Accept": "application/json"},
            timeout=10,
        )
    except Exception:
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason="transport_error",
            page_count=page_count,
        )

    if r is None or r.status_code != 200:
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason="non_200_response",
            page_count=page_count,
        )

    try:
        data = r.json()
    except Exception:
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason="malformed_payload",
            page_count=page_count,
        )

    if (
        not isinstance(data, dict)
        or "jobs" not in data
        or not isinstance(data.get("jobs"), list)
    ):
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason="malformed_payload",
            page_count=page_count,
        )

    jobs_data = data.get("jobs", [])
    if not all(isinstance(job, dict) for job in jobs_data):
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason="malformed_payload",
            page_count=page_count,
            raw_job_count=len(jobs_data),
        )

    page_count = 1
    jobs = []

    try:
        for job in jobs_data:

            city = str(job.get("city") or "").strip()
            state = str(job.get("state") or "").strip()
            country = str(job.get("country") or "").strip()

            location = ", ".join(
                part
                for part in (city, state, country)
                if part
            )

            shortcode = str(job.get("shortcode") or "").strip()

            url = (
                job.get("url")
                or job.get("shortlink")
                or job.get("application_url")
            )

            if not url and shortcode:
                url = (
                    f"https://apply.workable.com/"
                    f"{company}/j/{shortcode}/"
                )

            learn_from_job_url(url)

            workable_id = _workable_stable_id(job)

            jobs.append(
                Job(
                    company=company,
                    title=job.get("title"),
                    location=location,
                    url=url,
                    source="workable",
                    posted_at=(
                        job.get("published_on")
                        or job.get("created_at")
                        or job.get("published")
                    ),
                    meta={
                        "_shortcode": shortcode,
                    },
                    job_id=(
                        f"wb_{workable_id}"
                        if workable_id
                        else None
                    ),
                ).to_dict()
            )

    except Exception:
        status = (
            AcquisitionStatus.PARTIAL
            if jobs
            else AcquisitionStatus.FAILED
        )
        return AcquisitionOutcome(
            company,
            status,
            tuple(jobs),
            reason="parse_error",
            page_count=page_count,
            raw_job_count=len(jobs_data),
        )

    missing_jobs = [
        job
        for job in jobs
        if not job.get("posted_at")
        and job.get("_shortcode")
    ]

    if missing_jobs:
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_job = {
                executor.submit(
                    fetch_workable_timestamp,
                    job["company"],
                    job["_shortcode"],
                ): job
                for job in missing_jobs
            }

            for future in as_completed(future_to_job):
                job = future_to_job[future]

                try:
                    timestamp = future.result()
                    if timestamp:
                        job["posted_at"] = timestamp
                except Exception:
                    pass

    for job in jobs:
        job.pop("_shortcode", None)

    status = (
        AcquisitionStatus.SUCCESS
        if jobs
        else AcquisitionStatus.EMPTY
    )

    return AcquisitionOutcome(
        company,
        status,
        tuple(jobs),
        page_count=page_count,
        raw_job_count=len(jobs_data),
    )


def validate_workable_companies(companies):

    valid = []

    normalized = sorted(
        {
            slug
            for company in companies
            for slug in [normalize_workable_slug(company)]
            if slug
        }
    )

    for company in normalized:
        outcome = _fetch_company_outcome(company)

        if outcome.status in {
            AcquisitionStatus.SUCCESS,
            AcquisitionStatus.EMPTY,
        }:
            valid.append(company)

    return valid


def fetch_company_jobs(company):
    return list(_fetch_company_outcome(company).jobs)


def _fetch_company_result(company):
    return [
        observe_acquisition(
            "workable",
            lambda: _fetch_company_outcome(company),
            schedule_on_success=True,
            company=company,
        )
    ]


def scrape_all_workable():

    companies = load_lines("discovery://ats/workable")
    schedule = load_schedule()

    companies = [
        c for c in companies
        if should_scrape(c, schedule)
    ]

    # remove duplicates
    companies = sorted(set(companies))
    results = run_parallel(
        companies,
        _fetch_company_result,
        max_workers=5,
        desc="Workable scraping"
        )
    
    all_jobs = []
    for outcome in results:
        all_jobs.extend(outcome.jobs)

        if outcome.should_mark_scraped:
            mark_scraped(outcome.company, schedule)

    save_schedule(schedule)
    
    return all_jobs
