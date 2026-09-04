"""Focused integration and safety checks for Item 7.1C diagnostics activation."""

import json
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
COMPONENT = (
    ROOT / "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx"
).read_text(encoding="utf-8")
PLANNING_UI = (ROOT / "src/app/planning_ui.py").read_text(encoding="utf-8")

ADMIN = {"user_id": "admin-71c", "email": "admin@example.test", "is_admin": True}
SCAN = {
    "scan_id": "scan-71c",
    "job_company": "Acme",
    "job_title": "Engineer",
    "resume_name": "resume.pdf",
    "scan_status": "Reviewed",
    "scan_timestamp": "2026-08-23T00:00:00Z",
    "scan_source": "saved",
}


def _client(monkeypatch) -> TestClient:
    def guard(request):
        request.state.auth_user = dict(ADMIN)
        return None

    monkeypatch.setattr(api, "auth_guard_response", guard)
    return TestClient(api.app)


def _state_from_html(html: str) -> dict:
    marker = "window.__APPLYLENS_ADVANCED_DIAGNOSTICS_STATE__ = "
    payload = html.split(marker, 1)[1].split(";", 1)[0]
    return json.loads(payload)


def test_context_initial_state_hydrates_owner_scoped_persisted_readbacks(monkeypatch) -> None:
    owners: list[str] = []

    def scans(*, limit=50, owner_user_id=""):
        owners.append(owner_user_id)
        return {"ok": True, "saved_scans": [SCAN]}

    def report(scan_id, *, owner_user_id=""):
        owners.append(owner_user_id)
        assert scan_id == "scan-71c"
        return {
            "diagnostic_state": {
                "version": 1,
                "validated_readbacks": {
                    "live_tailoring_suggestion_readback": {
                        "validation_status": "valid",
                        "fallback_used": False,
                    }
                },
            },
            "jd_llm_extraction_readback": {
                "validation_status": "valid",
                "fallback_used": False,
            },
        }

    monkeypatch.setattr(services, "profile_saved_scans_payload", scans)
    monkeypatch.setattr(services, "saved_scan_report_payload", report)
    response = _client(monkeypatch).get(
        "/advanced-diagnostics", params={"saved_scan_id": "scan-71c"}
    )

    assert response.status_code == 200
    state = _state_from_html(response.text)
    assert state["mode"] == "context"
    assert state["diagnosticState"]["version"] == 1
    assert (
        state["diagnosticState"]["ambient_readbacks"]["jd_llm_extraction_readback"]
        ["validation_status"]
        == "valid"
    )
    assert owners == [ADMIN["user_id"], ADMIN["user_id"]]


def test_foreign_or_missing_scan_remains_neutral_and_does_not_load_report(monkeypatch) -> None:
    report = lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("must not load"))
    monkeypatch.setattr(
        services,
        "profile_saved_scans_payload",
        lambda **kwargs: {"ok": True, "saved_scans": [SCAN]},
    )
    monkeypatch.setattr(services, "saved_scan_report_payload", report)
    response = _client(monkeypatch).get(
        "/advanced-diagnostics", params={"saved_scan_id": "foreign-scan"}
    )
    state = _state_from_html(response.text)
    assert state["mode"] == "invalid"
    assert state["diagnosticState"] == {}


def test_frontend_uses_existing_state_route_and_has_no_mount_fetch() -> None:
    assert "/planning/saved-scan/${encodeURIComponent(state.selectedScanId)}/state" in COMPONENT
    assert "diagnostics_execution: true" in COMPONENT
    # Dialog/drawer effects manage only local presentation; diagnostic execution
    # remains exclusively inside the explicit action.
    assert "dialog.showModal()" in COMPONENT
    assert "useEffect(() => { request" not in COMPONENT
    assert "/advanced-diagnostics/execute" not in COMPONENT
    assert "setInterval" not in COMPONENT
    assert "setTimeout" not in COMPONENT
    retry_observability = 'addBoolean("retry_performed", "Retry performed");'
    assert retry_observability in COMPONENT
    assert '"Retry tailoring analysis"' in COMPONENT
    assert COMPONENT.count('runStage("live_tailoring_suggestion")') == 1
    assert "retryCount" not in COMPONENT
    assert "automaticRetry" not in COMPONENT


def test_human_inputs_are_explicit_and_no_automatic_application_mutation_exists() -> None:
    assert "accepted_exact_change_proposal_ids" in COMPONENT
    assert "verified_artifact_operator_decision_value" in COMPONENT
    assert '["rejected", "needs_changes", "accepted"]' in COMPONENT
    assert 'useState("accepted")' not in COMPONENT
    assert "Nothing is selected by default." in COMPONENT
    for forbidden in (
        "/application-actions",
        "mark-applied",
        "auto_apply",
        "auto_submit",
        "resume mutation",
    ):
        assert forbidden not in COMPONENT.lower()


def test_advanced_route_owns_only_the_item71c_bundle_cache_key() -> None:
    route = PLANNING_UI.split(
        '@router.get("/advanced-diagnostics", response_class=HTMLResponse)', 1
    )[1].split("\ndef scan_workspace(", 1)[0]
    marker = "eucalyptus_primary_shell_r1"
    assert f"executive-kpi.css?v={marker}" in route
    assert f"executive-kpi.js?v={marker}" in route
    assert "item2_phase3_shared_header_r1" not in route
