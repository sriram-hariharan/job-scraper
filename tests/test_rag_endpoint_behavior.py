import socket
from types import SimpleNamespace

import pytest


@pytest.fixture
def offline_rag_query_isolation(monkeypatch):
    from src.rag import query_engine
    from src.storage import rag_store

    counters = {
        "database_connection_factory_calls": 0,
        "database_client_constructions": 0,
        "database_cursor_calls": 0,
        "database_execute_calls": 0,
        "credential_reads": 0,
        "network_socket_calls": 0,
    }

    monkeypatch.setattr(
        query_engine,
        "_infer_metadata_filters",
        lambda _query: {},
    )

    def reject_database_adapter(*_args, **_kwargs):
        counters["database_connection_factory_calls"] += 1
        raise AssertionError("offline RAG test reached the database adapter")

    def reject_database_process(*_args, **_kwargs):
        counters["database_client_constructions"] += 1
        raise AssertionError("offline RAG test attempted database client construction")

    def reject_database_configuration(*_args, **_kwargs):
        counters["credential_reads"] += 1
        raise AssertionError("offline RAG test attempted database configuration access")

    def reject_socket(*_args, **_kwargs):
        counters["network_socket_calls"] += 1
        raise AssertionError("offline RAG test attempted network access")

    monkeypatch.setattr(rag_store, "_run_psql_statement", reject_database_adapter)
    monkeypatch.setattr(rag_store, "_run_psql_json_query", reject_database_adapter)
    monkeypatch.setattr(rag_store, "_database_url", reject_database_configuration)
    monkeypatch.setattr(rag_store.subprocess, "run", reject_database_process)
    monkeypatch.setattr(socket, "socket", reject_socket)

    yield counters

    assert counters == {
        "database_connection_factory_calls": 0,
        "database_client_constructions": 0,
        "database_cursor_calls": 0,
        "database_execute_calls": 0,
        "credential_reads": 0,
        "network_socket_calls": 0,
    }


def _raw_result(
    *,
    doc_id="job-1",
    company="Acme AI",
    title="Machine Learning Engineer",
    source="lever",
    text="Machine learning engineer role building model training systems.",
    score=1.0,
):
    return {
        "score": score,
        "text": text,
        "metadata": {
            "doc_id": doc_id,
            "company": company,
            "title": title,
            "location": "Remote",
            "source": source,
            "job_url": f"https://example.com/{doc_id}",
            "posted_at": "2026-05-01",
            "all_skills": ["machine learning", "python"],
        },
    }


def test_search_jobs_semantic_timeout_falls_back_to_lexical(
    monkeypatch,
    offline_rag_query_isolation,
):
    from src.rag import query_engine

    def timeout_retrieval(*args, **kwargs):
        raise TimeoutError("semantic retrieval timed out")

    monkeypatch.setattr(query_engine, "_retrieve_jobs_with_timeout", timeout_retrieval)
    monkeypatch.setattr(
        query_engine,
        "_lexical_search",
        lambda *args, **kwargs: [_raw_result()],
    )

    results = query_engine.search_jobs(
        query="machine learning engineer",
        top_k=3,
        fetch_k=5,
    )

    assert len(results) == 1
    assert results[0]["title"] == "Machine Learning Engineer"
    assert results[0]["retrieval_lanes"] == ["lexical"]


def test_search_jobs_semantic_unavailable_falls_back_to_lexical(
    monkeypatch,
    offline_rag_query_isolation,
):
    from src.rag import query_engine

    def unavailable_retrieval(*args, **kwargs):
        raise RuntimeError(
            "Legacy filesystem RAG index is disabled. "
            "Semantic vector retrieval will move to pgvector/vector DB in 6B.16."
        )

    monkeypatch.setattr(query_engine, "_retrieve_jobs_with_timeout", unavailable_retrieval)
    monkeypatch.setattr(
        query_engine,
        "_lexical_search",
        lambda *args, **kwargs: [_raw_result()],
    )

    results = query_engine.search_jobs(
        query="machine learning engineer",
        top_k=3,
        fetch_k=5,
    )

    assert len(results) == 1
    assert results[0]["title"] == "Machine Learning Engineer"
    assert results[0]["retrieval_lanes"] == ["lexical"]


