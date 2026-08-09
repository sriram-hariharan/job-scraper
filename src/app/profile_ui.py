from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from html import escape

from src.app.onboarding_ui import _preferences_header_html, _preferences_workflow_form_html
from src.app.ui_shell import render_top_shell
from src.auth.runtime import current_user_from_request

router = APIRouter()

# UI contract marker: profile_preferences_menu_r1 role_profile_preferences_menu_r1


def _preferences_section_html(*, hidden: bool = False, tab_panel: bool = False) -> str:
    hidden_class = " hidden" if hidden else ""
    tab_attr = " data-profile-tab-panel" if tab_panel else ""
    return f"""
    <section class="profile-section-card profile-preferences-section preferences-workflow{hidden_class}" id="profilePreferencesSection" data-preferences-workflow data-preferences-mode="profile"{tab_attr}>
      <div class="preferences-canvas">
        {_preferences_header_html(summary_id="profilePreferencesConfigurationSummary")}
        {_preferences_workflow_form_html(prefix="profilePreferences", mode="profile")}
      </div>
    </section>
"""


def _profile_navigation_icon_preloads_html() -> str:
    return """
    <div class="profile-navigation-icon-preloads hidden" aria-hidden="true">
      <img src="/static/media/profile_icon.svg" alt="" />
      <img src="/static/media/scan_icon.svg" alt="" />
    </div>
""".strip()


