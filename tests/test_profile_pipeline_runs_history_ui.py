"""Focused UI contracts for the Pipeline Runs history changeover.

The page moved from a wide multi-column admin table to a compact five-column
run-history grid. Detail inspection stays in the existing Pipeline Run Stats
modal, so this page deliberately has no expandable rows and no inline run
details.
"""

from pathlib import Path

from starlette.requests import Request

from src.app.profile_ui import profile_page


ROOT = Path(__file__).resolve().parents[1]
PROFILE_UI = (ROOT / "src/app/profile_ui.py").read_text(encoding="utf-8")
PROFILE_JS = (ROOT / "src/app/static/profile.js").read_text(encoding="utf-8")
APP_REDESIGN_CSS = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")
API_SOURCE = (ROOT / "src/app/api.py").read_text(encoding="utf-8")


def _request() -> Request:
    request = Request(
        {
            "type": "http",
            "method": "GET",
            "path": "/profile",
            "query_string": b"",
            "headers": [],
        }
    )
    request.state.auth_user = {
        "user_id": "pipeline-runs-history-user",
        "access_level": "user",
        "is_admin": False,
    }
    return request


def _render_runs() -> str:
    return PROFILE_JS.split("function renderPipelineRuns(runs) {", 1)[1].split(
        "\nfunction renderPipelineRunsPagination", 1
    )[0]


def _pagination() -> str:
    return PROFILE_JS.split("function renderPipelineRunsPagination() {", 1)[1].split(
        "\nfunction applyPipelineRunsPaginationPayload", 1
    )[0]


def _runs_css() -> str:
    """CSS scoped to the run-history grid only (marker -> re-run modal)."""
    return APP_REDESIGN_CSS.split("profile_pipeline_runs_history_r1", 1)[1].split(
        "#pipelineRunRerunModal {", 1
    )[0]


# --- table structure --------------------------------------------------------


def test_table_exposes_exactly_the_five_history_columns():
    html = profile_page(_request())
    head = html.split('<table class="pipeline-runs-table">', 1)[1].split("</thead>", 1)[0]

    for column in ("<th>Run</th>", "<th>Status</th>", "<th>Output</th>", "<th>Flow</th>"):
        assert column in head
    assert 'class="pipeline-runs-actions-head">Actions</th>' in head
    assert head.count("<th>") + head.count("<th ") == 5


def test_retired_columns_are_gone_from_the_table_presentation():
    html = profile_page(_request())
    head = html.split('<table class="pipeline-runs-table">', 1)[1].split("</thead>", 1)[0]

    for retired in ("Summary", "Final jobs", "Counts", "Settings", "Re-run", "Started"):
        assert f">{retired}</th>" not in head
    # The body colspan follows the new column count.
    assert 'colspan="5"' in html
    assert 'colspan="8"' not in html.split('id="pipelineRunsTableBody"', 1)[1][:400]


def test_no_expandable_rows_dropdown_or_inline_run_details():
    renderer = _render_runs()
    html = profile_page(_request())

    # The approved target image shows an expanded first row; that feature is
    # explicitly rejected - View Stats is the authoritative detail surface.
    for rejected in (
        "data-pipeline-run-expand",
        "data-pipeline-run-toggle",
        "pipeline-run-expander",
        "pipeline-run-row-details",
        "aria-expanded",
        "<details",
    ):
        assert rejected not in renderer, f"expandable-row artifact leaked: {rejected}"
    # No duplicated Run configuration / Pipeline counts panel inside the table.
    assert "Run configuration" not in renderer
    assert "Pipeline counts" not in renderer
    assert "pipeline-run-detail-panel" not in renderer
    assert 'id="pipelineRunsTableBody"' in html


def test_no_mockup_sidebar_was_introduced():
    html = profile_page(_request())
    for rejected in ("pipeline-runs-sidebar", "runs-nav-rail", "data-runs-sidebar"):
        assert rejected not in html
    assert "pipeline-runs-sidebar" not in APP_REDESIGN_CSS


