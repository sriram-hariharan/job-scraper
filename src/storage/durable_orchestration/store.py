"""Pure preparation helpers for the durable-orchestration SQL contract.

This module validates existing evidence-chain checkpoint and interrupt
payloads, prepares deterministic rows, and returns SQL plus parameters. It
does not own a database connection or transaction execution boundary.
"""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any, Mapping

from src.agents import evidence_chain_langgraph_harness as harness


GRAPH_RUN_STATUS_VALUES = ("running", "awaiting_decision")
INTERRUPT_STATUS_VALUES = ("pending",)
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
        "interrupt_status": "pending",
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
        "interrupt_status": "pending",
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
