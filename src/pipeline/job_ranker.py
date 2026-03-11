from datetime import datetime, timezone
from src.config.consts import TITLE_INCLUDE_REGEX, TITLE_EXCLUDE_REGEX


def title_score(title: str):

    if not title:
        return 0

    t = title.lower()

    for r in TITLE_EXCLUDE_REGEX:
        if r.search(t):
            return -100

    score = 0

    for r in TITLE_INCLUDE_REGEX:
        if r.search(t):
            score += 25

    return score


def recency_score(posted_at):

    if not posted_at:
        return 0

    try:
        dt = datetime.fromisoformat(posted_at.replace("Z","+00:00"))
        hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600
    except:
        return 0

    if hours <= 6:
        return 30
    elif hours <= 24:
        return 20
    elif hours <= 72:
        return 10

    return 0


def score_job(job):

    score = 0

    score += title_score(job.get("title",""))
    score += recency_score(job.get("posted_at"))

    return score

def rank_jobs(jobs):

    for job in jobs:
        job["_score"] = score_job(job)

    jobs.sort(key=lambda x: x["_score"], reverse=True)

    return jobs