def test_no_sorting_control_was_added():
    renderer = _render_runs()
    html = profile_page(_request())
    head = html.split('<table class="pipeline-runs-table">', 1)[1].split("</thead>", 1)[0]

    assert "sort-header-btn" not in head
    assert "data-pipeline-runs-sort" not in html
    assert "data-pipeline-runs-sort" not in renderer
    assert "aria-sort" not in head


# --- row content ------------------------------------------------------------


def test_run_column_uses_existing_timestamp_and_full_run_id():
    renderer = _render_runs()

    assert "formatPipelineRunHeaderDate(run.started_at" in renderer
    assert 'class="pipeline-run-id" title="${runId}"' in renderer


def test_output_column_uses_final_plus_authoritative_planned_and_packet():
    renderer = _render_runs()

    assert "run.final_job_count ?? counts.final_jobs" in renderer
    # Same authoritative semantics as the Pipeline Run Stats modal: planned and
    # packet jobs come from the persisted summary sentence only.
    assert "pipelineRunPlannedJobCount(run.summary_message" in renderer
    assert "pipelineRunPacketJobCount(run.summary_message" in renderer
    assert "planned" in renderer
    assert "packet" in renderer
    # Never substituted from the separate planning-packet artifact metrics.
    output_block = renderer.split("const outputParts = [];", 1)[1].split("const agenticReviewAction", 1)[0]
    for forbidden in ("planning_packets_total", "planning_packets_generated", "planning_packets_completed"):
        assert forbidden not in output_block


def test_flow_column_uses_real_scraped_filtered_new_final_metrics():
    renderer = _render_runs()

    assert 'pipelineRunFlowStep("Scraped", getFirstMetricValue(counts, ["scraped_jobs", "scraped"]))' in renderer
    assert 'pipelineRunFlowStep("Filtered", getFirstMetricValue(counts, ["filtered_jobs", "filtered"]))' in renderer
    assert 'pipelineRunFlowStep("New", getFirstMetricValue(counts, ["new_jobs", "new"]))' in renderer
    assert 'pipelineRunFlowStep("Final", finalJobs)' in renderer


def test_absent_flow_metrics_render_an_em_dash_rather_than_a_substitute():
    helper = PROFILE_JS.split("function pipelineRunFlowStep(label, value) {", 1)[1].split(
        "\nfunction ", 1
    )[0]

    assert "isDisplayableMetricValue(value)" in helper
    assert '"—"' in helper
    assert "getFirstMetricValue" not in helper


def test_status_keeps_its_text_label_alongside_the_dot():
    renderer = _render_runs()

    assert "pipelineRunStatusLabel(run.status)" in renderer
    assert 'class="pipeline-run-status-dot" aria-hidden="true"' in renderer


def test_total_history_count_drives_the_section_subtitle():
    renderer = _render_runs()

    assert "profileState.pipelineRunsTotalCount" in renderer
    assert "historical run" in renderer
    assert "pipeline run${items.length === 1" not in renderer


# --- actions ----------------------------------------------------------------


def test_actions_column_has_exactly_view_agentic_and_rerun():
    renderer = _render_runs()

    assert "data-pipeline-run-view=" in renderer
    assert "pipeline-run-agentic-review-btn" in renderer
    assert "data-pipeline-run-rerun=" in renderer
    # Re-run is an icon button in the Actions group, not its own column or a
    # large filled text button.
    assert ">Re-run</button>" not in renderer
    assert "pipeline-run-action-btn" not in renderer
    # No overflow / three-dot menu.
    assert "overflow-menu" not in renderer
    assert "data-pipeline-run-menu" not in renderer


def test_action_icons_have_descriptive_accessible_names():
    renderer = _render_runs()

    assert 'aria-label="View stats for ${runId}"' in renderer
    assert 'aria-label="Open agentic review for ${runId}"' in renderer
    assert 'aria-label="Re-run ${runId}"' in renderer
    # Tooltips are not the sole accessible name.
    assert 'data-tooltip="View stats"' in renderer
    assert 'data-tooltip="Agentic review"' in renderer
    assert 'data-tooltip="Re-run"' in renderer


