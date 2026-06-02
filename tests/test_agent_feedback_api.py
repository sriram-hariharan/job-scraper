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


def test_agentic_review_feedback_api_event_types_are_recordable(monkeypatch):
    captured = []

    def fake_record_agent_feedback_payload(**kwargs):
        captured.append(dict(kwargs))
        return {"ok": True, "recorded": True, "event": {"event_type": kwargs["event_type"]}}

    monkeypatch.setattr(services, "record_agent_feedback_payload", fake_record_agent_feedback_payload)

    for event_type in ("agentic_review_helpful", "agentic_review_not_helpful"):
        request = api.AgentFeedbackRequest(
            pipeline_run_id="run_1",
            target_type="agentic_review_section",
            target_id="run_1",
            event_type=event_type,
            payload_json={"section": "human_feedback"},
            source="agentic_review_ui",
        )
        payload = api.record_agent_feedback(request, _request("user_1"))
        assert payload["recorded"] is True

    assert [row["event_type"] for row in captured] == [
        "agentic_review_helpful",
        "agentic_review_not_helpful",
    ]
    assert all(row["owner_user_id"] == "user_1" for row in captured)


def test_agent_feedback_summary_api_uses_authenticated_owner_and_filters(monkeypatch):
    captured = {}

    def fake_agent_feedback_summary_payload(**kwargs):
        captured.update(kwargs)
        return {
            "ok": True,
            "owner_user_id": kwargs["owner_user_id"],
            "summary": {
                "total_events": 0,
                "event_type_counts": {},
                "target_type_counts": {},
                "latest_event_at": "",
            },
            "events": [],
        }

    monkeypatch.setattr(services, "agent_feedback_summary_payload", fake_agent_feedback_summary_payload)

    payload = api.agent_feedback_summary(
        _request("user_1"),
        pipeline_run_id="run_1",
        context_id="ctx_1",
        target_type="pipeline_run_job",
        event_type="job_saved",
        limit=25,
    )

    assert payload["owner_user_id"] == "user_1"
    assert captured == {
        "owner_user_id": "user_1",
        "pipeline_run_id": "run_1",
        "context_id": "ctx_1",
        "target_type": "pipeline_run_job",
        "event_type": "job_saved",
        "limit": 25,
    }


def test_agent_feedback_list_api_uses_authenticated_owner_and_filters(monkeypatch):
    captured = {}

    def fake_list_agent_feedback_payload(**kwargs):
        captured.update(kwargs)
        return {
            "ok": True,
            "owner_user_id": kwargs["owner_user_id"],
            "events": [],
            "count": 0,
        }

    monkeypatch.setattr(services, "list_agent_feedback_payload", fake_list_agent_feedback_payload)

    payload = api.list_agent_feedback(
        _request("user_1"),
        pipeline_run_id="run_1",
        context_id="ctx_1",
        target_type="operator_review_lane",
        event_type="operator_lane_overridden",
        limit=10,
    )

    assert payload["owner_user_id"] == "user_1"
    assert captured == {
        "owner_user_id": "user_1",
        "pipeline_run_id": "run_1",
        "context_id": "ctx_1",
        "target_type": "operator_review_lane",
        "event_type": "operator_lane_overridden",
        "limit": 10,
    }


def test_agent_feedback_read_apis_require_auth():
    with pytest.raises(HTTPException) as summary_exc:
        api.agent_feedback_summary(_request(""))
    with pytest.raises(HTTPException) as list_exc:
        api.list_agent_feedback(_request(""))

    assert summary_exc.value.status_code == 401
    assert list_exc.value.status_code == 401


def test_agent_feedback_service_bounds_read_limits(monkeypatch):
    captured = {}

    def fake_summarize_agent_feedback_events(**kwargs):
        captured["summary"] = dict(kwargs)
        return {
            "ok": True,
            "owner_user_id": kwargs["owner_user_id"],
            "summary": {
                "total_events": 0,
                "event_type_counts": {},
                "target_type_counts": {},
                "latest_event_at": "",
            },
            "events": [],
        }

    def fake_list_agent_feedback_events(**kwargs):
        captured["list"] = dict(kwargs)
        return {"ok": True, "events": [], "count": 0}

    monkeypatch.setattr(services, "summarize_agent_feedback_events", fake_summarize_agent_feedback_events)
    monkeypatch.setattr(services, "list_agent_feedback_events", fake_list_agent_feedback_events)

    summary_payload = services.agent_feedback_summary_payload(owner_user_id="user_1", limit=999999)
    list_payload = services.list_agent_feedback_payload(owner_user_id="user_1", limit=999999)

    assert summary_payload["limit"] == services.AGENT_FEEDBACK_SUMMARY_MAX_LIMIT
    assert list_payload["limit"] == services.AGENT_FEEDBACK_LIST_MAX_LIMIT
    assert captured["summary"]["limit"] == services.AGENT_FEEDBACK_SUMMARY_MAX_LIMIT
    assert captured["list"]["limit"] == services.AGENT_FEEDBACK_LIST_MAX_LIMIT
