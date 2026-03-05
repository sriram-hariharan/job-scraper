from typing import List, Dict, Any

from src.scrapers.workday_scraper import scrape_all_workday
from src.scrapers.greenhouse_scraper import scrape_all_greenhouse
from src.scrapers.lever_scraper import scrape_all_lever
from src.scrapers.ashby_scraper import scrape_all_ashby
from src.scrapers.workable_scraper import scrape_all_workable
from src.scrapers.jobvite_scraper import scrape_all_jobvite


def collect_all_jobs() -> List[Dict[str, Any]]:
    all_jobs: List[Dict[str, Any]] = []

    scrapers = [
        ("workday", scrape_all_workday),
        ("greenhouse", scrape_all_greenhouse),
        ("lever", scrape_all_lever),
        ("ashby", scrape_all_ashby),
        ("workable", scrape_all_workable),
        ("jobvite", scrape_all_jobvite),
    ]

    for name, fn in scrapers:
        try:
            jobs = fn()
            print(f"{name} jobs fetched: {len(jobs)}")
            all_jobs.extend(jobs)
        except Exception as e:
            print(f"{name} scraper failed:", e)

    print("Total raw jobs collected:", len(all_jobs))
    return all_jobs