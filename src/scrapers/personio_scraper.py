import html
import re
import xml.etree.ElementTree as ET
from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urlsplit

from tqdm import tqdm

from models.job import Job
from src.config.consts import PERSONIO_XML_URL, SCRAPER_HTTP_TIMEOUT_SECONDS
from src.discovery.crawl_scheduler import (
    AcquisitionOutcome,
    AcquisitionStatus,
    load_schedule,
    mark_scraped,
    save_schedule,
    should_scrape,
)
from src.utils.file_loader import load_lines
from src.utils.http_retry import http_get
from src.utils.logging import get_logger
from src.utils.parallel import run_parallel
from src.utils.pipeline_metrics import observe_acquisition

logger = get_logger("personio")

PERSONIO_MAX_XML_BYTES = 5 * 1024 * 1024
PERSONIO_MAX_POSITIONS = 5_000
PERSONIO_MAX_DESCRIPTION_CHARS = 100_000

_HOST_PATTERN = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.jobs\.personio\.(?:de|com)$"
)
_POSITION_ID_PATTERN = re.compile(r"^[0-9]+$")
_VISIBLE_URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
_XML_CONTENT_TYPES = frozenset({"application/xml", "text/xml"})
_FORBIDDEN_XML_MARKERS = (b"<!DOCTYPE", b"<!ENTITY")
_DESCRIPTION_BLOCK_TAGS = frozenset(
    {
        "address",
        "article",
        "aside",
        "blockquote",
        "br",
        "div",
        "dl",
        "fieldset",
        "figcaption",
        "figure",
        "footer",
        "h1",
        "h2",
        "h3",
        "h4",
        "h5",
        "h6",
        "header",
        "hr",
        "li",
        "main",
        "nav",
        "ol",
        "p",
        "pre",
        "section",
        "table",
        "td",
        "th",
        "tr",
        "ul",
    }
)
_DESCRIPTION_SUPPRESSED_TAGS = frozenset(
    {"button", "form", "script", "select", "style", "textarea"}
)
_HEADERS = {"User-Agent": "Mozilla/5.0"}


class _MalformedPayload(ValueError):
    pass


class _DescriptionHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self._parts = []
        self._suppressed_depth = 0

    def handle_starttag(self, tag, attrs):
        safe_tag = str(tag or "").lower()
        if self._suppressed_depth:
            self._suppressed_depth += 1
        elif safe_tag == "input":
            return
        elif safe_tag in _DESCRIPTION_SUPPRESSED_TAGS:
            self._suppressed_depth = 1
        elif safe_tag in _DESCRIPTION_BLOCK_TAGS:
            self._parts.append("\n")

    def handle_startendtag(self, tag, attrs):
        if not self._suppressed_depth and str(tag or "").lower() in _DESCRIPTION_BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag):
        if self._suppressed_depth:
            self._suppressed_depth -= 1
        elif str(tag or "").lower() in _DESCRIPTION_BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data):
        if not self._suppressed_depth and data:
            self._parts.append(data)

    def get_text(self):
        return "".join(self._parts)


def _normalize_host(value):
    raw = str(value or "")
    if not raw or any(character.isspace() for character in raw):
        return ""
    host = raw.lower()
    return host if _HOST_PATTERN.fullmatch(host) else ""


def _clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _element_text(parent, tag):
    element = parent.find(tag)
    if element is None:
        return ""
    return _clean_text("".join(element.itertext()))


