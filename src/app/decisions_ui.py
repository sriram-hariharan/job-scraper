from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.app.ui_shell import render_top_shell

router = APIRouter()


@router.get("/decisions-ui", response_class=HTMLResponse)
def decisions_dashboard() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Decisions Dashboard</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=ui_redesign_v23" />
</head>
<body>
{render_top_shell("/decisions-ui")}
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Decisions Dashboard</h1>
        <p class="subtext">Audit trail for operator decisions and selected resume variants.</p>
      </div>
    </header>

    <section class="card controls-card">
      <div class="controls-row">
        <div class="control-group">
          <label>Decision</label>
          <div class="multi-select" id="decisionFilter" data-placeholder="All">
            <button type="button" class="multi-select-trigger" aria-haspopup="menu" aria-expanded="false">
              <span class="multi-select-trigger-label">All</span>
              <span class="multi-select-trigger-icon">▾</span>
            </button>

            <div class="multi-select-menu" role="menu" hidden>
              <button type="button" class="multi-select-option" data-value="APPLY" aria-checked="false">
                <span class="multi-select-option-check">✓</span>
                <span class="multi-select-option-label">APPLY</span>
              </button>
              <button type="button" class="multi-select-option" data-value="TAILOR" aria-checked="false">
                <span class="multi-select-option-check">✓</span>
                <span class="multi-select-option-label">TAILOR</span>
              </button>
              <button type="button" class="multi-select-option" data-value="SKIP" aria-checked="false">
                <span class="multi-select-option-check">✓</span>
                <span class="multi-select-option-label">SKIP</span>
              </button>
              <button type="button" class="multi-select-option" data-value="HOLD" aria-checked="false">
                <span class="multi-select-option-check">✓</span>
                <span class="multi-select-option-label">HOLD</span>
              </button>
            </div>
          </div>
        </div>

        <div class="control-group">
          <label for="decisionCompanyFilter">Company contains</label>
          <input type="text" id="decisionCompanyFilter" placeholder="e.g. waymo" />
        </div>

        <div class="control-group">
          <label for="decisionLimitInput">Limit</label>
          <input type="number" id="decisionLimitInput" value="15" min="1" max="300" />
        </div>

        <div class="control-group button-group">
          <button id="decisionApplyFiltersBtn">Apply Filters</button>
          <button class="ghost-btn" id="decisionClearFiltersBtn">Clear</button>
        </div>
      </div>
    </section>

    <section class="stats-grid">
      <section class="card stat-card">
        <div class="stat-label">Decisions Shown</div>
        <div class="stat-value" id="decisionsShownCount">0</div>
      </section>
      <section class="card stat-card">
        <div class="stat-label">Jobs Touched</div>
        <div class="stat-value" id="decisionsJobsTouched">0</div>
      </section>
    </section>

    <section class="card table-card">
      <div class="section-header application-table-header">
        <h2>Operator Decisions</h2>
        <div class="application-table-header-right">
          <div class="subtext" id="decisionsTableMeta">Loading...</div>
          <div class="application-pagination-inline" id="decisionsPaginationInline">
            <div class="application-pagination-meta" id="decisionsPaginationMeta">Loading...</div>
            <div class="application-pagination-actions" id="decisionsPaginationActions"></div>
          </div>
        </div>
      </div>

      <div class="table-wrap">
        <table id="decisionsTable">
          <thead>
            <tr>
              <th>Date / Time</th>
              <th>Queue Rank</th>
              <th>Decision</th>
              <th>Company</th>
              <th>Title</th>
              <th>Posted At</th>
              <th>Planning Action</th>
              <th>Selected Resume</th>
              <th>Winner Resume</th>
              <th>Runner-Up Resume</th>
              <th>Note</th>
              <th class="sticky-apply-col">Apply</th>
            </tr>
          </thead>
          <tbody id="decisionsTableBody"></tbody>
        </table>
      </div>
    </section>
  </div>

  <section class="modal-backdrop hidden" id="applicationActionModal">
    <div class="modal-card">
      <div class="modal-header">
        <div>
          <h3>Update application status</h3>
          <div class="subtext" id="applicationModalMeta">Choose what happened after opening the job.</div>
        </div>
        <button class="ghost-btn modal-close-btn" id="closeApplicationModalBtn" type="button">Close</button>
      </div>

      <div class="modal-body">
        <div class="info-pair">
          <span class="label">Company</span>
          <span id="applicationModalCompany">-</span>
        </div>
        <div class="info-pair">
          <span class="label">Title</span>
          <span id="applicationModalTitle">-</span>
        </div>
      </div>

      <div class="modal-actions">
        <button type="button" class="status-action-btn applied-action-btn" data-status-action="APPLIED">Applied</button>
        <button type="button" class="status-action-btn saved-action-btn" data-status-action="SAVED">Save for later</button>
        <button type="button" class="status-action-btn not-applied-action-btn" data-status-action="NOT_APPLIED">Not applied</button>
        <button type="button" class="ghost-btn" data-status-action="DISMISSED">Dismiss</button>
      </div>
    </div>
  </section>

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
  <script src="/static/shell.js?v=ui_redesign_v17"></script>
  <script src="/static/decisions.js"></script>
</body>
</html>
    """.strip()