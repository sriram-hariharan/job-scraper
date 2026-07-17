import json
from pathlib import Path
import re
import subprocess

from src.app.onboarding_ui import (
    _preferences_header_html,
    _preferences_workflow_form_html,
    onboarding_page,
)
from src.app.profile_ui import profile_preferences_page
from src.app.ui_shell import render_top_shell


ROOT = Path(__file__).resolve().parents[1]
ONBOARDING_UI = (ROOT / "src/app/onboarding_ui.py").read_text(encoding="utf-8")
PROFILE_UI = (ROOT / "src/app/profile_ui.py").read_text(encoding="utf-8")
WORKFLOW_JS = (ROOT / "src/app/static/preferences_workflow.js").read_text(encoding="utf-8")
LOCATION_JS = (ROOT / "src/app/static/preference_location_selector.js").read_text(encoding="utf-8")
ONBOARDING_JS = (ROOT / "src/app/static/onboarding.js").read_text(encoding="utf-8")
PROFILE_JS = (ROOT / "src/app/static/profile.js").read_text(encoding="utf-8")
CSS = (ROOT / "src/app/static/preferences.css").read_text(encoding="utf-8")
APP_REDESIGN_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")
STYLES_CSS = (ROOT / "src/app/static/styles.css").read_text(encoding="utf-8")
ONBOARDING_FORM = _preferences_workflow_form_html(prefix="onboarding", mode="onboarding")
PROFILE_FORM = _preferences_workflow_form_html(prefix="profilePreferences", mode="profile")
PREFERENCES_HEADER = _preferences_header_html(summary_id="testPreferencesSummary")
NEUTRAL_BUTTON_CLASSES = (
    "preferences-step-button",
    "preference-location-option",
    "preferences-edit-button",
    "preference-location-chip-remove",
    "preferences-utility-button",
    "preferences-back-button",
    "preferences-secondary-action",
)


def _workflow_states(current_step: int) -> list[str]:
    script = f"""
global.window = {{}};
require({json.dumps(str(ROOT / 'src/app/static/preferences_workflow.js'))});
const state = window.ApplyLensPreferencesWorkflow.stepVisualState;
console.log(JSON.stringify(Array.from({{ length: 5 }}, (_, index) => state(index, {current_step}))));
"""
    result = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return json.loads(result.stdout)


def _rule_body(css: str, selector: str) -> str:
    match = re.search(rf"{re.escape(selector)}\s*\{{(?P<body>[^}}]*)\}}", css)
    assert match is not None, selector
    return match.group("body")


def _relevant_selector_counts(css: str) -> dict[str, int]:
    counts: dict[str, int] = {}
    for raw_selector in re.findall(r"([^{}]+)\{", css):
        selector = re.sub(r"\s+", " ", raw_selector).strip()
        if selector.startswith("@") or not any(
            marker in selector for marker in ("preferences", "app-shell-top-right--flow")
        ):
            continue
        counts[selector] = counts.get(selector, 0) + 1
    return counts


def test_guided_workflow_has_five_state_preserving_steps_and_review_navigation():
    for index in range(5):
        assert f'data-preferences-step="{index}"' in ONBOARDING_FORM
        assert f'data-preferences-step-target="{index}"' in ONBOARDING_FORM

    assert 'data-preferences-back' in ONBOARDING_FORM
    assert 'data-preferences-next' in ONBOARDING_FORM
    assert 'data-preferences-final-actions' in ONBOARDING_FORM
    assert 'data-preferences-edit-step' in ONBOARDING_FORM
    assert "panel.hidden = !isActive" in WORKFLOW_JS
    assert "showStep(currentStep - 1)" in WORKFLOW_JS
    assert "showStep(currentStep + 1)" in WORKFLOW_JS
    assert "form.addEventListener(\"input\", update)" in WORKFLOW_JS
    assert "form.addEventListener(\"change\", update)" in WORKFLOW_JS
    assert "form.reset" not in WORKFLOW_JS
    assert ONBOARDING_FORM.count("preferences-step-button is-active") == 1
    assert ONBOARDING_FORM.count("preferences-step-button is-upcoming") == 4
    assert 'const state = stepVisualState(buttonStep, nextStep)' in WORKFLOW_JS
    assert "buttonStep < maximumVisitedStep" not in WORKFLOW_JS


