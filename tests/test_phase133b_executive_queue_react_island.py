from pathlib import Path

from src.app.ui import executive_dashboard


ROOT = Path(__file__).resolve().parents[1]
UI_PATH = ROOT / "src/app/ui.py"
APP_JS_PATH = ROOT / "src/app/static/app.js"
QUEUE_COMPONENT_PATH = ROOT / "frontend/executive-kpi/src/ExecutiveQueue.tsx"
SHARED_TABLE_PATH = ROOT / "frontend/executive-kpi/src/table/TablePrimitives.tsx"
MAIN_PATH = ROOT / "frontend/executive-kpi/src/main.tsx"
BUNDLE_DIR = ROOT / "src/app/static/build/executive-kpi"


def test_executive_page_has_one_queue_island_and_no_hidden_legacy_queue():
    markup = executive_dashboard()

    assert markup.count('id="executiveQueueRoot"') == 1
    assert markup.count('id="executiveKpiRoot"') == 1
    assert "Executive Queue" in markup
    assert "Refresh Status" in markup
    assert "Run Live Pipeline" in markup
    assert 'id="applicationActionModal"' in markup
    assert "Choose what happened after opening the job." in markup

    for retired_id in (
        'id="actionFilter"',
        'id="preferenceFilter"',
        'id="limitInput"',
        'id="executiveUndecidedOnly"',
        'id="applyFiltersBtn"',
        'id="clearFiltersBtn"',
        'id="queueTable"',
        'id="queuePaginationActions"',
    ):
        assert retired_id not in markup


def test_app_js_is_the_only_queue_request_and_review_api_owner():
    app_source = APP_JS_PATH.read_text(encoding="utf-8")
    queue_source = QUEUE_COMPONENT_PATH.read_text(encoding="utf-8")
    main_source = MAIN_PATH.read_text(encoding="utf-8")

    assert 'const EXECUTIVE_QUEUE_STATE_EVENT_NAME = "applylens:executive-queue-state"' in app_source
    assert 'const EXECUTIVE_QUEUE_ACTION_EVENT_NAME = "applylens:executive-queue-action"' in app_source
    assert "function buildBrowseUrl(pageOverride = null)" in app_source
    assert 'appendMultiValueParams(params, "action", actions)' in app_source
    assert 'appendMultiValueParams(params, "preference_id", preferenceIds)' in app_source
    assert 'params.set("undecided_only", undecidedOnly)' in app_source
    assert 'params.set("limit", limit)' in app_source
    assert 'params.set("page", String(page))' in app_source
    assert 'fetchJson(`/browse?${params.toString()}`)' not in queue_source
    assert "fetch(" not in queue_source
    assert 'postJson("/application-actions"' not in queue_source
    assert 'postJson("/application-actions"' in app_source
    assert "OPENED" in app_source
    assert "pendingApplicationJob" in app_source
    assert "handleExecutiveQueueAction" in app_source
    assert "QUEUE_STATE_EVENT" in main_source
    assert "window.addEventListener(QUEUE_STATE_EVENT" in main_source
    assert "applylens:executive-queue-action" in queue_source


def test_queue_component_preserves_existing_filters_views_and_row_meanings():
    source = QUEUE_COMPONENT_PATH.read_text(encoding="utf-8")

    for marker in (
        "Action",
        "Preferences",
        "Limit",
        "Undecided only",
        "Apply Filters",
        "Clear",
        "All Preferences",
        "Detailed",
        "Simple",
        "Rank",
        "Job title",
        "Company",
        "Location",
        "Posted at",
        "Recommendation",
        "Packet",
        "Match",
        "Selected Resume",
        "Runner-up resume",
        "Score gap",
        "Missing requirements",
        "Next step",
        "Priority reason",
        "Review",
        "No jobs match these filters",
    ):
        assert marker in source

    assert "useReactTable" in source
    assert "manualSorting: true" in source
    assert 'type: "sort_change"' in source
    assert "enableSorting: false" in source
    assert 'columnResizeMode: "onChange"' in source
    assert "queueTableColumnWidths" in source
    assert "job_operator_executive_view_mode" in source
    assert "A packet is a review bundle for this job." in source
    assert "It does not apply to the job." in source
    assert "Math.random" not in source


def test_origin_ui_attribution_and_scoped_styles_are_present():
    source = QUEUE_COMPONENT_PATH.read_text(encoding="utf-8")
    styles = (ROOT / "frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")

    assert "Adapted from Origin UI Table by Origin UI" in source
    assert "Adopted 2026-07-17" in source
    for url in (
        "https://21st.dev/community/components/originui/table/card-table",
        "https://21st.dev/@originui/components/table/data-table-with-filters-made-with-tan-stack-table",
        "https://21st.dev/community/components/originui/table/example-of-a-more-complex-table-made-with-tan-stack-table",
    ):
        assert url in source

    assert "#executiveQueueRoot" in styles
    assert 'html[data-theme="dark"] #executiveQueueRoot' in styles
    assert "@tailwind base" not in styles
    assert "!important" not in styles


