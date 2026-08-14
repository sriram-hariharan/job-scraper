"""Phase 1 Step 8B — optional onboarding AI setup UI contracts."""

from pathlib import Path

from src.app.onboarding_ui import _preferences_workflow_form_html, onboarding_page
from src.app.profile_ui import profile_ai_settings_page
from src.app.provider_setup_guidance import (
    PROVIDER_KEY_GUIDANCE,
    PROVIDER_KEY_SECURITY_NOTE,
    render_provider_key_guidance_templates,
)


ROOT = Path(__file__).resolve().parents[1]
ONBOARDING_UI = (ROOT / "src/app/onboarding_ui.py").read_text(encoding="utf-8")
PROFILE_UI = (ROOT / "src/app/profile_ui.py").read_text(encoding="utf-8")
ONBOARDING_JS = (ROOT / "src/app/static/onboarding.js").read_text(encoding="utf-8")
WORKFLOW_JS = (ROOT / "src/app/static/preferences_workflow.js").read_text(encoding="utf-8")
PROFILE_AI_JS = (ROOT / "src/app/static/profile_ai_settings.js").read_text(encoding="utf-8")
PREFERENCES_CSS = (ROOT / "src/app/static/preferences.css").read_text(encoding="utf-8")
PROFILE_AI_CSS = (ROOT / "src/app/static/profile_ai_settings.css").read_text(encoding="utf-8")
SERVICES = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
API = (ROOT / "src/app/api.py").read_text(encoding="utf-8")
ONBOARDING_FORM = _preferences_workflow_form_html(prefix="onboarding", mode="onboarding")
PROFILE_FORM = _preferences_workflow_form_html(prefix="profilePreferences", mode="profile")
SYNTHETIC_SECRET = "synthetic-step8-browser-secret-never-render"


def _function(source: str, name: str, next_name: str) -> str:
    return source.split(f"function {name}", 1)[1].split(f"function {next_name}", 1)[0]


def test_onboarding_has_six_steps_and_profile_preferences_remains_five():
    assert ONBOARDING_FORM.count("data-preferences-step-target=") == 6
    assert ONBOARDING_FORM.count("data-preferences-step=") == 6
    assert 'data-preferences-step-target="4"' in ONBOARDING_FORM
    assert 'data-preferences-step-target="5"' in ONBOARDING_FORM
    assert 'data-preferences-step="4"' in ONBOARDING_FORM
    assert 'data-preferences-step="5"' in ONBOARDING_FORM
    assert "AI provider" in ONBOARDING_FORM
    assert "Connect AI" in ONBOARDING_FORM
    assert "Optional" in ONBOARDING_FORM
    assert "Step 6 of 6" in ONBOARDING_FORM

    assert PROFILE_FORM.count("data-preferences-step-target=") == 5
    assert PROFILE_FORM.count("data-preferences-step=") == 5
    assert 'data-preferences-step-target="5"' not in PROFILE_FORM
    assert 'data-preferences-step="5"' not in PROFILE_FORM
    assert "Connect AI" not in PROFILE_FORM
    assert "AI provider" not in PROFILE_FORM
    assert "Step 5 of 5" in PROFILE_FORM


def test_workflow_length_is_derived_from_rendered_panels_not_global_six():
    assert "const stepCount = panels.length;" in WORKFLOW_JS
    assert "STEP_COUNT" not in WORKFLOW_JS
    assert "stepCount - 1" in WORKFLOW_JS
    assert "of ${stepCount}" in WORKFLOW_JS
    assert "const stepCount = 6" not in WORKFLOW_JS


def test_optional_skip_is_navigation_only_and_advances_to_review():
    skip = _function(ONBOARDING_JS, "skipOnboardingAiSetup", "bindOnboardingAiEvents")
    assert "showStep(5)" in skip
    for forbidden in (
        "onboardingAiRequestJson",
        "fetch(",
        "preferred-provider",
        "test-connection",
        "credentials/",
        "onboarding/preferences",
        "localStorage",
        "sessionStorage",
    ):
        assert forbidden not in skip
    assert 'id="onboardingAiSkipBtn"' in ONBOARDING_FORM
    assert "data-preferences-skip" in ONBOARDING_FORM
    assert "Skip for now" in ONBOARDING_FORM
    assert "onboarding-ai-skip-row" not in ONBOARDING_FORM
    assert ONBOARDING_FORM.index("data-preferences-skip") > ONBOARDING_FORM.index("preferences-final-actions")


