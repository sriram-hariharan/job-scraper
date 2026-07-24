"""Explicit setup owner for package-managed LangGraph checkpoint tables.

The command is default-off, accepts one explicitly named database target, and
never runs from application startup.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import os
import re
from typing import Any, Mapping, Sequence

from langgraph.checkpoint.postgres import PostgresSaver

from src.storage.durable_orchestration import langgraph_postgres


SETUP_CAPABILITY_NAME = (
    "APPLYLENS_LANGGRAPH_POSTGRES_CHECKPOINTER_SCHEMA_SETUP_ENABLED"
)
GENERIC_DATABASE_URL_NAME = "DATABASE_URL"
SUPPORTED_SCHEMA = langgraph_postgres.LANGGRAPH_POSTGRES_SCHEMA
EXPECTED_PACKAGE_TABLES = (
    "checkpoint_migrations",
    "checkpoints",
    "checkpoint_blobs",
    "checkpoint_writes",
)
EXPECTED_COLUMNS = {
    "checkpoint_migrations": ("v",),
    "checkpoints": (
        "thread_id",
        "checkpoint_ns",
        "checkpoint_id",
        "parent_checkpoint_id",
        "type",
        "checkpoint",
        "metadata",
    ),
    "checkpoint_blobs": (
        "thread_id",
        "checkpoint_ns",
        "channel",
        "version",
        "type",
        "blob",
    ),
    "checkpoint_writes": (
        "thread_id",
        "checkpoint_ns",
        "checkpoint_id",
        "task_id",
        "idx",
        "channel",
        "type",
        "blob",
        "task_path",
    ),
}
EXPECTED_PRIMARY_KEYS = {
    "checkpoint_migrations": ("v",),
    "checkpoints": ("thread_id", "checkpoint_ns", "checkpoint_id"),
    "checkpoint_blobs": (
        "thread_id",
        "checkpoint_ns",
        "channel",
        "version",
    ),
    "checkpoint_writes": (
        "thread_id",
        "checkpoint_ns",
        "checkpoint_id",
        "task_id",
        "idx",
    ),
}
SUCCESS_OUTCOMES = frozenset({"planned", "absent", "compatible", "applied"})


@dataclass(frozen=True, slots=True)
class CheckpointerSetupResult:
    operation: str
    outcome: str
    schema: str
    object_count: int = 0
    migration_count: int = 0
    diagnostic_code: str = ""


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
        "enabled",
    }


def _validate_schema(value: Any) -> str:
    schema = str(value or "").strip()
    if schema != SUPPORTED_SCHEMA:
        raise ValueError("checkpointer_setup:schema_unsupported")
    return schema


def _validate_database_url_env(value: Any) -> str:
    name = str(value or "").strip()
    if (
        name == GENERIC_DATABASE_URL_NAME
        or re.fullmatch(r"[A-Z][A-Z0-9_]{2,127}", name) is None
    ):
        raise ValueError("checkpointer_setup:database_url_env_invalid")
    return name


def _mapping_rows(cursor: Any) -> list[Mapping[str, Any]]:
    rows = cursor.fetchall()
    if not isinstance(rows, list):
        rows = list(rows)
    if not all(isinstance(row, Mapping) for row in rows):
        raise ValueError("checkpointer_setup:catalog_rows_malformed")
    return rows


def _read_catalog(connection: Any, *, schema: str) -> dict[str, Any]:
    cursor = None
    try:
        cursor = connection.cursor()
        cursor.execute(
            """
            SELECT schema_name
            FROM information_schema.schemata
            WHERE schema_name = %(schema)s
            """,
            {"schema": schema},
        )
        schema_rows = _mapping_rows(cursor)
        schema_exists = len(schema_rows) == 1
        if schema_rows and set(schema_rows[0]) != {"schema_name"}:
            raise ValueError("checkpointer_setup:schema_catalog_malformed")

        cursor.execute(
            """
            SELECT table_schema, table_name, column_name, ordinal_position
            FROM information_schema.columns
            WHERE table_schema = ANY(%(schemas)s)
              AND table_name = ANY(%(tables)s)
            ORDER BY table_schema, table_name, ordinal_position
            """,
            {
                "schemas": [schema, "public"],
                "tables": list(EXPECTED_PACKAGE_TABLES),
            },
        )
        column_rows = _mapping_rows(cursor)

        cursor.execute(
            """
            SELECT namespace.nspname AS table_schema,
                   relation.relname AS table_name,
                   array_agg(attribute.attname ORDER BY key_part.ordinality)
                       AS primary_key_columns
            FROM pg_catalog.pg_constraint AS constraint_row
            JOIN pg_catalog.pg_class AS relation
              ON relation.oid = constraint_row.conrelid
            JOIN pg_catalog.pg_namespace AS namespace
              ON namespace.oid = relation.relnamespace
            JOIN unnest(constraint_row.conkey) WITH ORDINALITY
              AS key_part(attnum, ordinality) ON TRUE
            JOIN pg_catalog.pg_attribute AS attribute
              ON attribute.attrelid = relation.oid
             AND attribute.attnum = key_part.attnum
            WHERE constraint_row.contype = 'p'
              AND namespace.nspname = ANY(%(schemas)s)
              AND relation.relname = ANY(%(tables)s)
            GROUP BY namespace.nspname, relation.relname
            ORDER BY namespace.nspname, relation.relname
            """,
            {
                "schemas": [schema, "public"],
                "tables": list(EXPECTED_PACKAGE_TABLES),
            },
        )
        primary_key_rows = _mapping_rows(cursor)

        columns: dict[tuple[str, str], list[tuple[int, str]]] = {}
        for row in column_rows:
            if set(row) != {
                "table_schema",
                "table_name",
                "column_name",
                "ordinal_position",
            }:
                raise ValueError("checkpointer_setup:column_catalog_malformed")
            table_schema = str(row["table_schema"])
            table_name = str(row["table_name"])
            column_name = str(row["column_name"])
            ordinal_position = row["ordinal_position"]
            if (
                table_schema not in {schema, "public"}
                or table_name not in EXPECTED_PACKAGE_TABLES
                or not column_name
                or isinstance(ordinal_position, bool)
                or not isinstance(ordinal_position, int)
            ):
                raise ValueError("checkpointer_setup:column_catalog_malformed")
            columns.setdefault((table_schema, table_name), []).append(
                (ordinal_position, column_name)
            )

        primary_keys: dict[tuple[str, str], tuple[str, ...]] = {}
        for row in primary_key_rows:
            if set(row) != {
                "table_schema",
                "table_name",
                "primary_key_columns",
            }:
                raise ValueError(
                    "checkpointer_setup:primary_key_catalog_malformed"
                )
            key = (str(row["table_schema"]), str(row["table_name"]))
            raw_columns = row["primary_key_columns"]
            if (
                key[0] not in {schema, "public"}
                or key[1] not in EXPECTED_PACKAGE_TABLES
                or not isinstance(raw_columns, (list, tuple))
                or not all(
                    isinstance(column, str) and bool(column)
                    for column in raw_columns
                )
            ):
                raise ValueError(
                    "checkpointer_setup:primary_key_catalog_malformed"
                )
            primary_keys[key] = tuple(raw_columns)

        public_tables = {
            table_name
            for table_schema, table_name in columns
            if table_schema == "public"
        }
        dedicated_tables = {
            table_name
            for table_schema, table_name in columns
            if table_schema == schema
        }
        result: dict[str, Any] = {
            "schema_exists": schema_exists,
            "public_tables": public_tables,
            "dedicated_tables": dedicated_tables,
            "columns": {
                key: tuple(
                    column
                    for _, column in sorted(value, key=lambda item: item[0])
                )
                for key, value in columns.items()
            },
            "primary_keys": primary_keys,
            "migrations": (),
        }
        if dedicated_tables == set(EXPECTED_PACKAGE_TABLES):
            cursor.execute(
                """
                SELECT v
                FROM applylens_langgraph_checkpoint.checkpoint_migrations
                ORDER BY v
                """,
                {},
            )
            migration_rows = _mapping_rows(cursor)
            migrations = []
            for row in migration_rows:
                if set(row) != {"v"} or isinstance(row["v"], bool) or not isinstance(
                    row["v"], int
                ):
                    raise ValueError(
                        "checkpointer_setup:migration_catalog_malformed"
                    )
                migrations.append(row["v"])
            result["migrations"] = tuple(migrations)
        return result
    finally:
        if cursor is not None:
            cursor.close()


def _classify_catalog(
    catalog: Mapping[str, Any],
    *,
    schema: str = SUPPORTED_SCHEMA,
) -> CheckpointerSetupResult:
    expected = set(EXPECTED_PACKAGE_TABLES)
    public_tables = set(catalog.get("public_tables") or ())
    dedicated_tables = set(catalog.get("dedicated_tables") or ())
    if not public_tables <= expected or not dedicated_tables <= expected:
        return CheckpointerSetupResult(
            operation="check",
            outcome="incompatible",
            schema=schema,
            object_count=len(dedicated_tables),
            diagnostic_code="unexpected_catalog_table",
        )
    if public_tables:
        return CheckpointerSetupResult(
            operation="check",
            outcome="incompatible",
            schema=schema,
            object_count=len(dedicated_tables),
            diagnostic_code="package_table_in_public",
        )
    if not dedicated_tables:
        return CheckpointerSetupResult(
            operation="check",
            outcome="absent",
            schema=schema,
        )
    if dedicated_tables != expected:
        return CheckpointerSetupResult(
            operation="check",
            outcome="partial",
            schema=schema,
            object_count=len(dedicated_tables),
            diagnostic_code="partial_package_schema",
        )

    columns = catalog.get("columns")
    primary_keys = catalog.get("primary_keys")
    migrations = catalog.get("migrations")
    if (
        not isinstance(columns, Mapping)
        or not isinstance(primary_keys, Mapping)
        or not isinstance(migrations, (list, tuple))
    ):
        return CheckpointerSetupResult(
            operation="check",
            outcome="incompatible",
            schema=schema,
            object_count=len(expected),
            diagnostic_code="catalog_shape_invalid",
        )
    for table_name in EXPECTED_PACKAGE_TABLES:
        key = (schema, table_name)
        if (
            tuple(columns.get(key) or ()) != EXPECTED_COLUMNS[table_name]
            or tuple(primary_keys.get(key) or ())
            != EXPECTED_PRIMARY_KEYS[table_name]
        ):
            return CheckpointerSetupResult(
                operation="check",
                outcome="incompatible",
                schema=schema,
                object_count=len(expected),
                diagnostic_code="package_table_contract_mismatch",
            )
    expected_migrations = tuple(range(len(PostgresSaver.MIGRATIONS)))
    if tuple(migrations) != expected_migrations:
        return CheckpointerSetupResult(
            operation="check",
            outcome="incompatible",
            schema=schema,
            object_count=len(expected),
            migration_count=len(migrations),
            diagnostic_code="package_migration_state_invalid",
        )
    return CheckpointerSetupResult(
        operation="check",
        outcome="compatible",
        schema=schema,
        object_count=len(expected),
        migration_count=len(migrations),
    )


class LangGraphCheckpointerSetup:
    """Explicit plan/check/apply owner for the package schema."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        database_url: str = "",
        schema: str = SUPPORTED_SCHEMA,
    ) -> None:
        self._enabled = enabled is True
        self._database_url = str(database_url or "").strip()
        self._schema = _validate_schema(schema)

    def plan(self) -> CheckpointerSetupResult:
        return CheckpointerSetupResult(
            operation="plan",
            outcome="planned",
            schema=self._schema,
            object_count=len(EXPECTED_PACKAGE_TABLES),
            migration_count=len(PostgresSaver.MIGRATIONS),
        )

    def check(self) -> CheckpointerSetupResult:
        try:
            with langgraph_postgres.open_langgraph_postgres_connection(
                enabled=True,
                database_url=self._database_url,
                schema=self._schema,
                application_name="applylens-langgraph-checkpointer-setup-check",
            ) as connection:
                catalog = _read_catalog(connection, schema=self._schema)
            return _classify_catalog(catalog, schema=self._schema)
        except (langgraph_postgres.LangGraphPostgresSaverError, ValueError):
            return CheckpointerSetupResult(
                operation="check",
                outcome="unavailable",
                schema=self._schema,
                diagnostic_code="catalog_inspection_failed",
            )
        except Exception:
            return CheckpointerSetupResult(
                operation="check",
                outcome="unavailable",
                schema=self._schema,
                diagnostic_code="catalog_inspection_failed",
            )

    def apply(self) -> CheckpointerSetupResult:
        if not self._enabled:
            return CheckpointerSetupResult(
                operation="apply",
                outcome="disabled",
                schema=self._schema,
                diagnostic_code="setup_capability_disabled",
            )
        preflight = self.check()
        if preflight.outcome == "compatible":
            return CheckpointerSetupResult(
                operation="apply",
                outcome="compatible",
                schema=self._schema,
                object_count=preflight.object_count,
                migration_count=preflight.migration_count,
            )
        if preflight.outcome != "absent":
            return CheckpointerSetupResult(
                operation="apply",
                outcome=preflight.outcome,
                schema=self._schema,
                object_count=preflight.object_count,
                migration_count=preflight.migration_count,
                diagnostic_code=preflight.diagnostic_code,
            )
        try:
            with langgraph_postgres.open_langgraph_postgres_connection(
                enabled=True,
                database_url=self._database_url,
                schema=self._schema,
                application_name="applylens-langgraph-checkpointer-schema-create",
            ) as connection:
                cursor = connection.cursor()
                try:
                    cursor.execute(
                        "CREATE SCHEMA IF NOT EXISTS "
                        "applylens_langgraph_checkpoint"
                    )
                finally:
                    cursor.close()
            with langgraph_postgres.open_langgraph_postgres_saver(
                enabled=True,
                database_url=self._database_url,
                schema=self._schema,
                application_name="applylens-langgraph-checkpointer-setup",
            ) as saver:
                saver.setup()
        except Exception:
            return CheckpointerSetupResult(
                operation="apply",
                outcome="execution_failed",
                schema=self._schema,
                diagnostic_code="package_setup_failed",
            )
        postflight = self.check()
        if postflight.outcome != "compatible":
            return CheckpointerSetupResult(
                operation="apply",
                outcome="verification_failed",
                schema=self._schema,
                object_count=postflight.object_count,
                migration_count=postflight.migration_count,
                diagnostic_code=postflight.diagnostic_code,
            )
        return CheckpointerSetupResult(
            operation="apply",
            outcome="applied",
            schema=self._schema,
            object_count=postflight.object_count,
            migration_count=postflight.migration_count,
        )


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Explicit LangGraph PostgreSQL checkpointer schema setup."
    )
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument("--plan", action="store_true")
    operation.add_argument("--check", action="store_true")
    operation.add_argument("--apply", action="store_true")
    parser.add_argument("--database-url-env", required=True)
    parser.add_argument("--schema", required=True)
    return parser