def _html_to_bounded_text(value):
    parser = _DescriptionHTMLParser()
    try:
        parser.feed(str(value or ""))
        parser.close()
    except Exception:
        return ""
    text = html.unescape(parser.get_text())
    text = _VISIBLE_URL_PATTERN.sub("", text)
    text = re.sub(r"[^\S\n]+", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    text = re.sub(r"\n+", "\n", text).strip()
    return text[:PERSONIO_MAX_DESCRIPTION_CHARS].rstrip()


def _description_text(position):
    sections = []
    container = position.find("jobDescriptions")
    if container is None:
        return ""

    for section in container.findall("jobDescription"):
        heading = _element_text(section, "name")
        value_element = section.find("value")
        raw_value = "" if value_element is None else "".join(value_element.itertext())
        body = _html_to_bounded_text(raw_value)
        section_text = "\n".join(part for part in (heading, body) if part)
        if section_text:
            sections.append(section_text)

    return "\n\n".join(sections)[:PERSONIO_MAX_DESCRIPTION_CHARS].rstrip()


def _creation_timestamp(value):
    timestamp = _clean_text(value)
    if not timestamp:
        return ""
    try:
        datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return ""
    return timestamp


def _canonical_job_url(host, position_id):
    if not _normalize_host(host) or not _POSITION_ID_PATTERN.fullmatch(position_id):
        return ""
    url = f"https://{host}/job/{position_id}?language=en"
    parsed = urlsplit(url)
    if (
        parsed.scheme != "https"
        or parsed.hostname != host
        or parsed.netloc != host
        or parsed.path != f"/job/{position_id}"
        or parsed.query != "language=en"
    ):
        return ""
    return url


def _request_feed(host):
    return http_get(
        PERSONIO_XML_URL.format(host=host),
        headers=_HEADERS,
        timeout=SCRAPER_HTTP_TIMEOUT_SECONDS,
        allow_redirects=False,
    )


def _response_content(response):
    content = getattr(response, "content", b"")
    if isinstance(content, bytes):
        return content
    if isinstance(content, str):
        return content.encode("utf-8")
    raise _MalformedPayload("response content must be bytes")


def _parse_feed(response):
    content_type = str(getattr(response, "headers", {}).get("Content-Type", ""))
    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type not in _XML_CONTENT_TYPES:
        raise _MalformedPayload("unexpected content type")

    content = _response_content(response)
    if len(content) > PERSONIO_MAX_XML_BYTES:
        raise _MalformedPayload("response exceeds byte bound")
    upper_content = content.upper()
    if any(marker in upper_content for marker in _FORBIDDEN_XML_MARKERS):
        raise _MalformedPayload("forbidden XML declaration")

    try:
        root = ET.fromstring(content)
    except (ET.ParseError, ValueError):
        raise _MalformedPayload("invalid XML") from None

    if root.tag != "workzag-jobs":
        raise _MalformedPayload("unexpected XML root")
    if any(child.tag != "position" for child in root):
        raise _MalformedPayload("unexpected XML collection structure")

    positions = list(root)
    if len(positions) > PERSONIO_MAX_POSITIONS:
        raise _MalformedPayload("position count exceeds bound")
    return positions


def _locations(position):
    values = []
    primary = _element_text(position, "office")
    if primary:
        values.append(primary)

    additional = position.find("additionalOffices")
    if additional is not None:
        for office in additional.findall("office"):
            value = _clean_text("".join(office.itertext()))
            if value and value not in values:
                values.append(value)
    return values


def _metadata(position):
    metadata = {}
    description = _description_text(position)
    if description:
        metadata["description"] = description

    creation_timestamp = _creation_timestamp(_element_text(position, "createdAt"))
    if creation_timestamp:
        metadata["personio_created_at"] = creation_timestamp

    optional_fields = (
        ("department", "department"),
        ("recruiting_category", "recruitingCategory"),
        ("employment_type", "employmentType"),
        ("seniority", "seniority"),
        ("schedule", "schedule"),
        ("years_of_experience", "yearsOfExperience"),
        ("keywords", "keywords"),
        ("occupation", "occupation"),
        ("occupation_category", "occupationCategory"),
    )
    for key, tag in optional_fields:
        value = _element_text(position, tag)
        if value:
            metadata[key] = value
    return metadata


def validate_personio_company(company):
    host = _normalize_host(company)
    if not host:
        return False
    try:
        response = _request_feed(host)
        if response is None or response.status_code != 200:
            return False
        _parse_feed(response)
    except Exception:
        return False
    return True


def validate_personio_companies(companies):
    valid = set()
    for company in tqdm(companies, desc="Personio XML validation"):
        host = _normalize_host(company)
        if host and validate_personio_company(host):
            valid.add(host)
    logger.info("%s valid Personio companies from XML validation", len(valid))
    return valid


def _fetch_company_outcome(company):
    host = _normalize_host(company)
    if not host:
        return AcquisitionOutcome(
            str(company or "<invalid-personio-host>"),
            AcquisitionStatus.FAILED,
            reason="malformed_payload",
        )

    try:
        response = _request_feed(host)
    except Exception:
        return AcquisitionOutcome(
            host,
            AcquisitionStatus.FAILED,
            reason="transport_error",
        )

    if response is None or response.status_code != 200:
        return AcquisitionOutcome(
            host,
            AcquisitionStatus.FAILED,
            reason="non_200_response",
        )

    try:
        positions = _parse_feed(response)
    except _MalformedPayload:
        return AcquisitionOutcome(
            host,
            AcquisitionStatus.FAILED,
            reason="malformed_payload",
        )

    if not positions:
        return AcquisitionOutcome(
            host,
            AcquisitionStatus.EMPTY,
            page_count=1,
            raw_job_count=0,
        )

    jobs = []
    malformed_record_count = 0
    for position in positions:
        position_id = _element_text(position, "id")
        title = _element_text(position, "name")
        url = _canonical_job_url(host, position_id)
        if not position_id or not title or not url:
            malformed_record_count += 1
            continue

        company_name = _element_text(position, "subcompany") or host
        try:
            jobs.append(
                Job(
                    company=company_name,
                    title=title,
                    location=_locations(position),
                    url=url,
                    source="personio",
                    posted_at=None,
                    job_id=f"personio_{host}_{position_id}",
                    meta=_metadata(position),
                ).to_dict()
            )
        except Exception:
            malformed_record_count += 1

    if jobs:
        status = (
            AcquisitionStatus.PARTIAL
            if malformed_record_count
            else AcquisitionStatus.SUCCESS
        )
        return AcquisitionOutcome(
            host,
            status,
            tuple(jobs),
            reason="parse_error" if status is AcquisitionStatus.PARTIAL else "",
            page_count=1,
            raw_job_count=len(positions),
        )

    return AcquisitionOutcome(
        host,
        AcquisitionStatus.FAILED,
        reason="parse_error",
        page_count=1,
        raw_job_count=len(positions),
    )


def fetch_company_jobs(company):
    return list(_fetch_company_outcome(company).jobs)


def _fetch_company_result(company):
    host = _normalize_host(company) or str(company or "")
    return [
        observe_acquisition(
            "personio",
            lambda: _fetch_company_outcome(company),
            schedule_on_success=True,
            company=host,
        )
    ]


def scrape_all_personio():
    hosts = sorted(
        {
            host
            for host in (
                _normalize_host(company)
                for company in load_lines("discovery://ats/personio")
            )
            if host
        }
    )
    if not hosts:
        return []

    schedule = load_schedule()
    hosts = [host for host in hosts if should_scrape(host, schedule)]
    if not hosts:
        return []

    outcomes = run_parallel(
        hosts,
        _fetch_company_result,
        max_workers=10,
        desc="Personio scraping",
    )

    all_jobs = []
    schedule_changed = False
    for outcome in outcomes:
        all_jobs.extend(outcome.jobs)
        if outcome.should_mark_scraped:
            mark_scraped(outcome.company, schedule)
            schedule_changed = True

    if schedule_changed:
        save_schedule(schedule)
    return all_jobs
