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
          </label>
"""
        )
    return "".join(cards)


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
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=role_onboarding_r10_spacing" />
</head>
<body>
  {render_top_shell("/onboarding")}

  <main class="page onboarding-page" id="onboardingPage">
    <header class="page-header onboarding-header">
      <div>
        <div class="onboarding-kicker">First setup</div>
        <h1>Choose your job search focus.</h1>
        <p class="subtext">ApplyLens will use these preferences to tune your job queue and resume matching.</p>
      </div>
      <a class="ghost-btn onboarding-profile-link" href="/profile?onboarding=resume_upload">Manage resumes</a>
    </header>

    <form class="onboarding-layout" id="onboardingForm">
      <section class="card onboarding-panel">
        <div class="section-header">
          <div>
            <h2>Role interests</h2>
            <div class="subtext">Select at least one IT role family.</div>
          </div>
          <span class="onboarding-required-pill">Required</span>
        </div>
        <div class="onboarding-role-grid" id="onboardingRoleGrid">
          {_role_family_cards_html()}
        </div>
      </section>

      <section class="card onboarding-panel">
        <div class="section-header">
          <div>
            <h2>Seniority and work style</h2>
            <div class="subtext">These preferences are saved as selections only.</div>
          </div>
        </div>
        <div class="onboarding-field-grid">
          <fieldset class="onboarding-chip-group">
            <legend>Seniority</legend>
            <label><input type="checkbox" name="target_seniority" value="entry" /> Entry</label>
            <label><input type="checkbox" name="target_seniority" value="mid" /> Mid</label>
            <label><input type="checkbox" name="target_seniority" value="senior" /> Senior</label>
            <label><input type="checkbox" name="target_seniority" value="staff" /> Staff</label>
          </fieldset>

          <fieldset class="onboarding-chip-group">
            <legend>Work mode</legend>
            <label><input type="checkbox" name="work_modes" value="remote" /> Remote</label>
            <label><input type="checkbox" name="work_modes" value="hybrid" /> Hybrid</label>
            <label><input type="checkbox" name="work_modes" value="onsite" /> On-site</label>
          </fieldset>
        </div>

        <label class="onboarding-text-field">
          <span>Preferred locations</span>
          <textarea id="preferredLocationsInput" rows="3" placeholder="New York, Remote, Boston"></textarea>
        </label>
      </section>

      <section class="card onboarding-panel onboarding-resume-panel" id="onboardingResumePanel">
        <div class="section-header">
          <div>
            <h2>Resume requirement</h2>
            <div class="subtext" id="onboardingResumeStatus">Checking profile resumes...</div>
          </div>
          <span class="onboarding-required-pill">Required</span>
        </div>
        <div class="onboarding-resume-callout" id="onboardingResumeCallout">
          <strong>Upload at least one profile resume.</strong>
          <span>Resume files stay in the existing profile resume storage and are not stored locally by onboarding.</span>
        </div>
        <a class="onboarding-solid-link" href="/profile?onboarding=resume_upload">Open profile resume upload</a>
      </section>

      <section class="card onboarding-panel">
        <div class="section-header">
          <div>
            <h2>Skills and exclusions</h2>
            <div class="subtext">Optional keywords to guide future role expansion steps.</div>
          </div>
        </div>
        <div class="onboarding-field-grid">
          <label class="onboarding-text-field">
            <span>Preferred skills/tools</span>
            <textarea id="preferredSkillsInput" rows="4" placeholder="Python, AWS, React, Kubernetes"></textarea>
          </label>
          <label class="onboarding-text-field">
            <span>Excluded keywords</span>
            <textarea id="excludedKeywordsInput" rows="4" placeholder="intern, unpaid, commission only"></textarea>
          </label>
        </div>
      </section>

      <section class="card onboarding-panel onboarding-confirm-panel">
        <div>
          <h2>Confirm setup</h2>
          <p class="subtext" id="onboardingSaveStatus">Complete setup after selecting a role family and confirming a profile resume exists.</p>
        </div>
        <div class="onboarding-actions">
          <button type="button" class="ghost-btn" id="onboardingSaveDraftBtn">Save preferences</button>
          <button type="submit" id="onboardingCompleteBtn">Complete onboarding</button>
        </div>
      </section>
    </form>
  </main>

  <script src="/static/shell.js?v=role_onboarding_r6"></script>
  <script src="/static/onboarding.js?v=role_onboarding_r10"></script>
</body>
</html>
"""
