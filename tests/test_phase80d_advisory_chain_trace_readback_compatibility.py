from copy import deepcopy
import inspect

from src.agents import orchestrator_adapter_harness, workflow_registry


UNSAFE_FLAGS = [
    "auto_apply_allowed",
    "ats_submission_allowed",
    "apply_click_allowed",
    "queue_mutation_allowed",
    "ranking_mutation_allowed",
    "scoring_mutation_allowed",
    "filtering_mutation_allowed",
    "tailoring_mutation_allowed",
    "source_resume_mutation_allowed",
    "scheduler_mutation_allowed",
    "live_provider_allowed",
    "workflow_runner_live_execution_allowed",
]


def _trace_bundle():
    return orchestrator_adapter_harness.invoke_read_only_advisory_chain(
        pipeline_run_id="phase80d_run",
        owner_user_id="phase80d_owner",
        created_at_utc="2026-07-07T00:00:00+00:00",
    )["trace_ready_advisory_result"]


def _readback_payload():
    bundle = _trace_bundle()
    run = dict(bundle["run_snapshot"])
    steps = [
        {
            "agent_step_id": step["agent_step_id"],
            "agent_name": step["agent_name"],
            "agent_version": step["agent_version"],
            "status": step["status"],
            "started_at": step["started_at"],
            "completed_at": step["completed_at"],
            "latency_ms": step["latency_ms"],
            "model_provider": step["model_provider"],
            "model_name": step["model_name"],
            "input_json": deepcopy(step["input_json"]),
            "output_json": deepcopy(step["output_json"]),
            "validation_json": deepcopy(step["validation_json"]),
            "token_usage_json": deepcopy(step["token_usage_json"]),
            "cost_json": deepcopy(step["cost_json"]),
            "error": step["error"],
        }
        for step in bundle["step_summaries"]
    ]
    return {
        "pipeline_run_id": bundle["pipeline_run_id"],
        "owner_user_id": bundle["owner_user_id"],
        "agent_runs": [
            {
                "agent_run_id": run["agent_run_id"],
                "context_id": run["context_id"],
                "status": run["status"],
                "started_at": run["started_at"],
                "completed_at": run["completed_at"],
                "summary_json": deepcopy(run["summary_json"]),
                "error": run["error"],
                "steps": steps,
            }
        ],
        "counts": {
            "agent_runs": 1,
            "agent_steps": 6,
            "failed_steps": 0,
            "warning_steps": 0,
            "succeeded_steps": 0,
        },
    }


def test_valid_generic_readback_payload_is_compatible_and_ordered():
    result = orchestrator_adapter_harness.build_advisory_chain_trace_readback_compatibility(
        _readback_payload()
    )

    assert result["compatible"] is True
    assert result["run_count"] == 1
    assert result["step_count"] == 6
    assert result["expected_agent_order"] == workflow_registry.ORDERED_AGENT_KEYS
    assert result["observed_agent_order"] == workflow_registry.ORDERED_AGENT_KEYS
    assert result["missing_agents"] == []
    assert result["unexpected_agents"] == []
    assert result["reason_codes"] == []
    assert all(result["safety_flags_summary"][flag] is False for flag in UNSAFE_FLAGS)


def test_missing_run_returns_incompatible_without_side_effects():
    result = orchestrator_adapter_harness.build_advisory_chain_trace_readback_compatibility(
        {"pipeline_run_id": "phase80d_run", "owner_user_id": "phase80d_owner", "agent_runs": []}
    )

    assert result["compatible"] is False
    assert result["run_count"] == 0
    assert result["step_count"] == 0
    assert "missing_advisory_chain_run" in result["reason_codes"]
    assert result["missing_agents"] == workflow_registry.ORDERED_AGENT_KEYS
    assert result["read_only"] is True
    assert result["db_reads_performed"] is False
    assert result["db_writes_performed"] is False


