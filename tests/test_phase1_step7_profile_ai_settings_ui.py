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


def test_initial_load_fetches_three_read_apis_in_parallel_and_does_not_mutate():
    load_page = _function(AI_SETTINGS_JS, "loadPage", "refreshSettings")
    assert "Promise.all([" in load_page
    assert 'requestJson("/ai/settings")' in load_page
    assert 'requestJson("/ai/settings/catalog")' in load_page
    assert 'requestJson("/ai/settings/recommended-routes")' in load_page
    assert load_page.count("requestJson(") == 3
    assert AI_SETTINGS_JS.count('requestJson("/ai/settings/recommended-routes")') == 1
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
    render_models = _function(AI_SETTINGS_JS, "renderModels", "renderRouting")
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
        assert forbidden not in render_models.lower()


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


def test_task_routing_card_is_existing_editable_dom_owner():
    html = profile_ai_settings_page()
    assert "Task-specific model routing will appear here" not in html
    assert "ApplyLens Recommended (default)" in html
    assert "currently qualified provider/model choice" in html
    assert ">Read only<" not in html
    assert "profile-ai-settings-readonly-badge" not in html
    assert ">Qualified choices<" in html
    assert 'id="aiTaskRoutingSummary"' in html
    assert 'id="aiTaskRoutingList"' in html
    assert html.count("phase1_task_routing_ux_r3") == 1
    assert "profile_ai_settings.css?v=phase1_task_routing_ux_r3" in html
    assert (
        "profile_ai_settings.js?v=item2f5_manual_preview_default_r1"
        in html
    )
    assert "phase1_task_routing_r2" not in html
    assert "preferred_model" not in html + AI_SETTINGS_JS
    assert "Resume scoring" not in html + AI_SETTINGS_JS
    assert "Tailoring →" not in html + AI_SETTINGS_JS
    assert "Scan →" not in html + AI_SETTINGS_JS


def test_routing_validator_is_structural_bounded_and_backend_catalog_agnostic():
    row_validator = _function(
        AI_SETTINGS_JS,
        "validateRoutingRow",
        "validateRecommendedRoutes",
    )
    aggregate_validator = _function(
        AI_SETTINGS_JS,
        "validateRecommendedRoutes",
        "validateTaskRouteWriteResponse",
    )
    assert "payload.ok !== true" in aggregate_validator
    assert "!Array.isArray(payload.workloads)" in aggregate_validator
    assert "validateRoutingRow(row)" in aggregate_validator
    assert "seenWorkloads.has(route.workloadId)" in aggregate_validator
    assert "seenWorkloads.add(route.workloadId)" in aggregate_validator
    assert "typeof row.workload_id" in row_validator
    assert "row.workload_id.trim()" in row_validator
    for status in (
        "recommended",
        "fail_closed_zero_qualified",
        "blocked_non_live",
    ):
        assert f'"{status}"' in row_validator
    for mode in (
        "qualified_provider_model",
        "deterministic",
        "blocked_non_live",
    ):
        assert f'"{mode}"' in row_validator
    for status in ("none", "qualified", "no_longer_qualified"):
        assert f'"{status}"' in row_validator
    for source in (
        "user_override",
        "applylens_recommended",
        "deterministic",
        "blocked_non_live",
    ):
        assert f'"{source}"' in row_validator
    for field in (
        "row.execution_mode",
        "row.recommended_option",
        "row.qualified_options",
        "row.requested_selection",
        "row.requested_selection_status",
        "row.effective_selection",
        "row.effective_selection_source",
    ):
        assert field in row_validator
    assert "validateProviderModelPair" in row_validator
    assert "sameProviderModelPair" in row_validator
    assert "new Set(optionKeys).size !== optionKeys.length" in row_validator
    assert "state.catalog" not in row_validator + aggregate_validator
    assert "catalogProvider(" not in row_validator + aggregate_validator
    assert "providerSettings(" not in row_validator + aggregate_validator
    assert "selection_basis" not in row_validator + aggregate_validator


