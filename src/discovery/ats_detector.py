import requests
from requests.adapters import HTTPAdapter
import re
from src.config.consts import CAREER_PATHS, WORKDAY_REGEX, CAREER_SUBDOMAINS
import requests

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
    m = re.search(r"jobs\.ashbyhq\.com/([a-z0-9\-]+)", html.lower())
    if m:
        return m.group(1)
    return None


def extract_lever_slug(html):
    m = re.search(r"jobs\.lever\.co/([a-zA-Z0-9_-]+)", html)
    if m:
        return m.group(1)
    m = re.search(r"api\.lever\.co/v0/postings/([a-zA-Z0-9_-]+)", html)
    if m:
        return m.group(1)
    return None

def extract_workday_url(html):
    m = re.search(r"https://[a-z0-9\-]+\.myworkdayjobs\.com/[^\"]+", html)
    if m:
        return m.group(0).split("?")[0]

    return None


def extract_workable_slug(html):
    m = re.search(r"apply\.workable\.com/([a-z0-9\-]+)", html.lower())
    return m.group(1) if m else None


def extract_jobvite_slug(html):
    m = re.search(r"jobs\.jobvite\.com/([a-zA-Z0-9_-]+)", html)
    return m.group(1) if m else None

def extract_links_from_html(html):
    if not html:
        return []
    html = html.lower()
    links = re.findall(
        r'(?:href|src|data-url|data-href|data-src)=["\'](.*?)["\']',
        html
    )
    return links

# -----------------------------
# ATS FINGERPRINT
# -----------------------------

def detect_ats_from_html(html: str):

    if "boards.greenhouse.io" in html:
        return "greenhouse"

    if "jobs.ashbyhq.com" in html:
        return "ashby"

    if "jobs.lever.co" in html or "api.lever.co/v0/postings/" in html:
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

        link = link.lower()

        if "boards.greenhouse.io/" in link:
            return "greenhouse", link

        if "jobs.ashbyhq.com/" in link:
            return "ashby", link

        if "jobs.lever.co/" in link or "api.lever.co/v0/postings/" in link:
            return "lever", link

        if "myworkdayjobs.com" in link:
            return "workday", link

        if "apply.workable.com/" in link:
            return "workable", link

        if "jobs.jobvite.com/" in link:
            return "jobvite", link

    return None, None

def detect_ats_from_redirect(domain):

    paths = [
    "",
    "/careers",
    "/careers/",
    "/jobs",
    "/jobs/",
    "/join-us",
    "/join",
    "/work-with-us",
    "/careers/openings",
    "/company/careers"
    ]

    headers = {"User-Agent": "Mozilla/5.0"}

    for path in paths:

        url = f"https://{domain}{path}"

        try:
            r = requests.get(url, headers=headers, timeout=2, allow_redirects=True)
        except Exception:
            continue

        final_url = r.url.lower()

        if "boards.greenhouse.io" in final_url:
            slug = final_url.split("boards.greenhouse.io/")[1].split("/")[0]
            return "greenhouse", slug

        if "jobs.ashbyhq.com" in final_url:
            slug = final_url.split("jobs.ashbyhq.com/")[1].split("/")[0]
            return "ashby", slug

        if "jobs.lever.co/" in final_url:
            slug = final_url.split("jobs.lever.co/")[1].split("/")[0]
            return "lever", slug

        if "apply.workable.com" in final_url:
            slug = final_url.split("apply.workable.com/")[1].split("/")[0]
            return "workable", slug

        if "jobs.jobvite.com" in final_url:
            slug = final_url.split("jobs.jobvite.com/")[1].split("/")[0]
            return "jobvite", slug

        if "myworkdayjobs.com" in final_url:
            return "workday", final_url.split("?")[0]

    return None, None
def detect_ats_from_embeds(html):

    if not html:
        return None, None

    html = html.lower()

    # only match actual embedded URLs
    patterns = [
        ("greenhouse", r"boards\.greenhouse\.io/([a-z0-9\-]+)"),
        ("ashby", r"jobs\.ashbyhq\.com/([a-z0-9\-]+)/"),
        ("lever", r"jobs\.lever\.co/([a-z0-9\-]+)"),
        ("lever", r"api\.lever\.co/v0/postings/([a-z0-9\-]+)"),
        ("workable", r"apply\.workable\.com/([a-z0-9\-]+)"),
        ("jobvite", r"jobs\.jobvite\.com/([a-z0-9\-]+)"),
        ("workday", r"(https:\/\/[a-z0-9\-]+\.myworkdayjobs\.com\/[^\"'\s]+)")
    ]

    for ats, pattern in patterns:
        m = re.search(pattern, html)
        if m:
            if ats == "workday":
                return ats, m.group(1).split("?")[0]
            return ats, m.group(1)

    return None, None
# -----------------------------
# CAREER PAGE FETCH
# -----------------------------

def fetch_career_page(domain: str):

    base = normalize_domain(domain)

    for path in CAREER_PATHS:

        try:
            url = f"https://{base}{path}"

            r = session.get(
                url,
                timeout=2,
                allow_redirects=True,
                headers={"User-Agent": "Mozilla/5.0"}
            )

            if r.status_code == 200:
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

            r = session.get(url, timeout=2, allow_redirects=True)

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

        if r.status_code != 200:
            return False

        html = r.text.lower()
        # verify real ashby board content
        if "ashbyhq" in html and "jobs" in html:
            return True

        return False

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
            r = session.get(url, timeout=2)

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
            r = session.get(url, timeout=2, allow_redirects=True)

            if "myworkdayjobs.com" in r.url:
                return r.url.split("?")[0]

            m = WORKDAY_REGEX.search(r.text)
            if m:
                return m.group(0)

        except:
            pass

    return None