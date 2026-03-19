from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.app.ui_shell import render_top_shell

router = APIRouter()


@router.get("/intelligence", response_class=HTMLResponse)
def intelligence_dashboard() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Job Intelligence Dashboard</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
{render_top_shell("/intelligence")}
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Job Intelligence Dashboard</h1>
        <p class="subtext">Search the job corpus and ask grounded questions over retrieved jobs.</p>
      </div>
      <div class="header-actions">
        <a class="ghost-link-btn" href="/">Executive Dashboard</a>
        <a class="ghost-link-btn" href="/planning">Planning Detail</a>
        <a class="ghost-link-btn" href="/decisions-ui">Decisions</a>
      </div>
    </header>

    <section class="card controls-card">
      <div class="controls-row">
        <div class="control-group wide-control">
          <label for="ragRequestInput">Request</label>
          <input
            type="text"
            id="ragRequestInput"
            placeholder="e.g. find jobs at waymo or which jobs look strongest for experimentation-heavy data science work?"
          />
        </div>

        <div class="control-group">
          <label for="ragModeSelect">Mode</label>
          <select id="ragModeSelect">
            <option value="search">Search Jobs</option>
            <option value="answer">Answer Question</option>
          </select>
        </div>

        <div class="control-group">
          <label for="ragTopKInput">Results to Return</label>
          <input type="number" id="ragTopKInput" value="5" min="1" max="20" />
          <div class="control-help">How many final jobs or sources to show.</div>
        </div>

        <div class="control-group">
          <label for="ragFetchKInput">Candidates to Scan</label>
          <input type="number" id="ragFetchKInput" value="15" min="1" max="50" />
          <div class="control-help">How many jobs to search before narrowing to the best matches.</div>
        </div>

        <div class="control-group checkbox-group">
          <label for="ragDiagnosticsCheckbox">
            <input type="checkbox" id="ragDiagnosticsCheckbox" />
            Include diagnostics
          </label>
        </div>

        <div class="control-group button-group">
          <button id="runRagBtn">Run</button>
          <button class="ghost-btn" id="clearRagBtn">Clear</button>
        </div>
      </div>
    </section>

    <section class="stats-grid">
      <section class="card stat-card">
        <div class="stat-label">Results Returned</div>
        <div class="stat-value" id="ragResultsReturned">0</div>
      </section>
      <section class="card stat-card">
        <div class="stat-label">Candidates Considered</div>
        <div class="stat-value" id="ragCandidatesConsidered">0</div>
      </section>
      <section class="card stat-card">
        <div class="stat-label">Sources Used</div>
        <div class="stat-value" id="ragSourcesUsed">0</div>
      </section>
    </section>

    <section class="results-grid">
      <section class="card intelligence-card">
        <div class="section-header">
          <h2>Response Summary</h2>
          <div class="subtext" id="ragMeta">Idle</div>
        </div>
        <div id="ragSummary" class="stacked-panel">
          <div class="empty-state">Run a search or grounded question.</div>
        </div>
      </section>

      <section class="card intelligence-card">
        <div class="section-header">
          <h2>Results / Sources</h2>
        </div>
        <div id="ragResults" class="stacked-panel">
          <div class="empty-state">No results yet.</div>
        </div>
      </section>
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

  <script src="/static/shell.js"></script>
  <script src="/static/intelligence.js"></script>
</body>
</html>
    """.strip()