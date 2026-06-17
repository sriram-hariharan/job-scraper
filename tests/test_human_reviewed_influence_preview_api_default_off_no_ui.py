from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/human-reviewed-influence-preview"
PREVIEW_FLAG = "APPLYLENS_AGENTIC_PIPELINE_HUMAN_REVIEWED_INFLUENCE_PREVIEW_ENABLED"
KILL_SWITCH = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _enabled_config():
    return {PREVIEW_FLAG: True}


def _deterministic_score_context():
    return {
        "agent_name": "final_application_scoring_agent",
        "status": "completed",
        "deterministic_score": 0.91,
        "deterministic_decision": "qualified_priority_ready",
        "decision_counts": {"qualified": 4, "disqualified": 1},
    }


def _shadow_score_comparison_context():
    return {
        "comparison_status": "comparison_ready_with_fallback",
        "comparison_type": "shadow_sidecar_vs_deterministic_score",
        "deterministic_score": 0.91,
        "deterministic_decision": "qualified_priority_ready",
        "shadow_snapshot_status": "snapshot_ready_with_fallback",
        "shadow_agent_names": [
            "jd_intelligence",
            "tailoring_suggestion",
            "critic_guardrail",
        ],
        "shadow_risk_flag_count": 1,
        "shadow_blocking_finding_count": 0,
        "agreement_level": "needs_operator_review",
        "comparison_findings": [
            {
                "finding_code": "shadow_risk_flags_present",
                "severity": "warning",
                "read_only": True,
            }
        ],
        "operator_review_summary": {
            "summary_type": "shadow_sidecar_score_comparison",
            "operator_review_only": True,
            "recommended_review_focus": ["shadow_risk_flags_present"],
        },
    }


def _request_payload():
    return {
        "deterministic_score_context": _deterministic_score_context(),
        "shadow_score_comparison_context": _shadow_score_comparison_context(),
    }


