"""Pure SQL preparation helpers for agent state storage.

This module opens no database connections, commits no transactions, runs no
migrations, and executes no SQL. Callers receive deterministic SQL/params
payloads and must choose an explicit execution boundary in a separately
approved integration phase.
"""

from __future__ import annotations

from copy import deepcopy
import json
from typing import Any


SAFETY_FLAGS: dict[str, bool] = {
    "did_create_connection": False,
    "did_commit_transaction": False,
    "did_run_migration": False,
    "did_schedule_background_work": False,
    "did_execute_scheduler": False,
    "did_execute_reporting_job": False,
    "did_export_files": False,
    "did_execute_application": False,
    "did_submit_application": False,
    "migration_runner_added": False,
}

AGENT_STATE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS agent_runs (
    agent_run_id TEXT PRIMARY KEY,
    agent_run_key TEXT NOT NULL,
    context_key TEXT NOT NULL,
    approval_request_id TEXT NOT NULL DEFAULT '',
    job_id TEXT NOT NULL DEFAULT '',
    candidate_key TEXT NOT NULL DEFAULT '',
    agent_name TEXT NOT NULL,
    run_status TEXT NOT NULL,
    observed_at_utc TIMESTAMPTZ NOT NULL,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    safety_flags_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_agent_runs_agent_run_key UNIQUE (agent_run_key)
);

