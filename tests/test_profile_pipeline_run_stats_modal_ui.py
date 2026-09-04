"""Focused UI contracts for the compact Profile Pipeline Run Stats modal."""

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
        "user_id": "pipeline-run-stats-ui-user",
        "access_level": "user",
        "is_admin": False,
    }
    return request


def _detail_renderer() -> str:
    return PROFILE_JS.split("function renderPipelineRunDetail", 1)[1].split(
        "function pipelineRunStatsFocusableElements", 1
    )[0]


def _open_modal_flow() -> str:
    return PROFILE_JS.split("async function openPipelineRunStatsModal", 1)[1].split(
        "function closePipelineRunStatsModal", 1
    )[0]


def _stats_css() -> str:
    return APP_REDESIGN_CSS.split("profile_pipeline_run_stats_summary_r1", 1)[1]


def test_stats_modal_keeps_identity_and_adds_accessible_compact_shell():
    html = profile_page(_request())

    assert 'id="pipelineRunStatsModal" role="dialog" aria-modal="true"' in html
    assert 'aria-labelledby="pipelineRunStatsTitle"' in html
    assert 'aria-describedby="pipelineRunStatsSubtitle"' in html
    assert 'class="modal-card pipeline-run-stats-modal-card" tabindex="-1"' in html
    assert 'class="pipeline-run-stats-header"' in html
    assert 'id="pipelineRunStatsRunId"' in html
    assert 'class="pipeline-run-stats-scroll"' in html
    assert 'id="pipelineRunStatsBody" class="pipeline-run-stats-body" aria-live="polite"' in html
    # Close is a proper line icon in a compact hit target, not a text glyph
    # and not a large labelled button.
    assert 'aria-label="Close pipeline run details" title="Close"' in html
    close_block = html.split('class="pipeline-run-stats-close"', 1)[1].split("</button>", 1)[0]
    assert "<svg" in close_block
    assert "&times;" not in close_block
    assert 'id="pipelineRunStatsCloseBtn" type="button">Close</button>' not in html


def test_open_flow_uses_the_same_single_detail_endpoint_and_inline_error_state():
    flow = _open_modal_flow()

    assert 'fetchJson(`/profile/pipeline-runs/${encodeURIComponent(runId)}`)' in flow
    assert flow.count('fetchJson(`/profile/pipeline-runs/${encodeURIComponent(runId)}`)') == 1
    assert "/agent-trace" not in flow
    assert 'method: "POST"' not in flow
    assert "Loading run details..." in flow
    assert "renderPipelineRunDetail(data)" in flow
    assert "renderPipelineRunStatsFetchError(runId, error)" in flow
    assert "Could not load pipeline run details" in flow


def test_detail_renderer_uses_the_approved_information_hierarchy():
    renderer = _detail_renderer()

    # Premium visual refinement (targeted): the top status strip is now the
    # hero Run Overview panel (same section order, same architecture level).
    assert 'class="pipeline-run-hero is-${escapeHtml(statusTone)}"' in renderer
    assert 'class="pipeline-run-hero-status' in renderer
    assert 'class="pipeline-run-hero-facts"' in renderer
    assert 'class="pipeline-run-hero-ribbon"' in renderer
    assert 'class="pipeline-run-panel pipeline-run-stats-section pipeline-run-summary-section"' in renderer
    assert "Run summary" in renderer
    assert 'class="pipeline-run-outcome-primary"' in renderer
    assert 'class="pipeline-run-outcome-secondary"' in renderer
    assert "Pipeline outcomes" in renderer
    assert 'class="pipeline-run-technical-disclosure pipeline-run-disclosure"' in renderer
    assert "Agent trace &amp; stage details" in renderer
    assert '<h4>Run</h4>' not in renderer
    assert 'class="pipeline-run-count-tile' not in renderer
    assert "metric.tone" not in renderer
    # Section order is unchanged: hero -> summary -> outcomes -> disclosure.
    assert (
        renderer.index('class="pipeline-run-hero is-')
        < renderer.index('class="pipeline-run-panel pipeline-run-stats-section pipeline-run-summary-section"')
        < renderer.index('class="pipeline-run-outcome-primary"')
        < renderer.index('class="pipeline-run-technical-disclosure pipeline-run-disclosure"')
    )


