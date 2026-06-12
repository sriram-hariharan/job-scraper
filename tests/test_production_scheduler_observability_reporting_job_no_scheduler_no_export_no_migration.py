from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api


REPORTING_JOB_ENDPOINT = (
    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-reporting-job"
)
REPORT_ENDPOINT = (
    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-report"
)
DASHBOARD_ENDPOINT = (
    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-dashboard"
)
EXPORT_PREVIEW_ENDPOINT = (
    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-export-preview"
)
WRITER_STATUS_ENDPOINT = (
    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-writer-status"
)


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _allowed_reporting_decision():
    return {
        "production_scheduler_observability_reporting_allowed": True,
        "production_scheduler_observability_reporting_status": "passed",
        "production_scheduler_observability_reporting_read_only": True,
        "production_scheduler_observability_reporting_reason_codes": [],
    }


def _assert_reporting_job_no_side_effects(payload):
    assert payload["did_persist_reporting_result"] is False
    assert payload["did_schedule_background_work"] is False
    assert payload["did_create_reporting_job_record"] is False
    assert payload["did_export_files"] is False
    assert payload["did_execute_scheduler"] is False
    assert payload["did_execute_application"] is False
    assert payload["did_submit_application"] is False
    assert payload["migration_required"] is False
    assert payload["persistence_enabled"] is False
    assert payload["reporting_job_record_enabled"] is False
    assert payload["metrics_writer_enabled"] is False
    assert payload["logging_writer_enabled"] is False
    assert payload["audit_writer_enabled"] is False
    assert payload["export_file_creation_enabled"] is False
    assert payload["scheduler_execution_enabled"] is False
    assert payload["application_execution_enabled"] is False
    assert payload["application_submission_enabled"] is False
    assert payload["did_trigger_execution"] is False
    assert payload["did_trigger_submission"] is False
    assert payload["did_trigger_production_scheduler_wiring"] is False
    assert payload["did_trigger_scheduler_work"] is False
    assert payload["did_trigger_migration"] is False
    assert payload["did_write_metrics"] is False
    assert payload["did_write_logs"] is False
    assert payload["did_write_audit_events"] is False


def test_reporting_job_endpoint_exists_and_is_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[REPORTING_JOB_ENDPOINT].methods == {"POST"}


def test_existing_observability_surfaces_remain_get_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[REPORT_ENDPOINT].methods == {"GET"}
    assert routes[DASHBOARD_ENDPOINT].methods == {"GET"}
    assert routes[EXPORT_PREVIEW_ENDPOINT].methods == {"GET"}
    assert routes[WRITER_STATUS_ENDPOINT].methods == {"GET"}


def test_reporting_job_blocks_missing_reporting_decision(monkeypatch):
    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: None,
    )

    response = _client(monkeypatch).post(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-reporting-job"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reporting_job_invoked"] is True
    assert payload["reporting_job_status"] == "blocked"
    assert payload["reporting_job_key"] == (
        "production_scheduler_observability_reporting_job:approval_1"
    )
    assert payload["approval_request_id"] == "approval_1"
    assert payload["surface"] == "production_scheduler_observability_reporting_job"
    assert payload["reason_codes"] == [
        "missing_production_scheduler_observability_reporting_decision",
        "production_scheduler_observability_reporting_gate_not_passed",
    ]
    assert payload["blocked_by_production_scheduler_observability_reporting_job_endpoint"] is True
    _assert_reporting_job_no_side_effects(payload)


