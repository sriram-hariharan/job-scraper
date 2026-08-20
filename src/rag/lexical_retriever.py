import re
from typing import Any, Dict, List, Optional, Set

from src.config.consts import QUERY_STOPWORDS
from src.rag.corpus_store import _load_job_corpus
from src.rag.query_filters import _matches_filters, _normalize_text

_LEXICAL_SHORT_TERMS = {"ai", "ml"}


def expand_query_terms(query: str) -> str:
    normalized = _normalize_text(query)
    tokens = re.findall(r"[a-z0-9]+", normalized)
    token_set = set(tokens)
    expansions: List[str] = []

    def add(values: List[str]) -> None:
        for value in values:
            if value not in expansions:
                expansions.append(value)

    if "ai" in token_set:
        add(["artificial intelligence", "machine learning", "ai"])

    if "llm" in token_set:
        add(["large language model", "generative ai", "llm"])

    if "ml" in token_set:
        add(["machine learning", "ml"])

    if not expansions:
        return query

    return " ".join([str(query or "").strip(), *expansions]).strip()


def _extract_query_terms(query: str) -> List[str]:
    terms = re.findall(r"[a-z0-9\+\#\/\.\-]+", _normalize_text(expand_query_terms(query)))
    unique_terms: List[str] = []

    for term in terms:
        term = term.strip("-./")
        if "/" in term:
            split_terms = [part for part in term.split("/") if part]
        else:
            split_terms = [term]

        for split_term in split_terms:
            if len(split_term) < 3 and split_term not in _LEXICAL_SHORT_TERMS:
                continue
            if split_term in QUERY_STOPWORDS:
                continue
            if split_term not in unique_terms:
                unique_terms.append(split_term)

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

def _metadata_only_fallback_results(
    docs: List[Dict[str, Any]],
    top_k: int,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    matched_docs: List[Dict[str, Any]] = []

    for job_doc in docs:
        candidate = {
            "score": 0.0,
            "text": job_doc.get("retrieval_text", "") or "",
            "metadata": job_doc,
        }

        if not _matches_filters(candidate, filters):
            continue

        matched_docs.append(job_doc)

    if not matched_docs:
        return []

    matched_docs.sort(
        key=lambda doc: str(doc.get("posted_at", "") or ""),
        reverse=True,
    )

    results: List[Dict[str, Any]] = []
    for job_doc in matched_docs[:top_k]:
        results.append(_build_lexical_result(job_doc, 1.0))

    return results

def job_doc_identity_values(job_doc: Dict[str, Any]) -> List[str]:
    """Canonical identity values for a corpus document (doc_id / job_url)."""
    values: List[str] = []
    for key in ("doc_id", "job_url", "url", "link"):
        value = str(job_doc.get(key) or "").strip()
        if value and value not in values:
            values.append(value)
    return values


def is_job_doc_allowed(
    job_doc: Dict[str, Any],
    allowed_job_ids: Optional[Set[str]] = None,
) -> bool:
    """Owner-scope membership test.

    None means unscoped (non-chatbot callers keep existing behavior). An empty
    set is fail-closed: nothing is allowed, and retrieval must not widen back
    to the shared corpus.
    """
    if allowed_job_ids is None:
        return True
    if not allowed_job_ids:
        return False
    return any(value in allowed_job_ids for value in job_doc_identity_values(job_doc))


def _allowed_corpus_docs(
    docs: List[Dict[str, Any]],
    allowed_job_ids: Optional[Set[str]] = None,
    supplemental_docs: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Scoped retrieval population.

    Shared-corpus documents are filtered to the allowed scope, then any
    supplemental owner-artifact documents for allowed jobs that the shared
    corpus does not carry are appended. Deduplicated by canonical identity, so
    a job present in shared RAG always uses its shared document.
    """
    if allowed_job_ids is None:
        scoped = list(docs)
    else:
        scoped = [doc for doc in docs if is_job_doc_allowed(doc, allowed_job_ids)]

    if not supplemental_docs:
        return scoped

    seen: Set[str] = set()
    for doc in scoped:
        seen.update(job_doc_identity_values(doc))

    for doc in supplemental_docs:
        if allowed_job_ids is not None and not is_job_doc_allowed(doc, allowed_job_ids):
            continue
        identities = job_doc_identity_values(doc)
        if not identities or (set(identities) & seen):
            continue
        seen.update(identities)
        scoped.append(doc)

    return scoped


def _corpus_overview_results(
    top_k: int,
    allowed_job_ids: Optional[Set[str]] = None,
    supplemental_docs: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    """Bounded, deterministic corpus sample for aggregate/overview questions.

    Aggregate questions ("which companies are hiring?") do not lexically
    resemble any single posting, so term matching returns nothing. This returns
    the most recent postings as genuine evidence: real documents that the
    grounded answerer must still cite, so nothing is fabricated. It is only
    reached from the overview path in query_engine.search_jobs.
    """
    docs = _allowed_corpus_docs(_load_job_corpus(), allowed_job_ids, supplemental_docs)
    if not docs:
        return []

    ordered = sorted(
        docs,
        key=lambda d: (str(d.get("posted_at", "") or ""), str(d.get("doc_id", "") or "")),
        reverse=True,
    )

    return [_build_lexical_result(job_doc, 1.0) for job_doc in ordered[:max(0, int(top_k))]]


def _lexical_search(
    query: str,
    top_k: int,
    filters: Optional[Dict[str, Any]] = None,
    allowed_job_ids: Optional[Set[str]] = None,
    supplemental_docs: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    docs = _allowed_corpus_docs(_load_job_corpus(), allowed_job_ids, supplemental_docs)
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
        if filters:
            return _metadata_only_fallback_results(docs, top_k=top_k, filters=filters)
        return []

    top_scored = scored[:top_k]
    max_score = top_scored[0][0]

    results: List[Dict[str, Any]] = []

    for raw_score, job_doc in top_scored:
        normalized_score = raw_score / max_score if max_score > 0 else 0.0
        results.append(_build_lexical_result(job_doc, normalized_score))

    return results
