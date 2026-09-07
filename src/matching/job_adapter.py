import re
from dataclasses import replace
from typing import Any, Dict, List

from src.matching.jd_intelligence_contract import (
    JD_INTELLIGENCE_MATCHING_ENRICHMENT_FIELDS,
    JD_INTELLIGENCE_MATCHING_PROVENANCE_FIELDS,
)
from src.matching.job_models import JobEvidence
from src.config.consts import (
    ANALYTICS_ML_SIGNAL_PATTERNS,
    COMMON_SKILL_PATTERNS,
    DOMAIN_SIGNAL_PATTERNS,
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
from src.config.role_taxonomy import ROLE_TAXONOMY
from src.utils.skill_normalizer import normalize_skill

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

# ---------------------------------------------------------------------------
# JD-intelligence enrichment compatibility helpers.
#
# Pure functions only. Nothing in this module calls them and build_job_evidence
# is unchanged, so deterministic extraction behaves exactly as before.
#
# They exist because the existing New Scan mapper
# (services._planning_scan_phase34a_provider_payload) flattens workflows,
# methods, ownership_signals and stakeholder_contexts into one
# "responsibilities" list and business_contexts into a "domain" string. That is
# correct for its own consumer but destroys the category identity JobEvidence
# needs, so a future starvation-triggered fallback needs category-preserving
# grounding, a JobEvidence-shaped candidate, and a fill-missing merge.
# ---------------------------------------------------------------------------

# Validated JD-intelligence response categories this layer understands.
JD_INTELLIGENCE_CANDIDATE_CATEGORIES = (
    "required_skills",
    "preferred_skills",
    "required_tools",
    "preferred_tools",
    "workflows",
    "methods",
    "business_contexts",
    "stakeholder_contexts",
)

# Category -> JobEvidence field. The response schema has flat workflows/methods
# with no required/preferred signal, so both map to the required field only and
# preferred_workflows / preferred_methods stay deterministic-only.
JD_INTELLIGENCE_CANDIDATE_FIELD_MAP = {
    "required_skills": "required_skills",
    "preferred_skills": "preferred_skills",
    "required_tools": "required_tools",
    "preferred_tools": "preferred_tools",
    "workflows": "required_workflows",
    "methods": "required_methods",
    "business_contexts": "business_contexts",
    "stakeholder_contexts": "stakeholder_contexts",
}

# V2 matching-enrichment categories preserve the contract's explicit strength.
# The v1 constants above remain available for the existing P1S10 compatibility
# proof and its different, flat schema.
JD_INTELLIGENCE_V2_CANDIDATE_CATEGORIES = (
    *JD_INTELLIGENCE_MATCHING_ENRICHMENT_FIELDS,
)
# Domain is provenance rather than a JobEvidence candidate field, but it must be
# grounded before the category validator can decide whether a positively known
# business-context component is safe to project. Seniority remains outside this
# matching enrichment path.
JD_INTELLIGENCE_V2_GROUNDING_CATEGORIES = tuple(
    category
    for category in JD_INTELLIGENCE_MATCHING_PROVENANCE_FIELDS
    if category != "seniority"
)
JD_INTELLIGENCE_V2_CANDIDATE_FIELD_MAP = {
    category: category for category in JD_INTELLIGENCE_V2_CANDIDATE_CATEGORIES
}
JD_INTELLIGENCE_ENRICHABLE_JOB_EVIDENCE_FIELDS = frozenset(
    JD_INTELLIGENCE_CANDIDATE_FIELD_MAP.values()
) | frozenset(JD_INTELLIGENCE_V2_CANDIDATE_FIELD_MAP.values())
_JD_INTELLIGENCE_V2_STRENGTH_PAIRS = (
    ("required_skills", "preferred_skills"),
    ("required_tools", "preferred_tools"),
    ("required_workflows", "preferred_workflows"),
    ("required_methods", "preferred_methods"),
)

_JD_GROUNDING_STOP_WORDS = frozenset(
    {
        "a",
        "an",
        "and",
        "as",
        "at",
        "by",
        "for",
        "from",
        "in",
        "into",
        "of",
        "on",
        "or",
        "our",
        "the",
        "their",
        "to",
        "using",
        "with",
    }
)
_JD_GROUNDING_IRREGULAR_INFLECTIONS = {
    "analyses": "analysis",
}


def _jd_grounding_token(value: str) -> str:
    token = _JD_GROUNDING_IRREGULAR_INFLECTIONS.get(value, value)
    if token.endswith("ies") and len(token) > 4:
        return token[:-3] + "y"
    if token.endswith(("ches", "shes", "xes", "zes", "ses")) and len(token) > 4:
        return token[:-2]
    if token.endswith("ing") and len(token) > 5:
        stem = token[:-3]
        if len(stem) > 3 and stem[-1:] == stem[-2:-1]:
            stem = stem[:-1]
        return stem
    if token.endswith("ed") and len(token) > 4:
        stem = token[:-2]
        if len(stem) > 3 and stem[-1:] == stem[-2:-1]:
            stem = stem[:-1]
        return stem
    if token.endswith("s") and not token.endswith("ss") and len(token) > 3:
        return token[:-1]
    return token


def _jd_grounding_tokens(value: Any) -> set[str]:
    return {
        _jd_grounding_token(token)
        for token in re.findall(r"[a-z0-9+#]+", str(value or "").casefold())
        if token not in _JD_GROUNDING_STOP_WORDS
    }


def _jd_signal_is_supported_by_span(signal: Any, evidence_span: Any) -> bool:
    """Require narrow lexical support; no fuzzy or semantic acceptance."""

    raw_signal = _normalize_text(signal)
    if not raw_signal:
        return False
    signal_variants = [raw_signal]
    aliased = _SKILL_ALIASES.get(raw_signal.casefold())
    if aliased:
        signal_variants.append(aliased)
    span_tokens = _jd_grounding_tokens(evidence_span)
    return bool(span_tokens) and any(
        bool(signal_tokens) and signal_tokens <= span_tokens
        for signal_tokens in map(_jd_grounding_tokens, signal_variants)
    )


def ground_jd_intelligence_signals_v2(
    payload: Dict[str, Any],
    job_text: Any,
) -> tuple[Dict[str, List[Dict[str, str]]], Dict[str, List[Dict[str, Any]]]]:
    """Ground v2 item objects while preserving evidence through validation.

    A span must occur byte-for-byte in the authoritative JD and must narrowly
    support the normalized signal after punctuation, stopword, and conservative
    inflection normalization. Rejections retain their item and reason.
    """

    source_text = str(job_text or "")
    grounded: Dict[str, List[Dict[str, str]]] = {}
    rejected: Dict[str, List[Dict[str, Any]]] = {}
    strength_conflicts: set[str] = set()
    for required_category, preferred_category in _JD_INTELLIGENCE_V2_STRENGTH_PAIRS:
        strength_values: List[set[str]] = []
        for category in (required_category, preferred_category):
            strength_values.append(
                {
                    normalized[0]
                    for item in list(payload.get(category) or [])
                    if isinstance(item, dict)
                    for normalized in [_normalize_skill_list([item.get("signal")])]
                    if normalized
                }
            )
        strength_conflicts.update(strength_values[0] & strength_values[1])

    for category in JD_INTELLIGENCE_V2_GROUNDING_CATEGORIES:
        values = payload.get(category)
        if not isinstance(values, list):
            continue
        accepted: List[Dict[str, str]] = []
        refused: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for item in values:
            if not isinstance(item, dict):
                refused.append({"item": item, "reason": "malformed_item"})
                continue
            signal = _normalize_text(item.get("signal"))
            evidence_span = item.get("evidence_span")
            if not signal or not isinstance(evidence_span, str) or not evidence_span.strip():
                refused.append({"item": dict(item), "reason": "malformed_item"})
                continue
            normalized_values = _normalize_skill_list([signal])
            if not normalized_values:
                refused.append({"item": dict(item), "reason": "malformed_item"})
                continue
            normalized_signal = normalized_values[0]
            if normalized_signal in strength_conflicts:
                refused.append(
                    {
                        "item": dict(item),
                        "reason": "conflicting_requirement_strength",
                    }
                )
                continue
            if evidence_span not in source_text:
                refused.append({"item": dict(item), "reason": "span_not_verbatim"})
                continue
            if not _jd_signal_is_supported_by_span(signal, evidence_span):
                refused.append({"item": dict(item), "reason": "signal_not_supported"})
                continue
            if normalized_signal in seen:
                continue
            seen.add(normalized_signal)
            accepted.append(
                {"signal": normalized_signal, "evidence_span": evidence_span}
            )

        if accepted:
            grounded[category] = accepted
        if refused:
            rejected[category] = refused

    return grounded, rejected


_JD_INTELLIGENCE_V2_CATEGORY_BASE = {
    "required_skills": "skill",
    "preferred_skills": "skill",
    "required_tools": "tool",
    "preferred_tools": "tool",
    "required_workflows": "workflow",
    "preferred_workflows": "workflow",
    "required_methods": "method",
    "preferred_methods": "method",
    "business_contexts": "business_context",
    "stakeholder_contexts": "stakeholder_context",
    "ownership_signals": "ownership_signal",
    "domain": "domain",
}
_JD_INTELLIGENCE_V2_STRENGTH_DESTINATIONS = {
    ("skill", "required"): "required_skills",
    ("skill", "preferred"): "preferred_skills",
    ("tool", "required"): "required_tools",
    ("tool", "preferred"): "preferred_tools",
    ("workflow", "required"): "required_workflows",
    ("workflow", "preferred"): "preferred_workflows",
    ("method", "required"): "required_methods",
    ("method", "preferred"): "preferred_methods",
}
_JD_INTELLIGENCE_V2_UNSTRENGTHENED_DESTINATIONS = {
    "business_context": "business_contexts",
    "stakeholder_context": "stakeholder_contexts",
    "ownership_signal": "ownership_signals",
    "domain": "domain",
}
_JD_INTELLIGENCE_V2_CATEGORY_REASON_LABELS = {
    "skill": "skill",
    "tool": "tool",
    "workflow": "workflow",
    "method": "method",
    "business_context": "business_context",
    "stakeholder_context": "stakeholder_context",
    "ownership_signal": "ownership_signal",
    "domain": "domain",
}


def _jd_existing_role_taxonomy_tool_match(signal: str) -> bool:
    """Reuse only existing role-family tooling patterns; add no vocabulary."""

    normalized = _normalize_text(signal).lower()
    if not normalized:
        return False
    for family in ROLE_TAXONOMY.values():
        for pattern in family.get("tooling_patterns", ()):
            if re.fullmatch(str(pattern), normalized, re.I):
                return True
    return False


# Coordination punctuation and conjunctions that deterministically separate list
# members inside one signal. Nothing else splits a signal, so a compound such as
# "software-engineering" stays whole.
_JD_CONTEXT_SEGMENT_SPLIT = re.compile(r"\s*(?:[,;/&]|\band\b|\bor\b)\s*")


def _jd_context_segment_hits(
    normalized: str,
    candidates: List[str],
) -> List[str]:
    """Admit a context term only when it fills a whole coordination segment.

    P1S22 proved that lexical containment admits wrong categories: the
    stakeholder term "engineering" was accepted inside "strong
    software-engineering skills" and "long-horizon autonomous engineering",
    neither of which names a group. Requiring the term to fill a complete
    comma/conjunction segment preserves P1S18's "manufacturing and supply
    chain" -> "supply chain" projection while rejecting embedded compounds and
    trailing heads. It adds no vocabulary and infers nothing beyond the
    existing matcher; an undecidable case simply fails closed.
    """

    segments = {
        segment
        for segment in (
            _normalize_text(part).lower()
            for part in _JD_CONTEXT_SEGMENT_SPLIT.split(normalized)
        )
        if segment
    }
    if not segments:
        return []
    return [
        value
        for value in _extract_text_phrase_hits(normalized, candidates)
        if value in segments
    ]


# --- P1S24 validator-only supplemental recognition -------------------------
#
# Consulted ONLY by _jd_category_hits, which only the grounded-category
# validator calls. build_job_evidence, the scorer, resume extraction, the
# prefilter and the P1S21 extraction-health helper never reach it, so a term
# here cannot change baseline JD extraction or fallback eligibility. Adding it
# to src/config/consts.py would have all of those effects, which is why it
# lives here.
#
# It recognizes a grounded phrase AS A WHOLE by its grammatical head rather
# than extracting an embedded vocabulary term from a longer phrase, so it
# cannot reopen the P1S23 containment defect: "software-engineering skills"
# and "long-horizon autonomous engineering" have no group head and stay
# unrecognized, while "engineering team" is a group and is recognized.
_JD_SUPPLEMENTAL_STAKEHOLDER_HEADS = frozenset({"team", "teams"})
# A bare head is too generic to be evidence; a longer span is a sentence rather
# than a group name.
_JD_SUPPLEMENTAL_STAKEHOLDER_TOKEN_BOUNDS = (2, 4)
# Closed grammatical class: determiners, demonstratives, quantifiers, pronouns
# and prepositions. A group name is built from content words, so any function
# word inside the segment marks prose ("about the rl teams", "across teams")
# rather than a named group. The shared grounding stop words are reused and
# extended locally; grounding itself is untouched.
_JD_SUPPLEMENTAL_FUNCTION_WORDS = _JD_GROUNDING_STOP_WORDS | frozenset(
    {
        "about", "across", "after", "all", "any", "before", "between",
        "both", "each", "every", "few", "he", "her", "his", "it", "its",
        "many", "most", "my", "several", "she", "some", "such", "that",
        "these", "they", "this", "those", "us", "we", "what", "which",
        "who", "you", "your",
    }
)


def _jd_supplemental_stakeholder_hits(normalized: str) -> List[str]:
    """Recognize grounded phrases whose head noun names a team or function.

    Validator-only and pure. Reuses the P1S23 coordination segmentation, so a
    term embedded in a longer phrase is still refused; only a whole segment
    whose last token is a group head is admitted, and the segment is projected
    verbatim rather than reduced to a guessed canonical form.
    """

    minimum, maximum = _JD_SUPPLEMENTAL_STAKEHOLDER_TOKEN_BOUNDS
    hits: List[str] = []
    for part in _JD_CONTEXT_SEGMENT_SPLIT.split(normalized):
        segment = _normalize_text(part).lower()
        if not segment:
            continue
        tokens = segment.split(" ")
        if not minimum <= len(tokens) <= maximum:
            continue
        if tokens[-1] not in _JD_SUPPLEMENTAL_STAKEHOLDER_HEADS:
            continue
        # Function words mark prose, not a named group.
        if any(token in _JD_SUPPLEMENTAL_FUNCTION_WORDS for token in tokens):
            continue
        hits.append(segment)
    return list(dict.fromkeys(hits))


def _jd_category_hits(signal: str) -> Dict[str, List[str]]:
    """Return positive classifications from existing deterministic owners."""

    normalized_values = _normalize_skill_list([signal])
    if not normalized_values:
        return {}
    normalized = normalized_values[0]

    exact = lambda values: [value for value in values if value == normalized]
    hits: Dict[str, List[str]] = {
        "tool": _extract_text_phrase_hits(normalized, TOOLING_SIGNAL_PATTERNS),
        "workflow": exact(
            _extract_text_phrase_hits(normalized, _WORKFLOW_CANDIDATES)
        ),
        "method": exact(
            _extract_text_phrase_hits(
                normalized,
                ANALYTICS_ML_SIGNAL_PATTERNS
                + EXPERIMENTATION_SIGNAL_PATTERNS,
            )
        ),
        "business_context": _jd_context_segment_hits(
            normalized, _BUSINESS_CONTEXT_CANDIDATES
        ),
        "stakeholder_context": _normalize_skill_list(
            _jd_context_segment_hits(
                normalized, _STAKEHOLDER_CONTEXT_CANDIDATES
            )
            + _jd_supplemental_stakeholder_hits(normalized)
        ),
        "ownership_signal": _extract_text_phrase_hits(
            normalized, _OWNERSHIP_SIGNAL_CANDIDATES
        ),
        "domain": _jd_context_segment_hits(normalized, DOMAIN_SIGNAL_PATTERNS),
        "skill": exact(_extract_text_skill_hits(normalized)),
    }
    if not hits["tool"] and _jd_existing_role_taxonomy_tool_match(normalized):
        hits["tool"] = [normalized]

    # build_job_evidence already removes workflow overlaps from methods.
    hits["method"] = _prune_method_targets(hits["method"], hits["workflow"])

    # A dedicated category is stronger evidence than COMMON_SKILL_PATTERNS,
    # whose compatibility role intentionally includes tools and methods.
    dedicated = {
        value
        for category in ("tool", "workflow", "method")
        for value in hits[category]
    }
    hits["skill"] = [value for value in hits["skill"] if value not in dedicated]
    return {category: values for category, values in hits.items() if values}


def _jd_source_strength(category: str) -> str:
    if category.startswith("required_"):
        return "required"
    if category.startswith("preferred_"):
        return "preferred"
    return ""


def _jd_destination_category(base: str, source_category: str) -> str | None:
    strength = _jd_source_strength(source_category)
    if base in {"skill", "tool", "workflow", "method"}:
        if not strength:
            return None
        return _JD_INTELLIGENCE_V2_STRENGTH_DESTINATIONS.get((base, strength))
    return _JD_INTELLIGENCE_V2_UNSTRENGTHENED_DESTINATIONS.get(base)


def _jd_is_unsupported_education(signal: str) -> bool:
    normalized = _normalize_text(signal).lower()
    if not normalized:
        return False
    return normalize_skill(normalized) is None and any(
        marker in normalized
        for marker in ("degree", "bachelor", "master", "phd")
    )


def validate_grounded_jd_intelligence_categories_v2(
    grounded_signals: Dict[str, List[Dict[str, str]]],
) -> tuple[Dict[str, List[Dict[str, str]]], Dict[str, List[Dict[str, Any]]]]:
    """Validate grounded category identity using existing deterministic owners.

    The function is pure and fail-closed. It preserves evidence spans and
    required/preferred strength, projects only positively recognized taxonomy
    terms, and returns bounded kept/reclassified/quarantined diagnostics.
    """

    decisions: List[Dict[str, Any]] = []
    for source_category in JD_INTELLIGENCE_V2_GROUNDING_CATEGORIES:
        source_base = _JD_INTELLIGENCE_V2_CATEGORY_BASE[source_category]
        for raw_item in list(grounded_signals.get(source_category) or []):
            if not isinstance(raw_item, dict):
                continue
            signal = _normalize_text(raw_item.get("signal"))
            evidence_span = str(raw_item.get("evidence_span") or "")
            item = {
                "signal": signal.lower(),
                "evidence_span": evidence_span,
            }
            hits = _jd_category_hits(signal)

            # Domain provenance can safely yield a known business-context
            # component; it is never moved merely because domain lacks a
            # JobEvidence candidate field.
            if source_base == "domain" and hits.get("business_context"):
                supported_bases = ["business_context"]
            elif source_base in hits:
                supported_bases = [source_base]
            else:
                supported_bases = [
                    base
                    for base in hits
                    if _jd_destination_category(base, source_category)
                ]

            # Dedicated tool/workflow/method evidence outranks generic skill
            # evidence. Other multi-category overlap remains ambiguous.
            if source_base == "skill":
                specific = [
                    base
                    for base in ("tool", "workflow", "method")
                    if base in supported_bases
                ]
                if len(specific) == 1:
                    supported_bases = specific

            if len(supported_bases) != 1:
                reason = (
                    "unsupported_matching_category:education"
                    if _jd_is_unsupported_education(signal)
                    else "ambiguous_category"
                    if len(supported_bases) > 1
                    else "unknown_taxonomy_signal"
                )
                decisions.append(
                    {
                        "source_category": source_category,
                        "item": item,
                        "status": "quarantined",
                        "reason": reason,
                    }
                )
                continue

            destination_base = supported_bases[0]
            destination_category = _jd_destination_category(
                destination_base, source_category
            )
            if not destination_category:
                decisions.append(
                    {
                        "source_category": source_category,
                        "item": item,
                        "status": "quarantined",
                        "reason": "unsupported_matching_category",
                    }
                )
                continue

            projected = hits[destination_base]
            for projected_signal in projected:
                projected_item = {
                    "signal": projected_signal,
                    "evidence_span": evidence_span,
                }
                kept = destination_category == source_category
                decisions.append(
                    {
                        "source_category": source_category,
                        "destination_category": destination_category,
                        "item": projected_item,
                        "status": "kept" if kept else "reclassified",
                        "reason": (
                            "category_confirmed"
                            if kept
                            else "reclassified_to_"
                            + _JD_INTELLIGENCE_V2_CATEGORY_REASON_LABELS[
                                destination_base
                            ]
                        ),
                    }
                )

    # Resolve duplicates after reclassification. Dedicated categories beat a
    # generic skill placement; conflicting strengths fail closed.
    by_signal: Dict[str, List[Dict[str, Any]]] = {}
    for decision in decisions:
        if decision["status"] != "quarantined":
            by_signal.setdefault(decision["item"]["signal"], []).append(decision)

    for same_signal in by_signal.values():
        destinations = {
            decision["destination_category"] for decision in same_signal
        }
        bases = {
            _JD_INTELLIGENCE_V2_CATEGORY_BASE[destination]
            for destination in destinations
        }
        strengths = {
            _jd_source_strength(destination)
            for destination in destinations
            if _jd_source_strength(destination)
        }
        if len(strengths) > 1:
            for decision in same_signal:
                decision["status"] = "quarantined"
                decision["reason"] = (
                    "conflicting_requirement_strength_after_reclassification"
                )
            continue
        if len(destinations) == 1 and len(same_signal) > 1:
            winner = next(
                (
                    decision
                    for decision in same_signal
                    if decision["status"] == "kept"
                ),
                same_signal[0],
            )
            for decision in same_signal:
                if decision is winner:
                    continue
                decision["status"] = "quarantined"
                decision["reason"] = "duplicate_more_specific_category"
            continue
        if "skill" in bases and len(bases) == 2:
            non_skill = bases - {"skill"}
            if non_skill <= {"tool", "workflow", "method"}:
                for decision in same_signal:
                    if _JD_INTELLIGENCE_V2_CATEGORY_BASE[
                        decision["destination_category"]
                    ] == "skill":
                        decision["status"] = "quarantined"
                        decision["reason"] = "duplicate_more_specific_category"
        elif len(bases) > 1:
            for decision in same_signal:
                decision["status"] = "quarantined"
                decision["reason"] = "ambiguous_cross_category_duplicate"

    validated: Dict[str, List[Dict[str, str]]] = {}
    diagnostics: Dict[str, List[Dict[str, Any]]] = {
        "kept": [],
        "reclassified": [],
        "quarantined": [],
    }
    seen_outputs: set[tuple[str, str]] = set()
    for decision in decisions:
        diagnostic = {
            "source_category": decision["source_category"],
            "item": dict(decision["item"]),
            "reason": decision["reason"],
        }
        destination = decision.get("destination_category")
        if destination:
            diagnostic["destination_category"] = destination
        diagnostics[decision["status"]].append(diagnostic)
        if decision["status"] == "quarantined" or not destination:
            continue
        output_key = (destination, decision["item"]["signal"])
        if output_key in seen_outputs:
            continue
        seen_outputs.add(output_key)
        validated.setdefault(destination, []).append(dict(decision["item"]))

    return validated, diagnostics


def build_job_evidence_enrichment_candidate_v2(
    grounded_signals: Dict[str, List[Dict[str, str]]],
) -> Dict[str, List[str]]:
    """Project category-validated v2 items without changing strength."""

    candidate: Dict[str, List[str]] = {}
    for category, field_name in JD_INTELLIGENCE_V2_CANDIDATE_FIELD_MAP.items():
        values = _normalize_skill_list(
            [
                item.get("signal")
                for item in list(grounded_signals.get(category) or [])
                if isinstance(item, dict)
            ]
        )
        if values:
            candidate[field_name] = values
    return candidate


def _jd_signal_is_grounded(value: Any, source_text_norm: str) -> bool:
    """Reuse this module's existing containment check as the grounding test."""
    normalized = _normalize_text(value).lower()
    if not normalized:
        return False
    return _skill_present(source_text_norm, normalized)


def ground_jd_intelligence_signals(
    payload: Dict[str, Any],
    job_text: Any,
    *,
    grounding_predicate: Any = None,
) -> tuple[Dict[str, List[str]], Dict[str, List[str]]]:
    """Ground a validated JD-intelligence payload without flattening categories.

    Returns (grounded, rejected), both keyed by the original response category.
    A value is kept only when it appears in the supplied JD text.
    """
    source_text_norm = _normalize_text(job_text).lower()
    predicate = grounding_predicate or _jd_signal_is_grounded

    grounded: Dict[str, List[str]] = {}
    rejected: Dict[str, List[str]] = {}

    for category in JD_INTELLIGENCE_CANDIDATE_CATEGORIES:
        raw_values = payload.get(category)
        if not isinstance(raw_values, list):
            continue

        accepted: List[str] = []
        refused: List[str] = []
        for value in _normalize_skill_list(raw_values):
            if predicate(value, source_text_norm):
                accepted.append(value)
            else:
                refused.append(value)

        if accepted:
            grounded[category] = accepted
        if refused:
            rejected[category] = refused

    return grounded, rejected


def build_job_evidence_enrichment_candidate(
    grounded_signals: Dict[str, List[str]],
) -> Dict[str, List[str]]:
    """Map grounded categories onto JobEvidence field names.

    Evidence mapping only: no scoring values, no role archetype, no seniority,
    and never preferred_workflows / preferred_methods.
    """
    candidate: Dict[str, List[str]] = {}

    for category, field_name in JD_INTELLIGENCE_CANDIDATE_FIELD_MAP.items():
        values = _normalize_skill_list(list(grounded_signals.get(category) or []))
        if values:
            candidate[field_name] = values

    return candidate


def merge_missing_job_evidence(
    evidence: JobEvidence,
    candidate: Dict[str, List[str]],
) -> JobEvidence:
    """Fill-missing merge: populate only empty target groups.

    Deterministic evidence stays authoritative. A field that already holds any
    value is preserved byte-for-byte, and nothing is reclassified or removed.
    Returns a new JobEvidence; the input is never mutated.
    """
    fills: Dict[str, List[str]] = {}

    for field_name, values in dict(candidate or {}).items():
        if field_name not in JD_INTELLIGENCE_ENRICHABLE_JOB_EVIDENCE_FIELDS:
            continue
        if getattr(evidence, field_name, None):
            continue
        normalized = _normalize_skill_list(list(values or []))
        if normalized:
            fills[field_name] = normalized

    if not fills:
        return evidence

    return replace(evidence, **fills)


# ---------------------------------------------------------------------------
# JD extraction health / fallback eligibility.
#
# Pure and job-only. Nothing in this module calls it; it does not read resumes,
# scores, semantic similarity, the environment, or any provider.
#
# It replaces the experimental raw-field starvation test that counted six
# JobEvidence fields. P1S20 proved that test was structurally unsound: it gave
# required_* and preferred_* separate votes for one conceptual category, treated
# a legitimately absent "preferred" section as starvation, and counted the
# method fields even though generic process methods cannot currently be scored
# (job-side writers, resume-side evidence and both scorer consumers all project
# methods through analytics/ML and experimentation vocabularies). A single
# precise vocabulary addition could therefore flip fallback eligibility without
# the JD changing.
#
# Only categories matching can actually consume are counted. Methods are
# excluded until the method contract is extended. Skills and tools are excluded
# because they already have their own deterministic and LLM enrichment owners
# and were not part of the proven starvation mechanism.
# ---------------------------------------------------------------------------

# Conceptual category -> the JobEvidence fields that can satisfy it. A category
# is healthy when any of its fields holds evidence, so required/preferred pairs
# count once.
JD_CONSUMABLE_EVIDENCE_CATEGORIES = {
    "workflows": ("required_workflows", "preferred_workflows"),
    "business_context": ("business_contexts",),
    "stakeholder_context": ("stakeholder_contexts",),
}

# Selected from the measured 80-job distribution: eligibility requires every
# consumable category to be missing. At this threshold the trigger fires for
# 20/80 jobs and is identical before and after the P1S19 vocabulary additions,
# whereas the looser ">= 2 missing" rule fires for 42/80 and moves with them.
JD_CONSUMABLE_EVIDENCE_MISSING_THRESHOLD = len(JD_CONSUMABLE_EVIDENCE_CATEGORIES)


def assess_jd_extraction_health(evidence: JobEvidence) -> Dict[str, Any]:
    """Report which consumable evidence categories a JobEvidence is missing.

    Deterministic, job-only and side-effect free. Returns the populated and
    missing category names alongside the counts, so a caller can explain why
    enrichment was or was not considered rather than seeing only a boolean.
    """
    populated: List[str] = []
    missing: List[str] = []

    for category in sorted(JD_CONSUMABLE_EVIDENCE_CATEGORIES):
        fields = JD_CONSUMABLE_EVIDENCE_CATEGORIES[category]
        if any(getattr(evidence, field, None) for field in fields):
            populated.append(category)
        else:
            missing.append(category)

    return {
        "populated_categories": populated,
        "missing_categories": missing,
        "missing_count": len(missing),
        "considered_count": len(JD_CONSUMABLE_EVIDENCE_CATEGORIES),
        "threshold": JD_CONSUMABLE_EVIDENCE_MISSING_THRESHOLD,
        "enrichment_eligible": (
            len(missing) >= JD_CONSUMABLE_EVIDENCE_MISSING_THRESHOLD
        ),
    }
