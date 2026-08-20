from typing import Any, Dict, List, Optional, Set

from src.rag.diagnostic_filter import filter_diagnostic_rag_rows
from src.rag.lexical_retriever import (
    _corpus_overview_results,
    _lexical_search,
    is_job_doc_allowed,
)
from src.rag.query_filters import _infer_metadata_filters, _merge_filters, _matches_filters
from src.rag.retrieval_ranker import (
    _dedupe_results,
    _get_retrieval_gate_metrics,
    _merge_hybrid_results,
    _top_score_summary,
)
from src.rag.retriever import retrieve_jobs
from src.utils.logging import get_logger

from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError

logger = get_logger("rag.query_engine")

SEMANTIC_RETRIEVAL_TIMEOUT_SECONDS = 10
SEMANTIC_RETRIEVAL_UNAVAILABLE_MARKERS = (
    "Legacy filesystem RAG index is disabled",
)

# Aggregate questions about the corpus as a whole. These never resemble an
# individual posting lexically, so term matching legitimately returns nothing.
# Bounded ceiling on how many postings such a question may see as evidence.
CORPUS_OVERVIEW_EVIDENCE_LIMIT = 12

CORPUS_OVERVIEW_QUERY_PHRASES = (
    "what kinds of roles",
    "what kind of roles",
    "what types of roles",
    "what type of roles",
    "what roles are available",
    "what jobs are available",
    "which companies are hiring",
    "what companies are hiring",
    "who is hiring",
    "which companies",
    "what companies",
    "what skills",
    "which skills",
    "what technologies",
    "which technologies",
    "what tech stack",
    "most common",
    "most often",
    "commonly required",
    "overview of the corpus",
    "summarize the corpus",
    "summarise the corpus",
)


def _is_corpus_overview_query(query: str) -> bool:
    """Deterministic detector for corpus-level aggregate questions."""
    normalized = " ".join(str(query or "").strip().lower().split())
    if not normalized:
        return False
    return any(phrase in normalized for phrase in CORPUS_OVERVIEW_QUERY_PHRASES)

def _build_preview(text: str, max_length: int = 400) -> str:
    text = (text or "").strip()
    if len(text) <= max_length:
        return text
    return text[:max_length].rstrip() + "..."


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
        "retrieval_lanes": result.get("retrieval_lanes", []),
    }

def _retrieve_jobs_with_timeout(query: str, top_k: int) -> List[Dict[str, Any]]:
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(retrieve_jobs, query, top_k)
    try:
        return future.result(timeout=SEMANTIC_RETRIEVAL_TIMEOUT_SECONDS)
    except FuturesTimeoutError as exc:
        future.cancel()
        raise TimeoutError(
            f"Semantic retrieval timed out after {SEMANTIC_RETRIEVAL_TIMEOUT_SECONDS} seconds"
        ) from exc
    finally:
        executor.shutdown(wait=False, cancel_futures=True)

def _is_semantic_retrieval_unavailable_error(exc: Exception) -> bool:
    message = str(exc)
    return any(marker in message for marker in SEMANTIC_RETRIEVAL_UNAVAILABLE_MARKERS)

