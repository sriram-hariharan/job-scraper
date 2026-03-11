from src.utils.http_retry import http_get
from src.utils.logging import get_logger
from bs4 import BeautifulSoup
import json
import html
import re

logger = get_logger("greenhouse_details")

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

    url = job.get("url")

    if not url:
        job["_details_fetched"] = "failed"
        return job

    try:
        r = http_get(url, timeout=10)

        if r.status_code != 200:
            job["_details_fetched"] = "failed"
            return job

        page_html = r.text

    except Exception:
        job["_details_fetched"] = "failed"
        return job


    # ---------- Next.js JSON extraction ----------

    soup = BeautifulSoup(page_html, "html.parser")

    next_data = soup.find("script", {"id": "__NEXT_DATA__"})

    if next_data:
        try:
            data = json.loads(next_data.string)

            page_props = data.get("props", {}).get("pageProps", {})

            # case 1: job list
            jobs = page_props.get("jobs")

            if isinstance(jobs, dict):
                for j in jobs.values():
                    if j.get("url") and j.get("url") in url:
                        job["description_html"] = j.get("content")
                        job["description_text"] = BeautifulSoup(j.get("content"), "html.parser").get_text(" ", strip=True)
                        job["_details_fetched"] = "nextjs"
                        return job

            # case 2: single job
            single_job = page_props.get("job")

            if single_job and single_job.get("content"):
                dec_html = single_job.get("content")
                job["description_html"] = dec_html
                job["description_text"] = BeautifulSoup(dec_html, "html.parser").get_text(" ", strip=True)
                job["_details_fetched"] = "nextjs"
                return job

        except Exception:
            pass


    # ---------- Classic Greenhouse HTML extraction ----------

    desc = soup.find("div", {"id": "job-description"})

    if not desc:
        desc = soup.find("div", {"class": "job__description"})

    if not desc:
        desc = soup.find("div", {"class": "section-wrapper"})

    if desc:
        text = desc.get_text(" ", strip=True)

        # reject tiny containers
        if len(text) >= 200:
            job["description_html"] = str(desc)
            job["description_text"] = text
            job["_details_fetched"] = "html"
            return job

    # ---------- Greenhouse API fallback ----------

    company = job.get("company")
    job_id = job.get("job_id")

    api_desc = fetch_greenhouse_api(company, job_id)

    if api_desc:
        job["description_html"] = api_desc
        job["description_text"] = BeautifulSoup(api_desc, "html.parser").get_text(" ", strip=True)
        job["_details_fetched"] = "api"
        return job

    logger.warning(f"Greenhouse description not found: {url}")
    job["_details_fetched"] = "failed"
    return job