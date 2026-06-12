from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

import application_execution_queue as queue
from src.app import api, services


WRITER_STATUS_ENDPOINT = (
    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-writer-status"
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


def _assert_writer_status_no_side_effects(payload):
    assert payload["did_write_metrics"] is False
    assert payload["did_write_logs"] is False
    assert payload["did_write_audit_events"] is False
    assert payload["did_schedule_background_work"] is False
    assert payload["did_create_reporting_job"] is False
    assert payload["did_export_files"] is False
    assert payload["migration_required"] is False
    assert payload["persistence_enabled"] is False
    assert payload["metrics_writer_enabled"] is False
    assert payload["logging_writer_enabled"] is False
    assert payload["audit_writer_enabled"] is False
    assert payload["execution_enabled"] is False
    assert payload["submission_enabled"] is False
    assert payload["production_scheduler_wiring_enabled"] is False
    assert payload["scheduler_background_execution_enabled"] is False
    assert payload["live_scheduler_loop_enabled"] is False
    assert payload["migration_execution_enabled"] is False
    assert payload["did_trigger_execution"] is False
    assert payload["did_trigger_submission"] is False
    assert payload["did_trigger_production_scheduler_wiring"] is False
    assert payload["did_trigger_scheduler_work"] is False
    assert payload["did_trigger_migration"] is False


def test_writer_status_endpoint_exists_and_is_get_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[WRITER_STATUS_ENDPOINT].methods == {"GET"}


def test_writer_status_blocks_missing_reporting_decision(monkeypatch):
    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: None,
    )

    response = _client(monkeypatch).get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-writer-status"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["production_scheduler_observability_writer_status_eligible"] is False
    assert payload["production_scheduler_observability_writer_status"] == "blocked"
    assert payload["blocked_by_production_scheduler_observability_writer_status_endpoint"] is True
    assert payload["production_scheduler_observability_writer_status_reason_codes"] == [
        "missing_production_scheduler_observability_reporting_decision",
        "production_scheduler_observability_reporting_gate_not_passed",
    ]
    _assert_writer_status_no_side_effects(payload)


def test_writer_status_blocks_unsupported_reporting_decision(monkeypatch):
    blocked_decision = deepcopy(_allowed_reporting_decision())
    blocked_decision["production_scheduler_observability_reporting_allowed"] = False
    blocked_decision["production_scheduler_observability_reporting_status"] = "blocked"

    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: blocked_decision,
    )

    response = _client(monkeypatch).get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-writer-status"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["production_scheduler_observability_writer_status_eligible"] is False
    assert "production_scheduler_observability_reporting_not_allowed" in payload[
        "production_scheduler_observability_writer_status_reason_codes"
    ]
    assert "production_scheduler_observability_reporting_gate_not_passed" in payload[
        "production_scheduler_observability_writer_status_reason_codes"
    ]
    _assert_writer_status_no_side_effects(payload)


def test_allowed_reporting_decision_returns_deterministic_writer_status(monkeypatch):
    allowed_decision = _allowed_reporting_decision()
    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: deepcopy(allowed_decision),
    )
    client = _client(monkeypatch)

    first = client.get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-writer-status"
    ).json()
    second = client.get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-writer-status"
    ).json()

    assert first == second
    assert first["production_scheduler_observability_writer_status_eligible"] is True
    assert first["production_scheduler_observability_writer_status"] == "passed"
    assert first["production_scheduler_observability_writer_status_reason_codes"] == []
    assert first["production_scheduler_observability_writer_status_summary"] == {
        "eligible": True,
        "status": "passed",
        "reason_codes": [],
        "read_only": True,
        "metrics_writer_disabled": True,
        "logging_writer_disabled": True,
        "audit_writer_disabled": True,
        "persistence_disabled": True,
        "migration_required": False,
        "background_work_disabled": True,
        "reporting_job_disabled": True,
        "file_export_disabled": True,
    }
    _assert_writer_status_no_side_effects(first)


def test_api_writer_status_slice_has_no_file_background_or_emitter_markers():
    source = Path("src/app/api.py").read_text()
    helper_start = source.index(
        "def _agentic_production_scheduler_observability_writer_status_payload"
    )
    helper_end = source.index("app.include_router(ui_router)")
    route_start = source.index(
        '@app.get(\n    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-writer-status"'
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
        "metrics_emitter(",
        "logging_emitter(",
        "audit_writer(",
        "reporting_job(",
        "migration_runner",
        "run_migration",
        "src.storage.agentic_approvals",
        "schema.sql",
        "application_execution_queue.py",
        "workflow_runner.py",
    ]
    for token in forbidden_tokens:
        assert token not in snippet


def test_ui_references_writer_status_get_endpoint_only():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index(
        "function formatProductionSchedulerObservabilityWriterStatusMessage"
    )
    end = source.index("function renderAgenticReviewData")
    snippet = source[start:end]

    assert "production-scheduler-observability-writer-status" in snippet
    assert "fetchJson(" in snippet
    assert "method:" not in snippet
    assert "POST" not in snippet
    assert "PUT" not in snippet
    assert "PATCH" not in snippet
    assert "DELETE" not in snippet
    assert "metrics/logging/audit writers disabled" in snippet
    assert "persistence disabled" in snippet
    assert "migration disabled" in snippet
    assert "export file creation disabled" in snippet
    assert "reporting jobs disabled" in snippet
    assert "execution disabled" in snippet
    assert "submission disabled" in snippet
    assert "production scheduler wiring disabled" in snippet


def test_ui_writer_status_slice_does_not_trigger_unsafe_actions():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index(
        "function formatProductionSchedulerObservabilityWriterStatusMessage"
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
        "reporting_job",
        "export_writer",
        "metrics_emitter",
        "logging_emitter",
        "audit_writer",
    ]
    for token in forbidden_tokens:
        assert token not in snippet