def test_routing_rendering_preserves_backend_order_and_uses_generic_fields():
    display_task = _function(AI_SETTINGS_JS, "displayTaskName", "displayTaskDescription")
    rendering = _function(AI_SETTINGS_JS, "renderRouting", "renderAll")
    assert '.split(/[_-]+/)' in display_task
    assert "state.routing.workloads.forEach((route)" in rendering
    assert "displayTaskName(route.workloadId)" in rendering
    assert "displayTaskDescription(route.workloadId)" in rendering
    assert '"profile-ai-settings-routing-description"' in rendering
    assert rendering.index("displayTaskName(route.workloadId)") < rendering.index(
        "displayTaskDescription(route.workloadId)"
    )
    assert "route.qualifiedOptions.forEach((option, index)" in rendering
    assert "displayProviderName(route.effectiveSelection.provider)" in rendering
    assert "route.effectiveSelection.model" in rendering
    for label in (
        "Task",
        "Routing status",
        "Effective route",
        "Routing preference",
        "Qualified choices",
        "Deterministic",
        "Not live",
        "ApplyLens Recommended (default)",
        "Save route",
    ):
        assert f'"{label}"' in rendering
    assert "state.routing.workloads.reduce(" in rendering
    assert "requestJson(" not in rendering
    assert "ApplyLens Recommended (default) stores no explicit override." in rendering
    assert '"ApplyLens Recommended (default)"' in rendering
    assert "openai/gpt-oss-120b" not in AI_SETTINGS_JS
    for forbidden in (
        "test-connection",
        "preferred-provider",
        "credentials/",
        'method: "POST"',
        'method: "PUT"',
        'method: "DELETE"',
    ):
        assert forbidden not in rendering


def test_qualified_route_selector_uses_only_indexed_backend_options():
    rendering = _function(AI_SETTINGS_JS, "renderRouting", "renderAll")
    assert 'const applyLensRecommendedRouteValue = "applylens-recommended"' in AI_SETTINGS_JS
    assert (
        'makeElement("option", "", "ApplyLens Recommended (default)")'
        in rendering
    )
    assert 'recommendedChoice.value = applyLensRecommendedRouteValue' in rendering
    assert 'explicitChoice.value = `qualified:${index}`' in rendering
    assert "route.qualifiedOptions.forEach((option, index)" in rendering
    assert "route.qualifiedOptions.findIndex((option)" in rendering
    assert "sameProviderModelPair(option, route.requestedSelection)" in rendering
    assert 'select.value = `qualified:${requestedIndex}`' in rendering
    assert "select.value = applyLensRecommendedRouteValue" in rendering
    assert "appendProviderOptions" not in rendering
    assert "state.catalog" not in rendering
    assert "providerSettings(" not in rendering
    assert "preferredProvider" not in rendering
    assert "sort(" not in rendering


def test_stale_and_nonselectable_routes_are_visible_but_never_editable():
    rendering = _function(AI_SETTINGS_JS, "renderRouting", "renderAll")
    assert 'route.requestedSelectionStatus === "no_longer_qualified"' in rendering
    assert (
        "is no longer qualified. ApplyLens Recommended (default) is currently effective."
        in rendering
    )
    assert "route.requestedSelection.provider" in rendering
    assert "route.requestedSelection.model" in rendering
    assert 'route.executionMode === "qualified_provider_model"' in rendering
    assert 'route.executionMode === "deterministic"' in rendering
    assert "No provider call is used" in rendering
    assert "This task is not live and cannot be configured." in rendering
    assert rendering.count('makeElement("select"') == 1
    assert rendering.count("saveButton.dataset.routeSave") == 1
    qualified_branch = rendering.split(
        'if (route.executionMode === "qualified_provider_model") {', 1
    )[1].split("} else {", 1)[0]
    assert 'makeElement("select"' in qualified_branch


def test_task_route_write_uses_safe_index_resolution_and_exact_methods():
    saving = _function(AI_SETTINGS_JS, "saveTaskRoute", "bindEvents")
    assert "if (state.routeSavingWorkload) return" in saving
    assert '/^qualified:(0|[1-9]\\d*)$/' in saving
    assert "route.qualifiedOptions[selectedIndex]" in saving
    assert "Number.isSafeInteger(selectedIndex)" in saving
    assert "encodeURIComponent(workloadId)" in saving
    assert '`/ai/settings/task-routes/${encodeURIComponent(workloadId)}`' in saving
    assert 'method: "DELETE"' in saving
    assert 'method: "PUT"' in saving
    assert "provider: selectedOption.provider" in saving
    assert "model: selectedOption.model" in saving
    assert "validateTaskRouteWriteResponse(result, workloadId)" in saving
    assert "ApplyLens Recommended (default) is now effective." in saving
    assert "state.routing.workloads.map((existingRoute, index)" in saving
    delete_branch = saving.split("const result = useRecommended", 1)[1].split(
        ": await requestJson", 1
    )[0]
    assert 'method: "DELETE"' in delete_branch
    assert 'method: "PUT"' not in delete_branch
    for forbidden in (
        "owner_user_id",
        "execution_mode",
        "recommendation_status",
        "preferred_provider",
        "credential",
        "api_key",
        "evidence_sha256",
        "registry_sha",
        "test-connection",
        "credentials/",
    ):
        assert forbidden not in saving


