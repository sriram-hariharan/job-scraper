from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from src.app import auth_ui


ROOT = Path(__file__).resolve().parents[1]
AUTH_UI = ROOT / "src/app/auth_ui.py"
UI = ROOT / "src/app/ui.py"
PLANNING_UI = ROOT / "src/app/planning_ui.py"
APP_JS = ROOT / "src/app/static/app.js"
PLANNING_JS = ROOT / "src/app/static/planning.js"
CSS = ROOT / "src/app/static/styles.css"
AUTH_HERO_ICONS = ROOT / "src/app/static/media/auth_hero_icons"
AUTH_WORKFLOW_ARTWORK = ROOT / "src/app/static/media/auth_workflow_hero.svg"
D3_VENDOR = ROOT / "src/app/static/vendor/d3"


def _isolated_auth_client(monkeypatch) -> TestClient:
    monkeypatch.setattr(
        auth_ui,
        "current_user_from_request",
        lambda _request: None,
    )
    app = FastAPI()
    app.include_router(auth_ui.router)
    return TestClient(app)


def _enable_direct_registration(monkeypatch, *, active_user_count: int = 1):
    monkeypatch.setenv("JOB_STACK_AUTH_REGISTRATION_ENABLED", "true")
    monkeypatch.setenv("JOB_STACK_AUTH_REGISTRATION_APPROVAL_REQUIRED", "false")
    monkeypatch.setenv("JOB_STACK_AUTH_FIRST_USER_ADMIN_ENABLED", "true")
    monkeypatch.setattr(
        auth_ui,
        "_auth_user_counts",
        lambda: {
            "user_count": active_user_count,
            "active_user_count": active_user_count,
        },
    )


def _enable_legacy_approval_registration(monkeypatch):
    monkeypatch.setenv("JOB_STACK_AUTH_REGISTRATION_ENABLED", "false")
    monkeypatch.setenv("JOB_STACK_AUTH_REGISTRATION_APPROVAL_REQUIRED", "true")
    monkeypatch.setenv("JOB_STACK_AUTH_FIRST_USER_ADMIN_ENABLED", "false")


def _forbid_registration_writes(monkeypatch):
    def fail(*_args, **_kwargs):
        pytest.fail("invalid registration must not persist auth state")

    for name in (
        "create_auth_user_postgres_payload",
        "create_auth_session_postgres_payload",
        "create_auth_registration_request_postgres_payload",
        "new_auth_session_record",
    ):
        monkeypatch.setattr(auth_ui, name, fail)


def test_auth_pages_use_current_product_and_safety_copy():
    source = AUTH_UI.read_text(encoding="utf-8")
    for text in (
        "Turn live jobs into<br /><span>review-ready</span><br />applications.",
        'title = "Create your workspace" if is_register else "Welcome back"',
        "Live job pipeline",
        "Hybrid fit scoring",
        "Policy AI review",
        "Tailoring workspace",
        "You stay in control. No auto-apply. No recruiter messages.",
        "Secure and private. Built for your job search.",
    ):
        assert text in source
    assert 'mode == "register"' in source
    assert 'mode === "register" ? "/auth/register" : "/auth/login"' in source


def test_register_page_has_required_confirmation_and_login_does_not(monkeypatch):
    _enable_direct_registration(monkeypatch)
    client = _isolated_auth_client(monkeypatch)

    register = client.get("/register")
    login = client.get("/login")

    assert register.status_code == 200
    assert login.status_code == 200
    register_html = register.text
    assert '<span>Re-enter password</span>' in register_html
    assert (
        '<input id="confirmPasswordInput" type="password" '
        'autocomplete="new-password" placeholder="Re-enter your password" required />'
        in register_html
    )
    assert register_html.index('id="passwordInput"') < register_html.index(
        'id="confirmPasswordInput"'
    ) < register_html.index('id="authSubmitBtn"')
    assert '<input id="confirmPasswordInput"' not in login.text
    assert "Re-enter password" not in login.text


