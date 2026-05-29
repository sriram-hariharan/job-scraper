import html
import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import quote

from src.config.consts import LEVER_API
from src.utils.http_retry import http_get
from src.utils.logging import get_logger

logger = get_logger("lever_details")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: List[str] = []

    def handle_data(self, data: str) -> None:
        if data.strip():
            self._parts.append(data.strip())

    def get_text(self) -> str:
        return " ".join(self._parts)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _html_to_text(value: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(value or "")
    return _clean_text(html.unescape(parser.get_text()))


def _plain_to_html(value: str) -> str:
    paragraphs = [
        f"<p>{html.escape(part.strip())}</p>"
        for part in re.split(r"\n{2,}", value or "")
        if part.strip()
    ]
    return "".join(paragraphs)


def _extract_lever_identifiers(job: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    company = str(job.get("company") or "").strip() or None
    raw_job_id = str(job.get("job_id") or "").strip()

    if raw_job_id.startswith("lv_"):
        raw_job_id = raw_job_id[3:]
    elif raw_job_id.startswith("lever_"):
        raw_job_id = raw_job_id[6:]

    job_id = raw_job_id or None
    url = str(job.get("url") or job.get("job_url") or "").strip()

    match = re.search(r"(?:jobs|api)\.lever\.co/(?:v0/postings/)?([^/?#]+)/([^/?#]+)", url)
    if match:
        company = company or match.group(1)
        job_id = job_id or match.group(2)

    return company, job_id


def _list_section_html(section: Dict[str, Any]) -> str:
    heading = str(section.get("text") or "").strip()
    content = str(section.get("content") or "").strip()

    pieces = []
    if heading:
        pieces.append(f"<h3>{html.escape(heading)}</h3>")
    if content:
        pieces.append(content)
    return "".join(pieces)


def _list_section_text(section: Dict[str, Any]) -> str:
    heading = _clean_text(str(section.get("text") or ""))
    content = _html_to_text(str(section.get("content") or ""))
    return _clean_text(" ".join(part for part in [heading, content] if part))


def _extract_description_from_response(data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    if not isinstance(data, dict):
        return None, None

    html_parts: List[str] = []
    text_parts: List[str] = []

    description_html = str(data.get("description") or "").strip()
    description_plain = str(data.get("descriptionPlain") or "").strip()
    if description_html:
        html_parts.append(description_html)
        text_parts.append(_html_to_text(description_html))
    elif description_plain:
        html_parts.append(_plain_to_html(description_plain))
        text_parts.append(_clean_text(description_plain))

    lists = data.get("lists")
    if isinstance(lists, list):
        for section in lists:
            if not isinstance(section, dict):
                continue
            section_html = _list_section_html(section)
            section_text = _list_section_text(section)
            if section_html:
                html_parts.append(section_html)
            if section_text:
                text_parts.append(section_text)

    additional_html = str(data.get("additional") or "").strip()
    additional_plain = str(data.get("additionalPlain") or "").strip()
    if additional_html:
        html_parts.append(additional_html)
        text_parts.append(_html_to_text(additional_html))
    elif additional_plain:
        html_parts.append(_plain_to_html(additional_plain))
        text_parts.append(_clean_text(additional_plain))

    description_text = _clean_text(" ".join(part for part in text_parts if part))
    if not description_text:
        return None, None

    description_html = "".join(part for part in html_parts if part)
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
        "Lever detail fetch failed | company=%s | job_id=%s | status=%s | reason=%s",
        company or "",
        job_id or "",
        status_code if status_code is not None else "",
        marker,
    )
    job["_details_fetched"] = marker
    return job


def fetch_lever_details(job: Dict[str, Any]) -> Dict[str, Any]:
    company, job_id = _extract_lever_identifiers(job)

    if not company or not job_id:
        return _mark_failure(
            job,
            marker="lever_request_failed",
            company=company,
            job_id=job_id,
        )

    url = f"{LEVER_API}/{quote(company, safe='')}/{quote(job_id, safe='')}"

    try:
        response = http_get(url, headers=HEADERS, timeout=10)
    except Exception:
        response = None

    if response is None or response.status_code != 200:
        return _mark_failure(
            job,
            marker="lever_request_failed",
            company=company,
            job_id=job_id,
            status_code=getattr(response, "status_code", None),
        )

    try:
        data = response.json()
    except Exception:
        return _mark_failure(
            job,
            marker="lever_request_failed",
            company=company,
            job_id=job_id,
            status_code=response.status_code,
        )

    description_html, description_text = _extract_description_from_response(data)
    if not description_text:
        logger.warning(
            "Lever detail fetch empty body | company=%s | job_id=%s | status=%s | reason=%s",
            company,
            job_id,
            response.status_code,
            "lever_no_description",
        )
        job["_details_fetched"] = "lever_no_description"
        return job

    job["description_html"] = description_html
    job["description_text"] = description_text
    job["_details_fetched"] = "lever_api"
    return job
