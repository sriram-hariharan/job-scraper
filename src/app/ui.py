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


def _require_operations_viewer(request: Request) -> dict:
    user = _auth_user_from_request(request)
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")
    if not _is_admin_user(user) and str(user.get("access_level") or "").strip().lower() != "super_user":
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
  <link rel="stylesheet" href="/static/styles.css?v=eucalyptus_action_cascade_r2" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=eucalyptus_primary_shell_r1&ui=runtime_truth_r1" />
  <link rel="stylesheet" href="/static/build/executive-kpi/executive-kpi.css?v=eucalyptus_primary_shell_r1" />
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

        </header>
    <section class="executive-freshness-strip" id="executiveFreshnessStrip" aria-label="Executive Queue freshness">
      <div class="executive-freshness-main">
        <div class="executive-freshness-fact">
          <span class="executive-freshness-icon executive-freshness-icon--shared" aria-hidden="true"><svg viewBox="0 0 24 24"><ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7"/></svg></span>
          <div class="executive-freshness-copy">
            <strong id="sharedFreshnessLabel">Shared jobs updated · Checking…</strong>
            <span>Latest jobs from your connected sources.</span>
          </div>
          <span class="executive-freshness-badge is-unavailable" id="sharedFreshnessBadge">Unavailable</span>
        </div>
        <span class="executive-freshness-divider" aria-hidden="true"></span>
        <div class="executive-freshness-fact">
          <span class="executive-freshness-icon executive-freshness-icon--personal" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></svg></span>
          <div class="executive-freshness-copy">
            <strong id="personalFreshnessLabel">Your recommendations updated · Checking…</strong>
            <span>Personalized to your preferences and resumes.</span>
          </div>
          <span class="executive-freshness-badge is-unavailable" id="personalFreshnessBadge">Not generated</span>
        </div>
        <button id="runPipelineBtn" type="button">Refresh My Jobs</button>
      </div>
      <div class="executive-freshness-notice hidden" id="executiveFreshnessNotice" role="status"></div>
    </section>
    <section
      id="executiveKpiRoot"
      class="executive-kpi-root"
      aria-label="Executive queue metrics"
      aria-live="polite"
    >
      <div class="executive-kpi-server-fallback">Loading dashboard metrics...</div>
      <noscript>Enable JavaScript to view the Executive queue metrics.</noscript>
    </section>

    <section
      id="sourceYieldRoot"
      class="source-yield-root"
      aria-label="Source yield"
      aria-live="polite"
    >
      <div class="source-yield-server-fallback">Loading source yield...</div>
      <noscript>Enable JavaScript to view source yield.</noscript>
    </section>

    <div class="subtext pipeline-run-meta hidden" id="pipelineRunMeta">Pipeline idle.</div>
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

  <section class="modal-backdrop hidden" id="applicationActionModal" role="dialog" aria-modal="true" aria-labelledby="applicationStatusDialogTitle" aria-describedby="applicationModalMeta">
    <div class="modal-card application-status-dialog">
      <div class="application-status-dialog__header">
        <span class="application-status-dialog__icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M9 11l3 3L22 4"/><path d="M21 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11"/></svg></span>
        <div class="application-status-dialog__heading">
          <h3 id="applicationStatusDialogTitle">Update application status</h3>
          <div class="subtext" id="applicationModalMeta">Choose what happened after opening the job.</div>
        </div>
        <button class="ghost-btn modal-close-btn application-status-dialog__close" id="closeApplicationModalBtn" type="button" aria-label="Close application status dialog" title="Close"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg></button>
      </div>

      <div class="modal-body application-status-dialog__job" aria-label="Selected job">
        <div class="application-status-dialog__job-field">
          <span class="label">Company</span>
          <span id="applicationModalCompany">-</span>
        </div>
        <div class="application-status-dialog__job-field">
          <span class="label">Role</span>
          <span id="applicationModalTitle">-</span>
        </div>
      </div>

      <div class="application-status-dialog__prompt">Choose a status</div>
      <div class="modal-actions application-status-dialog__actions">
        <button type="button" class="status-action-btn applied-action-btn" data-status-action="APPLIED"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6"/></svg><span>Applied</span></button>
        <button type="button" class="status-action-btn saved-action-btn" data-status-action="SAVED"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6 3h12v18l-6-4-6 4z"/></svg><span>Save for later</span></button>
        <button type="button" class="status-action-btn not-applied-action-btn" data-status-action="NOT_APPLIED"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg><span>Not applied</span></button>
        <button type="button" class="ghost-btn application-status-dialog__dismiss" data-status-action="DISMISSED"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 18-6-6 6-6"/></svg><span>Dismiss</span></button>
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
  <script src="/static/shell.js?v=eucalyptus_primary_shell_r1&ui=runtime_truth_r1"></script>
  <script type="module" src="/static/build/executive-kpi/executive-kpi.js?v=eucalyptus_primary_shell_r1"></script>
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
          <h3 id="pipelineLaunchTitle">Refresh My Jobs</h3>
          <div class="subtext" id="pipelineLaunchDescription">Configure and launch a personalized scan using the latest shared job pool.</div>
        </div>
        <ol class="pipeline-launch-steps" aria-label="Pipeline launch progress">
          <li class="pipeline-launch-step-indicator is-active" data-pipeline-step-indicator="configure" aria-current="step">
            <span>1</span> Configure
          </li>
          <li class="pipeline-launch-step-indicator" data-pipeline-step-indicator="review">
            <span>2</span> Review &amp; launch
          </li>
        </ol>
        <button class="ghost-btn modal-close-btn" id="closePipelineConfigModalBtn" type="button" aria-label="Close pipeline settings" title="Close">×</button>
      </header>

      <div class="pipeline-modal-scroll" id="pipelineLaunchModalBody" tabindex="0">
        <section class="pipeline-launch-step" id="pipelineConfigureStep" data-pipeline-launch-panel="configure" aria-labelledby="pipelineConfigureHeading">
          <h4 class="sr-only" id="pipelineConfigureHeading">Configure pipeline run</h4>
          <div class="pipeline-config-layout">
          <div class="pipeline-freshness-callout" id="pipelineFreshnessCallout" role="status">
            <span class="pipeline-freshness-callout__icon" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v6l4 2"/></svg></span>
            <div><strong id="pipelineSharedFreshnessText">Checking shared job freshness…</strong><span id="pipelinePersonalFreshnessText"></span></div>
          </div>
          <div class="pipeline-option-sections compact-option-sections">
            <div class="pipeline-option-column pipeline-option-column--left">
            <section class="pipeline-option-section pipeline-option-section--scope">
              <div class="pipeline-option-section-header">
                <span class="pipeline-option-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/><circle cx="12" cy="12" r="4"/><path d="M12 2v3M22 12h-3M12 22v-3M2 12h3"/></svg></span>
                <div><div class="pipeline-option-title">Run scope</div><div class="pipeline-option-description">Control how many jobs to process and build packets.</div></div>
              </div>
              <div class="pipeline-form-grid pipeline-form-grid--compact">
                <div class="control-group pipeline-limit-group">
                  <label for="pipelineJobLimitInput">Job limit <span class="packet-info-icon pipeline-help-icon" title="Maximum qualified jobs from the current-run corpus that proceed through application planning." aria-label="Maximum qualified jobs from the current-run corpus that proceed through application planning.">?</span></label>
                  <input type="number" id="pipelineJobLimitInput" value="50" min="1" max="500" aria-describedby="pipelineJobLimitError" />
                  <div class="pipeline-inline-validation" id="pipelineJobLimitError" aria-live="polite"></div>
                </div>
                <div class="control-group">
                  <label for="pipelineJobPacketLimitInput">Packet limit <span class="packet-info-icon pipeline-help-icon" title="Maximum detailed planning packets to build. 0 means all selected jobs." aria-label="Maximum detailed planning packets to build. 0 means all selected jobs.">?</span></label>
                  <input type="number" id="pipelineJobPacketLimitInput" value="0" min="0" max="500" aria-describedby="pipelineJobPacketLimitError" />
                  <div class="pipeline-inline-validation" id="pipelineJobPacketLimitError" aria-live="polite"></div>
                  <div class="control-help">0 = all selected jobs</div>
                </div>
                <div class="pipeline-inline-helper pipeline-inline-helper--presets">
                  <span class="pipeline-inline-helper-label">Quick presets</span>
                  <div class="pipeline-chip-row pipeline-chip-row--compact">
                    <button type="button" class="ghost-btn pipeline-chip-btn" data-job-limit-preset="25">25</button>
                    <button type="button" class="ghost-btn pipeline-chip-btn" data-job-limit-preset="50">50</button>
                    <button type="button" class="ghost-btn pipeline-chip-btn" data-job-limit-preset="100">100</button>
                    <button type="button" class="ghost-btn pipeline-chip-btn" data-job-limit-preset="200">200</button>
                  </div>
                </div>
                <div class="pipeline-setting-row pipeline-setting-row--wide">
                  <div class="pipeline-toggle-copy">
                    <div class="pipeline-toggle-name">Rerun seen jobs <span class="packet-info-icon pipeline-help-icon" title="Controls seen-job history only; Scan + Plan scrapes current ATS jobs with either choice." aria-label="Controls seen-job history only; Scan + Plan scrapes current ATS jobs with either choice.">?</span></div>
                    <div class="pipeline-toggle-help" id="pipelineDeleteSeenDataHelp">No keeps seen-job history; Yes clears it before Scan + Plan so earlier jobs can be reconsidered.</div>
                  </div>
                  <div class="binary-toggle binary-toggle--compact" role="radiogroup" aria-label="Rerun seen jobs" aria-describedby="pipelineDeleteSeenDataHelp">
                    <label class="binary-toggle-option"><input type="radio" name="pipelineDeleteSeenData" value="no" checked /><span>No</span></label>
                    <label class="binary-toggle-option"><input type="radio" name="pipelineDeleteSeenData" value="yes" /><span>Yes</span></label>
                  </div>
                </div>
              </div>
            </section>

            <section class="pipeline-option-section pipeline-option-section--processing">
              <div class="pipeline-option-section-header">
                <span class="pipeline-option-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06-2.83 2.83-.06-.06a1.7 1.7 0 0 0-1.88-.34 1.7 1.7 0 0 0-1.03 1.56V21h-4v-.08a1.7 1.7 0 0 0-1.03-1.56 1.7 1.7 0 0 0-1.88.34l-.06.06-2.83-2.83.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.56-1.03H3v-4h.08A1.7 1.7 0 0 0 4.64 8.9a1.7 1.7 0 0 0-.34-1.88l-.06-.06 2.83-2.83.06.06A1.7 1.7 0 0 0 9 4.53a1.7 1.7 0 0 0 1-1.56V3h4v.08a1.7 1.7 0 0 0 1.03 1.56 1.7 1.7 0 0 0 1.88-.34l.06-.06 2.83 2.83-.06.06A1.7 1.7 0 0 0 19.4 9c.13.37.47.82 1.56 1H21v4h-.08A1.7 1.7 0 0 0 19.4 15Z"/></svg></span>
                <div><div class="pipeline-option-title">Processing</div><div class="pipeline-option-description">Choose how to build this run.</div></div>
              </div>
              <div class="pipeline-setting-row pipeline-setting-row--mode">
                <div class="pipeline-toggle-copy">
                  <div class="pipeline-toggle-name">Run mode</div>
                  <div class="pipeline-toggle-help">Choose fresh ATS collection or rebuild planning from the existing planning corpus.</div>
                </div>
                <div class="binary-toggle binary-toggle--compact pipeline-mode-toggle" role="radiogroup" aria-label="Run mode">
                  <label class="binary-toggle-option"><input type="radio" name="pipelinePlanningOnly" value="no" checked /><span>Scan + Plan <i class="packet-info-icon pipeline-help-icon" title="Scrape current jobs from configured ATS sources, then filter, score, and build planning outputs." aria-label="Scrape current jobs from configured ATS sources, then filter, score, and build planning outputs.">?</i></span></label>
                  <label class="binary-toggle-option"><input type="radio" name="pipelinePlanningOnly" value="yes" /><span>Plan only <i class="packet-info-icon pipeline-help-icon" title="Skip ATS scraping and rebuild application planning from the existing planning corpus." aria-label="Skip ATS scraping and rebuild application planning from the existing planning corpus.">?</i></span></label>
                </div>
              </div>
            </section>
            </div>

            <div class="pipeline-option-column pipeline-option-column--center">
            <section class="pipeline-option-section pipeline-option-section--intelligence">
              <div class="pipeline-option-section-header">
                <span class="pipeline-option-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="m12 3-1.6 4.4L6 9l4.4 1.6L12 15l1.6-4.4L18 9l-4.4-1.6L12 3Z"/><path d="m19 15-.8 2.2L16 18l2.2.8L19 21l.8-2.2L22 18l-2.2-.8L19 15ZM5 3l.6 1.4L7 5l-1.4.6L5 7l-.6-1.4L3 5l1.4-.6L5 3Z"/></svg></span>
                <div><div class="pipeline-option-title">Intelligence</div><div class="pipeline-option-description">Use AI to review and prioritize opportunities.</div></div>
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
                <span class="pipeline-option-icon" aria-hidden="true"><svg viewBox="0 0 24 24"><path d="M4 6h8M16 6h4M4 12h3M11 12h9M4 18h10M18 18h2"/><circle cx="14" cy="6" r="2"/><circle cx="9" cy="12" r="2"/><circle cx="16" cy="18" r="2"/></svg></span>
                <div><div class="pipeline-option-title">Advanced</div><div class="pipeline-option-description">Optional settings for more control.</div></div>
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
          </div>
          <aside class="pipeline-live-summary" aria-labelledby="pipelineLiveSummaryTitle">
            <div class="pipeline-live-summary__heading">
              <span class="pipeline-live-summary__step" aria-hidden="true">2</span>
              <div><strong id="pipelineLiveSummaryTitle">Review &amp; launch</strong><span>Confirm your settings before starting.</span></div>
            </div>
            <div class="pipeline-live-summary__title">Run summary</div>
            <div class="pipeline-live-summary__rows" id="pipelineLiveSummary"></div>
            <div class="pipeline-review-safety-note" role="note">
              <span class="pipeline-review-safety-note__icon" aria-hidden="true"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8h.01"/></svg></span>
              <span>This launches collection and planning only. It does not apply to jobs or message recruiters.</span>
            </div>
          </aside>
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
        <button type="button" id="openPipelineConfirmBtn"><span>Continue</span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="m9 18 6-6-6-6"/></svg></button>
        <button type="button" class="hidden" id="confirmPipelineRunBtn">Refresh My Jobs</button>
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
  <link rel="stylesheet" href="/static/app_redesign.css?v=eucalyptus_primary_shell_r1&ui=runtime_truth_r1" />
  <link rel="stylesheet" href="/static/build/executive-kpi/executive-kpi.css?v=eucalyptus_primary_shell_r1" />
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
  <script src="/static/shell.js?v=eucalyptus_primary_shell_r1&ui=runtime_truth_r1"></script>
  <script src="/static/app.js?v=phase133d_s1"></script>
  <script type="module" src="/static/build/executive-kpi/executive-kpi.js?v=eucalyptus_primary_shell_r1"></script>