def test_visual_step_state_is_mutually_exclusive_for_forward_and_backward_navigation():
    assert _workflow_states(0) == ["is-active", "is-upcoming", "is-upcoming", "is-upcoming", "is-upcoming"]
    assert _workflow_states(2) == ["is-complete", "is-complete", "is-active", "is-upcoming", "is-upcoming"]
    assert _workflow_states(4) == ["is-complete", "is-complete", "is-complete", "is-complete", "is-active"]
    backward = _workflow_states(1)
    assert backward == ["is-complete", "is-active", "is-upcoming", "is-upcoming", "is-upcoming"]
    assert all(state in {"is-active", "is-complete", "is-upcoming"} for state in backward)
    assert "getMaximumVisitedStep" in WORKFLOW_JS


def test_role_seniority_and_summary_contracts_preserve_existing_values_and_icons():
    assert ONBOARDING_UI.count('class="onboarding-role-icon-svg"') == 14
    for value in ("entry", "mid", "senior", "staff"):
        assert f'name="target_seniority" value="{value}"' in ONBOARDING_UI
    for key in ("roles", "seniority", "locations", "policy", "skills", "excluded"):
        assert f'data-preferences-summary="{key}"' in ONBOARDING_FORM
        assert f'data-preferences-review="{key}"' in ONBOARDING_FORM
    assert "selectedRoleNames" in WORKFLOW_JS
    assert "preferred_location_specs" in WORKFLOW_JS
    assert 'data-preferences-completion-bar style="width: 75%"' in ONBOARDING_FORM
    assert '<strong data-preferences-summary-completion>75%</strong><span>complete</span>' in ONBOARDING_FORM
    assert "completionPercent" in WORKFLOW_JS


def test_location_dom_uses_five_separate_regions_and_fixed_search_before_chips():
    region_markers = (
        "data-location-search-region",
        "data-location-dropdown-region",
        "data-location-selected-region",
        "data-location-policy-region",
        "data-location-status-region",
    )
    for marker in region_markers:
        assert marker in ONBOARDING_FORM

    search_position = ONBOARDING_FORM.index("data-location-search-region")
    dropdown_position = ONBOARDING_FORM.index("data-location-dropdown-region")
    selected_position = ONBOARDING_FORM.index("data-location-selected-region")
    policy_position = ONBOARDING_FORM.index("data-location-policy-region")
    status_position = ONBOARDING_FORM.index("data-location-status-region")
    assert search_position < dropdown_position < selected_position < policy_position < status_position
    assert ".preferences-workflow .preference-location-search-region" in CSS
    assert "width: clamp(420px, 52%, 680px)" in CSS
    assert "Selected locations" in ONBOARDING_FORM
    assert "Selection order preserved" in ONBOARDING_FORM
    assert ".preferences-workflow .preference-location-chips {\n  display: flex" in CSS
    assert "display: contents" not in CSS


def test_location_dropdown_is_bounded_neutral_accessible_and_selection_aware():
    assert "max-height: var(--preference-location-results-max-height, 320px)" in CSS
    assert "overflow-y: auto" in CSS
    assert ".preferences-workflow .preference-location-option" in CSS
    assert "background-image: none" in CSS
    assert "min-height: 42px" in CSS
    assert "preference-location-option-check" in LOCATION_JS
    assert "data-location-selection-empty" in ONBOARDING_FORM
    assert 'event.key === "ArrowDown"' in LOCATION_JS
    assert 'event.key === "ArrowUp"' in LOCATION_JS
    assert 'event.key === "Enter"' in LOCATION_JS
    assert 'event.key === "Escape"' in LOCATION_JS
    assert 'event.key === "Backspace"' in LOCATION_JS
    assert 'credentials: "same-origin"' in LOCATION_JS
    assert 'node.dataset.locationSelected === "true"' in LOCATION_JS


