"""Storage-only approval persistence helpers.

This module is intentionally not wired into runtime services in Step 123A.
Callers must inject an already configured DB-API compatible connection; this
module opens no database connections and executes no SQL at import time.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

APPROVAL_STATUS_VALUES = {
    "pending",
    "approved",
    "denied",
    "expired",
    "revoked",
    "consumed",
}

DECISION_STATUS_VALUES = {"approved", "denied", "revoked"}

_SENSITIVE_KEY_FRAGMENTS = (
    "api_key",
    "authorization",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
)

_REQUEST_COLUMNS = (
    "approval_request_id",
    "dry_run_artifact_id",
    "owner_id",
    "idempotency_key",
    "approval_status",
    "proposed_action_type",
    "proposed_action_summary",
    "safety_gate_snapshot_json",
    "fixture_validation_snapshot_json",
    "app_service_safety_gate_snapshot_json",
    "queue_safety_gate_snapshot_json",
    "reviewer_id",
    "review_decision",
    "review_reason",
    "created_at",
    "updated_at",
    "expires_at",
    "approved_at",
    "denied_at",
    "revoked_at",
)

_AUDIT_COLUMNS = (
    "audit_event_id",
    "approval_request_id",
    "event_type",
    "event_actor_id",
    "event_payload_json",
    "created_at",
)


def create_approval_request(
    connection: Any,
    *,
    approval_request_id: str,
    dry_run_artifact_id: str,
    owner_id: str,
    idempotency_key: str,
    expires_at: Any,
    proposed_action_type: str = "",
    proposed_action_summary: str = "",
    safety_gate_snapshot: Optional[Mapping[str, Any]] = None,
    fixture_validation_snapshot: Optional[Mapping[str, Any]] = None,
    app_service_safety_gate_snapshot: Optional[Mapping[str, Any]] = None,
    queue_safety_gate_snapshot: Optional[Mapping[str, Any]] = None,
    created_at: Any = None,
) -> Dict[str, Any]:
    """Create or return one pending approval request by idempotency key.

    The injected connection is the only execution boundary. The SQL preserves
    the schema's unique `idempotency_key` behavior and never runs unless this
    function is explicitly called by a future approved integration.
    """

    created_timestamp = created_at or _utc_now()
    _require_text(approval_request_id, "approval_request_id")
    _require_text(dry_run_artifact_id, "dry_run_artifact_id")
    _require_text(owner_id, "owner_id")
    _require_text(idempotency_key, "idempotency_key")
    _require_value(expires_at, "expires_at")

    snapshots = {
        "safety_gate_snapshot_json": _json_payload(safety_gate_snapshot),
        "fixture_validation_snapshot_json": _json_payload(fixture_validation_snapshot),
        "app_service_safety_gate_snapshot_json": _json_payload(app_service_safety_gate_snapshot),
        "queue_safety_gate_snapshot_json": _json_payload(queue_safety_gate_snapshot),
    }

    sql = f"""
WITH inserted AS (
    INSERT INTO agentic_approval_requests (
        approval_request_id,
        dry_run_artifact_id,
        owner_id,
        idempotency_key,
        approval_status,
        proposed_action_type,
        proposed_action_summary,
        safety_gate_snapshot_json,
        fixture_validation_snapshot_json,
        app_service_safety_gate_snapshot_json,
        queue_safety_gate_snapshot_json,
        created_at,
        updated_at,
        expires_at
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s, %s, %s)
    ON CONFLICT (idempotency_key) DO NOTHING
    RETURNING {_returning_columns(_REQUEST_COLUMNS)}
)
SELECT {_returning_columns(_REQUEST_COLUMNS)} FROM inserted
UNION ALL
SELECT {_returning_columns(_REQUEST_COLUMNS)}
FROM agentic_approval_requests
WHERE idempotency_key = %s
  AND NOT EXISTS (SELECT 1 FROM inserted)
LIMIT 1
""".strip()
    params = (
        _clean_text(approval_request_id),
        _clean_text(dry_run_artifact_id),
        _clean_text(owner_id),
        _clean_text(idempotency_key),
        "pending",
        _clean_text(proposed_action_type),
        _clean_text(proposed_action_summary),
        snapshots["safety_gate_snapshot_json"],
        snapshots["fixture_validation_snapshot_json"],
        snapshots["app_service_safety_gate_snapshot_json"],
        snapshots["queue_safety_gate_snapshot_json"],
        created_timestamp,
        created_timestamp,
        expires_at,
        _clean_text(idempotency_key),
    )
    return _execute_fetch_one(connection, sql, params, "create_approval_request")


def get_approval_request(
    connection: Any,
    *,
    approval_request_id: str = "",
    idempotency_key: str = "",
) -> Optional[Dict[str, Any]]:
    """Read one approval request by request id or idempotency key."""

    request_id = _clean_text(approval_request_id)
    idem_key = _clean_text(idempotency_key)
    if bool(request_id) == bool(idem_key):
        raise ValueError("Pass exactly one of approval_request_id or idempotency_key.")

    if request_id:
        where_clause = "approval_request_id = %s"
        param = request_id
    else:
        where_clause = "idempotency_key = %s"
        param = idem_key

    sql = f"""
