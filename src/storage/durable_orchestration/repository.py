"""Default-off executor for the first durable-orchestration storage subset.

The repository owns DB-API resource and transaction boundaries.  SQL for
graph-run, checkpoint, and interrupt operations remains owned by ``store``.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Mapping, Protocol, Sequence

from src.storage.durable_orchestration import store


CAPABILITY_NAME = (
    "APPLYLENS_DURABLE_ORCHESTRATION_RUNTIME_REPOSITORY_ENABLED"
)

RESULT_CLASSIFICATIONS = (
    "applied",
    "idempotent_existing",
    "not_found",
    "stale_state",
    "identity_mismatch",
    "already_terminal",
    "duplicate_conflict",
    "unavailable",
    "transaction_failed",
)

_TERMINAL_RUN_STATUSES = {"completed", "failed", "cancelled"}
_GRAPH_IDENTITY_FIELDS = (
    "graph_invocation_id",
    "graph_engine",
    "graph_state_schema_version",
    "owner_user_id",
    "pipeline_run_id",
    "context_id",
    "job_id",
    "job_index",
    "selected_resume_id",
)
_GRAPH_RESULT_FIELDS = (
    "graph_invocation_id",
    "owner_user_id",
    "run_status",
    "current_checkpoint_id",
    "lock_version",
)
_CHECKPOINT_RESULT_FIELDS = (
    "checkpoint_id",
    "graph_invocation_id",
    "owner_user_id",
    "checkpoint_status",
    "checkpoint_schema_version",
    "graph_state_schema_version",
    "checkpoint_envelope_digest",
    "next_node_key",
)
_INTERRUPT_RESULT_FIELDS = (
    "interrupt_request_id",
    "graph_invocation_id",
    "checkpoint_id",
    "owner_user_id",
    "interrupt_status",
    "lock_version",
    "node_key",
    "safe_next_node_key",
    "read_only",
    "diagnostic_only",
    "application_authorization",
    "resume_authorization",
)

_READINESS_REQUIREMENTS: Mapping[str, Mapping[str, tuple[str, ...]]] = {
    "orchestration_graph_runs": {
        "columns": (
            "graph_invocation_id",
            "owner_user_id",
            "run_status",
            "current_checkpoint_id",
            "lock_version",
        ),
        "primary_key": ("graph_invocation_id",),
        "constraints": ("uq_orchestration_graph_runs_bound_identity",),
    },
    "orchestration_checkpoints": {
        "columns": (
            "checkpoint_id",
            "graph_invocation_id",
            "owner_user_id",
            "checkpoint_envelope_digest",
            "next_node_key",
        ),
        "primary_key": ("checkpoint_id",),
        "constraints": (
            "fk_orchestration_checkpoints_graph_run",
            "uq_orchestration_checkpoints_bound_identity",
        ),
    },
    "orchestration_interrupt_requests": {
        "columns": (
            "interrupt_request_id",
            "graph_invocation_id",
            "checkpoint_id",
            "owner_user_id",
            "interrupt_status",
            "lock_version",
            "node_key",
        ),
        "primary_key": ("interrupt_request_id",),
        "constraints": (
            "fk_orchestration_interrupt_requests_graph_run",
            "fk_orchestration_interrupt_requests_checkpoint",
            "fk_orchestration_interrupt_requests_bound_checkpoint",
            "uq_orchestration_interrupt_requests_checkpoint_node",
        ),
    },
}

_READINESS_SQL = """
WITH required_objects(object_name) AS (
    VALUES
        ('orchestration_graph_runs'),
        ('orchestration_checkpoints'),
        ('orchestration_interrupt_requests')
)
SELECT
    required.object_name,
    table_info.oid IS NOT NULL AS present,
    COALESCE(columns.column_names, ARRAY[]::text[]) AS columns,
    COALESCE(primary_key.column_names, ARRAY[]::text[])
        AS primary_key_columns,
    COALESCE(constraints.constraint_names, ARRAY[]::text[])
        AS constraint_names