def test_global_button_owners_exclude_every_neutral_preferences_control():
    for stylesheet in (STYLES_CSS, APP_REDESIGN_CSS):
        global_button_selectors = [
            selector
            for selector in re.findall(r"(?:^|\n)([^{}]*button:not\([^{}]+)\{", stylesheet)
            if selector.strip().startswith(("button:not(", "body button:not("))
        ]
        assert global_button_selectors
        for selector in global_button_selectors:
            for class_name in NEUTRAL_BUTTON_CLASSES:
                assert f":not(.{class_name})" in selector

    for stylesheet in (STYLES_CSS, APP_REDESIGN_CSS):
        gradient_rules = re.findall(r"([^{}]*button:not\([^{}]+)\{([^{}]*linear-gradient[^{}]*)\}", stylesheet)
        assert gradient_rules
        for selector, body in gradient_rules:
            if "!important" not in body:
                continue
            for class_name in NEUTRAL_BUTTON_CLASSES:
                assert f":not(.{class_name})" in selector


def test_visual_polish_neutralizes_sidebar_and_dropdown_cta_inheritance():
    assert "--preferences-workflow-columns: 190px minmax(0, 1fr) 230px" in CSS
    assert ".preferences-workflow .preferences-workflow-layout" in CSS
    assert "align-items: start" in CSS
    assert "background-image: none" in CSS
    assert "text-align: left" in CSS
    assert "min-height: 42px" in CSS
    assert ".preferences-workflow .preferences-step-button.is-active" in CSS
    assert ".preferences-workflow .preferences-step-button.is-complete" in CSS
    assert "white-space: normal" in CSS
    assert "text-overflow: clip" in CSS
    assert "overflow: visible" in CSS
    assert "preferences-step-button" in ONBOARDING_FORM
    assert "gradient" not in ONBOARDING_FORM


def test_header_is_unframed_complete_and_separated_from_the_global_toolbar():
    rendered_page = onboarding_page()
    profile_page = profile_preferences_page()
    assert "Guided preferences" in PREFERENCES_HEADER
    assert "preferences-header-completion" not in PREFERENCES_HEADER
    assert "data-preferences-completion" not in PREFERENCES_HEADER
    assert rendered_page.index('app-shell-top-right app-shell-top-right--flow') < rendered_page.index('id="onboardingPage"')
    assert profile_page.index('app-shell-top-right app-shell-top-right--flow') < profile_page.index('class="page preferences-page"')
    assert 'app-shell-top-right--flow' in render_top_shell("/onboarding")
    assert 'app-shell-top-right--flow' in render_top_shell("/profile/preferences")
    assert 'app-shell-top-right--flow' not in render_top_shell("/")
    assert "body.preferences-page-shell > .app-shell-top-right--flow" in CSS
    assert "position: static" in _rule_body(CSS, "body.preferences-page-shell > .app-shell-top-right--flow")
    assert "padding-top: 104px" not in CSS
    assert "padding-top: 112px" not in CSS
    assert "font-size: clamp(26px, 2vw, 34px)" in CSS
    assert "grid-template-columns: var(--preferences-command-header-columns)" in _rule_body(
        CSS,
        ".preferences-workflow .preferences-canvas > .preferences-command-header",
    )
    assert "grid-column: var(--preferences-header-copy-column)" in _rule_body(
        CSS,
        ".preferences-workflow .preferences-header-copy",
    )


