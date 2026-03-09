import requests
from requests.adapters import HTTPAdapter
import re
from src.config.consts import CAREER_PATHS, WORKDAY_REGEX, CAREER_SUBDOMAINS

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 ATS Discovery Bot"
})

adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
session.mount("https://", adapter)
session.mount("http://", adapter)


def normalize_domain(domain: str) -> str:
    domain = domain.replace("https://", "").replace("http://", "")
    domain = domain.replace("www.", "")
    return domain.strip("/")


def slug_from_domain(domain: str) -> str:
    domain = normalize_domain(domain)
    return domain.split(".")[0]


# -----------------------------
# SLUG EXTRACTION
# -----------------------------

def extract_greenhouse_slug(html):
    m = re.search(r"boards\.greenhouse\.io/([a-zA-Z0-9_-]+)", html)
    return m.group(1) if m else None


def extract_ashby_slug(html):
    m = re.search(r"jobs\.ashbyhq\.com/([a-zA-Z0-9_-]+)", html)
    return m.group(1) if m else None


def extract_lever_slug(html):
    m = re.search(r"lever\.co/([a-zA-Z0-9_-]+)", html)
    return m.group(1) if m else None


def extract_workday_url(html):
    m = WORKDAY_REGEX.search(html)
    return m.group(0) if m else None


def extract_workable_slug(html):
    m = re.search(r"apply\.workable\.com/([a-zA-Z0-9_-]+)", html)
    return m.group(1) if m else None


def extract_jobvite_slug(html):
    m = re.search(r"jobs\.jobvite\.com/([a-zA-Z0-9_-]+)", html)
    return m.group(1) if m else None

def extract_links_from_html(html):
    links = re.findall(r'href=["\'](.*?)["\']', html)
    return links

# -----------------------------
# ATS FINGERPRINT
# -----------------------------

def detect_ats_from_html(html: str):

    if "boards.greenhouse.io" in html:
        return "greenhouse"

    if "jobs.ashbyhq.com" in html:
        return "ashby"

    if "lever.co" in html:
        return "lever"

    if "myworkdayjobs.com" in html:
        return "workday"

    if "apply.workable.com" in html:
        return "workable"

    if "jobs.jobvite.com" in html:
        return "jobvite"

    return None

def detect_ats_from_links(links):

    for link in links:

        if "boards.greenhouse.io" in link:
            return "greenhouse", link

        if "jobs.ashbyhq.com" in link:
            return "ashby", link

        if "lever.co" in link:
            return "lever", link

        if "myworkdayjobs.com" in link:
            return "workday", link

        if "apply.workable.com" in link:
            return "workable", link

        if "jobs.jobvite.com" in link:
            return "jobvite", link

    return None, None


# -----------------------------
# CAREER PAGE FETCH
# -----------------------------

def fetch_career_page(domain: str):

    base = normalize_domain(domain)

    for path in CAREER_PATHS:

        try:
            url = f"https://{base}{path}"
            r = session.get(url, timeout=4, allow_redirects=True)

            if r.status_code == 200 and r.text:
                return r.text

        except Exception:
            pass

    return None

def fetch_career_subdomain(domain: str):

    base = normalize_domain(domain)

    parts = base.split(".")
    root = ".".join(parts[-2:])

    for sub in CAREER_SUBDOMAINS:

        try:
            url = f"https://{sub}.{root}"

            r = session.get(url, timeout=4, allow_redirects=True)

            if r.status_code == 200 and r.text:
                return r.text

        except:
            pass

    return None


# -----------------------------
# VALIDATORS
# -----------------------------

def check_greenhouse(slug: str):

    url = f"https://boards.greenhouse.io/{slug}"

    try:
        r = session.get(url, timeout=2)
        return r.status_code == 200
    except:
        return False


def check_ashby(slug: str):

    url = f"https://jobs.ashbyhq.com/{slug}"

    try:
        r = session.get(url, timeout=2)
        return r.status_code == 200
    except:
        return False


# -----------------------------
# FALLBACK DETECTION
# -----------------------------

def extract_lever_slug_from_domain(domain: str):

    base = normalize_domain(domain)

    candidates = [
        base.split(".")[0],
        base.replace(".com", ""),
        base.replace(".ai", ""),
        base.replace(".io", "")
    ]

    for slug in candidates:

        try:
            url = f"https://api.lever.co/v0/postings/{slug}?mode=json"
            r = session.get(url, timeout=4)

            if r.status_code == 200 and r.json():
                return slug

        except:
            pass

    return None


def extract_workday_board_url(domain: str):

    base = normalize_domain(domain)

    for path in CAREER_PATHS:

        try:
            url = f"https://{base}{path}"
            r = session.get(url, timeout=4, allow_redirects=True)

            if "myworkdayjobs.com" in r.url:
                return r.url.split("?")[0]

            m = WORKDAY_REGEX.search(r.text)
            if m:
                return m.group(0)

        except:
            pass

    return None