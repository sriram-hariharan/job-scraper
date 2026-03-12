import requests
from src.utils.logging import get_logger
from src.config.consts import ATS_PATTERNS, ATS_SITES, SEARCH_URL, SEARCH_JOB_TITLES
import time
import random

logger = get_logger("search_discovery")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

PAGES = [0, 30, 60]   # first 3 result pages


def run_search_discovery():

    discovered = {k: set() for k in ATS_PATTERNS}

    session = requests.Session()
    session.headers.update(HEADERS)

    for ats, site in ATS_SITES.items():

        for title in SEARCH_JOB_TITLES:

            query = f"{site} \"{title}\""

            for start in PAGES:

                url = SEARCH_URL.format(query.replace(" ", "+"), start)

                try:
                    r = session.get(url, timeout=10)

                    html = r.text

                    # print(html[:1000])
                    if "Error getting results" in html:
                        logger.warning("DuckDuckGo blocked request")
                        break

                    matches = ATS_PATTERNS[ats].findall(html)

                    for m in matches:
                        discovered[ats].add(m)
                    
                    time.sleep(random.uniform(1.5, 3))

                except Exception:
                    continue

    for ats, companies in discovered.items():
        logger.info(f"{ats:15} {len(companies)} discovered via search")

    return discovered