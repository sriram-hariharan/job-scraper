from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from html import escape
from pathlib import Path
from urllib.parse import urlencode

from src.app import services
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


def _admin_owner_user_id(user: dict) -> str:
    return str(user.get("user_id") or user.get("sub") or "").strip()


def _saved_scan_context_options(owner_user_id: str = "") -> list[dict]:
    try:
        payload = services.profile_saved_scans_payload(limit=50, owner_user_id=owner_user_id)
    except Exception:
        return []

    options: list[dict] = []
    for row in payload.get("saved_scans", []) or []:
        if not isinstance(row, dict):
            continue
        scan_id = str(row.get("scan_id") or "").strip()
        if not scan_id:
            continue
        company = str(row.get("job_company") or "").strip()
        title = str(row.get("job_title") or "").strip()
        resume_name = str(row.get("resume_name") or row.get("resume_filename") or "").strip()
        status = str(row.get("scan_status") or "").strip()
        timestamp = str(row.get("scan_timestamp") or "").strip()
        source = str(row.get("scan_source") or row.get("resume_source") or "").strip()
        primary = " / ".join(part for part in (company, title) if part) or scan_id
        secondary_parts = []
        if resume_name:
            secondary_parts.append(f"Resume: {resume_name}")
        if status:
            secondary_parts.append(status)
        if timestamp:
            secondary_parts.append(timestamp)
        if source:
            secondary_parts.append(source)
        options.append(
            {
                "scan_id": scan_id,
                "company": company,
                "title": title,
                "resume": resume_name,
                "status": status,
                "primary": primary,
                "secondary": " · ".join(secondary_parts),
            }
        )
    return options


def _advanced_diagnostics_selector_html(options: list[dict], selected_scan_id: str = "") -> str:
    selected_scan_id = str(selected_scan_id or "").strip()
    if not options:
        return """
      <section class="card advanced-diagnostics-selector-card">
        <div class="section-header">
          <div>
            <h2>Choose scan context</h2>
            <div class="subtext">
              No scan diagnostics available yet. Open diagnostics from an AI Optimize Scan after saving or loading a scan.
            </div>
          </div>
        </div>
      </section>
        """.strip()

    option_rows = ['<option value="">Choose a saved scan...</option>']
    for option in options:
        scan_id = str(option.get("scan_id") or "")
        label = str(option.get("primary") or scan_id)
        secondary = str(option.get("secondary") or "")
        option_label = f"{label} — {secondary}" if secondary else label
        selected_attr = " selected" if scan_id and scan_id == selected_scan_id else ""
        option_rows.append(
            f'<option value="{escape(scan_id, quote=True)}"{selected_attr}>{escape(option_label)}</option>'
        )

    return f"""
      <section class="card advanced-diagnostics-selector-card">
        <div class="section-header advanced-diagnostics-selector-header">
          <div>
            <h2>Choose scan context</h2>
            <div class="subtext">
              Select a saved scan to open scan-specific diagnostics.
            </div>
          </div>
        </div>
        <form class="advanced-diagnostics-context-form" action="/advanced-diagnostics" method="get">
          <label class="scan-workspace-input-group advanced-diagnostics-context-select-wrap">
            <span class="scan-workspace-input-label">Saved scan</span>
            <select
              class="scan-workspace-input advanced-diagnostics-context-select"
              id="advancedDiagnosticsScanSelect"
              name="saved_scan_id"
              aria-label="Saved scan diagnostics context"
            >
              {"".join(option_rows)}
            </select>
          </label>
          <button
            type="submit"
            class="ghost-btn btn-sm advanced-diagnostics-open-btn"
            data-advanced-diagnostics-open
            disabled
          >
            Open diagnostics
          </button>
        </form>
      </section>
    """.strip()

_PLANNING_JSON_CONTEXT_SUFFIXES = ("__tailoring.json", "_tailoring.json", ".json")


def _resolve_workspace_route_resume_name(
    resume: str = "",
    *,
    packet_json: str = "",
    tailoring_json: str = "",
    output_dir: str = "",
) -> str:
    raw_name = Path(str(resume or "").replace("\\", "/")).name
    if raw_name.lower().endswith(_PLANNING_JSON_CONTEXT_SUFFIXES):
        try:
            return services.resolve_resume_preview_name_from_planning_context(
                resume_name=raw_name,
                packet_json_path=packet_json or tailoring_json or "",
                output_dir=Path(output_dir) if output_dir else services.DEFAULT_OUTPUT_DIR,
            )
        except Exception:
            return ""
    return raw_name


