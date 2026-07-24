"""Pure preparation helpers for the durable-orchestration SQL contract.

This module validates existing evidence-chain checkpoint and interrupt
payloads, prepares deterministic rows, and returns SQL plus parameters. It
does not own a database connection or transaction execution boundary.
"""

from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any, Mapping

from src.agents import evidence_chain_langgraph_harness as harness


GRAPH_RUN_STATUS_VALUES = (
    "running", "awaiting_decision", "decision_recorded", "resume_authorized",
    "resume_consumed", "decision_rejected", "resumed", "completed", "failed",
    "cancelled",
)
INTERRUPT_STATUS_VALUES = (
    "awaiting_decision", "decision_recorded", "resume_authorized",
    "resume_consumed", "decision_rejected", "cancelled", "expired",
)
MAX_CHECKPOINT_ENVELOPE_BYTES = 1_048_576
MAX_INTERRUPT_REQUEST_BYTES = 262_144

SAFETY_DECLARATIONS: dict[str, bool] = {
    "schema_executed": False,
    "database_connection_opened": False,
    "sql_executed": False,
    "transaction_committed": False,
    "checkpointer_configured": False,
    "graph_paused": False,
    "graph_resumed": False,
    "decision_accepted": False,
    "authorization_created": False,
    "production_activated": False,
}

_IDENTITY_COLUMNS = (
    "owner_user_id",
    "pipeline_run_id",
    "context_id",
    "job_id",
    "job_index",
    "selected_resume_id",
)

_GRAPH_RUN_COLUMNS = (
    "graph_invocation_id",
    "graph_engine",
    "graph_state_schema_version",
    *_IDENTITY_COLUMNS,
    "run_status",
    "current_checkpoint_id",
    "lock_version",
    "created_at",
    "updated_at",
    "terminal_at",
    "purge_after",
)

_CHECKPOINT_COLUMNS = (
    "checkpoint_id",
    "graph_invocation_id",
    "checkpoint_sequence",
    "checkpoint_schema_version",
    "graph_state_schema_version",
    "checkpoint_status",
    *_IDENTITY_COLUMNS,
    "checkpoint_envelope_json",
    "checkpoint_envelope_digest",
    "completed_node_keys_json",
    "next_node_key",
    "committed_at",
    "purge_after",
)

_INTERRUPT_COLUMNS = (
    "interrupt_request_id",
    "graph_invocation_id",
    "checkpoint_id",
    "interrupt_request_schema_version",
    "checkpoint_schema_version",
    "graph_state_schema_version",
    *_IDENTITY_COLUMNS,
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
)

_PROHIBITED_KEY_FRAGMENTS = (
    "api_key",
    "authorization_header",
    "bearer_token",
    "credential",
    "database_password",
    "database_url",
    "db_password",
    "password",
    "private_key",
    "provider_secret",
    "refresh_token",
    "resume_token",
    "secret_key",
)


def safety_declarations() -> dict[str, bool]:
    return dict(SAFETY_DECLARATIONS)


def durable_orchestration_table_specs() -> dict[str, dict[str, Any]]:
    return {
        "orchestration_graph_runs": {
            "primary_key": ["graph_invocation_id"],
            "status_values": list(GRAPH_RUN_STATUS_VALUES),
            "cas_column": "lock_version",
            "columns": list(_GRAPH_RUN_COLUMNS),
        },
        "orchestration_checkpoints": {
            "primary_key": ["checkpoint_id"],
            "foreign_keys": {
                "graph_invocation_id": (
                    "orchestration_graph_runs.graph_invocation_id"
                ),
            },
            "unique": ["graph_invocation_id", "checkpoint_sequence"],
            "immutable": True,
            "columns": list(_CHECKPOINT_COLUMNS),
        },
        "orchestration_interrupt_requests": {
            "primary_key": ["interrupt_request_id"],
            "foreign_keys": {
                "graph_invocation_id": (
                    "orchestration_graph_runs.graph_invocation_id"
                ),
                "checkpoint_id": "orchestration_checkpoints.checkpoint_id",
            },
            "unique": ["checkpoint_id", "node_key"],
            "status_values": list(INTERRUPT_STATUS_VALUES),
            "cas_column": "lock_version",
            "columns": list(_INTERRUPT_COLUMNS),
        },
    }


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _require_text(mapping: Mapping[str, Any], key: str) -> str:
    value = _clean_text(mapping.get(key))
    if not value:
        raise ValueError(f"{key} is required.")
    return value


def _optional_text(value: Any) -> str | None:
    text = _clean_text(value)
    return text or None