def test_page_canvas_toolbar_and_summary_share_the_wide_preferences_width_system():
    rendered_page = onboarding_page()
    profile_page = profile_preferences_page()
    for page in (rendered_page, profile_page):
        assert '<body class="preferences-page-shell">' in page
        assert page.count('class="preferences-canvas"') == 1

    shell = _rule_body(CSS, "body.preferences-page-shell")
    root_variables = _rule_body(CSS, ":root")
    canvas = _rule_body(CSS, ".preferences-canvas")
    toolbar = _rule_body(CSS, "body.preferences-page-shell > .app-shell-top-right--flow")
    page_shell = _rule_body(
        CSS,
        "body.preferences-page-shell .app-shell ~ .page.preferences-workflow,\nbody.preferences-page-shell .app-shell ~ .page.preferences-page",
    )
    header = _rule_body(CSS, ".preferences-workflow .preferences-canvas > .preferences-command-header")
    workflow = _rule_body(CSS, ".preferences-workflow .preferences-workflow-layout")
    actions = _rule_body(CSS, ".preferences-workflow .preferences-workflow-actions")
    tablet_rules = CSS.split("@media (max-width: 980px)", 1)[1].split("@media (max-width: 720px)", 1)[0]
    mobile_rules = CSS.split("@media (max-width: 560px)", 1)[1].split("@media (prefers-reduced-motion: reduce)", 1)[0]

    assert "--preferences-canvas-max: 1600px" in shell
    assert "--preferences-page-gutter: clamp(20px, 2vw, 32px)" in shell
    assert "--preferences-chat-safe-area: 112px" in shell
    assert "width: min(100%, var(--preferences-canvas-max))" in canvas
    assert "max-width: var(--preferences-canvas-max)" in canvas
    assert "box-sizing: border-box" in canvas
    assert "var(--preferences-canvas-pad-block-start)" in canvas
    assert "var(--preferences-canvas-pad-inline)" in canvas
    assert "var(--preferences-canvas-pad-block-end)" in canvas
    assert "--preferences-canvas-pad-block-start: clamp(28px, 2.2vw, 36px)" in root_variables
    assert "--preferences-canvas-pad-inline: clamp(36px, 3vw, 48px)" in root_variables
    assert "--preferences-canvas-pad-block-end: clamp(36px, 3vw, 44px)" in root_variables
    assert "--preferences-canvas-pad-block-start: 24px" in tablet_rules
    assert "--preferences-canvas-pad-inline: 24px" in tablet_rules
    assert "--preferences-canvas-pad-block-end: 28px" in tablet_rules
    assert "--preferences-canvas-pad-block-start: 18px" in mobile_rules
    assert "--preferences-canvas-pad-inline: 16px" in mobile_rules
    assert "--preferences-canvas-pad-block-end: 22px" in mobile_rules
    assert len(re.findall(r"(?m)^\.preferences-canvas\s*\{", CSS)) == 1
    assert "var(--preferences-page-gutter)" in page_shell
    assert "var(--preferences-chat-safe-area)" in page_shell
    assert "preferences-canvas-pad" not in page_shell
    assert "padding-bottom" not in actions
    assert "var(--preferences-toolbar-width)" in toolbar
    assert "display: flex" in toolbar
    assert "align-items: center" in toolbar
    assert "justify-content: flex-end" in toolbar
    assert "gap: 12px" in toolbar
    assert "background: transparent" in toolbar
    assert "background-image: none" in toolbar
    assert "border: 0" in toolbar
    assert "border-radius: 0" in toolbar
    assert "box-shadow: none" in toolbar
    assert "outline: 0" in toolbar
    assert "backdrop-filter: none" in toolbar
    assert "padding: 0" in toolbar
    assert "background: transparent" in header
    assert "border-radius: 0" in header
    assert "grid-template-columns: var(--preferences-workflow-columns)" in workflow
    assert "max-width: none" in workflow
    assert 'class="preferences-live-summary-column"' in ONBOARDING_FORM
    assert 'class="preferences-summary-completion"' in ONBOARDING_FORM
    assert 'class="preferences-summary-progress"' in ONBOARDING_FORM
    shell_markup = render_top_shell("/onboarding")
    for control_class in ("notification-btn", "theme-toggle-btn", "app-shell-primary-link", "profile-avatar-btn"):
        assert control_class in shell_markup
    assert "linear-gradient(135deg, var(--app-primary), var(--app-violet)) !important" in APP_REDESIGN_CSS
    assert ".app-shell-top-right--flow::before" not in CSS + STYLES_CSS + APP_REDESIGN_CSS
    assert ".app-shell-top-right--flow::after" not in CSS + STYLES_CSS + APP_REDESIGN_CSS


def test_preferences_css_has_one_owner_without_important_or_global_toolbar_surface_inheritance():
    toolbar_selector = "body.preferences-page-shell > .app-shell-top-right--flow"
    assert len(re.findall(rf"{re.escape(toolbar_selector)}\s*\{{", CSS)) == 1
    assert "!important" not in CSS

    duplicate_preferences_selectors = {
        selector: count
        for selector, count in _relevant_selector_counts(CSS).items()
        if count > 1
    }
    assert duplicate_preferences_selectors == {}

    unqualified_toolbar = re.compile(
        r'(?m)^\s*(?:html\[data-theme="light"\]\s+)?\.app-shell-top-right\s*\{'
    )
    for stylesheet in (STYLES_CSS, APP_REDESIGN_CSS):
        assert unqualified_toolbar.search(stylesheet) is None
        assert ".app-shell-top-right:not(.app-shell-top-right--flow)" in stylesheet


