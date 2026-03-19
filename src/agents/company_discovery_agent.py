import os
import requests
from tavily import TavilyClient
from urllib.parse import urlparse
from src.discovery.save_companies import append_new_companies
from src.utils.logging import get_logger
from tqdm import tqdm

logger = get_logger("company_agent")

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

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
]


def extract_urls(results):

    urls = []

    for r in results:
        url = r.get("url")

        if url and ("career" in url.lower() or "job" in url.lower()):
            urls.append(url)

    return urls

def extract_company_slug(url):

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = [p for p in parsed.path.split("/") if p]

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

    client = TavilyClient(api_key=TAVILY_API_KEY)

    discovered = {
        "greenhouse": [],
        "lever": [],
        "workday": [],
        "ashby": [],
        "workable": [],
        "jobvite": [],
        "smartrecruiters": []
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
        companies = list(set(companies))
        if not companies:
            continue

        append_new_companies(f"data/{ats}_companies.txt", companies)

        logger.info(f"{ats} → {len(companies)} companies added")

        total += len(companies)

    logger.info(f"Agent discovered {total} companies")

def detect_ats_from_page(url):

    try:

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
