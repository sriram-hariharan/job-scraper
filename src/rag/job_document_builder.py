import hashlib
from typing import Dict, Any, List


def _dedupe_keep_order(items: List[str]) -> List[str]:
    seen = set()
    result = []

    for item in items:
        if not item:
            continue
        if item not in seen:
            seen.add(item)
            result.append(item)

    return result


def build_job_doc_id(job: Dict[str, Any]) -> str:
    url = (job.get("url") or "").strip()
    if url:
        return url

    company = (job.get("company") or "").strip().lower()
    title = (job.get("title") or "").strip().lower()
    location = (job.get("location") or "").strip().lower()
    source = (job.get("source") or "").strip().lower()
    description = (
        (job.get("description_text") or job.get("description") or "")
        .strip()
        .lower()
    )

    raw = f"{company}|{title}|{location}|{source}|{description}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_retrieval_text(job_doc: Dict[str, Any]) -> str:
    ai_flags = [
        key for key, value in (job_doc.get("ai_flags") or {}).items()
        if value
    ]

    lines = [
        f"Company: {job_doc.get('company', '')}",
        f"Title: {job_doc.get('title', '')}",
        f"Location: {job_doc.get('location', '')}",
        f"Source: {job_doc.get('source', '')}",
        f"Role family: {job_doc.get('role_family', '')}",
        f"Seniority: {job_doc.get('seniority', '')}",
        f"Required skills: {', '.join(job_doc.get('required_skills', []))}",
        f"Preferred skills: {', '.join(job_doc.get('preferred_skills', []))}",
        f"AI flags: {', '.join(ai_flags)}",
        f"Visa sponsorship: {job_doc.get('visa_sponsorship', '')}",
        f"AI fit score: {job_doc.get('ai_fit_score', '')}",
        f"AI fit reason: {job_doc.get('ai_fit_reason', '')}",
        "",
        "Job description:",
        job_doc.get("description", ""),
    ]

    return "\n".join(lines).strip()


def build_job_document(job: Dict[str, Any]) -> Dict[str, Any]:
    intelligence = job.get("intelligence", {}) or {}
    skills = intelligence.get("skills", {}) or {}

    required_skills = skills.get("required", []) or []
    preferred_skills = skills.get("preferred", []) or []
    all_skills = _dedupe_keep_order(required_skills + preferred_skills)

    job_doc = {
        "doc_id": build_job_doc_id(job),
        "company": (job.get("company") or "").strip(),
        "title": (job.get("title") or "").strip(),
        "location": (job.get("location") or "").strip(),
        "source": (job.get("source") or "").strip(),
        "job_url": (job.get("url") or "").strip(),
        "posted_at": (job.get("posted_at") or "").strip(),
        "description": job.get("description_text", "") or job.get("description", ""),
        "role_family": intelligence.get("role_family", "") or job.get("role_family", ""),
        "seniority": intelligence.get("seniority", ""),
        "required_skills": required_skills,
        "preferred_skills": preferred_skills,
        "all_skills": all_skills,
        "ai_flags": intelligence.get("ai_flags", {}) or {},
        "visa_sponsorship": intelligence.get("visa_sponsorship", "unknown"),
        "ai_fit_score": job.get("ai_fit_score"),
        "ai_fit_reason": job.get("ai_fit_reason", ""),
        "resume_matches": job.get("resume_matches", []),
    }

    job_doc["retrieval_text"] = build_retrieval_text(job_doc)
    return job_doc