"""Item 3E2: the floating chatbot answers only from the owner's Dashboard population.

The shared RAG corpus stays the acquisition corpus and pipeline input. These
tests pin the query-time owner-scoped view over it: both chatbot intents, the
3E0 overview fallback, owner isolation, and fail-closed empty-dashboard
behavior. They also pin the retention protection for Dashboard-referenced jobs.
"""
import pytest


def _doc(doc_id, company, title, skills, text, role_family=""):
    return {
        "doc_id": doc_id,
        "company": company,
        "title": title,
        "location": "Remote",
        "source": "greenhouse",
        "job_url": doc_id,
        "posted_at": "2026-08-01",
        "role_family": role_family,
        "seniority": "mid",
        "required_skills": skills,
        "preferred_skills": [],
        "all_skills": skills,
        "visa_sponsorship": "",
        "ai_fit_score": 70,
        "retrieval_text": text,
    }


# Owner A dashboard jobs
A1 = _doc("https://x.test/a1", "Capital One", "Backend Engineer",
          ["Java", "Spring Boot", "AWS"],
          "Backend Engineer at Capital One using Java and Spring Boot on AWS.",
          role_family="backend")
A2 = _doc("https://x.test/a2", "Walmart", "Data Engineer",
          ["Python", "Spark", "AWS"],
          "Data Engineer at Walmart building pipelines with Python and Spark on AWS.",
          role_family="data")
# Owner B dashboard jobs
B1 = _doc("https://x.test/b1", "Stripe", "Java Developer",
          ["Java", "Kafka"], "Java Developer at Stripe with Java and Kafka.",
          role_family="backend")
B2 = _doc("https://x.test/b2", "Datadog", "Data Engineer",
          ["Python", "Airflow"], "Data Engineer at Datadog with Python and Airflow.",
          role_family="data")
# Shared-market jobs on nobody's dashboard
X1 = _doc("https://x.test/x1", "GlobalCorp", "Backend Engineer",
          ["Java", "AWS"], "Backend Engineer at GlobalCorp with Java on AWS.",
          role_family="backend")
X2 = _doc("https://x.test/x2", "MarketCo", "Data Engineer",
          ["Python", "AWS"], "Data Engineer at MarketCo with Python on AWS.",
          role_family="data")

SHARED_RAG = [A1, A2, B1, B2, X1, X2]
DASH_A = {A1["doc_id"], A2["doc_id"]}
DASH_B = {B1["doc_id"], B2["doc_id"]}


@pytest.fixture
def shared_corpus(monkeypatch):
    from src.rag import corpus_store, lexical_retriever, query_engine, query_filters

    corpus_store.reset_job_corpus_cache()
    monkeypatch.setattr(corpus_store, "_load_job_corpus", lambda: SHARED_RAG)
    monkeypatch.setattr(lexical_retriever, "_load_job_corpus", lambda: SHARED_RAG)

    def _unavailable(*_a, **_k):
        raise RuntimeError("Legacy filesystem RAG index is disabled")

    monkeypatch.setattr(query_engine, "retrieve_jobs", _unavailable)
    monkeypatch.setattr(query_filters, "_build_metadata_catalog", lambda: {
        "companies": {}, "sources": {}, "titles": {},
        "role_families": {"backend": "backend", "data": "data"},
        "seniorities": {}, "locations": {},
    })
    yield
    corpus_store.reset_job_corpus_cache()


def _scope_owner(monkeypatch, allowed):
    """Pin the Dashboard scope without touching pipeline/artifact storage.

    The 3C0 application-action overlay is presentation-only and reaches
    Postgres, so it is stubbed as a pass-through to keep these tests offline.
    """
    from src.app import services

    monkeypatch.setattr(services, "dashboard_allowed_job_ids", lambda _o="": allowed)
    monkeypatch.setattr(
        services, "_overlay_application_actions",
        lambda rows, owner_user_id="": rows,
    )


def _run_chat(request, owner="owner-a"):
    from src.app import services

    return services.assistant_query_payload(request, owner_user_id=owner, top_k=5, fetch_k=10)


