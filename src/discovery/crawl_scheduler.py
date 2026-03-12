import json
import os
import time

SCHEDULE_FILE = "data/company_crawl_state.json"
CRAWL_INTERVAL = 6 * 3600  # 6 hours


def load_schedule():
    if not os.path.exists(SCHEDULE_FILE):
        return {}

    try:
        with open(SCHEDULE_FILE, "r") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

    except Exception:
        pass

    return {}


def save_schedule(schedule):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(schedule, f, indent=2, sort_keys=True)


def should_scrape(company, schedule):
    entry = schedule.get(company)

    if not entry:
        return True

    last_scraped = entry.get("last_scraped", 0)

    return (time.time() - last_scraped) >= CRAWL_INTERVAL


def mark_scraped(company, schedule):
    now = time.time()

    if company not in schedule:
        schedule[company] = {}

    schedule[company]["last_scraped"] = now