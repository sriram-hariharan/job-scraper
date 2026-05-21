from pathlib import Path


def test_onboarding_role_cards_use_display_safe_tool_labels():
    source = Path("src/app/onboarding_ui.py").read_text(encoding="utf-8")

    assert '"backend_engineering": "Python, Go, Node.js"' in source
    assert '"data_science": "Python, R, statistics"' in source
    assert "go\\b" not in source
    assert "node\\.?js" not in source
    assert "r\\b" not in source


def test_onboarding_copy_is_user_facing_and_cache_busted():
    source = Path("src/app/onboarding_ui.py").read_text(encoding="utf-8")

    assert "ApplyLens will use these preferences to tune your job queue and resume matching." in source
    assert "without changing the pipeline defaults" not in source
    assert "role_onboarding_r10" in source


def test_onboarding_resume_satisfied_copy_contract():
    js = Path("src/app/static/onboarding.js").read_text(encoding="utf-8")

    assert "Resume requirement satisfied." in js
    assert "Upload at least one profile resume." in js


def test_profile_role_mapping_summary_has_click_affordance_and_cache_bust():
    profile_js = Path("src/app/static/profile.js").read_text(encoding="utf-8")
    profile_ui = Path("src/app/profile_ui.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    assert "resume-role-summary-caret" in profile_js
    assert "resume-role-summary-caret" in css
    assert "profile_preferences_menu_r1" in profile_ui
    assert "role_profile_preferences_menu_r1" in profile_ui


def test_profile_preferences_menu_page_reuses_onboarding_preferences_contract():
    profile_js = Path("src/app/static/profile.js").read_text(encoding="utf-8")
    profile_ui = Path("src/app/profile_ui.py").read_text(encoding="utf-8")
    shell = Path("src/app/ui_shell.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    assert '@router.get("/profile/preferences", response_class=HTMLResponse)' in profile_ui
    assert 'href="/profile/preferences"' in shell
    assert "profile-dropdown-nav-icon--preferences" in shell
    assert 'src="/static/media/preferences_icon.svg"' in shell
    assert 'src="/static/media/profile_icon.svg"' in profile_ui
    assert 'src="/static/media/scan_icon.svg"' in profile_ui
    assert 'id="profilePreferencesForm"' in profile_ui
    assert '"/onboarding/preferences"' in profile_js
    assert "loadProfilePreferences" in profile_js
    assert "saveProfilePreferences" in profile_js
    assert "isProfilePreferencesPage" in profile_js
    assert ".profile-preferences-section" in css
    assert ".profile-dropdown-nav-icon--preferences" in css


def test_floating_job_assistant_shell_contract():
    from src.app.ui_shell import NAV_ITEMS

    shell = Path("src/app/ui_shell.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    required_ids = [
        "floatingIntelligenceChat",
        "floatingIntelligenceChatButton",
        "floatingIntelligenceChatPanel",
        "floatingIntelligenceChatCloseBtn",
        "floatingIntelligenceModeSelect",
        "floatingIntelligenceInput",
        "floatingIntelligenceSendBtn",
        "floatingIntelligenceMessages",
        "floatingIntelligenceStatus",
    ]

    for element_id in required_ids:
        assert element_id in shell

    for selector in [
        "#floatingIntelligenceChatButton",
        "#floatingIntelligenceChatPanel",
        "#floatingIntelligenceChatPanel.hidden",
        ".floating-intelligence-chat-compose",
        "@media (max-width: 560px)",
    ]:
        assert selector in css

    assert "Intelligence" not in [label for label, _href, _short_label in NAV_ITEMS]