def _evidence_ids(payload):
    ids = {row.get("doc_id", "") for row in (payload.get("results") or [])}
    response = payload.get("response") or {}
    for key in ("sources", "job_evidence"):
        for row in (response.get(key) or []):
            ids.add(row.get("doc_id", ""))
    return {i for i in ids if i}


# --- 1. Shared RAG genuinely contains jobs outside the Dashboard -------------

def test_shared_rag_contains_jobs_outside_dashboard(shared_corpus):
    from src.rag.corpus_store import _load_job_corpus

    corpus_ids = {d["doc_id"] for d in _load_job_corpus()}
    assert len(corpus_ids) > len(DASH_A)
    assert X1["doc_id"] in corpus_ids and X2["doc_id"] in corpus_ids
    assert not (DASH_A & {X1["doc_id"], X2["doc_id"]})


# --- 2. Search intent is Dashboard scoped ------------------------------------

@pytest.mark.parametrize("request_text", [
    "Show backend engineering roles",
    "Show data engineering roles",
    "Show postings mentioning AWS",
    "Show Java developer jobs",
])
def test_search_intent_returns_only_dashboard_jobs(shared_corpus, monkeypatch, request_text):
    _scope_owner(monkeypatch, set(DASH_A))
    payload = _run_chat(request_text)
    got = _evidence_ids(payload)
    assert got, f"{request_text} returned nothing for a populated dashboard"
    assert got <= DASH_A, f"{request_text} leaked non-dashboard jobs: {got - DASH_A}"


# --- 3. Answer intent excludes out-of-scope jobs BEFORE LLM evidence ---------

def test_answer_intent_scopes_retrieval_before_llm(shared_corpus, monkeypatch):
    """The answerer must never receive out-of-scope documents."""
    from src.rag import rag_answerer

    seen_prompt_docs = {}

    def fake_llm(messages, owner_user_id=""):
        seen_prompt_docs["prompt"] = messages[-1]["content"]
        return {
            "content": '{"answer": "Java appears in one posting. [S1]",'
                       ' "insufficient_evidence": false, "used_source_ids": ["S1"],'
                       ' "job_evidence": []}',
            "provider": "test", "model": "test-model", "fallback_used": False,
        }

    monkeypatch.setattr(rag_answerer, "_run_chat_completion_with_timeout", fake_llm)
    _scope_owner(monkeypatch, set(DASH_A))

    _run_chat("Compare Java and Python requirements in available postings")

    prompt = seen_prompt_docs.get("prompt", "")
    assert prompt, "LLM was never invoked"
    # Out-of-scope jobs must not appear anywhere in the assembled evidence.
    assert X1["doc_id"] not in prompt
    assert X2["doc_id"] not in prompt
    assert B1["doc_id"] not in prompt
    assert "GlobalCorp" not in prompt and "MarketCo" not in prompt


def test_answer_retrieval_layer_is_scoped(shared_corpus):
    from src.rag.query_engine import search_jobs

    rows = search_jobs(query="Show backend engineering roles", top_k=5, fetch_k=10,
                       allowed_job_ids=set(DASH_A))
    assert rows
    assert {r["doc_id"] for r in rows} <= DASH_A


# --- 4. Overview fallback samples only Dashboard jobs ------------------------

@pytest.mark.parametrize("request_text", [
    "What kinds of roles are available?",
    "Which companies are hiring?",
    "What skills appear most often?",
])
def test_overview_fallback_samples_only_dashboard_jobs(shared_corpus, monkeypatch, request_text):
    from src.rag.query_engine import search_jobs

    rows = search_jobs(query=request_text, top_k=5, fetch_k=10, allowed_job_ids=set(DASH_A))
    assert rows, f"{request_text} produced no dashboard evidence"
    assert {r["doc_id"] for r in rows} <= DASH_A


def test_corpus_overview_results_respects_scope(shared_corpus):
    from src.rag.lexical_retriever import _corpus_overview_results

    rows = _corpus_overview_results(top_k=12, allowed_job_ids=set(DASH_A))
    assert {r["metadata"]["doc_id"] for r in rows} <= DASH_A


