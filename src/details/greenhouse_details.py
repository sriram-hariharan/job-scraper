from src.utils.http_retry import http_get
from src.utils.logging import get_logger
from bs4 import BeautifulSoup
import json
import html
import re
from threading import Lock

logger = get_logger("greenhouse_details")
company_cache_lock = Lock()

def fetch_greenhouse_company_jobs(company):

    url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs?content=true"

    try:
        resp = http_get(url)
    except Exception:
        return {}

    if not resp or resp.status_code != 200:
        return {}

    try:
        data = resp.json()
    except Exception:
        return {}

    job_map = {}

    for job in data.get("jobs", []):

        job_id = job.get("id")

        content = html.unescape(job.get("content", ""))

        if job_id and content:

            text = BeautifulSoup(content, "html.parser").get_text(" ", strip=True)

            job_map[job_id] = (content, text)

    return job_map

def extract_greenhouse_slug(url):

    m = re.search(r"boards\.greenhouse\.io/([a-zA-Z0-9_-]+)", url)
    if m:
        return m.group(1)

    m = re.search(r"job-boards\.greenhouse\.io/([a-zA-Z0-9_-]+)", url)
    if m:
        return m.group(1)

    return None

def fetch_greenhouse_api(company, job_id):
    logger.info(f"Greenhouse API attempt: {company} {job_id}")
    try:
        clean_id = job_id.replace("gh_", "")
        url = f"https://boards-api.greenhouse.io/v1/boards/{company}/jobs/{clean_id}"

        r = http_get(url, timeout=10)

        if r.status_code != 200:
            return None

        data = r.json()
        content = html.unescape(data.get("content", ""))

        if not content:
            return None
        
        return content

    except Exception:
        return None
    
def fetch_greenhouse_details(job):

    if not hasattr(fetch_greenhouse_details, "_company_cache"):
        fetch_greenhouse_details._company_cache = {}

    cache = fetch_greenhouse_details._company_cache

    company = job.get("company")
    job_id = job.get("job_id")
    url = job.get("url")

    if not url:
        job["_details_fetched"] = "failed"
        return job

    # -----------------------------
    # 1️⃣ Company batch API FIRST
    # -----------------------------

    if company not in cache:
        with company_cache_lock:
            if not company:
                job["_details_fetched"] = "failed"
                return job
            if company not in cache:
                company_jobs = fetch_greenhouse_company_jobs(company)
                cache[company] = company_jobs

    company_jobs = cache.get(company, {})

    clean_id = job_id.replace("gh_", "") if job_id else None

    if clean_id and clean_id in company_jobs:

        desc, text = company_jobs[clean_id]

        job["description_html"] = desc
        job["description_text"] = text
        job["_details_fetched"] = "company_api"

        return job

    # -----------------------------
    # 2️⃣ Job-level Greenhouse API
    # -----------------------------

    api_desc = fetch_greenhouse_api(company, job_id)

    if api_desc:
        job["description_html"] = api_desc
        job["description_text"] = BeautifulSoup(api_desc, "html.parser").get_text(" ", strip=True)
        job["_details_fetched"] = "api"
        return job

    # -----------------------------
    # 3️⃣ Fetch page only if APIs fail
    # -----------------------------

    try:
        r = http_get(url, timeout=10)

        if r.status_code != 200:
            job["_details_fetched"] = "failed"
            return job

        page_html = r.text

    except Exception:
        job["_details_fetched"] = "failed"
        return job

    soup = BeautifulSoup(page_html, "html.parser")

    # -----------------------------
    # 4️⃣ Next.js extraction
    # -----------------------------

    next_data = soup.find("script", {"id": "__NEXT_DATA__"})

    if next_data:
        try:
            data = json.loads(next_data.string)

            page_props = data.get("props", {}).get("pageProps", {})

            jobs = page_props.get("jobs")

            if isinstance(jobs, dict):
                for j in jobs.values():
                    if j.get("url") and j.get("url") in url:

                        content = html.unescape(j.get("content", ""))

                        if content:
                            job["description_html"] = content
                            job["description_text"] = BeautifulSoup(content, "html.parser").get_text(" ", strip=True)
                            job["_details_fetched"] = "nextjs"
                            return job

            single_job = page_props.get("job")

            if single_job and single_job.get("content"):
                dec_html = html.unescape(single_job.get("content", ""))

                job["description_html"] = dec_html
                job["description_text"] = BeautifulSoup(dec_html, "html.parser").get_text(" ", strip=True)
                job["_details_fetched"] = "nextjs"
                return job

        except Exception:
            pass

    # -----------------------------
    # 5️⃣ Classic HTML extraction
    # -----------------------------

    desc = soup.find("div", {"id": "job-description"})

    if not desc:
        desc = soup.find("div", {"class": "job__description"})

    if not desc:
        desc = soup.find("div", {"class": "section-wrapper"})

    if desc:

        text = desc.get_text(" ", strip=True)

        if len(text) >= 200:
            job["description_html"] = str(desc)
            job["description_text"] = text
            job["_details_fetched"] = "html"
            return job

    logger.warning(f"Greenhouse description not found: {url}")

    job["_details_fetched"] = "failed"
    return job