import os
import re
import requests
from tavily import TavilyClient
from urllib.parse import urlparse
from src.discovery.save_companies import append_new_companies
from src.discovery.learned_companies import normalize_workable_slug
from src.discovery.ats_detector import (
    detect_ats_from_embeds,
    detect_ats_from_html,
    detect_ats_from_links,
    extract_links_from_html,
)
from src.scrapers.jobvite_scraper import (
    _normalize_jobvite_company as normalize_jobvite_company,
    validate_jobvite_companies,
)
from src.scrapers.recruitee_scraper import (
    _normalize_tenant as normalize_recruitee_tenant,
    validate_recruitee_companies,
)
from src.utils.url_normalizer import normalize_workday_url
from src.utils.logging import get_logger
from tqdm import tqdm

logger = get_logger("company_agent")

INVALID_COMPANIES = {"www", "jobs", "careers", "job", "apply"}
_SMARTRECRUITERS_COMPANY_PATTERN = re.compile(
    r"^[a-z0-9](?:[a-z0-9_-]*[a-z0-9])?$"
)

SEARCH_QUERIES = [
    "AI company careers",
    "machine learning company careers",
    "data science team careers",
    "startup engineering careers",
    "technology company careers page",
    "software company careers",
    "AI research company careers",
    "venture backed startup careers",
    "engineering jobs careers site",
    "technology company hiring engineers",

    # ATS surface searches
    'site:boards.greenhouse.io "machine learning"',
    'site:boards.greenhouse.io "data scientist"',
    'site:jobs.lever.co "machine learning"',
    'site:jobs.lever.co "data scientist"',
    'site:jobs.ashbyhq.com "machine learning"',
    'site:apply.workable.com "data scientist"',
    'site:jobs.jobvite.com "machine learning"',
    'site:jobs.jobvite.com "data scientist"',
    'site:jobs.jobvite.com "software engineer"',
    'site:recruitee.com/o "machine learning"',
    'site:recruitee.com/o "data scientist"',
    'site:recruitee.com/o "software engineer"',
]


def _recruitee_tenant_from_url(url):
    try:
        parsed = urlparse(str(url or "").strip())
        if parsed.scheme.lower() not in {"http", "https"}:
            return None
        if parsed.username or parsed.password:
            return None

        hostname = (parsed.hostname or "").strip().lower()
        suffix = ".recruitee.com"
        if not hostname.endswith(suffix):
            return None

        tenant = hostname[: -len(suffix)]
        if not tenant or "." in tenant or tenant in INVALID_COMPANIES:
            return None

        normalized = normalize_recruitee_tenant(tenant)
        return normalized or None
    except (TypeError, ValueError):
        return None


def _jobvite_company_from_url(url):
    try:
        parsed = urlparse(str(url or "").strip())
        if parsed.scheme.lower() not in {"http", "https"}:
            return None
        if parsed.username or parsed.password:
            return None
        if (parsed.hostname or "").strip().lower() != "jobs.jobvite.com":
            return None

        path = [part for part in parsed.path.split("/") if part]
        if not path:
            return None
        company = normalize_jobvite_company(path[0])
        return company or None
    except (TypeError, ValueError):
        return None


def _workday_board_from_url(url):
    try:
        parsed = urlparse(str(url or "").strip())
        if parsed.scheme.lower() not in {"http", "https"}:
            return None
        if parsed.username or parsed.password or parsed.port is not None:
            return None

        hostname = (parsed.hostname or "").strip().lower()
        suffix = ".myworkdayjobs.com"
        if not hostname.endswith(suffix) or not hostname[: -len(suffix)]:
            return None

        path = [part for part in parsed.path.split("/") if part]
        if not path:
            return None

        return normalize_workday_url(f"https://{hostname}/{path[0]}")
    except (TypeError, ValueError):
        return None


def _smartrecruiters_company_from_url(url):
    try:
        parsed = urlparse(str(url or "").strip())
        if parsed.scheme.lower() not in {"http", "https"}:
            return None
        if parsed.username or parsed.password or parsed.port is not None:
            return None
        if (parsed.hostname or "").strip().lower() != "jobs.smartrecruiters.com":
            return None

        path = [part for part in parsed.path.split("/") if part]
        if not path:
            return None

        company = path[0].strip().lower()
        if company in INVALID_COMPANIES:
            return None
        if not _SMARTRECRUITERS_COMPANY_PATTERN.fullmatch(company):
            return None
        return company
    except (TypeError, ValueError):
        return None


def extract_urls(results):

    urls = []

    for r in results:
        url = r.get("url")

        if url and (
            "career" in url.lower()
            or "job" in url.lower()
            or _recruitee_tenant_from_url(url)
        ):
            urls.append(url)

    return urls

