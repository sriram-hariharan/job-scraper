from fastapi.testclient import TestClient

from src.app import api
from src.storage.agentic_approvals import store


class FakeConnection:
    pass


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def test_approval_decision_endpoint_records_valid_decision_with_fake_storage(monkeypatch):
    connection = FakeConnection()
    calls = []

    def fake_connection_provider():
        return connection

    def fake_record_approval_decision(passed_connection, **kwargs):
        calls.append((passed_connection, kwargs))
        return {
            "approval_request_id": kwargs["approval_request_id"],
            "approval_status": kwargs["approval_status"],
            "reviewer_id": kwargs["reviewer_id"],
        }

    monkeypatch.setattr(api, "_agentic_approval_storage_connection", fake_connection_provider)
    monkeypatch.setattr(store, "record_approval_decision", fake_record_approval_decision)

    response = _client(monkeypatch).post(
        "/api/agentic-approvals/approval_1/decision",
        json={
            "reviewer_id": "reviewer_1",
            "review_decision": "approved",
            "review_reason": "looks good",
            "decided_at": "2026-01-01T00:00:00+00:00",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["approval_api_endpoint_status"] == "passed"
    assert payload["blocked_by_approval_api_endpoint"] is False
    assert payload["approval_api_endpoint_reason_codes"] == []
    assert payload["approval_request"]["approval_status"] == "approved"
    assert payload["queue_mutation_enabled"] is False
    assert payload["did_mutate_queue"] is False
    assert payload["execution_enabled"] is False
    assert payload["did_execute_count"] == 0
    assert payload["did_execute_live"] is False
    assert payload["did_mutate_production"] is False
    assert payload["did_submit_application"] is False
    assert payload["scheduler_background_execution_enabled"] is False

    assert len(calls) == 1
    passed_connection, kwargs = calls[0]
    assert passed_connection is connection
    assert kwargs == {
        "approval_request_id": "approval_1",
        "approval_status": "approved",
        "reviewer_id": "reviewer_1",
        "review_reason": "looks good",
        "decided_at": "2026-01-01T00:00:00+00:00",
    }


def test_approval_decision_endpoint_rejects_unsupported_decision(monkeypatch):
    calls = []
    monkeypatch.setattr(api, "_agentic_approval_storage_connection", lambda: FakeConnection())
    monkeypatch.setattr(
        store,
        "record_approval_decision",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    response = _client(monkeypatch).post(
        "/api/agentic-approvals/approval_1/decision",
        json={"reviewer_id": "reviewer_1", "review_decision": "rejected"},
    )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["reason_code"] == "unsupported_review_decision"
    assert detail["allowed_review_decisions"] == ["approved", "denied", "revoked"]
    assert calls == []


def test_approval_decision_endpoint_blocks_when_storage_provider_unavailable(monkeypatch):
    calls = []
    monkeypatch.setattr(api, "_agentic_approval_storage_connection", lambda: None)
    monkeypatch.setattr(
        store,
        "record_approval_decision",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    response = _client(monkeypatch).post(
        "/api/agentic-approvals/approval_1/decision",
        json={"reviewer_id": "reviewer_1", "review_decision": "denied"},
    )

    assert response.status_code == 503
    detail = response.json()["detail"]
    assert detail["approval_api_endpoint_status"] == "blocked"
    assert detail["blocked_by_approval_api_endpoint"] is True
    assert detail["approval_api_endpoint_reason_codes"] == [
        "approval_storage_connection_unavailable"
    ]
    assert detail["queue_mutation_enabled"] is False
    assert detail["did_mutate_queue"] is False
    assert detail["execution_enabled"] is False
    assert detail["did_execute_count"] == 0
    assert detail["did_execute_live"] is False
    assert detail["did_mutate_production"] is False
    assert detail["did_submit_application"] is False
    assert detail["scheduler_background_execution_enabled"] is False
    assert calls == []