@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request) -> str:
    user = dict(getattr(request.state, "auth_user", {}) or {}) or current_user_from_request(request)
    access_level = str(user.get("access_level", "") or "").strip().lower()
    is_admin = bool(user.get("is_admin", False)) or access_level == "admin"
    admin_tab_html = (
        """
      <button type="button" class="profile-tab-btn" data-profile-tab-target="profileAdminUsersSection">
        <span class="profile-tab-icon-stack" aria-hidden="true">
          <img class="profile-tab-icon profile-tab-icon--dark" src="/static/media/admin_icon_dark.svg" alt="" />
          <img class="profile-tab-icon profile-tab-icon--light" src="/static/media/admin_icon_light.svg" alt="" />
        </span>
        <span>User access</span>
      </button>"""
        if is_admin
        else ""
    )
    profile_tabs_html = f"""
    <nav class="profile-tabs" id="profileTabs" aria-label="Profile sections">
      <button type="button" class="profile-tab-btn is-active" data-profile-tab-target="resumeSection">
        <span class="profile-tab-icon-stack" aria-hidden="true">
          <img class="profile-tab-icon profile-tab-icon--dark" src="/static/media/resume_icon_dark.svg" alt="" />
          <img class="profile-tab-icon profile-tab-icon--light" src="/static/media/resume_icon_light.svg" alt="" />
        </span>
        <span>Resumes</span>
      </button>
      <button type="button" class="profile-tab-btn" data-profile-tab-target="profilePipelineRunsSection">
        <span class="profile-tab-icon profile-tab-icon--pipeline" aria-hidden="true"></span>
        <span>Pipeline runs</span>
      </button>{admin_tab_html}
    </nav>
"""
    admin_users_section_html = (
        """
    <section class="card profile-section-card profile-admin-users-section hidden" id="profileAdminUsersSection" data-profile-tab-panel>
      <div class="section-header">
        <div>
          <h2>User access</h2>
          <div class="subtext" id="adminUsersMeta">Loading users...</div>
        </div>
        <button type="button" class="ghost-btn btn-sm" id="refreshAdminUsersBtn">
          Refresh
        </button>
      </div>

      <div class="profile-inline-status hidden" id="adminUsersStatusBanner"></div>

      <div class="admin-users-table-wrap">
        <table class="admin-users-table">
          <thead>
            <tr>
              <th>Name</th>
              <th>Email</th>
              <th>Access level</th>
              <th>Status</th>
              <th>Created</th>
              <th>Last login</th>
              <th>Access</th>
              <th>Delete user</th>
            </tr>
          </thead>
          <tbody id="adminUsersTableBody">
            <tr>
              <td colspan="8">Loading users...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
"""
        if is_admin
        else ""
    )
    pipeline_runs_section_html = """
    <section class="card profile-section-card profile-pipeline-runs-section hidden" id="profilePipelineRunsSection" data-profile-tab-panel>
      <div class="section-header">
        <div>
          <h2>Pipeline runs</h2>
          <div class="subtext" id="pipelineRunsMeta">Loading pipeline runs...</div>
        </div>
        <div class="profile-section-header-right">
          <div class="application-pagination-inline pipeline-runs-pagination-inline" id="pipelineRunsPaginationInline">
            <div class="application-pagination-meta" id="pipelineRunsPaginationMeta">Loading...</div>
            <div class="application-pagination-actions" id="pipelineRunsPaginationActions"></div>
          </div>
          <button type="button" class="ghost-btn btn-sm pipeline-runs-refresh-btn" id="refreshPipelineRunsBtn">
            Refresh
          </button>
        </div>
      </div>

      <div class="profile-inline-status hidden" id="pipelineRunsStatusBanner"></div>

      <div class="pipeline-runs-table-wrap">
        <table class="pipeline-runs-table">
          <thead>
            <tr>
              <th>Started</th>
              <th>Status</th>
              <th>Summary</th>
              <th>Final jobs</th>
              <th>Counts</th>
              <th>Settings</th>
              <th>Actions</th>
              <th>Re-run</th>
            </tr>
          </thead>
          <tbody id="pipelineRunsTableBody">
            <tr>
              <td colspan="8">Loading pipeline runs...</td>
            </tr>
          </tbody>
        </table>
      </div>

    </section>
"""
    admin_modals_html = (
        """
  <section class="modal-backdrop hidden" id="adminUserAccessModal">
    <div class="modal-card admin-user-confirm-card">
      <div class="modal-header">
        <div>
          <h3 id="adminUserAccessTitle">Change access</h3>
          <div class="subtext" id="adminUserAccessSubtitle">Confirm this user access change.</div>
        </div>
        <button class="ghost-btn modal-close-btn admin-user-modal-close-btn" id="adminUserAccessCloseBtn" type="button">Close</button>
      </div>

      <div class="modal-body">
        <div class="admin-user-confirm-copy" id="adminUserAccessMessage"></div>
      </div>

      <div class="modal-actions">
        <button type="button" id="adminUserAccessConfirmBtn">Confirm</button>
      </div>
    </div>
  </section>

  <section class="modal-backdrop hidden" id="adminUserDeleteModal">
    <div class="modal-card admin-user-confirm-card admin-user-danger-card">
      <div class="modal-header">
        <div>
          <h3>Delete user</h3>
          <div class="subtext">This permanently removes the user account.</div>
        </div>
        <button class="ghost-btn modal-close-btn admin-user-modal-close-btn" id="adminUserDeleteCloseBtn" type="button">Close</button>
      </div>

      <div class="modal-body">
        <div class="admin-user-high-warning">
          High warning: this action permanently deletes the user from the backend users table and removes their active sessions. This cannot be undone.
        </div>
        <div class="admin-user-confirm-copy" id="adminUserDeleteMessage"></div>
      </div>

      <div class="modal-actions">
        <button type="button" class="admin-user-delete-confirm-btn" id="adminUserDeleteConfirmBtn">Yes, delete user</button>
      </div>
    </div>
  </section>
"""
        if is_admin
        else ""
    )
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>My Profile</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=profile_pipeline_run_buttons_r1" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=item2_phase4_secondary_headers_r1" />
</head>
<body>
  {render_top_shell("/profile")}
  {_profile_navigation_icon_preloads_html()}

  <div class="page">
    <header class="page-header app-page-header">
      <div class="app-page-header__main">
        <div class="app-page-header__title-row">
          <h1 class="app-page-header__title">My Profile</h1>
        </div>
        <p class="subtext app-page-header__description">Manage resume files and persisted Live Pipeline runs.</p>
      </div>
    </header>

    {profile_tabs_html}

    <section class="card profile-section-card" id="resumeSection" data-profile-tab-panel>
      <div class="section-header">
        <div>
          <h2>Resumes</h2>
          <div class="subtext" id="resumeListMeta">Loading resumes...</div>
        </div>
      </div>

      <div class="profile-inline-status hidden" id="resumeStatusBanner"></div>

      <div class="resume-manager-grid">
        <section class="resume-upload-panel">
          <div
            class="resume-dropzone"
            id="resumeDropzone"
            tabindex="0"
            role="button"
            aria-label="Upload resume PDF by dragging and dropping or browsing"
          >
            <input
              type="file"
              id="resumeUploadInput"
              accept=".pdf,application/pdf"
              multiple
              class="resume-upload-input"
            />

            <div class="resume-dropzone-icon">↑</div>
            <div class="resume-dropzone-title">Upload resume PDF</div>
            <div class="resume-dropzone-text">
              Drag and drop one or more PDF resumes here, or browse from your computer.
            </div>

            <div class="resume-upload-actions">
              <button type="button" id="resumeBrowseBtn">Choose PDF</button>
            </div>

            <div class="control-help field-help-wide">
              Uploaded files are stored securely in your profile and become available to matching and scan workflows.
            </div>
          </div>

          <div class="profile-planning-upload-callout hidden" id="profilePlanningUploadCallout">
            <button type="button" class="profile-planning-options-btn" id="openProfilePlanningOptionsBtn">
              Planning &amp; Tailoring Options
            </button>
            <div class="control-help field-help-wide">
              You may want to run this after uploading new resumes so planning, fallback ranking, and tailoring can use the latest files.
            </div>
          </div>
        </section>

        <section class="resume-list-panel">
          <div class="resume-list" id="resumeList"></div>
        </section>
      </div>
    </section>

    {admin_users_section_html}
    {pipeline_runs_section_html}
  </div>

  <section class="modal-backdrop hidden" id="resumeDeleteModal">
  <div class="modal-card resume-delete-modal-card">
    <div class="modal-header">
      <div>
        <h3>Delete resume</h3>
        <div class="subtext">This removes the file from the profile resume directory.</div>
      </div>
      <button
        class="ghost-btn modal-close-btn resume-delete-modal-close-btn"
        id="closeResumeDeleteModalBtn"
        type="button"
      >
        Close
      </button>
    </div>

    <div class="modal-body">
      <div class="info-pair">
        <span class="label">Resume</span>
        <span id="resumeDeleteModalName">-</span>
      </div>
    </div>

    <div class="modal-actions resume-delete-modal-actions">
      <button
        type="button"
        class="resume-delete-confirm-btn"
        id="resumeDeleteConfirmBtn"
      >
        Yes, delete
      </button>
    </div>
  </div>
  </section>

  {admin_modals_html}

  <section class="modal-backdrop hidden" id="profilePlanningOptionsModal">
    <div class="modal-card pipeline-modal-card profile-planning-options-card">
      <div class="modal-header">
        <div>
          <h3>Planning &amp; Tailoring Options</h3>
          <div class="subtext">Rerun planning after uploading new resumes so matching can consider the latest files.</div>
        </div>
        <button class="ghost-btn modal-close-btn profile-planning-modal-close-btn" id="closeProfilePlanningOptionsModalBtn" type="button">Close</button>
      </div>

      <div class="pipeline-modal-scroll">
        <div class="pipeline-option-section-header profile-planning-option-header">
          <div class="pipeline-option-title">OPTIONS</div>
          <div class="pipeline-inline-actions">
            <button type="button" class="ghost-btn btn-sm pipeline-bulk-action-btn pipeline-bulk-action-btn--select" id="profilePlanningSelectAllOptionsBtn">Select all</button>
            <button type="button" class="ghost-btn btn-sm pipeline-bulk-action-btn pipeline-bulk-action-btn--clear" id="profilePlanningClearAllOptionsBtn">Clear all</button>
          </div>
        </div>
        <div class="pipeline-toggle-grid profile-planning-options-grid">
          <div class="pipeline-toggle-item">
            <div class="pipeline-toggle-copy">
              <div class="pipeline-toggle-name">Planning only</div>
              <div class="pipeline-toggle-help">Skip scraping and rerun downstream planning only.</div>
            </div>
            <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Planning only">
              <label class="binary-toggle-option">
                <input type="radio" name="profilePlanningOnly" value="no" />
                <span>No</span>
              </label>
              <label class="binary-toggle-option">
                <input type="radio" name="profilePlanningOnly" value="yes" checked />
                <span>Yes</span>
              </label>
            </div>
          </div>

          <div class="pipeline-toggle-item">
            <div class="pipeline-toggle-copy">
              <div class="pipeline-toggle-name">Generate tailoring</div>
              <div class="pipeline-toggle-help">Build deterministic tailoring artifacts.</div>
            </div>
            <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Generate tailoring">
              <label class="binary-toggle-option">
                <input type="radio" name="profileGenerateTailoring" value="no" checked />
                <span>No</span>
              </label>
              <label class="binary-toggle-option">
                <input type="radio" name="profileGenerateTailoring" value="yes" />
                <span>Yes</span>
              </label>
            </div>
          </div>

          <div class="pipeline-toggle-item">
            <div class="pipeline-toggle-copy">
              <div class="pipeline-toggle-name">Generate LLM tailoring</div>
              <div class="pipeline-toggle-help">Run live LLM tailoring generation.</div>
            </div>
            <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Generate LLM tailoring">
              <label class="binary-toggle-option">
                <input type="radio" name="profileGenerateLlmTailoring" value="no" checked />
                <span>No</span>
              </label>
              <label class="binary-toggle-option">
                <input type="radio" name="profileGenerateLlmTailoring" value="yes" />
                <span>Yes</span>
              </label>
            </div>
          </div>

          <div class="pipeline-toggle-item">
            <div class="pipeline-toggle-copy">
              <div class="pipeline-toggle-name">Refresh LLM tailoring</div>
              <div class="pipeline-toggle-help">Force regeneration instead of reusing cached tailoring.</div>
            </div>
            <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Refresh LLM tailoring">
              <label class="binary-toggle-option">
                <input type="radio" name="profileRefreshLlmTailoring" value="no" checked />
                <span>No</span>
              </label>
              <label class="binary-toggle-option">
                <input type="radio" name="profileRefreshLlmTailoring" value="yes" />
                <span>Yes</span>
              </label>
            </div>
          </div>

          <div class="pipeline-toggle-item">
            <div class="pipeline-toggle-copy">
              <div class="pipeline-toggle-name">Generate LLM fallback</div>
              <div class="pipeline-toggle-help">Run fallback resume ranking when needed.</div>
            </div>
            <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Generate LLM fallback">
              <label class="binary-toggle-option">
                <input type="radio" name="profileGenerateLlmFallback" value="no" />
                <span>No</span>
              </label>
              <label class="binary-toggle-option">
                <input type="radio" name="profileGenerateLlmFallback" value="yes" checked />
                <span>Yes</span>
              </label>
            </div>
          </div>

          <div class="pipeline-toggle-item">
            <div class="pipeline-toggle-copy">
              <div class="pipeline-toggle-name">Generate LLM adjudication</div>
              <div class="pipeline-toggle-help">Run LLM adjudication during application planning when enabled.</div>
            </div>
            <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Generate LLM adjudication">
              <label class="binary-toggle-option">
                <input type="radio" name="profileGenerateLlmAdjudication" value="no" />
                <span>No</span>
              </label>
              <label class="binary-toggle-option">
                <input type="radio" name="profileGenerateLlmAdjudication" value="yes" checked />
                <span>Yes</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-actions pipeline-modal-actions">
        <button type="button" class="ghost-btn profile-planning-cancel-btn" id="cancelProfilePlanningOptionsBtn">Cancel</button>
        <button type="button" class="profile-planning-run-btn" id="runProfilePlanningUpdateBtn">Run Planning Update</button>
      </div>
    </div>
  </section>

  <section class="modal-backdrop hidden" id="pipelineRunStatsModal">
    <div class="modal-card pipeline-run-stats-modal-card">
      <div class="modal-header">
        <div>
          <h3 id="pipelineRunStatsTitle">Pipeline run stats</h3>
          <div class="subtext" id="pipelineRunStatsSubtitle">Persisted run details.</div>
        </div>
        <button class="ghost-btn modal-close-btn" id="pipelineRunStatsCloseBtn" type="button">Close</button>
      </div>

      <div class="modal-body">
        <div id="pipelineRunStatsBody" class="pipeline-run-stats-body"></div>
      </div>
    </div>
  </section>

  <section class="modal-backdrop hidden" id="pipelineRunRerunModal">
    <div class="modal-card pipeline-run-rerun-modal-card">
      <div class="modal-header">
        <div>
          <h3 id="pipelineRunRerunTitle">Re-run pipeline</h3>
          <div class="subtext" id="pipelineRunRerunSubtitle">Review the run before starting a new one.</div>
        </div>
        <button class="ghost-btn modal-close-btn" id="pipelineRunRerunCloseBtn" type="button">Close</button>
      </div>

      <div class="modal-body">
        <div id="pipelineRunRerunBody" class="pipeline-run-rerun-body"></div>
      </div>

      <div class="modal-actions pipeline-run-rerun-actions">
        <div class="pipeline-run-rerun-question">Good to re-run?</div>
        <button type="button" class="ghost-btn" id="pipelineRunRerunCancelBtn">No</button>
        <button type="button" class="pipeline-run-rerun-confirm-btn" id="pipelineRunRerunConfirmBtn">Yes</button>
      </div>
    </div>
  </section>

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=phase133h_r1"></script>
  <script src="/static/profile.js?v=item2_phase4_profile_corrections_r1"></script>
