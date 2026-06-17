from copy import deepcopy
from pathlib import Path

from src.agents import shadow_sidecar_trace_readback as readback


GLOBAL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
READBACK_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_READBACK_ENABLED"
KILL_SWITCH = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"


def _enabled_config():
    return {
        GLOBAL_FLAG: True,
        READBACK_FLAG: True,
    }


def _lookup_kwargs():
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
            "summary_json": {
                "trace_persistence_status": "trace_persistence_ready",
            },
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


def _assert_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["trace_readback_only"] is True
    assert safety["did_read_database"] is False
    assert safety["did_write_database"] is False
    assert safety["did_write_agent_trace_run"] is False
    assert safety["did_write_agent_trace_step"] is False
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
    assert safety["pipeline_wiring_added"] is False
    assert safety["api_route_added"] is False
    assert safety["ui_action_added"] is False
    assert safety["auto_apply_enabled"] is False


def test_default_environment_returns_trace_readback_not_enabled():
    calls = []

    def reader(_context):
        calls.append("called")
        return _readback_source()

    payload = readback.build_shadow_sidecar_trace_readback_payload(
        **_lookup_kwargs(),
        sidecar_config={},
        readback_reader=reader,
    )

    assert payload["trace_readback_status"] == "trace_readback_not_enabled"
    assert payload["readback_attempted"] is False
    assert payload["trace_readback"] == {}
    assert calls == []
    _assert_safety(payload)


def test_global_sidecar_disabled_does_not_attempt_readback():
    calls = []

    def reader(_context):
        calls.append("called")
        return _readback_source()

    payload = readback.build_shadow_sidecar_trace_readback_payload(
        **_lookup_kwargs(),
        sidecar_config={GLOBAL_FLAG: False, READBACK_FLAG: True},
        readback_reader=reader,
    )

    assert payload["trace_readback_status"] == "trace_readback_not_enabled"
    assert payload["readback_attempted"] is False
    assert calls == []
    _assert_safety(payload)


def test_kill_switch_blocks_readback():
    payload = readback.build_shadow_sidecar_trace_readback_payload(
        **_lookup_kwargs(),
        sidecar_config={GLOBAL_FLAG: True, READBACK_FLAG: True, KILL_SWITCH: True},
        readback_source=_readback_source(),
    )

    assert payload["trace_readback_status"] == (
        "trace_readback_blocked_by_kill_switch"
    )
    assert payload["readback_attempted"] is False
    assert payload["trace_readback"] == {}
    _assert_safety(payload)


def test_missing_lookup_context_blocks_safely():
    payload = readback.build_shadow_sidecar_trace_readback_payload(
        sidecar_config=_enabled_config(),
        readback_source=_readback_source(),
    )

    assert payload["trace_readback_status"] == (
        "trace_readback_blocked_missing_context"
    )
    assert payload["trace_readback"] == {}
    _assert_safety(payload)


def test_invalid_lookup_context_blocks_safely():
    payload = readback.build_shadow_sidecar_trace_readback_payload(
        owner_user_id="owner_shadow",
        pipeline_run_id="pipeline\nshadow",
        sidecar_config=_enabled_config(),
        readback_source=_readback_source(),
    )

    assert payload["trace_readback_status"] == (
        "trace_readback_blocked_invalid_context"
    )
    assert payload["trace_readback"] == {}
    _assert_safety(payload)


def test_enabled_readback_builds_deterministic_envelope_without_live_db():
    source = _readback_source()
    before = deepcopy(source)

    first = readback.build_shadow_sidecar_trace_readback_payload(
        **_lookup_kwargs(),
        sidecar_config=_enabled_config(),
        readback_source=source,
    )
    second = readback.build_shadow_sidecar_trace_readback_payload(
        **_lookup_kwargs(),
        sidecar_config=_enabled_config(),
        readback_source=source,
    )

    assert first == second
    assert source == before
    assert first["trace_readback_status"] == "trace_readback_ready"
    assert first["requires_live_database"] is False
    assert first["provider_calls_disabled_in_tests"] is True
    assert first["source_trace_context"]["pipeline_run_id"] == "pipeline_shadow"
    envelope = first["trace_readback"]
    assert envelope["readback_type"] == "shadow_sidecar_trace_readback"
    assert envelope["counts"] == {"agent_runs": 1, "agent_steps": 1}
    assert envelope["trace_summary"]["summary_type"] == "agent_trace"
    assert envelope["trace_summary"]["run_count"] == 1
    assert envelope["trace_summary"]["step_count"] == 1
    assert envelope["stage_trace_bundle"]["bundle_type"] == "stage_trace_bundle"
    assert envelope["stage_trace_health"]["health_status"] in {"healthy", "warning"}
    assert envelope["stage_trace_readiness"]["readiness_status"] in {
        "ready",
        "warning",
        "blocked",
    }
    assert envelope["trace_evidence_pack"]["evidence_pack_type"] == (
        "agent_trace_evidence_pack"
    )
    assert first["live_provider_backed_automated_agents"] == 0
    assert first["mutation_authorized_agents"] == 0
    _assert_safety(first)


def test_enabled_readback_without_safe_source_skips_without_live_db():
    payload = readback.build_shadow_sidecar_trace_readback_payload(
        **_lookup_kwargs(),
        sidecar_config=_enabled_config(),
    )

    assert payload["trace_readback_status"] == "trace_readback_skipped_no_safe_source"
    assert payload["readback_attempted"] is False
    assert payload["trace_readback"] == {}
    assert payload["requires_live_database"] is False
    _assert_safety(payload)


def test_readback_failure_is_non_blocking_with_injected_reader():
    def reader(_context):
        raise RuntimeError("read boom")

    payload = readback.build_shadow_sidecar_trace_readback_payload(
        **_lookup_kwargs(),
        sidecar_config=_enabled_config(),
        readback_reader=reader,
    )

    assert payload["trace_readback_status"] == (
        "trace_readback_failed_non_blocking"
    )
    assert payload["readback_attempted"] is True
    assert payload["reader_result"]["error_type"] == "RuntimeError"
    assert payload["trace_readback"] == {}
    _assert_safety(payload)


def test_source_has_no_pipeline_api_ui_schema_or_provider_wiring():
    source = Path("src/agents/shadow_sidecar_trace_readback.py").read_text(
        encoding="utf-8"
    )
    forbidden = [
        "src.pipeline",
        "src.app.api",
        "src.app.services",
        "agentic_review.js",
        "schema.sql",
        "connect(",
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
        assert marker not in source


def test_runtime_api_ui_storage_schema_files_do_not_call_trace_readback_helper():
    protected_paths = [
        Path("src/pipeline/collector.py"),
        Path("src/app/api.py"),
        Path("src/app/services.py"),
        Path("src/app/static/agentic_review.js"),
        Path("src/storage/agent_trace/schema.sql"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in protected_paths)

    assert "shadow_sidecar_trace_readback" not in combined
    assert "build_shadow_sidecar_trace_readback_payload" not in combined
