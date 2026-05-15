import time

from src.storage.discovery_store import load_discovery_crawl_schedule, save_discovery_crawl_schedule

CRAWL_INTERVAL = 6 * 3600  # 6 hours


def load_schedule():
    return load_discovery_crawl_schedule()


def save_schedule(schedule):
    save_discovery_crawl_schedule(schedule)


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