def test_answer_job_query_uses_lexical_fallback_after_semantic_timeout(
    monkeypatch,
    offline_rag_query_isolation,
):
    from src.rag import query_engine, rag_answerer

    def timeout_retrieval(*args, **kwargs):
        raise TimeoutError("semantic retrieval timed out")

    monkeypatch.setattr(query_engine, "_retrieve_jobs_with_timeout", timeout_retrieval)
    monkeypatch.setattr(
        query_engine,
        "_lexical_search",
        lambda *args, **kwargs: [_raw_result()],
    )
    monkeypatch.setattr(
        rag_answerer,
        "_run_chat_completion_with_timeout",
        lambda messages: {
            "content": (
                '{"answer":"The strongest match is Acme AI because it is a '
                'machine learning engineering role. [S1]",'
                '"insufficient_evidence":false,'
                '"used_source_ids":["S1"],'
                '"job_evidence":[{"source_id":"S1","evidence_points":["Machine learning engineer title"]}]}'
            ),
            "provider": "test",
            "model": "deterministic",
            "fallback_used": False,
        },
    )

    payload = rag_answerer.answer_job_query(
        question="What are the best machine learning engineer jobs?",
        top_k=3,
        fetch_k=5,
    )

    assert payload["answer"] != "I could not answer this because semantic retrieval timed out."
    assert payload["insufficient_evidence"] is False
    assert payload["retrieval_lanes_used"] == ["lexical"]
    assert payload["sources"][0]["title"] == "Machine Learning Engineer"


def test_answer_job_query_uses_lexical_fallback_after_semantic_unavailable(
    monkeypatch,
    offline_rag_query_isolation,
):
    from src.rag import query_engine, rag_answerer

    def unavailable_retrieval(*args, **kwargs):
        raise RuntimeError(
            "Legacy filesystem RAG index is disabled. "
            "Semantic vector retrieval will move to pgvector/vector DB in 6B.16."
        )

    monkeypatch.setattr(query_engine, "_retrieve_jobs_with_timeout", unavailable_retrieval)
    monkeypatch.setattr(
        query_engine,
        "_lexical_search",
        lambda *args, **kwargs: [
            _raw_result(
                title="Backend Software Engineer",
                text="Backend software engineer role building APIs and Python services.",
            )
        ],
    )
    monkeypatch.setattr(
        rag_answerer,
        "_run_chat_completion_with_timeout",
        lambda messages: {
            "content": (
                '{"answer":"The backend software role is the clearest match '
                'from the retrieved corpus. [S1]",'
                '"insufficient_evidence":false,'
                '"used_source_ids":["S1"],'
                '"job_evidence":[{"source_id":"S1","evidence_points":["Backend software role"]}]}'
            ),
            "provider": "test",
            "model": "deterministic",
            "fallback_used": False,
        },
    )

    payload = rag_answerer.answer_job_query(
        question="What are the best backend software jobs?",
        top_k=3,
        fetch_k=5,
    )

    assert "Legacy filesystem RAG index is disabled" not in payload["answer"]
    assert payload["insufficient_evidence"] is False
    assert payload["retrieval_lanes_used"] == ["lexical"]
    assert payload["sources"][0]["title"] == "Backend Software Engineer"


def test_answer_job_query_no_matches_after_semantic_unavailable_is_clean(
    monkeypatch,
    offline_rag_query_isolation,
):
    from src.rag import query_engine, rag_answerer

    def unavailable_retrieval(*args, **kwargs):
        raise RuntimeError(
            "Legacy filesystem RAG index is disabled. "
            "Semantic vector retrieval will move to pgvector/vector DB in 6B.16."
        )

    monkeypatch.setattr(query_engine, "_retrieve_jobs_with_timeout", unavailable_retrieval)
    monkeypatch.setattr(query_engine, "_lexical_search", lambda *args, **kwargs: [])

    payload = rag_answerer.answer_job_query(
        question="What are the best data scientist jobs?",
        top_k=3,
        fetch_k=5,
    )

    assert payload["insufficient_evidence"] is True
    assert "Legacy filesystem RAG index is disabled" not in payload["answer"]
    assert "current corpus" in payload["answer"]
    assert "Try broadening" in payload["answer"]
    assert payload["sources"] == []


