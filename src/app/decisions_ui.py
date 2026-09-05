from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.app.ui_shell import render_top_shell

router = APIRouter()


@router.get("/decisions-ui", response_class=HTMLResponse)
def decisions_dashboard() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Decisions Dashboard</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=eucalyptus_action_cascade_r2" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=eucalyptus_primary_shell_r1&ui=runtime_truth_r1" />
  <link rel="stylesheet" href="/static/build/executive-kpi/executive-kpi.css?v=eucalyptus_primary_shell_r1" />
</head>
<body class="operational-dashboard-page decisions-dashboard-page">
{render_top_shell("/decisions-ui")}
  <main class="page operational-dashboard-shell">
    <header class="operational-dashboard-heading app-page-header">
      <div class="app-page-header__main">
        <span class="app-page-header__eyebrow">OPERATOR REVIEW</span>
        <div class="app-page-header__title-row">
          <h1 class="app-page-header__title">Decisions</h1>
        </div>
        <p class="app-page-header__description">Review recorded operator decisions, resume selections, and the resulting manual next steps.</p>
      </div>
    </header>
    <div id="decisionsDashboardRoot" aria-live="polite"><div class="operational-dashboard-fallback">Loading operator decisions...</div></div>
  </main>

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
  <script src="/static/decisions.js?v=phase133ef_r5"></script>
  <script type="module" src="/static/build/executive-kpi/executive-kpi.js?v=eucalyptus_primary_shell_r1"></script>
</body>
</html>
    """.strip()
