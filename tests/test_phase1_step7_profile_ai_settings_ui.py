"""Phase 1 Step 7 — authenticated Profile AI Settings UI contracts."""

from pathlib import Path

from src.app.api import app
from src.app.profile_ui import profile_ai_settings_page
from src.app.ui_shell import render_top_shell


ROOT = Path(__file__).resolve().parents[1]
PROFILE_UI = (ROOT / "src/app/profile_ui.py").read_text(encoding="utf-8")
UI_SHELL = (ROOT / "src/app/ui_shell.py").read_text(encoding="utf-8")
AI_SETTINGS_JS = (ROOT / "src/app/static/profile_ai_settings.js").read_text(
    encoding="utf-8"
)
AI_SETTINGS_CSS = (ROOT / "src/app/static/profile_ai_settings.css").read_text(
    encoding="utf-8"
)
APP_REDESIGN_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(
    encoding="utf-8"
)
OPENAI_PROVIDER_LOGO = ROOT / "src/app/static/media/openai_provider_logo.svg"
SYNTHETIC_SECRET = "synthetic-step7-browser-secret-never-persist"


def _function(source: str, name: str, next_name: str) -> str:
    return source.split(f"function {name}", 1)[1].split(
        f"function {next_name}", 1
    )[0]


def test_profile_ai_settings_route_exists_and_uses_shared_shell():
    assert any(route.path == "/profile/ai-settings" for route in app.routes)
    html = profile_ai_settings_page()
    assert 'id="appShell"' in html
    assert "render_top_shell(\"/profile/ai-settings\")" in PROFILE_UI
    assert "AI Settings" in html
    assert "Configure your AI providers and test model access." in html


def test_profile_ai_settings_keeps_shared_toolbar_in_standard_top_right_mode():
    shell = render_top_shell("/profile/ai-settings")
    assert 'class="app-shell-top-right"' in shell
    assert "app-shell-top-right--flow" not in shell
    assert "app-shell-top-right--flow" in render_top_shell("/profile/preferences")


def test_account_dropdown_adds_ai_settings_without_removing_existing_links():
    shell = render_top_shell("/profile/ai-settings")
    for href in (
        "/profile/saved-scans",
        "/profile",
        "/profile/preferences",
        "/profile/ai-settings",
    ):
        assert f'href="{href}"' in shell
    assert "Providers, API keys, and model access" in shell
    assert '{_icon_svg("ai-settings")}' in UI_SHELL


def test_page_has_dedicated_static_owners_and_no_browser_owner_control():
    html = profile_ai_settings_page()
    assert 'src="/static/profile_ai_settings.js' in html
    assert 'href="/static/profile_ai_settings.css' in html
    assert "owner_user_id" not in html
    assert SYNTHETIC_SECRET not in html
    for forbidden in (
        "GROQ_API_KEY",
        "OPENAI_API_KEY",
        "credential_ciphertext",
        "Fernet",
        "DATABASE_URL",
    ):
        assert forbidden not in html


def test_initial_load_fetches_both_read_apis_in_parallel_and_does_not_mutate():
    load_page = _function(AI_SETTINGS_JS, "loadPage", "refreshSettings")
    assert "Promise.all([" in load_page
    assert 'requestJson("/ai/settings")' in load_page
    assert 'requestJson("/ai/settings/catalog")' in load_page
    assert "test-connection" not in load_page
    assert "preferred-provider" not in load_page
    assert "credentials/" not in load_page
    assert 'method: "POST"' not in load_page
    assert 'method: "PUT"' not in load_page
    assert 'method: "DELETE"' not in load_page


def test_provider_cards_and_selectors_derive_from_validated_catalog_data():
    assert 'state.catalog.providers.forEach((catalogEntry)' in AI_SETTINGS_JS
    assert 'state.catalog.providers.forEach((entry)' in AI_SETTINGS_JS
    assert "appendProviderOptions(providerSelect, false)" in AI_SETTINGS_JS
    assert "appendProviderOptions(select, true)" in AI_SETTINGS_JS
    assert 'noPreference.value = ""' in AI_SETTINGS_JS
    assert 'state.settings.preferredProvider || ""' in AI_SETTINGS_JS
    assert "state.catalog.providers" in AI_SETTINGS_JS