SELECT {_returning_columns(_REQUEST_COLUMNS)}
FROM agentic_approval_requests
WHERE {where_clause}
LIMIT 1
""".strip()
    return _execute_fetch_optional(connection, sql, (param,), "get_approval_request")


def list_approval_requests(
    connection: Any,
    *,
    owner_id: str = "",
    approval_status: str = "",
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """List approval requests with deterministic ordering and optional filters."""

    if limit < 1 or limit > 500:
        raise ValueError("limit must be between 1 and 500.")

    clauses: List[str] = []
    params: List[Any] = []
    clean_owner_id = _clean_text(owner_id)
    clean_status = _clean_text(approval_status)

    if clean_owner_id:
        clauses.append("owner_id = %s")
        params.append(clean_owner_id)
    if clean_status:
        params.append(_normalize_approval_status(clean_status))
        clauses.append("approval_status = %s")

    where_sql = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = f"""
SELECT {_returning_columns(_REQUEST_COLUMNS)}
FROM agentic_approval_requests
{where_sql}
ORDER BY created_at DESC, approval_request_id ASC
LIMIT %s
""".strip()
    params.append(limit)
    return _execute_fetch_all(connection, sql, tuple(params), "list_approval_requests")


def record_approval_audit_event(
    connection: Any,
    *,
    audit_event_id: str,
    approval_request_id: str,
    event_type: str,
    event_actor_id: str = "",
    event_payload: Optional[Mapping[str, Any]] = None,
    created_at: Any = None,
) -> Dict[str, Any]:
    """Append an audit event linked to an existing approval request."""

    _require_text(audit_event_id, "audit_event_id")
    _require_text(approval_request_id, "approval_request_id")
    _require_text(event_type, "event_type")
    created_timestamp = created_at or _utc_now()

    sql = f"""
INSERT INTO agentic_approval_audit_events (
    audit_event_id,
    approval_request_id,
    event_type,
    event_actor_id,
    event_payload_json,
    created_at
)
VALUES (%s, %s, %s, %s, %s::jsonb, %s)
RETURNING {_returning_columns(_AUDIT_COLUMNS)}
""".strip()
    params = (
        _clean_text(audit_event_id),
        _clean_text(approval_request_id),
        _clean_text(event_type),
        _clean_text(event_actor_id),
        _json_payload(event_payload),
        created_timestamp,
    )
    return _execute_fetch_one(connection, sql, params, "record_approval_audit_event")


def record_approval_decision(
    connection: Any,
    *,
    approval_request_id: str,
    approval_status: str,
    reviewer_id: str,
    review_reason: str = "",
    audit_event_id: str = "",
    event_payload: Optional[Mapping[str, Any]] = None,
    decided_at: Any = None,
) -> Dict[str, Any]:
    """Record a storage-scoped approval decision without runtime side effects."""

    _require_text(approval_request_id, "approval_request_id")
    _require_text(reviewer_id, "reviewer_id")
    status = _normalize_decision_status(approval_status)
    decision_timestamp = decided_at or _utc_now()

    timestamp_column = {
        "approved": "approved_at",
        "denied": "denied_at",
        "revoked": "revoked_at",
    }[status]

    sql = f"""
UPDATE agentic_approval_requests
SET approval_status = %s,
    reviewer_id = %s,
    review_decision = %s,
    review_reason = %s,
    updated_at = %s,
    {timestamp_column} = %s
WHERE approval_request_id = %s
RETURNING {_returning_columns(_REQUEST_COLUMNS)}
""".strip()
    params = (
        status,
        _clean_text(reviewer_id),
        status,
        _clean_text(review_reason),
        decision_timestamp,
        decision_timestamp,
        _clean_text(approval_request_id),
    )
    request_row = _execute_fetch_one(connection, sql, params, "record_approval_decision")

    if _clean_text(audit_event_id):
        record_approval_audit_event(
            connection,
            audit_event_id=audit_event_id,
            approval_request_id=approval_request_id,
            event_type=f"approval_{status}",
            event_actor_id=reviewer_id,
            event_payload=event_payload or {"approval_status": status},
            created_at=decision_timestamp,
        )

    return request_row


def expire_approval_requests(
    connection: Any,
    *,
    now: Any = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """Mark expired pending approval requests without deleting records."""

    if limit < 1 or limit > 500:
        raise ValueError("limit must be between 1 and 500.")
    timestamp = now or _utc_now()

    sql = f"""
