from __future__ import annotations

import re
from typing import Iterable, List

from src.config.consts import TAILORING_FACET_PATTERNS


_NORMALIZE_RE = re.compile(r"[^a-z0-9+/]+")


def _norm(value: str) -> str:
    return " ".join(_NORMALIZE_RE.sub(" ", str(value or "").lower()).split())


def _contains_phrase(haystack: str, needle: str) -> bool:
    hay = f" {_norm(haystack)} "
    ned = f" {_norm(needle)} "
    return bool(needle) and ned in hay


def _unique_preserve_order(items: Iterable[str]) -> List[str]:
    seen = set()
    ordered: List[str] = []
    for item in items:
        text = str(item or "").strip()
        if not text:
            continue
        key = text.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(text)
    return ordered


_FAMILY_TO_TERMS = {
    family: _unique_preserve_order(_norm(term) for term in terms or [])
    for family, terms in TAILORING_FACET_PATTERNS.items()
}

_TERM_TO_FAMILIES = {}
for family, terms in _FAMILY_TO_TERMS.items():
    for term in terms:
        _TERM_TO_FAMILIES.setdefault(term, []).append(family)


def supported_term_hits(text: str, supported_terms: Iterable[str]) -> List[str]:
    hits: List[str] = []
    for term in supported_terms or []:
        raw = str(term or "").strip()
        if not raw:
            continue
        if _contains_phrase(text, raw):
            hits.append(raw)
    return _unique_preserve_order(hits)


def supported_family_hits(text: str, supported_terms: Iterable[str]) -> List[str]:
    unit_families: List[str] = []

    for term in supported_terms or []:
        normalized = _norm(term)
        if not normalized:
            continue
        unit_families.extend(_TERM_TO_FAMILIES.get(normalized, []))

    hits: List[str] = []
    for family in _unique_preserve_order(unit_families):
        family_label = family.replace("_", " ")
        aliases = _FAMILY_TO_TERMS.get(family, [])

        if _contains_phrase(text, family_label) or any(_contains_phrase(text, alias) for alias in aliases):
            hits.append(family_label)

    return _unique_preserve_order(hits)


def canonical_guardrail_targets(
    terms: Iterable[str],
    facets: Iterable[str],
    limit: int = 4,
) -> List[str]:
    raw_terms = _unique_preserve_order(str(item or "").strip() for item in terms or [])
    raw_facets = _unique_preserve_order(str(item or "").strip() for item in facets or [])

    family_labels: List[str] = []
    unmatched_terms: List[str] = []

    for item in raw_terms:
        normalized = _norm(item)
        matched_families = _TERM_TO_FAMILIES.get(normalized, [])
        if matched_families:
            family_labels.extend(family.replace("_", " ") for family in matched_families)
        else:
            unmatched_terms.append(item)

    explicit_facet_labels = [facet.replace("_", " ") for facet in raw_facets]
    ordered = _unique_preserve_order(family_labels + unmatched_terms + explicit_facet_labels)
    return ordered[:limit]

def guardrail_coverage_targets(
    terms: Iterable[str],
    facets: Iterable[str],
    limit: int = 12,
) -> List[str]:
    raw_terms = _unique_preserve_order(str(item or "").strip() for item in terms or [])
    raw_facets = _unique_preserve_order(str(item or "").strip() for item in facets or [])

    family_labels: List[str] = []
    for item in raw_terms:
        normalized = _norm(item)
        matched_families = _TERM_TO_FAMILIES.get(normalized, [])
        family_labels.extend(family.replace("_", " ") for family in matched_families)

    explicit_facet_labels = [facet.replace("_", " ") for facet in raw_facets]

    # Coverage matching should be permissive:
    # exact unsupported terms OR same-family labels should satisfy the gate.
    ordered = _unique_preserve_order(raw_terms + family_labels + explicit_facet_labels)
    return ordered[:limit]