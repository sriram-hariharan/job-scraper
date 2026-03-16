import json
import re
from typing import List, Dict, Any, Optional
from functools import lru_cache
from pathlib import Path

from src.rag.retriever import retrieve_jobs
from src.utils.logging import get_logger

logger = get_logger("rag.query_engine")

CORPUS_PATH = Path("data/rag/job_corpus.jsonl")

HYBRID_SEMANTIC_WEIGHT = 0.65
HYBRID_LEXICAL_WEIGHT = 0.35

QUERY_STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "best", "by", "find",
    "for", "from", "in", "into", "is", "job", "jobs", "look", "looks",
    "of", "on", "or", "role", "roles", "that", "the", "their", "these",
    "this", "to", "using", "what", "which", "with", "work", "working",
    "strongest", "retrieved", "emphasize", "emphasizes", "focused",
    "about", "requirement", "requirements",
}

def _normalize_text(value: Any) -> str:
    return str(value or "").strip().lower()


def _contains_text(haystack: Any, needle: Any) -> bool:
    return _normalize_text(needle) in _normalize_text(haystack)


def _list_contains(values: Any, needle: Any) -> bool:
    if not isinstance(values, list):
        return False

    needle_norm = _normalize_text(needle)
    return any(_normalize_text(v) == needle_norm for v in values)

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

@lru_cache(maxsize=1)
def _load_job_corpus() -> List[Dict[str, Any]]:
    if not CORPUS_PATH.exists():
        logger.warning("RAG lexical corpus missing | path=%s", CORPUS_PATH)
        return []

    docs: List[Dict[str, Any]] = []

    with CORPUS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            docs.append(json.loads(line))

    logger.info("RAG lexical corpus loaded | path=%s | docs=%s", CORPUS_PATH, len(docs))
    return docs

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
    terms = re.findall(r"[a-z0-9\+\#\/\.\-]+", _normalize_text(query))
    unique_terms: List[str] = []

    for term in terms:
        term = term.strip("-./")
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