def test_location_dropdown_placement_is_viewport_bounded_and_cleans_up_listeners():
    assert "getBoundingClientRect()" in LOCATION_JS
    assert "spaceBelow < 180 && spaceAbove > spaceBelow" in LOCATION_JS
    assert 'results.classList.toggle("opens-upward", opensUpward)' in LOCATION_JS
    assert 'global.addEventListener("resize", updateResultsPlacement)' in LOCATION_JS
    assert 'global.addEventListener("scroll", updateResultsPlacement, true)' in LOCATION_JS
    assert 'global.removeEventListener("resize", updateResultsPlacement)' in LOCATION_JS
    assert 'global.removeEventListener("scroll", updateResultsPlacement, true)' in LOCATION_JS
    assert ".preferences-workflow .preference-location-results.opens-upward" in CSS


def test_location_policy_uses_compact_accessible_switch_and_visible_focus():
    checkbox_selector = ".preferences-workflow .preference-policy-option input"
    assert checkbox_selector in CSS
    assert "inline-size: 1px" in CSS
    assert "block-size: 1px" in CSS
    assert "padding: 0" in CSS
    assert "box-shadow: none" in CSS
    assert 'class="preference-policy-switch"' in ONBOARDING_FORM
    assert ".preference-policy-option:focus-within .preference-policy-switch" in CSS
    assert "width: 32px" in CSS
    assert "height: 18px" in CSS
    assert "fallback.disabled = !strictEnabled" in LOCATION_JS
    assert "if (!strictEnabled) fallback.checked = false" in LOCATION_JS


def test_location_policy_remains_compact_truthful_and_preserves_serialization():
    assert "Only show jobs in preferred locations" in ONBOARDING_UI
    assert "Show other jobs if none match" in ONBOARDING_UI
    assert "Saved now. Applied to new pipeline runs after location filtering is enabled." in ONBOARDING_UI
    assert "fallback.disabled = !strictEnabled" in LOCATION_JS
    assert "if (!strictEnabled) fallback.checked = false" in LOCATION_JS
    assert "location_strict_match: Boolean(strict.checked)" in LOCATION_JS
    assert "location_show_others_if_unmatched: Boolean(strict.checked && fallback.checked)" in LOCATION_JS
    assert "min-height: 54px" in CSS


def test_existing_save_paths_own_persistence_and_prevent_duplicate_submission():
    assert 'onboardingFetchJson("/onboarding/preferences"' in ONBOARDING_JS
    assert 'postJson("/onboarding/preferences", preferences)' in PROFILE_JS
    assert "if (onboardingPreferencesSaving) return" in ONBOARDING_JS
    assert "if (profilePreferencesSaving) return" in PROFILE_JS
    assert "showValidationError" in ONBOARDING_JS
    assert "showValidationError" in PROFILE_JS
    assert 'window.location.href = "/"' in ONBOARDING_JS
    assert 'window.location.href = "/"' not in PROFILE_JS
    assert "fetch(" not in WORKFLOW_JS


