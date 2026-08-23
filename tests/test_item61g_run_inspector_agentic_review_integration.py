"""Item 6.1G read-only run inspector and Agentic Review integration boundary."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.app import api


ROOT = Path(__file__).resolve().parents[1]
COMPONENT_PATH = (
    ROOT / "frontend/executive-kpi/src/agentic/AgenticOperationsDashboard.tsx"
)
MODEL_PATH = ROOT / "frontend/executive-kpi/src/agentic/agenticOperationsModel.ts"
PROFILE_UI_PATH = ROOT / "src/app/profile_ui.py"
API_PATH = ROOT / "src/app/api.py"
SERVICES_PATH = ROOT / "src/app/services.py"
OVERVIEW_PATH = "/profile/admin/agentic-operations/overview"
REVIEW_ROUTE = "/profile/pipeline-runs/{run_id}/agentic-review"

ITEM61G_PRODUCTION_FILES = {
    "frontend/executive-kpi/src/agentic/AgenticOperationsDashboard.tsx",
    "frontend/executive-kpi/src/styles.css",
    "src/app/static/build/executive-kpi/executive-kpi.js",
    "src/app/static/build/executive-kpi/executive-kpi.css",
}


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _client_as(monkeypatch: pytest.MonkeyPatch, user: dict) -> TestClient:
    def guard(request):
        request.state.auth_user = dict(user)
        return None

    monkeypatch.setattr(api, "auth_guard_response", guard)
    return TestClient(api.app)


def test_existing_agentic_review_route_is_exact_and_remains_admin_protected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    profile_source = _source(PROFILE_UI_PATH)
    route_marker = f'@router.get("{REVIEW_ROUTE}", response_class=HTMLResponse)'
    assert profile_source.count(route_marker) == 1
    route = profile_source.split(route_marker, 1)[1].split("\n\n@router.", 1)[0]
    assert "_require_profile_admin_user(request)" in route

    forbidden = _client_as(
        monkeypatch,
        {"user_id": "owner", "is_admin": False, "access_level": "user"},
    ).get("/profile/pipeline-runs/run-61g/agentic-review")
    assert forbidden.status_code == 403
    assert forbidden.json() == {"detail": "Admin access required."}


def test_operations_links_to_existing_encoded_route_without_owner_context() -> None:
    component = _source(COMPONENT_PATH)
    assert (
        "`/profile/pipeline-runs/${encodeURIComponent(runId)}/agentic-review`"
        in component
    )
    assert "Open Agentic Review" in component
    link_source = component.split("Open Agentic Review", 1)[0].rsplit("<a ", 1)[1]
    assert "owner" not in link_source


def test_overview_remains_the_only_agentic_operations_data_endpoint() -> None:
    api_source = _source(API_PATH)
    services_source = _source(SERVICES_PATH)
    model = _source(MODEL_PATH)
    component = _source(COMPONENT_PATH)

    assert api_source.count(f'@app.get("{OVERVIEW_PATH}")') == 1
    assert api_source.count("/profile/admin/agentic-operations/") == 1
    assert model.count("fetch(") == 1
    assert (model + component).count(OVERVIEW_PATH) == 1
    assert "agentic_operations_run_inspector" not in api_source
    assert "agentic_operations_run_inspector" not in services_source


def test_operations_adds_no_detailed_readback_or_mutation_network_owner() -> None:
    combined = _source(MODEL_PATH) + "\n" + _source(COMPONENT_PATH)
    for endpoint in (
        "/agent-trace",
        "/evidence-chain-trace",
        "/agentic-review-data",
    ):
        assert endpoint not in combined
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        assert f'method: "{method}"' not in combined
    assert "setInterval(" not in combined
    assert "setTimeout(" not in combined


def test_item61g_ownership_excludes_review_advanced_and_backend_production_files() -> None:
    assert ITEM61G_PRODUCTION_FILES.isdisjoint(
        {
            "src/app/api.py",
            "src/app/services.py",
            "src/app/profile_ui.py",
            "src/app/static/agentic_review.js",
            "src/app/static/agentic_review.css",
            "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx",
            "frontend/executive-kpi/src/diagnostics/advancedDiagnosticsModel.ts",
        }
    )