def test_ai_state_never_enters_onboarding_preferences_or_completion_gate():
    collect = _function(ONBOARDING_JS, "collectOnboardingPreferences", "renderRequirementStatus")
    requirements = _function(ONBOARDING_JS, "renderRequirementStatus", "hydrateOnboardingForm")
    assert "ai" not in collect.lower()
    assert "hasResume && selectedRoleCount > 0" in requirements
    for forbidden in ("credential", "provider", "connection", "model"):
        assert forbidden not in requirements.lower()
    assert '"has_profile_resume"' in SERVICES
    assert '"has_selected_role_family"' in SERVICES
    assert '"can_complete_onboarding": has_profile_resume and has_selected_role_family' in SERVICES
    assert "user_ai" not in SERVICES.split("def _onboarding_requirement_status", 1)[1].split(
        "def onboarding_preferences_payload", 1
    )[0]


def test_ai_initial_load_uses_only_existing_safe_read_endpoints_in_parallel():
    load = _function(ONBOARDING_JS, "loadOnboardingAiSettings", "refreshOnboardingAiSettings")
    assert "Promise.all([" in load
    assert 'onboardingAiRequestJson("/ai/settings")' in load
    assert 'onboardingAiRequestJson("/ai/settings/catalog")' in load
    for forbidden in ('method: "POST"', 'method: "PUT"', 'method: "DELETE"'):
        assert forbidden not in load
    assert 'credentials: "same-origin"' in ONBOARDING_JS
    assert "owner_user_id" not in ONBOARDING_JS + ONBOARDING_FORM


def test_provider_cards_use_catalog_models_and_safe_credential_hints():
    render = _function(
        ONBOARDING_JS,
        "renderOnboardingAiProviderCards",
        "renderOnboardingAiConnectionSelectors",
    )
    assert "onboardingAiState.catalog.providers.forEach" in render
    assert "catalogEntry.models.length" in render
    assert "providerState.credentialHint" in render
    assert 'value.credential_hint === "string"' in ONBOARDING_JS
    assert "Stored credential hint" in render
    assert "credential_ciphertext" not in ONBOARDING_JS + ONBOARDING_FORM
    assert SYNTHETIC_SECRET not in onboarding_page()
    for model_id in ("openai/gpt-oss-20b", "openai/gpt-oss-120b", "gpt-5-mini", "gpt-5.1"):
        assert model_id not in ONBOARDING_JS + ONBOARDING_UI


def test_credential_save_uses_existing_endpoint_clears_secret_and_has_no_automatic_actions():
    save = _function(
        ONBOARDING_JS,
        "saveOnboardingAiCredential",
        "setOnboardingAiPreferredProvider",
    )
    assert "`/ai/settings/credentials/${encodeURIComponent(provider)}`" in save
    assert 'method: "PUT"' in save
    assert "input.value = \"\"" in save
    assert "requestBody.api_key = \"\"" in save
    assert "submittedCredential = \"\"" in save
    assert "test-connection" not in save
    assert "preferred-provider" not in save
    assert "setOnboardingAiPreferredProvider" not in save
    assert "testOnboardingAiConnection" not in save


def test_connection_test_is_manual_bounded_and_does_not_persist_model():
    connection = _function(
        ONBOARDING_JS,
        "testOnboardingAiConnection",
        "skipOnboardingAiSetup",
    )
    assert 'onboardingAiRequestJson("/ai/settings/test-connection"' in connection
    assert "JSON.stringify({ provider, model })" in connection
    assert "payload.status !== \"connected\"" in connection
    assert "payload.content" not in connection
    assert "api_key" not in connection
    assert "preferred-provider" not in connection
    assert "localStorage" not in connection
    assert "sessionStorage" not in connection
    assert 'id="onboardingAiTestStatus"' in ONBOARDING_FORM
    assert "onboardingAiSkipBtn" in ONBOARDING_FORM


