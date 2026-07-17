from __future__ import annotations

from html import escape

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.app.ui_shell import render_top_shell
from src.config.role_taxonomy import ROLE_TAXONOMY


router = APIRouter()

_ROLE_FAMILY_SUBTITLE_LABELS = {
    "data_science": "Python, R, statistics",
    "ml_ai_engineering": "PyTorch, TensorFlow, MLflow",
    "data_engineering": "Spark, Airflow, dbt",
    "analytics": "SQL, Tableau, Power BI",
    "backend_engineering": "Python, Go, Node.js",
    "frontend_engineering": "JavaScript, TypeScript, React",
    "fullstack_engineering": "TypeScript, React, Node.js",
    "software_engineering": "Git, Python, Java",
    "cloud_devops": "AWS, Terraform, Kubernetes",
    "sre": "Prometheus, Grafana, Kubernetes",
    "qa_automation": "Selenium, Playwright, Cypress",
    "security": "IAM, Okta, Splunk",
    "systems_it": "Linux, Active Directory, Intune",
    "solutions_engineering": "APIs, SQL, Salesforce",
}

ROLE_FAMILY_ICON_SVGS = {
    "data_science": """<svg class="onboarding-role-icon-svg" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 18h8" /><path d="M3 22h18" /><path d="M14 22a7 7 0 1 0 0 -14h-1" /><path d="M9 14h2" /><path d="M9 12a2 2 0 0 1 -2 -2v-4h6v4a2 2 0 0 1 -2 2z" /><path d="M10 6v-2" /><path d="M8 4h4" /></svg>""",
    "ml_ai_engineering": """<svg class="onboarding-role-icon-svg" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M15.5 13a3.5 3.5 0 0 0 -3.5 -3.5" /><path d="M12 3a4 4 0 0 0 -4 4" /><path d="M8 7a4 4 0 0 0 -4 4c0 1.3 .6 2.5 1.5 3.2" /><path d="M7 14.5a4 4 0 0 0 4 4h1" /><path d="M12 21a4 4 0 0 0 4 -4" /><path d="M16 17a4 4 0 0 0 4 -4a4 4 0 0 0 -4 -4" /><path d="M12 3v18" /></svg>""",
    "data_engineering": """<svg class="onboarding-role-icon-svg" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><ellipse cx="12" cy="6" rx="8" ry="3" /><path d="M4 6v6c0 1.7 3.6 3 8 3s8 -1.3 8 -3v-6" /><path d="M4 12v6c0 1.7 3.6 3 8 3s8 -1.3 8 -3v-6" /></svg>""",
    "analytics": """<svg class="onboarding-role-icon-svg" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12m0 1a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v6a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1z" /><path d="M10 8m0 1a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v10a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1z" /><path d="M17 4m0 1a1 1 0 0 1 1 -1h2a1 1 0 0 1 1 1v14a1 1 0 0 1 -1 1h-2a1 1 0 0 1 -1 -1z" /></svg>""",
    "backend_engineering": """<svg class="onboarding-role-icon-svg" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="8" rx="3" /><rect x="3" y="12" width="18" height="8" rx="3" /><path d="M7 8h.01" /><path d="M7 16h.01" /><path d="M11 8h6" /><path d="M11 16h6" /></svg>""",
    "frontend_engineering": """<svg class="onboarding-role-icon-svg" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="4" y="5" width="16" height="14" rx="2" /><path d="M4 9h16" /><path d="M8 7h.01" /><path d="M11 7h.01" /></svg>""",
    "fullstack_engineering": """<svg class="onboarding-role-icon-svg" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 4l8 4l-8 4l-8 -4z" /><path d="M4 12l8 4l8 -4" /><path d="M4 16l8 4l8 -4" /></svg>""",
    "software_engineering": """<svg class="onboarding-role-icon-svg" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M7 8l-4 4l4 4" /><path d="M17 8l4 4l-4 4" /><path d="M14 4l-4 16" /></svg>""",
    "cloud_devops": """<svg class="onboarding-role-icon-svg" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 18h-5a4 4 0 1 1 .4 -7.98a5 5 0 0 1 9.6 1.98" /><path d="M19 16.5a2.5 2.5 0 1 0 0 5a2.5 2.5 0 0 0 0 -5z" /><path d="M19 14.5v2" /><path d="M19 21.5v2" /><path d="M22 19h-2" /><path d="M18 19h-2" /></svg>""",
    "sre": """<svg class="onboarding-role-icon-svg" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 12h4l3 8l4 -16l3 8h4" /><path d="M19.5 5.5a2.5 2.5 0 0 1 0 3.5l-7.5 7.5l-7.5 -7.5a2.5 2.5 0 0 1 3.5 -3.5l.5 .5l.5 -.5a2.5 2.5 0 0 1 3.5 0" /></svg>""",
    "qa_automation": """<svg class="onboarding-role-icon-svg" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 5h-2a2 2 0 0 0 -2 2v12a2 2 0 0 0 2 2h10a2 2 0 0 0 2 -2v-12a2 2 0 0 0 -2 -2h-2" /><rect x="9" y="3" width="6" height="4" rx="2" /><path d="M9 14l2 2l4 -4" /></svg>""",
    "security": """<svg class="onboarding-role-icon-svg" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3l8 4v5c0 5 -3.5 8.5 -8 9c-4.5 -.5 -8 -4 -8 -9v-5z" /><rect x="9" y="11" width="6" height="5" rx="1" /><path d="M10 11v-2a2 2 0 1 1 4 0v2" /></svg>""",
    "systems_it": """<svg class="onboarding-role-icon-svg" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="12" rx="1" /><path d="M7 20h10" /><path d="M9 16v4" /><path d="M15 16v4" /><path d="M18 9.5a2.5 2.5 0 1 0 0 5a2.5 2.5 0 0 0 0 -5z" /><path d="M18 8v1.5" /><path d="M18 14.5v1.5" /></svg>""",
    "solutions_engineering": """<svg class="onboarding-role-icon-svg" aria-hidden="true" focusable="false" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 4h18v12h-18z" /><path d="M7 20h10" /><path d="M9 16v4" /><path d="M15 16v4" /><path d="M8 12v-3" /><path d="M12 12v-5" /><path d="M16 12v-2" /></svg>""",
}


