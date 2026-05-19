from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from src.app.onboarding_ui import _role_family_cards_html
from src.app.ui_shell import render_top_shell
from src.auth.runtime import current_user_from_request

router = APIRouter()


def _preferences_section_html(*, hidden: bool = False, tab_panel: bool = False) -> str:
    hidden_class = " hidden" if hidden else ""
    tab_attr = " data-profile-tab-panel" if tab_panel else ""
    return f"""
    <section class="card profile-section-card profile-preferences-section{hidden_class}" id="profilePreferencesSection"{tab_attr}>
      <div class="section-header">
        <div>
          <h2>Preferences</h2>
          <div class="subtext">Update the same role and matching preferences you selected during onboarding.</div>
        </div>
      </div>

      <div class="profile-inline-status hidden" id="profilePreferencesStatusBanner"></div>

      <form class="profile-preferences-form" id="profilePreferencesForm">
        <section class="profile-preferences-group">
          <div class="profile-preferences-group-header">
            <div>
              <h3>Role interests</h3>
              <p class="subtext">Select at least one role family to guide your job queue.</p>
            </div>
            <span class="onboarding-required-pill">Required</span>
          </div>
          <div class="onboarding-role-grid" id="profilePreferencesRoleGrid">
            {_role_family_cards_html()}
          </div>
        </section>

        <section class="profile-preferences-group">
          <div class="profile-preferences-group-header">
            <div>
              <h3>Seniority and work style</h3>
              <p class="subtext">These are saved as preferences and can be changed anytime.</p>
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
            <textarea id="profilePreferredLocationsInput" rows="3" placeholder="New York, Remote, Boston"></textarea>
          </label>
        </section>

        <section class="profile-preferences-group">
          <div class="profile-preferences-group-header">
            <div>
              <h3>Skills and exclusions</h3>
              <p class="subtext">Optional keywords to tune future role expansion and matching.</p>
            </div>
          </div>
          <div class="onboarding-field-grid">
            <label class="onboarding-text-field">
              <span>Preferred skills/tools</span>
              <textarea id="profilePreferredSkillsInput" rows="4" placeholder="Python, AWS, React, Kubernetes"></textarea>
            </label>
            <label class="onboarding-text-field">
              <span>Excluded keywords</span>
              <textarea id="profileExcludedKeywordsInput" rows="4" placeholder="intern, unpaid, commission only"></textarea>
            </label>
          </div>
        </section>

        <div class="profile-preferences-actions">
          <button type="submit" id="profilePreferencesSaveBtn">Save preferences</button>
        </div>
      </form>
    </section>
"""


@router.get("/profile", response_class=HTMLResponse)
def profile_page(request: Request) -> str:
    user = dict(getattr(request.state, "auth_user", {}) or {}) or current_user_from_request(request)
    access_level = str(user.get("access_level", "") or "").strip().lower()
    is_admin = bool(user.get("is_admin", False)) or access_level == "admin"
    admin_tab_html = (
        """
      <button type="button" class="profile-tab-btn" data-profile-tab-target="profileAdminUsersSection">User access</button>"""
        if is_admin
        else ""
    )
    profile_tabs_html = f"""
    <nav class="profile-tabs" id="profileTabs" aria-label="Profile sections">
      <button type="button" class="profile-tab-btn is-active" data-profile-tab-target="resumeSection">
        <img class="profile-tab-icon" src="/static/media/profile_icon.svg" alt="" aria-hidden="true" />
        <span>Resumes</span>
      </button>
      <button type="button" class="profile-tab-btn" data-profile-tab-target="profilePipelineRunsSection">
        <img class="profile-tab-icon" src="/static/media/scan_icon.svg" alt="" aria-hidden="true" />
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
          <button type="button" class="ghost-btn btn-sm" id="refreshPipelineRunsBtn">
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
              <th>View</th>
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
        <button class="ghost-btn modal-close-btn" id="adminUserAccessCloseBtn" type="button">Close</button>
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
        <button class="ghost-btn modal-close-btn" id="adminUserDeleteCloseBtn" type="button">Close</button>
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
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=role_profile_preferences_tabs_r1" />
</head>
<body>
  {render_top_shell("/profile")}

  <div class="page">
    <header class="page-header">
      <div>
        <h1>My Profile</h1>
        <p class="subtext">Manage resume files and persisted Live Pipeline runs.</p>
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
        class="ghost-btn modal-close-btn"
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
        class="ghost-btn resume-delete-cancel-btn"
        id="resumeDeleteCancelBtn"
      >
        No
      </button>
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

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=role_onboarding_r6"></script>
  <script src="/static/profile.js?v=profile_preferences_tabs_r1"></script>
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
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=role_profile_preferences_menu_r1" />
</head>
<body>
  {render_top_shell("/profile/preferences")}

  <div class="page">
    <header class="page-header">
      <div>
        <h1>Preferences</h1>
        <p class="subtext">Tune role interests, locations, work style, and matching keywords.</p>
      </div>
    </header>

    {_preferences_section_html()}
  </div>

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=role_onboarding_r6"></script>
  <script src="/static/profile.js?v=profile_preferences_menu_r1"></script>
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
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=role_expansion_r10_ui" />
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
            class="ghost-btn modal-close-btn"
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
            class="ghost-btn"
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
  <script src="/static/shell.js?v=role_onboarding_r6"></script>
  <script src="/static/profile.js?v=profile_saved_scans_e5_discard_icon_profile_resume_roles_r10"></script>
</body>
</html>
    """.strip()
