from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services
from src.app.application_hub_ui import applications_dashboard
from src.app.decisions_ui import decisions_dashboard
from src.storage.application_actions import read_postgres


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = ROOT / "frontend/executive-kpi/src/OperationalDashboards.tsx"
MAIN = ROOT / "frontend/executive-kpi/src/main.tsx"
SHARED = ROOT / "frontend/executive-kpi/src/table/TablePrimitives.tsx"
STYLES = ROOT / "frontend/executive-kpi/src/styles.css"
DECISIONS_JS = ROOT / "src/app/static/decisions.js"
APPLICATIONS_JS = ROOT / "src/app/static/application_views.js"


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_routes_mount_separate_react_islands_and_preserve_manual_modals() -> None:
    decisions = decisions_dashboard()
    applications = applications_dashboard()
    assert decisions.count('id="decisionsDashboardRoot"') == 1
    assert applications.count('id="applicationsDashboardRoot"') == 1
    assert 'id="applicationActionModal"' in decisions
    assert 'data-status-action="APPLIED"' in decisions
    assert 'data-status-action="SAVED"' in decisions
    assert 'data-status-action="NOT_APPLIED"' in decisions
    assert 'data-status-action="DISMISSED"' in decisions
    assert "/static/build/executive-kpi/executive-kpi.css?v=scheduler_health_react_r1" in decisions
    assert "/static/build/executive-kpi/executive-kpi.css?v=scheduler_health_react_r1" in applications
    assert "/static/build/executive-kpi/executive-kpi.js?v=scheduler_health_react_r1" in decisions
    assert "/static/build/executive-kpi/executive-kpi.js?v=scheduler_health_react_r1" in applications
    assert "/static/decisions.js?v=phase133ef_r5" in decisions
    assert "/static/application_views.js?v=phase133ef_r5" in applications


def test_shared_primitives_and_distinct_bridge_namespaces_are_used() -> None:
    component = _read(COMPONENT)
    main = _read(MAIN)
    shared = _read(SHARED)
    for primitive in ("SharedTableCard", "SharedExpansionButton", "SharedExpandedDetail", "SharedInfoPopover"):
        assert primitive in component
        assert f"export function {primitive}" in shared
    assert "applylens:decisions-dashboard-state" in component
    assert "applylens:applications-dashboard-state" in component
    assert 'document.getElementById("decisionsDashboardRoot")' in main
    assert 'document.getElementById("applicationsDashboardRoot")' in main
    assert "applylens.decisions.columnWidths.v1" in component
    assert "applylens.applications.columnWidths.v1" in component
    assert "if (window.__APPLYLENS_DECISIONS_STATE__) setState(window.__APPLYLENS_DECISIONS_STATE__)" in main
    assert "if (window.__APPLYLENS_APPLICATIONS_STATE__) setState(window.__APPLYLENS_APPLICATIONS_STATE__)" in main


def test_legacy_javascript_remains_the_only_request_and_write_owner() -> None:
    component = _read(COMPONENT)
    decisions = _read(DECISIONS_JS)
    applications = _read(APPLICATIONS_JS)
    assert "fetch(" not in component
    assert 'return `/decisions?${params.toString()}`' in decisions
    assert 'await postJson("/application-actions", { ...payload, application_status: "OPENED" })' in decisions
    assert 'await postJson("/application-actions", { ...job, application_status: status })' in decisions
    assert 'APPLIED: { endpoint: "/applied-jobs"' in applications
    assert 'SAVED: { endpoint: "/saved-jobs"' in applications
    assert 'params.set("application_status"' not in applications
    assert "fetchJson(buildApplicationListUrl())" in applications


def test_bridge_requests_ignore_stale_results_without_adding_request_owners() -> None:
    component = _read(COMPONENT)
    decisions = _read(DECISIONS_JS)
    applications = _read(APPLICATIONS_JS)
    assert "let decisionsRequestId = 0" in decisions
    assert "const requestId = ++decisionsRequestId" in decisions
    assert decisions.count("if (requestId !== decisionsRequestId) return") == 2
    assert "let applicationRequestId = 0" in applications
    assert "const requestId = ++applicationRequestId" in applications
    assert applications.count("if (requestId !== applicationRequestId) return") == 2
    assert "fetch(" not in component


def test_bootstrap_handshake_is_replayable_and_initializes_each_request_owner_once() -> None:
    main = _read(MAIN)
    decisions = _read(DECISIONS_JS)
    applications = _read(APPLICATIONS_JS)
    assert "DECISIONS_READY_EVENT" in main and "applylens:decisions-dashboard-ready" in decisions
    assert "APPLICATIONS_READY_EVENT" in main and "applylens:applications-dashboard-ready" in applications
    assert "window.__APPLYLENS_DECISIONS_REACT_READY__ = true" in main
    assert "window.__APPLYLENS_APPLICATIONS_REACT_READY__ = true" in main
    assert "window.__APPLYLENS_DECISIONS_STATE__" in main
    assert "window.__APPLYLENS_APPLICATIONS_STATE__" in main
    assert "let decisionsDashboardInitialized = false" in decisions
    assert "if (decisionsDashboardInitialized) { publishDecisionsState(); return; }" in decisions
    assert "let applicationsDashboardInitialized = false" in applications
    assert "if (applicationsDashboardInitialized) { publishApplicationsState(); return; }" in applications
    assert 'document.readyState === "loading"' in decisions
    assert 'document.readyState === "loading"' in applications
    assert "{ once: true }" in decisions and "{ once: true }" in applications
    assert decisions.count("function initializeDecisionsDashboard()") == 1
    assert applications.count("function initializeApplicationsDashboard()") == 1


