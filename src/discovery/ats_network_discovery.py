import random
import requests

session = requests.Session()
session.headers.update({"User-Agent": "Mozilla/5.0"})

def discover_greenhouse_neighbors(limit=50):

    url = "https://boards-api.greenhouse.io/v1/boards"

    try:
        r = session.get(url, timeout=10)
        if r.status_code != 200:
            return []

        data = r.json()
    except Exception:
        return []

    companies = []

    for board in data.get("boards", []):
        slug = board.get("token")
        if slug:
            companies.append(slug)

    # randomize so expansion is different every run
    random.shuffle(companies)

    # return only a small batch
    return companies[:limit]