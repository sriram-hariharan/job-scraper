from hashlib import sha256
from pathlib import Path
import subprocess


PLANNING_UI = Path("src/app/planning_ui.py")
PLANNING_JS = Path("src/app/static/planning.js")
SCAN_JS = Path("src/app/static/scan_workspace.js")
PREMIUM_CSS = Path("src/app/static/scan_workspace_premium.css")
LEGACY_CSS = Path("src/app/static/scan_workspace_review.css")
TAILORING_CSS = Path("src/app/static/tailoring_workspace_premium.css")


def _scan_route() -> str:
    source = PLANNING_UI.read_text(encoding="utf-8")
    return source.split("def scan_workspace(", 1)[1]


def test_scan_workspace_premium_is_the_route_owned_css_loaded_last():
    route = _scan_route()
    head = route.split("</head>", 1)[0]
    premium = "scan_workspace_premium.css?v=scan_workspace_premium_r1"

    assert PREMIUM_CSS.exists()
    assert LEGACY_CSS.exists()
    assert "scan_workspace_review.css" not in head
    assert premium in head
    assert head.index("vendor/tabler/tabler.min.css") < head.index("styles.css?v=")
    assert head.index("styles.css?v=") < head.index("app_redesign.css?v=")
    assert head.index("app_redesign.css?v=") < head.index(premium)


def test_scan_workspace_preserves_new_scan_processing_and_review_ids():
    route = _scan_route()
    required_ids = [
        "scanWorkspacePage",
        "scanWorkspaceViewSampleBtn",
        "scanWorkspaceResumeSelect",
        "scanWorkspaceCompanyInput",
        "scanWorkspaceRoleInput",
        "scanWorkspaceJobUrlInput",
        "scanWorkspaceJobDescriptionInput",
        "scanWorkspaceIntakeValidation",
        "scanWorkspaceClearIntakeBtn",
        "scanWorkspaceStartScanBtn",
        "scanWorkspaceProcessingBadge",
        "scanWorkspaceProcessingBackBtn",
        "scanWorkspaceProcessingTitle",
        "scanWorkspaceProcessingSubtitle",
        "scanWorkspaceProcessingSummary",
        "scanWorkspaceProcessingBar",
        "scanWorkspaceProcessingStepList",
        "scanWorkspaceProcessingNote",
        "scanWorkspaceProcessingComplete",
        "scanWorkspaceProcessingOkBtn",
        "scanWorkspaceScoreValue",
        "scanWorkspaceTrustedCount",
        "scanWorkspaceAiCount",
        "scanWorkspaceGuidanceCount",
        "scanWorkspaceInteractiveSummary",
        "scanWorkspaceDivider",
    ]
    for element_id in required_ids:
        assert f'id="{element_id}"' in route


def test_scan_workspace_preserves_tabs_preview_zoom_and_action_ids():
    route = _scan_route()
    scan_js = SCAN_JS.read_text(encoding="utf-8")
    required_route_ids = [
        "scanWorkspaceTabRow",
        "scanWorkspacePersonalTab",
        "scanWorkspaceTrustedTab",
        "scanWorkspaceAiTab",
        "scanWorkspaceFormattingTab",
        "scanWorkspaceGuidanceTab",
        "scanWorkspaceUndoBtn",
        "scanWorkspaceRedoBtn",
        "scanWorkspaceAcceptAllAiBtn",
        "scanWorkspaceExportBtn",
        "scanWorkspaceExportMenu",
        "scanWorkspaceCompareBtn",
        "scanWorkspaceSaveBtn",
        "scanWorkspaceRescanBtn",
        "scanWorkspaceAnnotationStage",
        "scanWorkspaceAnnotationOverlay",
        "scanWorkspaceLiveDraftPreview",
        "scanWorkspacePreviewStatus",
        "scanWorkspacePreviewMeta",
        "scanWorkspaceSuggestionPopover",
        "scanWorkspaceSuggestionAcceptBtn",
        "scanWorkspaceSuggestionRejectBtn",
        "scanWorkspaceSuggestionResetBtn",
        "scanWorkspaceContinueModal",
        "scanWorkspaceContinueToEditBtn",
        "scanWorkspaceContinueDownloadBtn",
        "scanWorkspaceCompareRefreshBtn",
        "scanWorkspaceCompareSummary",
        "scanWorkspaceCompareBeforePane",
        "scanWorkspaceCompareAfterPane",
    ]
    for element_id in required_route_ids:
        assert f'id="{element_id}"' in route

    for element_id in [
        "scanWorkspaceZoomOutBtn",
        "scanWorkspaceZoomResetBtn",
        "scanWorkspaceZoomInBtn",
        "scanWorkspacePdfScroller",
        "scanWorkspacePreviewEmpty",
        "scanWorkspacePdfPages",
    ]:
        assert f'id="{element_id}"' in scan_js


def test_scan_workspace_preserves_interaction_data_hooks():
    combined = "\n".join(
        path.read_text(encoding="utf-8")
        for path in [PLANNING_UI, PLANNING_JS, SCAN_JS]
    )
    required_hooks = [
        "data-scan-selected-tab",
        "data-scan-surface",
        "data-scan-switch-mode",
        "data-scan-focus-candidate",
        "data-scan-exclude-issue",
        "data-scan-reinclude-issue",
        "data-scan-review-action",
        "data-scan-review-edit",
        "data-scan-select-candidate",
        "data-scan-decision-action",
        "data-scan-phrase-action",
        "data-scan-export-format",
        "data-scan-continue-close",
    ]
    for hook in required_hooks:
        assert hook in combined


def test_scan_workspace_keeps_surface_pdf_phrase_compare_and_persistence_behavior():
    scan_js = SCAN_JS.read_text(encoding="utf-8")
    planning_js = PLANNING_JS.read_text(encoding="utf-8")
    for function_name in [
        "normalizeScanWorkspaceSurface",
        "updateScanWorkspaceSurfaceTabs",
        "renderScanWorkspaceJobDescriptionSurfaceInto",
        "renderScanWorkspacePdfPreviewShell",
        "renderScanWorkspaceLiveDraftPreviewInto",
        "generateScanWorkspacePhrasesForActiveMarker",
        "renderScanWorkspaceSuggestionPopover",
        "renderScanWorkspaceCompareShell",
        "saveScanWorkspaceDraftState",
        "exportScanWorkspaceDraft",
    ]:
        assert f"function {function_name}" in scan_js or f"async function {function_name}" in scan_js

    for function_name in [
        "renderScanWorkspaceView",
        "bindScanWorkspaceHandlers",
        "bindScanWorkspacePreviewControls",
        "bindScanWorkspaceDivider",
    ]:
        assert f"function {function_name}" in planning_js


def test_scan_route_removes_presentation_only_legacy_classes():
    route = _scan_route()
    markup = route.split('return f"""', 1)[1].split("</html>", 1)[0]
    forbidden = [
        'class="card',
        " ghost-btn",
        'class="ghost-btn',
        " btn-sm",
        'class="subtext',
        " app-page-header",
        " tailoring-workspace-subcard",
        " tailoring-interactive-shell",
        " tailoring-workspace-content",
        " tailoring-preview-shell",
        " tailoring-preview-canvas",
        " tailoring-workspace-preview-header",
    ]
    for marker in forbidden:
        assert marker not in markup


def test_scan_generated_markup_uses_scan_empty_and_zoom_components():
    scan_js = SCAN_JS.read_text(encoding="utf-8")
    planning_js = PLANNING_JS.read_text(encoding="utf-8")
    scan_planning = "\n".join([
        planning_js.split("function renderScanWorkspaceIssueInventory", 1)[1].split(
            "function getScanWorkspaceReplacementSuggestions", 1
        )[0],
        planning_js.split("function renderScanWorkspaceView", 1)[1].split(
            "async function previewScanWorkspaceState", 1
        )[0],
        planning_js.split("async function initScanWorkspacePage", 1)[1].split(
            "function buildTailoringWorkspaceUrl", 1
        )[0],
    ])

    assert 'class="scan-workspace-zoom-btn"' in scan_js
    assert 'class="scan-workspace-zoom-btn scan-workspace-zoom-value"' in scan_js
    assert "tailoring-empty-state" not in scan_js
    assert "tailoring-empty-state" not in scan_planning
    # Document mirror and PDF primitives remain intentionally shared.
    assert "tailoring-workspace-doc-page" in scan_js
    assert "tailoring-workspace-pdf-scroller" in scan_js


