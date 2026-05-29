import os
from collections import Counter
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
AI_EVALUATION_SKIP_STAGE = "ai_evaluation_filter"
SKIPPED_NO_DESCRIPTION = "SKIPPED_NO_DESCRIPTION"


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

def _job_url(job: Dict[str, Any]) -> str:
    return str(
        job.get("url")
        or job.get("job_url")
        or job.get("posting_url")
        or job.get("job_posting_url")
        or ""
    ).strip()


def _job_source(job: Dict[str, Any]) -> str:
    return str(
        job.get("source")
        or job.get("job_source")
        or job.get("platform")
        or ""
    ).strip()


def _attach_ai_evaluation_skip_metadata(
    job: Dict[str, Any],
    *,
    reason: str,
    message: str,
) -> None:
    company = str(job.get("company") or "").strip()
    title = str(job.get("title") or "").strip()
    url = _job_url(job)
    source = _job_source(job)

    job["ai_evaluation_skip_reason"] = reason
    job["ai_evaluation_skip_stage"] = AI_EVALUATION_SKIP_STAGE
    job["ai_evaluation_skip_company"] = company
    job["ai_evaluation_skip_title"] = title
    job["ai_evaluation_skip_url"] = url
    job["ai_evaluation_skip_source"] = source
    job["ai_evaluation_skip_metadata"] = {
        "company": company,
        "title": title,
        "url": url,
        "source": source,
        "reason": reason,
        "stage": AI_EVALUATION_SKIP_STAGE,
        "message": message,
    }


def _clear_ai_evaluation_skip_metadata(job: Dict[str, Any]) -> None:
    job.pop("ai_evaluation_skip_reason", None)
    job.pop("ai_evaluation_skip_stage", None)
    job.pop("ai_evaluation_skip_company", None)
    job.pop("ai_evaluation_skip_title", None)
    job.pop("ai_evaluation_skip_url", None)
    job.pop("ai_evaluation_skip_source", None)
    job.pop("ai_evaluation_skip_metadata", None)


def ai_evaluation_skip_summary(jobs: List[Dict[str, Any]], *, limit: int = 10) -> Dict[str, Any]:
    skipped = [
        job
        for job in jobs
        if str(job.get("ai_evaluation_skip_reason") or "").strip()
    ]
    reason_counts = Counter(
        str(job.get("ai_evaluation_skip_reason") or "").strip()
        for job in skipped
    )

    skipped_jobs = []
    for job in skipped[: max(0, int(limit))]:
        metadata = dict(job.get("ai_evaluation_skip_metadata") or {})
        skipped_jobs.append(
            {
                "company": str(metadata.get("company") or job.get("company") or "").strip(),
                "title": str(metadata.get("title") or job.get("title") or "").strip(),
                "url": str(metadata.get("url") or _job_url(job) or "").strip(),
                "source": str(metadata.get("source") or _job_source(job) or "").strip(),
                "reason": str(
                    metadata.get("reason")
                    or job.get("ai_evaluation_skip_reason")
                    or ""
                ).strip(),
            }
        )

    return {
        "skipped_count": len(skipped),
        "reason_counts": dict(sorted(reason_counts.items())),
        "skipped_jobs": skipped_jobs,
        "skipped_samples": skipped_jobs,
    }


def filter_jobs_for_ai_evaluation(jobs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:

    evaluable_jobs = []

    for job in jobs:

        description = job.get("description_text", "")

        if description and description.strip():
            _clear_ai_evaluation_skip_metadata(job)
            evaluable_jobs.append(job)
        else:
            job["ai_fit"] = SKIPPED_NO_DESCRIPTION
            job["ai_fit_score"] = 0
            job["ai_fit_reason"] = "Job description missing"
            _attach_ai_evaluation_skip_metadata(
                job,
                reason=SKIPPED_NO_DESCRIPTION,
                message="Job description missing",
            )

    logger.info(f"Jobs with descriptions for AI evaluation: {len(evaluable_jobs)}")

    return evaluable_jobs
