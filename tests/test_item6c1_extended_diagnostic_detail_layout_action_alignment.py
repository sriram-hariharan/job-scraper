from __future__ import annotations

from pathlib import Path

from tests.test_item6b65c_extended_trace_diagnostics_master_detail import (
    EXPECTED_DIAGNOSTIC_RENDERERS,
    _diagnostic_registry,
    _run_node,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILE_UI_PATH = ROOT / "src/app/profile_ui.py"
REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"
REVIEW_CSS_PATH = ROOT / "src/app/static/agentic_review.css"


def _source() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _diagnostic_css() -> str:
    css = REVIEW_CSS_PATH.read_text(encoding="utf-8")
    start = css.index("/* Item 6B6.5C:")
    end = css.index("/* Item 6B3:", start)
    return css[start:end]


def test_selected_title_and_status_badge_have_dedicated_normal_flow_ownership():
    result = _run_node(
        """
const item = {
  key: "long-title",
  title: "A deliberately long selected diagnostic title that must remain fully readable beside its status",
  state: "manual approval gate",
  category: "approval",
  markup: "<article>Existing detail</article>",
};
const markup = hooks.renderAgentTraceDiagnosticDetail(item);
console.log(JSON.stringify({ markup, fetchCalls, manualActionCalls }));
"""
    )
    css = _diagnostic_css()

    assert 'class="agent-trace-diagnostic-detail__heading"' in result["markup"]
    assert "agent-trace-diagnostic-detail__badge" in result["markup"]
    assert "A deliberately long selected diagnostic title" in result["markup"]
    assert "agentic-review-pill agent-trace-diagnostic-detail__badge is-info" in result["markup"]
    assert result["fetchCalls"] == 0
    assert result["manualActionCalls"] == 0

    assert "grid-template-columns: 42px minmax(0, 1fr) auto" in css
    assert ".agent-trace-diagnostic-detail__heading {\n  min-width: 0;" in css
    assert ".agent-trace-diagnostic-detail__badge {" in css
    badge_rule = css[css.index(".agent-trace-diagnostic-detail__badge {") :]
    badge_rule = badge_rule[: badge_rule.index("}") + 1]
    assert "align-self: start" in badge_rule
    assert "justify-self: end" in badge_rule
    assert "white-space: normal" in badge_rule
    assert "position: absolute" not in badge_rule


def test_secondary_titles_and_badges_wrap_without_semantic_label_changes():
    source = _source()
    css = _diagnostic_css()

    for label in (
        "GET readback",
        "Default-off",
        "Manual approval gate",
        "Transition audit",
        "Queue preview",
        "Queue handoff",
    ):
        assert f'<span class="agentic-workflow-badge">{label}</span>' in source

    assert ".agent-trace-diagnostic-detail__content .agentic-workflow-header {" in css
    assert "grid-template-columns: minmax(0, 1fr) auto" in css
    assert ".agent-trace-diagnostic-detail__content .agentic-workflow-header > div" in css
    assert ".agent-trace-diagnostic-detail__content .agentic-workflow-badge" in css
    assert "overflow-wrap: anywhere" in css


def test_manual_actions_and_confirmation_controls_have_separate_layout_regions():
    source = _source()
    css = _diagnostic_css()

    shadow_start = source.index("function renderShadowSidecarTraceReadbackSection")
    shadow_end = source.index("function shadowScoreComparisonRequestPayload", shadow_start)
    shadow = source[shadow_start:shadow_end]
    assert '<div class="agentic-feedback-actions">' in shadow
    assert shadow.index("data-shadow-sidecar-trace-readback ") < shadow.index(
        "data-shadow-sidecar-trace-readback-status"
    )

    approval_start = source.index("function renderHumanReviewedInfluenceApprovalRequestSection")
    approval_end = source.index("function renderAgentTraceDetailedSections", approval_start)
    approval = source[approval_start:approval_end]
    checkbox = approval.index("data-human-reviewed-influence-approval-request-confirmation")
    label_end = approval.index("</label>", checkbox)
    button = approval.index("data-human-reviewed-influence-approval-request ", label_end)
    explanation = approval.index("data-human-reviewed-influence-approval-request-status", button)
    assert checkbox < label_end < button < explanation

    assert ":is(.agentic-feedback-actions, .agentic-review-actions) {" in css
    assert "grid-template-columns: minmax(0, max-content) minmax(0, 1fr)" in css
    assert ".agentic-review-actions > label {" in css
    assert "grid-column: 1 / -1" in css
    assert "> .agentic-feedback-action" in css
    assert "> .agentic-review-muted" in css
    assert "font-weight: 580" in css
    assert "overflow-wrap: anywhere" in css


def test_metric_empty_disclosure_chip_and_action_regions_keep_distinct_spacing():
    source = _source()
    css = _diagnostic_css()
    evidence_start = source.index("function renderEvidenceChainReadbackCard")
    evidence_end = source.index("function renderAgentTraceCriticEvaluatorSection", evidence_start)
    evidence = source[evidence_start:evidence_end]

    assert evidence.index('class="agent-trace-counts"') < evidence.index(
        "No persisted Evidence Chain trace found for this run yet."
    )
    assert evidence.index("No persisted Evidence Chain trace found for this run yet.") < evidence.index(
        "renderEvidenceChainAgentStatusRows(perAgentStatus)"
    )
    assert evidence.index("renderEvidenceChainAgentStatusRows(perAgentStatus)") < evidence.index(
        'class="agent-trace-json-grid"'
    )

    assert "display: grid;\n  gap: 12px;" in css
    assert ".agent-trace-diagnostic-detail__content .agent-trace-counts" in css
    assert ".pipeline-runs-empty-cell.agent-trace-state" in css
    assert "padding: 13px 14px" in css
    assert ".agentic-review-chip-list" in css
    assert ".agent-trace-json-grid" in css


def test_confirmation_and_endpoint_ownership_are_unchanged_and_never_auto_triggered():
    source = _source()
    handler_start = source.index(
        'const button = event.target.closest("[data-human-reviewed-influence-approval-request]")'
    )
    handler_end = source.index(
        'const button = event.target.closest("[data-agent-recommendation-overlay]")',
        handler_start,
    )
    handler = source[handler_start:handler_end]

    assert 'querySelector("[data-human-reviewed-influence-approval-request-confirmation]")' in handler
    assert "reviewerConfirmation: Boolean(confirmation?.checked)" in handler
    assert '"/api/human-reviewed-influence-approval-request"' in handler
    assert 'method: "POST"' in handler
    assert ".click(" not in handler
    assert ".checked = true" not in source
    assert "/application-actions" not in source


def test_diagnostic_inventory_selection_agent_trace_search_and_advanced_shell_regressions():
    source = _source()
    profile = PROFILE_UI_PATH.read_text(encoding="utf-8")
    registry = _diagnostic_registry()

    assert sum(registry.count(f"{renderer}(") for renderer in EXPECTED_DIAGNOSTIC_RENDERERS) == 77
    assert "function selectAgentTraceDiagnostic" in source
    assert "renderAgentTraceMasterDetail(tracePayload)" in source
    assert 'id="agenticReviewQueueSearch" type="search"' in profile
    assert "title.includes(normalizedQuery) || company.includes(normalizedQuery)" in source
    assert 'data-agentic-tab-target="agenticReviewAdvancedTab">Advanced</button>' in profile
    assert 'data-agentic-advanced-target="agenticReviewTraceTab">Agent Trace</button>' in profile
