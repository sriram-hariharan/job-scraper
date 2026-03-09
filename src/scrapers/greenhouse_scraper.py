import asyncio
import aiohttp
from tqdm import tqdm
from src.config.consts import GREENHOUSE_API
from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.logging import get_logger
from src.discovery.learned_companies import learn_from_job_url, load_learned
from src.discovery.ats_network_discovery import discover_greenhouse_neighbors
from src.discovery.save_companies import append_new_companies
from src.discovery.crawl_scheduler import (
    load_schedule,
    save_schedule,
    should_scrape,
    mark_scraped
)

logger = get_logger("greenhouse")

async def fetch_company_jobs(session, company, schedule):

    url = GREENHOUSE_API.format(company)

    jobs = []

    try:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:

            if resp.status != 200:
                return jobs

            data = await resp.json()

        postings = data.get("jobs", [])

        for job in postings:
            title = job.get("title", "")
            location = job.get("location", {}).get("name", "")
            job_url = job.get("absolute_url")

            learn_from_job_url(job_url)

            jobs.append(
                Job(
                    company=company,
                    title=title,
                    location=location,
                    url=job_url,
                    source="greenhouse",
                    posted_at=job.get("updated_at")
                ).to_dict()
            )

        # --- ATS NETWORK DISCOVERY ---
        # neighbors = discover_greenhouse_neighbors(company)

        # if neighbors:
        #     append_new_companies(
        #         "data/greenhouse_companies.txt",
        #         neighbors
        #     )
        return jobs
    except Exception:
        pass

    finally:
        # ALWAYS mark company as crawled
        mark_scraped(company, schedule)

    return jobs


async def scrape_all_greenhouse_async():

    # companies = load_lines("data/greenhouse_companies.txt")
    companies = load_lines("data/greenhouse_companies.txt")
    learned = load_learned()
    companies += learned.get("greenhouse", [])

    # remove duplicates
    companies = list(set(companies))
    schedule = load_schedule()

    # scheduler filtering
    companies = [
        c for c in companies
        if should_scrape(c, schedule)
    ]

    connector = aiohttp.TCPConnector(limit=50)
    all_jobs = []

    async with aiohttp.ClientSession(connector=connector) as session:

        tasks = [fetch_company_jobs(session, c, schedule) for c in companies]

        all_neighbors = set()
        for future in tqdm(asyncio.as_completed(tasks),
                        total=len(tasks),
                        desc="Greenhouse scraping"):

            jobs, neighbors = await future

            all_jobs.extend(jobs)

            if neighbors:
                all_neighbors.update(neighbors)

        if all_neighbors:
            append_new_companies(
                "data/greenhouse_companies.txt",
                all_neighbors
            )

    save_schedule(schedule)
    return all_jobs

def scrape_all_greenhouse():

    jobs = asyncio.run(scrape_all_greenhouse_async())

    logger.info("Greenhouse summary")
    logger.info("------------------")
    logger.info(f"Total jobs collected: {len(jobs)}")

    return jobs