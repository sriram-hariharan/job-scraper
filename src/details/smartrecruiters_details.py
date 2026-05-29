import html
import json
import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple

from src.utils.http_retry import http_get
from src.utils.logging import get_logger

logger = get_logger("smartrecruiters_details")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}

SMARTRECRUITERS_DETAIL_API = (
    "https://api.smartrecruiters.com/v1/companies/{company}/postings/{posting_id}"
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


def smartrecruiters_identifiers(job: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    company = str(job.get("company") or "").strip() or None
    posting_id = str(job.get("id") or "").strip()

    if not posting_id and isinstance(job.get("meta"), dict):
        posting_id = str(job.get("meta", {}).get("id") or job.get("meta", {}).get("posting_id") or "").strip()

    if not posting_id:
        raw_job_id = str(job.get("job_id") or "").strip()
        if raw_job_id.startswith("sr_"):
            raw_job_id = raw_job_id[3:]
        posting_id = raw_job_id

    url = str(job.get("url") or job.get("job_url") or "").strip()
    match = re.search(r"jobs\.smartrecruiters\.com/([^/?#]+)/([^/?#]+)", url)
    if match:
        company = company or match.group(1)
        posting_id = posting_id or match.group(2)

    return company, posting_id or None


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


def _section_value(data: Dict[str, Any], *path: str) -> Any:
    current: Any = data
    for key in path:
        if not isinstance(current, dict):
            return None
        current = current.get(key)
    return current


def _extract_description_from_response(data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    if not isinstance(data, dict):
        return None, None

    candidates = [
        _section_value(data, "jobAd", "sections", "jobDescription", "text"),
        _section_value(data, "jobAd", "sections", "qualifications", "text"),
        _section_value(data, "jobAd", "sections", "additionalInformation", "text"),
        data.get("description"),
        data.get("responsibilities"),
        data.get("qualifications"),
    ]

    html_parts: List[str] = []
    text_parts: List[str] = []
    for candidate in candidates:
        candidate_html, candidate_text = _extract_html_text(candidate)
        if candidate_html:
            html_parts.append(candidate_html)
        if candidate_text:
            text_parts.append(candidate_text)

    description_text = _clean_text(" ".join(part for part in text_parts if part))
    if not description_text:
        return None, None

    return "".join(part for part in html_parts if part), description_text


def _jsonld_nodes(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, dict):
        nodes = [value]
        graph = value.get("@graph")
        if isinstance(graph, list):
            nodes.extend(node for node in graph if isinstance(node, dict))
        return nodes

    if isinstance(value, list):
        nodes = []
        for item in value:
            nodes.extend(_jsonld_nodes(item))
        return nodes

    return []


def _extract_description_from_html(page_html: str) -> Tuple[Optional[str], Optional[str]]:
    scripts = re.findall(
        r"<script[^>]+type=[\"']application/ld\+json[\"'][^>]*>(.*?)</script>",
        page_html or "",
        flags=re.IGNORECASE | re.DOTALL,
    )

    for script in scripts:
        try:
            data = json.loads(html.unescape(script.strip()))
        except Exception:
            continue

        for node in _jsonld_nodes(data):
            raw_type = node.get("@type") if isinstance(node, dict) else None
            values = raw_type if isinstance(raw_type, list) else [raw_type]
            if not any(str(value or "").lower() == "jobposting" for value in values):
                continue
            description_html, description_text = _extract_html_text(node.get("description"))
            if description_text:
                return description_html, description_text

    body_match = re.search(r"<body[^>]*>(.*?)</body>", page_html or "", flags=re.IGNORECASE | re.DOTALL)
    if body_match:
        body_html = body_match.group(1)
        body_text = _html_to_text(body_html)
        if body_text:
            return body_html, body_text

    return None, None


def _mark_failure(
    job: Dict[str, Any],
    *,
    marker: str,
    company: Optional[str],
    posting_id: Optional[str],
    status_code: Optional[int] = None,
) -> Dict[str, Any]:
    logger.warning(
        "SmartRecruiters detail fetch failed | company=%s | posting_id=%s | status=%s | reason=%s",
        company or "",
        posting_id or "",
        status_code if status_code is not None else "",
        marker,
    )
    job["_details_fetched"] = marker
    return job


def _fetch_html_fallback(job: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    url = str(job.get("url") or job.get("job_url") or "").strip()
    if not url:
        return None, None

    try:
        response = http_get(url, headers=HEADERS, timeout=10)
    except Exception:
        response = None

    if response is None or response.status_code != 200:
        return None, None

    page_html = str(getattr(response, "text", "") or "")
    if not page_html.strip():
        return None, None

    return _extract_description_from_html(page_html)


def fetch_smartrecruiters_details(job: Dict[str, Any]) -> Dict[str, Any]:
    company, posting_id = smartrecruiters_identifiers(job)

    if not company or not posting_id:
        return _mark_failure(
            job,
            marker="smartrecruiters_request_failed",
            company=company,
            posting_id=posting_id,
        )

    url = SMARTRECRUITERS_DETAIL_API.format(company=company, posting_id=posting_id)

    try:
        response = http_get(url, headers=HEADERS, timeout=10)
    except Exception:
        response = None

    if response is not None and response.status_code == 200:
        try:
            data = response.json()
        except Exception:
            data = None

        description_html, description_text = _extract_description_from_response(data or {})
        if description_text:
            job["description_html"] = description_html
            job["description_text"] = description_text
            job["_details_fetched"] = "smartrecruiters_api"
            return job

        description_html, description_text = _fetch_html_fallback(job)
        if description_text:
            job["description_html"] = description_html
            job["description_text"] = description_text
            job["_details_fetched"] = "smartrecruiters_api"
            return job

        job["_details_fetched"] = "smartrecruiters_no_description"
        return job

    description_html, description_text = _fetch_html_fallback(job)
    if description_text:
        job["description_html"] = description_html
        job["description_text"] = description_text
        job["_details_fetched"] = "smartrecruiters_api"
        return job

    return _mark_failure(
        job,
        marker="smartrecruiters_request_failed",
        company=company,
        posting_id=posting_id,
        status_code=getattr(response, "status_code", None),
    )