def test_provider_identity_uses_correct_openai_label_and_permitted_assets():
    assert 'normalizedProvider === "openai"' in AI_SETTINGS_JS
    assert 'return "OpenAI"' in AI_SETTINGS_JS
    assert "Openai" not in profile_ai_settings_page() + AI_SETTINGS_JS
    assert 'logo.src = "/static/media/openai_provider_logo.svg"' in AI_SETTINGS_JS
    assert OPENAI_PROVIDER_LOGO.is_file()
    assert OPENAI_PROVIDER_LOGO.read_text(encoding="utf-8").lstrip().startswith("<svg")
    assert "groq_provider_logo" not in AI_SETTINGS_JS.lower()
    assert not any(
        "groq" in asset.name.lower()
        for asset in (ROOT / "src/app/static/media").iterdir()
    )
    assert '"profile-ai-settings-provider-wordmark", "Groq"' in AI_SETTINGS_JS
    assert "Groq is a trademark of Groq LLC" in profile_ai_settings_page()


def test_configured_provider_uses_only_backend_credential_hint():
    render_cards = _function(AI_SETTINGS_JS, "renderProviderCards", "appendProviderOptions")
    assert "providerState.credentialHint" in render_cards
    assert 'value.credential_hint === "string"' in AI_SETTINGS_JS
    assert "slice(" not in render_cards
    assert "substring(" not in render_cards
    assert "submittedCredential" not in render_cards


def test_secure_add_replace_modal_is_accessible_and_write_only():
    html = profile_ai_settings_page()
    assert 'id="aiCredentialModal"' in html
    assert 'role="dialog"' in html
    assert 'aria-modal="true"' in html
    assert 'id="aiCredentialInput" type="password"' in html
    assert 'autocomplete="new-password"' in html
    assert "Add API key" in html
    assert "Replace API key" in AI_SETTINGS_JS
    assert 'method: "PUT"' in _function(
        AI_SETTINGS_JS, "submitCredential", "removeCredential"
    )


def test_credential_modal_is_compact_aligned_and_has_one_footer_exit_path():
    html = profile_ai_settings_page()
    credential_modal = html.split('id="aiCredentialModal"', 1)[1].split(
        'id="aiCredentialRemoveModal"', 1
    )[0]
    assert "aiCredentialModalCloseBtn" not in credential_modal
    assert "aiCredentialModalCloseBtn" not in AI_SETTINGS_JS
    assert 'id="aiCredentialCancelBtn"' in credential_modal
    assert 'id="aiCredentialSaveBtn"' in credential_modal
    assert "profile-ai-settings-modal-header" in credential_modal
    assert "profile-ai-settings-modal-body" in credential_modal
    assert "profile-ai-settings-modal-footer" in credential_modal
    assert "profile-ai-settings-credential-card" in credential_modal


def test_credential_visibility_uses_inline_icons_for_both_states():
    html = profile_ai_settings_page()
    toggle = html.split('id="aiCredentialVisibilityBtn"', 1)[1].split(
        "</button>", 1
    )[0]
    assert 'class="ghost-btn profile-ai-settings-secret-toggle"' in html
    assert 'aria-label="Show API key"' in toggle
    assert 'title="Show API key"' in toggle
    assert toggle.count("<svg") == 2
    assert toggle.count('viewBox="0 0 24 24"') == 2
    assert toggle.count('fill="none"') == 2
    assert toggle.count('stroke="currentColor"') == 2
    assert toggle.count('stroke-width="1.8"') == 2
    assert 'id="aiCredentialVisibilityShowIcon"' in toggle
    assert 'id="aiCredentialVisibilityHideIcon"' in toggle
    assert "<img" not in toggle
    assert "/static/media/" not in toggle
    assert ">Show</button>" not in html
    assert ">Hide</button>" not in html
    visibility = _function(AI_SETTINGS_JS, "setCredentialVisibility", "openCredentialModal")
    assert 'reveal ? "Hide API key" : "Show API key"' in visibility
    assert "showIcon.hidden = reveal" in visibility
    assert "hideIcon.hidden = !reveal" in visibility
    assert "textContent" not in visibility
    assert 'input.type = reveal ? "text" : "password"' in visibility
    assert 'button.setAttribute("aria-label", label)' in visibility
    assert 'button.setAttribute("aria-pressed", reveal ? "true" : "false")' in visibility


def test_successful_save_clears_secret_before_refresh_and_does_not_chain_actions():
    submit = _function(AI_SETTINGS_JS, "submitCredential", "removeCredential")
    clear_input = submit.index('input.value = ""')
    clear_request = submit.index('requestBody.api_key = ""')
    clear_local = submit.index('submittedCredential = ""')
    refresh = submit.index("await refreshSettings()")
    assert clear_input < refresh
    assert clear_request < refresh
    assert clear_local < refresh
    assert "test-connection" not in submit
    assert "preferred-provider" not in submit
    assert "state.settings.preferredProvider" not in submit


