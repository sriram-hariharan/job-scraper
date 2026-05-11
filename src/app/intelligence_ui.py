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
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=ui_redesign_v22" />
</head>
<body>
{render_top_shell("/intelligence")}
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Job Intelligence Dashboard</h1>
        <p class="subtext">Search the job corpus and ask grounded questions over retrieved jobs.</p>
      </div>
    </header>

    <section class="card controls-card">
      <div class="dashboard-toolbar dashboard-toolbar--intelligence">
        <div class="dashboard-toolbar-left dashboard-toolbar-left--intelligence">
          <div class="control-group dashboard-field intelligence-field--mode">
            <label for="ragModeSelect">Mode</label>
            <select id="ragModeSelect">
              <option value="search">Search Jobs</option>
              <option value="answer">Answer Question</option>
            </select>
          </div>

          <div class="control-group dashboard-field intelligence-field--topk">
            <label for="ragTopKInput">Results to Return</label>
            <input type="number" id="ragTopKInput" value="5" min="1" max="20" />
            <div class="control-help">How many final jobs or sources to show.</div>
          </div>

          <div class="control-group dashboard-field intelligence-field--fetchk">
            <label for="ragFetchKInput">Candidates to Scan</label>
            <input type="number" id="ragFetchKInput" value="15" min="1" max="50" />
            <div class="control-help">How many jobs to search before narrowing to the best matches.</div>
          </div>

          <div class="control-group dashboard-toggle-group intelligence-toolbar-toggle">
            <label>Include diagnostics</label>

            <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Include diagnostics">
              <label class="binary-toggle-option">
                <input type="radio" name="ragDiagnosticsToggle" value="no" checked />
                <span>No</span>
              </label>
              <label class="binary-toggle-option">
                <input type="radio" name="ragDiagnosticsToggle" value="yes" />
                <span>Yes</span>
              </label>
            </div>

            <div class="control-help field-help-wide">
              Yes includes extra backend diagnostics for Answer Question mode. Search Jobs ignores this setting.
            </div>
          </div>
        </div>
      </div>

      <div class="intelligence-query-row">
        <div class="control-group intelligence-request-inline-group">
          <label for="ragRequestInput">Search or question</label>
          <input
            type="text"
            id="ragRequestInput"
            placeholder="Search jobs by keywords, or ask a grounded question about the current job corpus."
          />
          <div class="control-help field-help-wide">
            Search Jobs uses this as the request text for retrieval. Answer Question uses it as the grounded prompt.
          </div>
        </div>

        <div class="control-group button-group dashboard-toolbar-actions intelligence-query-actions">
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
  <script src="/static/intelligence.js"></script>
</body>
</html>
    """.strip()