# --- 5. Owner isolation ------------------------------------------------------

def test_owner_a_cannot_retrieve_owner_b_dashboard_jobs(shared_corpus, monkeypatch):
    _scope_owner(monkeypatch, set(DASH_A))
    got_a = _evidence_ids(_run_chat("Show Java developer jobs", owner="owner-a"))
    assert got_a <= DASH_A
    assert not (got_a & DASH_B)

    _scope_owner(monkeypatch, set(DASH_B))
    got_b = _evidence_ids(_run_chat("Show Java developer jobs", owner="owner-b"))
    assert got_b <= DASH_B
    assert not (got_b & DASH_A)


def test_shared_market_jobs_never_surface(shared_corpus, monkeypatch):
    _scope_owner(monkeypatch, set(DASH_A))
    for request_text in ["Show backend engineering roles", "Show postings mentioning AWS"]:
        got = _evidence_ids(_run_chat(request_text))
        assert X1["doc_id"] not in got
        assert X2["doc_id"] not in got


# --- 6. Empty dashboard is fail-closed ---------------------------------------

@pytest.mark.parametrize("request_text", [
    "Show backend engineering roles",
    "What kinds of roles are available?",
    "Compare Java and Python requirements in available postings",
])
def test_empty_dashboard_never_falls_back_to_global_corpus(
    shared_corpus, monkeypatch, request_text
):
    _scope_owner(monkeypatch, set())
    payload = _run_chat(request_text)
    assert _evidence_ids(payload) == set(), "empty dashboard must not widen to shared RAG"


def test_empty_scope_blocks_retrieval_layer(shared_corpus):
    from src.rag.lexical_retriever import _corpus_overview_results, _lexical_search
    from src.rag.query_engine import search_jobs

    assert search_jobs(query="Show backend engineering roles", allowed_job_ids=set()) == []
    assert _lexical_search(query="Java", top_k=5, allowed_job_ids=set()) == []
    assert _corpus_overview_results(top_k=12, allowed_job_ids=set()) == []


# --- 7. Scope membership semantics -------------------------------------------

def test_unscoped_none_preserves_existing_behavior(shared_corpus):
    from src.rag.lexical_retriever import is_job_doc_allowed
    from src.rag.query_engine import search_jobs

    assert is_job_doc_allowed(X1, None) is True
    assert is_job_doc_allowed(X1, set()) is False
    assert is_job_doc_allowed(X1, {X1["doc_id"]}) is True
    rows = search_jobs(query="Show backend engineering roles", top_k=5, fetch_k=10)
    assert {r["doc_id"] for r in rows} & {X1["doc_id"]}


def test_dashboard_scope_is_none_without_owner_and_closed_without_run(monkeypatch):
    from src.app import services

    assert services.dashboard_allowed_job_ids("") is None
    monkeypatch.setattr(services, "_latest_user_pipeline_artifact_context", lambda **_k: {})
    assert services.dashboard_allowed_job_ids("owner-a") == set()


def test_dashboard_scope_uses_browse_base_membership(monkeypatch):
    from src.app import services

    ja = services._job_app()
    monkeypatch.setattr(ja, "_overlay_operator_decisions", lambda rows: rows)
    monkeypatch.setattr(
        services, "_latest_user_pipeline_artifact_context",
        lambda **_k: {
            "best_rows": [
                {"job_doc_id": A1["doc_id"], "job_company": "Capital One", "job_title": "Backend Engineer"},
                {"job_doc_id": A2["doc_id"], "job_company": "Walmart", "job_title": "Data Engineer"},
            ],
            "queue_rows": [], "manifest_rows": [],
        },
    )
    # Applied jobs are excluded from base membership, exactly as /browse does.
    monkeypatch.setattr(
        services, "_overlay_application_actions",
        lambda rows, owner_user_id="": [
            dict(r, is_applied=(r.get("job_doc_id") == A2["doc_id"])) for r in rows
        ],
    )
    allowed = services.dashboard_allowed_job_ids("owner-a")
    assert A1["doc_id"] in allowed
    assert A2["doc_id"] not in allowed


