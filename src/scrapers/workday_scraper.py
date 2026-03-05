import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import time
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
                # company = (url.split("https://")[1].split(".")[0])
                # if company == "otis":
                #     print("\n\nFound Otis in company list \n\n")
                    companies.append(url)
    return companies

def get_us_country_id(data):

    facets = data.get("facetMetadata", {}).get("facets", [])

    for facet in facets:
        if facet.get("name") == "locationCountry":

            for val in facet.get("values", []):
                if val.get("label") == "United States":
                    return val.get("id")

    return None

def scrape_company(board_url):

    host = board_url.split(".myworkdayjobs.com")[0].replace("https://", "")
    tenant = host.split(".")[0]
    site = board_url.split(".myworkdayjobs.com/")[1].split("?")[0].strip("/")

    api_url = f"https://{host}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"


    origin = f"https://{host}.myworkdayjobs.com"
    referer = board_url  # full page URL is fine as referer

    headers = {
    "Content-Type": "application/json",
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "User-Agent": "Mozilla/5.0",
    "Origin": origin,
    "Referer": referer,
    "X-Requested-With": "XMLHttpRequest",
    "Connection": "keep-alive"
    }

    jobs = []
    offset = 0
    limit = 20
    max_pages = 3
    page = 0
    country_filter = None

    #Country discovery
    payload = {
    "limit": 1,
    "offset": 0
    }

    r = session.post(api_url, data=json.dumps(payload), headers=headers, timeout=10)

    if r.status_code != 200:
        return []

    data = r.json()
    country_filter = get_us_country_id(data)

    while True:
        payload = {
            "limit": limit,
            "offset": offset,
        }

        if country_filter:
            payload["appliedFacets"] = {
                "locationCountry": [country_filter]
            }

        try:
            r = session.post(
                api_url,
                data = json.dumps(payload),
                headers=headers,
                timeout=10
            )
            if r.status_code != 200:
                break

            data = r.json()

            # if country_filter is None:
            #     country_filter = get_us_country_id(data)

            #     # restart pagination with filter
            #     offset = 0
            #     jobs = []
            #     continue

            time.sleep(0.05)

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

            location = job.get("locationsText", "")

            if "United States" in location or "USA" in location:
                jobs.append({
                    "title": job.get("title"),
                    "location": location,
                    "url": f"{board_url.rstrip('/')}/{job.get('externalPath','').lstrip('/')}",
                    "company": tenant,
                    "source": "workday"
                })

        offset += limit
        page += 1
        # print(f"Scraped page: {page}\n")
        tqdm.write(f"Scraped {len(jobs)} jobs (page {page})")
        if page >= max_pages:
            break
    print(list(j["location"] for j in jobs))
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