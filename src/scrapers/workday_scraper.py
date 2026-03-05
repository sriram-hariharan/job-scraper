import requests
import time
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


def load_companies(path="data/workday_companies.txt"):
    companies = []
    with open(path) as f:
        for line in f:
            url = line.strip()
            if url:
                companies.append(url)
    return companies
    # return [
    #     "https://motorolasolutions.wd5.myworkdayjobs.com/Careers",
    #     "https://iqvia.wd1.myworkdayjobs.com/IQVIA"
    # ]


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

    api_url = f"https://{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"

    origin = f"https://{host}.myworkdayjobs.com"

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

    # Discover US facet id
    payload = {"limit": 1, "offset": 0, "searchText": ""}
    r = session.post(api_url, json=payload, headers=headers, timeout=10)
    if r.status_code != 200:
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

        if country_filter:
            payload["appliedFacets"] = {
                facet_name: [country_filter]
            }

        try:
            r = session.post(api_url, json=payload, headers=headers, timeout=10)
            if r.status_code != 200:
                break
            data = r.json()
        except Exception:
            break

        # Set total once (or keep updating if you want)
        if total is None:
            total = data.get("total")
            # If API doesn't provide total, fallback to old stopping logic
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

            location = job.get("locationsText", "")

            jobs.append({
                "title": job.get("title"),
                "location": location,
                "url": f"{board_url.rstrip('/')}/{job_id.lstrip('/')}",
                "company": tenant,
                "source": "workday"
            })

        if new_jobs_this_page == 0:
            break
        offset += limit

        

        # Stop condition: prefer total when available
        if total is not None and offset >= total:
            break

        # Fallback stop condition if total is missing
        if total is None and len(postings) < limit:
            break
        time.sleep(0.05)
    print(f"{tenant} total reported:", data.get("total"), " collected:", len(seen_jobs))
    return jobs

def scrape_all_workday():

    companies = load_companies()
    all_jobs = []

    with ThreadPoolExecutor(max_workers=10) as executor:

        futures = [executor.submit(scrape_company, c) for c in companies]

        for future in tqdm(as_completed(futures), total=len(futures), desc="Workday scraping"):
            jobs = future.result()
            all_jobs.extend(jobs)

    return all_jobs