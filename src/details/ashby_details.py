import html
import re
from typing import Any, Dict, Optional, Tuple

from bs4 import BeautifulSoup

from src.config.consts import ASHBY_DETAIL_QUERY, ASHBY_URL
from src.utils.http_retry import http_post
from src.utils.logging import get_logger

logger = get_logger("ashby_details")

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


def fetch_ashby_details(job: Dict[str, Any]) -> Dict[str, Any]:
    company, job_id = _extract_ashby_identifiers(job)

    if not company or not job_id:
        job["_details_fetched"] = "failed"
        return job

    payload = {
        "operationName": "ApiJobPosting",
        "query": ASHBY_DETAIL_QUERY,
        "variables": {
            "organizationHostedJobsPageName": company,
            "jobPostingId": job_id,
        },
    }

    try:
        response = http_post(
            ASHBY_URL,
            json=payload,
            headers=HEADERS,
            timeout=10,
        )
    except Exception:
        logger.warning("Ashby detail request failed: %s %s", company, job_id)
        job["_details_fetched"] = "failed"
        return job

    if response is None or response.status_code != 200:
        job["_details_fetched"] = "failed"
        return job

    try:
        data = response.json()
    except Exception:
        job["_details_fetched"] = "failed"
        return job

    description_html, description_text = _extract_description_from_response(data)
    if not description_text:
        job["_details_fetched"] = "ashby_no_description"
        return job

    job["description_html"] = description_html
    job["description_text"] = description_text
    job["_details_fetched"] = "ashby_api"
    return job
