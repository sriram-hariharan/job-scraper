from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()

@router.get("/", response_class=HTMLResponse)
def dashboard_home() -> str:
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Job Operator Dashboard</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Job Operator Dashboard</h1>
        <p class="subtext">Executive queue view for review and action.</p>
      </div>
      <div class="header-actions">
        <button class="ghost-btn" id="refreshStatusBtn">Refresh Status</button>
      </div>
    </header>

    <section class="stats-grid" id="statsGrid">
      <div class="card stat-card">
        <div class="stat-label">Queue Rows</div>
        <div class="stat-value" id="statQueueRows">-</div>
      </div>
      <div class="card stat-card">
        <div class="stat-label">Operator Decisions</div>
        <div class="stat-value" id="statDecisionRows">-</div>
      </div>
      <div class="card stat-card">
        <div class="stat-label">Undecided Apply Review</div>
        <div class="stat-value" id="statUndecidedApplyReview">-</div>
      </div>
      <div class="card stat-card">
        <div class="stat-label">Undecided Maybe Tailor</div>
        <div class="stat-value" id="statUndecidedMaybeTailor">-</div>
      </div>
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

      <div class="quick-actions">
        <button class="quick-view-btn" data-view="direct_apply_pending">Direct Apply Pending</button>
        <button class="quick-view-btn" data-view="undecided_apply_review">Undecided Apply Review</button>
        <button class="quick-view-btn" data-view="undecided_maybe_tailor">Undecided Maybe Tailor</button>
        <button class="quick-view-btn" data-view="runner_up_selected">Runner-Up Selected</button>
      </div>
    </section>

    <section class="card table-card">
      <div class="section-header">
        <h2>Executive Queue</h2>
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
            </tr>
          </thead>
          <tbody id="queueTableBody">
          </tbody>
        </table>
      </div>
    </section>
  </div>

  <script src="/static/app.js"></script>
</body>
</html>
    """.strip()