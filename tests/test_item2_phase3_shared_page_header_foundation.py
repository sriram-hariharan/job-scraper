"""Item 2 Phase 3 — Shared Page Header Foundation (static contract).

Protects: the shared .app-page-header CSS class contract in
src/app/static/app_redesign.css and its application across the seven primary
authenticated surfaces (Overview, Planning, Decisions, Applications, Pipeline,
Scheduler Health, Advanced Diagnostics), without changing route paths, the
global shell toolbar, action IDs/callbacks, or any Item 1 Advanced
Diagnostics behavior (disabled execution, context-card actions).
"""

from pathlib import Path

from tests.support.phase_guard_registry import get_changed_files

ROOT = Path(__file__).resolve().parents[1]

APP_REDESIGN_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")
UI_SOURCE = (ROOT / "src/app/ui.py").read_text(encoding="utf-8")
PLANNING_UI_SOURCE = (ROOT / "src/app/planning_ui.py").read_text(encoding="utf-8")
DECISIONS_UI_SOURCE = (ROOT / "src/app/decisions_ui.py").read_text(encoding="utf-8")
APPLICATION_HUB_UI_SOURCE = (ROOT / "src/app/application_hub_ui.py").read_text(encoding="utf-8")
PIPELINE_DASHBOARD_TSX = (
    ROOT / "frontend/executive-kpi/src/pipeline/PipelineDashboard.tsx"
).read_text(encoding="utf-8")
SCHEDULER_DASHBOARD_TSX = (
    ROOT / "frontend/executive-kpi/src/scheduler/SchedulerHealthDashboard.tsx"
).read_text(encoding="utf-8")
ADVANCED_DIAGNOSTICS_TSX = (
    ROOT / "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx"
).read_text(encoding="utf-8")

SHARED_HEADER_CLASSES = (
    "app-page-header",
    "app-page-header__main",
    "app-page-header__main--with-icon",
    "app-page-header__copy",
    "app-page-header__eyebrow",
    "app-page-header__title-row",
    "app-page-header__title",
    "app-page-header__description",
    "app-page-header__actions",
    "app-page-header__badge",
)


# --- 1. Shared class contract exists ----------------------------------------


def test_app_redesign_css_defines_every_shared_header_class():
    for class_name in SHARED_HEADER_CLASSES:
        assert f".{class_name}" in APP_REDESIGN_CSS, class_name


# --- 2. Shared title rule ----------------------------------------------------


def test_shared_title_rule_has_bounded_sizing_and_restores_normal_wrapping():
    title_rule = APP_REDESIGN_CSS.split(
        ".page .app-page-header .app-page-header__title-row .app-page-header__title {",
        1,
    )[1].split("}", 1)[0]

    assert "clamp(30px, 2.5vw, 36px)" in title_rule
    assert "white-space: normal !important;" in title_rule
    assert "overflow: visible !important;" in title_rule
    assert "overflow-wrap: anywhere !important;" in title_rule
    assert "text-overflow: clip !important;" in title_rule
    # Must not reintroduce the legacy nowrap/ellipsis hero-title pattern.
    assert "nowrap" not in title_rule
    assert "ellipsis" not in title_rule


# --- 3. Shared description contract ------------------------------------------


def test_shared_description_contract_exists():
    description_rule = APP_REDESIGN_CSS.split(
        ".page .app-page-header .app-page-header__main .app-page-header__description,",
        1,
    )[1].split("}", 1)[0]
    assert "max-width: 760px;" in description_rule
    assert "font-size: 14px !important;" in description_rule
    assert "line-height: 1.5 !important;" in description_rule
    assert "white-space: normal !important;" in description_rule


# --- 4. Shared action row uses normal flow -----------------------------------


def test_shared_action_row_uses_normal_flow():
    actions_rule = APP_REDESIGN_CSS.split(".app-page-header__actions {", 1)[1].split("}", 1)[0]
    assert "display: flex;" in actions_rule
    assert "justify-content: flex-end;" in actions_rule
    assert "position: absolute" not in actions_rule
    assert "position: fixed" not in actions_rule


# --- 5-11. Pages migrated ----------------------------------------------------


def test_overview_uses_shared_header_classes():
    assert 'class="page-header app-page-header"' in UI_SOURCE
    assert 'class="page-header-main app-page-header__main"' in UI_SOURCE
    assert 'class="executive-title-row app-page-header__title-row"' in UI_SOURCE
    assert 'class="app-page-header__title"' in UI_SOURCE
    assert 'class="subtext app-page-header__description"' in UI_SOURCE
    assert 'class="header-actions app-page-header__actions"' in UI_SOURCE


