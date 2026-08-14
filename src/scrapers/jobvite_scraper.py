import requests
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup
from src.utils.html_timestamp_extractor import (
    extract_jsonld_dateposted,
    extract_jsonld_jobposting_metadata,
)
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

JOBVITE_BASE_URL = "https://jobs.jobvite.com"
_AMBIGUOUS_LOCATION_COUNT_RE = re.compile(r"^\d+\s+locations?$", re.I)
_AMBIGUOUS_LOCATION_PLACEHOLDERS = {
    "multiple locations",
    "n/a",
    "not specified",
    "remote",
    "see job description",
    "various locations",
}
_JOBVITE_COMPANY_PATTERN = re.compile(
    r"^[a-z0-9](?:[a-z0-9_-]*[a-z0-9])?$"
)
_JOBVITE_RESERVED_COMPANIES = {"www", "jobs", "job", "careers", "apply"}

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

@retry_request(retries=2)
def jobvite_get(url, **kwargs):
    return session.get(url, **kwargs)


def _normalize_jobvite_company(value):
    company = str(value or "").strip().lower()
    if not company:
        return None
    if company in _JOBVITE_RESERVED_COMPANIES:
        return None
    return company if _JOBVITE_COMPANY_PATTERN.fullmatch(company) else None

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


def _clean_listing_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _ambiguous_listing_location(value):
    normalized = _clean_listing_text(value)
    return (
        not normalized
        or normalized.lower() in _AMBIGUOUS_LOCATION_PLACEHOLDERS
        or bool(_AMBIGUOUS_LOCATION_COUNT_RE.fullmatch(normalized))
    )


def _jobvite_id(job_url):
    path = urlsplit(str(job_url or "")).path
    if "/job/" not in path:
        return ""
    return path.split("/job/", 1)[1].split("/", 1)[0].strip()


def _listing_container(link):
    featured = link.find_parent("div", class_="jv-featured-job")
    if featured is not None:
        return featured

    row = link.find_parent("li", class_="row")
    if row is not None and row.find_parent("div", class_="jv-job-list") is not None:
        return row

    return link.find_parent("div")


def _listing_title_location(link, container):
    values = []
    for value in link.stripped_strings:
        clean = _clean_listing_text(value)
        if clean and clean.lower() != "new" and clean not in values:
            values.append(clean)

    if not values and container is not None:
        for value in container.stripped_strings:
            clean = _clean_listing_text(value)
            if clean and clean.lower() != "new" and clean not in values:
                values.append(clean)

    title = values[0] if values else ""
    location = values[1] if len(values) > 1 else ""
    if "|" in location:
        location = location.split("|", 1)[0]
    location = _clean_listing_text(location)
    if location == title:
        location = ""
    return title, location


def parse_jobvite_listing(page_html):
    soup = BeautifulSoup(page_html or "", "html.parser")
    records = []
    seen_urls = set()

    for link in soup.select('a[href*="/job/"]'):
        job_url = urljoin(JOBVITE_BASE_URL, str(link.get("href") or "").strip())
        job_id = _jobvite_id(job_url)
        if not job_id or job_url in seen_urls:
            continue
        seen_urls.add(job_url)

        container = _listing_container(link)
        title, location = _listing_title_location(link, container)
        if not title:
            continue
        records.append(
            {
                "title": title,
                "location": location,
                "url": job_url,
                "jobvite_id": job_id,
                "is_new": bool(
                    container is not None
                    and container.find("span", class_="jv-tag-new") is not None
                ),
            }
        )

    return records


def validate_jobvite_company(company):
    company = _normalize_jobvite_company(company)
    if not company:
        return False

    for pattern in JOBVITE_URL_PATTERNS:
        try:
            response = jobvite_get(pattern.format(company=company), timeout=10)
            if response is None or response.status_code != 200:
                continue
            html = response.text
            if not isinstance(html, str) or not html:
                continue
            if parse_jobvite_listing(html):
                return True
        except Exception:
            continue

    return False


def validate_jobvite_companies(companies):
    normalized = sorted(
        {
            company
            for value in companies
            for company in [_normalize_jobvite_company(value)]
            if company
        }
    )
    return [
        company
        for company in normalized
        if validate_jobvite_company(company)
    ]


def fetch_jobvite_metadata_result(job_url):
    result = {
        "posted_at": None,
        "locations": [],
        "job_location_type": "",
        "applicant_location_requirements": [],
        "marker": "jobvite_metadata_request_failed",
        "status_code": None,
    }
    try:
        response = jobvite_get(job_url, timeout=10)
    except Exception:
        return result

    result["status_code"] = getattr(response, "status_code", None)
    if response is None or response.status_code != 200:
        return result

    metadata = extract_jsonld_jobposting_metadata(response.text)
    result.update(metadata)
    result["marker"] = (
        "" if metadata["posted_at"] or metadata["locations"] else "jobvite_metadata_missing"
    )
    return result

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

    try:
        records = parse_jobvite_listing(str(soup))
        for record in records:
            job_url = record["url"]
            learn_from_job_url(job_url)
            posted_at = None
            location = record["location"]
            metadata_source = "listing"
            if _ambiguous_listing_location(location):
                metadata = fetch_jobvite_metadata_result(job_url)
                posted_at = metadata["posted_at"]
                if metadata["locations"]:
                    location = (
                        metadata["locations"][0]
                        if len(metadata["locations"]) == 1
                        else metadata["locations"]
                    )
                metadata_source = (
                    "detail_fallback"
                    if not _ambiguous_listing_location(location)
                    else "unresolved"
                )

            jobs.append(
                Job(
                    company=company,
                    title=record["title"],
                    location=location,
                    url=job_url,
                    source="jobvite",
                    posted_at=posted_at,
                    meta={
                        "is_new": record["is_new"],
                        "_jobvite_metadata_source": metadata_source,
                    },
                    job_id=f"jv_{record['jobvite_id']}",
                ).to_dict()
            )
    except Exception:
        status = AcquisitionStatus.PARTIAL if jobs else AcquisitionStatus.FAILED
        return AcquisitionOutcome(
            company,
            status,
            tuple(jobs),
            reason="parse_error",
            raw_job_count=len(records) if "records" in locals() else 0,
        )

    status = AcquisitionStatus.SUCCESS if jobs else AcquisitionStatus.EMPTY
    return AcquisitionOutcome(
        company,
        status,
        tuple(jobs),
        raw_job_count=len(records),
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