CREATE INDEX IF NOT EXISTS idx_agent_runs_context_observed
ON agent_runs (context_key, observed_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_agent_runs_approval_observed
ON agent_runs (approval_request_id, observed_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_agent_runs_job_observed
ON agent_runs (job_id, observed_at_utc DESC);

CREATE TABLE IF NOT EXISTS agent_steps (
    agent_step_id TEXT PRIMARY KEY,
    agent_step_key TEXT NOT NULL,
    agent_run_id TEXT NOT NULL,
    context_key TEXT NOT NULL,
    approval_request_id TEXT NOT NULL DEFAULT '',
    job_id TEXT NOT NULL DEFAULT '',
    candidate_key TEXT NOT NULL DEFAULT '',
    agent_name TEXT NOT NULL,
    step_name TEXT NOT NULL,
    step_index INTEGER NOT NULL,
    step_status TEXT NOT NULL,
    observed_at_utc TIMESTAMPTZ NOT NULL,
    input_summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_summary_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    reason_codes_json JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    safety_flags_json JSONB NOT NULL DEFAULT '{}'::jsonb,
    CONSTRAINT uq_agent_steps_agent_step_key UNIQUE (agent_step_key),
    CONSTRAINT fk_agent_steps_agent_run
        FOREIGN KEY (agent_run_id)
        REFERENCES agent_runs (agent_run_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_agent_steps_run_observed
ON agent_steps (agent_run_id, observed_at_utc);

CREATE INDEX IF NOT EXISTS idx_agent_steps_context_observed
ON agent_steps (context_key, observed_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_agent_steps_approval_observed
ON agent_steps (approval_request_id, observed_at_utc DESC);

CREATE INDEX IF NOT EXISTS idx_agent_steps_job_observed
ON agent_steps (job_id, observed_at_utc DESC);
""".strip()

_RUN_COLUMNS = (
    "agent_run_id",
    "agent_run_key",
    "context_key",
    "approval_request_id",
    "job_id",
    "candidate_key",
    "agent_name",
    "run_status",
    "observed_at_utc",
    "metadata_json",
    "safety_flags_json",
)

_STEP_COLUMNS = (
    "agent_step_id",
    "agent_step_key",
    "agent_run_id",
    "context_key",
    "approval_request_id",
    "job_id",
    "candidate_key",
    "agent_name",
    "step_name",
    "step_index",
    "step_status",
    "observed_at_utc",
    "input_summary_json",
    "output_summary_json",
    "reason_codes_json",
    "metadata_json",
    "safety_flags_json",
)


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


def agent_state_schema_sql_text() -> str:
    return AGENT_STATE_SCHEMA_SQL


def agent_state_table_specs() -> dict[str, dict[str, Any]]:
    return {
        "agent_runs": {
            "primary_key": ["agent_run_id"],
            "unique": ["agent_run_key"],
            "columns": list(_RUN_COLUMNS),
        },
        "agent_steps": {
            "primary_key": ["agent_step_id"],
            "unique": ["agent_step_key"],
            "foreign_keys": {"agent_run_id": "agent_runs.agent_run_id"},
            "columns": list(_STEP_COLUMNS),
        },
    }


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _snapshot(value: dict[str, Any]) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _json_compact(value: Any) -> str:
    return json.dumps(
        value if value is not None else {},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _require_text(snapshot: dict[str, Any], key: str) -> str:
    value = _clean_text(snapshot.get(key))
    if not value:
        raise ValueError(f"{key} is required.")
    return value


def _returning_columns(columns: tuple[str, ...]) -> str:
    return ", ".join(columns)


def prepare_agent_run_upsert(run_snapshot: dict[str, Any]) -> dict[str, Any]:
    snapshot = _snapshot(run_snapshot)
    sql = f"""
INSERT INTO agent_runs (
    agent_run_id,
    agent_run_key,
    context_key,
    approval_request_id,
    job_id,
    candidate_key,
    agent_name,
    run_status,
    observed_at_utc,
    metadata_json,
    safety_flags_json
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
ON CONFLICT (agent_run_key) DO UPDATE SET
    run_status = EXCLUDED.run_status,
    metadata_json = EXCLUDED.metadata_json,
    safety_flags_json = EXCLUDED.safety_flags_json
RETURNING {_returning_columns(_RUN_COLUMNS)}
""".strip()
    params = (
        _require_text(snapshot, "agent_run_id"),
        _require_text(snapshot, "agent_run_key"),
        _require_text(snapshot, "context_key"),
        _clean_text(snapshot.get("approval_request_id")),
        _clean_text(snapshot.get("job_id")),
        _clean_text(snapshot.get("candidate_key")),
        _require_text(snapshot, "agent_name"),
        _require_text(snapshot, "run_status"),
        _require_text(snapshot, "observed_at_utc"),
        _json_compact(snapshot.get("metadata")),
        _json_compact(safety_flags()),
    )
    return {
        "operation": "prepare_agent_run_upsert",
        "table": "agent_runs",
        "sql": sql,
        "params": params,
        "snapshot": snapshot,
        **safety_flags(),
    }


def prepare_agent_step_upsert(step_snapshot: dict[str, Any]) -> dict[str, Any]:
    snapshot = _snapshot(step_snapshot)
    sql = f"""
INSERT INTO agent_steps (
    agent_step_id,
    agent_step_key,
    agent_run_id,
    context_key,
    approval_request_id,
    job_id,
    candidate_key,
    agent_name,
    step_name,
    step_index,
    step_status,
    observed_at_utc,
    input_summary_json,
    output_summary_json,
    reason_codes_json,
    metadata_json,
    safety_flags_json
)
VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb, %s::jsonb)
ON CONFLICT (agent_step_key) DO UPDATE SET
    step_status = EXCLUDED.step_status,
    output_summary_json = EXCLUDED.output_summary_json,
    reason_codes_json = EXCLUDED.reason_codes_json,
    metadata_json = EXCLUDED.metadata_json,
    safety_flags_json = EXCLUDED.safety_flags_json
RETURNING {_returning_columns(_STEP_COLUMNS)}
""".strip()
    params = (
        _require_text(snapshot, "agent_step_id"),
        _require_text(snapshot, "agent_step_key"),
        _require_text(snapshot, "agent_run_id"),
        _require_text(snapshot, "context_key"),
        _clean_text(snapshot.get("approval_request_id")),
        _clean_text(snapshot.get("job_id")),
        _clean_text(snapshot.get("candidate_key")),
        _require_text(snapshot, "agent_name"),
        _require_text(snapshot, "step_name"),
        int(snapshot.get("step_index", 0)),
        _require_text(snapshot, "step_status"),
        _require_text(snapshot, "observed_at_utc"),
        _json_compact(snapshot.get("input_summary")),
        _json_compact(snapshot.get("output_summary")),
        _json_compact(snapshot.get("reason_codes") or []),
        _json_compact(snapshot.get("metadata")),
        _json_compact(safety_flags()),
    )
    return {
        "operation": "prepare_agent_step_upsert",
        "table": "agent_steps",
        "sql": sql,
        "params": params,
        "snapshot": snapshot,
        **safety_flags(),
    }


def prepare_agent_run_select(
    *,
    approval_request_id: str,
    agent_run_id: str = "",
) -> dict[str, Any]:
    """Prepare a read-only lookup for one agent run."""

    approval_id = _clean_text(approval_request_id)
    if not approval_id:
        raise ValueError("approval_request_id is required.")
    run_id = _clean_text(agent_run_id)
    where_clause = "approval_request_id = %s"
    params: tuple[Any, ...] = (approval_id,)
    if run_id:
        where_clause = f"{where_clause} AND agent_run_id = %s"
        params = (approval_id, run_id)
    sql = f"""
SELECT {_returning_columns(_RUN_COLUMNS)}
FROM agent_runs
WHERE {where_clause}
ORDER BY observed_at_utc DESC, agent_run_id ASC
LIMIT 1
""".strip()
    return {
        "operation": "prepare_agent_run_select",
        "table": "agent_runs",
        "read_only": True,
        "sql": sql,
        "params": params,
        **safety_flags(),
    }


def prepare_agent_steps_select_for_run(*, agent_run_id: str) -> dict[str, Any]:
    """Prepare a read-only ordered step lookup for one agent run."""

    run_id = _clean_text(agent_run_id)
    if not run_id:
        raise ValueError("agent_run_id is required.")
    sql = f"""
SELECT {_returning_columns(_STEP_COLUMNS)}
FROM agent_steps
WHERE agent_run_id = %s
ORDER BY step_index ASC, observed_at_utc ASC, agent_step_id ASC
""".strip()
    return {
        "operation": "prepare_agent_steps_select_for_run",
        "table": "agent_steps",
        "read_only": True,
        "sql": sql,
        "params": (run_id,),
        **safety_flags(),
    }
