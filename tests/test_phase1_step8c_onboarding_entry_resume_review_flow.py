"""Phase 1 Step 8C — resume preflight and safe onboarding review contracts."""

import json
from pathlib import Path
import subprocess

from starlette.requests import Request

from src.app.onboarding_ui import _preferences_workflow_form_html
from src.app.profile_ui import profile_page


ROOT = Path(__file__).resolve().parents[1]
SHELL_JS = (ROOT / "src/app/static/shell.js").read_text(encoding="utf-8")
PROFILE_JS = (ROOT / "src/app/static/profile.js").read_text(encoding="utf-8")
PROFILE_UI = (ROOT / "src/app/profile_ui.py").read_text(encoding="utf-8")
ONBOARDING_JS = (ROOT / "src/app/static/onboarding.js").read_text(encoding="utf-8")
WORKFLOW_JS = (ROOT / "src/app/static/preferences_workflow.js").read_text(encoding="utf-8")
PROFILE_AI_JS = (ROOT / "src/app/static/profile_ai_settings.js").read_text(encoding="utf-8")
PREFERENCES_CSS = (ROOT / "src/app/static/preferences.css").read_text(encoding="utf-8")
APP_REDESIGN_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")
ONBOARDING_FORM = _preferences_workflow_form_html(prefix="onboarding", mode="onboarding")
PROFILE_FORM = _preferences_workflow_form_html(prefix="profilePreferences", mode="profile")


def _function(source: str, name: str, next_name: str) -> str:
    marker = f"function {name}"
    if marker not in source:
        marker = f"async function {name}"
    return source.split(marker, 1)[1].split(f"function {next_name}", 1)[0]


def _profile_request(query_string: bytes = b"") -> Request:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profile",
            "query_string": query_string,
            "headers": [],
        }
    )
    request.state.auth_user = {"user_id": "step8c-user", "access_level": "user"}
    return request