def test_registration_model_requires_confirmation_and_login_contract_is_unchanged():
    assert auth_ui.AuthRegisterRequest.model_fields[
        "confirm_password"
    ].is_required()
    assert set(auth_ui.AuthLoginRequest.model_fields) == {
        "email",
        "password",
        "next",
    }


def test_registration_script_blocks_mismatch_before_fetch_and_reenables_submit():
    source = AUTH_UI.read_text(encoding="utf-8")
    handler = source.split(
        'form.addEventListener("submit", async (event) =>',
        1,
    )[1]
    mismatch_at = handler.index("if (body.password !== confirmPassword)")
    fetch_at = handler.index("await fetch(")
    mismatch_branch = handler[mismatch_at:fetch_at]

    assert mismatch_at < fetch_at
    assert 'showError("Passwords do not match.")' in mismatch_branch
    assert "submitBtn.disabled = false" in mismatch_branch
    assert "return;" in mismatch_branch
    assert "body.confirm_password = confirmPassword" in handler[:fetch_at]
    assert "confirmPasswordInput.type" not in source


def test_mismatched_confirmation_returns_400_without_any_auth_write(monkeypatch):
    _enable_legacy_approval_registration(monkeypatch)
    _forbid_registration_writes(monkeypatch)
    monkeypatch.setattr(
        auth_ui,
        "validate_new_password",
        lambda _password: pytest.fail(
            "password strength validation must follow confirmation matching"
        ),
    )
    monkeypatch.setattr(
        auth_ui,
        "hash_password",
        lambda _password: pytest.fail("mismatched password must not be hashed"),
    )

    response = _isolated_auth_client(monkeypatch).post(
        "/auth/register",
        json={
            "email": "person@example.com",
            "password": "ValidPass123",
            "confirm_password": "DifferentPass123",
            "display_name": "Person",
        },
    )

    assert response.status_code == 400
    assert response.json() == {"detail": "Passwords do not match."}
    assert "set-cookie" not in response.headers


def test_missing_confirmation_is_rejected_by_request_model(monkeypatch):
    _enable_direct_registration(monkeypatch)
    _forbid_registration_writes(monkeypatch)

    response = _isolated_auth_client(monkeypatch).post(
        "/auth/register",
        json={
            "email": "person@example.com",
            "password": "ValidPass123",
            "display_name": "Person",
        },
    )

    assert response.status_code == 422


