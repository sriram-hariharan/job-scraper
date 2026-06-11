from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

import application_execution_queue as queue
from src.app import api, services


DASHBOARD_ENDPOINT = (
    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-dashboard"
)
EXPORT_PREVIEW_ENDPOINT = (
    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-export-preview"
)


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _provider(status):
    def load_approval_record(approval_request_id):
        return {
            "approval_request_id": approval_request_id,
            "approval_status": status,
            "idempotency_key": "idem_1",
        }

    return load_approval_record


def _allowed_reporting_decision():
    queue_gate = queue.queue_safety_gate_payload(
        services.app_service_agentic_workflow_safety_gate_payload()
    )
    execution_gate = queue.approval_gated_execution_payload(
        approval_request_id="approval_1",
        queue_safety_gate_output=queue_gate,
        approval_record_provider=_provider("approved"),
    )
    submission_gate = queue.application_submission_decision_payload(
        approval_request_id="approval_1",
        approval_gated_execution_output=execution_gate,
        approval_record_provider=_provider("approved"),
    )
    scheduler_gate = queue.scheduler_background_execution_decision_payload(
        approval_request_id="approval_1",
        application_submission_output=submission_gate,
        approval_record_provider=_provider("approved"),
    )
    live_scheduler_gate = queue.live_scheduler_execution_decision_payload(
        approval_request_id="approval_1",
        scheduler_background_execution_output=scheduler_gate,
        approval_record_provider=_provider("approved"),
    )
    wiring_gate = queue.production_scheduler_wiring_decision_payload(
        approval_request_id="approval_1",
        live_scheduler_execution_output=live_scheduler_gate,
        approval_record_provider=_provider("approved"),
    )
    observability_gate = queue.production_scheduler_observability_decision_payload(
        approval_request_id="approval_1",
        production_scheduler_wiring_output=wiring_gate,
        approval_record_provider=_provider("approved"),
    )
    return queue.production_scheduler_observability_reporting_payload(
        observability_gate
    )


def _assert_dashboard_export_no_side_effects(payload):
    assert payload["did_trigger_execution"] is False
    assert payload["did_trigger_submission"] is False
    assert payload["did_trigger_production_scheduler_wiring"] is False
    assert payload["did_trigger_scheduler_work"] is False
    assert payload["did_trigger_migration"] is False
    assert payload["did_write_audit_events"] is False
    assert payload["did_write_metrics"] is False
    assert payload["did_emit_logs"] is False
    assert payload["did_start_background_work"] is False
    assert payload["did_create_reporting_job"] is False
    assert payload["did_export_files"] is False
    assert payload["export_file_creation_enabled"] is False
    assert payload["execution_enabled"] is False
    assert payload["submission_enabled"] is False
    assert payload["production_scheduler_wiring_enabled"] is False
    assert payload["scheduler_background_execution_enabled"] is False
    assert payload["live_scheduler_loop_enabled"] is False
    assert payload["migration_execution_enabled"] is False
    assert payload["metrics_emitter_enabled"] is False
    assert payload["logging_emitter_enabled"] is False
    assert payload["audit_writer_enabled"] is False
    assert payload["export_code_enabled"] is False
    assert payload["reporting_job_enabled"] is False


def test_dashboard_and_export_preview_endpoints_exist_and_are_get_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[DASHBOARD_ENDPOINT].methods == {"GET"}
    assert routes[EXPORT_PREVIEW_ENDPOINT].methods == {"GET"}


def test_dashboard_blocks_missing_gate_decision(monkeypatch):
    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: None,
    )

    response = _client(monkeypatch).get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-dashboard"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["production_scheduler_observability_dashboard_allowed"] is False
    assert payload["production_scheduler_observability_dashboard_status"] == "blocked"
    assert payload["blocked_by_production_scheduler_observability_dashboard_endpoint"] is True
    assert payload["production_scheduler_observability_dashboard_reason_codes"] == [
        "missing_production_scheduler_observability_reporting_decision",
        "production_scheduler_observability_reporting_gate_not_passed",
    ]
    _assert_dashboard_export_no_side_effects(payload)


def test_export_preview_blocks_missing_gate_decision(monkeypatch):
    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: None,
    )

    response = _client(monkeypatch).get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-export-preview"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["production_scheduler_observability_export_preview_allowed"] is False
    assert payload["production_scheduler_observability_export_preview_status"] == "blocked"
    assert payload["blocked_by_production_scheduler_observability_export_preview_endpoint"] is True
    assert payload["production_scheduler_observability_export_preview_reason_codes"] == [
        "missing_production_scheduler_observability_reporting_decision",
        "production_scheduler_observability_reporting_gate_not_passed",
    ]
    assert payload["export_file_creation_disabled"] is True
    _assert_dashboard_export_no_side_effects(payload)


def test_dashboard_blocks_unsupported_gate_decision(monkeypatch):
    blocked_decision = deepcopy(_allowed_reporting_decision())
    blocked_decision["production_scheduler_observability_reporting_allowed"] = False
    blocked_decision["production_scheduler_observability_reporting_status"] = "blocked"

    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: blocked_decision,
    )

    response = _client(monkeypatch).get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-dashboard"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["production_scheduler_observability_dashboard_allowed"] is False
    assert "production_scheduler_observability_reporting_not_allowed" in payload[
        "production_scheduler_observability_dashboard_reason_codes"
    ]
    assert "production_scheduler_observability_reporting_gate_not_passed" in payload[
        "production_scheduler_observability_dashboard_reason_codes"
    ]
    _assert_dashboard_export_no_side_effects(payload)