def test_scan_premium_css_covers_modes_themes_states_and_responsive_layout():
    css = PREMIUM_CSS.read_text(encoding="utf-8")
    required = [
        "canonical route-owned premium visual system",
        "html[data-theme=\"dark\"] #scanWorkspacePage",
        ".scan-workspace-intake-grid",
        ".scan-workspace-processing-step.is-current",
        ".scan-workspace-processing-step.is-complete",
        ".scan-workspace-review-shell",
        "--scan-workspace-left-width",
        ".scan-workspace-divider",
        ".scan-workspace-review-score-ring",
        ".scan-workspace-tab-btn.active",
        "#scanWorkspaceTrustedTab.active::after",
        "#scanWorkspaceAiTab.active::after",
        "#scanWorkspaceGuidanceTab.active::after",
        ".scan-workspace-issue-row.is-active",
        ".scan-workspace-hard-requirement-warning",
        ".scan-workspace-suggestion-popover",
        ".scan-workspace-phrase-option",
        ".scan-workspace-inline-diff-del",
        ".scan-workspace-inline-diff-add",
        "#scanWorkspacePdfScroller",
        ".scan-workspace-preview-suggestion-target--replacement",
        ".scan-workspace-preview-suggestion-target--guidance",
        ".scan-workspace-compare-shell",
        ".scan-workspace-continue-modal-card",
        ".scan-workspace-empty-state",
        "@media (max-width: 900px)",
        "@media (prefers-reduced-motion: reduce)",
    ]
    for marker in required:
        assert marker in css
    assert "overflow-x: hidden" in css


def test_scan_premium_css_has_one_canonical_major_base_per_component():
    css = PREMIUM_CSS.read_text(encoding="utf-8")
    major_bases = [
        ".scan-workspace-intake-card {",
        ".scan-workspace-processing-card {",
        ".scan-workspace-review-shell {",
        ".scan-workspace-review-score-card {",
        ".scan-workspace-tab-row {",
        "#scanWorkspacePage .scan-workspace-issue-row {",
        ".scan-workspace-review-main-header {",
        ".scan-workspace-suggestion-popover {",
        ".scan-workspace-compare-shell {",
        ".scan-workspace-continue-modal-card {",
        ".scan-workspace-empty-state {",
    ]
    for selector in major_bases:
        assert css.count(f"\n{selector}") == 1


def test_scan_ui_b_restores_the_shared_page_grid_and_route_owned_title():
    route = _scan_route()
    css = PREMIUM_CSS.read_text(encoding="utf-8")

    assert 'class="page scan-workspace-page"' in route
    assert "body .app-shell ~ #scanWorkspacePage.page" in css
    assert "width: auto !important;" in css
    assert "#scanWorkspacePage .scan-workspace-header-copy h1 {" in css
    assert "font-size: clamp(26px, 2vw, 34px) !important;" in css
    assert route.index('class="scan-workspace-header-row"') < route.index(
        'class="scan-workspace-header-actions"'
    )


def test_scan_ui_b_uses_a_roomier_persisted_review_split():
    css = PREMIUM_CSS.read_text(encoding="utf-8")
    planning_js = PLANNING_JS.read_text(encoding="utf-8")

    assert "--scan-workspace-left-width: 40%;" in css
    assert "clampToRange(Number(percent) || 40, 30, 52)" in planning_js
    assert "Number.isFinite(saved) ? saved : 40" in planning_js
    assert 'id="scanWorkspaceDivider"' in _scan_route()


def test_scan_ui_b_equalizes_category_navigation_without_legacy_tabs():
    css = PREMIUM_CSS.read_text(encoding="utf-8")
    tab_row = css.split(".scan-workspace-tab-row {", 1)[1].split("}", 1)[0]
    tab_button = css.split(".scan-workspace-tab-btn {", 1)[1].split("}", 1)[0]

    assert "grid-template-columns: repeat(5, minmax(0, 1fr));" in tab_row
    assert "place-items: center;" in tab_button
    assert "font-size: 10px;" in tab_button
    assert "text-align: center;" in tab_button


def test_scan_ui_b_keeps_tooltips_visible_and_resets_jd_document_surface():
    route = _scan_route()
    css = PREMIUM_CSS.read_text(encoding="utf-8")
    tooltip_selector = '.scan-workspace-disabled-action-wrap[data-scan-help]:not([data-scan-help=""])::after {'
    tooltip = css.split(tooltip_selector, 1)[1].split("}", 1)[0]
    jd_pre = css.split(".scan-workspace-job-description-panel pre {", 1)[1].split("}", 1)[0]

    assert route.count('data-scan-help="No changes made"') == 2
    assert 'class="scan-workspace-disabled-action-wrap"\n                title=' not in route
    assert "content: attr(data-scan-help);" in tooltip
    assert "top: calc(100% + 7px);" in tooltip
    assert "bottom: auto;" in tooltip
    assert "color: #ffffff;" in tooltip
    assert "background: #111827;" in tooltip
    assert ".scan-workspace-annotation-topbar:has(.scan-workspace-annotation-status:empty)" in css
    assert "background: transparent !important;" in jd_pre
    assert "color: var(--scan-text-2) !important;" in jd_pre


def test_scan_ui_b_compare_and_all_modes_use_the_available_page_width():
    css = PREMIUM_CSS.read_text(encoding="utf-8")
    active_mode = css.split(".scan-workspace-mode-panel.is-active {", 1)[1].split("}", 1)[0]
    compare_grid = css.split(".scan-workspace-compare-grid {", 1)[1].split("}", 1)[0]

    assert "width: 100%;" in active_mode
    assert "max-width: none;" in active_mode
    assert "max-width: 1240px" not in css
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in compare_grid


def test_scan_ui_c_uses_one_flat_finding_family_for_all_taxonomy_tabs():
    route = _scan_route()
    planning_js = PLANNING_JS.read_text(encoding="utf-8")
    css = PREMIUM_CSS.read_text(encoding="utf-8")
    finding = css.split("#scanWorkspacePage .scan-workspace-issue-row {", 1)[1].split("}", 1)[0]

    for tab_id in [
        "scanWorkspacePersonalTab",
        "scanWorkspaceTrustedTab",
        "scanWorkspaceAiTab",
        "scanWorkspaceFormattingTab",
        "scanWorkspaceGuidanceTab",
    ]:
        assert f'id="{tab_id}"' in route

    assert 'class="scan-workspace-issue-row ${toneClass}' in planning_js
    assert "data-scan-focus-candidate" in planning_js
    assert "data-scan-exclude-issue" in planning_js
    assert "background-image: none !important;" in finding
    assert "linear-gradient" not in finding
    assert "font-size: 14px;" in css.split(".scan-workspace-issue-title {", 1)[1].split("}", 1)[0]
    assert "white-space: normal;" in css.split(".scan-workspace-issue-signals,", 1)[1].split("}", 1)[0]


def test_scan_ui_c_preserves_personal_details_counts_and_hard_requirement_contracts():
    planning_js = PLANNING_JS.read_text(encoding="utf-8")
    css = PREMIUM_CSS.read_text(encoding="utf-8")

    for field in ["name", "city", "state", "contact", "email", "linkedin", "github"]:
        assert f'data-scan-personal-detail="${{escapeHtml(field)}}"' in planning_js or (
            field == "state" and 'data-scan-personal-detail="state"' in planning_js
        )
    for metric in ["matchedCount", "missingCount", "aiCount"]:
        assert f"panel.{metric}" in planning_js
    assert "Hard requirement" in planning_js
    assert ".scan-workspace-hard-requirement-warning" in css
    assert "var(--scan-warning-soft)" in css


