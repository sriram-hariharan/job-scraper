import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

from src.utils.http_retry import retry_request
from src.config.consts import WORKABLE_V1_API, WORKABLE_V2_DETAIL_API, WORKABLE_V3_API
from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.parallel import run_parallel
from src.utils.logging import get_logger
from src.discovery.learned_companies import learn_from_job_url

logger = get_logger("workable")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

@retry_request(retries=2)
def workable_get(url, **kwargs):
    return session.get(url, **kwargs)


@retry_request(retries=2)
def workable_post(url, **kwargs):
    return session.post(url, **kwargs)

def fetch_workable_timestamp(company, shortcode):

    if not shortcode:
        return None

    url = WORKABLE_V2_DETAIL_API.format(company, shortcode)

    try:
        r = workable_get(url, timeout=10)

        if r is None or r.status_code != 200:
            return None

        data = r.json()
        return data.get("published")

    except Exception:
        return None


def extract_v3_jobs(data):

    if not isinstance(data, dict):
        return []

    if "results" in data and isinstance(data["results"], list):
        return data["results"]

    values = [v for v in data.values() if isinstance(v, dict)]
    return values


def fetch_company_jobs(company):

    jobs_data = []
    v3_url = WORKABLE_V3_API.format(company)

    limit = 50
    offset = 0

    try:

        while True:

            r = workable_post(
                v3_url,
                json={"limit": limit, "offset": offset},
                headers={"Content-Type": "application/json"},
                timeout=10
            )

            if r is None or r.status_code != 200:
                break

            data = r.json()
            postings = extract_v3_jobs(data)

            if not postings:
                break

            jobs_data.extend(postings)

            if len(postings) < limit:
                break

            offset += limit

    except Exception:
        pass

    # fallback to v1 widget API
    if not jobs_data:

        v1_url = WORKABLE_V1_API.format(company)

        try:
            r = workable_get(v1_url, timeout=10)

            if r is None or r.status_code != 200:
                return []

            data = r.json()
            jobs_data = data.get("jobs", [])

        except Exception:
            return []

    jobs = []

    for job in jobs_data:

        city = (job.get("city") or "").strip()
        state = (job.get("state") or "").strip()
        country = (job.get("country") or "").strip()

        location = ", ".join(p for p in [city, state, country] if p)
        if not location:
            location = country
        shortcode = job.get("shortcode")

        url = job.get("url")
        if not url and shortcode:
            url = f"https://apply.workable.com/{company}/j/{shortcode}/"
        learn_from_job_url(url)
        # jobs.append({
        #     "company": company,
        #     "title": job.get("title"),
        #     "location": location,
        #     "url": url,
        #     "source": "workable",
        #     "posted_at": job.get("published")
        #     or job.get("published_on")
        #     or job.get("created_at"),
        #     "_shortcode": shortcode
        # })
        workable_id = job.get("id")
        if not workable_id and url:
            workable_id = url.split("/j/")[-1].split("/")[0]

        jobs.append(Job(
            company=company,
            title=job.get("title"),
            location=location,
            url=url,
            source="workable",  
            posted_at=(
                job.get("published")
                or job.get("published_on")
                or job.get("created_at")
            ),
            meta={
                "_shortcode": shortcode
            },
            job_id=f"wb_{workable_id}" if workable_id else None
        ).to_dict())

    # resolve missing timestamps via v2 API
    missing_jobs = [
        j for j in jobs
        if not j.get("posted_at") and j.get("_shortcode")
        ]

    if missing_jobs:

        with ThreadPoolExecutor(max_workers=10) as executor:

            future_to_job = {
                executor.submit(
                    fetch_workable_timestamp,
                    job["company"],
                    job["_shortcode"]
                ): job
                for job in missing_jobs
            }

            for future in as_completed(future_to_job):

                job = future_to_job[future]

                try:
                    ts = future.result()
                    if ts:
                        job["posted_at"] = ts
                except Exception:
                    pass

    for job in jobs:
        job.pop("_shortcode", None)

    return jobs


def scrape_all_workable():

    companies = load_lines("data/workable_companies.txt")

    # remove duplicates
    companies = list(set(companies))
    all_jobs = run_parallel(
        companies,
        fetch_company_jobs,
        max_workers=5,
        desc="Workable scraping"
        )
    
    return all_jobs