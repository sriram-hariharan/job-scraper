from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/planning", response_class=HTMLResponse)
def planning_dashboard() -> str:
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Planning Detail Dashboard</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Planning Detail Dashboard</h1>
        <p class="subtext">Wide planning view with queue, fallback, tie, and operator decision fields.</p>
      </div>
      <div class="header-actions">
        <a class="ghost-link-btn" href="/">Executive Dashboard</a>
        <a class="ghost-link-btn" href="/decisions-ui">Decisions</a>
      </div>
    </header>

    <section class="card controls-card">
      <div class="controls-row">
        <div class="control-group">
          <label for="planningActionFilter">Action</label>
          <select id="planningActionFilter">
            <option value="">All</option>
            <option value="APPLY">APPLY</option>
            <option value="APPLY_REVIEW_VARIANTS">APPLY_REVIEW_VARIANTS</option>
            <option value="MAYBE_TAILOR">MAYBE_TAILOR</option>
            <option value="SKIP_FOR_NOW">SKIP_FOR_NOW</option>
          </select>
        </div>

        <div class="control-group">
          <label for="planningWinnerBucket">Winner Bucket</label>
          <select id="planningWinnerBucket">
            <option value="">All</option>
            <option value="strong">strong</option>
            <option value="solid">solid</option>
            <option value="moderate">moderate</option>
            <option value="weak">weak</option>
            <option value="filtered_out">filtered_out</option>
          </select>
        </div>

        <div class="control-group checkbox-group">
          <label for="planningUndecidedOnly">
            <input type="checkbox" id="planningUndecidedOnly" />
            Undecided only
          </label>
        </div>

        <div class="control-group">
          <label for="planningLimitInput">Limit</label>
          <input type="number" id="planningLimitInput" value="50" min="1" max="300" />
        </div>

        <div class="control-group button-group">
          <button id="planningApplyFiltersBtn">Apply Filters</button>
          <button class="ghost-btn" id="planningClearFiltersBtn">Clear</button>
        </div>
      </div>
    </section>

    <section class="card table-card">
      <div class="section-header">
        <h2>Planning Detail Table</h2>
        <div class="subtext" id="planningTableMeta">Loading...</div>
      </div>

      <div class="table-wrap">
        <table id="planningTable">
          <thead>
            <tr>
              <th>Queue Rank</th>
              <th>Action</th>
              <th>Company</th>
              <th>Title</th>
              <th>Winner Resume</th>
              <th>Winner Score</th>
              <th>Runner-Up Resume</th>
              <th>Runner-Up Score</th>
              <th>Score Gap</th>
              <th>Winner Bucket</th>
              <th>Is Tie</th>
              <th>Needs Review</th>
              <th>Missing Req Count</th>
              <th>Fallback Best Resume</th>
              <th>Fallback Status</th>
              <th>Operator Decision</th>
              <th>Operator Selected Resume</th>
              <th>Priority Reason</th>
            </tr>
          </thead>
          <tbody id="planningTableBody"></tbody>
        </table>
      </div>
    </section>
  </div>

  <script src="/static/planning.js"></script>
</body>
</html>
    """.strip()