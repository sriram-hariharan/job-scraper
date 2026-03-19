from urllib.parse import urlparse
import os

from src.utils.logging import get_logger

logger = get_logger("domain_learner")

DOMAIN_FILE = "data/company_domains.txt"

ATS_DOMAINS = {
    "boards.greenhouse.io",
    "job-boards.greenhouse.io",
    "jobs.lever.co",
    "jobs.ashbyhq.com",
    "apply.workable.com",
    "jobs.jobvite.com",
    "jobs.smartrecruiters.com",
    "smartrecruiters.com",
    "myworkdayjobs.com"
}

def extract_company_from_ats(url):

    if not url:
        return None

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        path = parsed.path.strip("/").split("/")

        # Greenhouse
        if "greenhouse.io" in domain and len(path) >= 1:
            return path[0]

        # Lever
        if "lever.co" in domain and len(path) >= 1:
            return path[0]

        # Ashby
        if "ashbyhq.com" in domain and len(path) >= 1:
            return path[0]

        # SmartRecruiters
        if "smartrecruiters.com" in domain and len(path) >= 1:
            return path[0]

        return None

    except Exception:
        return None
    
def extract_domain(url):

    if not url:
        return None

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()

        if domain.startswith("www."):
            domain = domain[4:]

        if "." not in domain:
            return None

        if domain in ATS_DOMAINS:
            return None
        
        if ".myworkdayjobs.com" in domain:
            return None
        
        return domain

    except Exception:
        return None


def learn_domains_from_jobs(jobs):

    if not jobs:
        return

    existing = set()

    if os.path.exists(DOMAIN_FILE):
        with open(DOMAIN_FILE) as f:
            existing = {line.strip() for line in f if line.strip()}

    learned = set()

    for job in jobs:

        url = job.get("url")

        domain = extract_domain(url)

        if domain and domain not in existing:
            learned.add(domain)

        # learn company from ATS path
        company_slug = extract_company_from_ats(url)

        if company_slug:
            guessed_domain = f"{company_slug}.com"

            if guessed_domain not in existing:
                learned.add(guessed_domain)

    if not learned:
        return

    with open(DOMAIN_FILE, "a") as f:
        for d in sorted(learned):
            f.write(d + "\n")

    logger.info(f"{len(learned)} new company domains learned")