@router.get("/planning", response_class=HTMLResponse)
def planning_dashboard() -> str:
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Planning Detail Dashboard</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=ui_redesign_v44_shell_menu_clearance" />
</head>
<body>
{render_top_shell("/planning")}
  <div class="page">
    <header class="page-header">
      <div>
        <h1>Planning Detail Dashboard</h1>
        <p class="subtext">Wide planning view with queue, selector state, fallback, and operator decision fields.</p>
      </div>
    </header>

    <section class="card controls-card">
      <div class="dashboard-toolbar dashboard-toolbar--planning">
        <div class="dashboard-toolbar-left dashboard-toolbar-left--planning">
          <div class="control-group dashboard-field dashboard-field--action">
            <label>Action</label>
            <div class="multi-select" id="planningActionFilter" data-placeholder="All">
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

          <div class="control-group dashboard-field planning-field--winner-bucket">
            <label>Match Strength</label>
            <div class="multi-select" id="planningWinnerBucket" data-placeholder="All">
              <button type="button" class="multi-select-trigger" aria-haspopup="menu" aria-expanded="false">
                <span class="multi-select-trigger-label">All</span>
                <span class="multi-select-trigger-icon">▾</span>
              </button>


              <div class="multi-select-menu" role="menu" hidden>
                <button type="button" class="multi-select-option" data-value="strong" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">Excellent match</span>
                </button>
                <button type="button" class="multi-select-option" data-value="solid" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">Strong match</span>
                </button>
                <button type="button" class="multi-select-option" data-value="moderate" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">Moderate match</span>
                </button>
                <button type="button" class="multi-select-option" data-value="weak" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">Weak match</span>
                </button>
                <button type="button" class="multi-select-option" data-value="filtered_out" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">No credible match</span>
                </button>
              </div>
            </div>
          </div>

          <div class="control-group dashboard-field planning-field--tailoring">
            <label>Tailoring</label>
            <div class="multi-select" id="planningTailoringFilter" data-placeholder="All">
              <button type="button" class="multi-select-trigger" aria-haspopup="menu" aria-expanded="false">
                <span class="multi-select-trigger-label">All</span>
                <span class="multi-select-trigger-icon">▾</span>
              </button>

              <div class="multi-select-menu" role="menu" hidden>
                <button type="button" class="multi-select-option" data-value="ready" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">Ready</span>
                </button>
                <button type="button" class="multi-select-option" data-value="review" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">Review</span>
                </button>
                <button type="button" class="multi-select-option" data-value="no_safe_rewrites" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">No safe rewrites</span>
                </button>
                <button type="button" class="multi-select-option" data-value="unavailable" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">Unavailable</span>
                </button>
              </div>
            </div>
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
            <input type="number" id="planningLimitInput" value="15" min="1" max="100" />
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
      <div class="section-header planning-table-header">
        <h2>Planning Detail Table</h2>

        <div class="planning-table-header-right">
          <div class="planning-pagination-inline" id="planningPaginationBar">
            <div class="subtext planning-pagination-meta" id="planningPaginationMeta">
              Page 1 of 1
            </div>
            <div class="planning-pagination-actions" id="planningPaginationActions"></div>
          </div>

          <div class="subtext" id="planningTableMeta">Loading...</div>
        </div>
      </div>

      <div class="table-wrap">
        <table id="planningTable" class="resizable-table">
          <colgroup id="planningTableColgroup">
            <col data-col-key="queue_rank" style="width: 110px;" />
            <col data-col-key="job_title" style="width: 320px;" />
            <col data-col-key="posted_at" style="width: 150px;" />
            <col data-col-key="recommendation" style="width: 260px;" />
            <col data-col-key="packet_status" style="width: 170px;" />
            <col data-col-key="winner_score" style="width: 120px;" />
            <col data-col-key="selected_resume" style="width: 240px;" />
            <col class="table-static-col" data-static-col-key="review" style="width: 150px;" />
          </colgroup>

          <thead>
            <tr>
              <th data-col-key="queue_rank">
                <div class="resizable-col-content"><span class="resizable-col-label">Rank</span></div>
                <span class="col-resize-handle" data-resize-key="queue_rank"></span>
              </th>
              <th data-col-key="job_title">
                <div class="resizable-col-content"><span class="resizable-col-label">Job title</span></div>
                <span class="col-resize-handle" data-resize-key="job_title"></span>
              </th>
              <th data-col-key="posted_at">
                <div class="resizable-col-content"><span class="resizable-col-label">Posted at</span></div>
                <span class="col-resize-handle" data-resize-key="posted_at"></span>
              </th>
              <th data-col-key="recommendation">
                <div class="resizable-col-content"><span class="resizable-col-label">Recommendation</span></div>
                <span class="col-resize-handle" data-resize-key="recommendation"></span>
              </th>
              <th data-col-key="packet_status">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Packet / Workspace</span>
                  <span class="packet-info-icon" title="A packet is a review bundle for this job. It includes the job, selected resume, match signals, gaps, and tailoring guidance. It does not apply to the job." aria-label="A packet is a review bundle for this job. It includes the job, selected resume, match signals, gaps, and tailoring guidance. It does not apply to the job.">ⓘ</span>
                </div>
                <span class="col-resize-handle" data-resize-key="packet_status"></span>
              </th>
              <th data-col-key="winner_score">
                <div class="resizable-col-content"><span class="resizable-col-label">Match</span></div>
                <span class="col-resize-handle" data-resize-key="winner_score"></span>
              </th>
              <th data-col-key="selected_resume">
                <div class="resizable-col-content"><span class="resizable-col-label">Selected Resume</span></div>
                <span class="col-resize-handle" data-resize-key="selected_resume"></span>
              </th>
              <th class="sticky-apply-col apply-col-fixed">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Review</span>
                </div>
              </th>
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

            <div
              id="resumeChoicePreviewPages"
              class="resume-choice-preview-pages hidden"
              aria-label="Resume quick preview"
            ></div>

            <div class="resume-choice-loading-overlay hidden" id="resumeChoiceLoadingOverlay">
              <div class="resume-choice-loading-card">
                <div class="loading-spinner"></div>
                <div class="resume-choice-loading-title" id="resumeChoiceLoadingTitle">
                  Generating tailoring suggestions
                </div>
                <div class="resume-choice-loading-text" id="resumeChoiceLoadingText">
                  Rebuilding packet and tailoring for the selected resume.
                </div>
                <div class="resume-choice-loading-steps hidden" id="resumeChoiceLoadingSteps"></div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="modal-actions resume-choice-modal-actions">
        <div class="resume-choice-status" id="resumeChoiceSaveStatus">No resume selected yet.</div>
        <div class="resume-choice-actions-right">
          <button class="ghost-btn" id="resumeChoiceCancelBtn" type="button">Close</button>
          <button class="ghost-btn" id="resumeChoiceGenerateLlmBtn" type="button" disabled>
            Generate LLM Tailoring
          </button>
          <button id="resumeChoiceSelectBtn" type="button" disabled>Select Resume</button>
        </div>
      </div>
    </div>
  </section>
  <section class="modal-backdrop hidden" id="tailoringModal">
    <div class="modal-card pipeline-modal-card tailoring-modal-card">
      <div class="modal-header">
        <div>
          <h3>Resume suggestions</h3>
          <div class="subtext" id="tailoringModalMeta">Suggested resume updates for this job.</div>
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
        <section class="card tailoring-overview-card tailoring-overview-card--compact">
          <div class="modal-body tailoring-meta-grid tailoring-meta-grid--compact">
            <div class="info-pair tailoring-meta-item">
              <span class="label">Company</span>
              <span id="tailoringModalCompany">-</span>
            </div>

            <div class="info-pair tailoring-meta-item">
              <span class="label">Role</span>
              <span id="tailoringModalTitle">-</span>
            </div>

            <div class="info-pair tailoring-meta-item">
              <span class="label">Status</span>
              <span id="tailoringModalStatus" class="tailoring-status-value">-</span>
            </div>
          </div>
        </section>

        <section class="card tailoring-primary-card">
          <div class="section-header">
            <div>
              <h3>Suggested changes</h3>
              <div class="subtext">
                Start here. These are the most useful resume suggestions for this job.
              </div>
            </div>
          </div>

          <div id="tailoringInteractiveSummary" class="tailoring-interactive-shell">
            <div class="tailoring-empty-state">
              Loading suggested changes...
            </div>
          </div>
        </section>

        <section class="card tailoring-primary-card hidden">
          <div class="section-header">
            <h3>Score preview</h3>
          </div>

          <div id="tailoringPatchPreviewSummary" class="tailoring-interactive-shell"></div>
        </section>

        <section class="card tailoring-primary-card hidden">
          <div class="section-header">
            <div>
              <h3>Saved patch preview</h3>
              <div class="subtext">
                Only shown when a saved patch selection or patch impact preview exists.
              </div>
            </div>
          </div>

          <div id="tailoringPatchSelectionShell" class="tailoring-patch-selection-shell"></div>
        </section>

        <details class="card tailoring-accordion">
                  <section class="card tailoring-manual-accordion">
          <button
            type="button"
            class="tailoring-manual-accordion-toggle"
            data-tailoring-accordion-toggle="tailoringTechnicalDetailsPanel"
            aria-expanded="false"
            aria-controls="tailoringTechnicalDetailsPanel"
          >
            <span class="tailoring-manual-accordion-label">Technical details</span>
          </button>

          <div id="tailoringTechnicalDetailsPanel" class="tailoring-manual-accordion-panel hidden">
            <div class="modal-body tailoring-meta-grid">
              <div class="info-pair tailoring-meta-item">
                <span class="label">Issue</span>
                <span id="tailoringModalError" class="tailoring-error-value">-</span>
              </div>

              <div class="info-pair tailoring-meta-item tailoring-meta-item--path">
                <span class="label">Notes file</span>
                <span id="tailoringModalMarkdownPath" class="tailoring-path-value">-</span>
              </div>

              <div class="info-pair tailoring-meta-item tailoring-meta-item--path">
                <span class="label">Rule-based JSON</span>
                <span id="tailoringModalJsonPath" class="tailoring-path-value">-</span>
              </div>

              <div class="info-pair tailoring-meta-item tailoring-meta-item--path">
                <span class="label">AI JSON</span>
                <span id="tailoringModalLlmJsonPath" class="tailoring-path-value">-</span>
              </div>

              <div class="info-pair tailoring-meta-item tailoring-meta-item--path">
                <span class="label">Packet JSON</span>
                <span id="tailoringModalPacketPath" class="tailoring-path-value">-</span>
              </div>
            </div>
          </div>
        </section>

        <section class="card tailoring-manual-accordion tailoring-manual-accordion--notes">
          <button
            type="button"
            class="tailoring-manual-accordion-toggle"
            data-tailoring-accordion-toggle="tailoringFullNotesPanel"
            aria-expanded="false"
            aria-controls="tailoringFullNotesPanel"
          >
            <span class="tailoring-manual-accordion-label">Full notes</span>
          </button>

          <div id="tailoringFullNotesPanel" class="tailoring-manual-accordion-panel tailoring-manual-accordion-panel--notes hidden">
            <div class="section-header tailoring-notes-header">
              <div class="subtext">
                Human-readable notes for deeper review.
              </div>

              <div class="section-header-actions">
                <button
                  type="button"
                  class="ghost-btn tailoring-copy-btn"
                  id="copyTailoringMarkdownBtn"
                  title="Copy notes"
                  aria-label="Copy notes"
                  disabled
                >
                  <span class="tailoring-copy-btn-icon" aria-hidden="true">
                    <svg viewBox="0 0 24 24" focusable="false" aria-hidden="true">
                      <rect x="9" y="9" width="10" height="10" rx="2"></rect>
                      <path d="M15 9V7a2 2 0 0 0-2-2H7a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2"></path>
                    </svg>
                  </span>
                  <span id="copyTailoringMarkdownLabel">Copy notes</span>
                </button>
              </div>
            </div>

            <div id="tailoringMarkdownContent" class="tailoring-artifact tailoring-artifact--markdown">No artifact loaded.</div>
          </div>
        </section>

        <section class="card tailoring-manual-accordion">
          <button
            type="button"
            class="tailoring-manual-accordion-toggle"
            data-tailoring-accordion-toggle="tailoringDeterministicJsonPanel"
            aria-expanded="false"
            aria-controls="tailoringDeterministicJsonPanel"
          >
            <span class="tailoring-manual-accordion-label">Deterministic Tailoring JSON</span>
          </button>

          <div id="tailoringDeterministicJsonPanel" class="tailoring-manual-accordion-panel tailoring-manual-accordion-panel--code hidden">
            <pre id="tailoringJsonContent" class="tailoring-artifact tailoring-artifact--code">No artifact loaded.</pre>
          </div>
        </section>

        <section class="card tailoring-manual-accordion">
          <button
            type="button"
            class="tailoring-manual-accordion-toggle"
            data-tailoring-accordion-toggle="tailoringLlmJsonPanel"
            aria-expanded="false"
            aria-controls="tailoringLlmJsonPanel"
          >
            <span class="tailoring-manual-accordion-label">LLM Tailoring JSON</span>
          </button>

          <div id="tailoringLlmJsonPanel" class="tailoring-manual-accordion-panel tailoring-manual-accordion-panel--code hidden">
            <pre id="tailoringLlmJsonContent" class="tailoring-artifact tailoring-artifact--code">No artifact loaded.</pre>
          </div>
        </section>

        <section class="card tailoring-manual-accordion">
          <button
            type="button"
            class="tailoring-manual-accordion-toggle"
            data-tailoring-accordion-toggle="tailoringPacketJsonPanel"
            aria-expanded="false"
            aria-controls="tailoringPacketJsonPanel"
          >
            <span class="tailoring-manual-accordion-label">Packet JSON</span>
          </button>

          <div id="tailoringPacketJsonPanel" class="tailoring-manual-accordion-panel tailoring-manual-accordion-panel--code hidden">
            <pre id="tailoringPacketJsonContent" class="tailoring-artifact tailoring-artifact--code">No artifact loaded.</pre>
          </div>
        </section>
        </details>
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
  <script src="/static/planning.js?v=planning_ui_20260512_tailoring_tabs8"></script>
