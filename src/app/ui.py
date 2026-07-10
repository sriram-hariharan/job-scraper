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
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=pipeline_options_controls_v4" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=pipeline_options_controls_v4" />
</head>
<body>
  {render_top_shell("/")}
  <div class="page">
        <header class="page-header">
          <div class="page-header-main">
            <div class="executive-title-row">
              <h1>Executive Queue</h1>
            </div>

            <p class="subtext">High-signal operator dashboard for direct apply and review decisions.</p>
          </div>

          <div class="header-actions">
            <button class="ghost-btn" id="refreshStatusBtn" type="button">Refresh Status</button>
            <button id="runPipelineBtn" type="button">Run Live Pipeline</button>
          </div>
        </header>
    <section class="stats-grid">
      <section class="card stat-card">
        <div class="stat-label">Queue Rows</div>
        <div class="stat-value" id="statQueueRows">-</div>
      </section>
      <section class="card stat-card">
        <div class="stat-label">Next Steps</div>
        <div class="stat-value" id="statDecisionRows">-</div>
      </section>
      <section class="card stat-card">
        <div class="stat-label">Undecided Job Reviews</div>
        <div class="stat-value" id="statUndecidedApplyReview">-</div>
      </section>
      <section class="card stat-card">
        <div class="stat-label">Undecided Maybe Tailor</div>
        <div class="stat-value" id="statUndecidedMaybeTailor">-</div>
      </section>
    </section>

    <section class="card controls-card">
      <div class="dashboard-toolbar dashboard-toolbar--executive">
        <div class="dashboard-toolbar-left dashboard-toolbar-left--executive">
          <div class="control-group dashboard-field dashboard-field--action">
            <label>Action</label>
            <div class="multi-select" id="actionFilter" data-placeholder="All">
              <button type="button" class="multi-select-trigger" aria-haspopup="menu" aria-expanded="false">
                <span class="multi-select-trigger-label">All</span>
                <span class="multi-select-trigger-icon">▾</span>
              </button>

              <div class="multi-select-menu" role="menu" hidden>
                <button type="button" class="multi-select-option" data-value="APPLY" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">Ready for review</span>
                </button>
                <button type="button" class="multi-select-option" data-value="APPLY_REVIEW_VARIANTS" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">Review resume choice</span>
                </button>
                <button type="button" class="multi-select-option" data-value="MAYBE_TAILOR" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">Tailor first</span>
                </button>
                <button type="button" class="multi-select-option" data-value="SKIP_FOR_NOW" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">Review later</span>
                </button>
              </div>
            </div>
          </div>

          <div class="control-group dashboard-field dashboard-field--limit">
            <label for="limitInput">Limit</label>
            <input type="number" id="limitInput" value="15" min="1" max="200" />
          </div>

          <div class="control-group dashboard-toggle-group executive-toolbar-toggle">
            <label>Undecided only</label>

            <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Undecided only">
              <label class="binary-toggle-option">
                <input type="radio" name="executiveUndecidedOnly" value="no" checked />
                <span>No</span>
              </label>
              <label class="binary-toggle-option">
                <input type="radio" name="executiveUndecidedOnly" value="yes" />
                <span>Yes</span>
              </label>
            </div>

            <div class="control-help field-help-wide">
              Yes shows only browse rows that do not have an operator decision yet.
            </div>
          </div>
        </div>

        <div class="dashboard-toolbar-right dashboard-toolbar-right--executive">
          <div class="control-group button-group dashboard-toolbar-actions">
            <button id="applyFiltersBtn">Apply Filters</button>
            <button class="ghost-btn" id="clearFiltersBtn">Clear</button>
          </div>
        </div>
      </div>
    </section>

    <div class="subtext pipeline-run-meta" id="pipelineRunMeta">Pipeline idle.</div>

    <section class="card table-card">
      <div class="section-header application-table-header">
        <div class="application-table-title-row">
          <h2>Queue Table</h2>
          <div class="executive-view-mode-row executive-view-mode-row--table">
            <span class="executive-view-mode-label">View mode</span>
            <div class="binary-toggle binary-toggle--compact binary-toggle--small" role="radiogroup" aria-label="Executive view mode">
              <label class="binary-toggle-option">
                <input type="radio" name="executiveViewMode" value="detailed" checked />
                <span>Detailed</span>
              </label>
              <label class="binary-toggle-option">
                <input type="radio" name="executiveViewMode" value="simple" />
                <span>Simple</span>
              </label>
            </div>
          </div>
        </div>
        <div class="application-table-header-right">
          <div class="subtext" id="tableMeta">Loading...</div>
          <div class="application-pagination-inline" id="queuePaginationInline">
            <div class="application-pagination-meta" id="queuePaginationMeta">Loading...</div>
            <div class="application-pagination-actions" id="queuePaginationActions"></div>
          </div>
        </div>
      </div>

      <div class="table-wrap">
        <table id="queueTable" class="resizable-table">
          <colgroup id="queueTableColgroup">
            <col data-col-key="queue_rank" style="width: 110px;" />
            <col data-col-key="job_title" style="width: 260px;" />
            <col data-col-key="job_company" style="width: 180px;" />
            <col data-col-key="job_location" style="width: 170px;" />
            <col data-col-key="posted_at" style="width: 150px;" />
            <col data-col-key="recommendation" style="width: 240px;" />
            <col data-col-key="packet_status" style="width: 150px;" />
            <col data-col-key="winner_score" style="width: 120px;" />
            <col data-col-key="selected_resume" style="width: 240px;" />
            <col data-col-key="runner_up_resume" style="width: 220px;" />
            <col data-col-key="score_gap" style="width: 110px;" />
            <col data-col-key="missing_requirement_count" style="width: 140px;" />
            <col data-col-key="next_step" style="width: 170px;" />
            <col data-col-key="queue_priority_reason" style="width: 190px;" />
            <col class="table-static-col" data-static-col-key="apply" style="width: 140px;" />
          </colgroup>

          <thead>
            <tr id="queueTableHeaderRow">
              <th data-col-key="queue_rank">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Rank</span>
                </div>
                <span class="col-resize-handle" data-resize-key="queue_rank"></span>
              </th>
              <th data-col-key="job_title">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Job title</span>
                </div>
                <span class="col-resize-handle" data-resize-key="job_title"></span>
              </th>
              <th data-col-key="job_company">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Company</span>
                </div>
                <span class="col-resize-handle" data-resize-key="job_company"></span>
              </th>
              <th data-col-key="job_location">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Location</span>
                </div>
                <span class="col-resize-handle" data-resize-key="job_location"></span>
              </th>
              <th data-col-key="posted_at">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Posted at</span>
                </div>
                <span class="col-resize-handle" data-resize-key="posted_at"></span>
              </th>
              <th data-col-key="recommendation">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Recommendation</span>
                </div>
                <span class="col-resize-handle" data-resize-key="recommendation"></span>
              </th>
              <th data-col-key="packet_status">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Packet</span>
                  <span class="packet-info-icon" title="A packet is a review bundle for this job. It includes the job, selected resume, match signals, gaps, and tailoring guidance. It does not apply to the job." aria-label="A packet is a review bundle for this job. It includes the job, selected resume, match signals, gaps, and tailoring guidance. It does not apply to the job.">ⓘ</span>
                </div>
                <span class="col-resize-handle" data-resize-key="packet_status"></span>
              </th>
              <th data-col-key="winner_score">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Match</span>
                </div>
                <span class="col-resize-handle" data-resize-key="winner_score"></span>
              </th>
              <th data-col-key="selected_resume">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Selected Resume</span>
                </div>
                <span class="col-resize-handle" data-resize-key="selected_resume"></span>
              </th>
              <th data-col-key="runner_up_resume">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Runner-up resume</span>
                </div>
                <span class="col-resize-handle" data-resize-key="runner_up_resume"></span>
              </th>
              <th data-col-key="score_gap">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Score gap</span>
                </div>
                <span class="col-resize-handle" data-resize-key="score_gap"></span>
              </th>
              <th data-col-key="missing_requirement_count">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Missing req count</span>
                </div>
                <span class="col-resize-handle" data-resize-key="missing_requirement_count"></span>
              </th>
              <th data-col-key="next_step">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Next step</span>
                </div>
                <span class="col-resize-handle" data-resize-key="next_step"></span>
              </th>
              <th data-col-key="queue_priority_reason">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Priority reason</span>
                </div>
                <span class="col-resize-handle" data-resize-key="queue_priority_reason"></span>
              </th>
              <th class="sticky-apply-col apply-col-fixed">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Review</span>
                </div>
              </th>
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
      </div>

      <div class="pipeline-modal-scroll">
        <div class="pipeline-option-sections compact-option-sections">
          <div class="pipeline-option-section">
            <div class="pipeline-option-section-header">
              <div class="pipeline-option-title">Run size</div>
            </div>

            <div class="pipeline-form-grid pipeline-form-grid--compact">
              <div class="control-group pipeline-limit-group">
                <label for="pipelineJobLimitInput">
                  Job limit
                  <span class="packet-info-icon pipeline-help-icon" title="Maximum jobs allowed into this run." aria-label="Maximum jobs allowed into this run.">?</span>
                </label>
            <input type="number" id="pipelineJobLimitInput" value="50" min="1" max="500" />

            <div class="pipeline-inline-helper">
              <span class="pipeline-inline-helper-label">Quick presets</span>
              <div class="pipeline-chip-row pipeline-chip-row--compact">
                <button type="button" class="ghost-btn pipeline-chip-btn" data-job-limit-preset="25">25</button>
                <button type="button" class="ghost-btn pipeline-chip-btn" data-job-limit-preset="50">50</button>
                <button type="button" class="ghost-btn pipeline-chip-btn" data-job-limit-preset="100">100</button>
                <button type="button" class="ghost-btn pipeline-chip-btn" data-job-limit-preset="200">200</button>
              </div>
            </div>

              </div>

              <div class="control-group">
                <label for="pipelineJobPacketLimitInput">
                  Packet limit
                  <span class="packet-info-icon pipeline-help-icon" title="Maximum detailed planning packets to build. 0 means all selected jobs." aria-label="Maximum detailed planning packets to build. 0 means all selected jobs.">?</span>
                </label>
                <input type="number" id="pipelineJobPacketLimitInput" value="0" min="0" max="500" />
              </div>

              <div class="control-group pipeline-toggle-group pipeline-toggle-group--inline">
                <label>
                  Rerun seen jobs
                  <span class="packet-info-icon pipeline-help-icon" title="Include jobs that were already seen before." aria-label="Include jobs that were already seen before.">?</span>
                </label>
                <div class="binary-toggle" role="radiogroup" aria-label="Rerun seen jobs">
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineDeleteSeenData" value="no" checked />
                    <span>No</span>
                  </label>
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineDeleteSeenData" value="yes" />
                    <span>Yes</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <div class="pipeline-option-section">
            <div class="pipeline-option-section-header">
              <div class="pipeline-option-title">Run mode</div>
            </div>

            <div class="pipeline-toggle-grid pipeline-toggle-grid--compact">
              <div class="pipeline-toggle-item pipeline-toggle-item--mode">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">
                    Scan + Plan
                    <span class="packet-info-icon pipeline-help-icon" title="Scrape jobs, score them, and build planning outputs." aria-label="Scrape jobs, score them, and build planning outputs.">?</span>
                  </div>
                </div>
                <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Run mode">
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelinePlanningOnly" value="no" checked />
                    <span>Scan + Plan</span>
                  </label>
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelinePlanningOnly" value="yes" />
                    <span>Plan only</span>
                  </label>
                </div>
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name pipeline-toggle-name--secondary">
                    Plan only
                    <span class="packet-info-icon pipeline-help-icon" title="Skip scraping and rebuild planning from existing jobs." aria-label="Skip scraping and rebuild planning from existing jobs.">?</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="pipeline-option-section">
            <div class="pipeline-option-section-header">
              <div class="pipeline-option-title">AI planning</div>
            </div>

            <div class="pipeline-toggle-grid pipeline-toggle-grid--compact">
              <div class="pipeline-toggle-item">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">
                    AI review
                    <span class="packet-info-icon pipeline-help-icon" title="Use AI to review planning decisions and borderline fits. This does not tailor resumes." aria-label="Use AI to review planning decisions and borderline fits. This does not tailor resumes.">?</span>
                  </div>
                </div>
                <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="AI review">
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineGenerateLlmAdjudication" value="no" />
                    <span>No</span>
                  </label>
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineGenerateLlmAdjudication" value="yes" checked />
                    <span>Yes</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <div class="pipeline-option-section pipeline-option-section--advanced">
            <div class="pipeline-option-section-header">
              <div class="pipeline-option-title">Advanced</div>
            </div>

            <div class="pipeline-toggle-grid pipeline-toggle-grid--compact">
              <div class="pipeline-toggle-item">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">
                    Backup ranking
                    <span class="packet-info-icon pipeline-help-icon" title="Use fallback ranking when normal ranking signals are incomplete." aria-label="Use fallback ranking when normal ranking signals are incomplete.">?</span>
                  </div>
                </div>
                <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Backup ranking">
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineGenerateLlmFallback" value="no" checked />
                    <span>No</span>
                  </label>
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineGenerateLlmFallback" value="yes" />
                    <span>Yes</span>
                  </label>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-actions pipeline-modal-actions">
        <button type="button" class="ghost-btn" id="cancelPipelineConfigBtn">Cancel</button>
        <button type="button" id="openPipelineConfirmBtn">Continue</button>
      </div>
    </div>
  </section>

  <section class="modal-backdrop hidden" id="pipelineConfirmModal">
    <div class="modal-card pipeline-confirm-card">
      <div class="modal-header pipeline-confirm-header">
        <div>
          <h3>Confirm pipeline run</h3>
          <div class="subtext">Final review before launching the live pipeline.</div>
        </div>
        <button class="ghost-btn modal-close-btn" id="closePipelineConfirmModalBtn" type="button">Close</button>
      </div>

      <div class="pipeline-confirm-scroll">
        <div class="confirm-summary-block" id="pipelineConfirmSummary"></div>
      </div>

      <div class="modal-actions pipeline-confirm-actions">
        <button type="button" class="ghost-btn" id="backToPipelineConfigBtn">Back</button>
        <button type="button" id="confirmPipelineRunBtn">Run pipeline</button>
      </div>
    </div>
  </section>

  <section class="page-loading-overlay hidden" id="pageLoadingOverlay">
    <div class="page-loading-card pipeline-loading-card" id="pipelineOverlayCard">
      <div class="pipeline-overlay-loading" id="pipelineOverlayLoading">
        <div class="loading-spinner"></div>
        <div class="page-loading-title" id="pageLoadingTitle">Running live pipeline...</div>
        <div class="page-loading-text" id="pageLoadingText">Preparing pipeline run.</div>

        <div class="pipeline-loading-meta" id="pipelineLoadingMeta"></div>
        <div class="pipeline-loading-counts" id="pipelineLoadingCounts"></div>
        <div class="pipeline-stage-stepper" id="pipelineStageStepper"></div>
      </div>

      <div class="pipeline-overlay-success hidden" id="pipelineOverlaySuccess">
        <div class="pipeline-success-visual">
          <img
            id="pipelineSuccessGif"
            class="pipeline-success-gif"
            src="/static/media/success_check.gif"
            data-src="/static/media/success_check.gif"
            alt="Pipeline completed successfully"
          />
          <div class="pipeline-success-static-check hidden" id="pipelineSuccessStaticCheck">✓</div>
        </div>

        <div class="page-loading-title pipeline-success-title" id="pipelineSuccessTitle">
          Pipeline completed
        </div>
        <div class="page-loading-text pipeline-success-text" id="pipelineSuccessText">
          Run finished successfully.
        </div>

        <div class="pipeline-success-summary" id="pipelineSuccessSummary"></div>

        <div class="modal-actions pipeline-success-actions">
          <button type="button" id="pipelineSuccessOkBtn">OK</button>
        </div>
      </div>

      <div class="pipeline-overlay-failure hidden" id="pipelineOverlayFailure">
        <div class="pipeline-success-visual">
          <img
            id="pipelineFailureGif"
            class="pipeline-success-gif"
            src="/static/media/failed.gif"
            data-src="/static/media/failed.gif"
            alt="Pipeline failed"
          />
          <div
            class="pipeline-success-static-check hidden"
            id="pipelineFailureStaticCross"
          >
            ✕
          </div>
        </div>

        <div class="page-loading-title pipeline-success-title" id="pipelineFailureTitle">
          Pipeline failed
        </div>
        <div class="page-loading-text pipeline-success-text" id="pipelineFailureText">
          Run failed.
        </div>

        <div class="pipeline-success-summary" id="pipelineFailureSummary"></div>
        <div class="pipeline-success-summary" id="pipelineFailureReason"></div>

        <div class="modal-actions pipeline-success-actions">
          <button type="button" id="pipelineFailureOkBtn">OK</button>
        </div>
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
  <script src="/static/shell.js?v=role_onboarding_r6"></script>
  <script src="/static/app.js?v=pipeline_options_controls_v4"></script>
  </body>
