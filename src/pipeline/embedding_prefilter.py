from typing import List, Dict, Any
import numpy as np

from src.ai.embedding_model import get_model
from src.resume.resume_embeddings import get_embedding_matrix
from src.utils.logging import get_logger

logger = get_logger("embedding_prefilter")


def build_job_embedding_text(job: Dict[str, Any]) -> str:

    intelligence = job.get("intelligence", {})

    parts = [
        job.get("title", ""),
        intelligence.get("role_family", ""),
        intelligence.get("seniority", ""),
        str(intelligence.get("years_required", "")),
        " ".join(intelligence.get("skills", [])),
        " ".join(intelligence.get("tools", [])),
        intelligence.get("domain", ""),
        intelligence.get("ai_focus", ""),
    ]

    return " ".join(p for p in parts if p)


def prefilter_jobs_by_embedding(
    jobs: List[Dict[str, Any]],
    top_n: int = 40
) -> List[Dict[str, Any]]:

    if not jobs:
        return jobs

    model = get_model()

    resume_matrix, resume_names = get_embedding_matrix()

    scored_jobs = []

    for job in jobs:

        text = build_job_embedding_text(job)

        if not text.strip():
            job["prefilter_similarity"] = 0
            scored_jobs.append(job)
            continue

        job_vec = model.encode(text, normalize_embeddings=True)

        similarities = resume_matrix @ job_vec

        best_score = float(np.max(similarities))

        job["prefilter_similarity"] = best_score

        scored_jobs.append(job)

    scored_jobs.sort(
        key=lambda j: j.get("prefilter_similarity", 0),
        reverse=True,
    )

    logger.info(
        f"Embedding prefilter: {len(jobs)} -> {min(top_n, len(scored_jobs))}"
    )

    return scored_jobs[:top_n]