</body>
</html>
    """.strip()


@router.get("/scan-workspace", response_class=HTMLResponse)
def scan_workspace_route(
    request: Request,
    company: str = "",
    title: str = "",
    resume: str = "",
    status: str = "",
    job_doc_id: str = "",
    tailoring_json: str = "",
    tailoring_md: str = "",
    tailoring_llm_json: str = "",
    packet_json: str = "",
    saved_scan_id: str = "",
    output_dir: str = "",
) -> str:
    return scan_workspace(
        auth_user=_auth_user_from_request(request),
        company=company,
        title=title,
        resume=resume,
        status=status,
        job_doc_id=job_doc_id,
        tailoring_json=tailoring_json,
        tailoring_md=tailoring_md,
        tailoring_llm_json=tailoring_llm_json,
        packet_json=packet_json,
        saved_scan_id=saved_scan_id,
        output_dir=output_dir,
    )

@router.get("/tailoring-workspace", response_class=HTMLResponse)
def tailoring_workspace(
    company: str = "",
    title: str = "",
    resume: str = "",
    status: str = "",
    job_doc_id: str = "",
    tailoring_json: str = "",
    tailoring_md: str = "",
    tailoring_llm_json: str = "",
    packet_json: str = "",
    output_dir: str = "",
) -> str:
    company_safe = escape(company or "-")
    title_safe = escape(title or "-")
    raw_resume_name = _resolve_workspace_route_resume_name(
        resume,
        packet_json=packet_json,
        tailoring_json=tailoring_json,
        output_dir=output_dir,
    )
    resume_safe = escape(raw_resume_name)
    resume_display_safe = escape(
        Path(raw_resume_name).stem.replace("_", " ") if raw_resume_name else "-"
    )
    status_safe = escape(status or "Suggestions available")

    job_doc_id_safe = escape(job_doc_id or "")
    tailoring_json_safe = escape(tailoring_json or "")
    tailoring_json_key_safe = escape(tailoring_json or "")
    tailoring_md_safe = escape(tailoring_md or "")
    tailoring_llm_json_safe = escape(tailoring_llm_json or "")
    packet_json_safe = escape(packet_json or "")
    packet_json_key_safe = escape(packet_json or "")
    output_dir_safe = escape(output_dir or "")

    scan_query = urlencode(
        {
            "company": company or "",
            "title": title or "",
            "resume": raw_resume_name or "",
            "status": status or "",
            "job_doc_id": job_doc_id or "",
            "tailoring_json": tailoring_json or "",
            "tailoring_md": tailoring_md or "",
            "tailoring_llm_json": tailoring_llm_json or "",
            "packet_json": packet_json or "",
            "output_dir": output_dir or "",
        }
    )
    scan_href_safe = escape(f"/scan-workspace?{scan_query}", quote=True)


    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Tailoring Workspace</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=ui_redesign_v44_shell_menu_clearance" />
  <link rel="stylesheet" href="/static/scan_workspace.css?v=tailoring_workspace_consolidated_v11" />
</head>
<body>
{render_top_shell("/tailoring-workspace")}
  <div
    class="page tailoring-workspace-page"
    data-job-doc-id="{job_doc_id_safe}"
    data-job-company="{company_safe}"
    data-job-title="{title_safe}"
    data-resume-name="{resume_safe}"
    data-tailoring-status="{status_safe}"
    data-tailoring-json-path="{tailoring_json_safe}"
    data-tailoring-json-key="{tailoring_json_key_safe}"
    data-tailoring-md-path="{tailoring_md_safe}"
    data-tailoring-llm-json-path="{tailoring_llm_json_safe}"
    data-packet-json-path="{packet_json_safe}"
    data-packet-json-key="{packet_json_key_safe}"
    data-planning-output-dir="{output_dir_safe}"
  >
    <header class="page-header tailoring-workspace-header">
      <div>
        <h1>Tailoring Workspace</h1>
        <p class="subtext">
          Review suggested bullet replacements on the left and resume preview on the right.
        </p>
      </div>
    </header>

    <section class="card tailoring-workspace-hero">
      <div class="tailoring-workspace-hero-grid">
        <div class="info-pair">
          <span class="label">Company</span>
          <span>{company_safe}</span>
        </div>

        <div class="info-pair">
          <span class="label">Role</span>
          <span>{title_safe}</span>
        </div>

        <div class="info-pair">
          <span class="label">Resume Variant</span>
          <span>{resume_display_safe}</span>
        </div>

        <div class="info-pair">
          <span class="label">Status</span>
          <span id="tailoringWorkspaceStatusValue">{status_safe}</span>
        </div>
      </div>
    </section>

    <section class="tailoring-workspace-layout">
      <section class="card tailoring-workspace-pane tailoring-workspace-pane--left">
        <div class="section-header">
          <div>
            <div class="tailoring-section-title-row">
              <h2>Suggested changes</h2>

              <a
                id="tailoringWorkspaceOpenScanBtn"
                class="ghost-btn tailoring-ai-optimize-btn"
                href="{scan_href_safe}"
              >
                <span class="tailoring-ai-optimize-btn-icon-wrap" aria-hidden="true">
                  <img
                    class="tailoring-ai-optimize-btn-icon"
                    src="/static/media/ai-img.svg"
                    alt=""
                    aria-hidden="true"
                  />
                </span>

                <span class="tailoring-ai-optimize-btn-label">AI optimize</span>
              </a>
            </div>

            <div class="subtext" id="tailoringWorkspaceMeta">
              Loading suggestion set...
            </div>
          </div>
        </div>

        <section
          class="card tailoring-workspace-subcard tailoring-workspace-selected-tabs hidden"
          id="tailoringWorkspaceSelectedTabsShell"
        >
          <div class="scheduler-table-tabs tailoring-selected-tabs-shell">
            <div class="scheduler-tab-row tailoring-selected-tab-row" id="tailoringWorkspaceSelectedTabRow">
              <button
                type="button"
                class="scheduler-tab-btn tailoring-selected-tab-btn tailoring-selected-tab-btn--ready active"
                id="tailoringWorkspaceSelectedReadyTab"
                data-tailoring-selected-tab="ready"
              >
                Ready
              </button>

              <button
                type="button"
                class="scheduler-tab-btn tailoring-selected-tab-btn tailoring-selected-tab-btn--review"
                id="tailoringWorkspaceSelectedReviewTab"
                data-tailoring-selected-tab="review"
              >
                Review
              </button>

              <button
                type="button"
                class="scheduler-tab-btn tailoring-selected-tab-btn tailoring-selected-tab-btn--free-edit"
                id="tailoringWorkspaceSelectedFreeEditTab"
                data-tailoring-selected-tab="free_edit"
              >
                Free Edit
              </button>
            </div>
          </div>
        </section>

        <div
          id="tailoringWorkspaceInteractiveSummary"
          class="tailoring-interactive-shell tailoring-workspace-content"
        >
          <div class="tailoring-empty-state">
            Loading suggested changes...
          </div>
        </div>

        <section id="tailoringWorkspaceSavedSelectionCard" class="card tailoring-workspace-subcard hidden">
          <div class="section-header section-header--compact">
            <div>
              <h3>Saved selection</h3>
              <div class="subtext">
                Last persisted suggestion choice for this job/resume pair.
              </div>
            </div>
          </div>

          <div id="tailoringWorkspaceSavedSelectionShell"></div>
        </section>
      </section>
      <section class="card tailoring-workspace-pane tailoring-workspace-pane--right">
        <div class="section-header">
          <div>
            <h2>Resume preview</h2>
            <div class="subtext">
              Review the selected resume variant here while checking suggestion coverage on the left.
            </div>
          </div>
        </div>
        
        <div class="tailoring-preview-shell">
          <div class="tailoring-preview-canvas tailoring-preview-canvas--pdfjs">
            <div class="tailoring-workspace-preview-header">
              <div class="tailoring-workspace-preview-header-main">
                <div class="subtext">Current resume preview</div>

                <div class="tailoring-workspace-preview-title-row">
                  <div
                    class="tailoring-workspace-preview-name"
                    id="tailoringWorkspacePreviewName"
                  >
                    {resume_display_safe}
                  </div>

                  <button
                    type="button"
                    class="ghost-btn tailoring-workspace-mode-toggle"
                    id="tailoringWorkspaceModeToggleBtn"
                    aria-label="Switch to edit mode"
                    aria-pressed="false"
                    data-preview-mode="pdf"
                  >
                    <span
                      class="tailoring-workspace-mode-toggle-segment tailoring-workspace-mode-toggle-segment--pdf is-active"
                      data-mode-segment="pdf"
                      aria-hidden="true"
                    >
                      <span class="tailoring-workspace-icon tailoring-workspace-icon--preview"></span>
                    </span>

                    <span
                      class="tailoring-workspace-mode-toggle-separator"
                      aria-hidden="true"
                    ></span>

                    <span
                      class="tailoring-workspace-mode-toggle-segment tailoring-workspace-mode-toggle-segment--edit"
                      data-mode-segment="edit"
                      aria-hidden="true"
                    >
                      <span class="tailoring-workspace-mode-image-icon"></span>
                    </span>
                  </button>
                </div>

                <div
                  class="subtext tailoring-workspace-selection-status"
                  id="tailoringWorkspaceSelectionStatus"
                  aria-live="polite"
                >
                  No actionable suggestions selected yet.
                </div>
              </div>

              <div class="tailoring-workspace-preview-header-actions">
                <span class="tailoring-workspace-action-tooltip" data-tooltip="Discard selection">
                  <button
                    type="button"
                    class="ghost-btn btn-sm tailoring-workspace-icon-btn"
                    id="tailoringWorkspaceDiscardBtn"
                    aria-label="Discard selection"
                    disabled
                  >
                    <span
                      class="tailoring-workspace-icon tailoring-workspace-icon--discard"
                      aria-hidden="true"
                    ></span>
                  </button>
                </span>

                <span class="tailoring-workspace-action-tooltip" data-tooltip="Export tailored draft">
                  <button
                    type="button"
                    class="ghost-btn btn-sm tailoring-workspace-icon-btn"
                    id="tailoringWorkspaceDownloadBtn"
                    aria-label="Export tailored draft"
                  >
                    <span
                      class="tailoring-workspace-icon tailoring-workspace-icon--download"
                      aria-hidden="true"
                    ></span>
                  </button>
                </span>

                <span class="tailoring-workspace-action-tooltip" data-tooltip="Save changes">
                  <button
                    type="button"
                    class="btn-sm tailoring-workspace-icon-btn tailoring-workspace-icon-btn--save"
                    id="tailoringWorkspaceSaveSelectionBtn"
                    aria-label="Save changes"
                    disabled
                  >
                    <span
                      class="tailoring-workspace-icon tailoring-workspace-icon--save"
                      aria-hidden="true"
                    ></span>
                  </button>
                </span>
              </div>
            </div>
            <div class="tailoring-workspace-preview-toolbar">
              <div class="tailoring-workspace-preview-toolbar-left">
                <button
                  type="button"
                  class="ghost-btn btn-sm"
                  id="tailoringWorkspaceZoomOutBtn"
                  aria-label="Zoom out"
                >
                  −
                </button>

                <button
                  type="button"
                  class="ghost-btn btn-sm tailoring-workspace-zoom-value"
                  id="tailoringWorkspaceZoomResetBtn"
                  aria-label="Reset zoom"
                >
                  100%
                </button>

                <button
                  type="button"
                  class="ghost-btn btn-sm"
                  id="tailoringWorkspaceZoomInBtn"
                  aria-label="Zoom in"
                >
                  +
                </button>
              </div>

              <div class="subtext" id="tailoringWorkspacePreviewMeta">
                Loading PDF preview...
              </div>
            </div>

            <div id="tailoringWorkspaceModeBody" class="tailoring-workspace-mode-body">
              <div
                id="tailoringWorkspaceLiveDraftPreview"
                class="tailoring-interactive-shell tailoring-workspace-mode-panel hidden"
              >
                <div class="tailoring-empty-state">
                  Loading working draft preview...
                </div>
              </div>

              <div
                class="tailoring-workspace-pdf-scroller tailoring-workspace-mode-panel"
                id="tailoringWorkspacePdfScroller"
              >
                <div class="resume-choice-empty" id="tailoringWorkspacePreviewEmpty">
                  Loading PDF preview...
                </div>

                <div
                  id="tailoringWorkspacePdfPages"
                  class="tailoring-workspace-pdf-pages hidden"
                ></div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </section>
  </div>

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=role_onboarding_r6"></script>
  <section class="modal-backdrop hidden" id="tailoringWorkspaceExportModal">
    <div class="modal-card tailoring-workspace-export-modal-card">
      <div class="modal-header">
        <div>
          <h3>Export tailored draft</h3>
          <div class="subtext">
            Export is only available from the saved workspace draft.
          </div>
        </div>
        <button
          class="ghost-btn modal-close-btn"
          id="closeTailoringWorkspaceExportModalBtn"
          type="button"
        >
          Close
        </button>
      </div>

      <div class="tailoring-workspace-export-shell">
        <div class="tailoring-workspace-export-summary">
          <div class="info-pair">
            <span class="label">Resume variant</span>
            <span id="tailoringWorkspaceExportResume">-</span>
          </div>

          <div class="info-pair">
            <span class="label">Export status</span>
            <span id="tailoringWorkspaceExportStatus">-</span>
          </div>
        </div>

        <div class="tailoring-workspace-export-format-grid">
          <button
            type="button"
            class="ghost-btn tailoring-workspace-export-format-btn planning-tailoring-btn--review"
            id="tailoringWorkspaceExportPdfBtn"
          >
            <span class="tailoring-workspace-export-format-title">
              <img
                src="/static/media/pdf-icon.svg"
                alt=""
                class="tailoring-workspace-action-icon"
                aria-hidden="true"
                style="width: 34px; height: 34px; min-width: 34px; min-height: 34px; flex: 0 0 34px;"
              />
              <span>PDF</span>
            </span>
            <span class="tailoring-workspace-export-format-copy">
              Export the saved tailored draft as PDF.
            </span>
          </button>

          <button
            type="button"
            class="ghost-btn tailoring-workspace-export-format-btn planning-tailoring-btn--ready"
            id="tailoringWorkspaceExportWordBtn"
          >
            <span class="tailoring-workspace-export-format-title">
              <img
                src="/static/media/doc-icon.svg"
                alt=""
                class="tailoring-workspace-action-icon"
                aria-hidden="true"
              />
              <span>Word</span>
            </span>
            <span class="tailoring-workspace-export-format-copy">
              Export the saved tailored draft as .docx.
            </span>
          </button>
        </div>
        </div>
    </div>
  </section>
  <script src="/static/planning.js?v=planning_ui_20260512_tailoring_tabs8"></script>
</body>
</html>
    """.strip()


