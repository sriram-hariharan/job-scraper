import os
import numpy as np
from typing import Dict
from tqdm import tqdm
from src.utils.logging import get_logger
from src.config.resume_registry import get_candidate_resumes

logger = get_logger("resume_matcher")

def _legacy_filesystem_resume_matching_enabled() -> bool:
    return str(
        os.environ.get("JOB_STACK_ENABLE_LEGACY_RESUME_MATCHING", "") or ""
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
    }


def build_job_embedding_text(job: Dict) -> str:
    """
    Build compact embedding text from job intelligence.
    """

    intel = job.get("intelligence", {})

    title = job.get("title", "")

    skills = ", ".join(intel.get("skills", []))

    seniority = intel.get("seniority", "")

    return f"""
    {title}

    skills: {skills}

    seniority: {seniority}
    """


def match_resume_for_job(job, job_embedding, resume_matrix, resume_names):

    intel = job.get("intelligence", {})
    role_family = intel.get("role_family", "")

    candidate_resume_names = get_candidate_resumes(role_family)

    if not candidate_resume_names:
        return {
            "embedding_resume_prior": None,
            "embedding_resume_prior_score": None,
        }

    if resume_matrix is None:
        return {
            "embedding_resume_prior": None,
            "embedding_resume_prior_score": None,
        }

    candidate_indices = [
        resume_names.index(name)
        for name in candidate_resume_names
        if name in resume_names
    ]

    if not candidate_indices:
        return {
            "embedding_resume_prior": None,
            "embedding_resume_prior_score": None,
        }

    candidate_matrix = resume_matrix[candidate_indices]

    similarities = candidate_matrix @ job_embedding

    best_local_idx = np.argmax(similarities)

    best_idx = candidate_indices[best_local_idx]

    best_resume = resume_names[best_idx]
    best_score = round(float(similarities[best_local_idx]), 4)

    return {
        "embedding_resume_prior": best_resume,
        "embedding_resume_prior_score": best_score,
    }


def _apply_neutral_resume_prior(jobs, *, reason: str = ""):
    if reason:
        logger.info("Skipping legacy filesystem resume matching: %s", reason)

    for job in jobs:
        job.setdefault("embedding_resume_prior", None)
        job.setdefault("embedding_resume_prior_score", None)

    return jobs


def match_resumes(jobs):
    if not jobs:
        return jobs

    if not _legacy_filesystem_resume_matching_enabled():
        return _apply_neutral_resume_prior(
            jobs,
            reason=(
                "legacy filesystem resume matching disabled; "
                "profile resumes are Postgres-backed"
            ),
        )

    from src.resume.resume_loader import load_resumes

    try:
        resumes = load_resumes()
    except RuntimeError as exc:
        return _apply_neutral_resume_prior(jobs, reason=str(exc))

    candidate_resume_names = [r["resume_name"] for r in resumes]

    if not candidate_resume_names:
        return _apply_neutral_resume_prior(
            jobs,
            reason="no legacy filesystem resumes available",
        )

    from src.resume.resume_embeddings import get_embedding_matrix
    from src.ai.embedding_model import get_model

    resume_matrix, resume_names = get_embedding_matrix(candidate_resume_names)

    if resume_matrix is None or not resume_names:
        return _apply_neutral_resume_prior(
            jobs,
            reason="legacy resume embedding matrix unavailable",
        )

    job_texts = [
        build_job_embedding_text(job)
        for job in jobs
    ]
    model = get_model()

    job_embeddings = model.encode(
        job_texts,
        normalize_embeddings=True
    )

    for i, job in enumerate(tqdm(jobs, desc="Matching resumes")):

        job_embedding = job_embeddings[i]

        result = match_resume_for_job(
            job,
            job_embedding,
            resume_matrix,
            resume_names
        )

        job.update(result)

    return jobs
