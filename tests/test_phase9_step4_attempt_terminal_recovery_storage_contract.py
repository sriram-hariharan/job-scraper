from copy import deepcopy
from pathlib import Path

import pytest

from src.agents import evidence_chain_langgraph_harness as harness
from src.storage.durable_orchestration import store


SCHEMA = Path("src/storage/durable_orchestration/schema.sql")
STORE = Path("src/storage/durable_orchestration/store.py")
NOW = "2026-07-25T12:00:00Z"


def _graph_run(status="resume_consumed"):
    return {
        "graph_invocation_id": "graph-1",
        "graph_engine": harness.CHECKPOINT_GRAPH_ENGINE,
        "graph_state_schema_version": harness.GRAPH_STATE_SCHEMA_VERSION,
        "owner_user_id": "owner-1",
        "pipeline_run_id": "run-1",
        "context_id": "context-1",
        "job_id": "job-1",
        "job_index": 0,
        "selected_resume_id": "resume-1",
        "run_status": status,
        "current_checkpoint_id": "checkpoint-1",
        "lock_version": 4,
        "created_at": NOW,
        "updated_at": NOW,
        "terminal_at": None,
        "purge_after": None,
    }


def _attempt(graph=None, *, resume_invocation_id="resume-invocation:1"):
    return store.prepare_node_attempt_row(
        graph or _graph_run(),
        input_checkpoint_id="checkpoint-1",
        node_key="finalize",
        attempt_number=1,
        input_digest="a" * 64,
        created_at=NOW,
        resume_invocation_id=resume_invocation_id,
    )


def _consumption():
    row = {key: "" for key in store._CONSUMPTION_COLUMNS}
    row.update({
        "consumption_id": "consumption-1",
        "authorization_id": "authorization-1",
        "decision_id": "decision-1",
        "graph_invocation_id": "graph-1",
        "checkpoint_id": "checkpoint-1",
        "interrupt_request_id": "interrupt-1",
        "owner_user_id": "owner-1",
        "pipeline_run_id": "run-1",
        "context_id": "context-1",
        "job_id": "job-1",
        "job_index": 0,
        "selected_resume_id": "resume-1",
        "resume_invocation_id": "resume-invocation:1",
        "consumer_instance_id": "worker-1",
        "claimed_at": NOW,
        "claim_status": "claimed",
        "expected_authorization_version": 0,
        "application_authorization": False,
    })
    return row


def _event(event_type, *, attempt=None, terminal=None, consumption=None):
    references = {
        "checkpoint_id": "checkpoint-1",
        "node_attempt_id": (attempt or {}).get("node_attempt_id"),
        "terminal_result_id": (terminal or {}).get("terminal_result_id"),
        "consumption_id": (consumption or {}).get("consumption_id"),
    }
    return store.prepare_lifecycle_event_row(
        _graph_run(),
        event_type=event_type,
        aggregate_type="graph_run",
        aggregate_id="graph-1",
        event_sequence=1,
        event_payload={"status": event_type},
        event_timestamp=NOW,
        references=references,
    )


def _terminal(status="completed", metadata=None):
    return store.prepare_terminal_result_row(
        _graph_run("resumed"),
        terminal_checkpoint_id="checkpoint-1",
        checkpoint_schema_version=harness.CHECKPOINT_SCHEMA_VERSION,
        terminal_status=status,
        result_metadata=metadata or {"result": "read-only"},
        completed_at=NOW,
        failure_code="node_failed" if status == "failed" else "",
    )


def test_exact_three_new_schema_objects_and_constraints():
    schema = SCHEMA.read_text(encoding="utf-8")
    assert schema.count("CREATE TABLE IF NOT EXISTS") == 9
    for table in (
        "orchestration_node_attempts",
        "orchestration_terminal_results",
        "orchestration_lifecycle_events",
    ):
        assert schema.count(f"CREATE TABLE IF NOT EXISTS {table}") == 1
    assert (
        "UNIQUE (graph_invocation_id, input_checkpoint_id, node_key, attempt_number)"
        in schema
    )
    assert "WHERE attempt_status = 'succeeded'" in schema
    assert "graph_invocation_id TEXT NOT NULL UNIQUE" in schema
    assert "UNIQUE (graph_invocation_id, aggregate_type, aggregate_id, event_sequence)" in schema
    assert "application_authorization = FALSE" in schema
    assert "mutation_authorization = FALSE" in schema


