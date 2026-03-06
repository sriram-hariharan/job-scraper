import asyncio
import aiohttp
from tqdm import tqdm


LEVER_API = "https://api.lever.co/v0/postings"


def load_lever_companies(path="data/lever_companies.txt"):

    companies = []

    try:
        with open(path, "r") as f:
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
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:

            if resp.status != 200:
                # print(f"{company} failed: status {resp.status}")
                return []

            data = await resp.json()

    except Exception as e:
        print(f"{company} error:", e)
        return []

    jobs = []

    for job in data:

        title = job.get("text", "")
        location = job.get("categories", {}).get("location", "")
        job_url = job.get("hostedUrl", "")

        jobs.append({
            "company": company,
            "title": title,
            "location": location,
            "url": job_url,
            "source": "lever",
            "posted_at": job.get("createdAt")
        })

    return jobs


async def scrape_all_lever_async():

    companies = load_lever_companies()

    connector = aiohttp.TCPConnector(limit=50)

    all_jobs = []

    async with aiohttp.ClientSession(connector=connector) as session:

        sem = asyncio.Semaphore(50)
        async def limited_fetch(company):
            async with sem:
                return await fetch_company_jobs(session, company)

        tasks = [limited_fetch(c) for c in companies]

        for future in tqdm(asyncio.as_completed(tasks),
                           total=len(tasks),
                           desc="Lever scraping"):

            jobs = await future
            all_jobs.extend(jobs)

    return all_jobs


def scrape_all_lever():

    jobs = asyncio.run(scrape_all_lever_async())

    print("\nLever summary")
    print("------------------")
    print("Total jobs collected:", len(jobs))

    return jobs