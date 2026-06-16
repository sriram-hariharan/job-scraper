from copy import deepcopy
from pathlib import Path

from src.agents import shadow_sidecar_trace_persistence as persistence


GLOBAL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
PERSISTENCE_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_PERSISTENCE_ENABLED"
)
KILL_SWITCH = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"


def _trace_capture_payload():
    return {
        "schema_version": "phase5_shadow_sidecar_trace_v1",
        "trace_capture_status": "trace_capture_captured",
        "trace_capture_only": True,
        "persistence_deferred": True,
        "hook_status": "hook_completed_with_fallback",
        "hook_preview_status": "hook_ready_for_shadow_sidecar",
        "chain_attempted": True,
        "chain_summary": {
            "chain_status": "completed_with_fallback",
            "stage_order": ["jd_intelligence"],
            "stage_statuses": {"jd_intelligence": "completed_with_fallback"},
            "fallback_used": True,
        },
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 1,
        "source_deterministic_decision": "scored_jobs_available",
        "source_deterministic_reason_codes": ["application_priority_completed"],
        "trace_bundle": {"bundle_type": "shadow_sidecar_chain_trace_bundle"},
        "evidence_pack": {"evidence_pack_type": "shadow_sidecar_chain_evidence_pack"},
        "safety_metadata": {
            "read_only": True,
            "shadow_only": True,
            "trace_capture_only": True,
            "pipeline_hook_called_by_pipeline": True,
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
        },
    }


def _enabled_config():
    return {
        GLOBAL_FLAG: True,
        PERSISTENCE_FLAG: True,
    }


def _assert_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["trace_persistence_only"] is True
    assert safety["pipeline_hook_called_by_pipeline"] is False
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
    assert safety["auto_apply_enabled"] is False


def test_default_environment_returns_trace_persistence_not_enabled():
    trace_capture = _trace_capture_payload()
    before = deepcopy(trace_capture)

    payload = persistence.build_shadow_sidecar_trace_persistence_payload(
        trace_capture_payload=trace_capture,
        sidecar_config={},
    )

    assert payload["trace_persistence_status"] == "trace_persistence_not_enabled"
    assert payload["persistence_attempted"] is False
    assert payload["persistence_records"] == {}
    assert trace_capture == before
    _assert_safety(payload)


def test_global_sidecar_disabled_does_not_attempt_persistence():
    calls = []

    def writer(_records):
        calls.append("called")
        return {"ok": True}

    payload = persistence.build_shadow_sidecar_trace_persistence_payload(
        trace_capture_payload=_trace_capture_payload(),
        sidecar_config={GLOBAL_FLAG: False, PERSISTENCE_FLAG: True},
        persistence_writer=writer,
    )

    assert payload["trace_persistence_status"] == "trace_persistence_not_enabled"
    assert payload["persistence_attempted"] is False
    assert calls == []
    _assert_safety(payload)


def test_kill_switch_blocks_persistence():
    payload = persistence.build_shadow_sidecar_trace_persistence_payload(
        trace_capture_payload=_trace_capture_payload(),
        sidecar_config={GLOBAL_FLAG: True, PERSISTENCE_FLAG: True, KILL_SWITCH: True},
    )

    assert payload["trace_persistence_status"] == (
        "trace_persistence_blocked_by_kill_switch"
    )
    assert payload["persistence_attempted"] is False
    _assert_safety(payload)


def test_missing_trace_capture_payload_blocks_safely():
    payload = persistence.build_shadow_sidecar_trace_persistence_payload(
        trace_capture_payload=None,
        sidecar_config=_enabled_config(),
    )

    assert payload["trace_persistence_status"] == (
        "trace_persistence_blocked_missing_trace"
    )
    assert payload["persistence_records"] == {}
    _assert_safety(payload)


def test_invalid_trace_capture_payload_blocks_safely():
    payload = persistence.build_shadow_sidecar_trace_persistence_payload(
        trace_capture_payload={"trace_capture_only": True},
        sidecar_config=_enabled_config(),
    )

    assert payload["trace_persistence_status"] == (
        "trace_persistence_blocked_invalid_trace"
    )
    assert payload["persistence_records"] == {}
    _assert_safety(payload)


def test_enabled_persistence_builds_deterministic_envelope_without_live_db():
    trace_capture = _trace_capture_payload()
    original = deepcopy(trace_capture)

    first = persistence.build_shadow_sidecar_trace_persistence_payload(
        trace_capture_payload=trace_capture,
        sidecar_config=_enabled_config(),
        owner_user_id="owner_shadow",
        pipeline_run_id="pipeline_shadow",
        context_id="context_shadow",
    )
    second = persistence.build_shadow_sidecar_trace_persistence_payload(
        trace_capture_payload=trace_capture,
        sidecar_config=_enabled_config(),
        owner_user_id="owner_shadow",
        pipeline_run_id="pipeline_shadow",
        context_id="context_shadow",
    )

    assert first == second
    assert trace_capture == original
    assert first["trace_persistence_status"] == "trace_persistence_skipped_no_safe_sink"
    assert first["requires_live_database"] is False
    assert first["provider_calls_disabled_in_tests"] is True
    records = first["persistence_records"]
    assert records["agent_run_record"]["owner_user_id"] == "owner_shadow"
    assert records["agent_run_record"]["pipeline_run_id"] == "pipeline_shadow"
    assert records["agent_step_record"]["agent_name"] == (
        "Shadow Sidecar Trace Persistence"
    )
    assert records["agent_step_record"]["output_json"]["trace_capture"] == trace_capture
    assert records["trace_summary"]["summary_type"] == "agent_trace"
    assert records["trace_summary"]["run_count"] == 1
    assert records["trace_summary"]["step_count"] == 1
    assert first["source_trace_context"]["hook_status"] == (
        "hook_completed_with_fallback"
    )
    assert first["live_provider_backed_automated_agents"] == 0
    assert first["mutation_authorized_agents"] == 0
    _assert_safety(first)


def test_persistence_failure_is_non_blocking_with_injected_writer():
    def writer(_records):
        raise RuntimeError("write boom")

    payload = persistence.build_shadow_sidecar_trace_persistence_payload(
        trace_capture_payload=_trace_capture_payload(),
        sidecar_config=_enabled_config(),
        persistence_writer=writer,
    )

    assert payload["trace_persistence_status"] == (
        "trace_persistence_failed_non_blocking"
    )
    assert payload["persistence_attempted"] is True
    assert payload["writer_result"]["error_type"] == "RuntimeError"
    _assert_safety(payload)


def test_source_has_no_pipeline_api_ui_schema_or_provider_wiring():
    source = Path("src/agents/shadow_sidecar_trace_persistence.py").read_text(
        encoding="utf-8"
    )
    forbidden = [
        "src.pipeline",
        "src.app.api",
        "src.app.services",
        "agentic_review.js",
        "schema.sql",
        "connect(",
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


def test_pipeline_runtime_files_do_not_call_trace_persistence_helper():
    pipeline_sources = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(Path("src/pipeline").glob("*.py"))
    )

    assert "shadow_sidecar_trace_persistence" not in pipeline_sources
    assert "build_shadow_sidecar_trace_persistence_payload" not in pipeline_sources