def test_scan_ui_c_toolbar_export_and_modal_keep_dedicated_semantic_classes():
    route = _scan_route()
    css = PREMIUM_CSS.read_text(encoding="utf-8")

    for modifier in [
        "scan-workspace-toolbar-btn--icon",
        "scan-workspace-toolbar-btn--positive",
        "scan-workspace-toolbar-btn--secondary",
        "scan-workspace-toolbar-btn--primary",
    ]:
        assert modifier in route

    assert "Export as" in route
    assert 'data-scan-export-format="pdf"' in route
    assert 'data-scan-export-format="word"' in route
    assert 'id="scanWorkspaceContinueModalCloseBtn"' in route
    assert 'data-scan-continue-close="true"' in route
    assert "scan-workspace-continue-modal-action--secondary" in route
    assert "scan-workspace-continue-modal-action--primary" in route
    assert "scan-workspace-continue-modal-primary" not in route
    assert "scan-workspace-continue-modal-secondary" not in route

    export_item = css.split("#scanWorkspacePage .scan-workspace-export-option {", 1)[1].split("}", 1)[0]
    modal_action = css.split("#scanWorkspacePage .scan-workspace-continue-modal-action {", 1)[1].split("}", 1)[0]
    modal_close = css.split("#scanWorkspacePage .scan-workspace-continue-modal-close {", 1)[1].split("}", 1)[0]
    for block in [export_item, modal_action, modal_close]:
        assert "background-image: none !important;" in block
        assert "linear-gradient" not in block


def test_scan_ui_c_collapses_the_obsolete_resume_mirror_note():
    css = PREMIUM_CSS.read_text(encoding="utf-8")
    block = css.split(
        "#scanWorkspaceLiveDraftPreview .tailoring-workspace-doc-mirror-note {", 1
    )[1].split("}", 1)[0]

    assert "display: none !important;" in block


def test_scan_ui_d_keeps_only_the_toolbar_resume_identity():
    route = _scan_route()
    css = PREMIUM_CSS.read_text(encoding="utf-8")

    assert 'id="scanWorkspaceToolbarResumeName"' in route
    assert 'id="scanWorkspacePreviewName"' not in route
    assert "scan-workspace-preview-name" not in route
    for preserved_id in [
        "scanWorkspaceAiSuggestionStep",
        "scanWorkspaceEditStep",
        "scanWorkspaceAnnotationStatus",
        "scanWorkspacePreviewStatus",
        "scanWorkspacePreviewMeta",
        "scanWorkspaceLiveDraftPreview",
    ]:
        assert f'id="{preserved_id}"' in route
    assert ".scan-workspace-preview-name {" not in css
    assert "justify-content: flex-end;" in css.split(
        ".scan-workspace-preview-title-row {", 1
    )[1].split("}", 1)[0]


def test_scan_ui_d_simplifies_only_skill_findings_and_preserves_full_jd_evidence():
    route = _scan_route()
    planning_js = PLANNING_JS.read_text(encoding="utf-8")
    css = PREMIUM_CSS.read_text(encoding="utf-8")

    assert 'panelKey: panel.key' in planning_js
    assert 'isSkillsPanel: panelKey === "skills"' in planning_js
    assert "normalizeScanWorkspaceFindingDisplayText(signal) !== normalizedTitle" in planning_js
    assert 'getScanWorkspaceIssueJdContext(item, { full: true })' in planning_js
    assert 'const jdContext = isSkillsPanel ? "" : getScanWorkspaceIssueJdContext(item);' in planning_js
    assert 'scoreTitle && !isSkillsPanel' in planning_js
    assert 'data-scan-evidence-tooltip=' in planning_js
    assert 'aria-describedby="scanWorkspaceEvidenceTooltip"' in planning_js
    assert 'id="scanWorkspaceEvidenceTooltip"' in route
    assert 'id="scanWorkspaceEvidenceTooltipCopy"' in route
    assert 'role="tooltip"' in route
    assert ".scan-workspace-issue-row--skill" in css
    assert ".scan-workspace-evidence-tooltip" in css
    assert 'root.addEventListener("pointerover"' in planning_js
    assert 'root.addEventListener("focusin"' in planning_js


def test_scan_ui_d_skill_finding_render_is_compact_without_changing_other_tabs():
    node_test = r"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync(process.argv[1], "utf8");
const sandbox = {
  console,
  setTimeout,
  clearTimeout,
  CustomEvent: function CustomEvent() {},
  Element: function Element() {},
  document: {
    querySelector: () => null,
    querySelectorAll: () => [],
    getElementById: () => null,
    addEventListener: () => {},
    body: { dataset: {}, classList: { add() {}, remove() {}, toggle() {} } },
  },
  localStorage: { getItem: () => null, setItem: () => {} },
  fetch: async () => ({ ok: true, json: async () => ({}) }),
};
sandbox.window = sandbox;
sandbox.window.addEventListener = () => {};
sandbox.window.location = { href: "", search: "", pathname: "/" };
vm.createContext(sandbox);
vm.runInContext(source, sandbox);