</body>
</html>
    """.strip()

@router.get("/scheduler", response_class=HTMLResponse)
def scheduler_dashboard(request: Request) -> str:
    user = _require_operations_viewer(request)
    can_manage = "true" if _is_admin_user(user) else "false"
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Scheduler Health</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=shared_filter_fluid_select_r2" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=eucalyptus_primary_shell_r1&ui=runtime_truth_r1" />
  <link rel="stylesheet" href="/static/build/executive-kpi/executive-kpi.css?v=eucalyptus_primary_shell_r1" />
</head>
<body class="scheduler-health-page">
  {render_top_shell("/scheduler")}
  <main class="page scheduler-health-shell">
    <section
      id="schedulerHealthDashboardRoot"
      data-can-manage="{can_manage}"
      aria-label="Scheduler health dashboard"
      aria-live="polite"
    >
      <div class="scheduler-health-server-fallback">Loading scheduler health...</div>
      <noscript>Enable JavaScript to monitor Scheduler Health.</noscript>
    </section>
  </main>

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=eucalyptus_primary_shell_r1&ui=runtime_truth_r1"></script>
  <script type="module" src="/static/build/executive-kpi/executive-kpi.js?v=eucalyptus_primary_shell_r1"></script>
</body>
</html>
    """.strip()