def _run_shell_gate(path: str, *, completed: bool, has_resume: bool) -> dict:
    start = SHELL_JS.index("async function redirectIncompleteOnboarding")
    end = SHELL_JS.index("\n  function closeFirstRunPrompt", start)
    function_source = SHELL_JS[start:end]
    script = f"""
global.document = {{ body: {{ classList: {{ contains: () => false }} }} }};
global.window = {{ location: {{ pathname: {json.dumps(path)}, href: {json.dumps(path)} }} }};
global.fetch = async () => ({{
  ok: true,
  json: async () => ({json.dumps({"onboarding_completed": completed, "requirements": {"has_profile_resume": has_resume}})})
}});
eval({json.dumps(function_source)});
redirectIncompleteOnboarding().then((redirecting) => {{
  console.log(JSON.stringify({{ redirecting, href: window.location.href }}));
}});
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def test_shell_gate_routes_resume_preflight_and_preserves_completed_destination():
    assert _run_shell_gate("/jobs", completed=False, has_resume=False) == {
        "redirecting": True,
        "href": "/profile?onboarding=resume_upload",
    }
    assert _run_shell_gate("/onboarding", completed=False, has_resume=False) == {
        "redirecting": True,
        "href": "/profile?onboarding=resume_upload",
    }
    assert _run_shell_gate("/jobs", completed=False, has_resume=True) == {
        "redirecting": True,
        "href": "/onboarding",
    }
    assert _run_shell_gate("/jobs", completed=True, has_resume=False) == {
        "redirecting": False,
        "href": "/jobs",
    }
    gate = SHELL_JS.split("async function redirectIncompleteOnboarding", 1)[1].split(
        "function closeFirstRunPrompt", 1
    )[0]
    assert 'currentPath === "/onboarding" || currentPath === "/profile"' not in gate
    assert 'currentPath === "/profile"' in gate
    initialization = SHELL_JS.rsplit("loadProfileShellUser();", 1)[1]
    assert initialization.index("redirectIncompleteOnboarding().then") < initialization.index(
        "showFirstRunPrompt();"
    )
    assert "if (redirecting || isAccountConfigurationRoute()) return" in initialization
    assert initialization.index("await refreshNewUserWorkspaceState()") < initialization.index(
        "showFirstRunPrompt();"
    )


def test_profile_query_emits_focused_mode_while_direct_profile_stays_normal():
    focused = profile_page(_profile_request(b"onboarding=resume_upload"))
    normal = profile_page(_profile_request())

    assert '<body class="profile-resume-onboarding-mode">' in focused
    assert 'data-profile-resume-onboarding="true"' in focused
    assert "Add your resume" in focused
    assert "required before preference setup" in focused
    assert 'id="resumeDropzone"' in focused
    assert 'id="resumeUploadInput"' in focused
    assert 'class="profile-tabs"' not in focused
    assert 'id="profilePipelineRunsSection"' not in focused
    assert 'id="profileAdminUsersSection"' not in focused

    assert '<body class="profile-resume-onboarding-mode">' not in normal
    assert 'data-profile-resume-onboarding="false"' in normal
    assert "My Profile" in normal
    assert 'class="profile-tabs"' in normal
    assert 'id="profilePipelineRunsSection"' in normal


def test_focused_mode_reuses_existing_uploader_and_redirects_only_full_success():
    upload = _function(PROFILE_JS, "uploadResumeFiles", "deleteResume")
    load = _function(PROFILE_JS, "loadResumes", "normalizeSavedScanSource")
    init = PROFILE_JS.split(
        "async function initProfilePage", 1
    )[1].split('window.addEventListener("DOMContentLoaded"', 1)[0]

    assert '`/profile/resumes/upload?filename=${encodeURIComponent(file.name)}`' in PROFILE_JS
    assert 'fetchJson("/profile/resumes")' in load
    assert "if (!isResumeOnboardingMode()) await loadResumeRoleMappings()" in load
    assert 'window.location.href = "/onboarding"' in upload
    full_success = upload.split("if (results.uploaded.length && !results.failed.length)", 1)[1].split(
        "if (results.uploaded.length && results.failed.length)", 1
    )[0]
    partial_failure = upload.split("if (results.uploaded.length && results.failed.length)", 1)[1]
    assert 'window.location.href = "/onboarding"' in full_success
    assert 'window.location.href = "/onboarding"' not in partial_failure
    assert "throw new Error(firstError)" in partial_failure
    assert "if (isResumeOnboardingMode())" in init
    assert init.index("bindUploadInteractions()") < init.index("if (isResumeOnboardingMode())")
    assert "Resume ready" in PROFILE_JS
    assert "Continue to onboarding" in PROFILE_JS


def test_review_uses_compact_resume_and_safe_ai_rows():
    assert "preferences-resume-requirement" not in ONBOARDING_FORM
    assert "Profile resume" in ONBOARDING_FORM
    assert "Manage or replace" in ONBOARDING_FORM
    assert 'href="/profile?onboarding=resume_upload"' in ONBOARDING_FORM
    assert "data-onboarding-ai-review-status" in ONBOARDING_FORM
    assert "data-onboarding-ai-review-preferred" in ONBOARDING_FORM
    assert "data-onboarding-ai-review-configured" in ONBOARDING_FORM
    assert 'data-preferences-edit-step="4"' in ONBOARDING_FORM
    assert "data-onboarding-ai-summary" in ONBOARDING_FORM
    assert "data-onboarding-ai-summary" not in PROFILE_FORM
    assert "AI status unavailable" in ONBOARDING_FORM

    projection = _function(
        ONBOARDING_JS,
        "onboardingAiSafeProjection",
        "updateOnboardingAiSafeProjection",
    )
    collect = _function(
        ONBOARDING_JS,
        "collectOnboardingPreferences",
        "renderRequirementStatus",
    )
    assert "AI not configured" in projection
    assert "Preferred: ${preferredLabel} · Configured: ${configuredLabel}" in projection
    assert "No preferred provider · Configured: ${configuredLabel}" in projection
    assert "credentialHint" not in projection
    assert "onboardingAi" not in collect
    assert "localStorage" not in ONBOARDING_JS
    assert "sessionStorage" not in ONBOARDING_JS


def test_explicit_clear_actions_use_only_existing_preference_delete():
    onboarding_clear = _function(
        ONBOARDING_JS,
        "clearOnboardingAiPreferredProvider",
        "testOnboardingAiConnection",
    )
    profile_clear = _function(PROFILE_AI_JS, "clearPreferredProvider", "testConnection")
    for clear in (onboarding_clear, profile_clear):
        assert '"/ai/settings/preferred-provider"' in clear
        assert 'method: "DELETE"' in clear
        assert "credentials/" not in clear
        assert "test-connection" not in clear
        assert "api_key" not in clear
    assert "Clear preference" in ONBOARDING_JS
    assert "Clear preference" in PROFILE_UI
    assert "aiPreferredProviderClearBtn" in PROFILE_AI_JS


def test_skip_is_footer_owned_navigation_only_and_non_primary():
    skip = _function(ONBOARDING_JS, "skipOnboardingAiSetup", "bindOnboardingAiEvents")
    assert "showStep(5)" in skip
    for forbidden in ("fetch", "RequestJson", "preferred-provider", "credentials/", "test-connection"):
        assert forbidden not in skip
    final_actions = ONBOARDING_FORM.split('<div class="preferences-final-actions">', 1)[1].split(
        "</div>", 1
    )[0]
    assert "data-preferences-skip" in final_actions
    assert "onboardingAiSkipBtn" in final_actions
    assert "data-preferences-skip" not in PROFILE_FORM
    assert 'root.dataset.preferencesMode !== "onboarding" || nextStep !== 4' in WORKFLOW_JS
    assert ".preferences-final-actions .onboarding-ai-skip-button" in PREFERENCES_CSS
    skip_css = PREFERENCES_CSS.split(
        ".preferences-workflow .preferences-final-actions .onboarding-ai-skip-button {", 1
    )[1].split("}", 1)[0]
    assert "background: #475569" in skip_css
    assert "linear-gradient" not in skip_css
    assert "transform: none" in skip_css


def test_resume_actions_have_owned_button_focus_and_focused_layout_styles():
    assert ".preferences-workflow .onboarding-solid-link" in PREFERENCES_CSS
    assert ".preferences-workflow .onboarding-solid-link:hover" in PREFERENCES_CSS
    assert ".preferences-workflow .onboarding-solid-link:focus-visible" in PREFERENCES_CSS
    assert "body.profile-resume-onboarding-mode .profile-resume-onboarding-page" in APP_REDESIGN_CSS
    assert "body.profile-resume-onboarding-mode .resume-manager-grid" in APP_REDESIGN_CSS
    assert "body.profile-resume-onboarding-mode .profile-onboarding-continue-btn:focus-visible" in APP_REDESIGN_CSS
