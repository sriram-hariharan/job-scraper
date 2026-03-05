import requests


def load_companies(path="data/workday_companies.txt"):

    companies = []

    with open(path) as f:

        for line in f:

            domain = line.strip()

            if domain:
                companies.append(domain)

    return companies


def scrape_company(domain):

    base = domain.replace("https://", "").replace("http://", "")

    possible_hosts = ["wd1", "wd3", "wd5"]

    jobs = []

    for wd in possible_hosts:

        url = f"https://{base}.{wd}.myworkdayjobs.com/wday/cxs/{base}/jobs"

        payload = {
            "limit": 20,
            "offset": 0
        }

        headers = {"Content-Type": "application/json"}

        try:

            r = requests.post(url, json=payload, headers=headers)

            if r.status_code != 200:
                continue

            data = r.json()

        except:
            continue

        for job in data.get("jobPostings", []):

            jobs.append({
                "title": job.get("title"),
                "location": job.get("locationsText"),
                "url": job.get("externalPath"),
                "company": base,
                "source": "workday"
            })

        if jobs:
            break

    return jobs

def scrape_all_workday():

    companies = load_companies()

    all_jobs = []

    for domain in companies:

        jobs = scrape_company(domain)
        all_jobs.extend(jobs)

    return all_jobs