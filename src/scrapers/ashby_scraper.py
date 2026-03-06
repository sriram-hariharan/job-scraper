import time

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

def fetch_job_timestamp(company, job_id):

    payload = {
        "operationName": "ApiJobPosting",
        "query": DETAIL_QUERY,
        "variables": {
            "organizationHostedJobsPageName": company,
            "jobPostingId": job_id
        }
    }

    try:
        for attempt in range(3):
            r = requests.post(
                "https://jobs.ashbyhq.com/api/non-user-graphql",
                json=payload,
                headers={"User-Agent": "Mozilla/5.0"},
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

    jobs = []

    payload = {
    "operationName": "ApiJobBoardWithTeams",
    "query": QUERY,
    "variables": {
        "organizationHostedJobsPageName": company
    }}

    try:
        r = requests.post(
            ASHBY_URL,
            json=payload,
            headers={"User-Agent": "Mozilla/5.0"},
            timeout=10
        )
    except:
        return []

    if r.status_code != 200:
        return []

    data = r.json()

    try:
        jobs_data = (
            data.get("data", {})
                .get("jobBoard", {})
                .get("jobPostings", [])
        )
    except:
        return []

    for job in jobs_data:

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

    for job in jobs:
        job_id = job.pop("_job_id", None)
        if job_id:
            posted_at, status = fetch_job_timestamp(company, job_id)
            job["posted_at"] = posted_at
            
    return jobs


def scrape_all_ashby():

    companies = load_companies()
    all_jobs = []

    with ThreadPoolExecutor(max_workers=10) as executor:

        futures = [executor.submit(fetch_company_jobs, c) for c in companies]

        for future in tqdm(as_completed(futures),
                           total=len(futures),
                           desc="Ashby scraping"):

            jobs = future.result()
            all_jobs.extend(jobs)

    print("\nAshby summary")
    print("------------------")
    print("Total jobs collected:", len(all_jobs))

    return all_jobs