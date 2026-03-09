import requests
import time
from src.utils.http_retry import retry_request
from src.config.consts import (
    WORKDAY_API_URL_TEMPLATE,
    WORKDAY_ORIGIN_TEMPLATE)
from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.parallel import run_parallel
from src.utils.logging import get_logger
from src.discovery.learned_companies import learn_from_job_url

logger = get_logger("workday")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


@retry_request(retries=2)
def workday_get(url, **kwargs):
    return session.get(url, **kwargs)


@retry_request(retries=2)
def workday_post(url, **kwargs):
    return session.post(url, **kwargs)

def get_us_country_facet(data):
    facets = data.get("facetMetadata", {}).get("facets", [])

    for facet in facets:
        for val in facet.get("values", []):
            label = val.get("label", "").lower()

            if "united states" in label or label == "us":
                return facet.get("name"), val.get("id")

    return None, None


def scrape_company(board_url):
    seen_jobs = set()
    host = board_url.split("//")[1].split("/")[0]
    host = host.replace(".myworkdayjobs.com", "")
    tenant = host.split(".")[0]
    site = board_url.split(".myworkdayjobs.com/")[1].split("?")[0].strip("/")

    api_url = WORKDAY_API_URL_TEMPLATE.format(
        host=host,
        tenant=tenant,
        site=site
    )

    origin = WORKDAY_ORIGIN_TEMPLATE.format(host=host)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Accept-Language": "en-US,en;q=0.9",
        "User-Agent": "Mozilla/5.0",
        "Origin": origin,
        "Referer": board_url,
        "X-Requested-With": "XMLHttpRequest",
        "Connection": "keep-alive",
    }

    jobs = []
    offset = 0
    limit = 20

    payload = {"limit": 1, "offset": 0, "searchText": ""}
    r = workday_post(api_url, json=payload, headers=headers, timeout=10)
    if r is None or r.status_code != 200:
        return []

    data = r.json()
    facet_name, country_filter = get_us_country_facet(data)
    total = None

    while True:
        payload = {
            "limit": limit,
            "offset": offset,
            "searchText": ""
        }

        if facet_name and country_filter:
            payload["appliedFacets"] = {
                facet_name: [country_filter]
            }

        try:
            r = workday_post(api_url, json=payload, headers=headers, timeout=10)

            if r is not None and r.status_code == 400 and "appliedFacets" in payload:
                payload.pop("appliedFacets")
                r = workday_post(api_url, json=payload, headers=headers, timeout=10)

            if r.status_code != 200:
                break

            data = r.json()
        except Exception:
            break

        if total is None:
            total = data.get("total")
            if not isinstance(total, int):
                total = None

        postings = (
            data.get("jobPostings")
            or data.get("jobs")
            or data.get("items")
            or []
        )

        if isinstance(postings, dict):
            postings = postings.get("postings", [])

        if not postings:
            break

        new_jobs_this_page = 0

        for job in postings:
            job_id = job.get("externalPath")
            if not job_id:
                continue

            if job_id in seen_jobs:
                continue

            seen_jobs.add(job_id)
            new_jobs_this_page += 1

            primary_location = (
                job.get("location")
                or job.get("locationsText")
            )

            additional_locations = job.get("additionalLocations") or []

            locations = []

            if primary_location:
                locations.append(primary_location)

            if isinstance(additional_locations, list):
                locations.extend(additional_locations)

            if not locations and job.get("locationsText"):
                locations.append(job.get("locationsText"))

            posted_at = (
                job.get("startDate")
                or job.get("postedDate")
                or job.get("postedAt")
                or job.get("createdDate")
                or job.get("createdAt")
            )

            job_url = f"{board_url.rstrip('/')}/{job_id.lstrip('/')}"
            learn_from_job_url(job_url)
            # jobs.append({
            #     "title": job.get("title"),
            #     "location": locations,  
            #     "url": job_url,
            #     "company": tenant,
            #     "source": "workday",
            #     "posted_at": posted_at,
            #     "_externalPath": job.get("externalPath"),
            #     "_board_url": board_url,
            # })
            jobs.append(Job(
                title=job.get("title"),
                location=locations,
                url=job_url,
                company=tenant,
                source="workday",
                posted_at=posted_at,
                meta={
                    "_externalPath": job.get("externalPath"),
                    "_board_url": board_url
                }
            ).to_dict())

        if new_jobs_this_page == 0:
            break

        offset += limit

        if total is not None and offset >= total:
            break

        if total is None and len(postings) < limit:
            break

        time.sleep(0.01)

    return jobs

def scrape_all_workday():

    companies = load_lines("data/workday_companies.txt")
    all_jobs = run_parallel(
                companies,
                scrape_company,
                max_workers=20,
                desc="Workday scraping"
                )

    logger.info("Workday summary")
    logger.info("------------------")
    logger.info(f"Total jobs collected: {len(all_jobs)}")

    return all_jobs