from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from src.app.ui_shell import render_top_shell
from src.auth.runtime import current_user_from_request

router = APIRouter()


def _is_admin_user(user: dict) -> bool:
    access_level = str(user.get("access_level", "") or "").strip().lower()
    return bool(user.get("is_admin", False)) or access_level == "admin"


def _auth_user_from_request(request: Request | None) -> dict:
    if request is None:
        return {}
    return dict(getattr(request.state, "auth_user", {}) or {}) or current_user_from_request(request)


def _require_admin_user(request: Request) -> dict:
    user = _auth_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if not _is_admin_user(user):
        raise HTTPException(status_code=403, detail="Admin access required.")
    return user


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
  <link rel="stylesheet" href="/static/styles.css?v=phase133d_s1" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=item2_phase4_secondary_headers_r1" />
  <link rel="stylesheet" href="/static/build/executive-kpi/executive-kpi.css?v=item2_phase3_shared_header_r1" />
</head>
<body class="executive-dashboard-page">
  {render_top_shell("/")}
  <div class="page">
        <header class="page-header app-page-header">
          <div class="page-header-main app-page-header__main">
            <div class="executive-title-row app-page-header__title-row">
              <h1 class="app-page-header__title">Executive Queue</h1>
            </div>

            <p class="subtext app-page-header__description">High-signal operator dashboard for direct apply and review decisions.</p>
          </div>

          <div class="header-actions app-page-header__actions">
            <button class="ghost-btn" id="refreshStatusBtn" type="button">Refresh Status</button>
            <button id="runPipelineBtn" type="button">Run Live Pipeline</button>
          </div>
        </header>
    <section
      id="executiveKpiRoot"
      class="executive-kpi-root"
      aria-label="Executive queue metrics"
      aria-live="polite"
    >
      <div class="executive-kpi-server-fallback">Loading dashboard metrics...</div>
      <noscript>Enable JavaScript to view the Executive queue metrics.</noscript>
    </section>

    <div class="subtext pipeline-run-meta" id="pipelineRunMeta">Pipeline idle.</div>
    <section
      id="executiveQueueRoot"
      class="executive-queue-root"
      aria-label="Executive queue"
      aria-live="polite"
    >
      <div class="executive-queue-server-fallback">Loading executive queue...</div>
      <noscript>Enable JavaScript to view and filter the Executive queue.</noscript>
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

  {_pipeline_dashboard_launch_dialogs()}

  <section class="page-loading-overlay workflow-overlay workflow-overlay--pipeline hidden" id="pageLoadingOverlay" aria-live="polite" aria-modal="true" role="dialog">
    <div class="page-loading-card pipeline-loading-card workflow-overlay__panel" id="pipelineOverlayCard">
      <div class="pipeline-overlay-loading" id="pipelineOverlayLoading">
        <header class="workflow-overlay__header pipeline-workflow-header">
          <div>
            <div class="workflow-overlay__eyebrow">Live workflow</div>
            <div class="page-loading-title" id="pageLoadingTitle">Running live job pipeline</div>
            <div class="page-loading-text" id="pageLoadingText">Collecting jobs, filtering duplicates, scoring fit, and preparing planning artifacts.</div>
            <div class="workflow-current-activity">
              <span class="workflow-current-activity__spinner" aria-hidden="true"></span>
              <div class="workflow-current-activity__copy">
                <span class="workflow-current-activity__label">Current activity</span>
                <div class="pipeline-loading-meta" id="pipelineLoadingMeta"></div>
              </div>
            </div>
          </div>
        </header>
        <div class="workflow-overlay__metrics">
          <div class="pipeline-loading-counts" id="pipelineLoadingCounts"></div>
        </div>
        <div class="workflow-overlay__body">
          <div class="workflow-step-viewport">
            <div class="pipeline-stage-stepper workflow-step-track" id="pipelineStageStepper"></div>
          </div>
        </div>
      </div>

      <div class="pipeline-overlay-success hidden" id="pipelineOverlaySuccess">
        <header class="workflow-overlay__header pipeline-result-header">
          <div class="pipeline-result-header__layout">
            <div class="workflow-completion-indicator" aria-hidden="true">✓</div>
            <div class="pipeline-result-header__copy">
              <div class="workflow-overlay__eyebrow">Complete</div>
              <div class="page-loading-title pipeline-success-title" id="pipelineSuccessTitle">
                Pipeline run is ready
              </div>
              <div class="page-loading-text pipeline-success-text" id="pipelineSuccessText">
                Your job results and planning artifacts are ready to review.
              </div>
            </div>
          </div>
        </header>
        <div class="workflow-overlay__metrics pipeline-success-summary" id="pipelineSuccessSummary">
          <div class="pipeline-result-metrics" id="pipelineResultMetrics"></div>
          <div class="pipeline-empty-reasons hidden" id="pipelineEmptyReasons"></div>
        </div>
        <div class="workflow-overlay__body workflow-overlay__body--completion">
          <div class="workflow-step-viewport">
            <div class="pipeline-stage-stepper workflow-step-track" id="pipelineSuccessStageStepper"></div>
          </div>
        </div>
        <div class="modal-actions pipeline-success-actions workflow-overlay__footer">
          <button type="button" class="ghost-btn pipeline-result-action pipeline-result-action--tertiary" id="pipelineSuccessOkBtn">Close</button>
          <button type="button" class="ghost-btn pipeline-result-action pipeline-result-action--secondary hidden" id="pipelineSuccessDetailsBtn">Review Run Details</button>
          <button type="button" class="pipeline-result-action pipeline-result-action--primary hidden" id="pipelineSuccessRunAgainBtn">Adjust Settings</button>
          <button type="button" id="pipelineSuccessPlanningBtn">View Planning</button>
        </div>
      </div>

      <div class="pipeline-overlay-failure hidden" id="pipelineOverlayFailure">
        <header class="workflow-overlay__header">
          <div>
            <div class="workflow-overlay__eyebrow">Needs attention</div>
            <div class="page-loading-title pipeline-success-title" id="pipelineFailureTitle">
              Pipeline could not finish
            </div>
            <div class="page-loading-text pipeline-success-text" id="pipelineFailureText">
              The run stopped before completion. Review diagnostics for technical details.
            </div>
          </div>
        </header>
        <div class="workflow-overlay__metrics">
          <div class="pipeline-success-summary" id="pipelineFailureSummary"></div>
          <div class="pipeline-success-summary" id="pipelineFailureReason"></div>
        </div>
        <div class="workflow-overlay__body workflow-overlay__body--completion">
          <div class="workflow-step-viewport">
            <div class="pipeline-stage-stepper workflow-step-track" id="pipelineFailureStageStepper"></div>
          </div>
        </div>
        <div class="modal-actions pipeline-success-actions workflow-overlay__footer">
          <button type="button" id="pipelineFailureOkBtn">Close</button>
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
  <script src="/static/shell.js?v=phase133h_r1"></script>
  <script type="module" src="/static/build/executive-kpi/executive-kpi.js?v=item2_phase3_shared_header_r1"></script>
  <script src="/static/app.js?v=phase133d_s1"></script>
  </body>