def test_actions_use_one_custom_tooltip_without_native_title_duplicates():
    renderer = _render_runs()

    for tooltip in ("View stats", "Agentic review", "Re-run"):
        assert renderer.count(f'data-tooltip="{tooltip}"') == 1
        assert f'title="{tooltip}"' not in renderer

    # The Run ID title remains intentionally outside the action controls.
    assert 'class="pipeline-run-id" title="${runId}"' in renderer


def test_view_stats_still_opens_the_existing_modal_via_the_existing_handler():
    bindings = PROFILE_JS.split("function bindPipelineRunsInteractions() {", 1)[1].split(
        "\nfunction ", 1
    )[0]

    assert "openPipelineRunStatsModal(viewBtn.dataset.pipelineRunView" in bindings
    assert "[data-pipeline-run-view]" in bindings


def test_agentic_review_keeps_its_existing_route_and_admin_gating():
    renderer = _render_runs()

    assert '/profile/pipeline-runs/${encodeURIComponent(rawRunId)}/agentic-review' in renderer
    assert "isCurrentUserAdmin(profileState.currentUser)" in renderer
    # Still a link, never converted into a modal.
    assert "<a" in renderer.split("agenticReviewAction", 1)[1][:400]


def test_rerun_icon_opens_confirmation_and_never_runs_directly():
    bindings = PROFILE_JS.split("function bindPipelineRunsInteractions() {", 1)[1].split(
        "\nfunction ", 1
    )[0]

    assert "openPipelineRunRerunModal(rerunBtn.dataset.pipelineRunRerun" in bindings
    # The row handler must not call the rerun API directly.
    assert "rerunPipelineRun(" not in bindings
    assert "/rerun" not in bindings


# --- pagination -------------------------------------------------------------


def test_pagination_is_compact_icon_controls_with_a_single_range_line():
    pagination = _pagination()

    assert "Showing ${startRow}-${endRow} of ${totalCount}" in pagination
    assert "· Page ${currentPage} of ${totalPages}" not in pagination
    assert "${currentPage} / ${totalPages}" in pagination
    # Arrows replaced the verbose Previous/Next text buttons.
    assert ">Previous<" not in pagination
    assert ">Next<" not in pagination
    assert 'pipelineRunIcon("chevronLeft"' in pagination
    assert 'pipelineRunIcon("chevron"' in pagination


def test_pagination_state_and_page_size_semantics_are_unchanged():
    pagination = _pagination()
    loader = PROFILE_JS.split("async function loadPipelineRuns(", 1)[1].split(
        "\nfunction ", 1
    )[0]

    assert "profileState.pipelineRunsHasPrevious" in pagination
    assert "profileState.pipelineRunsHasNext" in pagination
    assert 'aria-label="Previous pipeline runs page"' in pagination
    assert 'aria-label="Next pipeline runs page"' in pagination
    assert "data-pipeline-runs-page=" in pagination
    # Same endpoint, same page-size source.
    assert "/profile/pipeline-runs?page=" in loader
    assert "profileState.pipelineRunsPageSize || 15" in loader


def test_refresh_control_keeps_its_existing_handler():
    bindings = PROFILE_JS.split("function bindPipelineRunsInteractions() {", 1)[1].split(
        "\nfunction ", 1
    )[0]
    html = profile_page(_request())

    assert 'id="refreshPipelineRunsBtn"' in html
    assert 'qs("refreshPipelineRunsBtn")?.addEventListener' in bindings
    assert "loadPipelineRuns(profileState.pipelineRunsPage)" in bindings


