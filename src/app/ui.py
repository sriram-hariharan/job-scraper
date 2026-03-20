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

    <div class="subtext pipeline-run-meta" id="pipelineRunMeta">Pipeline idle.</div>

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
      <div class="dashboard-toolbar dashboard-toolbar--executive">
        <div class="dashboard-toolbar-left dashboard-toolbar-left--executive">
          <div class="control-group dashboard-field dashboard-field--action">
            <label for="actionFilter">Action</label>
            <select id="actionFilter">
              <option value="">All</option>
              <option value="APPLY">APPLY</option>
              <option value="APPLY_REVIEW_VARIANTS">APPLY_REVIEW_VARIANTS</option>
              <option value="MAYBE_TAILOR">MAYBE_TAILOR</option>
              <option value="SKIP_FOR_NOW">SKIP_FOR_NOW</option>
            </select>
          </div>

          <div class="control-group dashboard-field dashboard-field--limit">
            <label for="limitInput">Limit</label>
            <input type="number" id="limitInput" value="25" min="1" max="200" />
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

      <div class="controls-row quick-view-row quick-view-row--executive">
        <button class="ghost-btn quick-view-btn" data-view="direct_apply_pending">Direct Apply Pending</button>
        <button class="ghost-btn quick-view-btn" data-view="undecided_apply_review">Variant Review Pending</button>
        <button class="ghost-btn quick-view-btn" data-view="undecided_maybe_tailor">Tailor Pending</button>
        <button class="ghost-btn quick-view-btn" data-mode="applied_jobs">Applied Jobs</button>
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

      <div class="pipeline-modal-scroll">
        <div class="pipeline-form-grid">
          <div class="control-group pipeline-limit-group">
            <label for="pipelineJobLimitInput">Job limit</label>
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

            <div class="control-help field-help-wide">How many jobs can enter this run.</div>
          </div>

          <div class="control-group">
            <label for="pipelineJobPacketLimitInput">Job packet limit</label>
            <input type="number" id="pipelineJobPacketLimitInput" value="0" min="0" max="500" />
            <div class="control-help field-help-wide">How many detailed planning packets to build. 0 means all selected jobs.</div>
          </div>

          <div class="control-group wide-control pipeline-path-field">
            <label for="pipelineOutputDirInput">Output directory</label>
            <input type="text" id="pipelineOutputDirInput" value="outputs/application_planning" />
            <div class="control-help field-help-wide">Where pipeline outputs and planning artifacts are written.</div>
          </div>

          <div class="control-group wide-control pipeline-path-field">
            <label for="pipelineLogPathInput">Log path</label>
            <input type="text" id="pipelineLogPathInput" value="outputs/application_planning/live_pipeline_run.log" />
            <div class="control-help field-help-wide">Live pipeline log file written during the run.</div>
          </div>
        </div>

        <div class="pipeline-support-row">
          <div class="control-group pipeline-toggle-group">
            <label>Delete seen data</label>
            <div class="binary-toggle" role="radiogroup" aria-label="Delete seen data">
              <label class="binary-toggle-option">
                <input type="radio" name="pipelineDeleteSeenData" value="no" checked />
                <span>No</span>
              </label>
              <label class="binary-toggle-option">
                <input type="radio" name="pipelineDeleteSeenData" value="yes" />
                <span>Yes</span>
              </label>
            </div>
            <div class="control-help field-help-wide">No keeps the seen-job cache. Yes reruns jobs that were already seen before.</div>
          </div>
        </div>

        <div class="pipeline-option-sections compact-option-sections">
          <div class="pipeline-option-section">
            <div class="pipeline-option-section-header">
              <div class="pipeline-option-title">LLM ACTIONS</div>
              <div class="pipeline-inline-actions">
                <button type="button" class="ghost-btn btn-sm" id="pipelineSelectAllActionsBtn">Select all</button>
                <button type="button" class="ghost-btn btn-sm" id="pipelineClearAllActionsBtn">Clear all</button>
              </div>
            </div>

            <div class="pipeline-toggle-grid">
              <div class="pipeline-toggle-item">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">APPLY</div>
                  <div class="pipeline-toggle-help">Include APPLY jobs in the LLM action pass.</div>
                </div>
                <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="APPLY action">
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineLlmActionApply" data-pipeline-llm-action-toggle="APPLY" value="no" />
                    <span>No</span>
                  </label>
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineLlmActionApply" data-pipeline-llm-action-toggle="APPLY" value="yes" checked />
                    <span>Yes</span>
                  </label>
                </div>
              </div>

              <div class="pipeline-toggle-item">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">APPLY_REVIEW_VARIANTS</div>
                  <div class="pipeline-toggle-help">Include variant-review jobs in the LLM action pass.</div>
                </div>
                <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="APPLY_REVIEW_VARIANTS action">
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineLlmActionApplyReviewVariants" data-pipeline-llm-action-toggle="APPLY_REVIEW_VARIANTS" value="no" />
                    <span>No</span>
                  </label>
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineLlmActionApplyReviewVariants" data-pipeline-llm-action-toggle="APPLY_REVIEW_VARIANTS" value="yes" checked />
                    <span>Yes</span>
                  </label>
                </div>
              </div>

              <div class="pipeline-toggle-item">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">MAYBE_TAILOR</div>
                  <div class="pipeline-toggle-help">Include maybe-tailor jobs in the LLM action pass.</div>
                </div>
                <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="MAYBE_TAILOR action">
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineLlmActionMaybeTailor" data-pipeline-llm-action-toggle="MAYBE_TAILOR" value="no" checked />
                    <span>No</span>
                  </label>
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineLlmActionMaybeTailor" data-pipeline-llm-action-toggle="MAYBE_TAILOR" value="yes" />
                    <span>Yes</span>
                  </label>
                </div>
              </div>

              <div class="pipeline-toggle-item">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">SKIP_FOR_NOW</div>
                  <div class="pipeline-toggle-help">Include skip-for-now jobs in the LLM action pass.</div>
                </div>
                <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="SKIP_FOR_NOW action">
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineLlmActionSkipForNow" data-pipeline-llm-action-toggle="SKIP_FOR_NOW" value="no" checked />
                    <span>No</span>
                  </label>
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineLlmActionSkipForNow" data-pipeline-llm-action-toggle="SKIP_FOR_NOW" value="yes" />
                    <span>Yes</span>
                  </label>
                </div>
              </div>
            </div>
          </div>

          <div class="pipeline-option-section">
            <div class="pipeline-option-title">RUN OPTIONS</div>

            <div class="pipeline-toggle-grid">
              <div class="pipeline-toggle-item">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">Planning only</div>
                  <div class="pipeline-toggle-help">Skip the scrape and run downstream planning only.</div>
                </div>
                <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Planning only">
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelinePlanningOnly" value="no" checked />
                    <span>No</span>
                  </label>
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelinePlanningOnly" value="yes" />
                    <span>Yes</span>
                  </label>
                </div>
              </div>

              <div class="pipeline-toggle-item">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">Generate tailoring</div>
                  <div class="pipeline-toggle-help">Build deterministic tailoring artifacts.</div>
                </div>
                <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Generate tailoring">
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineGenerateTailoring" value="no" checked />
                    <span>No</span>
                  </label>
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineGenerateTailoring" value="yes" />
                    <span>Yes</span>
                  </label>
                </div>
              </div>

              <div class="pipeline-toggle-item">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">Generate LLM tailoring</div>
                  <div class="pipeline-toggle-help">Run live LLM tailoring generation.</div>
                </div>
                <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Generate LLM tailoring">
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineGenerateLlmTailoring" value="no" checked />
                    <span>No</span>
                  </label>
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineGenerateLlmTailoring" value="yes" />
                    <span>Yes</span>
                  </label>
                </div>
              </div>

              <div class="pipeline-toggle-item">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">Refresh LLM tailoring</div>
                  <div class="pipeline-toggle-help">Force regeneration instead of reusing cached tailoring.</div>
                </div>
                <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Refresh LLM tailoring">
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineRefreshLlmTailoring" value="no" checked />
                    <span>No</span>
                  </label>
                  <label class="binary-toggle-option">
                    <input type="radio" name="pipelineRefreshLlmTailoring" value="yes" />
                    <span>Yes</span>
                  </label>
                </div>
              </div>

              <div class="pipeline-toggle-item">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">Generate LLM fallback</div>
                  <div class="pipeline-toggle-help">Run fallback ranking when needed.</div>
                </div>
                <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Generate LLM fallback">
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
      <div class="modal-header">
        <div>
          <h3>Confirm pipeline run</h3>
          <div class="subtext">Review the selected configuration before launch.</div>
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
  <script src="/static/app.js"></script>
</body>
</html>
    """.strip()