def _scan_workspace_advanced_diagnostics_html() -> str:
    return """
              <section
                class="scan-workspace-advanced-diagnostics admin-diagnostics-shell"
                id="scanWorkspaceAdvancedDiagnostics"
              >
                <div class="admin-diagnostics-heading">
                  <h2>Advanced diagnostics</h2>
                </div>
                <p class="subtext scan-workspace-advanced-diagnostics-help">
                  Internal workflow controls and readbacks for debugging. These do not apply to jobs automatically.
                </p>
                <div class="admin-diagnostics-action-bar" aria-label="Diagnostics action safety">
                  <div class="admin-diagnostics-action-copy">
                    <strong>Selections are review-only</strong>
                    <span>Selecting diagnostics does not run them. Use Run selected diagnostics when execution is enabled.</span>
                    <span>Diagnostics never apply to jobs automatically.</span>
                  </div>
                  <div class="admin-diagnostics-action-buttons">
                    <button
                      type="button"
                      class="admin-diagnostics-run-btn"
                      data-admin-diagnostics-run
                      disabled
                      title="Execution is not enabled yet. Selections are for admin review only."
                    >
                      Run selected diagnostics
                    </button>
                    <button
                      type="button"
                      class="admin-diagnostics-clear-btn"
                      data-admin-diagnostics-clear
                    >
                      Clear selections
                    </button>
                  </div>
                  <p class="subtext admin-diagnostics-action-note">
                    Execution is not enabled yet. Selections are for admin review only.
                  </p>
                </div>
                <div class="scan-workspace-advanced-diagnostics-grid admin-diagnostics-grid">
                  <section class="admin-diagnostics-card admin-diagnostics-card--context">
                    <h3>Scan context summary</h3>
                    <p class="subtext">
                      Admin-only controls for the scan context selected above.
                    </p>
                  </section>
                  <section class="admin-diagnostics-card admin-diagnostics-card--generation">
                    <h3>Generation diagnostics</h3>
                    <p class="subtext admin-diagnostics-card-help">
                      Controls for suggestion and exact-change generation checks.
                    </p>
                    <div class="admin-diagnostics-card-fields">
              <label
                class="subtext scan-workspace-live-tailoring-toggle"
                for="scanWorkspaceLiveTailoringSuggestionToggle"
              >
                <input
                  type="checkbox"
                  id="scanWorkspaceLiveTailoringSuggestionToggle"
                />
                Live tailoring suggestions
              </label>
              <label
                class="subtext scan-workspace-live-exact-change-toggle"
                for="scanWorkspaceLiveExactChangeProposalToggle"
              >
                <input
                  type="checkbox"
                  id="scanWorkspaceLiveExactChangeProposalToggle"
                />
                Live exact change proposals
              </label>
              <label
                class="subtext scan-workspace-manual-exact-change-acceptance-toggle"
                for="scanWorkspaceManualExactChangeAcceptanceToggle"
              >
                <input
                  type="checkbox"
                  id="scanWorkspaceManualExactChangeAcceptanceToggle"
                />
                Accept selected exact changes
              </label>
              <input
                type="text"
                class="scan-workspace-manual-exact-change-ids-input"
                id="scanWorkspaceAcceptedExactChangeProposalIds"
                placeholder="Accepted proposal IDs"
                aria-label="Accepted exact change proposal IDs"
              />
                    </div>
                  </section>
                  <section class="admin-diagnostics-card admin-diagnostics-card--artifact-safety">
                    <h3>Resume artifact safety</h3>
                    <p class="subtext admin-diagnostics-card-help">
                      Checks protected resume-copy and artifact verification workflow.
                    </p>
                    <div class="admin-diagnostics-card-fields">
              <label
                class="subtext scan-workspace-guarded-resume-copy-artifact-toggle"
                for="scanWorkspaceGuardedResumeCopyArtifactToggle"
              >
                <input
                  type="checkbox"
                  id="scanWorkspaceGuardedResumeCopyArtifactToggle"
                />
                Create guarded resume copy
              </label>
              <input
                type="text"
                class="scan-workspace-approved-change-plan-id-input"
                id="scanWorkspaceApprovedChangePlanId"
                placeholder="Approved change plan ID"
                aria-label="Approved change plan ID"
              />
              <label
                class="subtext scan-workspace-guarded-resume-copy-artifact-verification-toggle"
                for="scanWorkspaceGuardedResumeCopyArtifactVerificationToggle"
              >
                <input
                  type="checkbox"
                  id="scanWorkspaceGuardedResumeCopyArtifactVerificationToggle"
                />
                Verify guarded resume copy
              </label>
              <input
                type="text"
                class="scan-workspace-guarded-resume-copy-artifact-id-input"
                id="scanWorkspaceGuardedResumeCopyArtifactId"
                placeholder="Guarded artifact ID"
                aria-label="Guarded resume copy artifact ID"
              />
                    </div>
                  </section>
                  <section class="admin-diagnostics-card admin-diagnostics-card--review-packet">
                    <h3>Review packet/operator decision</h3>
                    <p class="subtext admin-diagnostics-card-help">
                      Checks review-packet creation and human decision capture.
                    </p>
                    <div class="admin-diagnostics-card-fields">
              <label
                class="subtext scan-workspace-verified-artifact-operator-review-packet-toggle"
                for="scanWorkspaceVerifiedArtifactOperatorReviewPacketToggle"
              >
                <input
                  type="checkbox"
                  id="scanWorkspaceVerifiedArtifactOperatorReviewPacketToggle"
                />
                Create verified artifact review packet
              </label>
              <input
                type="text"
                class="scan-workspace-verified-artifact-operator-review-artifact-id-input"
                id="scanWorkspaceVerifiedArtifactOperatorReviewArtifactId"
                placeholder="Verified artifact ID"
                aria-label="Verified artifact operator review artifact ID"
              />
              <label
                class="subtext scan-workspace-verified-artifact-operator-decision-toggle"
                for="scanWorkspaceVerifiedArtifactOperatorDecisionToggle"
              >
                <input
                  type="checkbox"
                  id="scanWorkspaceVerifiedArtifactOperatorDecisionToggle"
                />
                Capture verified artifact operator decision
              </label>
              <input
                type="text"
                class="scan-workspace-verified-artifact-operator-decision-packet-id-input"
                id="scanWorkspaceVerifiedArtifactOperatorDecisionPacketId"
                placeholder="Operator review packet ID"
                aria-label="Verified artifact operator decision packet ID"
              />
              <input
                type="text"
                class="scan-workspace-verified-artifact-operator-decision-artifact-id-input"
                id="scanWorkspaceVerifiedArtifactOperatorDecisionArtifactId"
                placeholder="Verified artifact ID"
                aria-label="Verified artifact operator decision artifact ID"
              />
              <select
                class="scan-workspace-verified-artifact-operator-decision-value-input"
                id="scanWorkspaceVerifiedArtifactOperatorDecisionValue"
                aria-label="Verified artifact operator decision value"
              >
                <option value="">Decision</option>
                <option value="accepted">Accepted</option>
                <option value="rejected">Rejected</option>
                <option value="needs_changes">Needs changes</option>
              </select>
                    </div>
                  </section>
                  <section class="admin-diagnostics-card admin-diagnostics-card--handoff">
                    <h3>Manual handoff/readiness</h3>
                    <p class="subtext admin-diagnostics-card-help">
                      Checks manual-only application handoff, readiness, audit, and safety summaries.
                    </p>
                    <div class="admin-diagnostics-card-fields">
              <label
                class="subtext scan-workspace-application-readiness-packet-toggle"
                for="scanWorkspaceApplicationReadinessPacketToggle"
              >
                <input
                  type="checkbox"
                  id="scanWorkspaceApplicationReadinessPacketToggle"
                />
                Create application-readiness packet
              </label>
              <input
                type="text"
                class="scan-workspace-application-readiness-decision-id-input"
                id="scanWorkspaceApplicationReadinessDecisionId"
                placeholder="Operator decision ID"
                aria-label="Application readiness operator decision ID"
              />
              <input
                type="text"
                class="scan-workspace-application-readiness-review-packet-id-input"
                id="scanWorkspaceApplicationReadinessReviewPacketId"
                placeholder="Operator review packet ID"
                aria-label="Application readiness operator review packet ID"
              />
              <input
                type="text"
                class="scan-workspace-application-readiness-artifact-id-input"
                id="scanWorkspaceApplicationReadinessArtifactId"
                placeholder="Verified artifact ID"
                aria-label="Application readiness artifact ID"
              />
              <label
                class="subtext scan-workspace-manual-application-handoff-packet-toggle"
                for="scanWorkspaceManualApplicationHandoffPacketToggle"
              >
                <input
                  type="checkbox"
                  id="scanWorkspaceManualApplicationHandoffPacketToggle"
                />
                Create human-only manual application handoff packet
              </label>
              <input
                type="text"
                class="scan-workspace-manual-handoff-readiness-packet-id-input"
                id="scanWorkspaceManualHandoffReadinessPacketId"
                placeholder="Application readiness packet ID"
                aria-label="Manual handoff application readiness packet ID"
              />
              <input
                type="text"
                class="scan-workspace-manual-handoff-artifact-id-input"
                id="scanWorkspaceManualHandoffArtifactId"
                placeholder="Verified artifact ID"
                aria-label="Manual handoff verified artifact ID"
              />
              <label
                class="subtext scan-workspace-handoff-audit-trail-toggle"
                for="scanWorkspaceHandoffAuditTrailToggle"
              >
                <input
                  type="checkbox"
                  id="scanWorkspaceHandoffAuditTrailToggle"
                />
                Create human-only handoff audit trail
              </label>
              <input
                type="text"
                class="scan-workspace-handoff-audit-handoff-packet-id-input"
                id="scanWorkspaceHandoffAuditHandoffPacketId"
                placeholder="Manual handoff packet ID"
                aria-label="Handoff audit manual handoff packet ID"
              />
              <input
                type="text"
                class="scan-workspace-handoff-audit-readiness-packet-id-input"
                id="scanWorkspaceHandoffAuditReadinessPacketId"
                placeholder="Application readiness packet ID"
                aria-label="Handoff audit application readiness packet ID"
              />
              <input
                type="text"
                class="scan-workspace-handoff-audit-artifact-id-input"
                id="scanWorkspaceHandoffAuditArtifactId"
                placeholder="Verified artifact ID"
                aria-label="Handoff audit verified artifact ID"
              />
              <label
                class="subtext scan-workspace-safety-boundary-summary-toggle"
                for="scanWorkspaceSafetyBoundarySummaryToggle"
              >
                <input
                  type="checkbox"
                  id="scanWorkspaceSafetyBoundarySummaryToggle"
                />
                Create human-only safety boundary summary
              </label>
              <input
                type="text"
                class="scan-workspace-safety-boundary-audit-id-input"
                id="scanWorkspaceSafetyBoundaryAuditTrailId"
                placeholder="Handoff audit trail ID"
                aria-label="Safety boundary handoff audit trail ID"
              />
              <input
                type="text"
                class="scan-workspace-safety-boundary-handoff-packet-id-input"
                id="scanWorkspaceSafetyBoundaryHandoffPacketId"
                placeholder="Manual handoff packet ID"
                aria-label="Safety boundary manual handoff packet ID"
              />
              <input
                type="text"
                class="scan-workspace-safety-boundary-readiness-packet-id-input"
                id="scanWorkspaceSafetyBoundaryReadinessPacketId"
                placeholder="Application readiness packet ID"
                aria-label="Safety boundary application readiness packet ID"
              />
              <input
                type="text"
                class="scan-workspace-safety-boundary-artifact-id-input"
                id="scanWorkspaceSafetyBoundaryArtifactId"
                placeholder="Verified artifact ID"
                aria-label="Safety boundary verified artifact ID"
              />
              <label
                class="subtext scan-workspace-workflow-readiness-checkpoint-toggle"
                for="scanWorkspaceWorkflowReadinessCheckpointToggle"
              >
                <input
                  type="checkbox"
                  id="scanWorkspaceWorkflowReadinessCheckpointToggle"
                />
                Create human-only workflow readiness checkpoint
              </label>
              <input
                type="text"
                class="scan-workspace-workflow-readiness-summary-id-input"
                id="scanWorkspaceWorkflowReadinessSummaryId"
                placeholder="Safety boundary summary ID"
                aria-label="Workflow readiness safety boundary summary ID"
              />
              <input
                type="text"
                class="scan-workspace-workflow-readiness-audit-id-input"
                id="scanWorkspaceWorkflowReadinessAuditTrailId"
                placeholder="Handoff audit trail ID"
                aria-label="Workflow readiness handoff audit trail ID"
              />
              <input
                type="text"
                class="scan-workspace-workflow-readiness-handoff-packet-id-input"
                id="scanWorkspaceWorkflowReadinessHandoffPacketId"
                placeholder="Manual handoff packet ID"
                aria-label="Workflow readiness manual handoff packet ID"
              />
              <input
                type="text"
                class="scan-workspace-workflow-readiness-readiness-packet-id-input"
                id="scanWorkspaceWorkflowReadinessReadinessPacketId"
                placeholder="Application readiness packet ID"
                aria-label="Workflow readiness application readiness packet ID"
              />
              <input
                type="text"
                class="scan-workspace-workflow-readiness-artifact-id-input"
                id="scanWorkspaceWorkflowReadinessArtifactId"
                placeholder="Verified artifact ID"
                aria-label="Workflow readiness verified artifact ID"
              />
                    </div>
                  </section>
                  <section class="admin-diagnostics-card admin-diagnostics-card--readbacks">
                    <h3>Readback status</h3>
                    <p class="subtext admin-diagnostics-card-help">
                      Default-off feature/readback status for this scan context.
                    </p>
                    <div
                      class="scan-workspace-advanced-readbacks"
                      aria-label="Advanced diagnostic readbacks"
                    >
                  <div
                    class="subtext scan-workspace-jd-llm-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceJdLlmReadback"
                    aria-live="polite"
                  >
                    <span>Live JD LLM</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--default">default-off</span>
                  </div>
                  <div
                    class="subtext scan-workspace-tailoring-llm-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceTailoringLlmReadback"
                    aria-live="polite"
                  >
                    <span>Live tailoring LLM</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--default">default-off</span>
                  </div>
                  <div
                    class="subtext scan-workspace-exact-change-llm-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceExactChangeLlmReadback"
                    aria-live="polite"
                  >
                    <span>Live exact change LLM</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--default">default-off</span>
                  </div>
                  <div
                    class="subtext scan-workspace-manual-exact-change-acceptance-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceManualExactChangeAcceptanceReadback"
                    aria-live="polite"
                  >
                    <span>Manual exact change acceptance</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--default">default-off</span>
                  </div>
                  <div
                    class="subtext scan-workspace-guarded-resume-copy-artifact-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceGuardedResumeCopyArtifactReadback"
                    aria-live="polite"
                  >
                    <span>Guarded resume copy artifact</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--default">default-off</span>
                  </div>
                  <div
                    class="subtext scan-workspace-guarded-resume-copy-artifact-verification-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceGuardedResumeCopyArtifactVerificationReadback"
                    aria-live="polite"
                  >
                    <span>Guarded artifact verification</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--default">default-off</span>
                  </div>
                  <div
                    class="subtext scan-workspace-verified-artifact-operator-review-packet-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceVerifiedArtifactOperatorReviewPacketReadback"
                    aria-live="polite"
                  >
                    <span>Verified artifact operator review packet</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--default">default-off</span>
                  </div>
                  <div
                    class="subtext scan-workspace-verified-artifact-operator-decision-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceVerifiedArtifactOperatorDecisionReadback"
                    aria-live="polite"
                  >
                    <span>Verified artifact operator decision</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--default">default-off</span>
                  </div>
                  <div
                    class="subtext scan-workspace-application-readiness-packet-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceApplicationReadinessPacketReadback"
                    aria-live="polite"
                  >
                    <span>Application readiness packet</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--default">default-off</span>
                  </div>
                  <div
                    class="subtext scan-workspace-manual-application-handoff-packet-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceManualApplicationHandoffPacketReadback"
                    aria-live="polite"
                  >
                    <span>Manual application handoff packet</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--default">default-off</span>
                  </div>
                  <div
                    class="subtext scan-workspace-handoff-audit-trail-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceHandoffAuditTrailReadback"
                    aria-live="polite"
                  >
                    <span>Handoff audit trail</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--default">default-off</span>
                  </div>
                  <div
                    class="subtext scan-workspace-safety-boundary-summary-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceSafetyBoundarySummaryReadback"
                    aria-live="polite"
                  >
                    <span>Safety boundary summary</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--default">default-off</span>
                  </div>
                  <div
                    class="subtext scan-workspace-workflow-readiness-checkpoint-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceWorkflowReadinessCheckpointReadback"
                    aria-live="polite"
                  >
                    <span>Workflow readiness checkpoint</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--default">default-off</span>
                  </div>
                  <div
                    class="subtext scan-workspace-agentic-workflow-integration-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceAgenticWorkflowIntegrationReadback"
                    aria-live="polite"
                    aria-label="Agentic workflow demo readiness: waiting for existing scan/evaluation readback"
                  >
                    <span>Agentic workflow demo readiness</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--waiting">waiting for existing scan/evaluation readback</span>
                  </div>
                  <div
                    class="subtext scan-workspace-production-readiness-checkpoint-readback admin-diagnostics-readback-row"
                    id="scanWorkspaceProductionReadinessCheckpointReadback"
                    aria-live="polite"
                    aria-label="Demo readiness: backend checkpoint readback waiting for existing data"
                  >
                    <span>Demo readiness</span>
                    <span class="admin-diagnostics-status-chip admin-diagnostics-status-chip--waiting">backend checkpoint readback waiting for existing data</span>
                  </div>
                    </div>
                  </section>
                </div>
              </section>
    """.strip()


