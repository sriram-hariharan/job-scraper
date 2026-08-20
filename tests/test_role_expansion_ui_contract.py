import re
from pathlib import Path

from src.app.profile_ui import _preferences_section_html


def test_onboarding_role_cards_use_display_safe_tool_labels():
    source = Path("src/app/onboarding_ui.py").read_text(encoding="utf-8")

    assert '"backend_engineering": "Python, Go, Node.js"' in source
    assert '"data_science": "Python, R, statistics"' in source
    assert "go\\b" not in source
    assert "node\\.?js" not in source
    assert "r\\b" not in source


def test_onboarding_copy_is_user_facing_and_cache_busted():
    source = Path("src/app/onboarding_ui.py").read_text(encoding="utf-8")

    assert "Build a focused search profile for the roles, seniority, locations, and signals that matter to you." in source
    assert "without changing the pipeline defaults" not in source
    assert 'href="/static/styles.css?v=preferences_toolbar_ownership_r11"' in source
    assert 'src="/static/onboarding.js?v=phase1_step8b_r1"' in source


def test_onboarding_resume_satisfied_copy_contract():
    js = Path("src/app/static/onboarding.js").read_text(encoding="utf-8")

    assert '${profileResumeCount} resume${profileResumeCount === 1 ? "" : "s"} ready' in js
    assert ': "Ready")' in js
    assert ': "Resume required"' in js
    assert "Add at least one profile resume before completing onboarding." in js


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
    preferences_css = Path("src/app/static/preferences.css").read_text(encoding="utf-8")
    preferences_section = _preferences_section_html()

    assert '@router.get("/profile/preferences", response_class=HTMLResponse)' in profile_ui
    assert 'href="/profile/preferences"' in shell
    assert "profile-dropdown-nav-icon--preferences" in shell
    assert 'src="/static/media/preferences_icon.svg"' in shell
    assert 'src="/static/media/profile_icon.svg"' in profile_ui
    assert 'src="/static/media/scan_icon.svg"' in profile_ui
    assert 'id="profilePreferencesForm"' in preferences_section
    assert '"/onboarding/preferences"' in profile_js
    assert "loadProfilePreferences" in profile_js
    assert "saveProfilePreferences" in profile_js
    assert "isProfilePreferencesPage" in profile_js
    assert ".profile-preferences-section" in preferences_css
    assert re.search(r"(?m)^\s*\.profile-preferences-section(?:\s|,|\{)", css) is None
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
        ".floating-intelligence-chat-intent-chip",
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
    assert "buildEmptySearchResponseHtml" in chat_js
    assert "I did not find direct matches in the current job corpus." in chat_js
    assert "No search results returned." not in chat_js
    assert "OPENING_ASSISTANT_GREETING" in chat_js
    assert "ensureOpeningAssistantGreeting" in chat_js
    # The greeting is rendered as a designed empty state, not an assistant chat bubble.
    assert "buildEmptyStateHtml" in chat_js
    assert "escapeHtml(OPENING_ASSISTANT_GREETING)" in chat_js
    assert "What would you like to explore?" in chat_js
    assert "search the current job corpus" in chat_js
    assert "compare roles" in chat_js
    assert "inspect requirements" in chat_js
    assert "identify useful skills" in chat_js
    assert "saved or current jobs" not in chat_js
    assert "grounded answers from available job postings" in chat_js
    assert "Searched jobs" in chat_js
    assert "Answered from corpus" in chat_js
    assert 'id="floatingIntelligenceModeSelect" hidden' in shell
    assert "/static/floating_intelligence_chat.js?v=floating_job_assistant_r7" in shell
    assert "Intelligence" not in [label for label, _href, _short_label in NAV_ITEMS]