</body>
</html>
    """.strip()


@router.get("/profile/pipeline-runs/{run_id}/agentic-review", response_class=HTMLResponse)
def pipeline_run_agentic_review_page(run_id: str) -> str:
    safe_run_id = escape(str(run_id or "").strip())
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Agentic Review</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=agentic_review_v1" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=scheduler_health_polish_r1" />
  <link rel="stylesheet" href="/static/agentic_review.css?v=agentic_review_v1" />
</head>
<body>
{render_top_shell("/profile")}
  <div class="page agentic-review-page" data-agentic-review-run-id="{safe_run_id}">
    <header class="page-header agentic-review-header">
      <div>
        <h1>Agentic Review</h1>
        <p class="subtext" id="agenticReviewSubtitle">Pipeline run {safe_run_id}</p>
      </div>
      <div class="header-actions">
        <a class="ghost-btn" href="/profile?tab=pipeline-runs">Back to pipeline runs</a>
      </div>
    </header>

    <section class="card agentic-review-status-card" id="agenticReviewStatusCard">
      Loading agentic review...
    </section>

    <nav class="agentic-review-tabs" aria-label="Agentic Review sections" role="tablist">
      <button class="agentic-review-tab is-active" type="button" role="tab" aria-selected="true" data-agentic-tab-target="agenticReviewOverviewTab">Overview</button>
      <button class="agentic-review-tab" type="button" role="tab" aria-selected="false" data-agentic-tab-target="agenticReviewAdvisoryTab">Advisory Board</button>
      <button class="agentic-review-tab" type="button" role="tab" aria-selected="false" data-agentic-tab-target="agenticReviewTraceTab">Agent Trace</button>
      <button class="agentic-review-tab" type="button" role="tab" aria-selected="false" data-agentic-tab-target="agenticReviewDiagnosticsTab">Artifacts / Diagnostics</button>
    </nav>

    <main class="agentic-review-tab-panels">
      <section class="agentic-review-tab-panel" id="agenticReviewOverviewTab" data-agentic-tab-panel>
        <section id="agenticWorkflowSummaryPanel" class="card agentic-workflow-summary-card">
          <h2>Agentic Workflow Summary</h2>
          <div class="pipeline-runs-empty-cell">Loading workflow summary...</div>
        </section>
        <section id="agenticWorkflowVerificationPanel" class="card agentic-workflow-verification-card">
          <h2>Agentic Workflow Verification</h2>
          <div class="pipeline-runs-empty-cell">Loading workflow verification...</div>
        </section>
      </section>

      <section class="agentic-review-tab-panel hidden" id="agenticReviewAdvisoryTab" data-agentic-tab-panel>
        <div class="agentic-review-board-shell">
          <div class="agentic-workflow-header">
            <div>
              <h2>Advisory Board</h2>
              <p>Read-only priority, tailoring, and operator review guidance. Production action fields stay unchanged.</p>
            </div>
            <span class="agentic-workflow-badge">Advisory only</span>
          </div>
          <div class="agentic-review-segmented" role="tablist" aria-label="Advisory Board views">
            <button class="agentic-review-segment is-active" type="button" role="tab" aria-selected="true" data-agentic-advisory-target="agenticReviewPriorityPanel">Prioritization</button>
            <button class="agentic-review-segment" type="button" role="tab" aria-selected="false" data-agentic-advisory-target="agenticReviewTailoringPanel">Tailoring</button>
            <button class="agentic-review-segment" type="button" role="tab" aria-selected="false" data-agentic-advisory-target="agenticReviewOperatorPanel">Operator Review</button>
          </div>

          <section class="card agentic-review-section" id="agenticReviewPriorityPanel" data-agentic-advisory-panel>
            <h2>Job Prioritization</h2>
            <div class="pipeline-runs-empty-cell">Loading prioritization details...</div>
          </section>

          <section class="card agentic-review-section hidden" id="agenticReviewTailoringPanel" data-agentic-advisory-panel>
            <h2>Tailoring Decision</h2>
            <div class="pipeline-runs-empty-cell">Loading tailoring decision details...</div>
          </section>

          <section class="card agentic-review-section hidden" id="agenticReviewOperatorPanel" data-agentic-advisory-panel>
            <h2>Operator Review</h2>
            <div class="pipeline-runs-empty-cell">Loading operator review details...</div>
          </section>
        </div>
      </section>

      <section class="agentic-review-tab-panel hidden" id="agenticReviewTraceTab" data-agentic-tab-panel>
        <section class="card agent-trace-panel" id="agenticReviewTracePanel">
          <h2>Agent Trace</h2>
          <div class="pipeline-runs-empty-cell">Loading agent trace...</div>
        </section>
      </section>

      <section class="agentic-review-tab-panel hidden" id="agenticReviewDiagnosticsTab" data-agentic-tab-panel>
        <section class="card agentic-review-diagnostics-card" id="agenticReviewDiagnosticsPanel">
          <h2>Artifacts / Diagnostics</h2>
          <div class="pipeline-runs-empty-cell">Loading artifact diagnostics...</div>
        </section>
      </section>
    </main>
  </div>

  <script src="/static/shell.js?v=phase133h_r1"></script>
  <script src="/static/profile.js?v=agentic_review_v1"></script>
  <script src="/static/agentic_review.js?v=agentic_review_v1"></script>
</body>
</html>
    """.strip()