@router.get("/advanced-diagnostics", response_class=HTMLResponse)
def advanced_diagnostics(
    request: Request,
    company: str = "",
    title: str = "",
    resume: str = "",
    status: str = "",
    job_doc_id: str = "",
    tailoring_json: str = "",
    tailoring_md: str = "",
    tailoring_llm_json: str = "",
    packet_json: str = "",
    saved_scan_id: str = "",
    output_dir: str = "",
) -> str:
    admin_user = _require_admin_user(request)
    owner_user_id = _admin_owner_user_id(admin_user)
    scan_context_options = _saved_scan_context_options(owner_user_id=owner_user_id)
    selected_scan_id = str(saved_scan_id or "").strip()
    selected_scan_context = next(
        (
            option
            for option in scan_context_options
            if str(option.get("scan_id") or "").strip() == selected_scan_id
        ),
        {},
    )
    if selected_scan_context:
        company = company or str(selected_scan_context.get("company") or "")
        title = title or str(selected_scan_context.get("title") or "")
        resume = resume or str(selected_scan_context.get("resume") or "")
        status = status or str(selected_scan_context.get("status") or "")

    raw_resume_name = _resolve_workspace_route_resume_name(
        resume,
        packet_json=packet_json,
        tailoring_json=tailoring_json,
        output_dir=output_dir,
    )
    has_scan_context = bool(
        (tailoring_json or "").strip()
        or (tailoring_md or "").strip()
        or (tailoring_llm_json or "").strip()
        or (packet_json or "").strip()
        or (saved_scan_id or "").strip()
    )
    hub_mode = not has_scan_context
    selector_html = (
        _advanced_diagnostics_selector_html(scan_context_options, selected_scan_id="")
        if hub_mode
        else ""
    )
    context_query = urlencode(
        {
            "company": company or "",
            "title": title or "",
            "resume": raw_resume_name or "",
            "status": status or "",
            "job_doc_id": job_doc_id or "",
            "tailoring_json": tailoring_json or "",
            "tailoring_md": tailoring_md or "",
            "tailoring_llm_json": tailoring_llm_json or "",
            "packet_json": packet_json or "",
            "saved_scan_id": saved_scan_id or "",
            "output_dir": output_dir or "",
        }
    )
    scan_href_safe = escape(f"/scan-workspace?{context_query}", quote=True)
    context_summary_html = """
      <section class="card scan-workspace-intake-card advanced-diagnostics-empty-card">
        <div class="section-header">
          <div>
            <h2>No scan selected</h2>
            <div class="subtext">
              Choose a saved scan context to inspect scan-specific controls and readbacks.
            </div>
          </div>
        </div>
      </section>
    """.strip()
    diagnostics_html = ""

    if has_scan_context:
        company_safe = escape(company or "-")
        title_safe = escape(title or "-")
        resume_safe = escape(Path(raw_resume_name).stem.replace("_", " ") if raw_resume_name else "-")
        status_safe = escape(status or "Scan diagnostics context loaded")
        context_id = saved_scan_id or job_doc_id or packet_json or tailoring_json or tailoring_md or tailoring_llm_json
        context_id_safe = escape(Path(str(context_id).replace("\\", "/")).name if context_id else "Scan context")
        back_link_html = f'<a class="ghost-btn btn-sm advanced-diagnostics-back-btn" href="{scan_href_safe}">Back to scan</a>'
        context_summary_html = f"""
      <section class="card scan-workspace-intake-card advanced-diagnostics-context-card">
        <div class="section-header">
          <div>
            <h2>Scan diagnostics context</h2>
            <div class="subtext">{company_safe} / {title_safe}</div>
          </div>
          {back_link_html}
        </div>
        <div class="advanced-diagnostics-context-meta">
          <span><strong>Resume</strong>{resume_safe}</span>
          <span><strong>Status</strong>{status_safe}</span>
          <span><strong>Context</strong>{context_id_safe}</span>
        </div>
      </section>
        """.strip()
        diagnostics_html = f"""
      <section class="card scan-workspace-intake-card scan-workspace-admin-diagnostics-card">
        {_scan_workspace_advanced_diagnostics_html()}
      </section>
        """.strip()

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Advanced Diagnostics</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=ui_redesign_v44_shell_menu_clearance" />
  <link rel="stylesheet" href="/static/scan_workspace_review.css?v=scan_review_v2_75_popover_sticky_actions" />
