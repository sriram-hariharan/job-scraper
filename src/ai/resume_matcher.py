import numpy as np
from typing import Dict
from tqdm import tqdm
from src.ai.embedding_model import get_model

from src.config.resume_registry import get_candidate_resumes
from src.resume.resume_embeddings import get_embedding_matrix
from src.resume.resume_loader import load_resumes


def build_job_embedding_text(job: Dict) -> str:
    """
    Build compact embedding text from job intelligence.
    """

    intel = job.get("intelligence", {})

    title = job.get("title", "")

    skills = ", ".join(intel.get("skills", []))
    frameworks = ", ".join(intel.get("frameworks", []))
    cloud = ", ".join(intel.get("cloud_tools", []))

    seniority = intel.get("seniority", "")

    return f"""
    {title}

    skills: {skills}

    frameworks: {frameworks}

    cloud: {cloud}

    seniority: {seniority}
    """


def match_resume_for_job(job, job_embedding, resume_matrix, resume_names):

    intel = job.get("intelligence", {})
    role_family = intel.get("role_family", "")

    candidate_resume_names = get_candidate_resumes(role_family)

    if not candidate_resume_names:
        return {"best_resume": None, "resume_match_score": None}

    if resume_matrix is None:
        return {"best_resume": None, "resume_match_score": None}

    candidate_indices = [
        resume_names.index(name)
        for name in candidate_resume_names
        if name in resume_names
    ]

    if not candidate_indices:
        return {
            "best_resume": None,
            "resume_match_score": None
        }

    candidate_matrix = resume_matrix[candidate_indices]

    similarities = candidate_matrix @ job_embedding

    best_local_idx = np.argmax(similarities)

    best_idx = candidate_indices[best_local_idx]

    best_resume = resume_names[best_idx]

    best_score = similarities[best_local_idx]

    return {
        "best_resume": best_resume,
        "resume_match_score": round(float(best_score), 4)
    }


def match_resumes(jobs):

    resumes = load_resumes()
    candidate_resume_names = [r["resume_name"] for r in resumes]
    resume_matrix, resume_names = get_embedding_matrix(candidate_resume_names)

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