def test_preferences_assets_are_scoped_ordered_and_cache_busted_consistently():
    for source in (ONBOARDING_UI, PROFILE_UI):
        styles = source.index('/static/styles.css?v=preferences_toolbar_ownership_r11')
        redesign = source.index('/static/app_redesign.css?v=preferences_toolbar_ownership_r11')
        preferences = source.index('/static/preferences.css?v=preferences_footer_compact_r15')
        selector = source.index('/static/preference_location_selector.js?v=preferences_guided_parity_r9')
        workflow = source.index('/static/preferences_workflow.js?v=preferences_guided_parity_r9')
        assert styles < redesign
        assert redesign < preferences < selector < workflow
        for asset in ("styles.css", "app_redesign.css"):
            assert source.count(f'/static/{asset}?v=preferences_toolbar_ownership_r11') == 1
        assert source.count('/static/preferences.css?v=preferences_footer_compact_r15') == 1
        for asset in ("preference_location_selector.js", "preferences_workflow.js"):
            assert source.count(f'/static/{asset}?v=preferences_guided_parity_r9') == 1
        assert "preferences_toolbar_capsule_r10" not in source
        assert "preferences_spacing_local_r2" not in source
        assert '/static/preferences.css?v=preferences_guided_parity_r9' not in source

    assert '/static/onboarding.js?v=preferences_guided_parity_r9' in ONBOARDING_UI
    assert '/static/profile.js?v=preferences_guided_parity_r9' in PROFILE_UI
    assert "preferences_guided_parity_r8" not in ONBOARDING_UI + PROFILE_UI
    assert "preferences_guided_parity_r7" not in ONBOARDING_UI + PROFILE_UI
    assert "preferences_guided_parity_r6" not in ONBOARDING_UI + PROFILE_UI
    assert "preferences_guided_parity_r3" not in ONBOARDING_UI + PROFILE_UI
    assert "preferences_guided_r1" not in ONBOARDING_UI
    assert "preferences_guided_r1" not in PROFILE_UI

    assert CSS.count(".preferences-workflow") > 40
    assert "html[data-theme=\"light\"] .preferences-workflow" in CSS
    assert "@media (max-width: 980px)" in CSS
    assert "@media (max-width: 720px)" in CSS
    assert "@media (prefers-reduced-motion: reduce)" in CSS
    assert "--preferences-actions-margin-inline: clamp(20px, 2vw, 28px)" in CSS
    assert "margin: 24px var(--preferences-actions-margin-inline) 0" in CSS


def test_exact_prototype_structure_has_one_status_owner_and_canonical_style_owner():
    combined_forms = ONBOARDING_FORM + PROFILE_FORM
    assert ONBOARDING_FORM.count('id="onboardingChangeState"') == 1
    assert PROFILE_FORM.count('id="profilePreferencesChangeState"') == 1
    assert "data-preferences-local-state" not in combined_forms
    assert "data-preferences-local-state" not in WORKFLOW_JS
    assert "preferences-save-confirmation" in PROFILE_FORM
    assert "profile-inline-status" not in PROFILE_FORM
    assert "preferences-header-completion" not in ONBOARDING_UI + PROFILE_UI + WORKFLOW_JS + CSS
    assert "data-preferences-completion>" not in ONBOARDING_UI + PROFILE_UI
    assert "[data-preferences-completion]" not in WORKFLOW_JS
    for obsolete in (
        "completion(model)",
    ):
        assert obsolete not in ONBOARDING_UI + PROFILE_UI + WORKFLOW_JS + CSS
    assert ONBOARDING_FORM.count('class="preferences-summary-completion"') == 1
    assert PROFILE_FORM.count('class="preferences-summary-completion"') == 1
    assert "data-preferences-summary-completion" in WORKFLOW_JS
    assert "data-preferences-completion-bar" in WORKFLOW_JS
    assert ".preferences-workflow .preferences-summary-progress" in CSS
    assert "preferences_guided_polish_r2" not in ONBOARDING_UI + PROFILE_UI
    for obsolete_selector in (
        ".preferences-command-header",
        ".preference-location-selector",
        ".onboarding-role-card",
        ".profile-preferences-section",
    ):
        assert re.search(
            rf"(?m)^\s*{re.escape(obsolete_selector)}(?:\s|,|\{{)",
            APP_REDESIGN_CSS,
        ) is None


def test_prototype_geometry_keeps_controls_compact_and_reserved():
    assert "min-height: 590px" in CSS
    assert "grid-template-columns: 38px minmax(0, 1fr)" in CSS
    assert "padding: 10px 34px 10px 10px" in CSS
    assert "top: 7px" in CSS and "right: 7px" in CSS
    assert "width: 16px" in _rule_body(CSS, ".preferences-workflow .preferences-role-check")
    assert "flex: 1 1 130px" in CSS
    assert "min-height: 48px" in CSS
    footer = _rule_body(CSS, ".preferences-workflow .preferences-workflow-actions")
    assert "position: sticky" not in footer
    assert "body .app-shell ~ main.preferences-workflow" not in CSS