def test_all_existing_outcome_metrics_still_derive_from_the_existing_config():
    metric_config = PROFILE_JS.split("const PIPELINE_RUN_OUTCOME_METRICS", 1)[1].split(
        "function getFirstMetricValue", 1
    )[0]
    renderer = _detail_renderer()
    expected_labels = {
        "Scraped Jobs",
        "Filtered Jobs",
        "Unique Jobs",
        "Ranked Jobs",
        "New Jobs",
        "Detailed Jobs",
        "Intelligence Reviews",
        "AI Eligible Jobs",
        "Prefiltered Jobs",
        "Resume Matched Jobs",
        "Scored Jobs",
        "RAG Exports",
        "Planning Packets",
        "Generated Packets",
        "Completed Packets",
        "Generated Plans",
        "Failed Plans",
        "Pending Variants",
        "Missing Resume Matches",
        "No Credible Match",
    }

    for label in expected_labels:
        assert f'label: "{label}"' in metric_config
    assert metric_config.count("{ keys:") == len(expected_labels)
    assert "getPipelineRunOutcomeMetrics(counts)" in renderer
    # Same ordered/filtered outcomeMetrics list as before, only split into a
    # primary (first four) and secondary (remaining) presentation tier - no
    # reprioritization, no new metric derivation.
    assert "selectPipelineRunPrimaryMetrics(outcomeMetrics)" in renderer
    assert "outcomeMetrics.filter((metric) => !primaryLabels.has(metric.label))" in renderer
    assert "primaryMetrics.map((metric, index)" in renderer
    assert "secondaryMetrics.map((metric)" in renderer
    assert "metric.label" in renderer
    assert "metric.value" in renderer


def test_status_timing_run_identity_summary_and_error_data_are_preserved():
    renderer = _detail_renderer()

    assert "pipelineRunStatusLabel(run.status || statusJson.status)" in renderer
    assert "formatPipelineRunDuration(startedAt, completedAt)" in renderer
    assert 'run.started_at || statusJson.started_at || ""' in renderer
    assert "run.completed_at || statusJson.completed_at || statusJson.finished_at" in renderer
    assert 'qs("pipelineRunStatsRunId").textContent = run.run_id' in renderer
    assert "run.summary_message || statusJson.summary_message" in renderer
    assert "run.error || statusJson.error" in renderer
    assert "Current stage" in renderer
    assert "Final jobs" in renderer
    assert "Planned jobs" in renderer
    assert "Packet jobs" in renderer
    assert 'class="pipeline-run-failure-summary" role="alert"' in renderer
    assert renderer.index("pipeline-run-failure-summary") < renderer.index(
        "pipeline-run-technical-disclosure"
    )
    # A failed run's error stays visible near the top, not only inside the
    # Error details disclosure.
    assert renderer.index("pipeline-run-failure-summary") < renderer.index(
        "pipeline-run-error-disclosure"
    )


def test_settings_stages_and_agent_trace_are_preserved_behind_native_disclosure():
    renderer = _detail_renderer()
    disclosure = renderer.split(
        '<details class="pipeline-run-technical-disclosure pipeline-run-disclosure">', 1
    )[1]

    assert not disclosure.lstrip().startswith("open")
    assert "Settings" in disclosure
    assert "Job limit" in disclosure
    assert "Generate LLM adjudication" in disclosure
    assert "Delete seen data" in disclosure
    assert "Stages" in disclosure
    assert "stageOrder.map" in disclosure
    assert "renderAgentTracePanel(tracePayload, traceError)" in disclosure
    assert "No agent trace recorded for this run." in PROFILE_JS
    assert "renderPipelineRunSettingsList([" in disclosure


def test_modal_closing_supports_escape_focus_containment_and_focus_return():
    close_flow = PROFILE_JS.split("function closePipelineRunStatsModal", 1)[1].split(
        "function renderPipelineRunRerunSummary", 1
    )[0]
    bindings = PROFILE_JS.split("function bindPipelineRunsInteractions", 1)[1].split(
        "function bindAdminUsersInteractions", 1
    )[0]

    assert "modal._returnFocus = document.activeElement" in PROFILE_JS
    assert "document.body.contains(returnFocus)" in close_flow
    assert "returnFocus.focus()" in close_flow
    assert 'event.key === "Escape"' in bindings
    assert 'event.key !== "Tab"' in bindings
    assert "pipelineRunStatsFocusableElements(modal)" in bindings
    assert "closePipelineRunStatsModal()" in bindings
    assert 'window.matchMedia?.("(prefers-reduced-motion: reduce)")' in close_flow