def test_pagination_controls_use_scoped_eucalyptus_and_neutral_states():
    css = _runs_css().lower()
    base = css.split(
        "#profilepipelinerunssection .pipeline-runs-page-btn {", 1
    )[1].split("}", 1)[0]
    hover = css.split(
        "#profilepipelinerunssection .pipeline-runs-page-btn:not(:disabled):hover {", 1
    )[1].split("}", 1)[0]
    active = css.split(
        "#profilepipelinerunssection .pipeline-runs-page-btn:not(:disabled):active {", 1
    )[1].split("}", 1)[0]
    disabled = css.split(
        "#profilepipelinerunssection .pipeline-runs-page-btn:disabled {", 1
    )[1].split("}", 1)[0]
    indicator = css.split(".pipeline-runs-page-indicator {", 1)[1].split("}", 1)[0]

    assert "--runs-accent: #3c746a" in css
    assert "--runs-accent-hover: #315f57" in css
    assert "--runs-accent-pressed: #294f49" in css
    assert "background: var(--runs-accent) !important" in base
    assert "color: #ffffff !important" in base
    assert "background: var(--runs-accent-hover) !important" in hover
    assert "background: var(--runs-accent-pressed) !important" in active
    assert "background: var(--runs-pagination-disabled-bg) !important" in disabled
    assert "color: var(--runs-pagination-disabled-icon) !important" in disabled
    assert "opacity: 1" in disabled
    assert "color: var(--runs-pagination-indicator)" in indicator

    for forbidden in ("blue", "purple", "lavender", "#2563eb", "#4f46e5", "#7c3aed"):
        assert forbidden not in base + hover + active + disabled + indicator


def test_pagination_color_owner_outranks_legacy_catchalls_and_is_cache_busted():
    html = profile_page(_request())
    css = _runs_css()

    assert "#profilePipelineRunsSection .pipeline-runs-page-btn {" in css
    assert "#profilePipelineRunsSection .pipeline-runs-page-btn:not(:disabled):hover {" in css
    assert "#profilePipelineRunsSection .pipeline-runs-page-btn:not(:disabled):active {" in css
    assert "#profilePipelineRunsSection .pipeline-runs-page-btn:disabled {" in css
    assert '/static/app_redesign.css?v=eucalyptus_primary_shell_r1' in html


def test_refresh_remains_a_scoped_neutral_secondary_action():
    css = _runs_css().lower()
    refresh = css.split(
        ".profile-pipeline-runs-section .pipeline-runs-refresh-btn {", 1
    )[1].split("}", 1)[0]

    assert "background: var(--runs-surface) !important" in refresh
    assert "border: 1px solid var(--runs-border) !important" in refresh
    assert "color: var(--runs-secondary) !important" in refresh
    assert "background: var(--runs-accent)" not in refresh


def test_first_row_tooltips_flip_below_the_scrollport_boundary():
    css = _runs_css()
    wrapper = css.split(".pipeline-runs-table-wrap {", 1)[1].split("}", 1)[0]
    first_pointer = css.split(
        ".pipeline-runs-table tbody tr:first-child .pipeline-run-icon-btn::before {", 1
    )[1].split("}", 1)[0]
    first_label = css.split(
        ".pipeline-runs-table tbody tr:first-child .pipeline-run-icon-btn::after {", 1
    )[1].split("}", 1)[0]
    active_button = css.split(
        ".pipeline-run-icon-btn:hover,\n.pipeline-run-icon-btn:focus-visible {", 1
    )[1].split("}", 1)[0]

    # Horizontal responsiveness is preserved; the first row avoids trying to
    # escape this clipping scrollport by using an explicit downward placement.
    assert "overflow-x: auto" in wrapper
    assert "top: auto" in first_pointer
    assert "bottom: -10px" in first_pointer
    assert "border-bottom-color:" in first_pointer
    assert "top: calc(100% + 9px)" in first_label
    assert "z-index: 21" in active_button


# --- re-run modal -----------------------------------------------------------


def test_rerun_modal_keeps_dialog_semantics_and_existing_ids():
    html = profile_page(_request())

    assert 'id="pipelineRunRerunModal" role="dialog" aria-modal="true"' in html
    assert 'aria-labelledby="pipelineRunRerunTitle"' in html
    assert 'id="pipelineRunRerunBody"' in html
    assert 'id="pipelineRunRerunCancelBtn"' in html
    assert 'id="pipelineRunRerunConfirmBtn"' in html
    assert ">Cancel</button>" in html
    assert ">Re-run pipeline</button>" in html