def test_task_route_button_has_race_safe_saving_saved_and_reset_lifecycle():
    rendering = _function(AI_SETTINGS_JS, "renderRouting", "renderAll")
    saving = _function(AI_SETTINGS_JS, "saveTaskRoute", "bindEvents")

    assert 'makeElement("button", "", "Save route")' in rendering
    assert 'saveButton.textContent = "Saving…"' in rendering
    assert 'saveButton.classList.add("is-saving")' in rendering
    assert 'saveButton.setAttribute("aria-busy", "true")' in rendering
    assert 'saveButton.textContent = "✓ Saved"' in rendering
    assert 'saveButton.classList.add("is-saved")' in rendering
    assert "saveButton.disabled = routeSaving" in rendering
    assert "if (state.routeSavingWorkload) return" in saving

    validated = saving.index("validateTaskRouteWriteResponse(result, workloadId)")
    saved = saving.index("state.routeSavedWorkload = workloadId")
    assert validated < saved
    assert "state.routeSavePresentationVersion += 1" in saving
    assert "const presentationVersion = state.routeSavePresentationVersion" in saving
    assert "window.setTimeout(() =>" in saving
    assert "state.routeSavePresentationVersion !== presentationVersion" in saving
    assert "state.routeSavedWorkload !== workloadId" in saving
    assert "state.routeSavedWorkload = null" in saving
    assert "}, 1800)" in saving

    timeout = saving.split("window.setTimeout(() => {", 1)[1].split("}, 1800)", 1)[0]
    assert "requestJson(" not in timeout
    assert "state.routing" not in timeout
    assert "qualifiedOptions" not in timeout
    assert "renderRouting()" in timeout

    failure = saving.split("} catch (error) {", 1)[1].split("} finally {", 1)[0]
    assert "state.routeSavedWorkload = null" in failure
    assert "✓ Saved" not in failure
    assert "routeSavingWorkload = null" in saving


def test_routing_readability_and_button_states_are_narrowly_scoped():
    assert AI_SETTINGS_CSS.count("--ai-settings-muted:") == 2
    assert "--ai-settings-muted: #94a3b8" in AI_SETTINGS_CSS
    assert "--ai-settings-muted: #627087" in AI_SETTINGS_CSS

    readability = AI_SETTINGS_CSS.split(
        ".profile-ai-settings-routing .profile-ai-settings-routing-field-label,", 1
    )[1].split("@keyframes ai-settings-spin", 1)[0]
    for selector in (
        ".profile-ai-settings-routing-note",
        ".profile-ai-settings-routing-value",
        ".profile-ai-settings-routing-source",
        ".profile-ai-settings-routing-help",
        ".profile-ai-settings-routing-static-note",
        ".profile-ai-settings-routing-stale-note",
        ".profile-ai-settings-routing-description",
        ".profile-ai-settings-routing-status",
    ):
        assert selector in readability
    assert "font-size: 10px" in readability
    assert "font-size: 12px" in readability
    assert "color-mix(in srgb, var(--ai-settings-text)" in readability
    assert "> button.is-saving:disabled" in readability
    assert "opacity: 1 !important" in readability
    assert "> button.is-saved" in readability
    assert "var(--ai-settings-accent-soft)" in readability
    assert "var(--ai-settings-success)" in readability
    assert readability.count(".profile-ai-settings-routing") >= 10

    saved_rule = readability.split(
        ".profile-ai-settings-routing .profile-ai-settings-routing-controls > button.is-saved {",
        1,
    )[1].split("}", 1)[0]
    assert "border-color: var(--ai-settings-success)" in saved_rule
    assert "background: var(--ai-settings-success)" in saved_rule
    assert "color: var(--ai-settings-surface)" in saved_rule
    assert "box-shadow:" in saved_rule
    assert "var(--ai-settings-success-soft)" not in saved_rule


