from pathlib import Path

from src.app.planning_ui import planning_dashboard


ROOT = Path(__file__).resolve().parents[1]
PLANNING_UI = ROOT / "src/app/planning_ui.py"
PLANNING_JS = ROOT / "src/app/static/planning.js"
PLANNING_CSS = ROOT / "src/app/static/planning_dashboard.css"
PLANNING_REACT = ROOT / "frontend/executive-kpi/src/PlanningWorklist.tsx"
EXECUTIVE_REACT = ROOT / "frontend/executive-kpi/src/ExecutiveQueue.tsx"
SHARED_TABLE = ROOT / "frontend/executive-kpi/src/table/TablePrimitives.tsx"
SHARED_FILTER = ROOT / "frontend/executive-kpi/src/filter/FilterSelect.tsx"
FRONTEND_MAIN = ROOT / "frontend/executive-kpi/src/main.tsx"
FRONTEND_CSS = ROOT / "frontend/executive-kpi/src/styles.css"
API = ROOT / "src/app/api.py"
SERVICES = ROOT / "src/app/services.py"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_planning_route_mounts_the_scoped_react_islands_and_canonical_bundle() -> None:
    html = planning_dashboard()

    assert '<body class="planning-dashboard-page">' in html
    assert 'class="page planning-dashboard-shell"' in html
    assert html.count('id="planningSummaryRoot"') == 1
    assert html.count('id="planningFiltersRoot"') == 1
    assert html.count('id="planningWorklistRoot"') == 1
    assert 'id="planningTable"' not in html
    assert 'id="planningTableBody"' not in html
    assert '/static/planning_dashboard.css?v=phase133g_s1_r1' in html
    assert '/static/build/executive-kpi/executive-kpi.css?v=scheduler_health_react_r1' in html
    assert '/static/build/executive-kpi/executive-kpi.js?v=scheduler_health_react_r1' in html
    assert '/static/planning.js?v=phase133g_s1_r1' in html


def test_executive_and_planning_import_the_same_real_table_primitives() -> None:
    planning = _read(PLANNING_REACT)
    executive = _read(EXECUTIVE_REACT)
    shared = _read(SHARED_TABLE)

    for component in (
        "SharedTableCard",
        "SharedExpansionButton",
        "SharedMatchMeter",
        "SharedExpandedDetail",
    ):
        assert component in planning
        assert component in executive
        assert f"export function {component}" in shared
    for component in ("SharedResizableHeader", "SharedPagination"):
        assert f"export function {component}" in shared
        assert f"<{component}" in shared
    assert "SharedInfoPopover" in planning
    assert "SharedJobPreview" in planning
    assert "from \"./table/TablePrimitives\"" in planning
    assert "from \"./table/TablePrimitives\"" in executive


def test_planning_keeps_the_exact_nine_column_order_and_truthful_fields() -> None:
    planning = _read(PLANNING_REACT)
    columns = planning[planning.index("function buildPlanningColumns"):planning.index("export function PlanningWorklist")]
    ordered_ids = (
        'id: "expand"',
        'accessorKey: "queue_rank"',
        'id: "job_title"',
        'id: "posted_at"',
        'id: "recommendation"',
        'id: "winner_score"',
        'id: "selected_resume"',
        'id: "packet_status"',
        'id: "next_step"',
    )
    assert [columns.index(marker) for marker in ordered_ids] == sorted(columns.index(marker) for marker in ordered_ids)
    for label in (
        "Rank",
        "Job",
        "Posted at",
        "Review readiness",
        "Match score",
        "Resume selection",
        "Packet / workspace",
        "Next step",
    ):
        assert label in columns
    assert 'row.original.posted_at' in columns
    assert "recommendation(row.original)" in columns
    assert "row.original.winner_score" in columns
    assert "selectedResume(row.original)" in columns


def test_shared_expansion_is_collapsed_by_default_and_resets_on_result_changes() -> None:
    planning = _read(PLANNING_REACT)
    shared = _read(SHARED_TABLE)

    assert 'useState<string>("")' in planning
    assert 'useEffect(() => setExpandedId(""), [state.resultKey, state.pagination.page, state.sort.key, state.sort.direction])' in planning
    assert "onExpandedChange" in planning
    assert "newlyExpanded" in planning
    assert "getRowCanExpand: () => true" in planning
    assert "row.getIsExpanded() ?" in shared
    assert 'className="shared-table-detail-row"' in shared
    assert "SharedExpansionButton" in planning
    assert "planning-row-expand-btn" not in planning
    assert "linear-gradient" not in planning


