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


def test_search_jobs_semantic_timeout_falls_back_to_lexical(monkeypatch):
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


def test_search_jobs_semantic_unavailable_falls_back_to_lexical(monkeypatch):
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


def test_answer_job_query_uses_lexical_fallback_after_semantic_timeout(monkeypatch):
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


def test_answer_job_query_uses_lexical_fallback_after_semantic_unavailable(monkeypatch):
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


def test_answer_job_query_no_matches_after_semantic_unavailable_is_clean(monkeypatch):
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
        lambda request, top_k=5: {
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