def test_reporting_job_blocks_unsupported_reporting_decision(monkeypatch):
    blocked_decision = _allowed_reporting_decision()
    blocked_decision["production_scheduler_observability_reporting_allowed"] = False
    blocked_decision["production_scheduler_observability_reporting_status"] = "blocked"

    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: blocked_decision,
    )

    response = _client(monkeypatch).post(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-reporting-job"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["reporting_job_status"] == "blocked"
    assert "production_scheduler_observability_reporting_not_allowed" in payload[
        "reason_codes"
    ]
    assert "production_scheduler_observability_reporting_gate_not_passed" in payload[
        "reason_codes"
    ]
    _assert_reporting_job_no_side_effects(payload)


def test_allowed_reporting_decision_returns_deterministic_reporting_job(monkeypatch):
    allowed_decision = _allowed_reporting_decision()
    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: deepcopy(allowed_decision),
    )
    client = _client(monkeypatch)

    first = client.post(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-reporting-job"
    ).json()
    second = client.post(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-reporting-job"
    ).json()

    assert first == second
    assert first["reporting_job_invoked"] is True
    assert first["reporting_job_status"] == "completed"
    assert first["reporting_job_key"] == (
        "production_scheduler_observability_reporting_job:approval_1"
    )
    assert first["reason_codes"] == []
    assert first["result_summary"] == {
        "approval_request_id": "approval_1",
        "surface": "production_scheduler_observability_reporting_job",
        "status": "completed",
        "reason_codes": [],
        "structured_json_only": True,
        "persistence_disabled": True,
        "background_work_disabled": True,
        "file_export_disabled": True,
        "scheduler_execution_disabled": True,
        "application_execution_disabled": True,
        "application_submission_disabled": True,
    }
    _assert_reporting_job_no_side_effects(first)


def test_api_reporting_job_slice_has_no_file_background_storage_or_emitter_markers():
    source = Path("src/app/api.py").read_text()
    helper_start = source.index(
        "def _agentic_production_scheduler_observability_reporting_job_payload"
    )
    helper_end = source.index("app.include_router(ui_router)")
    route_start = source.index(
        '@app.post(\n    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-reporting-job"'
    )
    route_end = source.index('@app.get("/api/agent-feedback/summary")')
    snippet = source[helper_start:helper_end] + source[route_start:route_end]

    forbidden_tokens = [
        "FileResponse",
        "StreamingResponse",
        "open(",
        ".write(",
        "write_text",
        "write_bytes",
        "send_file",
        "subprocess",
        "background_tasks.add_task",
        "Thread",
        "Process",
        "export_writer",
        "persistent_storage_writer",
        "storage_writer(",
        "metrics_emitter(",
        "logging_emitter(",
        "audit_writer(",
        "scheduler_execution(",
        "application_execution(",
        "application_submission(",
        "migration_runner",
        "run_migration",
        "src.storage.agentic_approvals",
        "schema.sql",
        "application_execution_queue.py",
        "workflow_runner.py",
    ]
    for token in forbidden_tokens:
        assert token not in snippet


def test_ui_references_reporting_job_post_endpoint_only_for_explicit_action():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index(
        "function formatProductionSchedulerObservabilityReportingJobMessage"
    )
    end = source.index(
        "function formatProductionSchedulerObservabilityDashboardExportMessage"
    )
    snippet = source[start:end]

    assert "production-scheduler-observability-reporting-job" in snippet
    assert "fetchJson(" in snippet
    assert 'method: "POST"' in snippet
    assert "production-scheduler-observability-dashboard" not in snippet
    assert "production-scheduler-observability-export-preview" not in snippet
    assert "production-scheduler-observability-writer-status" not in snippet
    assert "persistence disabled" in snippet
    assert "scheduler and background work disabled" in snippet
    assert "file export disabled" in snippet
    assert "metrics/logging/audit writers disabled" in snippet
    assert "execution disabled" in snippet
    assert "submission disabled" in snippet
    assert "production scheduler wiring disabled" in snippet


def test_ui_reporting_job_slice_does_not_trigger_unsafe_actions():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index(
        "function formatProductionSchedulerObservabilityReportingJobMessage"
    )
    end = source.index(
        "function formatProductionSchedulerObservabilityDashboardExportMessage"
    )
    snippet = source[start:end]

    forbidden_tokens = [
        "application-actions",
        "queue mutation",
        "executeLive",
        "run_application_planning",
        "application_submission",
        "submit application",
        "mutation execution",
        "migration execution triggered",
        "export_writer",
        "persistent_storage_writer",
        "metrics_emitter",
        "logging_emitter",
        "audit_writer",
    ]
    for token in forbidden_tokens:
        assert token not in snippet
