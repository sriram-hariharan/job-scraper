from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.app.ui_shell import render_top_shell

router = APIRouter()


@router.get("/profile", response_class=HTMLResponse)
def profile_page() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>My Profile</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=ui_redesign_v28" />
</head>
<body>
  {render_top_shell("/profile")}

  <div class="page">
    <header class="page-header">
      <div>
        <h1>My Profile</h1>
        <p class="subtext">Manage the resume files used by deterministic matching and application planning.</p>
      </div>
    </header>

    <section class="card profile-section-card">
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
              Uploaded files go directly into the configured RESUME_DIR and become available to the existing resume loader.
            </div>
          </div>
        </section>

        <section class="resume-list-panel">
          <div class="resume-list" id="resumeList"></div>
        </section>
      </div>
    </section>
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

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=ui_redesign_v18"></script>
  <script src="/static/profile.js?v=profile_saved_scans_e5_discard_icon"></script>
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
  <link rel="stylesheet" href="/static/app_redesign.css?v=ui_redesign_v28" />
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
  <script src="/static/shell.js?v=ui_redesign_v18"></script>
  <script src="/static/profile.js?v=profile_saved_scans_e5_discard_icon"></script>
</body>
</html>
    """.strip()
