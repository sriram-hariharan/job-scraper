from typing import Dict, List, Sequence
import re

from src.config.consts import (
    ANALYTICS_ML_SIGNAL_PATTERNS,
    DOMAIN_SIGNAL_PATTERNS,
    EXPERIMENTATION_SIGNAL_PATTERNS,
    TOOLING_SIGNAL_PATTERNS,
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