import html
import re
import time
from typing import Any, Dict, Optional, Tuple

from bs4 import BeautifulSoup

from src.config.consts import ASHBY_DETAIL_QUERY, ASHBY_URL
from src.utils.http_retry import http_post
from src.utils.logging import get_logger

logger = get_logger("ashby_details")

ASHBY_DETAIL_RETRIES = 3
ASHBY_DETAIL_THROTTLE_SECONDS = 0.15
ASHBY_DETAIL_BACKOFF_SECONDS = 0.5

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "apollographql-client-name": "frontend_non_user",
    "apollographql-client-version": "0.1.0",
    "Origin": "https://jobs.ashbyhq.com",
    "Referer": "https://jobs.ashbyhq.com",
}


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _extract_ashby_identifiers(job: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    company = str(job.get("company") or "").strip() or None
    raw_job_id = (
        job.get("meta", {}).get("_job_id")
        if isinstance(job.get("meta"), dict)
        else None
    )
    raw_job_id = raw_job_id or job.get("job_id")
    job_id = str(raw_job_id or "").strip()

    if job_id.startswith("as_"):
        job_id = job_id[3:]

    url = str(job.get("url") or "").strip()
    match = re.search(r"jobs\.ashbyhq\.com/([^/?#]+)/([^/?#]+)", url)
    if match:
        company = company or match.group(1)
        job_id = job_id or match.group(2)

    return company, job_id or None


def _extract_description_from_response(data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    root = data.get("data") if isinstance(data, dict) else None
    posting = root.get("jobPosting") if isinstance(root, dict) else None
    if not isinstance(posting, dict):
        return None, None

    description_html = html.unescape(str(posting.get("descriptionHtml") or "")).strip()
    if not description_html:
        return None, None

    description_text = _clean_text(
        BeautifulSoup(description_html, "html.parser").get_text(" ", strip=True)
    )
    if not description_text:
        return None, None

    return description_html, description_text


def _mark_failure(
    job: Dict[str, Any],
    *,
    marker: str,
    company: Optional[str],
    job_id: Optional[str],
    status_code: Optional[int] = None,
) -> Dict[str, Any]:
    logger.warning(
        "Ashby detail fetch failed | company=%s | job_id=%s | status=%s | reason=%s",
        company or "",
        job_id or "",
        status_code if status_code is not None else "",
        marker,
    )
    job["_details_fetched"] = marker
    return job


def _post_ashby_detail_with_retry(
    payload: Dict[str, Any],
    *,
    company: str,
    job_id: str,
):
    last_response = None

    for attempt in range(ASHBY_DETAIL_RETRIES):
        if ASHBY_DETAIL_THROTTLE_SECONDS > 0:
            time.sleep(ASHBY_DETAIL_THROTTLE_SECONDS)

        try:
            response = http_post(
                ASHBY_URL,
                json=payload,
                headers=HEADERS,
                timeout=10,
            )
        except Exception:
            response = None

        last_response = response
        status_code = getattr(response, "status_code", None)
        if response is not None and status_code == 200:
            return response

        if attempt < ASHBY_DETAIL_RETRIES - 1:
            logger.info(
                "Retrying Ashby detail fetch | company=%s | job_id=%s | status=%s | attempt=%s",
                company,
                job_id,
                status_code if status_code is not None else "",
                attempt + 1,
            )
            time.sleep(ASHBY_DETAIL_BACKOFF_SECONDS * (attempt + 1))

    return last_response


def fetch_ashby_details(job: Dict[str, Any]) -> Dict[str, Any]:
    company, job_id = _extract_ashby_identifiers(job)

    if not company or not job_id:
        return _mark_failure(
            job,
            marker="ashby_request_failed",
            company=company,
            job_id=job_id,
        )

    payload = {
        "operationName": "ApiJobPosting",
        "query": ASHBY_DETAIL_QUERY,
        "variables": {
            "organizationHostedJobsPageName": company,
            "jobPostingId": job_id,
        },
    }

    response = _post_ashby_detail_with_retry(payload, company=company, job_id=job_id)
    if response is None or response.status_code != 200:
        return _mark_failure(
            job,
            marker="ashby_request_failed",
            company=company,
            job_id=job_id,
            status_code=getattr(response, "status_code", None),
        )

    try:
        data = response.json()
    except Exception:
        return _mark_failure(
            job,
            marker="ashby_parse_failed",
            company=company,
            job_id=job_id,
            status_code=response.status_code,
        )

    if not isinstance(data, dict):
        return _mark_failure(
            job,
            marker="ashby_parse_failed",
            company=company,
            job_id=job_id,
            status_code=response.status_code,
        )

    if data.get("errors"):
        return _mark_failure(
            job,
            marker="ashby_request_failed",
            company=company,
            job_id=job_id,
            status_code=response.status_code,
        )

    root = data.get("data")
    if not isinstance(root, dict) or not isinstance(root.get("jobPosting"), dict):
        return _mark_failure(
            job,
            marker="ashby_parse_failed",
            company=company,
            job_id=job_id,
            status_code=response.status_code,
        )

    description_html, description_text = _extract_description_from_response(data)
    if not description_text:
        logger.warning(
            "Ashby detail fetch empty body | company=%s | job_id=%s | status=%s | reason=%s",
            company,
            job_id,
            response.status_code,
            "ashby_no_description",
        )
        job["_details_fetched"] = "ashby_no_description"
        return job

    job["description_html"] = description_html
    job["description_text"] = description_text
    job["_details_fetched"] = "ashby_api"
    return job
