from __future__ import annotations

from pathlib import Path
import re

from tests.test_item6b65c_extended_trace_diagnostics_master_detail import (
    EXPECTED_DIAGNOSTIC_RENDERERS,
    _diagnostic_registry,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILE_UI_PATH = ROOT / "src/app/profile_ui.py"
REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"
REVIEW_CSS_PATH = ROOT / "src/app/static/agentic_review.css"


def _profile() -> str:
    return PROFILE_UI_PATH.read_text(encoding="utf-8")


def _source() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _css() -> str:
    return REVIEW_CSS_PATH.read_text(encoding="utf-8")


def _function(source: str, name: str, next_name: str) -> str:
    start = source.index(f"function {name}")
    return source[start : source.index(f"function {next_name}", start)]


def test_native_confirmation_control_is_one_label_row_separate_from_action_and_copy():
    source = _source()
    approval = _function(
        source,
        "renderHumanReviewedInfluenceApprovalRequestSection",
        "renderAgentTraceDetailedSections",
    )

    label_start = approval.index(
        '<label class="agentic-review-muted agent-trace-confirmation-control">'
    )
    checkbox = approval.index(
        '<input type="checkbox" data-human-reviewed-influence-approval-request-confirmation>',
        label_start,
    )
    label_text = approval.index("Explicitly create influence approval request", checkbox)
    label_end = approval.index("</label>", label_text)
    button = approval.index("data-human-reviewed-influence-approval-request ", label_end)
    explanation = approval.index(
        "data-human-reviewed-influence-approval-request-status", button
    )

    assert label_start < checkbox < label_text < label_end < button < explanation
    assert approval.count('type="checkbox"') == 1
    assert "checked" not in approval[checkbox:label_end]

    checkbox_labels = re.findall(
        r'<label class="agentic-review-muted agent-trace-confirmation-control">\s*'
        r'<input type="checkbox"',
        source,
    )
    assert len(checkbox_labels) == source.count('<input type="checkbox"') == 13


def test_confirmation_layout_centers_native_checkbox_and_preserves_intrinsic_cta():
    css = _css()

    label_rule = css[
        css.index(
            ".agent-trace-diagnostic-detail__content .agentic-review-actions > .agent-trace-confirmation-control {"
        ) :
    ]
    label_rule = label_rule[: label_rule.index("}") + 1]
    checkbox_rule = css[
        css.index(
            '.agent-trace-diagnostic-detail__content .agentic-review-actions > .agent-trace-confirmation-control input[type="checkbox"] {'
        ) :
    ]
    checkbox_rule = checkbox_rule[: checkbox_rule.index("}") + 1]
    action_rule = css[
        css.index(
            ".agent-trace-diagnostic-detail__content :is(.agentic-feedback-actions, .agentic-review-actions) > .agentic-feedback-action {"
        ) :
    ]
    action_rule = action_rule[: action_rule.index("}") + 1]

    assert "margin-bottom: 2px" in label_rule
    assert "cursor: pointer" in label_rule
    assert "width: 16px" in checkbox_rule
    assert "height: 16px" in checkbox_rule
    assert "margin: 0" in checkbox_rule
    assert "justify-self: start" in action_rule
    assert "width: auto" in action_rule
    assert "align-items: start" in css
    assert "grid-template-columns: minmax(0, max-content) minmax(0, 1fr)" in css


def test_json_markdown_and_raw_disclosures_share_an_inset_body_without_content_changes():
    source = _source()
    details = _function(
        source,
        "renderAgentTraceReadOnlyDetails",
        "agentTraceReadOnlyStepStatus",
    )
    markdown = _function(
        source,
        "renderAgenticWorkflowMarkdownSummary",
        "renderAgenticReviewFeedbackSection",
    )
    selected_step = _function(
        source,
        "renderAgentTraceSelectedStep",
        "renderAgentTraceCompactContext",
    )

    assert '<details class="agent-trace-json-detail"' in details
    assert "<summary>${escapeHtml(summary)}</summary>" in details
    assert '<div class="agent-trace-disclosure-body">' in details
    assert "JSON.stringify(value, null, 2)" in details
    assert "<pre>${escapeHtml(payload)}</pre>" in details

    assert '<details class="agentic-workflow-markdown' in markdown
    assert '<div class="agent-trace-disclosure-body">' in markdown
    assert "<pre>${escapeHtml(safeMarkdown)}</pre>" in markdown

    assert '<details class="agent-trace-raw-details"' in selected_step
    assert "<summary>Raw / debug</summary>" in selected_step
    assert (
        '<div class="agent-trace-disclosure-body agent-trace-disclosure-body--grid">'
        in selected_step
    )


def test_disclosure_body_and_preformatted_content_have_contained_open_state_rhythm():
    css = _css()
    body_rule = css[css.index(".agent-trace-disclosure-body {") :]
    body_rule = body_rule[: body_rule.index("}") + 1]
    pre_rule = css[css.index(".agentic-workflow-markdown pre,") :]
    pre_rule = pre_rule[: pre_rule.index("}") + 1]

    assert "display: grid" in body_rule
    assert "gap: 9px" in body_rule
    assert "padding: 10px 12px 12px" in body_rule
    assert "border-top:" in body_rule
    assert "max-width: 100%" in body_rule

    assert "padding: 12px" in pre_rule
    assert "border: 1px solid" in pre_rule
    assert "border-radius: 8px" in pre_rule
    assert "overflow: auto" in pre_rule
    assert "white-space: pre-wrap" in pre_rule
    assert ".agent-trace-raw-details > .agent-trace-disclosure-body" in css

    source = _source()
    for marker in (
        'renderAgentTraceReadOnlyDetails("Available sections"',
        'renderAgentTraceReadOnlyDetails("Safety metadata"',
        "renderAgenticWorkflowMarkdownSummary(",
        "Raw / debug",
    ):
        assert marker in source


def test_existing_back_navigation_uses_agentic_page_header_content_region_and_route():
    profile = _profile()
    css = _css()
    header_start = profile.index(
        '<header class="page-header app-page-header agentic-review-header">'
    )
    header = profile[header_start : profile.index("</header>", header_start)]

    assert (
        '<a class="agentic-review-back-link" href="/profile?tab=pipeline-runs">'
        in header
    )
    assert header.index('class="app-page-header__main"') < header.index(
        'class="agentic-review-back-link"'
    )
    assert header.index('class="agentic-review-back-link"') < header.index(
        'class="app-page-header__title-row"'
    )
    assert '<div class="header-actions app-page-header__actions">' not in header
    assert "Back to tailoring" not in header

    header_rule = css[
        css.index(
            "body .agentic-review-page.page > .agentic-review-header.app-page-header {"
        ) :
    ]
    header_rule = header_rule[: header_rule.index("}") + 1]
    back_rule = css[
        css.index(".agentic-review-header .agentic-review-back-link {") :
    ]
    back_rule = back_rule[: back_rule.index("}") + 1]

    assert "flex-direction: column" in header_rule
    assert "align-items: stretch" in header_rule
    assert "position: absolute" not in header_rule
    assert "position: fixed" not in header_rule
    assert "display: inline-flex !important" in back_rule
    assert "align-self: flex-start" in back_rule
    assert "var(--app-primary) 10%" in back_rule
    assert "linear-gradient" not in back_rule


def test_existing_gates_network_ownership_and_item6_architecture_are_preserved():
    source = _source()
    profile = _profile()
    registry = _diagnostic_registry()
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
    assert ".checked = true" not in source
    assert ".click(" not in handler
    assert "/application-actions" not in source

    assert len(EXPECTED_DIAGNOSTIC_RENDERERS) == 77
    assert sum(registry.count(f"{renderer}(") for renderer in EXPECTED_DIAGNOSTIC_RENDERERS) == 77
    assert 'data-agentic-tab-target="agenticReviewAdvisoryTab">Review</button>' in profile
    assert 'data-agentic-tab-target="agenticReviewAdvancedTab">Advanced</button>' in profile
    assert 'id="agenticReviewQueueSearch" type="search"' in profile
    assert "title.includes(normalizedQuery) || company.includes(normalizedQuery)" in source
    assert 'class="agent-trace-master-detail"' in source
    assert 'class="agent-trace-diagnostic-workspace"' in source
    assert "renderManualProviderPreviewAction" in source
