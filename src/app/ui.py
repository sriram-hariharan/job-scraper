from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.app.ui_shell import render_top_shell

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def executive_dashboard() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Executive Queue Dashboard</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
  {render_top_shell("/")}
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Executive Queue</h1>
        <p class="subtext">High-signal operator dashboard for direct apply and review decisions.</p>
      </div>
      <div class="header-actions">
        <a class="ghost-link-btn" href="/planning">Planning Detail</a>
        <a class="ghost-link-btn" href="/decisions-ui">Decisions</a>
        <a class="ghost-link-btn" href="/intelligence">Intelligence</a>
        <button class="ghost-btn" id="refreshStatusBtn">Refresh Status</button>
        <button id="runPipelineBtn">Run Live Pipeline</button>
      </div>
    </header>
    <div class="subtext" id="pipelineRunMeta">Pipeline idle.</div>
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
  
  <section class="modal-backdrop hidden" id="pipelineConfigModal">
  <div class="modal-card pipeline-modal-card">
    <div class="modal-header">
      <div>
        <h3>Run live pipeline</h3>
        <div class="subtext">Choose limits and options before starting the run.</div>
      </div>
      <button class="ghost-btn modal-close-btn" id="closePipelineConfigModalBtn" type="button">Close</button>
    </div>

    <div class="pipeline-form-grid">
      <div class="control-group">
        <label for="pipelineJobLimitInput">Job limit</label>
        <input type="number" id="pipelineJobLimitInput" value="50" min="1" max="500" />
      </div>

      <div class="control-group">
        <label for="pipelineJobPacketLimitInput">Job packet limit</label>
        <input type="number" id="pipelineJobPacketLimitInput" value="0" min="0" max="500" />
      </div>

      <div class="control-group wide-control">
        <label for="pipelineOutputDirInput">Output directory</label>
        <input type="text" id="pipelineOutputDirInput" value="outputs/application_planning" />
      </div>

      <div class="control-group wide-control">
        <label for="pipelineLogPathInput">Log path</label>
        <input type="text" id="pipelineLogPathInput" value="outputs/application_planning/live_pipeline_run.log" />
      </div>
    </div>

    <div class="pipeline-option-sections">
      <div class="pipeline-option-section">
        <div class="pipeline-option-title">LLM Actions</div>
        <div class="pipeline-checkbox-grid">
          <label><input type="checkbox" data-pipeline-llm-action value="APPLY" checked /> APPLY</label>
          <label><input type="checkbox" data-pipeline-llm-action value="APPLY_REVIEW_VARIANTS" checked /> APPLY_REVIEW_VARIANTS</label>
          <label><input type="checkbox" data-pipeline-llm-action value="MAYBE_TAILOR" /> MAYBE_TAILOR</label>
          <label><input type="checkbox" data-pipeline-llm-action value="SKIP_FOR_NOW" /> SKIP_FOR_NOW</label>
        </div>
      </div>

      <div class="pipeline-option-section">
        <div class="pipeline-option-title">Run Options</div>
        <div class="pipeline-checkbox-grid">
          <label><input type="checkbox" id="pipelinePlanningOnlyCheckbox" /> Planning only</label>
          <label><input type="checkbox" id="pipelineGenerateTailoringCheckbox" /> Generate tailoring</label>
          <label><input type="checkbox" id="pipelineGenerateLlmTailoringCheckbox" /> Generate LLM tailoring</label>
          <label><input type="checkbox" id="pipelineRefreshLlmTailoringCheckbox" /> Refresh LLM tailoring</label>
          <label><input type="checkbox" id="pipelineGenerateLlmFallbackCheckbox" /> Generate LLM fallback</label>
        </div>
      </div>
    </div>

    <div class="modal-actions">
      <button type="button" class="ghost-btn" id="cancelPipelineConfigBtn">Cancel</button>
      <button type="button" id="openPipelineConfirmBtn">Continue</button>
    </div>
  </div>
</section>

<section class="modal-backdrop hidden" id="pipelineConfirmModal">
  <div class="modal-card">
    <div class="modal-header">
      <div>
        <h3>Confirm pipeline run</h3>
        <div class="subtext">Review the selected options before starting.</div>
      </div>
      <button class="ghost-btn modal-close-btn" id="closePipelineConfirmModalBtn" type="button">Close</button>
    </div>

    <div class="confirm-summary-block" id="pipelineConfirmSummary"></div>

    <div class="modal-actions">
      <button type="button" class="ghost-btn" id="backToPipelineConfigBtn">Back</button>
      <button type="button" id="confirmPipelineRunBtn">Run</button>
    </div>
  </div>
</section>

<section class="page-loading-overlay hidden" id="pageLoadingOverlay">
  <div class="page-loading-card">
    <div class="loading-spinner"></div>
    <div class="page-loading-title" id="pageLoadingTitle">Running live pipeline...</div>
    <div class="page-loading-text" id="pageLoadingText">Preparing pipeline run.</div>
  </div>
</section>

  <script src="/static/shell.js"></script>
  <script src="/static/app.js"></script>
</body>
</html>
    """.strip()