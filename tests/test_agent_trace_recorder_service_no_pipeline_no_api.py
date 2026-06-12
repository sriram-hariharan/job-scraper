from copy import deepcopy
import importlib
from pathlib import Path

from src.agents.agent_state import (
    JobApplicationContext,
    build_agent_run_snapshot,
    build_agent_step_snapshot,
)
from src.agents import trace


class FakeCursor:
    def __init__(self):
        self.calls = []
        self.commit_calls = 0

    def execute(self, sql, params):
        self.calls.append((sql, params))

    def commit(self):
        self.commit_calls += 1


def _context():
    return JobApplicationContext(
        approval_request_id="approval_184a",
        job_id="job_184a",
        candidate_key="candidate_184a",
        role_family="software_engineering",
        run_mode="dry_run",
        observed_at_utc="2026-06-12T12:00:00Z",
        metadata={"source": "unit_test"},
    )


def _run_snapshot():
    return build_agent_run_snapshot(
        context=_context(),
        agent_name="trace_agent",
        observed_at_utc="2026-06-12T12:01:00Z",
        run_status="ready",
        metadata={"phase": "184A"},
    )


def _step_snapshot(run_id=None):
    return build_agent_step_snapshot(
        context=_context(),
        agent_name="trace_agent",
        step_name="prepare_trace",
        step_index=1,
        observed_at_utc="2026-06-12T12:02:00Z",
        step_status="ready",
        agent_run_id=run_id or _run_snapshot()["agent_run_id"],
        input_summary={"job_id": "job_184a"},
        output_summary={"result": "not_executed"},
        reason_codes=["trace_only"],
        metadata={"phase": "184A"},
    )


def _assert_safety_flags_false(payload):
    assert payload["did_create_connection"] is False
    assert payload["did_commit_transaction"] is False
    assert payload["did_run_migration"] is False
    assert payload["did_schedule_background_work"] is False
    assert payload["did_execute_scheduler"] is False
    assert payload["did_execute_reporting_job"] is False
    assert payload["did_export_files"] is False
    assert payload["did_execute_application"] is False
    assert payload["did_submit_application"] is False
    assert payload["api_route_added"] is False
    assert payload["ui_action_added"] is False
    assert payload["pipeline_wiring_added"] is False


def test_import_has_no_side_effects():
    module = importlib.reload(trace)
    payload = module.trace_recorder_safety_flags()

    _assert_safety_flags_false(payload)


def test_trace_payload_creation_is_deterministic_and_does_not_mutate_inputs():
    run_snapshot = _run_snapshot()
    step_snapshot = _step_snapshot(run_snapshot["agent_run_id"])
    original_run = deepcopy(run_snapshot)
    original_step = deepcopy(step_snapshot)
    steps = [step_snapshot]
    original_steps = deepcopy(steps)

    first = trace.build_agent_trace_recording_payload(
        run_snapshot=run_snapshot,
        step_snapshots=steps,
    )
    second = trace.build_agent_trace_recording_payload(
        run_snapshot=run_snapshot,
        step_snapshots=steps,
    )

    assert run_snapshot == original_run
    assert step_snapshot == original_step
    assert steps == original_steps
    assert first == second
    assert first["operation"] == "build_agent_trace_recording_payload"
    assert first["run_count"] == 1
    assert first["step_count"] == 1
    assert first["record_count"] == 2
    assert first["records"][0]["record_type"] == "agent_run"
    assert first["records"][1]["record_type"] == "agent_step"
    assert first["records"][0]["prepared_statement"]["table"] == "agent_runs"
    assert first["records"][1]["prepared_statement"]["table"] == "agent_steps"
    assert first["records"][0]["snapshot"] is not run_snapshot
    assert first["records"][1]["snapshot"] is not step_snapshot
    _assert_safety_flags_false(first)


def test_fake_smoke_trace_has_exactly_one_run_and_one_step():
    payload = trace.build_fake_smoke_trace_payload()

    assert payload["run_count"] == 1
    assert payload["step_count"] == 1
    assert payload["record_count"] == 2
    assert [record["record_type"] for record in payload["records"]] == [
        "agent_run",
        "agent_step",
    ]
    assert payload["records"][1]["snapshot"]["agent_run_id"] == (
        payload["records"][0]["snapshot"]["agent_run_id"]
    )
    _assert_safety_flags_false(payload)


def test_execution_requires_injected_cursor_or_callback():
    payload = trace.build_fake_smoke_trace_payload()

    for kwargs in [{}, {"cursor": FakeCursor(), "execute_callback": lambda op: op}]:
        try:
            trace.execute_agent_trace_recording(payload, **kwargs)
        except ValueError as exc:
            assert "exactly one" in str(exc)
        else:
            raise AssertionError("execution should require exactly one injection path")


def test_fake_cursor_receives_expected_operations_only_when_explicitly_invoked():
    payload = trace.build_fake_smoke_trace_payload()
    cursor = FakeCursor()

    assert cursor.calls == []
    result = trace.execute_agent_trace_recording(payload, cursor=cursor)

    assert len(cursor.calls) == 2
    assert "INSERT INTO agent_runs" in cursor.calls[0][0]
    assert "INSERT INTO agent_steps" in cursor.calls[1][0]
    assert cursor.commit_calls == 0
    assert result["executed_record_count"] == 2
    assert result["executed_operations"] == [
        {"record_type": "agent_run", "table": "agent_runs"},
        {"record_type": "agent_step", "table": "agent_steps"},
    ]
    _assert_safety_flags_false(result)


def test_execution_callback_receives_deep_copied_operations():
    payload = trace.build_fake_smoke_trace_payload()
    operations = []

    result = trace.execute_agent_trace_recording(
        payload,
        execute_callback=lambda operation: operations.append(operation),
    )
    operations[0]["table"] = "mutated"

    assert result["executed_operations"][0]["table"] == "agent_runs"
    assert len(operations) == 2
    _assert_safety_flags_false(result)


def test_trace_recorder_source_has_no_forbidden_runtime_markers():
    source = Path("src/agents/trace.py").read_text()

    forbidden_tokens = [
        "connect(",
        ".commit(",
        "commit_transaction(",
        "run_migration(",
        "FileResponse",
        "StreamingResponse",
        "open(",
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
        "metrics_emitter",
        "logging_emitter",
        "audit_writer",
        "datetime.",
        "utcnow",
        "now(",
        "uuid",
        "random",
        "src.app.api",
        "agentic_review.js",
        "workflow_runner",
        "application_execution_queue",
    ]
    for token in forbidden_tokens:
        assert token not in source
