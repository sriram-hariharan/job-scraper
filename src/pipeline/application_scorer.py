from datetime import datetime
from src.metrics.metrics_store import get_hiring_momentum

def score_job(job):

    score = 0

    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()

    # Seniority scoring
    if "senior" in title:
        score += 3
    elif "staff" in title or "principal" in title:
        score += 4
    else:
        score += 2

    # Company quality
    momentum = get_hiring_momentum()
    hot_companies = {c for c, _, _, _, _ in momentum[:10]}

    if company in hot_companies:
        score += 5

    # Recency bonus
    posted_at = job.get("posted_at")

    if posted_at:
        try:
            posted_time = datetime.fromisoformat(posted_at)
            hours_old = (datetime.utcnow() - posted_time).total_seconds() / 3600

            if hours_old < 6:
                score += 4
            elif hours_old < 24:
                score += 2

        except Exception:
            pass

    return score


def score_jobs(jobs):

    for job in jobs:
        job["priority_score"] = score_job(job)

    return jobs