def test_attempt_output_and_status_constraints_are_fail_closed():
    schema = SCHEMA.read_text(encoding="utf-8")
    assert (
        "attempt_status IN ('pending', 'claimed', 'succeeded', 'failed', 'abandoned')"
        in schema
    )
    assert (
        "attempt_status = 'succeeded' AND output_checkpoint_id IS NOT NULL "
        "AND output_digest IS NOT NULL"
    ) in schema
    assert (
        "attempt_status <> 'succeeded' AND output_checkpoint_id IS NULL "
        "AND output_digest IS NULL"
    ) in schema


def test_node_attempt_identity_is_deterministic_and_inputs_are_not_mutated():
    graph = _graph_run()
    original = deepcopy(graph)
    first, second = _attempt(graph), _attempt(graph)
    assert first == second
    assert first["node_attempt_id"].startswith("node-attempt:")
    assert first["attempt_status"] == "pending"
    assert first["application_authorization"] is False
    assert first["mutation_authorization"] is False
    assert graph == original
    with pytest.raises(ValueError, match="node_key"):
        store.prepare_node_attempt_row(
            graph, input_checkpoint_id="checkpoint-1", node_key="apply",
            attempt_number=1, input_digest="a" * 64, created_at=NOW,
        )


def test_terminal_identity_and_digest_are_deterministic_and_mismatch_rejected():
    first, second = _terminal(), _terminal()
    assert first == second
    assert first["terminal_result_id"].startswith("terminal-result:")
    assert first["application_authorization"] is False
    assert store.require_idempotent_terminal_result(first, second) == second
    conflicting = _terminal(metadata={"result": "different"})
    with pytest.raises(ValueError, match="digest_conflict"):
        store.require_idempotent_terminal_result(first, conflicting)


def test_lifecycle_event_is_deterministic_bounded_append_only_and_secret_free():
    attempt = _attempt()
    first = _event("node_attempt_claimed", attempt=attempt)
    second = _event("node_attempt_claimed", attempt=attempt)
    assert first == second
    assert first["event_id"].startswith("lifecycle-event:")
    assert first["projection_status"] == "pending"
    schema = SCHEMA.read_text(encoding="utf-8")
    assert "octet_length(event_payload_json::text) <= 262144" in schema
    assert "UPDATE orchestration_lifecycle_events" not in schema
    with pytest.raises(ValueError, match="prohibited"):
        store.prepare_lifecycle_event_row(
            _graph_run(), event_type="node_attempt_failed",
            aggregate_type="node_attempt", aggregate_id="attempt-1",
            event_sequence=2, event_payload={"api_key": "secret"},
            event_timestamp=NOW,
        )


def test_attempt_claim_success_failure_and_abandonment_have_cas_and_atomic_events():
    attempt = _attempt()
    claim = store.prepare_node_attempt_claim(
        attempt, _event("node_attempt_claimed", attempt=attempt),
        lease_owner_id="worker-1", lease_acquired_at=NOW,
        lease_expires_at="2026-07-25T12:05:00Z",
        expected_lock_version=0, expected_run_status="resumed",
        expected_run_lock_version=4,
    )
    success = store.prepare_node_attempt_success(
        attempt, _event("node_attempt_succeeded", attempt=attempt),
        output_checkpoint_id="checkpoint-2", output_digest="b" * 64,
        completed_at=NOW, duration_ms=10, lease_owner_id="worker-1",
        expected_lock_version=1, expected_run_status="resumed",
        expected_run_lock_version=4,
    )
    failure = store.prepare_node_attempt_failure(
        attempt, _event("node_attempt_failed", attempt=attempt),
        error_code="node_failed", error_detail="redacted",
        completed_at=NOW, lease_owner_id="worker-1",
        expected_lock_version=1, expected_run_status="resumed",
        expected_run_lock_version=4,
    )
    abandoned = store.prepare_expired_attempt_abandonment(
        attempt, _event("node_attempt_failed", attempt=attempt),
        recovery_at=NOW, expected_lock_version=1,
        expected_run_status="resumed", expected_run_lock_version=4,
    )
    for command in (claim, success, failure, abandoned):
        assert "owner_user_id = %(attempt_owner_user_id)s" in command["sql"]
        assert "lock_version = %(expected_lock_version)s" in command["sql"]
        assert "lock_version = %(expected_run_lock_version)s" in command["sql"]
        assert "INSERT INTO orchestration_lifecycle_events" in command["sql"]
        assert command["sql_executed"] is False
    assert "lease_owner_id = %(lease_owner_id)s" in success["sql"]
    assert "current_checkpoint_id = %(output_checkpoint_id)s" in success["sql"]
    assert "output_checkpoint_id" not in failure["params"]
    assert "lease_expires_at < %(recovery_at)s" in abandoned["sql"]


