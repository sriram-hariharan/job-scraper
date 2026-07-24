import ast
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.storage.durable_orchestration import repository, store
from tests.test_phase9_step2_durable_checkpoint_interrupt_storage_contract import (
    _contracts,
)


ROOT = Path(__file__).resolve().parents[1]
REPOSITORY_PATH = (
    ROOT / "src/storage/durable_orchestration/repository.py"
)
STORE_PATH = ROOT / "src/storage/durable_orchestration/store.py"
SCHEMA_PATH = ROOT / "src/storage/durable_orchestration/schema.sql"


class FakeDatabaseError(RuntimeError):
    def __init__(self, sqlstate, sensitive_text="sensitive-host"):
        self.sqlstate = sqlstate
        super().__init__(sensitive_text)


class FakeCursor:
    def __init__(self, responses, events):
        self._responses = list(responses)
        self._events = events
        self._current = None
        self.description = None
        self.executions = []
        self.closed = False

    def execute(self, sql, params):
        self._events.append("execute")
        self.executions.append((sql, dict(params)))
        if not self._responses:
            raise AssertionError("unexpected execute")
        self._current = self._responses.pop(0)
        error = self._current.get("error")
        if error is not None:
            raise error
        columns = self._current.get("columns")
        self.description = (
            tuple((column,) for column in columns)
            if columns is not None
            else None
        )

    def fetchall(self):
        self._events.append("fetchall")
        return list(self._current.get("rows", ()))

    def close(self):
        self.closed = True
        self._events.append("cursor.close")


class FakeConnection:
    def __init__(self, responses):
        self.events = []
        self.cursor_value = FakeCursor(responses, self.events)
        self.commit_count = 0
        self.rollback_count = 0
        self.closed = False

    def cursor(self):
        self.events.append("cursor")
        return self.cursor_value

    def commit(self):
        self.commit_count += 1
        self.events.append("commit")

    def rollback(self):
        self.rollback_count += 1
        self.events.append("rollback")

    def close(self):
        self.closed = True
        self.events.append("connection.close")


class FakeFactory:
    def __init__(self, *connections):
        self.connections = list(connections)
        self.call_count = 0

    def __call__(self):
        self.call_count += 1
        if not self.connections:
            raise AssertionError("unexpected connection")
        return self.connections.pop(0)


def _enabled(*responses):
    connection = FakeConnection(responses)
    factory = FakeFactory(connection)
    return (
        repository.DurableOrchestrationRepository(
            factory,
            enabled=True,
        ),
        factory,
        connection,
    )


def _graph_contract():
    _, envelope, _, graph_run, checkpoint, interrupt = _contracts()
    return envelope, graph_run, checkpoint, interrupt


def _graph_result(graph_run, *, duplicate=False, **overrides):
    result = dict(graph_run)
    result.update(overrides)
    result["idempotent_duplicate"] = duplicate
    return result


def _advanced_graph(graph_run, checkpoint, **overrides):
    result = dict(graph_run)
    result.update(
        {
            "current_checkpoint_id": checkpoint["checkpoint_id"],
            "run_status": "awaiting_decision",
            "lock_version": 1,
            "updated_at": checkpoint["committed_at"],
        }
    )
    result.update(overrides)
    return result


def _readiness_rows(*, missing=(), incompatible=()):
    rows = []
    requirements = repository._READINESS_REQUIREMENTS
    for name, required in requirements.items():
        row = {
            "object_name": name,
            "present": name not in missing,
            "columns": list(required["columns"]),
            "primary_key_columns": list(required["primary_key"]),
            "constraint_names": list(required["constraints"]),
        }
        if name in incompatible:
            row["columns"] = []
        rows.append(row)
    return rows


def test_repository_gate_defaults_off_and_never_calls_factory():
    factory = FakeFactory()

    with pytest.raises(
        repository.DurableOrchestrationRepositoryDisabled
    ) as captured:
        repository.DurableOrchestrationRepository(factory)

    assert factory.call_count == 0
    assert captured.value.classification == "unavailable"
    assert captured.value.reason_code == "capability_disabled"
    assert repository.CAPABILITY_NAME == (
        "APPLYLENS_DURABLE_ORCHESTRATION_RUNTIME_REPOSITORY_ENABLED"
    )


