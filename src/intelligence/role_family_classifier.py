import re


ML_ENGINEER_SKILLS = {
    "pytorch",
    "tensorflow",
    "model training",
    "model deployment",
    "inference",
    "deep learning",
    "ml pipeline",
}

DATA_SCIENTIST_SKILLS = {
    "statistics",
    "predictive modeling",
    "feature engineering",
    "ab testing",
    "experimentation",
}

ANALYTICS_SKILLS = {
    "sql",
    "tableau",
    "power bi",
    "dashboard",
    "reporting",
    "business intelligence",
}

DATA_ENGINEERING_SKILLS = {
    "spark",
    "airflow",
    "etl",
    "data pipeline",
    "data warehouse",
}


def classify_role_family(job):

    title = (job.get("title") or "").lower()
    skills = set(s.lower() for s in job.get("intelligence", {}).get("skills", []))

    # -------------------------
    # Title-based strong signals
    # -------------------------

    if re.search(r"machine learning engineer|ml engineer|ai engineer", title):
        return "ml_engineer"

    if re.search(r"data scientist|applied scientist|research scientist", title):
        return "data_scientist"

    if re.search(r"data analyst|analytics engineer|bi analyst", title):
        return "analytics"

    if re.search(r"data engineer|platform engineer", title):
        return "data_engineer"

    # -------------------------
    # Skill-based fallback
    # -------------------------

    if skills & ML_ENGINEER_SKILLS:
        return "ml_engineer"

    if skills & DATA_SCIENTIST_SKILLS:
        return "data_scientist"

    if skills & ANALYTICS_SKILLS:
        return "analytics"

    if skills & DATA_ENGINEERING_SKILLS:
        return "data_engineer"

    return "other"

def classify_roles(jobs):

    for job in jobs:
        job["role_family"] = classify_role_family(job)

    return jobs