@router.get("/agentic-operations", response_class=HTMLResponse)
def agentic_operations_console(request: Request) -> str:
    user = _require_operations_viewer(request)
    access_badge = "Admin only" if _is_admin_user(user) else "Read-only"
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Agentic Operations</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=eucalyptus_primary_shell_r1&ui=runtime_truth_r1" />
  <link rel="stylesheet" href="/static/build/executive-kpi/executive-kpi.css?v=eucalyptus_primary_shell_r1" />
</head>
<body class="agentic-operations-page">
  {render_top_shell("/agentic-operations")}
  <main class="page agentic-operations-shell">
    <header class="page-header app-page-header">
      <div class="page-header-main app-page-header__main">
        <div class="agentic-operations-header-title-row app-page-header__title-row">
          <h1 class="app-page-header__title">Agentic Operations</h1>
          <span class="agentic-operations-header-badge app-page-header__badge">{access_badge}</span>
          <span
            id="agenticOperationsHeaderReadOnlyBadge"
            class="agentic-operations-header-badge-slot"
          ></span>
        </div>
        <p class="subtext app-page-header__description">
          Administrative read-only workspace for agent supervision and runtime evidence.
        </p>
      </div>
    </header>

    <section
      id="agenticOperationsRoot"
      aria-label="Agentic Operations workspace"
      aria-live="polite"
    >
      <div class="agentic-operations-server-fallback">Loading Agentic Operations...</div>
      <noscript>Enable JavaScript to view Agentic Operations.</noscript>
    </section>
  </main>

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=eucalyptus_primary_shell_r1&ui=runtime_truth_r1"></script>
  <script type="module" src="/static/build/executive-kpi/executive-kpi.js?v=eucalyptus_primary_shell_r1"></script>
</body>
</html>
    """.strip()
