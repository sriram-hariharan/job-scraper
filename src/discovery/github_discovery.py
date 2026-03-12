import re
import requests
from src.utils.logging import get_logger
import os
from src.config.consts import GITHUB_SEARCH, ATS_PATTERNS, QUERIES
from dotenv import load_dotenv

logger = get_logger("github_discovery")

load_dotenv()

def run_github_discovery():

    discovered = {k: set() for k in ATS_PATTERNS}

    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {os.getenv('GITHUB_TOKEN')}",
        "User-Agent": "Mozilla/5.0"
    }

    for query in QUERIES:

        search_url = GITHUB_SEARCH.format(query)

        try:
            r = requests.get(search_url, headers=headers, timeout=10)

            if r.status_code != 200:
                continue

            data = r.json()
            items = data.get("items", [])

            for item in items:

                html_url = item.get("html_url", "")

                raw_url = html_url.replace(
                    "https://github.com/",
                    "https://raw.githubusercontent.com/"
                ).replace("/blob/", "/")

                try:
                    r = requests.get(raw_url, headers=headers, timeout=10)

                    if r.status_code != 200:
                        continue

                    text = r.text

                except Exception:
                    continue

                for ats, pattern in ATS_PATTERNS.items():

                    matches = pattern.findall(text)

                    for m in matches:
                        discovered[ats].add(m)

        except Exception:
            continue

    return discovered