const item = {
  scan_issue_id: "skill-python",
  scan_issue_group_id: "skills",
  scan_issue_bucket: "matched",
  row_action_type: "matched",
  can_focus_preview: false,
  display_term: "Python",
  supported_jd_signals: [" python ", "Airflow"],
  jd_context_anchors: [{ text: "Build resilient data pipelines with Python." }],
  coverage_label: "Seen 1",
};
const skill = sandbox.renderScanWorkspaceIssueInventory(
  [item],
  "matched",
  { isSkillsPanel: true }
);
const other = sandbox.renderScanWorkspaceIssueInventory([item], "matched");
const skillSignals = skill.match(/scan-workspace-issue-signals">([\s\S]*?)<\/span>/)?.[1] || "";

if (!skill.includes("scan-workspace-issue-row--skill")) throw new Error("skill modifier missing");
if (!skill.includes("Seen 1")) throw new Error("evidence badge count changed");
if (skillSignals.toLowerCase().includes("python")) throw new Error("duplicate skill signal remains");
if (!skillSignals.includes("Airflow")) throw new Error("distinct skill metadata was removed");
if (skill.includes("scan-workspace-issue-jd-context")) throw new Error("inline skill JD evidence remains");
if (skill.includes('title="JD:')) throw new Error("native-only skill evidence tooltip remains");
if (!skill.includes('data-scan-evidence-tooltip="Build resilient data pipelines with Python."')) {
  throw new Error("full skill JD evidence was not preserved");
}
if (!other.includes("scan-workspace-issue-jd-context") || !other.includes("JD:")) {
  throw new Error("non-skill inline JD context changed");
}
"""
    result = subprocess.run(
        ["node", "-e", node_test, str(PLANNING_JS)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_scan_skill_display_text_is_not_blindly_split_into_issue_identity():
    node_test = r"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync(process.argv[1], "utf8");
const sandbox = {
  console,
  setTimeout: () => 0,
  clearTimeout: () => {},
  CustomEvent: function CustomEvent() {},
  Element: function Element() {},
  document: {
    querySelector: () => null,
    querySelectorAll: () => [],
    getElementById: () => null,
    addEventListener: () => {},
    body: { dataset: {}, classList: { add() {}, remove() {}, toggle() {} } },
  },
  localStorage: { getItem: () => null, setItem: () => {} },
};
sandbox.window = sandbox;
sandbox.window.addEventListener = () => {};
sandbox.window.location = { href: "", search: "", pathname: "/" };
vm.createContext(sandbox);
vm.runInContext(source, sandbox);

const title = sandbox.getScanWorkspaceIssueTitle(
  { display_term: "C++, Python", supported_jd_signals: [] },
  0
);
if (title !== "C++, Python") throw new Error(`display text was parsed: ${title}`);
"""
    result = subprocess.run(
        ["node", "-e", node_test, str(PLANNING_JS)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_scan_exclusion_uses_shared_score_resolution_and_restores_state():
    scan_js = SCAN_JS.read_text(encoding="utf-8")
    assert "return resolveScanWorkspaceBaselineScorePoints(preload);" in scan_js

    node_test = r"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync(process.argv[1], "utf8");
const scoreNode = {
  textContent: "49",
  dataset: {},
  setAttribute() {},
};
const sandbox = {
  console,
  setTimeout: () => 0,
  clearTimeout: () => {},
  CustomEvent: function CustomEvent() {},
  Element: function Element() {},
  document: {
    querySelector: () => null,
    querySelectorAll: () => [],
    getElementById: (id) => id === "scanWorkspaceScoreValue" ? scoreNode : null,
    addEventListener: () => {},
    body: { dataset: {}, classList: { add() {}, remove() {}, toggle() {} } },
  },
  localStorage: { getItem: () => null, setItem: () => {} },
};
sandbox.window = sandbox;
sandbox.window.addEventListener = () => {};
sandbox.window.location = { href: "", search: "", pathname: "/" };
vm.createContext(sandbox);
vm.runInContext(source, sandbox);

const missingId = "scan_issue:skills:keyword:statistical_analysis";
const issues = [
  {
    issue_id: "scan_issue:skills:keyword:python",
    group_id: "skills",
    bucket: "matched",
    row_action_type: "matched",
    display_term: "Python",
    score_priority_weight: 0.238095,
  },
  {
    issue_id: missingId,
    group_id: "skills",
    bucket: "missing",
    row_action_type: "manual_guidance",
    display_term: "Statistical analysis",
    score_priority_weight: 0.238095,
  },
  {
    issue_id: "scan_issue:skills:keyword:ai_suggested_skill",
    group_id: "skills",
    bucket: "ai",
    row_action_type: "direct_replacement",
    display_term: "AI suggested skill",
    score_priority_weight: 0,
  },
];
const basePayload = {
  scan_issue_contract: {
    issues,
    groups: [{ group_id: "skills", label: "Skills", buckets: [] }],
  },
};

const baselineShapes = [
  [{ scan_score: { score: 49 } }, 49],
  [{ scan_score: { score: 76 } }, 76],
  [{ scan_score: { score: 0.49 } }, 49],
  [{ scan_score: {}, score_preview: { original_score: 0.49 } }, 49],
  [{ scan_score: {}, score_preview: { original_score_points: 49 } }, 49],
];
for (const [shape, expected] of baselineShapes) {
  const payload = { ...basePayload, ...shape };
  const resolved = sandbox.resolveScanWorkspaceBaselineScorePoints(payload);
  if (resolved !== expected) throw new Error(`baseline ${resolved} != ${expected}`);
  const adjusted = sandbox.getScanWorkspaceExclusionAdjustedScore(payload, {
    excludedIssueIds: [missingId],
  });
  if (!adjusted || adjusted.score < expected || adjusted.score > 100) {
    throw new Error(`unsafe adjusted score: ${JSON.stringify(adjusted)}`);
  }
  if (adjusted.score - expected > 8 || adjusted.excludedPenaltyRows !== 1) {
    throw new Error(`unbounded exclusion result: ${JSON.stringify(adjusted)}`);
  }
}

const payload = {
  ...basePayload,
  scan_score: { score: null },
  score_preview: { original_score: 0.49 },
};
sandbox.setScanWorkspaceIssueExcluded(missingId, true);
if (JSON.stringify(sandbox.getScanWorkspaceExcludedIssueIds()) !== JSON.stringify([missingId])) {
  throw new Error("exclude action did not persist the issue id in state");
}
let taxonomy = sandbox.buildScanWorkspaceTaxonomyFromIssueContract(payload);
if (
  taxonomy.skills.matchedCount !== 1
  || taxonomy.skills.missingCount !== 0
  || taxonomy.skills.aiCount !== 1
) {
  throw new Error(`exclude counts are wrong: ${JSON.stringify(taxonomy.skills)}`);
}
const excludedRows = taxonomy.skills.groups
  .flatMap((group) => group.items || [])
  .filter((item) => item.scan_issue_id === missingId);
if (excludedRows.length !== 1 || excludedRows[0].is_scan_excluded !== true) {
  throw new Error(`excluded row was dropped or duplicated: ${JSON.stringify(excludedRows)}`);
}
const excludedGroup = taxonomy.skills.groups.find((group) => group.bucket === "excluded");
if (!excludedGroup || excludedGroup.items.length !== 1) {
  throw new Error(`excluded row was not discoverable: ${JSON.stringify(taxonomy.skills.groups)}`);
}
if (sandbox.getScanWorkspaceReplacementSuggestions(payload).some(
  (item) => item.scan_issue_id === missingId
)) {
  throw new Error("excluded row leaked into the active annotation collection");
}
const excludedHtml = sandbox.renderScanWorkspaceIssueInventory(
  excludedGroup.items,
  excludedGroup.bucket,
  { isSkillsPanel: true }
);
if (
  !excludedHtml.includes(`data-scan-reinclude-issue="${missingId}"`)
  || !excludedHtml.includes("Re-include")
  || excludedHtml.includes(`data-scan-exclude-issue="${missingId}"`)
) {
  throw new Error(`excluded row did not expose only Re-include: ${excludedHtml}`);
}
sandbox.updateScanWorkspaceHeaderCounts(payload);
if (Number(scoreNode.textContent) < 49 || Number(scoreNode.textContent) > 57) {
  throw new Error(`top score was not safely adjusted: ${scoreNode.textContent}`);
}

sandbox.setScanWorkspaceIssueExcluded(missingId, false);
taxonomy = sandbox.buildScanWorkspaceTaxonomyFromIssueContract(payload);
if (
  taxonomy.skills.matchedCount !== 1
  || taxonomy.skills.missingCount !== 1
  || taxonomy.skills.aiCount !== 1
) {
  throw new Error(`include counts were not restored: ${JSON.stringify(taxonomy.skills)}`);
}
const activeRows = taxonomy.skills.groups
  .flatMap((group) => group.items || [])
  .filter((item) => item.scan_issue_id === missingId);
if (activeRows.length !== 1 || activeRows[0].is_scan_excluded === true) {
  throw new Error(`re-included row was dropped or duplicated: ${JSON.stringify(activeRows)}`);
}
if (sandbox.getScanWorkspaceReplacementSuggestions(payload).filter(
  (item) => item.scan_issue_id === missingId
).length !== 1) {
  throw new Error("re-included row did not return to the active collection exactly once");
}
const activeGroup = taxonomy.skills.groups.find(
  (group) => (group.items || []).some((item) => item.scan_issue_id === missingId)
);
const activeHtml = sandbox.renderScanWorkspaceIssueInventory(
  activeGroup.items,
  activeGroup.bucket,
  { isSkillsPanel: true }
);
if (
  !activeHtml.includes(`data-scan-exclude-issue="${missingId}"`)
  || activeHtml.includes(`data-scan-reinclude-issue="${missingId}"`)
) {
  throw new Error(`re-included row did not restore Exclude: ${activeHtml}`);
}
sandbox.updateScanWorkspaceHeaderCounts(payload);
const restoredScore = Number(scoreNode.textContent);
if (restoredScore !== 49) {
  throw new Error(`baseline score was not restored: ${scoreNode.textContent}`);
}

const invalidPayload = {
  ...basePayload,
  scan_score: { score: null },
  score_preview: {
    projected_score_points: null,
    projected_score: "",
    original_score_points: undefined,
    original_score: "not-a-score",
  },
};
scoreNode.textContent = "49";
const invalidResult = sandbox.getScanWorkspaceExclusionAdjustedScore(invalidPayload, {
  excludedIssueIds: [missingId],
});
if (invalidResult !== null) {
  throw new Error(`invalid score was manufactured: ${JSON.stringify(invalidResult)}`);
}
sandbox.setScanWorkspaceIssueExcluded(missingId, true);
sandbox.updateScanWorkspaceHeaderCounts(invalidPayload);
const unchangedScore = scoreNode.textContent;
if (unchangedScore !== "49") {
  throw new Error(`existing valid display was overwritten: ${scoreNode.textContent}`);
}
"""
    result = subprocess.run(
        ["node", "-e", node_test, str(PLANNING_JS)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_scan_reload_score_is_not_overwritten_by_annotation_or_tab_renders():
    node_test = r"""
const fs = require("fs");
const vm = require("vm");

function makeClassList() {
  return { add() {}, remove() {}, toggle() {}, contains() { return false; } };
}

const scoreNode = {
  textContent: "AI",
  dataset: {},
  classList: makeClassList(),
  setAttribute() {},
  removeAttribute() {},
};
const sandbox = {
  console,
  scoreNode,
  URL,
  URLSearchParams,
  AbortController,
  CustomEvent: function CustomEvent() {},
  Element: function Element() {},
  setTimeout: () => 0,
  clearTimeout: () => {},
  setInterval: () => 0,
  clearInterval: () => {},
  document: {
    querySelector: () => null,
    querySelectorAll: () => [],
    getElementById: (id) => id === "scanWorkspaceScoreValue" ? scoreNode : null,
    addEventListener: () => {},
    body: { dataset: {}, classList: makeClassList(), appendChild() {} },
  },
  localStorage: { getItem: () => null, setItem: () => {} },
  sessionStorage: { getItem: () => null, setItem: () => {} },
};
sandbox.window = sandbox;
sandbox.window.addEventListener = () => {};
sandbox.window.location = { href: "", search: "", pathname: "/scan-workspace" };
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), sandbox);
vm.runInContext(fs.readFileSync(process.argv[2], "utf8"), sandbox);

vm.runInContext(`(() => {
  const issueId = "scan_issue:skills:keyword:causal_inference";
  const issues = [
    {
      issue_id: "scan_issue:skills:keyword:python",
      group_id: "skills",
      bucket: "matched",
      row_action_type: "matched",
      display_term: "Python",
    },
    {
      issue_id: issueId,
      group_id: "skills",
      bucket: "missing",
      row_action_type: "manual_guidance",
      display_term: "Causal inference",
      score_priority_weight: 0.2,
    },
  ];
  scanWorkspaceAnnotationState.markers = [{
    id: "replacement-1",
    renderMode: "diff",
    isExactReplacement: true,
    decision: "pending",
  }];

  [49, 76].forEach((baseline) => {
    const payload = {
      scan_score: { score: baseline },
      scan_issue_contract: {
        issues,
        groups: [{ group_id: "skills", label: "Skills", buckets: [] }],
      },
    };
    scanWorkspaceState.preloadPayload = payload;
    setScanWorkspaceExcludedIssueIds([issueId]);

    updateScanWorkspaceHeaderCounts(payload);
    const correctAfterHydration = scoreNode.textContent;
    if (Number(correctAfterHydration) < baseline || Number(correctAfterHydration) > 100) {
      throw new Error("invalid hydrated score for " + baseline + ": " + correctAfterHydration);
    }
    if (scoreNode.dataset.scanScoreSource !== "exclusion_rescore_preview") {
      throw new Error("missing exclusion score ownership: " + scoreNode.dataset.scanScoreSource);
    }

    updateScanWorkspaceDecisionSummaryUi();
    updateScanWorkspaceDecisionSummaryUi();
    if (scoreNode.textContent !== correctAfterHydration) {
      throw new Error("later annotation render overwrote " + correctAfterHydration + " with " + scoreNode.textContent);
    }

    scanWorkspaceState.selectedTab = "skills";
    updateScanWorkspaceHeaderCounts(payload);
    updateScanWorkspaceDecisionSummaryUi();
    if (scoreNode.textContent !== correctAfterHydration) {
      throw new Error("tab render changed " + correctAfterHydration + " to " + scoreNode.textContent);
    }

    setScanWorkspaceExcludedIssueIds([]);
    updateScanWorkspaceHeaderCounts(payload);
    if (Number(scoreNode.textContent) !== baseline) {
      throw new Error("re-include did not restore " + baseline + ": " + scoreNode.textContent);
    }
  });

  scoreNode.textContent = "49";
  delete scoreNode.dataset.scanScoreSource;
  scanWorkspaceState.preloadPayload = {
    scan_score: { score: null },
    score_preview: {
      projected_score_points: null,
      projected_score: "",
      original_score_points: undefined,
      original_score: "not-a-score",
    },
  };
  updateScanWorkspaceDecisionSummaryUi();
  if (scoreNode.textContent !== "49") {
    throw new Error("missing baseline manufactured a score write: " + scoreNode.textContent);
  }
})()`, sandbox);
"""
    result = subprocess.run(
        ["node", "-e", node_test, str(PLANNING_JS), str(SCAN_JS)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_scan_exclusion_dirty_state_save_and_reload_use_existing_persistence_contract():
    node_test = r"""
const fs = require("fs");
const vm = require("vm");

function makeClassList() {
  return { add() {}, remove() {}, toggle() {}, contains() { return false; } };
}
const wrapper = {
  title: "",
  attrs: {},
  setAttribute(name, value) { this.attrs[name] = value; },
  removeAttribute(name) { delete this.attrs[name]; },
};
const label = { textContent: "Save" };
const listeners = {};
const saveButton = {
  disabled: true,
  title: "No changes made",
  dataset: {},
  attrs: {},
  classList: makeClassList(),
  setAttribute(name, value) { this.attrs[name] = value; },
  removeAttribute(name) { delete this.attrs[name]; if (name === "title") this.title = ""; },
  querySelector() { return label; },
  closest() { return wrapper; },
  addEventListener(name, handler) { listeners[name] = handler; },
};
const page = {
  dataset: {
    savedScanId: "",
    tailoringJsonPath: "",
    tailoringJsonKey: "",
    packetJsonPath: "",
    packetJsonKey: "job_packets/reddit.json",
    resumeName: "resume.pdf",
    planningOutputDir: "/run/application_planning",
    pipelineRunId: "20260908T010524479530Z",
    scanMode: "review",
  },
};
const sandbox = {
  console,
  saveButton,
  label,
  wrapper,
  listeners,
  page,
  URL,
  URLSearchParams,
  AbortController,
  CustomEvent: function CustomEvent() {},
  Element: function Element() {},
  setTimeout: () => 0,
  clearTimeout: () => {},
  setInterval: () => 0,
  clearInterval: () => {},
  fetch: async () => ({ ok: true, json: async () => ({}) }),
  document: {
    querySelector: (selector) => selector === ".scan-workspace-page" ? page : null,
    querySelectorAll: () => [],
    getElementById: (id) => id === "scanWorkspaceSaveBtn" ? saveButton : null,
    addEventListener: () => {},
    body: { dataset: {}, classList: makeClassList(), appendChild() {} },
  },
  localStorage: { getItem: () => null, setItem: () => {} },
  sessionStorage: { getItem: () => null, setItem: () => {} },
};
sandbox.window = sandbox;
sandbox.window.location = { href: "", search: "", pathname: "/scan-workspace" };
sandbox.window.addEventListener = () => {};
sandbox.window.dispatchEvent = () => {};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), sandbox);
vm.runInContext(fs.readFileSync(process.argv[2], "utf8"), sandbox);

