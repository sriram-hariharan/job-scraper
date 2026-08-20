"""Item 3E0: basic chatbot capability reliability against the job corpus.

These tests pin the categories a user reasonably expects from the current
corpus: role search, technology search, company/location search, corpus
overview, comparison, and genuine no-match. They exercise the real routing and
retrieval path (src.app.services.route_assistant_intent -> lexical search or
src.rag.query_engine.search_jobs) with only the corpus loader replaced, so no
production behavior is faked.
"""
import pytest


def _doc(doc_id, company, title, location, skills, text, role_family="", seniority=""):
    return {
        "doc_id": doc_id,
        "company": company,
        "title": title,
        "location": location,
        "source": "greenhouse",
        "job_url": f"https://example.test/{doc_id}",
        "posted_at": "2026-08-01",
        "role_family": role_family,
        "seniority": seniority,
        "required_skills": skills,
        "preferred_skills": [],
        "all_skills": skills,
        "visa_sponsorship": "",
        "ai_fit_score": 70,
        "retrieval_text": text,
    }


CORPUS = [
    _doc("d1", "Capital One", "Senior Backend Engineer", "McLean, Virginia",
         ["Java", "Spring Boot", "AWS", "Microservices"],
         "Senior Backend Engineer at Capital One. Build distributed services in "
         "Java and Spring Boot on AWS.",
         role_family="backend", seniority="senior"),
    _doc("d2", "Walmart", "Data Engineer", "Bentonville, Arkansas",
         ["Python", "Spark", "Databricks", "SQL"],
         "Data Engineer at Walmart. Build ETL pipelines with Python, Spark and "
         "Databricks. SQL required.",
         role_family="data", seniority="mid"),
    _doc("d3", "Capital One", "Machine Learning Engineer", "Remote",
         ["Python", "PyTorch", "AWS", "Machine Learning"],
         "Machine Learning Engineer. Train and deploy models with Python and "
         "PyTorch on AWS SageMaker.",
         role_family="ml", seniority="mid"),
    _doc("d4", "Stripe", "Java Developer", "Remote",
         ["Java", "Kafka", "PostgreSQL"],
         "Java Developer building payment services with Java, Kafka and PostgreSQL.",
         role_family="backend", seniority="mid"),
    _doc("d5", "Walmart", "Senior Data Engineer", "Virginia",
         ["Python", "Airflow", "AWS", "Snowflake"],
         "Senior Data Engineer. Orchestrate pipelines with Airflow on AWS, model "
         "data in Snowflake using Python.",
         role_family="data", seniority="senior"),
]


@pytest.fixture
def fixture_corpus(monkeypatch):
    """Replace only the corpus loader; all retrieval logic stays real."""
    from src.rag import corpus_store, lexical_retriever, query_engine, query_filters

    corpus_store.reset_job_corpus_cache()
    # Both modules bind the loader at import time, so both bindings are replaced.
    monkeypatch.setattr(corpus_store, "_load_job_corpus", lambda: CORPUS)
    monkeypatch.setattr(lexical_retriever, "_load_job_corpus", lambda: CORPUS)

    # Pin the semantic lane to its real default state (disabled) on the binding
    # query_engine actually calls, so these tests never depend on optional
    # embedding dependencies being importable.
    def _unavailable(*_args, **_kwargs):
        raise RuntimeError("Legacy filesystem RAG index is disabled")

    monkeypatch.setattr(query_engine, "retrieve_jobs", _unavailable)

    monkeypatch.setattr(query_filters, "_build_metadata_catalog", lambda: {
        "companies": {"capital one": "Capital One", "walmart": "Walmart", "stripe": "Stripe"},
        "sources": {"greenhouse": "greenhouse"},
        "titles": {},
        "role_families": {"backend": "backend", "data": "data", "ml": "ml"},
        "seniorities": {"senior": "senior", "mid": "mid"},
        "locations": {"remote": "Remote", "virginia": "Virginia"},
    })
    yield
    corpus_store.reset_job_corpus_cache()


def _evidence_for(request: str):
    """Run the real assistant path and return (intent, evidence_rows)."""
    from src.app.services import route_assistant_intent
    from src.rag.lexical_retriever import _lexical_search
    from src.rag.query_engine import search_jobs
    from src.rag.query_filters import _infer_metadata_filters

    intent = route_assistant_intent(request)["intent"]
    if intent == "answer_job_query":
        return intent, search_jobs(query=request, top_k=5, fetch_k=10)

    filters = _infer_metadata_filters(request)
    return intent, _lexical_search(query=request, top_k=15, filters=filters or None)[:5]


# --- A/B/C: search categories -------------------------------------------------

@pytest.mark.parametrize("request_text", [
    "Show backend engineering roles",
    "Show data engineering roles",
    "Show Java developer jobs",
    "Show machine learning roles",
])
def test_role_search_returns_job_evidence(fixture_corpus, request_text):
    intent, rows = _evidence_for(request_text)
    assert intent == "search_jobs", f"{request_text} should stay deterministic search"
    assert rows, f"{request_text} returned no job evidence"


@pytest.mark.parametrize("request_text", [
    "Show postings mentioning AWS",
    "Which jobs mention Java?",
    "Find jobs requiring Python",
    "Which postings ask for Spring Boot?",
])
def test_technology_search_returns_job_evidence(fixture_corpus, request_text):
    _intent, rows = _evidence_for(request_text)
    assert rows, f"{request_text} returned no job evidence"


@pytest.mark.parametrize("request_text", [
    "Show jobs at Capital One",
    "What roles are available at Walmart?",
    "Show jobs in Virginia",
    "Show remote roles",
])
def test_company_and_location_search_returns_job_evidence(fixture_corpus, request_text):
    _intent, rows = _evidence_for(request_text)
    assert rows, f"{request_text} returned no job evidence"


