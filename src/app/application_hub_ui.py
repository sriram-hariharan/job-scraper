from fastapi import APIRouter
from fastapi.responses import HTMLResponse

from src.app.ui_shell import render_top_shell

router = APIRouter()


@router.get("/applications", response_class=HTMLResponse)
def applications_dashboard() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Applications</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=phase133h_s1" />
  <link rel="stylesheet" href="/static/build/executive-kpi/executive-kpi.css?v=phase133ef_r3" />
</head>
<body class="operational-dashboard-page applications-dashboard-page">
  {render_top_shell("/applications")}

  <main class="page operational-dashboard-shell">
    <header class="operational-dashboard-heading">
      <span>APPLICATION TRACKING</span>
      <h1>Applications</h1>
      <p>Track applied jobs and jobs saved for later through the existing manual workflow.</p>
    </header>
    <div id="applicationsDashboardRoot" aria-live="polite"><div class="operational-dashboard-fallback">Loading applications...</div></div>
  </main>

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
  <script src="/static/application_views.js?v=phase133ef_r5"></script>
  <script type="module" src="/static/build/executive-kpi/executive-kpi.js?v=phase133ef_r3"></script>
</body>
</html>
    """.strip()