def test_module_import_has_no_connection_driver_environment_or_work():
    source = REPOSITORY_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }

    assert not {
        "psycopg",
        "psycopg2",
        "asyncpg",
        "sqlalchemy",
        "langgraph",
        "os",
    } & imported
    assert "getenv(" not in source
    assert "environ" not in source
    assert "schema.sql" not in source
    assert not any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "DurableOrchestrationRepository"
        for node in tree.body
    )


def test_result_contract_is_typed_deeply_immutable_and_bounded():
    result = repository.RepositoryResult.build(
        operation="read_graph_run",
        classification="applied",
        record={"graph_invocation_id": "graph-1", "nested": ["value"]},
        metadata={"retryable": False},
    )

    with pytest.raises(FrozenInstanceError):
        result.classification = "not_found"
    with pytest.raises(TypeError):
        result.record["graph_invocation_id"] = "other"
    assert result.record["nested"] == ("value",)
    assert set(repository.RESULT_CLASSIFICATIONS) == {
        "applied",
        "idempotent_existing",
        "not_found",
        "stale_state",
        "identity_mismatch",
        "already_terminal",
        "duplicate_conflict",
        "unavailable",
        "transaction_failed",
    }


def test_readiness_probe_checks_exact_three_objects_without_ddl_or_commit():
    executor, factory, connection = _enabled(
        {"rows": _readiness_rows()}
    )

    result = executor.probe_schema_readiness()

    assert result.classification == "applied"
    assert result.metadata["ready"] is True
    assert set(result.metadata["checked_objects"]) == {
        "orchestration_graph_runs",
        "orchestration_checkpoints",
        "orchestration_interrupt_requests",
    }
    sql, params = connection.cursor_value.executions[0]
    assert "pg_catalog" in sql
    assert "current_schema()" in sql
    assert not {"CREATE ", "ALTER ", "DROP ", "INSERT ", "UPDATE "} & {
        token + " " for token in sql.upper().split()
    }
    assert params == {}
    assert factory.call_count == 1
    assert connection.commit_count == 0
    assert connection.cursor_value.closed
    assert connection.closed


@pytest.mark.parametrize(
    ("missing", "incompatible", "expected_key"),
    [
        (("orchestration_checkpoints",), (), "missing_objects"),
        ((), ("orchestration_interrupt_requests",), "incompatible_objects"),
    ],
)
def test_readiness_probe_returns_bounded_unavailable_result(
    missing,
    incompatible,
    expected_key,
):
    executor, _, connection = _enabled(
        {
            "rows": _readiness_rows(
                missing=missing,
                incompatible=incompatible,
            )
        }
    )

    result = executor.probe_schema_readiness()

    assert result.classification == "unavailable"
    assert result.metadata["ready"] is False
    assert tuple(result.metadata[expected_key]) == (missing or incompatible)
    assert connection.commit_count == 0
    assert "database" not in result.metadata


@pytest.mark.parametrize(
    ("duplicate", "classification"),
    [(False, "applied"), (True, "idempotent_existing")],
)
def test_create_graph_run_applied_and_exact_idempotent_existing(
    duplicate,
    classification,
):
    envelope, graph_run, _, _ = _graph_contract()
    executor, _, connection = _enabled(
        {"rows": [_graph_result(graph_run, duplicate=duplicate)]}
    )

    result = executor.create_graph_run(
        envelope,
        created_at=graph_run["created_at"],
    )

    expected = store.prepare_graph_run_insert(graph_run)
    assert connection.cursor_value.executions == [
        (expected["sql"], expected["params"])
    ]
    assert result.classification == classification
    assert result.record["graph_invocation_id"] == (
        graph_run["graph_invocation_id"]
    )
    assert set(result.record) == {
        "graph_invocation_id",
        "owner_user_id",
        "run_status",
        "current_checkpoint_id",
        "lock_version",
    }
    assert connection.commit_count == 1
    assert connection.events.index("commit") < connection.events.index(
        "cursor.close"
    )


def test_create_graph_run_zero_row_duplicate_conflict_rolls_back():
    envelope, graph_run, _, _ = _graph_contract()
    executor, _, connection = _enabled({"rows": []})

    result = executor.create_graph_run(
        envelope,
        created_at=graph_run["created_at"],
    )

    assert result.classification == "duplicate_conflict"
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.events.index("rollback") < connection.events.index(
        "cursor.close"
    )