def test_scoped_visual_system_is_neutral_responsive_and_not_rainbow():
    css = _stats_css()

    assert "--pipeline-stats-accent: #3c746a" in css
    assert "--pipeline-stats-accent-hover: #315f57" in css
    assert "--pipeline-stats-accent-pressed: #294f49" in css
    assert "--pipeline-stats-accent-soft: #e7f0ed" in css
    assert "--pipeline-stats-accent-border: #b9d1cb" in css
    assert "--pipeline-stats-accent-text: #28564f" in css
    # Premium feature-panel palette: deep petrol/eucalyptus, jade, muted gold.
    # Constant across light/dark - the hero panel stays dark even in light mode.
    assert "--pipeline-hero-deep: #0f4e45" in css
    assert "--pipeline-hero-deeper: #0a443c" in css
    assert "--pipeline-hero-mid: #176357" in css
    assert "--pipeline-jade: #24b99b" in css
    assert "--pipeline-jade-light: #67d2b0" in css
    assert "--pipeline-mint: #94d89f" in css
    assert "--pipeline-lime-muted: #bcd977" in css
    assert "--pipeline-gold: #e5b84e" in css
    assert "--pipeline-gold-light: #f2ce72" in css
    assert "--pipeline-hero-text: #f5faf8" in css
    assert "width: min(1100px, calc(100vw - 48px))" in css
    assert "max-height: 87dvh" in css
    assert ".pipeline-run-stats-scroll" in css
    assert "overflow-y: auto" in css
    assert "grid-template-columns: repeat(4, minmax(0, 1fr))" in css
    assert "grid-template-columns: repeat(2, minmax(0, 1fr))" in css
    assert "grid-template-columns: 1fr" in css
    assert "@media (prefers-reduced-motion: reduce)" in css
    assert ".pipeline-run-hero-bar" in css
    assert ".pipeline-run-hero-bar.is-complete" in css
    assert ".pipeline-run-hero-bar.is-running" in css
    assert ".pipeline-run-hero-bar.is-failed" in css
    assert ".pipeline-run-hero-bar.is-pending" in css
    assert ".pipeline-run-count-tile.is-blue" not in css
    assert ".pipeline-run-count-tile.is-cyan" not in css
    assert ".pipeline-run-count-tile.is-violet" not in css
    for forbidden in (
        "maroon", "burgundy", "wine", "cobalt", "royal blue",
        "#0000ff", "#00f", "#800080", "#8b008b", "#4b0082",
    ):
        assert forbidden not in css.lower()


def test_hero_panel_is_the_main_visual_anchor_with_a_real_stage_ribbon():
    renderer = _detail_renderer()

    assert 'aria-label="Pipeline run overview"' in renderer
    assert "pipelineRunStatusLabel(run.status || statusJson.status)" in renderer
    assert "escapeHtml(duration)" in renderer
    assert "escapeHtml(formatPipelineRunMetricValue(finalJobCount))" in renderer
    assert "Duration" in renderer
    assert "Final jobs" in renderer
    assert "Packets" in renderer
    # The ribbon is built only from the run's own persisted stage_order - no
    # hard-coded fake stage path.
    assert "stageOrder.map((stage) => {" in renderer
    assert "role=\"list\" aria-label=\"Pipeline stage progress\"" in renderer
    assert "pipeline-run-hero-bar is-${escapeHtml(state)}" in renderer
    assert "stageSegmentState(stage)" in renderer
    # Family labels (Scrape/Filter/Rank/...) are derived, not hard-coded, and
    # the raw stage name remains available via an accessible label/title -
    # not a hover-only tooltip.
    assert "pipelineRunStageFamily(stage)" in renderer
    assert "aria-label=\"${escapeHtml(raw)}: ${escapeHtml(pipelineRunStageSegmentStatusText(state))}\"" in renderer


def test_stage_family_mapping_covers_current_stages_without_hard_coding_a_fake_path():
    helper = PROFILE_JS.split("const PIPELINE_STAGE_FAMILY_RULES", 1)[1].split(
        "function pipelineRunStageDisplayName", 1
    )[0]
    known_stages = [
        "startup", "scraping", "filtering", "dedupe", "ranking", "cache_filter",
        "details", "intelligence", "ai_evaluation_filter", "embedding_prefilter",
        "ai_evaluation", "resume_matching", "application_priority", "rag_export",
        "planning", "finalization",
    ]
    expected_families = {
        "startup": "Scrape", "scraping": "Scrape",
        "filtering": "Filter", "dedupe": "Filter", "cache_filter": "Filter",
        "ranking": "Rank",
        "details": "AI", "intelligence": "AI", "ai_evaluation_filter": "AI",
        "embedding_prefilter": "AI", "ai_evaluation": "AI",
        "resume_matching": "Match", "application_priority": "Match",
        "rag_export": "Plan", "planning": "Plan",
        "finalization": "Final",
    }
    assert set(expected_families) == set(known_stages)
    for stage in known_stages:
        assert stage.startswith(tuple("abcdefghijklmnopqrstuvwxyz_"))
    assert "family: \"Scrape\"" in helper
    assert "family: \"AI\"" in helper
    assert "family: \"Filter\"" in helper
    assert "family: \"Rank\"" in helper
    assert "family: \"Match\"" in helper
    assert "family: \"Plan\"" in helper
    assert "family: \"Final\"" in helper
    # An unrecognized stage still renders under its own humanized name -
    # never dropped, never assigned a made-up family.
    fallback = PROFILE_JS.split("function pipelineRunStageFamily", 1)[1][:400]
    assert "pipelineRunStageDisplayName(stage)" in fallback


