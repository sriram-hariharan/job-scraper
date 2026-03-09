import json
import os
from src.utils.logging import get_logger

logger = get_logger(__name__)

DATA_PATH = "data/learned_companies.json"

# in-memory store
_DISCOVERED = {
    "greenhouse": set(),
    "ashby": set(),
    "lever": set(),
    "workday": set(),
    "workable": set(),
    "jobvite": set()
}

def learn_from_job_url(url):

    if not url:
        return

    ats = None
    slug = None

    if "boards.greenhouse.io" in url:
        ats = "greenhouse"
        slug = url.split("boards.greenhouse.io/")[1].split("/")[0].split("?")[0]

    elif "jobs.ashbyhq.com" in url:
        ats = "ashby"
        slug = url.split("jobs.ashbyhq.com/")[1].split("/")[0].split("?")[0]

    elif "lever.co" in url:
        ats = "lever"
        slug = url.split("lever.co/")[1].split("/")[0].split("?")[0]

    elif "apply.workable.com" in url:
        ats = "workable"
        slug = url.split("apply.workable.com/")[1].split("/")[0].split("?")[0]

    elif "jobs.jobvite.com" in url:
        ats = "jobvite"
        slug = url.split("jobs.jobvite.com/")[1].split("/")[0].split("?")[0]

    if ats and slug:
        _DISCOVERED[ats].add(slug)


def save_learned():
    logger.info("Saving discovered companies...")
    
    os.makedirs("data", exist_ok=True)

    existing = {}

    if os.path.exists(DATA_PATH):
        try:
            with open(DATA_PATH) as f:
                existing = json.load(f)
        except:
            existing = {}

    # merge existing + discovered
    for ats, values in _DISCOVERED.items():

        existing.setdefault(ats, [])

        merged = set(existing[ats])
        merged.update(values)

        existing[ats] = sorted(list(merged))

    with open(DATA_PATH, "w") as f:
        json.dump(existing, f, indent=2)


def load_learned():

    if not os.path.exists(DATA_PATH):
        return {}

    try:
        with open(DATA_PATH) as f:
            return json.load(f)
    except:
        return {}