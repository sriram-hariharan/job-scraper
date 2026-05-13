from __future__ import annotations

import re
from typing import Any, Iterable, Set, Tuple

from src.config.consts import (
    _SCAN_RECRUITER_TIPS_SIGNAL_KEYS,
    _SCAN_SKILLS_SIGNAL_KEYS,
    _SKILL_ALIASES,
    TITLE_CANONICAL,
)

SCORER_ALIGNED_SIGNAL_FAMILY_DIMENSIONS = {
    "recruiter_tips": {
        "believability",
        "business_context",
        "human_recruiter_match",
        "ownership_scope",
        "stakeholder_translation_alignment",
    },
    "tooling": {
        "required_skills_alignment",
        "preferred_skills_alignment",
        "tooling_alignment",
    },
    "methods": {
        "analytics_ml_depth",
        "experimentation_depth",
        "ml_match",
    },
    "workflow": {
        "ats_match",
        "title_alignment",
        "workflow_alignment",
    },
    "domain": {
        "business_context",
        "domain_match",
        "domain_relevance",
    },
}

SOFT_SKILL_TERMS = {
    "adaptability",
    "collaboration",
    "communication",
    "cross functional",
    "cross-functional",
    "decision making",
    "empathy",
    "leadership",
    "mentoring",
    "organization",
    "ownership",
    "problem solving",
    "stakeholder management",
    "stakeholders",
    "teamwork",
    "written communication",
}

OTHER_KEYWORD_TERMS = {
    "business impact",
    "customer",
    "customers",
    "domain",
    "industry",
    "metrics",
    "ownership scope",
    "scale",
    "seniority",
}

OTHER_KEYWORD_DIMENSION_KEYS = {
    "business_context",
    "ownership_scope",
    "human_recruiter_match",
    "believability",
}

TOOLING_DIMENSION_KEYS = {
    "tooling_alignment",
    "required_skills_alignment",
    "preferred_skills_alignment",
}

METHOD_DIMENSION_KEYS = {
    "analytics_ml_depth",
    "ml_match",
    "experimentation_depth",
}

SKILL_DIMENSION_KEYS = {
    "workflow_alignment",
    "title_alignment",
    "ats_match",
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def signal_key(value: Any) -> str:
    return _clean_text(value).lower().replace("-", "_").replace(" ", "_")


def canonical_signal_term(value: Any) -> str:
    text = _clean_text(value).lower()
    if not text:
        return ""

    for source, target in TITLE_CANONICAL.items():
        text = re.sub(rf"\b{re.escape(source)}\b", target, text)

    text = text.replace("&", " and ")
    text = re.sub(r"[^a-z0-9+/\-\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return _SKILL_ALIASES.get(text, text)


def signal_key_set(values: Iterable[Any]) -> Set[str]:
    keys: Set[str] = set()

    for value in values or []:
        cleaned = _clean_text(value)
        if not cleaned:
            continue

        lowered = cleaned.lower()
        canonical = canonical_signal_term(cleaned)

        for candidate in (
            lowered,
            canonical,
            signal_key(lowered),
            signal_key(canonical),
        ):
            if candidate:
                keys.add(candidate)

    return keys


def scan_issue_group_id_for_signals(
    signal_values: Iterable[Any],
    *,
    likely_impacted_dimensions: Iterable[Any] | None = None,
    lane: str = "",
) -> str:
    keys = signal_key_set(
        list(signal_values or []) + list(likely_impacted_dimensions or [])
    )

    if keys & set(_SCAN_RECRUITER_TIPS_SIGNAL_KEYS):
        return "recruiter_tips"

    if keys & set(_SCAN_SKILLS_SIGNAL_KEYS):
        return "skills"

    if _clean_text(lane) == "direction_only":
        return "recruiter_tips"

    return "skills"


def scan_issue_term_family(
    value: Any,
    dimensions: Iterable[Any] | None = None,
) -> str:
    keys = signal_key_set([value] + list(dimensions or []))

    if keys & set(_SCAN_RECRUITER_TIPS_SIGNAL_KEYS):
        return "recruiter_tips"

    if keys & TOOLING_DIMENSION_KEYS:
        return "tooling"

    if keys & METHOD_DIMENSION_KEYS:
        return "methods"

    if keys & SKILL_DIMENSION_KEYS:
        return "skills"

    return "skills"


def scan_issue_skill_type(
    value: Any,
    dimensions: Iterable[Any] | None = None,
) -> Tuple[str, str]:
    keys = signal_key_set([value])
    display_key = _clean_text(value).lower()
    soft_skill_keys = signal_key_set(SOFT_SKILL_TERMS)
    other_keyword_keys = signal_key_set(OTHER_KEYWORD_TERMS)
    dimension_keys = signal_key_set(dimensions or [])

    if keys & soft_skill_keys or display_key in SOFT_SKILL_TERMS:
        return "soft_skill", "Soft skill"

    if keys & other_keyword_keys:
        return "other_keyword", "Other keyword"

    if dimension_keys & OTHER_KEYWORD_DIMENSION_KEYS:
        return "other_keyword", "Other keyword"

    return "hard_skill", "Hard skill"
