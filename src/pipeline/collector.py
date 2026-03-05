from typing import List, Dict, Any

from src.scrapers.workday_scraper import scrape_all_workday
from src.scrapers.greenhouse_scraper import scrape_all_greenhouse
from src.scrapers.lever_scraper import scrape_all_lever
from src.scrapers.ashby_scraper import scrape_all_ashby
from src.scrapers.workable_scraper import scrape_all_workable
from src.scrapers.jobvite_scraper import scrape_all_jobvite

from src.pipeline.job_filter import filter_jobs
from src.pipeline.dedupe import dedupe_jobs

import time
from concurrent.futures import ThreadPoolExecutor, as_completed


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

    start_total = time.time()

    with ThreadPoolExecutor(max_workers=len(scrapers)) as executor:

        futures = {
            executor.submit(fn): (name, time.time())
            for name, fn in scrapers
        }

        for future in as_completed(futures):

            name, start = futures[future]

            try:
                jobs = future.result()
                elapsed = round(time.time() - start, 2)

                print(f"{name} scraper finished | jobs: {len(jobs)} | time: {elapsed}s")

                all_jobs.extend(jobs)

            except Exception as e:
                print(f"{name} scraper failed:", e)

    total_elapsed = round(time.time() - start_total, 2)
    print(f"\nTotal scraping time: {total_elapsed}s")

    print("Total raw jobs collected:", len(all_jobs))

    filtered_jobs = filter_jobs(all_jobs)
    print("Total filtered jobs:", len(filtered_jobs))

    deduped_jobs = dedupe_jobs(filtered_jobs)
    print("Total deduped jobs:", len(deduped_jobs))

    return deduped_jobs