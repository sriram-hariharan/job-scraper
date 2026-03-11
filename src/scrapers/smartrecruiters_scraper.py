import requests
from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.parallel import run_parallel
from src.utils.logging import get_logger
from src.discovery.learned_companies import learn_from_job_url
from src.utils.http_retry import http_get

logger = get_logger("smartrecruiters")

API = "https://jobs.smartrecruiters.com/sr-jobs/search?limit=100"
COMPANY_API = "https://api.smartrecruiters.com/v1/companies/{company}/postings"

def fetch_company_board(company):

    url = COMPANY_API.format(company=company)

    try:
        r = http_get(url, timeout=10)

        if r.status_code != 200:
            return []

        data = r.json()

    except Exception:
        return []

    postings = data.get("content", [])

    jobs = []

    for job in postings:

        title = job.get("name", "")

        location_obj = job.get("location", {})
        location = (
            location_obj.get("city")
            or location_obj.get("region")
            or location_obj.get("country")
            or ""
        )

        sr_id = job.get("id")
        if not sr_id:
            continue

        identifier = job.get("company", {}).get("identifier")
        if not identifier:
            continue

        job_url = f"https://jobs.smartrecruiters.com/{identifier}/{sr_id}"

        learn_from_job_url(job_url)
        
        jobs.append(
            Job(
                company=company,
                title=title,
                location=location,
                url=job_url,
                source="smartrecruiters",
                posted_at=job.get("releasedDate"),
                job_id=f"sr_{sr_id}" if sr_id else None
            ).to_dict()
        )

    return jobs

def fetch_company_jobs(company):

    url = API.format(company=company)

    try:
        r = http_get(url, timeout=10)

        if r.status_code != 200:
            return []

        data = r.json()

    except Exception:
        return []

    postings = data.get("content", [])
    if not postings:
        return []
    
    jobs = []
    for job in postings:

        title = job.get("name", "")

        location_obj = job.get("location", {})
        location = (
            location_obj.get("city")
            or location_obj.get("region")
            or location_obj.get("country")
            or ""
        )

        job_url = job.get("applyUrl")
        sr_id = job.get("id")
        if not job_url:
            continue

        # discovery learning
        learn_from_job_url(job_url)

        company_slug = job.get("company", {}).get("identifier", company)

        jobs.append(
            Job(
                company=company_slug,
                title=title,
                location=location,
                url=job_url,
                source="smartrecruiters",
                posted_at=job.get("releasedDate"),
                job_id=f"sr_{sr_id}" if sr_id else None
            ).to_dict()
        )

    return jobs

def scrape_all_smartrecruiters():

    all_jobs = []

    # -------------------------
    # 1. GLOBAL FEED SCRAPE
    # -------------------------
    try:
        feed_jobs = fetch_company_jobs(None)   # uses feed endpoint
        all_jobs.extend(feed_jobs)

    except Exception as e:
        logger.warning(f"SmartRecruiters feed failed: {e}")

    # -------------------------
    # 2. COMPANY BOARD SCRAPE   
    # -------------------------
    companies = load_lines("data/smartrecruiters_companies.txt")
    companies = list(set(companies))

    results = run_parallel(
        companies,
        fetch_company_board,
        max_workers=20,
        desc="SmartRecruiters boards"
    )

    for r in results:
        if isinstance(r, list):
            all_jobs.extend(r)

    return all_jobs