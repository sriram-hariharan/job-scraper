import requests
from bs4 import BeautifulSoup
from src.utils.html_timestamp_extractor import extract_jsonld_dateposted
from src.utils.http_retry import retry_request
from src.utils.pipeline_metrics import observe_acquisition
from src.config.consts import JOBVITE_URL_PATTERNS
from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.parallel import run_parallel
from src.utils.logging import get_logger
from src.discovery.learned_companies import learn_from_job_url
from src.discovery.crawl_scheduler import (
    AcquisitionOutcome,
    AcquisitionStatus,
    load_schedule,
    save_schedule,
    should_scrape,
    mark_scraped
)

logger = get_logger("jobvite")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

@retry_request(retries=2)
def jobvite_get(url, **kwargs):
    return session.get(url, **kwargs)

def fetch_jobvite_posted_date(job_url):

    try:
        r = jobvite_get(job_url, timeout=10)
        if r is None or r.status_code != 200:
            return None
    except Exception:
        return None

    html = r.text

    # Use shared JSON-LD extractor
    ts = extract_jsonld_dateposted(html)

    return ts

def _fetch_company_outcome(company):

    urls = [u.format(company=company) for u in JOBVITE_URL_PATTERNS]
    html = None
    completed_request = False
    failure_reason = "non_200_response"

    for url in urls:

        try:
            r = jobvite_get(url, timeout=10)
        except Exception:
            failure_reason = "transport_error"
            continue

        if r is None or r.status_code != 200:
            continue
        completed_request = True
        html = r.text
        # if page actually contains jobs stop trying
        if "/job/" in html:
            break

    if not completed_request or not isinstance(html, str) or not html:
        logger.warning(f"{company} no jobvite page found")
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason=failure_reason if not completed_request else "malformed_payload",
        )

    try:
        soup = BeautifulSoup(html, "html.parser")
    except Exception:
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason="parse_error",
        )

    jobs = []
    raw_job_count = 0

    links = soup.find_all("a", href=True)

    seen_urls = set()

    try:
        for link in links:
            href = link["href"]
            if "/job/" not in href:
                continue

            job_url = href if href.startswith("http") else f"https://jobs.jobvite.com{href}"
            jobvite_id = job_url.split("/job/")[-1].split("?")[0]
            if job_url in seen_urls:
                continue

            seen_urls.add(job_url)
            raw_job_count += 1

            # find job container
            container = link.find_parent("div")

            is_new = False
            if container:
                if container.find("span", class_="jv-tag-new"):
                    is_new = True

            title = link.text.strip()

            learn_from_job_url(job_url)
            posted_at = None
            if is_new:
                posted_at = fetch_jobvite_posted_date(job_url)

            jobs.append(
                Job(
                    company=company,
                    title=title,
                    location="",
                    url=job_url,
                    source="jobvite",
                    posted_at=posted_at,
                    meta={
                        "is_new": is_new
                    },
                    job_id=f"jv_{jobvite_id}",
                ).to_dict()
            )
    except Exception:
        status = AcquisitionStatus.PARTIAL if jobs else AcquisitionStatus.FAILED
        return AcquisitionOutcome(
            company,
            status,
            tuple(jobs),
            reason="parse_error",
            raw_job_count=raw_job_count,
        )

    status = AcquisitionStatus.SUCCESS if jobs else AcquisitionStatus.EMPTY
    return AcquisitionOutcome(
        company,
        status,
        tuple(jobs),
        raw_job_count=raw_job_count,
    )


def fetch_company_jobs(company):
    return list(_fetch_company_outcome(company).jobs)


def _fetch_company_result(company):
    return [
        observe_acquisition(
            "jobvite",
            lambda: _fetch_company_outcome(company),
            schedule_on_success=True,
            company=company,
        )
    ]


def scrape_all_jobvite():

    companies = load_lines("discovery://ats/jobvite")
    schedule = load_schedule()

    companies = [
        c for c in companies
        if should_scrape(c, schedule)
    ]

    # remove duplicates
    companies = list(set(companies))
    results = run_parallel(
        companies,
        _fetch_company_result,
        max_workers=8,
        desc="Jobvite scraping"
        )
    
    all_jobs = []

    for outcome in results:
        all_jobs.extend(outcome.jobs)

        if outcome.should_mark_scraped:
            mark_scraped(outcome.company, schedule)

    save_schedule(schedule)

    return all_jobs