def test_create_graph_run_incompatible_duplicate_fails_closed():
    envelope, graph_run, _, _ = _graph_contract()
    returned = _graph_result(
        graph_run,
        duplicate=True,
        owner_user_id="wrong-owner",
    )
    executor, _, connection = _enabled({"rows": [returned]})

    with pytest.raises(
        repository.DurableOrchestrationRepositoryError
    ) as captured:
        executor.create_graph_run(
            envelope,
            created_at=graph_run["created_at"],
        )

    assert captured.value.classification == "identity_mismatch"
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.closed


def test_create_graph_run_accepts_driver_normalized_timestamp_values():
    envelope, graph_run, _, _ = _graph_contract()
    returned = _graph_result(
        graph_run,
        created_at=datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc),
        updated_at=datetime(2026, 7, 23, 12, 0, tzinfo=timezone.utc),
    )
    executor, _, connection = _enabled({"rows": [returned]})

    result = executor.create_graph_run(
        envelope,
        created_at=graph_run["created_at"],
    )

    assert result.classification == "applied"
    assert connection.commit_count == 1


@pytest.mark.parametrize(
    ("method_name", "row_kind"),
    [
        ("read_graph_run", "graph"),
        ("read_current_checkpoint", "checkpoint"),
        ("read_pending_interrupt", "interrupt"),
    ],
)
def test_owner_scoped_reads_reuse_store_commands_without_commit(
    method_name,
    row_kind,
):
    _, graph_run, checkpoint, interrupt = _graph_contract()
    row = {
        "graph": graph_run,
        "checkpoint": checkpoint,
        "interrupt": interrupt,
    }[row_kind]
    executor, _, connection = _enabled({"rows": [row]})

    result = getattr(executor, method_name)(
        owner_user_id=graph_run["owner_user_id"],
        graph_invocation_id=graph_run["graph_invocation_id"],
    )

    assert result.classification == "applied"
    assert result.record["owner_user_id"] == graph_run["owner_user_id"]
    assert result.record["graph_invocation_id"] == (
        graph_run["graph_invocation_id"]
    )
    sql, params = connection.cursor_value.executions[0]
    assert "owner_user_id" in sql
    assert params["owner_user_id"] == graph_run["owner_user_id"]
    assert params["graph_invocation_id"] == graph_run["graph_invocation_id"]
    assert connection.commit_count == 0
    assert connection.rollback_count == 0
    assert connection.closed


def test_owner_scoped_read_no_row_is_not_found_and_does_not_commit():
    _, graph_run, _, _ = _graph_contract()
    executor, _, connection = _enabled({"rows": []})

    result = executor.read_graph_run(
        owner_user_id=graph_run["owner_user_id"],
        graph_invocation_id=graph_run["graph_invocation_id"],
    )

    assert result.classification == "not_found"
    assert not result.record
    assert connection.commit_count == 0
    assert connection.closed


@pytest.mark.parametrize(
    "rows",
    [
        [{"graph_invocation_id": "a"}, {"graph_invocation_id": "b"}],
        [{"graph_invocation_id": "a"}],
    ],
)
def test_read_multiple_or_malformed_rows_fail_closed(rows):
    _, graph_run, _, _ = _graph_contract()
    executor, _, connection = _enabled({"rows": rows})

    with pytest.raises(repository.DurableOrchestrationRepositoryError):
        executor.read_graph_run(
            owner_user_id=graph_run["owner_user_id"],
            graph_invocation_id=graph_run["graph_invocation_id"],
        )

    assert connection.rollback_count == 1
    assert connection.commit_count == 0
    assert connection.closed


def test_tuple_rows_are_validated_through_cursor_description():
    _, graph_run, _, _ = _graph_contract()
    fields = repository._GRAPH_RESULT_FIELDS
    values = tuple(graph_run[field] for field in fields)
    executor, _, connection = _enabled(
        {"rows": [values], "columns": fields}
    )

    result = executor.read_graph_run(
        owner_user_id=graph_run["owner_user_id"],
        graph_invocation_id=graph_run["graph_invocation_id"],
    )

    assert result.classification == "applied"
    assert result.record["lock_version"] == 0
    assert connection.commit_count == 0


