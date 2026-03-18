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

def _extract_job_skills(job):
    raw_skills = []

    intelligence_skills = job.get("intelligence", {}).get("skills", {})

    if isinstance(intelligence_skills, dict):
        raw_skills.extend(intelligence_skills.get("required", []) or [])
        raw_skills.extend(intelligence_skills.get("preferred", []) or [])
    elif isinstance(intelligence_skills, list):
        raw_skills.extend(intelligence_skills)

    raw_skills.extend(job.get("required_skills", []) or [])
    raw_skills.extend(job.get("preferred_skills", []) or [])
    raw_skills.extend(job.get("all_skills", []) or [])

    return {
        str(skill).lower().strip()
        for skill in raw_skills
        if str(skill).strip()
    }

def classify_role_family(job):

    title = (job.get("title") or "").lower()
    skills = _extract_job_skills(job)

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