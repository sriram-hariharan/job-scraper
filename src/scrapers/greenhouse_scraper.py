import asyncio
import aiohttp
from tqdm import tqdm


GREENHOUSE_API = "https://boards-api.greenhouse.io/v1/boards/{}/jobs"


def load_companies(path="data/greenhouse_companies.txt"):
    companies = []

    with open(path, "r") as f:
        for line in f:
            c = line.strip()
            if c:
                companies.append(c)

    return companies


async def fetch_company_jobs(session, company):

    url = GREENHOUSE_API.format(company)

    try:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:

            if resp.status != 200:
                print(f"{company} failed: status {resp.status}")
                return []

            data = await resp.json()

    except Exception as e:
        print(f"{company} error:", e)
        return []

    jobs = []

    postings = data.get("jobs", [])

    for job in postings:

        title = job.get("title")
        location = job.get("location", {}).get("name", "")
        job_url = job.get("absolute_url")

        jobs.append({
            "company": company,
            "title": title,
            "location": location,
            "url": job_url,
            "source": "greenhouse"
        })

    print(f"{company} total reported:", len(postings), " collected:", len(jobs))

    return jobs


async def scrape_all_greenhouse_async():

    companies = load_companies()

    connector = aiohttp.TCPConnector(limit=50)

    all_jobs = []

    async with aiohttp.ClientSession(connector=connector) as session:

        tasks = [fetch_company_jobs(session, c) for c in companies]

        for future in tqdm(asyncio.as_completed(tasks),
                           total=len(tasks),
                           desc="Greenhouse scraping"):

            jobs = await future
            all_jobs.extend(jobs)

    return all_jobs


def scrape_all_greenhouse():

    jobs = asyncio.run(scrape_all_greenhouse_async())

    print("\nGreenhouse summary")
    print("------------------")
    print("Total jobs collected:", len(jobs))

    return jobs