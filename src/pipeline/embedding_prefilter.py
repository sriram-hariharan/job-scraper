from typing import List, Dict, Any
import numpy as np

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
    top_n: int | None = None,
) -> List[Dict[str, Any]]:
    logger.info("[embedding_prefilter] entered | jobs=%s | top_n=%s", len(jobs), top_n)
    logger.info("[embedding_prefilter] importing model + resume embedding dependencies")
    from src.ai.embedding_model import get_model
    from src.resume.resume_embeddings import get_embedding_matrix
    logger.info("[embedding_prefilter] local imports completed")
    
    if not jobs:
        return jobs
    logger.info("[embedding_prefilter] loading embedding model")
    model = get_model()
    logger.info("[embedding_prefilter] embedding model ready")
    logger.info("[embedding_prefilter] loading resume embedding matrix")
    resume_matrix, resume_names = get_embedding_matrix()
    logger.info("[embedding_prefilter] resume embedding matrix ready | resumes=%s | shape=%s", len(resume_names), getattr(resume_matrix, "shape", None))
    scored_jobs = []
    logger.info("[embedding_prefilter] starting per-job scoring loop")
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
    logger.info("[embedding_prefilter] built job embedding texts | count=%s", len(scored_jobs))
    scored_jobs.sort(
        key=lambda j: j.get("prefilter_similarity", 0),
        reverse=True,
    )

    kept = len(scored_jobs) if top_n is None else min(top_n, len(scored_jobs))

    logger.info(
        f"Embedding prefilter: {len(jobs)} -> {kept}"
    )

    return scored_jobs if top_n is None else scored_jobs[:top_n]