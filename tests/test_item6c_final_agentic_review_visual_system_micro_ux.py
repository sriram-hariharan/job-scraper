from __future__ import annotations

from pathlib import Path

from tests.test_item6b5_contextual_actions_manual_preview_integration import _run_node


ROOT = Path(__file__).resolve().parents[1]
PROFILE_UI_PATH = ROOT / "src/app/profile_ui.py"
REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"
REVIEW_CSS_PATH = ROOT / "src/app/static/agentic_review.css"


def _profile() -> str:
    return PROFILE_UI_PATH.read_text(encoding="utf-8")


def _source() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _polish_css() -> str:
    css = REVIEW_CSS_PATH.read_text(encoding="utf-8")
    return css[css.index("/* Item 6C:") :]


def _css_rule(css: str, selector: str) -> str:
    start = css.index(selector)
    return css[start : css.index("}", start) + 1]


def test_locked_review_advanced_and_master_detail_architecture_is_preserved():
    profile = _profile()
    source = _source()

    primary_nav = profile[
        profile.index('<nav class="agentic-review-tabs"') :
        profile.index("</nav>", profile.index('<nav class="agentic-review-tabs"'))
    ]
    assert primary_nav.count("data-agentic-tab-target=") == 2
    assert '>Review</button>' in primary_nav
    assert '>Advanced</button>' in primary_nav
    assert 'id="agenticReviewAdvisoryTab"' in profile
    assert 'id="agenticReviewQueuePanel"' in profile
    assert 'id="agenticReviewSelectedJobPanel"' in profile

    for panel_id in (
        "agenticReviewOverviewTab",
        "agenticReviewTraceTab",
        "agenticReviewDiagnosticsTab",
        "agenticReviewSourceViewsPanel",
    ):
        assert f'id="{panel_id}"' in profile

    for contract in (
        'class="agent-trace-master-detail"',
        'class="agent-trace-master"',
        'class="agent-trace-detail"',
        'class="agent-trace-diagnostic-workspace"',
        'id="agenticReviewDiagnosticMasterList"',
        'id="agenticReviewDiagnosticDetail"',
    ):
        assert contract in source


def test_search_filter_scroll_and_keyboard_editing_contracts_remain_intact():
    profile = _profile()
    source = _source()
    full_css = REVIEW_CSS_PATH.read_text(encoding="utf-8")
    css = _polish_css()

    assert 'id="agenticReviewQueueFilter"' in profile
    assert 'id="agenticReviewQueueSearch" type="search"' in profile
    assert 'class="agentic-review-queue-panel agentic-review-queue-scroll-region"' in profile
    assert 'agenticReviewQueueState.searchQuery = String(searchQuery || "")' in source
    assert 'String(searchQuery || "").trim().toLowerCase()' in source
    assert "title.includes(normalizedQuery) || company.includes(normalizedQuery)" in source
    assert "machineLane === normalizedLane" in source
    assert ".agentic-review-queue-scroll-region" in full_css
    assert "scrollbar-gutter: stable" in full_css
    assert "overflow: visible" in _css_rule(css, ".agentic-review-page .agentic-review-tabs {")