def test_direct_registration_creates_active_normal_user_and_session(monkeypatch):
    _enable_direct_registration(monkeypatch, active_user_count=2)
    observed = {
        "validated": [],
        "hashed": [],
        "user_records": [],
        "session_records": [],
    }
    user = {
        "user_id": "user-123",
        "email": "person@example.com",
        "display_name": "Person",
        "access_level": "user",
        "is_active": True,
        "is_admin": False,
        "last_login_at": "",
    }

    monkeypatch.setattr(
        auth_ui,
        "validate_new_password",
        lambda value: observed["validated"].append(value),
    )
    monkeypatch.setattr(
        auth_ui,
        "hash_password",
        lambda value: observed["hashed"].append(value) or "hashed-password",
    )
    monkeypatch.setattr(
        auth_ui,
        "create_auth_user_postgres_payload",
        lambda *, record, ensure_schema: observed["user_records"].append(record)
        or {"inserted": True, "user": user},
    )
    monkeypatch.setattr(
        auth_ui,
        "new_auth_session_record",
        lambda **_kwargs: ("session-token", {"session_id": "session-123"}),
    )
    monkeypatch.setattr(
        auth_ui,
        "create_auth_session_postgres_payload",
        lambda *, record, ensure_schema: observed["session_records"].append(record)
        or {"inserted": True},
    )
    monkeypatch.setattr(
        auth_ui,
        "touch_auth_user_last_login_postgres_payload",
        lambda **_kwargs: {"user": {**user, "last_login_at": "2026-09-14T00:00:00Z"}},
    )
    monkeypatch.setattr(
        auth_ui,
        "create_auth_registration_request_postgres_payload",
        lambda **_kwargs: pytest.fail(
            "direct registration must not create a pending request"
        ),
    )

    password = "ValidPass123"
    response = _isolated_auth_client(monkeypatch).post(
        "/auth/register",
        json={
            "email": user["email"],
            "password": password,
            "confirm_password": password,
            "display_name": user["display_name"],
            "next": "/planning",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["first_login"] is True
    assert payload["redirect_to"] == "/planning"
    assert "pending_approval" not in payload
    assert payload["user"]["access_level"] == "user"
    assert payload["user"]["is_active"] is True
    assert payload["user"]["is_admin"] is False
    assert auth_ui.auth_cookie_name() in response.cookies
    assert observed["validated"] == [password]
    assert observed["hashed"] == [password]
    assert observed["session_records"] == [{"session_id": "session-123"}]
    assert observed["user_records"] == [
        {
            "email": user["email"],
            "password_hash": "hashed-password",
            "display_name": user["display_name"],
            "access_level": "user",
            "is_active": True,
            "is_admin": False,
        }
    ]
    assert "confirm_password" not in observed["user_records"][0]


def test_legacy_pending_request_never_persists_confirmation(monkeypatch):
    _enable_legacy_approval_registration(monkeypatch)
    observed = {"request_records": [], "hashed": []}
    monkeypatch.setattr(auth_ui, "validate_new_password", lambda _value: None)
    monkeypatch.setattr(
        auth_ui,
        "hash_password",
        lambda value: observed["hashed"].append(value) or "hashed-password",
    )
    monkeypatch.setattr(
        auth_ui,
        "get_auth_user_by_email_postgres_payload",
        lambda **_kwargs: {"user": {}},
    )
    monkeypatch.setattr(
        auth_ui,
        "create_auth_user_postgres_payload",
        lambda **_kwargs: pytest.fail("approval mode must not create a user"),
    )
    monkeypatch.setattr(
        auth_ui,
        "create_auth_session_postgres_payload",
        lambda **_kwargs: pytest.fail("approval mode must not create a session"),
    )
    monkeypatch.setattr(
        auth_ui,
        "create_auth_registration_request_postgres_payload",
        lambda *, record, ensure_schema: observed["request_records"].append(record)
        or {
            "inserted": True,
            "request": {"request_id": "request-123"},
        },
    )
    monkeypatch.setattr(
        auth_ui,
        "build_auth_registration_admin_email_payload",
        lambda _request: {"message": "approval notice"},
    )
    monkeypatch.setattr(
        auth_ui,
        "deliver_auth_approval_email_payload",
        lambda _payload: {"ok": False},
    )

    password = "ValidPass123"
    response = _isolated_auth_client(monkeypatch).post(
        "/auth/register",
        json={
            "email": "legacy@example.com",
            "password": password,
            "confirm_password": password,
            "display_name": "Legacy User",
        },
    )

    assert response.status_code == 200
    assert response.json()["pending_approval"] is True
    assert observed["hashed"] == [password]
    assert len(observed["request_records"]) == 1
    assert observed["request_records"][0]["password_hash"] == "hashed-password"
    assert "password" not in observed["request_records"][0]
    assert "confirm_password" not in observed["request_records"][0]


def test_matching_weak_password_still_uses_existing_strength_policy(monkeypatch):
    _enable_direct_registration(monkeypatch)
    _forbid_registration_writes(monkeypatch)

    response = _isolated_auth_client(monkeypatch).post(
        "/auth/register",
        json={
            "email": "person@example.com",
            "password": "short",
            "confirm_password": "short",
        },
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Password must be at least 8 characters."
    }


def test_duplicate_email_behavior_remains_conflict_without_pending_request(
    monkeypatch,
):
    _enable_direct_registration(monkeypatch)
    monkeypatch.setattr(auth_ui, "validate_new_password", lambda _value: None)
    monkeypatch.setattr(auth_ui, "hash_password", lambda _value: "hashed-password")
    monkeypatch.setattr(
        auth_ui,
        "create_auth_user_postgres_payload",
        lambda **_kwargs: {"inserted": False, "user": {}},
    )
    monkeypatch.setattr(
        auth_ui,
        "create_auth_session_postgres_payload",
        lambda **_kwargs: pytest.fail("duplicate email must not create a session"),
    )
    monkeypatch.setattr(
        auth_ui,
        "create_auth_registration_request_postgres_payload",
        lambda **_kwargs: pytest.fail(
            "duplicate direct registration must not create a pending request"
        ),
    )

    response = _isolated_auth_client(monkeypatch).post(
        "/auth/register",
        json={
            "email": "person@example.com",
            "password": "ValidPass123",
            "confirm_password": "ValidPass123",
        },
    )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "An account already exists for this email."
    }


def test_first_user_bootstrap_and_legacy_approval_routes_remain_available(
    monkeypatch,
):
    _enable_direct_registration(monkeypatch, active_user_count=0)
    assert auth_ui._should_create_admin_user() is True
    monkeypatch.setattr(
        auth_ui,
        "_auth_user_counts",
        lambda: {"user_count": 2, "active_user_count": 2},
    )
    assert auth_ui._should_create_admin_user() is False

    paths = {route.path for route in auth_ui.router.routes}
    assert {
        "/admin/registration-requests",
        "/admin/registration-requests/data",
        "/admin/registration-requests/{request_id}/approve",
        "/admin/registration-requests/{request_id}/reject",
    } <= paths


def test_login_endpoint_keeps_original_payload_and_session_behavior(monkeypatch):
    client = _isolated_auth_client(monkeypatch)
    observed = {"verified": [], "sessions": []}
    user = {
        "user_id": "user-123",
        "email": "person@example.com",
        "display_name": "Person",
        "password_hash": "stored-hash",
        "access_level": "user",
        "is_active": True,
        "is_admin": False,
        "last_login_at": "2026-09-14T00:00:00Z",
    }
    monkeypatch.setattr(
        auth_ui,
        "get_auth_user_by_email_postgres_payload",
        lambda **_kwargs: {"user": user},
    )
    monkeypatch.setattr(
        auth_ui,
        "verify_password",
        lambda password, password_hash: observed["verified"].append(
            (password, password_hash)
        )
        or True,
    )
    monkeypatch.setattr(
        auth_ui,
        "new_auth_session_record",
        lambda **_kwargs: ("login-session-token", {"session_id": "login-session"}),
    )
    monkeypatch.setattr(
        auth_ui,
        "create_auth_session_postgres_payload",
        lambda *, record, ensure_schema: observed["sessions"].append(record)
        or {"inserted": True},
    )
    monkeypatch.setattr(
        auth_ui,
        "touch_auth_user_last_login_postgres_payload",
        lambda **_kwargs: {"user": user},
    )

    response = client.post(
        "/auth/login",
        json={
            "email": user["email"],
            "password": "ValidPass123",
            "next": "/planning",
        },
    )

    assert response.status_code == 200
    assert response.json()["redirect_to"] == "/planning"
    assert response.json()["first_login"] is False
    assert observed["verified"] == [("ValidPass123", "stored-hash")]
    assert observed["sessions"] == [{"session_id": "login-session"}]
    assert auth_ui.auth_cookie_name() in response.cookies


def test_auth_shell_is_cinematic_responsive_and_has_no_fake_social_login():
    source = AUTH_UI.read_text(encoding="utf-8")
    for marker in (
        "height: 100dvh",
        "overflow: hidden",
        "box-sizing: border-box",
        "auth-scene",
        "auth-scene-haze",
        "auth-scene-wave",
        "auth-workflow-artwork",
        'src="/static/media/auth_workflow_hero.svg"',
        "height: min(68vh, 650px)",
        "background: rgba(255, 255, 255, 0.76)",
        ".auth-password-toggle:focus-visible",
        "background: transparent !important",
        "background-image: none !important",
        "#passwordToggleBtn.auth-password-toggle",
        "scale(1.78)",
        "max-width: 500px",
        "backdrop-filter: blur(24px)",
        "@media (max-width: 900px)",
        "@media (max-width: 560px)",
        "overflow-y: auto",
        "@media (prefers-reduced-motion: reduce)",
        'url("/static/media/Login_page_BG_img.jpg")',
    ):
        assert marker in source
    assert "clip-path: polygon" not in source
    assert "auth-workflow-step" not in source
    assert "<span>01</span>" not in source
    assert "auth-workflow-tile--check" not in source
    assert "border: 1px solid rgba(100, 116, 139, 0.24) !important" not in source
    auth_input_css = source[source.index("    .auth-field input {{"):source.index("    .auth-field input::placeholder")]
    assert "font-weight: 450" in auth_input_css
    assert "font-weight: 650" not in auth_input_css
    assert "Scrape roles, score fit, review policy-driven AI notes" in source
    assert source.count('class="auth-hero-bullet"') == 4
    assert "setInterval" not in source
    assert "MutationObserver" not in source
    assert "ChatGPT Image" not in source
    assert (ROOT / "src/app/static/media/Login_page_BG_img.jpg").is_file()
    assert (ROOT / "src/app/static/media/Login_page_BG_img.LICENSE.txt").is_file()
    expected_icons = {
        "collect_jobs.svg",
        "score_fit.svg",
        "review_ai_notes.svg",
        "tailor_safely.svg",
        "apply_with_confidence.svg",
    }
    assert {path.name for path in AUTH_HERO_ICONS.glob("*.svg")} == expected_icons
    assert (AUTH_HERO_ICONS / "LICENSES.txt").is_file()
    for icon_name in expected_icons:
        icon_source = (AUTH_HERO_ICONS / icon_name).read_text(encoding="utf-8")
        assert 'viewBox="0 0 24 24"' in icon_source
        assert "<script" not in icon_source
        assert "<animate" not in icon_source
        assert "foreignObject" not in icon_source
        assert "href=" not in icon_source
        assert "onload=" not in icon_source
        assert "onclick=" not in icon_source
    for forbidden in ("Google login", "Facebook login", "Microsoft login", "Forgot password"):
        assert forbidden not in source


def test_auth_workflow_uses_finished_designer_artwork_only():
    source = AUTH_UI.read_text(encoding="utf-8")

    assert AUTH_WORKFLOW_ARTWORK.is_file()
    artwork_source = AUTH_WORKFLOW_ARTWORK.read_text(encoding="utf-8")
    assert artwork_source.lstrip().startswith("<svg")
    assert not D3_VENDOR.exists()
    assert "/static/vendor/d3/" not in source
    assert "window.d3" not in source
    assert "cdn.jsdelivr.net" not in source
    assert "unpkg.com" not in source
    assert source.count('class="auth-workflow-artwork"') == 1
    assert source.count('src="/static/media/auth_workflow_hero.svg"') == 1
    assert '<svg class="auth-workflow' not in source
    for forbidden in (
        "auth-workflow-scene",
        "auth-workflow-svg",
        "auth-workflow-rail",
        "auth-workflow-node",
        "auth-workflow-icon",
        "updateWorkflowConnector",
        "toWorkflowPoint",
        "connectorLine",
        "curveCatmullRom",
        "curveMonotoneY",
        "workflowPath.setAttribute",
        "scheduleWorkflowContrastUpdate",
        "sampleWorkflowLuminance",
        "relativeLuminance",
        "workflowContrastClasses",
        "workflowBackgroundContext",
        'document.createElement("canvas")',
    ):
        assert forbidden not in source
    assert "setInterval" not in source
    assert "MutationObserver" not in source
    assert "ResizeObserver" not in source
    assert ".auth-password-toggle:focus-visible" in source
    assert 'mode === "register" ? "/auth/register" : "/auth/login"' in source
    for fake_social in ("Google login", "Facebook login", "Microsoft login"):
        assert fake_social not in source


def test_generate_suggestions_success_waits_for_acknowledgement_and_refreshes_planning():
    markup = PLANNING_UI.read_text(encoding="utf-8")
    script = PLANNING_JS.read_text(encoding="utf-8")
    loader_start = script.index("function setGenerateSuggestionsLoaderState")
    loader_end = script.index("function closeGenerateSuggestionsLoader", loader_start)
    loader = script[loader_start:loader_end]
    success_branch = loader.split('if (state === "success")', 1)[1].split(
        "return;", 1
    )[0]
    acknowledge_start = script.index(
        "async function acknowledgeGenerateSuggestionsLoader"
    )
    acknowledge_end = script.index(
        "function getPlanningRowFromTailoringDataset", acknowledge_start
    )
    acknowledge = script[acknowledge_start:acknowledge_end]
    assert "Preparing tailoring workspace" in markup
    assert "Open Tailoring Workspace" in markup
    assert "Tailoring workspace is ready" in script
    assert 'state === "success" ? "Okay" : "Cancel"' in loader
    assert 'openBtn.classList.remove("hidden")' not in success_branch
    assert 'workflowState === "success"' in acknowledge
    assert acknowledge.index("closeGenerateSuggestionsLoader()") < acknowledge.index(
        "await loadPlanningTable({ forceNetwork: true })"
    )
    assert "window.location" not in acknowledge
    assert 'window.location.href = generateSuggestionsState.lastWorkspaceUrl' in script
    assert "window.setTimeout(() =>" not in script[script.index("async function handleGenerateSuggestionsClick"):script.index("async function retryGenerateSuggestions")]
    assert "workflow-overlay__panel" in markup
    assert "workflow-overlay--tailoring" in markup
    assert "workflow-overlay__body" in markup
    assert "workflow-step-viewport" in markup
    assert "generate-suggestions-document-stack" not in markup
    assert "workflow-overlay__footer" in markup
    assert 'aria-labelledby="generateSuggestionsLoaderTitle"' in markup
    assert 'aria-describedby="generateSuggestionsLoaderText"' in markup
    assert 'aria-current="step"' in script
    assert "setGenerateSuggestionsBackgroundInert" in script
    assert "Your suggestions and review packet are ready for inspection." in script
    assert 'button.disabled = true' in script[script.index("function openGenerateSuggestionsWorkspace"):]


def test_pipeline_overlay_waits_and_offers_planning_action():
    markup = UI.read_text(encoding="utf-8")
    script = APP_JS.read_text(encoding="utf-8")
    for overlay_id in [
        "pageLoadingOverlay",
        "pipelineOverlayCard",
        "pipelineOverlayLoading",
        "pipelineOverlaySuccess",
        "pipelineOverlayFailure",
    ]:
        assert f'id="{overlay_id}"' in markup
    assert "Running live job pipeline" in markup
    assert "Pipeline run is ready" in markup
    assert 'id="pipelineSuccessPlanningBtn">View Planning</button>' in markup
    assert 'window.location.href = "/planning"' in script
    assert 'qs("pipelineSuccessOkBtn").addEventListener' in script
    assert "workflow-overlay__panel" in markup
    assert "workflow-overlay--pipeline" in markup
    assert "workflow-step-viewport" in markup
    assert "pipeline-workflow-visual" not in markup
    assert "pipeline-workflow-orbit" not in markup
    assert "pipelineSuccessStageStepper" in markup
    assert "pipelineFailureStageStepper" in markup
    assert "workflow-current-activity" in markup
    assert "workflow-current-activity__spinner" in markup
    assert 'id="pipelineLoadingMeta"' in markup
    assert "Your job results and planning artifacts are ready to review." in script
    assert 'qs("pipelineSuccessPlanningBtn").disabled = true' in script
    assert "No application actions were taken." in script
    assert "PIPELINE_VISIBLE_STAGE_GROUPS" in script
    assert 'document.body.classList.add("pipeline-workflow-open")' in script
    assert 'document.body.classList.remove("pipeline-workflow-open")' in script
    assert 'window.location.href = "/planning"' in script
    assert "window.setTimeout" not in script[script.index("function showPipelineSuccessOverlay"):script.index("function showPageLoadingOverlay")]
    for label in [
        "Starting pipeline",
        "Collecting jobs",
        "Filtering and deduplicating",
        "Ranking opportunities",
        "Running job intelligence",
        "Evaluating fit",
        "Matching resumes",
        "Prioritizing applications",
        "Preparing planning artifacts",
        "Finalizing run",
    ]:
        assert label in script


def test_processing_surfaces_share_compact_moving_step_viewport_and_reduced_motion():
    source = CSS.read_text(encoding="utf-8")
    canonical_start = source.index("/* phase129c: canonical shared workflow overlay system. */")
    assert ".workflow-overlay__panel" in source
    pipeline_css = source[source.index(".workflow-overlay--pipeline {"):source.index(".workflow-overlay--tailoring {")]
    pipeline_panel_css = source[source.index("html[data-theme] body .workflow-overlay--pipeline .workflow-overlay__panel"):source.index(".workflow-overlay__header {")]
    assert "height: 100dvh" in pipeline_css
    assert "overflow-y: auto" in pipeline_css
    assert "overflow-x: hidden" in pipeline_css
    assert "overscroll-behavior: contain" in pipeline_css
    assert "width: 100% !important" in pipeline_panel_css
    assert "min-height: 100dvh !important" in pipeline_panel_css
    assert "max-height: none !important" in pipeline_panel_css
    assert "overflow: visible !important" in pipeline_panel_css
    assert "body.pipeline-workflow-open" in source
    assert ".workflow-overlay--pipeline .workflow-overlay__header" in source
    assert "position: sticky" in source
    assert ".workflow-current-activity__spinner" in source
    metric_start = source.index(".pipeline-loading-counts {", canonical_start)
    metric_end = source.index(".pipeline-count-chip {", metric_start)
    metric_css = source[metric_start:metric_end]
    assert "display: flex !important" in metric_css
    assert "flex-wrap: wrap" in metric_css
    assert "justify-content: center !important" in metric_css
    assert ".workflow-overlay__body" in source
    assert ".workflow-overlay--pipeline" in source
    assert ".workflow-overlay--tailoring" in source
    assert 'html[data-theme="light"] .workflow-overlay' in source
    assert 'html[data-theme="dark"] .workflow-overlay--tailoring' in source
    # The tailoring overlay accent was retuned away from violet (#7c3aed) at
    # 340be82c; the invariant is that pipeline and tailoring keep DISTINCT
    # accents, not the old hex.
    assert "--workflow-accent: #2563eb" in source
    tailoring = source.split(".workflow-overlay--tailoring {", 1)[1].split("}", 1)[0]
    assert "--workflow-accent: #bfaac5" in tailoring
    assert "--workflow-accent: #2563eb" not in tailoring
    assert ".workflow-step-viewport" in source
    assert ".workflow-step-track" in source
    assert ".workflow-step.is-complete" in source
    assert ".workflow-step.is-active" in source
    assert ".workflow-step.is-pending" in source
    assert ".workflow-step.is-error" in source
    assert ".workflow-step.is-previous" in source
    assert ".workflow-step.is-active-position" in source
    assert ".workflow-step.is-next" in source
    assert ".workflow-step.is-upcoming" in source
    assert ".workflow-step.is-hidden" in source
    tailoring_panel_start = source.index(
        "html[data-theme] body .workflow-overlay--tailoring .workflow-overlay__panel"
    )
    tailoring_panel_end = source.index(".workflow-overlay--tailoring .workflow-overlay__header", tailoring_panel_start)
    tailoring_panel_css = source[tailoring_panel_start:tailoring_panel_end]
    assert "width: min(680px, calc(100vw - 32px)) !important" in tailoring_panel_css
    assert "border-radius: 22px !important" in tailoring_panel_css
    assert "grid-template-rows: auto auto minmax(0, 1fr) auto !important" in tailoring_panel_css
    tailoring_steps_start = source.index(".workflow-overlay--tailoring .workflow-step,")
    tailoring_steps_end = source.index(
        ".workflow-overlay--tailoring .workflow-step:not(:last-child)::after",
        tailoring_steps_start,
    )
    tailoring_steps_css = source[tailoring_steps_start:tailoring_steps_end]
    assert "position: relative !important" in tailoring_steps_css
    assert "opacity: 1 !important" in tailoring_steps_css
    assert "transform: none !important" in tailoring_steps_css
    assert ".workflow-overlay--tailoring.is-error .workflow-step:not(.is-active-position)" in source
    assert "body.tailoring-workflow-open" in source
    assert ".workflow-overlay--tailoring .workflow-overlay__safety" in source
    assert ".workflow-overlay--tailoring .workflow-overlay__actions button" in source
    pipeline_timeline_start = source.index(".workflow-overlay--pipeline .workflow-step-track")
    pipeline_timeline_end = source.index(".workflow-overlay--pipeline .workflow-step {", pipeline_timeline_start)
    pipeline_timeline_css = source[pipeline_timeline_start:pipeline_timeline_end]
    assert "display: grid" in pipeline_timeline_css
    assert "height: auto" in pipeline_timeline_css
    pipeline_step_css = source[source.index(".workflow-overlay--pipeline .workflow-step {"):source.index(".workflow-step:not(:last-child)::after")]
    assert "position: relative !important" in pipeline_step_css
    assert "transform: none !important" in pipeline_step_css
    assert "transform 420ms" in source
    assert "@keyframes workflow-step-spin" in source
    assert "@media (max-width: 640px)" in source
    assert "@media (prefers-reduced-motion: reduce)" in source
    reduced_motion = source[source.index("@media (prefers-reduced-motion: reduce)"):]
    assert ".workflow-current-activity__spinner" in reduced_motion
    assert "animation: none !important" in reduced_motion
    assert "phase129b: shared cinematic workflow overlays" not in source
    assert "generate-suggestions-document-stack" not in source
    assert "pipeline-workflow-orbit" not in source
    assert "pipeline-success-gif" not in source
    assert PLANNING_UI.read_text(encoding="utf-8").count("<style>") == 0


def test_step_tracks_update_from_state_without_rebuilding_every_poll():
    app_script = APP_JS.read_text(encoding="utf-8")
    planning_script = PLANNING_JS.read_text(encoding="utf-8")
    pipeline_render = app_script[app_script.index("function renderPipelineStageStepper"):app_script.index("function getPipelineSuccessKey")]
    suggestions_render = planning_script[planning_script.index("function renderGenerateSuggestionsSteps"):planning_script.index("function startGenerateSuggestionsStepTimer")]

    assert "getPipelineStageRenderModel(pipeline, mode)" in pipeline_render
    assert "target.children.length !== model.groups.length" in pipeline_render
    assert 'target.dataset.activeIndex = String(currentGroupIndex)' in pipeline_render
    assert "getWorkflowStepPositionClass" in pipeline_render
    assert "track.children.length !== GENERATE_SUGGESTIONS_STEPS.length" in suggestions_render
    assert 'track.dataset.activeIndex = String(cappedIndex)' in suggestions_render
    assert "getGenerateSuggestionsStepPositionClass" not in suggestions_render
    assert 'step.setAttribute("aria-current", "step")' in suggestions_render
    assert 'step.removeAttribute("aria-current")' in suggestions_render
    assert "%" not in pipeline_render
    assert "%" not in suggestions_render


def test_phase129b_does_not_touch_backend_markers():
    markers = ("phase129b", "pipelineSuccessPlanningBtn", "auth-workflow-node")
    for relative in (
        "src/app/api.py",
        "src/app/services.py",
        "src/pipeline/collector.py",
        "src/matching/scorer.py",
        "batch_select_best_resume_variant.py",
    ):
        source = (ROOT / relative).read_text(encoding="utf-8")
        assert all(marker not in source for marker in markers), relative
