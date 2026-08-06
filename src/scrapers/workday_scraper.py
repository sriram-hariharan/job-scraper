import requests
import time

from src.utils.http_retry import retry_request
from src.config.consts import (
    WORKDAY_API_URL_TEMPLATE,
    WORKDAY_MAX_PAGES,
    WORKDAY_ORIGIN_TEMPLATE,
    WORKDAY_PAGE_SIZE,
)

from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.parallel import run_parallel
from src.utils.logging import get_logger
from src.discovery.learned_companies import learn_from_job_url
from src.utils.url_normalizer import normalize_workday_url
from src.utils.pipeline_metrics import observe_acquisition
from src.discovery.crawl_scheduler import (
    AcquisitionOutcome,
    AcquisitionStatus,
    load_schedule,
    save_schedule,
    should_scrape,
    mark_scraped
)

logger = get_logger("workday")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


@retry_request(retries=2)
def workday_post(url, **kwargs):
    return session.post(url, **kwargs)


def _workday_completed_outcome(company, jobs, page_count, raw_job_count=None):
    status = AcquisitionStatus.SUCCESS if jobs else AcquisitionStatus.EMPTY
    return AcquisitionOutcome(
        company,
        status,
        tuple(jobs),
        page_count=page_count,
        raw_job_count=raw_job_count,
    )


def _workday_interrupted_outcome(
    company, jobs, reason, page_count, raw_job_count=None
):
    status = AcquisitionStatus.PARTIAL if jobs else AcquisitionStatus.FAILED
    if status is AcquisitionStatus.PARTIAL and reason in {
        "transport_error",
        "non_200_response",
        "malformed_payload",
    }:
        reason = "pagination_interrupted"
    return AcquisitionOutcome(
        company,
        status,
        tuple(jobs),
        reason=reason,
        page_count=page_count,
        raw_job_count=raw_job_count,
    )


def _workday_page(data):
    if not isinstance(data, dict):
        raise ValueError("malformed Workday payload")

    total = None
    if "total" in data:
        total = data.get("total")
        if isinstance(total, bool) or not isinstance(total, int) or total < 0:
            raise ValueError("malformed Workday total")

    posting_values = [
        data.get(key)
        for key in ("jobPostings", "jobs", "items")
        if key in data
    ]
    if not posting_values:
        raise ValueError("missing Workday postings")

    postings = next((value for value in posting_values if value), posting_values[0])
    if isinstance(postings, dict):
        postings = postings.get("postings")

    if not isinstance(postings, list) or not all(
        isinstance(job, dict) for job in postings
    ):
        raise ValueError("malformed Workday postings")

    return total, postings


