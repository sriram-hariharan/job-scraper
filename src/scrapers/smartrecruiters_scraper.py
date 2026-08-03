from threading import local

import requests
from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.parallel import run_parallel
from src.utils.logging import get_logger
from src.discovery.learned_companies import learn_from_job_url
from src.discovery.crawl_scheduler import AcquisitionOutcome, AcquisitionStatus
from src.utils.http_retry import http_get
from src.utils.pipeline_metrics import observe_acquisition

logger = get_logger("smartrecruiters")

API = "https://jobs.smartrecruiters.com/sr-jobs/search?limit=100"
COMPANY_API = "https://api.smartrecruiters.com/v1/companies/{company}/postings"
_thread_outcome = local()


def _return_jobs(company, status, jobs=(), *, reason="", raw_job_count=None, page_count=None):
    outcome = AcquisitionOutcome(
        company,
        status,
        tuple(jobs),
        reason=reason,
        raw_job_count=raw_job_count,
        page_count=page_count,
    )
    _thread_outcome.value = outcome
    return list(outcome.jobs)


def _capture_public_outcome(company, fetch):
    _thread_outcome.value = None
    jobs = fetch()
    outcome = getattr(_thread_outcome, "value", None)
    if isinstance(outcome, AcquisitionOutcome):
        return outcome
    rows = tuple(jobs or ())
    status = AcquisitionStatus.SUCCESS if rows else AcquisitionStatus.EMPTY
    return AcquisitionOutcome(company, status, rows, raw_job_count=len(rows))


def fetch_company_board(company):

    url = COMPANY_API.format(company=company)

    try:
        r = http_get(url, timeout=10)
    except Exception:
        return _return_jobs(
            company, AcquisitionStatus.FAILED, reason="transport_error"
        )

    if r is None or r.status_code != 200:
        return _return_jobs(
            company, AcquisitionStatus.FAILED, reason="non_200_response"
        )

    try:
        data = r.json()
    except Exception:
        return _return_jobs(
            company, AcquisitionStatus.FAILED, reason="malformed_payload"
        )

    if not isinstance(data, dict) or not isinstance(data.get("content"), list):
        return _return_jobs(
            company,
            AcquisitionStatus.FAILED,
            reason="malformed_payload",
            page_count=1,
        )

    postings = data.get("content", [])

    jobs = []

    for job in postings:

        title = job.get("name", "")

        location_obj = job.get("location", {})
        location = (
            location_obj.get("city")
            or location_obj.get("region")
            or location_obj.get("country")
            or ""
        )

        sr_id = job.get("id")
        if not sr_id:
            continue

        identifier = job.get("company", {}).get("identifier")
        if not identifier:
            continue

        job_url = f"https://jobs.smartrecruiters.com/{identifier}/{sr_id}"

        learn_from_job_url(job_url)

        jobs.append(
            Job(
                company=company,
                title=title,
                location=location,
                url=job_url,
                source="smartrecruiters",
                posted_at=job.get("releasedDate"),
                job_id=f"sr_{sr_id}" if sr_id else None
            ).to_dict()
        )

    status = AcquisitionStatus.SUCCESS if jobs else AcquisitionStatus.EMPTY
    return _return_jobs(
        company,
        status,
        jobs,
        raw_job_count=len(postings),
        page_count=1,
    )


def fetch_company_jobs(company):

    outcome_company = "<global_feed>"
    url = API.format(company=company)

    try:
        r = http_get(url, timeout=10)
    except Exception:
        return _return_jobs(
            outcome_company, AcquisitionStatus.FAILED, reason="transport_error"
        )

    if r is None or r.status_code != 200:
        return _return_jobs(
            outcome_company, AcquisitionStatus.FAILED, reason="non_200_response"
        )

    try:
        data = r.json()
    except Exception:
        return _return_jobs(
            outcome_company, AcquisitionStatus.FAILED, reason="malformed_payload"
        )

    if not isinstance(data, dict) or not isinstance(data.get("content"), list):
        return _return_jobs(
            outcome_company,
            AcquisitionStatus.FAILED,
            reason="malformed_payload",
            page_count=1,
        )

    postings = data.get("content", [])

    jobs = []
    for job in postings:

        title = job.get("name", "")

        location_obj = job.get("location", {})
        location = (
            location_obj.get("city")
            or location_obj.get("region")
            or location_obj.get("country")
            or ""
        )

        job_url = job.get("applyUrl")
        sr_id = job.get("id")
        if not job_url:
            continue

        # discovery learning
        learn_from_job_url(job_url)

        company_slug = job.get("company", {}).get("identifier", company)

        jobs.append(
            Job(
                company=company_slug,
                title=title,
                location=location,
                url=job_url,
                source="smartrecruiters",
                posted_at=job.get("releasedDate"),
                job_id=f"sr_{sr_id}" if sr_id else None
            ).to_dict()
        )

    status = AcquisitionStatus.SUCCESS if jobs else AcquisitionStatus.EMPTY
    return _return_jobs(
        outcome_company,
        status,
        jobs,
        raw_job_count=len(postings),
        page_count=1,
    )


def _fetch_company_board_result(company):
    outcome = observe_acquisition(
        "smartrecruiters",
        lambda: _capture_public_outcome(
            company,
            lambda: fetch_company_board(company),
        ),
        schedule_on_success=False,
        company=company,
    )
    jobs = list(outcome.jobs)
    return [(company, jobs)] if jobs else []


def scrape_all_smartrecruiters():

    all_jobs = []

    # -------------------------
    # 1. GLOBAL FEED SCRAPE
    # -------------------------
    try:
        feed_outcome = observe_acquisition(
            "smartrecruiters",
            lambda: _capture_public_outcome(
                "<global_feed>",
                lambda: fetch_company_jobs(None),
            ),
            schedule_on_success=False,
            company="<global_feed>",
        )
        all_jobs.extend(feed_outcome.jobs)

    except Exception as e:
        logger.warning(f"SmartRecruiters feed failed: {e}")

    # -------------------------
    # 2. COMPANY BOARD SCRAPE
    # -------------------------
    companies = load_lines("discovery://ats/smartrecruiters")
    companies = list(set(companies))

    results = run_parallel(
        companies,
        _fetch_company_board_result,
        max_workers=20,
        desc="SmartRecruiters boards"
    )

    for _, jobs in results:
        if isinstance(jobs, list):
            all_jobs.extend(jobs)

    return all_jobs
