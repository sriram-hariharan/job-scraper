from src.app import services


def _run(**overrides):
    row = {
        "agent_run_id": "agent_run_1",
        "owner_user_id": "user_1",
        "pipeline_run_id": "run_1",
        "context_id": "",
        "status": "succeeded",
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:02Z",
        "summary_json": {"jobs": 2},
        "error": "",
    }
    row.update(overrides)
    return row


def _step(**overrides):
    row = {
        "agent_step_id": "agent_step_1",
        "agent_run_id": "agent_run_1",
        "owner_user_id": "user_1",
        "pipeline_run_id": "run_1",
        "context_id": "",
        "agent_name": "resume_match_agent",
        "agent_version": "v1",
        "input_json": {"jobs": 2},
        "output_json": {"selected": 1},
        "validation_json": {"validation_status": "passed"},
        "status": "succeeded",
        "started_at": "2026-01-01T00:00:00Z",
        "completed_at": "2026-01-01T00:00:01Z",
        "latency_ms": 100,
        "model_provider": "",
        "model_name": "",
        "token_usage_json": {},
        "cost_json": {},
        "error": "",
    }
    row.update(overrides)
    return row


def test_agent_trace_payload_includes_read_only_trace_summary(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"runs": [_run()]},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {
            "steps": [
                _step(),
                _step(
                    agent_step_id="agent_step_2",
                    agent_name="critic_agent",
                    status="failed",
                    error="invalid suggestion",
                    latency_ms=300,
                ),
            ]
        },
    )

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_trace_summary=True,
    )

    assert payload["counts"] == {
        "agent_runs": 1,
        "agent_steps": 2,
        "failed_steps": 1,
        "warning_steps": 0,
        "succeeded_steps": 1,
    }

    trace_summary = payload["trace_summary"]
    assert trace_summary["ok"] is True
    assert trace_summary["summary_type"] == "agent_trace"
    assert trace_summary["run_count"] == 1
    assert trace_summary["step_count"] == 2
    assert trace_summary["error_step_count"] == 1
    assert trace_summary["agent_counts"] == {
        "critic_agent": 1,
        "resume_match_agent": 1,
    }
    assert trace_summary["latency_summary"] == {
        "count": 2,
        "total_ms": 400,
        "min_ms": 100,
        "max_ms": 300,
        "average_ms": 200.0,
    }
    assert trace_summary["all_required_fields_present"] is True
    assert trace_summary["safety_metadata"]["did_read_database"] is False
    assert trace_summary["safety_metadata"]["did_write_database"] is False
    assert trace_summary["safety_metadata"]["did_call_llm"] is False
    assert trace_summary["safety_metadata"]["did_execute_application"] is False
    assert trace_summary["safety_metadata"]["did_submit_application"] is False


def test_agent_trace_payload_empty_result_includes_empty_trace_summary(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"runs": []},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {"steps": []},
    )

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_trace_summary=True,
    )

    assert payload["agent_runs"] == []
    assert payload["counts"]["agent_runs"] == 0
    assert payload["counts"]["agent_steps"] == 0
    assert payload["trace_summary"]["run_count"] == 0
    assert payload["trace_summary"]["step_count"] == 0
    assert payload["trace_summary"]["all_required_fields_present"] is True
    assert payload["trace_summary"]["safety_metadata"]["did_write_database"] is False


def test_agent_trace_payload_exception_fallback_includes_empty_trace_summary(monkeypatch):
    def fail_runs(**kwargs):
        raise SystemExit("database unavailable")

    monkeypatch.setattr(services, "list_agent_runs_postgres_payload", fail_runs)

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_trace_summary=True,
    )

    assert payload["agent_runs"] == []
    assert payload["counts"] == {
        "agent_runs": 0,
        "agent_steps": 0,
        "failed_steps": 0,
        "warning_steps": 0,
        "succeeded_steps": 0,
    }
    assert payload["trace_summary"]["run_count"] == 0
    assert payload["trace_summary"]["step_count"] == 0
    assert payload["trace_summary"]["safety_metadata"]["did_write_database"] is False


def test_agent_trace_payload_default_shape_preserves_existing_api_contract(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"runs": []},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {"steps": []},
    )

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
        include_trace_summary=True,
    )

    assert payload == {
        "pipeline_run_id": "run_1",
        "owner_user_id": "user_1",
        "agent_runs": [],
        "counts": {
            "agent_runs": 0,
            "agent_steps": 0,
            "failed_steps": 0,
            "warning_steps": 0,
            "succeeded_steps": 0,
        },
    }


def test_agent_trace_payload_default_shape_preserves_existing_api_contract(monkeypatch):
    monkeypatch.setattr(
        services,
        "list_agent_runs_postgres_payload",
        lambda **kwargs: {"runs": []},
    )
    monkeypatch.setattr(
        services,
        "list_agent_steps_postgres_payload",
        lambda **kwargs: {"steps": []},
    )

    payload = services.agent_trace_payload(
        owner_user_id="user_1",
        pipeline_run_id="run_1",
    )

    assert payload == {
        "pipeline_run_id": "run_1",
        "owner_user_id": "user_1",
        "agent_runs": [],
        "counts": {
            "agent_runs": 0,
            "agent_steps": 0,
            "failed_steps": 0,
            "warning_steps": 0,
            "succeeded_steps": 0,
        },
    }
