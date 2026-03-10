import json
import os
import re
from src.utils.logging import get_logger
from src.discovery.learn_domains import learn_domain_from_slug

logger = get_logger(__name__)

# in-memory store
_DISCOVERED = {
    "greenhouse": set(),
    "ashby": set(),
    "lever": set(),
    "workday": set(),
    "workable": set(),
    "jobvite": set()
}
def get_learned():
    return _DISCOVERED

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
        slug = url.split("apply.workable.com/")[1].split("/")[0].split("?")[0]

    elif "jobs.jobvite.com" in url:
        ats = "jobvite"
        slug = url.split("jobs.jobvite.com/")[1].split("/")[0].split("?")[0]

    elif "myworkdayjobs.com" in url:
        ats = "workday"
        slug = url.split("myworkdayjobs.com/")[1].split("/")[0]

    if ats and slug:
        _DISCOVERED[ats].add(slug)


