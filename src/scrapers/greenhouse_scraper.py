import asyncio
import aiohttp
from tqdm import tqdm
from src.config.consts import GREENHOUSE_API
from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.logging import get_logger

logger = get_logger("greenhouse")

async def fetch_company_jobs(session, company):

    url = GREENHOUSE_API.format(company)

    try:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:

            if resp.status != 200:
                return []

            data = await resp.json()

    except Exception as e:
        return []

    jobs = []

    postings = data.get("jobs", [])

    for job in postings:

        title = job.get("title", "")
        location = job.get("location", {}).get("name", "")
        job_url = job.get("absolute_url")

        # jobs.append({
        #     "company": company,
        #     "title": title,
        #     "location": location,
        #     "url": job_url,
        #     "source": "greenhouse",
        #     "posted_at": job.get("updated_at")
        # })
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

    return jobs


async def scrape_all_greenhouse_async():

    companies = load_lines("data/greenhouse_companies.txt")

    connector = aiohttp.TCPConnector(limit=50)

    all_jobs = []

    async with aiohttp.ClientSession(connector=connector) as session:

        tasks = [fetch_company_jobs(session, c) for c in companies]

        for future in tqdm(asyncio.as_completed(tasks),
                           total=len(tasks),
                           desc="Greenhouse scraping"):

            jobs = await future
            all_jobs.extend(jobs)

    return all_jobs

def scrape_all_greenhouse():

    jobs = asyncio.run(scrape_all_greenhouse_async())

    logger.info("Greenhouse summary")
    logger.info("------------------")
    logger.info(f"Total jobs collected: {len(jobs)}")

    return jobs