@router.get("/profile/preferences", response_class=HTMLResponse)
def profile_preferences_page() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Preferences · My Profile</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=preferences_toolbar_ownership_r11" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=scheduler_health_polish_r1" />
  <link rel="stylesheet" href="/static/preferences.css?v=preferences_footer_compact_r15" />
</head>
<body class="preferences-page-shell">
  {render_top_shell("/profile/preferences")}

  <div class="page preferences-page">
    {_preferences_section_html()}
  </div>

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=phase133h_r1"></script>
  <script src="/static/preference_location_selector.js?v=preferences_guided_parity_r9"></script>
  <script src="/static/preferences_workflow.js?v=preferences_guided_parity_r9"></script>
  <script src="/static/profile.js?v=preferences_guided_parity_r9"></script>
</body>
</html>
    """.strip()


@router.get("/profile/ai-settings", response_class=HTMLResponse)
def profile_ai_settings_page() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Settings · My Profile</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=profile_ai_settings_r1" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=profile_ai_settings_step7b_r1" />
  <link rel="stylesheet" href="/static/profile_ai_settings.css?v=phase1_step7b_r1" />
</head>
<body class="profile-ai-settings-page-shell">
  {render_top_shell("/profile/ai-settings")}

  <main class="page profile-ai-settings-page" id="profileAiSettingsPage">
    <header class="page-header app-page-header profile-ai-settings-header">
      <div class="app-page-header__main">
        <div class="app-page-header__title-row">
          <h1 class="app-page-header__title">AI Settings</h1>
        </div>
        <p class="subtext app-page-header__description">Configure your AI providers and test model access.</p>
      </div>
    </header>

    <section class="profile-ai-settings-security-note" aria-label="API key privacy">
      <span class="profile-ai-settings-security-icon" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
          <rect width="18" height="11" x="3" y="11" rx="2" ry="2"></rect>
          <path d="M7 11V7a5 5 0 0 1 10 0v4"></path>
        </svg>
      </span>
      <div>
        <strong>Your API keys stay private.</strong>
        <span>They are stored securely and are never shown again after saving.</span>
      </div>
    </section>

    <div class="profile-ai-settings-page-status hidden" id="aiSettingsPageStatus" role="status" aria-live="polite"></div>

    <section class="profile-ai-settings-loading" id="aiSettingsLoading" aria-live="polite">
      <span class="profile-ai-settings-spinner" aria-hidden="true"></span>
      <span>Loading AI settings…</span>
    </section>

    <section class="profile-ai-settings-error hidden" id="aiSettingsLoadError" role="alert">
      <div>
        <strong>AI settings could not be loaded.</strong>
        <span>Try again to retrieve your provider and model configuration.</span>
      </div>
      <button type="button" class="ghost-btn" id="aiSettingsRetryBtn">Retry</button>
    </section>

    <div class="profile-ai-settings-content hidden" id="aiSettingsContent">
      <section class="profile-ai-settings-card profile-ai-settings-card--providers" aria-labelledby="providerConfigurationTitle">
        <div class="profile-ai-settings-section-heading">
          <div>
            <h2 id="providerConfigurationTitle">Provider configuration</h2>
            <p>Manage write-only credentials for each available AI provider.</p>
          </div>
        </div>
        <div class="profile-ai-settings-provider-grid" id="aiSettingsProviderGrid"></div>
      </section>

      <div class="profile-ai-settings-two-column">
        <section class="profile-ai-settings-card profile-ai-settings-card--preferred" aria-labelledby="preferredProviderTitle">
          <div class="profile-ai-settings-section-heading">
            <div>
              <h2 id="preferredProviderTitle">Preferred provider</h2>
              <p>Save a provider preference without selecting a model.</p>
            </div>
          </div>
          <div class="profile-ai-settings-control-row">
            <div class="profile-ai-settings-field">
              <label for="aiPreferredProviderSelect">Provider</label>
              <select id="aiPreferredProviderSelect"></select>
            </div>
            <button type="button" id="aiPreferredProviderSaveBtn">Save preference</button>
          </div>
          <div class="profile-ai-settings-inline-message hidden" id="aiPreferredProviderStatus" role="status" aria-live="polite"></div>
          <div class="profile-ai-settings-warning hidden" id="aiPreferredProviderWarning" role="status"></div>
        </section>

        <section class="profile-ai-settings-card profile-ai-settings-card--test" aria-labelledby="connectionTestTitle">
          <div class="profile-ai-settings-section-heading">
            <div>
              <h2 id="connectionTestTitle">Test connection</h2>
              <p>Run a manual, bounded check with one available model.</p>
            </div>
          </div>
          <div class="profile-ai-settings-test-fields">
            <div class="profile-ai-settings-field">
              <label for="aiTestProviderSelect">Provider</label>
              <select id="aiTestProviderSelect"></select>
            </div>
            <div class="profile-ai-settings-field">
              <label for="aiTestModelSelect">Model</label>
              <select id="aiTestModelSelect"></select>
            </div>
          </div>
          <div class="profile-ai-settings-test-actions">
            <div class="profile-ai-settings-inline-message hidden" id="aiConnectionTestStatus" role="status" aria-live="polite"></div>
            <button type="button" id="aiConnectionTestBtn" disabled>Test connection</button>
          </div>
        </section>
      </div>

      <section class="profile-ai-settings-card profile-ai-settings-card--models" aria-labelledby="availableModelsTitle">
        <div class="profile-ai-settings-section-heading">
          <div>
            <h2 id="availableModelsTitle">Available models</h2>
            <p>Configuration candidates supplied by the provider catalog.</p>
          </div>
        </div>
        <div class="profile-ai-settings-model-groups" id="aiSettingsModelGroups"></div>
      </section>

      <section class="profile-ai-settings-card profile-ai-settings-routing" aria-labelledby="aiTaskRoutingTitle">
        <div class="profile-ai-settings-section-heading">
          <div>
            <h2 id="aiTaskRoutingTitle">AI task routing</h2>
            <p>Task-specific model routing will appear here after model qualification and routing configuration are enabled.</p>
          </div>
          <span class="profile-ai-settings-readonly-badge">Not configured</span>
        </div>
      </section>

      <p class="profile-ai-settings-provider-attribution">
        OpenAI and its logo are trademarks of OpenAI. Groq is a trademark of Groq LLC and/or its affiliates. ApplyLens is not affiliated with or endorsed by either provider.
      </p>
    </div>
  </main>

  <section class="modal-backdrop profile-ai-settings-modal hidden" id="aiCredentialModal" role="dialog" aria-modal="true" aria-labelledby="aiCredentialModalTitle">
    <div class="modal-card profile-ai-settings-modal-card profile-ai-settings-credential-card">
      <div class="modal-header profile-ai-settings-modal-header">
        <div>
          <h3 id="aiCredentialModalTitle">Add API key</h3>
          <p class="subtext profile-ai-settings-modal-provider" id="aiCredentialModalSubtitle"></p>
        </div>
      </div>
      <form class="profile-ai-settings-modal-form" id="aiCredentialForm" autocomplete="off">
        <div class="modal-body profile-ai-settings-modal-body">
          <div class="profile-ai-settings-field">
            <label for="aiCredentialInput">API key</label>
            <div class="profile-ai-settings-secret-control">
              <input id="aiCredentialInput" type="password" autocomplete="new-password" spellcheck="false" required />
              <button
                type="button"
                class="ghost-btn profile-ai-settings-secret-toggle"
                id="aiCredentialVisibilityBtn"
                aria-label="Show API key"
                aria-pressed="false"
                title="Show API key"
              >
                <svg
                  class="profile-ai-settings-secret-toggle-icon"
                  id="aiCredentialVisibilityShowIcon"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  aria-hidden="true"
                  focusable="false"
                >
                  <path d="M2.25 12s3.5-6.75 9.75-6.75S21.75 12 21.75 12 18.25 18.75 12 18.75 2.25 12 2.25 12Z"></path>
                  <circle cx="12" cy="12" r="3.25"></circle>
                </svg>
                <svg
                  class="profile-ai-settings-secret-toggle-icon"
                  id="aiCredentialVisibilityHideIcon"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  stroke-width="1.8"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  aria-hidden="true"
                  focusable="false"
                  hidden
                >
                  <path d="M3 3 21 21"></path>
                  <path d="M10.73 5.08A9.65 9.65 0 0 1 12 5c6.25 0 9.75 7 9.75 7a17.5 17.5 0 0 1-3.18 3.96"></path>
                  <path d="M14.12 14.12A3 3 0 0 1 9.88 9.88"></path>
                  <path d="M6.36 6.36C3.7 8.16 2.25 12 2.25 12s3.5 7 9.75 7a9.4 9.4 0 0 0 4.64-1.22"></path>
                </svg>
              </button>
            </div>
          </div>
          <p class="profile-ai-settings-privacy-copy">The key is encrypted before storage. ApplyLens will not display it again after you save.</p>
          <div class="profile-ai-settings-inline-message hidden" id="aiCredentialModalStatus" role="alert"></div>
        </div>
        <div class="modal-actions profile-ai-settings-modal-footer">
          <button type="button" class="ghost-btn" id="aiCredentialCancelBtn">Cancel</button>
          <button type="submit" id="aiCredentialSaveBtn">Save key</button>
        </div>
      </form>
    </div>
  </section>

  <section class="modal-backdrop profile-ai-settings-modal hidden" id="aiCredentialRemoveModal" role="dialog" aria-modal="true" aria-labelledby="aiCredentialRemoveTitle">
    <div class="modal-card profile-ai-settings-modal-card">
      <div class="modal-header">
        <div>
          <h3 id="aiCredentialRemoveTitle">Remove API key?</h3>
          <p class="subtext" id="aiCredentialRemoveSubtitle"></p>
        </div>
        <button type="button" class="ghost-btn modal-close-btn" id="aiCredentialRemoveCloseBtn" aria-label="Close remove API key dialog">Close</button>
      </div>
      <div class="modal-body">
        <p>ApplyLens will no longer be able to use this provider through your configured credential until a new key is saved. This does not revoke the key in the provider’s own dashboard.</p>
        <div class="profile-ai-settings-inline-message hidden" id="aiCredentialRemoveStatus" role="alert"></div>
      </div>
      <div class="modal-actions">
        <button type="button" class="ghost-btn" id="aiCredentialRemoveCancelBtn">Cancel</button>
        <button type="button" class="profile-ai-settings-danger-btn" id="aiCredentialRemoveConfirmBtn">Remove key</button>
      </div>
    </div>
  </section>

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=phase133h_r1"></script>
  <script src="/static/profile_ai_settings.js?v=phase1_step7b_r1"></script>
</body>
</html>
    """.strip()