def test_planning_uses_shared_header_classes():
    assert 'class="page-header planning-dashboard-header app-page-header"' in PLANNING_UI_SOURCE
    assert 'class="app-page-header__main"' in PLANNING_UI_SOURCE
    assert 'class="planning-dashboard-eyebrow app-page-header__eyebrow"' in PLANNING_UI_SOURCE
    assert 'class="app-page-header__title"' in PLANNING_UI_SOURCE
    assert 'class="subtext app-page-header__description"' in PLANNING_UI_SOURCE
    # No header actions for Planning.
    assert "app-page-header__actions" not in PLANNING_UI_SOURCE.split(
        '<title>Planning</title>', 1
    )[1].split("</header>", 1)[0]


def test_decisions_uses_shared_header_classes():
    assert 'class="operational-dashboard-heading app-page-header"' in DECISIONS_UI_SOURCE
    assert 'class="app-page-header__eyebrow"' in DECISIONS_UI_SOURCE
    assert 'class="app-page-header__title"' in DECISIONS_UI_SOURCE
    assert 'class="app-page-header__description"' in DECISIONS_UI_SOURCE
    assert "OPERATOR REVIEW" in DECISIONS_UI_SOURCE
    assert "<h1" in DECISIONS_UI_SOURCE and ">Decisions</h1>" in DECISIONS_UI_SOURCE


def test_applications_uses_shared_header_classes():
    assert 'class="operational-dashboard-heading app-page-header"' in APPLICATION_HUB_UI_SOURCE
    assert 'class="app-page-header__eyebrow"' in APPLICATION_HUB_UI_SOURCE
    assert 'class="app-page-header__title"' in APPLICATION_HUB_UI_SOURCE
    assert "APPLICATION TRACKING" in APPLICATION_HUB_UI_SOURCE
    assert ">Applications</h1>" in APPLICATION_HUB_UI_SOURCE


def test_pipeline_react_header_uses_shared_classes():
    assert 'className="pipeline-dashboard-header app-page-header"' in PIPELINE_DASHBOARD_TSX
    assert 'className="app-page-header__main"' in PIPELINE_DASHBOARD_TSX
    assert 'className="pipeline-dashboard-eyebrow app-page-header__eyebrow"' in PIPELINE_DASHBOARD_TSX
    assert 'className="app-page-header__title"' in PIPELINE_DASHBOARD_TSX
    assert 'className="app-page-header__description"' in PIPELINE_DASHBOARD_TSX
    assert 'className="pipeline-dashboard-actions app-page-header__actions"' in PIPELINE_DASHBOARD_TSX


def test_scheduler_health_react_header_uses_shared_classes():
    assert 'className="scheduler-health-header app-page-header"' in SCHEDULER_DASHBOARD_TSX
    assert 'className="scheduler-health-header-copy app-page-header__main"' in SCHEDULER_DASHBOARD_TSX
    assert 'className="scheduler-health-title-row app-page-header__title-row"' in SCHEDULER_DASHBOARD_TSX
    assert 'className="app-page-header__title"' in SCHEDULER_DASHBOARD_TSX
    assert "app-page-header__badge" in SCHEDULER_DASHBOARD_TSX
    assert 'className="app-page-header__description"' in SCHEDULER_DASHBOARD_TSX
    assert 'className="scheduler-health-header-actions app-page-header__actions"' in SCHEDULER_DASHBOARD_TSX


def test_advanced_diagnostics_react_header_uses_shared_classes():
    assert 'className="advanced-diagnostics-header app-page-header"' in ADVANCED_DIAGNOSTICS_TSX
    assert "app-page-header__main--with-icon" in ADVANCED_DIAGNOSTICS_TSX
    assert "app-page-header__copy" in ADVANCED_DIAGNOSTICS_TSX
    assert 'className="app-page-header__title"' in ADVANCED_DIAGNOSTICS_TSX
    assert "app-page-header__badge" in ADVANCED_DIAGNOSTICS_TSX


# --- 12-15. Preserved behavior ------------------------------------------------


def test_overview_action_ids_are_unchanged():
    assert 'id="refreshStatusBtn"' in UI_SOURCE
    assert 'id="runPipelineBtn"' in UI_SOURCE
    assert "Refresh Status" in UI_SOURCE
    assert "Run Live Pipeline" in UI_SOURCE


