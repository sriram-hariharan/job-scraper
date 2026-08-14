from threading import local

import requests
from models.job import Job
from src.config.consts import (
    SMARTRECRUITERS_MAX_COMPANY_PAGES,
    SMARTRECRUITERS_PAGE_SIZE,
)
from src.utils.file_loader import load_lines
from src.utils.parallel import run_parallel
from src.utils.logging import get_logger
from src.discovery.learned_companies import learn_from_job_url
from src.discovery.crawl_scheduler import AcquisitionOutcome, AcquisitionStatus
from src.utils.http_retry import http_get
from src.utils.pipeline_metrics import observe_acquisition

logger = get_logger("smartrecruiters")

API = "https://jobs.smartrecruiters.com/sr-jobs/search"
COMPANY_API = "https://api.smartrecruiters.com/v1/companies/{company}/postings"
_thread_outcome = local()


class _MalformedPayload(ValueError):
    pass


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


def _strict_int(value, *, positive=False):
    if isinstance(value, bool) or not isinstance(value, int):
        raise _MalformedPayload("invalid pagination metadata")
    if value < (1 if positive else 0):
        raise _MalformedPayload("invalid pagination metadata")
    return value


def _parse_page(response, *, requested_offset, global_feed=False):
    try:
        data = response.json()
    except Exception:
        raise _MalformedPayload("invalid JSON") from None
    if not isinstance(data, dict):
        raise _MalformedPayload("invalid response root")

    postings = data.get("content")
    if not isinstance(postings, list) or len(postings) > SMARTRECRUITERS_PAGE_SIZE:
        raise _MalformedPayload("invalid content")
    offset = _strict_int(data.get("offset"))
    limit = _strict_int(data.get("limit"), positive=True)
    total = _strict_int(data.get("totalFound"))
    if limit > SMARTRECRUITERS_PAGE_SIZE or len(postings) > limit:
        raise _MalformedPayload("invalid limit")
    expected_offset = 0 if global_feed else requested_offset
    if offset != expected_offset or offset + len(postings) > total:
        raise _MalformedPayload("inconsistent pagination")
    return postings, offset, limit, total


def _posting_id(posting):
    if not isinstance(posting, dict):
        return ""
    value = posting.get("id")
    if isinstance(value, bool) or value is None:
        return ""
    return str(value).strip()


def _normalize_posting(posting, *, company, global_feed):
    if not isinstance(posting, dict):
        return None
    sr_id = _posting_id(posting)
    if not sr_id:
        return None

    company_obj = posting.get("company")
    if not isinstance(company_obj, dict):
        return None
    identifier = company_obj.get("identifier")
    if not isinstance(identifier, str) or not identifier.strip():
        return None
    identifier = identifier.strip()

    location_obj = posting.get("location", {})
    if not isinstance(location_obj, dict):
        return None
    location = (
        location_obj.get("city")
        or location_obj.get("region")
        or location_obj.get("country")
        or ""
    )

    if global_feed:
        job_url = posting.get("applyUrl")
        if not isinstance(job_url, str) or not job_url.strip():
            return None
        job_url = job_url.strip()
        job_company = identifier
    else:
        job_url = f"https://jobs.smartrecruiters.com/{identifier}/{sr_id}"
        job_company = company

    try:
        return Job(
            company=job_company,
            title=posting.get("name", ""),
            location=location,
            url=job_url,
            source="smartrecruiters",
            posted_at=posting.get("releasedDate"),
            job_id=f"sr_{sr_id}",
        ).to_dict()
    except Exception:
        return None


def _learn_once(job_url):
    try:
        learn_from_job_url(job_url)
    except Exception:
        logger.warning("smartrecruiters_event discovery_learning_failed=true")


def _log_row_errors(count):
    if count:
        logger.info(
            "smartrecruiters_event row_normalization_parse_error_count=%s",
            count,
        )


def _finish_incomplete(company, jobs, reason, *, raw_job_count, page_count):
    if jobs:
        return _return_jobs(
            company,
            AcquisitionStatus.PARTIAL,
            jobs,
            reason=reason,
            raw_job_count=raw_job_count,
            page_count=page_count,
        )
    return _return_jobs(
        company,
        AcquisitionStatus.FAILED,
        reason=reason,
        raw_job_count=raw_job_count,
        page_count=page_count,
    )


def _normalize_unique_rows(postings, *, company, global_feed, seen_ids):
    jobs = []
    malformed_count = 0
    new_ids = set()
    for posting in postings:
        sr_id = _posting_id(posting)
        if not sr_id:
            malformed_count += 1
            continue
        if sr_id in seen_ids or sr_id in new_ids:
            continue
        job = _normalize_posting(posting, company=company, global_feed=global_feed)
        if job is None:
            malformed_count += 1
            continue
        new_ids.add(sr_id)
        jobs.append(job)
        _learn_once(job["url"])
    seen_ids.update(new_ids)
    return jobs, malformed_count, new_ids


