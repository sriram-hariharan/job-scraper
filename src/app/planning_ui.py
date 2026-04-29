from fastapi import APIRouter
from fastapi.responses import HTMLResponse
from html import escape
from pathlib import Path
from urllib.parse import urlencode

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
  <link rel="stylesheet" href="/static/styles.css?v=tailoring_ui_20260417_5" />
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
            <col data-col-key="action" style="width: 120px;" />
            <col data-col-key="job_company" style="width: 180px;" />
            <col data-col-key="job_title" style="width: 260px;" />
            <col data-col-key="posted_at" style="width: 160px;" />
            <col data-col-key="winner_resume" style="width: 220px;" />
            <col data-col-key="winner_score" style="width: 120px;" />
            <col data-col-key="runner_up_resume" style="width: 220px;" />
            <col data-col-key="runner_up_score" style="width: 130px;" />
            <col data-col-key="score_gap" style="width: 120px;" />
            <col data-col-key="winner_bucket" style="width: 150px;" />
            <col data-col-key="review_state" style="width: 150px;" />
            <col data-col-key="missing_requirement_count" style="width: 150px;" />
            <col data-col-key="llm_fallback_best_resume" style="width: 220px;" />
            <col data-col-key="llm_fallback_status" style="width: 150px;" />
            <col data-col-key="llm_adjudication_resume" style="width: 180px;" />
            <col data-col-key="operator_decision" style="width: 170px;" />
            <col data-col-key="operator_selected_resume" style="width: 220px;" />
            <col data-col-key="queue_priority_reason" style="width: 260px;" />
            <col data-col-key="tailoring" style="width: 190px;" />
            <col class="table-static-col" data-static-col-key="apply" style="width: 140px;" />
          </colgroup>

          <thead>
            <tr>
              <th data-col-key="queue_rank">
                <div class="resizable-col-content"><span class="resizable-col-label">Queue Rank</span></div>
                <span class="col-resize-handle" data-resize-key="queue_rank"></span>
              </th>
              <th data-col-key="action">
                <div class="resizable-col-content"><span class="resizable-col-label">Action</span></div>
                <span class="col-resize-handle" data-resize-key="action"></span>
              </th>
              <th data-col-key="job_company">
                <div class="resizable-col-content"><span class="resizable-col-label">Company</span></div>
                <span class="col-resize-handle" data-resize-key="job_company"></span>
              </th>
              <th data-col-key="job_title">
                <div class="resizable-col-content"><span class="resizable-col-label">Title</span></div>
                <span class="col-resize-handle" data-resize-key="job_title"></span>
              </th>
              <th data-col-key="posted_at">
                <div class="resizable-col-content"><span class="resizable-col-label">Posted At</span></div>
                <span class="col-resize-handle" data-resize-key="posted_at"></span>
              </th>
              <th data-col-key="winner_resume">
                <div class="resizable-col-content"><span class="resizable-col-label">Winner Resume</span></div>
                <span class="col-resize-handle" data-resize-key="winner_resume"></span>
              </th>
              <th data-col-key="winner_score">
                <div class="resizable-col-content"><span class="resizable-col-label">Winner Score</span></div>
                <span class="col-resize-handle" data-resize-key="winner_score"></span>
              </th>
              <th data-col-key="runner_up_resume">
                <div class="resizable-col-content"><span class="resizable-col-label">Runner-Up Resume</span></div>
                <span class="col-resize-handle" data-resize-key="runner_up_resume"></span>
              </th>
              <th data-col-key="runner_up_score">
                <div class="resizable-col-content"><span class="resizable-col-label">Runner-Up Score</span></div>
                <span class="col-resize-handle" data-resize-key="runner_up_score"></span>
              </th>
              <th data-col-key="score_gap">
                <div class="resizable-col-content"><span class="resizable-col-label">Score Gap</span></div>
                <span class="col-resize-handle" data-resize-key="score_gap"></span>
              </th>
              <th data-col-key="winner_bucket">
                <div class="resizable-col-content"><span class="resizable-col-label">Match Strength</span></div>
                <span class="col-resize-handle" data-resize-key="winner_bucket"></span>
              </th>
              <th data-col-key="review_state">
                <div class="resizable-col-content"><span class="resizable-col-label">Review State</span></div>
                <span class="col-resize-handle" data-resize-key="review_state"></span>
              </th>
              <th data-col-key="missing_requirement_count">
                <div class="resizable-col-content"><span class="resizable-col-label">Missing Req Count</span></div>
                <span class="col-resize-handle" data-resize-key="missing_requirement_count"></span>
              </th>
              <th data-col-key="llm_fallback_best_resume">
                <div class="resizable-col-content"><span class="resizable-col-label">Fallback Best Resume</span></div>
                <span class="col-resize-handle" data-resize-key="llm_fallback_best_resume"></span>
              </th>
              <th data-col-key="llm_fallback_status">
                <div class="resizable-col-content"><span class="resizable-col-label">Fallback Status</span></div>
                <span class="col-resize-handle" data-resize-key="llm_fallback_status"></span>
              </th>
              <th data-col-key="llm_adjudication_resume">
                <div class="resizable-col-content"><span class="resizable-col-label">LLM Review Hint</span></div>
                <span class="col-resize-handle" data-resize-key="llm_adjudication_resume"></span>
              </th>
              <th data-col-key="operator_decision">
                <div class="resizable-col-content"><span class="resizable-col-label">Operator Decision</span></div>
                <span class="col-resize-handle" data-resize-key="operator_decision"></span>
              </th>
              <th data-col-key="operator_selected_resume">
                <div class="resizable-col-content"><span class="resizable-col-label">Operator Selected Resume</span></div>
                <span class="col-resize-handle" data-resize-key="operator_selected_resume"></span>
              </th>
              <th data-col-key="queue_priority_reason">
                <div class="resizable-col-content"><span class="resizable-col-label">Priority Reason</span></div>
                <span class="col-resize-handle" data-resize-key="queue_priority_reason"></span>
              </th>
              <th data-col-key="tailoring">
                <div class="resizable-col-content"><span class="resizable-col-label">Tailor</span></div>
                <span class="col-resize-handle" data-resize-key="tailoring"></span>
              </th>
              <th class="sticky-apply-col apply-col-fixed">
                <div class="resizable-col-content">
                  <span class="resizable-col-label">Apply</span>
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

  <script src="/static/shell.js"></script>
  <script src="/static/planning.js?v=planning_ui_20260427_1"></script>
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
  <link rel="stylesheet" href="/static/styles.css?v=tailoring_workspace_20260417_6" />
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
      </section>
      <div
        class="tailoring-workspace-divider"
        id="tailoringWorkspaceDivider"
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize workspace panes"
        tabindex="0"
      ></div>

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

  <script src="/static/shell.js"></script>
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

        <div
          class="tailoring-workspace-export-note"
          id="tailoringWorkspaceExportHint"
        >
          Save changes before exporting.
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
  <script src="/static/planning.js?v=planning_ui_20260427_1"></script>