FROM required_objects AS required
LEFT JOIN pg_catalog.pg_class AS table_info
  ON table_info.relname = required.object_name
 AND table_info.relkind IN ('r', 'p')
 AND table_info.relnamespace = (
     SELECT oid
     FROM pg_catalog.pg_namespace
     WHERE nspname = current_schema()
 )
LEFT JOIN LATERAL (
    SELECT array_agg(attribute.attname ORDER BY attribute.attnum)
        AS column_names
    FROM pg_catalog.pg_attribute AS attribute
    WHERE attribute.attrelid = table_info.oid
      AND attribute.attnum > 0
      AND NOT attribute.attisdropped
) AS columns ON TRUE
LEFT JOIN LATERAL (
    SELECT array_agg(attribute.attname ORDER BY key_position.ordinality)
        AS column_names
    FROM pg_catalog.pg_constraint AS constraint_info
    JOIN unnest(constraint_info.conkey) WITH ORDINALITY
      AS key_position(attribute_number, ordinality) ON TRUE
    JOIN pg_catalog.pg_attribute AS attribute
      ON attribute.attrelid = constraint_info.conrelid
     AND attribute.attnum = key_position.attribute_number
    WHERE constraint_info.conrelid = table_info.oid
      AND constraint_info.contype = 'p'
) AS primary_key ON TRUE
LEFT JOIN LATERAL (
    SELECT array_agg(constraint_info.conname ORDER BY constraint_info.conname)
        AS constraint_names
    FROM pg_catalog.pg_constraint AS constraint_info
    WHERE constraint_info.conrelid = table_info.oid
) AS constraints ON TRUE
ORDER BY required.object_name
""".strip()


class CursorProtocol(Protocol):
    description: Sequence[Sequence[Any]] | None

    def execute(self, sql: str, params: Mapping[str, Any]) -> Any: ...

    def fetchall(self) -> Sequence[Any]: ...

    def close(self) -> Any: ...


class ConnectionProtocol(Protocol):
    def cursor(self) -> CursorProtocol: ...

    def commit(self) -> Any: ...

    def rollback(self) -> Any: ...

    def close(self) -> Any: ...


ConnectionFactory = Callable[[], ConnectionProtocol]


def _freeze(value: Any) -> Any:
    if isinstance(value, Mapping):
        return MappingProxyType(
            {str(key): _freeze(nested) for key, nested in value.items()}
        )
    if isinstance(value, (list, tuple)):
        return tuple(_freeze(nested) for nested in value)
    if isinstance(value, set):
        return frozenset(_freeze(nested) for nested in value)
    return deepcopy(value)


@dataclass(frozen=True, slots=True)
class RepositoryResult:
    operation: str
    classification: str
    record: Mapping[str, Any]
    metadata: Mapping[str, Any]

    @classmethod
    def build(
        cls,
        *,
        operation: str,
        classification: str,
        record: Mapping[str, Any] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "RepositoryResult":
        if classification not in RESULT_CLASSIFICATIONS:
            raise ValueError("repository_result_classification_invalid")
        return cls(
            operation=operation,
            classification=classification,
            record=_freeze(record or {}),
            metadata=_freeze(metadata or {}),
        )


class DurableOrchestrationRepositoryError(RuntimeError):
    """Bounded failure without SQL, parameter, or connection details."""

    def __init__(
        self,
        *,
        operation: str,
        classification: str,
        reason_code: str,
        retryable: bool = False,
    ) -> None:
        if classification not in RESULT_CLASSIFICATIONS:
            classification = "transaction_failed"
        self.operation = operation
        self.classification = classification
        self.reason_code = reason_code
        self.retryable = retryable
        super().__init__(
            f"durable_orchestration_repository:{operation}:"
            f"{classification}:{reason_code}"
        )


class DurableOrchestrationRepositoryDisabled(
    DurableOrchestrationRepositoryError
):
    pass


def _database_failure(
    operation: str,
    error: BaseException,
) -> DurableOrchestrationRepositoryError:
    sqlstate = str(
        getattr(error, "sqlstate", None)
        or getattr(error, "pgcode", None)
        or ""
    ).strip()
    if sqlstate == "40001":
        return DurableOrchestrationRepositoryError(
            operation=operation,
            classification="transaction_failed",
            reason_code="serialization_failure",
            retryable=True,
        )
    if sqlstate == "40P01":
        return DurableOrchestrationRepositoryError(
            operation=operation,
            classification="transaction_failed",
            reason_code="deadlock",
            retryable=True,
        )
    if sqlstate == "23505":
        return DurableOrchestrationRepositoryError(
            operation=operation,
            classification="duplicate_conflict",
            reason_code="unique_violation",
        )
    if sqlstate == "23503":
        return DurableOrchestrationRepositoryError(
            operation=operation,
            classification="identity_mismatch",
            reason_code="foreign_key_violation",
        )
    if sqlstate == "23514":
        return DurableOrchestrationRepositoryError(
            operation=operation,
            classification="transaction_failed",
            reason_code="check_violation",
        )
    if sqlstate.startswith("08") or "connection" in type(error).__name__.lower():
        return DurableOrchestrationRepositoryError(
            operation=operation,
            classification="unavailable",
            reason_code="connection_unavailable",
        )
    return DurableOrchestrationRepositoryError(
        operation=operation,
        classification="transaction_failed",
        reason_code="database_failure",
    )


def _rows(cursor: CursorProtocol) -> list[dict[str, Any]]:
    fetched = list(cursor.fetchall())
    if not fetched:
        return []
    if all(isinstance(row, Mapping) for row in fetched):
        return [deepcopy(dict(row)) for row in fetched]
    description = getattr(cursor, "description", None)
    if not description:
        raise ValueError("returned_row_description_missing")
    columns = tuple(str(column[0]) for column in description)
    if not columns or len(columns) != len(set(columns)):
        raise ValueError("returned_row_description_invalid")
    normalized: list[dict[str, Any]] = []
    for row in fetched:
        if not isinstance(row, (list, tuple)) or len(row) != len(columns):
            raise ValueError("returned_row_malformed")
        normalized.append(dict(zip(columns, row)))
    return normalized


def _require_fields(
    row: Mapping[str, Any],
    fields: Sequence[str],
) -> None:
    if any(field not in row for field in fields):
        raise ValueError("returned_row_required_fields_missing")


def _bounded_record(
    row: Mapping[str, Any],
    fields: Sequence[str],
) -> dict[str, Any]:
    _require_fields(row, fields)
    return {field: deepcopy(row[field]) for field in fields}


class DurableOrchestrationRepository:
    """Injected, explicitly enabled DB-API executor."""

    def __init__(
        self,
        connection_factory: ConnectionFactory,
        *,
        enabled: bool = False,
    ) -> None:
        if not enabled:
            raise DurableOrchestrationRepositoryDisabled(
                operation="construct",
                classification="unavailable",
                reason_code="capability_disabled",
            )
        if not callable(connection_factory):
            raise TypeError("connection_factory must be callable")
        self._connection_factory = connection_factory

    def _open(self, operation: str) -> tuple[ConnectionProtocol, CursorProtocol]:
        connection: ConnectionProtocol | None = None
        try:
            connection = self._connection_factory()
            cursor = connection.cursor()
            return connection, cursor
        except Exception as exc:
            self._rollback(connection)
            self._close(None, connection)
            raise _database_failure(operation, exc) from exc

    @staticmethod
    def _rollback(connection: ConnectionProtocol | None) -> None:
        if connection is None:
            return
        try:
            connection.rollback()
        except Exception:
            pass

    @staticmethod
    def _close(
        cursor: CursorProtocol | None,
        connection: ConnectionProtocol | None,
    ) -> None:
        if cursor is not None:
            try:
                cursor.close()
            except Exception:
                pass
        if connection is not None:
            try:
                connection.close()
            except Exception:
                pass

    def probe_schema_readiness(self) -> RepositoryResult:
        operation = "probe_schema_readiness"
        connection: ConnectionProtocol | None = None
        cursor: CursorProtocol | None = None
        try:
            connection, cursor = self._open(operation)
            cursor.execute(_READINESS_SQL, {})
            rows = _rows(cursor)
            if len(rows) != len(_READINESS_REQUIREMENTS):
                self._rollback(connection)
                return RepositoryResult.build(
                    operation=operation,
                    classification="unavailable",
                    metadata={
                        "ready": False,
                        "missing_objects": tuple(_READINESS_REQUIREMENTS),
                        "incompatible_objects": (),
                    },
                )
            by_name: dict[str, Mapping[str, Any]] = {}
            for row in rows:
                _require_fields(
                    row,
                    (
                        "object_name",
                        "present",
                        "columns",
                        "primary_key_columns",
                        "constraint_names",
                    ),
                )
                name = str(row["object_name"])
                if name in by_name or name not in _READINESS_REQUIREMENTS:
                    raise ValueError("readiness_object_invalid")
                by_name[name] = row
            missing: list[str] = []
            incompatible: list[str] = []
            for name, requirement in _READINESS_REQUIREMENTS.items():
                row = by_name.get(name)
                if row is None or row["present"] is not True:
                    missing.append(name)
                    continue
                columns = set(row["columns"] or ())
                primary_key = tuple(row["primary_key_columns"] or ())
                constraints = set(row["constraint_names"] or ())
                if (
                    not set(requirement["columns"]) <= columns
                    or primary_key != requirement["primary_key"]
                    or not set(requirement["constraints"]) <= constraints
                ):
                    incompatible.append(name)
            ready = not missing and not incompatible
            if not ready:
                self._rollback(connection)
            return RepositoryResult.build(
                operation=operation,
                classification="applied" if ready else "unavailable",
                metadata={
                    "ready": ready,
                    "checked_objects": tuple(_READINESS_REQUIREMENTS),
                    "missing_objects": tuple(missing),
                    "incompatible_objects": tuple(incompatible),
                },
            )
        except DurableOrchestrationRepositoryError:
            self._rollback(connection)
            raise
        except Exception as exc:
            self._rollback(connection)
            if isinstance(exc, ValueError):
                raise DurableOrchestrationRepositoryError(
                    operation=operation,
                    classification="unavailable",
                    reason_code="readiness_result_invalid",
                ) from exc
            raise _database_failure(operation, exc) from exc
        finally:
            self._close(cursor, connection)

    def create_graph_run(
        self,
        checkpoint_identity_or_envelope: Mapping[str, Any],
        *,
        created_at: str,
        updated_at: str = "",
        run_status: str = "running",
        current_checkpoint_id: str | None = None,
        lock_version: int = 0,
        terminal_at: str | None = None,
        purge_after: str | None = None,
    ) -> RepositoryResult:
        operation = "create_graph_run"
        row = store.prepare_graph_run_row(
            checkpoint_identity_or_envelope,
            created_at=created_at,
            updated_at=updated_at,
            run_status=run_status,
            current_checkpoint_id=current_checkpoint_id,
            lock_version=lock_version,
            terminal_at=terminal_at,
            purge_after=purge_after,
        )
        command = store.prepare_graph_run_insert(row)
        connection: ConnectionProtocol | None = None
        cursor: CursorProtocol | None = None
        try:
            connection, cursor = self._open(operation)
            cursor.execute(command["sql"], command["params"])
            returned = _rows(cursor)
            if not returned:
                self._rollback(connection)
                return RepositoryResult.build(
                    operation=operation,
                    classification="duplicate_conflict",
                )
            if len(returned) != 1:
                raise ValueError("returned_row_count_invalid")
            result_row = returned[0]
            _require_fields(
                result_row,
                (*tuple(row), "idempotent_duplicate"),
            )
            comparable_fields = (
                *_GRAPH_IDENTITY_FIELDS,
                "run_status",
                "current_checkpoint_id",
                "lock_version",
            )
            if any(
                result_row[field] != row[field]
                for field in comparable_fields
            ) or any(
                result_row[field] is None
                for field in ("created_at", "updated_at")
            ):
                raise ValueError("graph_run_returned_row_mismatch")
            duplicate = result_row["idempotent_duplicate"]
            if not isinstance(duplicate, bool):
                raise ValueError("idempotent_duplicate_invalid")
            connection.commit()
            return RepositoryResult.build(
                operation=operation,
                classification=(
                    "idempotent_existing" if duplicate else "applied"
                ),
                record=_bounded_record(result_row, _GRAPH_RESULT_FIELDS),
            )
        except DurableOrchestrationRepositoryError:
            self._rollback(connection)
            raise
        except Exception as exc:
            self._rollback(connection)
            if isinstance(exc, ValueError):
                raise DurableOrchestrationRepositoryError(
                    operation=operation,
                    classification="identity_mismatch",
                    reason_code="returned_graph_run_invalid",
                ) from exc
            raise _database_failure(operation, exc) from exc
        finally:
            self._close(cursor, connection)

    def read_graph_run(
        self,
        *,
        owner_user_id: str,
        graph_invocation_id: str,
    ) -> RepositoryResult:
        command = store.prepare_current_graph_run_read(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        return self._execute_owner_read(
            operation="read_graph_run",
            command=command,
            required_fields=_GRAPH_RESULT_FIELDS,
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )

    def read_current_checkpoint(
        self,
        *,
        owner_user_id: str,
        graph_invocation_id: str,
    ) -> RepositoryResult:
        command = store.prepare_current_checkpoint_read(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        return self._execute_owner_read(
            operation="read_current_checkpoint",
            command=command,
            required_fields=_CHECKPOINT_RESULT_FIELDS,
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )

    def read_pending_interrupt(
        self,
        *,
        owner_user_id: str,
        graph_invocation_id: str,
    ) -> RepositoryResult:
        command = store.prepare_pending_interrupt_read(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        return self._execute_owner_read(
            operation="read_pending_interrupt",
            command=command,
            required_fields=_INTERRUPT_RESULT_FIELDS,
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )

    def _execute_owner_read(
        self,
        *,
        operation: str,
        command: Mapping[str, Any],
        required_fields: Sequence[str],
        owner_user_id: str,
        graph_invocation_id: str,
    ) -> RepositoryResult:
        connection: ConnectionProtocol | None = None
        cursor: CursorProtocol | None = None
        try:
            connection, cursor = self._open(operation)
            cursor.execute(command["sql"], command["params"])
            returned = _rows(cursor)
            if not returned:
                return RepositoryResult.build(
                    operation=operation,
                    classification="not_found",
                )
            if len(returned) != 1:
                raise ValueError("returned_row_count_invalid")
            row = returned[0]
            _require_fields(row, required_fields)
            if (
                row["owner_user_id"] != owner_user_id
                or row["graph_invocation_id"] != graph_invocation_id
            ):
                raise ValueError("returned_identity_mismatch")
            return RepositoryResult.build(
                operation=operation,
                classification="applied",
                record=_bounded_record(row, required_fields),
            )
        except DurableOrchestrationRepositoryError:
            self._rollback(connection)
            raise
        except Exception as exc:
            self._rollback(connection)
            if isinstance(exc, ValueError):
                raise DurableOrchestrationRepositoryError(
                    operation=operation,
                    classification="identity_mismatch",
                    reason_code="returned_read_row_invalid",
                ) from exc
            raise _database_failure(operation, exc) from exc
        finally:
            self._close(cursor, connection)

    def commit_checkpoint_interrupt(
        self,
        *,
        graph_invocation_id: str,
        owner_user_id: str,
        expected_run_status: str,
        expected_lock_version: int,
        expected_current_checkpoint_id: str | None,
        checkpoint_row: Mapping[str, Any],
        interrupt_row: Mapping[str, Any],
    ) -> RepositoryResult:
        operation = "commit_checkpoint_interrupt"
        if checkpoint_row.get("graph_invocation_id") != graph_invocation_id:
            raise ValueError("checkpoint_graph_invocation_id_mismatch")
        if interrupt_row.get("graph_invocation_id") != graph_invocation_id:
            raise ValueError("interrupt_graph_invocation_id_mismatch")
        if checkpoint_row.get("owner_user_id") != owner_user_id:
            raise ValueError("checkpoint_owner_user_id_mismatch")
        if interrupt_row.get("owner_user_id") != owner_user_id:
            raise ValueError("interrupt_owner_user_id_mismatch")
        command = store.prepare_checkpoint_interrupt_commit(
            checkpoint_row=checkpoint_row,
            interrupt_row=interrupt_row,
            expected_owner_user_id=owner_user_id,
            expected_run_status=expected_run_status,
            expected_lock_version=expected_lock_version,
            expected_current_checkpoint_id=expected_current_checkpoint_id,
        )
        connection: ConnectionProtocol | None = None
        cursor: CursorProtocol | None = None
        try:
            connection, cursor = self._open(operation)
            cursor.execute(command["sql"], command["params"])
            returned = _rows(cursor)
            if not returned:
                self._rollback(connection)
                classification = self._classify_zero_checkpoint_result(
                    cursor=cursor,
                    owner_user_id=owner_user_id,
                    graph_invocation_id=graph_invocation_id,
                    expected_run_status=expected_run_status,
                    expected_lock_version=expected_lock_version,
                    expected_current_checkpoint_id=(
                        expected_current_checkpoint_id
                    ),
                )
                return RepositoryResult.build(
                    operation=operation,
                    classification=classification,
                )
            if len(returned) != 1:
                raise ValueError("returned_row_count_invalid")
            row = returned[0]
            _require_fields(row, _GRAPH_RESULT_FIELDS)
            if (
                row["graph_invocation_id"] != graph_invocation_id
                or row["owner_user_id"] != owner_user_id
                or row["current_checkpoint_id"]
                != checkpoint_row["checkpoint_id"]
                or row["run_status"] != "awaiting_decision"
                or row["lock_version"] != expected_lock_version + 1
            ):
                raise ValueError("advanced_graph_run_invalid")
            connection.commit()
            return RepositoryResult.build(
                operation=operation,
                classification="applied",
                record=_bounded_record(row, _GRAPH_RESULT_FIELDS),
            )
        except DurableOrchestrationRepositoryError:
            self._rollback(connection)
            raise
        except Exception as exc:
            self._rollback(connection)
            if isinstance(exc, ValueError):
                raise DurableOrchestrationRepositoryError(
                    operation=operation,
                    classification="transaction_failed",
                    reason_code="checkpoint_interrupt_result_invalid",
                ) from exc
            raise _database_failure(operation, exc) from exc
        finally:
            self._close(cursor, connection)

    @staticmethod
    def _classify_zero_checkpoint_result(
        *,
        cursor: CursorProtocol,
        owner_user_id: str,
        graph_invocation_id: str,
        expected_run_status: str,
        expected_lock_version: int,
        expected_current_checkpoint_id: str | None,
    ) -> str:
        command = store.prepare_current_graph_run_read(
            owner_user_id=owner_user_id,
            graph_invocation_id=graph_invocation_id,
        )
        cursor.execute(command["sql"], command["params"])
        rows = _rows(cursor)
        if not rows:
            return "identity_mismatch"
        if len(rows) != 1:
            raise ValueError("classification_row_count_invalid")
        row = rows[0]
        _require_fields(row, _GRAPH_RESULT_FIELDS)
        if (
            row["owner_user_id"] != owner_user_id
            or row["graph_invocation_id"] != graph_invocation_id
        ):
            return "identity_mismatch"
        if row["run_status"] in _TERMINAL_RUN_STATUSES:
            return "already_terminal"
        if (
            row["run_status"] != expected_run_status
            or row["lock_version"] != expected_lock_version
            or row["current_checkpoint_id"]
            != expected_current_checkpoint_id
        ):
            return "stale_state"
        return "duplicate_conflict"


__all__ = [
    "CAPABILITY_NAME",
    "ConnectionFactory",
    "DurableOrchestrationRepository",
    "DurableOrchestrationRepositoryDisabled",
    "DurableOrchestrationRepositoryError",
    "RepositoryResult",
    "RESULT_CLASSIFICATIONS",
]