def test_jobs_search_lite_excludes_obvious_rag_smoke_rows(monkeypatch):
    from src.app import services
    from src.rag import corpus_store, lexical_retriever, query_filters

    smoke = _raw_result(
        doc_id="rag-corpus-smoke-phase6b15g5a",
        company="RAG Corpus Smoke",
        title="RAG Corpus Smoke Phase6B15G5A",
        source="smoke phase",
        text="machine learning engineer diagnostic row",
    )
    real = _raw_result()

    monkeypatch.setattr(query_filters, "_infer_metadata_filters", lambda request: {})
    monkeypatch.setattr(lexical_retriever, "_lexical_search", lambda *args, **kwargs: [smoke, real])
    monkeypatch.setattr(corpus_store, "_load_job_corpus", lambda: [smoke, real])
    monkeypatch.setattr(services, "_overlay_application_actions", lambda rows, owner_user_id="": rows)

    payload = services.jobs_search_lite_payload("machine learning engineer", top_k=5)

    assert payload["result_count"] == 1
    assert payload["results"][0]["title"] == "Machine Learning Engineer"
    assert "RAG Corpus Smoke" not in {
        row["title"]
        for row in payload["results"]
    }


def test_assistant_intent_router_routes_keyword_searches():
    from src.app.services import route_assistant_intent

    assert route_assistant_intent("software engineer")["intent"] == "search_jobs"
    assert route_assistant_intent("backend python")["intent"] == "search_jobs"
    assert route_assistant_intent("machine learning engineer")["intent"] == "search_jobs"


def test_assistant_intent_router_routes_questions_and_recommendations():
    from src.app.services import route_assistant_intent

    assert (
        route_assistant_intent("What are the best backend engineering jobs?")["intent"]
        == "answer_job_query"
    )
    assert (
        route_assistant_intent("any of the jobs having python requirements?")["intent"]
        == "answer_job_query"
    )
    assert route_assistant_intent("give me jobs about AI")["intent"] == "answer_job_query"
    assert (
        route_assistant_intent("give me jobs with AI/LLM requirement")["intent"]
        == "answer_job_query"
    )
    assert (
        route_assistant_intent("jobs with python requirements")["intent"]
        == "answer_job_query"
    )
    assert (
        route_assistant_intent("do any jobs require python")["intent"]
        == "answer_job_query"
    )


def test_lexical_query_expansion_handles_common_ai_terms():
    from src.rag.lexical_retriever import expand_query_terms

    ai_expanded = expand_query_terms("give me jobs about AI")
    assert "artificial intelligence" in ai_expanded
    assert "machine learning" in ai_expanded

    llm_expanded = expand_query_terms("give me jobs with AI/LLM requirement")
    assert "artificial intelligence" in llm_expanded
    assert "large language model" in llm_expanded
    assert "generative ai" in llm_expanded


def test_lexical_search_finds_ai_jobs_with_expanded_query(monkeypatch):
    from src.rag import lexical_retriever

    monkeypatch.setattr(
        lexical_retriever,
        "_load_job_corpus",
        lambda: [
            {
                "doc_id": "job-ai-1",
                "company": "Air AI",
                "title": "AI Engineer",
                "location": "Remote",
                "source": "greenhouse",
                "job_url": "https://example.com/job-ai-1",
                "posted_at": "2026-05-01",
                "all_skills": ["AI", "Python"],
                "retrieval_text": "AI engineer building production artificial intelligence systems.",
            }
        ],
    )

    results = lexical_retriever._lexical_search(
        query="give me jobs about AI",
        top_k=5,
    )

    assert len(results) == 1
    assert results[0]["metadata"]["title"] == "AI Engineer"


