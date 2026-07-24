from __future__ import annotations

from copy import deepcopy
import os
from pathlib import Path
import re
from typing import Any, Mapping

import pytest

from src.storage.durable_orchestration import (
    postgres_connection,
    repository,
    store,
)
from tests.test_phase9_step2_durable_checkpoint_interrupt_storage_contract import (
    _contracts,
)


ROOT = Path(__file__).resolve().parents[1]
RUNTIME_GATE = "APPLYLENS_DURABLE_ORCHESTRATION_TEST_RUNTIME_DML_ENABLED"
TEST_TARGET = "APPLYLENS_DURABLE_ORCHESTRATION_TEST_DATABASE_URL"
RUNTIME_TARGET = "APPLYLENS_DURABLE_ORCHESTRATION_DATABASE_URL"
GENERIC_TARGET = "DATABASE_URL"
OWNER = "owner-phase9-step16a-runtime"
WRONG_OWNER = "owner-phase9-step16a-wrong"
NOW = "2026-07-24T12:00:00Z"
EXPIRES = "2026-07-24T13:00:00Z"
TOKEN_HASH = "b" * 64
WRONG_TOKEN_HASH = "c" * 64
_TRUE = {"1", "true", "yes", "on", "enabled"}
_TABLES = (
    "orchestration_lifecycle_events",
    "orchestration_terminal_results",
    "orchestration_node_attempts",
    "orchestration_resume_consumptions",
    "orchestration_resume_authorizations",
    "orchestration_human_decisions",
    "orchestration_interrupt_requests",
    "orchestration_checkpoints",
    "orchestration_graph_runs",
)


def _runtime_target_or_skip(configuration: Mapping[str, Any]) -> str:
    if (
        str(configuration.get(RUNTIME_GATE, "") or "").strip().lower()
        not in _TRUE
    ):
        pytest.skip("dedicated_step16a_runtime_dml_not_enabled")
    target = str(configuration.get(TEST_TARGET, "") or "").strip()
    if not target:
        pytest.skip("dedicated_step16a_database_target_missing")
    for name in (GENERIC_TARGET, RUNTIME_TARGET):
        other = str(configuration.get(name, "") or "").strip()
        if other and other == target:
            pytest.fail("dedicated_step16a_database_target_alias_rejected")
    return target


def _fixtures():
    return _contracts(
        owner_user_id=OWNER,
        pipeline_run_id="run-phase9-step16a-runtime",
        context_id="ctx-phase9-step16a-runtime",
        job_id="job-phase9-step16a-runtime",
        selected_resume_id="resume-phase9-step16a-runtime",
    )


def _decision(interrupt: Mapping[str, Any]) -> dict[str, Any]:
    return store.prepare_human_decision_row(
        interrupt,
        decision_value="continue_read_only",
        actor_id="actor-phase9-step16a",
        client_idempotency_key="client-phase9-step16a",
        expected_interrupt_version=0,
        expected_run_lock_version=1,
        created_at=NOW,
        reason="approved read-only continuation",
    )


def _authorization(decision: Mapping[str, Any]) -> dict[str, Any]:
    return store.prepare_resume_authorization_row(
        decision,
        authorization_token_hash=TOKEN_HASH,
        created_at=NOW,
        expires_at=EXPIRES,
    )


def _consumption(
    authorization: Mapping[str, Any],
    *,
    consumer: str = "worker-phase9-step16a",
    claimed_at: str = NOW,
    version: int = 0,
) -> dict[str, Any]:
    return store.prepare_resume_consumption_row(
        authorization,
        consumer_instance_id=consumer,
        claimed_at=claimed_at,
        expected_authorization_version=version,
    )


def _cte_bodies(sql: str) -> dict[str, str]:
    starts = list(
        re.finditer(
            r"(?:WITH|,\s*)\s*([a-z_]+)\s+AS\s*\(",
            sql,
            flags=re.IGNORECASE,
        )
    )
    result: dict[str, str] = {}
    for index, match in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(sql)
        result[match.group(1).lower()] = sql[match.end():end]
    return result


def _cleanup(factory, *, owner: str, graph_id: str) -> int:
    connection = factory()
    cursor = connection.cursor()
    removed = 0
    try:
        for table in _TABLES:
            cursor.execute(
                f"DELETE FROM {table} "
                "WHERE owner_user_id = %(owner_user_id)s "
                "AND graph_invocation_id = %(graph_invocation_id)s",
                {
                    "owner_user_id": owner,
                    "graph_invocation_id": graph_id,
                },
            )
            removed += max(cursor.rowcount, 0)
        connection.commit()
        return removed
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()
        connection.close()