def test_loading_empty_error_and_tab_contracts_are_explicit() -> None:
    component = _read(COMPONENT)
    shared = _read(SHARED)
    assert 'loading={state.status === "loading"}' in component
    assert 'state.activeTab === "APPLIED" ? "No applied jobs yet." : "No jobs have been saved for later."' in component
    assert 'aria-selected={state.activeTab === "APPLIED"}' in component
    assert 'aria-selected={state.activeTab === "SAVED"}' in component
    assert 'tab !== state.activeTab' in component
    assert 'preferences-secondary-action applications-tab' not in component
    assert 'SHARED_NEUTRAL_CONTROL_CLASS} applications-tab' in component
    assert 'active ? "is-active" : "is-inactive"' in component
    assert 'status === "loading" ? Array.from({ length: 5 }' in shared
    assert 'status === "error"' in shared
    assert 'shared-table-pagination--loading' in shared
    assert 'fillAvailableWidth ? "100%" : table.getTotalSize()' in shared


def test_full_width_sticky_action_neutral_loading_and_action_hierarchy() -> None:
    component = _read(COMPONENT)
    styles = _read(STYLES)
    assert component.count("fillAvailableWidth deferPaginationWhileLoading") == 2
    assert component.count('className="operational-primary-action"') == 2
    assert component.count("operational-secondary-action") == 2
    assert ".operational-dashboard { display: grid; width: 100%; min-width: 0;" in styles
    assert ".operational-table-card { width: 100%; min-width: 0;" in styles
    assert ".operational-table-card .shared-table-viewport table { width: 100%; }" in styles
    assert ".operational-table-card .is-sticky-action { position: sticky; right: 0;" in styles
    assert ".operational-table-card .shared-table-skeleton-row:nth-child(odd) td" in styles
    assert ".applications-tabs .applications-tab.is-active" in styles
    assert ".applications-tabs .applications-tab.is-inactive" in styles
    assert ".applications-tabs .applications-tab.is-inactive:hover" in styles
    assert "linear-gradient(115deg, #2563eb, #6d3df2)" in styles
    assert ".applications-tabs .applications-tab {" in styles and "background-image: none" in styles
    assert ".operational-filter-actions .operational-secondary-action" in styles
    assert "background-image: none" in styles
    assert ".operational-table-card > .shared-table-pagination { padding-right: var(--queue-chat-clearance); }" in styles


def test_decisions_uses_shared_premium_multiple_select_and_preserves_machine_values() -> None:
    component = _read(COMPONENT)
    decisions = _read(DECISIONS_JS)
    assert 'from "./filter/FilterSelect"' in component
    assert '<SharedFilterSelect id="decisionFilter"' in component
    assert 'mode="multiple"' in component
    assert 'placeholder="All" allLabel="All"' in component
    for value in ("APPLY", "TAILOR", "SKIP", "HOLD"):
        assert f'"{value}"' in component
    assert "<select" not in component
    assert 'params.append("decision", value)' in decisions
    assert "multi-select" not in decisions


def test_fields_filters_tabs_pagination_and_manual_boundaries_remain() -> None:
    component = _read(COMPONENT)
    decisions = _read(DECISIONS_JS)
    applications = _read(APPLICATIONS_JS)
    for value in ("APPLY", "TAILOR", "SKIP", "HOLD"):
        assert value in component
    for field in ("decision_timestamp", "queue_rank", "planning_action", "selected_resume", "winner_resume", "runner_up_resume", "note"):
        assert field in component
    for field in ("action_timestamp", "application_status", "source_view", "job_url"):
        assert field in component
    assert 'params.append("decision", value)' in decisions
    assert 'params.set("company_contains"' in decisions
    assert 'params.set("title_contains"' in applications
    assert 'params.set("page"' in decisions and 'params.set("page"' in applications
    assert "Applied Jobs" in component and "Saved for Later" in component
    assert 'rel="noopener noreferrer"' in component
    for forbidden in ("auto_apply", "submit_ats", "message_recruiter"):
        assert forbidden not in component.lower()
        assert forbidden not in decisions.lower()
        assert forbidden not in applications.lower()


def _authenticated_client(monkeypatch, owner_user_id: str) -> TestClient:
    def authenticated_guard(request):
        request.state.auth_user = {"user_id": owner_user_id, "email": f"{owner_user_id}@example.test"}
        return None

    monkeypatch.setattr(api, "auth_guard_response", authenticated_guard)
    return TestClient(api.app)