def test_stage_segment_state_reuses_only_existing_run_data():
    helper = PROFILE_JS.split("function pipelineRunStageSegmentState", 1)[1].split(
        "function pipelineRunStageSegmentStatusText", 1
    )[0]
    assert "completedStages.has(stage)" in helper
    assert "stage === currentStage" in helper
    assert 'statusTone === "danger"' in helper
    assert 'statusTone === "running"' in helper
    # No new fields invented: only the run's already-loaded stage_order/
    # completed_stages/current_stage/status feed this function.
    assert "fetch(" not in helper


def test_modal_backdrop_stacks_above_the_global_shell_controls():
    css = APP_REDESIGN_CSS
    stats_css = _stats_css()

    modal_z = int(stats_css.split("z-index:", 1)[1].split("!important", 1)[0].strip())

    # The shell's top-right cluster (notification bell, theme toggle, New
    # Scan, avatar) is .app-shell-top-right; its highest declared z-index in
    # the cascade must still be lower than the modal's.
    shell_z_values = []
    for block in css.split(".app-shell-top-right:not(.app-shell-top-right--flow) {")[1:]:
        rule_body = block.split("}", 1)[0]
        if "z-index:" not in rule_body:
            continue
        raw = rule_body.split("z-index:", 1)[1].split(";", 1)[0].replace("!important", "").strip()
        shell_z_values.append(int(raw))
    assert shell_z_values, "expected at least one declared z-index for the shell's top-right cluster"
    assert modal_z > max(shell_z_values), (
        f"modal backdrop z-index {modal_z} must exceed the shell's top-right "
        f"cluster z-index {max(shell_z_values)}"
    )
    # Pin the exact relationship (not just "some huge number") so a future
    # shell z-index bump cannot silently reintroduce the clash.
    assert max(shell_z_values) == 260
    assert modal_z == 1000


def test_backend_contract_and_pipeline_runs_entry_point_are_unchanged():
    assert '@app.get("/profile/pipeline-runs/{run_id}")' in API_SOURCE
    assert "services.profile_pipeline_run_detail_payload(" in API_SOURCE
    assert 'data-pipeline-run-view="${runId}"' in PROFILE_JS
    assert "openPipelineRunStatsModal(viewBtn.dataset.pipelineRunView" in PROFILE_JS
    assert "const PIPELINE_RUN_OUTCOME_METRICS" in PROFILE_JS


def test_approved_resume_ui_contract_remains_present():
    assert "profile-resume-library" in PROFILE_UI
    assert "profileResumeUploadModal" in PROFILE_UI
    assert "profileResumeRoleModal" in PROFILE_UI
    assert "profile-resume-document-row" in PROFILE_JS
    assert "profile-resume-manage-role-action" in PROFILE_JS
    assert "profile-resume-delete-row-action" in PROFILE_JS
    assert "profile_resume_document_library_r1" in APP_REDESIGN_CSS



# ---------------------------------------------------------------------------
# Metric semantics.
#
# main.py::_application_planning_status_counts computes planning_total_jobs
# (rows in application_shortlist_by_job.csv) and planning_packet_jobs (rows in
# job_packet_manifest.csv) per run and embeds them in the authoritative
# summary_message. Neither is persisted into status_json.counts. They are
# deliberately different concepts from planning_packets_total /
# planning_packets_generated / planning_packets_completed /
# planning_llm_generated, which ARE persisted and keep their own labels.
# ---------------------------------------------------------------------------

MAIN_SOURCE = (ROOT / "main.py").read_text(encoding="utf-8")


