import time
import requests
from src.config.consts import ASHBY_URL, ASHBY_DETAIL_QUERY, ASHBY_QUERY
from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.parallel import run_parallel
from src.utils.logging import get_logger
from src.discovery.learned_companies import learn_from_job_url, load_learned

logger = get_logger("ashby")

HEADERS = {"User-Agent": "Mozilla/5.0"}

def fetch_job_timestamp(company, job_id):

    payload = {
        "operationName": "ApiJobPosting",
        "query": ASHBY_DETAIL_QUERY,
        "variables": {
            "organizationHostedJobsPageName": company,
            "jobPostingId": job_id
        }
    }

    try:
        for attempt in range(3):

            r = requests.post(
                ASHBY_URL,
                json=payload,
                headers=HEADERS,
                timeout=10
            )
            if r is None or r.status_code == 429:
                time.sleep(1.5 * (attempt + 1))
                continue

            break

    except requests.Timeout:
        return None, "detail_timeout"
    except requests.RequestException:
        return None, "detail_request_error"
    except Exception:
        return None, "detail_unknown_exception"

    if r is None or r.status_code != 200:
        return None, f"detail_http_{r.status_code}"

    try:
        data = r.json()
        if data.get("errors"):
            logger.error(f"Ashby GraphQL error | company={company} | errors={data['errors']}")
    except Exception:
        return None, "detail_invalid_json"

    if data.get("errors"):
        return None, "detail_graphql_error"

    job = data.get("data", {}).get("jobPosting", {})

    if not isinstance(job, dict):
        return None, "detail_unexpected_shape"

    ts = job.get("publishedDate")
    if ts:
        return ts, "published_date_found"

    posting = job.get("posting")
    if isinstance(posting, dict):
        nested_ts = posting.get("publishedDate")
        if nested_ts:
            return nested_ts, "published_date_found_nested"

    return None, "published_date_missing"


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

        job_id = job.get("id")

        # jobs.append({
        #     "company": company,
        #     "title": job.get("title", ""),
        #     "location": job.get("locationName", ""),
        #     "url": f"https://jobs.ashbyhq.com/{company}/{job_id}",
        #     "source": "ashby",
        #     # "posted_at": None
        #     "posted_at": job.get("publishedDate")
        # })
        job_url = f"https://jobs.ashbyhq.com/{company}/{job_id}"
        learn_from_job_url(job_url)

        jobs.append(
            Job(
                company=company,
                title=job.get("title", ""),
                location=job.get("locationName", ""),
                url=job_url,
                source="ashby",
                posted_at=job.get("publishedDate")
            ).to_dict()
        )

    return jobs


def scrape_all_ashby():

    companies = load_lines("data/ashby_companies.txt")
    learned = load_learned()
    companies += learned.get("ashby", [])

    # remove duplicates
    companies = list(set(companies))

    all_jobs = run_parallel(
        companies,
        fetch_company_jobs,
        max_workers=20,
        desc="Ashby scraping"
        )

    logger.info("Ashby summary")
    logger.info("------------------")
    logger.info(f"Total jobs collected: {len(all_jobs)}")

    return all_jobs