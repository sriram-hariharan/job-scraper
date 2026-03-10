import requests
import time
from src.config.consts import ASHBY_URL, ASHBY_DETAIL_QUERY, ASHBY_QUERY
from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.parallel import run_parallel
from src.utils.logging import get_logger
from src.discovery.learned_companies import learn_from_job_url, load_learned
from concurrent.futures import ThreadPoolExecutor, as_completed

logger = get_logger("ashby")

HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Content-Type": "application/json",
    "apollographql-client-name": "frontend_non_user",
    "apollographql-client-version": "0.1.0",
    "Origin": "https://jobs.ashbyhq.com",
    "Referer": "https://jobs.ashbyhq.com"
}

def fetch_ashby_timestamp(company, job_id):
    time.sleep(0.4)
    payload = {
        "operationName": "ApiJobPosting",
        "query": ASHBY_DETAIL_QUERY,
        "variables": {
            "organizationHostedJobsPageName": company,
            "jobPostingId": job_id
        }
    }

    try:
        r = requests.post(
            ASHBY_URL,
            json=payload,
            headers=HEADERS,
            timeout=10
        )
        if r is None or r.status_code != 200:
            return None

        data = r.json()
        root = data.get("data")

        if not root:
            return None

        job = root.get("jobPosting")

        if not job:
            return None

        return job.get("publishedDate")

    except Exception:
        return None
    
def fetch_company_jobs(company):

    payload = {
        "operationName": "ApiJobBoardWithTeams",
        "query": ASHBY_QUERY,
        "variables": {"organizationHostedJobsPageName": company}
    }
    try:
        r = requests.post(
            ASHBY_URL,
            json=payload,
            headers=HEADERS,
            timeout=10
        )
    except Exception:
        return []

    if r is None or r.status_code != 200:
        return []

    data = r.json()
    data_root = data.get("data")
    if not data_root:
        return []

    job_board = data_root.get("jobBoard")

    if not job_board:
        return []

    jobs_data = job_board.get("jobPostings", [])

    jobs = []

    for job in jobs_data:
        
        title = job.get("title", "")
        job_id = job.get("id")

        job_url = f"https://jobs.ashbyhq.com/{company}/{job_id}"

        learn_from_job_url(job_url)

        jobs.append(
            Job(
                company=company,
                title=title,
                location=job.get("locationName") or "",
                url=job_url,
                source="ashby",
                posted_at=None,
                meta={"_job_id": job_id}
            ).to_dict()
        )

    return jobs


def scrape_all_ashby():
    companies = load_lines("data/ashby_companies.txt")
    learned = load_learned()
    companies += learned.get("ashby", [])

    # remove duplicates
    companies = list(set(companies))

    results = run_parallel(
    companies,
    fetch_company_jobs,
    max_workers=20,
    desc="Ashby scraping"   
    )

    all_jobs = []
    for r in results:
        if isinstance(r, list):
            all_jobs.extend(r)
        elif isinstance(r, dict):
            all_jobs.append(r)

    logger.info("Ashby summary")
    logger.info("------------------")
    logger.info(f"Total jobs collected: {len(all_jobs)}")
    print(type(all_jobs[0]))
    return all_jobs