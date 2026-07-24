from copy import deepcopy
from pathlib import Path

import pytest

from src.storage.durable_orchestration import store


SCHEMA = Path("src/storage/durable_orchestration/schema.sql")
NOW = "2026-07-24T12:00:00Z"


def _interrupt_row():
    row = {key: "" for key in store._INTERRUPT_COLUMNS}
    row.update({
        "interrupt_request_id": "interrupt-1",
        "graph_invocation_id": "graph-1",
        "checkpoint_id": "checkpoint-1",
        "interrupt_request_schema_version": "operator-review-interrupt-request-v1",
        "checkpoint_schema_version": "evidence-chain-checkpoint-envelope-v1",
        "graph_state_schema_version": "evidence-chain-graph-state-v1",
        "owner_user_id": "owner-1",
        "pipeline_run_id": "run-1",
        "context_id": "context-1",
        "job_id": "job-1",
        "job_index": 0,
        "selected_resume_id": "resume-1",
        "node_key": "operator_review",
        "safe_next_node_key": "finalize",
        "operator_review_artifact_type": "operator_review_tailoring_evidence",
        "operator_review_artifact_version": "v1",
        "operator_review_artifact_digest": "a" * 64,
        "allowed_decision_values_json": [
            "continue_read_only", "needs_revision", "cancel",
        ],
        "interrupt_request_json": {},
        "interrupt_status": "awaiting_decision",
        "lock_version": 0,
        "read_only": True,
        "diagnostic_only": True,
        "application_authorization": False,
        "resume_authorization": False,
        "created_at": NOW,
        "expires_at": None,
        "resolved_at": None,
    })
    return row


def _decision(value="continue_read_only"):
    return store.prepare_human_decision_row(
        _interrupt_row(), decision_value=value, actor_id="actor-1",
        client_idempotency_key="client-key-1",
        expected_interrupt_version=0, expected_run_lock_version=1,
        created_at=NOW, reason="reviewed",
    )


def _authorization():
    return store.prepare_resume_authorization_row(
        _decision(), authorization_token_hash="b" * 64,
        created_at=NOW, expires_at="2026-07-24T13:00:00Z",
    )