def extract_company_slug(url):

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = [p for p in parsed.path.split("/") if p]

        recruitee_tenant = _recruitee_tenant_from_url(url)
        if recruitee_tenant:
            return recruitee_tenant

        jobvite_company = _jobvite_company_from_url(url)
        if jobvite_company:
            return jobvite_company

        workday_board = _workday_board_from_url(url)
        if workday_board:
            return workday_board

        smartrecruiters_company = _smartrecruiters_company_from_url(url)
        if smartrecruiters_company:
            return smartrecruiters_company

        if not path:
            return None

        if "greenhouse.io" in domain:
            return path[0]

        if "lever.co" in domain:
            return path[0]

        if "ashbyhq.com" in domain:
            return path[0]

        if "apply.workable.com" in domain:
            return normalize_workable_slug(path[0])

        return None

    except Exception:
        return None
    
def run_company_discovery_agent():

    logger.info("")
    logger.info("AGENT COMPANY DISCOVERY")
    logger.info("----------------------")

    api_key = str(os.getenv("TAVILY_API_KEY", "") or "").strip()
    if not api_key:
        logger.info("Company discovery skipped: TAVILY_API_KEY is not configured")
        return

    client = TavilyClient(api_key=api_key)

    discovered = {
        "greenhouse": [],
        "lever": [],
        "workday": [],
        "ashby": [],
        "workable": [],
        "jobvite": [],
        "smartrecruiters": [],
        "recruitee": [],
    }

    for query in tqdm(SEARCH_QUERIES, desc="Agent search queries"):

        try:

            response = client.search(query=query, max_results=20)

            urls = extract_urls(response["results"])

            for url in urls:

                ats, company = _resolve_ats_identity_from_page(url)

                if ats:
                    if not company:
                        continue

                    if ats != "workday":
                        company = company.lower()

                    if company in INVALID_COMPANIES:
                        continue

                    discovered[ats].append(company)

        except Exception as e:

            logger.warning(f"Agent search failed for query: {query} | {e}")

    total = 0

    for ats, companies in discovered.items():
        if ats in {"jobvite", "recruitee"}:
            companies = sorted(set(companies))
        else:
            companies = list(set(companies))
        if not companies:
            continue

        if ats == "jobvite":
            try:
                validated = validate_jobvite_companies(companies)
            except Exception:
                logger.warning(
                    "Jobvite validation failed; no candidates persisted"
                )
                continue

            candidate_set = set(companies)
            companies = sorted(
                {
                    company
                    for value in validated
                    for company in [normalize_jobvite_company(value)]
                    if company and company in candidate_set
                }
            )
            if not companies:
                continue

        if ats == "recruitee":
            try:
                validated = validate_recruitee_companies(companies)
            except Exception:
                logger.warning(
                    "Recruitee validation failed; no candidates persisted"
                )
                continue

            candidate_set = set(companies)
            companies = sorted(
                {
                    tenant
                    for value in validated
                    for tenant in [normalize_recruitee_tenant(value)]
                    if tenant and tenant in candidate_set
                }
            )
            if not companies:
                continue

        append_new_companies(f"discovery://ats/{ats}", companies)

        logger.info(f"{ats} → {len(companies)} companies added")

        total += len(companies)

    logger.info(f"Agent discovered {total} companies")


def _resolve_ats_identity_from_page(url):

    try:

        recruitee_tenant = _recruitee_tenant_from_url(url)
        if recruitee_tenant:
            return "recruitee", recruitee_tenant

        jobvite_company = _jobvite_company_from_url(url)
        if jobvite_company:
            return "jobvite", jobvite_company

        workday_board = _workday_board_from_url(url)
        if workday_board:
            return "workday", workday_board

        r = requests.get(url, timeout=10)
        html = r.text
        html_lower = html.lower()

        for link in extract_links_from_html(html):
            ats, detected_link = detect_ats_from_links([link])
            if ats:
                if ats == "workday":
                    identity = normalize_workday_url(html)
                else:
                    identity = extract_company_slug(detected_link)
                if identity:
                    return ats, identity

            smartrecruiters_company = _smartrecruiters_company_from_url(link)
            if smartrecruiters_company:
                return "smartrecruiters", smartrecruiters_company

        ats, value = detect_ats_from_embeds(html)
        if ats:
            if ats == "workday":
                identity = normalize_workday_url(html)
            elif ats == "workable":
                identity = normalize_workable_slug(value)
            elif ats == "jobvite":
                identity = normalize_jobvite_company(value)
            else:
                identity = value or None
            if identity:
                return ats, identity

        workday_board = normalize_workday_url(html)
        if workday_board:
            return "workday", workday_board

        ats = detect_ats_from_html(html_lower)
        if not ats and "smartrecruiters.com" in html_lower:
            ats = "smartrecruiters"

        direct_identity = extract_company_slug(url)
        if ats and direct_identity:
            return ats, direct_identity

        return ats, None

    except Exception:
        return None, None


def detect_ats_from_page(url):
    ats, _identity = _resolve_ats_identity_from_page(url)
    return ats