# --- 8/9. Existing owner contracts preserved ---------------------------------

def test_owner_overlay_still_scoped_from_3c0(monkeypatch):
    from src.app import services

    seen = []
    monkeypatch.setattr(
        services, "_overlay_application_actions",
        lambda rows, owner_user_id="": seen.append(owner_user_id) or rows,
    )
    monkeypatch.setattr(services, "dashboard_allowed_job_ids", lambda _o="": None)
    monkeypatch.setattr(
        services, "route_assistant_intent",
        lambda _r: {"intent": "answer_job_query", "reason": "t"},
    )
    from src.rag import rag_executor

    monkeypatch.setattr(
        rag_executor, "execute_rag_request",
        lambda **_k: {"ok": True, "response": {"answer": "a", "sources": [], "job_evidence": []}},
    )
    services.assistant_query_payload("Which jobs require Python?", owner_user_id=" owner-z ")
    assert seen == ["owner-z", "owner-z"]


def test_provider_routing_remains_owner_scoped():
    import inspect

    from src.rag import rag_answerer

    src = inspect.getsource(rag_answerer._run_chat_completion_with_timeout)
    assert "resolve_effective_user_provider_route" in src
    assert "owner" in src


# --- 10. Owner-free /rag/search contract unchanged ----------------------------

def test_rag_search_endpoint_remains_owner_free(monkeypatch):
    from src.app import api as app_api

    calls = []
    monkeypatch.setattr(
        app_api, "_require_auth_owner_user_id",
        lambda *_a, **_k: pytest.fail("search must not require owner"),
    )
    monkeypatch.setattr(
        app_api.services, "rag_search_payload",
        lambda **kw: calls.append(kw) or {"ok": True},
    )
    app_api.rag_search("python jobs", top_k=2, fetch_k=4)
    assert "owner_user_id" not in calls[0]
    assert "allowed_job_ids" not in calls[0]


# --- Retention repair ---------------------------------------------------------

def test_retention_sql_protects_dashboard_referenced_documents():
    import inspect

    from src.storage import rag_store

    src = inspect.getsource(rag_store.delete_stale_rag_job_documents)
    # Protection is expressed in the existing bounded DELETE, not a rebuild.
    assert "protected" in src
    assert "merge_key NOT IN (SELECT merge_key FROM protected)" in src
    assert "best_resume_variant_by_job.csv" in src
    assert "application_execution_queue.csv" in src
    assert "job_packet_manifest.csv" in src
    assert "status = 'succeeded'" in src
    # Retention window and cache invalidation are preserved.
    assert "RAG_JOB_RETENTION_DAYS" in src or "stale_before" in src
    assert "TRUNCATE" not in src.upper()
    assert "DROP " not in src.upper()


def test_retention_reports_referenced_retained_count(monkeypatch):
    from src.storage import rag_store

    monkeypatch.setattr(rag_store, "init_rag_store", lambda: None)
    monkeypatch.setattr(
        rag_store, "_run_psql_json_query",
        lambda _sql: {
            "inspected_count": 10,
            "candidate_count": 4,
            "referenced_retained_count": 1,
            "deleted_count": 3,
        },
    )
    invalidated = []
    monkeypatch.setattr(
        rag_store, "_invalidate_rag_document_cache",
        lambda: invalidated.append(True) or True,
    )

    result = rag_store.delete_stale_rag_job_documents()
    assert result["deleted_count"] == 3
    assert result["referenced_retained_count"] == 1
    assert result["retained_count"] == 7
    assert result["cache_invalidation_attempted"] is True
    assert invalidated == [True]