(async () => {
  await vm.runInContext(`(async () => {
    const issueId = "scan_issue:skills:keyword:causal_inference";
    const emptyDraft = {
      selected_patch_candidate_ids: [],
      manual_bullet_edits: {},
      rewrite_review_decisions: {},
      excluded_scan_issue_ids: [],
      personal_details: {},
    };
    scanWorkspaceState.preloadPayload = {
      scan_entry_source: "base_planning_packet",
      draft: emptyDraft,
    };
    scanWorkspaceState.excludedScanIssueIds = [];
    scanWorkspacePersistenceState.loadResponse = { draft: emptyDraft };
    scanWorkspacePersistenceState.hydratedSignature =
      getSavedScanWorkspacePersistenceSignature();
    window.scanWorkspacePhase1 = {
      renderPersistenceStatus: () => renderScanWorkspacePersistenceStatus(),
    };

    let modalOpenCount = 0;
    openScanWorkspaceContinueModal = () => { modalOpenCount += 1; };
    refreshScanWorkspaceScorePreview = async () => {};
    ensureScanWorkspaceDocumentPreviewLoaded = () => {};
    ensureScanWorkspaceCompareLoaded = () => {};

    const requests = [];
    let failSave = false;
    let falseSuccess = false;
    postJsonWithTimeout = async (url, payload) => {
      if (failSave) throw new Error("simulated persistence failure");
      if (falseSuccess) {
        return { ok: false, has_saved_draft: true, draft: payload };
      }
      requests.push({ url, payload: JSON.parse(JSON.stringify(payload)) });
      return {
        ok: true,
        has_saved_draft: true,
        draft: {
          ...payload,
          saved_at: "2026-09-08T12:00:00Z",
        },
        score_preview: {},
      };
    };

    bindScanWorkspacePersistenceControls();
    const initialSignature = getCurrentScanWorkspacePersistenceSignature();
    if (!initialSignature || initialSignature !== scanWorkspacePersistenceState.hydratedSignature) {
      throw new Error("initial current and hydrated signatures differ");
    }
    if (!saveButton.disabled || saveButton.title !== "" || label.textContent !== "Save") {
      throw new Error("initial Save state is not clean");
    }
    if (wrapper.attrs["data-scan-help"] !== "No changes made") {
      throw new Error("clean Save did not expose exactly one custom-help source");
    }

    setScanWorkspaceIssueExcluded(issueId, true);
    const dirtySignature = getCurrentScanWorkspacePersistenceSignature();
    if (JSON.stringify(getCurrentScanWorkspaceExcludedIssueIds()) !== JSON.stringify([issueId])) {
      throw new Error("current exclusion was not recorded");
    }
    if (getSavedScanWorkspaceExcludedIssueIds().length !== 0) {
      throw new Error("saved exclusions changed before Save");
    }
    if (dirtySignature === scanWorkspacePersistenceState.hydratedSignature) {
      throw new Error("Exclude did not make the persistence signature dirty");
    }
    if (saveButton.disabled || saveButton.title !== "") {
      throw new Error("Save was not enabled for the exclusion");
    }
    if (wrapper.attrs["data-scan-help"] !== "Save changes") {
      throw new Error("dirty Save did not update the custom tooltip");
    }
    if (wrapper.attrs["aria-label"] !== "Save changes" || wrapper.title !== "") {
      throw new Error("dirty Save help surfaces are not synchronized");
    }

    await listeners.click();
    if (requests.length !== 1) throw new Error("Save did not issue one request");
    if (!requests[0].url.includes("/planning/save-workspace-draft")) {
      throw new Error("Save did not reuse the workspace-draft endpoint");
    }
    if (JSON.stringify(requests[0].payload.excluded_scan_issue_ids) !== JSON.stringify([issueId])) {
      throw new Error("Save request omitted excluded_scan_issue_ids");
    }
    if (requests[0].payload.pipeline_run_id !== "20260908T010524479530Z") {
      throw new Error("Artifact Save request omitted pipeline_run_id");
    }
    if (modalOpenCount !== 0 || page.dataset.scanMode !== "review") {
      throw new Error("Save navigated away from Optimization Review");
    }
    if (getCurrentScanWorkspacePersistenceSignature() !== scanWorkspacePersistenceState.hydratedSignature) {
      throw new Error("successful Save did not update the hydrated signature");
    }
    if (!saveButton.disabled || saveButton.title !== "") {
      throw new Error("successful Save did not return to clean state");
    }
    if (wrapper.attrs["data-scan-help"] !== "No changes made") {
      throw new Error("clean Save did not restore disabled help after persistence");
    }

    const persistedDraft = scanWorkspacePersistenceState.loadResponse.draft;
    scanWorkspaceState.excludedScanIssueIds = [];
    page.dataset.savedScanId = "saved-reddit-scan";
    scanWorkspaceState.preloadPayload = {
      scan_entry_source: "tailoring_suggestions",
      draft: persistedDraft,
    };
    await loadScanWorkspaceDraftState();
    if (JSON.stringify(getCurrentScanWorkspaceExcludedIssueIds()) !== JSON.stringify([issueId])) {
      throw new Error("reload did not restore the saved exclusion");
    }

    setScanWorkspaceIssueExcluded(issueId, false);
    if (getSavedScanWorkspaceExcludedIssueIds()[0] !== issueId || saveButton.disabled) {
      throw new Error("re-include did not become dirty against saved state");
    }
    const savedSignatureBeforeFailure = scanWorkspacePersistenceState.hydratedSignature;
    failSave = true;
    const failed = await saveScanWorkspaceDraftState();
    if (failed !== false || scanWorkspacePersistenceState.hydratedSignature !== savedSignatureBeforeFailure) {
      throw new Error("failed Save incorrectly marked state clean");
    }
    if (saveButton.disabled || saveButton.title !== "") {
      throw new Error("failed Save did not remain available");
    }
    if (wrapper.attrs["data-scan-help"] !== "Save changes") {
      throw new Error("failed dirty Save lost its custom help");
    }

    failSave = false;
    falseSuccess = true;
    const baselineBeforeFalseSuccess = scanWorkspacePersistenceState.hydratedSignature;
    const rejectedFalseSuccess = await saveScanWorkspaceDraftState();
    if (
      rejectedFalseSuccess !== false
      || scanWorkspacePersistenceState.hydratedSignature !== baselineBeforeFalseSuccess
      || saveButton.disabled
    ) {
      throw new Error("HTTP-style false success incorrectly advanced the clean baseline");
    }

    falseSuccess = false;
    await listeners.click();
    if (requests[1]?.url !== "/planning/saved-scan/saved-reddit-scan/state") {
      throw new Error("restored scan used the wrong endpoint: " + requests[1]?.url);
    }
    if (getSavedScanWorkspaceExcludedIssueIds().length !== 0) {
      throw new Error("saving re-include did not persist exclusion removal");
    }
    if (getCurrentScanWorkspacePersistenceSignature() !== scanWorkspacePersistenceState.hydratedSignature) {
      throw new Error("saving re-include did not return to clean state");
    }
    const persistedReincludeDraft = scanWorkspacePersistenceState.loadResponse.draft;
    scanWorkspaceState.excludedScanIssueIds = [issueId];
    hydrateScanWorkspacePersistenceStateFromDraft(persistedReincludeDraft);
    if (getCurrentScanWorkspaceExcludedIssueIds().length !== 0) {
      throw new Error("reload after saved re-include did not restore the active issue state");
    }
    renderScanWorkspacePersistenceStatus();
    if (!saveButton.disabled || wrapper.attrs["data-scan-help"] !== "No changes made") {
      throw new Error("reload after saved re-include did not remain clean");
    }
  })()`, sandbox);
})().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
"""
    result = subprocess.run(
        ["node", "-e", node_test, str(PLANNING_JS), str(SCAN_JS)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_fully_hydrated_review_records_field_trace_and_starts_clean():
    node_test = r"""
