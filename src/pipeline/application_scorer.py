from datetime import datetime
from src.storage.metrics_store import get_hiring_momentum


def score_job(job):

    base_score = 0

    title = (job.get("title") or "").lower()
    company = (job.get("company") or "").lower()

    # -----------------------------
    # Seniority scoring
    # -----------------------------
    if "principal" in title or "staff" in title:
        base_score += 4
    elif "senior" in title:
        base_score += 3
    else:
        base_score += 2

    # -----------------------------
    # Company hiring momentum
    # -----------------------------
    momentum = get_hiring_momentum()
    hot_companies = {c.lower() for c, _, _, _, _ in momentum[:10]}

    if company in hot_companies:
        base_score += 5

    # -----------------------------
    # Recency bonus
    # -----------------------------
    recency_score = 0

    posted_at = job.get("posted_at")

    if posted_at:
        try:
            posted_time = datetime.fromisoformat(posted_at)
            hours_old = (datetime.utcnow() - posted_time).total_seconds() / 3600

            if hours_old < 6:
                recency_score = 4
            elif hours_old < 24:
                recency_score = 2

        except Exception:
            pass

    base_score += recency_score

    # -----------------------------
    # AI SIGNAL SCORE
    # -----------------------------
    ai_signal_score = (
        job.get("ai_relevance", 0) * 0.35 +
        job.get("skill_match", 0) * 0.25 +
        job.get("seniority_match", 0) * 0.20 +
        job.get("learning_opportunity", 0) * 0.20
    )

    # -----------------------------
    # FINAL PRIORITY SCORE
    # -----------------------------
    priority_score = (
        0.50 * ai_signal_score +
        0.50 * base_score
    )

    job["ai_signal_score"] = round(ai_signal_score, 2)
    job["priority_score"] = round(priority_score, 2)

    return job


def score_jobs(jobs):

    for job in jobs:
        score_job(job)

    return jobs