</head>
<body>
{render_top_shell("/advanced-diagnostics")}
  <main class="page scan-workspace-diagnostics-page">
    <header class="page-header scan-workspace-header-shell scan-workspace-header-shell--minimal">
      <div class="scan-workspace-header-row">
          <div class="scan-workspace-header-copy">
          <h1>Advanced Diagnostics</h1>
          <div class="subtext">Admin workflow diagnostics for saved scan contexts and scan-specific readbacks.</div>
        </div>
      </div>
    </header>

    {selector_html}
    {context_summary_html}
    {diagnostics_html}
  </main>

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=role_onboarding_r6"></script>
  <script>
    (() => {{
      const select = document.getElementById("advancedDiagnosticsScanSelect");
      const button = document.querySelector("[data-advanced-diagnostics-open]");
      if (!select || !button) return;
      const sync = () => {{
        button.disabled = !select.value;
      }};
      select.addEventListener("change", sync);
      sync();
    }})();
    (() => {{
      const root = document.getElementById("scanWorkspaceAdvancedDiagnostics");
      const clearButton = document.querySelector("[data-admin-diagnostics-clear]");
      if (!root || !clearButton) return;
      clearButton.addEventListener("click", () => {{
        root.querySelectorAll('input[type="checkbox"]').forEach((input) => {{
          input.checked = false;
        }});
        root.querySelectorAll('input[type="text"]').forEach((input) => {{
          input.value = "";
        }});
        root.querySelectorAll("select").forEach((selectEl) => {{
          selectEl.value = "";
        }});
      }});
    }})();
  </script>
