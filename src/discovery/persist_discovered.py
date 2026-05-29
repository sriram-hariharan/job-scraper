from src.discovery.learned_companies import get_learned, normalize_workable_slug
from src.discovery.save_companies import append_new_companies
import re
from src.config.consts import INVALID_SLUGS

ATS_FILES = {
    "greenhouse": "discovery://ats/greenhouse",
    "lever": "discovery://ats/lever",
    "workday": "discovery://ats/workday",
    "ashby": "discovery://ats/ashby",
    "workable": "discovery://ats/workable",
    "jobvite": "discovery://ats/jobvite",
    "smartrecruiters": "discovery://ats/smartrecruiters",
}

def normalize_company_slug(slug: str) -> str:
    slug = slug.lower().strip()
    slug = re.sub(r'\d+$', '', slug)
    return slug

def persist_discovered_companies():
    learned = get_learned()
    for ats, companies in learned.items():
        if not companies:
            continue

        path = ATS_FILES.get(ats)

        if path:
            # normalize slugs before saving
            normalized = {
                normalize_company_slug(c)
                for c in companies
                if c
            }
            if ats == "workable":
                normalized = {
                    slug
                    for c in normalized
                    for slug in [normalize_workable_slug(c)]
                    if slug
                }
            # remove junk slugs
            normalized = {
                c for c in normalized
                if c not in INVALID_SLUGS
            }

            append_new_companies(path, normalized)
