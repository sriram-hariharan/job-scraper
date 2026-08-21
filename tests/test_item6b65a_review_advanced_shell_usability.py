from __future__ import annotations

from pathlib import Path

from tests.test_item6b2_consolidated_agentic_review_queue_foundation import _run_node


ROOT = Path(__file__).resolve().parents[1]
PROFILE_UI_PATH = ROOT / "src/app/profile_ui.py"
REVIEW_JS_PATH = ROOT / "src/app/static/agentic_review.js"
REVIEW_CSS_PATH = ROOT / "src/app/static/agentic_review.css"


def _profile() -> str:
    return PROFILE_UI_PATH.read_text(encoding="utf-8")


def _source() -> str:
    return REVIEW_JS_PATH.read_text(encoding="utf-8")


def _correction_css() -> str:
    css = REVIEW_CSS_PATH.read_text(encoding="utf-8")
    return css[css.index("/* Item 6B6.5A:") :]


def test_primary_tabs_remove_cross_axis_scrollbar_without_changing_behavior():
    profile = _profile()
    css = _correction_css()
    source = _source()

    assert '.agentic-review-page .agentic-review-tabs {' in css
    primary_rule = css[css.index('.agentic-review-page .agentic-review-tabs {') :]
    primary_rule = primary_rule[:primary_rule.index("}") + 1]
    assert "overflow: visible" in primary_rule
    assert "scrollbar-width: none" in primary_rule
    assert "overflow-x: auto" not in primary_rule
    assert "body" not in primary_rule
    assert 'data-agentic-tab-target="agenticReviewAdvisoryTab">Review</button>' in profile
    assert 'data-agentic-tab-target="agenticReviewAdvancedTab">Advanced</button>' in profile
    assert '"ArrowLeft", "ArrowRight"' in source


def test_advanced_navigation_is_restrained_and_preserves_all_panels():
    profile = _profile()
    css = _correction_css()

    for label, panel in (
        ("Workflow", "agenticReviewOverviewTab"),
        ("Agent Trace", "agenticReviewTraceTab"),
        ("Diagnostics", "agenticReviewDiagnosticsTab"),
        ("Source Views", "agenticReviewSourceViewsPanel"),
    ):
        assert f'data-agentic-advanced-target="{panel}">{label}</button>' in profile

    assert "body .agentic-review-page .agentic-review-advanced-tab" in css
    assert "background-image: none !important" in css
    assert ".agentic-review-advanced-tab.is-active" in css
    assert "color: var(--app-primary) !important" in css
    assert "linear-gradient" not in css
    assert "transform: none !important" in css


def test_lane_filters_use_exact_machine_values_without_mutating_records():
    result = _run_node(
        """
const records = hooks.consolidateAgenticReviewRows(
  [
    { job_id: "missing", title: "Unreviewed", company: "Neutral" },
    { job_id: "unknown", title: "Unknown", company: "Neutral" },
  ],
  [],
  [
    { job_id: "ready", title: "Ready role", company: "Acme", operator_review_lane: "ready_to_apply" },
    { job_id: "tailor", title: "Tailor role", company: "Beta", operator_review_lane: "tailor_then_apply" },
    { job_id: "review", title: "Review role", company: "Gamma", operator_review_lane: "review_before_action" },
    { job_id: "hold", title: "Hold role", company: "Delta", operator_review_lane: "hold_or_skip" },
    { job_id: "watch", title: "Watch role", company: "Epsilon", operator_review_lane: "source_watch" },
    { job_id: "unknown", operator_review_lane: "future_lane" },
  ],
);
const before = JSON.stringify(records);
const ids = (lane) => hooks.filterAgenticReviewQueueRecords(records, lane, "").map((record) => record.job_id);
console.log(JSON.stringify({
  all: ids("all"),
  ready: ids("ready_to_apply"),
  tailor: ids("tailor_then_apply"),
  review: ids("review_before_action"),
  hold: ids("hold_or_skip"),
  watch: ids("source_watch"),
  missing: ids("not_fully_evaluated"),
  invalidNormalizesTo: hooks.normalizeAgenticReviewQueueFilterLane("invented_lane"),
  unchanged: before === JSON.stringify(records),
}));
"""
    )

    assert result == {
        "all": ["missing", "unknown", "ready", "tailor", "review", "hold", "watch"],
        "ready": ["ready"],
        "tailor": ["tailor"],
        "review": ["review"],
        "hold": ["hold"],
        "watch": ["watch"],
        "missing": ["missing"],
        "invalidNormalizesTo": "all",
        "unchanged": True,
    }


def test_search_uses_only_title_and_company_and_composes_with_lane_filter():
    result = _run_node(
        """
const records = hooks.consolidateAgenticReviewRows(
  [
    { job_id: "a", title: "Data Engineer", company: "Acme" },
    { job_id: "b", title: "Platform Engineer", company: "Data Harbor" },
    { job_id: "c", title: "Analyst", company: "Gamma", hidden_metadata: "data secretneedle" },
  ],
  [],
  [
    { job_id: "a", operator_review_lane: "review_before_action" },
    { job_id: "b", operator_review_lane: "ready_to_apply" },
    { job_id: "c", operator_review_lane: "review_before_action", operator_review_reason_codes: ["secretneedle"] },
  ],
);
const ids = (lane, query) => hooks.filterAgenticReviewQueueRecords(records, lane, query).map((record) => record.job_id);
console.log(JSON.stringify({
  title: ids("all", "DATA engineer"),
  company: ids("all", "data HARBOR"),
  composed: ids("review_before_action", "data"),
  wrongLaneExcluded: ids("ready_to_apply", "acme"),
  hiddenFieldsIgnored: ids("all", "secretneedle"),
}));
"""
    )

    assert result == {
        "title": ["a"],
        "company": ["b"],
        "composed": ["a"],
        "wrongLaneExcluded": [],
        "hiddenFieldsIgnored": [],
    }


