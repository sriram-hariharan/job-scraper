import asyncio
import aiohttp
import json
import os
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
from src.utils.http_retry import http_get

logger = get_logger("lever")


def _selected_role_families_from_env():
    raw = str(os.environ.get("JOB_STACK_SELECTED_ROLE_FAMILIES", "") or "").strip()
    if not raw:
        return []

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.warning("Ignoring invalid JOB_STACK_SELECTED_ROLE_FAMILIES JSON.")
        return []

    if not isinstance(parsed, list):
        logger.warning("Ignoring non-list JOB_STACK_SELECTED_ROLE_FAMILIES value.")
        return []

    selected = []
    for value in parsed:
        role_family_id = str(value or "").strip()
        if role_family_id and role_family_id not in selected:
            selected.append(role_family_id)
    return selected


def _lever_company_url(company):
    return f"{LEVER_API}/{company}?mode=json"


def _parse_lever_postings_payload(data):
    if not isinstance(data, list):
        return []

    return [
        job for job in data
        if isinstance(job, dict)
        and str(job.get("id") or "").strip()
        and str(job.get("text") or "").strip()
    ]


def validate_lever_company(company):
    slug = str(company or "").strip()
    if not slug:
        return False

    try:
        response = http_get(
            _lever_company_url(slug),
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10,
        )
        if response is None or response.status_code != 200:
            return False

        return bool(_parse_lever_postings_payload(response.json()))
    except Exception:
        return False


def validate_lever_companies(slugs):
    valid = set()

    for slug in tqdm(slugs, desc="Lever API validation"):
        company = str(slug or "").strip()
        if company and validate_lever_company(company):
            valid.add(company)

    logger.info("%s valid lever companies from API validation", len(valid))
    return valid


def seed_valid_lever_companies(slugs, *, source="manual_lever_validation"):
    valid = validate_lever_companies(slugs)
    if not valid:
        return 0

    from src.storage.discovery_store import upsert_discovered_ats_companies

    return upsert_discovered_ats_companies(
        "lever",
        valid,
        source=source,
    )


async def fetch_company_jobs(session, company):

    url = _lever_company_url(company)
    selected_role_families = _selected_role_families_from_env()

    try:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:

            if resp.status != 200:
                return []

            data = await resp.json()

    except Exception:
        return []

    jobs = []

    for job in _parse_lever_postings_payload(data):

        title = job.get("text", "")
        location = job.get("categories", {}).get("location", "")
        job_url = job.get("hostedUrl", "")
        posted_at = job.get("createdAt")

        learn_from_job_url(job_url)

        # ---------- EARLY FILTERS ----------

        if not title_matches(
            title,
            selected_role_families=selected_role_families or None,
        ):
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

    companies = load_lines("discovery://ats/lever")
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

        async def run_company(company):
            jobs = await limited_fetch(company)
            return company, jobs

        tasks = [
            asyncio.create_task(run_company(c))
            for c in companies
        ]

        for task in tqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc="Lever scraping"
        ):

            company, jobs = await task

            all_jobs.extend(jobs)

            mark_scraped(company, schedule)

    save_schedule(schedule)
    return all_jobs


def scrape_all_lever():

    jobs = asyncio.run(scrape_all_lever_async())

    return jobs
