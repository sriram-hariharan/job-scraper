"""Item 6.1E Agentic Operations read-only overview UI integration."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.app import api


ROOT = Path(__file__).resolve().parents[1]
UI_SOURCE = (ROOT / "src/app/ui.py").read_text(encoding="utf-8")
API_SOURCE = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
MAIN_SOURCE = (
    ROOT / "frontend/executive-kpi/src/main.tsx"
).read_text(encoding="utf-8")
AGENTIC_COMPONENT_SOURCE = (
    ROOT
    / "frontend/executive-kpi/src/agentic/AgenticOperationsDashboard.tsx"
).read_text(encoding="utf-8")
AGENTIC_MODEL_SOURCE = (
    ROOT / "frontend/executive-kpi/src/agentic/agenticOperationsModel.ts"
).read_text(encoding="utf-8")
SHELL_JS_SOURCE = (ROOT / "src/app/static/shell.js").read_text(encoding="utf-8")
OVERVIEW_PATH = "/profile/admin/agentic-operations/overview"
ASSET_TOKEN = "item61e_operations_overview_r1"

ADMIN_USER = {
    "user_id": "admin-owner",
    "email": "admin@example.test",
    "is_admin": True,
}
NON_ADMIN_USER = {
    "user_id": "normal-owner",
    "email": "user@example.test",
    "is_admin": False,
    "access_level": "user",
}


def _client_as(monkeypatch: pytest.MonkeyPatch, user: dict | None) -> TestClient:
    def guard(request):
        if user is not None:
            request.state.auth_user = dict(user)
        return None

    monkeypatch.setattr(api, "auth_guard_response", guard)
    return TestClient(api.app)


def _agentic_operations_route_source() -> str:
    return UI_SOURCE.split(
        '@router.get("/agentic-operations", response_class=HTMLResponse)', 1
    )[1]


def test_agentic_operations_page_remains_server_side_admin_only(monkeypatch) -> None:
    admin = _client_as(monkeypatch, ADMIN_USER).get("/agentic-operations")
    assert admin.status_code == 200

    forbidden = _client_as(monkeypatch, NON_ADMIN_USER).get("/agentic-operations")
    assert forbidden.status_code == 403
    assert forbidden.json() == {"detail": "Admin access required."}

    route = _agentic_operations_route_source()
    assert route.count("_require_admin_user(request)") == 1
    assert route.index("_require_admin_user(request)") < route.index("return f")


def test_page_has_one_react_root_and_the_existing_bundle_assets(monkeypatch) -> None:
    response = _client_as(monkeypatch, ADMIN_USER).get("/agentic-operations")
    assert response.text.count('id="agenticOperationsRoot"') == 1
    assert response.text.count(
        f'/static/build/executive-kpi/executive-kpi.css?v={ASSET_TOKEN}'
    ) == 1
    assert response.text.count(
        f'/static/build/executive-kpi/executive-kpi.js?v={ASSET_TOKEN}'
    ) == 1
    assert "Loading Agentic Operations..." in response.text
    assert 'id="agenticOperationsRoot"\n      class="card"' not in response.text


def test_page_shell_injects_no_overview_data_or_request_owner() -> None:
    route = _agentic_operations_route_source()
    for forbidden in (
        OVERVIEW_PATH,
        "agentic_operations_overview_payload",
        "services.",
        "owner_user_id",
        "current_pipeline",
        "recent_runs",
        "safety_summary",
        "fetch(",
        "fetchJson(",
    ):
        assert forbidden not in route


def test_approved_backend_overview_path_is_unchanged() -> None:
    assert API_SOURCE.count(f'@app.get("{OVERVIEW_PATH}")') == 1
    route_start = API_SOURCE.index(f'@app.get("{OVERVIEW_PATH}")')
    route_end = API_SOURCE.index("\n\n@app.", route_start + 1)
    route = API_SOURCE[route_start:route_end]
    assert "_require_admin_user(http_request)" in route
    assert "agentic_operations_overview_payload(" in route
    assert "_require_auth_owner_user_id(http_request)" in route
    assert "Body(" not in route


def test_page_shell_adds_no_operational_controls() -> None:
    route = _agentic_operations_route_source()
    assert "<button" not in route
    assert "<form" not in route
    assert AGENTIC_COMPONENT_SOURCE.count("<button") == 1
    assert "Refresh overview" in AGENTIC_COMPONENT_SOURCE
    for forbidden in (
        "Run now",
        "Rerun",
        "Launch",
        "Approve",
        "Reject",
        "Submit",
        "Provider preview",
    ):
        assert forbidden not in AGENTIC_COMPONENT_SOURCE


def test_existing_multi_island_entrypoint_owns_one_agentic_mount() -> None:
    assert MAIN_SOURCE.count(
        'document.getElementById("agenticOperationsRoot")'
    ) == 1
    assert MAIN_SOURCE.count("<AgenticOperationsDashboard />") == 1
    assert MAIN_SOURCE.count(
        'import { AgenticOperationsDashboard } from "./agentic/AgenticOperationsDashboard";'
    ) == 1


def test_agentic_frontend_has_one_exact_network_owner_and_no_polling() -> None:
    combined = AGENTIC_MODEL_SOURCE + "\n" + AGENTIC_COMPONENT_SOURCE
    assert combined.count(OVERVIEW_PATH) == 1
    assert AGENTIC_MODEL_SOURCE.count("fetch(") == 1
    assert AGENTIC_COMPONENT_SOURCE.count("readAgenticOperationsOverview") == 2
    assert "credentials: \"same-origin\"" in AGENTIC_MODEL_SOURCE
    assert "headers: { Accept: \"application/json\" }" in AGENTIC_MODEL_SOURCE
    assert "body:" not in AGENTIC_MODEL_SOURCE
    assert "owner_user_id" not in AGENTIC_MODEL_SOURCE.split(
        "export async function readAgenticOperationsOverview", 1
    )[1]
    assert "setInterval(" not in combined
    assert "setTimeout(" not in combined
    assert OVERVIEW_PATH not in SHELL_JS_SOURCE


def test_agentic_frontend_contains_no_mutation_method_or_endpoint() -> None:
    combined = AGENTIC_MODEL_SOURCE + "\n" + AGENTIC_COMPONENT_SOURCE
    for method in ("POST", "PUT", "PATCH", "DELETE"):
        assert f'method: "{method}"' not in combined
    for endpoint_fragment in (
        "/scheduler/",
        "/application",
        "/provider",
        "/feedback",
        "/approval",
        "/resume",
    ):
        assert endpoint_fragment not in combined


def test_agentic_review_assets_remain_outside_operations_surface() -> None:
    route = _agentic_operations_route_source()
    combined = AGENTIC_MODEL_SOURCE + "\n" + AGENTIC_COMPONENT_SOURCE
    for asset in ("agentic_review.js", "agentic_review.css", "agentic-review-data"):
        assert asset not in route
        assert asset not in combined