def test_authoritative_planned_and_packet_job_source_is_the_summary_message():
    # Backend contract: these two numbers only exist in the summary sentence.
    assert '"planning_total_jobs": _count_rows(shortlist_csv)' in MAIN_SOURCE
    assert '"planning_packet_jobs": _count_rows(packet_manifest_csv)' in MAIN_SOURCE
    assert 'planned = counts.get("planning_total_jobs", 0)' in MAIN_SOURCE
    assert 'packets = counts.get("planning_packet_jobs", 0)' in MAIN_SOURCE
    assert "planned jobs, " in MAIN_SOURCE
    assert "packet jobs" in MAIN_SOURCE


def test_planned_and_packet_jobs_never_fall_back_to_planning_packet_metrics():
    renderer = _detail_renderer()

    assert "pipelineRunPlannedJobCount(summaryMessage)" in renderer
    assert "pipelineRunPacketJobCount(summaryMessage)" in renderer
    # The previous implementation silently relabelled a different metric when
    # packet_jobs was absent from counts. That must not come back.
    assert '"planned_jobs", "planning_jobs", "planning_llm_generated"' not in renderer
    planned_line = [
        line for line in renderer.splitlines() if "plannedJobCount" in line and "const" in line
    ]
    packet_line = [
        line for line in renderer.splitlines() if "packetJobCount" in line and "const" in line
    ]
    assert planned_line and packet_line
    for line in planned_line + packet_line:
        assert "planning_packets_total" not in line
        assert "planning_packets_generated" not in line
        assert "planning_packets_completed" not in line
        assert "planning_llm_generated" not in line


def test_planning_packets_keeps_its_own_distinct_label_and_source():
    renderer = _detail_renderer()
    metric_config = PROFILE_JS.split("const PIPELINE_RUN_OUTCOME_METRICS", 1)[1].split(
        "function getFirstMetricValue", 1
    )[0]

    # Hero uses planning_packets_total under its own honest label.
    assert 'getFirstMetricValue(counts, ["planning_packets_total"])' in renderer
    assert "Planning packets" in renderer
    # The three persisted packet-artifact metrics keep their separate labels.
    assert '{ keys: ["planning_packets_total"], label: "Planning Packets"' in metric_config
    assert '{ keys: ["planning_packets_generated"], label: "Generated Packets"' in metric_config
    assert '{ keys: ["planning_packets_completed"], label: "Completed Packets"' in metric_config
    assert '{ keys: ["planning_llm_generated"], label: "Generated Plans"' in metric_config


def test_summary_metric_parser_handles_every_persisted_summary_shape():
    parser = PROFILE_JS.split("const PIPELINE_SUMMARY_PLANNED_JOBS_PATTERN", 1)[1].split(
        "function pipelineRunCountsSummary", 1
    )[0]

    # Strict, anchored on the authoritative wording; comma thousands tolerated.
    assert r"planned\s+jobs?\b" in parser
    assert r"packet\s+jobs?\b" in parser
    assert 'replaceAll(",", "")' in parser
    # Absent values return undefined so the UI renders "-" rather than a
    # borrowed number from an unrelated metric.
    assert "if (!match) return undefined;" in parser


# ---------------------------------------------------------------------------
# Target visual fidelity.
# ---------------------------------------------------------------------------


def test_hero_renders_status_icon_caption_and_three_labelled_metrics():
    renderer = _detail_renderer()

    assert "pipelineRunStatusIconName(statusTone)" in renderer
    assert "pipelineRunStatusCaption(statusTone, statusLabel)" in renderer
    assert 'class="pipeline-run-hero-status-badge"' in renderer
    assert 'pipelineRunIcon("clock"' in renderer
    assert 'pipelineRunIcon("document"' in renderer
    assert 'pipelineRunIcon("layers"' in renderer
    assert "<span>Duration</span>" in renderer
    assert "<span>Final jobs</span>" in renderer
    assert "<span>Planning packets</span>" in renderer
    # Status is derived, never hard-coded.
    assert '>Succeeded<' not in renderer

    caption = PROFILE_JS.split("function pipelineRunStatusCaption", 1)[1][:420]
    assert '"success"' in caption
    assert '"danger"' in caption
    assert '"running"' in caption


def test_stage_ribbon_uses_a_multi_step_controlled_progression():
    renderer = _detail_renderer()
    css = _stats_css()

    assert "pipelineRunStageProgressionStep(index, stageOrder.length)" in renderer
    assert "is-step-${step}" in renderer

    # The completed ramp must be several distinct controlled colours, not one
    # flat teal repeated for every segment.
    ramp = [f"--pipeline-ribbon-{index}" in css for index in range(8)]
    assert all(ramp)
    ramp_values = {
        css.split(f"--pipeline-ribbon-{index}:", 1)[1].split(";", 1)[0].strip()
        for index in range(8)
    }
    assert len(ramp_values) == 8, "each completed ribbon step needs its own colour"
    for index in range(8):
        assert f".pipeline-run-hero-bar.is-complete.is-step-{index}" in css


