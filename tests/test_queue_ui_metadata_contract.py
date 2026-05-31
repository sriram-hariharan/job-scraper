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


def test_missing_job_prioritization_overlay_is_safe():
    rows = [{"job_doc_id": "job_1", "job_company": "Acme", "job_title": "Backend Engineer", "action": "APPLY"}]

    assert services._overlay_job_prioritization(rows, {}) == rows


def test_missing_tailoring_decision_overlay_is_safe():
    rows = [{"job_doc_id": "job_1", "job_company": "Acme", "job_title": "Backend Engineer", "action": "APPLY"}]

    assert services._overlay_tailoring_decisions(rows, {}) == rows
