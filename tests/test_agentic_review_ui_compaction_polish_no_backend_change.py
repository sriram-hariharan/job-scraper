from hashlib import sha256
from pathlib import Path


REVIEW_JS_PATH = Path("src/app/static/agentic_review.js")
CSS_PATH = Path("src/app/static/app_redesign.css")
DOC_PATH = Path("docs/agentic_review_ui_compaction_polish_no_backend_change.md")
ORCHESTRATOR_READINESS_DOC_PATH = Path("docs/orchestrator_readiness.md")

PROTECTED_FILE_HASHES = {
    "src/app/api.py": "65975190cebecd5cefc179be1d71c4cbe7b3214ed9c7b3691d6cc7877f7db6e3",
    "src/storage/agent_state/store.py": "3bd4d72496693c5a9391ff0ff5e3fb229b6c58df23a520113981eba0f96288cc",
    "src/storage/agent_state/schema.sql": "d7e91c2b7e6e7720a8aeb64b7292d9ce28d6008b14c1d149f56a6c1fa39b3526",
    "src/storage/agent_state/migration_runner.py": "488e25670d7043c6a5b938441e13d7c066bbcf5fccda1a41401723650e61969e",
    "src/storage/agentic_approvals/store.py": "9cd153ba1bdcac520c1ea0d3b04374671e8ace6c2635a60fce2544526201f5bf",
    "src/storage/agentic_approvals/schema.sql": "57e84094cdbd3a4e8542fd205d89bfde18179c5d07c15084354f31f77bf5d98f",
    "src/agents/workflow_runner.py": "bbdaf6d1dcc829809de6ee62a864ef5048a73ef63c288173f676a42ca1e6cd05",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _review_js() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _css() -> str:
    return CSS_PATH.read_text(encoding="utf-8")


def _trace_panel_snippet() -> str:
    source = _review_js()
    start = source.index("function renderAgentTraceReadOnlyDetails")
    end = source.index("async function refreshAgenticReviewFeedbackSummary")
    return source[start:end]


def _trace_fetch_snippet() -> str:
    source = _review_js()
    start = source.index("async function fetchAgentTraceReadOnlyPayload")
    end = source.index("async function refreshAgenticReviewFeedbackSummary")
    return source[start:end]


def test_step_206a_backend_storage_pipeline_and_execution_files_are_unchanged():
    for path, expected_hash in PROTECTED_FILE_HASHES.items():
        assert Path(path).exists(), path
        assert sha256(Path(path).read_bytes()).hexdigest() == expected_hash, path


def test_no_critic_evaluator_readonly_frontend_auto_call_or_hidden_llm_call():
    source = _review_js()
    init_start = source.index("async function initAgenticReviewPage")
    init_snippet = source[init_start : source.index('window.addEventListener("DOMContentLoaded", initAgenticReviewPage);')]

    assert source.count("/critic-evaluator-readonly") == 1
    assert source.count("data-agentic-critic-evaluator-readonly") == 2
    assert "data-agentic-critic-evaluator-readonly" in source
    assert "critic-evaluator-readonly" not in _trace_fetch_snippet()
    assert "critic-evaluator-readonly" not in init_snippet
    assert "Running read-only critic evaluator" in source
    assert "Manual, non-actionable trace review." in source
    for marker in [
        "run_llm",
        "model_client",
        "llm_provider",
        "openai.chat",
        "responses.create",
        "chat.completions.create",
    ]:
        assert marker not in source


def test_agent_trace_debug_details_are_present_collapsed_and_get_only():
    snippet = _trace_panel_snippet()
    fetch_snippet = _trace_fetch_snippet()
    debug_index = snippet.index("agent-trace-debug-details")
    debug_snippet = snippet[debug_index : snippet.index("</details>", debug_index)]

    assert "Debug details" in debug_snippet
    assert 'data-collapsed-by-default="true"' in debug_snippet
    assert " open" not in debug_snippet
    assert 'renderWorkflowSummaryMetric("Found"' in debug_snippet
    assert 'renderWorkflowSummaryMetric("Empty trace"' in debug_snippet
    assert 'renderWorkflowSummaryMetric("Read-only"' in debug_snippet

    trace_state_index = snippet.index('renderWorkflowSummaryMetric("Trace state"')
    primary_counts = snippet[trace_state_index:debug_index]
    for marker in ("shadow-sidecar-trace-readback", "shadow_sidecar_trace_readback"):
        if marker in primary_counts:
            primary_counts = primary_counts[: primary_counts.index(marker)]
            break
    assert 'renderWorkflowSummaryMetric("Trace state"' in primary_counts
    assert 'renderWorkflowSummaryMetric("Found"' not in primary_counts
    assert 'renderWorkflowSummaryMetric("Empty trace"' not in primary_counts
    assert 'renderWorkflowSummaryMetric("Read-only"' not in primary_counts

    assert "/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/agent-trace" in fetch_snippet
    assert "/profile/pipeline-runs/${encodeURIComponent(runId)}/agent-trace" in fetch_snippet
    for marker in ['method: "POST"', "method: 'POST'", 'method: "PUT"', 'method: "PATCH"', 'method: "DELETE"']:
        assert marker not in fetch_snippet


def test_optional_diagnostics_and_markdown_summaries_are_collapsed_by_default():
    source = _review_js()

    optional_index = source.index("agentic-review-optional-diagnostics")
    optional_snippet = source[optional_index : source.index("</details>", optional_index)]
    assert "Optional diagnostics not recorded" in optional_snippet
    assert "These optional diagnostics do not affect planning results." in optional_snippet
    assert 'data-collapsed-by-default="true"' in optional_snippet
    assert " open" not in optional_snippet

    assert "function renderAgenticWorkflowMarkdownSummary" in source
    assert "Markdown summary" in source
    assert "agentic-workflow-markdown-summary" in source
    assert 'data-collapsed-by-default="true"' in source[source.index("agentic-workflow-markdown-summary") :]
    assert "<details open" not in source


def test_css_includes_compact_collapsed_details_and_chat_safe_spacing():
    css = _css()

    assert "[data-agentic-review-run-id]" in css
    assert "padding-right: clamp(18px, 8vw, 132px)" in css
    assert "padding-bottom: clamp(168px, 18vh, 240px)" in css
    assert ".agentic-review-optional-diagnostics:not([open])" in css
    assert ".agent-trace-debug-details:not([open])" in css
    assert ".agentic-workflow-markdown:not([open])" in css
    assert ".agentic-workflow-markdown-summary" in css
    assert "max-height: 48px" in css


def test_compaction_polish_doc_and_orchestrator_link_cover_required_terms():
    assert DOC_PATH.exists()
    doc = DOC_PATH.read_text(encoding="utf-8")
    readiness = ORCHESTRATOR_READINESS_DOC_PATH.read_text(encoding="utf-8")

    for term in [
        "Agentic Review UI compaction polish",
        "UI-only",
        "no backend change",
        "no API change",
        "no storage change",
        "no pipeline change",
        "no scheduler change",
        "no application execution",
        "no application submission",
        "no approval mutation",
        "no scoring change",
        "no ranking change",
        "no live LLM call",
        "no model provider call",
        "read-only Agent Trace",
        "GET only",
        "Debug details collapsed by default",
        "Optional diagnostics not recorded collapsed by default",
        "Markdown summary collapsed by default",
        "floating chat safe spacing",
        "portfolio demo readability",
        "verification plan",
        "rollback plan",
    ]:
        assert term in doc

    assert "docs/agentic_review_ui_compaction_polish_no_backend_change.md" in readiness
