"""Explicit agent state migration runner helpers.

This module is intentionally inert on import. It reads no files, opens no
database connections, commits no transactions, and schedules no work. Callers
must provide both schema SQL text and an explicit cursor-like object.
"""

from __future__ import annotations

from typing import Any


TARGET_TABLES: tuple[str, str] = ("agent_runs", "agent_steps")
FORBIDDEN_SCOPE_TERMS: tuple[str, ...] = (
    "approval_requests",
    "agentic_approvals",
    "application_execution",
    "application_submissions",
)

SAFETY_FLAGS: dict[str, bool] = {
    "did_create_connection": False,
    "did_commit_transaction": False,
    "did_schedule_background_work": False,
    "did_execute_scheduler": False,
    "did_execute_reporting_job": False,
    "did_export_files": False,
    "did_execute_application": False,
    "did_submit_application": False,
    "api_route_added": False,
    "ui_action_added": False,
}


def _normalize_schema_sql(schema_sql: str) -> str:
    if not isinstance(schema_sql, str):
        raise TypeError("schema_sql must be a string.")
    normalized = schema_sql.strip()
    if not normalized:
        raise ValueError("schema_sql is required.")
    return normalized


def _without_line_comment(line: str) -> str:
    in_single_quote = False
    index = 0
    while index < len(line):
        char = line[index]
        next_char = line[index + 1] if index + 1 < len(line) else ""
        if char == "'":
            if in_single_quote and next_char == "'":
                index += 2
                continue
            in_single_quote = not in_single_quote
        if not in_single_quote and char == "-" and next_char == "-":
            return line[:index]
        index += 1
    return line


def _strip_sql_comments(schema_sql: str) -> str:
    return "\n".join(_without_line_comment(line) for line in schema_sql.splitlines())


def _split_sql_statements(schema_sql: str) -> tuple[str, ...]:
    cleaned_sql = _strip_sql_comments(schema_sql)
    statements: list[str] = []
    current: list[str] = []
    in_single_quote = False
    index = 0
    while index < len(cleaned_sql):
        char = cleaned_sql[index]
        next_char = cleaned_sql[index + 1] if index + 1 < len(cleaned_sql) else ""
        if char == "'":
            current.append(char)
            if in_single_quote and next_char == "'":
                current.append(next_char)
                index += 2
                continue
            in_single_quote = not in_single_quote
            index += 1
            continue
        if char == ";" and not in_single_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []
            index += 1
            continue
        current.append(char)
        index += 1
    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)
    return tuple(statements)


def _validate_agent_state_schema_scope(schema_sql: str) -> None:
    lowered = schema_sql.lower()
    missing_tables = [table for table in TARGET_TABLES if table not in lowered]
    if missing_tables:
        raise ValueError(
            "agent state schema scope is missing required table(s): "
            + ", ".join(missing_tables)
        )
    forbidden_terms = [term for term in FORBIDDEN_SCOPE_TERMS if term in lowered]
    if forbidden_terms:
        raise ValueError(
            "agent state schema scope includes forbidden term(s): "
            + ", ".join(forbidden_terms)
        )


def _metadata(statements: tuple[str, ...], *, did_run_migration: bool) -> dict[str, Any]:
    return {
        "migration_scope": "agent_state",
        "target_tables": list(TARGET_TABLES),
        "statement_count": len(statements),
        "did_run_migration": did_run_migration,
        **SAFETY_FLAGS,
    }


def build_agent_state_migration_plan(schema_sql: str) -> dict[str, Any]:
    """Build a deterministic migration plan from caller-supplied SQL text."""

    normalized_sql = _normalize_schema_sql(schema_sql)
    _validate_agent_state_schema_scope(normalized_sql)
    statements = _split_sql_statements(normalized_sql)
    if not statements:
        raise ValueError("schema_sql contains no executable statements.")
    return {
        "operation": "build_agent_state_migration_plan",
        "statements": list(statements),
        **_metadata(statements, did_run_migration=False),
    }


def run_agent_state_migration(cursor: Any, schema_sql: str) -> dict[str, Any]:
    """Run the prepared agent state schema statements on an injected cursor."""

    if cursor is None or not hasattr(cursor, "execute"):
        raise TypeError("cursor must provide an execute method.")
    plan = build_agent_state_migration_plan(schema_sql)
    statements = tuple(plan["statements"])
    for statement in statements:
        cursor.execute(statement)
    return {
        "operation": "run_agent_state_migration",
        "executed_statement_count": len(statements),
        "statements": list(statements),
        **_metadata(statements, did_run_migration=True),
    }