def _counts(factory, *, owner: str, graph_id: str) -> dict[str, int]:
    connection = factory()
    cursor = connection.cursor()
    try:
        result = {}
        for table in _TABLES:
            cursor.execute(
                f"SELECT count(*) AS record_count FROM {table} "
                "WHERE owner_user_id = %(owner_user_id)s "
                "AND graph_invocation_id = %(graph_invocation_id)s",
                {
                    "owner_user_id": owner,
                    "graph_invocation_id": graph_id,
                },
            )
            result[table] = int(cursor.fetchall()[0]["record_count"])
        return result
    finally:
        connection.rollback()
        cursor.close()
        connection.close()


def test_consumption_transaction_is_authorization_first_and_fully_gated():
    authorization = _authorization(_decision(_fixtures()[5]))
    command = store.prepare_resume_consumption_commit(
        _consumption(authorization),
        expected_run_lock_version=3,
        expected_interrupt_version=2,
    )
    bodies = _cte_bodies(command["sql"])
    order = list(bodies)

    assert order.index("locked_authorization") < order.index(
        "updated_authorization"
    ) < order.index("inserted_consumption")
    assert "updated_authorization" in bodies["inserted_consumption"].lower()
    assert "inserted_consumption" in bodies["updated_interrupt"].lower()
    assert "inserted_consumption" in bodies["updated_run"].lower()
    locked = bodies["locked_authorization"].lower()
    for predicate in (
        "authorization_id",
        "decision_id",
        "graph_invocation_id",
        "checkpoint_id",
        "interrupt_request_id",
        "owner_user_id",
        "selected_resume_id",
        "authorization_status = 'authorized'",
        "expected_authorization_version",
        "authorization_token_hash",
        "expires_at >",
    ):
        assert predicate in locked
    assert command["params"]["authorization_token_hash"] == TOKEN_HASH


def test_checkpoint_binding_is_deterministic_strict_and_owner_scoped():
    _, _, _, graph_run, checkpoint, _ = _fixtures()
    first = store.prepare_langgraph_checkpoint_binding_row(
        graph_run,
        repository_checkpoint_id=checkpoint["checkpoint_id"],
        langgraph_thread_id=graph_run["graph_invocation_id"],
        langgraph_checkpoint_namespace="",
        langgraph_checkpoint_id="package-checkpoint-step16a",
        event_timestamp=NOW,
    )
    second = store.prepare_langgraph_checkpoint_binding_row(
        graph_run,
        repository_checkpoint_id=checkpoint["checkpoint_id"],
        langgraph_thread_id=graph_run["graph_invocation_id"],
        langgraph_checkpoint_namespace="",
        langgraph_checkpoint_id="package-checkpoint-step16a",
        event_timestamp=NOW,
    )
    assert first == second
    assert first["event_type"] == "checkpoint_committed"
    assert first["aggregate_type"] == (
        store.LANGGRAPH_CHECKPOINT_BINDING_AGGREGATE_TYPE
    )
    assert first["aggregate_id"] == checkpoint["checkpoint_id"]
    assert first["event_sequence"] == 0
    assert first["checkpoint_id"] != (
        first["event_payload_json"]["langgraph_checkpoint_id"]
    )
    command = store.prepare_langgraph_checkpoint_binding_read(
        owner_user_id=OWNER,
        graph_invocation_id=graph_run["graph_invocation_id"],
        repository_checkpoint_id=checkpoint["checkpoint_id"],
    )
    assert command["read_only"] is True
    assert command["params"]["owner_user_id"] == OWNER
    assert command["params"]["graph_invocation_id"] == (
        graph_run["graph_invocation_id"]
    )
    assert command["params"]["repository_checkpoint_id"] == (
        checkpoint["checkpoint_id"]
    )
    conflicting = deepcopy(first)
    conflicting["event_payload_json"]["langgraph_checkpoint_id"] = "other"
    with pytest.raises(ValueError, match="checkpoint_binding_contract"):
        store.prepare_langgraph_checkpoint_binding_commit(conflicting)
    with pytest.raises(ValueError, match="must_be_distinct"):
        store.prepare_langgraph_checkpoint_binding_row(
            graph_run,
            repository_checkpoint_id=checkpoint["checkpoint_id"],
            langgraph_thread_id=graph_run["graph_invocation_id"],
            langgraph_checkpoint_namespace="",
            langgraph_checkpoint_id=checkpoint["checkpoint_id"],
            event_timestamp=NOW,
        )


def test_repository_remains_explicitly_enabled_and_has_no_runtime_expansion():
    with pytest.raises(
        repository.DurableOrchestrationRepositoryDisabled
    ):
        repository.DurableOrchestrationRepository(lambda: None)
    source = Path(repository.__file__).read_text(encoding="utf-8")
    for prohibited in (
        "os.environ",
        "DATABASE_URL",
        "from langgraph",
        "src.agents",
        "node_attempt",
        "terminalization",
        "application_action",
        "auto_apply",
        "submit_application",
    ):
        assert prohibited not in source