def test_recovery_claim_requires_same_consumption_resume_and_is_idempotent_only_exactly():
    graph, consumption, attempt = _graph_run(), _consumption(), _attempt()
    normalized = store.prepare_recovery_claim_inputs(
        consumption, graph, attempt
    )
    assert normalized["node_attempt"]["resume_invocation_id"] == (
        consumption["resume_invocation_id"]
    )
    conflicting = deepcopy(attempt)
    conflicting["resume_invocation_id"] = "resume-invocation:other"
    with pytest.raises(ValueError, match="resume_identity_mismatch"):
        store.prepare_recovery_claim_inputs(consumption, graph, conflicting)
    command = store.prepare_resume_recovery_claim(
        consumption, graph, attempt,
        _event(
            "recovery_claim_recorded",
            attempt=attempt,
            consumption=consumption,
        ),
        expected_run_lock_version=4,
    )
    assert "run_status = 'resume_consumed'" in command["sql"]
    assert "SET run_status = 'resumed'" in command["sql"]
    assert "existing.resume_invocation_id = %(consumption_resume_invocation_id)s" in command["sql"]
    assert "ON CONFLICT" in command["sql"]
    assert "INSERT INTO orchestration_lifecycle_events" in command["sql"]


def test_terminalization_is_atomic_cas_idempotent_and_cannot_reopen_terminal_state():
    terminal = _terminal()
    command = store.prepare_terminalization(
        _graph_run("resumed"), terminal,
        _event("terminal_result_recorded", terminal=terminal),
        expected_run_status="resumed", expected_run_lock_version=4,
    )
    assert "run_status NOT IN ('completed', 'failed', 'cancelled')" in command["sql"]
    assert "ON CONFLICT (graph_invocation_id) DO NOTHING" in command["sql"]
    assert "existing.result_digest = %(terminal_result_digest)s" in command["sql"]
    assert "terminal_at = %(terminal_completed_at)s" in command["sql"]
    assert "INSERT INTO orchestration_lifecycle_events" in command["sql"]
    with pytest.raises(ValueError, match="expected_status"):
        store.prepare_terminalization(
            _graph_run("completed"), terminal,
            _event("terminal_result_recorded", terminal=terminal),
            expected_run_status="completed", expected_run_lock_version=4,
        )


def test_owner_scoped_reads_have_graph_scope_and_no_global_work_queue():
    reads = (
        store.prepare_active_node_attempt_read(
            owner_user_id="owner-1", graph_invocation_id="graph-1"),
        store.prepare_latest_successful_attempt_read(
            owner_user_id="owner-1", graph_invocation_id="graph-1",
            input_checkpoint_id="checkpoint-1", node_key="finalize"),
        store.prepare_recoverable_expired_attempt_read(
            owner_user_id="owner-1", graph_invocation_id="graph-1",
            recovery_at=NOW),
        store.prepare_terminal_result_read(
            owner_user_id="owner-1", graph_invocation_id="graph-1"),
        store.prepare_unprojected_lifecycle_events_read(
            owner_user_id="owner-1", graph_invocation_id="graph-1"),
        store.prepare_restart_reconciliation_read(
            owner_user_id="owner-1", graph_invocation_id="graph-1"),
    )
    for command in reads:
        assert command["read_only"] is True
        assert "owner_user_id = %(owner_user_id)s" in command["sql"]
        assert "graph_invocation_id = %(graph_invocation_id)s" in command["sql"]
        assert command["params"]["owner_user_id"] == "owner-1"
        assert command["params"]["graph_invocation_id"] == "graph-1"


def test_preparation_is_static_and_has_no_execution_or_runtime_integration():
    source = STORE.read_text(encoding="utf-8")
    for marker in (
        "import psycopg", "import sqlalchemy", "from langgraph", ".execute(",
        ".cursor(", ".commit(", "src.app", "src.collector", "scheduler",
        "src.storage.application_actions",
    ):
        assert marker not in source
    assert all(value is False for value in store.safety_declarations().values())
