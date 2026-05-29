import html
import json
import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple

from src.utils.http_retry import http_get
from src.utils.logging import get_logger

logger = get_logger("jobvite_details")

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


def _is_jobposting_node(node: Dict[str, Any]) -> bool:
    raw_type = node.get("@type")
    if isinstance(raw_type, list):
        values = raw_type
    else:
        values = [raw_type]
    return any(str(value or "").lower() == "jobposting" for value in values)


def _extract_jsonld_description(page_html: str) -> Tuple[Optional[str], Optional[str]]:
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
            if not _is_jobposting_node(node):
                continue
            raw_description = str(node.get("description") or "").strip()
            if not raw_description:
                continue

            if "<" in raw_description and ">" in raw_description:
                description_html = raw_description
                description_text = _html_to_text(raw_description)
            else:
                description_html = _plain_to_html(raw_description)
                description_text = _clean_text(raw_description)

            if description_text:
                return description_html, description_text

    return None, None


def _extract_container_html(page_html: str) -> Tuple[Optional[str], Optional[str]]:
    container_patterns = [
        r"<div[^>]+id=[\"']jv-job-detail[\"'][^>]*>(.*?)</div>\s*</div>",
        r"<div[^>]+class=[\"'][^\"']*jv-job-detail[^\"']*[\"'][^>]*>(.*?)</div>\s*</div>",
        r"<div[^>]+class=[\"'][^\"']*jv-job-description[^\"']*[\"'][^>]*>(.*?)</div>",
        r"<section[^>]+class=[\"'][^\"']*job-description[^\"']*[\"'][^>]*>(.*?)</section>",
        r"<div[^>]+class=[\"'][^\"']*job-description[^\"']*[\"'][^>]*>(.*?)</div>",
    ]

    for pattern in container_patterns:
        match = re.search(pattern, page_html or "", flags=re.IGNORECASE | re.DOTALL)
        if not match:
            continue
        description_html = match.group(0)
        description_text = _html_to_text(description_html)
        if description_text:
            return description_html, description_text

    body_match = re.search(r"<body[^>]*>(.*?)</body>", page_html or "", flags=re.IGNORECASE | re.DOTALL)
    if body_match:
        body_html = body_match.group(1)
        body_text = _html_to_text(body_html)
        if body_text:
            return body_html, body_text

    return None, None


def _extract_description_from_html(page_html: str) -> Tuple[Optional[str], Optional[str]]:
    description_html, description_text = _extract_jsonld_description(page_html)
    if description_text:
        return description_html, description_text

    return _extract_container_html(page_html)


def _mark_failure(
    job: Dict[str, Any],
    *,
    marker: str,
    url: Optional[str],
    status_code: Optional[int] = None,
) -> Dict[str, Any]:
    logger.warning(
        "Jobvite detail fetch failed | url=%s | status=%s | reason=%s",
        url or "",
        status_code if status_code is not None else "",
        marker,
    )
    job["_details_fetched"] = marker
    return job


def fetch_jobvite_details(job: Dict[str, Any]) -> Dict[str, Any]:
    url = str(job.get("url") or job.get("job_url") or "").strip()

    if not url:
        return _mark_failure(job, marker="jobvite_request_failed", url=url)

    try:
        response = http_get(url, headers=HEADERS, timeout=10)
    except Exception:
        response = None

    if response is None or response.status_code != 200:
        return _mark_failure(
            job,
            marker="jobvite_request_failed",
            url=url,
            status_code=getattr(response, "status_code", None),
        )

    page_html = str(getattr(response, "text", "") or "")
    if not page_html.strip():
        job["_details_fetched"] = "jobvite_no_description"
        return job

    description_html, description_text = _extract_description_from_html(page_html)
    if not description_text:
        logger.warning(
            "Jobvite detail fetch empty body | url=%s | status=%s | reason=%s",
            url,
            response.status_code,
            "jobvite_no_description",
        )
        job["_details_fetched"] = "jobvite_no_description"
        return job

    job["description_html"] = description_html
    job["description_text"] = description_text
    job["_details_fetched"] = "jobvite_html"
    return job
