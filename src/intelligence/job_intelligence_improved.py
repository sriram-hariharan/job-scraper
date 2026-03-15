import re
from typing import List, Dict, Any

from src.utils.logging import get_logger
from src.storage.skill_db import get_existing_skills
from src.ai.job_fit_evaluator import detect_visa_sponsorship
from ai.skill_llm_enricher_regex import enrich_skills_with_llm

from src.config.consts import (
    TITLE_INCLUDE_PATTERNS,
    BASE_SKILL_PATTERNS,
    BASE_AI_FLAG_PATTERNS,
    BASE_SENIORITY_PATTERNS,
    SECTION_PATTERNS,
    SKILL_STOPWORDS,
    TRUSTED_CORE_SKILLS,
    NORMALIZATION_MAP
)

logger = get_logger("ai_eval_filter")

SKILL_PATTERNS = BASE_SKILL_PATTERNS
AI_FLAG_PATTERNS = BASE_AI_FLAG_PATTERNS
SENIORITY_PATTERNS = BASE_SENIORITY_PATTERNS


def normalize_skills(skills):
    normalized = []

    for s in skills:
        s = s.lower().strip()
        s = NORMALIZATION_MAP.get(s, s)
        normalized.append(s)

    return list(set(normalized))

# ---------------------------------------------------
# LLM TRIGGER
# ---------------------------------------------------

def needs_llm_skill_enrichment(required_skills):

    if not required_skills:
        return True

    trusted = 0

    for skill in required_skills:
        if skill.lower() in TRUSTED_CORE_SKILLS:
            trusted += 1

    ratio = trusted / len(required_skills)

    # run LLM if skill list is small OR low quality
    if len(required_skills) < 4:
        return True

    if ratio <= 0.4:
        return True

    return False


# ---------------------------------------------------
# SKILL EXTRACTION
# ---------------------------------------------------

def extract_skills(text):

    if not text:
        return []

    text = text.lower()

    skills = []

    # static patterns
    for s in SKILL_PATTERNS:
        if s in text:
            skills.append(s)

    # dynamically discovered skills
    discovered = get_existing_skills()

    for s in discovered:
        if s in text:
            skills.append(s)

    skills = [s for s in skills if s not in SKILL_STOPWORDS]

    return list(set(skills))


# ---------------------------------------------------
# AI SIGNALS
# ---------------------------------------------------

def detect_ai_flags(text):

    text = text.lower()

    flags = {}

    for flag, patterns in AI_FLAG_PATTERNS.items():
        flags[flag] = any(p in text for p in patterns)

    return flags


# ---------------------------------------------------
# SECTION EXTRACTION
# ---------------------------------------------------

def extract_sections(description):

    text = description.lower()

    required_text = ""
    preferred_text = ""

    for p in SECTION_PATTERNS["required"]:
        m = re.search(p, text)
        if m:
            required_text = text[m.start():]
            break

    for p in SECTION_PATTERNS["preferred"]:
        m = re.search(p, text)
        if m:
            preferred_text = text[m.start():]
            break

    return {
        "required": required_text,
        "preferred": preferred_text
    }


# ---------------------------------------------------
# SENIORITY
# ---------------------------------------------------

def detect_seniority(title):

    title = title.lower()

    for level, patterns in SENIORITY_PATTERNS.items():
        if any(p in title for p in patterns):
            return level

    return "unknown"


# ---------------------------------------------------
# ROLE FAMILY
# ---------------------------------------------------

def detect_role_family(title):

    title = title.lower()

    for pattern in TITLE_INCLUDE_PATTERNS:
        if re.search(pattern, title):
            return pattern

    return "other"


# ---------------------------------------------------
# YEARS OF EXPERIENCE
# ---------------------------------------------------

def extract_years(text):

    match = re.search(r"(\d+)\+?\s+years", text.lower())

    if match:
        return int(match.group(1))

    return None


# ---------------------------------------------------
# BUILD JOB INTELLIGENCE
# ---------------------------------------------------

def build_job_intelligence(job):

    description = job.get("description_text", "") or ""
    title = job.get("title", "") or ""

    text = f"{title} {description}"

    sections = extract_sections(description)

    visa_signal = detect_visa_sponsorship(description)

    required_skills = extract_skills(sections.get("required") or text)
    preferred_skills = extract_skills(sections.get("preferred"))

    # ---------------------------------------------------
    # LLM ENRICHMENT
    # ---------------------------------------------------

    if needs_llm_skill_enrichment(required_skills):

        llm_result = enrich_skills_with_llm(description)

        llm_required = llm_result.get("required_skills", [])
        llm_preferred = llm_result.get("preferred_skills", [])
        if llm_required or llm_preferred:
            logger.info("LLM enrichment applied")

        required_skills = normalize_skills(llm_required)
        preferred_skills = normalize_skills(llm_preferred)

    else:
        required_skills = normalize_skills(required_skills)
        preferred_skills = normalize_skills(preferred_skills)
    
    preferred_skills = [s for s in preferred_skills if s not in required_skills]

    intelligence = {
        "skills": {
            "required": required_skills,
            "preferred": preferred_skills
        },
        "role_family": detect_role_family(title),
        "seniority": detect_seniority(title),
        "years_required": extract_years(text),
        "ai_flags": detect_ai_flags(text),
        "visa_sponsorship": visa_signal
    }

    job["intelligence"] = intelligence

    return job


# ---------------------------------------------------
# FILTER JOBS FOR AI EVALUATION
# ---------------------------------------------------

def filter_jobs_for_ai_evaluation(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    evaluable_jobs = []

    for job in jobs:

        intel = job.get("intelligence", {})

        has_description = bool((job.get("description_text") or "").strip())

        skills = intel.get("skills", {})

        has_structured_signals = any([
            skills.get("required"),
            skills.get("preferred"),
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