import asyncio
import aiohttp
from tqdm import tqdm
from src.config.consts import (
    LEVER_API,
    SCRAPER_ASYNC_TOTAL_TIMEOUT_SECONDS,
    SCRAPER_RETRY_ATTEMPTS,
    SCRAPER_RETRY_DELAY_SECONDS,
    SCRAPER_RETRY_MAX_DELAY_SECONDS,
)
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
from src.utils.http_retry import (
    TRANSIENT_HTTP_STATUSES,
    http_get,
    record_http_request,
    record_http_response_status,
    record_http_retry,
    retry_delay_seconds,
)
from src.utils.pipeline_metrics import observe_acquisition_async

logger = get_logger("lever")


async def _fetch_json(session, url):
    for attempt in range(SCRAPER_RETRY_ATTEMPTS):
        try:
            record_http_request()
            async with session.get(
                url,
                headers={"User-Agent": "Mozilla/5.0"},
            ) as resp:
                record_http_response_status(resp.status)
                if resp.status in TRANSIENT_HTTP_STATUSES:
                    if attempt < SCRAPER_RETRY_ATTEMPTS - 1:
                        record_http_retry()
                        await asyncio.sleep(
                            retry_delay_seconds(
                                getattr(resp, "headers", None),
                                fallback_delay=SCRAPER_RETRY_DELAY_SECONDS,
                                max_delay=SCRAPER_RETRY_MAX_DELAY_SECONDS,
                            )
                        )
                        continue
                    return None, "non_200_response"

                if resp.status != 200:
                    return None, "non_200_response"

                try:
                    return await resp.json(), ""
                except Exception:
                    return None, "malformed_payload"
        except (asyncio.TimeoutError, aiohttp.ClientConnectionError, OSError):
            if attempt == SCRAPER_RETRY_ATTEMPTS - 1:
                return None, "transport_error"
            record_http_retry()
            await asyncio.sleep(SCRAPER_RETRY_DELAY_SECONDS)
        except Exception:
            return None, "transport_error"

    return None, "transport_error"


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


async def _fetch_company_outcome(session, company):

    url = _lever_company_url(company)

    data, failure_reason = await _fetch_json(session, url)
    if failure_reason:
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason=failure_reason,
        )

    if not isinstance(data, list):
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason="malformed_payload",
        )

    jobs = []
    postings = _parse_lever_postings_payload(data)
    payload_incomplete = len(postings) != len(data)

    try:
        for job in postings:

            title = job.get("text", "")
            location = job.get("categories", {}).get("location", "")
            job_url = job.get("hostedUrl", "")
            posted_at = job.get("createdAt")

            learn_from_job_url(job_url)

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
    except Exception:
        status = AcquisitionStatus.PARTIAL if jobs else AcquisitionStatus.FAILED
        return AcquisitionOutcome(
            company,
            status,
            tuple(jobs),
            reason="parse_error",
            raw_job_count=len(data),
        )

    if payload_incomplete:
        status = AcquisitionStatus.PARTIAL if jobs else AcquisitionStatus.FAILED
        return AcquisitionOutcome(
            company,
            status,
            tuple(jobs),
            reason="malformed_payload",
            raw_job_count=len(data),
        )

    status = AcquisitionStatus.SUCCESS if jobs else AcquisitionStatus.EMPTY
    return AcquisitionOutcome(
        company,
        status,
        tuple(jobs),
        raw_job_count=len(data),
    )


async def fetch_company_jobs(session, company):
    outcome = await _fetch_company_outcome(session, company)
    return list(outcome.jobs)


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

    timeout = aiohttp.ClientTimeout(total=SCRAPER_ASYNC_TOTAL_TIMEOUT_SECONDS)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:

        sem = asyncio.Semaphore(100)
        async def limited_fetch(company):
            async with sem:
                return await observe_acquisition_async(
                    "lever",
                    lambda: _fetch_company_outcome(session, company),
                    schedule_on_success=True,
                    company=company,
                )

        async def run_company(company):
            return await limited_fetch(company)

        tasks = [
            asyncio.create_task(run_company(c))
            for c in companies
        ]

        for task in tqdm(
            asyncio.as_completed(tasks),
            total=len(tasks),
            desc="Lever scraping"
        ):

            try:
                outcome = await task
            except Exception as exc:
                logger.warning(f"Lever worker failed: {exc}")
                continue

            all_jobs.extend(outcome.jobs)

            if outcome.should_mark_scraped:
                mark_scraped(outcome.company, schedule)

    save_schedule(schedule)
    return all_jobs


def scrape_all_lever():

    jobs = asyncio.run(scrape_all_lever_async())

    return jobs