def test_preferred_provider_changes_only_from_explicit_action():
    preferred = _function(
        ONBOARDING_JS,
        "setOnboardingAiPreferredProvider",
        "testOnboardingAiConnection",
    )
    assert 'onboardingAiRequestJson("/ai/settings/preferred-provider"' in preferred
    assert 'method: "POST"' in preferred
    assert "JSON.stringify({ provider })" in preferred
    assert "model" not in preferred.lower()
    bind = _function(ONBOARDING_JS, "bindOnboardingAiEvents", "document.addEventListener")
    assert "[data-onboarding-ai-preferred]" in bind
    assert "setOnboardingAiPreferredProvider" in bind
    clear = _function(
        ONBOARDING_JS,
        "clearOnboardingAiPreferredProvider",
        "testOnboardingAiConnection",
    )
    assert 'onboardingAiRequestJson("/ai/settings/preferred-provider", { method: "DELETE" })' in clear
    assert "credentials/" not in clear
    assert "test-connection" not in clear
    assert "await refreshOnboardingAiSettings()" in clear
    assert "data-onboarding-ai-clear-preferred" in ONBOARDING_JS


def test_safe_ai_state_projects_to_review_and_live_summary_without_persistence():
    projection = _function(
        ONBOARDING_JS,
        "onboardingAiSafeProjection",
        "updateOnboardingAiSafeProjection",
    )
    update = _function(
        ONBOARDING_JS,
        "updateOnboardingAiSafeProjection",
        "extractOnboardingAiErrorCategory",
    )
    collect = _function(
        ONBOARDING_JS,
        "collectOnboardingPreferences",
        "renderRequirementStatus",
    )
    assert "AI status unavailable" in projection
    assert "AI not configured" in projection
    assert "No preferred provider · Configured:" in projection
    assert "Preferred: ${preferredLabel} · Configured: ${configuredLabel}" in projection
    assert "data-onboarding-ai-summary" in ONBOARDING_FORM
    assert "data-onboarding-ai-review-preferred" in ONBOARDING_FORM
    assert "data-onboarding-ai-review-configured" in ONBOARDING_FORM
    assert 'data-preferences-edit-step="4"' in ONBOARDING_FORM
    assert "[data-onboarding-ai-summary]" in update
    assert "[data-onboarding-ai-review-status]" in update
    assert "credentialHint" not in projection + update
    assert "onboardingAi" not in collect


def test_shared_guidance_owner_supplies_both_surfaces():
    templates = render_provider_key_guidance_templates()
    onboarding_html = onboarding_page()
    profile_html = profile_ai_settings_page()
    assert "render_provider_key_guidance_templates" in ONBOARDING_UI
    assert "render_provider_key_guidance_templates" in PROFILE_UI
    assert templates in onboarding_html
    assert templates in profile_html
    assert "providerKeyGuidanceTemplate-${provider}" in ONBOARDING_JS
    assert "providerKeyGuidanceTemplate-${provider}" in PROFILE_AI_JS
    assert "How to get your API key" in onboarding_html
    assert "How to get your API key" in profile_html


def test_guidance_uses_only_exact_official_destinations_and_safe_links():
    assert PROVIDER_KEY_GUIDANCE["openai"]["api_keys_url"] == "https://platform.openai.com/api-keys"
    assert PROVIDER_KEY_GUIDANCE["openai"]["quickstart_url"] == (
        "https://platform.openai.com/docs/quickstart/make-your-first-api-request"
    )
    assert PROVIDER_KEY_GUIDANCE["groq"]["api_keys_url"] == "https://console.groq.com/keys"
    assert PROVIDER_KEY_GUIDANCE["groq"]["quickstart_url"] == "https://console.groq.com/docs/quickstart"
    templates = render_provider_key_guidance_templates()
    assert templates.count('target="_blank"') == 4
    assert templates.count('rel="noopener noreferrer"') == 4
    assert "?" not in "".join(
        guidance[key]
        for guidance in PROVIDER_KEY_GUIDANCE.values()
        for key in ("api_keys_url", "quickstart_url")
    )
    for forbidden in ("api_key", "credential", "owner_user_id"):
        assert forbidden not in "".join(
            guidance[key]
            for guidance in PROVIDER_KEY_GUIDANCE.values()
            for key in ("api_keys_url", "quickstart_url")
        )


