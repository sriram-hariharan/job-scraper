import requests

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

def slug_from_domain(domain):

    domain = domain.replace("https://", "")
    domain = domain.replace("http://", "")
    domain = domain.replace("www.", "")

    return domain.split(".")[0]


def check_greenhouse(slug):

    url = f"https://boards.greenhouse.io/{slug}"

    try:
        r = requests.get(url, timeout=5)
        return r.status_code == 200
    except:
        return False


def check_ashby(slug):

    url = f"https://jobs.ashbyhq.com/{slug}"

    try:
        r = requests.get(url, timeout=5)
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

            r = requests.get(url, headers=headers, timeout=5)

            if "myworkdayjobs.com" in r.text:
                return True

        except:
            pass

    return False

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

            r = requests.get(url, timeout=8)

            if r.status_code == 200 and len(r.json()) > 0:
                return slug

        except Exception:
            pass

    return None