def test_filtering_preserves_or_rehomes_selection_and_never_fetches():
    result = _run_node(
        """
const records = hooks.consolidateAgenticReviewRows(
  [
    { job_id: "a", title: "Backend Engineer", company: "Acme" },
    { job_id: "b", title: "Data Scientist", company: "Beta" },
    { job_id: "c", title: "Analyst", company: "Gamma" },
  ],
  [],
  [
    { job_id: "a", operator_review_lane: "ready_to_apply" },
    { job_id: "b", operator_review_lane: "review_before_action" },
    { job_id: "c", operator_review_lane: "review_before_action" },
  ],
);
const before = JSON.stringify(records);
hooks.setAgenticReviewQueueRecords(records);
hooks.selectAgenticReviewQueueJob("b");
hooks.setAgenticReviewQueueFilter("review_before_action");
const selectedStillVisible = vm.runInContext("agenticReviewQueueState.selectedJobId", context);
hooks.setAgenticReviewQueueSearch("analyst");
const deterministicFallback = vm.runInContext("agenticReviewQueueState.selectedJobId", context);
hooks.setAgenticReviewQueueSearch("no-match-value");
const zeroSelection = vm.runInContext("agenticReviewQueueState.selectedJobId", context);
const filteredQueueMarkup = elements.agenticReviewQueuePanel.innerHTML;
const filteredInspectorMarkup = elements.agenticReviewSelectedJobPanel.innerHTML;
hooks.clearAgenticReviewQueueFilters();
console.log(JSON.stringify({
  selectedStillVisible,
  deterministicFallback,
  zeroSelection,
  filteredQueue: filteredQueueMarkup.includes("No jobs match the current filters."),
  filteredInspector: filteredInspectorMarkup.includes("No matching job selected"),
  selectedAfterClear: vm.runInContext("agenticReviewQueueState.selectedJobId", context),
  visibleAfterClear: hooks.visibleAgenticReviewQueueRecords().map((record) => record.job_id),
  unchanged: before === JSON.stringify(records),
  fetchCalls,
}));
"""
    )

    assert result == {
        "selectedStillVisible": "b",
        "deterministicFallback": "c",
        "zeroSelection": "",
        "filteredQueue": True,
        "filteredInspector": True,
        "selectedAfterClear": "a",
        "visibleAfterClear": ["a", "b", "c"],
        "unchanged": True,
        "fetchCalls": 0,
    }


def test_filter_controls_and_dedicated_queue_scroller_are_structurally_separate():
    profile = _profile()
    css = _correction_css()
    queue_start = profile.index('class="agentic-review-queue-surface"')
    inspector_start = profile.index('id="agenticReviewSelectedJobPanel"', queue_start)
    queue_markup = profile[queue_start:inspector_start]

    assert 'id="agenticReviewQueueFilter"' in queue_markup
    assert 'id="agenticReviewQueueSearch" type="search"' in queue_markup
    assert 'id="agenticReviewQueueClear"' in queue_markup
    for value in (
        "all",
        "ready_to_apply",
        "tailor_then_apply",
        "review_before_action",
        "hold_or_skip",
        "source_watch",
        "not_fully_evaluated",
    ):
        assert f'value="{value}"' in queue_markup

    assert 'class="agentic-review-queue-panel agentic-review-queue-scroll-region"' in queue_markup
    assert 'id="agenticReviewSelectedJobPanel"' not in queue_markup
    assert ".agentic-review-queue-scroll-region" in css
    assert "overflow-y: auto" in css
    assert "max-height: clamp(" in css
    assert "scrollbar-gutter: stable" in css


def test_inspector_preview_planning_and_safety_contracts_remain_intact():
    source = _source()
    profile = _profile()
    queue_start = source.index("const AGENTIC_REVIEW_QUEUE_GROUPS")
    queue_end = source.index("function renderAgenticReviewRows", queue_start)
    queue_workspace = source[queue_start:queue_end]

    for marker in (
        "Recommendation",
        'id="agenticReviewInspectorWhyHeading">Why',
        "Evaluation coverage",
        'id="agenticReviewInspectorEvidenceHeading">Evidence',
        'id="agenticReviewInspectorAgentViewsHeading">Agent views',
        'id="agenticReviewInspectorNextStepHeading">Next step',
        "AI Tailoring Preview",
        'href="${AGENTIC_REVIEW_PLANNING_PATH}"',
        "renderManualProviderPreviewAction",
    ):
        assert marker in source

    assert 'id="manualProviderPreviewConfirmModal"' in profile
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
        "ATS submission",
        "recruiter messaging",
    ):
        assert forbidden not in queue_workspace
