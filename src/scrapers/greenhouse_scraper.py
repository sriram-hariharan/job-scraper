import asyncio
import aiohttp
from tqdm import tqdm
from src.config.consts import (
    GREENHOUSE_API,
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
    record_http_request,
    record_http_response_status,
    record_http_retry,
    retry_delay_seconds,
)
from src.utils.pipeline_metrics import observe_acquisition_async

logger = get_logger("greenhouse")


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

async def _fetch_company_outcome(session, company):

    url = GREENHOUSE_API.format(company)

    jobs = []

    data, failure_reason = await _fetch_json(session, url)
    if failure_reason:
        return AcquisitionOutcome(
            company,
            AcquisitionStatus.FAILED,
            reason=failure_reason,
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
            raw_job_count=len(postings),
        )

    status = AcquisitionStatus.SUCCESS if jobs else AcquisitionStatus.EMPTY
    return AcquisitionOutcome(
        company,
        status,
        tuple(jobs),
        raw_job_count=len(postings),
    )


async def fetch_company_jobs(session, company):
    outcome = await _fetch_company_outcome(session, company)
    return list(outcome.jobs)

async def run_company(session, company):
    return await observe_acquisition_async(
        "greenhouse",
        lambda: _fetch_company_outcome(session, company),
        schedule_on_success=True,
        company=company,
    )

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

    timeout = aiohttp.ClientTimeout(total=SCRAPER_ASYNC_TOTAL_TIMEOUT_SECONDS)
    async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:

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