def test_browser_secret_is_never_persisted_logged_or_echoed():
    combined = profile_ai_settings_page() + AI_SETTINGS_JS
    assert SYNTHETIC_SECRET not in combined
    for forbidden in (
        "localStorage",
        "sessionStorage",
        "console.log",
        "console.error",
        "console.debug",
        "window.location",
        "location.search",
        "location.hash",
    ):
        assert forbidden not in AI_SETTINGS_JS
    assert "state.api" not in AI_SETTINGS_JS
    assert "state.credentialValue" not in AI_SETTINGS_JS
    assert "dataset.api" not in AI_SETTINGS_JS


def test_remove_key_requires_confirmation_and_preserves_preference():
    html = profile_ai_settings_page()
    assert 'id="aiCredentialRemoveModal"' in html
    assert "Remove API key?" in html
    assert "This does not revoke the key in the provider’s own dashboard." in html
    remove = _function(AI_SETTINGS_JS, "removeCredential", "savePreferredProvider")
    assert 'method: "DELETE"' in remove
    assert "credentials/${encodeURIComponent(provider)}" in remove
    assert "preferred-provider" not in remove
    assert "preferredProvider = null" not in remove
    assert "is preferred but does not have an API key configured" in AI_SETTINGS_JS


def test_preferred_provider_has_explicit_set_and_clear_actions_only():
    html = profile_ai_settings_page()
    preferred = _function(AI_SETTINGS_JS, "savePreferredProvider", "testConnection")
    clear = _function(AI_SETTINGS_JS, "clearPreferredProvider", "testConnection")
    assert 'id="aiPreferredProviderClearBtn"' in html
    assert "Clear preference" in html
    assert 'requestJson("/ai/settings/preferred-provider"' in preferred
    assert 'method: "POST"' in preferred
    assert "JSON.stringify({ provider: selectedProvider })" in preferred
    assert 'method: "DELETE"' in preferred
    assert "test-connection" not in preferred
    assert "model" not in preferred.lower()
    assert 'requestJson("/ai/settings/preferred-provider", { method: "DELETE" })' in clear
    assert "credentials/" not in clear
    assert "test-connection" not in clear
    assert "await refreshSettings()" in clear


def test_models_render_exact_catalog_rows_without_unverified_claims_or_ids():
    render_models = _function(AI_SETTINGS_JS, "renderModels", "renderAll")
    assert "entry.models.forEach((model)" in render_models
    assert "model.modelId" in render_models
    assert "model.provider" in render_models
    assert "Configuration candidate" in AI_SETTINGS_JS
    assert "Needs live qualification" in AI_SETTINGS_JS
    for forbidden in (
        "llama-3",
        "llama3",
        "gpt-5.6",
        "luna",
        "terra",
        "sol",
        "production approved",
        "production-qualified",
        "recommended",
    ):
        assert forbidden not in AI_SETTINGS_JS.lower()


def test_connection_test_posts_only_provider_and_model_and_never_renders_content():
    connection = _function(AI_SETTINGS_JS, "testConnection", "bindEvents")
    assert 'requestJson("/ai/settings/test-connection"' in connection
    assert "JSON.stringify({ provider, model })" in connection
    assert "api_key" not in connection
    assert 'result.status !== "connected"' in connection
    assert "result.content" not in connection
    assert "innerHTML" not in connection
    assert 'button.textContent = state.connectionTesting ? "Testing…"' in AI_SETTINGS_JS
    assert "!configured || !model || state.connectionTesting" in AI_SETTINGS_JS
    for category in (
        "credential_not_configured",
        "unsupported_provider_model",
        "connection_test_failed",
    ):
        assert category in AI_SETTINGS_JS


def test_task_routing_is_read_only_and_does_not_invent_mappings():
    html = profile_ai_settings_page()
    assert "Task-specific model routing will appear here" in html
    assert "preferred_model" not in html + AI_SETTINGS_JS
    assert "Resume scoring" not in html + AI_SETTINGS_JS
    assert "Tailoring →" not in html + AI_SETTINGS_JS
    assert "Scan →" not in html + AI_SETTINGS_JS


def test_modal_keyboard_background_and_focus_return_behaviors_exist():
    assert 'event.key !== "Escape"' in AI_SETTINGS_JS
    assert 'event.target === byId("aiCredentialModal")' in AI_SETTINGS_JS
    assert 'event.target === byId("aiCredentialRemoveModal")' in AI_SETTINGS_JS
    assert "if (restoreFocus && trigger) trigger.focus()" in AI_SETTINGS_JS