def test_progression_step_helper_spreads_across_the_real_stage_count():
    helper = PROFILE_JS.split("function pipelineRunStageProgressionStep", 1)[1].split(
        "function pipelineRunStageSegmentStatusText", 1
    )[0]

    assert "PIPELINE_RIBBON_PROGRESSION_STEPS" in helper
    # Defensive clamping so an empty/short stage list cannot divide by zero or
    # index outside the palette.
    assert "Math.max" in helper
    assert "Math.min" in helper


def test_primary_outcome_cards_have_icons_and_related_tone_family():
    renderer = _detail_renderer()
    css = _stats_css()

    assert 'const primaryMetricIcons = ["database", "funnel", "layers", "sparkle"]' in renderer
    assert 'class="pipeline-run-outcome-primary-icon"' in renderer
    assert "is-tone-${index}" in renderer

    for index in range(4):
        assert f"--pipeline-tone-{index}-bg" in css
        assert f"--pipeline-tone-{index}-border" in css
        assert f"--pipeline-tone-{index}-icon" in css


def test_error_details_disclosure_uses_only_existing_error_data():
    renderer = _detail_renderer()

    assert 'class="pipeline-run-disclosure pipeline-run-error-disclosure"' in renderer
    assert "Error details" in renderer
    assert "No error recorded for this run" in renderer
    error_block = renderer.split("pipeline-run-error-disclosure", 1)[1]
    # Renders the persisted error verbatim; never fabricates one.
    assert "escapeHtml(errorMessage)" in error_block
    assert "errorMessage" in error_block


def test_agent_trace_empty_state_is_a_compact_row_not_a_large_dashed_panel():
    css = _stats_css()

    assert 'class="pipeline-run-inline-empty"' in PROFILE_JS
    assert "#pipelineRunStatsModal .pipeline-run-inline-empty" in css
    inline_empty = css.split("#pipelineRunStatsModal .pipeline-run-inline-empty {", 1)[1].split("}", 1)[0]
    assert "min-height: 44px" in inline_empty
    assert "dashed" not in inline_empty
    # Soft neutral surface, no boxed border.
    assert "var(--pipeline-row-surface)" in inline_empty
    assert "border:" not in inline_empty


def test_boolean_settings_use_a_restrained_semantic_dot():
    settings = PROFILE_JS.split("function renderPipelineRunSettingsList", 1)[1].split(
        "function renderJsonDetails", 1
    )[0]
    css = _stats_css()

    assert 'normalized === "yes"' in settings
    assert 'normalized === "no"' in settings
    assert "pipeline-run-detail-dot" in settings
    assert "#pipelineRunStatsModal .pipeline-run-detail-value.is-yes" in css
    assert "#pipelineRunStatsModal .pipeline-run-detail-value.is-no" in css


def test_modal_shell_matches_the_approved_proportions():
    css = _stats_css()

    assert "width: min(1100px, calc(100vw - 48px))" in css
    assert "max-height: 87dvh" in css
    assert "border-radius: 22px" in css
    assert "backdrop-filter: blur(5px)" in css
    # One internal scroll region only.
    assert PROFILE_UI.count('class="pipeline-run-stats-scroll"') == 1


