from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.app.ui_shell import render_top_shell

router = APIRouter()


@router.get("/planning", response_class=HTMLResponse)
def planning_dashboard() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Planning Detail Dashboard</title>
  <link rel="stylesheet" href="/static/styles.css" />
</head>
<body>
{render_top_shell("/planning")}
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Planning Detail Dashboard</h1>
          <p class="subtext">Wide planning view with queue, selector state, fallback, and operator decision fields.</p>
      </div>
      <div class="header-actions">
        <a class="ghost-link-btn" href="/">Executive Dashboard</a>
        <a class="ghost-link-btn" href="/decisions-ui">Decisions</a>
        <a class="ghost-link-btn" href="/intelligence">Intelligence</a>
      </div>
    </header>

    <section class="card controls-card">
      <div class="dashboard-toolbar dashboard-toolbar--planning">
        <div class="dashboard-toolbar-left dashboard-toolbar-left--planning">
          <div class="control-group dashboard-field dashboard-field--action">
            <label for="planningActionFilter">Action</label>
            <select id="planningActionFilter">
              <option value="">All</option>
              <option value="APPLY">APPLY</option>
              <option value="APPLY_REVIEW_VARIANTS">APPLY_REVIEW_VARIANTS</option>
              <option value="MAYBE_TAILOR">MAYBE_TAILOR</option>
              <option value="SKIP_FOR_NOW">SKIP_FOR_NOW</option>
            </select>
          </div>

          <div class="control-group dashboard-field planning-field--winner-bucket">
            <label for="planningWinnerBucket">Match Strength</label>
            <select id="planningWinnerBucket">
              <option value="">All</option>
              <option value="strong">Excellent match</option>
              <option value="solid">Strong match</option>
              <option value="moderate">Moderate match</option>
              <option value="weak">Weak match</option>
              <option value="filtered_out">No credible match</option>
            </select>
          </div>

          <div class="control-group dashboard-toggle-group planning-toolbar-toggle">
            <label>Undecided only</label>

            <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Planning undecided only">
              <label class="binary-toggle-option">
                <input type="radio" name="planningUndecidedOnlyToggle" value="no" checked />
                <span>No</span>
              </label>
              <label class="binary-toggle-option">
                <input type="radio" name="planningUndecidedOnlyToggle" value="yes" />
                <span>Yes</span>
              </label>
            </div>

            <div class="control-help field-help-wide">
              Yes shows only planning rows that do not have an operator decision yet.
            </div>
          </div>

          <div class="control-group dashboard-field dashboard-field--limit">
            <label for="planningLimitInput">Limit</label>
            <input type="number" id="planningLimitInput" value="50" min="1" max="300" />
          </div>
        </div>

        <div class="dashboard-toolbar-right dashboard-toolbar-right--planning">
          <div class="control-group button-group dashboard-toolbar-actions">
            <button id="planningApplyFiltersBtn">Apply Filters</button>
            <button class="ghost-btn" id="planningClearFiltersBtn">Clear</button>
          </div>
        </div>
      </div>
    </section>

    <section class="stats-grid">
      <section class="card stat-card">
        <div class="stat-label">Jobs Shown</div>
        <div class="stat-value" id="planningJobsShown">0</div>
      </section>
      <section class="card stat-card">
        <div class="stat-label">Active Filters</div>
        <div class="stat-value" id="planningActiveFilters">0</div>
      </section>
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
              <th>Posted At</th>
              <th>Winner Resume</th>
              <th>Winner Score</th>
              <th>Runner-Up Resume</th>
              <th>Runner-Up Score</th>
              <th>Score Gap</th>
              <th>Match Strength</th>
              <th>Review State</th>
              <th>Missing Req Count</th>
              <th>Fallback Best Resume</th>
              <th>Fallback Status</th>
              <th>Operator Decision</th>
              <th>Operator Selected Resume</th>
              <th>Priority Reason</th>
              <th>Tailoring</th>
              <th class="sticky-apply-col">Apply</th>
            </tr>
          </thead>
          <tbody id="planningTableBody"></tbody>
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
    <section class="modal-backdrop hidden" id="resumeChoiceModal">
    <div class="modal-card resume-choice-modal-card">
      <div class="modal-header">
        <div>
          <h3>View Resume Choices</h3>
          <div class="subtext" id="resumeChoiceModalMeta">
            Review the winner and runner-up resumes, preview them, and lock one selection.
          </div>
        </div>
        <button class="ghost-btn modal-close-btn" id="closeResumeChoiceModalBtn" type="button">Close</button>
      </div>

      <div class="resume-choice-modal-body">
        <div class="resume-choice-list-pane">
          <div class="resume-choice-job-grid">
            <div class="info-pair">
              <span class="label">Company</span>
              <span id="resumeChoiceCompany">-</span>
            </div>
            <div class="info-pair">
              <span class="label">Title</span>
              <span id="resumeChoiceTitle">-</span>
            </div>
            <div class="info-pair">
              <span class="label">Planning Action</span>
              <span id="resumeChoiceAction">-</span>
            </div>
            <div class="info-pair">
              <span class="label">Score Gap</span>
              <span id="resumeChoiceGap">-</span>
            </div>
          </div>

          <div class="resume-choice-help">
            Eligible choices are limited to the current top two variants for this row.
          </div>

          <div class="resume-choice-list" id="resumeChoiceList">
            <div class="resume-choice-empty">No resume choices available.</div>
          </div>
        </div>

        <div class="resume-choice-preview-pane">
          <div class="resume-choice-preview-header">
            <div>
              <div class="subtext">Quick preview</div>
              <div class="resume-choice-preview-name" id="resumeChoicePreviewName">Select a resume to preview</div>
            </div>
          </div>

          <div class="resume-choice-preview-frame-wrap">
            <div class="resume-choice-empty" id="resumeChoicePreviewEmpty">
              Select a resume on the left to load its PDF preview.
            </div>

            <iframe
              id="resumeChoicePreviewFrame"
              class="resume-choice-preview-frame hidden"
              title="Resume quick preview"
            ></iframe>

            <div class="resume-choice-loading-overlay hidden" id="resumeChoiceLoadingOverlay">
              <div class="resume-choice-loading-card">
                <div class="loading-spinner"></div>
                <div class="resume-choice-loading-title">Generating tailoring suggestions</div>
                <div class="resume-choice-loading-text">
                  Rebuilding packet and tailoring for the selected resume.
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-actions resume-choice-modal-actions">
        <div class="resume-choice-status" id="resumeChoiceSaveStatus">No resume selected yet.</div>
        <div class="resume-choice-actions-right">
          <button class="ghost-btn" id="resumeChoiceCancelBtn" type="button">Close</button>
          <button id="resumeChoiceSelectBtn" type="button" disabled>Select Resume</button>
        </div>
      </div>
    </div>
  </section>
  <section class="modal-backdrop hidden" id="tailoringModal">
    <div class="modal-card pipeline-modal-card tailoring-modal-card">
      <div class="modal-header">
        <div>
          <h3>Tailoring Detail</h3>
          <div class="subtext" id="tailoringModalMeta">Planning artifact details for the selected job.</div>
        </div>
        <button class="ghost-btn modal-close-btn" id="closeTailoringModalBtn" type="button">Close</button>
      </div>

      <div class="tailoring-provenance-bar">
        <div id="tailoringProviderMeta" class="summary-chip-row tailoring-chip-row">
          <span class="summary-chip chip-muted">Loading provider…</span>
        </div>
        <div id="tailoringSourceChips" class="summary-chip-row tailoring-chip-row">
          <span class="summary-chip chip-muted">Loading provenance…</span>
        </div>
      </div>

      <div class="pipeline-modal-scroll" id="tailoringModalScroll">
        <section class="card tailoring-overview-card">
          <div class="section-header section-header--compact">
            <h3>Overview</h3>
          </div>

          <div class="modal-body tailoring-meta-grid">
            <div class="info-pair tailoring-meta-item">
              <span class="label">Company</span>
              <span id="tailoringModalCompany">-</span>
            </div>

            <div class="info-pair tailoring-meta-item">
              <span class="label">Title</span>
              <span id="tailoringModalTitle">-</span>
            </div>

            <div class="info-pair tailoring-meta-item">
              <span class="label">Tailoring Status</span>
              <span id="tailoringModalStatus" class="tailoring-status-value">-</span>
            </div>

            <div class="info-pair tailoring-meta-item">
              <span class="label">LLM Error</span>
              <span id="tailoringModalError" class="tailoring-error-value">-</span>
            </div>

            <div class="info-pair tailoring-meta-item tailoring-meta-item--path">
              <span class="label">Tailoring Markdown Path</span>
              <span id="tailoringModalMarkdownPath" class="tailoring-path-value">-</span>
            </div>

            <div class="info-pair tailoring-meta-item tailoring-meta-item--path">
              <span class="label">Tailoring LLM JSON Path</span>
              <span id="tailoringModalLlmJsonPath" class="tailoring-path-value">-</span>
            </div>

            <div class="info-pair tailoring-meta-item tailoring-meta-item--path">
              <span class="label">Packet JSON Path</span>
              <span id="tailoringModalPacketPath" class="tailoring-path-value">-</span>
            </div>
          </div>
        </section>

        <section class="card tailoring-primary-card">
          <div class="section-header">
            <h3>Tailoring Markdown</h3>
            <div class="section-header-actions">
              <button
                type="button"
                class="ghost-btn tailoring-copy-btn"
                id="copyTailoringMarkdownBtn"
                title="Copy tailoring markdown"
                aria-label="Copy tailoring markdown"
                disabled
              >
                <span class="tailoring-copy-btn-icon" aria-hidden="true">
                  <svg viewBox="0 0 24 24" focusable="false" aria-hidden="true">
                    <rect x="9" y="9" width="10" height="10" rx="2"></rect>
                    <path d="M15 9V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"></path>
                  </svg>
                </span>
                <span id="copyTailoringMarkdownLabel">Copy</span>
              </button>
            </div>
          </div>
          <div id="tailoringMarkdownContent" class="tailoring-artifact tailoring-artifact--markdown">No artifact loaded.</div>
        </section>

        <details class="card tailoring-accordion">
          <summary>LLM Tailoring JSON</summary>
          <pre id="tailoringLlmJsonContent" class="tailoring-artifact tailoring-artifact--code">No artifact loaded.</pre>
        </details>

        <details class="card tailoring-accordion">
          <summary>Packet JSON</summary>
          <pre id="tailoringPacketJsonContent" class="tailoring-artifact tailoring-artifact--code">No artifact loaded.</pre>
        </details>
      </div>

      <div class="modal-actions">
        <button type="button" class="ghost-btn" id="closeTailoringFooterBtn">Close</button>
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

  <script src="/static/shell.js"></script>
  <script src="/static/planning.js"></script>
</body>
</html>
    """.strip()