def test_assistant_query_payload_for_search_uses_search_lite(monkeypatch):
    from src.app import services

    monkeypatch.setattr(
        services,
        "jobs_search_lite_payload",
        lambda request, top_k=5, owner_user_id="", allowed_job_ids=None, supplemental_docs=None: {
            "ok": True,
            "request": request,
            "result_count": 1,
            "results": [
                {
                    "company": "Acme AI",
                    "title": "Software Engineer",
                }
            ],
        },
    )

    payload = services.assistant_query_payload("software engineer", top_k=5)

    assert payload["ok"] is True
    assert payload["intent"] == "search_jobs"
    assert payload["natural_intent"] == "search_jobs"
    assert payload["result_count"] == 1
    assert payload["results"][0]["title"] == "Software Engineer"
    assert payload["response"] is None
    assert payload["router"]["intent"] == "search_jobs"


def test_assistant_query_payload_for_answer_uses_rag_answer(monkeypatch):
    from src.app import services

    monkeypatch.setattr(
        services,
        "rag_answer_payload",
        lambda request, top_k=5, fetch_k=10, output_mode="compact", include_diagnostics=False: {
            "ok": True,
            "request": request,
            "response": {
                "answer": "The backend role is strongest. [S1]",
                "sources": [
                    {
                        "source_id": "S1",
                        "company": "Acme AI",
                        "title": "Backend Engineer",
                    }
                ],
            },
        },
    )

    payload = services.assistant_query_payload(
        "What are the best backend engineering jobs?",
        top_k=5,
        fetch_k=10,
        include_diagnostics=False,
    )

    assert payload["ok"] is True
    assert payload["intent"] == "answer_job_query"
    assert payload["natural_intent"] == "answer_job_query"
    assert payload["result_count"] == 1
    assert payload["results"] == []
    assert payload["response"]["answer"] == "The backend role is strongest. [S1]"
    assert payload["router"]["intent"] == "answer_job_query"


def test_assistant_query_payload_cleans_known_internal_retrieval_error(monkeypatch):
    from src.app import services

    def raise_internal_error(*args, **kwargs):
        raise RuntimeError(
            "Legacy filesystem RAG index is disabled. "
            "Semantic vector retrieval will move to pgvector/vector DB in 6B.16."
        )

    monkeypatch.setattr(services, "rag_answer_payload", raise_internal_error)

    payload = services.assistant_query_payload("What jobs have Python requirements?")

    assert payload["ok"] is True
    assert payload["intent"] == "answer_job_query"
    assert payload["result_count"] == 0
    assert payload["response"]["insufficient_evidence"] is True
    assert "Legacy filesystem RAG index is disabled" not in payload["response"]["answer"]
    assert "current corpus" in payload["response"]["answer"]
    assert "Try broadening" in payload["response"]["answer"]


@pytest.mark.parametrize(
    ("endpoint_name", "service_name"),
    (
        ("rag_answer", "rag_answer_payload"),
        ("assistant_query", "assistant_query_payload"),
    ),
)
def test_grounded_answer_api_requires_and_passes_exact_authenticated_owner(
    monkeypatch,
    endpoint_name,
    service_name,
):
    from src.app import api as app_api

    auth_calls = []
    service_calls = []
    monkeypatch.setattr(
        app_api,
        "_require_auth_owner_user_id",
        lambda request: auth_calls.append(request) or "owner-a",
    )
    monkeypatch.setattr(
        app_api.services,
        service_name,
        lambda **kwargs: service_calls.append(kwargs) or {"ok": True},
    )
    http_request = SimpleNamespace(state=SimpleNamespace(auth_user={}))

    result = getattr(app_api, endpoint_name)(
        "Which jobs require Python?",
        http_request,
        top_k=3,
        fetch_k=7,
        include_diagnostics=True,
    )

    assert result == {"ok": True}
    assert auth_calls == [http_request]
    assert service_calls[0]["owner_user_id"] == "owner-a"
    assert service_calls[0]["request"] == "Which jobs require Python?"
    assert service_calls[0]["top_k"] == 3
    assert service_calls[0]["fetch_k"] == 7


