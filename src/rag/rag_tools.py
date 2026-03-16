from typing import Any, Callable, Dict, List, Optional

from src.rag.query_engine import search_jobs
from src.rag.rag_answerer import answer_job_query


def search_jobs_tool(
    query: str,
    top_k: int = 5,
    fetch_k: int = 15,
    filters: Optional[Dict[str, Any]] = None,
    include_diagnostics: bool = False,
) -> Dict[str, Any]:
    results = search_jobs(
        query=query,
        top_k=top_k,
        fetch_k=fetch_k,
        filters=filters,
    )

    payload: Dict[str, Any] = {
        "tool_name": "search_jobs",
        "ok": True,
        "query": query,
        "result_count": len(results),
        "results": results,
    }

    if include_diagnostics:
        payload["diagnostics"] = {
            "top_k": top_k,
            "fetch_k": fetch_k,
            "filters": filters or {},
        }

    return payload


def answer_job_query_tool(
    question: str,
    top_k: int = 5,
    fetch_k: int = 15,
    filters: Optional[Dict[str, Any]] = None,
    include_diagnostics: bool = False,
) -> Dict[str, Any]:
    result = answer_job_query(
        question=question,
        top_k=top_k,
        fetch_k=fetch_k,
        filters=filters,
    )

    payload: Dict[str, Any] = {
        "tool_name": "answer_job_query",
        "ok": True,
        **result,
    }

    if include_diagnostics:
        payload["diagnostics"] = {
            "top_k": top_k,
            "fetch_k": fetch_k,
            "filters": filters or {},
        }

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
            "optional_args": ["top_k", "fetch_k", "filters", "include_diagnostics"],
        },
        {
            "name": "answer_job_query",
            "description": "Answer a natural-language question using only retrieved job documents and grounded citations.",
            "required_args": ["question"],
            "optional_args": ["top_k", "fetch_k", "filters", "include_diagnostics"],
        },
    ]


def run_rag_tool(tool_name: str, **kwargs: Any) -> Dict[str, Any]:
    tool = RAG_TOOL_REGISTRY.get(tool_name)
    if tool is None:
        return {
            "tool_name": tool_name,
            "ok": False,
            "error": f"Unknown RAG tool: {tool_name}",
            "available_tools": [tool["name"] for tool in list_rag_tools()],
        }

    return tool(**kwargs)


if __name__ == "__main__":
    print(list_rag_tools())