@router.get("/profile/saved-scans", response_class=HTMLResponse)
def saved_scans_page() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Saved Scans</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=profile_confirm_specific_r2" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=scheduler_health_polish_r1" />
</head>
<body>
  {render_top_shell("/profile/saved-scans")}

  <div class="page">
    <header class="page-header">
      <div>
        <h1>Saved Scans</h1>
        <p class="subtext">Review New Scan reports generated from submitted resumes and job descriptions.</p>
      </div>
    </header>

    <section class="card profile-section-card">
      <div class="section-header">
        <div>
          <h2>Saved Scans</h2>
          <div class="subtext" id="savedScansMeta">Loading saved scans...</div>
        </div>
        <button type="button" class="ghost-btn btn-sm" id="refreshSavedScansBtn">
          Refresh
        </button>
      </div>

      <div class="saved-scans-note">
        New Scan rows now store the generated match score and review payload in Postgres.
      </div>

      <div class="saved-scans-table-wrap">
        <table class="saved-scans-table">
          <thead>
            <tr>
              <th>Scanned</th>
              <th>Company</th>
              <th>Role</th>
              <th>Resume</th>
              <th>Source</th>
              <th>Status</th>
              <th>Match</th>
              <th>Action</th>
              <th></th>
            </tr>
          </thead>
          <tbody id="savedScansTableBody">
            <tr>
              <td colspan="9">Loading saved scans...</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section class="modal-backdrop hidden" id="savedScanDeleteModal">
      <div class="modal-card resume-delete-modal-card">
        <div class="modal-header">
          <div>
            <h3>Delete saved scan?</h3>
            <p class="subtext">This removes the selected scan row and stored report payload.</p>
          </div>
          <button
            type="button"
            class="ghost-btn modal-close-btn resume-delete-modal-close-btn"
            id="savedScanDeleteCloseBtn"
          >
            Close
          </button>
        </div>
        <div class="modal-body">
          Are you sure you want to delete
          <strong id="savedScanDeleteName">this saved scan</strong>?
        </div>
        <div class="modal-actions resume-delete-modal-actions">
          <button
            type="button"
            class="ghost-btn resume-delete-cancel-btn"
            id="savedScanDeleteCancelBtn"
          >
            No
          </button>
          <button
            type="button"
            class="resume-delete-confirm-btn"
            id="savedScanDeleteConfirmBtn"
          >
            Yes, delete
          </button>
        </div>
      </div>
    </section>
  </div>

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=phase133h_r1"></script>
  <script src="/static/profile.js?v=profile_saved_scans_e5_discard_icon_profile_resume_roles_r10"></script>
</body>
</html>
    """.strip()
