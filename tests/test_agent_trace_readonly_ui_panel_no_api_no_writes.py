from hashlib import sha256
from pathlib import Path


REVIEW_JS_PATH = Path("src/app/static/agentic_review.js")
DOC_PATH = Path("docs/agent_trace_readonly_ui_panel_no_api_no_writes.md")

PROTECTED_FILE_HASHES = {
    # src/app/api.py is intentionally not hash-pinned here after later approved read-only API endpoint steps.
    "src/storage/agent_state/store.py": "3bd4d72496693c5a9391ff0ff5e3fb229b6c58df23a520113981eba0f96288cc",
    "src/storage/agent_state/schema.sql": "d7e91c2b7e6e7720a8aeb64b7292d9ce28d6008b14c1d149f56a6c1fa39b3526",
    "src/storage/agent_state/migration_runner.py": "488e25670d7043c6a5b938441e13d7c066bbcf5fccda1a41401723650e61969e",
    "src/storage/agentic_approvals/store.py": "9cd153ba1bdcac520c1ea0d3b04374671e8ace6c2635a60fce2544526201f5bf",
    "src/storage/agentic_approvals/schema.sql": "57e84094cdbd3a4e8542fd205d89bfde18179c5d07c15084354f31f77bf5d98f",
    "src/agents/trace.py": "595e4cfdde253bb42013a9b684bd7be69d0e53eaf5fcddbe0a788b13bb0f8df2",
    "src/agents/agent_state.py": "6daaa56b2af95e36547e89e928c354038b5bab6ff2cc35e49bf259d0d9d1cdac",
    "src/agents/relevance_prefilter.py": "36703c0c3d24b61a70f09cafd77c243ca253407fc439dc5fd4aa1851577371ea",
    "src/agents/deduplication.py": "a338326a2a4092c2b9a3bac0d1381d5e2b5a83cc35892d92f1870ae448dbe878",
    "src/agents/jd_intelligence.py": "a8ac3f59c089326dfbeff7d70b4fcae05e22c7e67e9deb58013dffb84deaf6c5",
    "src/agents/final_application_scoring.py": "3a6d1a800bc728fa24992396ef1a30ac994deedd86a82f07d36aa0eebb28088d",
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


def test_agent_trace_readonly_panel_is_present_and_display_only():
    snippet = _trace_panel_snippet()

    assert "function renderAgentTraceReadOnlyPanel" in snippet
    assert "data-agent-trace-read-only-panel" in snippet
    assert "Read-only trace panel" in snippet
    assert "GET only" in snippet
    assert "ordered agent steps" in snippet
    assert "No persisted trace found for this run" in snippet
    assert "The trace panel is read-only and will show ordered agent steps when trace records are available." in snippet
    assert "Empty trace: agent run metadata is available" in snippet
    assert "No ordered agent steps returned for this trace." in snippet
    assert "Safety metadata" in snippet
    assert "validation_json" in snippet
    assert "Fetch failure:" in snippet
    assert "Read-only display preserved." in snippet
    assert "<button" not in snippet


def test_agent_trace_readonly_panel_uses_get_only_existing_endpoint():
    fetch_snippet = _trace_fetch_snippet()
    init_snippet = _init_snippet()

    assert "/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/agent-trace" in fetch_snippet
    assert "/profile/pipeline-runs/${encodeURIComponent(runId)}/agent-trace" in fetch_snippet
    assert "fetchAgentTraceReadOnlyPayload(payload, runId)" in init_snippet
    assert "renderAgentTraceReadOnlyPanel(tracePayload || {})" in _source()

    forbidden_methods = [
        'method: "POST"',
        "method: 'POST'",
        'method: "PUT"',
        "method: 'PUT'",
        'method: "PATCH"',
        "method: 'PATCH'",
        'method: "DELETE"',
        "method: 'DELETE'",
    ]
    for marker in forbidden_methods:
        assert marker not in fetch_snippet
        assert marker not in init_snippet


def test_agent_trace_readonly_panel_does_not_add_trace_actions():
    snippet = _trace_panel_snippet()
    forbidden_markers = [
        "data-agentic-approval-decision",
        "data-agentic-submit",
        "data-agentic-run",
        "data-agentic-retry",
        "data-agentic-export",
        "FileResponse",
        "StreamingResponse",
        "write_text",
        "write_bytes",
        "background_tasks.add_task",
        "subprocess",
    ]

    for marker in forbidden_markers:
        assert marker not in snippet


def test_agent_trace_readonly_ui_doc_contains_required_contract():
    doc = DOC_PATH.read_text()
    required_terms = [
        "Agent Trace read-only UI panel",
        "no API changes",
        "no storage changes",
        "no storage writes",
        "no schema migration",
        "no pipeline wiring",
        "no scheduler",
        "no background task",
        "no file export",
        "no application execution",
        "no application submission",
        "no live LLM call",
        "no approval mutation",
        "ordered agent steps",
        "empty trace",
        "not found trace",
        "safety metadata",
        "validation_json",
        "no approve",
        "no apply",
        "no submit",
        "no run",
        "no retry",
        "no export",
        "deterministic",
    ]

    for term in required_terms:
        assert term in doc


def test_protected_backend_storage_runtime_files_are_unchanged():
    for path, expected_hash in PROTECTED_FILE_HASHES.items():
        assert Path(path).exists(), path
        assert sha256(Path(path).read_bytes()).hexdigest() == expected_hash, path