@pytest.mark.parametrize("endpoint_name", ("rag_answer", "assistant_query"))
def test_grounded_answer_api_missing_owner_stops_before_service(
    monkeypatch,
    endpoint_name,
):
    from src.app import api as app_api

    monkeypatch.setattr(
        app_api.services,
        "rag_answer_payload",
        lambda **_kwargs: pytest.fail("RAG answer service must not run"),
    )
    monkeypatch.setattr(
        app_api.services,
        "assistant_query_payload",
        lambda **_kwargs: pytest.fail("assistant service must not run"),
    )
    http_request = SimpleNamespace(
        state=SimpleNamespace(auth_user={}),
    )

    with pytest.raises(app_api.HTTPException) as exc_info:
        getattr(app_api, endpoint_name)(
            "Which jobs require Python?",
            http_request,
        )

    assert exc_info.value.status_code == 401
    assert exc_info.value.detail == "Authentication required."


def test_rag_search_api_remains_owner_free_and_retrieval_only(monkeypatch):
    from src.app import api as app_api

    calls = []
    monkeypatch.setattr(
        app_api,
        "_require_auth_owner_user_id",
        lambda *_args, **_kwargs: pytest.fail("search must not require owner"),
    )
    monkeypatch.setattr(
        app_api.services,
        "rag_search_payload",
        lambda **kwargs: calls.append(kwargs) or {"ok": True},
    )

    result = app_api.rag_search(
        "python jobs",
        top_k=2,
        fetch_k=4,
    )

    assert result == {"ok": True}
    assert calls == [
        {
            "request": "python jobs",
            "top_k": 2,
            "fetch_k": 4,
            "output_mode": "compact",
            "include_diagnostics": False,
        }
    ]


def test_assistant_and_rag_services_propagate_normalized_owner(monkeypatch):
    from src.app import services
    from src.rag import rag_executor

    original_rag_answer_payload = services.rag_answer_payload
    answer_calls = []
    monkeypatch.setattr(
        services,
        "route_assistant_intent",
        lambda _request: {
            "intent": "answer_job_query",
            "reason": "test",
        },
    )
    monkeypatch.setattr(
        services,
        "rag_answer_payload",
        lambda **kwargs: answer_calls.append(kwargs) or {
            "ok": True,
            "response": {"answer": "answer", "sources": []},
        },
    )

    services.assistant_query_payload(
        "Which jobs require Python?",
        owner_user_id=" owner-a ",
    )

    assert answer_calls[0]["owner_user_id"] == "owner-a"

    executor_calls = []
    monkeypatch.setattr(
        rag_executor,
        "execute_rag_request",
        lambda **kwargs: executor_calls.append(kwargs) or {
            "ok": True,
            "response": {},
        },
    )
    monkeypatch.setattr(
        services,
        "_overlay_application_actions",
        lambda rows, owner_user_id="": rows,
    )

    original_rag_answer_payload(
        "Which jobs require Python?",
        owner_user_id=" owner-a ",
    )

    assert executor_calls == [
        {
            "request": "Which jobs require Python?",
            "top_k": 5,
            "fetch_k": 15,
            "filters": None,
            "output_mode": "compact",
            "include_diagnostics": False,
            "intent_override": "answer_job_query",
            "owner_user_id": "owner-a",
        }
    ]


