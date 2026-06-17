from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services
from src.storage.agentic_approvals import store


ENDPOINT = "/api/human-reviewed-influence-approval-request"
REQUEST_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_HUMAN_REVIEWED_INFLUENCE_APPROVAL_REQUEST_ENABLED"
)
KILL_SWITCH = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"


class FakeConnection:
    pass


class FakeStorageModule:
    def __init__(self):
        self.created_requests = []

    def create_approval_request(self, connection, **kwargs):
        self.created_requests.append((connection, kwargs))
        return {
            "approval_request_id": kwargs["approval_request_id"],
            "approval_status": "pending",
            "idempotency_key": kwargs["idempotency_key"],
        }


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _preview_payload():
    return {
        "preview_status": "preview_ready_with_fallback",
        "preview_type": "human_reviewed_shadow_score_influence_preview",
        "preview_enabled": True,
        "deterministic_score_context": {
            "deterministic_score": 0.91,
            "deterministic_decision": "qualified_priority_ready",
            "context_id": "ctx-1",
            "job_id": "job-1",
        },
        "shadow_comparison_context": {
            "comparison_status": "comparison_ready_with_fallback",
            "agreement_level": "needs_operator_review",
            "shadow_risk_flag_count": 1,
            "shadow_blocking_finding_count": 0,
        },
        "proposed_influence_summary": {
            "summary_type": "human_reviewed_influence_preview",
            "recommended_operator_review": "review_shadow_risk_flags_before_any_future_influence",
        },
        "proposed_score_adjustment_preview": {
            "adjustment_preview_type": "human_review_required_no_score_change",
            "proposed_score_delta": 0.0,
            "did_mutate_scoring": False,
        },
        "proposed_ranking_effect_preview": {
            "ranking_effect_preview_type": "human_review_required_no_ranking_change",
            "proposed_ranking_delta": 0,
            "did_change_ranking": False,
        },
        "required_human_review": True,
        "approval_gate_required": True,
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _enabled_config():
    return {REQUEST_FLAG: True}


def _assert_safety(payload: dict, *, created: bool) -> None:
    safety = payload["safety_metadata"]
    assert safety["read_only"] is (not created)
    assert safety["manual_only"] is True
    assert safety["approval_request_only"] is True
    assert safety["influence_not_applied"] is True
    assert safety["human_review_required"] is True
    assert safety["approval_gate_required"] is True
    assert safety["did_create_approval"] is created
    assert safety["did_mutate_approval"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_create_execution_request"] is False
    assert safety["did_create_execution_launch_request"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False


def test_default_flag_off_does_not_create_approval_request():
    fake_storage = FakeStorageModule()

    payload = services.build_human_reviewed_influence_approval_request_payload(
        human_reviewed_influence_preview_payload=_preview_payload(),
        reviewer_confirmation=True,
        connection=FakeConnection(),
        storage_module=fake_storage,
    )

    assert payload["request_status"] == "not_enabled"
    assert payload["approval_request_created"] is False
    assert payload["created_approval_request_id"] == ""
    assert fake_storage.created_requests == []
    _assert_safety(payload, created=False)


def test_kill_switch_blocks_before_storage():
    fake_storage = FakeStorageModule()
    connection_calls = []

    payload = services.build_human_reviewed_influence_approval_request_payload(
        human_reviewed_influence_preview_payload=_preview_payload(),
        preview_config={REQUEST_FLAG: True, KILL_SWITCH: True},
        reviewer_confirmation=True,
        connection_provider=lambda: connection_calls.append("connection") or FakeConnection(),
        storage_module=fake_storage,
    )

    assert payload["request_status"] == "blocked_by_kill_switch"
    assert connection_calls == []
    assert fake_storage.created_requests == []
    _assert_safety(payload, created=False)


def test_missing_preview_context_blocks_before_storage():
    fake_storage = FakeStorageModule()

    payload = services.build_human_reviewed_influence_approval_request_payload(
        human_reviewed_influence_preview_payload={"preview_status": "preview_not_enabled"},
        preview_config=_enabled_config(),
        reviewer_confirmation=True,
        connection=FakeConnection(),
        storage_module=fake_storage,
    )

    assert payload["request_status"] == "blocked_missing_preview_context"
    assert "human_reviewed_influence_preview_not_ready" in payload["blocked_actions"]
    assert fake_storage.created_requests == []
    _assert_safety(payload, created=False)


def test_missing_reviewer_confirmation_blocks_before_storage():
    fake_storage = FakeStorageModule()

    payload = services.build_human_reviewed_influence_approval_request_payload(
        human_reviewed_influence_preview_payload=_preview_payload(),
        preview_config=_enabled_config(),
        reviewer_confirmation=False,
        connection=FakeConnection(),
        storage_module=fake_storage,
    )

    assert payload["request_status"] == "blocked_missing_reviewer_confirmation"
    assert payload["created_approval_request_id"] == ""
    assert fake_storage.created_requests == []
    _assert_safety(payload, created=False)


def test_enabled_manual_request_creates_approval_request_only_with_fake_storage():
    fake_storage = FakeStorageModule()
    connection = FakeConnection()
    preview = _preview_payload()
    before = deepcopy(preview)

    payload = services.build_human_reviewed_influence_approval_request_payload(
        human_reviewed_influence_preview_payload=preview,
        preview_config=_enabled_config(),
        reviewer_confirmation=True,
        reviewer_note="Looks safe for review only.",
        context_id="ctx-1",
        job_id="job-1",
        connection=connection,
        storage_module=fake_storage,
    )

    assert preview == before
    assert payload["request_status"] == "created"
    assert payload["approval_request_type"] == "approval_gated_influence_request"
    assert payload["approval_request_created"] is True
    assert payload["created_approval_request_id"].startswith("manual_influence_approval_")
    assert payload["proposed_score_adjustment_preview"]["did_mutate_scoring"] is False
    assert payload["proposed_ranking_effect_preview"]["did_change_ranking"] is False
    assert len(fake_storage.created_requests) == 1
    passed_connection, create_kwargs = fake_storage.created_requests[0]
    assert passed_connection is connection
    assert create_kwargs["proposed_action_type"] == "human_reviewed_influence_preview"
    assert "influence is not applied" in create_kwargs["proposed_action_summary"]
    assert create_kwargs["queue_safety_gate_snapshot"] == {}
    fixture_snapshot = create_kwargs["fixture_validation_snapshot"]
    assert fixture_snapshot["deterministic_score_context"]["deterministic_score"] == 0.91
    assert fixture_snapshot["shadow_comparison_context"]["comparison_status"] == (
        "comparison_ready_with_fallback"
    )
    assert fixture_snapshot["proposed_score_adjustment_preview"]["did_mutate_scoring"] is False
    assert fixture_snapshot["proposed_ranking_effect_preview"]["did_change_ranking"] is False
    assert fixture_snapshot["human_review_required"] is True
    assert fixture_snapshot["approval_gate_required"] is True
    assert fixture_snapshot["safety_metadata"]["influence_not_applied"] is True
    _assert_safety(payload, created=True)


def test_storage_failure_is_non_blocking():
    class FailingStorage(FakeStorageModule):
        def create_approval_request(self, connection, **kwargs):
            raise RuntimeError("storage unavailable")

    payload = services.build_human_reviewed_influence_approval_request_payload(
        human_reviewed_influence_preview_payload=_preview_payload(),
        preview_config=_enabled_config(),
        reviewer_confirmation=True,
        connection=FakeConnection(),
        storage_module=FailingStorage(),
    )

    assert payload["request_status"] == "failed_non_blocking"
    assert payload["approval_request_created"] is False
    assert payload["created_approval_request_id"] == ""
    _assert_safety(payload, created=False)


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_creates_with_fake_storage_only(monkeypatch):
    connection = FakeConnection()
    calls = []

    def fake_create_approval_request(passed_connection, **kwargs):
        calls.append((passed_connection, kwargs))
        return {
            "approval_request_id": kwargs["approval_request_id"],
            "approval_status": "pending",
            "idempotency_key": kwargs["idempotency_key"],
        }

    monkeypatch.setattr(api, "_agentic_approval_storage_connection", lambda: connection)
    monkeypatch.setattr(store, "create_approval_request", fake_create_approval_request)

    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "human_reviewed_influence_preview_payload": _preview_payload(),
            "preview_config": _enabled_config(),
            "reviewer_confirmation": True,
            "context_id": "ctx-1",
            "job_id": "job-1",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_surface"] == "human_reviewed_influence_approval_request"
    assert payload["explicit_user_action"] is True
    assert payload["request_status"] == "created"
    assert len(calls) == 1
    _assert_safety(payload, created=True)


def test_api_blocks_default_off_and_does_not_open_storage(monkeypatch):
    calls = []
    monkeypatch.setattr(api, "_agentic_approval_storage_connection", lambda: calls.append("connection"))
    monkeypatch.setattr(store, "create_approval_request", lambda *args, **kwargs: calls.append("create"))

    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "human_reviewed_influence_preview_payload": _preview_payload(),
            "reviewer_confirmation": True,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["request_status"] == "not_enabled"
    assert payload["created_approval_request_id"] == ""
    assert calls == []
    _assert_safety(payload, created=False)


def test_api_route_slice_has_no_scoring_ranking_queue_resume_execution_or_submission_mutation():
    source = Path("src/app/api.py").read_text()
    route_start = source.index('@app.post("/api/human-reviewed-influence-approval-request")')
    route_end = source.index('@app.get("/profile/pipeline-runs/{run_id}/agentic-review-data")')
    snippet = source[route_start:route_end]

    forbidden_markers = [
        "application_execution_queue",
        "score_resume_job_match",
        "ranking_update",
        "ranking_mutation",
        "insert_operator_decision",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "run_chat_completion",
        "openai",
        "anthropic",
        "llm_client",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet


def test_service_helper_slice_uses_existing_approval_persist_call_only():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_human_reviewed_influence_approval_request_payload")
    end = source.index("def record_agent_feedback_payload")
    snippet = source[start:end]

    forbidden_markers = [
        "application_execution_queue",
        "score_resume_job_match",
        "ranking_update",
        "ranking_mutation",
        "insert_operator_decision",
        "record_approval_decision(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "run_chat_completion",
        "openai",
        "anthropic",
        "llm_client",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet
    assert "app_service_persist_agentic_approval_request(" in snippet


def test_ui_renders_manual_influence_approval_request_and_escapes_output():
    source = Path("src/app/static/agentic_review.js").read_text()
    start = source.index("function renderHumanReviewedInfluenceApprovalRequestSection")
    end = source.index("function renderAgentTraceDetailedSections")
    snippet = source[start:end]

    assert "Human-reviewed Influence Approval Request" in snippet
    assert "Request Influence Approval" in snippet
    assert "data-human-reviewed-influence-approval-request" in snippet
    assert "data-human-reviewed-influence-approval-request-confirmation" in snippet
    assert "escapeHtml(contextId)" in snippet
    assert "escapeHtml(jobId)" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Influence preview payload\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Proposed score adjustment preview\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Proposed ranking effect preview\"" in snippet
    assert "renderAgentTraceReadOnlyDetails(\"Safety metadata\"" in snippet


def test_ui_posts_endpoint_and_existing_influence_preview_still_works():
    source = Path("src/app/static/agentic_review.js").read_text()

    assert source.count("/api/human-reviewed-influence-approval-request") == 1
    assert "human_reviewed_influence_approval_request_result" in source
    assert "renderHumanReviewedInfluenceApprovalRequestSection(tracePayload)" in source
    assert source.count("/api/human-reviewed-influence-preview") == 1
    assert "renderHumanReviewedInfluencePreviewSection(tracePayload)" in source
