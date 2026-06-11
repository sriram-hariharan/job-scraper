from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

import application_execution_queue as queue
from src.app import api, services


REPORT_ENDPOINT = (
    "/api/agentic-approvals/{approval_request_id}/production-scheduler-observability-report"
)
UI_REPORT_ENDPOINT = (
    "/api/agentic-approvals/${encodeURIComponent(approvalRequestId)}"
    "/production-scheduler-observability-report"
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


def _healthy_queue_gate():
    return queue.queue_safety_gate_payload(
        services.app_service_agentic_workflow_safety_gate_payload()
    )


def _allowed_reporting_decision():
    execution_gate = queue.approval_gated_execution_payload(
        approval_request_id="approval_1",
        queue_safety_gate_output=_healthy_queue_gate(),
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


def _assert_api_no_side_effects(payload):
    assert payload["production_scheduler_observability_reporting_endpoint_method"] == "GET"
    assert payload["production_scheduler_observability_reporting_endpoint_read_only"] is True
    assert payload["execution_enabled"] is False
    assert payload["submission_enabled"] is False
    assert payload["production_scheduler_wiring_enabled"] is False
    assert payload["scheduler_background_execution_enabled"] is False
    assert payload["live_scheduler_loop_enabled"] is False
    assert payload["migration_execution_enabled"] is False
    assert payload["metrics_emitter_enabled"] is False
    assert payload["logging_emitter_enabled"] is False
    assert payload["audit_writer_enabled"] is False
    assert payload["dashboard_code_enabled"] is False
    assert payload["export_code_enabled"] is False
    assert payload["reporting_job_enabled"] is False
    assert payload["did_execute_count"] == 0
    assert payload["did_execute_live"] is False
    assert payload["did_submit_application"] is False
    assert payload["did_mutate_production"] is False
    assert payload["did_write_db"] is False
    assert payload["did_emit_metrics"] is False
    assert payload["did_emit_logs"] is False
    assert payload["did_write_audit_events"] is False
    assert payload["did_start_background_work"] is False
    assert payload["did_export_files"] is False
    assert payload["did_create_dashboard_jobs"] is False
    assert payload["did_create_reporting_jobs"] is False


def test_reporting_endpoint_exists_and_is_get_read_only_only():
    matching_routes = [
        route
        for route in api.app.routes
        if getattr(route, "path", "") == REPORT_ENDPOINT
    ]

    assert len(matching_routes) == 1
    assert matching_routes[0].methods == {"GET"}


def test_reporting_endpoint_blocks_missing_reporting_decision(monkeypatch):
    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: None,
    )

    response = _client(monkeypatch).get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-report"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["production_scheduler_observability_reporting_allowed"] is False
    assert payload["production_scheduler_observability_reporting_status"] == "blocked"
    assert payload["blocked_by_production_scheduler_observability_reporting_endpoint"] is True
    assert payload["production_scheduler_observability_reporting_reason_codes"] == [
        "missing_production_scheduler_observability_reporting_decision"
    ]
    _assert_api_no_side_effects(payload)


def test_reporting_endpoint_blocks_unsupported_reporting_decision(monkeypatch):
    blocked_decision = deepcopy(_allowed_reporting_decision())
    blocked_decision["production_scheduler_observability_reporting_allowed"] = False
    blocked_decision["production_scheduler_observability_reporting_status"] = "blocked"
    blocked_decision["production_scheduler_observability_reporting_read_only"] = False

    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: blocked_decision,
    )

    response = _client(monkeypatch).get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-report"
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["production_scheduler_observability_reporting_allowed"] is False
    assert payload["production_scheduler_observability_reporting_status"] == "blocked"
    assert payload["production_scheduler_observability_reporting_reason_codes"] == [
        "production_scheduler_observability_reporting_not_allowed",
        "production_scheduler_observability_reporting_not_read_only",
        "production_scheduler_observability_reporting_status_not_passed",
    ]
    _assert_api_no_side_effects(payload)


def test_reporting_endpoint_returns_allowed_read_only_summary(monkeypatch):
    allowed_decision = _allowed_reporting_decision()
    calls = []

    def fake_reporting_decision(approval_request_id):
        calls.append(approval_request_id)
        return allowed_decision

    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        fake_reporting_decision,
    )

    response = _client(monkeypatch).get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-report"
    )

    assert response.status_code == 200
    payload = response.json()
    assert calls == ["approval_1"]
    assert payload["production_scheduler_observability_reporting_allowed"] is True
    assert payload["production_scheduler_observability_reporting_status"] == "passed"
    assert payload["production_scheduler_observability_reporting_reason_codes"] == []
    assert payload["production_scheduler_observability_reporting_summary"] == {
        "allowed": True,
        "status": "passed",
        "reason_codes": [],
        "read_only": True,
        "approval_request_id": "approval_1",
        "approval_status": "approved",
        "production_scheduler_observability_status": "passed",
    }
    _assert_api_no_side_effects(payload)


def test_reporting_endpoint_response_is_deterministic(monkeypatch):
    allowed_decision = _allowed_reporting_decision()
    monkeypatch.setattr(
        api,
        "_production_scheduler_observability_reporting_decision_for_approval",
        lambda approval_request_id: deepcopy(allowed_decision),
    )
    client = _client(monkeypatch)

    first = client.get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-report"
    ).json()
    second = client.get(
        "/api/agentic-approvals/approval_1/production-scheduler-observability-report"
    ).json()

    assert first == second


def test_reporting_ui_action_references_read_only_get_endpoint_only():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function setProductionSchedulerObservabilityReportStatus")
    end = source.index("function renderAgenticReviewData")
    snippet = source[start:end]

    assert UI_REPORT_ENDPOINT in snippet
    assert "fetchJson(" in snippet
    assert "method:" not in snippet
    assert "POST" not in snippet
    assert "PUT" not in snippet
    assert "PATCH" not in snippet
    assert "DELETE" not in snippet
    assert "data-agentic-production-scheduler-observability-report" in source
    assert "execution disabled" in snippet
    assert "submission disabled" in snippet
    assert "production scheduler wiring disabled" in snippet
    assert "migration disabled" in snippet
    assert "emitters/export/dashboard/reporting jobs disabled" in snippet


def test_reporting_ui_action_keeps_unsafe_paths_out():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function setProductionSchedulerObservabilityReportStatus")
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
    ]
    for token in forbidden_tokens:
        assert token not in snippet


def test_reporting_api_and_ui_do_not_add_emitters_exports_jobs_or_migration_constructs():
    source = (
        Path("src/app/api.py").read_text()
        + "\n"
        + Path("src/app/static/agentic_review.js").read_text()
    )
    forbidden_tokens = [
        "asyncio.create_task",
        "BackgroundTasks",
        "subprocess.run",
        "subprocess.Popen",
        "subprocess.",
        "Popen(",
        "os.system",
        "migration_runner",
        "run_migration",
        "metrics_emitter(",
        "logging_emitter(",
        "audit_writer(",
        "dashboard_export",
        "reporting_job(",
        "export_writer(",
    ]
    for token in forbidden_tokens:
        assert token not in source