def test_footer_actions_keep_status_and_primary_controls_on_stable_columns():
    footer = _rule_body(CSS, ".preferences-workflow .preferences-workflow-actions")
    actions = _rule_body(CSS, ".preferences-workflow .preferences-final-actions")
    primary = _rule_body(CSS, ".preferences-workflow .preferences-primary-action")
    save_state = _rule_body(CSS, ".preferences-workflow .preferences-save-state")
    back = _rule_body(CSS, ".preferences-workflow .preferences-workflow-actions .preferences-back-button")

    assert "display: grid" in footer
    assert "grid-template-columns: var(--preferences-footer-columns)" in footer
    assert "align-items: center" in footer
    assert "column-gap: var(--preferences-footer-action-gap)" in footer
    assert "display: grid" in actions
    assert "grid-template-columns: var(--preferences-right-action-columns)" in actions
    assert "gap: var(--preferences-footer-action-gap)" in actions
    assert "--preferences-save-status-width: 184px" in CSS
    assert "--preferences-primary-action-width: 168px" in CSS
    assert "--preferences-footer-action-gap: 12px" in CSS
    assert "--preferences-footer-control-height: 44px" in CSS
    assert "padding: 16px 0 20px var(--preferences-actions-padding-left)" in footer
    assert "width: var(--preferences-primary-action-width)" in primary
    assert "height: var(--preferences-footer-control-height)" in primary
    assert "width: var(--preferences-save-status-width)" in save_state
    assert "height: var(--preferences-footer-control-height)" in save_state
    assert "min-height: var(--preferences-footer-control-height)" in back
    assert ONBOARDING_FORM.count('class="preferences-primary-action"') == 2
    assert PROFILE_FORM.count('class="preferences-primary-action"') == 2
    assert 'class="preferences-primary-action" data-preferences-next>Next</button>' in PROFILE_FORM
    assert 'class="preferences-primary-action" id="profilePreferencesSaveBtn">Save preferences</button>' in PROFILE_FORM
    assert CSS.count(".preferences-workflow .preferences-final-actions {") == 1
    assert CSS.count(".preferences-workflow .preferences-primary-action {") == 1
    assert "padding-bottom: 28px" not in CSS
    assert "is-review" not in CSS
    assert 'finalActions?.classList.toggle("hidden", nextStep !== STEP_COUNT - 1)' in WORKFLOW_JS
    assert 'showStep(currentStep - 1)' in WORKFLOW_JS
    assert 'showStep(currentStep + 1)' in WORKFLOW_JS


def test_rail_states_match_prototype_surface_ownership():
    base_css = CSS.split("@media (max-width: 980px)", 1)[0]
    active = _rule_body(CSS, ".preferences-workflow .preferences-step-button.is-active")
    complete = _rule_body(CSS, ".preferences-workflow .preferences-step-button.is-complete")
    upcoming = _rule_body(CSS, ".preferences-workflow .preferences-step-button.is-upcoming")
    marker = _rule_body(CSS, ".preferences-workflow .preferences-step-number")
    check = _rule_body(CSS, ".preferences-workflow .preferences-step-button.is-complete .preferences-step-number::after")
    assert "background: var(--preferences-bg)" in active
    assert "box-shadow: 0 8px 20px" in active
    assert "background: transparent" in complete
    assert "box-shadow: none" in complete
    assert "background: transparent" in upcoming
    assert "box-shadow: none" in upcoming
    assert "position: relative" in marker
    assert "top: 50%" in check and "left: 50%" in check
    assert "translate(-50%, -58%) rotate(45deg)" in check
    assert base_css.count(".preferences-workflow .preferences-step-button {") == 1
    assert base_css.count(".preferences-workflow .preference-location-option {") == 1


def test_guided_ui_does_not_activate_runtime_filters_or_unsafe_actions():
    combined = "\n".join((ONBOARDING_UI, PROFILE_UI, WORKFLOW_JS, LOCATION_JS, ONBOARDING_JS, PROFILE_JS, CSS))
    for forbidden in (
        "auto_apply",
        "submit_ats",
        "message_recruiter",
        "mark_applied",
        "/pipeline/run",
    ):
        assert forbidden not in "\n".join((ONBOARDING_UI, WORKFLOW_JS, LOCATION_JS, CSS))
    assert "location_matcher" not in combined
    assert "location_show_others_if_unmatched" in combined
