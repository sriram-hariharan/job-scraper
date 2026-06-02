import types

from fastapi import HTTPException
import pytest

from src.app import api, services


def _request(owner_user_id="user_1"):
    return types.SimpleNamespace(
        state=types.SimpleNamespace(auth_user={"user_id": owner_user_id} if owner_user_id else {})
    )


def test_agent_feedback_api_uses_authenticated_owner_and_ignores_client_owner(monkeypatch):
    captured = {}

    def fake_record_agent_feedback_payload(**kwargs):
        captured.update(kwargs)
        return {
            "ok": True,
            "recorded": True,
            "event": {
                "event_id": "feedback_1",
                "owner_user_id": kwargs["owner_user_id"],
            },
        }

    monkeypatch.setattr(services, "record_agent_feedback_payload", fake_record_agent_feedback_payload)

    request_data = {
        "owner_user_id": "attacker",
        "event_type": "job_saved",
        "target_type": "pipeline_run_job",
        "target_id": "job_1",
        "payload_json": {"owner_user_id": "payload_value", "note": "save clicked"},
        "source": "ui",
    }
    request = (
        api.AgentFeedbackRequest.model_validate(request_data)
        if hasattr(api.AgentFeedbackRequest, "model_validate")
        else api.AgentFeedbackRequest(**request_data)
    )
    payload = api.record_agent_feedback(request, _request("user_1"))

    assert payload["recorded"] is True
    assert captured["owner_user_id"] == "user_1"
    assert captured["payload_json"]["owner_user_id"] == "payload_value"
    fields_set = request.model_fields_set if hasattr(request, "model_fields_set") else request.__fields_set__
    assert "owner_user_id" not in fields_set


def test_agent_feedback_api_requires_auth():
    request = api.AgentFeedbackRequest(
        event_type="job_saved",
        target_type="pipeline_run_job",
        target_id="job_1",
    )

    with pytest.raises(HTTPException) as exc:
        api.record_agent_feedback(request, _request(""))

    assert exc.value.status_code == 401


def test_agent_feedback_api_returns_validation_error(monkeypatch):
    def fake_record_agent_feedback_payload(**kwargs):
        raise ValueError("Unsupported agent feedback event_type: nope.")

    monkeypatch.setattr(services, "record_agent_feedback_payload", fake_record_agent_feedback_payload)

    request = api.AgentFeedbackRequest(
        event_type="nope",
        target_type="pipeline_run_job",
        target_id="job_1",
    )

    with pytest.raises(HTTPException) as exc:
        api.record_agent_feedback(request, _request("user_1"))

    assert exc.value.status_code == 400
    assert "Unsupported agent feedback event_type" in exc.value.detail