def test_authenticated_decisions_zero_and_applied_row_preserve_owner_and_pagination(monkeypatch) -> None:
    calls = []

    def decisions_payload(**kwargs):
        calls.append(("decisions", kwargs))
        return {
            "rows": [], "count": 0, "total_count": 0, "page": 1, "page_size": 15,
            "total_pages": 1, "has_prev_page": False, "has_next_page": False,
        }

    def applied_payload(**kwargs):
        calls.append(("applied", kwargs))
        return {
            "rows": [{"action_key": "owned-applied", "job_title": "Owned Applied Job", "application_status": "APPLIED", "note": ""}],
            "count": 1, "total_count": 1, "page": 1, "page_size": 15,
            "total_pages": 1, "has_prev_page": False, "has_next_page": False,
        }

    monkeypatch.setattr(services, "decisions_payload", decisions_payload)
    monkeypatch.setattr(services, "applied_jobs_payload", applied_payload)
    client = _authenticated_client(monkeypatch, "owner-a")

    decisions_response = client.get("/decisions", params={"limit": 3, "page": 1})
    applied_response = client.get("/applied-jobs", params={"limit": 3, "page": 1})

    assert decisions_response.status_code == 200
    assert decisions_response.json()["rows"] == []
    assert decisions_response.json()["total_count"] == 0
    assert applied_response.status_code == 200
    assert applied_response.json()["rows"][0]["note"] == ""
    assert applied_response.json()["total_count"] == 1
    assert applied_response.json()["page_size"] == 15
    assert [call[1]["owner_user_id"] for call in calls] == ["owner-a", "owner-a"]


def test_saved_jobs_is_authenticated_owner_scoped_and_status_fixed(monkeypatch) -> None:
    captured = []

    def saved_payload(**kwargs):
        captured.append(kwargs)
        return {
            "rows": [{"action_key": "owned-saved", "job_title": "Owned Saved Job", "application_status": "SAVED"}],
            "count": 1, "total_count": 1, "page": 1, "page_size": 15,
            "total_pages": 1, "has_prev_page": False, "has_next_page": False,
        }

    monkeypatch.setattr(services, "application_actions_payload", saved_payload)
    client = _authenticated_client(monkeypatch, "owner-a")
    response = client.get(
        "/saved-jobs",
        params={"company_contains": "Example", "title_contains": "Engineer", "limit": 30, "page": 2},
    )

    assert response.status_code == 200
    assert response.json()["rows"][0]["application_status"] == "SAVED"
    assert response.json()["total_count"] == 1
    assert captured == [{
        "application_status": "SAVED",
        "company_contains": "Example",
        "title_contains": "Engineer",
        "limit": 30,
        "page": 2,
        "owner_user_id": "owner-a",
    }]


def test_operational_read_routes_reject_missing_authenticated_owner(monkeypatch) -> None:
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    client = TestClient(api.app)

    for path in ("/decisions", "/applied-jobs", "/saved-jobs"):
        response = client.get(path)
        assert response.status_code == 401
        assert response.json() == {"detail": "Authentication required."}


def test_latest_application_action_reader_uses_exact_owner_predicate() -> None:
    sql = read_postgres._build_latest_application_actions_rows_sql(owner_user_id="owner-a")
    assert "WHERE owner_user_id = 'owner-a'" in sql
    assert "DISTINCT ON (action_key)" in sql
    assert "ORDER BY action_key, action_timestamp DESC, action_id DESC" in sql
    assert "owner_user_id = ''" not in sql


def test_saved_payload_reuses_latest_state_status_filters_and_pagination(monkeypatch) -> None:
    def latest_rows(owner_user_id=""):
        assert owner_user_id == "owner-a"
        return [
            {"owner_user_id": "owner-a", "application_status": "SAVED", "job_company": "Example Labs", "job_title": "ML Engineer"},
            {"owner_user_id": "owner-a", "application_status": "SAVED", "job_company": "Different Co", "job_title": "Data Engineer"},
            {"owner_user_id": "owner-a", "application_status": "APPLIED", "job_company": "Example Labs", "job_title": "ML Engineer"},
        ]

    monkeypatch.setattr(services, "_load_latest_application_actions", latest_rows)
    payload = services.application_actions_payload(
        application_status="SAVED",
        company_contains="example",
        title_contains="ml engineer",
        limit=15,
        page=1,
        owner_user_id="owner-a",
    )

    assert payload["rows"] == [{
        "owner_user_id": "owner-a",
        "application_status": "SAVED",
        "job_company": "Example Labs",
        "job_title": "ML Engineer",
    }]
    assert payload["count"] == 1
    assert payload["total_count"] == 1
    assert payload["page"] == 1
    assert payload["page_size"] == 15
    assert payload["total_pages"] == 1
    assert payload["has_prev_page"] is False
    assert payload["has_next_page"] is False