def _role_family_subtitle(role_family_id: str) -> str:
    return _ROLE_FAMILY_SUBTITLE_LABELS.get(str(role_family_id or "").strip(), "Role-focused skills and tools")


def _role_family_cards_html() -> str:
    cards = []
    for role_family_id, family in ROLE_TAXONOMY.items():
        display_name = escape(str(family.get("display_name", role_family_id)))
        subtitle = _role_family_subtitle(role_family_id)
        cards.append(
            f"""
          <label class="onboarding-role-card">
            <input type="checkbox" name="selected_role_families" value="{escape(role_family_id)}" />
            <span class="onboarding-role-icon">
              {ROLE_FAMILY_ICON_SVGS.get(role_family_id, "")}
            </span>
            <span class="onboarding-role-card-copy">
              <span class="onboarding-role-card-title">{display_name}</span>
              <span class="onboarding-role-card-subtitle">{escape(subtitle)}</span>
            </span>
            <span class="preferences-role-check" aria-hidden="true">✓</span>
          </label>
"""
        )
    return "".join(cards)


def _location_preferences_html(*, prefix: str) -> str:
    safe_prefix = escape(prefix)
    title_id = f"{safe_prefix}LocationTitle"
    input_id = f"{safe_prefix}LocationSearch"
    listbox_id = f"{safe_prefix}LocationListbox"
    return f"""
      <div class="preference-location-selector" id="{safe_prefix}LocationSelector" data-location-selector>
        <div class="preference-location-search-region" data-location-search-region>
          <div class="preference-location-heading">
            <div>
              <h3 id="{title_id}">Find preferred locations</h3>
              <p>Search US cities, states, Remote (US), or United States.</p>
            </div>
            <span class="preference-location-count" data-location-count>0 selected</span>
          </div>
          <div class="preference-location-combobox" data-location-combobox>
          <input
            id="{input_id}"
            class="preference-location-search"
            type="search"
            role="combobox"
            aria-labelledby="{title_id}"
            aria-autocomplete="list"
            aria-expanded="false"
            aria-controls="{listbox_id}"
            autocomplete="off"
            placeholder="Try Virginia, Arlington, VA, or Remote"
            data-location-search
          />
          </div>
          <div class="preference-location-dropdown-region" data-location-dropdown-region>
          <div
            class="preference-location-results hidden"
            id="{listbox_id}"
            role="listbox"
            data-location-results
          ></div>
          </div>
        </div>

        <div class="preference-location-selected-region" data-location-selected-region>
          <div class="preference-location-selected-heading">
            <strong>Selected locations</strong>
            <span>Selection order preserved</span>
          </div>
          <div class="preference-location-chips" data-location-chips></div>
          <p class="preference-location-empty-selection" data-location-selection-empty>No preferred locations selected yet.</p>
        </div>

        <div class="preference-location-policy" data-location-policy-region>
          <label class="preference-policy-option">
            <input type="checkbox" name="location_strict_match" data-location-strict />
            <span class="preference-policy-switch" aria-hidden="true"></span>
            <span class="preference-policy-copy">
              <strong>Only show jobs in preferred locations</strong>
              <small>When enabled, jobs outside your selected locations are removed.</small>
            </span>
          </label>
          <label class="preference-policy-option preference-policy-option--fallback" data-location-fallback-row>
            <input type="checkbox" name="location_show_others_if_unmatched" data-location-fallback disabled />
            <span class="preference-policy-switch" aria-hidden="true"></span>
            <span class="preference-policy-copy">
              <strong>Show other jobs if none match</strong>
              <small>If no preferred-location jobs are found, keep other US jobs as fallback options.</small>
            </span>
          </label>
        </div>
        <p class="preference-location-release-note">
          Saved now. Applied to new pipeline runs after location filtering is enabled.
        </p>
        <p class="preference-location-status" data-location-status-region data-location-status aria-live="polite">
          No preferred locations selected.
        </p>
      </div>
"""


