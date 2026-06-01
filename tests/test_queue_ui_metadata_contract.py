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
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
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
    css = Path("src/app/static/app_redesign.css").read_text(encoding="utf-8")
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


def test_missing_job_prioritization_overlay_is_safe():
    rows = [{"job_doc_id": "job_1", "job_company": "Acme", "job_title": "Backend Engineer", "action": "APPLY"}]

    assert services._overlay_job_prioritization(rows, {}) == rows


def test_missing_tailoring_decision_overlay_is_safe():
    rows = [{"job_doc_id": "job_1", "job_company": "Acme", "job_title": "Backend Engineer", "action": "APPLY"}]

    assert services._overlay_tailoring_decisions(rows, {}) == rows


def test_missing_operator_review_overlay_is_safe():
    rows = [{"job_doc_id": "job_1", "job_company": "Acme", "job_title": "Backend Engineer", "action": "APPLY"}]

    assert services._overlay_operator_review(rows, {}) == rows