def _assert_api_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["service_helper_only"] is True
    assert safety["api_readback_only"] is True
    assert safety["influence_preview_only"] is True
    assert safety["human_review_required"] is True
    assert safety["approval_gate_required"] is True
    assert safety["did_read_database"] is False
    assert safety["did_write_database"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_create_execution_request"] is False
    assert safety["did_create_execution_launch_request"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False
    assert payload["api_readback_only"] is True
    assert payload["api_surface"] == "human_reviewed_influence_preview"
    assert payload["ui_action_added"] is False


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_default_environment_returns_preview_not_enabled(monkeypatch):
    response = _client(monkeypatch).post(ENDPOINT, json=_request_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview_status"] == "preview_not_enabled"
    assert payload["preview_enabled"] is False
    assert payload["preview_findings"] == []
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    _assert_api_safety(payload)


def test_kill_switch_blocks_api_preview(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            **_request_payload(),
            "preview_config": {PREVIEW_FLAG: True, KILL_SWITCH: True},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview_status"] == "preview_blocked_by_kill_switch"
    assert payload["preview_enabled"] is False
    _assert_api_safety(payload)


def test_missing_deterministic_context_blocks_api_safely(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "preview_config": _enabled_config(),
            "shadow_score_comparison_context": _shadow_score_comparison_context(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview_status"] == "preview_blocked_missing_deterministic_context"
    assert payload["deterministic_score_context"]["deterministic_score"] is None
    _assert_api_safety(payload)


def test_missing_shadow_comparison_blocks_api_safely(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "preview_config": _enabled_config(),
            "deterministic_score_context": _deterministic_score_context(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview_status"] == "preview_blocked_missing_shadow_comparison"
    assert payload["shadow_comparison_context"]["comparison_status"] == ""
    _assert_api_safety(payload)


def test_enabled_api_preview_returns_operator_review_payload(monkeypatch):
    request_payload = {**_request_payload(), "preview_config": _enabled_config()}
    before = deepcopy(request_payload)

    first = _client(monkeypatch).post(ENDPOINT, json=request_payload).json()
    second = _client(monkeypatch).post(ENDPOINT, json=request_payload).json()

    assert first == second
    assert request_payload == before
    assert first["preview_status"] == "preview_ready_with_fallback"
    assert first["preview_type"] == "human_reviewed_shadow_score_influence_preview"
    assert first["deterministic_score_context"]["deterministic_score"] == 0.91
    assert first["shadow_comparison_context"]["comparison_status"] == (
        "comparison_ready_with_fallback"
    )
    assert first["proposed_influence_summary"]["summary_type"] == (
        "human_reviewed_influence_preview"
    )
    assert first["proposed_score_adjustment_preview"]["proposed_score_delta"] == 0.0
    assert first["proposed_score_adjustment_preview"]["did_mutate_scoring"] is False
    assert first["proposed_ranking_effect_preview"]["proposed_ranking_delta"] == 0
    assert first["proposed_ranking_effect_preview"]["did_change_ranking"] is False
    assert first["required_human_review"] is True
    assert first["approval_gate_required"] is True
    assert first["operator_review_summary"]["operator_review_only"] is True
    assert first["operator_review_summary"]["approval_gate_required"] is True
    assert first["provider_calls_disabled_in_tests"] is True
    assert first["requires_live_database"] is False
    assert first["live_provider_backed_automated_agents"] == 0
    assert first["mutation_authorized_agents"] == 0
    _assert_api_safety(first)


def test_api_preview_failure_is_non_blocking(monkeypatch):
    def failing_service(**_kwargs):
        return {
            "preview_status": "preview_failed_non_blocking",
            "preview_type": "human_reviewed_shadow_score_influence_preview",
            "preview_enabled": True,
            "deterministic_score_context": {},
            "shadow_comparison_context": {},
            "proposed_influence_summary": {},
            "proposed_score_adjustment_preview": {},
            "proposed_ranking_effect_preview": {},
            "required_human_review": True,
            "approval_gate_required": True,
            "operator_review_summary": {
                "summary_type": "human_reviewed_influence_preview",
                "review_status": "failed_non_blocking",
                "operator_review_only": True,
                "read_only": True,
                "advisory_only": True,
                "approval_gate_required": True,
            },
            "preview_findings": [],
            "error_type": "RuntimeError",
            "provider_calls_disabled_in_tests": True,
            "requires_live_database": False,
            "live_provider_backed_automated_agents": 0,
            "mutation_authorized_agents": 0,
            "service_helper_only": True,
            "api_route_added": False,
            "ui_action_added": False,
            "safety_metadata": {
                "read_only": True,
                "advisory_only": True,
                "service_helper_only": True,
                "influence_preview_only": True,
                "human_review_required": True,
                "approval_gate_required": True,
                "did_read_database": False,
                "did_write_database": False,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
                "did_mutate_queue": False,
                "did_create_approval": False,
                "did_mutate_approval": False,
                "did_mutate_resume": False,
                "did_create_execution_request": False,
                "did_create_execution_launch_request": False,
                "did_execute_application": False,
                "did_submit_application": False,
                "auto_apply_enabled": False,
                "mutation_authorized": False,
            },
        }

    monkeypatch.setattr(
        services,
        "human_reviewed_influence_preview_service_payload",
        failing_service,
    )
    response = _client(monkeypatch).post(ENDPOINT, json=_request_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["preview_status"] == "preview_failed_non_blocking"
    assert payload["error_type"] == "RuntimeError"
    _assert_api_safety(payload)


def test_api_route_slice_has_no_storage_scoring_queue_execution_or_submission_calls():
    source = Path("src/app/api.py").read_text(encoding="utf-8")
    start = source.index("def human_reviewed_influence_preview")
    end = source.index("def profile_pipeline_run_agentic_review_data", start)
    route_source = source[start:end]
    forbidden = [
        "get_agent_run_postgres_payload(",
        "list_agent_runs_postgres_payload(",
        "list_agent_steps_postgres_payload(",
        "create_agent_run_postgres_payload(",
        "record_agent_step_postgres_payload(",
        "execute_agent_trace_recording(",
        "score_jobs(",
        "rank_jobs(",
        "save_new_job_ids(",
        "create_approval_request(",
        "record_approval_decision(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
    ]
    for marker in forbidden:
        assert marker not in route_source


def test_no_pipeline_or_schema_wiring_for_api_preview():
    helper_markers = [
        "human_reviewed_influence_preview_service_payload",
        "/api/human-reviewed-influence-preview",
    ]
    protected_paths = [
        Path("src/pipeline/collector.py"),
        Path("src/storage/agent_trace/schema.sql"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in protected_paths)

    for marker in helper_markers:
        assert marker not in combined
