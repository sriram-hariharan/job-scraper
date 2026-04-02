import re
from typing import Any, Dict, List

from src.matching.job_models import JobEvidence
from src.config.consts import (
    ANALYTICS_ML_SIGNAL_PATTERNS,
    COMMON_SKILL_PATTERNS,
    EXPERIMENTATION_SIGNAL_PATTERNS,
    GENERIC_REQUIRED_SKILL_TARGETS,
    PREFERRED_CONTEXT_PATTERNS,
    REQUIRED_CONTEXT_PATTERNS,
    RESPONSIBILITY_CONTEXT_PATTERNS,
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

        skill = _normalize_text(_SKILL_ALIASES.get(skill, skill)).lower()
        if not skill:
            continue

        if skill not in seen:
            seen.add(skill)
            normalized.append(skill)

    return normalized

def _filter_known_skill_targets(values: Any) -> List[str]:
    allowed = {_normalize_text(value).lower() for value in COMMON_SKILL_PATTERNS}
    normalized = _normalize_skill_list(values)
    return [value for value in normalized if value in allowed]

def _filter_specific_required_skill_targets(values: Any) -> List[str]:
    generic = {_normalize_text(value).lower() for value in GENERIC_REQUIRED_SKILL_TARGETS}
    normalized = _normalize_skill_list(values)
    return [value for value in normalized if value not in generic]

def _merge_structured_skill_targets(
    raw_skills: Any,
    contextual_skill_hits: List[str],
    tools: List[str],
) -> List[str]:
    filtered_raw = _filter_specific_required_skill_targets(
        _filter_known_skill_targets(raw_skills)
    )
    filtered_contextual = _filter_specific_required_skill_targets(contextual_skill_hits)

    return list(dict.fromkeys(
        filtered_raw
        + filtered_contextual
        + _normalize_skill_list(tools)
    ))

def _strip_company_self_mentions(text: Any, company: Any) -> str:
    value = _normalize_text(text)
    company_norm = _normalize_text(company).lower()

    if not value or not company_norm:
        return value

    escaped = re.escape(company_norm).replace(r"\ ", r"\s+")
    stripped = re.sub(
        rf"(?<![a-z0-9]){escaped}(?![a-z0-9])",
        " ",
        value,
        flags=re.I,
    )
    return _normalize_text(stripped)


def _filter_company_self_match(values: Any, company: Any) -> List[str]:
    company_norm = _normalize_text(company).lower()
    normalized = _normalize_skill_list(values)

    if not company_norm:
        return normalized

    return [value for value in normalized if value != company_norm]

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

def _collect_context_chunks(
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

    return list(dict.fromkeys(gathered_chunks))

def _extract_contextual_skill_hits(
    text: Any,
    context_patterns: List[str],
) -> List[str]:
    gathered_chunks = _collect_context_chunks(text, context_patterns)
    if not gathered_chunks:
        return []

    return _extract_text_skill_hits(" ".join(gathered_chunks))

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
    gathered_chunks = _collect_context_chunks(text, context_patterns)
    if not gathered_chunks:
        return []

    return _extract_text_phrase_hits(" ".join(gathered_chunks), candidates)

def _prune_method_targets(
    values: List[str],
    workflow_targets: List[str],
) -> List[str]:
    normalized_values = _normalize_skill_list(values)
    workflow_set = set(_normalize_skill_list(workflow_targets))

    filtered = [
        value for value in normalized_values
        if value not in workflow_set
    ]

    return [
        value for value in filtered
        if value not in GENERIC_REQUIRED_SKILL_TARGETS
    ]

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
    raw_company = job.get("company", "")

    sanitized_preview = _strip_company_self_mentions(raw_preview, raw_company)
    sanitized_retrieval_text = _strip_company_self_mentions(raw_retrieval_text, raw_company)

    combined_text = " ".join([str(raw_title or ""), sanitized_preview, sanitized_retrieval_text]).strip()
    required_context_text = " ".join([sanitized_preview, sanitized_retrieval_text]).strip()
    required_work_context_patterns = list(dict.fromkeys(
        REQUIRED_CONTEXT_PATTERNS + RESPONSIBILITY_CONTEXT_PATTERNS
    ))
    structured_context_patterns = list(dict.fromkeys(
        required_work_context_patterns + PREFERRED_CONTEXT_PATTERNS
    ))
    structured_context_chunks = _collect_context_chunks(
        required_context_text,
        structured_context_patterns,
    )

    structured_context_text = " ".join(structured_context_chunks).strip() or combined_text

    raw_required_skills = job.get("required_skills", [])
    raw_preferred_skills = job.get("preferred_skills", [])
    raw_all_skills = _filter_known_skill_targets(job.get("all_skills", []))

    fallback_required = _extract_contextual_skill_hits(
        required_context_text,
        REQUIRED_CONTEXT_PATTERNS,
    )
    fallback_preferred = _extract_contextual_skill_hits(
        required_context_text,
        PREFERRED_CONTEXT_PATTERNS,
    )
    fallback_all = _filter_specific_required_skill_targets(
        _extract_text_skill_hits(combined_text)
    )

    required_methods = _normalize_skill_list(_extract_contextual_phrase_hits(
        required_context_text,
        required_work_context_patterns,
        ANALYTICS_ML_SIGNAL_PATTERNS + EXPERIMENTATION_SIGNAL_PATTERNS,
    ))
    preferred_methods = [
        value for value in _normalize_skill_list(_extract_contextual_phrase_hits(
            required_context_text,
            PREFERRED_CONTEXT_PATTERNS,
            ANALYTICS_ML_SIGNAL_PATTERNS + EXPERIMENTATION_SIGNAL_PATTERNS,
        ))
        if value not in required_methods
    ]

    required_tools = _normalize_skill_list(_extract_contextual_phrase_hits(
        required_context_text,
        required_work_context_patterns,
        TOOLING_SIGNAL_PATTERNS,
    ))
    preferred_tools = [
        value for value in _normalize_skill_list(_extract_contextual_phrase_hits(
            required_context_text,
            PREFERRED_CONTEXT_PATTERNS,
            TOOLING_SIGNAL_PATTERNS,
        ))
        if value not in required_tools
    ]
    required_tools = _filter_company_self_match(required_tools, raw_company)
    preferred_tools = _filter_company_self_match(preferred_tools, raw_company)

    required_workflows = _normalize_skill_list(_extract_contextual_phrase_hits(
        required_context_text,
        required_work_context_patterns,
        _WORKFLOW_CANDIDATES,
    ))
    preferred_workflows = [
        value for value in _normalize_skill_list(_extract_contextual_phrase_hits(
            required_context_text,
            PREFERRED_CONTEXT_PATTERNS,
            _WORKFLOW_CANDIDATES,
        ))
        if value not in required_workflows
    ]
    
    required_methods = _prune_method_targets(
        required_methods,
        required_workflows + preferred_workflows,
    )
    preferred_methods = [
        value for value in _prune_method_targets(
            preferred_methods,
            required_workflows + preferred_workflows,
        )
        if value not in required_methods
    ]

    required_skills = _filter_company_self_match(
        _merge_structured_skill_targets(
            raw_required_skills,
            fallback_required,
            required_tools,
        ),
        raw_company,
    )
    preferred_skills = [
        skill
        for skill in _filter_company_self_match(
            _merge_structured_skill_targets(
                raw_preferred_skills,
                fallback_preferred,
                preferred_tools,
            ),
            raw_company,
        )
        if skill not in required_skills
    ]

    if not required_skills and not required_tools and preferred_tools:
        required_skills = _filter_company_self_match(
            _normalize_skill_list(preferred_tools),
            raw_company,
        )
        preferred_skills = [
            skill for skill in preferred_skills
            if skill not in required_skills
        ]

    required_tools = list(dict.fromkeys(
        required_tools
        + [skill for skill in required_skills if skill in TOOLING_SIGNAL_PATTERNS]
    ))
    preferred_tools = list(dict.fromkeys(
        [skill for skill in preferred_tools if skill not in required_tools]
        + [
            skill for skill in preferred_skills
            if skill in TOOLING_SIGNAL_PATTERNS and skill not in required_tools
        ]
    ))

    all_skills = _filter_company_self_match(
        [
            skill
            for skill in list(dict.fromkeys(
                raw_all_skills
                + required_skills
                + preferred_skills
                + [
                    skill for skill in fallback_all
                    if skill not in required_skills and skill not in preferred_skills
                ]
            ))
            if skill not in GENERIC_REQUIRED_SKILL_TARGETS
        ],
        raw_company,
    )

    business_contexts = _extract_text_phrase_hits(structured_context_text, _BUSINESS_CONTEXT_CANDIDATES)
    stakeholder_contexts = _extract_text_phrase_hits(structured_context_text, _STAKEHOLDER_CONTEXT_CANDIDATES)
    kpi_metrics = _extract_text_phrase_hits(structured_context_text, _KPI_METRIC_CANDIDATES)
    ownership_signals = _extract_text_phrase_hits(structured_context_text, _OWNERSHIP_SIGNAL_CANDIDATES)

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