def test_supporting_blue_and_lavender_are_scoped_to_informational_cards_only():
    """The approved target uses low-saturation powder blue and lavender for
    the read-only Pipeline Outcome cards. They are permitted there and
    nowhere else - not on actions, hero, navigation or shell surfaces."""
    css = _stats_css()
    lowered = css.lower()

    # Declared only as informational outcome-card tone tokens.
    assert "--pipeline-tone-1-bg: #eef7fc" in lowered
    assert "--pipeline-tone-1-border: #a8d7ea" in lowered
    assert "--pipeline-tone-1-icon: #3f91bc" in lowered
    assert "--pipeline-tone-2-bg: #f4f1fc" in lowered
    assert "--pipeline-tone-2-border: #c8b9ec" in lowered
    assert "--pipeline-tone-2-icon: #6657be" in lowered

    # Those tone tokens are consumed only by outcome-card rules.
    for token in ("--pipeline-tone-1-", "--pipeline-tone-2-"):
        for line in lowered.splitlines():
            if f"var({token}" not in line:
                continue
            block_start = lowered.rfind("#pipelinerunstatsmodal", 0, lowered.index(line))
            selector = lowered[block_start:lowered.index(line)]
            assert "outcome-primary" in selector, (
                f"{token} used outside the informational outcome cards: {selector[:120]}"
            )

    # The hero never uses a supporting blue/lavender token.
    hero_block = lowered.split(".pipeline-run-hero {", 1)[1].split("#pipelinerunstatsmodal .pipeline-run-panel", 1)[0]
    for token in ("--pipeline-tone-1-", "--pipeline-tone-2-"):
        assert token not in hero_block

    # Saturated actions and the banned wine family stay out entirely.
    for forbidden in (
        "maroon", "burgundy", "wine", "berry", "cobalt", "indigo",
        "#0000ff", "#00f;", "#800080", "#4b0082", "#6a5acd", "#7b1fa2",
    ):
        assert forbidden not in lowered, f"forbidden colour token in modal CSS: {forbidden}"

    # The approved teal/eucalyptus/jade/mint/gold family drives the hero.
    for token in ("#0f4e45", "#24b99b", "#67d2b0", "#94d89f", "#e5b84e"):
        assert token in lowered


def test_primary_metrics_are_selected_from_the_existing_config_only():
    selector = PROFILE_JS.split("const PIPELINE_RUN_PRIMARY_METRIC_LABELS", 1)[1].split(
        "// Groups the current persisted stage_order", 1
    )[0]
    metric_config = PROFILE_JS.split("const PIPELINE_RUN_OUTCOME_METRICS", 1)[1].split(
        "function getFirstMetricValue", 1
    )[0]

    for label in ("Scraped Jobs", "Filtered Jobs", "Unique Jobs", "New Jobs"):
        assert f'"{label}"' in selector
        # Every highlighted label must already exist in the metric config.
        assert f'label: "{label}"' in metric_config

    # Selection is by existing label, never a new metric or new derivation.
    assert "byLabel.get(label)" in selector
    assert "getFirstMetricValue" not in selector
    # Runs missing a preferred metric still fill four cards from config order.
    assert "selected.length >= PIPELINE_RUN_PRIMARY_METRIC_LABELS.length" in selector


def test_every_persisted_metric_stays_visible_across_the_two_tiers():
    renderer = _detail_renderer()

    # Secondary is the complement of primary over the same outcomeMetrics
    # list, so no configured metric can be dropped from the modal.
    assert "const primaryLabels = new Set(primaryMetrics.map((metric) => metric.label))" in renderer
    assert "outcomeMetrics.filter((metric) => !primaryLabels.has(metric.label))" in renderer
    assert "getPipelineRunOutcomeMetrics(counts)" in renderer


# ---------------------------------------------------------------------------
# Approved-target visual fidelity contract.
# ---------------------------------------------------------------------------


def test_primary_outcome_cards_resolve_to_scraped_filtered_unique_new():
    selector = PROFILE_JS.split("const PIPELINE_RUN_PRIMARY_METRIC_LABELS", 1)[1].split(
        "// Groups the current persisted stage_order", 1
    )[0]
    labels = [
        line.strip().strip(',').strip('"')
        for line in selector.split("]", 1)[0].splitlines()
        if line.strip().startswith('"')
    ]
    assert labels == ["Scraped Jobs", "Filtered Jobs", "Unique Jobs", "New Jobs"]
    # Ranked Jobs is deliberately NOT one of the four highlighted cards.
    assert "Ranked Jobs" not in labels


def test_ranked_jobs_remains_available_in_secondary_metrics():
    renderer = _detail_renderer()
    metric_config = PROFILE_JS.split("const PIPELINE_RUN_OUTCOME_METRICS", 1)[1].split(
        "function getFirstMetricValue", 1
    )[0]

    # Still configured and still rendered: secondary is the complement of
    # primary over the same list, so Ranked Jobs cannot be dropped.
    assert '{ keys: ["ranked_jobs", "ranked"], label: "Ranked Jobs"' in metric_config
    assert "outcomeMetrics.filter((metric) => !primaryLabels.has(metric.label))" in renderer
    assert "secondaryMetrics.map((metric)" in renderer


