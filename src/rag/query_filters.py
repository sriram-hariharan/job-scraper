import re
from typing import Any, Dict, List, Optional

from src.rag.corpus_store import _build_metadata_catalog


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _contains_text(haystack: Any, needle: Any) -> bool:
    return _normalize_text(needle) in _normalize_text(haystack)


def _list_contains(values: Any, needle: Any) -> bool:
    if not isinstance(values, list):
        return False

    needle_norm = _normalize_text(needle)
    return any(_normalize_text(v) == needle_norm for v in values)


def _tokenize_for_match(value: Any) -> List[str]:
    return re.findall(r"[a-z0-9]+", _normalize_text(value))


def _contains_token_sequence(query_tokens: List[str], candidate_tokens: List[str]) -> bool:
    if not query_tokens or not candidate_tokens:
        return False

    candidate_len = len(candidate_tokens)
    query_len = len(query_tokens)

    if candidate_len > query_len:
        return False

    for i in range(query_len - candidate_len + 1):
        if query_tokens[i:i + candidate_len] == candidate_tokens:
            return True

    return False


def _match_known_value(query_norm: str, candidates: Dict[str, str]) -> Optional[str]:
    query_tokens = _tokenize_for_match(query_norm)
    matches = []

    for candidate_norm, candidate_value in candidates.items():
        candidate_tokens = _tokenize_for_match(candidate_norm)
        if not candidate_tokens:
            continue

        if _contains_token_sequence(query_tokens, candidate_tokens):
            matches.append((len(candidate_tokens), len(candidate_norm), candidate_value))

    if not matches:
        return None

    matches.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return matches[0][2]


def _infer_seniority_from_query(query_norm: str, catalog: Dict[str, Any]) -> Optional[str]:
    seniority_keywords = [
        "principal",
        "staff",
        "senior",
        "lead",
        "junior",
        "intern",
    ]

    for keyword in seniority_keywords:
        if keyword in query_norm:
            return keyword

    return _match_known_value(query_norm, catalog["seniorities"])


def _infer_visa_sponsorship_from_query(query_norm: str) -> Optional[str]:
    visa_terms = [
        "visa sponsorship",
        "sponsorship",
        "sponsor",
        "h1b",
        "h-1b",
        "opt",
        "stem opt",
    ]

    if any(term in query_norm for term in visa_terms):
        return "possible"

    return None


def _infer_metadata_filters(query: str) -> Dict[str, Any]:
    query_norm = _normalize_text(query)
    catalog = _build_metadata_catalog()

    inferred: Dict[str, Any] = {}

    company = _match_known_value(query_norm, catalog["companies"])
    if company:
        inferred["company"] = company

    source = _match_known_value(query_norm, catalog["sources"])
    if source:
        inferred["source"] = source

    location = _match_known_value(query_norm, catalog["locations"])
    if location:
        inferred["location"] = location

    title_contains = _match_known_value(query_norm, catalog["titles"])
    if title_contains:
        inferred["title_contains"] = title_contains

    role_family = _match_known_value(query_norm, catalog["role_families"])
    if role_family:
        inferred["role_family"] = role_family

    seniority = _infer_seniority_from_query(query_norm, catalog)
    if seniority:
        inferred["seniority"] = seniority

    visa_sponsorship = _infer_visa_sponsorship_from_query(query_norm)
    if visa_sponsorship:
        inferred["visa_sponsorship"] = visa_sponsorship

    return inferred


def _merge_filters(
    explicit_filters: Optional[Dict[str, Any]],
    inferred_filters: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}

    if inferred_filters:
        merged.update({k: v for k, v in inferred_filters.items() if v not in (None, "", [])})

    if explicit_filters:
        merged.update({k: v for k, v in explicit_filters.items() if v not in (None, "", [])})

    return merged


def _matches_filters(result: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
    if not filters:
        return True

    metadata = result.get("metadata", {}) or {}

    company = filters.get("company")
    source = filters.get("source")
    location = filters.get("location")
    title_contains = filters.get("title_contains")
    role_family = filters.get("role_family")
    seniority = filters.get("seniority")
    required_skill = filters.get("required_skill")
    any_skill = filters.get("any_skill")
    visa_sponsorship = filters.get("visa_sponsorship")
    min_ai_fit_score = filters.get("min_ai_fit_score")

    if company and not _contains_text(metadata.get("company"), company):
        return False

    if source and not _contains_text(metadata.get("source"), source):
        return False

    if location and not _contains_text(metadata.get("location"), location):
        return False

    if title_contains and not _contains_text(metadata.get("title"), title_contains):
        return False

    if role_family and not _contains_text(metadata.get("role_family"), role_family):
        return False

    if seniority and not (
        _contains_text(metadata.get("seniority"), seniority)
        or _contains_text(metadata.get("title"), seniority)
    ):
        return False

    if required_skill and not _list_contains(metadata.get("required_skills", []), required_skill):
        return False

    if any_skill and not _list_contains(metadata.get("all_skills", []), any_skill):
        return False

    if visa_sponsorship and not _contains_text(metadata.get("visa_sponsorship"), visa_sponsorship):
        return False

    if min_ai_fit_score is not None:
        score = metadata.get("ai_fit_score")
        if score is None or score < min_ai_fit_score:
            return False

    return True