</body>
</html>
    """.strip()

@router.get("/scan-workspace", response_class=HTMLResponse)
def scan_workspace(
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
    status_safe = escape(status or "Scan preload available")

    job_doc_id_safe = escape(job_doc_id or "")
    tailoring_json_safe = escape(tailoring_json or "")
    tailoring_md_safe = escape(tailoring_md or "")
    tailoring_llm_json_safe = escape(tailoring_llm_json or "")
    packet_json_safe = escape(packet_json or "")

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
        }
    )
    back_href_safe = escape(f"/tailoring-workspace?{back_query}", quote=True)

    scan_initial_mode = "review" if (tailoring_json or packet_json or raw_resume_name) else "new_scan"
    scan_initial_mode_safe = escape(scan_initial_mode)

    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>AI Optimize Scan</title>
  <link rel="stylesheet" href="/static/styles.css?v=scan_workspace_20260422_2" />
  <link rel="stylesheet" href="/static/scan_workspace.css?v=scan_workspace_phase10_11" />
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
    data-tailoring-md-path="{tailoring_md_safe}"
    data-tailoring-llm-json-path="{tailoring_llm_json_safe}"
    data-packet-json-path="{packet_json_safe}"
    data-scan-initial-mode="{scan_initial_mode_safe}"
    data-scan-mode=""
  >
    <header class="page-header scan-workspace-header-shell scan-workspace-header-shell--minimal">
      <div class="scan-workspace-header-row">
        <div class="scan-workspace-header-copy">
          <h1>AI Optimize Scan</h1>
        </div>

        <div class="scan-workspace-header-actions">
          <a class="ghost-btn tailoring-scan-back-btn" href="{back_href_safe}">
            Back to Tailoring
          </a>

          <button
            type="button"
            class="ghost-btn scan-workspace-sample-btn"
            id="scanWorkspaceHeaderNewScanBtn"
            data-scan-switch-mode="new_scan"
          >
            New Scan
          </button>
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
              Upload or choose a resume, paste a job description, and start an AI optimization scan.
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
          <section class="scan-workspace-intake-panel">
            <div class="scan-workspace-intake-panel-header">
              <h3>Resume</h3>
              <div class="subtext">
                Use the current resume variant or paste resume text for a fresh scan.
              </div>
            </div>

            <label class="scan-workspace-input-group">
              <span class="scan-workspace-input-label">Saved resume variant</span>
              <input
                type="text"
                id="scanWorkspaceResumeNameInput"
                class="scan-workspace-input"
                value="{resume_display_safe if raw_resume_name else ''}"
                placeholder="No saved resume selected yet"
                readonly
              />
            </label>

            <label class="scan-workspace-input-group">
              <span class="scan-workspace-input-label">Resume text</span>
              <textarea
                id="scanWorkspaceResumeTextInput"
                class="scan-workspace-textarea"
                placeholder="Paste resume content here if you want to scan without using the saved variant."
              ></textarea>
            </label>

            <div class="scan-workspace-input-hint">
              A scan can start from either a saved resume variant or pasted resume text.
            </div>
          </section>

          <section class="scan-workspace-intake-panel">
            <div class="scan-workspace-intake-panel-header">
              <h3>Job Description</h3>
              <div class="subtext">
                Paste the target job description to generate the optimization review.
              </div>
            </div>

            <label class="scan-workspace-input-group">
              <span class="scan-workspace-input-label">Company</span>
              <input
                type="text"
                id="scanWorkspaceCompanyInput"
                class="scan-workspace-input"
                value="{company_safe if company else ''}"
                placeholder="Optional company name"
              />
            </label>

            <label class="scan-workspace-input-group">
              <span class="scan-workspace-input-label">Role</span>
              <input
                type="text"
                id="scanWorkspaceRoleInput"
                class="scan-workspace-input"
                value="{title_safe if title else ''}"
                placeholder="Optional job title"
              />
            </label>

            <label class="scan-workspace-input-group">
              <span class="scan-workspace-input-label">Job description</span>
              <textarea
                id="scanWorkspaceJobDescriptionInput"
                class="scan-workspace-textarea scan-workspace-textarea--jd"
                placeholder="Paste the full job description here."
              ></textarea>
            </label>
          </section>
        </div>

        <div class="scan-workspace-intake-footer">
          <a
            class="scan-workspace-power-edit-link"
            href="{back_href_safe}"
          >
            Prefer full control? Use Power Edit
          </a>

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
        </div>
      </section>
    </section>

    <section
      class="scan-workspace-mode-panel scan-workspace-mode-panel--review"
      data-scan-mode-panel="review"
      hidden
    >
      <section class="scan-workspace-review-shell">
        <aside class="card scan-workspace-review-rail">
          <div class="scan-workspace-review-rail-header">
            <div class="scan-workspace-review-score-card scan-workspace-review-score-card--minimal">
              <div class="scan-workspace-review-score-ring" id="scanWorkspaceScoreValue">AI</div>

              <div class="scan-workspace-review-score-copy">
                <div class="scan-workspace-review-score-title">Optimization review</div>

                <div class="scan-workspace-review-context-line" id="scanWorkspaceContextLine">
                  {company_safe} / {title_safe}
                </div>

                <div class="subtext" id="scanWorkspaceMeta">
                  {resume_display_safe}
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
                  data-scan-selected-tab="trusted"
                  id="scanWorkspaceTrustedTab"
                >
                  Trusted
                </button>

                <button
                  type="button"
                  class="scan-workspace-tab-btn"
                  data-scan-selected-tab="ai_optimize"
                  id="scanWorkspaceAiTab"
                >
                  AI Suggestions
                </button>

                <button
                  type="button"
                  class="scan-workspace-tab-btn"
                  data-scan-selected-tab="guidance"
                  id="scanWorkspaceGuidanceTab"
                >
                  Guidance
                </button>
              </div>
            </div>

            <div class="scan-workspace-review-controls-body">
              <div
                class="subtext tailoring-workspace-selection-status"
                id="scanWorkspaceSelectionStatus"
              >
                No scan actions selected yet.
              </div>

              <div class="scan-workspace-review-actions scan-workspace-review-actions--rail">
                <button
                  type="button"
                  class="ghost-btn btn-sm"
                  id="scanWorkspaceSaveBtn"
                >
                  Save
                </button>
              </div>

              <div
                class="subtext scan-workspace-persist-status"
                id="scanWorkspacePersistStatus"
                aria-live="polite"
              >
                Scan decisions are not saved yet.
              </div>
            </div>
          </section>

          <div class="scan-workspace-review-rail-body">
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

        <section class="card scan-workspace-review-main">
          <div class="scan-workspace-review-main-header">
            <div
              class="scan-workspace-review-surface-tabs"
              role="tablist"
              aria-label="Optimization surfaces"
            >
              <button
                type="button"
                class="scan-workspace-surface-tab is-active"
                aria-pressed="true"
              >
                Resume
              </button>

              <button
                type="button"
                class="scan-workspace-surface-tab"
                disabled
              >
                Cover Letter
              </button>

              <button
                type="button"
                class="scan-workspace-surface-tab"
                disabled
              >
                Job Description
              </button>
            </div>

            <div class="scan-workspace-review-main-actions">
              <button
                type="button"
                class="ghost-btn btn-sm scan-workspace-toolbar-btn"
                id="scanWorkspaceAcceptAllAiBtn"
              >
                Accept All
              </button>

              <button
                type="button"
                class="ghost-btn btn-sm scan-workspace-toolbar-btn"
                data-scan-switch-mode="compare"
              >
                Compare
              </button>

              <a
                class="scan-workspace-toolbar-link scan-workspace-toolbar-link--primary"
                id="scanWorkspaceContinueBtn"
                href="{back_href_safe}"
              >
                Continue
              </a>
            </div>
          </div>

          <section class="scan-workspace-annotation-shell">
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
                          Live draft preview
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
                  >
                    Close
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
                  >
                    Reset
                  </button>

                  <button
                    type="button"
                    class="btn-sm scan-workspace-suggestion-action-btn"
                    id="scanWorkspaceSuggestionAcceptBtn"
                    data-scan-decision-action="accept"
                    disabled
                  >
                    Accept
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

  <script src="/static/shell.js"></script>
  <script src="/static/planning.js?v=planning_ui_20260429_scan_d6c"></script>
  <script src="/static/scan_workspace.js?v=scan_workspace_phase10_11"></script>
</body>
</html>
    """.strip()