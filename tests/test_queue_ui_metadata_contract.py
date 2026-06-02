from pathlib import Path

from src.app import services


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
        assert "Apply now" in source
        assert "Skip for now" in source
        assert "Watch source" in source
        assert "Advisory" in source
        assert "row.action" in source

    assert ".queue-advisory-priority" in css
    assert ".queue-advisory-pill--skip_for_now" in css
    assert ".queue-advisory-pill--watch_source" in css
    assert "job_prioritization_recommendations.csv" in services_source
    assert "JOB_PRIORITIZATION_OVERLAY_FIELDS" in services_source


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
        assert "Tailoring advisory" in source
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
        assert "Ready to apply" in source
        assert "Hold / skip" in source
        assert "Operator review" in source
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