def test_planning_resizing_uses_shared_tanstack_boundaries_and_separate_storage() -> None:
    planning = _read(PLANNING_REACT)
    shared = _read(SHARED_TABLE)
    executive = _read(EXECUTIVE_REACT)

    assert 'PLANNING_COLUMN_WIDTH_STORAGE_KEY = "applylens.planning.columnWidths.v1"' in planning
    assert "QUEUE_COLUMN_WIDTH_STORAGE_KEY" in executive
    assert "PLANNING_COLUMN_WIDTH_STORAGE_KEY" not in executive
    assert 'columnResizeMode: "onChange"' in planning
    assert "header.getResizeHandler()" in shared
    assert "header.column.getCanResize()" in shared
    assert "header.getSize()" in shared
    assert 'role="separator"' in shared
    assert 'aria-label={`Resize ${resizeLabel(header)} column`}' in shared
    assert "Array.isArray(parsed)" in planning
    assert "WIDTH_BOUNDS" in planning


def test_planning_job_preview_match_meter_and_compact_information_popovers_are_shared() -> None:
    planning = _read(PLANNING_REACT)
    shared = _read(SHARED_TABLE)
    css = _read(FRONTEND_CSS)

    assert '<SharedJobPreview title={title} location={location}>' in planning
    assert "shared-job-preview__popover" in shared
    assert "<strong>{title || \"Untitled job\"}</strong>" in shared
    assert "<span>{location || \"Location unavailable\"}</span>" in shared
    assert '<SharedMatchMeter value={row.original.winner_score}' in planning
    assert 'role="progressbar"' in shared
    assert "Math.abs(parsed) <= 1 ? parsed * 100 : parsed" in shared
    assert "SharedInfoPopover" in planning
    assert "shared-info-popover__trigger" in shared
    assert ".shared-info-popover__trigger" in css
    assert "linear-gradient" not in css[css.index(".shared-info-popover__trigger"):css.index(".shared-info-popover__content")]


def test_both_tables_render_synchronized_top_and_bottom_shared_pagination() -> None:
    planning = _read(PLANNING_REACT)
    executive = _read(EXECUTIVE_REACT)
    shared = _read(SHARED_TABLE)

    assert 'pageControls("top")' in shared
    assert 'pageControls("bottom")' in shared
    assert "SharedTableCard" in planning
    assert "SharedTableCard" in executive
    assert 'paginationLabel="Planning worklist"' in planning
    assert 'title="Planning worklist"' in planning
    assert "Planning view · ${state.pagination.totalCount} total job" in planning
    assert "onPageChange={(page) => publishPlanningAction" in planning


def test_planning_javascript_remains_the_only_browse_and_action_owner() -> None:
    js = _read(PLANNING_JS)
    planning = _read(PLANNING_REACT)

    assert "function buildPlanningUrl(" in js
    assert "return `/browse?${params.toString()}`" in js
    loader = js[js.index("async function loadPlanningTable"):js.index("function clearPlanningFilters")]
    assert loader.count("fetchJson(url") == 1
    assert 'PLANNING_WORKLIST_STATE_EVENT_NAME = "applylens:planning-worklist-state"' in js
    assert 'PLANNING_WORKLIST_ACTION_EVENT_NAME = "applylens:planning-worklist-action"' in js
    assert "publishPlanningWorklistState()" in js
    assert 'action.type === "page_change"' in js
    assert 'action.type === "sort_change"' in js
    assert 'action.type !== "next_step"' in js
    assert "handleTailoringClick(buttonLike)" in js
    assert "handleGenerateSuggestionsClick(buttonLike)" in js
    assert 'fetch("/browse' not in planning
    assert "fetch(" not in planning


def test_planning_bridge_mounts_summary_and_worklist_from_one_state_event() -> None:
    main = _read(FRONTEND_MAIN)

    assert 'document.getElementById("planningSummaryRoot")' in main
    assert 'document.getElementById("planningWorklistRoot")' in main
    assert "window.__APPLYLENS_PLANNING_WORKLIST_STATE__" in main
    assert "window.addEventListener(PLANNING_STATE_EVENT" in main
    assert "<PlanningSummary state={state}" in main
    assert "<PlanningWorklist state={state}" in main


