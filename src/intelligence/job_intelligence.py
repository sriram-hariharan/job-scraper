from typing import List, Dict, Any

from src.utils.logging import get_logger
from src.utils.skill_normalizer import normalize_skills

from src.ai.skill_llm_enricher import enrich_skills_with_llm
from src.ai.job_fit_evaluator import detect_visa_sponsorship

logger = get_logger("ai_eval_filter")


# ---------------------------------------------------
# BUILD JOB INTELLIGENCE (BASELINE VERSION)
# ---------------------------------------------------

def build_job_intelligence(job: Dict[str, Any]) -> Dict[str, Any]:

    description = job.get("description_text", "") or ""
    title = job.get("title", "") or ""

    if not description.strip():
        logger.warning("Job has empty description")
        job["intelligence"] = {
            "skills": {
                "required": [],
                "preferred": []
            },
            "visa_sponsorship": None
        }
        return job

    # ---- LLM skill extraction ----
    llm_result = enrich_skills_with_llm(description)

    required_skills = normalize_skills(llm_result.get("required_skills", []))
    preferred_skills = normalize_skills(llm_result.get("preferred_skills", []))

    preferred_skills = [s for s in preferred_skills if s not in required_skills]

    if required_skills or preferred_skills:
        logger.info("LLM enrichment applied")
    else:
        logger.info("LLM enrichment empty")

    # ---- visa detection (kept because it is independent) ----
    visa_signal = detect_visa_sponsorship(description)

    intelligence = {
        "skills": {
            "required": required_skills,
            "preferred": preferred_skills
        },
        "visa_sponsorship": visa_signal
    }

    job["intelligence"] = intelligence

    return job


# ---------------------------------------------------
# FILTER JOBS FOR AI EVALUATION (minimal)
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