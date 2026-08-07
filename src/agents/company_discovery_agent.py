import os
import requests
from tavily import TavilyClient
from urllib.parse import urlparse
from src.discovery.save_companies import append_new_companies
from src.scrapers.recruitee_scraper import (
    _normalize_tenant as normalize_recruitee_tenant,
    validate_recruitee_companies,
)
from src.utils.logging import get_logger
from tqdm import tqdm

logger = get_logger("company_agent")

INVALID_COMPANIES = {"www", "jobs", "careers", "job", "apply"}

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

        if not path:
            return None

        if "greenhouse.io" in domain:
            return path[0]

        if "lever.co" in domain:
            return path[0]

        if "ashbyhq.com" in domain:
            return path[0]

        if "apply.workable.com" in domain:
            return path[0]

        if "smartrecruiters.com" in domain and len(path) > 1:
            return path[1]

        if "myworkdayjobs.com" in domain:
            return path[0]

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

                ats = detect_ats_from_page(url)

                if ats:
                    company = extract_company_slug(url)

                    if not company:
                        continue

                    company = company.lower()

                    if company in INVALID_COMPANIES:
                        continue

                    discovered[ats].append(company)

        except Exception as e:

            logger.warning(f"Agent search failed for query: {query} | {e}")

    total = 0

    for ats, companies in discovered.items():
        if ats == "recruitee":
            companies = sorted(set(companies))
        else:
            companies = list(set(companies))
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

def detect_ats_from_page(url):

    try:

        if _recruitee_tenant_from_url(url):
            return "recruitee"

        r = requests.get(url, timeout=10)
        html = r.text.lower()

        if "boards.greenhouse.io" in html:
            return "greenhouse"

        if "jobs.lever.co" in html:
            return "lever"

        if "jobs.ashbyhq.com" in html:
            return "ashby"

        if "smartrecruiters.com" in html:
            return "smartrecruiters"

        if "apply.workable.com" in html:
            return "workable"

        if "myworkdayjobs.com" in html:
            return "workday"

        return None

    except Exception:
        return None
