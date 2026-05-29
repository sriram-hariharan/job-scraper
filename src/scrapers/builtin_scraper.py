import re
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from typing import Dict, List, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from urllib.parse import urljoin

from models.job import Job
from src.discovery.learned_companies import learn_from_job_url
from src.utils.logging import get_logger

logger = get_logger("builtin")

BUILTIN_JOBS_URL = "https://builtin.com/jobs/dev-engineering"
BUILTIN_BASE_URL = "https://builtin.com"

POSTED_TEXT_RE = re.compile(
    r"\b(?:reposted\s+)?(?:(\d+)\s+)?"
    r"(minute|minutes|hour|hours|day|days|week|weeks|month|months|yesterday)"
    r"\s*(?:ago)?\b",
    re.I,
)
JOB_HREF_RE = re.compile(r"/job/[^\"?#]+/\d+")
COMPANY_HREF_RE = re.compile(r"/company/[^\"?#]+")
URL_SENIORITY_TERMS = (
    ("sr-director", "Senior Director"),
    ("director", "Director"),
    ("principal", "Principal"),
    ("staff", "Staff"),
    ("lead", "Lead"),
)


class _BuiltinHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.tokens: List[Dict[str, str]] = []
        self._href_stack: List[str] = []

    def handle_starttag(self, tag, attrs):
        if tag.lower() != "a":
            return
        href = ""
        for key, value in attrs:
            if key.lower() == "href":
                href = value or ""
                break
        self._href_stack.append(href)

    def handle_endtag(self, tag):
        if tag.lower() == "a" and self._href_stack:
            self._href_stack.pop()

    def handle_data(self, data):
        text = re.sub(r"\s+", " ", str(data or "")).strip()
        if not text:
            return
        self.tokens.append({"text": text, "href": self._href_stack[-1] if self._href_stack else ""})


def parse_builtin_posted_at(value: str, *, now: Optional[datetime] = None) -> Optional[str]:
    text = str(value or "").strip().lower()
    if not text:
        return None

    match = POSTED_TEXT_RE.search(text)
    if not match:
        return None

    current = now or datetime.now(timezone.utc)
    if current.tzinfo is None:
        current = current.replace(tzinfo=timezone.utc)
    current = current.astimezone(timezone.utc)

    unit = match.group(2).lower()
    amount = int(match.group(1) or 1)

    if unit == "yesterday":
        delta = timedelta(days=1)
    elif unit.startswith("minute"):
        delta = timedelta(minutes=amount)
    elif unit.startswith("hour"):
        delta = timedelta(hours=amount)
    elif unit.startswith("day"):
        delta = timedelta(days=amount)
    elif unit.startswith("week"):
        delta = timedelta(weeks=amount)
    elif unit.startswith("month"):
        delta = timedelta(days=amount * 30)
    else:
        return None

    return (current - delta).replace(microsecond=0).isoformat()


def _looks_like_location(text: str) -> bool:
    value = str(text or "").strip()
    lowered = value.lower()
    if not value:
        return False
    if lowered in {"remote", "hybrid", "in-office", "in office", "saved", "easy apply"}:
        return False
    if "$" in value:
        return False
    if re.search(r"\b(annually|level|junior|senior|mid|expert|leader|full-time)\b", lowered):
        return False
    if "," in value:
        return True
    if lowered in {"united states", "remote - us", "remote us"}:
        return True
    if re.search(r"\b[A-Z]{2},\s*USA\b", value):
        return True
    if re.search(r"\b\d+\s+locations?\b", lowered):
        return True
    return False


def _find_company(tokens: List[Dict[str, str]], index: int) -> str:
    for token in reversed(tokens[max(0, index - 12):index]):
        if COMPANY_HREF_RE.search(token.get("href", "")):
            return token.get("text", "").strip()
    return ""


def _find_posted_and_location(tokens: List[Dict[str, str]], index: int, *, now=None):
    posted_at = None
    posted_index = None
    for offset, token in enumerate(tokens[index + 1:index + 45], start=index + 1):
        if JOB_HREF_RE.search(token.get("href", "")):
            break
        parsed = parse_builtin_posted_at(token.get("text", ""), now=now)
        if parsed:
            posted_at = parsed
            posted_index = offset
            break

    if not posted_at or posted_index is None:
        return None, ""

    for token in tokens[posted_index + 1:posted_index + 18]:
        if JOB_HREF_RE.search(token.get("href", "")):
            break
        text = token.get("text", "")
        if _looks_like_location(text):
            return posted_at, text

    return posted_at, ""


def _job_slug_from_href(href: str) -> str:
    path = str(href or "").split("?", 1)[0].split("#", 1)[0]
    parts = [part for part in path.split("/") if part]
    if len(parts) < 3 or parts[0] != "job":
        return ""
    return parts[-2]


def _title_with_url_seniority(title: str, href: str) -> str:
    clean_title = str(title or "").strip()
    slug = _job_slug_from_href(href).lower()
    if not clean_title or not slug:
        return clean_title

    title_words = set(re.findall(r"[a-z]+", clean_title.lower()))
    slug_terms = set(slug.split("-"))

    for slug_term, label in URL_SENIORITY_TERMS:
        term_words = slug_term.split("-")
        label_words = set(label.lower().split())
        if not all(word in slug_terms for word in term_words):
            continue
        if label_words.issubset(title_words):
            return clean_title
        return f"{label} {clean_title}"

    return clean_title


def extract_builtin_jobs_from_html(html_text: str, *, now: Optional[datetime] = None) -> List[Dict[str, str]]:
    parser = _BuiltinHTMLParser()
    try:
        parser.feed(html_text or "")
    except Exception:
        return []

    jobs: List[Dict[str, str]] = []
    seen_urls = set()
    for index, token in enumerate(parser.tokens):
        href = token.get("href", "")
        if not JOB_HREF_RE.search(href):
            continue

        title = _title_with_url_seniority(token.get("text", ""), href)
        company = _find_company(parser.tokens, index)
        posted_at, location = _find_posted_and_location(parser.tokens, index, now=now)
        url = urljoin(BUILTIN_BASE_URL, href)

        if not (title and company and location and posted_at and url):
            continue
        if url in seen_urls:
            continue
        seen_urls.add(url)

        job_id = f"builtin_{url.rstrip('/').split('/')[-1]}"
        jobs.append(
            Job(
                company=company,
                title=title,
                location=location,
                url=url,
                source="builtin",
                posted_at=posted_at,
                job_id=job_id,
            ).to_dict()
        )

    return jobs


def fetch_builtin_jobs_html() -> str:
    try:
        request = Request(
            BUILTIN_JOBS_URL,
            headers={"User-Agent": "Mozilla/5.0"},
        )
        with urlopen(request, timeout=15) as response:
            if response.status != 200:
                logger.warning("Built In jobs fetch returned status=%s", response.status)
                return ""
            return response.read().decode("utf-8", "replace")
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        logger.warning("Built In jobs fetch failed: %s", exc)
        return ""


def smoke_builtin_live(limit: int = 5) -> List[Dict[str, str]]:
    html_text = fetch_builtin_jobs_html()
    if not html_text:
        return []
    return extract_builtin_jobs_from_html(html_text)[:limit]


def scrape_all_builtin() -> List[Dict[str, str]]:
    jobs = smoke_builtin_live(limit=10_000)
    for job in jobs:
        learn_from_job_url(job.get("url"))

    logger.info("Built In jobs parsed: %s", len(jobs))
    return jobs
