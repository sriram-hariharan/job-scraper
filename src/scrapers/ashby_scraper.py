<<<<<<< HEAD
import time
=======
<<<<<<< Updated upstream
import requests
from src.pipeline.job_filter import title_matches, us_location
>>>>>>> main

import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed


# ASHBY_URL = "https://jobs.ashbyhq.com/api/non-user-graphql"
ASHBY_URL = "https://jobs.ashbyhq.com/api/non-user-graphql?op=ApiJobBoardWithTeams"

QUERY = """
query ApiJobBoardWithTeams($organizationHostedJobsPageName: String!) {
  jobBoard: jobBoardWithTeams(
    organizationHostedJobsPageName: $organizationHostedJobsPageName
  ) {
    jobPostings {
      id
      title
      locationName
      workplaceType
      employmentType
    }
  }
}
"""

DETAIL_QUERY = """
query ApiJobPosting($organizationHostedJobsPageName: String!, $jobPostingId: String!) {
  jobPosting(
    organizationHostedJobsPageName: $organizationHostedJobsPageName
    jobPostingId: $jobPostingId
  ) {
    id
    title
    publishedDate
  }
}
"""

def load_companies(path="data/ashby_companies.txt"):
    companies = []

    with open(path) as f:
        for line in f:
            c = line.strip()
            if c:
                companies.append(c)
    return companies

<<<<<<< HEAD
=======
=======
import time
import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config.consts import ASHBY_URL, ASHBY_DETAIL_QUERY, ASHBY_QUERY

HEADERS = {"User-Agent": "Mozilla/5.0"}

def load_companies(path="data/ashby_companies.txt"):
    with open(path) as f:
        return [line.strip() for line in f if line.strip()]


>>>>>>> main
def fetch_job_timestamp(company, job_id):

    payload = {
        "operationName": "ApiJobPosting",
<<<<<<< HEAD
        "query": DETAIL_QUERY,
=======
        "query": ASHBY_DETAIL_QUERY,
>>>>>>> main
        "variables": {
            "organizationHostedJobsPageName": company,
            "jobPostingId": job_id
        }
    }

    try:
        for attempt in range(3):
<<<<<<< HEAD
            r = requests.post(
                "https://jobs.ashbyhq.com/api/non-user-graphql",
                json=payload,
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=10
            )

=======

            r = requests.post(
                ASHBY_URL,
                json=payload,
                headers=HEADERS,
                timeout=10
            )
>>>>>>> main
            if r.status_code == 429:
                time.sleep(1.5 * (attempt + 1))
                continue

            break
<<<<<<< HEAD
=======

>>>>>>> main
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
<<<<<<< HEAD
=======
        if data.get("errors"):
            print("Ashby GraphQL error:", company, data["errors"])
>>>>>>> main
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
<<<<<<< HEAD
=======
>>>>>>> Stashed changes

>>>>>>> main

def fetch_company_jobs(company):

    payload = {
<<<<<<< HEAD
    "operationName": "ApiJobBoardWithTeams",
    "query": QUERY,
    "variables": {
        "organizationHostedJobsPageName": company
    }}
=======
<<<<<<< Updated upstream
        "operationName": "JobBoard",
        "query": QUERY,
        "variables": {
            "organizationHostedJobsPageName": company
        }
    }
>>>>>>> main

    try:
        r = requests.post(
            ASHBY_URL,
            json=payload,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
    except:
<<<<<<< HEAD
        return []
=======
        return jobs
=======
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
>>>>>>> Stashed changes
>>>>>>> main

    if r.status_code != 200:
        return []

    data = r.json()

<<<<<<< Updated upstream
    try:
        jobs_data = (
            data.get("data", {})
                .get("jobBoard", {})
                .get("jobPostings", [])
        )
    except:
<<<<<<< HEAD
        return []
=======
        return jobs
=======
    # jobs_data = (
    #     data.get("data", {})
    #         .get("jobBoard", {})
    #         .get("jobPostings", [])
    # )
    data_root = data.get("data")
    if not data_root:
        return []
>>>>>>> Stashed changes

    job_board = data_root.get("jobBoard")

    if not job_board:
        return []

    jobs_data = job_board.get("jobPostings", [])

    jobs = []
>>>>>>> main

    for job in jobs_data:

<<<<<<< Updated upstream
        title = job.get("title", "")
        location = job.get("locationName", "")
        job_id = job.get("id")

        # collect basic job info first
        jobs.append({
            "company": company,
            "title": title,
            "location": location,
            "url": f"https://jobs.ashbyhq.com/{company}/{job_id}",
            "source": "ashby",
            "posted_at": None,
            "_job_id": job_id  # temporary field for later timestamp fetch
        })

<<<<<<< HEAD
    for job in jobs:
        job_id = job.pop("_job_id", None)
        if job_id:
            posted_at, status = fetch_job_timestamp(company, job_id)
            job["posted_at"] = posted_at
            
=======
=======
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

>>>>>>> Stashed changes
>>>>>>> main
    return jobs


def scrape_all_ashby():

    companies = load_companies()
    all_jobs = []

<<<<<<< HEAD
    with ThreadPoolExecutor(max_workers=10) as executor:

        futures = [executor.submit(fetch_company_jobs, c) for c in companies]

        for future in tqdm(as_completed(futures),
                           total=len(futures),
                           desc="Ashby scraping"):

            jobs = future.result()
            all_jobs.extend(jobs)
=======
<<<<<<< Updated upstream
    for company in companies:
        jobs = fetch_company_jobs(company)
        all_jobs.extend(jobs)
=======
    with ThreadPoolExecutor(max_workers=20) as executor:

        futures = [executor.submit(fetch_company_jobs, c) for c in companies]

        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Ashby scraping"
        ):
            all_jobs.extend(future.result())
>>>>>>> main

    print("\nAshby summary")
    print("------------------")
    print("Total jobs collected:", len(all_jobs))
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
>>>>>>> main

    return all_jobs