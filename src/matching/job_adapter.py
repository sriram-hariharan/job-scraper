import re
from typing import Any, Dict, List

from src.matching.job_models import JobEvidence
from src.config.consts import (
    ANALYTICS_ML_SIGNAL_PATTERNS,
    COMMON_SKILL_PATTERNS,
    EXPERIMENTATION_SIGNAL_PATTERNS,
    PREFERRED_CONTEXT_PATTERNS,
    REQUIRED_CONTEXT_PATTERNS,
    SENIORITY_HINTS,
    TOOLING_SIGNAL_PATTERNS,
    _SKILL_ALIASES,
    _BUSINESS_CONTEXT_CANDIDATES,
    _STAKEHOLDER_CONTEXT_CANDIDATES,
    _KPI_METRIC_CANDIDATES,
    _OWNERSHIP_SIGNAL_CANDIDATES,
    _WORKFLOW_CANDIDATES,
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

def _extract_text_phrase_hits(text: Any, candidates: List[str]) -> List[str]:
    text_norm = _normalize_text(text).lower()
    hits: List[str] = []

    for candidate in candidates:
        candidate_norm = _normalize_text(candidate).lower()
        if not candidate_norm:
            continue

        escaped = re.escape(candidate_norm).replace(r"\ ", r"\s+")
        prefix = r"(?<![a-z0-9])" if candidate_norm[:1].isalnum() else ""
        suffix = r"(?![a-z0-9])" if candidate_norm[-1:].isalnum() else ""

        if re.search(prefix + escaped + suffix, text_norm):
            hits.append(candidate_norm)

    return list(dict.fromkeys(hits))


def _extract_contextual_phrase_hits(
    text: Any,
    context_patterns: List[str],
    candidates: List[str],
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
    return _extract_text_phrase_hits(" ".join(deduped_chunks), candidates)


def _infer_role_archetype(
    title: str,
    role_family: str,
    business_contexts: List[str],
    workflows: List[str],
) -> str:
    title_norm = _normalize_text(title).lower()
    role_family_norm = _normalize_text(role_family).lower()
    business_contexts_set = set(_normalize_skill_list(business_contexts))
    workflows_set = set(_normalize_skill_list(workflows))

    if "analytics engineer" in title_norm or role_family_norm == "analytics engineer":
        return "analytics_engineer"

    if (
        "sales intelligence" in title_norm
        or "revenue operations" in title_norm
        or "sales" in business_contexts_set
        or "customer success" in business_contexts_set
        or "sales intelligence" in business_contexts_set
    ):
        return "revenue_sales_intelligence"

    if (
        "growth" in title_norm
        or "product" in title_norm
        or "plg" in business_contexts_set
        or "growth" in business_contexts_set
        or "retention" in business_contexts_set
        or "expansion" in business_contexts_set
        or "contraction" in business_contexts_set
    ):
        return "growth_product_analytics"

    if (
        "machine learning engineer" in title_norm
        or "ml engineer" in title_norm
        or "applied scientist" in title_norm
        or role_family_norm in {"ml engineer", "machine learning engineer"}
    ):
        return "applied_ml"

    if "data scientist" in title_norm or role_family_norm == "data scientist":
        return "data_scientist"

    if (
        "analyst" in title_norm
        or role_family_norm in {"analytics", "data analyst"}
        or "dashboards" in workflows_set
        or "reporting" in workflows_set
    ):
        return "data_analyst_bi"

    if business_contexts_set & {"public safety", "healthcare", "risk", "fraud", "supply chain"}:
        return "domain_heavy_analyst"

    return "general_analytics"


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
    raw_role_family = job.get("role_family", "")

    combined_text = " ".join([str(raw_title or ""), str(raw_preview or ""), str(raw_retrieval_text or "")]).strip()
    required_context_text = " ".join([str(raw_preview or ""), str(raw_retrieval_text or "")])

    required_skills = _normalize_skill_list(job.get("required_skills", []))
    preferred_skills = _normalize_skill_list(job.get("preferred_skills", []))
    all_skills = _normalize_skill_list(job.get("all_skills", []))

    fallback_required = _extract_contextual_skill_hits(
        required_context_text,
        REQUIRED_CONTEXT_PATTERNS,
    )
    fallback_preferred = _extract_contextual_skill_hits(
        required_context_text,
        PREFERRED_CONTEXT_PATTERNS,
    )
    fallback_all = _extract_text_skill_hits(combined_text)

    required_skills = list(dict.fromkeys(required_skills + fallback_required))
    preferred_skills = list(dict.fromkeys(preferred_skills + fallback_preferred))

    if not all_skills:
        all_skills = list(dict.fromkeys(required_skills + preferred_skills + fallback_all))
    else:
        all_skills = list(dict.fromkeys(all_skills + required_skills + preferred_skills + fallback_all))

    required_methods = _extract_contextual_phrase_hits(
        required_context_text,
        REQUIRED_CONTEXT_PATTERNS,
        ANALYTICS_ML_SIGNAL_PATTERNS + EXPERIMENTATION_SIGNAL_PATTERNS,
    )
    preferred_methods = _extract_contextual_phrase_hits(
        required_context_text,
        PREFERRED_CONTEXT_PATTERNS,
        ANALYTICS_ML_SIGNAL_PATTERNS + EXPERIMENTATION_SIGNAL_PATTERNS,
    )

    required_tools = _extract_contextual_phrase_hits(
        required_context_text,
        REQUIRED_CONTEXT_PATTERNS,
        TOOLING_SIGNAL_PATTERNS,
    )
    preferred_tools = _extract_contextual_phrase_hits(
        required_context_text,
        PREFERRED_CONTEXT_PATTERNS,
        TOOLING_SIGNAL_PATTERNS,
    )

    required_workflows = _extract_contextual_phrase_hits(
        required_context_text,
        REQUIRED_CONTEXT_PATTERNS,
        _WORKFLOW_CANDIDATES,
    )
    preferred_workflows = _extract_contextual_phrase_hits(
        required_context_text,
        PREFERRED_CONTEXT_PATTERNS,
        _WORKFLOW_CANDIDATES,
    )

    business_contexts = _extract_text_phrase_hits(combined_text, _BUSINESS_CONTEXT_CANDIDATES)
    stakeholder_contexts = _extract_text_phrase_hits(combined_text, _STAKEHOLDER_CONTEXT_CANDIDATES)
    kpi_metrics = _extract_text_phrase_hits(combined_text, _KPI_METRIC_CANDIDATES)
    ownership_signals = _extract_text_phrase_hits(combined_text, _OWNERSHIP_SIGNAL_CANDIDATES)

    title = _normalize_text(raw_title)
    role_family = _normalize_text(raw_role_family)
    seniority = _infer_seniority(title, job.get("seniority", ""))

    role_archetype = _infer_role_archetype(
        title,
        role_family,
        business_contexts,
        list(dict.fromkeys(required_workflows + preferred_workflows)),
    )

    return JobEvidence(
        job_doc_id=_normalize_text(job.get("doc_id", "")),
        company=_normalize_text(job.get("company", "")),
        title=title,
        location=_normalize_text(job.get("location", "")),
        source=_normalize_text(job.get("source", "")),
        job_url=_normalize_text(job.get("job_url", "")),
        posted_at=_normalize_text(job.get("posted_at", "")),
        role_family=role_family,
        seniority=seniority,
        required_skills=required_skills,
        preferred_skills=preferred_skills,
        all_skills=all_skills,
        role_archetype=role_archetype,
        required_methods=required_methods,
        preferred_methods=preferred_methods,
        required_tools=required_tools,
        preferred_tools=preferred_tools,
        required_workflows=required_workflows,
        preferred_workflows=preferred_workflows,
        business_contexts=business_contexts,
        stakeholder_contexts=stakeholder_contexts,
        kpi_metrics=kpi_metrics,
        ownership_signals=ownership_signals,
        visa_sponsorship=_normalize_text(job.get("visa_sponsorship", "")).lower(),
        ai_fit_score=job.get("ai_fit_score"),
        retrieval_text=_normalize_text(job.get("retrieval_text", "")),
        preview=_normalize_text(job.get("preview", "")),
        notes={
            "adapter_version": "v2_jd_structured_fields",
            "required_skill_count": len(required_skills),
            "preferred_skill_count": len(preferred_skills),
            "all_skill_count": len(all_skills),
            "required_method_count": len(required_methods),
            "preferred_method_count": len(preferred_methods),
            "required_tool_count": len(required_tools),
            "preferred_tool_count": len(preferred_tools),
            "required_workflow_count": len(required_workflows),
            "preferred_workflow_count": len(preferred_workflows),
            "business_context_count": len(business_contexts),
            "stakeholder_context_count": len(stakeholder_contexts),
            "kpi_metric_count": len(kpi_metrics),
            "ownership_signal_count": len(ownership_signals),
        },
    )


def build_job_evidence_batch(jobs: List[Dict[str, Any]]) -> List[JobEvidence]:
    return [build_job_evidence(job) for job in jobs]