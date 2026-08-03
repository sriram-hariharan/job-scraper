import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.utils.http_retry import retry_request
from src.utils.pipeline_metrics import observe_acquisition
from src.config.consts import (
    WORKABLE_MAX_PAGES,
    WORKABLE_PAGE_SIZE,
    WORKABLE_V1_API,
    WORKABLE_V2_DETAIL_API,
    WORKABLE_V3_API,
)
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


def _workable_stable_id(job):
    value = job.get("id") or job.get("shortcode") or job.get("url")
    if value is None:
        return ""
    if not isinstance(value, (str, int)):
        raise ValueError("unsupported Workable stable identifier")
    return str(value).strip()


def _fetch_company_outcome(company):

    jobs_data = []
    v3_url = WORKABLE_V3_API.format(company)

    limit = WORKABLE_PAGE_SIZE
    offset = 0
    page_count = 0
    interruption_reason = ""
    seen_page_signatures = set()
    seen_provider_ids = set()

    while True:

        if page_count >= WORKABLE_MAX_PAGES:
            interruption_reason = "pagination_interrupted"
            break

        try:
            r = workable_post(
                v3_url,
                json={"limit": limit, "offset": offset},
                headers={"Content-Type": "application/json"},
                timeout=10
            )
        except Exception:
            interruption_reason = "transport_error"
            break

        if r is None or r.status_code != 200:
            interruption_reason = "non_200_response"
            break

        try:
            data = r.json()
        except Exception:
            interruption_reason = "malformed_payload"
            break

        if not isinstance(data, dict):
            interruption_reason = "malformed_payload"
            break

        postings = extract_v3_jobs(data)
        if not isinstance(postings, list) or not all(
            isinstance(job, dict) for job in postings
        ):
            interruption_reason = "malformed_payload"
            break

        page_count += 1

        if not postings:
            break

        try:
            page_ids = tuple(
                stable_id
                for stable_id in (_workable_stable_id(job) for job in postings)
                if stable_id
            )
        except (TypeError, ValueError):
            interruption_reason = "parse_error"
            break
        page_signature = page_ids
        new_provider_ids = set(page_ids) - seen_provider_ids

        if page_signature in seen_page_signatures or not new_provider_ids:
            interruption_reason = "pagination_interrupted"
            break

        seen_page_signatures.add(page_signature)
        seen_provider_ids.update(new_provider_ids)

        jobs_data.extend(postings)

        if len(postings) < limit:
            break

        offset += limit

    # fallback to v1 widget API
    if not jobs_data and not interruption_reason:

        v1_url = WORKABLE_V1_API.format(company)

        try:
            r = workable_get(v1_url, timeout=10)
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
            )
        page_count += 1
        interruption_reason = ""

    jobs = []

    try:
        for job in jobs_data:

            city = (job.get("city") or "").strip()
            state = (job.get("state") or "").strip()
            country = (job.get("country") or "").strip()

            location = ", ".join(p for p in [city, state, country] if p)
            if not location:
                location = country
            shortcode = job.get("shortcode")

            url = job.get("url")
            if not url and shortcode:
                url = f"https://apply.workable.com/{company}/j/{shortcode}/"
            learn_from_job_url(url)
            workable_id = job.get("id")
            if not workable_id and url:
                workable_id = url.split("/j/")[-1].split("/")[0]

            jobs.append(Job(
                company=company,
                title=job.get("title"),
                location=location,
                url=url,
                source="workable",
                posted_at=(
                    job.get("published")
                    or job.get("published_on")
                    or job.get("created_at")
                ),
                meta={
                    "_shortcode": shortcode
                },
                job_id=f"wb_{workable_id}" if workable_id else None
            ).to_dict())
    except Exception:
        status = AcquisitionStatus.PARTIAL if jobs else AcquisitionStatus.FAILED
        return AcquisitionOutcome(
            company,
            status,
            tuple(jobs),
            reason="parse_error",
            page_count=page_count,
            raw_job_count=len(jobs_data),
        )

    # resolve missing timestamps via v2 API
    missing_jobs = [
        j for j in jobs
        if not j.get("posted_at") and j.get("_shortcode")
        ]

    if missing_jobs:

        with ThreadPoolExecutor(max_workers=10) as executor:

            future_to_job = {
                executor.submit(
                    fetch_workable_timestamp,
                    job["company"],
                    job["_shortcode"]
                ): job
                for job in missing_jobs
            }

            for future in as_completed(future_to_job):

                job = future_to_job[future]

                try:
                    ts = future.result()
                    if ts:
                        job["posted_at"] = ts
                except Exception:
                    pass

    for job in jobs:
        job.pop("_shortcode", None)

    if interruption_reason:
        status = AcquisitionStatus.PARTIAL if jobs else AcquisitionStatus.FAILED
        reason = "pagination_interrupted" if jobs else interruption_reason
        return AcquisitionOutcome(
            company,
            status,
            tuple(jobs),
            reason=reason,
            page_count=page_count,
            raw_job_count=len(jobs_data),
        )

    status = AcquisitionStatus.SUCCESS if jobs else AcquisitionStatus.EMPTY
    return AcquisitionOutcome(
        company,
        status,
        tuple(jobs),
        page_count=page_count,
        raw_job_count=len(jobs_data),
    )


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
    companies = list(set(companies))
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
