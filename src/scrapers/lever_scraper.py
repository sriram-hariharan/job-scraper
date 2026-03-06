import asyncio
import aiohttp
<<<<<<< Updated upstream
from src.pipeline.job_filter import title_matches, us_location


LEVER_API = "https://api.lever.co/v0/postings"

=======
from tqdm import tqdm
from src.config.consts import LEVER_API
>>>>>>> Stashed changes

def load_lever_companies():

    companies = []

    try:
        with open("data/lever_companies.txt", "r") as f:
            for line in f:
                c = line.strip()
                if c:
                    companies.append(c)
    except:
        pass

    return companies


async def fetch_company_jobs(session, company):

    url = f"{LEVER_API}/{company}?mode=json"

    try:
        async with session.get(url) as resp:

            if resp.status != 200:
                return []

            data = await resp.json()
    except:
        return []

    jobs = []

    for job in data:
        title = job.get("text", "")
        location = job.get("categories", {}).get("location", "")
        job_url = job.get("hostedUrl", "")

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


async def scrape_all_lever_async():

    companies = load_lever_companies()

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


def scrape_all_lever():

    return asyncio.run(scrape_all_lever_async())