def _workflow_step_navigation_html(*, prefix: str) -> str:
    safe_prefix = escape(prefix)
    labels = ("Role interests", "Seniority", "Preferred locations", "Skills and exclusions", "Review")
    return "".join(
        f"""
          <button type="button" class="preferences-step-button{' is-active' if index == 0 else ' is-upcoming'}" data-preferences-step-target="{index}" aria-controls="{safe_prefix}PreferenceStep{index}" aria-current="{'step' if index == 0 else 'false'}">
            <span class="preferences-step-number" aria-hidden="true">{index + 1}</span>
            <span class="preferences-step-copy"><strong>{escape(label)}</strong><small data-preferences-step-summary="{index}">{'In progress' if index == 0 else 'Not started'}</small></span>
          </button>
"""
        for index, label in enumerate(labels)
    )


def _workflow_summary_html(*, prefix: str) -> str:
    safe_prefix = escape(prefix)
    return f"""
      <div class="preferences-live-summary-column">
        <div class="preferences-summary-completion" aria-label="Search profile completion">
          <strong data-preferences-summary-completion>75%</strong><span>complete</span>
        </div>
        <aside class="preferences-live-summary" aria-labelledby="{safe_prefix}PreferenceSummaryTitle">
          <div class="preferences-summary-heading">
            <span class="preferences-eyebrow">Live summary</span>
            <h2 id="{safe_prefix}PreferenceSummaryTitle">Your search profile</h2>
          </div>
          <dl class="preferences-summary-list">
            <div><dt>Role interests</dt><dd data-preferences-summary="roles">None selected</dd></div>
            <div><dt>Seniority</dt><dd data-preferences-summary="seniority">Not selected</dd></div>
            <div><dt>Locations</dt><dd data-preferences-summary="locations">No preferred locations</dd></div>
            <div><dt>Location policy</dt><dd data-preferences-summary="policy">Flexible matching</dd></div>
            <div><dt>Preferred skills</dt><dd data-preferences-summary="skills">None added</dd></div>
            <div><dt>Excluded keywords</dt><dd data-preferences-summary="excluded">None added</dd></div>
          </dl>
          <div class="preferences-summary-progress" aria-hidden="true">
            <span data-preferences-completion-bar style="width: 75%"></span>
          </div>
        </aside>
      </div>
"""


def _workflow_review_html(*, prefix: str, include_resume: bool) -> str:
    safe_prefix = escape(prefix)
    groups = (
        ("roles", "Role interests", 0),
        ("seniority", "Seniority", 1),
        ("locations", "Preferred locations", 2),
        ("policy", "Location policy", 2),
        ("skills", "Preferred skills", 3),
        ("excluded", "Excluded keywords", 3),
    )
    review_groups = "".join(
        f"""
              <article class="preferences-review-item">
                <div><span>{escape(label)}</span><strong data-preferences-review="{key}">Not configured</strong></div>
                <button type="button" class="preferences-edit-button" data-preferences-edit-step="{step}">Edit</button>
              </article>
"""
        for key, label, step in groups
    )
    resume = (
        """
            <section class="preferences-resume-requirement onboarding-resume-panel" id="onboardingResumePanel">
              <div>
                <span class="preferences-eyebrow">Onboarding requirement</span>
                <h3>Profile resume</h3>
                <p id="onboardingResumeStatus">Checking profile resumes...</p>
              </div>
              <div class="onboarding-resume-callout" id="onboardingResumeCallout">
                <strong>Upload at least one profile resume.</strong>
                <span>Resume files stay in the existing profile resume storage and are not stored locally by onboarding.</span>
              </div>
              <a class="onboarding-solid-link" href="/profile?onboarding=resume_upload">Open profile resume upload</a>
            </section>
"""
        if include_resume
        else ""
    )
    return f"""
          <div class="preferences-review-grid" id="{safe_prefix}PreferenceReview">
{review_groups}
          </div>
{resume}
"""


