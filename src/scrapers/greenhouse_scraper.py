import asyncio
import aiohttp
from tqdm import tqdm
from src.config.consts import GREENHOUSE_API
from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.logging import get_logger
from src.discovery.learned_companies import learn_from_job_url
from src.discovery.crawl_scheduler import (
    AcquisitionOutcome,
    AcquisitionStatus,
    load_schedule,
    save_schedule,
    should_scrape,
    mark_scraped
)
from src.pipeline.job_filter import title_matches, us_location, posted_within_24h

logger = get_logger("greenhouse")

async def _fetch_company_outcome(session, company):

    url = GREENHOUSE_API.format(company)

    jobs = []

    try:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:

            if resp.status != 200:
                return AcquisitionOutcome(
                    company,
                    AcquisitionStatus.FAILED,
                    reason="non_200_response",
                )

            try:
                data = await resp.json()
            except Exception:
                return AcquisitionOutcome(
                    company,
                    AcquisitionStatus.FAILED,
                    reason="malformed_payload",
                )
    except Exception:
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason="transport_error",
        )

    if (
        not isinstance(data, dict)
        or "jobs" not in data
        or not isinstance(data.get("jobs"), list)
    ):
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason="malformed_payload",
        )

    postings = data.get("jobs", [])
    if not all(isinstance(job, dict) for job in postings):
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason="malformed_payload",
        )

    try:
        for job in postings:

            title = job.get("title", "")
            location = job.get("location", {}).get("name", "")
            job_url = job.get("absolute_url")
            posted_at = job.get("updated_at")

            # --- PRE FILTERS ---
            if not title_matches(title):
                continue

            if not us_location(location, "greenhouse"):
                continue

            if not posted_within_24h(posted_at):
                continue

            learn_from_job_url(job_url)

            jobs.append(
                Job(
                    company=company,
                    title=title,
                    location=location,
                    url=job_url,
                    source="greenhouse",
                    posted_at=posted_at,
                    job_id=f"gh_{job.get('id')}"
                ).to_dict()
            )

    except Exception:
        status = AcquisitionStatus.PARTIAL if jobs else AcquisitionStatus.FAILED
        return AcquisitionOutcome(
            company,
            status,
            tuple(jobs),
            reason="parse_error",
        )

    status = AcquisitionStatus.SUCCESS if jobs else AcquisitionStatus.EMPTY
    return AcquisitionOutcome(company, status, tuple(jobs))


async def fetch_company_jobs(session, company):
    outcome = await _fetch_company_outcome(session, company)
    return list(outcome.jobs)

async def run_company(session, company):
    return await _fetch_company_outcome(session, company)

async def scrape_all_greenhouse_async():

    companies = sorted(set(load_lines("discovery://ats/greenhouse")))

    schedule = load_schedule()

    companies = [
        c for c in companies
        if should_scrape(c, schedule)
    ]
    logger.info(f"Greenhouse companies after schedule filter: {len(companies)}")

    connector = aiohttp.TCPConnector(limit=50)
    all_jobs = []

    async with aiohttp.ClientSession(connector=connector) as session:

        tasks = [
            asyncio.create_task(run_company(session, c))
            for c in companies
        ]

        for task in tqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc="Greenhouse scraping"
        ):

            try:
                outcome = await task
            except Exception as exc:
                logger.warning(f"Greenhouse worker failed: {exc}")
                continue

            all_jobs.extend(outcome.jobs)

            if outcome.should_mark_scraped:
                mark_scraped(outcome.company, schedule)
            
    save_schedule(schedule)
    return all_jobs

def scrape_all_greenhouse():

    jobs = asyncio.run(scrape_all_greenhouse_async())

    return jobs
