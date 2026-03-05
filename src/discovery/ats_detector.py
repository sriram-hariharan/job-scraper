import requests
import re
from requests.adapters import HTTPAdapter

CAREER_PATHS = [
    "/careers",
    "/careers/",
    "/jobs",
    "/jobs/",
    "/careers/jobs",
    "/careers/jobs/",
    "/join-us",
    "/join-us/",
    "/work-with-us",
    "/work-with-us/",
]

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 ATS Discovery Bot"
})
adapter = HTTPAdapter(pool_connections=100, pool_maxsize=100)
session.mount("https://", adapter)
session.mount("http://", adapter)

def slug_from_domain(domain):

    domain = domain.replace("https://", "")
    domain = domain.replace("http://", "")
    domain = domain.replace("www.", "")

    return domain.split(".")[0]


def check_greenhouse(slug):

    url = f"https://boards.greenhouse.io/{slug}"

    try:
        r = session.get(url, timeout=2)
        return r.status_code == 200
    except:
        return False


def check_ashby(slug):

    url = f"https://jobs.ashbyhq.com/{slug}"

    try:
        r = session.get(url, timeout=2)
        return r.status_code == 200
    except:
        return False


def check_workday(domain):

    base = domain.replace("https://", "").replace("http://", "").strip()

    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    for path in CAREER_PATHS:

        try:

            url = f"https://{base}{path}"

            r = session.get(url, headers=headers, timeout=2, allow_redirects=True)

            final_url = r.url

            if "myworkdayjobs.com" in final_url:
                return True

            if "myworkdayjobs.com" in r.text:
                return True

        except:
            pass

    return False

def extract_workday_board_url(domain):

    base = domain.replace("https://", "").replace("http://", "").strip()

    headers = {"User-Agent": "Mozilla/5.0"}

    for path in CAREER_PATHS:

        try:
            url = f"https://{base}{path}"
            r = session.get(url, headers=headers, timeout=2, allow_redirects=True)

            # 1) if it redirected straight to workday
            if "myworkdayjobs.com" in r.url:
                return r.url.split("?")[0]

            # 2) otherwise parse the html for a workday link
            m = re.search(r"https://[a-zA-Z0-9-]+\.wd[0-9]+\.myworkdayjobs\.com/[a-zA-Z0-9_-]+", r.text)
            if m:
                return m.group(0).split("?")[0]

        except:
            pass

    return None

def extract_lever_slug_from_domain(domain: str):

    base = domain.replace("https://", "").replace("http://", "").strip()

    candidates = [
        base.split(".")[0],
        base.replace(".com", ""),
        base.replace(".ai", ""),
        base.replace(".io", ""),
    ]

    for slug in candidates:

        try:
            url = f"https://api.lever.co/v0/postings/{slug}?mode=json"

            r = session.get(url, timeout=5)

            if r.status_code == 200 and len(r.json()) > 0:
                return slug

        except Exception:
            pass

    return None