const fs = require("fs");
const vm = require("vm");

function makeClassList() {
  return { add() {}, remove() {}, toggle() {}, contains() { return false; } };
}
function makeButton(wrapper) {
  return {
    disabled: false,
    title: "",
    dataset: {},
    attrs: {},
    classList: makeClassList(),
    setAttribute(name, value) { this.attrs[name] = value; },
    removeAttribute(name) { delete this.attrs[name]; if (name === "title") this.title = ""; },
    querySelector() { return null; },
    closest() { return wrapper; },
    addEventListener() {},
  };
}
const saveWrap = {
  attrs: {},
  setAttribute(name, value) { this.attrs[name] = value; },
  removeAttribute(name) { delete this.attrs[name]; },
};
const compareWrap = {
  attrs: {},
  setAttribute(name, value) { this.attrs[name] = value; },
  removeAttribute(name) { delete this.attrs[name]; },
};
const saveButton = makeButton(saveWrap);
const compareButton = makeButton(compareWrap);
const page = {
  dataset: {
    savedScanId: "saved-scan-1",
    resumeName: "resume.pdf",
    scanMode: "review",
  },
};
const nodes = {
  scanWorkspaceSaveBtn: saveButton,
  scanWorkspaceCompareBtn: compareButton,
};
const sandbox = {
  console,
  saveButton,
  compareButton,
  saveWrap,
  compareWrap,
  URL,
  URLSearchParams,
  AbortController,
  CustomEvent: function CustomEvent() {},
  Element: function Element() {},
  setTimeout: () => 0,
  clearTimeout: () => {},
  setInterval: () => 0,
  clearInterval: () => {},
  document: {
    querySelector: (selector) => selector === ".scan-workspace-page" ? page : null,
    querySelectorAll: () => [],
    getElementById: (id) => nodes[id] || null,
    addEventListener: () => {},
    body: { dataset: {}, classList: makeClassList(), appendChild() {} },
  },
  localStorage: { getItem: () => null, setItem: () => {} },
  sessionStorage: { getItem: () => null, setItem: () => {} },
};
sandbox.window = sandbox;
sandbox.window.location = { href: "http://127.0.0.1:8000/scan-workspace?saved_scan_id=saved-scan-1", search: "", pathname: "/scan-workspace" };
sandbox.window.addEventListener = () => {};
sandbox.window.dispatchEvent = () => {};
vm.createContext(sandbox);
vm.runInContext(fs.readFileSync(process.argv[1], "utf8"), sandbox);
vm.runInContext(fs.readFileSync(process.argv[2], "utf8"), sandbox);

