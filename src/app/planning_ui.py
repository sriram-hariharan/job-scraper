from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from html import escape
from pathlib import Path

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
  <link rel="stylesheet" href="/static/styles.css?v=tailoring_ui_20260328_1" />
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
                  <span class="multi-select-option-label">APPLY</span>
                </button>
                <button type="button" class="multi-select-option" data-value="APPLY_REVIEW_VARIANTS" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">APPLY_REVIEW_VARIANTS</span>
                </button>
                <button type="button" class="multi-select-option" data-value="MAYBE_TAILOR" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">MAYBE_TAILOR</span>
                </button>
                <button type="button" class="multi-select-option" data-value="SKIP_FOR_NOW" aria-checked="false">
                  <span class="multi-select-option-check">✓</span>
                  <span class="multi-select-option-label">SKIP_FOR_NOW</span>
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
        <details class="card tailoring-accordion tailoring-accordion--notes">
          <summary><span class="tailoring-accordion-summary-label">Full notes</span></summary>

          <div class="tailoring-accordion-body">
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
        </details>

        <details class="card tailoring-accordion">
          <summary><span class="tailoring-accordion-summary-label">Deterministic Tailoring JSON</span></summary>
          <pre id="tailoringJsonContent" class="tailoring-artifact tailoring-artifact--code">No artifact loaded.</pre>
        </details>

        <details class="card tailoring-accordion">
          <summary><span class="tailoring-accordion-summary-label">LLM Tailoring JSON</span></summary>
          <pre id="tailoringLlmJsonContent" class="tailoring-artifact tailoring-artifact--code">No artifact loaded.</pre>
        </details>

        <details class="card tailoring-accordion">
          <summary><span class="tailoring-accordion-summary-label">Packet JSON</span></summary>
          <pre id="tailoringPacketJsonContent" class="tailoring-artifact tailoring-artifact--code">No artifact loaded.</pre>
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

  <script src="/static/shell.js"></script>
  <script src="/static/planning.js?v=tailoring_ui_20260328_1"></script>
</body>
</html>
    """.strip()

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
) -> str:
    company_safe = escape(company or "-")
    title_safe = escape(title or "-")
    raw_resume_name = resume or ""
    resume_safe = escape(raw_resume_name)
    resume_display_safe = escape(
        Path(raw_resume_name).stem.replace("_", " ") if raw_resume_name else "-"
    )
    status_safe = escape(status or "Suggestions available")

    job_doc_id_safe = escape(job_doc_id or "")
    tailoring_json_safe = escape(tailoring_json or "")
    tailoring_md_safe = escape(tailoring_md or "")
    tailoring_llm_json_safe = escape(tailoring_llm_json or "")
    packet_json_safe = escape(packet_json or "")

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Tailoring Workspace</title>
  <link rel="stylesheet" href="/static/styles.css?v=tailoring_workspace_20260328_5" />
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
    data-tailoring-md-path="{tailoring_md_safe}"
    data-tailoring-llm-json-path="{tailoring_llm_json_safe}"
    data-packet-json-path="{packet_json_safe}"
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
          <span>{status_safe}</span>
        </div>
      </div>
    </section>

    <section class="tailoring-workspace-layout">
      <section class="card tailoring-workspace-pane tailoring-workspace-pane--left">
        <div class="section-header">
          <div>
            <h2>Suggested changes</h2>
            <div class="subtext" id="tailoringWorkspaceMeta">
              Loading suggestion set...
            </div>
          </div>
        </div>

        <div
          id="tailoringWorkspaceInteractiveSummary"
          class="tailoring-interactive-shell tailoring-workspace-content"
        >
          <div class="tailoring-empty-state">
            Loading suggested changes...
          </div>
        </div>

        <section class="card tailoring-workspace-subcard hidden">
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

        <section class="card tailoring-workspace-subcard tailoring-workspace-selection-bar">
          <div class="tailoring-workspace-selection-bar-copy">
            <div class="tailoring-workspace-selection-title">Selection actions</div>
            <div class="subtext" id="tailoringWorkspaceSelectionStatus">
              No actionable suggestions selected yet.
            </div>
          </div>

          <div class="tailoring-workspace-selection-actions">
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

            <span class="tailoring-workspace-action-tooltip" data-tooltip="Download resume">
              <button
                type="button"
                class="ghost-btn btn-sm tailoring-workspace-icon-btn"
                id="tailoringWorkspaceDownloadBtn"
                aria-label="Download resume"
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
        </section>
      </section>

      <section class="card tailoring-workspace-pane tailoring-workspace-pane--right">
        <div class="section-header">
          <div>
            <h2>Resume preview</h2>
            <div class="subtext">
              This right pane will become the live resume preview/editor surface.
            </div>
          </div>
        </div>

        <div class="tailoring-preview-shell">
          <div class="tailoring-preview-canvas tailoring-preview-canvas--pdfjs">
            <div class="tailoring-workspace-preview-header">
              <div class="subtext">Current resume preview</div>
              <div class="tailoring-workspace-preview-name" id="tailoringWorkspacePreviewName">
                {resume_display_safe}
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

            <div class="tailoring-workspace-pdf-scroller" id="tailoringWorkspacePdfScroller">
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
      </section>
    </section>
  </div>

  <script src="/static/shell.js"></script>
  <script src="/static/planning.js?v=tailoring_workspace_20260328_5"></script>
</body>
</html>
    """.strip()