"""Item 6.1D Agentic Operations admin-only console shell and discovery."""

import json
from pathlib import Path
import subprocess

import pytest
from fastapi.testclient import TestClient

from src.app import api
from src.app.ui_shell import NAV_GROUPS, NAV_ITEMS


ROOT = Path(__file__).resolve().parents[1]
UI_SOURCE = (ROOT / "src/app/ui.py").read_text(encoding="utf-8")
UI_SHELL_SOURCE = (ROOT / "src/app/ui_shell.py").read_text(encoding="utf-8")
SHELL_JS_SOURCE = (ROOT / "src/app/static/shell.js").read_text(encoding="utf-8")
OVERVIEW_ENDPOINT = "/profile/admin/agentic-operations/overview"

ADMIN_USER = {
    "user_id": "admin-owner",
    "email": "admin@example.test",
    "is_admin": True,
}
ACCESS_LEVEL_ADMIN = {
    "user_id": "access-admin-owner",
    "email": "access-admin@example.test",
    "is_admin": False,
    "access_level": "admin",
}
NON_ADMIN_USER = {
    "user_id": "user-owner",
    "email": "user@example.test",
    "is_admin": False,
    "access_level": "user",
}


def _client_as(monkeypatch, user: dict | None) -> TestClient:
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


def _profile_link_source() -> str:
    before, after = UI_SHELL_SOURCE.split('id="profileAgenticOperationsLink"', 1)
    return before.rsplit("<a", 1)[1] + after.split("</a>", 1)[0]


def _function_source(source: str, name: str, next_name: str) -> str:
    start = source.index(f"function {name}")
    end = source.index(f"async function {next_name}", start)
    return source[start:end]


@pytest.mark.parametrize("admin_user", [ADMIN_USER, ACCESS_LEVEL_ADMIN])
def test_admin_representations_can_open_agentic_operations_shell(
    monkeypatch,
    admin_user,
) -> None:
    response = _client_as(monkeypatch, admin_user).get("/agentic-operations")

    assert response.status_code == 200
    assert "<title>Agentic Operations</title>" in response.text
    assert '<h1 class="app-page-header__title">Agentic Operations</h1>' in response.text
    assert response.text.count('id="agenticOperationsRoot"') == 1


def test_direct_non_admin_request_is_forbidden(monkeypatch) -> None:
    response = _client_as(monkeypatch, NON_ADMIN_USER).get("/agentic-operations")

    assert response.status_code == 403
    assert response.json() == {"detail": "Admin access required."}


def test_unauthenticated_request_preserves_ui_admin_401(monkeypatch) -> None:
    response = _client_as(monkeypatch, None).get("/agentic-operations")

    assert response.status_code == 401
    assert response.json() == {"detail": "Authentication required."}


def test_route_reuses_shared_shell_and_existing_admin_helper() -> None:
    route = _agentic_operations_route_source()

    assert route.count("_require_admin_user(request)") == 1
    assert route.index("_require_admin_user(request)") < route.index("return f")
    assert 'render_top_shell("/agentic-operations")' in route
    assert "def _require_admin_user" not in route
    assert "app-shell-sidebar" not in route


def test_profile_dropdown_has_one_initially_hidden_admin_entry() -> None:
    assert UI_SHELL_SOURCE.count('id="profileAgenticOperationsLink"') == 1
    entry = _profile_link_source()

    assert 'class="profile-dropdown-nav-btn hidden"' in entry
    assert 'href="/agentic-operations"' in entry
    assert 'data-admin-only="true"' in entry
    assert "Agentic Operations" in entry
    assert "profile-dropdown-nav-subtitle" not in entry
    assert 'profile-dropdown-nav-icon--agentic-operations' in entry
    assert '{_icon_svg("agentic-operations")}' in entry
    assert "<img" not in entry


def test_agentic_operations_is_excluded_from_normal_navigation() -> None:
    labels = {label for _group, items in NAV_GROUPS for label, _href, _icon in items}
    hrefs = {href for _label, href, _icon in NAV_ITEMS}

    assert "Agentic Operations" not in labels
    assert "/agentic-operations" not in hrefs


def test_shell_uses_existing_admin_state_for_visibility() -> None:
    predicate = _function_source(
        SHELL_JS_SOURCE,
        "setProfileShellUser",
        "loadProfileShellUser",
    )

    assert SHELL_JS_SOURCE.count('qs("profileAgenticOperationsLink")') == 1
    assert predicate.count(
        'Boolean(user?.is_admin) || accessLevel === "admin"'
    ) == 1
    assert (
        'profileAgenticOperationsLink.classList.toggle("hidden", !isAdmin)'
        in predicate
    )
    assert (
        'profileAgenticOperationsLink.setAttribute("aria-hidden", '
        'isAdmin ? "false" : "true")'
        in predicate
    )
    assert "profileAgenticOperationsLink.tabIndex = isAdmin ? 0 : -1" in predicate
    assert SHELL_JS_SOURCE.count('fetchJson("/auth/me")') == 1


def test_shell_visibility_behavior_is_admin_only_and_non_tabbable() -> None:
    predicate = _function_source(
        SHELL_JS_SOURCE,
        "setProfileShellUser",
        "loadProfileShellUser",
    )
    script = f"""
const state = {{ hidden: true, ariaHidden: "true", tabIndex: -1 }};
const profileAgenticOperationsLink = {{
  classList: {{ toggle: (name, force) => {{ if (name === "hidden") state.hidden = force; }} }},
  setAttribute: (name, value) => {{ if (name === "aria-hidden") state.ariaHidden = value; }},
  set tabIndex(value) {{ state.tabIndex = value; }},
}};
const menuButton = null;
const profileDropdownAvatar = null;
const profileDropdownName = null;
const profileDropdownEmail = null;
const profileAdminToolsSection = null;
const profileAdvancedDiagnosticsLink = null;
const profileSchedulerHealthLink = null;
function userInitialFromName() {{ return "A"; }}
eval({json.dumps(predicate)});
setProfileShellUser({{ is_admin: true }});
const admin = {{ ...state }};
setProfileShellUser({{ is_admin: false, access_level: "user" }});
console.log(JSON.stringify({{ admin, nonAdmin: state }}));
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["admin"] == {
        "hidden": False,
        "ariaHidden": "false",
        "tabIndex": 0,
    }
    assert payload["nonAdmin"] == {
        "hidden": True,
        "ariaHidden": "true",
        "tabIndex": -1,
    }


def test_page_shell_has_no_data_fetch_polling_or_operational_controls() -> None:
    route = _agentic_operations_route_source()

    assert OVERVIEW_ENDPOINT not in route
    for forbidden in (
        "fetch(",
        "fetchJson(",
        "XMLHttpRequest",
        "setInterval(",
        "<button",
        "<form",
        "Run now",
        "Retry",
        "Approve",
        "Apply",
        "Submit",
        "Launch",
        "Execute",
    ):
        assert forbidden not in route


def test_page_shell_adds_no_backend_or_runtime_owner() -> None:
    route = _agentic_operations_route_source()

    for forbidden in (
        "services.",
        "database",
        "status_path",
        "provider",
        "pipeline",
        "scheduler",
        "agent_trace",
        "application",
    ):
        assert forbidden not in route.lower()
