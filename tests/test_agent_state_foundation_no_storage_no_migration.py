from copy import deepcopy
from pathlib import Path

from src.agents.agent_state import (
    JobApplicationContext,
    append_trace_step,
    build_agent_run_snapshot,
    build_agent_step_snapshot,
    job_application_context_payload,
    safety_flags,
)


def _context() -> JobApplicationContext:
    return JobApplicationContext(
        approval_request_id="approval_1",
        job_id="job_1",
        candidate_key="candidate_1",
        role_family="software_engineering",
        run_mode="dry_run",
        observed_at_utc="2026-06-12T10:00:00Z",
        metadata={"source": "unit_test", "nested": {"rank": 1}},
    )


def _assert_safety_flags_false(payload):
    for key, expected in safety_flags().items():
        assert payload[key] is expected


def test_job_application_context_serializes_to_plain_dict_deterministically():
    first = _context().to_dict()
    second = _context().to_dict()

    assert first == second
    assert first == {
        "context_id": "",
        "context_key": (
            "job_application_context:approval_1:job_1:candidate_1:dry_run"
        ),
        "approval_request_id": "approval_1",
        "job_id": "job_1",
        "candidate_key": "candidate_1",
        "role_family": "software_engineering",
        "run_mode": "dry_run",
        "observed_at_utc": "2026-06-12T10:00:00Z",
        "metadata": {"source": "unit_test", "nested": {"rank": 1}},
        **safety_flags(),
    }
    assert isinstance(first, dict)
    _assert_safety_flags_false(first)


def test_job_application_context_round_trips_from_dict_and_copies_metadata():
    payload = job_application_context_payload(
        approval_request_id="approval_2",
        job_id="job_2",
        candidate_key="candidate_2",
        role_family="data",
        run_mode="review",
        observed_at_utc="2026-06-12T11:00:00Z",
        metadata={"labels": ["safe", "pure"]},
        context_id="ctx_explicit",
    )
    restored = JobApplicationContext.from_dict(payload)

    assert restored.to_dict() == payload
    payload["metadata"]["labels"].append("mutated")
    assert restored.to_dict()["metadata"]["labels"] == ["safe", "pure"]


def test_agent_run_snapshot_is_deterministic_and_has_disabled_safety_flags():
    context = _context()

    first = build_agent_run_snapshot(
        context=context,
        agent_name="review_agent",
        observed_at_utc="2026-06-12T10:01:00Z",
        run_status="ready",
        metadata={"attempt": 1},
    )
    second = build_agent_run_snapshot(
        context=context.to_dict(),
        agent_name="review_agent",
        observed_at_utc="2026-06-12T10:01:00Z",
        run_status="ready",
        metadata={"attempt": 1},
    )

    assert first == second
    assert first["agent_run_id"] == (
        "agent_run:job_application_context:approval_1:job_1:candidate_1:dry_run:"
        "review_agent:2026-06-12T10:01:00Z"
    )
    assert first["agent_run_key"] == first["agent_run_id"]
    assert first["context_key"] == context.context_key
    assert first["run_status"] == "ready"
    assert first["metadata"] == {"attempt": 1}
    _assert_safety_flags_false(first)


def test_agent_step_snapshot_is_deterministic_and_serializable():
    context = _context()

    first = build_agent_step_snapshot(
        context=context,
        agent_name="review_agent",
        step_name="score_job",
        step_index=1,
        observed_at_utc="2026-06-12T10:02:00Z",
        step_status="completed",
        input_summary={"job_id": "job_1"},
        output_summary={"decision": "review"},
        reason_codes=["deterministic"],
        metadata={"phase": "179A"},
    )
    second = build_agent_step_snapshot(
        context=context,
        agent_name="review_agent",
        step_name="score_job",
        step_index=1,
        observed_at_utc="2026-06-12T10:02:00Z",
        step_status="completed",
        input_summary={"job_id": "job_1"},
        output_summary={"decision": "review"},
        reason_codes=["deterministic"],
        metadata={"phase": "179A"},
    )

    assert first == second
    assert first["agent_step_id"] == (
        "agent_step:job_application_context:approval_1:job_1:candidate_1:dry_run:"
        "review_agent:score_job:1"
    )
    assert first["agent_run_id"] == (
        "agent_run:job_application_context:approval_1:job_1:candidate_1:dry_run:"
        "review_agent:2026-06-12T10:02:00Z"
    )
    assert first["input_summary"] == {"job_id": "job_1"}
    assert first["output_summary"] == {"decision": "review"}
    assert first["reason_codes"] == ["deterministic"]
    _assert_safety_flags_false(first)


def test_append_trace_step_returns_new_payload_without_mutating_input():
    original = {
        "context_key": _context().context_key,
        "trace_steps": [{"agent_step_id": "existing_step"}],
    }
    original_copy = deepcopy(original)
    step = build_agent_step_snapshot(
        context=_context(),
        agent_name="review_agent",
        step_name="score_job",
        step_index=2,
        observed_at_utc="2026-06-12T10:03:00Z",
    )

    updated = append_trace_step(original, step)

    assert original == original_copy
    assert updated is not original
    assert updated["trace_steps"] is not original["trace_steps"]
    assert updated["trace_steps"] == [
        {"agent_step_id": "existing_step"},
        step,
    ]
    _assert_safety_flags_false(updated)


def test_agent_state_module_has_no_storage_migration_runtime_side_effect_markers():
    source = Path("src/agents/agent_state.py").read_text()

    forbidden_tokens = [
        "FileResponse",
        "StreamingResponse",
        "open(",
        ".write(",
        "write_text",
        "write_bytes",
        "send_file",
        "subprocess",
        "background_tasks.add_task",
        "Thread",
        "Process",
        "scheduler_execution(",
        "reporting_job_execution(",
        "application_execution(",
        "application_submission(",
        "export_writer",
        "persistent_storage_writer",
        "metrics_emitter",
        "logging_emitter",
        "audit_writer",
        "datetime.",
        "utcnow",
        "now(",
        "uuid",
        "random",
        "src.storage",
        "application_execution_queue",
        "workflow_runner",
        "schema.sql",
        "migrations",
    ]
    for token in forbidden_tokens:
        assert token not in source