def test_atomic_checkpoint_interrupt_success_commits_after_exact_validation():
    _, graph_run, checkpoint, interrupt = _graph_contract()
    advanced = _advanced_graph(graph_run, checkpoint)
    executor, _, connection = _enabled({"rows": [advanced]})

    result = executor.commit_checkpoint_interrupt(
        graph_invocation_id=graph_run["graph_invocation_id"],
        owner_user_id=graph_run["owner_user_id"],
        expected_run_status="running",
        expected_lock_version=0,
        expected_current_checkpoint_id=None,
        checkpoint_row=checkpoint,
        interrupt_row=interrupt,
    )

    expected = store.prepare_checkpoint_interrupt_commit(
        checkpoint_row=checkpoint,
        interrupt_row=interrupt,
        expected_owner_user_id=graph_run["owner_user_id"],
        expected_run_status="running",
        expected_lock_version=0,
        expected_current_checkpoint_id=None,
    )
    assert connection.cursor_value.executions == [
        (expected["sql"], expected["params"])
    ]
    assert result.classification == "applied"
    assert result.record["current_checkpoint_id"] == checkpoint[
        "checkpoint_id"
    ]
    assert result.record["run_status"] == "awaiting_decision"
    assert result.record["lock_version"] == 1
    assert connection.commit_count == 1
    assert connection.rollback_count == 0


@pytest.mark.parametrize(
    "overrides",
    [
        {"graph_invocation_id": "wrong-graph"},
        {"owner_user_id": "wrong-owner"},
        {"current_checkpoint_id": "wrong-checkpoint"},
        {"run_status": "running"},
        {"lock_version": 3},
    ],
)
def test_atomic_returned_graph_advancement_is_exact(overrides):
    _, graph_run, checkpoint, interrupt = _graph_contract()
    executor, _, connection = _enabled(
        {"rows": [_advanced_graph(graph_run, checkpoint, **overrides)]}
    )

    with pytest.raises(
        repository.DurableOrchestrationRepositoryError
    ) as captured:
        executor.commit_checkpoint_interrupt(
            graph_invocation_id=graph_run["graph_invocation_id"],
            owner_user_id=graph_run["owner_user_id"],
            expected_run_status="running",
            expected_lock_version=0,
            expected_current_checkpoint_id=None,
            checkpoint_row=checkpoint,
            interrupt_row=interrupt,
        )

    assert captured.value.classification == "transaction_failed"
    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.events.index("rollback") < connection.events.index(
        "cursor.close"
    )


@pytest.mark.parametrize(
    ("classification_row", "classification"),
    [
        (None, "identity_mismatch"),
        ({"run_status": "completed"}, "already_terminal"),
        ({"run_status": "awaiting_decision"}, "stale_state"),
        ({"lock_version": 4}, "stale_state"),
        ({"current_checkpoint_id": "older"}, "stale_state"),
        ({}, "duplicate_conflict"),
    ],
)
def test_zero_row_cas_rolls_back_then_classifies_boundedly(
    classification_row,
    classification,
):
    _, graph_run, checkpoint, interrupt = _graph_contract()
    current = dict(graph_run)
    if classification_row is None:
        read_rows = []
    else:
        current.update(classification_row)
        read_rows = [current]
    executor, _, connection = _enabled(
        {"rows": []},
        {"rows": read_rows},
    )

    result = executor.commit_checkpoint_interrupt(
        graph_invocation_id=graph_run["graph_invocation_id"],
        owner_user_id=graph_run["owner_user_id"],
        expected_run_status="running",
        expected_lock_version=0,
        expected_current_checkpoint_id=None,
        checkpoint_row=checkpoint,
        interrupt_row=interrupt,
    )

    assert result.classification == classification
    assert len(connection.cursor_value.executions) == 2
    assert connection.events.index("rollback") < (
        connection.events.index("execute", 2)
    )
    assert connection.commit_count == 0
    assert connection.closed


@pytest.mark.parametrize(
    "rows",
    [
        [{"graph_invocation_id": "a"}, {"graph_invocation_id": "b"}],
        [{"graph_invocation_id": "a"}],
    ],
)
def test_atomic_multiple_or_malformed_rows_fail_closed(rows):
    _, graph_run, checkpoint, interrupt = _graph_contract()
    executor, _, connection = _enabled({"rows": rows})

    with pytest.raises(repository.DurableOrchestrationRepositoryError):
        executor.commit_checkpoint_interrupt(
            graph_invocation_id=graph_run["graph_invocation_id"],
            owner_user_id=graph_run["owner_user_id"],
            expected_run_status="running",
            expected_lock_version=0,
            expected_current_checkpoint_id=None,
            checkpoint_row=checkpoint,
            interrupt_row=interrupt,
        )

    assert connection.commit_count == 0
    assert connection.rollback_count == 1
    assert connection.closed