def test_filter_toolbar_preserves_all_controls_and_uses_a_dedicated_actions_group() -> None:
    html = planning_dashboard()
    planning = _read(PLANNING_REACT)
    shared_filter = _read(SHARED_FILTER)
    css = _read(FRONTEND_CSS)

    assert 'id="planningFiltersRoot"' in html
    for filter_id in (
        "planningActionFilter",
        "planningPreferenceFilter",
        "planningWinnerBucket",
        "planningTailoringFilter",
        "planningLimitInput",
        "planningApplyFiltersBtn",
        "planningClearFiltersBtn",
    ):
        assert f'id="{filter_id}"' in planning
    assert planning.count("<SharedFilterSelect") == 4
    assert 'className="planning-react-segmented"' in planning
    assert 'className="planning-react-filter-actions"' in planning
    assert "export function SharedFilterSelect" in shared_filter
    actions_start = css.index(".planning-react-filter-actions {")
    actions = css[actions_start:css.index("}", actions_start) + 1]
    assert "display: grid" in actions
    assert "grid-template-columns: minmax(132px, 1fr) minmax(78px, auto)" in actions
    assert "min-width: 0" in actions
    assert "position: absolute" not in actions
    assert "margin: -" not in actions
    assert "transform:" not in actions

    responsive_start = css.index("@media (max-width: 1180px)", css.index(".planning-react-filter-grid"))
    responsive = css[responsive_start:css.index("@media (max-width: 760px)", responsive_start)]
    assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in responsive
    assert ".planning-react-limit-field" in responsive
    assert "grid-column: 2" in responsive
    assert "grid-column: 3 / -1" in responsive

    limit_start = css.index(".planning-react-limit-field input")
    limit_rule = css[limit_start:css.index("}", limit_start)]
    assert "width: 100%" in limit_rule
    assert "min-width: 0" in limit_rule


def test_summary_uses_real_metrics_and_compact_help_without_demo_trends() -> None:
    planning = _read(PLANNING_REACT)
    js = _read(PLANNING_JS)

    for key in ("total", "readyForReview", "packetReady", "needsDecision"):
        assert f'key: "{key}"' in planning
    assert "planningTableState.metrics =" in js
    assert 'String(row?.action || "").trim().toUpperCase() === "APPLY"' in js
    assert "normalizeBool(row?.packet_generation_allowed)" in js
    assert "!String(row?.operator_decision || \"\").trim()" in js
    assert "SharedInfoPopover" in planning
    assert "trend" not in planning.lower()
    assert ">?</button>" not in planning


def test_readiness_capsules_use_semantic_fills_while_advisory_stays_neutral() -> None:
    css = _read(FRONTEND_CSS)

    for selector in (
        ".planning-react-badge--ready",
        ".planning-react-badge--tailor",
        ".planning-react-badge--choice",
        ".planning-react-badge--later",
    ):
        start = css.index(selector)
        rule = css[start:css.index("}", start)]
        assert "background:" in rule
        assert "color-mix(" in rule

    shared_start = css.index(".planning-react-badge,\n.planning-react-advisory")
    shared_rule = css[shared_start:css.index("}", shared_start)]
    assert "background: var(--queue-surface-muted)" in shared_rule


def test_detail_content_retains_runner_up_gap_priority_and_advisory_readback() -> None:
    planning = _read(PLANNING_REACT)
    details = planning[planning.index("function PlanningDetails"):planning.index("function buildPlanningColumns")]

    for label in (
        "Full location",
        "Prefilter relevance",
        "AI evaluation",
        "Runner-up resume",
        "Runner-up score",
        "Score gap",
        "Operator decision",
        "Priority reason",
        "Missing requirements",
        "View AI Review",
    ):
        assert label in planning
    assert "Advisory only. Does not override the selected resume or score." in planning


def test_pinned_next_step_and_chat_clearance_use_the_shared_table_contract() -> None:
    planning = _read(PLANNING_REACT)
    shared = _read(SHARED_TABLE)
    css = _read(FRONTEND_CSS)

    assert 'stickyColumnId="next_step"' in planning
    assert "PLANNING_NEXT_STEP_COLUMN_WIDTH = 190" in planning
    assert 'cell.column.id === stickyColumnId ? "is-sticky-action"' in shared
    assert "right: 0" in css
    assert "--shared-sticky-width" in css
    assert "padding: 9px var(--queue-chat-clearance) 9px 16px" in css
    assert "Generate Suggestions" in _read(PLANNING_JS)


def test_planning_endpoint_contract_and_safety_boundaries_are_unchanged() -> None:
    api = _read(API)
    services = _read(SERVICES)
    ui = _read(PLANNING_UI)
    js = _read(PLANNING_JS)

    assert '@app.get("/browse")' in api
    assert "services.browse_payload(" in api
    assert "def browse_payload(" in services
    for field in ("rows", "total_count", "page", "page_size", "total_pages"):
        assert f'"{field}"' in services
    assert "/pipeline/run" not in ui
    assert "auto-apply" not in ui.lower()
    loader = js[js.index("async function loadPlanningTable"):js.index("function clearPlanningFilters")]
    assert "setInterval(" not in loader
    assert "window.location.assign" not in loader


def test_origin_ui_attribution_and_light_dark_responsive_contracts_remain() -> None:
    planning = _read(PLANNING_REACT)
    css = _read(FRONTEND_CSS)

    assert "https://21st.dev/community/components/originui/table/default" in planning
    assert "data-theme=\"dark\"" in css
    assert "@media (max-width: 760px)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