def search_jobs(
    query: str,
    top_k: int = 5,
    fetch_k: int = 15,
    filters: Optional[Dict[str, Any]] = None,
    allowed_job_ids: Optional[Set[str]] = None,
    supplemental_docs: Optional[List[Dict[str, Any]]] = None,
) -> List[Dict[str, Any]]:
    # allowed_job_ids scopes retrieval to the authenticated owner's Dashboard
    # population BEFORE any evidence reaches the grounded answerer. None keeps
    # existing unscoped behavior for non-chatbot callers; an empty set is
    # fail-closed and must never widen back to the shared corpus.
    inferred_filters = _infer_metadata_filters(query)
    effective_filters = _merge_filters(filters, inferred_filters)

    logger.info(
        "RAG inferred filters | query=%r | inferred=%s | explicit=%s | effective=%s",
        query,
        inferred_filters,
        filters or {},
        effective_filters,
    )

    semantic_fallback_reason = ""
    try:
        semantic_raw_results = _retrieve_jobs_with_timeout(query=query, top_k=fetch_k)
    except TimeoutError:
        semantic_fallback_reason = "timeout"
        semantic_raw_results = []
        logger.warning(
            "RAG semantic retrieval timeout; falling back to lexical retrieval | "
            "query=%r | fetch_k=%s | effective_filters=%s",
            query,
            fetch_k,
            effective_filters,
        )
    except Exception as exc:
        if not _is_semantic_retrieval_unavailable_error(exc):
            logger.exception(
                "RAG semantic retrieval failed | query=%r | fetch_k=%s | effective_filters=%s",
                query,
                fetch_k,
                effective_filters,
            )
            raise

        semantic_fallback_reason = "unavailable"
        semantic_raw_results = []
        logger.warning(
            "RAG semantic retrieval unavailable; falling back to lexical retrieval | "
            "query=%r | fetch_k=%s | effective_filters=%s | error=%s",
            query,
            fetch_k,
            effective_filters,
            exc,
        )
    semantic_filtered_results = [
        result for result in semantic_raw_results
        if _matches_filters(result, effective_filters)
        and is_job_doc_allowed(
            (result.get("metadata", {}) or {}),
            allowed_job_ids,
        )
    ]

    semantic_deduped_results = filter_diagnostic_rag_rows(
        _dedupe_results(semantic_filtered_results)
    )

    lexical_results = filter_diagnostic_rag_rows(
        _lexical_search(
            query=query,
            top_k=fetch_k,
            filters=effective_filters,
            allowed_job_ids=allowed_job_ids,
            supplemental_docs=supplemental_docs,
        )
    )

    semantic_doc_ids = {
        ((result.get("metadata", {}) or {}).get("doc_id", ""))
        for result in semantic_deduped_results
        if ((result.get("metadata", {}) or {}).get("doc_id", ""))
    }

    lexical_doc_ids = {
        ((result.get("metadata", {}) or {}).get("doc_id", ""))
        for result in lexical_results
        if ((result.get("metadata", {}) or {}).get("doc_id", ""))
    }

    hybrid_results = _merge_hybrid_results(
        semantic_results=semantic_deduped_results,
        lexical_results=lexical_results,
    )

    gate_metrics = _get_retrieval_gate_metrics(
        query,
        hybrid_results,
        effective_filters,
    )

    logger.info(
        "RAG retrieval | query=%r | fetch_k=%s | semantic_raw=%s | semantic_filtered=%s | "
        "semantic_deduped=%s | lexical=%s | hybrid=%s | semantic_fallback_reason=%r | "
        "gate_pass=%s | max_overlap=%s | "
        "required_overlap=%s | top_scores=%s",
        query,
        fetch_k,
        len(semantic_raw_results),
        len(semantic_filtered_results),
        len(semantic_deduped_results),
        len(lexical_results),
        len(hybrid_results),
        semantic_fallback_reason,
        gate_metrics["passed"],
        gate_metrics["max_overlap"],
        gate_metrics["required_overlap"],
        _top_score_summary(hybrid_results),
    )

    # Corpus-level aggregate questions cannot match any single posting by term
    # overlap. When term matching finds nothing, fall back to a bounded, ordered
    # sample of real postings so the grounded answerer has genuine, citable
    # evidence. The gate is skipped for this path because the sample is a
    # deliberate corpus projection, not a claimed lexical match.
    effective_top_k = top_k
    if not hybrid_results and _is_corpus_overview_query(query):
        overview_results = _corpus_overview_results(
            top_k=CORPUS_OVERVIEW_EVIDENCE_LIMIT,
            allowed_job_ids=allowed_job_ids,
            supplemental_docs=supplemental_docs,
        )
        if overview_results:
            hybrid_results = _merge_hybrid_results(
                semantic_results=[],
                lexical_results=overview_results,
            )
            effective_top_k = max(top_k, min(CORPUS_OVERVIEW_EVIDENCE_LIMIT, len(hybrid_results)))
            gate_metrics = dict(gate_metrics)
            gate_metrics["passed"] = True
            logger.info(
                "RAG corpus overview evidence used | query=%r | sampled=%s | effective_top_k=%s",
                query,
                len(hybrid_results),
                effective_top_k,
            )

    if not gate_metrics["passed"]:
        if effective_filters and hybrid_results:
            logger.info(
                "RAG retrieval gate bypassed for metadata-filtered query | query=%r | "
                "effective_filters=%s | hybrid=%s | query_terms=%s",
                query,
                effective_filters,
                len(hybrid_results),
                gate_metrics["query_terms"],
            )
        else:
            logger.info(
                "RAG retrieval gate rejected results | query=%r | query_terms=%s",
                query,
                gate_metrics["query_terms"],
            )
            return []

    annotated_hybrid_results = []

    for result in hybrid_results:
        metadata = result.get("metadata", {}) or {}
        doc_id = metadata.get("doc_id", "")

        retrieval_lanes = []
        if doc_id in semantic_doc_ids:
            retrieval_lanes.append("semantic")
        if doc_id in lexical_doc_ids:
            retrieval_lanes.append("lexical")

        annotated_result = dict(result)
        annotated_result["retrieval_lanes"] = retrieval_lanes
        annotated_hybrid_results.append(annotated_result)

    formatted_results = [_format_result(result) for result in annotated_hybrid_results]
    final_results = formatted_results[:effective_top_k]

    logger.info(
        "RAG retrieval return | query=%r | returned=%s | dashboard_allowed_job_count=%s | "
        "doc_ids=%s",
        query,
        len(final_results),
        "unscoped" if allowed_job_ids is None else len(allowed_job_ids),
        [result.get("doc_id", "") for result in final_results],
    )

    return final_results
