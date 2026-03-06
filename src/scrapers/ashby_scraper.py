import time
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config.consts import ASHBY_URL, ASHBY_DETAIL_QUERY, ASHBY_QUERY

HEADERS = {"User-Agent": "Mozilla/5.0"}

def load_companies(path="data/ashby_companies.txt"):
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]


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
            if r.status_code == 429:
                time.sleep(1.5 * (attempt + 1))
                continue

            break

    except requests.Timeout:
        return None, "detail_timeout"
    except requests.RequestException:
        return None, "detail_request_error"
    except Exception:
        return None, "detail_unknown_exception"

    if r.status_code != 200:
        return None, f"detail_http_{r.status_code}"

    try:
        data = r.json()
        if data.get("errors"):
            print("Ashby GraphQL error:", company, data["errors"])
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
    print("Ashby company slug:", company)
    try:
        r = requests.post(
            ASHBY_URL,
            json=payload,
            headers=HEADERS,
            timeout=10
        )
    except Exception:
        return []

    if r.status_code != 200:
        return []

    data = r.json()

    # jobs_data = (
    #     data.get("data", {})
    #         .get("jobBoard", {})
    #         .get("jobPostings", [])
    # )
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

        jobs.append({
            "company": company,
            "title": job.get("title", ""),
            "location": job.get("locationName", ""),
            "url": f"https://jobs.ashbyhq.com/{company}/{job_id}",
            "source": "ashby",
            # "posted_at": None
            "posted_at": job.get("publishedDate")
        })

    # # timestamp fetch
    # for job, job_data in zip(jobs, jobs_data):

    #     job_id = job_data.get("id")

    #     if job_id:
    #         posted_at, _ = fetch_job_timestamp(company, job_id)
    #         job["posted_at"] = posted_at

    return jobs


def scrape_all_ashby():

    companies = load_companies()
    all_jobs = []

    with ThreadPoolExecutor(max_workers=20) as executor:

        futures = [executor.submit(fetch_company_jobs, c) for c in companies]

        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Ashby scraping"
        ):
            all_jobs.extend(future.result())

    print("\nAshby summary")
    print("------------------")
    print("Total jobs collected:", len(all_jobs))

    return all_jobs