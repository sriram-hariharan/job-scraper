from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.app.ui_shell import render_top_shell

router = APIRouter()


@router.get("/applications", response_class=HTMLResponse)
def applications_dashboard() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Applications</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v6" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=ui_redesign_v6" />
</head>
<body>
  {render_top_shell("/applications")}

  <div class="page">
    <header class="page-header">
      <div>
        <h1>Applications</h1>
        <p class="subtext">Track jobs you applied to or saved for later.</p>
      </div>
    </header>

    <section class="card controls-card" id="applicationViewRoot">
      <div class="application-tabs" id="applicationTabs">
        <button type="button" class="application-tab active" data-app-tab="APPLIED">Applied Jobs</button>
        <button type="button" class="application-tab" data-app-tab="SAVED">Saved for Later</button>
      </div>

      <div class="controls-row">
        <div class="control-group">
          <label for="applicationCompanyFilter">Company contains</label>
          <input type="text" id="applicationCompanyFilter" placeholder="e.g. waymo" />
        </div>

        <div class="control-group">
          <label for="applicationTitleFilter">Title contains</label>
          <input type="text" id="applicationTitleFilter" placeholder="e.g. machine learning" />
        </div>

        <div class="control-group">
          <label for="applicationLimitInput">Limit</label>
          <input type="number" id="applicationLimitInput" value="15" min="1" max="100" />
        </div>

        <div class="control-group button-group">
          <button id="applicationApplyFiltersBtn">Apply Filters</button>
          <button class="ghost-btn" id="applicationClearFiltersBtn">Clear</button>
        </div>
      </div>
    </section>

    <section class="stats-grid">
      <section class="card stat-card">
        <div class="stat-label">Jobs Shown</div>
        <div class="stat-value" id="applicationJobsShown">0</div>
      </section>
      <section class="card stat-card">
        <div class="stat-label">Current View</div>
        <div class="stat-value" id="applicationViewLabel">Applied</div>
      </section>
    </section>

    <section class="card table-card">
      <div class="section-header application-table-header">
        <h2 id="applicationTableTitle">Applied Jobs</h2>

        <div class="application-table-header-right">
          <div class="application-pagination-inline" id="applicationPaginationBar">
            <div class="subtext application-pagination-meta" id="applicationPaginationMeta">
              Page 1 of 1
            </div>
            <div class="application-pagination-actions" id="applicationPaginationActions"></div>
          </div>

          <div class="subtext" id="applicationTableMeta">Loading...</div>
        </div>
      </div>

      <div class="table-wrap">
        <table id="applicationTable">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Company</th>
              <th>Title</th>
              <th>Status</th>
              <th>Source View</th>
              <th>Note</th>
              <th>Open</th>
            </tr>
          </thead>
          <tbody id="applicationTableBody"></tbody>
        </table>
      </div>
    </section>
  </div>

  <section class="modal-backdrop hidden" id="appErrorModal">
    <div class="modal-card app-error-modal-card">
      <div class="modal-header app-error-modal-header">
        <div>
          <h3 id="appErrorTitle">Something went wrong</h3>
          <div class="subtext" id="appErrorSubtitle">Review the message below.</div>
        </div>
        <button class="ghost-btn modal-close-btn" id="closeAppErrorModalBtn" type="button">Close</button>
      </div>

      <div class="app-error-panel">
        <div class="app-error-icon-wrap" aria-hidden="true">
          <img
            class="app-error-icon-img"
            src="/static/media/error_img.png"
            alt=""
          />
        </div>
        <div class="app-error-copy">
          <div class="app-error-badge">Warning</div>
          <div class="app-error-message" id="appErrorMessage"></div>
        </div>
      </div>

      <div class="modal-actions app-error-actions">
        <button type="button" id="appErrorOkBtn">OK</button>
      </div>
    </div>
  </section>

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=ui_redesign_v6"></script>
  <script src="/static/application_views.js"></script>
</body>
</html>
    """.strip()