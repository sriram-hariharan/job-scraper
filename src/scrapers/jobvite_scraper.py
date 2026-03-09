import requests
from bs4 import BeautifulSoup
from src.utils.html_timestamp_extractor import extract_jsonld_dateposted
from src.utils.http_retry import retry_request
from src.config.consts import JOBVITE_URL_PATTERNS
from models.job import Job
from src.utils.file_loader import load_lines
from src.utils.parallel import run_parallel
from src.utils.logging import get_logger
from src.discovery.learned_companies import learn_from_job_url, load_learned

logger = get_logger("jobvite")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

@retry_request(retries=2)
def jobvite_get(url, **kwargs):
    return session.get(url, **kwargs)

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

    urls = [u.format(company=company) for u in JOBVITE_URL_PATTERNS]

    html = None

    for url in urls:

        r = jobvite_get(url, timeout=10)
        if r is None or r.status_code != 200:
            continue
        html = r.text
        # if page actually contains jobs stop trying
        if "/job/" in html:
            break

    if not html:
        logger.warning(f"{company} no jobvite page found")
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
        learn_from_job_url(job_url)
        posted_at = fetch_jobvite_posted_date(job_url)

        # jobs.append({
        #     "company": company,
        #     "title": title,
        #     "location": "",
        #     "url": job_url,
        #     "source": "jobvite",
        #     "posted_at": posted_at,
        #     "is_new": is_new
        # })
        jobs.append(
            Job(
                company=company,
                title=title,
                location="",
                url=job_url,
                source="jobvite",
                posted_at=posted_at,
                meta={
                    "is_new": is_new
                }
            ).to_dict()
        )

    return jobs

def scrape_all_jobvite():

    companies = load_lines("data/jobvite_companies.txt")
    learned = load_learned()
    companies += learned.get("jobvite", [])

    # remove duplicates
    companies = list(set(companies))
    all_jobs = run_parallel(
        companies,
        fetch_company_jobs,
        max_workers=8,
        desc="Jobvite scraping"
        )
    
    logger.info("Jobvite summary")
    logger.info("------------------")
    logger.info(f"Total jobs collected: {len(all_jobs)}")

    return all_jobs