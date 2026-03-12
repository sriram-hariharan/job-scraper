import asyncio
import aiohttp
from tqdm import tqdm
from src.config.consts import LEVER_API
from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.logging import get_logger
from src.discovery.learned_companies import learn_from_job_url
from src.pipeline.job_filter import (
    title_matches,
    us_location,
    posted_within_24h
)
from src.discovery.crawl_scheduler import (
    load_schedule,
    save_schedule,
    should_scrape,
    mark_scraped
)

logger = get_logger("lever")

async def fetch_company_jobs(session, company):

    url = f"{LEVER_API}/{company}?mode=json"

    try:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:

            if resp.status != 200:
                return []

            data = await resp.json()

    except Exception:
        return []

    jobs = []

    for job in data:

        title = job.get("text", "")
        location = job.get("categories", {}).get("location", "")
        job_url = job.get("hostedUrl", "")
        posted_at = job.get("createdAt")

        learn_from_job_url(job_url)

        # ---------- EARLY FILTERS ----------

        if not title_matches(title):
            continue

        if not us_location(location, "lever"):
            continue

        if not posted_within_24h(posted_at):
            continue
        # -----------------------------------

        jobs.append(
            Job(
                company=company,
                title=title,
                location=location,
                url=job_url,
                source="lever",
                posted_at=posted_at,
                job_id=f"lv_{job.get('id')}"
            ).to_dict()
        )

    return jobs


async def scrape_all_lever_async():

    companies = load_lines("data/lever_companies.txt")
    schedule = load_schedule()

    companies = [
    c for c in companies
    if should_scrape(c, schedule)
    ]
    
    # remove duplicates
    companies = list(set(companies))

    connector = aiohttp.TCPConnector(limit=100)

    all_jobs = []

    async with aiohttp.ClientSession(connector=connector) as session:

        sem = asyncio.Semaphore(100)
        async def limited_fetch(company):
            async with sem:
                return await fetch_company_jobs(session, company)

        task_map = {
            asyncio.create_task(limited_fetch(c)): c
            for c in companies
        }

        for task in tqdm(asyncio.as_completed(task_map),
                        total=len(task_map),
                        desc="Lever scraping"):

            company = task_map[task]

            jobs = await task
            all_jobs.extend(jobs)

            mark_scraped(company, schedule)

    save_schedule(schedule)
    return all_jobs


def scrape_all_lever():

    jobs = asyncio.run(scrape_all_lever_async())

    return jobs