vm.runInContext(`(() => {
  const savedDraft = {
    selected_patch_candidate_ids: ["candidate-accepted"],
    rewrite_review_decisions: {
      "candidate-accepted": { state: "accepted", note: "saved note" },
      "candidate-rejected": { state: "rejected", note: "saved note" },
    },
    manual_bullet_edits: { "experience:0": "Saved manual bullet." },
    excluded_scan_issue_ids: ["scan_issue:skills:keyword:beam"],
    personal_details: { name: "Alex Rivera" },
  };
  scanWorkspaceState.preloadPayload = {
    scan_entry_source: "scan_workspace_new_scan",
    ai_optimize_suggestions: [
      { replacement_candidate_id: "candidate-accepted" },
      { replacement_candidate_id: "candidate-rejected" },
    ],
    personal_details: {
      extracted: { email: "alex@example.com" },
      current: {},
    },
    draft: savedDraft,
  };
  captureScanWorkspacePersistenceCheckpoint("A: immediately after preload assignment");
  scanWorkspaceAnnotationState.markers = [
    { id: "marker-accepted", candidateIds: ["candidate-accepted"], decision: "pending" },
    { id: "marker-rejected", candidateIds: ["candidate-rejected"], decision: "pending" },
  ];
  scanWorkspacePersistenceState.loadResponse = {
    ok: true,
    has_saved_draft: true,
    draft: savedDraft,
  };
  hydrateScanWorkspacePersistenceStateFromDraft(savedDraft);
  renderScanWorkspacePersistenceStatus();
  captureScanWorkspacePersistenceCheckpoint("I: after final initial persistence render");

  const trace = scanWorkspacePersistenceState.hydrationTrace;
  const labels = trace.map((entry) => entry.checkpoint);
  const expectedLabels = [
    "A: immediately after preload assignment",
    "B: after saved draft load",
    "C: after excluded issue IDs hydration",
    "D: after personal details hydration",
    "E: after rewrite decisions hydration",
    "F: after manual bullet edits hydration",
    "G: after selected candidate IDs hydration",
    "H: when hydrated signature is assigned",
    "I: after final initial persistence render",
  ];
  if (JSON.stringify(labels) !== JSON.stringify(expectedLabels)) {
    throw new Error("hydration checkpoints differ: " + JSON.stringify(labels));
  }
  const fieldsAt = (checkpoint) => Object.keys(
    trace.find((entry) => entry.checkpoint.startsWith(checkpoint)).differences
  ).sort();
  const expectedBeforeHydration = [
    "excluded_scan_issue_ids",
    "manual_bullet_edits",
    "personal_details",
    "rewrite_review_decisions",
    "selected_patch_candidate_ids",
  ];
  if (JSON.stringify(fieldsAt("B:")) !== JSON.stringify(expectedBeforeHydration)) {
    throw new Error("saved-draft trace did not identify every unhydrated field");
  }
  if (fieldsAt("C:").includes("excluded_scan_issue_ids")) {
    throw new Error("exclusion hydration did not resolve its field difference");
  }
  if (fieldsAt("F:").includes("manual_bullet_edits")) {
    throw new Error("manual-edit hydration did not resolve its field difference");
  }
  if (fieldsAt("H:").length) {
    throw new Error("baseline was captured before hydration finished");
  }
  const finalTrace = trace[trace.length - 1];
  if (Object.keys(finalTrace.differences).length) {
    throw new Error("fully hydrated fields differ: " + JSON.stringify(finalTrace.differences));
  }
  if (finalTrace.current_signature !== finalTrace.hydrated_signature || finalTrace.is_dirty) {
    throw new Error("fully hydrated review did not start clean");
  }
  if (!saveButton.disabled || !compareButton.disabled) {
    throw new Error("clean review actions were enabled");
  }
  if (saveWrap.attrs["data-scan-help"] !== "No changes made") {
    throw new Error("clean Save tooltip is wrong");
  }
  if (saveButton.title || compareButton.title) {
    throw new Error("native title tooltip survived custom tooltip hydration");
  }

  window.scanWorkspacePhase1 = {
    renderPersistenceStatus: () => renderScanWorkspacePersistenceStatus(),
  };
  setScanWorkspaceIssueExcluded("scan_issue:skills:keyword:flink", true);
  captureScanWorkspacePersistenceCheckpoint("mutation: excluded flink");
  if (saveButton.disabled || compareButton.disabled) {
    throw new Error("real exclusion did not enable dirty actions");
  }
  if (saveWrap.attrs["data-scan-help"] !== "Save changes") {
    throw new Error("dirty Save tooltip is wrong");
  }
  if (compareWrap.attrs["data-scan-help"] !== "Compare draft changes") {
    throw new Error("dirty Compare tooltip is wrong");
  }
  const mutation = scanWorkspacePersistenceState.hydrationTrace.at(-1);
  if (!mutation.is_dirty || !mutation.differences.excluded_scan_issue_ids) {
    throw new Error("exclusion field was not the traced dirty cause");
  }
})()`, sandbox);
"""
    result = subprocess.run(
        ["node", "-e", node_test, str(PLANNING_JS), str(SCAN_JS)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_scan_toolbar_save_copy_and_binding_do_not_open_continue_modal():
    route = _scan_route()
    scan_js = SCAN_JS.read_text(encoding="utf-8")
    save_index = route.index('id="scanWorkspaceSaveBtn"')
    save_markup = route[save_index - 400:route.index("</button>", save_index)]
    persistence_status = scan_js.split("function renderScanWorkspacePersistenceStatus()", 1)[1].split(
        "function formatScanWorkspaceSavedAt", 1
    )[0]
    binding = scan_js.split("function bindScanWorkspacePersistenceControls()", 1)[1].split(
        "function maybeWarnBeforeUnload", 1
    )[0]
    continue_flow = scan_js.split("async function continueScanWorkspaceAfterReview()", 1)[1].split(
        "function bindScanWorkspacePersistenceControls", 1
    )[0]

    assert "<span data-scan-action-label>Save</span>" in save_markup
    assert 'data-scan-help="No changes made"' in save_markup
    assert 'title="No changes made"' not in save_markup
    assert 'idleLabel: "Save"' in persistence_status
    assert 'loadingLabel: "Saving..."' in persistence_status
    assert 'syncDisabledHelp(saveBtn, isSaveDisabled, "Save changes")' in persistence_status
    assert 'wrapper.setAttribute("data-scan-help", helpLabel)' in persistence_status
    assert 'button.removeAttribute("title")' in persistence_status
    assert "await saveScanWorkspaceDraftState();" in binding
    assert "continueScanWorkspaceAfterReview" not in binding
    assert "openScanWorkspaceContinueModal" not in binding
    assert "openScanWorkspaceContinueModal();" in continue_flow


def test_scan_ui_c_loading_state_preserves_premium_base_and_variant_classes():
    scan_js = SCAN_JS.read_text(encoding="utf-8")
    assert 'class="scan-workspace-phrase-generate-btn ${scanWorkspacePhraseState.isLoading' in scan_js
    assert 'aria-busy="${scanWorkspacePhraseState.isLoading' in scan_js
    assert "syncScanWorkspacePremiumActionState(saveBtn" in scan_js

    node_test = r"""
