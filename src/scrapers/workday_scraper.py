import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from src.discovery.ats_detector import session

def load_companies(path="data/workday_companies.txt"):

    companies = []
    with open(path) as f:
        for line in f:
            url = line.strip()
            if url:
                companies.append(url)

    return companies


def scrape_company(board_url):

    host = board_url.split(".myworkdayjobs.com")[0].replace("https://", "")
    tenant = host.split(".")[0]
    site = board_url.split(".myworkdayjobs.com/")[1].strip("/")

    api_url = f"https://{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"


    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": "Mozilla/5.0",
        "Origin": board_url,
        "Referer": board_url + "/"
    }

    jobs = []
    offset = 0
    limit = 100

    while True:

        payload = {
            "appliedFacets": {},
            "limit": limit,
            "offset": offset,
            "searchText": ""
        }

        try:
            r = session.post(api_url, json=payload, headers=headers, timeout=10)
            print(api_url, r.status_code)
            if r.status_code != 200:
                break

            data = r.json()
            print(data.keys())

        except Exception as e:
            print("Workday error:", e)
            break

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

        for job in postings:

            jobs.append({
                "title": job.get("title"),
                "location": job.get("locationsText"),
                "url": f"{board_url.rstrip('/')}/{job.get('externalPath','').lstrip('/')}",
                "company": board_url.split(".")[0].replace("https://", ""),
                "source": "workday"
            })

        offset += limit

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