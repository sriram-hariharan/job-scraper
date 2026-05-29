import html
import json
import re
from html.parser import HTMLParser
from typing import Any, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from src.utils.logging import get_logger

logger = get_logger("builtin_details")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
}


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: List[str] = []

    def handle_data(self, data: str) -> None:
        text = str(data or "").strip()
        if text:
            self._parts.append(text)

    def get_text(self) -> str:
        return " ".join(self._parts)


def _clean_text(value: str) -> str:
    return re.sub(r"\s+", " ", value or "").strip()


def _html_to_text(value: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(value or "")
    return _clean_text(html.unescape(parser.get_text()))


def _plain_to_html(value: str) -> str:
    return "".join(
        f"<p>{html.escape(part.strip())}</p>"
        for part in re.split(r"\n{2,}", value or "")
        if part.strip()
    )


def _extract_html_text(value: Any) -> Tuple[str, str]:
    if value is None:
        return "", ""

    raw = str(value or "").strip()
    if not raw:
        return "", ""

    if "<" in raw and ">" in raw:
        return raw, _html_to_text(raw)

    return _plain_to_html(raw), _clean_text(raw)


def _jsonld_nodes(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, dict):
        nodes = [value]
        graph = value.get("@graph")
        if isinstance(graph, list):
            nodes.extend(node for node in graph if isinstance(node, dict))
        return nodes

    if isinstance(value, list):
        nodes: List[Dict[str, Any]] = []
        for item in value:
            nodes.extend(_jsonld_nodes(item))
        return nodes

    return []


def extract_builtin_description_from_html(page_html: str) -> Tuple[Optional[str], Optional[str]]:
    scripts = re.findall(
        r"<script[^>]+type=[\"']application/ld(?:\+|&#x2B;|&#43;)json[\"'][^>]*>(.*?)</script>",
        page_html or "",
        flags=re.IGNORECASE | re.DOTALL,
    )

    for script in scripts:
        try:
            data = json.loads(html.unescape(script.strip()))
        except Exception:
            continue

        for node in _jsonld_nodes(data):
            raw_type = node.get("@type")
            node_types = raw_type if isinstance(raw_type, list) else [raw_type]
            if not any(str(value or "").lower() == "jobposting" for value in node_types):
                continue

            description_html, description_text = _extract_html_text(node.get("description"))
            if description_text:
                return description_html, description_text

    return None, None


def fetch_builtin_detail_html(url: str) -> Tuple[Optional[str], Optional[int]]:
    if not str(url or "").strip():
        return None, None

    try:
        request = Request(str(url), headers=HEADERS)
        with urlopen(request, timeout=10) as response:
            status = getattr(response, "status", None)
            if status != 200:
                return None, status
            return response.read().decode("utf-8", "replace"), status
    except HTTPError as exc:
        return None, exc.code
    except (URLError, TimeoutError, OSError):
        return None, None


def fetch_builtin_details(job: Dict[str, Any]) -> Dict[str, Any]:
    url = str(job.get("url") or job.get("job_url") or "").strip()
    if not url:
        job["_details_fetched"] = "builtin_request_failed"
        return job

    page_html, status_code = fetch_builtin_detail_html(url)
    if not page_html:
        logger.warning(
            "Built In detail fetch failed | url=%s | status=%s | reason=%s",
            url,
            status_code if status_code is not None else "",
            "builtin_request_failed",
        )
        job["_details_fetched"] = "builtin_request_failed"
        return job

    description_html, description_text = extract_builtin_description_from_html(page_html)
    if not description_text:
        logger.warning(
            "Built In detail fetch empty body | url=%s | status=%s | reason=%s",
            url,
            status_code if status_code is not None else "",
            "builtin_no_description",
        )
        job["_details_fetched"] = "builtin_no_description"
        return job

    job["description_html"] = description_html
    job["description_text"] = description_text
    job["_details_fetched"] = "builtin_page"
    return job
