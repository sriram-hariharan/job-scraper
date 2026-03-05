import asyncio
import aiohttp
from src.pipeline.job_filter import title_matches, us_location


GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{}/jobs"


def load_companies():

    companies = []

    with open("data/greenhouse_companies.txt", "r") as f:
        for line in f:
            c = line.strip()

            if c:
                companies.append(c)

    return companies


async def fetch_company_jobs(session, company):

    url = GREENHOUSE_API.format(company)

    try:
        async with session.get(url) as resp:

            if resp.status != 200:
                return []

            data = await resp.json()

    except:
        return []

    jobs = []

    for job in data.get("jobs", []):

        title = job["title"]
        location = job["location"]["name"]
        job_url = job["absolute_url"]

        if not title_matches(title):
            continue

        if not us_location(location):
            continue

        jobs.append({
            "company": company,
            "title": title,
            "location": location,
            "url": job_url
        })

    return jobs


async def scrape_all_greenhouse_async():

    companies = load_companies()

    connector = aiohttp.TCPConnector(limit=50)

    async with aiohttp.ClientSession(connector=connector) as session:

        tasks = []
        for company in companies:
            tasks.append(fetch_company_jobs(session, company))

        results = await asyncio.gather(*tasks)

    all_jobs = []

    for job_list in results:
        all_jobs.extend(job_list)
    return all_jobs

def scrape_all_greenhouse():

    return asyncio.run(scrape_all_greenhouse_async())