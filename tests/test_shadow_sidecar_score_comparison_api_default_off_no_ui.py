from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/shadow-sidecar/score-comparison"
GLOBAL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
COMPARISON_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SCORE_COMPARISON_ENABLED"
KILL_SWITCH = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _enabled_config():
    return {
        GLOBAL_FLAG: True,
        COMPARISON_FLAG: True,
    }


def _deterministic_score_context():
    return {
        "agent_name": "final_application_scoring_agent",
        "status": "completed",
        "deterministic_score": 0.91,
        "deterministic_decision": "qualified_priority_ready",
        "score_summary": {"max_score": 0.91, "average_score": 0.72},
    }


def _shadow_snapshot_payload():
    return {
        "snapshot_status": "snapshot_ready_with_fallback",
        "snapshot_type": "shadow_sidecar_evidence_snapshot",
        "agent_names": [
            "jd_intelligence",
            "tailoring_suggestion",
            "critic_guardrail",
        ],
        "fallback_count": 1,
        "risk_flag_count": 1,
        "blocking_finding_count": 0,
    }


def _request_payload():
    return {
        "deterministic_score_context": _deterministic_score_context(),
        "shadow_evidence_snapshot_payload": _shadow_snapshot_payload(),
    }


def _assert_api_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["service_helper_only"] is True
    assert safety["api_readback_only"] is True
    assert safety["score_comparison_only"] is True
    assert safety["operator_review_only"] is True
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
    assert payload["api_surface"] == "shadow_sidecar_score_comparison"
    assert payload["ui_action_added"] is False


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_default_environment_returns_comparison_not_enabled(monkeypatch):
    response = _client(monkeypatch).post(ENDPOINT, json=_request_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["comparison_status"] == "comparison_not_enabled"
    assert payload["comparison_enabled"] is False
    assert payload["comparison_findings"] == []
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    _assert_api_safety(payload)


def test_kill_switch_blocks_api_comparison(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            **_request_payload(),
            "sidecar_config": {
                GLOBAL_FLAG: True,
                COMPARISON_FLAG: True,
                KILL_SWITCH: True,
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["comparison_status"] == "comparison_blocked_by_kill_switch"
    assert payload["comparison_enabled"] is False
    _assert_api_safety(payload)


def test_missing_deterministic_score_context_blocks_api_safely(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "sidecar_config": _enabled_config(),
            "shadow_evidence_snapshot_payload": _shadow_snapshot_payload(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["comparison_status"] == (
        "comparison_blocked_missing_deterministic_context"
    )
    assert payload["deterministic_score"] is None
    _assert_api_safety(payload)


def test_missing_shadow_snapshot_blocks_api_safely(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "sidecar_config": _enabled_config(),
            "deterministic_score_context": _deterministic_score_context(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["comparison_status"] == (
        "comparison_blocked_missing_shadow_snapshot"
    )
    assert payload["shadow_snapshot_status"] == ""
    _assert_api_safety(payload)


def test_enabled_api_comparison_returns_operator_review_payload(monkeypatch):
    request_payload = {**_request_payload(), "sidecar_config": _enabled_config()}
    before = deepcopy(request_payload)

    first = _client(monkeypatch).post(ENDPOINT, json=request_payload).json()
    second = _client(monkeypatch).post(ENDPOINT, json=request_payload).json()

    assert first == second
    assert request_payload == before
    assert first["comparison_status"] == "comparison_ready_with_fallback"
    assert first["deterministic_score"] == 0.91
    assert first["deterministic_decision"] == "qualified_priority_ready"
    assert first["shadow_snapshot_status"] == "snapshot_ready_with_fallback"
    assert first["agreement_level"] == "needs_operator_review"
    assert first["comparison_findings"]
    assert first["operator_review_summary"]["operator_review_only"] is True
    assert first["provider_calls_disabled_in_tests"] is True
    assert first["requires_live_database"] is False
    assert first["live_provider_backed_automated_agents"] == 0
    assert first["mutation_authorized_agents"] == 0
    _assert_api_safety(first)


def test_api_comparison_failure_is_non_blocking(monkeypatch):
    def failing_service(**_kwargs):
        return {
            "comparison_status": "comparison_failed_non_blocking",
            "comparison_type": "shadow_sidecar_vs_deterministic_score",
            "comparison_enabled": True,
            "deterministic_score": None,
            "deterministic_decision": "",
            "shadow_snapshot_status": "",
            "shadow_agent_names": [],
            "shadow_risk_flag_count": 0,
            "shadow_blocking_finding_count": 0,
            "agreement_level": "",
            "operator_review_summary": {
                "summary_type": "shadow_sidecar_score_comparison",
                "review_status": "failed_non_blocking",
                "operator_review_only": True,
                "read_only": True,
            },
            "comparison_findings": [],
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
                "shadow_only": True,
                "service_helper_only": True,
                "score_comparison_only": True,
                "operator_review_only": True,
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
        "shadow_sidecar_score_comparison_service_payload",
        failing_service,
    )
    response = _client(monkeypatch).post(ENDPOINT, json=_request_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["comparison_status"] == "comparison_failed_non_blocking"
    assert payload["error_type"] == "RuntimeError"
    _assert_api_safety(payload)


def test_api_route_slice_has_no_storage_scoring_queue_execution_or_submission_calls():
    source = Path("src/app/api.py").read_text(encoding="utf-8")
    start = source.index("def shadow_sidecar_score_comparison")
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


def test_no_pipeline_or_schema_wiring_for_api_comparison():
    protected_paths = [
        Path("src/pipeline/collector.py"),
        Path("src/storage/agent_trace/schema.sql"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in protected_paths)

    assert "shadow_sidecar_score_comparison" not in combined
    assert "shadow_sidecar_score_comparison_service_payload" not in combined
