import os
from typing import List, Dict, Any

from src.utils.logging import get_logger
from src.utils.skill_normalizer import normalize_skills

from src.ai.skill_llm_enricher import enrich_skills_with_llm
from src.ai.hybrid_skill_extractor import (
    extract_skills_deterministic,
    extract_skills_hybrid,
)
from src.ai.job_fit_evaluator import detect_visa_sponsorship
from src.intelligence.role_family_classifier import classify_role_family

logger = get_logger("ai_eval_filter")

SKILL_EXTRACTION_BACKEND = os.getenv("SKILL_EXTRACTION_BACKEND", "groq_first").strip().lower()
_VALID_BACKENDS = {"groq_first", "deterministic", "hybrid"}


def _extract_skills(description: str) -> Dict[str, List[str]]:
    backend = SKILL_EXTRACTION_BACKEND
    if backend not in _VALID_BACKENDS:
        logger.warning(
            f"Invalid SKILL_EXTRACTION_BACKEND='{backend}'. Falling back to 'groq_first'."
        )
        backend = "groq_first"

    if backend == "deterministic":
        logger.info("Using deterministic skill extraction backend")
        return extract_skills_deterministic(description)

    if backend == "hybrid":
        logger.info("Using hybrid skill extraction backend")
        return extract_skills_hybrid(description)

    logger.info("Using Groq-first skill extraction backend")
    llm_result = enrich_skills_with_llm(description)
    required_skills = normalize_skills(llm_result.get("required_skills", []))
    preferred_skills = normalize_skills(llm_result.get("preferred_skills", []))
    preferred_skills = [s for s in preferred_skills if s not in required_skills]

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "all_skills": required_skills + [s for s in preferred_skills if s not in required_skills],
    }


# ---------------------------------------------------
# BUILD JOB INTELLIGENCE
# ---------------------------------------------------

def build_job_intelligence(job: Dict[str, Any]) -> Dict[str, Any]:

    description = job.get("description_text", "") or ""

    if not description.strip():
        logger.warning("Job has empty description")
        job["intelligence"] = {
            "skills": {
                "required": [],
                "preferred": [],
                "all": [],
            },
            "visa_sponsorship": None
        }
        return job

    skill_result = _extract_skills(description)

    required_skills = normalize_skills(skill_result.get("required_skills", []))
    preferred_skills = normalize_skills(skill_result.get("preferred_skills", []))
    preferred_skills = [s for s in preferred_skills if s not in required_skills]

    raw_all_skills = skill_result.get(
        "all_skills",
        required_skills + [s for s in preferred_skills if s not in required_skills],
    )
    normalized_all_skills = normalize_skills(raw_all_skills)

    all_skills = []
    seen = set()
    for skill in required_skills + preferred_skills + normalized_all_skills:
        if skill not in seen:
            seen.add(skill)
            all_skills.append(skill)

    if required_skills or preferred_skills or all_skills:
        logger.info("Skill extraction applied")
    else:
        logger.info("Skill extraction empty")

    visa_signal = detect_visa_sponsorship(description)

    intelligence = {
        "skills": {
            "required": required_skills,
            "preferred": preferred_skills,
            "all": all_skills,
        },
        "visa_sponsorship": visa_signal
    }

    job["intelligence"] = intelligence
    job["role_family"] = classify_role_family(job)

    return job


# ---------------------------------------------------
# FILTER JOBS FOR AI EVALUATION
# ---------------------------------------------------

def filter_jobs_for_ai_evaluation(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    evaluable_jobs = []

    for job in jobs:

        description = job.get("description_text", "")

        if description and description.strip():
            evaluable_jobs.append(job)
        else:
            job["ai_fit"] = "SKIPPED_NO_DESCRIPTION"
            job["ai_fit_score"] = 0
            job["ai_fit_reason"] = "Job description missing"

    logger.info(f"Jobs with descriptions for AI evaluation: {len(evaluable_jobs)}")

    return evaluable_jobs