def test_assistant_query_payload_propagates_owner_to_overlay_for_both_intents(monkeypatch):
    from src.app import services

    overlay_owner_calls = []

    def fake_overlay(rows, owner_user_id=""):
        overlay_owner_calls.append(owner_user_id)
        return rows

    monkeypatch.setattr(services, "_overlay_application_actions", fake_overlay)

    monkeypatch.setattr(
        services,
        "route_assistant_intent",
        lambda _request: {"intent": "search_jobs", "reason": "test"},
    )
    from src.rag import corpus_store, lexical_retriever, query_filters

    monkeypatch.setattr(query_filters, "_infer_metadata_filters", lambda request: {})
    monkeypatch.setattr(lexical_retriever, "_lexical_search", lambda *args, **kwargs: [])
    monkeypatch.setattr(corpus_store, "_load_job_corpus", lambda: [])

    services.assistant_query_payload(
        "python jobs",
        owner_user_id=" owner-c ",
    )

    assert overlay_owner_calls == ["owner-c"]

    monkeypatch.setattr(
        services,
        "route_assistant_intent",
        lambda _request: {"intent": "answer_job_query", "reason": "test"},
    )
    from src.rag import rag_executor

    monkeypatch.setattr(
        rag_executor,
        "execute_rag_request",
        lambda **kwargs: {
            "ok": True,
            "response": {"answer": "answer", "sources": [], "job_evidence": []},
        },
    )

    services.assistant_query_payload(
        "Which jobs require Python?",
        owner_user_id=" owner-c ",
    )

    assert overlay_owner_calls == ["owner-c", "owner-c", "owner-c"]


def test_rag_executor_routes_owner_only_to_answer_tool(monkeypatch):
    from src.rag import rag_executor

    answer_calls = []
    search_calls = []
    monkeypatch.setattr(
        rag_executor,
        "answer_job_query_tool",
        lambda **kwargs: answer_calls.append(kwargs) or {"ok": True},
    )
    monkeypatch.setattr(
        rag_executor,
        "search_jobs_tool",
        lambda **kwargs: search_calls.append(kwargs) or {"ok": True},
    )

    rag_executor.execute_rag_request(
        "Which jobs require Python?",
        intent_override="answer_job_query",
        owner_user_id=" owner-a ",
    )
    rag_executor.execute_rag_request(
        "find python jobs",
        intent_override="search_jobs",
        owner_user_id="owner-a",
    )

    assert answer_calls[0]["owner_user_id"] == "owner-a"
    assert "owner_user_id" not in search_calls[0]


def test_rag_tool_and_answerer_propagate_owner_to_timeout(monkeypatch):
    from src.rag import rag_answerer, rag_tools

    tool_calls = []
    monkeypatch.setattr(
        rag_tools,
        "answer_job_query",
        lambda **kwargs: tool_calls.append(kwargs) or {
            "question": kwargs["question"],
            "answer": "No match",
            "insufficient_evidence": True,
            "sources": [],
        },
    )

    rag_tools.answer_job_query_tool(
        "Which jobs require Python?",
        owner_user_id=" owner-a ",
    )

    assert tool_calls[0]["owner_user_id"] == "owner-a"

    timeout_calls = []
    monkeypatch.setattr(
        rag_answerer,
        "search_jobs",
        lambda **_kwargs: [_grounded_answer_result()],
    )
    monkeypatch.setattr(
        rag_answerer,
        "_run_chat_completion_with_timeout",
        lambda **kwargs: timeout_calls.append(kwargs) or _grounded_llm_result(),
    )

    rag_answerer.answer_job_query(
        "Which jobs require Python?",
        owner_user_id=" owner-a ",
    )

    assert timeout_calls[0]["owner_user_id"] == "owner-a"


def _grounded_answer_result():
    return {
        "score": 1.0,
        "doc_id": "job-1",
        "company": "Acme AI",
        "title": "Machine Learning Engineer",
        "location": "Remote",
        "source": "lever",
        "job_url": "https://example.com/job-1",
        "posted_at": "2026-05-01",
        "preview": "Python machine learning role.",
        "retrieval_text": "Python machine learning role.",
        "retrieval_lanes": ["semantic"],
    }


def _grounded_llm_result(provider="openai", model="gpt-5-mini"):
    return {
        "content": (
            '{"answer":"The Acme role requires Python. [S1]",'
            '"insufficient_evidence":false,'
            '"used_source_ids":["S1"],'
            '"job_evidence":[{"source_id":"S1",'
            '"evidence_points":["Python requirement"]}]}'
        ),
        "provider": provider,
        "model": model,
        "fallback_used": False,
    }