const fs = require("fs");
const vm = require("vm");
const source = fs.readFileSync(process.argv[1], "utf8");
const sandbox = {
  console,
  setTimeout: () => 0,
  clearTimeout: () => {},
  CustomEvent: function CustomEvent() {},
  Element: function Element() {},
  document: {
    querySelector: () => null,
    querySelectorAll: () => [],
    getElementById: () => null,
    addEventListener: () => {},
    body: { dataset: {}, classList: { add() {}, remove() {}, toggle() {} } },
  },
  localStorage: { getItem: () => null, setItem: () => {} },
};
sandbox.window = sandbox;
sandbox.window.addEventListener = () => {};
vm.createContext(sandbox);
vm.runInContext(source, sandbox);

const classes = new Set([
  "scan-workspace-toolbar-btn",
  "scan-workspace-toolbar-btn--primary",
  "scan-workspace-continue-btn",
]);
const attrs = {};
const label = { textContent: "Continue" };
const button = {
  disabled: false,
  classList: {
    toggle(name, enabled) { enabled ? classes.add(name) : classes.delete(name); },
  },
  setAttribute(name, value) { attrs[name] = value; },
  querySelector() { return label; },
};

sandbox.syncScanWorkspacePremiumActionState(button, {
  disabled: true,
  loading: true,
  idleLabel: "Save",
  loadingLabel: "Saving...",
});
if (!classes.has("scan-workspace-toolbar-btn")) throw new Error("premium base class was removed");
if (!classes.has("scan-workspace-toolbar-btn--primary")) throw new Error("premium variant was removed");
if (!classes.has("is-loading")) throw new Error("loading state was not added");
if (!button.disabled || attrs["aria-busy"] !== "true" || label.textContent !== "Saving...") {
  throw new Error("loading state was not synchronized");
}

sandbox.syncScanWorkspacePremiumActionState(button, {
  disabled: false,
  loading: false,
  idleLabel: "Save",
  loadingLabel: "Saving...",
});
if (!classes.has("scan-workspace-toolbar-btn") || !classes.has("scan-workspace-toolbar-btn--primary")) {
  throw new Error("premium identity did not survive loading");
}
if (classes.has("is-loading") || button.disabled || attrs["aria-busy"] !== "false") {
  throw new Error("idle state was not restored");
}
"""
    result = subprocess.run(
        ["node", "-e", node_test, str(SCAN_JS)],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr


def test_scan_phrase_options_wrap_complete_multiline_text_without_horizontal_scroll():
    scan_js = SCAN_JS.read_text(encoding="utf-8")
    css = PREMIUM_CSS.read_text(encoding="utf-8")
    renderer = scan_js.split("function renderScanWorkspacePhraseOptionsHtml", 1)[1].split(
        "function getScanWorkspaceMarkerAnchorTexts", 1
    )[0]
    option = css.split("\n.scan-workspace-phrase-option {", 1)[1].split("}", 1)[0]
    option_text = css.split("\n.scan-workspace-phrase-option-text {", 1)[1].split("}", 1)[0]
    popover = css.split(".scan-workspace-suggestion-popover {", 1)[1].split("}", 1)[0]
    popover_body = css.split(".scan-workspace-suggestion-popover-copy {", 1)[1].split("}", 1)[0]

    assert "String(option?.text || \"\").trim()" in renderer
    assert ".slice(" not in renderer
    assert ".substring(" not in renderer
    assert "width: 100%;" in option
    assert "white-space: normal !important;" in option
    assert "white-space: normal !important;" in option_text
    assert "overflow-wrap: anywhere;" in option_text
    assert "text-overflow: clip;" in option_text
    assert "overflow: hidden;" in popover
    assert "overflow-x: hidden;" in popover_body
    assert "overflow-y: auto;" in popover_body


def test_scan_phrase_dialog_is_viewport_bound_with_internal_body_scrolling_and_stable_actions():
    route = _scan_route()
    scan_js = SCAN_JS.read_text(encoding="utf-8")
    css = PREMIUM_CSS.read_text(encoding="utf-8")
    modal_markup = route.split('id="scanWorkspaceSuggestionPopover"', 1)[1].split(
        'class="scan-workspace-review-statusbar"', 1
    )[0]
    popover = css.split(".scan-workspace-suggestion-popover {", 1)[1].split("}", 1)[0]
    body = css.split(".scan-workspace-suggestion-popover-copy {", 1)[1].split("}", 1)[0]
    positioner = scan_js.split("function getScanWorkspaceSuggestionPopoverPosition", 1)[1].split(
        "function positionScanWorkspaceSuggestionPopover", 1
    )[0]

    assert 'id="scanWorkspaceSuggestionPopoverCloseBtn"' in modal_markup
    assert 'id="scanWorkspaceSuggestionPopoverCopy"' in modal_markup
    assert 'id="scanWorkspaceSuggestionRejectBtn"' in modal_markup
    assert 'id="scanWorkspaceSuggestionResetBtn"' in modal_markup
    assert "Generate LLM phrase options" in scan_js
    assert 'data-scan-phrase-option="' in scan_js
    assert 'rejectBtn.textContent = isReplacement' in scan_js
    assert ': "Revert edit";' in scan_js
    assert 'resetBtn.textContent = isReplacement ? "Reset" : "Save edit";' in scan_js
    assert "position: fixed;" in popover
    assert "display: grid;" in popover
    assert "grid-template-rows: auto auto minmax(0, 1fr) auto auto;" in popover
    assert "max-height: calc(100dvh -" in popover
    assert "overflow: hidden;" in popover
    assert "min-height: 0;" in body
    assert "overflow-y: auto;" in body
    assert 'top: "50%"' in positioner
    assert 'transform: "translate(-50%, -50%)"' in positioner
    assert 'document.body.classList.add("scan-workspace-suggestion-dialog-open")' in scan_js
    assert 'document.body.classList.remove("scan-workspace-suggestion-dialog-open")' in scan_js
    assert 'body.scan-workspace-suggestion-dialog-open' in css


def test_scan_phrase_authoritative_option_text_flows_to_textarea_and_saved_edit():
    scan_js = SCAN_JS.read_text(encoding="utf-8")
    renderer = scan_js.split("function renderScanWorkspacePhraseOptionsHtml", 1)[1].split(
        "function getScanWorkspaceMarkerAnchorTexts", 1
    )[0]
    selector = scan_js.split("function applyScanWorkspacePhraseOption", 1)[1].split(
        "function bindScanWorkspaceAnnotationShell", 1
    )[0]
    saver = scan_js.split("async function saveScanWorkspaceGuidanceEditForActiveMarker", 1)[1].split(
        "async function revertScanWorkspaceGuidanceEditForActiveMarker", 1
    )[0]

    assert 'String(option?.text || "").trim()' in renderer
    assert 'const text = String(option?.text || "").trim();' in selector
    assert "textarea.value = text;" in selector
    assert 'const nextText = String(textarea.value || "").trim();' in saver
    assert "[bulletKey]: nextText" in saver


def test_scan_premium_adds_no_framework_dependency_and_keeps_tailoring_unchanged():
    route_and_css = _scan_route() + PREMIUM_CSS.read_text(encoding="utf-8")
    for marker in [
        "react-resizable-panels",
        "@radix-ui",
        "@heroui",
        "tailwindcss",
        "createRoot(",
        "lucide",
    ]:
        assert marker not in route_and_css.lower()

    assert sha256(TAILORING_CSS.read_bytes()).hexdigest() == (
        "5623270c3d551741eb37bc9766cd63e40db5ec297dba9592268bbaf965acd8d2"
    )


def test_scan_keeps_back_to_tailoring_and_admin_diagnostics_contracts():
    route = _scan_route()

    assert "Back to Tailoring" in route
    assert 'href="{back_href_safe}"' in route
    assert 'class="scan-workspace-diagnostics-icon-btn"' in route
    assert 'href="{scan_diagnostics_href_safe}"' in route
    assert 'aria-label="View diagnostics for this scan"' in route
