"""Phase 1 Step 8D — focused Profile and configuration-route regressions."""

import json
from pathlib import Path
import subprocess

import pytest
from fastapi import HTTPException
from starlette.requests import Request

from src.app.onboarding_ui import _preferences_workflow_form_html, onboarding_page
from src.app.planning_ui import _require_admin_user
from src.app.profile_ui import (
    _is_resume_onboarding_query,
    profile_page,
    profile_preferences_page,
)


ROOT = Path(__file__).resolve().parents[1]
PROFILE_UI = (ROOT / "src/app/profile_ui.py").read_text(encoding="utf-8")
PROFILE_JS = (ROOT / "src/app/static/profile.js").read_text(encoding="utf-8")
SHELL_JS = (ROOT / "src/app/static/shell.js").read_text(encoding="utf-8")
SHELL_UI = (ROOT / "src/app/ui_shell.py").read_text(encoding="utf-8")
APP_JS = (ROOT / "src/app/static/app.js").read_text(encoding="utf-8")
SERVICES = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
ONBOARDING_UI = (ROOT / "src/app/onboarding_ui.py").read_text(encoding="utf-8")
APP_REDESIGN_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")
PREFERENCES_CSS = (ROOT / "src/app/static/preferences.css").read_text(encoding="utf-8")
ONBOARDING_FORM = _preferences_workflow_form_html(prefix="onboarding", mode="onboarding")
PROFILE_FORM = _preferences_workflow_form_html(prefix="profilePreferences", mode="profile")
CANONICAL_RESUME_URL = "/profile?onboarding=resume_upload"


def _request(path: str = "/profile", query_string: bytes = b"", user: dict | None = None) -> Request:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": path,
            "query_string": query_string,
            "headers": [],
        }
    )
    request.state.auth_user = user or {
        "user_id": "step8d-user",
        "access_level": "user",
        "is_admin": False,
    }
    return request


def _function(source: str, name: str, next_name: str) -> str:
    start = source.index(f"function {name}")
    end = source.index(f"function {next_name}", start)
    return source[start:end]


def _browser_resume_mode(search: str) -> bool:
    functions = _function(
        PROFILE_JS,
        "normalizeResumeOnboardingQuery",
        "getProfileTabTargetFromUrl",
    )
    script = f"""
global.window = {{ location: {{ search: {json.dumps(search)} }} }};
eval({json.dumps(functions)});
console.log(JSON.stringify(isResumeOnboardingMode()));
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def _configuration_route(path: str) -> bool:
    function_source = _function(
        SHELL_JS,
        "isAccountConfigurationRoute",
        "clearNewUserWorkspaceEmptyState",
    )
    script = f"""
global.window = {{ location: {{ pathname: "/" }} }};
eval({json.dumps(function_source)});
console.log(JSON.stringify(isAccountConfigurationRoute({json.dumps(path)})));
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("resume_upload", True),
        ("resume_upload\\", True),
        ("resume_upload/", True),
        ("  resume_upload  ", True),
        ("resume_upload_anything", False),
        ("anything_resume_upload", False),
        ("resume_uploa", False),
        ("", False),
    ],
)
def test_server_resume_query_normalization_is_narrow(value: str, expected: bool):
    assert _is_resume_onboarding_query(value) is expected


@pytest.mark.parametrize(
    ("search", "expected"),
    [
        ("?onboarding=resume_upload", True),
        ("?onboarding=resume_upload%5C", True),
        ("?onboarding=resume_upload%2F", True),
        ("?onboarding=%20resume_upload%20", True),
        ("?onboarding=resume_upload_anything", False),
        ("?onboarding=anything_resume_upload", False),
        ("?onboarding=resume", False),
    ],
)
def test_browser_resume_query_normalization_matches_server(search: str, expected: bool):
    assert _browser_resume_mode(search) is expected


def test_focused_server_mode_is_prepaint_and_normal_profile_is_unchanged():
    focused = profile_page(_request(query_string=b"onboarding=resume_upload%5C"))
    normal = profile_page(_request())

    assert '<body class="profile-resume-onboarding-mode">' in focused
    assert 'data-profile-resume-onboarding="true"' in focused
    assert "Add your resume" in focused
    assert 'id="resumeDropzone"' in focused
    assert 'class="profile-tabs"' not in focused
    assert 'id="profilePipelineRunsSection"' not in focused
    assert 'id="profileAdminUsersSection"' not in focused

    assert '<body class="profile-resume-onboarding-mode">' not in normal
    assert 'data-profile-resume-onboarding="false"' in normal
    assert "My Profile" in normal
    assert 'class="profile-tabs"' in normal
    assert 'id="profilePipelineRunsSection"' in normal


def test_every_generated_resume_preflight_url_remains_exactly_canonical():
    for source in (ONBOARDING_UI, SHELL_JS, APP_JS, SERVICES):
        assert CANONICAL_RESUME_URL in source
        assert f"{CANONICAL_RESUME_URL}\\" not in source
        assert f"{CANONICAL_RESUME_URL}/" not in source
        assert f"{CANONICAL_RESUME_URL}%5C" not in source
        assert f"{CANONICAL_RESUME_URL}%2F" not in source


def test_profile_preferences_light_surface_excludes_workflow_wrapper():
    light_surface = APP_REDESIGN_CSS.split('html[data-theme="light"] .card,', 1)[1].split(
        "{", 1
    )[0]
    assert 'html[data-theme="light"] .profile-section-card:not(.profile-preferences-section)' in light_surface
    assert 'html[data-theme="light"] .profile-section-card,' not in light_surface
    assert ".profile-preferences-section.preferences-workflow" in PREFERENCES_CSS
    wrapper = PREFERENCES_CSS.split(".profile-preferences-section.preferences-workflow {", 1)[1].split(
        "}", 1
    )[0]
    assert "background: transparent" in wrapper


