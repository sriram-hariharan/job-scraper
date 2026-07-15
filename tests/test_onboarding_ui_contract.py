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


def test_onboarding_and_profile_share_accessible_location_selector_contract():
    onboarding_ui = Path("src/app/onboarding_ui.py").read_text(encoding="utf-8")
    profile_ui = Path("src/app/profile_ui.py").read_text(encoding="utf-8")
    onboarding_js = Path("src/app/static/onboarding.js").read_text(encoding="utf-8")
    profile_js = Path("src/app/static/profile.js").read_text(encoding="utf-8")
    selector_js = Path("src/app/static/preference_location_selector.js").read_text(encoding="utf-8")

    assert "_location_preferences_html" in onboarding_ui
    assert '_location_preferences_html(prefix="onboarding")' in onboarding_ui
    assert '_location_preferences_html(prefix="profilePreferences")' in profile_ui
    assert onboarding_ui.count('role="combobox"') == 1
    assert onboarding_ui.count('role="listbox"') == 1
    assert 'aria-activedescendant' in selector_js
    assert 'event.key === "ArrowDown"' in selector_js
    assert 'event.key === "ArrowUp"' in selector_js
    assert 'event.key === "Enter"' in selector_js
    assert 'event.key === "Escape"' in selector_js
    assert 'event.key === "Backspace"' in selector_js
    assert 'credentials: "same-origin"' in selector_js
    assert "/onboarding/location-search" in selector_js
    assert "preferred_location_specs" in onboarding_js
    assert "location_strict_match" in onboarding_js
    assert "preferred_location_specs" in profile_js
    assert "location_show_others_if_unmatched" in profile_js
    assert "preferredLocationsInput" not in onboarding_ui
    assert "profilePreferredLocationsInput" not in profile_ui


def test_location_selector_preserves_legacy_chips_and_strict_fallback_semantics():
    selector_js = Path("src/app/static/preference_location_selector.js").read_text(encoding="utf-8")
    onboarding_ui = Path("src/app/onboarding_ui.py").read_text(encoding="utf-8")

    assert 'type: "legacy_text"' in selector_js
    assert "seenLabels" in selector_js
    assert 'className = `preference-location-chip${item.type === "legacy_text"' in selector_js
    assert "fallback.disabled = !strictEnabled" in selector_js
    assert "if (!strictEnabled) fallback.checked = false" in selector_js
    assert "location_show_others_if_unmatched: Boolean(strict.checked && fallback.checked)" in selector_js
    assert "Saved now. Applied to new pipeline runs after location filtering is enabled." in onboarding_ui


def test_preferences_premium_responsive_and_reduced_motion_contract():
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
    onboarding_ui = Path("src/app/onboarding_ui.py").read_text(encoding="utf-8")
    profile_ui = Path("src/app/profile_ui.py").read_text(encoding="utf-8")

    assert "preferences-command-header" in onboarding_ui
    assert "preferences-command-header" in profile_ui
    assert "onboardingConfigurationSummary" in onboarding_ui
    assert "profilePreferencesConfigurationSummary" in profile_ui
    assert "onboardingSelectAllRolesBtn" in onboarding_ui
    assert "onboardingClearAllRolesBtn" in onboarding_ui
    assert ".preference-location-results" in css
    assert "max-height: min(330px, 45vh)" in css
    assert ".preference-location-policy" in css
    assert "@media (max-width: 760px)" in css
    assert "@media (prefers-reduced-motion: reduce)" in css


def test_work_mode_is_not_part_of_onboarding_or_profile_ui_contract():
    onboarding_source = Path("src/app/onboarding_ui.py").read_text(encoding="utf-8")
    profile_source = Path("src/app/profile_ui.py").read_text(encoding="utf-8")
    profile_js = Path("src/app/static/profile.js").read_text(encoding="utf-8")

    assert "work_modes" not in onboarding_source
    assert "Work mode" not in onboarding_source
    assert "work_modes" not in profile_source
    assert "Work mode" not in profile_source
    assert "work_modes" not in profile_js
