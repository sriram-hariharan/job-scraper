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

    if not learned:
        return

    with open(DOMAIN_FILE, "a") as f:
        for d in sorted(learned):
            f.write(d + "\n")

    logger.info(f"{len(learned)} new company domains learned")