def fetch_company_board(company):

    url = COMPANY_API.format(company=company)
    jobs = []
    seen_ids = set()
    page_fingerprints = set()
    raw_job_count = 0
    page_count = 0
    requested_offset = 0

    for page in range(1, SMARTRECRUITERS_MAX_COMPANY_PAGES + 1):
        try:
            response = http_get(
                url,
                params={"limit": SMARTRECRUITERS_PAGE_SIZE, "offset": requested_offset},
                timeout=10,
            )
        except Exception:
            reason = "transport_error" if page == 1 else "pagination_interrupted"
            return _finish_incomplete(
                company,
                jobs,
                reason,
                raw_job_count=raw_job_count,
                page_count=page_count,
            )
        if response is None or response.status_code != 200:
            reason = "non_200_response" if page == 1 else "pagination_interrupted"
            return _finish_incomplete(
                company,
                jobs,
                reason,
                raw_job_count=raw_job_count,
                page_count=page_count,
            )
        try:
            postings, offset, _limit, total = _parse_page(
                response, requested_offset=requested_offset
            )
        except _MalformedPayload:
            reason = "malformed_payload" if page == 1 else "pagination_interrupted"
            return _finish_incomplete(
                company,
                jobs,
                reason,
                raw_job_count=raw_job_count,
                page_count=page_count,
            )

        page_count += 1
        raw_job_count += len(postings)
        page_ids = tuple(_posting_id(posting) for posting in postings)
        fingerprint = (len(postings), page_ids)
        has_more = offset + len(postings) < total
        if has_more and fingerprint in page_fingerprints:
            return _finish_incomplete(
                company,
                jobs,
                "pagination_no_progress",
                raw_job_count=raw_job_count,
                page_count=page_count,
            )
        page_fingerprints.add(fingerprint)

        page_jobs, page_malformed, new_ids = _normalize_unique_rows(
            postings,
            company=company,
            global_feed=False,
            seen_ids=seen_ids,
        )
        jobs.extend(page_jobs)
        _log_row_errors(page_malformed)

        if has_more and not new_ids:
            return _finish_incomplete(
                company,
                jobs,
                "pagination_no_progress",
                raw_job_count=raw_job_count,
                page_count=page_count,
            )
        if not has_more:
            break
        if page == SMARTRECRUITERS_MAX_COMPANY_PAGES:
            return _finish_incomplete(
                company,
                jobs,
                "pagination_limit_reached",
                raw_job_count=raw_job_count,
                page_count=page_count,
            )
        requested_offset = offset + len(postings)

    if not jobs and raw_job_count:
        return _return_jobs(
            company,
            AcquisitionStatus.FAILED,
            reason="parse_error",
            raw_job_count=raw_job_count,
            page_count=page_count,
        )
    status = AcquisitionStatus.SUCCESS if jobs else AcquisitionStatus.EMPTY
    return _return_jobs(
        company,
        status,
        jobs,
        raw_job_count=raw_job_count,
        page_count=page_count,
    )


def fetch_company_jobs(company):

    outcome_company = "<global_feed>"
    url = API

    try:
        r = http_get(
            url,
            params={"limit": SMARTRECRUITERS_PAGE_SIZE},
            timeout=10,
        )
    except Exception:
        return _return_jobs(
            outcome_company, AcquisitionStatus.FAILED, reason="transport_error"
        )

    if r is None or r.status_code != 200:
        return _return_jobs(
            outcome_company, AcquisitionStatus.FAILED, reason="non_200_response"
        )

    try:
        postings, offset, _limit, total = _parse_page(
            r, requested_offset=0, global_feed=True
        )
    except _MalformedPayload:
        return _return_jobs(
            outcome_company,
            AcquisitionStatus.FAILED,
            reason="malformed_payload",
            page_count=1,
        )

    seen_ids = set()
    jobs, malformed_count, _new_ids = _normalize_unique_rows(
        postings,
        company=company,
        global_feed=True,
        seen_ids=seen_ids,
    )
    _log_row_errors(malformed_count)
    if not jobs and postings:
        return _return_jobs(
            outcome_company,
            AcquisitionStatus.FAILED,
            reason="parse_error",
            raw_job_count=len(postings),
            page_count=1,
        )
    if offset + len(postings) < total and jobs:
        return _return_jobs(
            outcome_company,
            AcquisitionStatus.PARTIAL,
            jobs,
            reason="pagination_limit_reached",
            raw_job_count=len(postings),
            page_count=1,
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
