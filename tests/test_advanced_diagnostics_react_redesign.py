"""Advanced Diagnostics React Command Center (Item 1 Phase 3).

Protects: admin-only enforcement and owner scoping on the /advanced-diagnostics
route (src/app/planning_ui.py), the React-island server contract (mode, saved
scan options, selected context, and route hrefs serialized into
window.__APPLYLENS_ADVANCED_DIAGNOSTICS_STATE__), the invalid-saved-scan
correction (a saved_scan_id with no owner-scoped match and no artifact
context renders an "invalid" mode rather than placeholder-context controls),
and removal of the old server-rendered selector/diagnostics-grid markup and
inline JS controllers now owned by
frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services

ROOT = Path(__file__).resolve().parents[1]
PLANNING_UI_SOURCE = (ROOT / "src/app/planning_ui.py").read_text(encoding="utf-8")

ADMIN_USER = {"user_id": "admin-1", "email": "admin@example.test", "is_admin": True}
NON_ADMIN_USER = {"user_id": "user-1", "email": "user@example.test", "is_admin": False, "access_level": "user"}

SAVED_SCAN_ROWS = [
    {
        "scan_id": "scan-42",
        "job_company": "Acme Corp",
        "job_title": "Staff Engineer",
        "resume_name": "resume_v2.pdf",
        "scan_status": "Reviewed",
        "scan_timestamp": "2026-07-01T00:00:00Z",
        "scan_source": "saved",
    }
]


def _client_as(monkeypatch, user: dict | None) -> TestClient:
    def guard(request):
        if user is not None:
            request.state.auth_user = dict(user)
        return None

    monkeypatch.setattr(api, "auth_guard_response", guard)
    return TestClient(api.app)


def _mock_saved_scans(monkeypatch, rows: list[dict], captured_owner_ids: list[str] | None = None) -> None:
    def fake_payload(*, limit: int = 50, owner_user_id: str = ""):
        if captured_owner_ids is not None:
            captured_owner_ids.append(owner_user_id)
        return {"ok": True, "source": "postgres", "count": len(rows), "saved_scans": rows}

    monkeypatch.setattr(services, "profile_saved_scans_payload", fake_payload)


# --- Access control ---------------------------------------------------------


def test_unauthenticated_request_remains_401(monkeypatch) -> None:
    _mock_saved_scans(monkeypatch, SAVED_SCAN_ROWS)
    client = _client_as(monkeypatch, None)
    response = client.get("/advanced-diagnostics")
    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


def test_non_admin_remains_403(monkeypatch) -> None:
    _mock_saved_scans(monkeypatch, SAVED_SCAN_ROWS)
    client = _client_as(monkeypatch, NON_ADMIN_USER)
    response = client.get("/advanced-diagnostics")
    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required."}


def test_admin_receives_the_react_root_and_initial_state(monkeypatch) -> None:
    _mock_saved_scans(monkeypatch, SAVED_SCAN_ROWS)
    client = _client_as(monkeypatch, ADMIN_USER)
    response = client.get("/advanced-diagnostics")
    assert response.status_code == 200
    assert 'id="advancedDiagnosticsRoot"' in response.text
    assert "window.__APPLYLENS_ADVANCED_DIAGNOSTICS_STATE__ = " in response.text
    assert '"mode": "hub"' in response.text or '"mode":"hub"' in response.text


def test_saved_scan_retrieval_remains_owner_scoped(monkeypatch) -> None:
    captured_owner_ids: list[str] = []
    _mock_saved_scans(monkeypatch, SAVED_SCAN_ROWS, captured_owner_ids)
    client = _client_as(monkeypatch, ADMIN_USER)
    response = client.get("/advanced-diagnostics")
    assert response.status_code == 200
    assert captured_owner_ids == [ADMIN_USER["user_id"]]


# --- Mode contract -----------------------------------------------------------


def test_hub_state_when_saved_scans_exist_and_none_selected(monkeypatch) -> None:
    _mock_saved_scans(monkeypatch, SAVED_SCAN_ROWS)
    client = _client_as(monkeypatch, ADMIN_USER)
    response = client.get("/advanced-diagnostics")
    assert response.status_code == 200
    assert '"mode": "hub"' in response.text
    assert '"scanId": "scan-42"' in response.text
    assert '"company": "Acme Corp"' in response.text


def test_empty_state_when_no_saved_scans_exist(monkeypatch) -> None:
    _mock_saved_scans(monkeypatch, [])
    client = _client_as(monkeypatch, ADMIN_USER)
    response = client.get("/advanced-diagnostics")
    assert response.status_code == 200
    assert '"mode": "empty"' in response.text
    assert '"savedScanOptions": []' in response.text


def test_valid_saved_scan_context(monkeypatch) -> None:
    _mock_saved_scans(monkeypatch, SAVED_SCAN_ROWS)
    client = _client_as(monkeypatch, ADMIN_USER)
    response = client.get("/advanced-diagnostics", params={"saved_scan_id": "scan-42"})
    assert response.status_code == 200
    assert '"mode": "context"' in response.text
    assert '"company": "Acme Corp"' in response.text
    assert '"title": "Staff Engineer"' in response.text
    assert '"contextId": "scan-42"' in response.text
    assert "backToScanHref" in response.text


def test_valid_artifact_context_without_saved_scan_id(monkeypatch) -> None:
    _mock_saved_scans(monkeypatch, SAVED_SCAN_ROWS)
    client = _client_as(monkeypatch, ADMIN_USER)
    response = client.get(
        "/advanced-diagnostics",
        params={"company": "Globex", "title": "Analyst", "tailoring_json": "outputs/globex__tailoring.json"},
    )
    assert response.status_code == 200
    assert '"mode": "context"' in response.text
    assert '"company": "Globex"' in response.text
    assert '"title": "Analyst"' in response.text


def test_invalid_unavailable_saved_scan_id_renders_invalid_mode(monkeypatch) -> None:
    _mock_saved_scans(monkeypatch, SAVED_SCAN_ROWS)
    client = _client_as(monkeypatch, ADMIN_USER)
    response = client.get("/advanced-diagnostics", params={"saved_scan_id": "not-a-real-scan"})
    assert response.status_code == 200
    assert '"mode": "invalid"' in response.text
    assert '"context": null' in response.text
    # Must not leak whether a foreign user's scan exists via placeholder context metadata.
    assert "Scan diagnostics context loaded" not in response.text


def test_back_to_scan_query_preservation(monkeypatch) -> None:
    _mock_saved_scans(monkeypatch, SAVED_SCAN_ROWS)
    client = _client_as(monkeypatch, ADMIN_USER)
    response = client.get(
        "/advanced-diagnostics",
        params={"saved_scan_id": "scan-42", "output_dir": "outputs/custom"},
    )
    assert response.status_code == 200
    assert "saved_scan_id=scan-42" in response.text
    assert "output_dir=outputs" in response.text


# --- Safety / route surface --------------------------------------------------


def test_no_new_api_route_was_introduced() -> None:
    api_source = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
    assert "advanced-diagnostics" not in api_source


def test_generated_bundle_is_referenced(monkeypatch) -> None:
    _mock_saved_scans(monkeypatch, SAVED_SCAN_ROWS)
    client = _client_as(monkeypatch, ADMIN_USER)
    response = client.get("/advanced-diagnostics")
    assert "/static/build/executive-kpi/executive-kpi.css" in response.text
    assert "/static/build/executive-kpi/executive-kpi.js" in response.text
    assert "scan_workspace.js" not in response.text
    assert "planning.js" not in response.text


def test_old_inline_controllers_are_absent() -> None:
    assert "data-advanced-diagnostics-open" not in PLANNING_UI_SOURCE
    assert "data-admin-diagnostics-clear" not in PLANNING_UI_SOURCE
    assert "data-admin-diagnostics-run" not in PLANNING_UI_SOURCE
    assert "getElementById(\"advancedDiagnosticsScanSelect\")" not in PLANNING_UI_SOURCE


def test_old_duplicate_diagnostic_markup_is_absent() -> None:
    assert "_scan_workspace_advanced_diagnostics_html" not in PLANNING_UI_SOURCE
    assert "_advanced_diagnostics_selector_html" not in PLANNING_UI_SOURCE
    assert "admin-diagnostics-shell" not in PLANNING_UI_SOURCE
    assert "scanWorkspaceAdvancedDiagnostics" not in PLANNING_UI_SOURCE
