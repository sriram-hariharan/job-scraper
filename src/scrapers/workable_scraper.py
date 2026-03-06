import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.utils.http_retry import retry_request
<<<<<<< HEAD

WORKABLE_V3_API = "https://apply.workable.com/api/v3/accounts/{}/jobs"
WORKABLE_V1_API = "https://apply.workable.com/api/v1/widget/accounts/{}"
WORKABLE_V2_DETAIL_API = "https://apply.workable.com/api/v2/accounts/{}/jobs/{}"
=======
from src.config.consts import WORKABLE_V1_API, WORKABLE_V2_DETAIL_API, WORKABLE_V3_API
>>>>>>> main

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


def load_companies(path="data/workable_companies.txt"):

    companies = []

    with open(path) as f:
        for line in f:
            c = line.strip()
            if c:
                companies.append(c)

    return companies


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

    # Some Workable v3 responses are keyed as {"0": {...}, "1": {...}}
    # and some may expose a "results" array.
    if "results" in data and isinstance(data["results"], list):
        return data["results"]

    values = [v for v in data.values() if isinstance(v, dict)]
    return values


def fetch_company_jobs(company):

    jobs_data = []

    # Try v3 first
    v3_url = WORKABLE_V3_API.format(company)

    try:
        r = workable_post(
            v3_url,
            json={"limit": 50, "offset": 0},
            headers={"Content-Type": "application/json"},
            timeout=10
        )

        if r is not None and r.status_code == 200:
            data = r.json()
            jobs_data = extract_v3_jobs(data)

    except Exception:
        pass

    # Fallback to v1 widget API
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

        shortcode = job.get("shortcode")

        url = job.get("url")
        if not url and shortcode:
            url = f"https://apply.workable.com/{company}/j/{shortcode}/"

        jobs.append({
            "company": company,
            "title": job.get("title"),
            "location": location,
            "url": url,
            "source": "workable",
            "posted_at": job.get("published") or job.get("published_on") or job.get("created_at"),
            "_shortcode": shortcode
        })

    # Resolve missing timestamps via v2 detail API
    missing_jobs = [j for j in jobs if not j.get("posted_at") and j.get("_shortcode")]

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

    # Cleanup internal helper field
    for job in jobs:
        job.pop("_shortcode", None)

    return jobs


def scrape_all_workable():

    companies = load_companies()
    all_jobs = []

    with ThreadPoolExecutor(max_workers=10) as executor:

        futures = [executor.submit(fetch_company_jobs, c) for c in companies]

        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Workable scraping"
        ):
            jobs = future.result()
            all_jobs.extend(jobs)

    print("\nWorkable summary")
    print("------------------")
    print("Total jobs collected:", len(all_jobs))

    return all_jobs