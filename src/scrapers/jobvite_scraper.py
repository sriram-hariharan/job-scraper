import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup

JOBVITE_API = "https://jobs.jobvite.com/api/jobs/{}"


def load_companies(path="data/jobvite_companies.txt"):

    companies = []

    with open(path) as f:
        for line in f:
            c = line.strip()
            if c:
                companies.append(c)

    return companies

def fetch_company_jobs(company):

    urls = [
        f"https://jobs.jobvite.com/{company}/jobs/alljobs",
        f"https://jobs.jobvite.com/{company}/jobs"
    ]

    html = None

    for url in urls:

        try:
            r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
        except Exception:
            continue

        if r.status_code != 200:
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

        title = link.text.strip()

        job_url = href if href.startswith("http") else f"https://jobs.jobvite.com{href}"

        jobs.append({
            "company": company,
            "title": title,
            "location": "",
            "url": job_url,
            "source": "jobvite"
        })

    print(f"{company} collected:", len(jobs))

    return jobs

def scrape_all_jobvite():

    companies = load_companies()
    all_jobs = []

    with ThreadPoolExecutor(max_workers=10) as executor:

        futures = [executor.submit(fetch_company_jobs, c) for c in companies]

        for future in tqdm(as_completed(futures),
                           total=len(futures),
                           desc="Jobvite scraping"):

            jobs = future.result()
            all_jobs.extend(jobs)

    return all_jobs