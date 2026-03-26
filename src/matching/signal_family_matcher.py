from typing import Dict, List, Sequence
import re

from src.config.consts import (
    ANALYTICS_ML_SIGNAL_PATTERNS,
    DOMAIN_SIGNAL_PATTERNS,
    EXPERIMENTATION_SIGNAL_PATTERNS,
    TOOLING_SIGNAL_PATTERNS,
    _SKILL_ALIASES,
)

FAMILY_PRIORITY = [
    "experimentation",
    "analytics_ml",
    "domain",
    "tooling",
]

FAMILY_PATTERNS: Dict[str, List[str]] = {
    "experimentation": list(EXPERIMENTATION_SIGNAL_PATTERNS),
    "analytics_ml": list(ANALYTICS_ML_SIGNAL_PATTERNS),
    "domain": list(DOMAIN_SIGNAL_PATTERNS),
    "tooling": list(TOOLING_SIGNAL_PATTERNS),
}

def normalize_signal_text(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def _unique_preserve_order(values: Sequence[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []

    for value in values:
        item = normalize_signal_text(value)
        if not item or item in seen:
            continue
        seen.add(item)
        ordered.append(item)

    return ordered


def family_registry() -> Dict[str, List[str]]:
    return {
        family: _unique_preserve_order(patterns)
        for family, patterns in FAMILY_PATTERNS.items()
    }


def family_hits_from_text(text: str) -> Dict[str, List[str]]:
    text_norm = normalize_signal_text(text)
    if not text_norm:
        return {}

    hits: Dict[str, List[str]] = {}
    registry = family_registry()

    for family in FAMILY_PRIORITY:
        matched = [
            term
            for term in registry.get(family, [])
            if term and term in text_norm
        ]
        if matched:
            hits[family] = matched

    return hits


def prioritized_family_terms_from_text(text: str) -> List[str]:
    hits = family_hits_from_text(text)
    ordered: List[str] = []

    for family in FAMILY_PRIORITY:
        ordered.extend(hits.get(family, []))

    return _unique_preserve_order(ordered)


def families_for_terms(terms: Sequence[str]) -> List[str]:
    normalized_terms = set(_unique_preserve_order(terms))
    if not normalized_terms:
        return []

    registry = family_registry()
    matched_families: List[str] = []

    for family in FAMILY_PRIORITY:
        family_terms = set(registry.get(family, []))
        if normalized_terms & family_terms:
            matched_families.append(family)

    return matched_families

def family_for_term(term: str) -> str:
    normalized = normalize_signal_text(term)
    if not normalized:
        return ""

    registry = family_registry()
    for family in FAMILY_PRIORITY:
        if normalized in set(registry.get(family, [])):
            return family
    return ""


def strongest_supported_signal_in_text(
    text: str,
    supported_terms: Sequence[str],
) -> Dict[str, str]:
    text_terms = prioritized_family_terms_from_text(text)
    if not text_terms:
        return {"term": "", "family": ""}

    supported_families = set(families_for_terms(supported_terms))

    for term in text_terms:
        family = family_for_term(term)
        if not family:
            continue
        if supported_families and family in supported_families:
            return {"term": term, "family": family}

    if supported_families:
        return {"term": "", "family": ""}

    first_term = text_terms[0]
    return {"term": first_term, "family": family_for_term(first_term)}


_SIGNAL_EQUIVALENT_TERMS: Dict[str, List[str]] = {
    "a/b test": ["a/b testing", "a/b experiment", "a/b experiments"],
    "a/b testing": ["a/b test", "a/b experiment", "a/b experiments"],
}


def equivalent_signal_terms(term: str) -> List[str]:
    normalized = normalize_signal_text(term)
    if not normalized:
        return []
    return list(_SIGNAL_EQUIVALENT_TERMS.get(normalized, []))

def _signal_tokens(value: str) -> List[str]:
    return [token for token in normalize_signal_text(value).split(" ") if token]


def _compact_signal_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_signal_text(value))


def _is_safe_surface_expansion_alias(alias: str, canonical: str) -> bool:
    alias_norm = normalize_signal_text(alias)
    canonical_norm = normalize_signal_text(canonical)

    if not alias_norm or not canonical_norm or alias_norm == canonical_norm:
        return False

    alias_tokens = _signal_tokens(alias_norm)
    canonical_tokens = _signal_tokens(canonical_norm)

    if len(alias_tokens) == 1 and len(canonical_tokens) > 1:
        return True

    return _compact_signal_text(alias_norm) == _compact_signal_text(canonical_norm)


def expandable_aliases_for_supported_term(term: str) -> List[str]:
    normalized = normalize_signal_text(term)
    if not normalized:
        return []

    aliases = [
        alias
        for alias, canonical in _SKILL_ALIASES.items()
        if normalize_signal_text(canonical) == normalized
    ]
    aliases.extend(equivalent_signal_terms(normalized))

    return [
        alias
        for alias in _unique_preserve_order(aliases)
        if _is_safe_surface_expansion_alias(alias, normalized)
    ]

def supported_signal_match_in_text(
    text: str,
    supported_terms: Sequence[str],
) -> Dict[str, str]:
    text_norm = normalize_signal_text(text)
    if not text_norm:
        return {"matched_term": "", "supported_term": "", "family": ""}

    supported = _unique_preserve_order(supported_terms)
    if not supported:
        return {"matched_term": "", "supported_term": "", "family": ""}

    for supported_term in supported:
        family = family_for_term(supported_term)
        if not family:
            continue

        supported_norm = normalize_signal_text(supported_term)
        candidate_variants = [supported_term] + equivalent_signal_terms(supported_term)

        for variant in candidate_variants:
            variant_norm = normalize_signal_text(variant)
            if not variant_norm:
                continue
            if variant_norm in text_norm:
                return {
                    "matched_term": variant,
                    "supported_term": supported_term,
                    "family": family,
                }

    return {"matched_term": "", "supported_term": "", "family": ""}