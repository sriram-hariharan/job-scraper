from hashlib import sha256
from pathlib import Path


REVIEW_JS_PATH = Path("src/app/static/agentic_review.js")
CSS_PATH = Path("src/app/static/app_redesign.css")
DOC_PATH = Path("docs/agentic_review_ui_portfolio_polish_no_backend_change.md")
ORCHESTRATOR_READINESS_DOC_PATH = Path("docs/orchestrator_readiness.md")

PROTECTED_FILE_HASHES = {
    "src/app/api.py": "aa5cd674812a02e7d76afccf807e9cadd2545478507ca6e4a808a1a30518d4f3",
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


def _approval_mock_snippet() -> str:
    source = _review_js()
    start = source.index("function renderApprovalDecisionActionSection")
    end = source.index("function setAgenticApprovalStatus")
    return source[start:end]


def test_step_205a_agentic_review_polish_is_ui_only_and_backend_is_unchanged():
    for path, expected_hash in PROTECTED_FILE_HASHES.items():
        assert Path(path).exists(), path
        assert sha256(Path(path).read_bytes()).hexdigest() == expected_hash, path


def test_agent_trace_copy_is_clean_readonly_get_only_and_debug_values_are_collapsed():
    snippet = _trace_panel_snippet()
    fetch_snippet = _trace_fetch_snippet()

    assert "Read-only trace panel. Uses GET only and never changes approvals, queues, scoring, execution, or submissions." in snippet
    assert "No persisted trace found for this run" in snippet
    assert "will show ordered agent steps when trace records are available" in snippet
    assert "Debug details" in snippet
    assert "agent-trace-debug-details" in snippet
    assert "Read-only trace panel. Read-only agent trace panel." not in snippet
    assert 'renderWorkflowSummaryMetric("Found"' in snippet[snippet.index("Debug details") :]
    assert 'renderWorkflowSummaryMetric("Empty trace"' in snippet[snippet.index("Debug details") :]
    assert 'renderWorkflowSummaryMetric("Read-only"' in snippet[snippet.index("Debug details") :]

    assert "/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}/agent-trace" in fetch_snippet
    assert "/profile/pipeline-runs/${encodeURIComponent(runId)}/agent-trace" in fetch_snippet
    for marker in ['method: "POST"', "method: 'POST'", 'method: "PUT"', 'method: "PATCH"', 'method: "DELETE"']:
        assert marker not in fetch_snippet


def test_no_new_critic_evaluator_readonly_frontend_auto_call_or_hidden_model_call():
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


def test_summary_hierarchy_optional_diagnostics_and_button_groups_are_present():
    source = _review_js()
    approval_snippet = _approval_mock_snippet()

    primary_index = source.index("agentic-review-health-strip--primary")
    secondary_index = source.index("Secondary diagnostics")
    assert primary_index < secondary_index
    for label in [
        "Run status",
        "Verification",
        "Final jobs",
        "Ready to apply",
        "Tailor then apply",
        "Hold / skip",
        "Agent trace",
    ]:
        assert label in source[primary_index:secondary_index]

    assert "Optional diagnostics not recorded" in source
    assert "agentic-review-optional-diagnostics" in source
    assert "agentic-approval-button-group--actions" in approval_snippet
    assert "agentic-approval-button-group--observability" in approval_snippet
    assert approval_snippet.index("agentic-approval-button-group--actions") < approval_snippet.index(
        "agentic-approval-button-group--observability"
    )


def test_css_includes_wrapping_action_groups_and_floating_chat_safe_spacing():
    css = _css()

    assert "[data-agentic-review-run-id]" in css
    assert "padding-bottom: clamp(168px, 18vh, 240px)" in css
    assert ".agentic-feedback-actions" in css
    assert ".agentic-approval-button-group" in css
    assert "flex-wrap: wrap" in css
    assert ".agentic-approval-button-group--actions" in css
    assert ".agentic-approval-button-group--observability" in css
    assert ".agentic-review-optional-diagnostics" in css
    assert ".agent-trace-debug-details" in css


def test_portfolio_polish_doc_and_orchestrator_link_cover_required_terms():
    assert DOC_PATH.exists()
    doc = DOC_PATH.read_text(encoding="utf-8")
    orchestrator_doc = ORCHESTRATOR_READINESS_DOC_PATH.read_text(encoding="utf-8")

    for term in [
        "Agentic Review UI portfolio polish",
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
        "No persisted trace found for this run",
        "Debug details",
        "Optional diagnostics not recorded",
        "button wrapping",
        "floating chat safe spacing",
        "portfolio demo readability",
        "verification plan",
        "rollback plan",
    ]:
        assert term in doc

    assert "docs/agentic_review_ui_portfolio_polish_no_backend_change.md" in orchestrator_doc