</body>
</html>
    """.strip()

def scan_workspace(
    auth_user: dict | None = None,
    company: str = "",
    title: str = "",
    resume: str = "",
    status: str = "",
    job_doc_id: str = "",
    tailoring_json: str = "",
    tailoring_md: str = "",
    tailoring_llm_json: str = "",
    packet_json: str = "",
    saved_scan_id: str = "",
    output_dir: str = "",
) -> str:
    company_safe = escape(company or "-")
    title_safe = escape(title or "-")
    raw_resume_name = _resolve_workspace_route_resume_name(
        resume,
        packet_json=packet_json,
        tailoring_json=tailoring_json,
        output_dir=output_dir,
    )
    resume_safe = escape(raw_resume_name)
    resume_display_safe = escape(
        Path(raw_resume_name).stem.replace("_", " ") if raw_resume_name else "-"
    )
    status_safe = escape(status or "Scan preload available")

    job_doc_id_safe = escape(job_doc_id or "")
    tailoring_json_safe = escape(tailoring_json or "")
    tailoring_json_key_safe = escape(tailoring_json or "")
    tailoring_md_safe = escape(tailoring_md or "")
    tailoring_llm_json_safe = escape(tailoring_llm_json or "")
    packet_json_safe = escape(packet_json or "")
    packet_json_key_safe = escape(packet_json or "")
    saved_scan_id_safe = escape(saved_scan_id or "")
    output_dir_safe = escape(output_dir or "")

    loaded_job_context = services.scan_workspace_job_context_payload(
        output_dir=Path(output_dir) if output_dir else services.DEFAULT_OUTPUT_DIR,
        tailoring_json_path=tailoring_json or "",
        job_doc_id=job_doc_id or "",
        company=company or "",
        title=title or "",
    )
    loaded_company = loaded_job_context.get("company") or company or ""
    loaded_title = loaded_job_context.get("title") or title or ""
    loaded_job_url = loaded_job_context.get("job_url") or ""
    loaded_job_description = loaded_job_context.get("job_description_text") or ""
    loaded_company_safe = escape(loaded_company)
    loaded_title_safe = escape(loaded_title)
    loaded_job_url_safe = escape(loaded_job_url, quote=True)
    loaded_job_description_safe = escape(loaded_job_description)

    has_tailoring_context = bool(
        (tailoring_json or "").strip()
        or (tailoring_md or "").strip()
        or (tailoring_llm_json or "").strip()
        or (packet_json or "").strip()
    )

    back_query = urlencode(
        {
            "company": company or "",
            "title": title or "",
            "resume": raw_resume_name or "",
            "status": status or "",
            "job_doc_id": job_doc_id or "",
            "tailoring_json": tailoring_json or "",
            "tailoring_md": tailoring_md or "",
            "tailoring_llm_json": tailoring_llm_json or "",
            "packet_json": packet_json or "",
            "output_dir": output_dir or "",
        }
    )
    back_href_safe = escape(f"/tailoring-workspace?{back_query}", quote=True)

    tailoring_back_link_html = ""
    power_edit_link_html = ""
    if has_tailoring_context:
        tailoring_back_link_html = f"""
          <a class="ghost-btn tailoring-scan-back-btn" href="{back_href_safe}">
            Back to Tailoring
          </a>
        """.strip()

        power_edit_link_html = f"""
          <a
            class="scan-workspace-power-edit-link"
            href="{back_href_safe}"
          >
            Prefer full control? Use Power Edit
          </a>
        """.strip()

    has_saved_scan_context = bool(saved_scan_id)
    has_scan_diagnostics_context = has_tailoring_context or has_saved_scan_context
    scan_diagnostics_query = urlencode(
        {
            "company": company or "",
            "title": title or "",
            "resume": raw_resume_name or "",
            "status": status or "",
            "job_doc_id": job_doc_id or "",
            "tailoring_json": tailoring_json or "",
            "tailoring_md": tailoring_md or "",
            "tailoring_llm_json": tailoring_llm_json or "",
            "packet_json": packet_json or "",
            "saved_scan_id": saved_scan_id or "",
            "output_dir": output_dir or "",
        }
    )
    scan_diagnostics_href_safe = escape(f"/advanced-diagnostics?{scan_diagnostics_query}", quote=True)
    scan_diagnostics_icon_html = ""
    if _is_admin_user(auth_user or {}):
        if has_scan_diagnostics_context:
            scan_diagnostics_icon_html = f'''
              <a
                class="scan-workspace-diagnostics-icon-btn"
                href="{scan_diagnostics_href_safe}"
                aria-label="View diagnostics for this scan"
                title="View diagnostics for this scan"
              >
                <img
                  src="/static/media/adv_diagnostics_img.svg"
                  alt=""
                  aria-hidden="true"
                />
              </a>
            '''.strip()
        else:
            scan_diagnostics_icon_html = '''
              <span
                class="scan-workspace-diagnostics-icon-btn is-disabled"
                aria-disabled="true"
                aria-label="Diagnostics require a saved scan or run context."
                title="Diagnostics require a saved scan or run context."
              >
                <img
                  src="/static/media/adv_diagnostics_img.svg"
                  alt=""
                  aria-hidden="true"
                />
              </span>
            '''.strip()
    scan_initial_mode = "review" if (has_tailoring_context or has_saved_scan_context) else "new_scan"
    scan_initial_mode_safe = escape(scan_initial_mode)

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Optimize Scan</title>
  <link rel="stylesheet" href="/static/vendor/tabler/tabler.min.css" />
  <link rel="stylesheet" href="/static/styles.css?v=ui_redesign_v17" />
  <link rel="stylesheet" href="/static/app_redesign.css?v=ui_redesign_v44_shell_menu_clearance" />
  <link rel="stylesheet" href="/static/scan_workspace_review.css?v=scan_review_v2_75_popover_sticky_actions" />
</head>
<body>
{render_top_shell("/scan-workspace")}
  <div
    class="page scan-workspace-page"
    data-job-doc-id="{job_doc_id_safe}"
    data-job-company="{company_safe}"
    data-job-title="{title_safe}"
    data-resume-name="{resume_safe}"
    data-tailoring-status="{status_safe}"
    data-tailoring-json-path="{tailoring_json_safe}"
    data-tailoring-json-key="{tailoring_json_key_safe}"
    data-tailoring-md-path="{tailoring_md_safe}"
    data-tailoring-llm-json-path="{tailoring_llm_json_safe}"
    data-packet-json-path="{packet_json_safe}"
    data-packet-json-key="{packet_json_key_safe}"
    data-saved-scan-id="{saved_scan_id_safe}"
    data-planning-output-dir="{output_dir_safe}"
    data-scan-initial-mode="{scan_initial_mode_safe}"
    data-scan-mode=""
  >
    <header class="page-header scan-workspace-header-shell scan-workspace-header-shell--minimal">
      <div class="scan-workspace-header-row">
        <div class="scan-workspace-header-copy">
          <h1>AI Optimize Scan</h1>
        </div>

        <div class="scan-workspace-header-actions">
          {tailoring_back_link_html}

        </div>
      </div>
    </header>

    <section
      class="scan-workspace-mode-panel scan-workspace-mode-panel--new"
      data-scan-mode-panel="new_scan"
      hidden
    >
      <section class="card scan-workspace-intake-card">
        <div class="scan-workspace-intake-header">
          <div>
            <h2>New scan</h2>
            <div class="subtext">
              Choose a saved profile resume, paste a job description, and start an AI optimization scan.
            </div>
          </div>

          <button
            type="button"
            class="ghost-btn scan-workspace-sample-btn"
            id="scanWorkspaceViewSampleBtn"
            data-scan-switch-mode="review"
          >
            View a Sample Scan
          </button>
        </div>

        <div class="scan-workspace-intake-grid">
          <section class="scan-workspace-intake-panel scan-workspace-intake-panel--resume">
            <div class="scan-workspace-intake-panel-header">
              <h3>Resume</h3>
              <div class="subtext">
                Select one of the resumes saved in your profile.
              </div>
            </div>

            <label class="scan-workspace-input-group">
              <span class="scan-workspace-input-label">Saved resume</span>
              <select
                id="scanWorkspaceResumeSelect"
                class="scan-workspace-input"
                data-initial-resume="{resume_display_safe if raw_resume_name else ''}"
              >
                <option value="">Loading saved resumes...</option>
              </select>
              <span class="scan-workspace-field-error" id="scanWorkspaceResumeError"></span>
            </label>

            <div class="scan-workspace-input-hint">
              Upload resumes in My Profile if you need more resume options.
            </div>
          </section>

          <section class="scan-workspace-intake-panel scan-workspace-intake-panel--job">
            <div class="scan-workspace-intake-panel-header">
              <h3>Job Description</h3>
              <div class="subtext">
                Paste the target job description to generate the optimization review.
              </div>
            </div>

            <label class="scan-workspace-input-group scan-workspace-input-group--company">
              <span class="scan-workspace-input-label">Company</span>
              <input
                type="text"
                id="scanWorkspaceCompanyInput"
                class="scan-workspace-input"
                value="{loaded_company_safe if loaded_company else ''}"
                placeholder="Company name"
              />
              <span class="scan-workspace-field-error" id="scanWorkspaceCompanyError"></span>
            </label>

            <label class="scan-workspace-input-group scan-workspace-input-group--role">
              <span class="scan-workspace-input-label">Role</span>
              <input
                type="text"
                id="scanWorkspaceRoleInput"
                class="scan-workspace-input"
                value="{loaded_title_safe if loaded_title else ''}"
                placeholder="Job title"
              />
              <span class="scan-workspace-field-error" id="scanWorkspaceRoleError"></span>
            </label>

            <label class="scan-workspace-input-group scan-workspace-input-group--url">
              <span class="scan-workspace-input-label">Job posting URL</span>
              <input
                type="url"
                id="scanWorkspaceJobUrlInput"
                class="scan-workspace-input"
                value="{loaded_job_url_safe if loaded_job_url else ''}"
                placeholder="Posting URL"
              />
              <span class="scan-workspace-field-error" id="scanWorkspaceJobUrlError"></span>
            </label>

          </section>

          <section class="scan-workspace-intake-panel scan-workspace-intake-panel--jd">
            <label class="scan-workspace-input-group scan-workspace-input-group--jd">
              <span class="scan-workspace-input-label">Job description</span>
              <textarea
                id="scanWorkspaceJobDescriptionInput"
                class="scan-workspace-textarea scan-workspace-textarea--jd"
                placeholder="Paste the full job description here."
              >{loaded_job_description_safe}</textarea>
              <span class="scan-workspace-field-error" id="scanWorkspaceJobDescriptionError"></span>
            </label>
          </section>
        </div>

        <div
          class="scan-workspace-intake-validation"
          id="scanWorkspaceIntakeValidation"
          role="status"
          aria-live="polite"
        ></div>

        <div class="scan-workspace-intake-footer">
          {power_edit_link_html}

          <div class="scan-workspace-intake-actions">
            <button
              type="button"
              class="ghost-btn"
              id="scanWorkspaceClearIntakeBtn"
            >
              Clear
            </button>

            <button
              type="button"
              id="scanWorkspaceStartScanBtn"
              class="scan-workspace-start-btn"
              disabled
            >
              Start scan
            </button>
          </div>
        </div>
      </section>
    </section>

    <section
      class="scan-workspace-mode-panel scan-workspace-mode-panel--processing"
      data-scan-mode-panel="processing"
      hidden
    >
      <section class="card scan-workspace-processing-card">
        <div class="scan-workspace-processing-topline">
          <div
            class="scan-workspace-processing-badge"
            id="scanWorkspaceProcessingBadge"
          >
            Preparing scan
          </div>

          <button
            type="button"
            class="ghost-btn scan-workspace-processing-back-btn"
            id="scanWorkspaceProcessingBackBtn"
          >
            Back
          </button>
        </div>

        <div class="scan-workspace-processing-shell">
          <div
            class="scan-workspace-processing-title"
            id="scanWorkspaceProcessingTitle"
          >
            Structuring your content with AI
          </div>

          <div
            class="subtext scan-workspace-processing-subtitle"
            id="scanWorkspaceProcessingSubtitle"
          >
            Preparing scan request...
          </div>

          <div
            class="scan-workspace-processing-summary"
            id="scanWorkspaceProcessingSummary"
          ></div>

          <div
            class="scan-workspace-processing-bar"
            id="scanWorkspaceProcessingBar"
            aria-hidden="true"
          >
            <div class="scan-workspace-processing-bar-fill"></div>
          </div>

          <div
            class="scan-workspace-processing-step-list"
            id="scanWorkspaceProcessingStepList"
          ></div>

          <div
            class="scan-workspace-processing-note"
            id="scanWorkspaceProcessingNote"
          >
            Waiting for the real scan runner. This phase adds the processing shell and stage model only.
          </div>

          <div
            class="scan-workspace-processing-complete"
            id="scanWorkspaceProcessingComplete"
            hidden
          >
            <div class="scan-workspace-processing-check" aria-hidden="true"></div>
            <div>
              <div class="scan-workspace-processing-complete-title">Scan complete</div>
              <div class="subtext">The match report is ready to review.</div>
            </div>
            <button
              type="button"
              class="scan-workspace-processing-ok-btn"
              id="scanWorkspaceProcessingOkBtn"
            >
              OK
            </button>
          </div>
        </div>
      </section>
    </section>

    <section
      class="scan-workspace-mode-panel scan-workspace-mode-panel--review"
      data-scan-mode-panel="review"
      hidden
    >
      <section class="scan-workspace-review-shell scan-review-v2">
        <aside class="card scan-workspace-review-rail scan-review-left-pane">
          <div class="scan-workspace-review-rail-header">
            <div class="scan-workspace-review-score-card scan-workspace-review-score-card--minimal">
              <div class="scan-workspace-review-score-ring" id="scanWorkspaceScoreValue">AI</div>

              <div class="scan-workspace-review-score-copy">
                <div class="scan-workspace-review-score-title">Optimization review</div>

                <div class="scan-workspace-review-context-line" id="scanWorkspaceContextLine">
                  {company_safe} / {title_safe}
                </div>

                <div class="scan-workspace-review-inline-metrics" id="scanWorkspaceScoreMetrics">
                  <span class="scan-workspace-review-inline-metric">
                    <span class="scan-workspace-review-inline-metric-label">Trusted</span>
                    <span class="scan-workspace-review-inline-metric-value" id="scanWorkspaceTrustedCount">0</span>
                  </span>

                  <span class="scan-workspace-review-inline-metric">
                    <span class="scan-workspace-review-inline-metric-label">AI</span>
                    <span class="scan-workspace-review-inline-metric-value" id="scanWorkspaceAiCount">0</span>
                  </span>

                  <span class="scan-workspace-review-inline-metric">
                    <span class="scan-workspace-review-inline-metric-label">Guidance</span>
                    <span class="scan-workspace-review-inline-metric-value" id="scanWorkspaceGuidanceCount">0</span>
                  </span>
                </div>

              </div>
            </div>
          </div>

          <section
            class="card tailoring-workspace-subcard scan-workspace-review-controls"
            id="scanWorkspaceControlsShell"
          >
            <div class="scan-workspace-tabs-shell">
              <div class="scan-workspace-tab-row" id="scanWorkspaceTabRow">
                <button
                  type="button"
                  class="scan-workspace-tab-btn active"
                  data-scan-selected-tab="personal_details"
                  id="scanWorkspacePersonalTab"
                >
                  Personal Details
                </button>

                <button
                  type="button"
                  class="scan-workspace-tab-btn"
                  data-scan-selected-tab="trusted"
                  id="scanWorkspaceTrustedTab"
                >
                  Skills
                </button>

                <button
                  type="button"
                  class="scan-workspace-tab-btn"
                  data-scan-selected-tab="ai_optimize"
                  id="scanWorkspaceAiTab"
                >
                  Searchability
                </button>

                <button
                  type="button"
                  class="scan-workspace-tab-btn"
                  data-scan-selected-tab="formatting"
                  id="scanWorkspaceFormattingTab"
                >
                  Formatting
                </button>

                <button
                  type="button"
                  class="scan-workspace-tab-btn"
                  data-scan-selected-tab="guidance"
                  id="scanWorkspaceGuidanceTab"
                >
                  Recruiter Tips
                </button>
              </div>
            </div>

          </section>

          <div class="scan-workspace-review-rail-body scan-review-left-scroll">
            <div
              id="scanWorkspaceInteractiveSummary"
              class="tailoring-interactive-shell tailoring-workspace-content"
            >
              <div class="tailoring-empty-state">
                Loading scan suggestions...
              </div>
            </div>
          </div>
        </aside>

        <div
          class="scan-workspace-divider scan-review-resizer"
          id="scanWorkspaceDivider"
          role="separator"
          aria-orientation="vertical"
          aria-label="Resize scan workspace panes"
          tabindex="0"
        ></div>

        <section class="card scan-workspace-review-main scan-review-right-pane">
          <div class="scan-workspace-review-main-header scan-review-toolbar">
            <div class="scan-workspace-review-toolbar-row">
              <div class="scan-workspace-review-nav">
                <div
                  class="scan-workspace-review-surface-tabs scan-review-surface-tabs"
                  role="tablist"
                  aria-label="Optimization surfaces"
                >
                  <button
                    type="button"
                    class="scan-workspace-surface-tab is-active"
                    aria-pressed="true"
                    data-scan-surface="resume"
                  >
                    Resume
                  </button>

                  <button
                    type="button"
                    class="scan-workspace-surface-tab"
                    data-scan-surface="job_description"
                    aria-disabled="false"
                  >
                    Job Description
                  </button>
                  {scan_diagnostics_icon_html}
                </div>
              </div>

              <div class="scan-workspace-review-main-actions scan-review-actions">
                <button
                  type="button"
                  class="ghost-btn btn-sm scan-workspace-toolbar-btn"
                  id="scanWorkspaceUndoBtn"
                  aria-label="Undo scan change"
                  aria-disabled="true"
                >
                  <img
                    class="scan-workspace-toolbar-icon"
                    src="/static/media/undo.svg"
                    alt=""
                    aria-hidden="true"
                  />
                  <span class="visually-hidden">Undo</span>
                </button>

              <button
                type="button"
                class="ghost-btn btn-sm scan-workspace-toolbar-btn"
                id="scanWorkspaceRedoBtn"
                aria-label="Redo scan change"
                aria-disabled="true"
              >
                <img
                  class="scan-workspace-toolbar-icon"
                  src="/static/media/redo.svg"
                  alt=""
                  aria-hidden="true"
                />
                <span class="visually-hidden">Redo</span>
              </button>

              <button
                type="button"
                class="ghost-btn btn-sm scan-workspace-toolbar-btn"
                id="scanWorkspaceAcceptAllAiBtn"
              >
                Accept All
              </button>

              <div class="scan-workspace-export-menu-wrap">
                <button
                  type="button"
                  class="ghost-btn btn-sm scan-workspace-toolbar-btn scan-workspace-export-btn"
                  id="scanWorkspaceExportBtn"
                  aria-haspopup="menu"
                  aria-expanded="false"
                >
                  <img
                    class="scan-workspace-toolbar-icon"
                    src="/static/media/download_img.svg"
                    alt=""
                    aria-hidden="true"
                  />
                  <span>Export</span>
                </button>

                <div
                  class="scan-workspace-export-menu hidden"
                  id="scanWorkspaceExportMenu"
                  role="menu"
                  aria-label="Export optimized draft"
                >
                  <button
                    type="button"
                    class="scan-workspace-export-option"
                    data-scan-export-format="pdf"
                    role="menuitem"
                  >
                    <img
                      class="scan-workspace-export-format-icon"
                      src="/static/media/pdf-icon.svg"
                      alt=""
                      aria-hidden="true"
                    />
                    <span>PDF</span>
                  </button>

                  <button
                    type="button"
                    class="scan-workspace-export-option"
                    data-scan-export-format="word"
                    role="menuitem"
                  >
                    <img
                      class="scan-workspace-export-format-icon"
                      src="/static/media/doc-icon.svg"
                      alt=""
                      aria-hidden="true"
                    />
                    <span>DOCX</span>
                  </button>
                </div>
              </div>

              <span
                class="scan-workspace-disabled-action-wrap"
                data-scan-disabled-help="No changes made"
                title="No changes made"
              >
                <button
                  type="button"
                  class="ghost-btn btn-sm scan-workspace-toolbar-btn"
                  data-scan-switch-mode="compare"
                  id="scanWorkspaceCompareBtn"
                  aria-disabled="true"
                  disabled
                  title="No changes made"
                >
                  Compare
                </button>
              </span>

              <span
                class="scan-workspace-disabled-action-wrap"
                data-scan-disabled-help="No changes made"
                title="No changes made"
              >
                <button
                  type="button"
                  class="btn-sm scan-workspace-toolbar-btn scan-workspace-continue-btn"
                  id="scanWorkspaceSaveBtn"
                  aria-disabled="true"
                  disabled
                  title="No changes made"
                >
                  Continue
                </button>
              </span>

              </div>
            </div>

            <div class="scan-workspace-toolbar-context">
              <div class="scan-workspace-toolbar-title-actions">
                <div class="scan-workspace-toolbar-resume-name" id="scanWorkspaceToolbarResumeName">
                  {resume_display_safe}
                </div>

                <button
                  type="button"
                  class="ghost-btn btn-sm scan-workspace-toolbar-btn scan-workspace-rescan-btn"
                  id="scanWorkspaceRescanBtn"
                  hidden
                >
                  Re-scan
                </button>
              </div>

              <div
                class="scan-workspace-workflow-row scan-review-workflow"
                aria-label="Resume optimization workflow"
              >
                <div
                  class="scan-workspace-workflow-step is-active"
                  id="scanWorkspaceAiSuggestionStep"
                >
                  <span class="scan-workspace-workflow-step-number">1</span>
                  <span id="scanWorkspaceAiSuggestionStepLabel">AI Suggestions (0/0)</span>
                </div>

                <div
                  class="scan-workspace-workflow-step is-disabled"
                  id="scanWorkspaceEditStep"
                  aria-disabled="true"
                  title="Edit step will unlock after backend scan editing is connected."
                >
                  <span class="scan-workspace-workflow-step-number">2</span>
                  <span>Edit</span>
                </div>
              </div>
            </div>
          </div>

          <section class="scan-workspace-annotation-shell scan-review-preview-area">
            <div class="scan-workspace-annotation-topbar scan-workspace-annotation-topbar--minimal">
              <div
                class="subtext scan-workspace-annotation-status"
                id="scanWorkspaceAnnotationStatus"
                aria-live="polite"
              ></div>
            </div>

            <div class="scan-workspace-annotation-stage" id="scanWorkspaceAnnotationStage">
              <div
                class="scan-workspace-annotation-overlay"
                id="scanWorkspaceAnnotationOverlay"
                aria-hidden="true"
              ></div>

              <div class="tailoring-preview-shell scan-workspace-review-preview-shell">
                <div class="tailoring-preview-canvas tailoring-preview-canvas--pdfjs">
                  <div class="tailoring-workspace-preview-header scan-workspace-preview-header--minimal">
                    <div class="tailoring-workspace-preview-title-row scan-workspace-preview-title-row--minimal">
                      <div
                        class="tailoring-workspace-preview-name"
                        id="scanWorkspacePreviewName"
                      >
                        {resume_display_safe}
                      </div>

                      <div class="scan-workspace-preview-meta-inline">
                        <span
                          class="subtext tailoring-workspace-selection-status"
                          id="scanWorkspacePreviewStatus"
                          aria-live="polite"
                        >
                          Resume preview
                        </span>

                        <span class="subtext" id="scanWorkspacePreviewMeta">
                          Loading preview...
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="tailoring-workspace-mode-body">
                    <div
                      id="scanWorkspaceLiveDraftPreview"
                      class="scan-workspace-live-draft-preview"
                    >
                      <div class="tailoring-empty-state">
                        Loading reconstructed draft preview...
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div
                class="scan-workspace-suggestion-popover hidden"
                id="scanWorkspaceSuggestionPopover"
                role="dialog"
                aria-live="polite"
                aria-label="AI suggestion details"
              >
                <div class="scan-workspace-suggestion-popover-topline">
                  <div class="scan-workspace-suggestion-popover-kicker">
                    AI suggested change
                  </div>

                  <button
                    type="button"
                    class="ghost-btn btn-sm scan-workspace-suggestion-popover-close"
                    id="scanWorkspaceSuggestionPopoverCloseBtn"
                    aria-label="Close suggestion dialog"
                  >
                    X
                  </button>
                </div>

                <div
                  class="scan-workspace-suggestion-popover-title"
                  id="scanWorkspaceSuggestionPopoverTitle"
                >
                  Select a suggestion anchor to inspect it here.
                </div>

                <div
                  class="scan-workspace-suggestion-popover-copy"
                  id="scanWorkspaceSuggestionPopoverCopy"
                >
                  This shell is now ready for anchored AI suggestion details. Real suggestion positioning and accept/reject state wiring come in the next phase.
                </div>

                <div class="scan-workspace-suggestion-popover-meta">
                  <span
                    class="scan-workspace-suggestion-decision-pill scan-workspace-suggestion-decision-pill--pending"
                    id="scanWorkspaceSuggestionDecisionPill"
                  >
                    Pending
                  </span>

                  <span
                    class="subtext scan-workspace-suggestion-decision-meta"
                    id="scanWorkspaceSuggestionDecisionMeta"
                  >
                    No decision recorded yet.
                  </span>
                </div>

                <div class="scan-workspace-suggestion-popover-actions">
                  <button
                    type="button"
                    class="btn-sm scan-workspace-suggestion-action-btn"
                    id="scanWorkspaceSuggestionAcceptBtn"
                    data-scan-decision-action="accept"
                    disabled
                  >
                    Accept
                  </button>

                  <button
                    type="button"
                    class="ghost-btn btn-sm scan-workspace-suggestion-action-btn"
                    id="scanWorkspaceSuggestionRejectBtn"
                    data-scan-decision-action="reject"
                    disabled
                  >
                    Reject
                  </button>

                  <button
                    type="button"
                    class="ghost-btn btn-sm scan-workspace-suggestion-action-btn"
                    id="scanWorkspaceSuggestionResetBtn"
                    data-scan-decision-action="reset"
                    disabled
                    hidden
                  >
                    Reset
                  </button>
                </div>
              </div>
            </div>

            <div
              class="scan-workspace-continue-modal hidden"
              id="scanWorkspaceContinueModal"
              role="dialog"
              aria-modal="true"
              aria-labelledby="scanWorkspaceContinueModalTitle"
            >
              <div class="scan-workspace-continue-modal-backdrop" data-scan-continue-close="true"></div>

              <div class="scan-workspace-continue-modal-card">
                <button
                  type="button"
                  class="scan-workspace-continue-modal-close"
                  id="scanWorkspaceContinueModalCloseBtn"
                  aria-label="Close continue dialog"
                >
                  ×
                </button>

                <div class="scan-workspace-continue-modal-icon" aria-hidden="true">
                  ✓
                </div>

                <h2 id="scanWorkspaceContinueModalTitle">
                  Great progress! AI suggestions applied.
                </h2>

                <p>
                  Your scan decisions are saved. Continue to Edit Mode to keep editing, or download the optimized draft.
                </p>

                <div class="scan-workspace-continue-modal-actions">
                  <button
                    type="button"
                    class="scan-workspace-continue-modal-primary"
                    id="scanWorkspaceContinueToEditBtn"
                  >
                    Continue to edit
                  </button>

                  <button
                    type="button"
                    class="scan-workspace-continue-modal-secondary"
                    id="scanWorkspaceContinueDownloadBtn"
                  >
                    <img
                      class="scan-workspace-toolbar-icon"
                      src="/static/media/download_img.svg"
                      alt=""
                      aria-hidden="true"
                    />
                    <span>Download</span>
                  </button>
                </div>
              </div>
            </div>
          </section>
        </section>
      </section>
    </section>

    <section
      class="scan-workspace-mode-panel scan-workspace-mode-panel--compare"
      data-scan-mode-panel="compare"
      hidden
    >
      <section class="card scan-workspace-compare-shell">
        <div class="scan-workspace-compare-header">
          <div>
            <h2>Compare</h2>
            <div class="subtext" id="scanWorkspaceCompareStatus">
              Compare the baseline draft against the current accepted AI decision set.
            </div>
          </div>

          <div class="scan-workspace-compare-header-actions">
            <button
              type="button"
              class="ghost-btn btn-sm"
              id="scanWorkspaceCompareRefreshBtn"
            >
              Refresh compare
            </button>

            <button
              type="button"
              class="ghost-btn btn-sm"
              data-scan-switch-mode="review"
            >
              Back to review
            </button>
          </div>
        </div>

        <div class="scan-workspace-compare-summary" id="scanWorkspaceCompareSummary">
          <div class="scan-workspace-compare-summary-card">
            <div class="scan-workspace-compare-summary-label">Compare</div>
            <div class="scan-workspace-compare-summary-value">Loading…</div>
          </div>
        </div>

        <div class="scan-workspace-compare-grid">
          <section class="scan-workspace-compare-pane">
            <div class="scan-workspace-compare-pane-header">
              <div>
                <div class="scan-workspace-compare-pane-kicker">Before</div>
                <div class="scan-workspace-compare-pane-title">Baseline draft</div>
              </div>

              <div class="subtext" id="scanWorkspaceCompareBeforeMeta">
                Loading baseline preview...
              </div>
            </div>

            <div
              class="scan-workspace-compare-pane-body"
              id="scanWorkspaceCompareBeforePane"
            >
              <div class="tailoring-empty-state">
                Loading baseline preview...
              </div>
            </div>
          </section>

          <section class="scan-workspace-compare-pane scan-workspace-compare-pane--after">
            <div class="scan-workspace-compare-pane-header">
              <div>
                <div class="scan-workspace-compare-pane-kicker">After</div>
                <div class="scan-workspace-compare-pane-title">Accepted AI decision set</div>
              </div>

              <div class="subtext" id="scanWorkspaceCompareAfterMeta">
                Waiting for accepted linked suggestions...
              </div>
            </div>

            <div
              class="scan-workspace-compare-pane-body"
              id="scanWorkspaceCompareAfterPane"
            >
              <div class="tailoring-empty-state">
                Accept at least one linked suggestion to generate the after preview.
              </div>
            </div>
          </section>
        </div>
      </section>
    </section>
  </div>

  <script src="/static/vendor/tabler/tabler.min.js"></script>
  <script src="/static/shell.js?v=role_onboarding_r6"></script>
  <script src="/static/planning.js?v=planning_ui_20260518_scan_replacement_markers"></script>
  <script src="/static/scan_workspace.js?v=scan_workspace_rescan6_popover_phrase_scroll"></script>
</body>
</html>
    """.strip()
