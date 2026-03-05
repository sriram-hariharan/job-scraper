import requests
from src.pipeline.job_filter import title_matches, us_location

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


def load_companies():
    companies = []

    with open("data/ashby_companies.txt") as f:
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
        r = requests.post(ASHBY_URL, json=payload)
    except:
        return jobs

    if r.status_code != 200:
        return jobs

    data = r.json()

    try:
        jobs_data = data["data"]["jobBoardWithTeams"]["jobPostings"]
    except:
        return jobs

    for job in jobs_data:

        title = job.get("title", "")
        location = job.get("locationName", "")

        if not title_matches(title):
            continue

        if not us_location(location):
            continue

        jobs.append({
            "company": company,
            "title": title,
            "location": location,
            "url": f"https://jobs.ashbyhq.com/{company}/{job['id']}"
        })

    return jobs


def scrape_all_ashby():

    companies = load_companies()

    all_jobs = []

    for company in companies:
        jobs = fetch_company_jobs(company)
        all_jobs.extend(jobs)

    return all_jobs