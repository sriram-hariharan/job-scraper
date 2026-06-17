from copy import deepcopy
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ENDPOINT = "/api/shadow-sidecar/trace-readback"
GLOBAL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
READBACK_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_READBACK_ENABLED"
KILL_SWITCH = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"


def _client(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    return TestClient(api.app)


def _enabled_config():
    return {
        GLOBAL_FLAG: True,
        READBACK_FLAG: True,
    }


def _lookup_payload():
    return {
        "owner_user_id": "owner_shadow",
        "pipeline_run_id": "pipeline_shadow",
        "context_id": "context_shadow",
    }


def _readback_source():
    return {
        "agent_run_record": {
            "agent_run_id": "shadow_sidecar_trace_persistence",
            "owner_user_id": "owner_shadow",
            "pipeline_run_id": "pipeline_shadow",
            "context_id": "context_shadow",
            "status": "ready",
            "started_at": "in_memory",
            "completed_at": "in_memory",
            "summary_json": {"trace_persistence_status": "trace_persistence_ready"},
            "error": "",
        },
        "agent_step_record": {
            "agent_step_id": "shadow_sidecar_trace_persistence_step",
            "agent_run_id": "shadow_sidecar_trace_persistence",
            "owner_user_id": "owner_shadow",
            "pipeline_run_id": "pipeline_shadow",
            "context_id": "context_shadow",
            "agent_name": "Shadow Sidecar Trace Persistence",
            "agent_version": "phase5_shadow_sidecar_trace_v1",
            "input_json": {"trace_capture_status": "trace_capture_captured"},
            "output_json": {
                "trace_bundle": {"bundle_type": "shadow_sidecar_chain_trace_bundle"},
                "evidence_pack": {
                    "evidence_pack_type": "shadow_sidecar_chain_evidence_pack"
                },
            },
            "validation_json": {"trace_capture_valid": True},
            "status": "ready",
            "started_at": "in_memory",
            "completed_at": "in_memory",
            "latency_ms": 0,
            "model_provider": "",
            "model_name": "",
            "token_usage_json": {},
            "cost_json": {},
            "error": "",
        },
    }


def _assert_api_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["api_readback_only"] is True
    assert safety["service_helper_only"] is True
    assert safety["trace_readback_only"] is True
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
    assert payload["api_readback_only"] is True
    assert payload["api_surface"] == "shadow_sidecar_trace_readback"
    assert payload["ui_action_added"] is False


def test_api_route_exists_as_post_only():
    routes = {getattr(route, "path", ""): route for route in api.app.routes}

    assert routes[ENDPOINT].methods == {"POST"}


def test_api_route_default_environment_returns_trace_readback_not_enabled(monkeypatch):
    response = _client(monkeypatch).post(ENDPOINT, json=_lookup_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["trace_readback_status"] == "trace_readback_not_enabled"
    assert payload["readback_attempted"] is False
    assert payload["trace_readback"] == {}
    _assert_api_safety(payload)


def test_global_sidecar_disabled_does_not_attempt_api_readback(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            **_lookup_payload(),
            "sidecar_config": {GLOBAL_FLAG: False, READBACK_FLAG: True},
            "readback_source": _readback_source(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["trace_readback_status"] == "trace_readback_not_enabled"
    assert payload["readback_attempted"] is False
    assert payload["trace_readback"] == {}
    _assert_api_safety(payload)


def test_kill_switch_blocks_api_readback(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            **_lookup_payload(),
            "sidecar_config": {GLOBAL_FLAG: True, READBACK_FLAG: True, KILL_SWITCH: True},
            "readback_source": _readback_source(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["trace_readback_status"] == (
        "trace_readback_blocked_by_kill_switch"
    )
    assert payload["trace_readback"] == {}
    _assert_api_safety(payload)


def test_missing_lookup_context_blocks_api_readback_safely(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "sidecar_config": _enabled_config(),
            "readback_source": _readback_source(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["trace_readback_status"] == (
        "trace_readback_blocked_missing_context"
    )
    assert payload["trace_readback"] == {}
    _assert_api_safety(payload)


def test_invalid_lookup_context_blocks_api_readback_safely(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={
            "owner_user_id": "owner_shadow",
            "pipeline_run_id": "pipeline\nshadow",
            "sidecar_config": _enabled_config(),
            "readback_source": _readback_source(),
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["trace_readback_status"] == (
        "trace_readback_blocked_invalid_context"
    )
    assert payload["trace_readback"] == {}
    _assert_api_safety(payload)


def test_enabled_api_readback_returns_deterministic_envelope_without_live_db(monkeypatch):
    request_payload = {
        **_lookup_payload(),
        "sidecar_config": _enabled_config(),
        "readback_source": _readback_source(),
    }
    before = deepcopy(request_payload)

    first = _client(monkeypatch).post(ENDPOINT, json=request_payload).json()
    second = _client(monkeypatch).post(ENDPOINT, json=request_payload).json()

    assert first == second
    assert request_payload == before
    assert first["trace_readback_status"] == "trace_readback_ready"
    assert first["requires_live_database"] is False
    assert first["provider_calls_disabled_in_tests"] is True
    assert first["source_trace_context"]["pipeline_run_id"] == "pipeline_shadow"
    envelope = first["trace_readback"]
    assert envelope["readback_type"] == "shadow_sidecar_trace_readback"
    assert envelope["counts"] == {"agent_runs": 1, "agent_steps": 1}
    assert envelope["trace_summary"]["summary_type"] == "agent_trace"
    assert envelope["trace_evidence_pack"]["evidence_pack_type"] == (
        "agent_trace_evidence_pack"
    )
    assert first["live_provider_backed_automated_agents"] == 0
    assert first["mutation_authorized_agents"] == 0
    _assert_api_safety(first)


def test_api_readback_without_safe_source_skips_without_live_db(monkeypatch):
    response = _client(monkeypatch).post(
        ENDPOINT,
        json={**_lookup_payload(), "sidecar_config": _enabled_config()},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["trace_readback_status"] == "trace_readback_skipped_no_safe_source"
    assert payload["readback_attempted"] is False
    assert payload["trace_readback"] == {}
    assert payload["requires_live_database"] is False
    _assert_api_safety(payload)


def test_api_readback_failure_is_non_blocking(monkeypatch):
    def failing_service(**_kwargs):
        return {
            "trace_readback_status": "trace_readback_failed_non_blocking",
            "trace_readback_only": True,
            "readback_attempted": True,
            "source_trace_context": _lookup_payload(),
            "trace_readback": {},
            "reader_result": {"error_type": "RuntimeError"},
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
                "trace_readback_only": True,
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
            },
        }

    monkeypatch.setattr(
        services,
        "shadow_sidecar_trace_readback_service_payload",
        failing_service,
    )
    response = _client(monkeypatch).post(ENDPOINT, json=_lookup_payload())

    assert response.status_code == 200
    payload = response.json()
    assert payload["trace_readback_status"] == (
        "trace_readback_failed_non_blocking"
    )
    assert payload["reader_result"]["error_type"] == "RuntimeError"
    assert payload["trace_readback"] == {}
    _assert_api_safety(payload)


def test_api_route_slice_has_no_storage_scoring_queue_or_execution_calls():
    source = Path("src/app/api.py").read_text(encoding="utf-8")
    start = source.index("def shadow_sidecar_trace_readback")
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


def test_no_ui_pipeline_or_schema_wiring_for_api_readback():
    protected_paths = [
        Path("src/pipeline/collector.py"),
        Path("src/app/static/agentic_review.js"),
        Path("src/storage/agent_trace/schema.sql"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in protected_paths)

    assert "shadow_sidecar_trace_readback" not in combined
    assert "shadow_sidecar_trace_readback_service_payload" not in combined
