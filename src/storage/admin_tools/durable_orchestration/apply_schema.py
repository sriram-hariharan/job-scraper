"""Explicit PostgreSQL schema owner for durable orchestration.

Direct invocation:

    python -m src.storage.admin_tools.durable_orchestration.apply_schema --plan
    python -m src.storage.admin_tools.durable_orchestration.apply_schema --check
    python -m src.storage.admin_tools.durable_orchestration.apply_schema --apply

The command is default-off and reads only the dedicated configuration named
below. Importing this module never reads configuration or invokes ``psql``.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import subprocess
from typing import Any, Callable, Mapping, Sequence


CAPABILITY_NAME = (
    "APPLYLENS_DURABLE_ORCHESTRATION_SCHEMA_EXECUTION_ENABLED"
)
DATABASE_URL_NAME = "APPLYLENS_DURABLE_ORCHESTRATION_DATABASE_URL"
TEST_DATABASE_URL_NAME = (
    "APPLYLENS_DURABLE_ORCHESTRATION_TEST_DATABASE_URL"
)
TEST_EXECUTION_CAPABILITY_NAME = (
    "APPLYLENS_DURABLE_ORCHESTRATION_TEST_SCHEMA_EXECUTION_ENABLED"
)
SCHEMA_CONTRACT_VERSION = "durable-orchestration-schema-v1"
SCHEMA_PATH = (
    Path(__file__).resolve().parents[2]
    / "durable_orchestration"
    / "schema.sql"
)
PSQL_TIMEOUT_SECONDS = 60
MAX_CAPTURED_OUTPUT_CHARS = 16_384

OUTCOMES = (
    "planned",
    "absent",
    "compatible",
    "applied",
    "partial",
    "incompatible",
    "disabled",
    "unavailable",
    "execution_failed",
    "verification_failed",
)

_EXPECTED_TABLES = (
    "orchestration_graph_runs",
    "orchestration_checkpoints",
    "orchestration_interrupt_requests",
    "orchestration_human_decisions",
    "orchestration_resume_authorizations",
    "orchestration_resume_consumptions",
    "orchestration_node_attempts",
    "orchestration_terminal_results",
    "orchestration_lifecycle_events",
)

_COMMON_IDENTITY_COLUMNS = (
    "owner_user_id",
    "pipeline_run_id",
    "context_id",
    "job_id",
    "job_index",
    "selected_resume_id",
)

_TABLE_CONTRACTS: Mapping[str, Mapping[str, Any]] = {
    "orchestration_graph_runs": {
        "columns": (
            "graph_invocation_id",
            "graph_engine",
            "graph_state_schema_version",
            *_COMMON_IDENTITY_COLUMNS,
            "run_status",
            "current_checkpoint_id",
            "lock_version",
            "created_at",
            "updated_at",
            "terminal_at",
            "purge_after",
        ),
        "column_types": {
            "graph_invocation_id": "text",
            "owner_user_id": "text",
            "run_status": "text",
            "current_checkpoint_id": "text",
            "lock_version": "integer",
        },
        "primary_key": ("graph_invocation_id",),
        "constraint_names": (
            "ck_orchestration_graph_runs_job_index",
            "ck_orchestration_graph_runs_lock_version",
            "ck_orchestration_graph_runs_status",
            "ck_orchestration_graph_runs_current_checkpoint",
            "uq_orchestration_graph_runs_logical_identity",
            "uq_orchestration_graph_runs_bound_identity",
        ),
        "definition_fragments": (
            "primary key (graph_invocation_id)",
            "unique (graph_engine,graph_state_schema_version,"
            "owner_user_id,pipeline_run_id,context_id,job_id,job_index,"
            "selected_resume_id)",
            "unique (graph_invocation_id,owner_user_id,pipeline_run_id,"
            "context_id,job_id,job_index,selected_resume_id)",
            "run_status",
            "lock_version",
            "current_checkpoint_id",
        ),
        "index_names": (
            "idx_orchestration_graph_runs_owner_updated",
            "idx_orchestration_graph_runs_pipeline_context",
            "idx_orchestration_graph_runs_current_checkpoint",
            "idx_orchestration_graph_runs_purge",
        ),
    },
    "orchestration_checkpoints": {
        "columns": (
            "checkpoint_id",
            "graph_invocation_id",
            "checkpoint_sequence",
            "checkpoint_schema_version",
            "graph_state_schema_version",
            "checkpoint_status",
            *_COMMON_IDENTITY_COLUMNS,
            "checkpoint_envelope_json",
            "checkpoint_envelope_digest",
            "completed_node_keys_json",
            "next_node_key",
            "committed_at",
            "purge_after",
        ),
        "column_types": {
            "checkpoint_id": "text",
            "graph_invocation_id": "text",
            "owner_user_id": "text",
            "checkpoint_envelope_json": "jsonb",
            "completed_node_keys_json": "jsonb",
        },
        "primary_key": ("checkpoint_id",),
        "constraint_names": (
            "ck_orchestration_checkpoints_sequence",
            "ck_orchestration_checkpoints_job_index",
            "ck_orchestration_checkpoints_status",
            "ck_orchestration_checkpoints_envelope_object",
            "ck_orchestration_checkpoints_envelope_size",
            "ck_orchestration_checkpoints_digest",
            "ck_orchestration_checkpoints_completed_nodes",
            "uq_orchestration_checkpoints_run_sequence",
            "uq_orchestration_checkpoints_run_checkpoint",
            "uq_orchestration_checkpoints_bound_identity",
            "fk_orchestration_checkpoints_graph_run",
        ),
        "definition_fragments": (
            "primary key (checkpoint_id)",
            "unique (graph_invocation_id,checkpoint_sequence)",
            "foreign key (graph_invocation_id,owner_user_id,"
            "pipeline_run_id,context_id,job_id,job_index,"
            "selected_resume_id)",
            "references orchestration_graph_runs(graph_invocation_id,"
            "owner_user_id,pipeline_run_id,context_id,job_id,job_index,"
            "selected_resume_id)",
            "checkpoint_status",
            "checkpoint_envelope_json",
        ),
        "index_names": (
            "idx_orchestration_checkpoints_owner_run_sequence",
            "idx_orchestration_checkpoints_purge",
        ),
    },
    "orchestration_interrupt_requests": {
        "columns": (
            "interrupt_request_id",
            "graph_invocation_id",
            "checkpoint_id",
            "interrupt_request_schema_version",
            "checkpoint_schema_version",
            "graph_state_schema_version",
            *_COMMON_IDENTITY_COLUMNS,
            "node_key",
            "safe_next_node_key",
            "operator_review_artifact_type",
            "operator_review_artifact_version",
            "operator_review_artifact_digest",
            "allowed_decision_values_json",
            "interrupt_request_json",
            "interrupt_status",
            "lock_version",
            "read_only",
            "diagnostic_only",
            "application_authorization",
            "resume_authorization",
            "created_at",
            "expires_at",
            "resolved_at",
        ),
        "column_types": {
            "interrupt_request_id": "text",
            "graph_invocation_id": "text",
            "checkpoint_id": "text",
            "owner_user_id": "text",
            "allowed_decision_values_json": "jsonb",
            "interrupt_request_json": "jsonb",
            "interrupt_status": "text",
            "lock_version": "integer",
            "read_only": "boolean",
            "diagnostic_only": "boolean",
            "application_authorization": "boolean",
            "resume_authorization": "boolean",
        },
        "primary_key": ("interrupt_request_id",),
        "constraint_names": (
            "ck_orchestration_interrupt_requests_job_index",
            "ck_orchestration_interrupt_requests_lock_version",
            "ck_orchestration_interrupt_requests_status",
            "ck_orchestration_interrupt_requests_unresolved",
            "ck_orchestration_interrupt_requests_boundary",
            "ck_orchestration_interrupt_requests_artifact_digest",
            "ck_orchestration_interrupt_requests_allowed_decisions",
            "ck_orchestration_interrupt_requests_payload_object",
            "ck_orchestration_interrupt_requests_payload_size",
            "ck_orchestration_interrupt_requests_safety",
            "uq_orchestration_interrupt_requests_checkpoint_node",
            "fk_orchestration_interrupt_requests_graph_run",
            "fk_orchestration_interrupt_requests_checkpoint",
            "fk_orchestration_interrupt_requests_bound_checkpoint",
        ),
        "definition_fragments": (
            "primary key (interrupt_request_id)",
            "unique (checkpoint_id,node_key)",
            "foreign key (graph_invocation_id)",
            "references orchestration_graph_runs(graph_invocation_id)",
            "foreign key (checkpoint_id)",
            "references orchestration_checkpoints(checkpoint_id)",
            "foreign key (checkpoint_id,graph_invocation_id,"
            "owner_user_id,pipeline_run_id,context_id,job_id,job_index,"
            "selected_resume_id)",
            "interrupt_status",
            "lock_version",
            "application_authorization",
            "resume_authorization",
        ),
        "index_names": (
            "idx_orchestration_interrupt_requests_pending_owner",
            "idx_orchestration_interrupt_requests_expiry",
        ),
    },
    "orchestration_human_decisions": {
        "columns": (
            "decision_id",
            "graph_invocation_id",
            "checkpoint_id",
            "interrupt_request_id",
            *_COMMON_IDENTITY_COLUMNS,
            "operator_review_artifact_digest",
            "decision_value",
            "actor_id",
            "client_idempotency_key",
            "expected_interrupt_status",
            "expected_interrupt_version",
            "expected_run_lock_version",
            "decision_record_status",
            "reason",
            "rejection_code",
            "application_authorization",
            "created_at",
        ),
        "column_types": {
            "decision_id": "text",
            "graph_invocation_id": "text",
            "owner_user_id": "text",
            "expected_interrupt_version": "integer",
            "expected_run_lock_version": "integer",
            "application_authorization": "boolean",
        },
        "primary_key": ("decision_id",),
        "constraint_names": (
            "uq_orchestration_human_decisions_idempotency",
        ),
        "definition_fragments": (
            "primary key (decision_id)",
            "foreign key (graph_invocation_id)",
            "references orchestration_graph_runs(graph_invocation_id)",
            "foreign key (checkpoint_id)",
            "references orchestration_checkpoints(checkpoint_id)",
            "foreign key (interrupt_request_id)",
            "references orchestration_interrupt_requests"
            "(interrupt_request_id)",
            "decision_value",
            "decision_record_status",
            "application_authorization",
        ),
        "index_names": (
            "uq_orchestration_human_decisions_current",
            "idx_orchestration_human_decisions_owner_interrupt",
        ),
    },
    "orchestration_resume_authorizations": {
        "columns": (
            "authorization_id",
            "decision_id",
            "graph_invocation_id",
            "checkpoint_id",
            "interrupt_request_id",
            *_COMMON_IDENTITY_COLUMNS,
            "operator_review_artifact_digest",
            "decision_value",
            "safe_next_node_key",
            "authorization_token_hash",
            "authorization_status",
            "lock_version",
            "read_only",
            "application_authorization",
            "resume_text_mutation_authorization",
            "queue_mutation_authorization",
            "operator_state_mutation_authorization",
            "created_at",
            "expires_at",
            "consumed_at",
        ),
        "column_types": {
            "authorization_id": "text",
            "decision_id": "text",
            "graph_invocation_id": "text",
            "owner_user_id": "text",
            "authorization_status": "text",
            "lock_version": "integer",
            "read_only": "boolean",
            "application_authorization": "boolean",
        },
        "primary_key": ("authorization_id",),
        "constraint_names": (),
        "definition_fragments": (
            "primary key (authorization_id)",
            "unique (decision_id)",
            "foreign key (decision_id)",
            "references orchestration_human_decisions(decision_id)",
            "foreign key (graph_invocation_id)",
            "references orchestration_graph_runs(graph_invocation_id)",
            "authorization_status",
            "lock_version",
            "read_only",
            "application_authorization",
            "resume_text_mutation_authorization",
            "queue_mutation_authorization",
            "operator_state_mutation_authorization",
        ),
        "index_names": (
            "idx_orchestration_resume_authorizations_owner_status",
        ),
    },
    "orchestration_resume_consumptions": {
        "columns": (
            "consumption_id",
            "authorization_id",
            "decision_id",
            "graph_invocation_id",
            "checkpoint_id",
            "interrupt_request_id",
            *_COMMON_IDENTITY_COLUMNS,
            "resume_invocation_id",
            "consumer_instance_id",
            "claimed_at",
            "claim_status",
            "expected_authorization_version",
            "application_authorization",
        ),
        "column_types": {
            "consumption_id": "text",
            "authorization_id": "text",
            "graph_invocation_id": "text",
            "owner_user_id": "text",
            "claim_status": "text",
            "expected_authorization_version": "integer",
            "application_authorization": "boolean",
        },
        "primary_key": ("consumption_id",),
        "constraint_names": (),
        "definition_fragments": (
            "primary key (consumption_id)",
            "unique (authorization_id)",
            "unique (resume_invocation_id)",
            "foreign key (authorization_id)",
            "references orchestration_resume_authorizations"
            "(authorization_id)",
            "foreign key (decision_id)",
            "references orchestration_human_decisions(decision_id)",
            "claim_status",
            "expected_authorization_version",
            "application_authorization",
        ),
        "index_names": (
            "idx_orchestration_resume_consumptions_owner_authorization",
        ),
    },
    "orchestration_node_attempts": {
        "columns": (
            "node_attempt_id",
            "graph_invocation_id",
            "input_checkpoint_id",
            "output_checkpoint_id",
            *_COMMON_IDENTITY_COLUMNS,
            "node_key",
            "attempt_number",
            "resume_invocation_id",
            "attempt_status",
            "lease_owner_id",
            "lease_acquired_at",
            "lease_expires_at",
            "started_at",
            "completed_at",
            "duration_ms",
            "input_digest",
            "output_digest",
            "error_code",
            "error_detail",
            "lock_version",
            "application_authorization",
            "mutation_authorization",
            "created_at",
            "updated_at",
        ),
        "column_types": {
            "node_attempt_id": "text",
            "graph_invocation_id": "text",
            "owner_user_id": "text",
            "attempt_number": "integer",
            "attempt_status": "text",
            "lock_version": "integer",
            "application_authorization": "boolean",
            "mutation_authorization": "boolean",
        },
        "primary_key": ("node_attempt_id",),
        "constraint_names": (
            "uq_orchestration_node_attempt_identity",
            "ck_orchestration_node_attempt_output",
        ),
        "definition_fragments": (
            "primary key (node_attempt_id)",
            "foreign key (graph_invocation_id)",
            "references orchestration_graph_runs(graph_invocation_id)",
            "foreign key (input_checkpoint_id)",
            "references orchestration_checkpoints(checkpoint_id)",
            "attempt_status",
            "lock_version",
            "application_authorization",
            "mutation_authorization",
        ),
        "index_names": (
            "uq_orchestration_node_attempt_success",
            "idx_orchestration_node_attempts_owner_recovery",
        ),
    },
    "orchestration_terminal_results": {
        "columns": (
            "terminal_result_id",
            "graph_invocation_id",
            "terminal_checkpoint_id",
            *_COMMON_IDENTITY_COLUMNS,
            "graph_state_schema_version",
            "checkpoint_schema_version",
            "terminal_status",
            "result_digest",
            "result_metadata_json",
            "final_node_order_json",
            "failure_code",
            "application_authorization",
            "completed_at",
        ),
        "column_types": {
            "terminal_result_id": "text",
            "graph_invocation_id": "text",
            "owner_user_id": "text",
            "terminal_status": "text",
            "result_metadata_json": "jsonb",
            "final_node_order_json": "jsonb",
            "application_authorization": "boolean",
        },
        "primary_key": ("terminal_result_id",),
        "constraint_names": (),
        "definition_fragments": (
            "primary key (terminal_result_id)",
            "unique (graph_invocation_id)",
            "foreign key (graph_invocation_id)",
            "references orchestration_graph_runs(graph_invocation_id)",
            "foreign key (terminal_checkpoint_id)",
            "references orchestration_checkpoints(checkpoint_id)",
            "terminal_status",
            "result_metadata_json",
            "final_node_order_json",
            "application_authorization",
        ),
        "index_names": (
            "idx_orchestration_terminal_results_owner_graph",
        ),
    },
    "orchestration_lifecycle_events": {
        "columns": (
            "event_id",
            "graph_invocation_id",
            "checkpoint_id",
            "interrupt_request_id",
            "decision_id",
            "authorization_id",
            "consumption_id",
            "node_attempt_id",
            "terminal_result_id",
            "owner_user_id",
            "event_type",
            "aggregate_type",
            "aggregate_id",
            "event_sequence",
            "event_payload_json",
            "event_timestamp",
            "projection_status",
            "projected_at",
            "projection_retry_count",
        ),
        "column_types": {
            "event_id": "text",
            "graph_invocation_id": "text",
            "owner_user_id": "text",
            "event_type": "text",
            "event_sequence": "integer",
            "event_payload_json": "jsonb",
            "projection_status": "text",
            "projection_retry_count": "integer",
        },
        "primary_key": ("event_id",),
        "constraint_names": (
            "uq_orchestration_lifecycle_event_sequence",
        ),
        "definition_fragments": (
            "primary key (event_id)",
            "foreign key (graph_invocation_id)",
            "references orchestration_graph_runs(graph_invocation_id)",
            "foreign key (checkpoint_id)",
            "references orchestration_checkpoints(checkpoint_id)",
            "foreign key (interrupt_request_id)",
            "references orchestration_interrupt_requests"
            "(interrupt_request_id)",
            "event_type",
            "event_sequence",
            "event_payload_json",
            "projection_status",
            "projection_retry_count",
        ),
        "index_names": (
            "idx_orchestration_lifecycle_events_owner_projection",
        ),
    },
}

_CATALOG_SQL = """
WITH expected(object_name) AS (
    VALUES
        ('orchestration_graph_runs'),
        ('orchestration_checkpoints'),
        ('orchestration_interrupt_requests'),
        ('orchestration_human_decisions'),
        ('orchestration_resume_authorizations'),
        ('orchestration_resume_consumptions'),
        ('orchestration_node_attempts'),
        ('orchestration_terminal_results'),
        ('orchestration_lifecycle_events')
)
SELECT json_build_object(
    'object_name', table_info.relname,
    'schema_name', namespace_info.nspname,
    'relkind', table_info.relkind,
    'columns', COALESCE(columns.column_names, '[]'::json),
    'column_types', COALESCE(columns.column_types, '{}'::json),
    'primary_key_columns',
        COALESCE(primary_key.column_names, '[]'::json),
    'constraint_names',
        COALESCE(constraints.constraint_names, '[]'::json),
    'constraint_definitions',
        COALESCE(constraints.constraint_definitions, '[]'::json),
    'index_names', COALESCE(indexes.index_names, '[]'::json)
)::text
FROM expected
JOIN pg_catalog.pg_class AS table_info
  ON table_info.relname = expected.object_name