def _preferences_workflow_form_html(*, prefix: str, mode: str) -> str:
    safe_prefix = escape(prefix)
    is_onboarding = mode == "onboarding"
    form_id = "onboardingForm" if is_onboarding else "profilePreferencesForm"
    role_grid_id = "onboardingRoleGrid" if is_onboarding else "profilePreferencesRoleGrid"
    select_all_id = "onboardingSelectAllRolesBtn" if is_onboarding else "profilePreferencesSelectAllRolesBtn"
    clear_all_id = "onboardingClearAllRolesBtn" if is_onboarding else "profilePreferencesClearAllRolesBtn"
    skills_id = "preferredSkillsInput" if is_onboarding else "profilePreferredSkillsInput"
    excluded_id = "excludedKeywordsInput" if is_onboarding else "profileExcludedKeywordsInput"
    final_actions = (
        """
              <button type="button" class="preferences-secondary-action" id="onboardingSaveDraftBtn">Save preferences</button>
              <button type="submit" class="preferences-primary-action" id="onboardingCompleteBtn">Complete onboarding</button>
"""
        if is_onboarding
        else '<button type="submit" class="preferences-primary-action" id="profilePreferencesSaveBtn">Save preferences</button>'
    )
    final_status = (
        '<p class="preferences-final-status" id="onboardingSaveStatus">Complete setup after selecting a role family and confirming a profile resume exists.</p>'
        if is_onboarding
        else ""
    )
    save_state_id = "onboardingChangeState" if is_onboarding else "profilePreferencesChangeState"
    transient_status = (
        ""
        if is_onboarding
        else '<div class="preferences-save-confirmation hidden" id="profilePreferencesStatusBanner" role="status" aria-live="polite"></div>'
    )
    return f"""
      <form class="preferences-workflow-layout {'onboarding-layout' if is_onboarding else 'profile-preferences-form'}" id="{form_id}" data-preferences-form novalidate>
        <nav class="preferences-step-navigation" aria-label="Preference setup steps">
{_workflow_step_navigation_html(prefix=safe_prefix)}
        </nav>

        <div class="preferences-editor-shell">
          <div class="preferences-role-error hidden" id="{safe_prefix}RoleError" data-preferences-role-error tabindex="-1">Select at least one role family before saving.</div>

          <section class="preferences-step-panel is-active" id="{safe_prefix}PreferenceStep0" data-preferences-step="0" aria-labelledby="{safe_prefix}PreferenceStep0Title">
            <div class="preferences-step-heading"><span>Step 1 of 5</span><h2 id="{safe_prefix}PreferenceStep0Title" tabindex="-1">Which roles are you targeting?</h2><p>Select at least one role family to guide your job queue.</p></div>
            <div class="preferences-section-actions">
              <button type="button" class="preferences-utility-button" id="{select_all_id}">Select all</button>
              <button type="button" class="preferences-utility-button" id="{clear_all_id}">Clear all</button>
              <span class="onboarding-required-pill">Required</span>
            </div>
            <div class="onboarding-role-grid" id="{role_grid_id}">{_role_family_cards_html()}</div>
          </section>

          <section class="preferences-step-panel" id="{safe_prefix}PreferenceStep1" data-preferences-step="1" aria-labelledby="{safe_prefix}PreferenceStep1Title" hidden>
            <div class="preferences-step-heading"><span>Step 2 of 5</span><h2 id="{safe_prefix}PreferenceStep1Title" tabindex="-1">Which seniority levels fit?</h2><p>Choose every level that belongs in your current search.</p></div>
            <fieldset class="onboarding-chip-group preferences-seniority-group">
              <legend class="sr-only">Seniority levels</legend>
              <label><input type="checkbox" name="target_seniority" value="entry" /><span>Entry</span></label>
              <label><input type="checkbox" name="target_seniority" value="mid" /><span>Mid</span></label>
              <label><input type="checkbox" name="target_seniority" value="senior" /><span>Senior</span></label>
              <label><input type="checkbox" name="target_seniority" value="staff" /><span>Staff</span></label>
            </fieldset>
          </section>

          <section class="preferences-step-panel preference-location-panel" id="{safe_prefix}PreferenceStep2" data-preferences-step="2" aria-labelledby="{safe_prefix}PreferenceStep2Title" hidden>
            <div class="preferences-step-heading"><span>Step 3 of 5</span><h2 id="{safe_prefix}PreferenceStep2Title" tabindex="-1">Where do you want to work?</h2><p>Add cities, states, remote roles, or nationwide jobs.</p></div>
            {_location_preferences_html(prefix=safe_prefix)}
          </section>

          <section class="preferences-step-panel" id="{safe_prefix}PreferenceStep3" data-preferences-step="3" aria-labelledby="{safe_prefix}PreferenceStep3Title" hidden>
            <div class="preferences-step-heading"><span>Step 4 of 5</span><h2 id="{safe_prefix}PreferenceStep3Title" tabindex="-1">Refine your matching signals.</h2><p>Optional keywords preserve the existing preference payload behavior.</p></div>
            <div class="preferences-editor-grid">
              <label class="onboarding-text-field"><span>Preferred skills/tools</span><textarea id="{skills_id}" rows="5" placeholder="Python, AWS, React, Kubernetes"></textarea><small>Skills and tools that should strengthen relevance.</small></label>
              <label class="onboarding-text-field"><span>Excluded keywords</span><textarea id="{excluded_id}" rows="5" placeholder="intern, unpaid, commission only"></textarea><small>Terms that should lower a role's relevance.</small></label>
            </div>
          </section>

          <section class="preferences-step-panel" id="{safe_prefix}PreferenceStep4" data-preferences-step="4" aria-labelledby="{safe_prefix}PreferenceStep4Title" hidden>
            <div class="preferences-step-heading"><span>Step 5 of 5</span><h2 id="{safe_prefix}PreferenceStep4Title" tabindex="-1">Review your preferences.</h2><p>Check every group before saving. Edit actions preserve all unsaved values.</p></div>
            {_workflow_review_html(prefix=safe_prefix, include_resume=is_onboarding)}
            {final_status}
          </section>

          <div class="preferences-workflow-actions">
            <button type="button" class="preferences-back-button" data-preferences-back disabled>Back</button>
            <span class="preferences-mobile-completion" data-preferences-mobile-completion>Step 1 of 5</span>
            <div class="preferences-final-actions">
              {transient_status}
              <span class="preferences-save-state is-loading" id="{save_state_id}" role="status" aria-live="polite">Loading preferences</span>
              <button type="button" class="preferences-primary-action" data-preferences-next>Next</button>
              <div class="preferences-review-actions hidden" data-preferences-final-actions>{final_actions}</div>
            </div>
          </div>
        </div>

        {_workflow_summary_html(prefix=safe_prefix)}
      </form>
"""