def test_rerun_modal_shows_saved_configuration_from_existing_config_only():
    summary = PROFILE_JS.split("function renderPipelineRunRerunSummary(run) {", 1)[1].split(
        "\nfunction ", 1
    )[0]

    assert "Saved configuration" in summary
    for field in (
        "config.job_limit",
        "config.job_packet_limit",
        "config.llm_actions",
        "config.planning_only",
        "config.generate_tailoring",
        "config.generate_llm_tailoring",
        "config.refresh_llm_tailoring",
        "config.generate_llm_fallback",
        "config.generate_llm_adjudication",
    ):
        assert field in summary
    # Re-running does not alter the existing run; the copy says so.
    assert "The existing run remains unchanged." in summary


def test_rerun_confirm_uses_the_existing_rerun_path_and_pending_run_id():
    confirm = PROFILE_JS.split("async function confirmPipelineRunRerun() {", 1)[1].split(
        "\nfunction ", 1
    )[0]
    rerun = PROFILE_JS.split("async function rerunPipelineRun(runId) {", 1)[1].split(
        "\nasync function ", 1
    )[0]

    assert "profileState.pendingRerunRunId" in confirm
    assert "rerunPipelineRun(runId)" in confirm
    assert "Starting..." in confirm
    assert "/profile/pipeline-runs/${encodeURIComponent(runId)}/rerun" in rerun
    assert "postJson(" in rerun


def test_rerun_cancel_closes_without_mutating():
    close = PROFILE_JS.split("function closePipelineRunRerunModal() {", 1)[1].split(
        "\nasync function ", 1
    )[0]

    assert "profileState.pendingRerunRunId = null" in close
    assert "classList.add(\"hidden\")" in close
    assert "postJson" not in close
    assert "rerunPipelineRun" not in close
    # Focus returns to the control that opened the dialog.
    assert "returnFocus.focus()" in close


# --- visual system ----------------------------------------------------------


def test_rows_are_neutral_with_no_pastel_zebra_treatment():
    css = _runs_css()

    assert ".pipeline-runs-table tbody tr {" in css
    body_rows = css.split(".pipeline-runs-table tbody tr {", 1)[1].split("}", 1)[0]
    assert "var(--runs-surface)" in body_rows
    assert "nth-child" not in css.split(".pipeline-runs-table tbody", 1)[1].split(".pipeline-run-cell-run", 1)[0]


def test_action_buttons_avoid_saturated_blue_and_purple():
    css = _runs_css()
    lowered = css.lower()

    for forbidden in (
        "#2563eb", "#1d4ed8", "#93c5fd", "#60a5fa",
        "#7c3aed", "#c4b5fd", "#4f46e5",
        "maroon", "burgundy", "wine", "berry",
    ):
        assert forbidden not in lowered, f"rejected colour in pipeline runs CSS: {forbidden}"

    # Neutral idle state with a selective eucalyptus hover.
    icon_btn = css.split(".pipeline-run-icon-btn {", 1)[1].split("}", 1)[0]
    assert "var(--runs-secondary)" in icon_btn
    assert "var(--runs-accent-soft)" in icon_btn


def test_rerun_modal_primary_action_is_deep_eucalyptus_not_danger_styling():
    modal_css = APP_REDESIGN_CSS.split("#pipelineRunRerunModal {", 1)[1].split(
        "[data-agentic-review-run-id]", 1
    )[0]
    lowered = modal_css.lower()

    assert "--rerun-accent: #2f7668" in lowered
    assert "--rerun-accent-hover: #265f55" in lowered
    for forbidden in ("#be123c", "#e11d48", "#2563eb", "#1d4ed8", "#4f46e5"):
        assert forbidden not in lowered, f"rejected colour in re-run modal CSS: {forbidden}"


# --- backend safety ---------------------------------------------------------


def test_no_backend_or_api_change_for_the_history_page():
    assert '@app.get("/profile/pipeline-runs")' in API_SOURCE
    assert "services.profile_pipeline_runs_payload(" in API_SOURCE
    assert "services.profile_pipeline_run_detail_payload(" in API_SOURCE
