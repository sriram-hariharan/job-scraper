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
    chat_js_path = Path("src/app/static/floating_intelligence_chat.js")
    chat_js = chat_js_path.read_text(encoding="utf-8")

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
        assert element_id in chat_js

    for selector in [
        "#floatingIntelligenceChatButton",
        "#floatingIntelligenceChatPanel",
        "#floatingIntelligenceChatPanel.hidden",
        "#floatingIntelligenceModeSelect[hidden]",
        ".floating-intelligence-chat-message",
        ".floating-intelligence-chat-message--user",
        ".floating-intelligence-chat-message--assistant",
        ".floating-intelligence-chat-message--error",
        ".floating-intelligence-chat-bubble",
        ".floating-intelligence-chat-card",
        ".floating-intelligence-chat-card-meta",
        "#floatingIntelligenceMessages .floating-intelligence-chat-message--assistant .floating-intelligence-chat-bubble p",
        ".floating-intelligence-chat-compose",
        "@media (max-width: 560px)",
    ]:
        assert selector in css

    for generated_class in [
        "floating-intelligence-chat-message",
        "floating-intelligence-chat-message--user",
        "floating-intelligence-chat-message--assistant",
        "floating-intelligence-chat-message--error",
        "floating-intelligence-chat-bubble",
        "floating-intelligence-chat-card",
        "floating-intelligence-chat-card-meta",
    ]:
        assert generated_class in chat_js

    assert chat_js_path.exists()
    assert "/assistant/query" in chat_js
    assert "/jobs/search-lite" not in chat_js
    assert "/rag/answer" not in chat_js
    assert 'metaItem("Score"' not in chat_js
    assert 'id="floatingIntelligenceModeSelect" hidden' in shell
    assert "/static/floating_intelligence_chat.js?v=floating_job_assistant_r1" in shell
    assert "Intelligence" not in [label for label, _href, _short_label in NAV_ITEMS]


def test_rag_answer_prompt_guides_human_readable_grounded_answers():
    source = Path("src/rag/rag_answerer.py").read_text(encoding="utf-8")

    assert "direct answer" in source
    assert "concise, human-readable" in source
    assert "short readable bullets" in source
    assert "source-grounded evidence" in source
    assert "Do not expose backend, retrieval, vector index, timeout, or diagnostic internals." in source
    assert "Return JSON only." in source
