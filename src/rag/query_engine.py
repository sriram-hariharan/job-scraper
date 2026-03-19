from typing import Any, Dict, List, Optional

from src.rag.lexical_retriever import _lexical_search
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

def search_jobs(
    query: str,
    top_k: int = 5,
    fetch_k: int = 15,
    filters: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    inferred_filters = _infer_metadata_filters(query)
    effective_filters = _merge_filters(filters, inferred_filters)

    logger.info(
        "RAG inferred filters | query=%r | inferred=%s | explicit=%s | effective=%s",
        query,
        inferred_filters,
        filters or {},
        effective_filters,
    )

    try:
        semantic_raw_results = _retrieve_jobs_with_timeout(query=query, top_k=fetch_k)
    except TimeoutError:
        logger.warning(
            "RAG semantic retrieval timeout | query=%r | fetch_k=%s | effective_filters=%s",
            query,
            fetch_k,
            effective_filters,
        )
        raise
    except Exception:
        logger.exception(
            "RAG semantic retrieval failed | query=%r | fetch_k=%s | effective_filters=%s",
            query,
            fetch_k,
            effective_filters,
        )
        raise

    semantic_filtered_results = [
        result for result in semantic_raw_results
        if _matches_filters(result, effective_filters)
    ]

    semantic_deduped_results = _dedupe_results(semantic_filtered_results)

    lexical_results = _lexical_search(
        query=query,
        top_k=fetch_k,
        filters=effective_filters,
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
    final_results = formatted_results[:top_k]

    logger.info(
        "RAG retrieval return | query=%r | returned=%s | doc_ids=%s",
        query,
        len(final_results),
        [result.get("doc_id", "") for result in final_results],
    )

    return final_results