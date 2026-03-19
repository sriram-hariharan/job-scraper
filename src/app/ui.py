from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def executive_dashboard() -> str:
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Executive Queue Dashboard</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Executive Queue</h1>
        <p class="subtext">High-signal operator dashboard for direct apply and review decisions.</p>
      </div>
      <div class="header-actions">
        <button id="refreshStatusBtn">Refresh</button>
        <a class="ghost-link-btn" href="/planning">Planning Detail</a>
        <a class="ghost-link-btn" href="/decisions-ui">Decisions</a>
        <a class="ghost-link-btn" href="/intelligence">Intelligence</a>
      </div>
    </header>

    <section class="stats-grid">
      <section class="card stat-card">
        <div class="stat-label">Queue Rows</div>
        <div class="stat-value" id="statQueueRows">-</div>
      </section>
      <section class="card stat-card">
        <div class="stat-label">Operator Decisions</div>
        <div class="stat-value" id="statDecisionRows">-</div>
      </section>
      <section class="card stat-card">
        <div class="stat-label">Undecided Apply Review</div>
        <div class="stat-value" id="statUndecidedApplyReview">-</div>
      </section>
      <section class="card stat-card">
        <div class="stat-label">Undecided Maybe Tailor</div>
        <div class="stat-value" id="statUndecidedMaybeTailor">-</div>
      </section>
    </section>

    <section class="card controls-card">
      <div class="controls-row">
        <div class="control-group">
          <label for="actionFilter">Action</label>
          <select id="actionFilter">
            <option value="">All</option>
            <option value="APPLY">APPLY</option>
            <option value="APPLY_REVIEW_VARIANTS">APPLY_REVIEW_VARIANTS</option>
            <option value="MAYBE_TAILOR">MAYBE_TAILOR</option>
            <option value="SKIP_FOR_NOW">SKIP_FOR_NOW</option>
          </select>
        </div>

        <div class="control-group checkbox-group">
          <label for="undecidedOnly">
            <input type="checkbox" id="undecidedOnly" />
            Undecided only
          </label>
        </div>

        <div class="control-group">
          <label for="limitInput">Limit</label>
          <input type="number" id="limitInput" value="25" min="1" max="200" />
        </div>

        <div class="control-group button-group">
          <button id="applyFiltersBtn">Apply Filters</button>
          <button class="ghost-btn" id="clearFiltersBtn">Clear</button>
        </div>
      </div>

      <div class="controls-row quick-view-row">
        <button class="ghost-btn quick-view-btn" data-view="direct_apply_pending">Direct Apply Pending</button>
        <button class="ghost-btn quick-view-btn" data-view="variant_review_pending">Variant Review Pending</button>
        <button class="ghost-btn quick-view-btn" data-view="tailor_pending">Tailor Pending</button>
        <button class="ghost-btn quick-view-btn" data-view="applied_jobs">Applied Jobs</button>
      </div>
    </section>

    <section class="card table-card">
      <div class="section-header">
        <h2>Queue Table</h2>
        <div class="subtext" id="tableMeta">Loading...</div>
      </div>

      <div class="table-wrap">
        <table id="queueTable">
          <thead>
            <tr>
              <th>Queue Rank</th>
              <th>Action</th>
              <th>Company</th>
              <th>Title</th>
              <th>Winner Resume</th>
              <th>Winner Score</th>
              <th>Runner-Up Resume</th>
              <th>Score Gap</th>
              <th>Missing Req Count</th>
              <th>Operator Decision</th>
              <th>Selected Resume</th>
              <th>Priority Reason</th>
              <th class="sticky-apply-col">Apply</th>
            </tr>
          </thead>
          <tbody id="queueTableBody"></tbody>
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

  <script src="/static/app.js"></script>
</body>
</html>
    """.strip()