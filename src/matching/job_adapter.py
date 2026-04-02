import re
from typing import Any, Dict, List

from src.matching.job_models import JobEvidence
from src.config.consts import (
    COMMON_SKILL_PATTERNS,
    PREFERRED_CONTEXT_PATTERNS,
    REQUIRED_CONTEXT_PATTERNS,
    SENIORITY_HINTS,
    _SKILL_ALIASES,
)

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

def _skill_present(text_norm: str, candidate: str) -> bool:
    normalized = _normalize_text(candidate).lower()
    if not normalized:
        return False

    escaped = re.escape(normalized).replace(r"\ ", r"\s+")
    prefix = r"(?<![a-z0-9])" if normalized[:1].isalnum() else ""
    suffix = r"(?![a-z0-9])" if normalized[-1:].isalnum() else ""

    return re.search(prefix + escaped + suffix, text_norm) is not None

def _extract_text_skill_hits(text: Any) -> List[str]:
    text_norm = _normalize_text(text).lower()
    hits: List[str] = []

    for pattern in COMMON_SKILL_PATTERNS:
        canonical = _normalize_text(pattern).lower()
        candidates = {canonical}

        for alias, alias_target in _SKILL_ALIASES.items():
            if _normalize_text(alias_target).lower() == canonical:
                candidates.add(_normalize_text(alias).lower())

        if any(_skill_present(text_norm, candidate) for candidate in candidates):
            hits.append(canonical)

    return list(dict.fromkeys(hits))


def _split_context_chunks(text: Any) -> List[str]:
    raw = str(text or "")
    if not raw.strip():
        return []

    chunks = re.split(r"[\n\r]+|(?<=[\.\:\;\!\?])\s+", raw)
    cleaned = [_normalize_text(chunk) for chunk in chunks if _normalize_text(chunk)]
    return cleaned

def _is_heading_like_chunk(chunk: str) -> bool:
    raw = str(chunk or "").strip()
    if not raw:
        return False

    return re.search(r"^[A-Za-z][A-Za-z0-9& /'’\-\+]{0,60}:", raw) is not None

def _extract_contextual_skill_hits(
    text: Any,
    context_patterns: List[str],
) -> List[str]:
    chunks = _split_context_chunks(text)
    if not chunks:
        return []

    gathered_chunks: List[str] = []

    for idx, chunk in enumerate(chunks):
        if not any(re.search(pattern, chunk, re.I) for pattern in context_patterns):
            continue

        if _is_heading_like_chunk(chunk):
            for follow_chunk in chunks[idx + 1:]:
                if _is_heading_like_chunk(follow_chunk):
                    break
                gathered_chunks.append(follow_chunk)
        else:
            gathered_chunks.append(chunk)

    if not gathered_chunks:
        return []

    deduped_chunks = list(dict.fromkeys(gathered_chunks))
    return _extract_text_skill_hits(" ".join(deduped_chunks))

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
    raw_title = job.get("title", "")
    raw_preview = job.get("preview", "")
    raw_retrieval_text = job.get("retrieval_text", "")

    required_skills = _normalize_skill_list(job.get("required_skills", []))
    preferred_skills = _normalize_skill_list(job.get("preferred_skills", []))
    all_skills = _normalize_skill_list(job.get("all_skills", []))

    fallback_required = _extract_contextual_skill_hits(
        " ".join([str(raw_preview or ""), str(raw_retrieval_text or "")]),
        REQUIRED_CONTEXT_PATTERNS,
    )
    fallback_preferred = _extract_contextual_skill_hits(
        " ".join([str(raw_preview or ""), str(raw_retrieval_text or "")]),
        PREFERRED_CONTEXT_PATTERNS,
    )
    fallback_all = _extract_text_skill_hits(
        " ".join([str(raw_title or ""), str(raw_preview or ""), str(raw_retrieval_text or "")])
    )

    required_skills = list(dict.fromkeys(required_skills + fallback_required))
    preferred_skills = list(dict.fromkeys(preferred_skills + fallback_preferred))

    if not all_skills:
        all_skills = list(dict.fromkeys(required_skills + preferred_skills + fallback_all))
    else:
        all_skills = list(dict.fromkeys(all_skills + required_skills + preferred_skills + fallback_all))

    title = _normalize_text(raw_title)
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