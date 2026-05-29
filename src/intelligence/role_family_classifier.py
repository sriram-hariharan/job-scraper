import re

from src.config.role_taxonomy import ROLE_TAXONOMY

TITLE_ROLE_PRIORITY = (
    "sre",
    "fullstack_engineering",
    "backend_engineering",
    "frontend_engineering",
    "ml_ai_engineering",
    "data_science",
    "data_engineering",
    "analytics",
    "cloud_devops",
    "qa_automation",
    "security",
    "systems_it",
    "solutions_engineering",
    "software_engineering",
)

SKILL_ROLE_PRIORITY = (
    "ml_ai_engineering",
    "data_science",
    "data_engineering",
    "analytics",
    "sre",
    "cloud_devops",
    "qa_automation",
    "security",
    "systems_it",
    "solutions_engineering",
    "fullstack_engineering",
    "backend_engineering",
    "frontend_engineering",
    "software_engineering",
)


def _pattern_matches_text(pattern, text):
    return re.search(pattern, text, re.I) is not None


def _role_matches_title(role_family_id, title):
    family = ROLE_TAXONOMY[role_family_id]
    return any(
        _pattern_matches_text(pattern, title)
        for pattern in family["title_include_patterns"]
    )


def _role_matches_skills(role_family_id, skills_text, field_name):
    family = ROLE_TAXONOMY[role_family_id]
    return any(
        _pattern_matches_text(pattern, skills_text)
        for pattern in family[field_name]
    )

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
    skills_text = " ".join(sorted(skills))

    # -------------------------
    # Title-based strong signals
    # -------------------------

    for role_family_id in TITLE_ROLE_PRIORITY:
        if _role_matches_title(role_family_id, title):
            return role_family_id

    # -------------------------
    # Skill/tool-based fallback
    # -------------------------

    for role_family_id in SKILL_ROLE_PRIORITY:
        if _role_matches_skills(role_family_id, skills_text, "skill_patterns"):
            return role_family_id

    for role_family_id in SKILL_ROLE_PRIORITY:
        if _role_matches_skills(role_family_id, skills_text, "tooling_patterns"):
            return role_family_id

    return "other"

def classify_roles(jobs):

    for job in jobs:
        job["role_family"] = classify_role_family(job)

    return jobs