def test_queue_visual_hierarchy_and_pinned_review_contract_are_scoped():
    source = QUEUE_COMPONENT_PATH.read_text(encoding="utf-8")
    shared = SHARED_TABLE_PATH.read_text(encoding="utf-8")
    styles = (ROOT / "frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")

    assert 'export const QUEUE_REVIEW_COLUMN_WIDTH = 128' in source
    assert 'export const QUEUE_SELECTED_RESUME_MIN_WIDTH = 220' in source
    assert 'size: QUEUE_REVIEW_COLUMN_WIDTH' in source
    assert 'minSize: QUEUE_REVIEW_COLUMN_WIDTH' in source
    assert 'maxSize: QUEUE_REVIEW_COLUMN_WIDTH' in source
    assert 'className="executive-queue-selected-resume-value"' in source
    assert 'row.original.is_applied ? "Reviewed" : "Review"' in source
    assert "<ChevronDown size={15}" in shared
    assert "<ChevronRight size={15}" in shared
    assert 'className={`executive-queue-table-card executive-queue-table-card--${state.viewMode}`}' in source
    assert 'rowClassName={(row) => `executive-queue-row ${row.getIsExpanded() ? "is-expanded" : ""}`.trim()}' in source
    assert 'executive-queue-details executive-queue-details--neutral' in source

    assert "--queue-review-column-width: 128px" in styles
    assert "--queue-row-default: #ffffff" in styles
    assert "--queue-row-default: #111827" in styles
    assert "--queue-row-alternate: #fbfcfe" in styles
    assert "--queue-row-alternate: #141d2c" in styles
    assert "--queue-details-surface: #f8fafc" in styles
    assert "--queue-details-surface: #172033" in styles
    assert "--queue-review-shadow: rgba(15, 23, 42, 0.72)" in styles
    assert "--queue-review-shadow: rgba(2, 6, 23, 0.82)" in styles
    assert "right: 0" in styles
    assert "scroll-padding-right: var(--queue-review-column-width)" in styles
    assert "background: var(--queue-row-alternate)" in styles
    assert "background: var(--queue-row-hover)" in styles
    assert "background: var(--queue-row-expanded)" in styles
    assert "box-shadow: -6px 0 8px -8px var(--queue-review-shadow)" in styles
    assert ".executive-queue-column--selected_resume" in styles
    assert ".executive-queue-details" in styles
    assert "background: var(--queue-details-surface)" in styles
    assert ".executive-queue-sort-btn.is-sorted" in styles
    assert ".executive-queue-table-card--simple" in styles
    assert "linear-gradient(135deg, var(--queue-accent), var(--queue-accent-violet))" in styles


def test_executive_chat_offset_and_pagination_clearance_are_scoped_without_behavior_changes():
    markup = executive_dashboard()
    queue_source = QUEUE_COMPONENT_PATH.read_text(encoding="utf-8")
    shared = SHARED_TABLE_PATH.read_text(encoding="utf-8")
    queue_styles = (ROOT / "frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
    app_styles = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")
    shell = (ROOT / "src/app/ui_shell.py").read_text(encoding="utf-8")

    assert '<body class="executive-dashboard-page">' in markup
    assert "--queue-chat-clearance: calc(64px + 28px + 18px)" in queue_styles
    table_card_rule = queue_styles.split(".executive-queue-table-card {", 2)[2].split("}", 1)[0]
    assert "margin-right" not in table_card_rule
    assert "padding: 9px var(--queue-chat-clearance) 9px 16px" in queue_styles
    assert "--floating-chat-launcher-bottom: max(8px, env(safe-area-inset-bottom))" in app_styles
    assert "bottom: var(--floating-chat-launcher-bottom, max(28px, env(safe-area-inset-bottom)))" in app_styles
    assert 'id="floatingIntelligenceChatButton"' in shell
    assert 'aria-label="Open Job Assistant"' in shell
    assert 'paginationLabel="Executive queue"' in queue_source
    assert 'aria-label={`Previous ${ariaLabel.toLowerCase()}`}' in shared
    assert 'aria-label={`Next ${ariaLabel.toLowerCase()}`}' in shared


def test_canonical_production_assets_are_the_only_generated_queue_assets():
    generated_names = sorted(path.name for path in BUNDLE_DIR.iterdir())
    bundle = (BUNDLE_DIR / "executive-kpi.js").read_text(encoding="utf-8")

    assert generated_names == ["executive-kpi.css", "executive-kpi.js"]
    assert "executiveQueueRoot" in bundle
    assert "applylens:executive-queue-state" in bundle
    assert "applylens:executive-queue-action" in bundle
    assert "localhost" not in bundle


def test_queue_migration_does_not_add_application_submission_or_auto_apply():
    queue_source = QUEUE_COMPONENT_PATH.read_text(encoding="utf-8")
    ui_source = UI_PATH.read_text(encoding="utf-8")

    assert 'type: "review"' in queue_source
    assert "publishQueueAction({ type: \"review\", row: row.original })" in queue_source
    for forbidden in (
        "auto_apply",
        "submit_ats",
        "message_recruiter",
        "mark_applied",
    ):
        assert forbidden not in queue_source.lower()
        assert forbidden not in ui_source.lower()