JOIN pg_catalog.pg_namespace AS namespace_info
  ON namespace_info.oid = table_info.relnamespace
 AND namespace_info.nspname = current_schema()
LEFT JOIN LATERAL (
    SELECT
        json_agg(attribute.attname ORDER BY attribute.attnum)
            AS column_names,
        json_object_agg(
            attribute.attname,
            pg_catalog.format_type(attribute.atttypid, attribute.atttypmod)
        ) AS column_types
    FROM pg_catalog.pg_attribute AS attribute
    WHERE attribute.attrelid = table_info.oid
      AND attribute.attnum > 0
      AND NOT attribute.attisdropped
) AS columns ON TRUE
LEFT JOIN LATERAL (
    SELECT json_agg(attribute.attname ORDER BY key_item.ordinality)
        AS column_names
    FROM pg_catalog.pg_constraint AS constraint_info
    JOIN unnest(constraint_info.conkey) WITH ORDINALITY
      AS key_item(attribute_number, ordinality) ON TRUE
    JOIN pg_catalog.pg_attribute AS attribute
      ON attribute.attrelid = constraint_info.conrelid
     AND attribute.attnum = key_item.attribute_number
    WHERE constraint_info.conrelid = table_info.oid
      AND constraint_info.contype = 'p'
) AS primary_key ON TRUE
LEFT JOIN LATERAL (
    SELECT
        json_agg(
            constraint_info.conname ORDER BY constraint_info.conname
        ) AS constraint_names,
        json_agg(
            pg_catalog.pg_get_constraintdef(
                constraint_info.oid, TRUE
            )
            ORDER BY constraint_info.conname
        ) AS constraint_definitions
    FROM pg_catalog.pg_constraint AS constraint_info
    WHERE constraint_info.conrelid = table_info.oid
) AS constraints ON TRUE
LEFT JOIN LATERAL (
    SELECT json_agg(index_info.relname ORDER BY index_info.relname)
        AS index_names
    FROM pg_catalog.pg_index AS index_link
    JOIN pg_catalog.pg_class AS index_info
      ON index_info.oid = index_link.indexrelid
    WHERE index_link.indrelid = table_info.oid
) AS indexes ON TRUE
ORDER BY expected.object_name
""".strip()


Runner = Callable[..., Any]


@dataclass(frozen=True, slots=True)
class SchemaExecutionResult:
    operation: str
    outcome: str
    schema_contract_version: str = SCHEMA_CONTRACT_VERSION
    schema_sha256: str = ""
    object_count: int = 0
    compatibility: str = ""
    diagnostic_code: str = ""
    subprocess_succeeded: bool = False

    def __post_init__(self) -> None:
        if self.outcome not in OUTCOMES:
            raise ValueError("schema_executor_outcome_invalid")


@dataclass(frozen=True, slots=True)
class _SchemaArtifact:
    path: Path
    digest: str


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {
        "1", "true", "yes", "on", "enabled",
    }


def _normalize_definition(value: Any) -> str:
    text = str(value or "").replace('"', "").lower()
    text = re.sub(r"\s+", " ", text).strip()
    return re.sub(r"\s*([(),])\s*", r"\1", text)


def _load_schema_artifact(path: Path = SCHEMA_PATH) -> _SchemaArtifact:
    resolved = Path(path)
    if resolved.is_symlink():
        raise ValueError("schema_artifact_symlink_rejected")
    if not resolved.exists() or not resolved.is_file():
        raise ValueError("schema_artifact_missing")
    try:
        content = resolved.read_bytes()
        decoded = content.decode("utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValueError("schema_artifact_unreadable") from exc
    if not decoded.strip():
        raise ValueError("schema_artifact_empty")
    for table in _EXPECTED_TABLES:
        marker = f"CREATE TABLE IF NOT EXISTS {table}"
        if marker not in decoded:
            raise ValueError("schema_artifact_contract_incomplete")
    upper = decoded.upper()
    for prohibited in (
        "CREATE DATABASE",
        "DROP DATABASE",
        "DROP TABLE",
    ):
        if prohibited in upper:
            raise ValueError("schema_artifact_destructive_statement")
    return _SchemaArtifact(
        path=resolved.resolve(strict=True),
        digest=sha256(content).hexdigest(),
    )


def _catalog_command(*, psql_bin: str, database_url: str) -> list[str]:
    return [
        str(psql_bin),
        str(database_url),
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-A",
        "-t",
        "-c",
        _CATALOG_SQL,
    ]


def _apply_command(
    *,
    psql_bin: str,
    database_url: str,
    schema_path: Path,
) -> list[str]:
    return [
        str(psql_bin),
        str(database_url),
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-1",
        "-f",
        str(schema_path),
    ]


def _invoke(
    runner: Runner,
    command: Sequence[str],
    *,
    timeout_seconds: int,
) -> Any:
    return runner(
        list(command),
        check=False,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        shell=False,
    )


def _bounded_process_diagnostic(completed: Any) -> str:
    stdout = str(getattr(completed, "stdout", "") or "")
    stderr = str(getattr(completed, "stderr", "") or "")
    per_stream_limit = MAX_CAPTURED_OUTPUT_CHARS // 2
    combined = (
        stdout[:per_stream_limit]
        + "\n"
        + stderr[:per_stream_limit]
    )
    lowered = combined.lower()
    if "permission denied" in lowered:
        return "psql_permission_denied"
    if "could not connect" in lowered or "connection refused" in lowered:
        return "psql_connection_unavailable"
    return "psql_nonzero_exit"


def _parse_catalog(stdout: Any) -> list[dict[str, Any]]:
    text = str(stdout or "")
    if len(text) > MAX_CAPTURED_OUTPUT_CHARS:
        raise ValueError("catalog_output_too_large")
    rows: list[dict[str, Any]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        value = json.loads(stripped)
        if not isinstance(value, dict):
            raise ValueError("catalog_row_malformed")
        rows.append(value)
    return rows


def _catalog_compatibility(rows: Sequence[Mapping[str, Any]]) -> tuple[str, int]:
    if not rows:
        return "absent", 0
    by_name: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        name = str(row.get("object_name") or "")
        if name not in _TABLE_CONTRACTS or name in by_name:
            raise ValueError("catalog_object_set_invalid")
        by_name[name] = row
    if len(by_name) != len(_EXPECTED_TABLES):
        return "partial", len(by_name)

    for name, contract in _TABLE_CONTRACTS.items():
        row = by_name[name]
        required_fields = {
            "schema_name",
            "relkind",
            "columns",
            "column_types",
            "primary_key_columns",
            "constraint_names",
            "constraint_definitions",
            "index_names",
        }
        if not required_fields <= set(row):
            return "incompatible", len(by_name)
        if not str(row["schema_name"]).strip() or row["relkind"] != "r":
            return "incompatible", len(by_name)
        columns = set(row["columns"] or ())
        if not set(contract["columns"]) <= columns:
            return "incompatible", len(by_name)
        column_types = dict(row["column_types"] or {})
        if any(
            column_types.get(column) != expected_type
            for column, expected_type in contract["column_types"].items()
        ):
            return "incompatible", len(by_name)
        if tuple(row["primary_key_columns"] or ()) != contract["primary_key"]:
            return "incompatible", len(by_name)
        constraint_names = set(row["constraint_names"] or ())
        if not set(contract["constraint_names"]) <= constraint_names:
            return "incompatible", len(by_name)
        index_names = set(row["index_names"] or ())
        if not set(contract["index_names"]) <= index_names:
            return "incompatible", len(by_name)
        definitions = " ".join(
            _normalize_definition(value)
            for value in row["constraint_definitions"] or ()
        )
        if any(
            _normalize_definition(fragment) not in definitions
            for fragment in contract["definition_fragments"]
        ):
            return "incompatible", len(by_name)
    return "compatible", len(by_name)


class DurableOrchestrationSchemaExecutor:
    """Explicit, injected ``psql`` administration boundary."""

    def __init__(
        self,
        *,
        enabled: bool = False,
        runner: Runner = subprocess.run,
        psql_bin: str = "psql",
        timeout_seconds: int = PSQL_TIMEOUT_SECONDS,
    ) -> None:
        self._enabled = bool(enabled)
        self._runner = runner
        self._psql_bin = str(psql_bin or "").strip() or "psql"
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, int)
            or timeout_seconds < 1
            or timeout_seconds > PSQL_TIMEOUT_SECONDS
        ):
            raise ValueError("schema_executor_timeout_invalid")
        self._timeout_seconds = timeout_seconds

    def _disabled(self, operation: str) -> SchemaExecutionResult | None:
        if self._enabled:
            return None
        return SchemaExecutionResult(
            operation=operation,
            outcome="disabled",
            diagnostic_code="capability_disabled",
        )

    def plan(self) -> SchemaExecutionResult:
        disabled = self._disabled("plan")
        if disabled is not None:
            return disabled
        try:
            artifact = _load_schema_artifact()
        except ValueError as exc:
            return SchemaExecutionResult(
                operation="plan",
                outcome="unavailable",
                diagnostic_code=str(exc),
            )
        return SchemaExecutionResult(
            operation="plan",
            outcome="planned",
            schema_sha256=artifact.digest,
            object_count=len(_EXPECTED_TABLES),
            compatibility="not_inspected",
        )

    def check(self, *, database_url: str) -> SchemaExecutionResult:
        disabled = self._disabled("check")
        if disabled is not None:
            return disabled
        target = str(database_url or "").strip()
        if not target:
            return SchemaExecutionResult(
                operation="check",
                outcome="unavailable",
                diagnostic_code="dedicated_target_missing",
            )
        return self._inspect(target, operation="check")

    def apply(self, *, database_url: str) -> SchemaExecutionResult:
        disabled = self._disabled("apply")
        if disabled is not None:
            return disabled
        target = str(database_url or "").strip()
        if not target:
            return SchemaExecutionResult(
                operation="apply",
                outcome="unavailable",
                diagnostic_code="dedicated_target_missing",
            )
        try:
            artifact = _load_schema_artifact()
        except ValueError as exc:
            return SchemaExecutionResult(
                operation="apply",
                outcome="unavailable",
                diagnostic_code=str(exc),
            )

        preflight = self._inspect(target, operation="apply_preflight")
        if preflight.outcome not in {"absent", "compatible"}:
            return SchemaExecutionResult(
                operation="apply",
                outcome=preflight.outcome,
                schema_sha256=artifact.digest,
                object_count=preflight.object_count,
                compatibility=preflight.outcome,
                diagnostic_code=preflight.diagnostic_code,
            )

        command = _apply_command(
            psql_bin=self._psql_bin,
            database_url=target,
            schema_path=artifact.path,
        )
        try:
            completed = _invoke(
                self._runner,
                command,
                timeout_seconds=self._timeout_seconds,
            )
        except subprocess.TimeoutExpired as exc:
            result = SchemaExecutionResult(
                operation="apply",
                outcome="execution_failed",
                schema_sha256=artifact.digest,
                object_count=preflight.object_count,
                compatibility=preflight.outcome,
                diagnostic_code="psql_timeout",
            )
            raise SchemaExecutorProcessError(result) from exc
        except (OSError, subprocess.SubprocessError) as exc:
            result = SchemaExecutionResult(
                operation="apply",
                outcome="execution_failed",
                schema_sha256=artifact.digest,
                object_count=preflight.object_count,
                compatibility=preflight.outcome,
                diagnostic_code="psql_unavailable",
            )
            raise SchemaExecutorProcessError(result) from exc
        if int(getattr(completed, "returncode", 1)) != 0:
            return SchemaExecutionResult(
                operation="apply",
                outcome="execution_failed",
                schema_sha256=artifact.digest,
                object_count=preflight.object_count,
                compatibility=preflight.outcome,
                diagnostic_code=_bounded_process_diagnostic(completed),
            )

        postflight = self._inspect(target, operation="apply_postflight")
        if postflight.outcome != "compatible":
            return SchemaExecutionResult(
                operation="apply",
                outcome="verification_failed",
                schema_sha256=artifact.digest,
                object_count=postflight.object_count,
                compatibility=postflight.outcome,
                diagnostic_code=(
                    postflight.diagnostic_code
                    or "postflight_not_compatible"
                ),
                subprocess_succeeded=True,
            )
        return SchemaExecutionResult(
            operation="apply",
            outcome="applied",
            schema_sha256=artifact.digest,
            object_count=len(_EXPECTED_TABLES),
            compatibility="compatible",
            subprocess_succeeded=True,
        )

    def _inspect(
        self,
        database_url: str,
        *,
        operation: str,
    ) -> SchemaExecutionResult:
        command = _catalog_command(
            psql_bin=self._psql_bin,
            database_url=database_url,
        )
        try:
            completed = _invoke(
                self._runner,
                command,
                timeout_seconds=self._timeout_seconds,
            )
        except subprocess.TimeoutExpired:
            return SchemaExecutionResult(
                operation=operation,
                outcome="unavailable",
                diagnostic_code="catalog_timeout",
            )
        except (OSError, subprocess.SubprocessError):
            return SchemaExecutionResult(
                operation=operation,
                outcome="unavailable",
                diagnostic_code="catalog_unavailable",
            )
        if int(getattr(completed, "returncode", 1)) != 0:
            return SchemaExecutionResult(
                operation=operation,
                outcome="unavailable",
                diagnostic_code=_bounded_process_diagnostic(completed),
            )
        try:
            rows = _parse_catalog(getattr(completed, "stdout", ""))
            outcome, count = _catalog_compatibility(rows)
        except (TypeError, ValueError, json.JSONDecodeError):
            return SchemaExecutionResult(
                operation=operation,
                outcome="unavailable",
                diagnostic_code="catalog_result_invalid",
            )
        return SchemaExecutionResult(
            operation=operation,
            outcome=outcome,
            object_count=count,
            compatibility=outcome,
        )


class SchemaExecutorProcessError(RuntimeError):
    """Carries only a bounded result; original errors remain chained."""

    def __init__(self, result: SchemaExecutionResult) -> None:
        self.result = result
        super().__init__(
            f"durable_orchestration_schema_executor:"
            f"{result.outcome}:{result.diagnostic_code}"
        )


def dedicated_test_database_target(
    configuration: Mapping[str, Any],
) -> str | None:
    """Return the test-only target only under its separate explicit opt-in."""
    if not _truthy(configuration.get(TEST_EXECUTION_CAPABILITY_NAME)):
        return None
    value = str(configuration.get(TEST_DATABASE_URL_NAME, "") or "").strip()
    return value or None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Explicit durable-orchestration PostgreSQL schema "
            "administration tool."
        )
    )
    operation = parser.add_mutually_exclusive_group(required=True)
    operation.add_argument(
        "--plan",
        action="store_true",
        help="Validate and fingerprint the local schema; do not call psql.",
    )
    operation.add_argument(
        "--check",
        action="store_true",
        help="Inspect the dedicated target without applying DDL.",
    )
    operation.add_argument(
        "--apply",
        action="store_true",
        help="Atomically apply the schema after a safe preflight.",
    )
    parser.add_argument(
        "--psql-bin",
        default="psql",
        help="psql executable name or explicit executable path.",
    )
    return parser


def _print_result(result: SchemaExecutionResult) -> None:
    fields = [
        f"operation={result.operation}",
        f"outcome={result.outcome}",
        f"schema_contract_version={result.schema_contract_version}",
        f"object_count={result.object_count}",
    ]
    if result.schema_sha256:
        fields.append(f"schema_sha256={result.schema_sha256}")
    if result.compatibility:
        fields.append(f"compatibility={result.compatibility}")
    if result.diagnostic_code:
        fields.append(f"diagnostic_code={result.diagnostic_code}")
    print(" ".join(fields))


def main(
    argv: Sequence[str] | None = None,
    *,
    configuration: Mapping[str, Any] | None = None,
    runner: Runner = subprocess.run,
) -> int:
    args = _parser().parse_args(argv)
    config = os.environ if configuration is None else configuration
    enabled = _truthy(config.get(CAPABILITY_NAME))
    executor = DurableOrchestrationSchemaExecutor(
        enabled=enabled,
        runner=runner,
        psql_bin=args.psql_bin,
    )
    target = str(config.get(DATABASE_URL_NAME, "") or "").strip()
    try:
        if args.plan:
            result = executor.plan()
        elif args.check:
            result = executor.check(database_url=target)
        else:
            result = executor.apply(database_url=target)
    except SchemaExecutorProcessError as exc:
        result = exc.result
    _print_result(result)
    return 0 if result.outcome in {"planned", "compatible", "applied"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
