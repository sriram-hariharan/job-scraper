import requests
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed


ASHBY_URL = "https://jobs.ashbyhq.com/api/non-user-graphql"

QUERY = """
query JobBoard($organizationHostedJobsPageName: String!) {
  jobBoardWithTeams(
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


def load_companies(path="data/ashby_companies.txt"):
    companies = []

    with open(path) as f:
        for line in f:
            c = line.strip()
            if c:
                companies.append(c)

    return companies


def fetch_company_jobs(company):

    jobs = []

    payload = {
        "operationName": "JobBoard",
        "query": QUERY,
        "variables": {
            "organizationHostedJobsPageName": company
        }
    }

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
        jobs_data = data["data"]["jobBoardWithTeams"]["jobPostings"]
    except:
        return []

    for job in jobs_data:

        title = job.get("title", "")
        location = job.get("locationName", "")

        jobs.append({
            "company": company,
            "title": title,
            "location": location,
            "url": f"https://jobs.ashbyhq.com/{company}/{job['id']}",
            "source": "ashby"
        })

    print(f"{company} total reported:", len(jobs_data), " collected:", len(jobs))

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

    return all_jobs