def test_page_css_has_light_dark_responsive_and_disabled_contracts():
    assert 'html[data-theme="light"] .profile-ai-settings-page-shell' in AI_SETTINGS_CSS
    assert ".profile-ai-settings-page-shell" in AI_SETTINGS_CSS
    assert "@media (max-width: 920px)" in AI_SETTINGS_CSS
    assert "@media (max-width: 640px)" in AI_SETTINGS_CSS
    assert ":disabled" in AI_SETTINGS_CSS
    assert "cursor: not-allowed" in AI_SETTINGS_CSS
    assert "linear-gradient" not in AI_SETTINGS_CSS
    assert "backdrop-filter" not in AI_SETTINGS_CSS


def test_page_css_stays_scoped_away_from_shared_shell_and_generic_chrome():
    for forbidden in (
        ".app-shell",
        ".notification-shell",
        ".theme-toggle",
        "\nbutton {",
        "\nheader {",
        "\nsection {",
        "\nselect {",
        "\ninput {",
        "\n.page {",
    ):
        assert forbidden not in AI_SETTINGS_CSS


def test_secret_visibility_control_uses_stable_grid_overlay_geometry():
    secret_section = AI_SETTINGS_CSS.split(
        ".profile-ai-settings-secret-control {", 1
    )[1].split(".profile-ai-settings-privacy-copy", 1)[0]
    assert "display: grid" in secret_section
    assert ".profile-ai-settings-secret-control > input" in secret_section
    assert "grid-area: 1 / 1" in secret_section
    assert "padding-right: 52px" in secret_section
    secret_control_css = secret_section.split(
        ".profile-ai-settings-secret-control button,", 1
    )[1]
    for state in ("button:hover", "button:focus", "button:focus-visible", "button:active"):
        assert state in secret_control_css
    assert "position: absolute" not in secret_control_css
    assert "transform" not in secret_control_css
    assert "translate" not in secret_control_css
    assert "scale" not in secret_control_css
    for dimension in (
        "grid-area: 1 / 1 !important",
        "justify-self: end !important",
        "align-self: center !important",
        "margin-right: 11px !important",
        "width: 28px !important",
        "height: 28px !important",
        "border: 1px solid transparent !important",
        "border-radius: 6px !important",
        "background: transparent !important",
        "box-shadow: none !important",
    ):
        assert dimension in secret_control_css

    icon_rule = AI_SETTINGS_CSS.split(
        ".profile-ai-settings-secret-toggle-icon {", 1
    )[1].split("}", 1)[0]
    assert "width: 17px" in icon_rule
    assert "height: 17px" in icon_rule


def test_all_profile_dropdown_icons_share_geometry_and_owned_soft_tints():
    base_icon_rule = APP_REDESIGN_CSS.split(".profile-dropdown-nav-icon {", 1)[1].split(
        "}", 1
    )[0]
    for geometry in (
        "width: 44px !important",
        "height: 44px !important",
        "border-radius: 14px !important",
        "align-items: center !important",
        "justify-content: center !important",
    ):
        assert geometry in base_icon_rule

    for preserved in ("scans", "profile", "preferences"):
        assert f".profile-dropdown-nav-icon--{preserved}" in APP_REDESIGN_CSS
    for corrected in ("ai-settings", "diagnostics", "scheduler"):
        assert f".profile-dropdown-nav-icon--{corrected}" in APP_REDESIGN_CSS
        assert f'profile-dropdown-nav-icon--{corrected}' in UI_SHELL
        assert f'html[data-theme="light"] .profile-dropdown-nav-icon--{corrected}' in APP_REDESIGN_CSS


def test_ai_settings_sections_have_restrained_semantic_accent_ownership():
    html = profile_ai_settings_page()
    for modifier in (
        "profile-ai-settings-card--providers",
        "profile-ai-settings-card--preferred",
        "profile-ai-settings-card--test",
        "profile-ai-settings-card--models",
    ):
        assert modifier in html
    assert ".profile-ai-settings-card--preferred" in AI_SETTINGS_CSS
    assert "var(--ai-settings-violet)" in AI_SETTINGS_CSS
    assert ".profile-ai-settings-card--test" in AI_SETTINGS_CSS
    assert "var(--ai-settings-blue)" in AI_SETTINGS_CSS
    assert '.profile-ai-settings-provider-card[data-provider="groq"]' in AI_SETTINGS_CSS
    assert '.profile-ai-settings-provider-card[data-provider="openai"]' in AI_SETTINGS_CSS
    qualification = AI_SETTINGS_CSS.split(
        ".profile-ai-settings-model-badge.is-muted {", 1
    )[1].split("}", 1)[0]
    assert "var(--ai-settings-amber-soft)" in qualification
    assert "var(--ai-settings-amber)" in qualification
    routing = AI_SETTINGS_CSS.split(".profile-ai-settings-routing {", 1)[1].split(
        "}", 1
    )[0]
    assert "var(--ai-settings-violet)" in routing
    assert "box-shadow: none" in routing