def test_guidance_is_concise_numbered_provider_specific_and_security_aware():
    for provider in ("groq", "openai"):
        assert len(PROVIDER_KEY_GUIDANCE[provider]["steps"]) == 4
    assert "OpenAI" in PROVIDER_KEY_GUIDANCE["openai"]["heading"]
    assert "Groq" in PROVIDER_KEY_GUIDANCE["groq"]["heading"]
    assert "selected project" in PROVIDER_KEY_GUIDANCE["groq"]["provider_note"]
    assert "encrypted" in PROVIDER_KEY_SECURITY_NOTE
    assert "masked hint" in PROVIDER_KEY_SECURITY_NOTE
    templates = render_provider_key_guidance_templates()
    assert templates.count("<details") == 2
    assert templates.count("<ol>") == 2
    assert "billing" not in templates.lower()
    assert "pricing" not in templates.lower()
    assert "free credit" not in templates.lower()


def test_provider_identity_preserves_permitted_openai_asset_and_plain_groq_wordmark():
    assert 'logo.src = "/static/media/openai_provider_logo.svg"' in ONBOARDING_JS
    assert 'onboardingAiElement("span", "onboarding-ai-provider-wordmark"' in ONBOARDING_JS
    assert "groq_provider_logo" not in ONBOARDING_JS.lower()
    assert "provider_logos/groq" not in ONBOARDING_JS.lower()
    assert "groq_ai.png" not in ONBOARDING_JS.lower()


def test_secure_modal_preserves_accessibility_clearing_and_focus_behaviors():
    page = onboarding_page()
    assert 'id="onboardingAiCredentialModal" role="dialog" aria-modal="true"' in page
    assert 'id="onboardingAiCredentialInput" type="password"' in page
    assert 'autocomplete="new-password"' in page
    assert 'aria-label="Show API key"' in page
    assert 'title="Show API key"' in page
    assert page.count('class="onboarding-ai-secret-icon"') == 2
    assert 'viewBox="0 0 24 24"' in page
    assert 'reveal ? "Hide API key" : "Show API key"' in ONBOARDING_JS
    assert 'event.key === "Escape"' in ONBOARDING_JS
    assert 'event.target === onboardingQs("onboardingAiCredentialModal")' in ONBOARDING_JS
    assert "if (restoreFocus && trigger) trigger.focus()" in ONBOARDING_JS
    assert "console." not in ONBOARDING_JS
    assert "localStorage" not in ONBOARDING_JS
    assert "sessionStorage" not in ONBOARDING_JS


def test_onboarding_ai_styles_are_scoped_compact_responsive_and_theme_owned():
    assert ".preferences-workflow .onboarding-ai-provider-grid" in PREFERENCES_CSS
    assert ".preferences-workflow .provider-key-guidance" in PREFERENCES_CSS
    assert ".onboarding-ai-modal-card" in PREFERENCES_CSS
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in PREFERENCES_CSS
    assert "@media (max-width: 720px)" in PREFERENCES_CSS
    assert "display: grid" in PREFERENCES_CSS.split(".onboarding-ai-secret-control {", 1)[1].split("}", 1)[0]
    assert "width: 28px" in PREFERENCES_CSS
    assert "width: 17px" in PREFERENCES_CSS
    assert ".profile-ai-settings-page .provider-key-guidance" in PROFILE_AI_CSS
    assert "linear-gradient" not in PREFERENCES_CSS.split(
        ".preferences-workflow .onboarding-ai-step {", 1
    )[1].split("@media (min-width: 1720px)", 1)[0]


def test_step8_adds_no_endpoint_schema_or_production_routing_activation():
    assert '"/ai/settings"' in API
    assert '"/ai/settings/catalog"' in API
    assert '"/ai/settings/credentials/{provider}"' in API
    assert '"/ai/settings/test-connection"' in API
    assert '"/ai/settings/preferred-provider"' in API
    assert "/onboarding/ai" not in API
    assert "onboarding_ai" not in API.lower()
    assert "ai_provider" not in ONBOARDING_FORM.lower().replace("onboarding-ai-provider", "")
    assert "preferred_model" not in ONBOARDING_JS + ONBOARDING_UI
    assert "llm_client" not in ONBOARDING_JS + ONBOARDING_UI
    assert "user_provider_runtime" not in ONBOARDING_JS + ONBOARDING_UI