</html>
    """.strip()


def _pipeline_dashboard_launch_dialogs() -> str:
    """Render the canonical reviewed Live Pipeline launch flow."""
    return """
  <section
    class="modal-backdrop hidden pipeline-launch-modal"
    id="pipelineConfigModal"
    role="dialog"
    aria-modal="true"
    aria-labelledby="pipelineLaunchTitle"
    aria-describedby="pipelineLaunchDescription"
  >
    <div class="modal-card pipeline-modal-card" data-pipeline-launch-step="configure">
      <header class="modal-header pipeline-launch-header">
        <div class="pipeline-launch-heading">
          <div class="pipeline-launch-eyebrow">Live pipeline</div>
          <h3 id="pipelineLaunchTitle">Run live pipeline</h3>
          <div class="subtext" id="pipelineLaunchDescription">Choose limits and options before starting the run.</div>
        </div>
        <ol class="pipeline-launch-steps" aria-label="Pipeline launch progress">
          <li class="pipeline-launch-step-indicator is-active" data-pipeline-step-indicator="configure" aria-current="step">
            <span>1</span> Configure
          </li>
          <li class="pipeline-launch-step-indicator" data-pipeline-step-indicator="review">
            <span>2</span> Review &amp; launch
          </li>
        </ol>
        <button class="ghost-btn modal-close-btn" id="closePipelineConfigModalBtn" type="button" aria-label="Close pipeline settings">Close</button>
      </header>

      <div class="pipeline-modal-scroll" id="pipelineLaunchModalBody" tabindex="0">
        <section class="pipeline-launch-step" id="pipelineConfigureStep" data-pipeline-launch-panel="configure" aria-labelledby="pipelineConfigureHeading">
          <h4 class="sr-only" id="pipelineConfigureHeading">Configure pipeline run</h4>
          <div class="pipeline-option-sections compact-option-sections">
            <section class="pipeline-option-section pipeline-option-section--scope">
              <div class="pipeline-option-section-header">
                <div><div class="pipeline-option-kicker">Scope</div><div class="pipeline-option-title">Run scope</div></div>
                <div class="pipeline-option-description">Control how many jobs enter the run and how many planning packets are produced.</div>
              </div>
              <div class="pipeline-form-grid pipeline-form-grid--compact">
                <div class="control-group pipeline-limit-group">
                  <label for="pipelineJobLimitInput">Job limit <span class="packet-info-icon pipeline-help-icon" title="Maximum jobs allowed into this run." aria-label="Maximum jobs allowed into this run.">?</span></label>
                  <input type="number" id="pipelineJobLimitInput" value="50" min="1" max="500" aria-describedby="pipelineJobLimitError" />
                  <div class="pipeline-inline-validation" id="pipelineJobLimitError" aria-live="polite"></div>
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
                  <label for="pipelineJobPacketLimitInput">Packet limit <span class="packet-info-icon pipeline-help-icon" title="Maximum detailed planning packets to build. 0 means all selected jobs." aria-label="Maximum detailed planning packets to build. 0 means all selected jobs.">?</span></label>
                  <input type="number" id="pipelineJobPacketLimitInput" value="0" min="0" max="500" aria-describedby="pipelineJobPacketLimitError" />
                  <div class="pipeline-inline-validation" id="pipelineJobPacketLimitError" aria-live="polite"></div>
                  <div class="control-help">Use 0 to build packets for every selected job.</div>
                </div>
                <div class="pipeline-setting-row pipeline-setting-row--wide">
                  <div class="pipeline-toggle-copy">
                    <div class="pipeline-toggle-name">Rerun seen jobs <span class="packet-info-icon pipeline-help-icon" title="Include jobs that were already seen before." aria-label="Include jobs that were already seen before.">?</span></div>
                    <div class="pipeline-toggle-help">Include jobs that were processed in an earlier run.</div>
                  </div>
                  <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Rerun seen jobs">
                    <label class="binary-toggle-option"><input type="radio" name="pipelineDeleteSeenData" value="no" checked /><span>No</span></label>
                    <label class="binary-toggle-option"><input type="radio" name="pipelineDeleteSeenData" value="yes" /><span>Yes</span></label>
                  </div>
                </div>
              </div>
            </section>

            <section class="pipeline-option-section">
              <div class="pipeline-option-section-header">
                <div><div class="pipeline-option-kicker">Processing</div><div class="pipeline-option-title">Run mode</div></div>
              </div>
              <div class="pipeline-setting-row pipeline-setting-row--mode">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">Pipeline stages</div>
                  <div class="pipeline-toggle-help">Scan and plan new jobs, or rebuild planning from jobs already collected.</div>
                </div>
                <div class="binary-toggle binary-toggle--compact pipeline-mode-toggle" role="radiogroup" aria-label="Run mode">
                  <label class="binary-toggle-option"><input type="radio" name="pipelinePlanningOnly" value="no" checked /><span>Scan + Plan <i class="packet-info-icon pipeline-help-icon" title="Scrape jobs, score them, and build planning outputs." aria-label="Scrape jobs, score them, and build planning outputs.">?</i></span></label>
                  <label class="binary-toggle-option"><input type="radio" name="pipelinePlanningOnly" value="yes" /><span>Plan only <i class="packet-info-icon pipeline-help-icon" title="Skip scraping and rebuild planning from existing jobs." aria-label="Skip scraping and rebuild planning from existing jobs.">?</i></span></label>
                </div>
              </div>
            </section>

            <section class="pipeline-option-section">
              <div class="pipeline-option-section-header">
                <div><div class="pipeline-option-kicker">Intelligence</div><div class="pipeline-option-title">AI planning</div></div>
              </div>
              <div class="pipeline-setting-row">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">AI review <span class="packet-info-icon pipeline-help-icon" title="Use AI to review planning decisions and borderline fits. This does not tailor resumes." aria-label="Use AI to review planning decisions and borderline fits. This does not tailor resumes.">?</span></div>
                  <div class="pipeline-toggle-help">Review planning decisions and borderline fits without tailoring resumes.</div>
                </div>
                <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="AI review">
                  <label class="binary-toggle-option"><input type="radio" name="pipelineGenerateLlmAdjudication" value="no" /><span>No</span></label>
                  <label class="binary-toggle-option"><input type="radio" name="pipelineGenerateLlmAdjudication" value="yes" checked /><span>Yes</span></label>
                </div>
              </div>
            </section>

            <section class="pipeline-option-section pipeline-option-section--advanced">
              <div class="pipeline-option-section-header">
                <div><div class="pipeline-option-kicker">Optional</div><div class="pipeline-option-title">Advanced</div></div>
              </div>
              <div class="pipeline-setting-row">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">Backup ranking <span class="packet-info-icon pipeline-help-icon" title="Use fallback ranking when normal ranking signals are incomplete." aria-label="Use fallback ranking when normal ranking signals are incomplete.">?</span></div>
                  <div class="pipeline-toggle-help">Use fallback ranking only when normal ranking signals are incomplete.</div>
                </div>
                <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Backup ranking">
                  <label class="binary-toggle-option"><input type="radio" name="pipelineGenerateLlmFallback" value="no" checked /><span>No</span></label>
                  <label class="binary-toggle-option"><input type="radio" name="pipelineGenerateLlmFallback" value="yes" /><span>Yes</span></label>
                </div>
              </div>
            </section>
          </div>
        </section>

        <section class="pipeline-launch-step hidden" id="pipelineConfirmModal" data-pipeline-launch-panel="review" aria-labelledby="pipelineReviewHeading" aria-live="polite">
          <h4 class="sr-only" id="pipelineReviewHeading">Review and launch pipeline run</h4>
          <div class="confirm-summary-block" id="pipelineConfirmSummary"></div>
        </section>
      </div>

      <footer class="modal-actions pipeline-modal-actions">
        <button type="button" class="ghost-btn" id="cancelPipelineConfigBtn">Cancel</button>
        <button type="button" class="ghost-btn hidden" id="backToPipelineConfigBtn">Back</button>
        <button type="button" id="openPipelineConfirmBtn">Continue</button>
        <button type="button" class="hidden" id="confirmPipelineRunBtn">Run Pipeline</button>
      </footer>
    </div>
  </section>
    """.strip()


def _pipeline_dashboard_error_dialog() -> str:
    return """
  <section class="modal-backdrop hidden" id="appErrorModal">
    <div class="modal-card app-error-modal-card">
      <div class="modal-header app-error-modal-header">
        <div><h3 id="appErrorTitle">Something went wrong</h3><div class="subtext" id="appErrorSubtitle">Review the message below.</div></div>
        <button class="ghost-btn modal-close-btn" id="closeAppErrorModalBtn" type="button">Close</button>
      </div>
      <div class="app-error-panel">
        <div class="app-error-icon-wrap" aria-hidden="true"><img class="app-error-icon-img" src="/static/media/error_img.png" alt="" /></div>
        <div class="app-error-copy"><div class="app-error-badge">Warning</div><div class="app-error-message" id="appErrorMessage"></div></div>
      </div>
      <div class="modal-actions app-error-actions"><button type="button" id="appErrorOkBtn">OK</button></div>
    </div>
  </section>
    """.strip()


@router.get("/pipeline", response_class=HTMLResponse)
def pipeline_dashboard() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Pipeline Dashboard</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=phase133d_s1" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=item2_phase4_secondary_headers_r1" />
  <link rel="stylesheet" href="/static/build/executive-kpi/executive-kpi.css?v=item2_phase3_shared_header_r1" />
</head>
<body class="pipeline-dashboard-page">
  {render_top_shell("/pipeline")}
  <main class="page pipeline-dashboard-shell">
    <section
      id="pipelineDashboardRoot"
      aria-label="Pipeline monitoring dashboard"
      aria-live="polite"
    >
      <div class="pipeline-dashboard-server-fallback">Loading pipeline status...</div>
      <noscript>Enable JavaScript to monitor Pipeline status.</noscript>
    </section>
  </main>
  {_pipeline_dashboard_launch_dialogs()}
  {_pipeline_dashboard_error_dialog()}
  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=phase133h_r1"></script>
  <script src="/static/app.js?v=phase133d_s1"></script>
  <script type="module" src="/static/build/executive-kpi/executive-kpi.js?v=item2_phase3_shared_header_r1"></script>
</body>
</html>
    """.strip()

@router.get("/scheduler", response_class=HTMLResponse)
def scheduler_dashboard(request: Request) -> str:
    _require_admin_user(request)
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Scheduler Health</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=item2_phase4_secondary_headers_r1" />
  <link rel="stylesheet" href="/static/build/executive-kpi/executive-kpi.css?v=item2_phase3_shared_header_r1" />
</head>
<body class="scheduler-health-page">
  {render_top_shell("/scheduler")}
  <main class="page scheduler-health-shell">
    <section
      id="schedulerHealthDashboardRoot"
      aria-label="Scheduler health dashboard"
      aria-live="polite"
    >
      <div class="scheduler-health-server-fallback">Loading scheduler health...</div>
      <noscript>Enable JavaScript to monitor Scheduler Health.</noscript>
    </section>
  </main>

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=phase133h_r1"></script>
  <script type="module" src="/static/build/executive-kpi/executive-kpi.js?v=item2_phase3_shared_header_r1"></script>
</body>
</html>
    """.strip()