def test_pipeline_button_labels_and_callback_ownership_are_unchanged():
    assert "onClick={onRefresh}" in PIPELINE_DASHBOARD_TSX
    assert "onClick={onRun}" in PIPELINE_DASHBOARD_TSX
    assert '"Refreshing" : "Refresh Status"' in PIPELINE_DASHBOARD_TSX
    assert '"Pipeline Running..." : "Run Pipeline"' in PIPELINE_DASHBOARD_TSX


def test_scheduler_refresh_behavior_markers_remain():
    assert "onClick={onRefresh}" in SCHEDULER_DASHBOARD_TSX
    assert "Last refreshed at" in SCHEDULER_DASHBOARD_TSX
    assert "Not refreshed yet" in SCHEDULER_DASHBOARD_TSX


def test_advanced_diagnostics_context_actions_remain_outside_main_header():
    header_source = ADVANCED_DIAGNOSTICS_TSX.split(
        "function AdvancedDiagnosticsHeader()", 1
    )[1].split("\nfunction ", 1)[0]
    assert "Back to scan" not in header_source
    assert "Change scan" not in header_source
    # They still exist elsewhere (the Scan Context card, per Item 1 Phase 4).
    assert "Back to scan" in ADVANCED_DIAGNOSTICS_TSX
    assert "Change scan" in ADVANCED_DIAGNOSTICS_TSX


# --- 16-17. No route/shell changes -------------------------------------------


def test_no_route_path_changed():
    assert '@router.get("/", response_class=HTMLResponse)' in UI_SOURCE
    assert '@router.get("/pipeline", response_class=HTMLResponse)' in UI_SOURCE
    assert '@router.get("/scheduler", response_class=HTMLResponse)' in UI_SOURCE
    assert '@router.get("/planning", response_class=HTMLResponse)' in PLANNING_UI_SOURCE
    assert '@router.get("/advanced-diagnostics", response_class=HTMLResponse)' in PLANNING_UI_SOURCE
    assert '@router.get("/decisions-ui", response_class=HTMLResponse)' in DECISIONS_UI_SOURCE
    assert '@router.get("/applications", response_class=HTMLResponse)' in APPLICATION_HUB_UI_SOURCE


def test_no_global_shell_toolbar_markup_changed():
    changed = get_changed_files(ROOT)
    if "src/app/ui_shell.py" in changed:
        # Item 2 Phase 4 Correction Pass 1 intentionally adds a "diagnostics"
        # inline SVG icon to fix the profile-menu dark-mode icon bug; this is
        # the only shell change expected at this point (see
        # tests/test_item2_phase4_profile_corrections_and_legacy_route_retirement.py).
        ui_shell_source = (ROOT / "src/app/ui_shell.py").read_text(encoding="utf-8")
        assert '"diagnostics": (' in ui_shell_source
        assert '_icon_svg("diagnostics")' in ui_shell_source
    assert "src/app/static/shell.js" not in changed


# --- 18. Cache marker scoping -------------------------------------------------


def test_new_cache_marker_appears_only_on_intended_affected_route_assets():
    # The Phase 3 marker still owns the executive-kpi bundle references on the
    # seven Phase 3 routes; app_redesign.css's own marker was legitimately
    # bumped again in Item 2 Phase 4 (a further app_redesign.css change),
    # covered by tests/test_item2_phase4_secondary_page_headers.py.
    marker = "item2_phase3_shared_header_r1"
    occurrences = (
        UI_SOURCE.count(marker)
        + PLANNING_UI_SOURCE.count(marker)
        + DECISIONS_UI_SOURCE.count(marker)
        + APPLICATION_HUB_UI_SOURCE.count(marker)
    )
    # 7 migrated routes x 2 bundle asset references (executive-kpi.css, executive-kpi.js).
    assert occurrences == 14


# --- 19. Scan Workspace / Tailoring Workspace exceptions untouched -----------


def test_scan_and_tailoring_workspace_title_exceptions_remain_unchanged():
    assert "body .scan-workspace-page.page > .page-header h1" in APP_REDESIGN_CSS
    assert "body .tailoring-workspace-page.page > .page-header h1" in APP_REDESIGN_CSS
    assert ".scan-workspace-page .page-header h1" in APP_REDESIGN_CSS
    assert ".tailoring-workspace-page .page-header h1" in APP_REDESIGN_CSS


# --- 20. No diagnostic execution enabled -------------------------------------


def test_no_diagnostic_execution_was_enabled():
    run_button_block = ADVANCED_DIAGNOSTICS_TSX.split('className="advanced-diagnostics-run-btn"', 1)[1].split(
        "</button>", 1
    )[0]
    assert "disabled" in run_button_block
    assert "onClick" not in run_button_block
    assert "Execution is not enabled yet. Selections are for admin review only." in run_button_block
