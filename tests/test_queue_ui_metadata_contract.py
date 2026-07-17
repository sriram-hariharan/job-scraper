from pathlib import Path

from src.app import services


def _css_block(css: str, selector: str) -> str:
    start = css.index(selector)
    end = css.index("}", start) + 1
    return css[start:end]


def test_phase77f_css_load_order_and_canonical_cascade_contract():
    executive_markup = Path("src/app/ui.py").read_text(encoding="utf-8")
    planning_markup = Path("src/app/planning_ui.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    for markup in (executive_markup, planning_markup):
        styles_index = markup.index("/static/styles.css")
        redesign_index = markup.index("/static/app_redesign.css")
    assert styles_index < redesign_index

    assert css.count("body .scheduler-page .scheduler-tab-btn {") == 1
    assert css.count("\nbody .scheduler-page .scheduler-table-tabs,") == 1
    assert "body .scheduler-page .scheduler-table-tabs button.scheduler-tab-btn[data-tab]" in css
    assert "#queueTable thead th button.sort-header-btn[data-sort-key]" in css
    assert "html[data-theme=\"light\"] .pill.recommendation-chip.recommendation-chip--tailor" in css
    assert "html[data-theme=\"light\"] .pill.recommendation-chip.recommendation-chip--later" in css
    assert "html[data-theme=\"light\"] .job-apply-btn.review-action-button.review-action-button--available" in css
    assert ".executive-view-mode-row--table .binary-toggle--small .binary-toggle-option span" in css


def test_phase77g_app_chrome_utility_buttons_are_secondary():
    shell_source = Path("src/app/ui_shell.py").read_text(encoding="utf-8")
    app_markup = Path("src/app/ui.py").read_text(encoding="utf-8")
    planning_markup = Path("src/app/planning_ui.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    for class_name in (
        "notification-btn",
        "theme-toggle-btn",
        "profile-avatar-btn",
        "app-shell-menu-btn",
        "app-shell-primary-link",
    ):
        assert class_name in shell_source

    assert "New Scan" in shell_source
    assert "Run Live Pipeline" in app_markup
    assert "Refresh Status" in app_markup
    assert "multi-select-trigger-icon" in app_markup
    assert "multi-select-trigger-icon" in planning_markup

    primary_selector = (
        "button:not(.agentic-review-tab):not(.agentic-review-segment):not(.profile-tab-btn)"
        ":not(.pipeline-run-icon-btn):not(.scan-workspace-tab-btn):not(.scan-workspace-surface-tab)"
        ":not(.sort-header-btn):not(.scheduler-tab-btn)"
        ":not(.ghost-btn):not(.notification-btn):not(.theme-toggle-btn):not(.profile-avatar-btn)"
        ":not(.app-shell-menu-btn):not(.multi-select-trigger):not(.multi-select-option)"
        ":not(.preferences-step-button):not(.preference-location-option):not(.preferences-edit-button)"
        ":not(.preference-location-chip-remove):not(.preferences-utility-button)"
        ":not(.preferences-back-button):not(.preferences-secondary-action)"
    )
    assert primary_selector in css
    assert f"{primary_selector},\n.app-shell-primary-link" in css
    assert "background: linear-gradient(135deg, var(--app-primary), var(--app-violet)) !important" in css

    utility_css = css[
        css.index(".notification-btn,\n.theme-toggle-btn,\n.app-shell-top-right .profile-avatar-btn {"):
        css.index(".theme-toggle-btn,\n.app-shell-primary-link {")
    ]
    for forbidden in (
        "linear-gradient(135deg, var(--app-primary), var(--app-violet))",
        "rgba(37, 99, 235, 0.9)",
    ):
        assert forbidden not in utility_css
    assert "rgba(15, 23, 42, 0.64)" in utility_css
    assert "rgba(241, 245, 249, 0.92)" in utility_css
    assert ".theme-toggle-btn[aria-pressed=\"true\"] .theme-toggle-track" in utility_css
    assert "background: rgba(96, 165, 250, 0.24) !important" in utility_css

    menu_css = _css_block(css, ".app-shell-menu-btn {")
    assert "rgba(15, 23, 42, 0.64)" in menu_css
    assert "linear-gradient(135deg, var(--app-primary), var(--app-violet))" not in menu_css
    assert "background: rgba(255, 255, 255, 0.78) !important" in css

    assert "body .multi-select-trigger {" in css
    caret_css = _css_block(css, "body .multi-select-trigger-icon {")
    assert "background: transparent !important" in caret_css
    assert "width: auto !important" in caret_css
    assert "color: var(--app-muted) !important" in caret_css


def test_queue_ui_renders_job_location_below_title():
    source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    assert "row.job_location" in source
    assert "queue-job-location" in source
    assert "queue-simple-location" in source
    assert ".queue-job-location" in css
    assert ".queue-simple-location" in css
    assert "color: var(--app-muted)" in css
    assert "font-size: 12px" in css


def test_queue_ui_labels_allowed_unknown_timestamps():
    source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    assert 'freshness_status === "unknown_timestamp_allowed"' in source
    assert "Timestamp unavailable" in source
    assert "timestamp-unavailable-label" in source
    assert ".timestamp-unavailable-label" in css


def test_queue_ui_renders_job_prioritization_advisory_separately():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    for source in (app_source, planning_source):
        assert "buildAdvisoryPriorityHtml" in source
        assert "advisory_priority" in source
        assert "existing_action" in source
        assert "Ready for review" in source
        assert "Review later" in source
        assert "Watch source" in source
        assert "<summary>Why?</summary>" in source
        assert "Raw action" in source
        assert "No clear resume match" in source
        assert "Borderline match" in source
        assert "Tailoring may improve fit" in source
        assert "Packet unavailable" in source
        assert "queue-advisory-kicker" not in source
        assert "row.action" in source

    assert ".queue-advisory-priority" in css
    assert ".queue-advisory-pill--skip_for_now" in css
    assert ".queue-advisory-pill--watch_source" in css
    assert ".queue-recommendation-details" in css
    assert ".queue-packet-pill--ready" in css
    assert ".queue-packet-pill--blocked" in css
    assert "job_prioritization_recommendations.csv" in services_source
    assert "JOB_PRIORITIZATION_OVERLAY_FIELDS" in services_source


def test_queue_ui_uses_compact_decision_chips_and_details():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    for source in (app_source, planning_source):
        assert "formatQueueActionLabel" in source
        assert "Ready for review" in source
        assert "Review resume choice" in source
        assert "Tailor first" in source
        assert "Review later" in source
        assert "buildPacketStatusChipHtml" in source
        assert "Packet ready" in source
        assert "No packet" in source
        assert "queue-recommendation-details" in source
        assert "<summary>Why?</summary>" in source
        assert "Action: ${" not in source
        assert "Packet: ${" not in source
        assert "Block: ${" not in source

    assert "flex-direction: row" in css
    assert ".queue-packet-pill" in css
    assert ".queue-recommendation-detail-row" in css


def test_queue_ui_uses_simplified_job_seeker_columns():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    app_markup = Path("src/app/ui.py").read_text(encoding="utf-8")
    planning_markup = Path("src/app/planning_ui.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    for source in (app_source, planning_source):
        assert 'label: "Rank"' in source
        assert 'label: "Job title"' in source
        assert 'label: "Posted at"' in source
        assert 'label: "Recommendation"' in source
        assert 'label: "Match"' in source
        assert 'label: "Selected Resume"' in source
        assert 'label: "Review"' in source
        assert "Review job" in source
        assert "Review later" in source
        assert "Choose resume" in source
        assert "Close resume match" in source
        assert "No clear resume match" in source or "No resume match" in source
        assert "Runner-up resume" in source
        assert "Score gap" in source
        assert "Missing req count" in source or "Missing requirements" in source
        assert "Next step" in source
        assert "Priority reason" in source
        assert "A packet is a review bundle for this job." in source

    for markup in (app_markup, planning_markup):
        assert "Recommendation" in markup
        assert "Posted at" in markup
        assert "Selected Resume" in markup
        assert "Review" in markup
        assert ">Apply<" not in markup

    assert ".queue-job-summary" in css
    assert ".queue-status-stack" in css
    assert ".queue-workspace-pill" in css


def test_phase77b_executive_detail_and_packet_help_contract():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    app_markup = Path("src/app/ui.py").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    planning_markup = Path("src/app/planning_ui.py").read_text(encoding="utf-8")

    assert 'key: "posted_at", label: "Posted at", type: "date"' in app_source
    assert 'key: "runner_up_resume", label: "Runner-up resume"' in app_source
    assert 'key: "score_gap", label: "Score gap"' in app_source
    assert 'key: "missing_requirement_count", label: "Missing req count"' in app_source
    assert 'key: "next_step", label: "Next step"' in app_source
    assert 'key: "queue_priority_reason", label: "Priority reason"' in app_source
    assert 'data-col-key="runner_up_resume"' in app_markup
    assert 'data-col-key="score_gap"' in app_markup
    assert 'data-col-key="missing_requirement_count"' in app_markup
    assert 'data-col-key="next_step"' in app_markup
    assert 'data-col-key="queue_priority_reason"' in app_markup

    for source in (app_source, planning_source, app_markup, planning_markup):
        assert "A packet is a review bundle for this job." in source
        assert "It does not apply to the job." in source

    assert "executive-view-mode-row--table" in app_markup
    queue_header_index = app_markup.index("<h2>Queue Table</h2>")
    toggle_index = app_markup.index("executive-view-mode-row--table")
    controls_start = app_markup.index('<section class="card controls-card">')
    controls_end = app_markup.index('<div class="subtext pipeline-run-meta"')
    assert toggle_index > queue_header_index
    assert "executive-view-mode-row--table" not in app_markup[controls_start:controls_end]


def test_phase77b_recommendation_has_single_why_control_per_cell():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")

    for source in (app_source, planning_source):
        assert "buildQueueRecommendationCellHtml" in source or "buildPlanningRecommendationCellHtml" in source
        assert "${buildAdvisoryPriorityHtml(row)}" not in source
        assert "${buildTailoringDecisionHtml(row)}" not in source
        assert "${buildOperatorReviewHtml(row)}" not in source
        assert "<summary>Why?</summary>" in source


def test_phase77c_table_polish_contract():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    app_markup = Path("src/app/ui.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    assert "binary-toggle--small" in app_markup
    assert "application-table-title-row" in app_markup
    assert "executive-view-mode-row--table" in app_markup
    title_row_index = app_markup.index("application-table-title-row")
    toggle_index = app_markup.index("executive-view-mode-row--table")
    header_right_index = app_markup.index("application-table-header-right")
    assert title_row_index < toggle_index < header_right_index
    assert "Posted:" not in app_source
    assert "Posted:" not in planning_source
    assert 'key: "posted_at", label: "Posted at", type: "date"' in app_source
    assert 'key: "posted_at", label: "Posted at", type: "date"' in planning_source
    assert "grid-template-columns: minmax(0, 1fr) auto" in css
    assert ".application-table-title-row" in css
    assert "body .multi-select-trigger-icon" in css
    assert "border-radius: 0 !important" in css
    assert "appearance: none !important" in css
    assert "background-image: none !important" in css
    assert ".table-wrap thead .sort-header-btn" in css
    assert 'class="sort-header-btn"' in app_source
    assert '<span class="sort-header-indicator">↕</span>' in app_source
    actual_sort_css = css[
        css.index(".table-wrap thead .sort-header-btn,"):
        css.index(".table-wrap thead .sort-header-btn::before,")
    ]
    for boxed_property in (
        "padding: 8px",
        "border-radius: 9px",
        "border-radius: 999px",
        "box-shadow: var(--app-shadow-sm)",
        "background: linear-gradient(135deg, var(--app-primary), var(--app-violet))",
    ):
        assert boxed_property not in actual_sort_css
    assert "background: transparent !important" in actual_sort_css
    assert "border-radius: 0 !important" in actual_sort_css
    id_sort_css = _css_block(css, "#queueTable thead th button.sort-header-btn[data-sort-key],")
    assert "border: 0 !important" in id_sort_css
    assert "border-radius: 0 !important" in id_sort_css
    assert "background: transparent !important" in id_sort_css
    assert "background-image: none !important" in id_sort_css


def test_phase77d_stateful_table_header_and_review_styling_contract():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    for source in (app_source, planning_source):
        assert "getRecommendationTone" in source
        assert "recommendation-chip recommendation-chip--${tone}" in source
        assert "review-action-button--available" in source
        assert "review-action-button--disabled" in source

    assert ".recommendation-chip--tailor" in css
    assert ".recommendation-chip--later" in css
    assert ".recommendation-chip--ready" in css
    assert ".recommendation-chip--choice" in css
    assert ".recommendation-chip--unavailable" in css
    assert "background: #ddd6fe !important" in css
    assert "background: #fcd34d !important" in css
    tailor_css = _css_block(css, ".recommendation-chip--tailor,")
    later_css = _css_block(css, ".recommendation-chip--later,")
    for block in (tailor_css, later_css):
        assert "rgba(255, 255, 255" not in block
        assert "transparent" not in block
    assert "background: #ddd6fe !important" in tailor_css
    assert "background: #fcd34d !important" in later_css
    recommendation_css = css[
        css.index(".recommendation-chip {"):
        css.index(".queue-workspace-pill")
    ]
    assert "background: rgba(124, 58, 237" not in recommendation_css
    assert "background: rgba(245, 158, 11, 0.16)" not in recommendation_css
    assert ".review-action-button--available" in css
    assert ".review-action-button--disabled" in css
    assert 'html[data-theme="dark"] .recommendation-chip--tailor' in css
    assert 'html[data-theme="dark"] .review-action-button--available' in css
    assert "button:not(.agentic-review-tab):not(.agentic-review-segment):not(.profile-tab-btn):not(.pipeline-run-icon-btn):not(.scan-workspace-tab-btn):not(.scan-workspace-surface-tab):not(.sort-header-btn):not(.scheduler-tab-btn)" in css
    assert css.count(".recommendation-chip--tailor") == 3
    assert css.count(".review-action-button--available") == 4
    assert 'data-view-tailoring="true"' in planning_source
    assert "handleTailoringClick(button)" in planning_source
    assert 'stateClass = "planning-tailoring-btn--review";' in planning_source
    assert "reviewActionStateClass = \"review-action-button--available\";" in planning_source


def test_phase77e_scheduler_tabs_are_underline_style():
    app_markup = Path("src/app/ui.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    assert "Contract Health" in app_markup
    assert "JSONL Rows" in app_markup
    assert "Postgres Rows" in app_markup
    assert "Latest Runs by Job" in app_markup
    scheduler_section = app_markup[
        app_markup.index('<div class="scheduler-table-tabs">'):
        app_markup.index('<div class="scheduler-table-header">')
    ]
    assert "scheduler-tab-btn" in scheduler_section
    assert "ghost-btn scheduler-tab-btn" not in scheduler_section
    assert "body .scheduler-page .scheduler-tab-btn::after" in css
    assert "body .scheduler-page .scheduler-tab-btn.active::after" in css
    assert "html[data-theme=\"light\"] body .scheduler-page .scheduler-table-tabs" in css
    assert "background: transparent !important" in css
    scheduler_css = css[
        css.index("body .scheduler-page .scheduler-table-tabs,"):
        css.index("/* ui_redesign_v25: remove remaining tab button chrome on concrete pages. */")
    ]
    for boxed_property in (
        "border-radius: 12px",
        "background: #e0f2fe",
        "background: linear-gradient(135deg, var(--app-primary), var(--app-violet))",
        "box-shadow: var(--app-shadow-sm)",
    ):
        assert boxed_property not in scheduler_css
    assert "border-radius: 0 !important" in scheduler_css
    assert "background-color: transparent !important" in scheduler_css
    assert "background-image: none !important" in scheduler_css
    assert "body .scheduler-page .scheduler-table-tabs button.scheduler-tab-btn[data-tab]" in scheduler_css
    concrete_state_selector = (
        "body .scheduler-page .scheduler-table-tabs .scheduler-tab-row > "
        "button.scheduler-tab-btn[data-tab][role=\"tab\"].active"
    )
    assert concrete_state_selector in scheduler_css
    concrete_tab_css = _css_block(
        css, "body .scheduler-page .scheduler-table-tabs button.scheduler-tab-btn[data-tab],"
    )
    active_tab_css = _css_block(
        css, "body .scheduler-page .scheduler-table-tabs button.scheduler-tab-btn[data-tab].active,"
    )
    for block in (concrete_tab_css, active_tab_css):
        assert "border: 0 !important" in block
        assert "border-width: 0 !important" in block
        assert "border-style: none !important" in block
        assert "border-color: transparent !important" in block
        assert "border-radius: 0 !important" in block
        assert "background: transparent !important" in block
        assert "background-color: transparent !important" in block
        assert "background-image: none !important" in block
        assert "box-shadow: none !important" in block
        assert "background: var(--app-panel)" not in block
        assert "background: #ffffff" not in block
        assert "border: 1px solid" not in block
        assert "linear-gradient(135deg, var(--app-primary), var(--app-violet))" not in block
    assert "button.scheduler-tab-btn[data-tab].active::after" in scheduler_css
    assert "background: linear-gradient(90deg, #2563eb, #06b6d4) !important" in scheduler_css


def test_phase77h_dark_tabs_keep_underline_style_with_readable_text():
    app_markup = Path("src/app/ui.py").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    scheduler_section = app_markup[
        app_markup.index('<div class="scheduler-table-tabs">'):
        app_markup.index('<div class="scheduler-table-header">')
    ]
    assert 'class="scheduler-tab-btn active"' in scheduler_section
    assert 'class="scheduler-tab-btn"' in scheduler_section
    assert 'data-tab="contract"' in scheduler_section
    assert 'role="tab"' in scheduler_section

    dark_tab_css = css[
        css.index('html[data-theme="dark"] body .scheduler-page .scheduler-table-tabs,'):
        css.index('html[data-theme="dark"] body .scheduler-page .scheduler-table-header h2,')
    ]

    assert 'html[data-theme="dark"] body .scheduler-page .scheduler-tab-btn' in dark_tab_css
    assert (
        'html[data-theme="dark"] body .scheduler-page .scheduler-table-tabs '
        '.scheduler-tab-row button.scheduler-tab-btn'
    ) in dark_tab_css
    assert (
        'html[data-theme="dark"] body .scheduler-page .scheduler-table-tabs '
        '.scheduler-tab-row > button.scheduler-tab-btn[data-tab][role="tab"]'
    ) in dark_tab_css
    assert (
        'html[data-theme="dark"] body .scheduler-page .scheduler-table-tabs '
        '.scheduler-tab-row button.scheduler-tab-btn.active'
    ) in dark_tab_css
    assert (
        'html[data-theme="dark"] body .scheduler-page .scheduler-table-tabs '
        '.scheduler-tab-row > button.scheduler-tab-btn[data-tab][role="tab"].active'
    ) in dark_tab_css
    assert 'html[data-theme="dark"] body #applicationViewRoot .application-tab' in dark_tab_css
    assert 'html[data-theme="dark"] body #applicationViewRoot .application-tab:not(.active)' in dark_tab_css
    assert 'html[data-theme="dark"] body #applicationViewRoot .application-tab.active' in dark_tab_css
    assert "color: #cbd5e1 !important" in dark_tab_css
    assert "color: #f8fafc !important" in dark_tab_css
    assert "color: #ffffff !important" in dark_tab_css
    assert "background: linear-gradient(90deg, #60a5fa, #22d3ee) !important" in dark_tab_css

    for block in (
        _css_block(css, 'html[data-theme="dark"] body .scheduler-page .scheduler-tab-btn,'),
        _css_block(css, 'html[data-theme="dark"] body .scheduler-page .scheduler-tab-btn.active,'),
    ):
        assert "background: transparent !important" in block
        assert "background-color: transparent !important" in block
        assert "background-image: none !important" in block
        assert "border: 0 !important" in block
        assert "border-width: 0 !important" in block
        assert "border-style: none !important" in block
        assert "border-radius: 0 !important" in block
        assert "box-shadow: none !important" in block
        assert "background: var(--app-panel)" not in block
        assert "border: 1px solid" not in block
        assert "border-radius: 12px" not in block
        assert "linear-gradient(135deg, var(--app-primary), var(--app-violet))" not in block


def test_queue_ui_renders_tailoring_decision_advisory_separately():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    for source in (app_source, planning_source):
        assert "buildTailoringDecisionHtml" in source
        assert "tailoring_decision" in source
        assert "tailoring_reason_codes" in source
        assert "No tailoring needed" in source
        assert "Tailor before apply" in source
        assert "Do not tailor" in source
        assert "<summary>Why?</summary>" in source
        assert "queue-tailoring-kicker" not in source
        assert "row.action" in source

    assert ".queue-tailoring-decision" in css
    assert ".queue-tailoring-pill--do_not_tailor" in css
    assert ".queue-tailoring-pill--tailor_before_apply" in css
    assert "tailoring_decision_recommendations.csv" in services_source
    assert "TAILORING_DECISION_OVERLAY_FIELDS" in services_source


def test_queue_ui_renders_operator_review_advisory_separately():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    for source in (app_source, planning_source):
        assert "buildOperatorReviewHtml" in source
        assert "operator_review_lane" in source
        assert "operator_review_reason_codes" in source
        assert "Ready for review" in source
        assert "Skip for now" in source
        assert "<summary>Why?</summary>" in source
        assert "queue-operator-kicker" not in source
        assert "row.action" in source

    assert ".queue-operator-review" in css
    assert ".queue-operator-pill--ready_to_apply" in css
    assert ".queue-operator-pill--hold_or_skip" in css
    assert "operator_review_recommendations.csv" in services_source
    assert "OPERATOR_REVIEW_OVERLAY_FIELDS" in services_source


def test_agentic_workflow_summary_ui_contract():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    profile_source = Path("src/app/static/profile.js").read_text(encoding="utf-8")
    css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    for source in (app_source, planning_source, profile_source):
        assert "renderAgenticWorkflowSummaryPanel" in source
        assert "Agentic Workflow Summary" in source
        assert "ready_to_apply_count" in source
        assert "hold_or_skip_count" in source
        assert "missing_artifacts" in source
        assert "summary_markdown" in source
        assert "escapeHtml(markdown)" in source

    assert "No agentic workflow summary recorded for this run." in profile_source
    assert ".agentic-workflow-summary-card" in css
    assert ".agentic-workflow-markdown" in css
    assert "agentic_workflow_summary.json" in services_source
    assert "agentic_workflow_summary.md" in services_source
    assert "agentic_workflow_summary_json" in services_source
    assert "agentic_workflow_summary_md" in services_source


def test_agentic_workflow_verification_ui_contract():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    profile_source = Path("src/app/static/profile.js").read_text(encoding="utf-8")
    css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    for source in (app_source, planning_source, profile_source):
        assert "renderAgenticWorkflowVerificationPanel" in source
        assert "Agentic Workflow Verification" in source
        assert "validation_status" in source
        assert "checked_artifacts" in source
        assert "missing_artifacts" in source
        assert "reason_codes" in source
        assert "consistency_checks" in source
        assert "verification_json" in source

    assert "No agentic workflow verification recorded for this run." in profile_source
    assert ".agentic-workflow-verification-card" in css
    assert ".agentic-workflow-verification-status--passed" in css
    assert ".agentic-workflow-verification-status--warning" in css
    assert ".agentic-workflow-verification-status--failed" in css
    assert "agentic_workflow_verification.json" in services_source
    assert "agentic_workflow_verification_json" in services_source


def test_agentic_workflow_manifest_ui_contract():
    review_source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    review_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    assert "Agentic Workflow Manifest" in review_source
    assert "agentic_workflow_manifest" in review_source
    assert "manifest_json" in review_source
    assert "manifest_markdown" in review_source
    assert "ordered_agent_keys" in review_source
    assert "generated_artifact_kinds" in review_source
    assert "artifact_dependency_order" in review_source
    assert "mutates_production_decisions" in review_source
    assert "No agentic workflow manifest recorded for this run." in review_source
    assert "Manifest markdown" in review_source
    assert "escapeHtml(markdown)" in review_source

    assert ".agentic-workflow-manifest-card" in review_css
    assert ".agentic-review-manifest-agent" in review_css
    assert ".agentic-review-manifest-metrics" in review_css
    assert ".agentic-review-manifest-agent-pills" in review_css

    assert "agentic_workflow_manifest.json" in services_source
    assert "agentic_workflow_manifest.md" in services_source
    assert "agentic_workflow_manifest_json" in services_source
    assert "agentic_workflow_manifest_md" in services_source
    assert "_agentic_workflow_manifest_from_artifacts" in services_source


def test_agentic_workflow_execution_plan_ui_contract():
    review_source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    review_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    assert "Agentic Workflow Execution Plan" in review_source
    assert "agentic_workflow_execution_plan" in review_source
    assert "plan_json" in review_source
    assert "plan_markdown" in review_source
    assert "ordered_steps" in review_source
    assert "execution_mode" in review_source
    assert "execution_enabled" in review_source
    assert "execution_status" in review_source
    assert "No agentic workflow execution plan recorded for this run." in review_source
    assert "Execution plan markdown" in review_source
    assert "escapeHtml(markdown)" in review_source

    assert ".agentic-workflow-execution-plan-card" in review_css
    assert ".agentic-review-plan-step" in review_css
    assert ".agentic-review-plan-metrics" in review_css

    assert "agentic_workflow_execution_plan.json" in services_source
    assert "agentic_workflow_execution_plan.md" in services_source
    assert "agentic_workflow_execution_plan_json" in services_source
    assert "agentic_workflow_execution_plan_md" in services_source
    assert "_agentic_workflow_execution_plan_from_artifacts" in services_source


def test_agentic_workflow_dry_run_ui_contract():
    review_source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    review_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    assert "Agentic Workflow Dry Run" in review_source
    assert "agentic_workflow_dry_run" in review_source
    assert "result_json" in review_source
    assert "report_markdown" in review_source
    assert "ordered_step_results" in review_source
    assert "runner_version" in review_source
    assert "executed_step_count" in review_source
    assert "did_execute" in review_source
    assert "would_trace" in review_source
    assert "No agentic workflow dry run recorded for this run." in review_source
    assert "Dry-run report markdown" in review_source
    assert "escapeHtml(markdown)" in review_source

    assert ".agentic-workflow-dry-run-card" in review_css
    assert ".agentic-review-dry-run-step" in review_css
    assert ".agentic-review-dry-run-metrics" in review_css

    assert "agentic_workflow_dry_run_result.json" in services_source
    assert "agentic_workflow_dry_run_report.md" in services_source
    assert "agentic_workflow_dry_run_result_json" in services_source
    assert "agentic_workflow_dry_run_report_md" in services_source
    assert "_agentic_workflow_dry_run_from_artifacts" in services_source


def test_proposal_only_mutation_plan_agentic_review_ui_contract():
    review_source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    review_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    assert "Proposal-Only Mutation Plan" in review_source
    assert "proposal_only_mutation_plan" in review_source
    assert "renderProposalOnlyMutationPlanSection" in review_source
    assert "proposal_only_mutation_planner.EXECUTION_MODE" in services_source or "proposal_only_mutation_planner" in services_source
    assert "proposal_only_mutation_plan_result.json" in services_source
    assert "proposal_only_mutation_plan_report.md" in services_source
    assert "proposal_only_mutation_plan_result_json" in services_source
    assert "proposal_only_mutation_plan_report_md" in services_source
    assert "_proposal_only_mutation_plan_from_artifacts" in services_source
    assert "No proposal-only mutation plan artifacts recorded for this run yet." in review_source
    assert "can_mutate" in review_source
    assert "can_approve" in review_source
    assert "did_store_approval" in review_source
    assert "Required future gates" in review_source
    assert "Proposal mutation types" in review_source
    assert "Blocked execution reasons" in review_source
    assert "Proposal plan report markdown" in review_source
    assert "escapeHtml(markdown)" in review_source

    assert ".proposal-only-mutation-plan-card" in review_css
    assert ".proposal-only-mutation-plan-metrics" in review_css
    assert ".proposal-only-mutation-plan-warning" in review_css
    assert ".proposal-only-mutation-plan-notice" in review_css

    for forbidden in [
        "proposalPlanApprove",
        "proposalPlanReject",
        "proposal_only_mutation_approve",
        "proposal_only_mutation_reject",
        "/proposal-approval",
        "/mutation-execution",
    ]:
        assert forbidden not in review_source
        assert forbidden not in services_source


def test_read_only_adapter_preflight_ui_contract():
    review_source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    review_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    assert "Read-Only Adapter Preflight" in review_source
    assert "read_only_adapter_preflight" in review_source
    assert "renderReadOnlyAdapterPreflightSection" in review_source
    assert "renderReadOnlyAdapterPreflightRow" in review_source
    assert "adapter_preflight_results" in review_source
    assert "planned_adapter_count" in review_source
    assert "executable_adapter_count" in review_source
    assert "ready_read_only_contract_count" in review_source
    assert "needs_adapter_count" in review_source
    assert "blocked_count" in review_source
    assert "preflight_status" in review_source
    assert "allowed_execution_mode" in review_source
    assert "execution_enabled" in review_source
    assert "did_execute" in review_source
    assert "No read-only adapter preflight recorded for this run." in review_source
    assert "Preflight report markdown" in review_source
    assert "no agents executed" in review_source

    assert ".read-only-adapter-preflight-card" in review_css
    assert ".read-only-adapter-preflight-metrics" in review_css
    assert ".read-only-adapter-preflight-row" in review_css
    assert ".read-only-adapter-preflight-pills" in review_css

    assert "read_only_adapter_preflight.json" in services_source
    assert "read_only_adapter_preflight.md" in services_source
    assert "read_only_adapter_preflight_json" in services_source
    assert "read_only_adapter_preflight_md" in services_source
    assert "_read_only_adapter_preflight_from_artifacts" in services_source


def test_manual_read_only_adapter_chain_empty_read_model_is_safe():
    payload = services._manual_read_only_adapter_chain_from_artifacts([])

    assert payload["present"] is False
    assert payload["available"] is False
    assert payload["validation_status"] == "missing"
    assert payload["did_execute_chain"] is False
    assert payload["did_mutate_production"] is False
    assert payload["adapter_execution_order"] == []
    assert payload["summary"] == {}
    assert payload["reason_codes"] == []
    assert payload["warning_codes"] == []


def test_explicit_read_only_chain_generator_empty_read_model_is_safe():
    payload = services._explicit_read_only_chain_artifact_generation_from_artifacts([])

    assert payload["present"] is False
    assert payload["available"] is False
    assert payload["validation_status"] == "missing"
    assert payload["did_run_chain"] is False
    assert payload["did_mutate_production"] is False
    assert payload["require_explicit_input"] is False
    assert payload["require_explicit_output_dir"] is False
    assert payload["queue_input_artifact_path"] == ""
    assert payload["output_dir"] == ""
    assert payload["chain_result_summary"] == {}
    assert payload["generator_artifacts"] == []
    assert payload["reason_codes"] == []
    assert payload["warning_codes"] == []


def test_agentic_review_dedicated_page_contract():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    profile_source = Path("src/app/static/profile.js").read_text(encoding="utf-8")
    review_source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    profile_ui_source = Path("src/app/profile_ui.py").read_text(encoding="utf-8")
    shell_source = Path("src/app/ui_shell.py").read_text(encoding="utf-8")
    api_source = Path("src/app/api.py").read_text(encoding="utf-8")
    review_css = Path("src/app/static/agentic_review.css").read_text(encoding="utf-8")
    common_css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
    executive_ui_source = Path("src/app/ui.py").read_text(encoding="utf-8")
    planning_ui_source = Path("src/app/planning_ui.py").read_text(encoding="utf-8")

    for source in (app_source, planning_source, profile_source):
        assert "View Agentic Review" not in source
        assert "agentic-review-link-card" not in source

    assert "pipeline-run-agentic-review-btn" in profile_source
    assert 'aria-label="Agentic review"' in profile_source
    assert 'data-tooltip="View"' in profile_source
    assert 'data-tooltip="Agentic review"' in profile_source
    assert '/profile/pipeline-runs/${encodeURIComponent(run.run_id || "")}/agentic-review' in profile_source
    assert '<th>Actions</th>' in profile_ui_source
    assert '<th>View</th>' not in profile_ui_source
    assert "pipeline-run-actions-cell" in profile_source
    assert "pipeline-run-icon-btn pipeline-run-view-btn" in profile_source
    assert "pipeline-run-icon-btn pipeline-run-agentic-review-btn" in profile_source
    assert "pipeline-run-action-icon--view" in profile_source
    assert "pipeline-run-action-icon--agentic" in profile_source
    assert '("Scheduler", "/scheduler", "S")' in shell_source
    assert '("Agentic Review", "/agentic-review", "AR")' not in shell_source

    assert '@router.get("/agentic-review"' not in profile_ui_source
    assert '@router.get("/profile/pipeline-runs/{run_id}/agentic-review"' in profile_ui_source
    assert '@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")' in api_source
    route_source = profile_ui_source.split('@router.get("/profile/pipeline-runs/{run_id}/agentic-review"', 1)[1]
    route_source = route_source.split('@router.get("/profile/preferences"', 1)[0]
    assert "Agentic Workflow Summary" in profile_ui_source
    assert "Agentic Workflow Verification" in profile_ui_source
    assert "Agent Trace" in profile_ui_source
    assert "Overview" in profile_ui_source
    assert "Advisory Board" in profile_ui_source
    assert "Artifacts / Diagnostics" in profile_ui_source
    assert "Job Prioritization" in profile_ui_source
    assert "Tailoring Decision" in profile_ui_source
    assert "Operator Review" in profile_ui_source
    assert "agentic_review.js" in profile_ui_source
    assert "agentic_review.css" in profile_ui_source
    assert route_source.index("app_redesign.css") < route_source.index("agentic_review.css")
    assert "{render_top_shell(\"/profile\")}" in route_source
    assert 'href="/profile?tab=pipeline-runs">Back to pipeline runs</a>' in route_source
    assert 'href="/profile">Back to pipeline runs</a>' not in route_source
    assert "getProfileTabTargetFromUrl" in profile_source
    assert 'tab === "pipeline-runs"' in profile_source
    assert 'activateProfileTab(getProfileTabTargetFromUrl())' in profile_source
    assert "New Scan" in shell_source
    assert "app-shell-top-right" in shell_source
    assert 'body class="agentic-review-body"' not in route_source
    assert "agentic-review-standalone-nav" not in route_source
    assert 'role="tablist"' in profile_ui_source
    assert 'aria-selected="true"' in profile_ui_source
    assert "app_redesign.css" in executive_ui_source
    assert "app_redesign.css" in planning_ui_source

    assert "agenticReviewPriorityPanel" in review_source
    assert "job_prioritization_rows" in review_source
    assert "tailoring_decision_rows" in review_source
    assert "operator_review_rows" in review_source
    assert "No advisory rows recorded for this run." in review_source
    assert "data-agentic-tab-target" in profile_ui_source
    assert "data-agentic-advisory-target" in profile_ui_source
    assert "bindAgenticReviewTabs" in review_source
    assert "renderAgenticReviewDiagnosticsPanel" in review_source
    assert "renderAgenticWorkflowManifestSection" in review_source
    assert "owner_user_id" not in review_source

    assert ".agentic-review-link-card" not in common_css
    assert ".agentic-review-link-btn" not in common_css
    assert ".profile-tabs" in common_css
    assert ".profile-tab-btn::after" in common_css
    assert "--profile-tab-color" in common_css
    assert ".profile-tab-btn.is-active::after" in common_css
    assert ".pipeline-run-actions-cell" in common_css
    assert ".pipeline-run-icon-btn" in common_css
    assert ".pipeline-run-icon-btn::after" in common_css
    assert "content: attr(data-tooltip)" in common_css
    assert "html[data-theme=\"light\"] .pipeline-run-icon-btn" in common_css
    assert 'url("/static/media/view_img.svg")' in common_css
    assert 'url("/static/media/ai-img.svg")' in common_css
    profile_tabs_block = common_css.split(".profile-tabs", 1)[1].split(".profile-tab-btn", 1)[0]
    assert "border-radius: 999px" not in profile_tabs_block
    assert "background: var(--app-surface-2)" not in profile_tabs_block
    assert "box-shadow: var(" not in profile_tabs_block
    profile_tab_button_block = common_css.split("\n.profile-tab-btn {", 1)[1].split(".profile-tab-btn::after", 1)[0]
    assert "border-radius: 999px" not in profile_tab_button_block
    assert "background: var(--app-surface-2)" not in profile_tab_button_block
    profile_active_block = common_css.split(".profile-tab-btn.is-active", 1)[1].split(
        ".profile-tab-btn.is-active .profile-tab-icon", 1
    )[0]
    assert "outline-offset: -4px" not in profile_active_block
    assert "inset 0 0 0 2px" not in profile_active_block
    assert ".agentic-review-body" not in review_css
    assert ".agentic-review-standalone-nav" not in review_css
    assert ".agentic-review-page" in review_css
    assert ".agentic-review-tabs" in review_css
    assert ".agentic-review-segmented" in review_css
    assert ".agentic-review-tab::after" in review_css
    assert ".agentic-review-segment::after" in review_css
    assert "--agentic-tab-color" in review_css
    assert 'data-agentic-tab-target="agenticReviewOverviewTab"' in review_css
    assert 'data-agentic-advisory-target="agenticReviewTailoringPanel"' in review_css
    assert ".agentic-review-table" in review_css
    assert ".agent-trace-json-detail pre" in review_css
    assert "box-sizing: border-box" in review_css
    assert "min-width: 0" in review_css
    assert "overflow: auto" in review_css
    assert "background: #f8fafc" in review_css
    assert "color: #0f172a" in review_css
    assert ".app-shell" not in review_css
    assert ".sidebar" not in review_css
    assert ".topbar" not in review_css
    assert "body {" not in review_css
    assert ".agentic-review-page" not in common_css
    assert ".agentic-review-tabs" not in common_css
    assert ".agentic-review-tab::after" not in common_css
    assert ".agentic-review-segmented" not in common_css
    assert ".agentic-workflow-summary-card" not in common_css
    assert ".agent-trace-panel" not in common_css


def test_missing_job_prioritization_overlay_is_safe():
    rows = [{"job_doc_id": "job_1", "job_company": "Acme", "job_title": "Backend Engineer", "action": "APPLY"}]

    assert services._overlay_job_prioritization(rows, {}) == rows


def test_missing_tailoring_decision_overlay_is_safe():
    rows = [{"job_doc_id": "job_1", "job_company": "Acme", "job_title": "Backend Engineer", "action": "APPLY"}]

    assert services._overlay_tailoring_decisions(rows, {}) == rows


def test_missing_operator_review_overlay_is_safe():
    rows = [{"job_doc_id": "job_1", "job_company": "Acme", "job_title": "Backend Engineer", "action": "APPLY"}]

    assert services._overlay_operator_review(rows, {}) == rows


def test_live_pipeline_overlay_keeps_one_finalizing_activity_state():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    markup = Path("src/app/ui.py").read_text(encoding="utf-8")
    css = Path("src/app/static/styles.css").read_text(encoding="utf-8")

    assert 'label: "Finalizing pipeline results"' in app_source
    assert 'description: "Saving run results and preparing the dashboards."' in app_source
    assert "allKnownStagesComplete" in app_source
    assert "groups.push(PIPELINE_FINALIZING_FALLBACK)" in app_source
    assert 'status === "running"' in app_source
    assert 'activeStep.scrollIntoView({ block: "nearest", behavior: "smooth" })' in app_source
    assert "window.location" not in app_source[app_source.index("function renderPipelineStageStepper"):app_source.index("function getPipelineSuccessKey")]
    for overlay_id in ("pipelineOverlayLoading", "pipelineOverlaySuccess", "pipelineOverlayFailure"):
        assert f'id="{overlay_id}"' in markup
    metric_css = css[css.index(".pipeline-loading-counts {", css.index("/* phase129c:")):]
    assert "display: flex !important" in metric_css
    assert "flex-wrap: wrap" in metric_css
    assert "justify-content: center !important" in metric_css
    assert "animation: workflow-step-spin 900ms linear infinite" in css


def test_executive_and_planning_preferences_filters_use_backend_ids_and_search():
    executive_markup = Path("src/app/ui.py").read_text(encoding="utf-8")
    planning_markup = Path("src/app/planning_ui.py").read_text(encoding="utf-8")
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    api_source = Path("src/app/api.py").read_text(encoding="utf-8")
    services_source = Path("src/app/services.py").read_text(encoding="utf-8")

    assert 'id="preferenceFilter"' in executive_markup
    assert 'id="planningPreferenceFilter"' in planning_markup
    for markup in (executive_markup, planning_markup):
        assert 'data-all-value="__all__"' in markup
        assert 'data-searchable="true"' in markup
        assert "All Preferences" in markup
        assert "Search preferences" in markup
        assert "No preferences found" in markup

    for source in (app_source, planning_source):
        assert 'fetchJson("/onboarding/preferences")' in source
        assert 'appendMultiValueParams(params, "preference_id", preferenceIds)' in source
        assert 'value !== (root.dataset.allValue || "")' in source
        assert "filterMultiSelectOptions" in source
        assert "resetMultiSelectToAll" in source

    assert "preference_id: list[str] | None = Query(default=None)" in api_source
    assert "preference_id=preference_id or []" in api_source
    assert '"preference_options"' in services_source
    assert "_filter_browse_rows_by_preference_ids" in services_source
    assert 'if _clean_text(row.get("role_family")) in allowed' in services_source
    assert "total_count = len(selected)" in services_source


def test_shared_multi_select_contract_supports_dynamic_preference_options():
    executive_markup = Path("src/app/ui.py").read_text(encoding="utf-8")
    planning_markup = Path("src/app/planning_ui.py").read_text(encoding="utf-8")
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    for markup in (executive_markup, planning_markup):
        preference_markup = markup[markup.index('data-placeholder="All Preferences"'):]
        assert 'class="multi-select-option is-selected" data-value="__all__" aria-checked="true"' in preference_markup
        assert preference_markup.count('placeholder="Search preferences"') == 1
        assert preference_markup.count('aria-label="Search preferences"') == 1
        assert 'class="multi-select-empty" hidden' in preference_markup

    for source in (app_source, planning_source):
        engine = source[source.index("function handleMultiSelectOptionSelection"):source.index("function normalize", source.index("function handleMultiSelectOptionSelection"))]
        assert 'menu.addEventListener("click", (event) =>' in engine
        assert 'event.target.closest(".multi-select-option")' in engine
        assert "handleMultiSelectOptionSelection(root, option)" in engine
        assert 'setMultiSelectOptionSelected(candidate, candidate === option)' in engine
        assert "setMultiSelectOptionSelected(allOption, false)" in engine
        assert "resetMultiSelectToAll(root.id)" in engine
        assert 'getMultiSelectMenu(root)?.querySelector(".multi-select-options")' in engine
        assert 'option.addEventListener("click"' not in engine
        assert 'root.classList.toggle("opens-upward", openAbove)' in source
        assert 'menu.dataset.placement = openAbove ? "top" : "bottom"' in source

    canonical_css = css[css.index("body .multi-select {"):css.index("body .application-tabs {")]
    assert "background: var(--app-surface-2) !important" in canonical_css
    assert "position: sticky" in canonical_css
    assert "overflow-y: auto !important" in canonical_css
    assert "linear-gradient(135deg, var(--app-primary), var(--app-violet))" not in canonical_css
    assert ":not(.multi-select-option)" in css


def test_shared_preference_search_filters_current_portaled_options_without_mutating_selection():
    app_source = Path("src/app/static/app.js").read_text(encoding="utf-8")
    planning_source = Path("src/app/static/planning.js").read_text(encoding="utf-8")
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")

    for source in (app_source, planning_source):
        search_engine = source[
            source.index("function normalizeMultiSelectSearchText"):
            source.index("function handleMultiSelectOptionSelection")
        ]
        assert '.addEventListener("input", () => filterMultiSelectOptions' in search_engine
        assert '.toLowerCase()' in search_engine
        assert '.replace(/[\\/_-]+/g, " ")' in search_engine
        assert '.replace(/\\s+/g, " ")' in search_engine
        assert "normalizeMultiSelectSearchText(label).includes(normalizedQuery)" in search_engine
        assert "getMultiSelectOptions(root).forEach((option) =>" in search_engine
        assert 'getMultiSelectMenu(root)?.querySelector(".multi-select-search-input")' in search_engine
        assert "option.hidden = !isVisible" in search_engine
        assert "empty.hidden = visibleCount > 0" in search_engine
        assert "setMultiSelectOptionSelected" not in search_engine
        assert "aria-checked" not in search_engine
        assert "fetch(" not in search_engine
        assert "fetchJson(" not in search_engine

    assert "body .multi-select-option[hidden]" in css
    assert "body .multi-select-empty[hidden]" in css
    assert "display: none !important" in css


def test_preference_filter_rejects_ids_outside_authenticated_owner_preferences(monkeypatch):
    monkeypatch.setattr(
        services,
        "_preferences_for_pipeline",
        lambda owner_user_id="": {"selected_role_families": ["data_science"]},
    )
    requested, validated = services._validated_browse_preference_ids(
        ["data_science", "backend_engineering"],
        owner_user_id="owner-1",
    )
    rows = [
        {"job_doc_id": "job-1", "role_family": "data_science"},
        {"job_doc_id": "job-2", "role_family": "backend_engineering"},
    ]
    filtered = services._filter_browse_rows_by_preference_ids(
        rows,
        requested_ids=requested,
        validated_ids=validated,
    )

    assert validated == ["data_science"]
    assert [row["job_doc_id"] for row in filtered] == ["job-1"]