def test_owner_grounded_answer_executes_exact_route_once_inside_timeout(
    monkeypatch,
):
    from src.rag import rag_answerer

    resolver_calls = []
    runtime_calls = []
    monkeypatch.setattr(
        rag_answerer,
        "search_jobs",
        lambda **_kwargs: [_grounded_answer_result()],
    )
    monkeypatch.setattr(
        rag_answerer,
        "resolve_effective_user_provider_route",
        lambda owner, workload: resolver_calls.append(
            (owner, workload)
        ) or {
            "provider": "openai",
            "model": "gpt-5-mini",
            "effective_selection_source": "user_override",
        },
    )
    monkeypatch.setattr(
        rag_answerer,
        "run_user_chat_completion_with_metadata",
        lambda **kwargs: runtime_calls.append(kwargs)
        or _grounded_llm_result(),
    )
    monkeypatch.setattr(
        rag_answerer,
        "run_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail("legacy runtime must not execute"),
    )

    result = rag_answerer.answer_job_query(
        "Which jobs require Python?",
        owner_user_id=" owner-a ",
    )

    assert resolver_calls == [("owner-a", "grounded_rag_answer")]
    assert len(runtime_calls) == 1
    call = runtime_calls[0]
    assert call["owner_user_id"] == "owner-a"
    assert call["provider"] == "openai"
    assert call["model"] == "gpt-5-mini"
    assert call["temperature"] == rag_answerer.GROUNDED_RAG_TEMPERATURE
    assert call["max_tokens"] == rag_answerer.GROUNDED_RAG_MAX_TOKENS
    assert "fallback_enabled" not in call
    assert result["insufficient_evidence"] is False
    assert result["llm_provider"] == "openai"
    assert result["llm_model"] == "gpt-5-mini"
    assert result["llm_fallback_used"] is False


def test_owner_grounded_answer_timeout_uses_existing_executor_without_fallback(
    monkeypatch,
):
    from src.rag import rag_answerer

    submitted = []
    future_events = []
    executor_events = []

    class TimeoutFuture:
        def result(self, timeout):
            future_events.append(("result", timeout))
            raise rag_answerer.FuturesTimeoutError()

        def cancel(self):
            future_events.append(("cancel",))

    class RecordingExecutor:
        def __init__(self, max_workers):
            executor_events.append(("init", max_workers))

        def submit(self, function, **kwargs):
            submitted.append((function, kwargs))
            return TimeoutFuture()

        def shutdown(self, *, wait, cancel_futures):
            executor_events.append(("shutdown", wait, cancel_futures))

    monkeypatch.setattr(
        rag_answerer,
        "search_jobs",
        lambda **_kwargs: [_grounded_answer_result()],
    )
    monkeypatch.setattr(
        rag_answerer,
        "resolve_effective_user_provider_route",
        lambda owner, workload: {
            "provider": "groq",
            "model": "openai/gpt-oss-120b",
        },
    )
    monkeypatch.setattr(
        rag_answerer,
        "ThreadPoolExecutor",
        RecordingExecutor,
    )
    monkeypatch.setattr(
        rag_answerer,
        "run_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail("legacy runtime must not execute"),
    )

    result = rag_answerer.answer_job_query(
        "Which jobs require Python?",
        owner_user_id="owner-a",
    )

    assert submitted[0][0] is (
        rag_answerer.run_user_chat_completion_with_metadata
    )
    assert submitted[0][1]["owner_user_id"] == "owner-a"
    assert submitted[0][1]["provider"] == "groq"
    assert submitted[0][1]["model"] == "openai/gpt-oss-120b"
    assert "fallback_enabled" not in submitted[0][1]
    assert future_events == [
        ("result", rag_answerer.ANSWER_LLM_TIMEOUT_SECONDS),
        ("cancel",),
    ]
    assert executor_events == [
        ("init", 1),
        ("shutdown", False, True),
    ]
    assert result["insufficient_evidence"] is True
    assert "timed out after 25 seconds" in result["answer"]
    assert result["llm_fallback_used"] is False


