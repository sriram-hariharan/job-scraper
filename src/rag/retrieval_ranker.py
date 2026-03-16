from typing import Any, Dict, List, Optional

from src.rag.lexical_retriever import _extract_query_terms
from src.rag.query_filters import _normalize_text

HYBRID_SEMANTIC_WEIGHT = 0.65
HYBRID_LEXICAL_WEIGHT = 0.35


def _score_value(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _top_score_summary(results: List[Dict[str, Any]], limit: int = 5) -> List[float]:
    return [
        round(_score_value(result.get("score")), 4)
        for result in results[:limit]
    ]


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


def _required_overlap_count(
    query_terms: List[str],
    effective_filters: Optional[Dict[str, Any]] = None,
) -> int:
    if not query_terms:
        return 0

    if len(query_terms) <= 2:
        return 1

    has_filters = bool(effective_filters)

    if len(query_terms) >= 5 and not has_filters:
        return 3

    return 2


def _get_retrieval_gate_metrics(
    query: str,
    results: List[Dict[str, Any]],
    effective_filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not results:
        return {
            "query_terms": [],
            "required_overlap": 0,
            "max_overlap": 0,
            "passed": False,
        }

    query_terms = _extract_query_terms(query)
    if not query_terms:
        return {
            "query_terms": [],
            "required_overlap": 0,
            "max_overlap": 0,
            "passed": True,
        }

    required_overlap = _required_overlap_count(query_terms, effective_filters)
    max_overlap = max(_query_overlap_count(query_terms, result) for result in results)

    return {
        "query_terms": query_terms,
        "required_overlap": required_overlap,
        "max_overlap": max_overlap,
        "passed": max_overlap >= required_overlap,
    }


def _passes_retrieval_gate(
    query: str,
    results: List[Dict[str, Any]],
    effective_filters: Optional[Dict[str, Any]] = None,
) -> bool:
    return _get_retrieval_gate_metrics(query, results, effective_filters)["passed"]


def _merge_hybrid_results(
    semantic_results: List[Dict[str, Any]],
    lexical_results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    ordered_keys: List[str] = []

    def _upsert(
        result: Dict[str, Any],
        semantic_score: float = 0.0,
        lexical_score: float = 0.0,
    ) -> None:
        key = _dedupe_key(result)
        existing = merged.get(key)

        if existing is None:
            existing = {
                "score": 0.0,
                "text": result.get("text", "") or "",
                "metadata": result.get("metadata", {}) or {},
                "_semantic_score": 0.0,
                "_lexical_score": 0.0,
            }
            merged[key] = existing
            ordered_keys.append(key)

        if semantic_score > 0 and result.get("text"):
            existing["text"] = result.get("text", "") or ""
        elif not existing.get("text") and result.get("text"):
            existing["text"] = result.get("text", "") or ""

        if result.get("metadata"):
            existing["metadata"] = result.get("metadata", {}) or existing["metadata"]

        existing["_semantic_score"] = max(existing["_semantic_score"], semantic_score)
        existing["_lexical_score"] = max(existing["_lexical_score"], lexical_score)

    for result in semantic_results:
        _upsert(result, semantic_score=_score_value(result.get("score")))

    for result in lexical_results:
        _upsert(result, lexical_score=_score_value(result.get("score")))

    hybrid_results: List[Dict[str, Any]] = []

    for key in ordered_keys:
        item = merged[key]
        item["score"] = (
            HYBRID_SEMANTIC_WEIGHT * item["_semantic_score"] +
            HYBRID_LEXICAL_WEIGHT * item["_lexical_score"]
        )
        hybrid_results.append(item)

    hybrid_results.sort(key=lambda item: _score_value(item.get("score")), reverse=True)
    return hybrid_results