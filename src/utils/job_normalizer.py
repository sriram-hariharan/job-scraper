import re
from src.config.consts import COMPANY_SUFFIXES, TITLE_CANONICAL
import hashlib

def normalize_company(company: str) -> str:
    if not company:
        return ""

    c = company.lower()
    c = re.sub(r"[^\w\s]", "", c)

    parts = c.split()
    parts = [p for p in parts if p not in COMPANY_SUFFIXES]

    return " ".join(parts).strip()

def normalize_title(title: str) -> str:

    if not title:
        return ""

    t = title.lower().strip()

    # remove brackets
    t = re.sub(r"\(.*?\)", "", t)

    # remove punctuation
    t = re.sub(r"[^\w\s]", " ", t)

    # canonical replacements
    for k, v in TITLE_CANONICAL.items():
        t = re.sub(rf"\b{k}\b", v, t)

    # normalize spaces
    t = re.sub(r"\s+", " ", t)

    return t.strip()

def normalize_location(location: str) -> str:

    if not location:
        return ""

    # Workday multi-location lists
    if isinstance(location, list):
        location = " ".join(sorted(location))

    l = location.lower()

    l = l.replace("united states", "")
    l = l.replace("usa", "")

    l = re.sub(r"[^\w\s]", " ", l)
    l = re.sub(r"\s+", " ", l)

    return l.strip()

def job_fingerprint(job: dict) -> str:
    """
    Generate stable fingerprint for fallback dedupe.
    """

    company = normalize_company(job.get("company", ""))
    title = normalize_title(job.get("title", ""))

    key = f"{company}|{title}"

    return hashlib.sha1(key.encode("utf-8")).hexdigest()