def _preferences_header_html(*, summary_id: str, include_resume_link: bool = False) -> str:
    resume_link = (
        '<a class="ghost-btn onboarding-profile-link" href="/profile?onboarding=resume_upload">Manage resumes</a>'
        if include_resume_link
        else ""
    )
    header_actions = f'<div class="preferences-header-actions">{resume_link}</div>' if resume_link else ""
    return f"""
    <header class="page-header onboarding-header preferences-command-header">
      <div class="preferences-header-copy">
        <span class="preferences-eyebrow">Job search profile</span>
        <h1>Guided preferences</h1>
        <p class="subtext">Build a focused search profile for the roles, seniority, locations, and signals that matter to you.</p>
        <div class="preferences-configuration-summary" id="{escape(summary_id)}">Loading your configuration...</div>
      </div>
      {header_actions}
    </header>
"""


@router.get("/onboarding", response_class=HTMLResponse)
def onboarding_page() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Onboarding · ApplyLens AI</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=preferences_toolbar_ownership_r11" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=preferences_toolbar_ownership_r11" />
  <link rel="stylesheet" href="/static/preferences.css?v=preferences_footer_compact_r15" />
</head>
<body class="preferences-page-shell">
  {render_top_shell("/onboarding")}

  <main class="page onboarding-page preferences-workflow" id="onboardingPage" data-preferences-workflow data-preferences-mode="onboarding">
    <div class="preferences-canvas">
      {_preferences_header_html(summary_id="onboardingConfigurationSummary", include_resume_link=True)}

      {_preferences_workflow_form_html(prefix="onboarding", mode="onboarding")}
    </div>
  </main>

  <script src="/static/shell.js?v=role_onboarding_r6"></script>
  <script src="/static/preference_location_selector.js?v=preferences_guided_parity_r9"></script>
  <script src="/static/preferences_workflow.js?v=preferences_guided_parity_r9"></script>
  <script src="/static/onboarding.js?v=preferences_guided_parity_r9"></script>
</body>
</html>
"""
