from datetime import datetime, timezone

from src.agents import workflow_runner
from src.app import services


class FakeStorageModule:
    def __init__(self, fail=False):
        self.fail = fail
        self.created_requests = []
        self.audit_events = []

    def create_approval_request(self, connection, **kwargs):
        if self.fail:
            raise RuntimeError("connection unavailable")
        self.created_requests.append((connection, kwargs))
        return {
            "approval_request_id": kwargs["approval_request_id"],
            "approval_status": "pending",
            "idempotency_key": kwargs["idempotency_key"],
        }

    def record_approval_audit_event(self, connection, **kwargs):
        self.audit_events.append((connection, kwargs))
        return {
            "audit_event_id": kwargs["audit_event_id"],
            "approval_request_id": kwargs["approval_request_id"],
            "event_type": kwargs["event_type"],
        }


def _healthy_app_service_gate():
    return services.app_service_agentic_workflow_safety_gate_payload(
        workflow_runner.run_agentic_workflow_dry_run()
    )


def _approval_kwargs(app_gate, storage_module, **overrides):
    kwargs = {
        "app_service_safety_gate_output": app_gate,
        "approval_request_id": "approval_1",
        "dry_run_artifact_id": "dry_run_1",
        "owner_id": "owner_1",
        "idempotency_key": "idem_1",
        "expires_at": datetime(2026, 1, 1, tzinfo=timezone.utc),
        "proposed_action_type": "operator_review",
        "proposed_action_summary": "Persist review approval request",
        "audit_event_id": "audit_1",
        "event_actor_id": "app_service",
        "created_at": datetime(2025, 1, 1, tzinfo=timezone.utc),
        "storage_module": storage_module,
    }
    kwargs.update(overrides)
    return kwargs


def test_app_service_approval_storage_call_site_persists_with_fake_storage_only():
    app_gate = _healthy_app_service_gate()
    fake_storage = FakeStorageModule()
    connection = object()

    result = services.app_service_persist_agentic_approval_request(
        connection,
        **_approval_kwargs(app_gate, fake_storage),
    )

    assert result["approval_storage_call_site"] == "src/app/services.py"
    assert result["approval_storage_status"] == "passed"
    assert result["approval_storage_reason_codes"] == []
    assert result["did_create_approval_request"] is True
    assert result["did_record_approval_audit_event"] is True
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False
    assert result["allow_agent_execution"] is False
    assert result["execution_enabled"] is False

    assert len(fake_storage.created_requests) == 1
    create_connection, create_kwargs = fake_storage.created_requests[0]
    assert create_connection is connection
    assert create_kwargs["approval_request_id"] == "approval_1"
    assert create_kwargs["dry_run_artifact_id"] == "dry_run_1"
    assert create_kwargs["owner_id"] == "owner_1"
    assert create_kwargs["idempotency_key"] == "idem_1"
    assert create_kwargs["app_service_safety_gate_snapshot"]["app_service_safety_gate_passed"] is True
    assert create_kwargs["queue_safety_gate_snapshot"] == {}

    assert len(fake_storage.audit_events) == 1
    _, audit_kwargs = fake_storage.audit_events[0]
    assert audit_kwargs["approval_request_id"] == "approval_1"
    assert audit_kwargs["event_type"] == "approval_request_persisted"
    assert audit_kwargs["event_payload"]["storage_call_site"] == "src/app/services.py"


def test_app_service_approval_storage_call_site_blocks_failed_app_service_gate():
    app_gate = _healthy_app_service_gate()
    app_gate["app_service_safety_gate_passed"] = False
    app_gate["app_service_safety_gate_status"] = "failed"
    app_gate["blocked_by_app_service_safety_gate"] = True
    fake_storage = FakeStorageModule()

    result = services.app_service_persist_agentic_approval_request(
        object(),
        **_approval_kwargs(app_gate, fake_storage),
    )

    assert result["approval_storage_status"] == "blocked"
    assert "app_service_safety_gate_blocked" in result["approval_storage_reason_codes"]
    assert result["did_create_approval_request"] is False
    assert result["did_record_approval_audit_event"] is False
    assert fake_storage.created_requests == []
    assert fake_storage.audit_events == []
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False


def test_app_service_approval_storage_call_site_preserves_queue_safety_gate():
    app_gate = _healthy_app_service_gate()
    queue_gate = {
        "queue_safety_gate_passed": False,
        "queue_safety_gate_status": "failed",
        "blocked_by_queue_safety_gate": True,
    }
    fake_storage = FakeStorageModule()

    result = services.app_service_persist_agentic_approval_request(
        object(),
        **_approval_kwargs(
            app_gate,
            fake_storage,
            queue_safety_gate_output=queue_gate,
        ),
    )

    assert result["approval_storage_status"] == "blocked"
    assert "queue_safety_gate_blocked" in result["approval_storage_reason_codes"]
    assert fake_storage.created_requests == []
    assert fake_storage.audit_events == []
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False


def test_app_service_approval_storage_call_site_storage_failure_is_non_executing():
    app_gate = _healthy_app_service_gate()
    fake_storage = FakeStorageModule(fail=True)

    result = services.app_service_persist_agentic_approval_request(
        object(),
        **_approval_kwargs(app_gate, fake_storage),
    )

    assert result["approval_storage_status"] == "failed"
    assert result["approval_storage_reason_codes"] == ["approval_storage_unavailable"]
    assert result["did_create_approval_request"] is False
    assert result["did_record_approval_audit_event"] is False
    assert result["did_execute_count"] == 0
    assert result["did_execute_live"] is False
    assert result["did_mutate_production"] is False
    assert result["did_write_db"] is False
