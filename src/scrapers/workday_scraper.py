import requests
<<<<<<< Updated upstream
=======
import time
from tqdm import tqdm
from src.utils.http_retry import retry_request
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.config.consts import (
    WORKDAY_API_URL_TEMPLATE,
    WORKDAY_ORIGIN_TEMPLATE)
>>>>>>> Stashed changes



def load_companies(path="data/workday_companies.txt"):

    companies = []

    with open(path) as f:

        for line in f:

            domain = line.strip()

            if domain:
                companies.append(domain)

    return companies

<<<<<<< Updated upstream

def scrape_company(domain):

    base = domain.replace("https://", "").replace("http://", "")

    possible_hosts = ["wd1", "wd3", "wd5"]
=======
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
    host = board_url.split(".myworkdayjobs.com")[0].replace("https://", "")
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
>>>>>>> Stashed changes

    jobs = []

<<<<<<< Updated upstream
    for wd in possible_hosts:

        url = f"https://{base}.{wd}.myworkdayjobs.com/wday/cxs/{base}/jobs"
=======
    payload = {"limit": 1, "offset": 0, "searchText": ""}
    r = workday_post(api_url, json=payload, headers=headers, timeout=10)
    if r.status_code != 200:
        return []

    data = r.json()
    facet_name, country_filter = get_us_country_facet(data)
    total = None
>>>>>>> Stashed changes

        payload = {
            "limit": 20,
            "offset": 0
        }

        headers = {"Content-Type": "application/json"}

        try:

<<<<<<< Updated upstream
            r = requests.post(url, json=payload, headers=headers)

            if r.status_code != 200:
                continue
=======
            if r is not None and r.status_code == 400 and "appliedFacets" in payload:
                payload.pop("appliedFacets")
                r = workday_post(api_url, json=payload, headers=headers, timeout=10)

            if r.status_code != 200:
                break
>>>>>>> Stashed changes

            data = r.json()

<<<<<<< Updated upstream
        except:
            continue

        for job in data.get("jobPostings", []):

            jobs.append({
                "title": job.get("title"),
                "location": job.get("locationsText"),
                "url": job.get("externalPath"),
                "company": base,
                "source": "workday"
=======
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

            jobs.append({
                "title": job.get("title"),
                "location": locations,  
                "url": job_url,
                "company": tenant,
                "source": "workday",
                "posted_at": posted_at,
                "_externalPath": job.get("externalPath"),
                "_board_url": board_url,
>>>>>>> Stashed changes
            })

        if jobs:
            break
<<<<<<< Updated upstream
=======

        offset += limit

        if total is not None and offset >= total:
            break

        if total is None and len(postings) < limit:
            break

        time.sleep(0.05)
>>>>>>> Stashed changes

    return jobs

def scrape_all_workday():

    companies = load_companies()

    all_jobs = []

    for domain in companies:

<<<<<<< Updated upstream
        jobs = scrape_company(domain)
        all_jobs.extend(jobs)
=======
        futures = [executor.submit(scrape_company, c) for c in companies]

        for future in tqdm(
            as_completed(futures),
            total=len(futures),
            desc="Workday scraping"
        ):
            jobs = future.result()
            all_jobs.extend(jobs)

    print("\nWorkday summary")
    print("------------------")
    print("Total jobs collected:", len(all_jobs))
>>>>>>> Stashed changes

    return all_jobs