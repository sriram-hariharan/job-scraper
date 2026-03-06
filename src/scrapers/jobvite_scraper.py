import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup
from src.utils.html_timestamp_extractor import extract_jsonld_dateposted
from src.utils.http_retry import retry_request


session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


@retry_request(retries=2)
def jobvite_get(url, **kwargs):
    return session.get(url, **kwargs)

JOBVITE_API = "https://jobs.jobvite.com/api/jobs/{}"

def load_companies(path="data/jobvite_companies.txt"):

    companies = []

    with open(path) as f:
        for line in f:
            c = line.strip()
            if c:
                companies.append(c)

    return companies

def fetch_jobvite_posted_date(job_url):

    try:
        r = jobvite_get(job_url, timeout=10)
        if r is None or r.status_code != 200:
            return None
    except Exception:
        return None

    html = r.text

    # Use shared JSON-LD extractor
    ts = extract_jsonld_dateposted(html)

    return ts

def fetch_company_jobs(company):

    urls = [
        f"https://jobs.jobvite.com/{company}/jobs/alljobs",
        f"https://jobs.jobvite.com/{company}/jobs"
    ]

    html = None

    for url in urls:

        try:
            r = jobvite_get(url, timeout=10)
        except Exception:
            continue
        if r is None or r.status_code != 200:
            continue

        html = r.text
        # if page actually contains jobs stop trying
        if "/job/" in html:
            break

    if not html:
        print(f"{company} no page")
        return []

    soup = BeautifulSoup(html, "html.parser")

    jobs = []

    links = soup.find_all("a", href=True)

    for link in links:

        href = link["href"]

        if "/job/" not in href:
            continue

        # find job container
        container = link.find_parent("div")

        is_new = False
        if container:
            if container.find("span", class_="jv-tag-new"):
                is_new = True

        title = link.text.strip()

        job_url = href if href.startswith("http") else f"https://jobs.jobvite.com{href}"
        posted_at = fetch_jobvite_posted_date(job_url)

        jobs.append({
            "company": company,
            "title": title,
            "location": "",
            "url": job_url,
            "source": "jobvite",
            "posted_at": posted_at,
            "is_new": is_new
        })

    return jobs

def scrape_all_jobvite():

    companies = load_companies()
    all_jobs = []

    with ThreadPoolExecutor(max_workers=20) as executor:

        futures = [executor.submit(fetch_company_jobs, c) for c in companies]

        for future in tqdm(as_completed(futures),
                           total=len(futures),
                           desc="Jobvite scraping"):

            jobs = future.result()
            all_jobs.extend(jobs)
    
    print("\nJobvite summary")
    print("------------------")
    print("Total jobs collected:", len(all_jobs))

    return all_jobs