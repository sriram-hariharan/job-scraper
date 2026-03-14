import re
from src.config.consts import TITLE_INCLUDE_PATTERNS
from typing import List, Dict, Any
from src.utils.logging import get_logger
from src.storage.skill_db import get_existing_skills
from src.config.consts import (
    TITLE_INCLUDE_PATTERNS,
    BASE_SKILL_PATTERNS,
    BASE_FRAMEWORK_PATTERNS,
    BASE_CLOUD_PATTERNS,
    BASE_AI_FLAG_PATTERNS,
    BASE_SENIORITY_PATTERNS
)

logger = get_logger("ai_eval_filter")

SKILL_PATTERNS = BASE_SKILL_PATTERNS
FRAMEWORK_PATTERNS = BASE_FRAMEWORK_PATTERNS
CLOUD_PATTERNS = BASE_CLOUD_PATTERNS
AI_FLAG_PATTERNS = BASE_AI_FLAG_PATTERNS
SENIORITY_PATTERNS = BASE_SENIORITY_PATTERNS


def extract_skills(text):

    text = text.lower()

    skills = []

    # static patterns from config
    for s in SKILL_PATTERNS:
        if s in text:
            skills.append(s)

    # dynamically discovered skills
    discovered = get_existing_skills()

    for s in discovered:
        if s in text:
            skills.append(s)

    return list(set(skills))


def extract_frameworks(text):

    text = text.lower()

    frameworks = []

    for f in FRAMEWORK_PATTERNS:
        if f in text:
            frameworks.append(f)

    return list(set(frameworks))


def extract_cloud(text):

    text = text.lower()

    cloud = []

    for c in CLOUD_PATTERNS:
        if c in text:
            cloud.append(c)

    return list(set(cloud))


def detect_ai_flags(text):

    text = text.lower()

    flags = {}

    for flag, patterns in AI_FLAG_PATTERNS.items():

        flags[flag] = any(p in text for p in patterns)

    return flags


def detect_seniority(title):

    title = title.lower()

    for level, patterns in SENIORITY_PATTERNS.items():

        if any(p in title for p in patterns):
            return level

    return "unknown"


def detect_role_family(title):

    title = title.lower()

    for pattern in TITLE_INCLUDE_PATTERNS:

        if re.search(pattern, title):
            return pattern

    return "other"


def extract_years(text):

    match = re.search(r"(\d+)\+?\s+years", text.lower())

    if match:
        return int(match.group(1))

    return None


def build_job_intelligence(job):

    description = job.get("description_text", "") or ""
    title = job.get("title", "") or ""

    text = f"{title} {description}"

    intelligence = {
        "skills": extract_skills(text),
        "frameworks": extract_frameworks(text),
        "cloud_tools": extract_cloud(text),
        "role_family": detect_role_family(title),
        "seniority": detect_seniority(title),
        "years_required": extract_years(text),
        "ai_flags": detect_ai_flags(text)
    }

    job["intelligence"] = intelligence

    return job

def filter_jobs_for_ai_evaluation(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    evaluable_jobs = []

    for job in jobs:

        intel = job.get("intelligence", {})

        has_description = bool((job.get("description_text") or "").strip())

        has_structured_signals = any([
            intel.get("skills"),
            intel.get("frameworks"),
            intel.get("cloud_tools"),
            any(intel.get("ai_flags", {}).values()),
            intel.get("years_required") is not None,
        ])

        if has_description or has_structured_signals:
            evaluable_jobs.append(job)

        else:
            job["ai_fit"] = "SKIPPED_NO_EVIDENCE"
            job["ai_fit_score"] = 0
            job["ai_fit_reason"] = "No JD evidence available for evaluation"

    logger.info(f"Jobs with enough evidence for AI evaluation: {len(evaluable_jobs)}")

    return evaluable_jobs