def _print_result(result: CheckpointerSetupResult) -> None:
    fields = [
        f"operation={result.operation}",
        f"outcome={result.outcome}",
        f"schema={result.schema}",
        f"object_count={result.object_count}",
        f"migration_count={result.migration_count}",
    ]
    if result.diagnostic_code:
        fields.append(f"diagnostic_code={result.diagnostic_code}")
    print(" ".join(fields))


def main(
    argv: Sequence[str] | None = None,
    *,
    configuration: Mapping[str, Any] | None = None,
) -> int:
    args = _parser().parse_args(argv)
    config = os.environ if configuration is None else configuration
    try:
        schema = _validate_schema(args.schema)
        database_url_env = _validate_database_url_env(args.database_url_env)
    except ValueError:
        result = CheckpointerSetupResult(
            operation="validation",
            outcome="unavailable",
            schema=SUPPORTED_SCHEMA,
            diagnostic_code="configuration_invalid",
        )
        _print_result(result)
        return 1

    if args.plan:
        result = LangGraphCheckpointerSetup(schema=schema).plan()
    else:
        target = str(config.get(database_url_env, "") or "").strip()
        enabled = _truthy(config.get(SETUP_CAPABILITY_NAME))
        setup = LangGraphCheckpointerSetup(
            enabled=enabled,
            database_url=target,
            schema=schema,
        )
        result = setup.apply() if args.apply else setup.check()
    _print_result(result)
    return 0 if result.outcome in SUCCESS_OUTCOMES else 1


if __name__ == "__main__":
    raise SystemExit(main())