</html>
    """.strip()

@router.get("/scheduler", response_class=HTMLResponse)
def scheduler_dashboard() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Scheduler Ops Dashboard</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=ui_redesign_v44_shell_menu_clearance" />
</head>
<body>
  {render_top_shell("/scheduler")}
  <div class="page scheduler-page">
    <header class="page-header">
      <div class="page-header-main">
        <h1>Scheduler Ops</h1>
        <p class="subtext">Operational view for scheduler health, persistence status, and recent runs.</p>
      </div>

    </header>

    <div class="subtext pipeline-run-meta" id="schedulerOpsMeta" hidden aria-hidden="true">
      Loading scheduler summary...
    </div>

    <section class="card table-card scheduler-table-card">
      <div class="scheduler-table-tabs">
        <div class="scheduler-tab-row" role="tablist" aria-label="Scheduler views">
          <button type="button" class="scheduler-tab-btn active" data-tab="contract" role="tab" aria-selected="true">
            Contract Health
          </button>
          <button type="button" class="scheduler-tab-btn" data-tab="jsonl" role="tab" aria-selected="false">
            JSONL Rows
          </button>
          <button type="button" class="scheduler-tab-btn" data-tab="postgres" role="tab" aria-selected="false">
            Postgres Rows
          </button>
          <button type="button" class="scheduler-tab-btn" data-tab="latest" role="tab" aria-selected="false">
            Latest Runs by Job
          </button>
        </div>
      </div>

      <div class="scheduler-table-header">
        <div class="scheduler-table-title-wrap">
          <h2 id="schedulerTableTitle">Contract Health</h2>
          <div class="subtext" id="schedulerTableSubtitle">Artifact drift and scheduler contract checks.</div>
        </div>
        <div class="scheduler-table-header-right">
          <button class="ghost-btn" id="refreshSchedulerSummaryBtn" type="button">Refresh</button>
        </div>
      </div>

      <div class="table-wrap scheduler-attached-table-wrap">
        <table id="schedulerTable">
          <thead id="schedulerTableHead">
            <tr>
              <th>Check</th>
              <th>Value</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id="schedulerTableBody">
            <tr><td colspan="3" class="empty-state">Loading...</td></tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=role_onboarding_r6"></script>
  <script>
    (function () {{
      const summaryUrl = "/scheduler/summary?limit=25";

      const metaEl = document.getElementById("schedulerOpsMeta");
      const refreshBtn = document.getElementById("refreshSchedulerSummaryBtn");
      const tableTitleEl = document.getElementById("schedulerTableTitle");
      const tableSubtitleEl = document.getElementById("schedulerTableSubtitle");
      const tableHeadEl = document.getElementById("schedulerTableHead");
      const tableBodyEl = document.getElementById("schedulerTableBody");

      const tabButtons = Array.from(document.querySelectorAll(".scheduler-tab-btn"));

      let currentPayload = null;
      let activeTab = "contract";

      if (!metaEl || !refreshBtn || !tableTitleEl || !tableSubtitleEl || !tableHeadEl || !tableBodyEl || !tabButtons.length) {{
        return;
      }}

      function escapeHtml(value) {{
        return String(value ?? "")
          .replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/"/g, "&quot;")
          .replace(/'/g, "&#39;");
      }}

      const DATE_ONLY_FORMATTER = new Intl.DateTimeFormat(undefined, {{
        month: "short",
        day: "numeric",
        year: "numeric",
      }});

      const TIME_ONLY_FORMATTER = new Intl.DateTimeFormat(undefined, {{
        hour: "numeric",
        minute: "2-digit",
        timeZoneName: "short",
      }});

      function buildDateTimeCellHtml(value) {{
        if (!value) {{
          return "-";
        }}

        const date = new Date(value);
        if (Number.isNaN(date.getTime())) {{
          return escapeHtml(String(value));
        }}

        return `
          <div class="datetime-cell">
            <div class="datetime-cell-date">${{escapeHtml(DATE_ONLY_FORMATTER.format(date))}}</div>
            <div class="datetime-cell-time">${{escapeHtml(TIME_ONLY_FORMATTER.format(date))}}</div>
          </div>
        `;
      }}

      function statusBadgeClass(status) {{
        const normalized = String(status || "").toLowerCase();
        if (normalized === "succeeded") return "scheduler-run-badge scheduler-run-badge--success";
        if (normalized === "failed") return "scheduler-run-badge scheduler-run-badge--danger";
        return "scheduler-run-badge scheduler-run-badge--muted";
      }}

      function yesNoBadgeClass(value) {{
        return value
          ? "scheduler-run-badge scheduler-run-badge--success"
          : "scheduler-run-badge scheduler-run-badge--danger";
      }}

      function renderEmptyRow(colspan, message) {{
        return `<tr><td colspan="${{colspan}}" class="empty-state">${{escapeHtml(message)}}</td></tr>`;
      }}

      function renderContractRows(contractHealth) {{
        const checks = contractHealth?.checks || {{}};
        const overall = Boolean(contractHealth?.all_checks_pass);

        const rows = [
          {{
            label: "Overall Contract Health",
            value: overall ? "Healthy" : "Drift",
            ok: overall,
          }},
          {{
            label: "Seed SQL matches artifact",
            value: checks.seed_sql_matches_artifact ? "Yes" : "No",
            ok: Boolean(checks.seed_sql_matches_artifact),
          }},
          {{
            label: "Init SQL matches artifact",
            value: checks.init_sql_matches_artifact ? "Yes" : "No",
            ok: Boolean(checks.init_sql_matches_artifact),
          }},
        ];

        return rows.map((row) => {{
          return `
            <tr>
              <td>${{escapeHtml(row.label)}}</td>
              <td>${{escapeHtml(row.value)}}</td>
              <td><span class="${{yesNoBadgeClass(row.ok)}}">${{row.ok ? "OK" : "Issue"}}</span></td>
            </tr>
          `;
        }}).join("");
      }}

      function renderRunRows(rows) {{
        if (!Array.isArray(rows) || rows.length === 0) {{
          return renderEmptyRow(6, "No rows found.");
        }}

        return rows.map((row) => {{
          return `
            <tr>
              <td>${{escapeHtml(row.run_id || "-")}}</td>
              <td>${{escapeHtml(row.job_name || "-")}}</td>
              <td><span class="${{statusBadgeClass(row.status)}}">${{escapeHtml(row.status || "-")}}</span></td>
              <td>${{escapeHtml(row.return_code ?? "-")}}</td>
              <td>${{buildDateTimeCellHtml(row.started_at)}}</td>
              <td>${{buildDateTimeCellHtml(row.finished_at)}}</td>
            </tr>
          `;
        }}).join("");
      }}

      const tabConfig = {{
        contract: {{
          title: "Contract Health",
          subtitle: "Artifact drift and scheduler contract checks.",
          columns: ["Check", "Value", "Status"],
          renderRows(payload) {{
            return renderContractRows(payload?.contract_health || {{}});
          }},
        }},
        jsonl: {{
          title: "JSONL Rows",
          subtitle: "Recent scheduler runs from the JSONL audit trail.",
          columns: ["Run ID", "Job", "Status", "Return Code", "Started", "Finished"],
          renderRows(payload) {{
            return renderRunRows(payload?.recent_jsonl_runs || []);
          }},
        }},
        postgres: {{
          title: "Postgres Rows",
          subtitle: "Recent scheduler runs currently mirrored into Postgres.",
          columns: ["Run ID", "Job", "Status", "Return Code", "Started", "Finished"],
          renderRows(payload) {{
            return renderRunRows(payload?.recent_postgres_runs || []);
          }},
        }},
        latest: {{
          title: "Latest Runs by Job",
          subtitle: "Most recent run per scheduler job.",
          columns: ["Run ID", "Job", "Status", "Return Code", "Started", "Finished"],
          renderRows(payload) {{
            return renderRunRows(payload?.latest_runs_by_job || []);
          }},
        }},
      }};

      function activateTab(tabName) {{
        if (!tabConfig[tabName]) {{
          return;
        }}

        activeTab = tabName;

        tabButtons.forEach((btn) => {{
          const isActive = btn.dataset.tab === tabName;
          btn.classList.toggle("active", isActive);
          btn.setAttribute("aria-selected", isActive ? "true" : "false");
        }});

        renderActiveTable();
      }}

      function renderActiveTable() {{
        const config = tabConfig[activeTab];
        if (!config) {{
          return;
        }}

        tableTitleEl.textContent = config.title;
        tableSubtitleEl.textContent = config.subtitle;

        tableHeadEl.innerHTML = `
          <tr>
            ${{config.columns.map((column) => `<th>${{escapeHtml(column)}}</th>`).join("")}}
          </tr>
        `;

        if (!currentPayload) {{
          tableBodyEl.innerHTML = renderEmptyRow(config.columns.length, "Loading...");
          return;
        }}

        tableBodyEl.innerHTML = config.renderRows(currentPayload);
      }}

      async function loadSchedulerSummary() {{
        metaEl.textContent = "Loading scheduler summary...";
        refreshBtn.disabled = true;

        try {{
          const response = await fetch(summaryUrl, {{ cache: "no-store" }});
          const payload = await response.json();

          if (!response.ok) {{
            throw new Error(payload.detail || "Failed to load scheduler summary.");
          }}

          currentPayload = payload;

          const countsMatch = Boolean(payload?.history?.count_matches);
          const countsMatchBadge = `<span class="${{yesNoBadgeClass(countsMatch)}}">${{countsMatch ? "Yes" : "No"}}</span>`;

          metaEl.innerHTML =
            `Job defs: ${{payload?.postgres_summary?.job_definition_count ?? 0}} · ` +
            `Active jobs: ${{payload?.postgres_summary?.active_job_count ?? 0}} · ` +
            `Success: ${{payload?.postgres_summary?.success_count ?? 0}} · ` +
            `Failure: ${{payload?.postgres_summary?.failure_count ?? 0}} · ` +
            `Counts Match: ${{countsMatchBadge}}`;

          renderActiveTable();
        }} catch (error) {{
          currentPayload = null;
          renderActiveTable();
          metaEl.textContent = error?.message || "Failed to load scheduler summary.";
        }} finally {{
          refreshBtn.disabled = false;
        }}
      }}

      tabButtons.forEach((btn) => {{
        btn.addEventListener("click", () => activateTab(btn.dataset.tab));
      }});

      refreshBtn.addEventListener("click", loadSchedulerSummary);

      activateTab("contract");
      loadSchedulerSummary();
    }})();
  </script>
</body>
</html>
    """.strip()