def test_retention_skips_cache_invalidation_when_nothing_deleted(monkeypatch):
    from src.storage import rag_store

    monkeypatch.setattr(rag_store, "init_rag_store", lambda: None)
    monkeypatch.setattr(
        rag_store, "_run_psql_json_query",
        lambda _sql: {
            "inspected_count": 5, "candidate_count": 0,
            "referenced_retained_count": 0, "deleted_count": 0,
        },
    )
    monkeypatch.setattr(
        rag_store, "_invalidate_rag_document_cache",
        lambda: pytest.fail("must not invalidate when nothing was deleted"),
    )
    result = rag_store.delete_stale_rag_job_documents()
    assert result["deleted_count"] == 0
    assert result["cache_invalidation_attempted"] is False


def test_chatbot_reader_uses_same_active_window_as_pipeline_reader():
    import inspect

    from src.storage import rag_store

    chatbot_src = inspect.getsource(rag_store.get_rag_job_documents)
    pipeline_src = inspect.getsource(
        rag_store.get_bounded_owner_projection_rag_job_documents
    )
    window = "updated_at >= statement_timestamp() - INTERVAL"
    assert window in chatbot_src, "chatbot reader must honor the active window"
    assert window in pipeline_src


# =============================================================================
# Item 3E2-R: Dashboard evidence completeness.
# Dashboard = {A1, A2, C}; Shared RAG = {A1, A2, B1, B2, X1, X2} (no C).
# Effective chatbot evidence must be {A1, A2, C} — never dropping C, never X.
# =============================================================================

C_MISSING = _doc("https://x.test/c1", "Aurora Labs", "Platform Engineer",
                 ["Go", "Kubernetes", "AWS"],
                 "Platform Engineer at Aurora Labs working with Go, Kubernetes and AWS.",
                 role_family="backend")

DASH_A_PLUS_C = DASH_A | {C_MISSING["doc_id"]}


def _run_corpus_jsonl(*docs):
    import json

    return "\n".join(json.dumps(d) for d in docs)


def _supplemental_for(monkeypatch, run_docs, allowed):
    """Build artifact-backed evidence through the real services helper."""
    from src.app import services

    monkeypatch.setattr(
        services, "_latest_user_pipeline_artifact_context",
        lambda **_k: {"current_run_job_corpus_text": _run_corpus_jsonl(*run_docs)},
    )
    return services.dashboard_supplemental_documents(
        owner_user_id="owner-a", allowed_job_ids=allowed
    )


def test_artifact_backed_document_is_built_from_real_artifact_fields(monkeypatch):
    docs = _supplemental_for(monkeypatch, [C_MISSING], set(DASH_A_PLUS_C))
    assert len(docs) == 1
    doc = docs[0]
    assert doc["doc_id"] == C_MISSING["doc_id"]
    assert doc["title"] == "Platform Engineer"
    assert doc["company"] == "Aurora Labs"
    assert doc["location"] == "Remote"
    assert doc["source"] == "greenhouse"
    assert "Kubernetes" in doc["retrieval_text"]


def test_supplemental_never_widens_beyond_dashboard(monkeypatch):
    # X1 is in the run corpus but NOT an allowed dashboard job.
    docs = _supplemental_for(monkeypatch, [C_MISSING, X1], set(DASH_A_PLUS_C))
    assert {d["doc_id"] for d in docs} == {C_MISSING["doc_id"]}


def test_supplemental_does_not_fabricate_content_when_text_missing(monkeypatch):
    bare = dict(C_MISSING, retrieval_text="", description="")
    docs = _supplemental_for(monkeypatch, [bare], set(DASH_A_PLUS_C))
    assert docs == [], "records without searchable text must not become evidence"


def test_supplemental_is_empty_without_owner_or_scope(monkeypatch):
    from src.app import services

    assert services.dashboard_supplemental_documents("", {"x"}) == []
    assert services.dashboard_supplemental_documents("owner-a", None) == []
    assert services.dashboard_supplemental_documents("owner-a", set()) == []


