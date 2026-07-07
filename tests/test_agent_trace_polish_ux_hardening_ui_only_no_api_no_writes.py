from hashlib import sha256
from pathlib import Path


REVIEW_JS_PATH = Path("src/app/static/agentic_review.js")
DOC_PATH = Path("docs/agent_trace_polish_ux_hardening_ui_only_no_api_no_writes.md")

PROTECTED_FILE_HASHES = {
    # src/app/api.py is intentionally not hash-pinned here after later approved read-only API endpoint steps.
    "src/storage/agent_state/store.py": "3bd4d72496693c5a9391ff0ff5e3fb229b6c58df23a520113981eba0f96288cc",
    "src/storage/agent_state/schema.sql": "d7e91c2b7e6e7720a8aeb64b7292d9ce28d6008b14c1d149f56a6c1fa39b3526",
    "src/storage/agent_state/migration_runner.py": "488e25670d7043c6a5b938441e13d7c066bbcf5fccda1a41401723650e61969e",
    "src/storage/agentic_approvals/store.py": "9cd153ba1bdcac520c1ea0d3b04374671e8ace6c2635a60fce2544526201f5bf",
    "src/storage/agentic_approvals/schema.sql": "57e84094cdbd3a4e8542fd205d89bfde18179c5d07c15084354f31f77bf5d98f",
    "src/agents/trace.py": "f4527c224ea0d3fc05d14883bb036311e7120a6a9abc9a54a58396e76ddada41",
    "src/agents/agent_state.py": "6daaa56b2af95e36547e89e928c354038b5bab6ff2cc35e49bf259d0d9d1cdac",
    "src/agents/relevance_prefilter.py": "5be6d21c27b720472daef6f85f813bc6561c90f9f8abfcfc09e88a5cd36a490b",
    "src/agents/deduplication.py": "7aeb6e831197a63f66b83fff898ccef77db177e39594464e1c215cffaed432b8",
    "src/agents/jd_intelligence.py": "f204bf788c2e8c019e3a9dc65e932981ec1081c5386573b956ce1d2dfcd7dd46",
    "src/agents/final_application_scoring.py": "eed7eed337b860345f38005c1f898732c8c809f6087e7fbbf33de6f4ad7ed2fd",
    "src/agents/workflow_runner.py": "bbdaf6d1dcc829809de6ee62a864ef5048a73ef63c288173f676a42ca1e6cd05",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _source() -> str:
    return REVIEW_JS_PATH.read_text()


def _trace_panel_snippet() -> str:
    source = _source()
    start = source.index("function renderAgentTraceReadOnlyDetails")
    end = source.index("async function refreshAgenticReviewFeedbackSummary")
    return source[start:end]


def _trace_fetch_snippet() -> str:
    source = _source()
    start = source.index("async function fetchAgentTraceReadOnlyPayload")
    end = source.index("async function refreshAgenticReviewFeedbackSummary")
    return source[start:end]


def _init_snippet() -> str:
    source = _source()
    start = source.index("async function initAgenticReviewPage")
    end = source.index('window.addEventListener("DOMContentLoaded", initAgenticReviewPage);')
    return source[start:end]


def test_trace_polish_ui_terms_are_present_in_readonly_panel():
    snippet = _trace_panel_snippet()

    for term in [
        "read-only",
        "agent trace",
        "ordered agent steps",
        "empty trace",
        "not found trace",
        "fetch failure",
        "loading state",
        "safety metadata",
        "validation_json",
        "Stage Trace Bundle",
        "stage_trace_bundle",
        "Stage order valid",
        "Missing expected stages",
        "Unexpected stages",
        "Duplicate stages",
        "Stage Trace Health",
        "stage_trace_health",
        "Required fields",
        "Findings",
        "Warnings",
        "Stage Trace Readiness",
        "stage_trace_readiness",
        "Readiness",
        "Reason codes",
        "Blocking findings",
        "Warning findings",
        "Trace Evidence Pack",
        "trace_evidence_pack",
        "Evidence",
        "Available sections",
        "Missing sections",
        "Decision reason codes",
        "Detailed trace sections",
        "Lower-level trace summary, bundle, health, and readiness details remain read-only",
        "Read-only Critic Evaluator",
        "Manual, non-actionable trace review.",
        "data-agentic-critic-evaluator-readonly",
        "collapsed step details",
        "accessibility labels",
        "Long trace readability",
    ]:
        assert term in snippet


def test_trace_polish_fetch_remains_get_only_existing_endpoint():
    fetch_snippet = _trace_fetch_snippet()
    init_snippet = _init_snippet()

    assert "/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/agent-trace" in fetch_snippet
    assert "/profile/pipeline-runs/${encodeURIComponent(runId)}/agent-trace" in fetch_snippet
    assert "include_trace_summary=1" in fetch_snippet
    assert "include_stage_trace_bundle=1" in fetch_snippet
    assert "include_stage_trace_health=1" in fetch_snippet
    assert "include_stage_trace_readiness=1" in fetch_snippet
    assert "include_trace_evidence_pack=1" in fetch_snippet
    assert "/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/agent-trace?include_stage_trace_bundle=1" not in fetch_snippet
    assert "/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/agent-trace?include_stage_trace_health=1" not in fetch_snippet
    assert "/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/agent-trace?include_stage_trace_readiness=1" not in fetch_snippet
    assert "/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/agent-trace?include_trace_evidence_pack=1" not in fetch_snippet
    assert "fetchAgentTraceReadOnlyPayload(payload, runId)" in init_snippet
    assert "loading_state: true" in init_snippet

    for marker in [
        'method: "POST"',
        "method: 'POST'",
        'method: "PUT"',
        "method: 'PUT'",
        'method: "PATCH"',
        "method: 'PATCH'",
        'method: "DELETE"',
        "method: 'DELETE'",
    ]:
        assert marker not in fetch_snippet
        assert marker not in init_snippet


def test_trace_polish_does_not_add_actions_exports_or_llm_behavior():
    snippet = _trace_panel_snippet()
    forbidden_markers = [
        "data-agentic-approval-decision",
        "data-agentic-submit",
        "data-agentic-run",
        "data-agentic-retry",
        "data-agentic-export",
        "download",
        "FileResponse",
        "StreamingResponse",
        "write_text",
        "write_bytes",
        "send_file",
        "background_tasks.add_task",
        "subprocess",
        "run_llm",
        "model_client",
        "llm_provider",
    ]

    for marker in forbidden_markers:
        assert marker not in snippet

    assert snippet.count("data-agentic-critic-evaluator-readonly") == 1


def test_recommendation_explainer_terms_are_present_in_advisory_ui():
    source = _source()

    for term in [
        "function buildRecommendationExplainer",
        "function renderRecommendationExplainer",
        "Why surfaced",
        "agentic-review-recommendation-explainer",
        "Primary reasons",
        "Supporting signals",
        "Risk signals",
        "Missing evidence",
        "Score breakdown",
        "no rescoring is performed",
    ]:
        assert term in source


def test_trace_polish_accessibility_and_collapsed_details_are_present():
    snippet = _trace_panel_snippet()

    assert "aria-label" in snippet
    assert 'role="status"' in snippet
    assert "<details" in snippet
    assert "<summary>" in snippet
    assert "renderAgentTraceReadOnlyDetails" in snippet
    assert "Readable safety metadata display." in snippet
    assert "Readable validation_json display." in snippet


def test_trace_polish_doc_contains_required_contract():
    doc = DOC_PATH.read_text()
    required_terms = [
        "Agent Trace polish / UX hardening UI-only implementation",
        "UI-only",
        "read-only",
        "no API changes",
        "no storage changes",
        "no storage writes",
        "no schema migration",
        "no pipeline wiring",
        "no scheduler",
        "no background task",
        "no file export",
        "no live LLM call",
        "no approval mutation",
        "no application execution",
        "no application submission",
        "loading state",
        "empty trace",
        "not found trace",
        "fetch failure",
        "ordered agent steps",
        "collapsed step details",
        "accessibility labels",
        "safety metadata",
        "validation_json",
        "no approve",
        "no apply",
        "no submit",
        "no run",
        "no retry",
        "no export",
        "deterministic",
        "rollback plan",
        "verification plan",
    ]

    for term in required_terms:
        assert term in doc


def test_protected_backend_storage_runtime_files_are_unchanged():
    for path, expected_hash in PROTECTED_FILE_HASHES.items():
        assert Path(path).exists(), path
        assert sha256(Path(path).read_bytes()).hexdigest() == expected_hash, path