WITH candidates AS (
    SELECT approval_request_id
    FROM agentic_approval_requests
    WHERE approval_status = %s
      AND expires_at <= %s
    ORDER BY expires_at ASC, approval_request_id ASC
    LIMIT %s
)
UPDATE agentic_approval_requests AS requests
SET approval_status = %s,
    review_decision = %s,
    updated_at = %s,
    denied_at = COALESCE(denied_at, %s)
FROM candidates
WHERE requests.approval_request_id = candidates.approval_request_id
RETURNING {_returning_columns(tuple(f"requests.{column}" for column in _REQUEST_COLUMNS))}
""".strip()
    params = ("pending", timestamp, limit, "expired", "expired", timestamp, timestamp)
    return _execute_fetch_all(connection, sql, params, "expire_approval_requests")


def _execute_fetch_one(
    connection: Any,
    sql: str,
    params: Sequence[Any],
    operation_name: str,
) -> Dict[str, Any]:
    row = _execute_fetch_optional(connection, sql, params, operation_name)
    if row is None:
        raise LookupError(f"{operation_name} returned no row.")
    return row


def _execute_fetch_optional(
    connection: Any,
    sql: str,
    params: Sequence[Any],
    operation_name: str,
) -> Optional[Dict[str, Any]]:
    rows = _execute_fetch_all(connection, sql, params, operation_name)
    return rows[0] if rows else None


def _execute_fetch_all(
    connection: Any,
    sql: str,
    params: Sequence[Any],
    operation_name: str,
) -> List[Dict[str, Any]]:
    if connection is None:
        raise ValueError("connection is required.")

    cursor = connection.cursor()
    try:
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall() if hasattr(cursor, "fetchall") else []
        description = getattr(cursor, "description", None) or []
        return [_row_to_dict(row, description) for row in rows]
    except Exception as exc:
        raise ApprovalStorageError(
            operation_name=operation_name,
            reason_code=_classify_exception(exc),
        ) from exc
    finally:
        close = getattr(cursor, "close", None)
        if callable(close):
            close()


class ApprovalStorageError(RuntimeError):
    """Deterministic storage error wrapper with non-secret observability fields."""

    def __init__(self, *, operation_name: str, reason_code: str) -> None:
        self.operation_name = operation_name
        self.reason_code = reason_code
        super().__init__(f"{operation_name} failed: {reason_code}")


def _row_to_dict(row: Any, description: Iterable[Any]) -> Dict[str, Any]:
    if isinstance(row, Mapping):
        return dict(row)

    columns = []
    for item in description:
        if isinstance(item, str):
            columns.append(item)
        else:
            columns.append(str(item[0]))

    return {column: row[index] for index, column in enumerate(columns)}


def _returning_columns(columns: Tuple[str, ...]) -> str:
    return ", ".join(columns)


def _classify_exception(exc: Exception) -> str:
    message = str(exc).lower()
    if "duplicate" in message or "unique" in message:
        return "duplicate_idempotency_or_primary_key"
    if "foreign key" in message or "violates" in message:
        return "constraint_violation"
    if "serialization" in message or "deadlock" in message:
        return "retryable_transaction_failure"
    if "connection" in message or "timeout" in message:
        return "connection_failure"
    return "storage_operation_failed"


def _normalize_approval_status(value: str) -> str:
    normalized = _clean_text(value).lower()
    if normalized not in APPROVAL_STATUS_VALUES:
        allowed = ", ".join(sorted(APPROVAL_STATUS_VALUES))
        raise ValueError(f"Invalid approval_status={normalized!r}. Allowed values: {allowed}.")
    return normalized


def _normalize_decision_status(value: str) -> str:
    normalized = _normalize_approval_status(value)
    if normalized not in DECISION_STATUS_VALUES:
        allowed = ", ".join(sorted(DECISION_STATUS_VALUES))
        raise ValueError(f"Invalid decision approval_status={normalized!r}. Allowed values: {allowed}.")
    return normalized


def _json_payload(value: Optional[Mapping[str, Any]]) -> str:
    payload = dict(value or {})
    _reject_sensitive_payload(payload)
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _reject_sensitive_payload(value: Any, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            normalized_key = str(key).lower()
            if any(fragment in normalized_key for fragment in _SENSITIVE_KEY_FRAGMENTS):
                raise ValueError(f"{path} contains disallowed sensitive field: {key}")
            _reject_sensitive_payload(nested_value, f"{path}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_sensitive_payload(item, f"{path}[{index}]")


def _require_text(value: Any, field_name: str) -> None:
    if not _clean_text(value):
        raise ValueError(f"{field_name} is required.")


def _require_value(value: Any, field_name: str) -> None:
    if value is None or value == "":
        raise ValueError(f"{field_name} is required.")


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)