def test_real_postgres_step16a_decision_authorization_consumption_runtime():
    target = _runtime_target_or_skip(os.environ)
    _, envelope, _, graph_run, checkpoint, interrupt = _fixtures()
    graph_id = graph_run["graph_invocation_id"]
    factory = postgres_connection.build_postgres_connection_factory(
        enabled=True,
        database_url=target,
        connect_timeout_seconds=5,
        statement_timeout_ms=10_000,
        application_name="applylens-phase9-step16a-integration",
    )
    executor = repository.DurableOrchestrationRepository(
        factory, enabled=True
    )
    unrelated_before = _counts(
        factory, owner=WRONG_OWNER, graph_id="unrelated-step16a"
    )
    _cleanup(factory, owner=OWNER, graph_id=graph_id)
    decision = _decision(interrupt)
    authorization = _authorization(decision)
    valid_consumption = _consumption(authorization)
    try:
        assert executor.create_graph_run(
            envelope, created_at=graph_run["created_at"]
        ).classification == "applied"
        assert executor.commit_checkpoint_interrupt(
            graph_invocation_id=graph_id,
            owner_user_id=OWNER,
            expected_run_status="running",
            expected_lock_version=0,
            expected_current_checkpoint_id=None,
            checkpoint_row=checkpoint,
            interrupt_row=interrupt,
        ).classification == "applied"

        binding = store.prepare_langgraph_checkpoint_binding_row(
            graph_run,
            repository_checkpoint_id=checkpoint["checkpoint_id"],
            langgraph_thread_id=graph_id,
            langgraph_checkpoint_namespace="",
            langgraph_checkpoint_id="package-checkpoint-step16a-live",
            event_timestamp=NOW,
        )
        assert executor.commit_checkpoint_binding(
            binding
        ).classification == "applied"
        assert executor.commit_checkpoint_binding(
            binding
        ).classification == "idempotent_existing"
        assert executor.read_checkpoint_binding(
            owner_user_id=OWNER,
            graph_invocation_id=graph_id,
            repository_checkpoint_id=checkpoint["checkpoint_id"],
        ).record["event_payload_json"]["langgraph_checkpoint_id"] == (
            "package-checkpoint-step16a-live"
        )
        assert executor.read_checkpoint_binding(
            owner_user_id=WRONG_OWNER,
            graph_invocation_id=graph_id,
            repository_checkpoint_id=checkpoint["checkpoint_id"],
        ).classification == "not_found"

        stale_decision = deepcopy(decision)
        stale_decision["expected_run_lock_version"] = 0
        assert executor.record_human_decision(
            stale_decision
        ).classification == "stale_state"
        wrong_owner_decision = deepcopy(decision)
        wrong_owner_decision["owner_user_id"] = WRONG_OWNER
        assert executor.record_human_decision(
            wrong_owner_decision
        ).classification == "not_found"
        assert executor.record_human_decision(
            decision
        ).classification == "applied"
        assert executor.record_human_decision(
            decision
        ).classification == "idempotent_existing"
        assert executor.read_current_human_decision(
            owner_user_id=OWNER,
            interrupt_request_id=interrupt["interrupt_request_id"],
        ).record["decision_value"] == "continue_read_only"
        assert executor.read_current_human_decision(
            owner_user_id=WRONG_OWNER,
            interrupt_request_id=interrupt["interrupt_request_id"],
        ).classification == "not_found"

        assert executor.create_resume_authorization(
            authorization,
            expected_run_lock_version=1,
            expected_interrupt_version=1,
        ).classification == "stale_state"
        wrong_owner_authorization = deepcopy(authorization)
        wrong_owner_authorization["owner_user_id"] = WRONG_OWNER
        assert executor.create_resume_authorization(
            wrong_owner_authorization,
            expected_run_lock_version=2,
            expected_interrupt_version=1,
        ).classification == "not_found"
        assert executor.create_resume_authorization(
            authorization,
            expected_run_lock_version=2,
            expected_interrupt_version=1,
        ).classification == "applied"
        assert executor.create_resume_authorization(
            authorization,
            expected_run_lock_version=2,
            expected_interrupt_version=1,
        ).classification == "idempotent_existing"
        conflicting_authorization = store.prepare_resume_authorization_row(
            decision,
            authorization_token_hash=WRONG_TOKEN_HASH,
            created_at=NOW,
            expires_at=EXPIRES,
        )
        assert executor.create_resume_authorization(
            conflicting_authorization,
            expected_run_lock_version=2,
            expected_interrupt_version=1,
        ).classification == "duplicate_conflict"
        authorization_result = executor.read_resume_authorization(
            owner_user_id=OWNER,
            decision_id=decision["decision_id"],
        )
        assert authorization_result.record["authorization_status"] == (
            "authorized"
        )
        assert "authorization_token_hash" not in authorization_result.record
        assert executor.read_authorized_resume_work(
            owner_user_id=OWNER,
            graph_invocation_id=graph_id,
        ).classification == "applied"

        stale = _consumption(authorization, version=1)
        assert executor.consume_resume_authorization(
            stale,
            expected_run_lock_version=3,
            expected_interrupt_version=2,
            authorization_token_hash=TOKEN_HASH,
        ).classification == "stale_state"
        assert executor.consume_resume_authorization(
            valid_consumption,
            expected_run_lock_version=3,
            expected_interrupt_version=2,
            authorization_token_hash=WRONG_TOKEN_HASH,
        ).classification == "stale_state"
        expired = _consumption(
            authorization,
            claimed_at="2026-07-24T14:00:00Z",
        )
        expired_result = executor.consume_resume_authorization(
            expired,
            expected_run_lock_version=3,
            expected_interrupt_version=2,
            authorization_token_hash=TOKEN_HASH,
        )
        assert expired_result.classification == "stale_state"
        assert expired_result.metadata["reason_code"] == "expired"
        wrong_checkpoint = deepcopy(valid_consumption)
        wrong_checkpoint["checkpoint_id"] = "checkpoint-step16a-wrong"
        assert executor.consume_resume_authorization(
            wrong_checkpoint,
            expected_run_lock_version=3,
            expected_interrupt_version=2,
            authorization_token_hash=TOKEN_HASH,
        ).classification == "stale_state"
        wrong_interrupt = deepcopy(valid_consumption)
        wrong_interrupt["interrupt_request_id"] = "interrupt-step16a-wrong"
        assert executor.consume_resume_authorization(
            wrong_interrupt,
            expected_run_lock_version=3,
            expected_interrupt_version=2,
            authorization_token_hash=TOKEN_HASH,
        ).classification == "stale_state"
        assert executor.read_resume_consumption(
            owner_user_id=OWNER,
            authorization_id=authorization["authorization_id"],
        ).classification == "not_found"
        assert executor.read_graph_run(
            owner_user_id=OWNER,
            graph_invocation_id=graph_id,
        ).record["run_status"] == "resume_authorized"

        consumed = executor.consume_resume_authorization(
            valid_consumption,
            expected_run_lock_version=3,
            expected_interrupt_version=2,
            authorization_token_hash=TOKEN_HASH,
        )
        assert consumed.classification == "applied"
        assert executor.consume_resume_authorization(
            valid_consumption,
            expected_run_lock_version=3,
            expected_interrupt_version=2,
            authorization_token_hash=TOKEN_HASH,
        ).classification == "idempotent_existing"
        conflicting = _consumption(
            authorization, consumer="worker-phase9-step16a-conflict"
        )
        assert executor.consume_resume_authorization(
            conflicting,
            expected_run_lock_version=3,
            expected_interrupt_version=2,
            authorization_token_hash=TOKEN_HASH,
        ).classification == "duplicate_conflict"
        wrong_owner = deepcopy(valid_consumption)
        wrong_owner["owner_user_id"] = WRONG_OWNER
        assert executor.consume_resume_authorization(
            wrong_owner,
            expected_run_lock_version=3,
            expected_interrupt_version=2,
            authorization_token_hash=TOKEN_HASH,
        ).classification == "not_found"

        final_authorization = executor.read_resume_authorization(
            owner_user_id=OWNER,
            decision_id=decision["decision_id"],
        )
        assert final_authorization.record["authorization_status"] == "consumed"
        assert final_authorization.record["lock_version"] == 1
        final_run = executor.read_graph_run(
            owner_user_id=OWNER, graph_invocation_id=graph_id
        )
        assert final_run.record["run_status"] == "resume_consumed"
        assert final_run.record["lock_version"] == 4
        final_counts = _counts(factory, owner=OWNER, graph_id=graph_id)
        assert final_counts["orchestration_lifecycle_events"] == 1
        assert final_counts["orchestration_resume_consumptions"] == 1
        assert final_counts["orchestration_node_attempts"] == 0
        assert final_counts["orchestration_terminal_results"] == 0
    finally:
        _cleanup(factory, owner=OWNER, graph_id=graph_id)
    assert _counts(
        factory, owner=WRONG_OWNER, graph_id="unrelated-step16a"
    ) == unrelated_before
