import json
from typing import List, Dict, Any, Optional
import re

from src.rag.retriever import retrieve_jobs


def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _contains_text(haystack: Any, needle: Any) -> bool:
    return _normalize_text(needle) in _normalize_text(haystack)


def _list_contains(values: Any, needle: Any) -> bool:
    if not isinstance(values, list):
        return False

    needle_norm = _normalize_text(needle)
    return any(_normalize_text(v) == needle_norm for v in values)

QUERY_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "best", "by", "find",
    "for", "from", "in", "into", "is", "job", "jobs", "look", "looks",
    "of", "on", "or", "role", "roles", "that", "the", "their", "these",
    "this", "to", "using", "what", "which", "with", "work", "working",
    "strongest", "retrieved", "emphasize", "emphasizes", "focused",
}


def _score_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _dedupe_key(result: Dict[str, Any]) -> str:
    metadata = result.get("metadata", {}) or {}
    doc_id = str(metadata.get("doc_id") or "").strip()
    if doc_id:
        return doc_id

    job_url = str(metadata.get("job_url") or "").strip()
    if job_url:
        return job_url

    company = str(metadata.get("company") or "").strip()
    title = str(metadata.get("title") or "").strip()
    location = str(metadata.get("location") or "").strip()

    composite = "|".join([company, title, location]).strip("|")
    if composite:
        return composite

    text = str(result.get("text") or "").strip()
    return text[:200]


def _dedupe_results(results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    best_by_key: Dict[str, Dict[str, Any]] = {}
    ordered_keys: List[str] = []

    for result in results:
        key = _dedupe_key(result)
        existing = best_by_key.get(key)

        if existing is None:
            best_by_key[key] = result
            ordered_keys.append(key)
            continue

        if _score_value(result.get("score")) > _score_value(existing.get("score")):
            best_by_key[key] = result

    deduped = [best_by_key[key] for key in ordered_keys]
    deduped.sort(key=lambda item: _score_value(item.get("score")), reverse=True)
    return deduped


def _extract_query_terms(query: str) -> List[str]:
    terms = re.findall(r"[a-z0-9\+\#\-]+", _normalize_text(query))
    unique_terms: List[str] = []

    for term in terms:
        term = term.strip("-")
        if len(term) < 3:
            continue
        if term in QUERY_STOPWORDS:
            continue
        if term not in unique_terms:
            unique_terms.append(term)

    return unique_terms


def _searchable_text(result: Dict[str, Any]) -> str:
    metadata = result.get("metadata", {}) or {}

    parts = [
        metadata.get("company", ""),
        metadata.get("title", ""),
        metadata.get("location", ""),
        metadata.get("source", ""),
        metadata.get("role_family", ""),
        metadata.get("seniority", ""),
        metadata.get("visa_sponsorship", ""),
        " ".join(metadata.get("required_skills", []) or []),
        " ".join(metadata.get("preferred_skills", []) or []),
        " ".join(metadata.get("all_skills", []) or []),
        result.get("text", ""),
    ]

    return _normalize_text(" ".join(str(part or "") for part in parts))


def _query_overlap_count(query_terms: List[str], result: Dict[str, Any]) -> int:
    if not query_terms:
        return 0

    searchable = _searchable_text(result)
    return sum(1 for term in query_terms if term in searchable)


def _passes_retrieval_gate(query: str, results: List[Dict[str, Any]]) -> bool:
    if not results:
        return False

    query_terms = _extract_query_terms(query)
    if not query_terms:
        return True

    required_overlap = 1 if len(query_terms) <= 2 else 2
    max_overlap = max(_query_overlap_count(query_terms, result) for result in results)

    return max_overlap >= required_overlap


def _matches_filters(result: Dict[str, Any], filters: Optional[Dict[str, Any]]) -> bool:
    if not filters:
        return True

    metadata = result.get("metadata", {}) or {}

    company = filters.get("company")
    source = filters.get("source")
    location = filters.get("location")
    title_contains = filters.get("title_contains")
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


def _build_preview(text: str, max_chars: int = 400) -> str:
    text = (text or "").strip().replace("\n", " ")
    if len(text) <= max_chars:
        return text
    return text[:max_chars].rstrip() + "..."


def _format_result(result: Dict[str, Any]) -> Dict[str, Any]:
    metadata = result.get("metadata", {}) or {}
    text = result.get("text", "") or ""

    return {
        "score": result.get("score"),
        "doc_id": metadata.get("doc_id", ""),
        "company": metadata.get("company", ""),
        "title": metadata.get("title", ""),
        "location": metadata.get("location", ""),
        "source": metadata.get("source", ""),
        "job_url": metadata.get("job_url", ""),
        "posted_at": metadata.get("posted_at", ""),
        "role_family": metadata.get("role_family", ""),
        "seniority": metadata.get("seniority", ""),
        "required_skills": metadata.get("required_skills", []),
        "preferred_skills": metadata.get("preferred_skills", []),
        "all_skills": metadata.get("all_skills", []),
        "visa_sponsorship": metadata.get("visa_sponsorship", ""),
        "ai_fit_score": metadata.get("ai_fit_score"),
        "preview": _build_preview(text),
        "retrieval_text": text,
    }


def search_jobs(
    query: str,
    top_k: int = 5,
    fetch_k: int = 15,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    """
    Semantic search over the local job corpus with optional post-retrieval filters.

    top_k:
        Final number of results returned.

    fetch_k:
        Number of semantic candidates to retrieve before filtering.
        Keep this > top_k when using filters.
    """

    raw_results = retrieve_jobs(query=query, top_k=fetch_k)

    filtered_results = [
        result for result in raw_results
        if _matches_filters(result, filters)
    ]

    deduped_results = _dedupe_results(filtered_results)

    if not _passes_retrieval_gate(query, deduped_results):
        return []

    formatted_results = [_format_result(result) for result in deduped_results]
    return formatted_results[:top_k]


if __name__ == "__main__":
    query = "experimentation-heavy data science roles using looker and causal inference"

    results = search_jobs(
        query=query,
        top_k=5,
        fetch_k=15,
        filters={
            "source": "greenhouse",
        },
    )

    print(json.dumps(results, indent=2, ensure_ascii=False))