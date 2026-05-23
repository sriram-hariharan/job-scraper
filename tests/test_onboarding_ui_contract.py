from pathlib import Path


def test_onboarding_page_defines_authenticated_flow():
    source = Path("src/app/onboarding_ui.py").read_text(encoding="utf-8")

    assert '@router.get("/onboarding", response_class=HTMLResponse)' in source
    assert 'id="onboardingForm"' in source
    assert 'name="selected_role_families"' in source
    assert "/profile?onboarding=resume_upload" in source


def test_onboarding_role_cards_render_decorative_icons():
    source = Path("src/app/onboarding_ui.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    assert "ROLE_FAMILY_ICON_SVGS" in source
    assert 'class="onboarding-role-icon"' in source
    assert 'class="onboarding-role-icon-svg"' in source
    assert 'aria-hidden="true"' in source
    assert 'focusable="false"' in source
    assert ".onboarding-role-icon" in css
    assert ".onboarding-role-icon-svg" in css


def test_shell_redirects_incomplete_onboarding():
    source = Path("src/app/static/shell.js").read_text(encoding="utf-8")

    assert 'fetch("/onboarding/status"' in source
    assert 'payload.onboarding_completed === false' in source
    assert 'window.location.href = "/onboarding"' in source


def test_onboarding_client_saves_preferences():
    source = Path("src/app/static/onboarding.js").read_text(encoding="utf-8")

    assert '"/onboarding/preferences"' in source
    assert "selected_role_families" in source
    assert "onboarding_completed" in source
    assert "work_modes" not in source


def test_work_mode_is_not_part_of_onboarding_or_profile_ui_contract():
    onboarding_source = Path("src/app/onboarding_ui.py").read_text(encoding="utf-8")
    profile_source = Path("src/app/profile_ui.py").read_text(encoding="utf-8")
    profile_js = Path("src/app/static/profile.js").read_text(encoding="utf-8")

    assert "work_modes" not in onboarding_source
    assert "Work mode" not in onboarding_source
    assert "work_modes" not in profile_source
    assert "Work mode" not in profile_source
    assert "work_modes" not in profile_js
