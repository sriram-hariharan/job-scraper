import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed


WORKABLE_API = "https://apply.workable.com/api/v1/widget/accounts/{}"


def load_companies(path="data/workable_companies.txt"):

    companies = []

    with open(path) as f:
        for line in f:
            c = line.strip()
            if c:
                companies.append(c)

    return companies


def fetch_company_jobs(company):

    url = WORKABLE_API.format(company)

    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=10)
    except:
        return []

    if r.status_code != 200:
        return []

    data = r.json()

    jobs = []

    for job in data.get("jobs", []):

        jobs.append({
            "company": company,
            "title": job.get("title"),
            "location": job.get("location", ""),
            "url": job.get("url"),
            "source": "workable"
        })

    print(f"{company} total reported:", len(data.get("jobs", [])), " collected:", len(jobs))

    return jobs


def scrape_all_workable():

    companies = load_companies()
    all_jobs = []

    with ThreadPoolExecutor(max_workers=10) as executor:

        futures = [executor.submit(fetch_company_jobs, c) for c in companies]

        for future in tqdm(as_completed(futures),
                           total=len(futures),
                           desc="Workable scraping"):

            jobs = future.result()
            all_jobs.extend(jobs)

    return all_jobs