def test_missing_steps_returns_incompatible():
    payload = _readback_payload()
    payload["agent_runs"][0]["steps"] = payload["agent_runs"][0]["steps"][:4]

    result = orchestrator_adapter_harness.build_advisory_chain_trace_readback_compatibility(payload)

    assert result["compatible"] is False
    assert result["step_count"] == 4
    assert "advisory_chain_step_count_mismatch" in result["reason_codes"]
    assert result["missing_agents"] == ["tailoring_decision", "operator_review"]


def test_wrong_agent_order_is_detected():
    payload = _readback_payload()
    steps = payload["agent_runs"][0]["steps"]
    steps[0], steps[1] = steps[1], steps[0]

    result = orchestrator_adapter_harness.build_advisory_chain_trace_readback_compatibility(payload)

    assert result["compatible"] is False
    assert result["observed_agent_order"][:2] == ["resume_match", "source_health"]
    assert "advisory_chain_agent_order_mismatch" in result["reason_codes"]


def test_true_safety_flag_makes_readback_incompatible():
    payload = _readback_payload()
    payload["agent_runs"][0]["steps"][2]["validation_json"]["safety_flags"][
        "auto_apply_allowed"
    ] = True

    result = orchestrator_adapter_harness.build_advisory_chain_trace_readback_compatibility(payload)

    assert result["compatible"] is False
    assert result["safety_flags_summary"]["auto_apply_allowed"] is True
    assert result["unsafe_safety_flags"] == ["auto_apply_allowed"]
    assert "advisory_chain_unsafe_safety_flags_present" in result["reason_codes"]


def test_helper_is_pure_and_does_not_call_db_or_persistence(monkeypatch):
    payload = _readback_payload()
    original = deepcopy(payload)

    def fail_if_called(*args, **kwargs):
        raise AssertionError("readback compatibility helper must be in-memory only")

    monkeypatch.setattr(orchestrator_adapter_harness, "persist_read_only_advisory_chain_trace", fail_if_called)
    monkeypatch.setattr(
        orchestrator_adapter_harness.agent_trace_store,
        "list_agent_runs_postgres_payload",
        fail_if_called,
        raising=False,
    )
    monkeypatch.setattr(
        orchestrator_adapter_harness.agent_trace_store,
        "list_agent_steps_postgres_payload",
        fail_if_called,
        raising=False,
    )

    result = orchestrator_adapter_harness.build_advisory_chain_trace_readback_compatibility(payload)

    assert payload == original
    assert result["compatible"] is True
    assert result["db_reads_performed"] is False
    assert result["db_writes_performed"] is False


def test_no_api_ui_pipeline_or_application_mutation_metadata_is_exposed():
    result = orchestrator_adapter_harness.build_advisory_chain_trace_readback_compatibility(
        _readback_payload()
    )

    for flag in [
        "api_changed",
        "ui_changed",
        "pipeline_changed",
        "did_call_llm",
        "did_call_live_provider",
        "did_call_workflow_runner",
        "did_call_live_workflow_runner",
        "did_change_queue",
        "did_change_scoring",
        "did_change_ranking",
        "did_change_filtering",
        "did_change_tailoring",
        "did_mutate_source_resume",
        "did_execute_scheduler",
        "did_click_apply",
        "did_execute_application",
        "did_submit_application",
        "did_send_recruiter_message",
        "did_mark_applied",
    ]:
        assert result[flag] is False


def test_helper_source_has_no_runtime_or_io_calls():
    source = inspect.getsource(
        orchestrator_adapter_harness.build_advisory_chain_trace_readback_compatibility
    )

    for forbidden in [
        "agent_trace_payload(",
        "persist_read_only_advisory_chain_trace(",
        "execute(",
        "subprocess",
        "open(",
        "write(",
        "workflow_runner",
        "run_chat_completion",
        "submit_application",
        "auto_" + "apply",
    ]:
        assert forbidden not in source
