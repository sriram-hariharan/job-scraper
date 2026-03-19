from typing import Any, Callable, Dict, List, Optional

from src.rag.query_engine import search_jobs
from src.rag.rag_answerer import answer_job_query


ALLOWED_OUTPUT_MODES = {"full", "compact"}


def _error_payload(
    tool_name: str,
    error: str,
    error_type: str = "validation_error",
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "tool_name": tool_name,
        "ok": False,
        "error": error,
        "error_type": error_type,
    }

    if details:
        payload["details"] = details

    return payload


def _validate_non_empty_string(value: Any, field_name: str) -> Optional[str]:
    if not isinstance(value, str):
        return f"{field_name} must be a string"

    normalized = value.strip()
    if not normalized:
        return f"{field_name} must not be empty"

    return None


def _validate_positive_int(value: Any, field_name: str) -> Optional[str]:
    if not isinstance(value, int):
        return f"{field_name} must be an integer"

    if value <= 0:
        return f"{field_name} must be > 0"

    return None


def _validate_filters(filters: Any) -> Optional[str]:
    if filters is None:
        return None

    if not isinstance(filters, dict):
        return "filters must be a dictionary"

    return None


def _validate_output_mode(output_mode: Any) -> Optional[str]:
    if not isinstance(output_mode, str):
        return "output_mode must be a string"

    if output_mode not in ALLOWED_OUTPUT_MODES:
        return f"output_mode must be one of {sorted(ALLOWED_OUTPUT_MODES)}"

    return None


def _build_diagnostics(
    top_k: int,
    fetch_k: int,
    filters: Optional[Dict[str, Any]],
    output_mode: str,
) -> Dict[str, Any]:
    return {
        "top_k": top_k,
        "fetch_k": fetch_k,
        "filters": filters or {},
        "output_mode": output_mode,
    }


def _compact_job_result(result: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "score": result.get("score"),
        "doc_id": result.get("doc_id", ""),
        "company": result.get("company", ""),
        "title": result.get("title", ""),
        "location": result.get("location", ""),
        "source": result.get("source", ""),
        "job_url": result.get("job_url", ""),
        "posted_at": result.get("posted_at", ""),
        "visa_sponsorship": result.get("visa_sponsorship", ""),
        "ai_fit_score": result.get("ai_fit_score"),
    }


def _shape_search_results(results: List[Dict[str, Any]], output_mode: str) -> List[Dict[str, Any]]:
    if output_mode == "full":
        return results

    return [_compact_job_result(result) for result in results]


def _shape_answer_payload(result: Dict[str, Any], output_mode: str) -> Dict[str, Any]:
    if output_mode == "full":
        payload = dict(result)
        payload["source_count"] = len(result.get("sources", []))
        return payload

    compact_sources = [
        _compact_job_result(source)
        for source in result.get("sources", [])
    ]

    return {
        "question": result.get("question", ""),
        "answer": result.get("answer", ""),
        "insufficient_evidence": result.get("insufficient_evidence", False),
        "used_source_ids": result.get("used_source_ids", []),
        "source_count": len(compact_sources),
        "sources": compact_sources,
        "retrieved_count": result.get("retrieved_count", 0),
        "llm_provider": result.get("llm_provider", ""),
        "llm_model": result.get("llm_model", ""),
        "llm_fallback_used": result.get("llm_fallback_used", False),
        "retrieval_lanes_used": result.get("retrieval_lanes_used", []),
    }


def search_jobs_tool(
    query: str,
    top_k: int = 5,
    fetch_k: int = 15,
    filters: Optional[Dict[str, Any]] = None,
    include_diagnostics: bool = False,
    output_mode: str = "full",
) -> Dict[str, Any]:
    query_error = _validate_non_empty_string(query, "query")
    if query_error:
        return _error_payload("search_jobs", query_error)

    top_k_error = _validate_positive_int(top_k, "top_k")
    if top_k_error:
        return _error_payload("search_jobs", top_k_error)

    fetch_k_error = _validate_positive_int(fetch_k, "fetch_k")
    if fetch_k_error:
        return _error_payload("search_jobs", fetch_k_error)

    filters_error = _validate_filters(filters)
    if filters_error:
        return _error_payload("search_jobs", filters_error)

    output_mode_error = _validate_output_mode(output_mode)
    if output_mode_error:
        return _error_payload("search_jobs", output_mode_error)

    if fetch_k < top_k:
        return _error_payload(
            "search_jobs",
            "fetch_k must be >= top_k",
            details={"top_k": top_k, "fetch_k": fetch_k},
        )

    try:
        results = search_jobs(
            query=query,
            top_k=top_k,
            fetch_k=fetch_k,
            filters=filters,
        )
    except Exception as exc:
        return _error_payload(
            "search_jobs",
            str(exc),
            error_type="execution_error",
        )

    shaped_results = _shape_search_results(results, output_mode)

    payload: Dict[str, Any] = {
        "tool_name": "search_jobs",
        "ok": True,
        "query": query,
        "output_mode": output_mode,
        "result_count": len(shaped_results),
        "results": shaped_results,
    }

    if include_diagnostics:
        payload["diagnostics"] = _build_diagnostics(top_k, fetch_k, filters, output_mode)

    return payload


