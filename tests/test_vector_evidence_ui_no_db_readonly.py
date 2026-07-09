# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
# phase26b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
from hashlib import sha256
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"
ENDPOINT = "/api/vector-evidence"


def _source() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _request_snippet() -> str:
    source = _source()
    start = source.index("function vectorEvidenceRequestPayload")
    end = source.index("function renderVectorEvidenceSnippets", start)
    return source[start:end]


def _section_snippet() -> str:
    source = _source()
    start = source.index("function renderVectorEvidenceSnippets")
    end = source.index("function renderHumanReviewedInfluencePreviewSection", start)
    return source[start:end]


def _handler_snippet() -> str:
    source = _source()
    start = source.index(
        'event.target.closest("[data-vector-evidence-retrieve]")'
    )
    end = source.index(
        'event.target.closest("[data-manual-shadow-recommendation-handoff-dry-run]")',
        start,
    )
    return source[start:end]


def _init_snippet() -> str:
    source = _source()
    start = source.index("async function initAgenticReviewPage")
    end = source.index(
        'window.addEventListener("DOMContentLoaded", initAgenticReviewPage);'
    )
    return source[start:end]


def test_ui_includes_vector_evidence_fetch_and_display_hook():
    source = _source()
    section = _section_snippet()
    handler = _handler_snippet()

    assert "function renderVectorEvidenceSection" in source
    assert "Vector Evidence" in section
    assert "data-vector-evidence-query" in section
    assert "data-vector-evidence-retrieve" in section
    assert "Retrieve Evidence" in section
    assert "renderVectorEvidenceSection(tracePayload)" in source
    assert ENDPOINT in handler
    assert 'method: "POST"' in handler
    assert "vectorEvidenceRequestPayload" in handler
    assert "vector_evidence_result" in handler


def test_ui_builds_request_from_existing_readonly_evidence_payloads():
    snippet = _request_snippet()

    for phrase in (
        "query_text",
        "job_payload",
        "job_description_payload",
        "resume_profile_payload",
        "trace_evidence_payload",
        "operator_review_packet_payload",
        "top_k",
        "trace_evidence_pack",
        "pipeline_generated_overlay_review_packet_result",
    ):
        assert phrase in snippet

    assert "fetchJson" not in snippet
    assert "setInterval" not in snippet


def test_ui_displays_retrieval_status_and_summaries():
    snippet = _section_snippet()

    assert 'renderWorkflowSummaryMetric("Retrieval status", status)' in snippet
    assert "indexing_summary" in snippet
    assert "retrieval_summary" in snippet
    assert 'renderAgentTraceReadOnlyDetails("Indexing summary"' in snippet
    assert 'renderAgentTraceReadOnlyDetails("Retrieval summary"' in snippet


def test_ui_displays_matched_chunk_count_types_and_evidence_snippets():
    snippet = _section_snippet()

    assert 'renderWorkflowSummaryMetric("Matched chunks", matchedChunks.length)' in snippet
    assert 'renderWorkflowSummaryMetric("Matched types"' in snippet
    assert "matched_chunks" in snippet
    assert "matchedChunkTypes" in snippet
    assert "renderVectorEvidenceSnippets(matchedChunks)" in snippet
    assert "Top matched vector evidence snippets" in snippet
    assert "evidence_text" in snippet


def test_ui_displays_skipped_reasons_and_collapses_raw_details():
    snippet = _section_snippet()

    assert 'renderAgentTraceReadOnlyDetails("Skipped reasons"' in snippet
    assert "data-collapsed-by-default" in _source()
    assert "<details" not in snippet
    assert "<pre>" not in snippet


def test_ui_displays_safe_missing_query_and_no_result_states():
    snippet = _section_snippet()

    assert "vector_evidence_service_invalid_query" in snippet
    assert "Enter a query" in snippet
    assert "No result was produced and no state was changed" in snippet
    assert "vector_evidence_service_no_chunks" in snippet
    assert "No usable evidence chunks are available" in snippet
    assert "vector_evidence_service_no_results" in snippet
    assert "No evidence matched this query" in snippet
    assert "Continue without retrieval influence" in snippet


def test_ui_labels_output_readonly_advisory_and_no_external_calls():
    snippet = _section_snippet()

    for phrase in (
        "Advisory read-only",
        "Read-only and advisory only",
        "Embeddings created",
        "Vector DB connected",
        "Provider calls",
        "no embeddings are created",
        "no vector database is connected",
        "no provider is called",
        "Scoring/ranking mutation",
        "Queue/application mutation",
        "No embeddings, vector DB, provider calls, or application mutations",
    ):
        assert phrase in snippet


def test_ui_adds_no_score_ranking_queue_approval_resume_or_execution_controls():
    combined = (_section_snippet() + "\n" + _handler_snippet()).lower()
    forbidden = (
        "data-scoring-override",
        "data-ranking-override",
        "data-queue",
        "data-approve",
        "data-reject",
        "data-resume",
        "data-execute",
        "data-submit",
        "setagenticapprovalstatus",
        "approve-application",
        "submit-application",
        "execute-application",
        "/api/manual-approval",
        "/api/manual-queue",
        "/api/manual-execution",
        "create_approval_request(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
    )
    for marker in forbidden:
        assert marker not in combined


def test_ui_calls_api_only_from_explicit_operator_action_without_auto_refresh():
    handler = _handler_snippet()
    init_snippet = _init_snippet()

    assert ENDPOINT in handler
    assert ENDPOINT not in init_snippet
    assert "setInterval" not in handler
    assert "setInterval" not in init_snippet
    assert "setTimeout" in handler


def test_no_api_service_pipeline_schema_or_dependency_change():
    protected_hashes = {
        "src/app/api.py": (
            "d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004"
        ),
        "src/pipeline/collector.py": (
            "1d35d00e54d1d858134b2e524955887bd7adbbce3a01e53d1782debc4584490a"
        ),
        "requirements.txt": (
            "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"
        ),
        "src/storage/agent_trace/schema.sql": (
            "69305cd1bec0be9caa8c8c1b93e8fc10a3e80a92c08acd5683e7800763d2a77a"
        ),
        "src/storage/agentic_approvals/schema.sql": (
            "57e84094cdbd3a4e8542fd205d89bfde18179c5d07c15084354f31f77bf5d98f"
        ),
        "src/storage/profile_resumes/schema.sql": (
            "a71d55d9306258661b99f9bc88aa122fbf24443e7bd43a9ba597133289df1e57"
        ),
    }
    for relative_path, expected_hash in protected_hashes.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_ui_has_no_embedding_vector_db_or_provider_implementation():
    combined = _request_snippet() + "\n" + _handler_snippet()

    for marker in (
        "create_embedding(",
        "embeddings.create(",
        "vector_db.connect(",
        "pinecone",
        "chromadb",
        "faiss",
        "openai",
        "anthropic",
        "llm_client",
        "responses.create",
        "chat.completions.create",
    ):
        assert marker not in combined.lower()
