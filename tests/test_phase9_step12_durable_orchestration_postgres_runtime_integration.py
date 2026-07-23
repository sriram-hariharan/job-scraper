import ast
from copy import deepcopy
from datetime import datetime
import importlib
import inspect
import os
from pathlib import Path
from typing import Any, Mapping

import pytest

from src.storage.durable_orchestration import postgres_connection, repository
from tests.test_phase9_step2_durable_checkpoint_interrupt_storage_contract import (
    _contracts,
)


ROOT = Path(__file__).resolve().parents[1]
CONNECTION_PATH = (
    ROOT / "src/storage/durable_orchestration/postgres_connection.py"
)
RUNTIME_DML_GATE = (
    "APPLYLENS_DURABLE_ORCHESTRATION_TEST_RUNTIME_DML_ENABLED"
)
TEST_DATABASE_URL = (
    "APPLYLENS_DURABLE_ORCHESTRATION_TEST_DATABASE_URL"
)
RUNTIME_DATABASE_URL = (
    "APPLYLENS_DURABLE_ORCHESTRATION_DATABASE_URL"
)
GENERIC_DATABASE_URL = "DATABASE_URL"
TEST_OWNER = "owner-phase9-step12-runtime-integration"
WRONG_OWNER = "owner-phase9-step12-wrong"

_TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}
_CLEANUP_TABLES = (
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
_UNSUPPORTED_TABLES = _CLEANUP_TABLES[:6]


class _FakeConnection:
    pass


def _valid_target() -> str:
    return "postgresql://fixture-user:fixture-secret@fixture.test/fixture_db"


def _prohibited_connect(*args: Any, **kwargs: Any) -> Any:
    raise AssertionError("postgres_connection_opened")


def _runtime_target_or_skip(configuration: Mapping[str, Any]) -> str:
    enabled = str(configuration.get(RUNTIME_DML_GATE, "") or "").strip().lower()
    if enabled not in _TRUE_VALUES:
        pytest.skip("dedicated_test_runtime_dml_not_enabled")
    target = str(configuration.get(TEST_DATABASE_URL, "") or "").strip()
    if not target:
        pytest.skip("dedicated_test_runtime_database_target_missing")
    for name in (GENERIC_DATABASE_URL, RUNTIME_DATABASE_URL):
        other = str(configuration.get(name, "") or "").strip()
        if other and other == target:
            pytest.fail("dedicated_test_runtime_database_target_alias_rejected")
    return target


def _integration_contracts():
    return _contracts(
        owner_user_id=TEST_OWNER,
        pipeline_run_id="run-phase9-step12-runtime-integration",
        context_id="ctx-phase9-step12-runtime-integration",
        job_id="job-phase9-step12-runtime-integration",
        selected_resume_id="resume-phase9-step12-runtime-integration",
    )


def _cleanup_exact_records(
    connection_factory,
    *,
    owner_user_id: str,
    graph_invocation_id: str,
) -> int:
    connection = connection_factory()
    cursor = None
    removed = 0
    try:
        cursor = connection.cursor()
        for table_name in _CLEANUP_TABLES:
            cursor.execute(
                f"""
                DELETE FROM {table_name}
                WHERE owner_user_id = %(owner_user_id)s
                  AND graph_invocation_id = %(graph_invocation_id)s
                """,
                {
                    "owner_user_id": owner_user_id,
                    "graph_invocation_id": graph_invocation_id,
                },
            )
            removed += max(0, int(cursor.rowcount))
        connection.commit()
        return removed
    except Exception:
        connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def _exact_record_counts(
    connection_factory,
    *,
    owner_user_id: str,
    graph_invocation_id: str,
) -> dict[str, int]:
    connection = connection_factory()
    cursor = None
    try:
        cursor = connection.cursor()
        counts = {}
        for table_name in _CLEANUP_TABLES:
            cursor.execute(
                f"""
                SELECT count(*) AS row_count
                FROM {table_name}
                WHERE owner_user_id = %(owner_user_id)s
                  AND graph_invocation_id = %(graph_invocation_id)s
                """,
                {
                    "owner_user_id": owner_user_id,
                    "graph_invocation_id": graph_invocation_id,
                },
            )
            counts[table_name] = int(cursor.fetchone()["row_count"])
        return counts
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def _non_test_record_counts(
    connection_factory,
    *,
    owner_user_id: str,
    graph_invocation_id: str,
) -> dict[str, int]:
    connection = connection_factory()
    cursor = None
    try:
        cursor = connection.cursor()
        counts = {}
        for table_name in _CLEANUP_TABLES:
            cursor.execute(
                f"""
                SELECT count(*) AS row_count
                FROM {table_name}
                WHERE NOT (
                    owner_user_id = %(owner_user_id)s
                    AND graph_invocation_id = %(graph_invocation_id)s
                )
                """,
                {
                    "owner_user_id": owner_user_id,
                    "graph_invocation_id": graph_invocation_id,
                },
            )
            counts[table_name] = int(cursor.fetchone()["row_count"])
        return counts
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def _assert_real_result_shapes(
    connection_factory,
    *,
    owner_user_id: str,
    graph_invocation_id: str,
) -> None:
    connection = connection_factory()
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT
                graph_run.created_at,
                graph_run.lock_version,
                graph_run.current_checkpoint_id,
                graph_run.terminal_at,
                checkpoint.checkpoint_envelope_json,
                checkpoint.completed_node_keys_json,
                interrupt_request.allowed_decision_values_json,
                interrupt_request.interrupt_request_json,
                interrupt_request.read_only,
                interrupt_request.diagnostic_only,
                interrupt_request.application_authorization,
                interrupt_request.resume_authorization
            FROM orchestration_graph_runs AS graph_run
            JOIN orchestration_checkpoints AS checkpoint
              ON checkpoint.checkpoint_id = graph_run.current_checkpoint_id
            JOIN orchestration_interrupt_requests AS interrupt_request
              ON interrupt_request.checkpoint_id = checkpoint.checkpoint_id
            WHERE graph_run.owner_user_id = %(owner_user_id)s
              AND graph_run.graph_invocation_id = %(graph_invocation_id)s
            """,
            {
                "owner_user_id": owner_user_id,
                "graph_invocation_id": graph_invocation_id,
            },
        )
        row = cursor.fetchone()
        assert isinstance(row, dict)
        assert isinstance(row["created_at"], datetime)
        assert isinstance(row["lock_version"], int)
        assert isinstance(row["current_checkpoint_id"], str)
        assert row["terminal_at"] is None
        assert isinstance(row["checkpoint_envelope_json"], dict)
        assert isinstance(row["completed_node_keys_json"], list)
        assert isinstance(row["allowed_decision_values_json"], list)
        assert isinstance(row["interrupt_request_json"], dict)
        assert row["read_only"] is True
        assert row["diagnostic_only"] is True
        assert row["application_authorization"] is False
        assert row["resume_authorization"] is False
        cursor.execute(
            "SELECT ARRAY['operator_review', 'finalize']::text[] AS node_keys",
            {},
        )
        assert cursor.fetchone()["node_keys"] == ["operator_review", "finalize"]
    finally:
        if cursor is not None:
            cursor.close()
        connection.close()


def test_connection_factory_is_default_off_and_errors_are_bounded(monkeypatch):
    monkeypatch.setattr(postgres_connection.psycopg, "connect", _prohibited_connect)
    target = _valid_target()

    with pytest.raises(
        postgres_connection.PostgresConnectionFactoryError
    ) as captured:
        postgres_connection.build_postgres_connection_factory(
            database_url=target,
        )

    assert str(captured.value).endswith("capability_disabled")
    assert "fixture-secret" not in str(captured.value)
    assert target not in str(captured.value)


def test_blank_target_rejects_environment_and_database_url_fallback(
    monkeypatch,
):
    monkeypatch.setenv(TEST_DATABASE_URL, _valid_target())
    monkeypatch.setenv(GENERIC_DATABASE_URL, _valid_target())
    monkeypatch.setattr(postgres_connection.psycopg, "connect", _prohibited_connect)

    with pytest.raises(
        postgres_connection.PostgresConnectionFactoryError
    ) as captured:
        postgres_connection.build_postgres_connection_factory(
            enabled=True,
            database_url="",
        )

    assert str(captured.value).endswith("database_url_missing")


def test_factory_opens_new_connections_with_exact_bounded_configuration(
    monkeypatch,
):
    calls = []

    def fake_connect(target, **options):
        connection = _FakeConnection()
        calls.append((target, options, connection))
        return connection

    monkeypatch.setattr(postgres_connection.psycopg, "connect", fake_connect)
    target = _valid_target()
    factory = postgres_connection.build_postgres_connection_factory(
        enabled=True,
        database_url=target,
        connect_timeout_seconds=7,
        statement_timeout_ms=8_000,
        application_name="applylens-phase9-step12-test",
    )

    assert callable(factory)
    assert not inspect.signature(factory).parameters
    first = factory()
    second = factory()
    assert first is not second
    assert len(calls) == 2
    for actual_target, options, _ in calls:
        assert actual_target == target
        assert options == {
            "autocommit": False,
            "row_factory": postgres_connection.dict_row,
            "connect_timeout": 7,
            "options": "-c statement_timeout=8000",
            "application_name": "applylens-phase9-step12-test",
        }
    assert target not in repr(factory)
    assert "fixture-secret" not in repr(factory)


def test_ssl_mode_is_only_applied_when_explicit(monkeypatch):
    calls = []
    monkeypatch.setattr(
        postgres_connection.psycopg,
        "connect",
        lambda target, **options: calls.append(options) or _FakeConnection(),
    )

    factory = postgres_connection.build_postgres_connection_factory(
        enabled=True,
        database_url=_valid_target(),
        ssl_mode="verify-full",
    )
    factory()

    assert calls[0]["sslmode"] == "verify-full"


@pytest.mark.parametrize(
    "overrides",
    [
        {"database_url": "not-a-postgres-target"},
        {"connect_timeout_seconds": 0},
        {"connect_timeout_seconds": 31},
        {"statement_timeout_ms": 0},
        {"statement_timeout_ms": 60_001},
        {"application_name": ""},
        {"application_name": "x" * 64},
        {"ssl_mode": "implicit-unsafe-mode"},
    ],
)
def test_malformed_or_unbounded_configuration_fails_before_connect(
    monkeypatch,
    overrides,
):
    monkeypatch.setattr(postgres_connection.psycopg, "connect", _prohibited_connect)
    arguments = {
        "enabled": True,
        "database_url": _valid_target(),
    }
    arguments.update(overrides)

    with pytest.raises(postgres_connection.PostgresConnectionFactoryError):
        postgres_connection.build_postgres_connection_factory(**arguments)


def test_driver_failure_drops_sensitive_details_and_exception_cause(
    monkeypatch,
):
    target = _valid_target()

    def failed_connect(*args, **kwargs):
        raise RuntimeError(target)

    monkeypatch.setattr(postgres_connection.psycopg, "connect", failed_connect)
    factory = postgres_connection.build_postgres_connection_factory(
        enabled=True,
        database_url=target,
    )

    with pytest.raises(
        postgres_connection.PostgresConnectionFactoryError
    ) as captured:
        factory()

    assert str(captured.value).endswith("connection_failed")
    assert captured.value.__cause__ is None
    assert target not in str(captured.value)
    assert "fixture-secret" not in str(captured.value)


def test_module_import_opens_no_connection_and_adds_no_lifecycle_work(
    monkeypatch,
):
    calls = []
    monkeypatch.setattr(
        postgres_connection.psycopg,
        "connect",
        lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    reloaded = importlib.reload(postgres_connection)

    assert reloaded is postgres_connection
    assert calls == []
    source = CONNECTION_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        node.module or ""
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    assert "os" not in imported_modules
    for marker in (
        "os.getenv(",
        "os.environ",
        "DATABASE_URL",
        ".commit(",
        ".rollback(",
        "create_pool",
        "ConnectionPool",
        "retry",
        "schema.sql",
        "CREATE TABLE",
        "ALTER TABLE",
        "DROP TABLE",
    ):
        assert marker not in source


def test_runtime_dml_gate_is_independent_and_rejects_aliases():
    with pytest.raises(pytest.skip.Exception):
        _runtime_target_or_skip(
            {TEST_DATABASE_URL: _valid_target()}
        )
    with pytest.raises(pytest.skip.Exception):
        _runtime_target_or_skip(
            {RUNTIME_DML_GATE: "1"}
        )
    with pytest.raises(pytest.fail.Exception):
        _runtime_target_or_skip(
            {
                RUNTIME_DML_GATE: "1",
                TEST_DATABASE_URL: _valid_target(),
                GENERIC_DATABASE_URL: _valid_target(),
            }
        )
    with pytest.raises(pytest.fail.Exception):
        _runtime_target_or_skip(
            {
                RUNTIME_DML_GATE: "1",
                TEST_DATABASE_URL: _valid_target(),
                RUNTIME_DATABASE_URL: _valid_target(),
            }
        )


def test_real_postgres_runtime_repository_first_subset():
    target = _runtime_target_or_skip(os.environ)
    _, envelope, _, graph_run, checkpoint, interrupt = _integration_contracts()
    graph_invocation_id = graph_run["graph_invocation_id"]
    factory = postgres_connection.build_postgres_connection_factory(
        enabled=True,
        database_url=target,
        connect_timeout_seconds=5,
        statement_timeout_ms=10_000,
        application_name="applylens-phase9-step12-integration",
    )
    executor = repository.DurableOrchestrationRepository(
        factory,
        enabled=True,
    )
    non_test_counts = _non_test_record_counts(
        factory,
        owner_user_id=TEST_OWNER,
        graph_invocation_id=graph_invocation_id,
    )
    _cleanup_exact_records(
        factory,
        owner_user_id=TEST_OWNER,
        graph_invocation_id=graph_invocation_id,
    )

    try:
        readiness = executor.probe_schema_readiness()
        assert readiness.classification == "applied"
        assert readiness.metadata["ready"] is True

        created = executor.create_graph_run(
            envelope,
            created_at=graph_run["created_at"],
        )
        assert created.classification == "applied"
        assert created.record["graph_invocation_id"] == graph_invocation_id
        assert created.record["owner_user_id"] == TEST_OWNER
        assert created.record["run_status"] == "running"
        assert created.record["current_checkpoint_id"] is None
        assert created.record["lock_version"] == 0

        duplicate = executor.create_graph_run(
            envelope,
            created_at=graph_run["created_at"],
        )
        assert duplicate.classification == "idempotent_existing"
        assert duplicate.record == created.record

        incompatible_identity = deepcopy(envelope["checkpoint_identity"])
        incompatible_identity["context_id"] = "ctx-phase9-step12-incompatible"
        incompatible = executor.create_graph_run(
            incompatible_identity,
            created_at=graph_run["created_at"],
        )
        assert incompatible.classification == "duplicate_conflict"

        owner_read = executor.read_graph_run(
            owner_user_id=TEST_OWNER,
            graph_invocation_id=graph_invocation_id,
        )
        assert owner_read.classification == "applied"
        assert owner_read.record == created.record
        wrong_owner_read = executor.read_graph_run(
            owner_user_id=WRONG_OWNER,
            graph_invocation_id=graph_invocation_id,
        )
        assert wrong_owner_read.classification == "not_found"

        stale = executor.commit_checkpoint_interrupt(
            graph_invocation_id=graph_invocation_id,
            owner_user_id=TEST_OWNER,
            expected_run_status="running",
            expected_lock_version=1,
            expected_current_checkpoint_id=None,
            checkpoint_row=checkpoint,
            interrupt_row=interrupt,
        )
        assert stale.classification == "stale_state"
        assert executor.read_current_checkpoint(
            owner_user_id=TEST_OWNER,
            graph_invocation_id=graph_invocation_id,
        ).classification == "not_found"
        assert executor.read_pending_interrupt(
            owner_user_id=TEST_OWNER,
            graph_invocation_id=graph_invocation_id,
        ).classification == "not_found"

        with pytest.raises(ValueError, match="checkpoint_owner_user_id_mismatch"):
            executor.commit_checkpoint_interrupt(
                graph_invocation_id=graph_invocation_id,
                owner_user_id=WRONG_OWNER,
                expected_run_status="running",
                expected_lock_version=0,
                expected_current_checkpoint_id=None,
                checkpoint_row=checkpoint,
                interrupt_row=interrupt,
            )
        counts_before_valid_commit = _exact_record_counts(
            factory,
            owner_user_id=TEST_OWNER,
            graph_invocation_id=graph_invocation_id,
        )
        assert counts_before_valid_commit["orchestration_checkpoints"] == 0
        assert (
            counts_before_valid_commit["orchestration_interrupt_requests"]
            == 0
        )

        committed = executor.commit_checkpoint_interrupt(
            graph_invocation_id=graph_invocation_id,
            owner_user_id=TEST_OWNER,
            expected_run_status="running",
            expected_lock_version=0,
            expected_current_checkpoint_id=None,
            checkpoint_row=checkpoint,
            interrupt_row=interrupt,
        )
        assert committed.classification == "applied"
        assert committed.record["run_status"] == "awaiting_decision"
        assert committed.record["current_checkpoint_id"] == checkpoint[
            "checkpoint_id"
        ]
        assert committed.record["lock_version"] == 1

        current_checkpoint = executor.read_current_checkpoint(
            owner_user_id=TEST_OWNER,
            graph_invocation_id=graph_invocation_id,
        )
        assert current_checkpoint.classification == "applied"
        assert current_checkpoint.record["checkpoint_id"] == checkpoint[
            "checkpoint_id"
        ]
        assert current_checkpoint.record["checkpoint_envelope_digest"] == (
            checkpoint["checkpoint_envelope_digest"]
        )
        pending_interrupt = executor.read_pending_interrupt(
            owner_user_id=TEST_OWNER,
            graph_invocation_id=graph_invocation_id,
        )
        assert pending_interrupt.classification == "applied"
        assert pending_interrupt.record["interrupt_request_id"] == interrupt[
            "interrupt_request_id"
        ]
        assert pending_interrupt.record["checkpoint_id"] == checkpoint[
            "checkpoint_id"
        ]
        assert pending_interrupt.record["read_only"] is True
        assert pending_interrupt.record["diagnostic_only"] is True
        assert pending_interrupt.record["application_authorization"] is False
        assert pending_interrupt.record["resume_authorization"] is False

        final_graph = executor.read_graph_run(
            owner_user_id=TEST_OWNER,
            graph_invocation_id=graph_invocation_id,
        )
        assert final_graph.record == committed.record
        assert executor.read_current_checkpoint(
            owner_user_id=WRONG_OWNER,
            graph_invocation_id=graph_invocation_id,
        ).classification == "not_found"
        assert executor.read_pending_interrupt(
            owner_user_id=WRONG_OWNER,
            graph_invocation_id=graph_invocation_id,
        ).classification == "not_found"

        exact_counts = _exact_record_counts(
            factory,
            owner_user_id=TEST_OWNER,
            graph_invocation_id=graph_invocation_id,
        )
        assert exact_counts["orchestration_graph_runs"] == 1
        assert exact_counts["orchestration_checkpoints"] == 1
        assert exact_counts["orchestration_interrupt_requests"] == 1
        assert all(exact_counts[table_name] == 0 for table_name in _UNSUPPORTED_TABLES)
        _assert_real_result_shapes(
            factory,
            owner_user_id=TEST_OWNER,
            graph_invocation_id=graph_invocation_id,
        )
    finally:
        _cleanup_exact_records(
            factory,
            owner_user_id=TEST_OWNER,
            graph_invocation_id=graph_invocation_id,
        )
        assert all(
            count == 0
            for count in _exact_record_counts(
                factory,
                owner_user_id=TEST_OWNER,
                graph_invocation_id=graph_invocation_id,
            ).values()
        )
        assert _non_test_record_counts(
            factory,
            owner_user_id=TEST_OWNER,
            graph_invocation_id=graph_invocation_id,
        ) == non_test_counts