def test_effective_evidence_equals_dashboard_membership(shared_corpus, monkeypatch):
    """Dashboard {A1,A2,C} over RAG {A1,A2,B,X} must yield exactly {A1,A2,C}."""
    from src.rag.lexical_retriever import _allowed_corpus_docs
    from src.rag.corpus_store import _load_job_corpus

    supplemental = _supplemental_for(monkeypatch, [C_MISSING], set(DASH_A_PLUS_C))
    population = _allowed_corpus_docs(
        _load_job_corpus(), set(DASH_A_PLUS_C), supplemental
    )
    ids = {d["doc_id"] for d in population}
    assert ids == DASH_A_PLUS_C
    assert X1["doc_id"] not in ids and B1["doc_id"] not in ids


def test_no_duplicate_when_job_exists_in_both(shared_corpus, monkeypatch):
    from src.rag.lexical_retriever import _allowed_corpus_docs
    from src.rag.corpus_store import _load_job_corpus

    # A1 is in shared RAG AND in the run corpus artifact.
    supplemental = _supplemental_for(monkeypatch, [A1, C_MISSING], set(DASH_A_PLUS_C))
    population = _allowed_corpus_docs(
        _load_job_corpus(), set(DASH_A_PLUS_C), supplemental
    )
    ids = [d["doc_id"] for d in population]
    assert len(ids) == len(set(ids)), f"duplicate evidence documents: {ids}"
    assert ids.count(A1["doc_id"]) == 1


def test_search_path_sees_artifact_backed_job(shared_corpus, monkeypatch):
    from src.rag.lexical_retriever import _lexical_search

    supplemental = _supplemental_for(monkeypatch, [C_MISSING], set(DASH_A_PLUS_C))
    rows = _lexical_search(
        query="Show Kubernetes platform roles", top_k=15,
        allowed_job_ids=set(DASH_A_PLUS_C), supplemental_docs=supplemental,
    )
    assert C_MISSING["doc_id"] in {r["metadata"]["doc_id"] for r in rows}


def test_answer_path_includes_artifact_backed_job_before_llm(shared_corpus, monkeypatch):
    from src.rag.query_engine import search_jobs

    supplemental = _supplemental_for(monkeypatch, [C_MISSING], set(DASH_A_PLUS_C))
    rows = search_jobs(
        query="Show Kubernetes platform roles", top_k=12, fetch_k=12,
        allowed_job_ids=set(DASH_A_PLUS_C), supplemental_docs=supplemental,
    )
    ids = {r["doc_id"] for r in rows}
    assert C_MISSING["doc_id"] in ids
    assert ids <= DASH_A_PLUS_C


def test_overview_path_includes_artifact_backed_job(shared_corpus, monkeypatch):
    from src.rag.lexical_retriever import _corpus_overview_results

    supplemental = _supplemental_for(monkeypatch, [C_MISSING], set(DASH_A_PLUS_C))
    rows = _corpus_overview_results(
        top_k=12, allowed_job_ids=set(DASH_A_PLUS_C), supplemental_docs=supplemental,
    )
    ids = {r["metadata"]["doc_id"] for r in rows}
    assert ids == DASH_A_PLUS_C


def test_owner_a_artifact_fallback_cannot_leak_to_owner_b(shared_corpus, monkeypatch):
    from src.rag.lexical_retriever import _allowed_corpus_docs
    from src.rag.corpus_store import _load_job_corpus

    supplemental_a = _supplemental_for(monkeypatch, [C_MISSING], set(DASH_A_PLUS_C))
    # Owner B's scope must reject Owner A's artifact-backed document.
    population_b = _allowed_corpus_docs(_load_job_corpus(), set(DASH_B), supplemental_a)
    ids_b = {d["doc_id"] for d in population_b}
    assert C_MISSING["doc_id"] not in ids_b
    assert ids_b <= DASH_B


def test_empty_scope_still_fail_closed_with_supplemental(shared_corpus, monkeypatch):
    from src.rag.lexical_retriever import _allowed_corpus_docs
    from src.rag.corpus_store import _load_job_corpus

    supplemental = _supplemental_for(monkeypatch, [C_MISSING], set(DASH_A_PLUS_C))
    assert _allowed_corpus_docs(_load_job_corpus(), set(), supplemental) == []
