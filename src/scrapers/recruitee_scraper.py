import re
from urllib.parse import urlsplit

from tqdm import tqdm

from models.job import Job
from src.config.consts import RECRUITEE_API, SCRAPER_HTTP_TIMEOUT_SECONDS
from src.discovery.crawl_scheduler import (
    AcquisitionOutcome,
    AcquisitionStatus,
    load_schedule,
    mark_scraped,
    save_schedule,
    should_scrape,
)
from src.utils.file_loader import load_lines
from src.utils.http_retry import http_get
from src.utils.logging import get_logger
from src.utils.parallel import run_parallel
from src.utils.pipeline_metrics import observe_acquisition

logger = get_logger("recruitee")

_TENANT_PATTERN = re.compile(
    r"^[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?$"
)
_HEADERS = {"User-Agent": "Mozilla/5.0"}
_LOCATION_COMPONENT_FIELDS = ("name", "city", "state")


def _normalize_tenant(value):
    tenant = str(value or "").strip().lower()
    return tenant if _TENANT_PATTERN.fullmatch(tenant) else ""


def _public_job_url(value):
    url = str(value or "").strip()
    parsed = urlsplit(url)
    if parsed.scheme != "https" or not parsed.netloc:
        return ""
    return url


def _location_component(value):
    return str(value or "").strip() if isinstance(value, (str, int)) else ""


def _structured_location(group):
    if not isinstance(group, dict):
        return ""

    country = _location_component(group.get("country"))
    country_code = _location_component(group.get("country_code")).upper()
    if not country:
        if country_code == "US":
            country = "United States"
        else:
            return ""

    components = [
        _location_component(group.get(field_name))
        for field_name in _LOCATION_COMPONENT_FIELDS
    ]
    components.append(country)

    unique_components = []
    seen = set()
    for component in components:
        if component and component not in seen:
            seen.add(component)
            unique_components.append(component)
    return ", ".join(unique_components)


def _offer_location(offer):
    locations = []
    primary = offer.get("location")
    if isinstance(primary, str) and primary.strip():
        locations.append(primary)

    secondary_groups = offer.get("locations")
    if isinstance(secondary_groups, list):
        for group in secondary_groups:
            location = _structured_location(group)
            if location and location not in locations:
                locations.append(location)

    if not locations:
        return ""
    if len(locations) == 1:
        return locations[0]
    return locations


def _request_offers(tenant):
    return http_get(
        RECRUITEE_API.format(tenant=tenant),
        headers=_HEADERS,
        timeout=SCRAPER_HTTP_TIMEOUT_SECONDS,
    )


def validate_recruitee_company(company):
    tenant = _normalize_tenant(company)
    if not tenant:
        return False

    try:
        response = _request_offers(tenant)
        if response is None or response.status_code != 200:
            return False
        payload = response.json()
    except Exception:
        return False

    return (
        isinstance(payload, dict)
        and "offers" in payload
        and isinstance(payload.get("offers"), list)
    )


def validate_recruitee_companies(companies):
    valid = set()
    for company in tqdm(companies, desc="Recruitee API validation"):
        tenant = _normalize_tenant(company)
        if tenant and validate_recruitee_company(tenant):
            valid.add(tenant)

    logger.info("%s valid Recruitee companies from API validation", len(valid))
    return valid


