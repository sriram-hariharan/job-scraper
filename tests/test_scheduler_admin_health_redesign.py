"""Scheduler Health admin-only redesign.

Protects: admin-only enforcement on the /scheduler HTML route and the
/scheduler/summary, /scheduler/history, /scheduler/postgres-status APIs
(src/app/ui.py, src/app/api.py), the shared-shell navigation change that
removes Scheduler from normal-user navigation while keeping Pipeline
(src/app/ui_shell.py), the admin diagnostics discovery entry
(src/app/ui_shell.py + src/app/static/shell.js), and preservation of every
existing scheduler payload field, route, and single-request-owner contract.

Scheduler Health Visual Correction migrated the page from a classic
server-rendered table to a React island (frontend/executive-kpi/src/scheduler)
that is the sole /scheduler/summary request owner; the presentation-layer
assertions below read the React source instead of src/app/ui.py, which now
contains only the shared shell + a bare mount root.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services
from src.app.ui_shell import NAV_GROUPS, NAV_ITEMS, render_top_shell

ROOT = Path(__file__).resolve().parents[1]
UI_SOURCE = (ROOT / "src/app/ui.py").read_text(encoding="utf-8")
SHELL_SOURCE = (ROOT / "src/app/ui_shell.py").read_text(encoding="utf-8")
SHELL_JS = (ROOT / "src/app/static/shell.js").read_text(encoding="utf-8")
MAIN_TSX = (ROOT / "frontend/executive-kpi/src/main.tsx").read_text(encoding="utf-8")
SCHEDULER_DASHBOARD_TSX = (
    ROOT / "frontend/executive-kpi/src/scheduler/SchedulerHealthDashboard.tsx"
).read_text(encoding="utf-8")
SCHEDULER_MODEL_TS = (
    ROOT / "frontend/executive-kpi/src/scheduler/schedulerModel.ts"
).read_text(encoding="utf-8")
SERVICES_SOURCE = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
REACT_CSS = (ROOT / "frontend/executive-kpi/src/styles.css").read_text(encoding="utf-8")
APP_REDESIGN_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")

ADMIN_USER = {"user_id": "admin-1", "email": "admin@example.test", "is_admin": True}
NON_ADMIN_USER = {"user_id": "user-1", "email": "user@example.test", "is_admin": False, "access_level": "user"}

FAKE_SUMMARY_PAYLOAD = {
    "ok": True,
    "limit": 25,
    "contract_health": {
        "ok": True,
        "checks": {"seed_sql_matches_artifact": True, "init_sql_matches_artifact": True},
        "all_checks_pass": True,
    },
    "history": {
        "jsonl_path": "outputs/scheduler_history.jsonl",
        "jsonl_row_count": 3,
        "postgres_row_count": 3,
        "count_matches": True,
    },
    "latest_runs_by_job": [
        {"run_id": "r1", "job_name": "live_pipeline", "status": "succeeded", "return_code": 0,
         "started_at": "2026-07-20T01:00:00Z", "finished_at": "2026-07-20T01:05:00Z"},
    ],
    "recent_postgres_runs": [
        {"run_id": "r1", "job_name": "live_pipeline", "status": "succeeded", "return_code": 0,
         "started_at": "2026-07-20T01:00:00Z", "finished_at": "2026-07-20T01:05:00Z"},
    ],
    "recent_jsonl_runs": [
        {"run_id": "r1", "job_name": "live_pipeline", "status": "succeeded", "return_code": 0,
         "started_at": "2026-07-20T01:00:00Z", "finished_at": "2026-07-20T01:05:00Z"},
    ],
    "postgres_summary": {
        "job_definition_count": 1,
        "active_job_count": 1,
        "run_history_count": 3,
        "success_count": 3,
        "failure_count": 0,
    },
    "postgres_command_text": "SELECT 1",
}


def _client_as(monkeypatch, user: dict | None) -> TestClient:
    def guard(request):
        if user is not None:
            request.state.auth_user = dict(user)
        return None

    monkeypatch.setattr(api, "auth_guard_response", guard)
    return TestClient(api.app)


# --- Access control -------------------------------------------------------


def test_admin_can_open_scheduler_page(monkeypatch) -> None:
    client = _client_as(monkeypatch, ADMIN_USER)
    response = client.get("/scheduler")
    assert response.status_code == 200
    assert "Scheduler Health" in response.text


def test_non_admin_cannot_open_scheduler_page(monkeypatch) -> None:
    client = _client_as(monkeypatch, NON_ADMIN_USER)
    response = client.get("/scheduler")
    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required."}


def test_unauthenticated_access_to_scheduler_page_follows_existing_auth_contract(monkeypatch) -> None:
    client = _client_as(monkeypatch, None)
    response = client.get("/scheduler")
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


def test_admin_can_call_scheduler_summary_api(monkeypatch) -> None:
    monkeypatch.setattr(services, "scheduler_operator_summary_payload", lambda **kwargs: FAKE_SUMMARY_PAYLOAD)
    client = _client_as(monkeypatch, ADMIN_USER)
    response = client.get("/scheduler/summary")
    assert response.status_code == 200
    assert response.json() == FAKE_SUMMARY_PAYLOAD


def test_non_admin_receives_existing_admin_forbidden_api_response(monkeypatch) -> None:
    monkeypatch.setattr(services, "scheduler_operator_summary_payload", lambda **kwargs: FAKE_SUMMARY_PAYLOAD)
    client = _client_as(monkeypatch, NON_ADMIN_USER)
    response = client.get("/scheduler/summary")
    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required."}


def test_unauthenticated_scheduler_summary_follows_existing_auth_contract(monkeypatch) -> None:
    client = _client_as(monkeypatch, None)
    response = client.get("/scheduler/summary")
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


def test_scheduler_history_endpoint_is_admin_only(monkeypatch) -> None:
    monkeypatch.setattr(services, "scheduler_history_payload", lambda **kwargs: {"ok": True, "rows": []})
    admin_response = _client_as(monkeypatch, ADMIN_USER).get("/scheduler/history")
    assert admin_response.status_code == 200

    non_admin_response = _client_as(monkeypatch, NON_ADMIN_USER).get("/scheduler/history")
    assert non_admin_response.status_code == 403
    assert non_admin_response.json() == {"detail": "Admin access required."}

    unauth_response = _client_as(monkeypatch, None).get("/scheduler/history")
    assert unauth_response.status_code == 401
    assert unauth_response.json() == {"detail": "Authentication required."}


def test_scheduler_postgres_status_endpoint_is_admin_only(monkeypatch) -> None:
    monkeypatch.setattr(
        services,
        "scheduler_postgres_status_payload",
        lambda **kwargs: {"ok": True, "postgres": {}},
    )
    admin_response = _client_as(monkeypatch, ADMIN_USER).get("/scheduler/postgres-status")
    assert admin_response.status_code == 200

    non_admin_response = _client_as(monkeypatch, NON_ADMIN_USER).get("/scheduler/postgres-status")
    assert non_admin_response.status_code == 403
    assert non_admin_response.json() == {"detail": "Admin access required."}

    unauth_response = _client_as(monkeypatch, None).get("/scheduler/postgres-status")
    assert unauth_response.status_code == 401
    assert unauth_response.json() == {"detail": "Authentication required."}


def test_page_and_api_use_the_same_admin_semantics() -> None:
    # Both the HTML route and the JSON route call the identical semantics:
    # is_admin truthy OR access_level == "admin"; 401 unauthenticated, 403 non-admin.
    assert "def _is_admin_user(user: dict) -> bool:" in UI_SOURCE
    assert 'access_level == "admin"' in UI_SOURCE
    assert "status_code=401" in UI_SOURCE and "Authentication required." in UI_SOURCE
    assert "status_code=403" in UI_SOURCE and "Admin access required." in UI_SOURCE
    api_source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    assert 'access_level != "admin"' in api_source
    assert "_require_admin_user(http_request)" in api_source


# --- Navigation ------------------------------------------------------------


def test_scheduler_absent_from_normal_user_sidebar_navigation() -> None:
    labels = {label for _group, items in NAV_GROUPS for (label, _href, _icon) in items}
    hrefs = {href for _label, href, _icon in NAV_ITEMS}
    assert "Scheduler" not in labels
    assert "/scheduler" not in hrefs


def test_pipeline_remains_in_normal_navigation() -> None:
    labels = {label for _group, items in NAV_GROUPS for (label, _href, _icon) in items}
    hrefs = {href for _label, href, _icon in NAV_ITEMS}
    assert "Pipeline" in labels
    assert "/pipeline" in hrefs


def test_admin_has_a_discoverable_scheduler_health_entry_via_admin_diagnostics_surface() -> None:
    assert SHELL_SOURCE.count('id="profileSchedulerHealthLink"') == 1
    entry = SHELL_SOURCE.split('id="profileSchedulerHealthLink"', 1)[0].rsplit("<a", 1)[1]
    entry += SHELL_SOURCE.split('id="profileSchedulerHealthLink"', 1)[1].split("</a>", 1)[0]
    assert 'href="/scheduler"' in entry
    assert 'data-admin-only="true"' in entry
    assert "hidden" in entry
    assert "Scheduler Health" in entry
    # Reuses the existing admin-only toggle convention (mirrors Advanced Diagnostics).
    assert SHELL_JS.count('qs("profileSchedulerHealthLink")') == 1
    assert "profileSchedulerHealthLink.classList.toggle(\"hidden\", !isAdmin)" in SHELL_JS


def test_scheduler_health_entry_is_not_duplicated() -> None:
    assert SHELL_SOURCE.count("Scheduler Health") == 1


# --- Route / payload preservation ------------------------------------------


def test_scheduler_url_is_unchanged() -> None:
    assert '@router.get("/scheduler", response_class=HTMLResponse)' in UI_SOURCE


def test_scheduler_summary_endpoint_path_is_unchanged() -> None:
    api_source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    assert '@app.get("/scheduler/summary")' in api_source


def test_existing_payload_keys_remain_available_in_service_and_react_model() -> None:
    for key in (
        "contract_health",
        "history",
        "latest_runs_by_job",
        "recent_postgres_runs",
        "recent_jsonl_runs",
        "postgres_summary",
    ):
        assert key in SCHEDULER_MODEL_TS
    assert '"contract_health": contract' in SERVICES_SOURCE
    assert '"latest_runs_by_job": postgres_block.get("latest_runs_by_job", [])' in SERVICES_SOURCE
    assert '"recent_postgres_runs": postgres_block.get("recent_runs", [])' in SERVICES_SOURCE
    assert '"recent_jsonl_runs": latest_jsonl_rows' in SERVICES_SOURCE


def test_configuration_integrity_checks_remain_available() -> None:
    assert "seed_sql_matches_artifact" in SCHEDULER_DASHBOARD_TSX
    assert "init_sql_matches_artifact" in SCHEDULER_DASHBOARD_TSX
    assert "all_checks_pass" in SCHEDULER_DASHBOARD_TSX
    assert "Configuration Integrity" in SCHEDULER_DASHBOARD_TSX


def test_file_audit_tab_is_removed_but_jsonl_fields_remain_backward_compatible() -> None:
    # File Audit is removed from the UI entirely (dashboard no longer reads
    # recent_jsonl_runs or renders a File Audit tab)...
    assert "File Audit" not in SCHEDULER_DASHBOARD_TSX
    assert "file_audit" not in SCHEDULER_DASHBOARD_TSX
    assert "recent_jsonl_runs" not in SCHEDULER_DASHBOARD_TSX
    # ...but the payload typing stays backward-compatible with the unchanged
    # backend response, which still returns these fields.
    assert "recent_jsonl_runs" in SCHEDULER_MODEL_TS
    assert "jsonl_row_count" in SCHEDULER_MODEL_TS
    assert "count_matches" in SCHEDULER_MODEL_TS


def test_database_history_rows_remain_available() -> None:
    assert "recent_postgres_runs" in SCHEDULER_DASHBOARD_TSX
    assert "Database History" in SCHEDULER_DASHBOARD_TSX


def test_job_status_uses_latest_runs_by_job() -> None:
    assert "latest_runs_by_job" in SCHEDULER_DASHBOARD_TSX
    assert "Job Status" in SCHEDULER_DASHBOARD_TSX
    assert "sortJobStatusRows" in SCHEDULER_DASHBOARD_TSX


def test_storage_sync_and_count_matches_are_removed_from_the_health_calculation() -> None:
    # count_matches/jsonl_row_count no longer factor into overall health or any
    # displayed metric; the payload field itself remains typed (see
    # test_file_audit_tab_is_removed_but_jsonl_fields_remain_backward_compatible).
    assert "count_matches" not in SCHEDULER_DASHBOARD_TSX
    assert "Storage sync" not in SCHEDULER_DASHBOARD_TSX
    assert "storage sync" not in SCHEDULER_DASHBOARD_TSX.lower()


def test_overall_health_depends_only_on_contract_health() -> None:
    assert "const overallHealthy = Boolean(payload) && contractOk;" in SCHEDULER_DASHBOARD_TSX
    assert "postgres_summary?.run_history_count" in SCHEDULER_DASHBOARD_TSX
    assert "Recorded runs" in SCHEDULER_DASHBOARD_TSX


def test_no_fake_time_period_labels_introduced() -> None:
    for source in (SCHEDULER_DASHBOARD_TSX.lower(), UI_SOURCE.lower()):
        assert "today" not in source
        assert "last 24" not in source
        assert "past 24 hours" not in source


def test_no_new_scheduler_write_or_control_action_introduced() -> None:
    for forbidden in (
        'method: "POST"', "method: 'POST'",
        'method: "PUT"', "method: 'PUT'",
        'method: "DELETE"', "method: 'DELETE'",
        "/scheduler/run", "/scheduler/stop", "/scheduler/trigger",
    ):
        assert forbidden not in SCHEDULER_DASHBOARD_TSX


def test_react_island_is_the_sole_scheduler_summary_request_owner() -> None:
    # Exactly one fetch() call anywhere in the scheduler React module, and the
    # classic page source no longer performs its own competing fetch.
    assert SCHEDULER_MODEL_TS.count("fetch(") == 1
    assert '"/scheduler/summary?limit=25"' in SCHEDULER_MODEL_TS
    assert "fetch(" not in SCHEDULER_DASHBOARD_TSX
    scheduler_route = UI_SOURCE[UI_SOURCE.index('@router.get("/scheduler"'):]
    assert "fetch(" not in scheduler_route
    assert "<script>" not in scheduler_route


def test_scheduler_page_contains_exactly_one_react_mount_root() -> None:
    scheduler_route = UI_SOURCE[UI_SOURCE.index('@router.get("/scheduler"'):]
    assert scheduler_route.count('id="schedulerHealthDashboardRoot"') == 1
    assert "Loading scheduler health" in scheduler_route
    assert "<noscript>" in scheduler_route


def test_scheduler_page_no_longer_contains_the_old_inline_render_owner() -> None:
    scheduler_route = UI_SOURCE[UI_SOURCE.index('@router.get("/scheduler"'):]
    for legacy_marker in (
        "schedulerTableBody", "schedulerJobStatusBody", "schedulerRunHistoryBody",
        "refreshSchedulerSummaryBtn", "activateTab(", "renderContractRows",
    ):
        assert legacy_marker not in scheduler_route


def test_main_tsx_mounts_the_scheduler_health_island() -> None:
    assert 'document.getElementById("schedulerHealthDashboardRoot")' in MAIN_TSX
    assert "SchedulerHealthDashboard" in MAIN_TSX


def test_shared_table_and_filter_primitives_are_reused() -> None:
    assert "SharedTableCard" in SCHEDULER_DASHBOARD_TSX
    assert "SharedFilterSelect" in SCHEDULER_DASHBOARD_TSX
    assert "useReactTable" in SCHEDULER_DASHBOARD_TSX
    assert 'from "../table/TablePrimitives"' in SCHEDULER_DASHBOARD_TSX
    assert 'from "../filter/FilterSelect"' in SCHEDULER_DASHBOARD_TSX


def test_job_status_and_run_history_share_one_table_surface() -> None:
    assert SCHEDULER_DASHBOARD_TSX.count("function SchedulerRunsCard") == 1
    assert SCHEDULER_DASHBOARD_TSX.count("<SharedTableCard") == 2
    assert 'title="Scheduler Runs"' in SCHEDULER_DASHBOARD_TSX


def test_diagnostics_are_not_permanently_rendered_in_the_page_flow() -> None:
    assert "if (!open) return null;" in SCHEDULER_DASHBOARD_TSX
    assert "function DiagnosticsModal" in SCHEDULER_DASHBOARD_TSX


def test_diagnostics_modal_has_accessible_dialog_semantics() -> None:
    assert 'role="dialog"' in SCHEDULER_DASHBOARD_TSX
    assert 'aria-modal="true"' in SCHEDULER_DASHBOARD_TSX
    assert 'event.key === "Escape"' in SCHEDULER_DASHBOARD_TSX
    assert "triggerRef.current?.focus()" in SCHEDULER_DASHBOARD_TSX


def test_configuration_checks_render_as_status_rows_not_a_legacy_table() -> None:
    assert "function ConfigStatusRow" in SCHEDULER_DASHBOARD_TSX
    assert "scheduler-config-row" in SCHEDULER_DASHBOARD_TSX


def test_light_dark_structural_classes_remain_supported() -> None:
    assert "Scheduler Health" in REACT_CSS
    assert 'html[data-theme="dark"] #schedulerHealthDashboardRoot' in REACT_CSS
    assert "--scheduler-ink" in REACT_CSS


def test_classic_shell_js_ownership_is_unaffected() -> None:
    # The scheduler page still loads the shared classic shell.js for the app
    # shell/sidebar/theme toggle; it is not a competing request owner for
    # /scheduler/summary (that fetch lives only in the React module).
    scheduler_route = UI_SOURCE[UI_SOURCE.index('@router.get("/scheduler"'):]
    assert "/static/shell.js" in scheduler_route
    assert "/scheduler/summary" not in SHELL_JS


# --- Visual polish (Scheduler Health Final Visual Polish) ------------------


def test_page_title_uses_the_scoped_scheduler_class_not_a_global_display_style() -> None:
    # The <h1> carries no page-specific "display title" class of its own —
    # only the shared Item 2 Phase 3 title class. Its compact size comes from
    # a selector scoped to that shared class, overriding the shared global h1
    # rule that otherwise renders every <h1> oversized (clamp(38px, 5vw,
    # 74px)). The override lives in the classic app_redesign.css — the only
    # stylesheet already using !important to win that cascade fight — not in
    # the React stylesheet. (Formerly a scheduler-specific override; Item 2
    # Phase 3 consolidated it into the shared .app-page-header__title rule,
    # which is now the sole owner of this sizing.)
    assert '<h1 className="app-page-header__title">Scheduler Health</h1>' in SCHEDULER_DASHBOARD_TSX
    assert "!important" not in REACT_CSS
    assert (
        ".page .app-page-header .app-page-header__title-row .app-page-header__title {"
        in APP_REDESIGN_CSS
    )
    header_override = APP_REDESIGN_CSS[
        APP_REDESIGN_CSS.index(
            ".page .app-page-header .app-page-header__title-row .app-page-header__title {"
        ):
    ]
    header_override = header_override[: header_override.index("}") + 1]
    assert "font-size: clamp(30px, 2.5vw, 36px) !important" in header_override
    # The old scheduler-specific override is gone now that the shared class owns it.
    assert ".scheduler-health-page #schedulerHealthDashboardRoot h1 {" not in APP_REDESIGN_CSS


def test_scheduler_refresh_is_inside_scheduler_content_not_the_shared_shell() -> None:
    assert 'className="scheduler-health-header app-page-header"' in SCHEDULER_DASHBOARD_TSX
    header_block = SCHEDULER_DASHBOARD_TSX[
        SCHEDULER_DASHBOARD_TSX.index('function DashboardHeader'):
        SCHEDULER_DASHBOARD_TSX.index('function OverviewPanel')
    ]
    assert "scheduler-refresh-btn" in header_block
    assert "scheduler-last-refreshed" in header_block
    # Not part of ui_shell.py's shared top-right toolbar.
    assert "scheduler-refresh-btn" not in SHELL_SOURCE
    assert "scheduler-last-refreshed" not in SHELL_SOURCE


def test_populated_table_does_not_receive_a_forced_height_class() -> None:
    assert ".scheduler-shared-table-card .shared-table-viewport { min-height: 0; }" in REACT_CSS
    # The shared 286px minimum (tuned for large paginated tables) is untouched
    # for every other page; only the scheduler card's instance is overridden.
    assert ".shared-table-viewport {" in REACT_CSS
    base_rule = REACT_CSS[REACT_CSS.index(".shared-table-viewport {"):]
    base_rule = base_rule[: base_rule.index("}") + 1]
    assert "min-height: 286px" in base_rule


def test_only_one_pagination_region_is_rendered() -> None:
    assert (
        ".scheduler-shared-table-card .shared-table-header-actions > .shared-table-pagination { display: none; }"
        in REACT_CSS
    )


def test_one_page_results_hide_duplicate_prev_next_controls() -> None:
    assert ":has(> button:first-child:disabled):has(> button:last-child:disabled)" in REACT_CSS
    # Both scheduler pagination objects are hardcoded to a single page, so the
    # collapse rule always applies for this page without touching other pages.
    assert '"totalPages": 1' not in SCHEDULER_DASHBOARD_TSX  # not JSON-shaped in TSX
    assert "totalPages: 1" in SCHEDULER_DASHBOARD_TSX


def test_run_history_filters_are_scoped_to_the_run_history_branch_only() -> None:
    job_status_branch = SCHEDULER_DASHBOARD_TSX[
        SCHEDULER_DASHBOARD_TSX.index('if (activeTab === "job_status") {'):
        SCHEDULER_DASHBOARD_TSX.index('return (\n    <SharedTableCard', SCHEDULER_DASHBOARD_TSX.index('if (activeTab === "job_status") {'))
    ]
    assert "SharedFilterSelect" not in job_status_branch


def test_scheduler_rows_are_not_colored_by_job_only_by_semantic_failed_state() -> None:
    for forbidden_pattern in ("job_name}--", "row--${", "scheduler-run-row--"):
        assert forbidden_pattern not in SCHEDULER_DASHBOARD_TSX
    assert 'rowClassName={(row) => `scheduler-run-row ${isFailedStatus(row.original.status) ? "is-attention" : ""}`}' in SCHEDULER_DASHBOARD_TSX


def test_failed_status_styling_remains_semantic() -> None:
    assert ".scheduler-run-row.is-attention { box-shadow: inset 3px 0 0 var(--scheduler-red); }" in REACT_CSS
    assert "isFailedStatus" in SCHEDULER_DASHBOARD_TSX


def test_diagnostics_table_has_bounded_overflow_behavior() -> None:
    assert ".scheduler-diagnostics-table-viewport { overflow-x: auto;" in REACT_CSS
    assert ".scheduler-diagnostics-table-viewport table { width: 100%; min-width: 720px;" in REACT_CSS
    assert 'width: min(820px, calc(100vw - 48px))' in REACT_CSS


def test_full_run_id_remains_accessible_via_title_when_visually_truncated() -> None:
    assert 'title={runId}' in SCHEDULER_DASHBOARD_TSX
    assert "text-overflow: ellipsis" in REACT_CSS


def test_diagnostics_modal_locks_background_scroll_while_open() -> None:
    assert 'document.body.style.overflow = "hidden"' in SCHEDULER_DASHBOARD_TSX
    assert "previousBodyOverflow" in SCHEDULER_DASHBOARD_TSX


def test_shared_table_tokens_are_defined_so_rows_use_neutral_shared_backgrounds() -> None:
    # Root cause of the "pastel row" bug: SharedTableCard/SharedFilterSelect
    # read --queue-* tokens; without a scheduler-scoped definition they were
    # unset, and the page's own gradient background showed through the rows.
    assert "#schedulerHealthDashboardRoot {" in REACT_CSS
    root_block = REACT_CSS[REACT_CSS.index("#schedulerHealthDashboardRoot {"):]
    root_block = root_block[: root_block.index("}") + 1]
    for token in ("--queue-row-default", "--queue-row-alternate", "--queue-border", "--queue-surface"):
        assert token in root_block