def _require_nonnegative_int(value: Any, key: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{key} must be a non-negative integer.")
    return value


def _canonical_json(value: Any, *, field_path: str) -> str:
    normalized = harness._checkpoint_json_value(value, field_path=field_path)
    return json.dumps(
        normalized,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _reject_prohibited_payload(value: Any, *, field_path: str) -> None:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if not isinstance(key, str):
                raise ValueError(
                    f"storage_payload_non_string_key:{field_path}"
                )
            normalized_key = key.strip().lower()
            if normalized_key in {
                "application_authorization",
                "resume_authorization",
            }:
                if nested is not False:
                    raise ValueError(
                        f"storage_payload_authorization_prohibited:{field_path}.{key}"
                    )
            elif (
                normalized_key == "token"
                or normalized_key.endswith("_token")
                or any(
                    fragment in normalized_key
                    for fragment in _PROHIBITED_KEY_FRAGMENTS
                )
            ):
                raise ValueError(
                    f"storage_payload_secret_field_prohibited:{field_path}.{key}"
                )
            _reject_prohibited_payload(
                nested,
                field_path=f"{field_path}.{key}",
            )
        return
    if isinstance(value, (list, tuple)):
        for index, nested in enumerate(value):
            _reject_prohibited_payload(
                nested,
                field_path=f"{field_path}[{index}]",
            )
        return
    if isinstance(value, str) and value.lstrip().lower().startswith("bearer "):
        raise ValueError(f"storage_payload_bearer_value_prohibited:{field_path}")


def _require_exact_fields(
    value: Mapping[str, Any],
    expected: tuple[str, ...] | set[str],
    label: str,
) -> None:
    expected_fields = set(expected)
    actual_fields = set(value)
    if actual_fields != expected_fields:
        raise ValueError(f"{label}_fields_invalid")


def _validated_checkpoint_envelope(
    envelope: Mapping[str, Any],
) -> dict[str, Any]:
    if not isinstance(envelope, Mapping):
        raise ValueError("checkpoint_envelope_malformed")
    _reject_prohibited_payload(envelope, field_path="checkpoint_envelope")
    serialized = harness._serialize_checkpoint_envelope(envelope)
    if len(serialized.encode("utf-8")) > MAX_CHECKPOINT_ENVELOPE_BYTES:
        raise ValueError("checkpoint_envelope_too_large")
    return dict(harness._deserialize_checkpoint_envelope(serialized))


def _validated_identity(source: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(source, Mapping):
        raise ValueError("checkpoint_identity_malformed")
    if "checkpoint_identity" in source:
        return dict(
            _validated_checkpoint_envelope(source)["checkpoint_identity"]
        )

    expected = set(harness.EvidenceChainCheckpointIdentityPayload.__required_keys__)
    if set(source) != expected:
        raise ValueError("checkpoint_identity_fields_invalid")
    _reject_prohibited_payload(source, field_path="checkpoint_identity")
    normalized = harness._checkpoint_json_value(
        source,
        field_path="checkpoint_identity",
    )
    if normalized.get("graph_engine") != harness.CHECKPOINT_GRAPH_ENGINE:
        raise ValueError("checkpoint_graph_engine_unsupported")
    if (
        normalized.get("checkpoint_schema_version")
        != harness.CHECKPOINT_SCHEMA_VERSION
    ):
        raise ValueError("checkpoint_schema_version_unsupported")
    if (
        normalized.get("graph_state_schema_version")
        != harness.GRAPH_STATE_SCHEMA_VERSION
    ):
        raise ValueError("checkpoint_graph_state_schema_version_unsupported")
    for key in (
        "owner_user_id",
        "pipeline_run_id",
        "context_id",
        "job_id",
        "selected_resume_id",
        "graph_invocation_id",
        "checkpoint_id",
    ):
        _require_text(normalized, key)
    _require_nonnegative_int(normalized.get("job_index"), "job_index")
    return dict(normalized)


def prepare_graph_run_row(
    checkpoint_identity_or_envelope: Mapping[str, Any],
    *,
    created_at: str,
    updated_at: str = "",
    run_status: str = "running",
    current_checkpoint_id: str | None = None,
    lock_version: int = 0,
    terminal_at: str | None = None,
    purge_after: str | None = None,
) -> dict[str, Any]:
    identity = _validated_identity(checkpoint_identity_or_envelope)
    normalized_status = _clean_text(run_status).lower()
    if normalized_status not in GRAPH_RUN_STATUS_VALUES:
        raise ValueError("graph_run_status_unsupported")
    checkpoint_id = _optional_text(current_checkpoint_id)
    if normalized_status == "running" and checkpoint_id is not None:
        raise ValueError("running_graph_run_current_checkpoint_invalid")
    if normalized_status == "awaiting_decision" and checkpoint_id is None:
        raise ValueError("awaiting_graph_run_current_checkpoint_required")
    if terminal_at is not None:
        raise ValueError("terminal_graph_run_not_supported")

    created = _clean_text(created_at)
    if not created:
        raise ValueError("created_at is required.")
    updated = _clean_text(updated_at) or created
    row = {
        "graph_invocation_id": identity["graph_invocation_id"],
        "graph_engine": identity["graph_engine"],
        "graph_state_schema_version": identity["graph_state_schema_version"],
        **{key: deepcopy(identity[key]) for key in _IDENTITY_COLUMNS},
        "run_status": normalized_status,
        "current_checkpoint_id": checkpoint_id,
        "lock_version": _require_nonnegative_int(lock_version, "lock_version"),
        "created_at": created,
        "updated_at": updated,
        "terminal_at": None,
        "purge_after": _optional_text(purge_after),
    }
    return deepcopy(row)


def prepare_checkpoint_row(
    checkpoint_envelope: Mapping[str, Any],
    *,
    committed_at: str,
    purge_after: str | None = None,
) -> dict[str, Any]:
    envelope = _validated_checkpoint_envelope(checkpoint_envelope)
    identity = envelope["checkpoint_identity"]
    committed = _clean_text(committed_at)
    if not committed:
        raise ValueError("committed_at is required.")
    completed = list(envelope["completed_node_keys"])
    row = {
        "checkpoint_id": identity["checkpoint_id"],
        "graph_invocation_id": identity["graph_invocation_id"],
        "checkpoint_sequence": len(completed),
        "checkpoint_schema_version": envelope["checkpoint_schema_version"],
        "graph_state_schema_version": envelope[
            "graph_state_schema_version"
        ],
        "checkpoint_status": envelope["checkpoint_status"],
        **{key: deepcopy(identity[key]) for key in _IDENTITY_COLUMNS},
        "checkpoint_envelope_json": deepcopy(envelope),
        "checkpoint_envelope_digest": harness._checkpoint_digest(envelope),
        "completed_node_keys_json": completed,
        "next_node_key": envelope["next_node_key"],
        "committed_at": committed,
        "purge_after": _optional_text(purge_after),
    }
    return deepcopy(row)


def prepare_interrupt_request_row(
    interrupt_request: Mapping[str, Any],
    *,
    checkpoint_envelope: Mapping[str, Any],
    created_at: str,
    expires_at: str | None = None,
) -> dict[str, Any]:
    envelope = _validated_checkpoint_envelope(checkpoint_envelope)
    if not isinstance(interrupt_request, Mapping):
        raise ValueError("interrupt_request_malformed")
    _reject_prohibited_payload(
        interrupt_request,
        field_path="interrupt_request",
    )
    validated = harness._validate_operator_review_interrupt_request(
        interrupt_request,
        envelope["state"],
    )
    serialized = _canonical_json(
        validated,
        field_path="interrupt_request",
    )
    if len(serialized.encode("utf-8")) > MAX_INTERRUPT_REQUEST_BYTES:
        raise ValueError("interrupt_request_too_large")
    if validated["checkpoint_id"] != envelope["checkpoint_identity"][
        "checkpoint_id"
    ]:
        raise ValueError("interrupt_request_checkpoint_mismatch")
    created = _clean_text(created_at)
    if not created:
        raise ValueError("created_at is required.")
    row = {
        "interrupt_request_id": validated["interrupt_request_id"],
        "graph_invocation_id": validated["graph_invocation_id"],
        "checkpoint_id": validated["checkpoint_id"],
        "interrupt_request_schema_version": validated[
            "interrupt_request_schema_version"
        ],
        "checkpoint_schema_version": validated["checkpoint_schema_version"],
        "graph_state_schema_version": validated[
            "graph_state_schema_version"
        ],
        **{key: deepcopy(validated[key]) for key in _IDENTITY_COLUMNS},
        "node_key": validated["node_key"],
        "safe_next_node_key": validated["safe_next_node_key"],
        "operator_review_artifact_type": validated[
            "operator_review_artifact_type"
        ],
        "operator_review_artifact_version": validated[
            "operator_review_artifact_version"
        ],
        "operator_review_artifact_digest": validated[
            "operator_review_artifact_digest"
        ],
        "allowed_decision_values_json": list(
            validated["allowed_decision_values"]
        ),
        "interrupt_request_json": deepcopy(validated),
        "interrupt_status": "awaiting_decision",
        "lock_version": 0,
        "read_only": True,
        "diagnostic_only": True,
        "application_authorization": False,
        "resume_authorization": False,
        "created_at": created,
        "expires_at": _optional_text(expires_at),
        "resolved_at": None,
    }
    return deepcopy(row)


def checkpoint_rows_are_identical(
    existing: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> bool:
    _require_exact_fields(existing, _CHECKPOINT_COLUMNS, "checkpoint_row")
    _require_exact_fields(candidate, _CHECKPOINT_COLUMNS, "checkpoint_row")
    return _canonical_json(existing, field_path="existing_checkpoint_row") == (
        _canonical_json(candidate, field_path="candidate_checkpoint_row")
    )


def interrupt_rows_are_identical(
    existing: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> bool:
    _require_exact_fields(existing, _INTERRUPT_COLUMNS, "interrupt_row")
    _require_exact_fields(candidate, _INTERRUPT_COLUMNS, "interrupt_row")
    return _canonical_json(existing, field_path="existing_interrupt_row") == (
        _canonical_json(candidate, field_path="candidate_interrupt_row")
    )


def require_idempotent_checkpoint_duplicate(
    existing: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    if not checkpoint_rows_are_identical(existing, candidate):
        raise ValueError("checkpoint_duplicate_content_conflict")
    return deepcopy(dict(candidate))


def require_idempotent_interrupt_duplicate(
    existing: Mapping[str, Any],
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    if not interrupt_rows_are_identical(existing, candidate):
        raise ValueError("interrupt_duplicate_content_conflict")
    return deepcopy(dict(candidate))


def _command(
    *,
    operation: str,
    tables: tuple[str, ...],
    sql: str,
    params: Mapping[str, Any],
    read_only: bool,
) -> dict[str, Any]:
    return {
        "operation": operation,
        "tables": list(tables),
        "sql": sql.strip(),
        "params": deepcopy(dict(params)),
        "read_only": read_only,
        **safety_declarations(),
    }


def _graph_run_params(row: Mapping[str, Any]) -> dict[str, Any]:
    _require_exact_fields(row, _GRAPH_RUN_COLUMNS, "graph_run_row")
    if row["graph_engine"] != harness.CHECKPOINT_GRAPH_ENGINE:
        raise ValueError("checkpoint_graph_engine_unsupported")
    if (
        row["graph_state_schema_version"]
        != harness.GRAPH_STATE_SCHEMA_VERSION
    ):
        raise ValueError("checkpoint_graph_state_schema_version_unsupported")
    if row["run_status"] not in GRAPH_RUN_STATUS_VALUES:
        raise ValueError("graph_run_status_unsupported")
    _require_nonnegative_int(row["lock_version"], "lock_version")
    _reject_prohibited_payload(row, field_path="graph_run_row")
    return deepcopy(dict(row))


def _checkpoint_params(row: Mapping[str, Any]) -> dict[str, Any]:
    _require_exact_fields(row, _CHECKPOINT_COLUMNS, "checkpoint_row")
    rebuilt = prepare_checkpoint_row(
        row["checkpoint_envelope_json"],
        committed_at=_require_text(row, "committed_at"),
        purge_after=row.get("purge_after"),
    )
    if not checkpoint_rows_are_identical(rebuilt, row):
        raise ValueError("checkpoint_row_content_mismatch")
    params = deepcopy(dict(row))
    params["checkpoint_envelope_json"] = _canonical_json(
        row["checkpoint_envelope_json"],
        field_path="checkpoint_envelope",
    )
    params["completed_node_keys_json"] = _canonical_json(
        row["completed_node_keys_json"],
        field_path="completed_node_keys",
    )
    return params


def _interrupt_params(
    row: Mapping[str, Any],
    *,
    checkpoint_envelope: Mapping[str, Any],
) -> dict[str, Any]:
    _require_exact_fields(row, _INTERRUPT_COLUMNS, "interrupt_row")
    rebuilt = prepare_interrupt_request_row(
        row["interrupt_request_json"],
        checkpoint_envelope=checkpoint_envelope,
        created_at=_require_text(row, "created_at"),
        expires_at=row.get("expires_at"),
    )
    if not interrupt_rows_are_identical(rebuilt, row):
        raise ValueError("interrupt_row_content_mismatch")
    params = deepcopy(dict(row))
    params["allowed_decision_values_json"] = _canonical_json(
        row["allowed_decision_values_json"],
        field_path="allowed_decision_values",
    )
    params["interrupt_request_json"] = _canonical_json(
        row["interrupt_request_json"],
        field_path="interrupt_request",
    )
    return params


def prepare_graph_run_insert(
    graph_run_row: Mapping[str, Any],
) -> dict[str, Any]:
    params = _graph_run_params(graph_run_row)
    sql = """
WITH inserted AS (
    INSERT INTO orchestration_graph_runs (
        graph_invocation_id, graph_engine, graph_state_schema_version,
        owner_user_id, pipeline_run_id, context_id, job_id, job_index,
        selected_resume_id, run_status, current_checkpoint_id, lock_version,
        created_at, updated_at, terminal_at, purge_after
    )
    VALUES (
        %(graph_invocation_id)s, %(graph_engine)s,
        %(graph_state_schema_version)s, %(owner_user_id)s,
        %(pipeline_run_id)s, %(context_id)s, %(job_id)s, %(job_index)s,
        %(selected_resume_id)s, %(run_status)s, %(current_checkpoint_id)s,
        %(lock_version)s, %(created_at)s, %(updated_at)s, %(terminal_at)s,
        %(purge_after)s
    )
    ON CONFLICT (graph_invocation_id) DO NOTHING
    RETURNING *, FALSE AS idempotent_duplicate
),
accepted AS (
    SELECT * FROM inserted
    UNION ALL
    SELECT existing.*, TRUE AS idempotent_duplicate
    FROM orchestration_graph_runs AS existing
    WHERE existing.graph_invocation_id = %(graph_invocation_id)s
      AND existing.graph_engine = %(graph_engine)s
      AND existing.graph_state_schema_version = %(graph_state_schema_version)s
      AND existing.owner_user_id = %(owner_user_id)s
      AND existing.pipeline_run_id = %(pipeline_run_id)s
      AND existing.context_id = %(context_id)s
      AND existing.job_id = %(job_id)s
      AND existing.job_index = %(job_index)s
      AND existing.selected_resume_id = %(selected_resume_id)s
      AND existing.run_status = %(run_status)s
      AND existing.current_checkpoint_id
          IS NOT DISTINCT FROM %(current_checkpoint_id)s
      AND existing.lock_version = %(lock_version)s
      AND existing.created_at = %(created_at)s
      AND existing.updated_at = %(updated_at)s
      AND existing.terminal_at IS NOT DISTINCT FROM %(terminal_at)s
      AND existing.purge_after IS NOT DISTINCT FROM %(purge_after)s
      AND NOT EXISTS (SELECT 1 FROM inserted)
)
SELECT * FROM accepted
LIMIT 1
"""
    return _command(
        operation="prepare_graph_run_insert",
        tables=("orchestration_graph_runs",),
        sql=sql,
        params=params,
        read_only=False,
    )


def prepare_current_graph_run_read(
    *,
    owner_user_id: str,
    graph_invocation_id: str,
) -> dict[str, Any]:
    params = {
        "owner_user_id": _clean_text(owner_user_id),
        "graph_invocation_id": _clean_text(graph_invocation_id),
    }
    for key in params:
        if not params[key]:
            raise ValueError(f"{key} is required.")
    sql = """
SELECT *
FROM orchestration_graph_runs
WHERE owner_user_id = %(owner_user_id)s
  AND graph_invocation_id = %(graph_invocation_id)s
LIMIT 1
"""
    return _command(
        operation="prepare_current_graph_run_read",
        tables=("orchestration_graph_runs",),
        sql=sql,
        params=params,
        read_only=True,
    )


def prepare_current_checkpoint_read(
    *,
    owner_user_id: str,
    graph_invocation_id: str,
) -> dict[str, Any]:
    params = {
        "owner_user_id": _clean_text(owner_user_id),
        "graph_invocation_id": _clean_text(graph_invocation_id),
    }
    for key in params:
        if not params[key]:
            raise ValueError(f"{key} is required.")
    sql = """
SELECT checkpoint.*
FROM orchestration_graph_runs AS graph_run
JOIN orchestration_checkpoints AS checkpoint
  ON checkpoint.graph_invocation_id = graph_run.graph_invocation_id
 AND checkpoint.checkpoint_id = graph_run.current_checkpoint_id
WHERE graph_run.owner_user_id = %(owner_user_id)s
  AND graph_run.graph_invocation_id = %(graph_invocation_id)s
LIMIT 1
"""
    return _command(
        operation="prepare_current_checkpoint_read",
        tables=(
            "orchestration_graph_runs",
            "orchestration_checkpoints",
        ),
        sql=sql,
        params=params,
        read_only=True,
    )


def prepare_pending_interrupt_read(
    *,
    owner_user_id: str,
    graph_invocation_id: str,
) -> dict[str, Any]:
    params = {
        "owner_user_id": _clean_text(owner_user_id),
        "graph_invocation_id": _clean_text(graph_invocation_id),
        "interrupt_status": "awaiting_decision",
    }
    for key in ("owner_user_id", "graph_invocation_id"):
        if not params[key]:
            raise ValueError(f"{key} is required.")
    sql = """
SELECT interrupt_request.*
FROM orchestration_graph_runs AS graph_run
JOIN orchestration_interrupt_requests AS interrupt_request
  ON interrupt_request.graph_invocation_id = graph_run.graph_invocation_id
 AND interrupt_request.checkpoint_id = graph_run.current_checkpoint_id
WHERE graph_run.owner_user_id = %(owner_user_id)s
  AND graph_run.graph_invocation_id = %(graph_invocation_id)s
  AND interrupt_request.interrupt_status = %(interrupt_status)s
ORDER BY interrupt_request.created_at, interrupt_request.interrupt_request_id
LIMIT 1
"""
    return _command(
        operation="prepare_pending_interrupt_read",
        tables=(
            "orchestration_graph_runs",
            "orchestration_interrupt_requests",
        ),
        sql=sql,
        params=params,
        read_only=True,
    )


def prepare_checkpoint_interrupt_commit(
    *,
    checkpoint_row: Mapping[str, Any],
    interrupt_row: Mapping[str, Any],
    expected_owner_user_id: str,
    expected_run_status: str,
    expected_lock_version: int,
    expected_current_checkpoint_id: str | None = None,
) -> dict[str, Any]:
    checkpoint_params = _checkpoint_params(checkpoint_row)
    if expected_run_status != "running":
        raise ValueError("expected_run_status_must_be_running")
    owner = _clean_text(expected_owner_user_id)
    if not owner:
        raise ValueError("expected_owner_user_id is required.")
    version = _require_nonnegative_int(
        expected_lock_version,
        "expected_lock_version",
    )
    if checkpoint_row["owner_user_id"] != owner:
        raise ValueError("checkpoint_owner_mismatch")
    for key in (
        "graph_invocation_id",
        "checkpoint_id",
        *_IDENTITY_COLUMNS,
    ):
        if interrupt_row[key] != checkpoint_row[key]:
            raise ValueError(f"checkpoint_interrupt_identity_mismatch:{key}")
    if checkpoint_row["completed_node_keys_json"] != list(
        harness.ORDERED_AGENT_KEYS
    ):
        raise ValueError("checkpoint_interrupt_completed_node_keys_invalid")
    if checkpoint_row["next_node_key"] != (
        harness.OPERATOR_REVIEW_INTERRUPT_SAFE_NEXT_NODE_KEY
    ):
        raise ValueError("checkpoint_interrupt_next_node_invalid")
    if interrupt_row["node_key"] != harness.OPERATOR_REVIEW_INTERRUPT_NODE_KEY:
        raise ValueError("checkpoint_interrupt_node_invalid")
    interrupt_params = _interrupt_params(
        interrupt_row,
        checkpoint_envelope=checkpoint_row["checkpoint_envelope_json"],
    )

    params: dict[str, Any] = {
        **{
            f"checkpoint_{key}": value
            for key, value in checkpoint_params.items()
        },
        **{
            f"interrupt_{key}": value
            for key, value in interrupt_params.items()
        },
        "expected_owner_user_id": owner,
        "expected_run_status": expected_run_status,
        "expected_lock_version": version,
        "expected_current_checkpoint_id": _optional_text(
            expected_current_checkpoint_id
        ),
        "next_run_status": "awaiting_decision",
    }
    sql = """
WITH locked_run AS (
    SELECT *
    FROM orchestration_graph_runs
    WHERE graph_invocation_id = %(checkpoint_graph_invocation_id)s
      AND owner_user_id = %(expected_owner_user_id)s
      AND pipeline_run_id = %(checkpoint_pipeline_run_id)s
      AND context_id = %(checkpoint_context_id)s
      AND job_id = %(checkpoint_job_id)s
      AND job_index = %(checkpoint_job_index)s
      AND selected_resume_id = %(checkpoint_selected_resume_id)s
      AND run_status = %(expected_run_status)s
      AND lock_version = %(expected_lock_version)s
      AND current_checkpoint_id
          IS NOT DISTINCT FROM %(expected_current_checkpoint_id)s
    FOR UPDATE
),
inserted_checkpoint AS (
    INSERT INTO orchestration_checkpoints (
        checkpoint_id, graph_invocation_id, checkpoint_sequence,
        checkpoint_schema_version, graph_state_schema_version,
        checkpoint_status, owner_user_id, pipeline_run_id, context_id,
        job_id, job_index, selected_resume_id, checkpoint_envelope_json,
        checkpoint_envelope_digest, completed_node_keys_json, next_node_key,
        committed_at, purge_after
    )
    SELECT
        %(checkpoint_checkpoint_id)s,
        %(checkpoint_graph_invocation_id)s,
        %(checkpoint_checkpoint_sequence)s,
        %(checkpoint_checkpoint_schema_version)s,
        %(checkpoint_graph_state_schema_version)s,
        %(checkpoint_checkpoint_status)s,
        %(checkpoint_owner_user_id)s,
        %(checkpoint_pipeline_run_id)s,
        %(checkpoint_context_id)s,
        %(checkpoint_job_id)s,
        %(checkpoint_job_index)s,
        %(checkpoint_selected_resume_id)s,
        %(checkpoint_checkpoint_envelope_json)s::jsonb,
        %(checkpoint_checkpoint_envelope_digest)s,
        %(checkpoint_completed_node_keys_json)s::jsonb,
        %(checkpoint_next_node_key)s,
        %(checkpoint_committed_at)s,
        %(checkpoint_purge_after)s
    FROM locked_run
    ON CONFLICT (checkpoint_id) DO NOTHING
    RETURNING checkpoint_id
),
accepted_checkpoint AS (
    SELECT checkpoint_id FROM inserted_checkpoint
    UNION ALL
    SELECT existing.checkpoint_id
    FROM orchestration_checkpoints AS existing
    WHERE existing.checkpoint_id = %(checkpoint_checkpoint_id)s
      AND existing.graph_invocation_id
          = %(checkpoint_graph_invocation_id)s
      AND existing.checkpoint_sequence
          = %(checkpoint_checkpoint_sequence)s
      AND existing.checkpoint_envelope_digest
          = %(checkpoint_checkpoint_envelope_digest)s
      AND existing.checkpoint_envelope_json
          = %(checkpoint_checkpoint_envelope_json)s::jsonb
      AND existing.completed_node_keys_json
          = %(checkpoint_completed_node_keys_json)s::jsonb
      AND existing.next_node_key = %(checkpoint_next_node_key)s
      AND NOT EXISTS (SELECT 1 FROM inserted_checkpoint)
),
inserted_interrupt AS (
    INSERT INTO orchestration_interrupt_requests (
        interrupt_request_id, graph_invocation_id, checkpoint_id,
        interrupt_request_schema_version, checkpoint_schema_version,
        graph_state_schema_version, owner_user_id, pipeline_run_id,
        context_id, job_id, job_index, selected_resume_id, node_key,
        safe_next_node_key, operator_review_artifact_type,
        operator_review_artifact_version, operator_review_artifact_digest,
        allowed_decision_values_json, interrupt_request_json,
        interrupt_status, lock_version, read_only, diagnostic_only,
        application_authorization, resume_authorization, created_at,
        expires_at, resolved_at
    )
    SELECT
        %(interrupt_interrupt_request_id)s,
        %(interrupt_graph_invocation_id)s,
        %(interrupt_checkpoint_id)s,
        %(interrupt_interrupt_request_schema_version)s,
        %(interrupt_checkpoint_schema_version)s,
        %(interrupt_graph_state_schema_version)s,
        %(interrupt_owner_user_id)s,
        %(interrupt_pipeline_run_id)s,
        %(interrupt_context_id)s,
        %(interrupt_job_id)s,
        %(interrupt_job_index)s,
        %(interrupt_selected_resume_id)s,
        %(interrupt_node_key)s,
        %(interrupt_safe_next_node_key)s,
        %(interrupt_operator_review_artifact_type)s,
        %(interrupt_operator_review_artifact_version)s,
        %(interrupt_operator_review_artifact_digest)s,
        %(interrupt_allowed_decision_values_json)s::jsonb,
        %(interrupt_interrupt_request_json)s::jsonb,
        %(interrupt_interrupt_status)s,
        %(interrupt_lock_version)s,
        %(interrupt_read_only)s,
        %(interrupt_diagnostic_only)s,
        %(interrupt_application_authorization)s,
        %(interrupt_resume_authorization)s,
        %(interrupt_created_at)s,
        %(interrupt_expires_at)s,
        %(interrupt_resolved_at)s
    FROM locked_run
    JOIN accepted_checkpoint ON TRUE
    ON CONFLICT (interrupt_request_id) DO NOTHING
    RETURNING interrupt_request_id
),
accepted_interrupt AS (
    SELECT interrupt_request_id FROM inserted_interrupt
    UNION ALL
    SELECT existing.interrupt_request_id
    FROM orchestration_interrupt_requests AS existing
    WHERE existing.interrupt_request_id
          = %(interrupt_interrupt_request_id)s
      AND existing.checkpoint_id = %(interrupt_checkpoint_id)s
      AND existing.node_key = %(interrupt_node_key)s
      AND existing.operator_review_artifact_digest
          = %(interrupt_operator_review_artifact_digest)s
      AND existing.interrupt_request_json
          = %(interrupt_interrupt_request_json)s::jsonb
      AND NOT EXISTS (SELECT 1 FROM inserted_interrupt)
),
advanced_run AS (
    UPDATE orchestration_graph_runs
    SET current_checkpoint_id = %(checkpoint_checkpoint_id)s,
        run_status = %(next_run_status)s,
        lock_version = lock_version + 1,
        updated_at = %(checkpoint_committed_at)s
    WHERE graph_invocation_id = %(checkpoint_graph_invocation_id)s
      AND owner_user_id = %(expected_owner_user_id)s
      AND run_status = %(expected_run_status)s
      AND lock_version = %(expected_lock_version)s
      AND current_checkpoint_id
          IS NOT DISTINCT FROM %(expected_current_checkpoint_id)s
      AND EXISTS (SELECT 1 FROM accepted_checkpoint)
      AND EXISTS (SELECT 1 FROM accepted_interrupt)
    RETURNING *
)
SELECT *
FROM advanced_run
"""
    return _command(
        operation="prepare_checkpoint_interrupt_commit",
        tables=(
            "orchestration_graph_runs",
            "orchestration_checkpoints",
            "orchestration_interrupt_requests",
        ),
        sql=sql,
        params=params,
        read_only=False,
    )


_DECISION_COLUMNS = (
    "decision_id", "graph_invocation_id", "checkpoint_id",
    "interrupt_request_id", *_IDENTITY_COLUMNS,
    "operator_review_artifact_digest", "decision_value", "actor_id",
    "client_idempotency_key", "expected_interrupt_status",
    "expected_interrupt_version", "expected_run_lock_version",
    "decision_record_status", "reason", "rejection_code",
    "application_authorization", "created_at",
)
_AUTHORIZATION_COLUMNS = (
    "authorization_id", "decision_id", "graph_invocation_id", "checkpoint_id",
    "interrupt_request_id", *_IDENTITY_COLUMNS,
    "operator_review_artifact_digest", "decision_value",
    "safe_next_node_key", "authorization_token_hash",
    "authorization_status", "lock_version", "read_only",
    "application_authorization", "resume_text_mutation_authorization",
    "queue_mutation_authorization", "operator_state_mutation_authorization",
    "created_at", "expires_at", "consumed_at",
)
_CONSUMPTION_COLUMNS = (
    "consumption_id", "authorization_id", "decision_id",
    "graph_invocation_id", "checkpoint_id", "interrupt_request_id",
    *_IDENTITY_COLUMNS, "resume_invocation_id", "consumer_instance_id",
    "claimed_at", "claim_status", "expected_authorization_version",
    "application_authorization",
)


def _deterministic_id(prefix: str, payload: Mapping[str, Any]) -> str:
    _reject_prohibited_payload(payload, field_path=prefix)
    return f"{prefix}:{harness._checkpoint_digest(payload)}"


def prepare_human_decision_row(
    interrupt_row: Mapping[str, Any],
    *,
    decision_value: str,
    actor_id: str,
    client_idempotency_key: str,
    expected_interrupt_version: int,
    expected_run_lock_version: int,
    created_at: str,
    reason: str = "",
) -> dict[str, Any]:
    _require_exact_fields(interrupt_row, _INTERRUPT_COLUMNS, "interrupt_row")
    decision = _clean_text(decision_value)
    if decision not in harness.OPERATOR_REVIEW_INTERRUPT_ALLOWED_DECISIONS:
        raise ValueError("decision_value_unsupported")
    actor = _clean_text(actor_id)
    idempotency_key = _clean_text(client_idempotency_key)
    created = _clean_text(created_at)
    if not actor or not idempotency_key or not created:
        raise ValueError("decision_required_field_missing")
    note = _clean_text(reason)
    if len(note.encode("utf-8")) > 4096:
        raise ValueError("decision_reason_too_large")
    seed = {
        "interrupt_request_id": interrupt_row["interrupt_request_id"],
        "client_idempotency_key": idempotency_key,
        "decision_value": decision,
        "actor_id": actor,
        "graph_invocation_id": interrupt_row["graph_invocation_id"],
        "checkpoint_id": interrupt_row["checkpoint_id"],
        "operator_review_artifact_digest": interrupt_row[
            "operator_review_artifact_digest"
        ],
    }
    return {
        "decision_id": _deterministic_id("human-decision", seed),
        "graph_invocation_id": interrupt_row["graph_invocation_id"],
        "checkpoint_id": interrupt_row["checkpoint_id"],
        "interrupt_request_id": interrupt_row["interrupt_request_id"],
        **{key: deepcopy(interrupt_row[key]) for key in _IDENTITY_COLUMNS},
        "operator_review_artifact_digest": interrupt_row[
            "operator_review_artifact_digest"
        ],
        "decision_value": decision,
        "actor_id": actor,
        "client_idempotency_key": idempotency_key,
        "expected_interrupt_status": "awaiting_decision",
        "expected_interrupt_version": _require_nonnegative_int(
            expected_interrupt_version, "expected_interrupt_version"
        ),
        "expected_run_lock_version": _require_nonnegative_int(
            expected_run_lock_version, "expected_run_lock_version"
        ),
        "decision_record_status": "recorded",
        "reason": note,
        "rejection_code": "",
        "application_authorization": False,
        "created_at": created,
    }


def prepare_resume_authorization_row(
    decision_row: Mapping[str, Any],
    *,
    authorization_token_hash: str,
    created_at: str,
    expires_at: str,
) -> dict[str, Any]:
    _require_exact_fields(decision_row, _DECISION_COLUMNS, "decision_row")
    if decision_row["decision_value"] != "continue_read_only":
        raise ValueError("decision_not_resume_authorizable")
    token_hash = _clean_text(authorization_token_hash)
    if re.fullmatch(r"[0-9a-f]{64}", token_hash) is None:
        raise ValueError("authorization_token_hash_invalid")
    created, expires = _clean_text(created_at), _clean_text(expires_at)
    if not created or not expires:
        raise ValueError("authorization_timestamp_required")
    seed = {
        "decision_id": decision_row["decision_id"],
        "interrupt_request_id": decision_row["interrupt_request_id"],
        "authorization_token_hash": token_hash,
        "safe_next_node_key": "finalize",
    }
    return {
        "authorization_id": _deterministic_id("resume-authorization", seed),
        "decision_id": decision_row["decision_id"],
        "graph_invocation_id": decision_row["graph_invocation_id"],
        "checkpoint_id": decision_row["checkpoint_id"],
        "interrupt_request_id": decision_row["interrupt_request_id"],
        **{key: deepcopy(decision_row[key]) for key in _IDENTITY_COLUMNS},
        "operator_review_artifact_digest": decision_row[
            "operator_review_artifact_digest"
        ],
        "decision_value": "continue_read_only",
        "safe_next_node_key": "finalize",
        "authorization_token_hash": token_hash,
        "authorization_status": "authorized",
        "lock_version": 0,
        "read_only": True,
        "application_authorization": False,
        "resume_text_mutation_authorization": False,
        "queue_mutation_authorization": False,
        "operator_state_mutation_authorization": False,
        "created_at": created,
        "expires_at": expires,
        "consumed_at": None,
    }


def prepare_resume_consumption_row(
    authorization_row: Mapping[str, Any],
    *,
    consumer_instance_id: str,
    claimed_at: str,
    expected_authorization_version: int,
) -> dict[str, Any]:
    _require_exact_fields(
        authorization_row, _AUTHORIZATION_COLUMNS, "authorization_row"
    )
    if authorization_row["authorization_status"] != "authorized":
        raise ValueError("authorization_not_consumable")
    consumer, claimed = (
        _clean_text(consumer_instance_id), _clean_text(claimed_at)
    )
    if not consumer or not claimed:
        raise ValueError("consumption_required_field_missing")
    resume_seed = {
        "authorization_id": authorization_row["authorization_id"],
        "consumer_instance_id": consumer,
    }
    resume_id = _deterministic_id("resume-invocation", resume_seed)
    return {
        "consumption_id": _deterministic_id(
            "resume-consumption",
            {"authorization_id": authorization_row["authorization_id"]},
        ),
        "authorization_id": authorization_row["authorization_id"],
        "decision_id": authorization_row["decision_id"],
        "graph_invocation_id": authorization_row["graph_invocation_id"],
        "checkpoint_id": authorization_row["checkpoint_id"],
        "interrupt_request_id": authorization_row["interrupt_request_id"],
        **{key: deepcopy(authorization_row[key]) for key in _IDENTITY_COLUMNS},
        "resume_invocation_id": resume_id,
        "consumer_instance_id": consumer,
        "claimed_at": claimed,
        "claim_status": "claimed",
        "expected_authorization_version": _require_nonnegative_int(
            expected_authorization_version, "expected_authorization_version"
        ),
        "authorization_token_hash_proof": authorization_row[
            "authorization_token_hash"
        ],
        "application_authorization": False,
    }


def _owner_scoped_read(
    operation: str, table: str, id_column: str, id_value: str,
    owner_user_id: str,
) -> dict[str, Any]:
    owner, identifier = _clean_text(owner_user_id), _clean_text(id_value)
    if not owner or not identifier:
        raise ValueError("owner_and_identity_required")
    return _command(
        operation=operation, tables=(table,), read_only=True,
        sql=f"SELECT * FROM {table} WHERE owner_user_id = %(owner_user_id)s "
            f"AND {id_column} = %(identity)s LIMIT 1",
        params={"owner_user_id": owner, "identity": identifier},
    )


def prepare_current_decision_read(*, owner_user_id: str, interrupt_request_id: str):
    return _owner_scoped_read(
        "prepare_current_decision_read", "orchestration_human_decisions",
        "interrupt_request_id", interrupt_request_id, owner_user_id,
    )


def prepare_resume_authorization_read(*, owner_user_id: str, decision_id: str):
    return _owner_scoped_read(
        "prepare_resume_authorization_read",
        "orchestration_resume_authorizations", "decision_id", decision_id,
        owner_user_id,
    )


def prepare_resume_consumption_read(*, owner_user_id: str, authorization_id: str):
    return _owner_scoped_read(
        "prepare_resume_consumption_read", "orchestration_resume_consumptions",
        "authorization_id", authorization_id, owner_user_id,
    )


def prepare_authorized_resume_work_read(*, owner_user_id: str, graph_invocation_id: str):
    owner, graph_id = _clean_text(owner_user_id), _clean_text(graph_invocation_id)
    if not owner or not graph_id:
        raise ValueError("owner_and_identity_required")
    return _command(
        operation="prepare_authorized_resume_work_read",
        tables=("orchestration_resume_authorizations",),
        read_only=True,
        sql="SELECT * FROM orchestration_resume_authorizations "
            "WHERE owner_user_id = %(owner_user_id)s "
            "AND graph_invocation_id = %(graph_invocation_id)s "
            "AND authorization_status = 'authorized' ORDER BY created_at LIMIT 1",
        params={"owner_user_id": owner, "graph_invocation_id": graph_id},
    )


def _atomic_transition_command(
    operation: str, row: Mapping[str, Any], columns: tuple[str, ...],
    insert_table: str, expected_run_status: str,
    expected_interrupt_status: str, next_run_status: str,
    next_interrupt_status: str, insert_columns: tuple[str, ...] | None = None,
) -> dict[str, Any]:
    _require_exact_fields(row, columns, operation)
    params = deepcopy(dict(row))
    params.update({
        "expected_run_status": expected_run_status,
        "expected_interrupt_status": expected_interrupt_status,
        "next_run_status": next_run_status,
        "next_interrupt_status": next_interrupt_status,
    })
    persisted_columns = insert_columns or columns
    column_sql = ", ".join(persisted_columns)
    value_sql = ", ".join(f"%({column})s" for column in persisted_columns)
    sql = f"""
WITH locked_run AS (
 SELECT * FROM orchestration_graph_runs
 WHERE graph_invocation_id = %(graph_invocation_id)s
   AND owner_user_id = %(owner_user_id)s
   AND current_checkpoint_id = %(checkpoint_id)s
   AND run_status = %(expected_run_status)s
   AND lock_version = %(expected_run_lock_version)s FOR UPDATE
), locked_interrupt AS (
 SELECT * FROM orchestration_interrupt_requests
 WHERE interrupt_request_id = %(interrupt_request_id)s
   AND checkpoint_id = %(checkpoint_id)s
   AND operator_review_artifact_digest = %(operator_review_artifact_digest)s
   AND interrupt_status = %(expected_interrupt_status)s
   AND lock_version = %(expected_interrupt_version)s FOR UPDATE
), inserted AS (
 INSERT INTO {insert_table} ({column_sql})
 SELECT {value_sql} FROM locked_run JOIN locked_interrupt ON TRUE
 ON CONFLICT DO NOTHING RETURNING *
), updated_interrupt AS (
 UPDATE orchestration_interrupt_requests
 SET interrupt_status = %(next_interrupt_status)s, lock_version = lock_version + 1
 WHERE interrupt_request_id = %(interrupt_request_id)s
   AND EXISTS (SELECT 1 FROM inserted) RETURNING *
)
UPDATE orchestration_graph_runs
SET run_status = %(next_run_status)s, lock_version = lock_version + 1
WHERE graph_invocation_id = %(graph_invocation_id)s
  AND EXISTS (SELECT 1 FROM inserted)
RETURNING *
"""
    return _command(
        operation=operation,
        tables=("orchestration_graph_runs",
                "orchestration_interrupt_requests", insert_table),
        sql=sql, params=params, read_only=False,
    )


def prepare_human_decision_recording(decision_row: Mapping[str, Any]):
    decision = decision_row.get("decision_value")
    next_status = {
        "continue_read_only": "decision_recorded",
        "needs_revision": "decision_rejected",
        "cancel": "cancelled",
    }.get(decision)
    if next_status is None:
        raise ValueError("decision_value_unsupported")
    return _atomic_transition_command(
        "prepare_human_decision_recording", decision_row, _DECISION_COLUMNS,
        "orchestration_human_decisions", "awaiting_decision",
        "awaiting_decision", next_status, next_status,
    )


def prepare_resume_authorization_commit(
    authorization_row: Mapping[str, Any], *,
    expected_run_lock_version: int, expected_interrupt_version: int,
):
    row = dict(authorization_row)
    row["expected_run_lock_version"] = _require_nonnegative_int(
        expected_run_lock_version, "expected_run_lock_version"
    )
    row["expected_interrupt_version"] = _require_nonnegative_int(
        expected_interrupt_version, "expected_interrupt_version"
    )
    columns = (*_AUTHORIZATION_COLUMNS,
               "expected_run_lock_version", "expected_interrupt_version")
    return _atomic_transition_command(
        "prepare_resume_authorization_commit", row, columns,
        "orchestration_resume_authorizations", "decision_recorded",
        "decision_recorded", "resume_authorized", "resume_authorized",
        _AUTHORIZATION_COLUMNS,
    )


def prepare_resume_consumption_commit(
    consumption_row: Mapping[str, Any], *, expected_run_lock_version: int,
    expected_interrupt_version: int,
    authorization_token_hash: str | None = None,
):
    _require_exact_fields(
        consumption_row,
        (*_CONSUMPTION_COLUMNS, "authorization_token_hash_proof"),
        "consumption_row",
    )
    token_hash = _clean_text(
        authorization_token_hash
        if authorization_token_hash is not None
        else consumption_row["authorization_token_hash_proof"]
    )
    if re.fullmatch(r"[0-9a-f]{64}", token_hash) is None:
        raise ValueError("authorization_token_hash_invalid")
    params = {
        **{
            key: deepcopy(consumption_row[key])
            for key in _CONSUMPTION_COLUMNS
        },
        "authorization_token_hash": token_hash,
        "expected_run_lock_version": _require_nonnegative_int(
            expected_run_lock_version, "expected_run_lock_version"
        ),
        "expected_interrupt_version": _require_nonnegative_int(
            expected_interrupt_version, "expected_interrupt_version"
        ),
    }
    columns = ", ".join(_CONSUMPTION_COLUMNS)
    values = ", ".join(f"%({column})s" for column in _CONSUMPTION_COLUMNS)
    identity_predicates = "\n".join(
        f"   AND {column} = %({column})s"
        for column in (
            "decision_id", "graph_invocation_id", "checkpoint_id",
            "interrupt_request_id", *_IDENTITY_COLUMNS,
        )
    )
    sql = f"""
WITH locked_authorization AS (
 SELECT * FROM orchestration_resume_authorizations
 WHERE authorization_id = %(authorization_id)s
{identity_predicates}
   AND authorization_status = 'authorized'
   AND lock_version = %(expected_authorization_version)s
   AND authorization_token_hash = %(authorization_token_hash)s
   AND expires_at > %(claimed_at)s
 FOR UPDATE
), locked_run AS (
 SELECT * FROM orchestration_graph_runs
 WHERE graph_invocation_id = %(graph_invocation_id)s
   AND owner_user_id = %(owner_user_id)s
   AND current_checkpoint_id = %(checkpoint_id)s
   AND run_status = 'resume_authorized'
   AND lock_version = %(expected_run_lock_version)s
 FOR UPDATE
), locked_interrupt AS (
 SELECT * FROM orchestration_interrupt_requests
 WHERE interrupt_request_id = %(interrupt_request_id)s
   AND graph_invocation_id = %(graph_invocation_id)s
   AND checkpoint_id = %(checkpoint_id)s
   AND owner_user_id = %(owner_user_id)s
   AND interrupt_status = 'resume_authorized'
   AND lock_version = %(expected_interrupt_version)s
 FOR UPDATE
), updated_authorization AS (
 UPDATE orchestration_resume_authorizations
 SET authorization_status = 'consumed', consumed_at = %(claimed_at)s,
     lock_version = lock_version + 1
 WHERE authorization_id = %(authorization_id)s
   AND EXISTS (SELECT 1 FROM locked_authorization)
   AND EXISTS (SELECT 1 FROM locked_run)
   AND EXISTS (SELECT 1 FROM locked_interrupt)
 RETURNING *
), inserted_consumption AS (
 INSERT INTO orchestration_resume_consumptions ({columns})
 SELECT {values} FROM updated_authorization
 ON CONFLICT DO NOTHING RETURNING *
), updated_interrupt AS (
 UPDATE orchestration_interrupt_requests
 SET interrupt_status = 'resume_consumed', lock_version = lock_version + 1
 WHERE interrupt_request_id = %(interrupt_request_id)s
   AND EXISTS (SELECT 1 FROM inserted_consumption)
 RETURNING *
), updated_run AS (
 UPDATE orchestration_graph_runs
 SET run_status = 'resume_consumed', lock_version = lock_version + 1,
     updated_at = %(claimed_at)s
 WHERE graph_invocation_id = %(graph_invocation_id)s
   AND EXISTS (SELECT 1 FROM inserted_consumption)
   AND EXISTS (SELECT 1 FROM updated_interrupt)
 RETURNING *
)
SELECT inserted_consumption.*
FROM inserted_consumption JOIN updated_run ON TRUE
"""
    return _command(
        operation="prepare_resume_consumption_commit",
        tables=(
            "orchestration_graph_runs",
            "orchestration_interrupt_requests",
            "orchestration_resume_authorizations",
            "orchestration_resume_consumptions",
        ),
        sql=sql,
        params=params,
        read_only=False,
    )


NODE_ATTEMPT_STATUS_VALUES = (
    "pending", "claimed", "succeeded", "failed", "abandoned",
)
TERMINAL_STATUS_VALUES = ("completed", "failed", "cancelled")
LIFECYCLE_EVENT_TYPE_VALUES = (
    "graph_run_created", "checkpoint_committed", "interrupt_created",
    "decision_recorded", "decision_rejected", "authorization_created",
    "authorization_consumed", "node_attempt_claimed",
    "node_attempt_succeeded", "node_attempt_failed",
    "terminal_result_recorded", "recovery_claim_recorded",
)
_NODE_ATTEMPT_COLUMNS = (
    "node_attempt_id", "graph_invocation_id", "input_checkpoint_id",
    "output_checkpoint_id", *_IDENTITY_COLUMNS, "node_key",
    "attempt_number", "resume_invocation_id", "attempt_status",
    "lease_owner_id", "lease_acquired_at", "lease_expires_at", "started_at",
    "completed_at", "duration_ms", "input_digest", "output_digest",
    "error_code", "error_detail", "lock_version",
    "application_authorization", "mutation_authorization",
    "created_at", "updated_at",
)
_TERMINAL_RESULT_COLUMNS = (
    "terminal_result_id", "graph_invocation_id", "terminal_checkpoint_id",
    *_IDENTITY_COLUMNS, "graph_state_schema_version",
    "checkpoint_schema_version", "terminal_status", "result_digest",
    "result_metadata_json", "final_node_order_json", "failure_code",
    "application_authorization", "completed_at",
)
_LIFECYCLE_EVENT_COLUMNS = (
    "event_id", "graph_invocation_id", "checkpoint_id",
    "interrupt_request_id", "decision_id", "authorization_id",
    "consumption_id", "node_attempt_id", "terminal_result_id",
    "owner_user_id", "event_type", "aggregate_type", "aggregate_id",
    "event_sequence", "event_payload_json", "event_timestamp",
    "projection_status", "projected_at", "projection_retry_count",
)

LANGGRAPH_CHECKPOINT_BINDING_SCHEMA_VERSION = (
    "langgraph-checkpoint-binding-v1"
)
LANGGRAPH_CHECKPOINT_BINDING_AGGREGATE_TYPE = (
    "langgraph_checkpoint_binding"
)


def _require_digest(value: Any, key: str) -> str:
    digest = _clean_text(value)
    if re.fullmatch(r"[0-9a-f]{64}", digest) is None:
        raise ValueError(f"{key}_invalid")
    return digest


def prepare_node_attempt_row(
    graph_run_row: Mapping[str, Any],
    *,
    input_checkpoint_id: str,
    node_key: str,
    attempt_number: int,
    input_digest: str,
    created_at: str,
    resume_invocation_id: str = "",
) -> dict[str, Any]:
    _graph_run_params(graph_run_row)
    checkpoint_id = _clean_text(input_checkpoint_id)
    node = _clean_text(node_key)
    if not checkpoint_id:
        raise ValueError("input_checkpoint_id_required")
    if node not in (*harness.ORDERED_AGENT_KEYS, "finalize"):
        raise ValueError("node_key_unsupported")
    attempt = _require_nonnegative_int(attempt_number, "attempt_number")
    if attempt < 1:
        raise ValueError("attempt_number_must_be_positive")
    created = _clean_text(created_at)
    if not created:
        raise ValueError("created_at is required.")
    resume_id = _optional_text(resume_invocation_id)
    seed = {
        "graph_invocation_id": graph_run_row["graph_invocation_id"],
        "input_checkpoint_id": checkpoint_id,
        "node_key": node,
        "attempt_number": attempt,
        "resume_invocation_id": resume_id,
    }
    return {
        "node_attempt_id": _deterministic_id("node-attempt", seed),
        "graph_invocation_id": graph_run_row["graph_invocation_id"],
        "input_checkpoint_id": checkpoint_id,
        "output_checkpoint_id": None,
        **{key: deepcopy(graph_run_row[key]) for key in _IDENTITY_COLUMNS},
        "node_key": node,
        "attempt_number": attempt,
        "resume_invocation_id": resume_id,
        "attempt_status": "pending",
        "lease_owner_id": None,
        "lease_acquired_at": None,
        "lease_expires_at": None,
        "started_at": None,
        "completed_at": None,
        "duration_ms": None,
        "input_digest": _require_digest(input_digest, "input_digest"),
        "output_digest": None,
        "error_code": "",
        "error_detail": "",
        "lock_version": 0,
        "application_authorization": False,
        "mutation_authorization": False,
        "created_at": created,
        "updated_at": created,
    }


def prepare_terminal_result_row(
    graph_run_row: Mapping[str, Any],
    *,
    terminal_checkpoint_id: str,
    checkpoint_schema_version: str,
    terminal_status: str,
    result_metadata: Mapping[str, Any],
    completed_at: str,
    failure_code: str = "",
) -> dict[str, Any]:
    _graph_run_params(graph_run_row)
    status = _clean_text(terminal_status)
    if status not in TERMINAL_STATUS_VALUES:
        raise ValueError("terminal_status_unsupported")
    checkpoint_id = _clean_text(terminal_checkpoint_id)
    if not checkpoint_id:
        raise ValueError("terminal_checkpoint_id_required")
    if checkpoint_schema_version != harness.CHECKPOINT_SCHEMA_VERSION:
        raise ValueError("checkpoint_schema_version_unsupported")
    _reject_prohibited_payload(result_metadata, field_path="result_metadata")
    metadata_json = json.loads(
        _canonical_json(result_metadata, field_path="result_metadata")
    )
    if len(
        _canonical_json(
            metadata_json, field_path="result_metadata"
        ).encode("utf-8")
    ) > 262144:
        raise ValueError("result_metadata_too_large")
    result_digest = harness._checkpoint_digest(metadata_json)
    failure = _clean_text(failure_code)
    completed = _clean_text(completed_at)
    if not completed:
        raise ValueError("completed_at_required")
    if len(failure.encode("utf-8")) > 256:
        raise ValueError("failure_code_too_large")
    if status == "failed" and not failure:
        raise ValueError("failed_terminal_result_requires_failure_code")
    if status != "failed" and failure:
        raise ValueError("nonfailed_terminal_result_prohibits_failure_code")
    seed = {
        "graph_invocation_id": graph_run_row["graph_invocation_id"],
        "terminal_checkpoint_id": checkpoint_id,
        "terminal_status": status,
        "result_digest": result_digest,
    }
    return {
        "terminal_result_id": _deterministic_id("terminal-result", seed),
        "graph_invocation_id": graph_run_row["graph_invocation_id"],
        "terminal_checkpoint_id": checkpoint_id,
        **{key: deepcopy(graph_run_row[key]) for key in _IDENTITY_COLUMNS},
        "graph_state_schema_version": graph_run_row[
            "graph_state_schema_version"
        ],
        "checkpoint_schema_version": checkpoint_schema_version,
        "terminal_status": status,
        "result_digest": result_digest,
        "result_metadata_json": deepcopy(metadata_json),
        "final_node_order_json": list(harness.ORDERED_AGENT_KEYS),
        "failure_code": failure,
        "application_authorization": False,
        "completed_at": completed,
    }


def prepare_lifecycle_event_row(
    graph_run_row: Mapping[str, Any],
    *,
    event_type: str,
    aggregate_type: str,
    aggregate_id: str,
    event_sequence: int,
    event_payload: Mapping[str, Any],
    event_timestamp: str,
    references: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    _graph_run_params(graph_run_row)
    event = _clean_text(event_type)
    if event not in LIFECYCLE_EVENT_TYPE_VALUES:
        raise ValueError("event_type_unsupported")
    aggregate, aggregate_key = (
        _clean_text(aggregate_type), _clean_text(aggregate_id)
    )
    if not aggregate or not aggregate_key:
        raise ValueError("aggregate_identity_required")
    sequence = _require_nonnegative_int(event_sequence, "event_sequence")
    timestamp = _clean_text(event_timestamp)
    if not timestamp:
        raise ValueError("event_timestamp_required")
    _reject_prohibited_payload(event_payload, field_path="event_payload")
    payload_json = json.loads(
        _canonical_json(event_payload, field_path="event_payload")
    )
    if len(_canonical_json(payload_json, field_path="event_payload").encode()) > 262144:
        raise ValueError("event_payload_too_large")
    refs = dict(references or {})
    allowed_refs = {
        "checkpoint_id", "interrupt_request_id", "decision_id",
        "authorization_id", "consumption_id", "node_attempt_id",
        "terminal_result_id",
    }
    if set(refs) - allowed_refs:
        raise ValueError("lifecycle_event_reference_fields_invalid")
    normalized_refs = {
        key: _optional_text(refs.get(key)) for key in allowed_refs
    }
    seed = {
        "graph_invocation_id": graph_run_row["graph_invocation_id"],
        "event_type": event,
        "aggregate_type": aggregate,
        "aggregate_id": aggregate_key,
        "event_sequence": sequence,
        "references": normalized_refs,
        "payload_digest": harness._checkpoint_digest(payload_json),
    }
    return {
        "event_id": _deterministic_id("lifecycle-event", seed),
        "graph_invocation_id": graph_run_row["graph_invocation_id"],
        **normalized_refs,
        "owner_user_id": graph_run_row["owner_user_id"],
        "event_type": event,
        "aggregate_type": aggregate,
        "aggregate_id": aggregate_key,
        "event_sequence": sequence,
        "event_payload_json": deepcopy(payload_json),
        "event_timestamp": timestamp,
        "projection_status": "pending",
        "projected_at": None,
        "projection_retry_count": 0,
    }


def prepare_langgraph_checkpoint_binding_row(
    graph_run_row: Mapping[str, Any],
    *,
    repository_checkpoint_id: str,
    langgraph_thread_id: str,
    langgraph_checkpoint_namespace: str,
    langgraph_checkpoint_id: str,
    event_timestamp: str,
) -> dict[str, Any]:
    repository_id = _clean_text(repository_checkpoint_id)
    thread_id = _clean_text(langgraph_thread_id)
    checkpoint_id = _clean_text(langgraph_checkpoint_id)
    if not repository_id or not thread_id or not checkpoint_id:
        raise ValueError("checkpoint_binding_identity_required")
    if repository_id == checkpoint_id:
        raise ValueError("checkpoint_binding_ids_must_be_distinct")
    payload = {
        "binding_schema_version": LANGGRAPH_CHECKPOINT_BINDING_SCHEMA_VERSION,
        "graph_invocation_id": graph_run_row.get("graph_invocation_id"),
        "repository_checkpoint_id": repository_id,
        "langgraph_thread_id": thread_id,
        "langgraph_checkpoint_namespace": _clean_text(
            langgraph_checkpoint_namespace
        ),
        "langgraph_checkpoint_id": checkpoint_id,
    }
    return prepare_lifecycle_event_row(
        graph_run_row,
        event_type="checkpoint_committed",
        aggregate_type=LANGGRAPH_CHECKPOINT_BINDING_AGGREGATE_TYPE,
        aggregate_id=repository_id,
        event_sequence=0,
        event_payload=payload,
        event_timestamp=event_timestamp,
        references={"checkpoint_id": repository_id},
    )


def prepare_langgraph_checkpoint_binding_commit(
    binding_row: Mapping[str, Any],
) -> dict[str, Any]:
    _require_exact_fields(
        binding_row, _LIFECYCLE_EVENT_COLUMNS, "checkpoint_binding"
    )
    payload = binding_row["event_payload_json"]
    normalized_refs = {
        key: binding_row[key]
        for key in (
            "checkpoint_id", "interrupt_request_id", "decision_id",
            "authorization_id", "consumption_id", "node_attempt_id",
            "terminal_result_id",
        )
    }
    expected_event_id = _deterministic_id(
        "lifecycle-event",
        {
            "graph_invocation_id": binding_row["graph_invocation_id"],
            "event_type": binding_row["event_type"],
            "aggregate_type": binding_row["aggregate_type"],
            "aggregate_id": binding_row["aggregate_id"],
            "event_sequence": binding_row["event_sequence"],
            "references": normalized_refs,
            "payload_digest": harness._checkpoint_digest(payload),
        },
    )
    if (
        binding_row["event_type"] != "checkpoint_committed"
        or binding_row["aggregate_type"]
        != LANGGRAPH_CHECKPOINT_BINDING_AGGREGATE_TYPE
        or binding_row["event_sequence"] != 0
        or binding_row["aggregate_id"] != binding_row["checkpoint_id"]
        or not isinstance(payload, Mapping)
        or payload.get("binding_schema_version")
        != LANGGRAPH_CHECKPOINT_BINDING_SCHEMA_VERSION
        or payload.get("graph_invocation_id")
        != binding_row["graph_invocation_id"]
        or payload.get("repository_checkpoint_id")
        != binding_row["checkpoint_id"]
        or binding_row["event_id"] != expected_event_id
    ):
        raise ValueError("checkpoint_binding_contract_invalid")
    params = _prefixed_params("binding", binding_row)
    params["binding_event_payload_json"] = _canonical_json(
        payload, field_path="checkpoint_binding.event_payload"
    )
    sql = """
WITH locked_checkpoint AS (
 SELECT checkpoint_id FROM orchestration_checkpoints
 WHERE checkpoint_id = %(binding_checkpoint_id)s
   AND graph_invocation_id = %(binding_graph_invocation_id)s
   AND owner_user_id = %(binding_owner_user_id)s
), inserted_binding AS (
 INSERT INTO orchestration_lifecycle_events
 SELECT %(binding_event_id)s, %(binding_graph_invocation_id)s,
        %(binding_checkpoint_id)s, %(binding_interrupt_request_id)s,
        %(binding_decision_id)s, %(binding_authorization_id)s,
        %(binding_consumption_id)s, %(binding_node_attempt_id)s,
        %(binding_terminal_result_id)s, %(binding_owner_user_id)s,
        %(binding_event_type)s, %(binding_aggregate_type)s,
        %(binding_aggregate_id)s, %(binding_event_sequence)s,
        %(binding_event_payload_json)s::jsonb,
        %(binding_event_timestamp)s, %(binding_projection_status)s,
        %(binding_projected_at)s, %(binding_projection_retry_count)s
 FROM locked_checkpoint
 ON CONFLICT DO NOTHING RETURNING *
), accepted_binding AS (
 SELECT inserted_binding.*, FALSE AS idempotent_duplicate
 FROM inserted_binding
 UNION ALL
 SELECT existing.*, TRUE AS idempotent_duplicate
 FROM orchestration_lifecycle_events AS existing
 WHERE existing.event_id = %(binding_event_id)s
   AND existing.graph_invocation_id = %(binding_graph_invocation_id)s
   AND existing.checkpoint_id = %(binding_checkpoint_id)s
   AND existing.owner_user_id = %(binding_owner_user_id)s
   AND existing.event_type = %(binding_event_type)s
   AND existing.aggregate_type = %(binding_aggregate_type)s
   AND existing.aggregate_id = %(binding_aggregate_id)s
   AND existing.event_sequence = %(binding_event_sequence)s
   AND existing.event_payload_json = %(binding_event_payload_json)s::jsonb
   AND NOT EXISTS (SELECT 1 FROM inserted_binding)
)
SELECT * FROM accepted_binding
"""
    return _command(
        operation="prepare_langgraph_checkpoint_binding_commit",
        tables=(
            "orchestration_checkpoints",
            "orchestration_lifecycle_events",
        ),
        sql=sql,
        params=params,
        read_only=False,
    )


def prepare_langgraph_checkpoint_binding_read(
    *,
    owner_user_id: str,
    graph_invocation_id: str,
    repository_checkpoint_id: str,
) -> dict[str, Any]:
    owner = _clean_text(owner_user_id)
    graph_id = _clean_text(graph_invocation_id)
    checkpoint_id = _clean_text(repository_checkpoint_id)
    if not owner or not graph_id or not checkpoint_id:
        raise ValueError("checkpoint_binding_read_identity_required")
    return _command(
        operation="prepare_langgraph_checkpoint_binding_read",
        tables=("orchestration_lifecycle_events",),
        read_only=True,
        sql="""
SELECT * FROM orchestration_lifecycle_events
WHERE owner_user_id = %(owner_user_id)s
  AND graph_invocation_id = %(graph_invocation_id)s
  AND checkpoint_id = %(repository_checkpoint_id)s
  AND event_type = 'checkpoint_committed'
  AND aggregate_type = %(aggregate_type)s
  AND aggregate_id = %(repository_checkpoint_id)s
  AND event_sequence = 0
""",
        params={
            "owner_user_id": owner,
            "graph_invocation_id": graph_id,
            "repository_checkpoint_id": checkpoint_id,
            "aggregate_type": LANGGRAPH_CHECKPOINT_BINDING_AGGREGATE_TYPE,
        },
    )


def terminal_results_are_identical(
    existing: Mapping[str, Any], candidate: Mapping[str, Any]
) -> bool:
    _require_exact_fields(existing, _TERMINAL_RESULT_COLUMNS, "terminal_result")
    _require_exact_fields(candidate, _TERMINAL_RESULT_COLUMNS, "terminal_result")
    return _canonical_json(existing, field_path="existing_terminal") == (
        _canonical_json(candidate, field_path="candidate_terminal")
    )


def require_idempotent_terminal_result(
    existing: Mapping[str, Any], candidate: Mapping[str, Any]
) -> dict[str, Any]:
    if not terminal_results_are_identical(existing, candidate):
        raise ValueError("terminal_result_digest_conflict")
    return deepcopy(dict(candidate))


def _prefixed_params(prefix: str, row: Mapping[str, Any]) -> dict[str, Any]:
    return {f"{prefix}_{key}": deepcopy(value) for key, value in row.items()}


def prepare_pending_node_attempt_insert(attempt_row: Mapping[str, Any]):
    _require_exact_fields(attempt_row, _NODE_ATTEMPT_COLUMNS, "node_attempt")
    columns = ", ".join(_NODE_ATTEMPT_COLUMNS)
    values = ", ".join(f"%({column})s" for column in _NODE_ATTEMPT_COLUMNS)
    return _command(
        operation="prepare_pending_node_attempt_insert",
        tables=("orchestration_node_attempts",), read_only=False,
        sql=f"INSERT INTO orchestration_node_attempts ({columns}) VALUES "
            f"({values}) ON CONFLICT "
            "(graph_invocation_id, input_checkpoint_id, node_key, attempt_number) "
            "DO NOTHING RETURNING *",
        params=attempt_row,
    )


def _attempt_transition_command(
    operation: str, attempt_row: Mapping[str, Any],
    lifecycle_event_row: Mapping[str, Any], *, expected_status: str,
    next_status: str, expected_lock_version: int,
    expected_run_status: str, expected_run_lock_version: int,
    extra_set: str = "",
):
    _require_exact_fields(attempt_row, _NODE_ATTEMPT_COLUMNS, "node_attempt")
    _require_exact_fields(
        lifecycle_event_row, _LIFECYCLE_EVENT_COLUMNS, "lifecycle_event"
    )
    if (
        lifecycle_event_row["graph_invocation_id"]
        != attempt_row["graph_invocation_id"]
        or lifecycle_event_row["owner_user_id"]
        != attempt_row["owner_user_id"]
        or lifecycle_event_row["node_attempt_id"]
        != attempt_row["node_attempt_id"]
    ):
        raise ValueError("attempt_lifecycle_identity_mismatch")
    expected_event_type = {
        "prepare_node_attempt_claim": "node_attempt_claimed",
        "prepare_node_attempt_success": "node_attempt_succeeded",
        "prepare_node_attempt_failure": "node_attempt_failed",
        "prepare_expired_attempt_abandonment": "node_attempt_failed",
    }[operation]
    if lifecycle_event_row["event_type"] != expected_event_type:
        raise ValueError("attempt_lifecycle_event_type_mismatch")
    params = {
        **_prefixed_params("attempt", attempt_row),
        **_prefixed_params("event", lifecycle_event_row),
        "expected_status": expected_status,
        "next_status": next_status,
        "expected_lock_version": _require_nonnegative_int(
            expected_lock_version, "expected_lock_version"
        ),
        "expected_run_status": _clean_text(expected_run_status),
        "expected_run_lock_version": _require_nonnegative_int(
            expected_run_lock_version, "expected_run_lock_version"
        ),
    }
    if params["expected_run_status"] not in (
        "resume_consumed", "resumed",
    ):
        raise ValueError("node_attempt_run_status_unsupported")
    sql = f"""
WITH locked_run AS (
 SELECT * FROM orchestration_graph_runs
 WHERE graph_invocation_id = %(attempt_graph_invocation_id)s
   AND owner_user_id = %(attempt_owner_user_id)s
   AND current_checkpoint_id = %(attempt_input_checkpoint_id)s
   AND run_status = %(expected_run_status)s
   AND lock_version = %(expected_run_lock_version)s
 FOR UPDATE
), updated_attempt AS (
 UPDATE orchestration_node_attempts
 SET attempt_status = %(next_status)s, lock_version = lock_version + 1,
     updated_at = %(event_event_timestamp)s {extra_set}
 WHERE node_attempt_id = %(attempt_node_attempt_id)s
   AND owner_user_id = %(attempt_owner_user_id)s
   AND attempt_status = %(expected_status)s
   AND lock_version = %(expected_lock_version)s
   AND EXISTS (SELECT 1 FROM locked_run)
 RETURNING *
), inserted_event AS (
 INSERT INTO orchestration_lifecycle_events
 SELECT %(event_event_id)s, %(event_graph_invocation_id)s,
        %(event_checkpoint_id)s, %(event_interrupt_request_id)s,
        %(event_decision_id)s, %(event_authorization_id)s,
        %(event_consumption_id)s, %(event_node_attempt_id)s,
        %(event_terminal_result_id)s, %(event_owner_user_id)s,
        %(event_event_type)s, %(event_aggregate_type)s,
        %(event_aggregate_id)s, %(event_event_sequence)s,
        %(event_event_payload_json)s::jsonb, %(event_event_timestamp)s,
        %(event_projection_status)s, %(event_projected_at)s,
        %(event_projection_retry_count)s
 FROM updated_attempt ON CONFLICT (event_id) DO NOTHING RETURNING *
)
SELECT * FROM updated_attempt
"""
    return _command(
        operation=operation,
        tables=("orchestration_graph_runs", "orchestration_node_attempts",
                "orchestration_lifecycle_events"),
        sql=sql, params=params, read_only=False,
    )


def prepare_node_attempt_claim(
    attempt_row, lifecycle_event_row, *, lease_owner_id: str,
    lease_acquired_at: str, lease_expires_at: str, expected_lock_version: int,
    expected_run_status: str, expected_run_lock_version: int,
):
    lease_owner = _clean_text(lease_owner_id)
    acquired, expires = (
        _clean_text(lease_acquired_at), _clean_text(lease_expires_at)
    )
    if not lease_owner or not acquired or not expires:
        raise ValueError("attempt_lease_fields_required")
    command = _attempt_transition_command(
        "prepare_node_attempt_claim", attempt_row, lifecycle_event_row,
        expected_status="pending", next_status="claimed",
        expected_lock_version=expected_lock_version,
        expected_run_status=expected_run_status,
        expected_run_lock_version=expected_run_lock_version,
        extra_set=", lease_owner_id = %(lease_owner_id)s, "
                  "lease_acquired_at = %(lease_acquired_at)s, "
                  "lease_expires_at = %(lease_expires_at)s, "
                  "started_at = %(lease_acquired_at)s",
    )
    command["sql"] = command["sql"].replace(
        "attempt_status = %(expected_status)s",
        "(attempt_status = %(expected_status)s OR "
        "(attempt_status = 'claimed' "
        "AND lease_expires_at < %(lease_acquired_at)s))",
    )
    command["params"].update({
        "lease_owner_id": lease_owner,
        "lease_acquired_at": acquired,
        "lease_expires_at": expires,
    })
    return command


def prepare_node_attempt_success(
    attempt_row, lifecycle_event_row, *, output_checkpoint_id: str,
    output_digest: str, completed_at: str, duration_ms: int,
    lease_owner_id: str, expected_lock_version: int,
    expected_run_status: str, expected_run_lock_version: int,
):
    output_checkpoint = _clean_text(output_checkpoint_id)
    completed = _clean_text(completed_at)
    lease_owner = _clean_text(lease_owner_id)
    if not output_checkpoint or not completed or not lease_owner:
        raise ValueError("attempt_success_fields_required")
    command = _attempt_transition_command(
        "prepare_node_attempt_success", attempt_row, lifecycle_event_row,
        expected_status="claimed", next_status="succeeded",
        expected_lock_version=expected_lock_version,
        expected_run_status=expected_run_status,
        expected_run_lock_version=expected_run_lock_version,
        extra_set=", output_checkpoint_id = %(output_checkpoint_id)s, "
                  "output_digest = %(output_digest)s, "
                  "completed_at = %(completed_at)s, duration_ms = %(duration_ms)s",
    )
    command["params"].update({
        "output_checkpoint_id": output_checkpoint,
        "output_digest": _require_digest(output_digest, "output_digest"),
        "completed_at": completed,
        "duration_ms": _require_nonnegative_int(duration_ms, "duration_ms"),
        "lease_owner_id": lease_owner,
    })
    command["sql"] = command["sql"].replace(
        "AND attempt_status = %(expected_status)s",
        "AND attempt_status = %(expected_status)s "
        "AND lease_owner_id = %(lease_owner_id)s",
    )
    command["sql"] = command["sql"].replace(
        "), inserted_event AS (",
        """), advanced_run AS (
 UPDATE orchestration_graph_runs
 SET current_checkpoint_id = %(output_checkpoint_id)s,
     lock_version = lock_version + 1,
     updated_at = %(completed_at)s
 WHERE graph_invocation_id = %(attempt_graph_invocation_id)s
   AND owner_user_id = %(attempt_owner_user_id)s
   AND run_status = %(expected_run_status)s
   AND lock_version = %(expected_run_lock_version)s
   AND EXISTS (SELECT 1 FROM updated_attempt)
 RETURNING *
), inserted_event AS (""",
    )
    command["sql"] = command["sql"].replace(
        "FROM updated_attempt ON CONFLICT",
        "FROM updated_attempt JOIN advanced_run ON TRUE "
        "ON CONFLICT",
    )
    return command


def prepare_node_attempt_failure(
    attempt_row, lifecycle_event_row, *, error_code: str, error_detail: str,
    completed_at: str, lease_owner_id: str, expected_lock_version: int,
    expected_run_status: str, expected_run_lock_version: int,
):
    code, detail = _clean_text(error_code), _clean_text(error_detail)
    completed, lease_owner = (
        _clean_text(completed_at), _clean_text(lease_owner_id)
    )
    if not code or not completed or not lease_owner:
        raise ValueError("attempt_failure_fields_required")
    if len(code.encode()) > 256 or len(detail.encode()) > 4096:
        raise ValueError("attempt_error_too_large")
    command = _attempt_transition_command(
        "prepare_node_attempt_failure", attempt_row, lifecycle_event_row,
        expected_status="claimed", next_status="failed",
        expected_lock_version=expected_lock_version,
        expected_run_status=expected_run_status,
        expected_run_lock_version=expected_run_lock_version,
        extra_set=", error_code = %(error_code)s, error_detail = %(error_detail)s, "
                  "completed_at = %(completed_at)s",
    )
    command["params"].update({
        "error_code": code, "error_detail": detail,
        "completed_at": completed,
        "lease_owner_id": lease_owner,
    })
    command["sql"] = command["sql"].replace(
        "AND attempt_status = %(expected_status)s",
        "AND attempt_status = %(expected_status)s "
        "AND lease_owner_id = %(lease_owner_id)s",
    )
    return command


def prepare_expired_attempt_abandonment(
    attempt_row, lifecycle_event_row, *, recovery_at: str,
    expected_lock_version: int, expected_run_status: str,
    expected_run_lock_version: int,
):
    recovered_at = _clean_text(recovery_at)
    if not recovered_at:
        raise ValueError("recovery_at_required")
    command = _attempt_transition_command(
        "prepare_expired_attempt_abandonment", attempt_row,
        lifecycle_event_row, expected_status="claimed",
        next_status="abandoned", expected_lock_version=expected_lock_version,
        expected_run_status=expected_run_status,
        expected_run_lock_version=expected_run_lock_version,
    )
    command["params"]["recovery_at"] = recovered_at
    command["sql"] = command["sql"].replace(
        "AND lock_version = %(expected_lock_version)s",
        "AND lock_version = %(expected_lock_version)s "
        "AND lease_expires_at < %(recovery_at)s",
    )
    return command


def prepare_recovery_claim_inputs(
    consumption_row: Mapping[str, Any],
    graph_run_row: Mapping[str, Any],
    node_attempt_row: Mapping[str, Any],
) -> dict[str, Any]:
    _require_exact_fields(
        consumption_row, _CONSUMPTION_COLUMNS, "consumption_row"
    )
    _graph_run_params(graph_run_row)
    _require_exact_fields(
        node_attempt_row, _NODE_ATTEMPT_COLUMNS, "node_attempt"
    )
    if consumption_row["claim_status"] != "claimed":
        raise ValueError("resume_consumption_not_claimed")
    if graph_run_row["run_status"] != "resume_consumed":
        raise ValueError("graph_run_not_recoverable")
    shared = (
        "graph_invocation_id", *_IDENTITY_COLUMNS,
    )
    if any(
        consumption_row[key] != graph_run_row[key]
        or node_attempt_row[key] != graph_run_row[key]
        for key in shared
    ):
        raise ValueError("recovery_identity_mismatch")
    if (
        consumption_row["checkpoint_id"]
        != graph_run_row["current_checkpoint_id"]
        or node_attempt_row["input_checkpoint_id"]
        != consumption_row["checkpoint_id"]
        or node_attempt_row["resume_invocation_id"]
        != consumption_row["resume_invocation_id"]
    ):
        raise ValueError("recovery_resume_identity_mismatch")
    if node_attempt_row["attempt_status"] != "pending":
        raise ValueError("recovery_attempt_not_pending")
    return {
        "consumption": deepcopy(dict(consumption_row)),
        "graph_run": deepcopy(dict(graph_run_row)),
        "node_attempt": deepcopy(dict(node_attempt_row)),
    }


def prepare_resume_recovery_claim(
    consumption_row: Mapping[str, Any],
    graph_run_row: Mapping[str, Any],
    node_attempt_row: Mapping[str, Any],
    lifecycle_event_row: Mapping[str, Any],
    *,
    expected_run_lock_version: int,
):
    rows = prepare_recovery_claim_inputs(
        consumption_row, graph_run_row, node_attempt_row
    )
    _require_exact_fields(
        lifecycle_event_row, _LIFECYCLE_EVENT_COLUMNS, "lifecycle_event"
    )
    if lifecycle_event_row["event_type"] != "recovery_claim_recorded":
        raise ValueError("recovery_lifecycle_event_required")
    if (
        lifecycle_event_row["graph_invocation_id"]
        != graph_run_row["graph_invocation_id"]
        or lifecycle_event_row["owner_user_id"]
        != graph_run_row["owner_user_id"]
        or lifecycle_event_row["consumption_id"]
        != consumption_row["consumption_id"]
        or lifecycle_event_row["node_attempt_id"]
        != node_attempt_row["node_attempt_id"]
    ):
        raise ValueError("recovery_lifecycle_identity_mismatch")
    params = {
        **_prefixed_params("consumption", rows["consumption"]),
        **_prefixed_params("run", rows["graph_run"]),
        **_prefixed_params("attempt", rows["node_attempt"]),
        **_prefixed_params("event", lifecycle_event_row),
        "expected_run_lock_version": _require_nonnegative_int(
            expected_run_lock_version, "expected_run_lock_version"
        ),
    }
    sql = """
WITH locked_run AS (
 SELECT * FROM orchestration_graph_runs
 WHERE graph_invocation_id = %(run_graph_invocation_id)s
   AND owner_user_id = %(run_owner_user_id)s
   AND current_checkpoint_id = %(consumption_checkpoint_id)s
   AND run_status = 'resume_consumed'
   AND lock_version = %(expected_run_lock_version)s
 FOR UPDATE
), locked_consumption AS (
 SELECT * FROM orchestration_resume_consumptions
 WHERE consumption_id = %(consumption_consumption_id)s
   AND authorization_id = %(consumption_authorization_id)s
   AND decision_id = %(consumption_decision_id)s
   AND interrupt_request_id = %(consumption_interrupt_request_id)s
   AND graph_invocation_id = %(consumption_graph_invocation_id)s
   AND checkpoint_id = %(consumption_checkpoint_id)s
   AND owner_user_id = %(consumption_owner_user_id)s
   AND resume_invocation_id = %(consumption_resume_invocation_id)s
   AND claim_status = 'claimed'
), inserted_attempt AS (
 INSERT INTO orchestration_node_attempts
 SELECT %(attempt_node_attempt_id)s, %(attempt_graph_invocation_id)s,
        %(attempt_input_checkpoint_id)s, %(attempt_output_checkpoint_id)s,
        %(attempt_owner_user_id)s, %(attempt_pipeline_run_id)s,
        %(attempt_context_id)s, %(attempt_job_id)s, %(attempt_job_index)s,
        %(attempt_selected_resume_id)s, %(attempt_node_key)s,
        %(attempt_attempt_number)s, %(attempt_resume_invocation_id)s,
        %(attempt_attempt_status)s, %(attempt_lease_owner_id)s,
        %(attempt_lease_acquired_at)s, %(attempt_lease_expires_at)s,
        %(attempt_started_at)s, %(attempt_completed_at)s,
        %(attempt_duration_ms)s, %(attempt_input_digest)s,
        %(attempt_output_digest)s, %(attempt_error_code)s,
        %(attempt_error_detail)s, %(attempt_lock_version)s,
        %(attempt_application_authorization)s,
        %(attempt_mutation_authorization)s, %(attempt_created_at)s,
        %(attempt_updated_at)s
 FROM locked_run JOIN locked_consumption ON TRUE
 ON CONFLICT (graph_invocation_id, input_checkpoint_id, node_key, attempt_number)
 DO NOTHING RETURNING *
), accepted_attempt AS (
 SELECT * FROM inserted_attempt
 UNION ALL
 SELECT existing.* FROM orchestration_node_attempts AS existing
 WHERE existing.node_attempt_id = %(attempt_node_attempt_id)s
   AND existing.resume_invocation_id = %(consumption_resume_invocation_id)s
   AND existing.input_digest = %(attempt_input_digest)s
   AND existing.attempt_status = 'pending'
   AND NOT EXISTS (SELECT 1 FROM inserted_attempt)
), advanced_run AS (
 UPDATE orchestration_graph_runs
 SET run_status = 'resumed', lock_version = lock_version + 1,
     updated_at = %(event_event_timestamp)s
 WHERE graph_invocation_id = %(run_graph_invocation_id)s
   AND run_status = 'resume_consumed'
   AND lock_version = %(expected_run_lock_version)s
   AND EXISTS (SELECT 1 FROM accepted_attempt)
 RETURNING *
), inserted_event AS (
 INSERT INTO orchestration_lifecycle_events
 SELECT %(event_event_id)s, %(event_graph_invocation_id)s,
        %(event_checkpoint_id)s, %(event_interrupt_request_id)s,
        %(event_decision_id)s, %(event_authorization_id)s,
        %(event_consumption_id)s, %(event_node_attempt_id)s,
        %(event_terminal_result_id)s, %(event_owner_user_id)s,
        %(event_event_type)s, %(event_aggregate_type)s,
        %(event_aggregate_id)s, %(event_event_sequence)s,
        %(event_event_payload_json)s::jsonb, %(event_event_timestamp)s,
        %(event_projection_status)s, %(event_projected_at)s,
        %(event_projection_retry_count)s
 FROM advanced_run
 ON CONFLICT (event_id) DO NOTHING RETURNING *
)
SELECT * FROM accepted_attempt
"""
    return _command(
        operation="prepare_resume_recovery_claim",
        tables=(
            "orchestration_graph_runs",
            "orchestration_resume_consumptions",
            "orchestration_node_attempts",
            "orchestration_lifecycle_events",
        ),
        sql=sql,
        params=params,
        read_only=False,
    )


def prepare_terminalization(
    graph_run_row: Mapping[str, Any],
    terminal_result_row: Mapping[str, Any],
    lifecycle_event_row: Mapping[str, Any],
    *,
    expected_run_status: str,
    expected_run_lock_version: int,
):
    _graph_run_params(graph_run_row)
    _require_exact_fields(
        terminal_result_row, _TERMINAL_RESULT_COLUMNS, "terminal_result"
    )
    _require_exact_fields(
        lifecycle_event_row, _LIFECYCLE_EVENT_COLUMNS, "lifecycle_event"
    )
    expected = _clean_text(expected_run_status)
    if expected not in (
        "awaiting_decision", "decision_recorded", "resume_authorized",
        "resume_consumed", "decision_rejected", "resumed",
    ):
        raise ValueError("terminalization_expected_status_invalid")
    if (
        terminal_result_row["terminal_status"] not in TERMINAL_STATUS_VALUES
        or terminal_result_row["graph_invocation_id"]
        != graph_run_row["graph_invocation_id"]
        or terminal_result_row["owner_user_id"]
        != graph_run_row["owner_user_id"]
        or terminal_result_row["terminal_checkpoint_id"]
        != graph_run_row["current_checkpoint_id"]
    ):
        raise ValueError("terminal_result_identity_mismatch")
    if (
        lifecycle_event_row["event_type"] != "terminal_result_recorded"
        or lifecycle_event_row["terminal_result_id"]
        != terminal_result_row["terminal_result_id"]
        or lifecycle_event_row["owner_user_id"]
        != graph_run_row["owner_user_id"]
    ):
        raise ValueError("terminal_lifecycle_identity_mismatch")
    params = {
        **_prefixed_params("run", graph_run_row),
        **_prefixed_params("terminal", terminal_result_row),
        **_prefixed_params("event", lifecycle_event_row),
        "expected_run_status": expected,
        "expected_run_lock_version": _require_nonnegative_int(
            expected_run_lock_version, "expected_run_lock_version"
        ),
    }
    sql = """
WITH locked_run AS (
 SELECT * FROM orchestration_graph_runs
 WHERE graph_invocation_id = %(run_graph_invocation_id)s
   AND owner_user_id = %(run_owner_user_id)s
   AND current_checkpoint_id = %(terminal_terminal_checkpoint_id)s
   AND run_status = %(expected_run_status)s
   AND run_status NOT IN ('completed', 'failed', 'cancelled')
   AND lock_version = %(expected_run_lock_version)s
 FOR UPDATE
), inserted_terminal AS (
 INSERT INTO orchestration_terminal_results
 SELECT %(terminal_terminal_result_id)s,
        %(terminal_graph_invocation_id)s,
        %(terminal_terminal_checkpoint_id)s,
        %(terminal_owner_user_id)s, %(terminal_pipeline_run_id)s,
        %(terminal_context_id)s, %(terminal_job_id)s,
        %(terminal_job_index)s, %(terminal_selected_resume_id)s,
        %(terminal_graph_state_schema_version)s,
        %(terminal_checkpoint_schema_version)s,
        %(terminal_terminal_status)s, %(terminal_result_digest)s,
        %(terminal_result_metadata_json)s::jsonb,
        %(terminal_final_node_order_json)s::jsonb,
        %(terminal_failure_code)s,
        %(terminal_application_authorization)s,
        %(terminal_completed_at)s
 FROM locked_run
 ON CONFLICT (graph_invocation_id) DO NOTHING RETURNING *
), accepted_terminal AS (
 SELECT * FROM inserted_terminal
 UNION ALL
 SELECT existing.* FROM orchestration_terminal_results AS existing
 WHERE existing.graph_invocation_id = %(terminal_graph_invocation_id)s
   AND existing.terminal_result_id = %(terminal_terminal_result_id)s
   AND existing.terminal_checkpoint_id = %(terminal_terminal_checkpoint_id)s
   AND existing.terminal_status = %(terminal_terminal_status)s
   AND existing.result_digest = %(terminal_result_digest)s
   AND existing.result_metadata_json = %(terminal_result_metadata_json)s::jsonb
   AND NOT EXISTS (SELECT 1 FROM inserted_terminal)
), terminalized_run AS (
 UPDATE orchestration_graph_runs
 SET run_status = %(terminal_terminal_status)s,
     current_checkpoint_id = %(terminal_terminal_checkpoint_id)s,
     terminal_at = %(terminal_completed_at)s,
     updated_at = %(terminal_completed_at)s,
     lock_version = lock_version + 1
 WHERE graph_invocation_id = %(run_graph_invocation_id)s
   AND run_status = %(expected_run_status)s
   AND lock_version = %(expected_run_lock_version)s
   AND EXISTS (SELECT 1 FROM accepted_terminal)
 RETURNING *
), inserted_event AS (
 INSERT INTO orchestration_lifecycle_events
 SELECT %(event_event_id)s, %(event_graph_invocation_id)s,
        %(event_checkpoint_id)s, %(event_interrupt_request_id)s,
        %(event_decision_id)s, %(event_authorization_id)s,
        %(event_consumption_id)s, %(event_node_attempt_id)s,
        %(event_terminal_result_id)s, %(event_owner_user_id)s,
        %(event_event_type)s, %(event_aggregate_type)s,
        %(event_aggregate_id)s, %(event_event_sequence)s,
        %(event_event_payload_json)s::jsonb, %(event_event_timestamp)s,
        %(event_projection_status)s, %(event_projected_at)s,
        %(event_projection_retry_count)s
 FROM terminalized_run
 ON CONFLICT (event_id) DO NOTHING RETURNING *
)
SELECT * FROM accepted_terminal
"""
    return _command(
        operation="prepare_terminalization",
        tables=(
            "orchestration_graph_runs", "orchestration_terminal_results",
            "orchestration_lifecycle_events",
        ),
        sql=sql,
        params=params,
        read_only=False,
    )


def _graph_owner_read(
    operation: str,
    table: str,
    graph_invocation_id: str,
    owner_user_id: str,
    suffix: str = "",
    extra_params: Mapping[str, Any] | None = None,
):
    graph_id, owner = (
        _clean_text(graph_invocation_id), _clean_text(owner_user_id)
    )
    if not graph_id or not owner:
        raise ValueError("owner_and_graph_identity_required")
    return _command(
        operation=operation,
        tables=(table,),
        sql=f"SELECT * FROM {table} "
            "WHERE owner_user_id = %(owner_user_id)s "
            "AND graph_invocation_id = %(graph_invocation_id)s "
            f"{suffix}".strip(),
        params={
            "owner_user_id": owner,
            "graph_invocation_id": graph_id,
            **deepcopy(dict(extra_params or {})),
        },
        read_only=True,
    )


def prepare_active_node_attempt_read(*, owner_user_id: str, graph_invocation_id: str):
    return _graph_owner_read(
        "prepare_active_node_attempt_read", "orchestration_node_attempts",
        graph_invocation_id, owner_user_id,
        "AND attempt_status = 'claimed' ORDER BY updated_at DESC LIMIT 1",
    )


def prepare_latest_successful_attempt_read(
    *, owner_user_id: str, graph_invocation_id: str,
    input_checkpoint_id: str, node_key: str,
):
    checkpoint, node = (
        _clean_text(input_checkpoint_id), _clean_text(node_key)
    )
    if not checkpoint or node not in (*harness.ORDERED_AGENT_KEYS, "finalize"):
        raise ValueError("attempt_read_identity_invalid")
    return _graph_owner_read(
        "prepare_latest_successful_attempt_read",
        "orchestration_node_attempts", graph_invocation_id, owner_user_id,
        "AND input_checkpoint_id = %(input_checkpoint_id)s "
        "AND node_key = %(node_key)s AND attempt_status = 'succeeded' "
        "ORDER BY attempt_number DESC LIMIT 1",
        {"input_checkpoint_id": checkpoint, "node_key": node},
    )


def prepare_recoverable_expired_attempt_read(
    *, owner_user_id: str, graph_invocation_id: str, recovery_at: str,
):
    recovered_at = _clean_text(recovery_at)
    if not recovered_at:
        raise ValueError("recovery_at_required")
    return _graph_owner_read(
        "prepare_recoverable_expired_attempt_read",
        "orchestration_node_attempts", graph_invocation_id, owner_user_id,
        "AND attempt_status = 'claimed' "
        "AND lease_expires_at < %(recovery_at)s "
        "ORDER BY lease_expires_at LIMIT 1",
        {"recovery_at": recovered_at},
    )


def prepare_terminal_result_read(*, owner_user_id: str, graph_invocation_id: str):
    return _graph_owner_read(
        "prepare_terminal_result_read", "orchestration_terminal_results",
        graph_invocation_id, owner_user_id, "LIMIT 1",
    )


def prepare_unprojected_lifecycle_events_read(
    *, owner_user_id: str, graph_invocation_id: str,
):
    return _graph_owner_read(
        "prepare_unprojected_lifecycle_events_read",
        "orchestration_lifecycle_events", graph_invocation_id, owner_user_id,
        "AND projection_status IN ('pending', 'failed') "
        "ORDER BY event_sequence",
    )


def prepare_restart_reconciliation_read(
    *, owner_user_id: str, graph_invocation_id: str,
):
    return _graph_owner_read(
        "prepare_restart_reconciliation_read", "orchestration_graph_runs",
        graph_invocation_id, owner_user_id,
        "AND run_status IN ('resume_consumed', 'resumed') LIMIT 1",
    )
