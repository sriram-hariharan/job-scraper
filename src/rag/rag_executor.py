from typing import Any, Dict, List, Optional

from src.rag.rag_tools import (
    answer_job_query_tool,
    search_jobs_tool,
)


ALLOWED_RAG_INTENTS = {"search_jobs", "answer_job_query", "unknown"}


def _normalize_request(value: Any) -> str:
    return str(value or "").strip().lower()


def _error_payload(
    request: str,
    error: str,
    error_type: str = "routing_error",
    intent: str = "unknown",
    details: Optional[Dict[str, Any]] = None,
    suggestions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "ok": False,
        "intent": intent,
        "request": request,
        "error": error,
        "error_type": error_type,
    }

    if details:
        payload["details"] = details

    if suggestions:
        payload["suggestions"] = suggestions

    return payload


def _looks_like_search_request(request: str) -> bool:
    request_norm = _normalize_request(request)

    strong_search_phrases = [
        "find jobs",
        "find me jobs",
        "search jobs",
        "show jobs",
        "list jobs",
        "jobs at ",
        "roles at ",
        "openings at ",
        "job openings",
        "search for jobs",
        "find roles",
        "show roles",
        "list roles",
    ]

    search_words = ["find", "search", "show", "list"]
    target_words = ["job", "jobs", "role", "roles", "opening", "openings"]

    if any(phrase in request_norm for phrase in strong_search_phrases):
        return True

    return any(word in request_norm for word in search_words) and any(
        word in request_norm for word in target_words
    )


def _looks_like_answer_request(request: str) -> bool:
    request_norm = _normalize_request(request)

    strong_answer_phrases = [
        "which jobs",
        "which roles",
        "what jobs",
        "what roles",
        "best jobs",
        "strongest jobs",
        "strongest roles",
        "compare jobs",
        "compare roles",
        "does any job",
        "does any role",
        "which job looks",
        "which roles look",
        "which jobs look",
    ]

    answer_starters = [
        "which",
        "what",
        "does",
        "compare",
        "are there",
        "is there",
    ]

    answer_targets = [
        "job",
        "jobs",
        "role",
        "roles",
        "posting",
        "postings",
    ]

    if any(phrase in request_norm for phrase in strong_answer_phrases):
        return True

    return any(request_norm.startswith(starter) for starter in answer_starters) and any(
        target in request_norm for target in answer_targets
    )


def classify_rag_intent(request: str) -> str:
    request_norm = _normalize_request(request)

    if not request_norm:
        return "unknown"

    if _looks_like_search_request(request_norm):
        return "search_jobs"

    if _looks_like_answer_request(request_norm):
        return "answer_job_query"

    return "unknown"


def _routing_suggestions(natural_intent: str) -> List[str]:
    if natural_intent == "search_jobs":
        return ["search_jobs"]

    if natural_intent == "answer_job_query":
        return ["answer_job_query"]

    return ["search_jobs", "answer_job_query"]


def _override_warning(
    natural_intent: str,
    final_intent: str,
    intent_override: Optional[str],
) -> Optional[Dict[str, Any]]:
    if not intent_override:
        return None

    if natural_intent == final_intent:
        return None

    return {
        "warning_type": "intent_override_mismatch",
        "message": (
            f"intent_override forced '{final_intent}' "
            f"but natural classification was '{natural_intent}'"
        ),
        "natural_intent": natural_intent,
        "forced_intent": final_intent,
    }


def execute_rag_request(
    request: str,
    top_k: int = 5,
    fetch_k: int = 15,
    filters: Optional[Dict[str, Any]] = None,
    output_mode: str = "compact",
    include_diagnostics: bool = False,
    intent_override: Optional[str] = None,
) -> Dict[str, Any]:
    request_norm = str(request or "").strip()
    if not request_norm:
        return _error_payload(
            request=request_norm,
            error="request must not be empty",
            error_type="validation_error",
        )

    natural_intent = classify_rag_intent(request_norm)
    final_intent = intent_override or natural_intent

    if final_intent not in ALLOWED_RAG_INTENTS:
        return _error_payload(
            request=request_norm,
            error=f"intent_override must be one of {sorted(ALLOWED_RAG_INTENTS)}",
            error_type="validation_error",
            details={"intent_override": intent_override},
        )

    if final_intent == "unknown":
        return _error_payload(
            request=request_norm,
            error="Could not classify request as search_jobs or answer_job_query",
            error_type="routing_error",
            intent="unknown",
            details={"natural_intent": natural_intent},
            suggestions=_routing_suggestions(natural_intent),
        )

    warning = _override_warning(
        natural_intent=natural_intent,
        final_intent=final_intent,
        intent_override=intent_override,
    )

    if final_intent == "search_jobs":
        response = search_jobs_tool(
            query=request_norm,
            top_k=top_k,
            fetch_k=fetch_k,
            filters=filters,
            include_diagnostics=include_diagnostics,
            output_mode=output_mode,
        )
        payload = {
            "ok": response.get("ok", False),
            "intent": "search_jobs",
            "natural_intent": natural_intent,
            "tool_name": "search_jobs",
            "request": request_norm,
            "response": response,
        }
    else:
        response = answer_job_query_tool(
            question=request_norm,
            top_k=top_k,
            fetch_k=fetch_k,
            filters=filters,
            include_diagnostics=include_diagnostics,
            output_mode=output_mode,
        )
        payload = {
            "ok": response.get("ok", False),
            "intent": "answer_job_query",
            "natural_intent": natural_intent,
            "tool_name": "answer_job_query",
            "request": request_norm,
            "response": response,
        }

    if warning:
        payload["warning"] = warning

    return payload


if __name__ == "__main__":
    demo_requests = [
        "find jobs at roku in new york",
        "which jobs look strongest for experimentation-heavy data science work using causal inference and looker?",
        "hello there",
    ]

    for request in demo_requests:
        print(execute_rag_request(request))