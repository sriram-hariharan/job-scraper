import json
import os
import re
from src.utils.logging import get_logger

logger = get_logger(__name__)

WORKABLE_ROUTE_SLUGS = {"j", "job", "jobs", "api", "accounts"}

# in-memory store
_DISCOVERED = {
    "greenhouse": set(),
    "ashby": set(),
    "lever": set(),
    "workday": set(),
    "workable": set(),
    "jobvite": set(),
    "smartrecruiters": set()
}
def get_learned():
    return _DISCOVERED


def normalize_workable_slug(slug):
    slug = str(slug or "").strip().lower()
    if not slug or slug in WORKABLE_ROUTE_SLUGS:
        return None
    return slug


def learn_from_job_url(url):

    if not url:
        return

    ats = None
    slug = None

    if "boards.greenhouse.io" in url:
        ats = "greenhouse"
        slug = url.split("boards.greenhouse.io/")[1].split("/")[0].split("?")[0]

    elif "jobs.lever.co" in url:
        ats = "lever"
        slug = url.split("jobs.lever.co/")[1].split("/")[0].split("?")[0]

    elif "jobs.ashbyhq.com" in url:
        ats = "ashby"
        slug = url.split("jobs.ashbyhq.com/")[1].split("/")[0].split("?")[0]

    elif "apply.workable.com" in url:
        ats = "workable"
        slug = normalize_workable_slug(
            url.split("apply.workable.com/")[1].split("/")[0].split("?")[0]
        )

    elif "jobs.jobvite.com" in url:
        ats = "jobvite"
        slug = url.split("jobs.jobvite.com/")[1].split("/")[0].split("?")[0]

    elif "myworkdayjobs.com" in url:
        ats = "workday"
        m = re.search(r"https://[^/]+\.myworkdayjobs\.com/[^/?#]+", url)
        if m:
            slug = m.group(0)

    elif "smartrecruiters.com" in url:
        ats = "smartrecruiters"

        # example URL
        # https://jobs.smartrecruiters.com/Nvidia/12345-ml-engineer

        try:
            slug = url.split("smartrecruiters.com/")[1].split("/")[0]
        except Exception:
            slug = None

    if ats and slug:
        _DISCOVERED[ats].add(slug)

def learn_company(ats, slug):

    if not ats or not slug:
        return

    if ats not in _DISCOVERED:
        return

    slug = slug.strip().lower()
    if ats == "workable":
        slug = normalize_workable_slug(slug)
        if not slug:
            return

    _DISCOVERED[ats].add(slug)

