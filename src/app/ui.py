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
  <link rel="stylesheet" href="/static/styles.css?v=phase133d_s1" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=phase133d_s1" />
  <link rel="stylesheet" href="/static/build/executive-kpi/executive-kpi.css?v=phase133a" />
</head>
<body class="executive-dashboard-page">
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
  <script src="/static/shell.js?v=role_onboarding_r6"></script>
  <script type="module" src="/static/build/executive-kpi/executive-kpi.js?v=phase133a_fix1"></script>
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
  <link rel="stylesheet" href="/static/app_redesign.css?v=phase133d_s1" />
  <link rel="stylesheet" href="/static/build/executive-kpi/executive-kpi.css?v=phase133d" />
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
  <script src="/static/shell.js?v=role_onboarding_r6"></script>
  <script src="/static/app.js?v=phase133d_s1"></script>
  <script type="module" src="/static/build/executive-kpi/executive-kpi.js?v=phase133d"></script>
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