@pytest.mark.parametrize(
    ("sqlstate", "classification", "reason", "retryable"),
    [
        ("40001", "transaction_failed", "serialization_failure", True),
        ("40P01", "transaction_failed", "deadlock", True),
        ("23505", "duplicate_conflict", "unique_violation", False),
        ("23503", "identity_mismatch", "foreign_key_violation", False),
        ("23514", "transaction_failed", "check_violation", False),
        ("08006", "unavailable", "connection_unavailable", False),
        ("XX000", "transaction_failed", "database_failure", False),
    ],
)
def test_generic_sqlstate_failures_are_bounded_and_never_retried(
    sqlstate,
    classification,
    reason,
    retryable,
):
    _, graph_run, _, _ = _graph_contract()
    executor, factory, connection = _enabled(
        {"error": FakeDatabaseError(sqlstate)}
    )

    with pytest.raises(
        repository.DurableOrchestrationRepositoryError
    ) as captured:
        executor.read_graph_run(
            owner_user_id=graph_run["owner_user_id"],
            graph_invocation_id=graph_run["graph_invocation_id"],
        )

    error = captured.value
    assert error.classification == classification
    assert error.reason_code == reason
    assert error.retryable is retryable
    assert "sensitive-host" not in str(error)
    assert "SELECT" not in str(error)
    assert graph_run["owner_user_id"] not in str(error)
    assert factory.call_count == 1
    assert connection.rollback_count == 1
    assert connection.cursor_value.closed
    assert connection.closed


def test_connection_and_cursor_close_when_commit_or_fetch_validation_fails():
    envelope, graph_run, _, _ = _graph_contract()
    executor, _, connection = _enabled(
        {"rows": [_graph_result(graph_run)]}
    )

    def failing_commit():
        connection.events.append("commit")
        raise FakeDatabaseError("08006")

    connection.commit = failing_commit
    with pytest.raises(repository.DurableOrchestrationRepositoryError):
        executor.create_graph_run(
            envelope,
            created_at=graph_run["created_at"],
        )

    assert connection.rollback_count == 1
    assert connection.cursor_value.closed
    assert connection.closed


def test_only_existing_prepared_commands_execute_and_static_contracts_stay_pure():
    repository_source = REPOSITORY_PATH.read_text(encoding="utf-8")
    store_source = STORE_PATH.read_text(encoding="utf-8")
    schema_source = SCHEMA_PATH.read_text(encoding="utf-8")

    for helper in (
        "prepare_graph_run_row",
        "prepare_graph_run_insert",
        "prepare_current_graph_run_read",
        "prepare_current_checkpoint_read",
        "prepare_pending_interrupt_read",
        "prepare_checkpoint_interrupt_commit",
    ):
        assert f"store.{helper}(" in repository_source
    assert ".execute(" not in store_source
    assert "database_connection_opened" in store_source
    assert '"database_connection_opened": False' in store_source
    assert schema_source.startswith(
        "-- Static PostgreSQL contract only. This artifact is not executed"
    )
    for ddl in ("CREATE TABLE", "ALTER TABLE", "DROP TABLE"):
        assert ddl not in repository_source


def test_repository_import_boundary_and_public_surface_are_narrow():
    source = REPOSITORY_PATH.read_text(encoding="utf-8")
    forbidden_import_fragments = (
        "src.agents",
        "src.pipeline",
        "src.app",
        "src.services",
        "src.cli",
        "src.scheduler",
        "langgraph",
        "provider",
        "application_action",
    )
    for fragment in forbidden_import_fragments:
        assert fragment not in source

    public_methods = {
        name
        for name, value in vars(
            repository.DurableOrchestrationRepository
        ).items()
        if callable(value) and not name.startswith("_")
    }
    assert public_methods == {
        "probe_schema_readiness",
        "create_graph_run",
        "read_graph_run",
        "read_current_checkpoint",
        "read_pending_interrupt",
        "commit_checkpoint_interrupt",
    }
    for prohibited in (
        "record_decision",
        "authorize_resume",
        "consume_resume",
        "record_attempt",
        "record_terminal_result",
        "recover_run",
        "append_lifecycle_event",
    ):
        assert not hasattr(
            repository.DurableOrchestrationRepository,
            prohibited,
        )