def test_onboarding_and_profile_preferences_keep_intentional_modes():
    onboarding_html = onboarding_page()
    preferences_html = profile_preferences_page()
    assert '<body class="preferences-page-shell">' in onboarding_html
    assert '<body class="preferences-page-shell">' in preferences_html
    assert 'data-preferences-mode="onboarding"' in onboarding_html
    assert 'data-preferences-mode="profile"' in preferences_html
    assert ONBOARDING_FORM.count("data-preferences-step=") == 6
    assert PROFILE_FORM.count("data-preferences-step=") == 5


def test_hidden_profile_navigation_rule_wins_after_grid_rule():
    grid_rule = APP_REDESIGN_CSS.index(".profile-dropdown-nav-btn {")
    hidden_rule = APP_REDESIGN_CSS.index(".profile-dropdown-nav-btn.hidden {")
    hidden_body = APP_REDESIGN_CSS[hidden_rule:APP_REDESIGN_CSS.index("}", hidden_rule)]
    assert grid_rule < hidden_rule
    assert "display: none !important" in hidden_body
    diagnostics = SHELL_UI.split('href="/advanced-diagnostics"', 1)[1].split("</a>", 1)[0]
    assert "hidden" in diagnostics
    assert 'data-admin-only="true"' in diagnostics
    assert 'profileAdvancedDiagnosticsLink.classList.toggle("hidden", !isAdmin)' in SHELL_JS


def test_existing_admin_predicate_and_diagnostics_authorization_remain_intact():
    with pytest.raises(HTTPException) as denied:
        _require_admin_user(_request(path="/advanced-diagnostics"))
    assert denied.value.status_code == 403
    assert denied.value.detail == "Admin access required."

    admin = _request(
        path="/advanced-diagnostics",
        user={"user_id": "admin", "access_level": "admin", "is_admin": False},
    )
    assert _require_admin_user(admin)["user_id"] == "admin"
    predicate = _function(SHELL_JS, "setProfileShellUser", "loadProfileShellUser")
    assert 'Boolean(user?.is_admin) || accessLevel === "admin"' in predicate


@pytest.mark.parametrize(
    "path",
    [
        "/onboarding",
        "/onboarding/",
        "/profile",
        "/profile/",
        "/profile/preferences",
        "/profile/ai-settings",
    ],
)
def test_account_configuration_routes_are_classified(path: str):
    assert _configuration_route(path) is True


@pytest.mark.parametrize("path", ["/", "/planning", "/applications", "/pipeline"])
def test_data_dependent_routes_are_not_configuration_routes(path: str):
    assert _configuration_route(path) is False


def test_empty_state_and_prompt_reuse_the_single_route_classifier():
    ensure = _function(SHELL_JS, "ensureNewUserEmptyState", "refreshNewUserWorkspaceState")
    refresh = _function(SHELL_JS, "refreshNewUserWorkspaceState", "redirectIncompleteOnboarding")
    prompt = _function(SHELL_JS, "showFirstRunPrompt", "closeProfileMenu")
    for owner in (ensure, refresh, prompt):
        assert "isAccountConfigurationRoute()" in owner
    assert "new-user-empty-state" in ensure
    assert 'fetch("/user/workspace-state"' in refresh
    assert "ensureNewUserEmptyState()" in refresh
    assert "firstRunPromptModal" in prompt


def test_onboarding_routing_precedes_workspace_state_and_stops_on_redirect():
    initialization = SHELL_JS.rsplit("loadProfileShellUser();", 1)[1]
    assert "redirectIncompleteOnboarding().then(async (redirecting)" in initialization
    assert "if (redirecting || isAccountConfigurationRoute()) return" in initialization
    assert initialization.index("redirectIncompleteOnboarding().then") < initialization.index(
        "await refreshNewUserWorkspaceState()"
    )
    assert initialization.index("await refreshNewUserWorkspaceState()") < initialization.index(
        "showFirstRunPrompt()"
    )
    assert "\n  refreshNewUserWorkspaceState();" not in initialization


def test_workspace_empty_state_cleanup_is_defined_and_narrow():
    cleanup = _function(
        SHELL_JS,
        "clearNewUserWorkspaceEmptyState",
        "openLivePipelineFromShell",
    )
    refresh = _function(SHELL_JS, "refreshNewUserWorkspaceState", "redirectIncompleteOnboarding")
    assert "clearNewUserOnboardingState" not in SHELL_JS
    assert "clearNewUserWorkspaceEmptyState()" in refresh
    assert "storageRemove(window.localStorage, APPLYLENS_NEW_USER_EMPTY_KEY)" in cleanup
    assert 'document.body.classList.remove("app-new-user-empty")' in cleanup
    assert 'document.querySelectorAll(".new-user-empty-state")' in cleanup
    for forbidden in (
        "sessionStorage",
        "onboarding/preferences",
        "auth",
        "credential",
        "JOBSTACK_THEME_KEY",
        "APP_SHELL_COLLAPSED_KEY",
    ):
        assert forbidden not in cleanup


def test_workspace_success_uses_cleanup_without_changing_api_semantics():
    refresh = _function(SHELL_JS, "refreshNewUserWorkspaceState", "redirectIncompleteOnboarding")
    assert 'fetch("/user/workspace-state"' in refresh
    assert "payload && payload.has_owned_data === false" in refresh
    assert "clearNewUserWorkspaceEmptyState()" in refresh
    assert "clearNewUserWorkspaceEmptyState" in SHELL_JS
    assert "/onboarding/preferences" not in refresh
    assert "owner_user_id" not in refresh