def test_owner_grounded_route_failure_is_bounded_and_calls_no_runtime(
    monkeypatch,
):
    from src.rag import rag_answerer

    monkeypatch.setattr(
        rag_answerer,
        "search_jobs",
        lambda **_kwargs: [_grounded_answer_result()],
    )
    monkeypatch.setattr(
        rag_answerer,
        "resolve_effective_user_provider_route",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(
            RuntimeError("secret registry database detail")
        ),
    )
    monkeypatch.setattr(
        rag_answerer,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail("user runtime must not execute"),
    )
    monkeypatch.setattr(
        rag_answerer,
        "run_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail("legacy runtime must not execute"),
    )
    monkeypatch.setattr(
        rag_answerer,
        "ThreadPoolExecutor",
        lambda *_args, **_kwargs: pytest.fail("executor must not be created"),
    )

    result = rag_answerer.answer_job_query(
        "Which jobs require Python?",
        owner_user_id="owner-a",
    )

    assert result["insufficient_evidence"] is True
    assert "grounded_rag_owner_route_unavailable" in result["answer"]
    assert "secret" not in repr(result)
    assert result["sources"] == []
    assert result["llm_fallback_used"] is False


def test_owner_grounded_provider_failure_never_uses_legacy_fallback(monkeypatch):
    from src.rag import rag_answerer

    monkeypatch.setattr(
        rag_answerer,
        "search_jobs",
        lambda **_kwargs: [_grounded_answer_result()],
    )
    monkeypatch.setattr(
        rag_answerer,
        "resolve_effective_user_provider_route",
        lambda owner, workload: {
            "provider": "openai",
            "model": "gpt-5-mini",
        },
    )
    monkeypatch.setattr(
        rag_answerer,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: (_ for _ in ()).throw(
            RuntimeError("provider unavailable")
        ),
    )
    monkeypatch.setattr(
        rag_answerer,
        "run_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail("legacy runtime must not execute"),
    )

    result = rag_answerer.answer_job_query(
        "Which jobs require Python?",
        owner_user_id="owner-a",
    )

    assert result["insufficient_evidence"] is True
    assert "grounded answer generation failed" in result["answer"]
    assert result["llm_fallback_used"] is False


def test_blank_owner_grounded_answer_preserves_legacy_timeout_path(monkeypatch):
    from src.rag import rag_answerer

    legacy_calls = []
    monkeypatch.setattr(
        rag_answerer,
        "search_jobs",
        lambda **_kwargs: [_grounded_answer_result()],
    )
    monkeypatch.setattr(
        rag_answerer,
        "resolve_effective_user_provider_route",
        lambda *_args, **_kwargs: pytest.fail("resolver must not execute"),
    )
    monkeypatch.setattr(
        rag_answerer,
        "run_user_chat_completion_with_metadata",
        lambda **_kwargs: pytest.fail("user runtime must not execute"),
    )
    monkeypatch.setattr(
        rag_answerer,
        "run_chat_completion_with_metadata",
        lambda **kwargs: legacy_calls.append(kwargs)
        or _grounded_llm_result("legacy", rag_answerer.MODEL),
    )

    result = rag_answerer.answer_job_query(
        "Which jobs require Python?",
    )

    assert len(legacy_calls) == 1
    assert legacy_calls[0]["model"] == rag_answerer.MODEL
    assert result["llm_provider"] == "legacy"
    assert result["llm_model"] == rag_answerer.MODEL


def test_execute_rag_request_blank_owner_remains_cli_compatible(monkeypatch):
    from src.rag import rag_executor

    calls = []
    monkeypatch.setattr(
        rag_executor,
        "answer_job_query_tool",
        lambda question, top_k, fetch_k, filters, include_diagnostics, output_mode: (
            calls.append(question) or {"ok": True}
        ),
    )

    payload = rag_executor.execute_rag_request(
        "Which jobs require Python?",
        intent_override="answer_job_query",
    )

    assert calls == ["Which jobs require Python?"]
    assert payload["ok"] is True