def test_route_failures_are_bounded_and_dynamic_events_use_existing_list_owner():
    saving = _function(AI_SETTINGS_JS, "saveTaskRoute", "bindEvents")
    binding = _function(AI_SETTINGS_JS, "bindEvents", "init")
    for category in (
        "task_route_not_qualified",
        "task_route_write_failed",
        "task_route_delete_failed",
        "task_route_state_unavailable",
    ):
        assert category in AI_SETTINGS_JS
    assert (
        "The task route could not be returned to ApplyLens Recommended (default). Try again."
        in AI_SETTINGS_JS
    )
    assert "error.message" not in saving
    assert "error.stack" not in saving
    assert 'byId("aiTaskRoutingList").addEventListener("click"' in binding
    assert 'event.target.closest("[data-route-save]")' in binding
    assert 'trigger.closest(\n        ".profile-ai-settings-routing-row[data-workload-id]"' in binding
    assert 'trigger.closest("[data-workload-id]")' not in binding
    assert 'row.querySelector("[data-route-select]")' in binding
    assert "row.dataset.workloadId !== workloadId" in binding
    guard = binding.index("row.dataset.workloadId !== workloadId")
    save = binding.index("saveTaskRoute(workloadId, select.value)")
    assert guard < save
    assert "saveTaskRoute(workloadId, select.value)" in binding


def test_task_descriptions_cover_current_workloads_and_are_presentation_only():
    descriptions = _function(
        AI_SETTINGS_JS,
        "displayTaskDescription",
        "createProviderMark",
    )
    expected = {
        "skill_extraction": "Finds the important skills and requirements mentioned in a job posting.",
        "job_fit_evaluation": "Compares your profile with a job and explains how well they match.",
        "jd_intelligence": "Breaks a job description into structured requirements and useful signals.",
        "grounded_rag_answer": "Answers questions using only the relevant evidence available to ApplyLens.",
        "resume_fallback_ranking": "Ranks resume options when ApplyLens needs a fallback comparison.",
        "ambiguous_resume_adjudication": "Reviews closely matched resume choices and recommends the best-supported option.",
        "critic_evaluation": "Checks whether an AI suggestion is actually supported by the available evidence.",
        "tailoring_generation": "Creates evidence-based resume tailoring suggestions for your review.",
        "tailoring_refinement": "Improves a proposed resume edit while keeping it grounded in your evidence.",
        "tailoring_judge": "Compares tailoring options and identifies the strongest supported version.",
        "manual_scan_phrase": "Suggests phrases you can manually review and use while improving a resume.",
        "manual_provider_preview": "Generates a manual AI preview for review before anything is applied.",
    }
    for workload_id, description in expected.items():
        assert f'{workload_id}: "{description}"' in descriptions
    assert '|| "Controls how ApplyLens handles this task."' in descriptions
    for forbidden in (
        "qualifiedOptions",
        "preferredProvider",
        "providerSettings",
        "credential",
        "task-routes",
        "requestJson",
        "effectiveSelection",
    ):
        assert forbidden not in descriptions

    description_css = AI_SETTINGS_CSS.split(
        ".profile-ai-settings-routing-description {", 1
    )[1].split("}", 1)[0]
    assert "max-width: 34rem" in description_css
    assert "color: var(--ai-settings-muted)" in description_css
    assert "font-size: 9px" in description_css
    assert "line-height: 1.4" in description_css
    assert "white-space: nowrap" not in description_css


def test_task_descriptions_do_not_become_a_routing_catalog_or_internal_evidence():
    static_ui = profile_ai_settings_page() + AI_SETTINGS_JS
    descriptions = _function(
        AI_SETTINGS_JS,
        "displayTaskDescription",
        "createProviderMark",
    )
    routing_logic = _function(
        AI_SETTINGS_JS,
        "validateRoutingRow",
        "validateRecommendedRoutes",
    ) + _function(AI_SETTINGS_JS, "saveTaskRoute", "bindEvents")
    assert "displayTaskDescription" not in routing_logic
    for workload_id in (
        "skill_extraction",
        "jd_intelligence",
        "grounded_rag_answer",
        "ambiguous_resume_adjudication",
        "tailoring_refinement",
        "tailoring_judge",
        "job_fit_evaluation",
        "resume_fallback_ranking",
        "critic_evaluation",
        "tailoring_generation",
        "manual_scan_phrase",
        "manual_provider_preview",
    ):
        assert descriptions.count(f"{workload_id}:") == 1
        assert workload_id not in routing_logic
    for internal_field in (
        "task_contract_sha256",
        "qualification_binding_sha256",
        "evidence_sha256",
        "review_sha256",
    ):
        assert internal_field not in static_ui


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
