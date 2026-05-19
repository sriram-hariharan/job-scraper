import html
import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple

from src.config.consts import WORKABLE_V2_DETAIL_API
from src.utils.http_retry import http_get
from src.utils.logging import get_logger

logger = get_logger("workable_details")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

DESCRIPTION_FIELDS = (
    "description",
    "description_html",
    "full_description",
    "requirements",
    "benefits",
    "job_description",
)


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


def workable_shortcode(job: Dict[str, Any]) -> str:
    shortcode = str(job.get("_shortcode") or "").strip()

    if not shortcode and isinstance(job.get("meta"), dict):
        shortcode = str(job.get("meta", {}).get("_shortcode") or "").strip()

    if not shortcode:
        job_id = str(job.get("job_id") or "").strip()
        if job_id.startswith("wb_"):
            job_id = job_id[3:]
        shortcode = job_id

    if not shortcode:
        url = str(job.get("url") or job.get("job_url") or "").strip()
        match = re.search(r"/j/([^/?#]+)/?", url)
        if match:
            shortcode = match.group(1)

    return shortcode


def _extract_html_text(value: Any) -> Tuple[str, str]:
    if value is None:
        return "", ""

    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return "", ""
        if "<" in raw and ">" in raw:
            return raw, _html_to_text(raw)
        return _plain_to_html(raw), _clean_text(raw)

    if isinstance(value, list):
        html_parts: List[str] = []
        text_parts: List[str] = []
        for item in value:
            item_html, item_text = _extract_html_text(item)
            if item_html:
                html_parts.append(item_html)
            if item_text:
                text_parts.append(item_text)
        return "".join(html_parts), _clean_text(" ".join(text_parts))

    if isinstance(value, dict):
        html_parts = []
        text_parts = []
        for key in ("title", "name", "text", "content", "description", "body"):
            item_html, item_text = _extract_html_text(value.get(key))
            if item_html:
                html_parts.append(item_html)
            if item_text:
                text_parts.append(item_text)
        return "".join(html_parts), _clean_text(" ".join(text_parts))

    return "", ""


def _extract_description_from_response(data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    if not isinstance(data, dict):
        return None, None

    html_parts: List[str] = []
    text_parts: List[str] = []

    for field in DESCRIPTION_FIELDS:
        field_html, field_text = _extract_html_text(data.get(field))
        if field_html:
            html_parts.append(field_html)
        if field_text:
            text_parts.append(field_text)

    description_text = _clean_text(" ".join(part for part in text_parts if part))
    if not description_text:
        return None, None

    return "".join(part for part in html_parts if part), description_text


def _mark_failure(
    job: Dict[str, Any],
    *,
    marker: str,
    company: Optional[str],
    shortcode: Optional[str],
    status_code: Optional[int] = None,
) -> Dict[str, Any]:
    logger.warning(
        "Workable detail fetch failed | company=%s | shortcode=%s | status=%s | reason=%s",
        company or "",
        shortcode or "",
        status_code if status_code is not None else "",
        marker,
    )
    job["_details_fetched"] = marker
    return job


def fetch_workable_details(job: Dict[str, Any]) -> Dict[str, Any]:
    company = str(job.get("company") or "").strip() or None
    shortcode = workable_shortcode(job)

    if not company or not shortcode:
        return _mark_failure(
            job,
            marker="workable_request_failed",
            company=company,
            shortcode=shortcode,
        )

    url = WORKABLE_V2_DETAIL_API.format(company, shortcode)

    try:
        response = http_get(url, headers=HEADERS, timeout=10)
    except Exception:
        response = None

    if response is None or response.status_code != 200:
        return _mark_failure(
            job,
            marker="workable_request_failed",
            company=company,
            shortcode=shortcode,
            status_code=getattr(response, "status_code", None),
        )

    try:
        data = response.json()
    except Exception:
        return _mark_failure(
            job,
            marker="workable_request_failed",
            company=company,
            shortcode=shortcode,
            status_code=response.status_code,
        )

    description_html, description_text = _extract_description_from_response(data)
    if not description_text:
        logger.warning(
            "Workable detail fetch empty body | company=%s | shortcode=%s | status=%s | reason=%s",
            company,
            shortcode,
            response.status_code,
            "workable_no_description",
        )
        job["_details_fetched"] = "workable_no_description"
        return job

    job["description_html"] = description_html
    job["description_text"] = description_text
    job["_details_fetched"] = "workable_api"
    return job