# --- D: corpus overview -------------------------------------------------------

@pytest.mark.parametrize("request_text", [
    "What kinds of roles are available?",
    "Which companies are hiring?",
    "What skills appear most often?",
    "What technologies are common in the current postings?",
])
def test_corpus_overview_questions_receive_bounded_evidence(fixture_corpus, request_text):
    from src.rag.query_engine import CORPUS_OVERVIEW_EVIDENCE_LIMIT

    intent, rows = _evidence_for(request_text)
    assert intent == "answer_job_query"
    assert rows, f"{request_text} produced no corpus evidence"
    assert len(rows) <= CORPUS_OVERVIEW_EVIDENCE_LIMIT
    # Evidence must be real corpus documents, never synthesized.
    corpus_ids = {d["doc_id"] for d in CORPUS}
    assert {row["doc_id"] for row in rows} <= corpus_ids


def test_corpus_overview_detector_is_conservative():
    from src.rag.query_engine import _is_corpus_overview_query

    assert _is_corpus_overview_query("Which companies are hiring?")
    assert _is_corpus_overview_query("What skills appear most often?")
    # Narrow searches must not be treated as corpus overviews.
    assert not _is_corpus_overview_query("Show backend engineering roles")
    assert not _is_corpus_overview_query("Show jobs at Capital One")
    assert not _is_corpus_overview_query("")


def test_corpus_overview_fallback_is_bounded_and_ordered(fixture_corpus):
    from src.rag.lexical_retriever import _corpus_overview_results

    rows = _corpus_overview_results(top_k=3)
    assert len(rows) == 3
    assert all(row["metadata"]["doc_id"] for row in rows)


# --- E: comparison ------------------------------------------------------------

@pytest.mark.parametrize("request_text", [
    "Compare Java and Python requirements in available postings",
    "Compare backend and data engineering roles",
    "How do AWS requirements differ across these jobs?",
])
def test_comparison_questions_retrieve_evidence(fixture_corpus, request_text):
    intent, rows = _evidence_for(request_text)
    assert intent == "answer_job_query"
    assert rows, f"{request_text} produced no comparison evidence"


def test_gate_sizes_requirement_from_content_terms_only():
    from src.rag.retrieval_ranker import _content_query_terms, _required_overlap_count

    terms = ["compare", "java", "python", "available", "postings"]
    assert _content_query_terms(terms) == ["java", "python"]
    # Scaffolding must not inflate the requirement past what a posting can match.
    assert _required_overlap_count(terms) == 1
    # A query made only of substantive terms keeps its original strictness.
    assert _required_overlap_count(["java", "python", "kafka", "spark", "airflow"]) == 3


# --- NO MATCH: safety ---------------------------------------------------------

@pytest.mark.parametrize("request_text", [
    "Show postings requiring COBOL on mainframe Fortran",
    "Which jobs require Haskell and Erlang telephony switching?",
])
def test_genuinely_absent_technology_returns_no_evidence(fixture_corpus, request_text):
    _intent, rows = _evidence_for(request_text)
    assert rows == [], f"{request_text} must not fabricate evidence"


# --- Owner safety -------------------------------------------------------------

def test_authenticated_owner_still_propagates_through_chat_overlay(monkeypatch):
    from src.app import services

    seen = []

    def fake_overlay(rows, owner_user_id=""):
        seen.append(owner_user_id)
        return rows

    monkeypatch.setattr(services, "_overlay_application_actions", fake_overlay)
    monkeypatch.setattr(
        services, "route_assistant_intent",
        lambda _r: {"intent": "answer_job_query", "reason": "test"},
    )
    from src.rag import rag_executor

    monkeypatch.setattr(
        rag_executor, "execute_rag_request",
        lambda **_kw: {"ok": True, "response": {"answer": "a", "sources": [], "job_evidence": []}},
    )

    services.assistant_query_payload("Which jobs require Python?", owner_user_id=" owner-z ")
    assert seen == ["owner-z", "owner-z"]


# --- Provider failure stays distinct from insufficient evidence ---------------

def test_provider_failure_answer_is_distinct_from_no_match_answer():
    from src.rag.rag_answerer import _no_matching_jobs_answer

    no_match = _no_matching_jobs_answer()
    provider_failure = (
        "I could not answer this because grounded answer generation failed: "
        "grounded_rag_owner_execution_unavailable"
    )

    assert no_match != provider_failure
    # The frontend classifier keys off this marker; it must not appear in the
    # genuine no-match answer or the two states would be conflated.
    assert "grounded answer generation failed" not in no_match
    assert "grounded answer generation failed" in provider_failure


# --- Corpus freshness ---------------------------------------------------------

def test_corpus_cache_expires_on_existing_rag_ttl(monkeypatch):
    from src.rag import corpus_store

    corpus_store.reset_job_corpus_cache()
    loads = {"n": 0}

    def fake_documents(*_args, **_kwargs):
        loads["n"] += 1
        return [dict(CORPUS[0])]

    monkeypatch.setattr(corpus_store, "get_rag_job_documents", fake_documents)
    monkeypatch.setattr(corpus_store, "_rag_cache_ttl_seconds", lambda: 120)

    clock = {"t": 1000.0}
    monkeypatch.setattr(corpus_store.time, "monotonic", lambda: clock["t"])

    corpus_store._load_job_corpus()
    corpus_store._load_job_corpus()
    assert loads["n"] == 1, "corpus must stay cached within the TTL"

    # Past the TTL the in-process cache refreshes instead of serving forever.
    clock["t"] += 121.0
    corpus_store._load_job_corpus()
    assert loads["n"] == 2

    corpus_store.reset_job_corpus_cache()
