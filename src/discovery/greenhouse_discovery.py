import requests
import os
from dotenv import load_dotenv

load_dotenv()

SERPER_KEY = os.getenv("SERPER_API_KEY")
SERPER_URL = "https://google.serper.dev/search"
GREENHOUSE_BOARDS_API = "https://boards-api.greenhouse.io/v1/boards?per_page=500"

def serper_search(query, page=1):

    payload = {
        "q": query,
        "page": page
    }

    headers = {
        "X-API-KEY": SERPER_KEY,
        "Content-Type": "application/json"
    }

    try:
        r = requests.post(SERPER_URL, json=payload, headers=headers)
        data = r.json()
    except Exception:
        return []

    links = []

    for result in data.get("organic", []):
        link = result.get("link")
        if link:
            links.append(link)

    return links

def extract_greenhouse_slug(url):
    """
    Extracts the company slug from greenhouse URLs.

    Works for:
    boards.greenhouse.io/company
    boards.greenhouse.io/company/jobs
    boards.greenhouse.io/company/jobs/123
    """

    if "boards.greenhouse.io/" not in url:
        return None

    try:
        slug = url.split("boards.greenhouse.io/")[1].split("/")[0]
        return slug
    except Exception:
        return None


def discover_greenhouse():

    companies = discover_greenhouse_from_api()

    save_companies(companies, "data/greenhouse_companies.txt")

    return companies

def save_companies(companies, file_path):
    """
    Saves newly discovered companies into the file without duplicates.
    """

    existing = set()

    if os.path.exists(file_path):

        with open(file_path, "r") as f:
            existing = set(x.strip() for x in f.readlines())

    new_companies = companies - existing

    if not new_companies:
        print("No new companies discovered")
        return

    with open(file_path, "a") as f:

        for c in new_companies:
            f.write(c + "\n")

    print("New companies added:", len(new_companies))


# def discover_greenhouse_from_api():

#     try:
#         r = requests.get(
#             GREENHOUSE_BOARDS_API,
#             timeout=20,
#             headers={"User-Agent": "job-scraper"}
#         )

#         if r.status_code != 200:
#             return set()

#         data = r.json()

#     except Exception:
#         return set()

#     companies = set()

#     for board in data.get("boards", []):

#         slug = board.get("short_name")

#         if slug:
#             companies.add(slug)

#     print("Greenhouse API discovered:", len(companies))

#     return companies

def discover_greenhouse_from_api():

    test_slugs = [
        "stripe",
        "airbnb",
        "notion",
        "databricks",
        "figma",
        "openai",
        "coinbase",
        "robinhood",
        "snowflake",
        "doordash",
    ]

    companies = set()

    for slug in test_slugs:

        url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

        try:
            r = requests.get(url, timeout=10)

            if r.status_code == 200:
                companies.add(slug)

        except:
            pass

    print("Greenhouse verified companies:", len(companies))

    return companies