from pathlib import Path


def test_onboarding_page_defines_authenticated_flow():
    source = Path("src/app/onboarding_ui.py").read_text(encoding="utf-8")

    assert '@router.get("/onboarding", response_class=HTMLResponse)' in source
    assert 'id="onboardingForm"' in source
    assert 'name="selected_role_families"' in source
    assert "/profile?onboarding=resume_upload" in source


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