def _get_retrieval_gate_metrics(query: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
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

    required_overlap = 1 if len(query_terms) <= 2 else 2
    max_overlap = max(_query_overlap_count(query_terms, result) for result in results)

    return {
        "query_terms": query_terms,
        "required_overlap": required_overlap,
        "max_overlap": max_overlap,
        "passed": max_overlap >= required_overlap,
    }

def _build_query_phrases(query_terms: List[str]) -> List[str]:
    phrases: List[str] = []

    for i in range(len(query_terms) - 1):
        phrase = f"{query_terms[i]} {query_terms[i + 1]}".strip()
        if phrase and phrase not in phrases:
            phrases.append(phrase)

    return phrases


def _skill_text(job_doc: Dict[str, Any]) -> str:
    return " | ".join(_normalize_text(skill) for skill in (job_doc.get("all_skills") or []))


def _lexical_match_score(query: str, job_doc: Dict[str, Any]) -> float:
    query_norm = _normalize_text(query)
    query_terms = _extract_query_terms(query)
    query_phrases = _build_query_phrases(query_terms)

    title = _normalize_text(job_doc.get("title", ""))
    company = _normalize_text(job_doc.get("company", ""))
    location = _normalize_text(job_doc.get("location", ""))
    role_family = _normalize_text(job_doc.get("role_family", ""))
    seniority = _normalize_text(job_doc.get("seniority", ""))
    skills_text = _skill_text(job_doc)
    searchable = _normalize_text(job_doc.get("retrieval_text", ""))

    score = 0.0

    if query_norm and query_norm in searchable:
        score += 6.0

    for phrase in query_phrases:
        if phrase in title:
            score += 4.0
        elif phrase in skills_text:
            score += 3.0
        elif phrase in searchable:
            score += 2.0

    for term in query_terms:
        if term in title:
            score += 2.5
        elif term in role_family or term in seniority:
            score += 1.5

        if any(term == _normalize_text(skill) or term in _normalize_text(skill) for skill in (job_doc.get("all_skills") or [])):
            score += 2.0
        elif term in company or term in location:
            score += 1.0
        elif term in searchable:
            score += 0.75

    return score


def _build_lexical_result(job_doc: Dict[str, Any], normalized_score: float) -> Dict[str, Any]:
    metadata = {
        "doc_id": job_doc.get("doc_id", ""),
        "company": job_doc.get("company", ""),
        "title": job_doc.get("title", ""),
        "location": job_doc.get("location", ""),
        "source": job_doc.get("source", ""),
        "job_url": job_doc.get("job_url", ""),
        "posted_at": job_doc.get("posted_at", ""),
        "role_family": job_doc.get("role_family", ""),
        "seniority": job_doc.get("seniority", ""),
        "required_skills": job_doc.get("required_skills", []),
        "preferred_skills": job_doc.get("preferred_skills", []),
        "all_skills": job_doc.get("all_skills", []),
        "visa_sponsorship": job_doc.get("visa_sponsorship", ""),
        "ai_fit_score": job_doc.get("ai_fit_score"),
    }

    return {
        "score": normalized_score,
        "text": job_doc.get("retrieval_text", "") or "",
        "metadata": metadata,
    }


def _lexical_search(
    query: str,
    top_k: int,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    docs = _load_job_corpus()
    scored: List[Any] = []

    for job_doc in docs:
        candidate = {
            "score": 0.0,
            "text": job_doc.get("retrieval_text", "") or "",
            "metadata": job_doc,
        }

        if not _matches_filters(candidate, filters):
            continue

        raw_score = _lexical_match_score(query, job_doc)
        if raw_score <= 0:
            continue

        scored.append((raw_score, job_doc))

    scored.sort(key=lambda item: item[0], reverse=True)

    if not scored:
        return []

    top_scored = scored[:top_k]
    max_score = top_scored[0][0]

    results: List[Dict[str, Any]] = []

    for raw_score, job_doc in top_scored:
        normalized_score = raw_score / max_score if max_score > 0 else 0.0
        results.append(_build_lexical_result(job_doc, normalized_score))

    return results


def _merge_hybrid_results(
    semantic_results: List[Dict[str, Any]],
    lexical_results: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    merged: Dict[str, Dict[str, Any]] = {}
    ordered_keys: List[str] = []

    def _upsert(result: Dict[str, Any], semantic_score: float = 0.0, lexical_score: float = 0.0) -> None:
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

def _passes_retrieval_gate(query: str, results: List[Dict[str, Any]]) -> bool:
    return _get_retrieval_gate_metrics(query, results)["passed"]


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

    semantic_raw_results = retrieve_jobs(query=query, top_k=fetch_k)

    semantic_filtered_results = [
        result for result in semantic_raw_results
        if _matches_filters(result, filters)
    ]

    semantic_deduped_results = _dedupe_results(semantic_filtered_results)
    lexical_results = _lexical_search(query=query, top_k=fetch_k, filters=filters)

    hybrid_results = _merge_hybrid_results(
        semantic_results=semantic_deduped_results,
        lexical_results=lexical_results,
    )

    gate_metrics = _get_retrieval_gate_metrics(query, hybrid_results)

    logger.info(
        "RAG retrieval | query=%r | fetch_k=%s | semantic_raw=%s | semantic_filtered=%s | "
        "semantic_deduped=%s | lexical=%s | hybrid=%s | gate_pass=%s | max_overlap=%s | "
        "required_overlap=%s | top_scores=%s",
        query,
        fetch_k,
        len(semantic_raw_results),
        len(semantic_filtered_results),
        len(semantic_deduped_results),
        len(lexical_results),
        len(hybrid_results),
        gate_metrics["passed"],
        gate_metrics["max_overlap"],
        gate_metrics["required_overlap"],
        _top_score_summary(hybrid_results),
    )

    if not gate_metrics["passed"]:
        logger.info(
            "RAG retrieval gate rejected results | query=%r | query_terms=%s",
            query,
            gate_metrics["query_terms"],
        )
        return []

    formatted_results = [_format_result(result) for result in hybrid_results]
    final_results = formatted_results[:top_k]

    logger.info(
        "RAG retrieval return | query=%r | returned=%s | doc_ids=%s",
        query,
        len(final_results),
        [result.get("doc_id", "") for result in final_results],
    )

    return final_results


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