def test_exact_new_schema_tables_constraints_and_statuses():
    schema = SCHEMA.read_text(encoding="utf-8")
    for table in (
        "orchestration_human_decisions",
        "orchestration_resume_authorizations",
        "orchestration_resume_consumptions",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in schema
    assert schema.count("CREATE TABLE IF NOT EXISTS") == 9
    for table in (
        "orchestration_node_attempts",
        "orchestration_terminal_results",
        "orchestration_lifecycle_events",
    ):
        assert f"CREATE TABLE IF NOT EXISTS {table}" in schema
    assert "UNIQUE (interrupt_request_id, client_idempotency_key)" in schema
    assert "WHERE decision_record_status = 'recorded'" in schema
    assert "decision_id TEXT NOT NULL UNIQUE" in schema
    assert "authorization_id TEXT NOT NULL UNIQUE" in schema
    assert "decision_value IN ('continue_read_only', 'needs_revision', 'cancel')" in schema
    assert "authorization_status IN ('authorized', 'consumed', 'expired', 'revoked')" in schema
    assert "claim_status IN ('claimed', 'reconciled', 'failed')" in schema


def test_authorization_schema_is_read_only_hash_only_and_negative_for_mutation():
    schema = SCHEMA.read_text(encoding="utf-8")
    assert "authorization_token_hash TEXT NOT NULL" in schema
    assert "raw_token" not in schema
    assert "safe_next_node_key = 'finalize'" in schema
    for field in (
        "application_authorization",
        "resume_text_mutation_authorization",
        "queue_mutation_authorization",
        "operator_state_mutation_authorization",
    ):
        assert f"{field} BOOLEAN NOT NULL DEFAULT FALSE" in schema


def test_decision_identity_is_deterministic_timestamp_independent_and_bound():
    first = _decision()
    second = _decision()
    later = store.prepare_human_decision_row(
        _interrupt_row(), decision_value="continue_read_only",
        actor_id="actor-1", client_idempotency_key="client-key-1",
        expected_interrupt_version=0, expected_run_lock_version=1,
        created_at="2030-01-01T00:00:00Z", reason="reviewed",
    )
    assert first == second
    assert first["decision_id"] == later["decision_id"]
    assert first["checkpoint_id"] == "checkpoint-1"
    assert first["operator_review_artifact_digest"] == "a" * 64
    assert first["application_authorization"] is False


def test_decision_vocabulary_versions_and_reason_fail_closed():
    with pytest.raises(ValueError, match="decision_value"):
        _decision("apply")
    with pytest.raises(ValueError, match="expected_interrupt_version"):
        store.prepare_human_decision_row(
            _interrupt_row(), decision_value="cancel", actor_id="actor",
            client_idempotency_key="key", expected_interrupt_version=-1,
            expected_run_lock_version=0, created_at=NOW,
        )
    with pytest.raises(ValueError, match="too_large"):
        store.prepare_human_decision_row(
            _interrupt_row(), decision_value="cancel", actor_id="actor",
            client_idempotency_key="key", expected_interrupt_version=0,
            expected_run_lock_version=0, created_at=NOW, reason="x" * 4097,
        )


def test_authorization_is_continue_only_deterministic_and_rejects_raw_tokens():
    first, second = _authorization(), _authorization()
    assert first == second
    assert first["safe_next_node_key"] == "finalize"
    assert first["read_only"] is True
    for key in (
        "application_authorization",
        "resume_text_mutation_authorization",
        "queue_mutation_authorization",
        "operator_state_mutation_authorization",
    ):
        assert first[key] is False
    for rejected in (_decision("needs_revision"), _decision("cancel")):
        with pytest.raises(ValueError, match="not_resume_authorizable"):
            store.prepare_resume_authorization_row(
                rejected, authorization_token_hash="b" * 64,
                created_at=NOW, expires_at="2026-07-24T13:00:00Z",
            )
    with pytest.raises(ValueError, match="token_hash_invalid"):
        store.prepare_resume_authorization_row(
            _decision(), authorization_token_hash="Bearer raw-token",
            created_at=NOW, expires_at="2026-07-24T13:00:00Z",
        )


def test_consumption_is_single_identity_deterministic_and_not_execution_result():
    first = store.prepare_resume_consumption_row(
        _authorization(), consumer_instance_id="worker-1", claimed_at=NOW,
        expected_authorization_version=0,
    )
    second = store.prepare_resume_consumption_row(
        _authorization(), consumer_instance_id="worker-1", claimed_at=NOW,
        expected_authorization_version=0,
    )
    assert first == second
    assert first["claim_status"] == "claimed"
    assert first["application_authorization"] is False
    assert "result" not in first
    assert first["resume_invocation_id"].startswith("resume-invocation:")


def test_owner_scoped_reads_are_deterministic_and_never_unscoped():
    commands = (
        store.prepare_current_decision_read(
            owner_user_id="owner-1", interrupt_request_id="interrupt-1"),
        store.prepare_resume_authorization_read(
            owner_user_id="owner-1", decision_id="decision-1"),
        store.prepare_resume_consumption_read(
            owner_user_id="owner-1", authorization_id="authorization-1"),
        store.prepare_authorized_resume_work_read(
            owner_user_id="owner-1", graph_invocation_id="graph-1"),
    )
    for command in commands:
        assert command["read_only"] is True
        assert "owner_user_id = %(owner_user_id)s" in command["sql"]
        assert command["params"]["owner_user_id"] == "owner-1"
    with pytest.raises(ValueError):
        store.prepare_current_decision_read(
            owner_user_id="", interrupt_request_id="interrupt-1")


def test_decision_authorization_and_consumption_sql_are_atomic_cas_contracts():
    decision_command = store.prepare_human_decision_recording(_decision())
    authorization_command = store.prepare_resume_authorization_commit(
        _authorization(), expected_run_lock_version=2,
        expected_interrupt_version=1,
    )
    consumption = store.prepare_resume_consumption_row(
        _authorization(), consumer_instance_id="worker-1", claimed_at=NOW,
        expected_authorization_version=0,
    )
    consumption_command = store.prepare_resume_consumption_commit(
        consumption, expected_run_lock_version=3,
        expected_interrupt_version=2,
    )
    for command in (decision_command, authorization_command, consumption_command):
        assert "FOR UPDATE" in command["sql"]
        assert "current_checkpoint_id = %(checkpoint_id)s" in command["sql"]
        assert "lock_version = %(expected_run_lock_version)s" in command["sql"]
        assert "lock_version = %(expected_interrupt_version)s" in command["sql"]
        assert "lock_version = lock_version + 1" in command["sql"]
        assert "ON CONFLICT DO NOTHING" in command["sql"]
        assert command["sql_executed"] is False
    assert "authorization_status = 'consumed'" in consumption_command["sql"]
    assert "expected_authorization_version" in consumption_command["sql"]


def test_decision_outcomes_do_not_authorize_revision_or_cancel():
    revision = store.prepare_human_decision_recording(_decision("needs_revision"))
    cancel = store.prepare_human_decision_recording(_decision("cancel"))
    assert revision["params"]["next_run_status"] == "decision_rejected"
    assert cancel["params"]["next_run_status"] == "cancelled"
    assert "resume_authorization" not in revision["tables"]
    assert "resume_authorization" not in cancel["tables"]


def test_store_remains_pure_and_package_inert():
    source = Path("src/storage/durable_orchestration/store.py").read_text()
    package = Path("src/storage/durable_orchestration/__init__.py").read_text()
    for marker in (
        "import psycopg", "import sqlalchemy", "from langgraph", ".execute(",
        ".cursor(", ".commit(", "os.environ", "src.app", "src.collector",
        "src.storage.application_actions",
    ):
        assert marker not in source
    assert "import " not in package
    assert all(value is False for value in store.safety_declarations().values())