def test_preview_states_are_mutually_coherent_and_keep_existing_gates():
    result = _run_node(
        """
const record = hooks.consolidateAgenticReviewRows([], [{
  job_id: "job-a",
  title: "Engineer",
  company: "Acme",
  tailoring_decision: "tailor_before_apply",
}], [])[0];
vm.runInContext('manualProviderPreviewState.readiness = "eligible";', context);
const ready = hooks.renderAgenticReviewNextStep(record);
vm.runInContext('manualProviderPreviewState.results.set("job-a", { kind: "error", category: "activation_disabled" });', context);
const unavailable = hooks.renderAgenticReviewNextStep(record);
vm.runInContext('manualProviderPreviewState.results.set("job-a", { kind: "error", category: "provider_failure" });', context);
const failed = hooks.renderAgenticReviewNextStep(record);
vm.runInContext(`manualProviderPreviewState.results.set("job-a", {
  kind: "success",
  preview: {
    provider: "synthetic",
    model: "qualified-model",
    suggestions: [{
      previewText: "Grounded suggestion.",
      rationale: "Grounded rationale.",
      evidenceIds: ["evidence-1"],
      riskFlags: [],
    }],
  },
});`, context);
const complete = hooks.renderAgenticReviewNextStep(record);
vm.runInContext('manualProviderPreviewState.results.delete("job-a"); manualProviderPreviewState.inFlight = true; manualProviderPreviewState.pendingJobId = "job-a";', context);
const generating = hooks.renderAgenticReviewNextStep(record);
console.log(JSON.stringify({ ready, unavailable, failed, complete, generating, fetchCalls }));
"""
    )

    assert "Ready for manual preview" in result["ready"]
    assert "Generate AI Preview" in result["ready"]
    assert "disabled" not in result["ready"]

    assert "Ready for manual preview" not in result["unavailable"]
    assert "Preview unavailable" in result["unavailable"]
    assert "AI preview unavailable" in result["unavailable"]
    assert "disabled" in result["unavailable"]

    assert "Ready for manual preview" not in result["failed"]
    assert "Preview failed — retry manually" in result["failed"]
    assert "Retry AI Preview" in result["failed"]
    assert "disabled" not in result["failed"]

    assert "Ready for manual preview" not in result["complete"]
    assert "Preview generated" in result["complete"]
    assert "Generate another preview" in result["complete"]
    assert "AI tailoring suggestions" in result["complete"]

    assert "Generating preview…" in result["generating"]
    assert "disabled" in result["generating"]
    assert result["fetchCalls"] == 0


def test_navigation_queue_and_action_visual_contracts_defeat_global_cta_styles():
    css = _polish_css()

    primary = _css_rule(css, ".agentic-review-page .agentic-review-tabs {")
    assert "width: fit-content" in primary
    assert "overflow: visible" in primary
    assert "scrollbar-width: none" in primary

    advanced = _css_rule(css, "#agenticReviewAdvancedTab .agentic-review-advanced-tab {")
    assert "background: transparent !important" in advanced
    assert "background-image: none !important" in advanced
    assert "linear-gradient" not in advanced
    assert "box-shadow: none !important" in advanced

    selected_queue = _css_rule(css, "#agenticReviewQueuePanel .agentic-review-queue-item.is-selected {")
    assert "linear-gradient" not in selected_queue
    assert "var(--app-primary) 7%" in selected_queue

    manual_action = _css_rule(
        css,
        "body .agentic-review-page .agentic-feedback-action:not(.manual-provider-preview-action) {",
    )
    assert "background-image: none !important" in manual_action
    assert "linear-gradient" not in manual_action
    assert "border-radius: 8px !important" in manual_action


def test_diagnostic_visual_identity_selection_and_single_detail_contract_remain():
    source = _source()
    css = _polish_css()

    assert "function renderAgentTraceDiagnosticIcon" in source
    assert 'class="agent-trace-diagnostic-item__icon"' in source
    assert 'class="agent-trace-diagnostic-detail__icon"' in source
    assert 'class="agent-trace-diagnostic-item ${isSelected ? "is-selected" : ""}"' in source
    assert 'aria-pressed="${isSelected ? "true" : "false"}"' in source
    assert "renderAgentTraceDiagnosticDetail(selectedItem)" in source

    assert ".agent-trace-diagnostic-workspace" in css
    assert ".agent-trace-diagnostic-item__icon svg" in css
    assert "stroke-width: 1.8" in css
    assert ".agent-trace-master-list::-webkit-scrollbar-thumb" in css


def test_presentation_only_safety_boundary_is_unchanged():
    source = _source()
    queue_start = source.index("const AGENTIC_REVIEW_QUEUE_GROUPS")
    queue_end = source.index("function renderAgenticReviewRows", queue_start)
    queue_workspace = source[queue_start:queue_end]
    action_start = source.index("function renderManualProviderPreviewAction")
    action_end = source.index("function safeManualProviderPreviewStringList", action_start)
    preview_action = source[action_start:action_end]

    assert source.count("/api/manual-generate-ai-tailoring-preview-live") == 1
    assert "fetch(" not in preview_action
    assert "window.fetch" not in queue_workspace
    assert "fetchJson(" not in queue_workspace
    assert "/application-actions" not in source
    assert "localStorage" not in queue_workspace
    assert "consensus" not in queue_workspace.lower()
    assert "agents aligned" not in queue_workspace.lower()
    assert "ats submission" not in queue_workspace.lower()
    assert "recruiter messaging" not in queue_workspace.lower()
