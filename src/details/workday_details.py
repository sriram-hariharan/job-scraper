import json
import re
import requests

from bs4 import BeautifulSoup

from src.utils.http_retry import retry_request
from src.utils.logging import get_logger

logger = get_logger("workday_details")

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})


@retry_request(retries=2)
def workday_get(url, **kwargs):
    return session.get(url, **kwargs)


def clean_text(text):
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()

def build_workday_api_url(job_url):
    """
    Convert Workday job page URL to Workday JSON API endpoint.
    """

    try:
        parts = job_url.split("/")

        host = parts[2]

        tenant = host.split(".")[0]

        site = parts[3]

        job_path = "/".join(parts[4:])

        api_url = f"https://{host}/wday/cxs/{tenant}/{site}/{job_path}"

        return api_url

    except Exception:
        return None

def build_workday_company_jobs_api(job_url):
    """
    Build Workday company jobs API endpoint.

    Example:
    https://capitalone.wd12.myworkdayjobs.com/Capital_One/job/... 

    →

    https://capitalone.wd12.myworkdayjobs.com/wday/cxs/capitalone/Capital_One/jobs
    """

    try:
        parts = job_url.split("/")

        host = parts[2]
        tenant = host.split(".")[0]
        site = parts[3]

        return f"https://{host}/wday/cxs/{tenant}/{site}/jobs"

    except Exception:
        return None

def fetch_workday_company_jobs(job_url):

    api_url = build_workday_company_jobs_api(job_url)

    if not api_url:
        return {}

    try:
        resp = workday_get(api_url, timeout=20)
    except Exception:
        return {}

    if resp is None or resp.status_code != 200:
        return {}

    try:
        data = resp.json()
    except Exception:
        return {}

    job_map = {}

    postings = data.get("jobPostings", [])

    for job in postings:

        external_path = job.get("externalPath")

        desc = job.get("jobDescription")

        if external_path and desc:
            text = clean_text(
                BeautifulSoup(desc, "html.parser").get_text(" ", strip=True)
            )

            job_map[external_path] = (desc, text)

    return job_map
def get_workday_external_path(job_url):

    try:
        parts = job_url.split("/")

        return "/" + "/".join(parts[4:])

    except Exception:
        return None
def extract_from_workday_api(job_url):

    api_url = build_workday_api_url(job_url)

    if not api_url:
        return None, None, None

    try:
        resp = workday_get(api_url, timeout=15)
    except Exception:
        return None, None, None

    if resp is None or resp.status_code != 200:
        return None, None, None

    try:
        data = resp.json()
    except Exception:
        return None, None, None

    desc = data.get("jobPostingInfo", {}).get("jobDescription")

    if desc:
        text = clean_text(BeautifulSoup(desc, "html.parser").get_text(" ", strip=True))
        return desc, text, "api"

    return None, None, None


def extract_from_html(soup):
    """
    Primary Workday job description containers.
    These are the most common patterns on Workday-hosted job pages.
    """
    selectors = [
        '[data-automation-id="jobPostingDescription"]',
        '[data-automation-id="jobDescription"]',
        '[data-automation-id="formattedJobDescription"]',
        '[data-automation-id="externalPosting"]',
        '[data-automation-id="externalJobPostingDescription"]',
    ]

    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            html = str(node)
            text = clean_text(node.get_text(" ", strip=True))
            if text:
                return html, text, "html"

    return None, None, None


def extract_from_json_scripts(html):
    """
    Fallback:
    Some Workday pages embed useful structured JSON in script tags.
    This is intentionally conservative. We only extract if a clear
    description-like field exists.
    """
    soup = BeautifulSoup(html, "html.parser")

    for script in soup.find_all("script"):
        raw = script.string or script.get_text()
        if not raw:
            continue

        raw = raw.strip()
        if not raw:
            continue

        # Only try obvious JSON-looking blobs
        if not (raw.startswith("{") or raw.startswith("[")):
            continue

        try:
            data = json.loads(raw)
        except Exception:
            continue

        result = find_description_in_json(data)
        if result:
            return result, clean_text(BeautifulSoup(result, "html.parser").get_text(" ", strip=True)), "json"

    return None, None, None


def find_description_in_json(obj):
    """
    Recursively search for common description fields.
    """
    target_keys = {
        "jobpostingdescription",
        "jobdescription",
        "description",
        "externaljobdescription",
        "formatteddescription",
        "richtextdescription",
    }

    if isinstance(obj, dict):
        for key, value in obj.items():
            normalized_key = str(key).replace("_", "").lower()

            if normalized_key in target_keys and isinstance(value, str) and value.strip():
                return value

            found = find_description_in_json(value)
            if found:
                return found

    elif isinstance(obj, list):
        for item in obj:
            found = find_description_in_json(item)
            if found:
                return found

    return None


def fetch_workday_details(job):

    url = job.get("url")

    if not url:
        job["_details_fetched"] = "failed"
        return job

    # ---------------------------------------------------
    # 1️⃣ Company-level batch cache
    # ---------------------------------------------------

    if not hasattr(fetch_workday_details, "_company_cache"):
        fetch_workday_details._company_cache = {}

    cache = fetch_workday_details._company_cache

    external_path = get_workday_external_path(url)

    # Populate cache if needed
    if external_path not in cache:

        company_jobs = fetch_workday_company_jobs(url)

        for path, data in company_jobs.items():
            cache[path] = data

    if external_path in cache:

        desc, text = cache[external_path]

        job["description_html"] = desc
        job["description_text"] = text
        job["_details_fetched"] = "company_api"

        return job

    # ---------------------------------------------------
    # 2️⃣ Try per-job Workday API
    # ---------------------------------------------------

    description_html, description_text, method = extract_from_workday_api(url)

    if description_text:
        job["description_html"] = description_html
        job["description_text"] = description_text
        job["_details_fetched"] = method
        return job

    # ---------------------------------------------------
    # 3️⃣ Only fetch HTML page if API fails
    # ---------------------------------------------------

    try:
        response = workday_get(url, timeout=15)
    except Exception:
        response = None

    if response is None or response.status_code != 200:
        job["_details_fetched"] = "failed"
        return job

    html = response.text
    soup = BeautifulSoup(html, "html.parser")

    # ---------------------------------------------------
    # 4️⃣ HTML extraction
    # ---------------------------------------------------

    description_html, description_text, method = extract_from_html(soup)

    # ---------------------------------------------------
    # 5️⃣ JSON script fallback
    # ---------------------------------------------------

    if not description_text:
        description_html, description_text, method = extract_from_json_scripts(html)

    if description_text:
        job["description_html"] = description_html
        job["description_text"] = description_text
        job["_details_fetched"] = method
        return job

    job["_details_fetched"] = "failed"
    return job