def _fetch_company_outcome(company):
    tenant = _normalize_tenant(company)
    if not tenant:
        return AcquisitionOutcome(
            str(company or "<invalid-recruitee-tenant>"),
            AcquisitionStatus.FAILED,
            reason="malformed_payload",
        )

    try:
        response = _request_offers(tenant)
    except Exception:
        return AcquisitionOutcome(
            tenant,
            AcquisitionStatus.FAILED,
            reason="transport_error",
        )

    if response is None or response.status_code != 200:
        return AcquisitionOutcome(
            tenant,
            AcquisitionStatus.FAILED,
            reason="non_200_response",
        )

    try:
        payload = response.json()
    except Exception:
        return AcquisitionOutcome(
            tenant,
            AcquisitionStatus.FAILED,
            reason="malformed_payload",
        )

    if (
        not isinstance(payload, dict)
        or "offers" not in payload
        or not isinstance(payload.get("offers"), list)
    ):
        return AcquisitionOutcome(
            tenant,
            AcquisitionStatus.FAILED,
            reason="malformed_payload",
        )

    offers = payload["offers"]
    if not offers:
        return AcquisitionOutcome(
            tenant,
            AcquisitionStatus.EMPTY,
            page_count=1,
            raw_job_count=0,
        )

    jobs = []
    valid_record_count = 0
    malformed_record_count = 0

    for offer in offers:
        if not isinstance(offer, dict):
            malformed_record_count += 1
            continue

        offer_id = str(offer.get("id") or "").strip()
        title = str(offer.get("title") or "").strip()
        job_url = _public_job_url(offer.get("careers_url"))
        if not offer_id or not title or not job_url:
            malformed_record_count += 1
            continue

        valid_record_count += 1
        location = _offer_location(offer)
        posted_at = offer.get("published_at")

        try:
            jobs.append(
                Job(
                    company=tenant,
                    title=title,
                    location=location,
                    url=job_url,
                    source="recruitee",
                    posted_at=posted_at,
                    job_id=f"rq_{tenant}_{offer_id}",
                    meta={
                        "description": offer.get("description") or "",
                        "requirements": offer.get("requirements") or "",
                    },
                ).to_dict()
            )
        except Exception:
            malformed_record_count += 1
            valid_record_count -= 1

    if jobs:
        status = (
            AcquisitionStatus.PARTIAL
            if malformed_record_count
            else AcquisitionStatus.SUCCESS
        )
        return AcquisitionOutcome(
            tenant,
            status,
            tuple(jobs),
            reason="parse_error" if status is AcquisitionStatus.PARTIAL else "",
            page_count=1,
            raw_job_count=len(offers),
        )

    if malformed_record_count and not valid_record_count:
        return AcquisitionOutcome(
            tenant,
            AcquisitionStatus.FAILED,
            reason="parse_error",
            page_count=1,
            raw_job_count=len(offers),
        )

    if malformed_record_count:
        return AcquisitionOutcome(
            tenant,
            AcquisitionStatus.FAILED,
            reason="parse_error",
            page_count=1,
            raw_job_count=len(offers),
        )

    return AcquisitionOutcome(
        tenant,
        AcquisitionStatus.EMPTY,
        page_count=1,
        raw_job_count=len(offers),
    )


def fetch_company_jobs(company):
    return list(_fetch_company_outcome(company).jobs)


def _fetch_company_result(company):
    tenant = _normalize_tenant(company) or str(company or "")
    return [
        observe_acquisition(
            "recruitee",
            lambda: _fetch_company_outcome(company),
            schedule_on_success=True,
            company=tenant,
        )
    ]


def scrape_all_recruitee():
    companies = sorted(
        {
            tenant
            for tenant in (
                _normalize_tenant(company)
                for company in load_lines("discovery://ats/recruitee")
            )
            if tenant
        }
    )
    if not companies:
        return []

    schedule = load_schedule()
    companies = [
        company for company in companies if should_scrape(company, schedule)
    ]
    if not companies:
        return []

    outcomes = run_parallel(
        companies,
        _fetch_company_result,
        max_workers=10,
        desc="Recruitee scraping",
    )

    all_jobs = []
    schedule_changed = False
    for outcome in outcomes:
        all_jobs.extend(outcome.jobs)
        if outcome.should_mark_scraped:
            mark_scraped(outcome.company, schedule)
            schedule_changed = True

    if schedule_changed:
        save_schedule(schedule)

    return all_jobs
