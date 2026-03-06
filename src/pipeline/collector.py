from typing import List, Dict, Any
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter

from src.scrapers.workday_scraper import scrape_all_workday
from src.scrapers.greenhouse_scraper import scrape_all_greenhouse
from src.scrapers.lever_scraper import scrape_all_lever
from src.scrapers.ashby_scraper import scrape_all_ashby
from src.scrapers.workable_scraper import scrape_all_workable
from src.scrapers.jobvite_scraper import scrape_all_jobvite

from src.pipeline.job_filter import filter_jobs
from src.pipeline.dedupe import dedupe_jobs


def collect_all_jobs() -> List[Dict[str, Any]]:

    scrapers = [
        # ("workday", scrape_all_workday),
        # ("greenhouse", scrape_all_greenhouse),
        # ("lever", scrape_all_lever),
        # ("ashby", scrape_all_ashby),
        # ("workable", scrape_all_workable),
        ("jobvite", scrape_all_jobvite),
    ]

    all_jobs: List[Dict[str, Any]] = []
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

    print("\nRaw jobs by source:")
    for source, count in Counter(job["source"] for job in all_jobs).items():
        print(source, count)

    print("\nJobs missing posted_at:")
    missing = Counter(job["source"] for job in all_jobs if not job.get("posted_at"))
    for source, count in missing.items():
        print(source, count)

    filtered_jobs = filter_jobs(all_jobs)

    print("\nTotal filtered jobs:", len(filtered_jobs))

    print("\nFiltered jobs by source:")
    for source, count in Counter(job["source"] for job in filtered_jobs).items():
        print(source, count)

    deduped_jobs = dedupe_jobs(filtered_jobs)

    print("\nTotal deduped jobs:", len(deduped_jobs))

    return deduped_jobs