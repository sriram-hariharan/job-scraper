from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/decisions-ui", response_class=HTMLResponse)
def decisions_dashboard() -> str:
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Decisions Dashboard</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Decisions Dashboard</h1>
        <p class="subtext">Audit trail for operator decisions and selected resume variants.</p>
      </div>
      <div class="header-actions">
        <a class="ghost-link-btn" href="/">Executive Dashboard</a>
        <a class="ghost-link-btn" href="/planning">Planning Detail</a>
      </div>
    </header>

    <section class="card controls-card">
      <div class="controls-row">
        <div class="control-group">
          <label for="decisionFilter">Decision</label>
          <select id="decisionFilter">
            <option value="">All</option>
            <option value="APPLY">APPLY</option>
            <option value="TAILOR">TAILOR</option>
            <option value="SKIP">SKIP</option>
            <option value="HOLD">HOLD</option>
          </select>
        </div>

        <div class="control-group">
          <label for="decisionCompanyFilter">Company contains</label>
          <input type="text" id="decisionCompanyFilter" placeholder="e.g. waymo" />
        </div>

        <div class="control-group">
          <label for="decisionLimitInput">Limit</label>
          <input type="number" id="decisionLimitInput" value="50" min="1" max="300" />
        </div>

        <div class="control-group button-group">
          <button id="decisionApplyFiltersBtn">Apply Filters</button>
          <button class="ghost-btn" id="decisionClearFiltersBtn">Clear</button>
        </div>
      </div>
    </section>

    <section class="card table-card">
      <div class="section-header">
        <h2>Operator Decisions</h2>
        <div class="subtext" id="decisionsTableMeta">Loading...</div>
      </div>

      <div class="table-wrap">
        <table id="decisionsTable">
          <thead>
            <tr>
              <th>Timestamp</th>
              <th>Queue Rank</th>
              <th>Decision</th>
              <th>Company</th>
              <th>Title</th>
              <th>Planning Action</th>
              <th>Selected Resume</th>
              <th>Winner Resume</th>
              <th>Runner-Up Resume</th>
              <th>Note</th>
            </tr>
          </thead>
          <tbody id="decisionsTableBody"></tbody>
        </table>
      </div>
    </section>
  </div>

  <script src="/static/decisions.js"></script>
</body>
</html>
    """.strip()