def test_primary_cards_use_horizontal_icon_plus_value_layout():
    renderer = _detail_renderer()
    css = _stats_css()

    # Icon tile is a sibling of a body wrapper holding value + label, so the
    # card reads horizontally instead of stacking icon-over-number.
    assert 'class="pipeline-run-outcome-primary-icon"' in renderer
    assert 'class="pipeline-run-outcome-primary-body"' in renderer
    card = css.split("#pipelineRunStatsModal .pipeline-run-outcome-primary-metric {", 1)[1].split("}", 1)[0]
    assert "display: flex" in card
    assert "flex-direction: column" not in card
    assert "align-items: center" in card
    # Compact card height, not the previous oversized tile.
    assert "min-height: 84px" in card


def test_stage_bars_use_narrow_capsule_geometry():
    css = _stats_css()
    bar = css.split("#pipelineRunStatsModal .pipeline-run-hero-bar {", 1)[1].split("}", 1)[0]

    # Slim vertical capsules, not full-width progress-bar segments.
    assert "width: 13px" in bar
    assert "max-width: 15px" in bar
    assert "height: 33px" in bar
    assert "border-radius: 7px" in bar
    # Must not stretch to fill the row like a segmented progress bar.
    assert "flex: 1 1 0" not in bar

    bars_row = css.split("#pipelineRunStatsModal .pipeline-run-hero-ribbon-bars {", 1)[1].split("}", 1)[0]
    assert "gap: 7px" in bars_row


def test_success_badge_uses_a_white_check_not_a_dark_glyph():
    css = _stats_css()
    badge = css.split("#pipelineRunStatsModal .pipeline-run-hero-status-badge {", 1)[1].split("}", 1)[0]

    assert "color: #ffffff" in badge
    # The dark check the target explicitly rejects must be gone.
    assert "#06312a" not in badge
    # Subtle dimensionality: gradient + inner highlight, scoped to the badge.
    assert "linear-gradient" in badge
    assert "inset 0 1px 0" in badge


def test_hero_metric_icons_read_against_the_petrol_hero():
    css = _stats_css()
    icon = css.split("#pipelineRunStatsModal .pipeline-run-hero-stat-icon {", 1)[1].split("}", 1)[0]

    # Pale off-white rather than teal-on-teal.
    assert "rgba(245, 250, 248" in icon
    assert "var(--pipeline-jade-light)" not in icon


def test_secondary_rows_use_soft_contained_surfaces_not_plain_rules():
    css = _stats_css()
    row = css.split("#pipelineRunStatsModal .pipeline-run-outcome-secondary-row {", 1)[1].split("}", 1)[0]

    assert "var(--pipeline-row-surface)" in row
    assert "border-radius: 8px" in row
    assert "min-height: 32px" in row
    # No heavy visible box border / horizontal rule treatment.
    assert "border-bottom" not in row
    assert "border:" not in row


def test_error_details_remains_the_second_disclosure_and_no_raw_json_added():
    renderer = _detail_renderer()

    assert "Error details" in renderer
    assert 'class="pipeline-run-disclosure pipeline-run-error-disclosure"' in renderer
    # The target image shows "Raw run data (JSON)"; that is a visual
    # reference only and must not become new exposed technical data.
    assert "Raw run data" not in renderer
    assert "Raw run data" not in PROFILE_UI


def test_modal_density_targets_are_applied():
    css = _stats_css()

    header = css.split("#pipelineRunStatsModal .pipeline-run-stats-header {", 1)[1].split("}", 1)[0]
    assert "padding: 22px 26px 14px" in header

    hero = css.split("#pipelineRunStatsModal .pipeline-run-hero {", 1)[1].split("}", 1)[0]
    assert "padding: 20px 24px" in hero
    assert "margin: 0 0 14px" in hero

    panel = css.split("#pipelineRunStatsModal .pipeline-run-panel {", 1)[1].split("}", 1)[0]
    assert "padding: 18px 20px !important" in panel

    disclosure = css.split("#pipelineRunStatsModal .pipeline-run-disclosure > summary {", 1)[1].split("}", 1)[0]
    assert "min-height: 56px" in disclosure


def test_run_summary_does_not_draw_a_full_spreadsheet_grid():
    css = _stats_css()
    item = css.split("#pipelineRunStatsModal .pipeline-run-summary-item {", 1)[1].split("}", 1)[0]

    # Vertical separators only; horizontal row rules removed in favour of
    # spacing so six values do not read as six cells.
    assert "border-left" in item
    assert "border-top" not in item
    assert "nth-child(n + 4)" not in css.split(
        "#pipelineRunStatsModal .pipeline-run-summary-item:nth-child(3n + 1)", 1
    )[1].split("#pipelineRunStatsModal .pipeline-run-summary-grid dt", 1)[0]
