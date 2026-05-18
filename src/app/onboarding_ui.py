from __future__ import annotations

from html import escape

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.app.ui_shell import render_top_shell
from src.config.role_taxonomy import ROLE_TAXONOMY


router = APIRouter()


def _role_family_cards_html() -> str:
    cards = []
    for role_family_id, family in ROLE_TAXONOMY.items():
        display_name = escape(str(family.get("display_name", role_family_id)))
        sample_skills = ", ".join(str(value) for value in family.get("tooling_patterns", ())[:3])
        cards.append(
            f"""
          <label class="onboarding-role-card">
            <input type="checkbox" name="selected_role_families" value="{escape(role_family_id)}" />
            <span class="onboarding-role-card-copy">
              <span class="onboarding-role-card-title">{display_name}</span>
              <span class="onboarding-role-card-subtitle">{escape(sample_skills)}</span>
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
  <link rel="stylesheet" href="/static/app_redesign.css?v=role_onboarding_r6" />
</head>
<body>
  {render_top_shell("/onboarding")}

  <main class="page onboarding-page" id="onboardingPage">
    <header class="page-header onboarding-header">
      <div>
        <div class="onboarding-kicker">First setup</div>
        <h1>Choose your job search focus.</h1>
        <p class="subtext">Pick role families and search preferences so ApplyLens AI can tune your job queue without changing the pipeline defaults for anyone else.</p>
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
  <script src="/static/onboarding.js?v=role_onboarding_r6"></script>
</body>
</html>
"""
