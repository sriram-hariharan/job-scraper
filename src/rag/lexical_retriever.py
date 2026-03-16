import re
from typing import Any, Dict, List, Optional

from src.config.consts import QUERY_STOPWORDS
from src.rag.corpus_store import _load_job_corpus
from src.rag.query_filters import _matches_filters, _normalize_text


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


def _build_query_phrases(query_terms: List[str]) -> List[str]:
    phrases: List[str] = []

    for i in range(len(query_terms) - 1):
        phrase = f"{query_terms[i]} {query_terms[i + 1]}".strip()
        if phrase and phrase not in phrases:
            phrases.append(phrase)

    return phrases


def _skill_text(job_doc: Dict[str, Any]) -> str:
    return " | ".join(_normalize_text(skill) for skill in (job_doc.get("all_skills") or []))


def _metadata_text(job_doc: Dict[str, Any]) -> str:
    return " | ".join(
        _normalize_text(value)
        for value in [
            job_doc.get("company", ""),
            job_doc.get("title", ""),
            job_doc.get("location", ""),
            job_doc.get("source", ""),
            job_doc.get("role_family", ""),
            job_doc.get("seniority", ""),
            job_doc.get("visa_sponsorship", ""),
        ]
    )


def _has_strong_lexical_signal(query: str, job_doc: Dict[str, Any]) -> bool:
    query_norm = _normalize_text(query)
    query_terms = _extract_query_terms(query)
    query_phrases = _build_query_phrases(query_terms)

    if not query_terms:
        return False

    title = _normalize_text(job_doc.get("title", ""))
    skills_text = _skill_text(job_doc)
    metadata_text = _metadata_text(job_doc)
    searchable = _normalize_text(job_doc.get("retrieval_text", ""))

    if query_norm and query_norm in searchable:
        return True

    if any(phrase in title or phrase in skills_text for phrase in query_phrases):
        return True

    title_skill_hits = sum(
        1 for term in query_terms
        if term in title or term in skills_text
    )

    metadata_hits = sum(
        1 for term in query_terms
        if term in metadata_text
    )

    return title_skill_hits >= 1 or metadata_hits >= 2


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

        if not _has_strong_lexical_signal(query, job_doc):
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