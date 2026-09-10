from __future__ import annotations

from pathlib import Path

from tests.test_item6b2_consolidated_agentic_review_queue_foundation import _run_node


ROOT = Path(__file__).resolve().parents[1]
REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"
PROFILE_UI_PATH = ROOT / "src/app/profile_ui.py"
REVIEW_CSS_PATH = ROOT / "src/app/static/agentic_review.css"


def _review_js() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _css_rule(css: str, selector: str) -> str:
    start = css.index(selector)
    return css[start : css.index("}", start) + 1]


def test_queue_union_grouping_and_selection_behavior_are_unchanged():
    result = _run_node(
        """
const records = hooks.consolidateAgenticReviewRows(
  [
    { job_id: "job-a", title: "First", company: "Acme" },
    { job_id: "job-b", title: "Second", company: "Beta" },
  ],
  [{ job_id: "job-a", tailoring_decision: "tailor_before_apply" }],
  [
    { job_id: "job-a", operator_review_lane: "ready_to_apply" },
    { job_id: "job-b", operator_review_lane: "review_before_action" },
  ],
);
hooks.bindAgenticReviewQueue();
hooks.setAgenticReviewQueueRecords(records);
const initial = vm.runInContext("agenticReviewQueueState.selectedJobId", context);
listeners.click({ target: { closest() { return { dataset: { agenticReviewQueueJobId: "job-b" } }; } } });
console.log(JSON.stringify({
  count: records.length,
  order: records.map((record) => record.job_id),
  groups: records.map((record) => hooks.agenticReviewQueueGroup(record).key),
  initial,
  selected: vm.runInContext("agenticReviewQueueState.selectedJobId", context),
  selectedCount: (elements.agenticReviewQueuePanel.innerHTML.match(/aria-pressed="true"/g) || []).length,
  selectedCopy: elements.agenticReviewQueuePanel.innerHTML.includes("Selected · 2 of 3 perspectives"),
  fetchCalls,
}));
"""
    )

    assert result == {
        "count": 2,
        "order": ["job-a", "job-b"],
        "groups": ["ready_to_apply", "review_before_action"],
        "initial": "job-a",
        "selected": "job-b",
        "selectedCount": 1,
        "selectedCopy": True,
        "fetchCalls": 0,
    }


def test_queue_rows_use_restrained_semantic_surfaces_and_explicit_selection():
    css = REVIEW_CSS_PATH.read_text(encoding="utf-8")
    source = _review_js()
    normal = _css_rule(css, "#agenticReviewQueuePanel .agentic-review-queue-item {")
    selected = _css_rule(css, "#agenticReviewQueuePanel .agentic-review-queue-item.is-selected {")

    assert "linear-gradient" not in normal
    assert "background-image: none !important" in normal
    assert "var(--agentic-queue-state) 3%" in normal
    assert "inset 3px 0 0 var(--agentic-queue-state)" in normal
    assert "linear-gradient" not in selected
    assert "background-image: none !important" in selected
    assert "var(--app-primary) 9%" in selected
    assert "0 0 0 1px" in selected
    assert 'aria-pressed="${isSelected ? "true" : "false"}"' in source
    assert 'const perspectiveSummary = `${isSelected ? "Selected · " : ""}' in source

    for lane in (
        "ready_to_apply",
        "tailor_then_apply",
        "review_before_action",
        "hold_or_skip",
        "source_watch",
    ):
        assert f'data-agentic-review-lane="{lane}"' in css


def test_queue_heading_and_text_density_contract_are_corrected():
    profile = PROFILE_UI_PATH.read_text(encoding="utf-8")
    css = REVIEW_CSS_PATH.read_text(encoding="utf-8")
    queue_item = _css_rule(css, "#agenticReviewQueuePanel .agentic-review-queue-item {")

    assert '<h3 id="agenticReviewQueueHeading">Review Queue</h3>' in profile
    assert "Jobs requiring review" not in profile
    assert "min-height: 52px" in queue_item
    assert "padding: 9px 10px 9px 12px" in queue_item
    assert ".agentic-review-queue-item__copy strong" in css
    assert ".agentic-review-queue-item__copy > span" in css
    assert ".agentic-review-queue-item__meta small" in css
    assert "#agenticReviewQueuePanel .agentic-review-queue-item:focus-visible" in css
    assert "@media (max-width: 720px)" in css
    assert "@media (max-width: 560px)" in css


def test_run_context_keeps_all_facts_in_a_compact_collapsed_presentation():
    source = _review_js()
    css = REVIEW_CSS_PATH.read_text(encoding="utf-8")
    start = source.index("function renderAgenticReviewStatus")
    end = source.index("function countBy", start)
    status = source[start:end]

    assert 'id="agenticReviewStatusCard"' in PROFILE_UI_PATH.read_text(encoding="utf-8")
    assert "agentic-review-status-run-id" in status
    assert "<h2>${escapeHtml(run?.run_id" not in status
    for label in (
        "Run status",
        "Verification",
        "Final jobs",
        "Ready to apply",
        "Tailor then apply",
        "Hold / skip",
        "Agent trace",
        "Source watch",
        "Missing artifacts",
        "Trace steps",
        "Scraped / filtered",
    ):
        assert label in status

    diagnostics = status[status.index("agentic-review-secondary-diagnostics") :]
    assert "Secondary diagnostics" in diagnostics
    assert 'data-collapsed-by-default="true"' in diagnostics
    assert " open" not in diagnostics.split(">", 1)[0]
    assert "#agenticReviewStatusCard .agentic-review-health-strip" in css
    assert "#agenticReviewStatusCard .agentic-workflow-metric" in css
    assert ".agentic-review-secondary-diagnostics > summary" in css


def test_inspector_source_views_and_manual_preview_remain_intact():
    profile = PROFILE_UI_PATH.read_text(encoding="utf-8")
    source = _review_js()

    for marker in (
        "Recommendation",
        'id="agenticReviewInspectorWhyHeading">Why',
        "Evaluation coverage",
        'id="agenticReviewInspectorEvidenceHeading">Evidence',
        'id="agenticReviewInspectorAgentViewsHeading">Agent views',
    ):
        assert marker in source

    for marker in (
        'id="agenticReviewSourceViews"',
        'id="agenticReviewPriorityPanel"',
        'id="agenticReviewTailoringPanel"',
        'id="agenticReviewOperatorPanel"',
        'id="manualProviderPreviewConfirmModal"',
    ):
        assert marker in profile

    for marker in (
        "renderManualProviderPreviewAction",
        "openManualProviderPreviewConfirmation",
        "submitManualProviderPreview",
        "manualProviderPreviewState.tailoringRows",
    ):
        assert marker in source


def test_visual_pass_adds_no_network_or_mutation_authority():
    source = _review_js()
    start = source.index("const AGENTIC_REVIEW_QUEUE_GROUPS")
    end = source.index("function renderAgenticReviewRows", start)
    queue_and_inspector = source[start:end]

    for forbidden in (
        "/application-actions",
        "window.fetch",
        "fetchJson(",
        "localStorage",
        "MANUAL_PROVIDER_PREVIEW_ENDPOINT",
        'method: "POST"',
        'method: "PUT"',
        'method: "PATCH"',
        'method: "DELETE"',
        "queue_mutation",
        "resume_mutation",
        "application_mutation",
        "approval_mutation",
        "ATS submission",
        "recruiter messaging",
        "consensus",
    ):
        assert forbidden not in queue_and_inspector
