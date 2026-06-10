from __future__ import annotations

import importlib
from datetime import datetime, timezone

import pytest


class FakeCursor:
    def __init__(self, rows=None, columns=None, fail_with=None):
        self.rows = rows or []
        self.description = [(column,) for column in (columns or [])]
        self.fail_with = fail_with
        self.closed = False
        self.executed = []

    def execute(self, sql, params):
        if self.fail_with:
            raise self.fail_with
        self.executed.append((sql, params))

    def fetchall(self):
        return self.rows

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, rows=None, columns=None, fail_with=None):
        self.cursor_count = 0
        self.cursor_obj = FakeCursor(rows=rows, columns=columns, fail_with=fail_with)

    def cursor(self):
        self.cursor_count += 1
        return self.cursor_obj


REQUEST_COLUMNS = [
    "approval_request_id",
    "dry_run_artifact_id",
    "owner_id",
    "idempotency_key",
    "approval_status",
]


def test_import_has_no_db_connection_or_sql_execution_side_effects():
    module = importlib.import_module("src.storage.agentic_approvals.store")

    assert module.__name__ == "src.storage.agentic_approvals.store"
    assert hasattr(module, "create_approval_request")


def test_create_approval_request_uses_idempotency_key_conflict_boundary():
    from src.storage.agentic_approvals import store

    connection = FakeConnection(
        rows=[
            (
                "approval_1",
                "dry_run_1",
                "owner_1",
                "idem_1",
                "pending",
            )
        ],
        columns=REQUEST_COLUMNS,
    )

    row = store.create_approval_request(
        connection,
        approval_request_id="approval_1",
        dry_run_artifact_id="dry_run_1",
        owner_id="owner_1",
        idempotency_key="idem_1",
        proposed_action_type="operator_review",
        safety_gate_snapshot={"status": "passed"},
        expires_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )

    sql, params = connection.cursor_obj.executed[0]
    assert "ON CONFLICT (idempotency_key) DO NOTHING" in sql
    assert "WHERE idempotency_key = %s" in sql
    assert params[3] == "idem_1"
    assert params[4] == "pending"
    assert params[-1] == "idem_1"
    assert row["approval_request_id"] == "approval_1"
    assert connection.cursor_obj.closed is True


def test_get_and_list_approval_requests_are_read_only_queries():
    from src.storage.agentic_approvals import store

    connection = FakeConnection(
        rows=[("approval_1", "pending")],
        columns=["approval_request_id", "approval_status"],
    )

    row = store.get_approval_request(connection, approval_request_id="approval_1")

    sql, params = connection.cursor_obj.executed[0]
    assert sql.startswith("SELECT")
    assert "FROM agentic_approval_requests" in sql
    assert "approval_request_id = %s" in sql
    assert params == ("approval_1",)
    assert row == {"approval_request_id": "approval_1", "approval_status": "pending"}

    connection = FakeConnection(rows=[], columns=REQUEST_COLUMNS)
    rows = store.list_approval_requests(
        connection,
        owner_id="owner_1",
        approval_status="pending",
        limit=25,
    )
    sql, params = connection.cursor_obj.executed[0]
    assert sql.startswith("SELECT")
    assert "owner_id = %s" in sql
    assert "approval_status = %s" in sql
    assert "ORDER BY created_at DESC, approval_request_id ASC" in sql
    assert params == ("owner_1", "pending", 25)
    assert rows == []


def test_record_audit_event_preserves_foreign_key_boundary():
    from src.storage.agentic_approvals import store

    connection = FakeConnection(
        rows=[("event_1", "approval_1", "approval_requested")],
        columns=["audit_event_id", "approval_request_id", "event_type"],
    )

    row = store.record_approval_audit_event(
        connection,
        audit_event_id="event_1",
        approval_request_id="approval_1",
        event_type="approval_requested",
        event_actor_id="operator",
        event_payload={"reason_code": "manual_review"},
        created_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )

    sql, params = connection.cursor_obj.executed[0]
    assert "INSERT INTO agentic_approval_audit_events" in sql
    assert "approval_request_id" in sql
    assert params[1] == "approval_1"
    assert row["audit_event_id"] == "event_1"


def test_record_decision_updates_request_and_optionally_appends_audit_event():
    from src.storage.agentic_approvals import store

    connection = FakeConnection(
        rows=[("approval_1", "approved")],
        columns=["approval_request_id", "approval_status"],
    )

    row = store.record_approval_decision(
        connection,
        approval_request_id="approval_1",
        approval_status="approved",
        reviewer_id="reviewer_1",
        review_reason="looks good",
        audit_event_id="event_1",
        event_payload={"approval_status": "approved"},
        decided_at=datetime(2025, 1, 1, tzinfo=timezone.utc),
    )

    update_sql, update_params = connection.cursor_obj.executed[0]
    audit_sql, audit_params = connection.cursor_obj.executed[1]
    assert update_sql.startswith("UPDATE agentic_approval_requests")
    assert "approved_at = %s" in update_sql
    assert update_params[0] == "approved"
    assert "INSERT INTO agentic_approval_audit_events" in audit_sql
    assert audit_params[2] == "approval_approved"
    assert row["approval_status"] == "approved"


def test_expire_approval_requests_marks_pending_rows_without_deleting():
    from src.storage.agentic_approvals import store

    connection = FakeConnection(
        rows=[("approval_1", "expired")],
        columns=["approval_request_id", "approval_status"],
    )

    rows = store.expire_approval_requests(
        connection,
        now=datetime(2025, 1, 1, tzinfo=timezone.utc),
        limit=10,
    )

    sql, params = connection.cursor_obj.executed[0]
    assert sql.startswith("WITH candidates AS")
    assert "UPDATE agentic_approval_requests AS requests" in sql
    assert "DELETE" not in sql
    assert params[0] == "pending"
    assert params[3] == "expired"
    assert rows == [{"approval_request_id": "approval_1", "approval_status": "expired"}]


def test_storage_api_rejects_invalid_status_and_sensitive_payload_keys():
    from src.storage.agentic_approvals import store

    with pytest.raises(ValueError, match="Invalid approval_status"):
        store.list_approval_requests(FakeConnection(), approval_status="waiting")

    with pytest.raises(ValueError, match="sensitive field"):
        store.record_approval_audit_event(
            FakeConnection(),
            audit_event_id="event_1",
            approval_request_id="approval_1",
            event_type="approval_requested",
            event_payload={"raw_credentials": "nope"},
        )


def test_storage_errors_are_wrapped_with_reason_codes():
    from src.storage.agentic_approvals import store

    connection = FakeConnection(fail_with=RuntimeError("duplicate key value"))

    with pytest.raises(store.ApprovalStorageError) as exc_info:
        store.get_approval_request(connection, approval_request_id="approval_1")

    assert exc_info.value.operation_name == "get_approval_request"
    assert exc_info.value.reason_code == "duplicate_idempotency_or_primary_key"