def test_floating_job_assistant_functional_chat_contract():
    """Item 3D: suggested prompts, New Chat, Stop, Retry, composer, provider metadata."""
    shell = Path("src/app/ui_shell.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
    chat_js = Path("src/app/static/floating_intelligence_chat.js").read_text(encoding="utf-8")

    # New Chat, jump-to-latest, and the textarea composer exist in the shell.
    assert 'id="floatingIntelligenceNewChatBtn"' in shell
    assert 'id="floatingIntelligenceJumpBtn"' in shell
    assert '<textarea' in shell
    assert 'id="floatingIntelligenceInput"' in shell
    assert "floating-intelligence-chat-stop-icon" in shell

    # Suggested prompts are clickable and carry a real request string.
    assert "data-floating-chat-prompt" in chat_js
    assert "request:" in chat_js

    # Frontend-only cancellation via AbortController, with stale-response guards.
    assert "AbortController" in chat_js
    assert "controller.signal" in chat_js
    assert "AbortError" in chat_js
    assert "activeRequestId" in chat_js
    assert "requestId !== activeRequestId" in chat_js

    # New Chat / Retry are transient frontend state only.
    assert "startNewChat" in chat_js
    assert "resetToEmptyState" in chat_js
    assert "data-floating-chat-retry" in chat_js
    assert "skipUserEcho" in chat_js

    # Composer: Enter sends, Shift+Enter inserts a newline.
    assert "!event.shiftKey" in chat_js
    assert "autoGrowComposer" in chat_js

    # Provider/model metadata is rendered from the existing backend contract only.
    assert "llm_provider" in chat_js
    assert "llm_model" in chat_js
    assert "llm_fallback_used" in chat_js
    assert "insufficient_evidence" in chat_js

    # Scroll pinning replaces unconditional forced scrolling.
    assert "isNearBottom" in chat_js
    assert "scrollToLatest" in chat_js

    # Links stay safe and the endpoint contract is unchanged.
    assert 'rel="noopener noreferrer"' in chat_js
    assert "/assistant/query" in chat_js

    for selector in [
        ".floating-intelligence-chat-thinking",
        ".floating-intelligence-chat-retry-btn",
        ".floating-intelligence-chat-provider-meta",
        ".floating-intelligence-chat-insufficient",
        ".floating-intelligence-chat-jump-btn",
        '#floatingIntelligenceSendBtn[data-state="busy"]',
    ]:
        assert selector in css


def test_floating_job_assistant_error_classification_contract():
    """Item 3D-R: execution failure is not insufficient evidence, and leaks no internals."""
    shell = Path("src/app/ui_shell.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
    chat_js = Path("src/app/static/floating_intelligence_chat.js").read_text(encoding="utf-8")
    answerer = Path("src/rag/rag_answerer.py").read_text(encoding="utf-8")

    # The frontend markers must still match the strings the backend actually emits.
    # Adjacent Python string literals are joined so multi-line answers compare as
    # they do at runtime.
    joined_answerer = re.sub(r'"\s*\n\s*f?"', "", answerer)
    assert "grounded answer generation failed" in joined_answerer
    assert "the LLM timed out" in joined_answerer
    assert "retrieval failed" in joined_answerer
    for marker in [
        "grounded answer generation failed",
        "the LLM timed out",
        "retrieval failed",
    ]:
        assert marker in chat_js

    # Provider/runtime failures are classified separately from insufficient evidence.
    assert "classifyAnswerFailure" in chat_js
    assert "ANSWER_FAILURE_MARKERS" in chat_js
    assert "buildAnswerFailureHtml" in chat_js
    assert '"provider"' in chat_js
    assert "AI answer temporarily unavailable" in chat_js
    assert "The configured AI provider or model could not complete this request." in chat_js

    # Internal identifiers are never rendered as user-facing copy.
    assert "grounded_rag_owner_execution_unavailable" not in chat_js
    assert "grounded_rag_owner_route_unavailable" not in chat_js
    assert "grounded_rag_owner_execution_unavailable" not in shell

    # Retry is offered for provider/runtime failures, not for search turns.
    assert "isRetryableFailure" in chat_js
    assert "appendRetryAction(answerEl)" in chat_js

    # Failure treatment is visually distinct from the amber insufficient-evidence block.
    assert ".floating-intelligence-chat-failure" in css
    assert ".floating-intelligence-chat-failure-title" in css
    assert ".floating-intelligence-chat-insufficient" in css


def test_floating_job_assistant_truthful_prompts_and_neutral_status():
    """Item 3D-R: prompts map to real router behavior; status badge implies no health."""
    from src.app.services import route_assistant_intent

    shell = Path("src/app/ui_shell.py").read_text(encoding="utf-8")
    chat_js = Path("src/app/static/floating_intelligence_chat.js").read_text(encoding="utf-8")

    expected_prompts = {
        "Show backend engineering roles": "search_jobs",
        "Show data engineering roles": "search_jobs",
        "Show postings that mention AWS": "search_jobs",
        "Compare Java and Python requirements in available postings": "answer_job_query",
    }
    for prompt, expected_intent in expected_prompts.items():
        assert prompt in chat_js
        assert route_assistant_intent(prompt)["intent"] == expected_intent

    # No personalization claims: the assistant has no resume/profile/saved-job context.
    assert "Find matching roles" not in chat_js
    for banned in ["your resume", "your profile", "saved jobs", "matching your"]:
        assert banned.lower() not in chat_js.lower()

    # Neutral capability badge, not a live health indicator.
    assert "Job corpus" in shell
    assert "Grounded in job corpus" not in shell
    assert "floating-intelligence-chat-status-dot" not in shell


def test_floating_job_assistant_theme_contrast_contract():
    """Item 3D-R: explicit readable text tiers exist for both themes."""
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    # Both themes define the chat surfaces explicitly.
    assert "#floatingIntelligenceInput::placeholder" in css
    assert 'html[data-theme="light"] #floatingIntelligenceInput::placeholder' in css
    assert (
        'html[data-theme="light"] #floatingIntelligenceMessages'
        " .floating-intelligence-chat-suggested-prompt-hint"
    ) in css
    assert 'html[data-theme="light"] .floating-intelligence-chat-card-meta-item' in css
    assert 'html[data-theme="light"] .floating-intelligence-chat-failure' in css
    assert (
        "#floatingIntelligenceMessages .floating-intelligence-chat-suggested-prompt-icon"
    ) in css
    assert "#floatingIntelligenceSendBtn:disabled" in css

    # The dark panel base is opaque so page content cannot bleed through.
    assert "linear-gradient(180deg, #161d33 0%, #0c1120 100%)" in css


def test_floating_job_assistant_prompt_card_accent_contract():
    """Item 3 card fix: neutral surfaces, uniform geometry, distinct icon accents."""
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
    chat_js = Path("src/app/static/floating_intelligence_chat.js").read_text(encoding="utf-8")

    # The tiles are <button>s, so they must outrank the global CTA gradient rule
    # `button:not(...)x24` (specificity 0,24,1). Every card rule is ID-scoped.
    for stray in re.findall(r"(?m)^[^\n{]*floating-intelligence-chat-suggested-prompt[^\n{]*\{", css):
        assert "#floatingIntelligenceMessages" in stray, f"unscoped card rule: {stray.strip()}"

    # Each prompt declares a distinct accent identity, emitted as data-accent.
    assert 'data-accent="${escapeHtml(prompt.accent || "blue")}"' in chat_js
    for accent in ["blue", "violet", "amber", "teal"]:
        assert f'accent: "{accent}"' in chat_js
        assert (
            "#floatingIntelligenceMessages .floating-intelligence-chat-suggested-prompt"
            f'[data-accent="{accent}"]'
        ) in css
        assert (
            'html[data-theme="light"] #floatingIntelligenceMessages'
            " .floating-intelligence-chat-suggested-prompt"
            f'[data-accent="{accent}"]'
        ) in css

    # Accent is expressed through tokens consumed by the icon container only.
    for token in ["--prompt-accent", "--prompt-accent-bg", "--prompt-accent-border"]:
        assert token in css

    # Uniform geometry: fixed 42px icon column so text columns start identically.
    assert "grid-template-columns: 42px minmax(0, 1fr)" in css
    assert "flex: 0 0 42px !important" in css
    assert "width: 42px !important" in css
    assert "height: 42px !important" in css

    def rule_body(selector):
        body = css.split(selector + " {", 1)[1].split("}", 1)[0]
        # Strip CSS comments so documentation of intent never trips the guard.
        return re.sub(r"/\*.*?\*/", "", body, flags=re.S)

    # Dark card surface is a solid neutral slate, never a gradient or violet fill.
    dark = rule_body(
        "#floatingIntelligenceMessages .floating-intelligence-chat-suggested-prompt"
    )
    assert "background: #182033 !important" in dark
    assert "background-image: none !important" in dark
    assert "gradient" not in dark

    # Light card surface is white, never a gradient or tinted CTA fill.
    light = rule_body(
        'html[data-theme="light"] #floatingIntelligenceMessages'
        " .floating-intelligence-chat-suggested-prompt"
    )
    assert "background: #ffffff !important" in light
    assert "background-image: none !important" in light
    assert "gradient" not in light

    # No card rule anywhere may reintroduce a gradient fill.
    css_no_comments = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    for block in re.findall(
        r"[^}]*floating-intelligence-chat-suggested-prompt[^{]*\{[^}]*\}", css_no_comments
    ):
        assert "linear-gradient" not in block
        assert "radial-gradient" not in block

    # High-contrast text tiers in both themes.
    assert "color: #f8fafc !important" in css
    assert "color: #cbd5e1 !important" in css
    assert "color: #0f172a !important" in css
    assert "color: #475569 !important" in css

    # Keyboard focus stays visible.
    assert (
        "#floatingIntelligenceMessages .floating-intelligence-chat-suggested-prompt:focus-visible"
        in css
    )

    # Prompt actions themselves are unchanged.
    for request in [
        "Show backend engineering roles",
        "Show data engineering roles",
        "Show postings that mention AWS",
        "Compare Java and Python requirements in available postings",
    ]:
        assert request in chat_js


def test_rag_answer_prompt_guides_human_readable_grounded_answers():
    source = Path("src/rag/rag_answerer.py").read_text(encoding="utf-8")

    assert "direct answer" in source
    assert "concise, human-readable" in source
    assert "helpful job-search assistant, not a backend report" in source
    assert "short readable paragraphs or bullets" in source
    assert "source-grounded evidence" in source
    assert "Mention uncertainty plainly when the evidence is thin." in source
    assert "Avoid robotic phrases." in source
    assert "Never expose retrieval internals, backend errors, vector index details, or implementation details." in source
    assert "Do not invent unsupported claims." in source
    assert "Return JSON only." in source


def test_floating_job_assistant_accessibility_contract():
    """Item 3E: dialog semantics, focus management, live regions, accessible names."""
    shell = Path("src/app/ui_shell.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
    chat_js = Path("src/app/static/floating_intelligence_chat.js").read_text(encoding="utf-8")

    # Dialog semantics, named/described by existing visible copy.
    assert 'role="dialog"' in shell
    assert 'aria-modal="true"' in shell
    assert 'aria-labelledby="floatingIntelligenceChatTitle"' in shell
    assert 'aria-describedby="floatingIntelligenceChatSubtitle"' in shell
    assert 'id="floatingIntelligenceChatTitle"' in shell
    assert 'id="floatingIntelligenceChatSubtitle"' in shell

    # Launcher advertises the dialog it controls; its pinned name is preserved.
    assert 'aria-label="Open Job Assistant"' in shell
    assert 'aria-haspopup="dialog"' in shell
    assert 'aria-controls="floatingIntelligenceChatPanel"' in shell

    # Icon-only controls have accessible names that do not depend on title.
    assert 'aria-label="Start new chat"' in shell
    assert 'aria-label="Close Job Assistant"' in shell
    assert 'aria-label="Message ApplyLens AI"' in shell

    # Message stream is a polite log announcing appended content only.
    assert 'role="log"' in shell
    assert 'aria-live="polite"' in shell
    assert 'aria-relevant="additions"' in shell
    assert 'aria-atomic="false"' in shell

    # Busy state is exposed on the dialog and mirrors the state machine.
    assert 'aria-busy="false"' in shell
    assert 'panel.setAttribute("aria-busy"' in chat_js

    # Send/Stop accessible name changes with state.
    assert '"Stop generating" : "Send message"' in chat_js

    # Thinking indicator is one status, not per-dot announcements.
    assert 'aria-label="Generating answer"' in chat_js
    assert 'class="floating-intelligence-chat-thinking-dot" aria-hidden="true"' in chat_js

    # Focus management: dynamic discovery, trap, Escape, restoration.
    assert "FOCUSABLE_SELECTOR" in chat_js
    assert "focusableElements" in chat_js
    assert "trapFocus" in chat_js
    assert "restoreLauncherFocus" in chat_js
    assert 'event.key === "Escape"' in chat_js
    assert "event.shiftKey" in chat_js
    assert "preventScroll: true" in chat_js
    # The trap must not hard-code a static control list.
    assert "querySelectorAll(FOCUSABLE_SELECTOR)" in chat_js

    # Keyboard send semantics preserved.
    assert "!event.shiftKey" in chat_js

    # Focus-visible rings exist in both themes.
    assert "#floatingIntelligenceSendBtn:focus-visible" in css
    assert 'html[data-theme="light"] #floatingIntelligenceSendBtn:focus-visible' in css
    assert ".floating-intelligence-chat-suggested-prompt:focus-visible" in css

    # Mobile viewport + safe areas.
    assert "100dvh" in css
    assert "env(safe-area-inset-bottom)" in css
    assert "env(safe-area-inset-right)" in css
    assert "env(safe-area-inset-left)" in css
    assert "@media (max-width: 400px)" in css
    assert "@media (pointer: coarse)" in css

    # Long strings can never force horizontal overflow.
    assert "overflow-wrap: anywhere !important" in css

    # Reduced motion covers the added chatbot motion.
    assert "@media (prefers-reduced-motion: reduce)" in css

    # Launcher footprint contract is unchanged.
    assert "width: 64px !important" in css
    assert "width: 58px !important" in css