def _scrape_company_outcome(board_url):

    if not isinstance(board_url, str) or not board_url.strip():
        return AcquisitionOutcome(
            "<invalid_workday_board>",
            AcquisitionStatus.FAILED,
            reason="parse_error",
            page_count=0,
        )

    seen_jobs = set()
    seen_page_signatures = set()
    seen_provider_ids = set()

    host_part = board_url.split(".myworkdayjobs.com")[0]
    host = host_part.replace("https://", "")
    tenant = host.split(".")[0]

    site = ""
    if ".myworkdayjobs.com/" in board_url:
        site = board_url.split(".myworkdayjobs.com/", 1)[1].split("?")[0].strip("/")

    if not site:
        return AcquisitionOutcome(
            board_url,
            AcquisitionStatus.FAILED,
            reason="parse_error",
            page_count=0,
        )

    api_url = WORKDAY_API_URL_TEMPLATE.format(
        host=host,
        tenant=tenant,
        site=site
    )

    origin = WORKDAY_ORIGIN_TEMPLATE.format(host=host)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0",
        "Origin": origin,
        "Referer": board_url,
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
    }

    jobs = []
    offset = 0
    limit = WORKDAY_PAGE_SIZE
    advisory_total = None

    page_count = 0
    raw_job_count = 0

    while True:

        if page_count >= WORKDAY_MAX_PAGES:
            return _workday_interrupted_outcome(
                board_url, jobs, "pagination_limit_reached", page_count, raw_job_count
            )

        payload = {
            "limit": limit,
            "offset": offset,
            "searchText": ""
        }

        try:
            r = workday_post(api_url, json=payload, headers=headers, timeout=10)
        except Exception:
            return _workday_interrupted_outcome(
                board_url, jobs, "transport_error", page_count, raw_job_count
            )

        if r is None or r.status_code != 200:
            return _workday_interrupted_outcome(
                board_url, jobs, "non_200_response", page_count, raw_job_count
            )

        try:
            data = r.json()
        except Exception:
            return _workday_interrupted_outcome(
                board_url, jobs, "malformed_payload", page_count, raw_job_count
            )

        try:
            page_total, postings = _workday_page(data)
        except ValueError:
            return _workday_interrupted_outcome(
                board_url, jobs, "malformed_payload", page_count, raw_job_count
            )

        page_count += 1
        raw_job_count += len(postings)

        if advisory_total is None and not (page_total == 0 and postings):
            advisory_total = page_total

        if not postings:
            if advisory_total is not None and offset < advisory_total:
                return _workday_interrupted_outcome(
                    board_url,
                    jobs,
                    "pagination_no_progress",
                    page_count,
                    raw_job_count,
                )
            return _workday_completed_outcome(
                board_url, jobs, page_count, raw_job_count
            )

        page_ids = tuple(
            job.get("externalPath")
            for job in postings
            if isinstance(job.get("externalPath"), str)
            and job.get("externalPath")
        )
        page_signature = page_ids
        new_provider_ids = set(page_ids) - seen_provider_ids

        if page_signature in seen_page_signatures or not new_provider_ids:
            return _workday_interrupted_outcome(
                board_url, jobs, "pagination_no_progress", page_count, raw_job_count
            )

        seen_page_signatures.add(page_signature)
        seen_provider_ids.update(new_provider_ids)

        for job in postings:

            job_id = job.get("externalPath")

            if not job_id:
                continue

            if not isinstance(job_id, str):
                return _workday_interrupted_outcome(
                    board_url, jobs, "parse_error", page_count, raw_job_count
                )

            if job_id in seen_jobs:
                continue

            title = job.get("title")

            primary_location = (
                job.get("location")
                or job.get("locationsText")
            )

            additional_locations = job.get("additionalLocations") or []

            locations = []

            if primary_location:
                locations.append(primary_location)

            if isinstance(additional_locations, list):
                locations.extend(additional_locations)

            if not locations and job.get("locationsText"):
                locations.append(job.get("locationsText"))

            seen_jobs.add(job_id)

            info = job.get("jobPostingInfo", {})
            if not isinstance(info, dict):
                return _workday_interrupted_outcome(
                    board_url, jobs, "parse_error", page_count, raw_job_count
                )

            posted_at = (
                info.get("startDate")
                or job.get("startDate")
                or info.get("postedOn")
                or job.get("postedOn")
                or job.get("postedDate")
                or job.get("postedAt")
                or job.get("createdDate")
                or job.get("createdAt")
            )

            job_url = f"{board_url.rstrip('/')}/{job_id.lstrip('/')}"
            try:
                normalized = normalize_workday_url(job_url)

                if normalized:
                    learn_from_job_url(normalized)
            except Exception:
                return _workday_interrupted_outcome(
                    board_url, jobs, "parse_error", page_count, raw_job_count
                )

            job_req_id = None
            if job_url:
                job_req_id = job_url.split("/")[-1]

            try:
                jobs.append(
                    Job(
                        title=title,
                        location=locations,
                        url=job_url,
                        company=tenant,
                        source="workday",
                        posted_at=posted_at,
                        meta={
                            "_externalPath": job.get("externalPath"),
                            "_board_url": board_url
                        },
                        job_id=f"wd_{job_req_id}"
                    ).to_dict()
                )
            except Exception:
                return _workday_interrupted_outcome(
                    board_url, jobs, "parse_error", page_count, raw_job_count
                )

        offset = offset + len(postings)

        if (
            advisory_total is not None
            and advisory_total < WORKDAY_PAGE_SIZE * WORKDAY_MAX_PAGES
            and offset >= advisory_total
        ):
            return _workday_completed_outcome(
                board_url, jobs, page_count, raw_job_count
            )

        if advisory_total is None and len(postings) < limit:
            return _workday_completed_outcome(
                board_url, jobs, page_count, raw_job_count
            )

        if page_count >= WORKDAY_MAX_PAGES:
            return _workday_interrupted_outcome(
                board_url,
                jobs,
                "pagination_limit_reached",
                page_count,
                raw_job_count,
            )

        time.sleep(0.01)

    return _workday_completed_outcome(
        board_url, jobs, page_count, raw_job_count
    )


def scrape_company(board_url):
    return list(_scrape_company_outcome(board_url).jobs)


def _scrape_company_result(company):
    return [
        observe_acquisition(
            "workday",
            lambda: _scrape_company_outcome(company),
            schedule_on_success=True,
            company=company,
        )
    ]


def scrape_all_workday():

    companies = load_lines("discovery://ats/workday")
    schedule = load_schedule()

    companies = [
        c for c in companies
        if should_scrape(c, schedule)
    ]

    results = run_parallel(
        companies,
        _scrape_company_result,
        max_workers=5,
        desc="Workday scraping"
    )
    all_jobs = []

    for outcome in results:
        all_jobs.extend(outcome.jobs)

        if outcome.should_mark_scraped:
            mark_scraped(outcome.company, schedule)

    save_schedule(schedule)
    return all_jobs
