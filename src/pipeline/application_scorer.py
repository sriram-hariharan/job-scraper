from datetime import datetime
from src.storage.metrics_store import get_hiring_momentum


def score_job(job):

    base_score = 0

    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()

    # Seniority
    if "principal" in title or "staff" in title:
        base_score += 4
    elif "senior" in title:
        base_score += 3
    else:
        base_score += 2

    # Hiring momentum
    momentum = get_hiring_momentum()
    hot_companies = {c.lower() for c, _, _, _, _ in momentum[:10]}

    if company in hot_companies:
        base_score += 5

    # Recency
    posted_at = job.get("posted_at")

    if posted_at:
        try:
            posted_time = datetime.fromisoformat(posted_at)
            hours_old = (datetime.utcnow() - posted_time).total_seconds() / 3600

            if hours_old < 6:
                base_score += 4
            elif hours_old < 24:
                base_score += 2

        except Exception:
            pass

    # AI signal score
    ai_signal_score = (
        job.get("ai_relevance", 0) * 0.35 +
        job.get("skill_match", 0) * 0.25 +
        job.get("seniority_match", 0) * 0.20 +
        job.get("learning_opportunity", 0) * 0.20
    )

    # Resume similarity
    resume_match = job.get("resume_match_score", 0)
    resume_score = resume_match * 10

    # Visa signal
    visa_signal = job.get("intelligence", {}).get("visa_sponsorship", "unknown")

    visa_score = 0
    if visa_signal == "possible":
        visa_score = 3
    elif visa_signal == "no":
        visa_score = -5

    # Role family
    role_family = job.get("intelligence", {}).get("role_family")

    role_score = 0
    if role_family in ["data scientist", "machine learning engineer", "ai engineer"]:
        role_score = 3
    elif role_family == "data analyst":
        role_score = 1

    # Final score
    priority_score = (
        0.40 * ai_signal_score +
        0.30 * resume_score +
        0.20 * base_score +
        0.10 * role_score +
        visa_score
    )

    job["ai_signal_score"] = round(ai_signal_score, 2)
    job["priority_score"] = round(priority_score, 2)

    return job


def score_jobs(jobs):

    for job in jobs:
        score_job(job)

    # rank jobs by priority
    jobs.sort(
        key=lambda j: j.get("priority_score", 0),
        reverse=True
    )

    return jobs