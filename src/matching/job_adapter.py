import re
from typing import Any, Dict, List

from src.matching.job_models import JobEvidence
from src.config.consts import SENIORITY_HINTS

def _normalize_text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize_skill_list(values: Any) -> List[str]:
    if not isinstance(values, list):
        return []

    normalized: List[str] = []
    seen = set()

    for value in values:
        skill = _normalize_text(value).lower()
        if not skill:
            continue
        if skill not in seen:
            seen.add(skill)
            normalized.append(skill)

    return normalized


def _infer_seniority(title: str, seniority: str) -> str:
    seniority = _normalize_text(seniority)
    if seniority:
        return seniority.lower()

    title_norm = _normalize_text(title).lower()
    for hint in SENIORITY_HINTS:
        if re.search(rf"\b{re.escape(hint)}\b", title_norm):
            return hint

    return ""


def build_job_evidence(job: Dict[str, Any]) -> JobEvidence:
    required_skills = _normalize_skill_list(job.get("required_skills", []))
    preferred_skills = _normalize_skill_list(job.get("preferred_skills", []))
    all_skills = _normalize_skill_list(job.get("all_skills", []))

    if not all_skills:
        all_skills = list(dict.fromkeys(required_skills + preferred_skills))

    title = _normalize_text(job.get("title", ""))
    seniority = _infer_seniority(title, job.get("seniority", ""))

    return JobEvidence(
        job_doc_id=_normalize_text(job.get("doc_id", "")),
        company=_normalize_text(job.get("company", "")),
        title=title,
        location=_normalize_text(job.get("location", "")),
        source=_normalize_text(job.get("source", "")),
        job_url=_normalize_text(job.get("job_url", "")),
        posted_at=_normalize_text(job.get("posted_at", "")),
        role_family=_normalize_text(job.get("role_family", "")),
        seniority=seniority,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        all_skills=all_skills,
        visa_sponsorship=_normalize_text(job.get("visa_sponsorship", "")).lower(),
        ai_fit_score=job.get("ai_fit_score"),
        retrieval_text=_normalize_text(job.get("retrieval_text", "")),
        preview=_normalize_text(job.get("preview", "")),
        notes={
            "adapter_version": "v1",
            "required_skill_count": len(required_skills),
            "preferred_skill_count": len(preferred_skills),
            "all_skill_count": len(all_skills),
        },
    )


def build_job_evidence_batch(jobs: List[Dict[str, Any]]) -> List[JobEvidence]:
    return [build_job_evidence(job) for job in jobs]