def answer_job_query_tool(
    question: str,
    top_k: int = 5,
    fetch_k: int = 15,
    filters: Optional[Dict[str, Any]] = None,
    include_diagnostics: bool = False,
    output_mode: str = "full",
) -> Dict[str, Any]:
    question_error = _validate_non_empty_string(question, "question")
    if question_error:
        return _error_payload("answer_job_query", question_error)

    top_k_error = _validate_positive_int(top_k, "top_k")
    if top_k_error:
        return _error_payload("answer_job_query", top_k_error)

    fetch_k_error = _validate_positive_int(fetch_k, "fetch_k")
    if fetch_k_error:
        return _error_payload("answer_job_query", fetch_k_error)

    filters_error = _validate_filters(filters)
    if filters_error:
        return _error_payload("answer_job_query", filters_error)

    output_mode_error = _validate_output_mode(output_mode)
    if output_mode_error:
        return _error_payload("answer_job_query", output_mode_error)

    if fetch_k < top_k:
        return _error_payload(
            "answer_job_query",
            "fetch_k must be >= top_k",
            details={"top_k": top_k, "fetch_k": fetch_k},
        )

    try:
        result = answer_job_query(
            question=question,
            top_k=top_k,
            fetch_k=fetch_k,
            filters=filters,
        )
    except Exception as exc:
        return _error_payload(
            "answer_job_query",
            str(exc),
            error_type="execution_error",
        )

    shaped_result = _shape_answer_payload(result, output_mode)

    payload: Dict[str, Any] = {
        "tool_name": "answer_job_query",
        "ok": True,
        "output_mode": output_mode,
        **shaped_result,
    }

    if include_diagnostics:
        payload["diagnostics"] = _build_diagnostics(top_k, fetch_k, filters, output_mode)

    return payload


RAG_TOOL_REGISTRY: Dict[str, Callable[..., Dict[str, Any]]] = {
    "search_jobs": search_jobs_tool,
    "answer_job_query": answer_job_query_tool,
}


def list_rag_tools() -> List[Dict[str, Any]]:
    return [
        {
            "name": "search_jobs",
            "description": "Retrieve relevant jobs from the local RAG corpus using hybrid retrieval, metadata inference, and grounding-aware gating.",
            "required_args": ["query"],
            "optional_args": ["top_k", "fetch_k", "filters", "include_diagnostics", "output_mode"],
            "output_modes": ["full", "compact"],
        },
        {
            "name": "answer_job_query",
            "description": "Answer a natural-language question using only retrieved job documents and grounded citations.",
            "required_args": ["question"],
            "optional_args": ["top_k", "fetch_k", "filters", "include_diagnostics", "output_mode"],
            "output_modes": ["full", "compact"],
        },
    ]


def run_rag_tool(tool_name: str, **kwargs: Any) -> Dict[str, Any]:
    tool = RAG_TOOL_REGISTRY.get(tool_name)
    if tool is None:
        return {
            "tool_name": tool_name,
            "ok": False,
            "error": f"Unknown RAG tool: {tool_name}",
            "error_type": "unknown_tool",
            "available_tools": [tool["name"] for tool in list_rag_tools()],
        }

    try:
        return tool(**kwargs)
    except TypeError as exc:
        return _error_payload(
            tool_name,
            str(exc),
            error_type="argument_error",
        )
    except Exception as exc:
        return _error_payload(
            tool_name,
            str(exc),
            error_type="execution_error",
        )


if __name__ == "__main__":
    print(list_rag_tools())