def test_export_preview_blocks_unsupported_gate_decision(monkeypatch):
    blocked_decision = deepcopy(_allowed_reporting_decision())
    blocked_decision["production_scheduler_observability_reporting_allowed"] = False
    blocked_decision["production_scheduler_observability_reporting_status"] = "blocked"

    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: blocked_decision,
    )

    response = _client(monkeypatch).get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-export-preview"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["production_scheduler_observability_export_preview_allowed"] is False
    assert "production_scheduler_observability_reporting_not_allowed" in payload[
        "production_scheduler_observability_export_preview_reason_codes"
    ]
    assert "production_scheduler_observability_reporting_gate_not_passed" in payload[
        "production_scheduler_observability_export_preview_reason_codes"
    ]
    assert payload["export_file_creation_disabled"] is True
    _assert_dashboard_export_no_side_effects(payload)


def test_allowed_reporting_decision_returns_deterministic_dashboard_summary(monkeypatch):
    allowed_decision = _allowed_reporting_decision()
    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: deepcopy(allowed_decision),
    )
    client = _client(monkeypatch)

    first = client.get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-dashboard"
    ).json()
    second = client.get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-dashboard"
    ).json()

    assert first == second
    assert first["production_scheduler_observability_dashboard_allowed"] is True
    assert first["production_scheduler_observability_dashboard_status"] == "passed"
    assert first["production_scheduler_observability_dashboard_summary"] == {
        "allowed": True,
        "status": "passed",
        "reason_codes": [],
        "read_only": True,
        "execution_disabled": True,
        "submission_disabled": True,
        "production_scheduler_wiring_disabled": True,
        "scheduler_work_disabled": True,
        "migration_disabled": True,
        "audit_metrics_logging_disabled": True,
        "reporting_job_disabled": True,
        "file_export_disabled": True,
    }
    _assert_dashboard_export_no_side_effects(first)


def test_allowed_reporting_decision_returns_deterministic_export_preview(monkeypatch):
    allowed_decision = _allowed_reporting_decision()
    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: deepcopy(allowed_decision),
    )
    client = _client(monkeypatch)

    first = client.get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-export-preview"
    ).json()
    second = client.get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-export-preview"
    ).json()

    assert first == second
    assert first["production_scheduler_observability_export_preview_allowed"] is True
    assert first["production_scheduler_observability_export_preview_status"] == "passed"
    assert first["production_scheduler_observability_export_preview_manifest"] == {
        "allowed": True,
        "status": "passed",
        "reason_codes": [],
        "read_only": True,
        "format": "json_preview_only",
        "file_creation_enabled": False,
        "export_file_creation_disabled": True,
        "reporting_job_disabled": True,
        "migration_disabled": True,
    }
    assert first["export_file_creation_disabled"] is True
    _assert_dashboard_export_no_side_effects(first)


def test_api_does_not_return_file_or_stream_responses_or_write_files():
    source = Path("src/app/api.py").read_text()
    dashboard_start = source.index(
        "def _agentic_production_scheduler_observability_dashboard_and_export_base_payload"
    )
    dashboard_end = source.index('@app.get("/api/agent-feedback/summary")')
    snippet = source[dashboard_start:dashboard_end]

    forbidden_tokens = [
        "FileResponse",
        "StreamingResponse",
        "open(",
        ".write(",
        "write_text",
        "write_bytes",
        "export_writer",
        "metrics_emitter(",
        "logging_emitter(",
        "audit_writer(",
        "reporting_job(",
        "asyncio.create_task",
        "BackgroundTasks",
        "subprocess",
        "os.system",
        "migration_runner",
        "run_migration",
    ]
    for token in forbidden_tokens:
        assert token not in snippet


def test_ui_references_dashboard_and_export_preview_get_endpoints_only():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index(
        "function formatProductionSchedulerObservabilityDashboardExportMessage"
    )
    end = source.index("function renderAgenticReviewData")
    snippet = source[start:end]

    assert "production-scheduler-observability-dashboard" in snippet
    assert "production-scheduler-observability-export-preview" in snippet
    assert "fetchJson(" in snippet
    assert "method:" not in snippet
    assert "POST" not in snippet
    assert "PUT" not in snippet
    assert "PATCH" not in snippet
    assert "DELETE" not in snippet
    assert "execution disabled" in snippet
    assert "submission disabled" in snippet
    assert "production scheduler wiring disabled" in snippet
    assert "scheduler, background, and live scheduler work disabled" in snippet
    assert "migration disabled" in snippet
    assert "metrics/logging/audit writers disabled" in snippet
    assert "export file creation disabled" in snippet
    assert "reporting jobs disabled" in snippet


def test_ui_does_not_trigger_dashboard_export_unsafe_actions():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index(
        "function formatProductionSchedulerObservabilityDashboardExportMessage"
    )
    end = source.index("function renderAgenticReviewData")
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
        "dashboard_export",
        "reporting_job",
        "export_writer",
    ]
    for token in forbidden_tokens:
        assert token not in snippet
