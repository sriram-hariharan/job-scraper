from copy import deepcopy
from pathlib import Path

from src.agents.agent_state import (
    JobApplicationContext,
    build_agent_run_snapshot,
    build_agent_step_snapshot,
)
from src.storage.agent_state import store


def _context():
    return JobApplicationContext(
        approval_request_id="approval_1",
        job_id="job_1",
        candidate_key="candidate_1",
        role_family="software_engineering",
        run_mode="dry_run",
        observed_at_utc="2026-06-12T10:00:00Z",
        metadata={"source": "unit_test"},
    )


def _run_snapshot():
    return build_agent_run_snapshot(
        context=_context(),
        agent_name="review_agent",
        observed_at_utc="2026-06-12T10:01:00Z",
        run_status="ready",
        metadata={"attempt": 1},
    )


def _step_snapshot():
    return build_agent_step_snapshot(
        context=_context(),
        agent_name="review_agent",
        step_name="score_job",
        step_index=1,
        observed_at_utc="2026-06-12T10:02:00Z",
        step_status="completed",
        input_summary={"job_id": "job_1"},
        output_summary={"decision": "review"},
        reason_codes=["deterministic"],
        metadata={"phase": "181A"},
    )


def _assert_storage_safety_flags_false(payload):
    for key, expected in store.safety_flags().items():
        assert payload[key] is expected


def test_schema_file_contains_agent_runs_and_agent_steps_only():
    schema = Path("src/storage/agent_state/schema.sql").read_text()

    assert "CREATE TABLE IF NOT EXISTS agent_runs" in schema
    assert "CREATE TABLE IF NOT EXISTS agent_steps" in schema
    assert schema.count("CREATE TABLE IF NOT EXISTS") == 2
    assert "agentic_approval_requests" not in schema
    assert "agentic_approval_audit_events" not in schema
    assert "ALTER TABLE" not in schema
    assert "\nINSERT INTO" not in schema
    assert "\nUPDATE " not in schema
    assert "\nDELETE FROM" not in schema
    assert "CREATE INDEX IF NOT EXISTS" in schema


def test_schema_text_helper_is_deterministic_and_scoped_to_agent_state():
    first = store.agent_state_schema_sql_text()
    second = store.agent_state_schema_sql_text()

    assert first == second
    assert "CREATE TABLE IF NOT EXISTS agent_runs" in first
    assert "CREATE TABLE IF NOT EXISTS agent_steps" in first
    assert "agentic_approval" not in first
    assert store.agent_state_table_specs() == {
        "agent_runs": {
            "primary_key": ["agent_run_id"],
            "unique": ["agent_run_key"],
            "columns": [
                "agent_run_id",
                "agent_run_key",
                "context_key",
                "approval_request_id",
                "job_id",
                "candidate_key",
                "agent_name",
                "run_status",
                "observed_at_utc",
                "metadata_json",
                "safety_flags_json",
            ],
        },
        "agent_steps": {
            "primary_key": ["agent_step_id"],
            "unique": ["agent_step_key"],
            "foreign_keys": {"agent_run_id": "agent_runs.agent_run_id"},
            "columns": [
                "agent_step_id",
                "agent_step_key",
                "agent_run_id",
                "context_key",
                "approval_request_id",
                "job_id",
                "candidate_key",
                "agent_name",
                "step_name",
                "step_index",
                "step_status",
                "observed_at_utc",
                "input_summary_json",
                "output_summary_json",
                "reason_codes_json",
                "metadata_json",
                "safety_flags_json",
            ],
        },
    }


def test_prepare_agent_run_upsert_is_deterministic_and_does_not_mutate_input():
    snapshot = _run_snapshot()
    original = deepcopy(snapshot)

    first = store.prepare_agent_run_upsert(snapshot)
    second = store.prepare_agent_run_upsert(snapshot)

    assert snapshot == original
    assert first == second
    assert first["operation"] == "prepare_agent_run_upsert"
    assert first["table"] == "agent_runs"
    assert "INSERT INTO agent_runs" in first["sql"]
    assert "ON CONFLICT (agent_run_key)" in first["sql"]
    assert "RETURNING agent_run_id" in first["sql"]
    assert first["params"] == (
        snapshot["agent_run_id"],
        snapshot["agent_run_key"],
        snapshot["context_key"],
        "approval_1",
        "job_1",
        "candidate_1",
        "review_agent",
        "ready",
        "2026-06-12T10:01:00Z",
        '{"attempt":1}',
        (
            '{"did_commit_transaction":false,"did_create_connection":false,'
            '"did_execute_application":false,"did_execute_reporting_job":false,'
            '"did_execute_scheduler":false,"did_export_files":false,'
            '"did_run_migration":false,"did_schedule_background_work":false,'
            '"did_submit_application":false,"migration_runner_added":false}'
        ),
    )
    assert first["snapshot"] == snapshot
    assert first["snapshot"] is not snapshot
    _assert_storage_safety_flags_false(first)


def test_prepare_agent_step_upsert_is_deterministic_and_does_not_mutate_input():
    snapshot = _step_snapshot()
    original = deepcopy(snapshot)

    first = store.prepare_agent_step_upsert(snapshot)
    second = store.prepare_agent_step_upsert(snapshot)

    assert snapshot == original
    assert first == second
    assert first["operation"] == "prepare_agent_step_upsert"
    assert first["table"] == "agent_steps"
    assert "INSERT INTO agent_steps" in first["sql"]
    assert "ON CONFLICT (agent_step_key)" in first["sql"]
    assert "RETURNING agent_step_id" in first["sql"]
    assert first["params"] == (
        snapshot["agent_step_id"],
        snapshot["agent_step_key"],
        snapshot["agent_run_id"],
        snapshot["context_key"],
        "approval_1",
        "job_1",
        "candidate_1",
        "review_agent",
        "score_job",
        1,
        "completed",
        "2026-06-12T10:02:00Z",
        '{"job_id":"job_1"}',
        '{"decision":"review"}',
        '["deterministic"]',
        '{"phase":"181A"}',
        (
            '{"did_commit_transaction":false,"did_create_connection":false,'
            '"did_execute_application":false,"did_execute_reporting_job":false,'
            '"did_execute_scheduler":false,"did_export_files":false,'
            '"did_run_migration":false,"did_schedule_background_work":false,'
            '"did_submit_application":false,"migration_runner_added":false}'
        ),
    )
    assert first["snapshot"] == snapshot
    assert first["snapshot"] is not snapshot
    _assert_storage_safety_flags_false(first)


def test_store_module_has_no_connection_commit_migration_or_runtime_markers():
    source = Path("src/storage/agent_state/store.py").read_text()

    forbidden_tokens = [
        "connect(",
        ".commit(",
        "commit_transaction(",
        "run_migration(",
        "execute_migration(",
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
        "agentic_approval_requests",
        "agentic_approval_audit_events",
        "src.app.api",
        "agentic_review.js",
        "workflow_runner",
        "application_execution_queue",
    ]
    for token in forbidden_tokens:
        assert token not in source
