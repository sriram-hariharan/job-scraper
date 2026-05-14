from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

DEFAULT_USER_PIPELINE_SCHEMA_SQL_PATH = Path("src/storage/user_pipeline/schema.sql")


def _read_sql_artifact(path: Path, label: str) -> str:
    resolved = Path(path)
    if not resolved.exists():
        raise ValueError(f"Missing {label} SQL file: {resolved}")

    sql = resolved.read_text(encoding="utf-8")
    if not sql.strip():
        raise ValueError(f"{label.capitalize()} SQL file is empty: {resolved}")

    return sql


def user_pipeline_table_specs() -> Dict[str, Any]:
    return {
        "user_pipeline_runs": {
            "description": "Owner-scoped live pipeline run state and durable status snapshots.",
            "primary_key": ["run_id"],
            "owner_column": "owner_user_id",
            "columns": [
                {"name": "run_id", "type": "text", "nullable": False},
                {"name": "owner_user_id", "type": "text", "nullable": False},
                {"name": "status", "type": "text", "nullable": False},
                {"name": "current_stage", "type": "text", "nullable": False},
                {"name": "stage_message", "type": "text", "nullable": False},
                {"name": "summary_message", "type": "text", "nullable": False},
                {"name": "return_code", "type": "integer", "nullable": True},
                {"name": "started_at", "type": "timestamptz", "nullable": False},
                {"name": "updated_at", "type": "timestamptz", "nullable": False},
                {"name": "completed_at", "type": "timestamptz", "nullable": True},
                {"name": "config_json", "type": "jsonb", "nullable": False},
                {"name": "status_json", "type": "jsonb", "nullable": False},
                {"name": "error", "type": "text", "nullable": False},
            ],
        },
        "user_seen_jobs": {
            "description": "Owner-scoped seen-job registry replacing shared seen_job_ids files.",
            "primary_key": ["owner_user_id", "seen_key"],
            "owner_column": "owner_user_id",
            "columns": [
                {"name": "owner_user_id", "type": "text", "nullable": False},
                {"name": "seen_key", "type": "text", "nullable": False},
                {"name": "source", "type": "text", "nullable": False},
                {"name": "job_url", "type": "text", "nullable": False},
                {"name": "job_doc_id", "type": "text", "nullable": False},
                {"name": "company", "type": "text", "nullable": False},
                {"name": "title", "type": "text", "nullable": False},
                {"name": "first_seen_at", "type": "timestamptz", "nullable": False},
                {"name": "last_seen_at", "type": "timestamptz", "nullable": False},
                {"name": "first_run_id", "type": "text", "nullable": False},
                {"name": "last_run_id", "type": "text", "nullable": False},
                {"name": "metadata_json", "type": "jsonb", "nullable": False},
            ],
        },
        "user_pipeline_artifacts": {
            "description": "Owner-scoped generated pipeline artifacts stored durably in Postgres.",
            "primary_key": ["artifact_id"],
            "owner_column": "owner_user_id",
            "columns": [
                {"name": "artifact_id", "type": "text", "nullable": False},
                {"name": "owner_user_id", "type": "text", "nullable": False},
                {"name": "run_id", "type": "text", "nullable": False},
                {"name": "artifact_kind", "type": "text", "nullable": False},
                {"name": "artifact_name", "type": "text", "nullable": False},
                {"name": "content_type", "type": "text", "nullable": False},
                {"name": "content_json", "type": "jsonb", "nullable": True},
                {"name": "content_text", "type": "text", "nullable": False},
                {"name": "content_bytes", "type": "bytea", "nullable": True},
                {"name": "created_at", "type": "timestamptz", "nullable": False},
            ],
        },
    }


def render_user_pipeline_schema_sql() -> str:
    return "\n".join(
        [
            "CREATE TABLE IF NOT EXISTS user_pipeline_runs (",
            "    run_id TEXT PRIMARY KEY,",
            "    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,",
            "    status TEXT NOT NULL,",
            "    current_stage TEXT NOT NULL DEFAULT '',",
            "    stage_message TEXT NOT NULL DEFAULT '',",
            "    summary_message TEXT NOT NULL DEFAULT '',",
            "    return_code INTEGER,",
            "    started_at TIMESTAMPTZ NOT NULL,",
            "    updated_at TIMESTAMPTZ NOT NULL,",
            "    completed_at TIMESTAMPTZ,",
            "    config_json JSONB NOT NULL DEFAULT '{}'::jsonb,",
            "    status_json JSONB NOT NULL DEFAULT '{}'::jsonb,",
            "    error TEXT NOT NULL DEFAULT ''",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_pipeline_runs_owner_started",
            "ON user_pipeline_runs (owner_user_id, started_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_pipeline_runs_status_started",
            "ON user_pipeline_runs (status, started_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_pipeline_runs_owner_status_started",
            "ON user_pipeline_runs (owner_user_id, status, started_at DESC);",
            "",
            "CREATE TABLE IF NOT EXISTS user_seen_jobs (",
            "    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,",
            "    seen_key TEXT NOT NULL,",
            "    source TEXT NOT NULL DEFAULT '',",
            "    job_url TEXT NOT NULL DEFAULT '',",
            "    job_doc_id TEXT NOT NULL DEFAULT '',",
            "    company TEXT NOT NULL DEFAULT '',",
            "    title TEXT NOT NULL DEFAULT '',",
            "    first_seen_at TIMESTAMPTZ NOT NULL,",
            "    last_seen_at TIMESTAMPTZ NOT NULL,",
            "    first_run_id TEXT NOT NULL DEFAULT '',",
            "    last_run_id TEXT NOT NULL DEFAULT '',",
            "    metadata_json JSONB NOT NULL DEFAULT '{}'::jsonb,",
            "    PRIMARY KEY (owner_user_id, seen_key)",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_seen_jobs_owner_last_seen",
            "ON user_seen_jobs (owner_user_id, last_seen_at DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_seen_jobs_job_doc_id",
            "ON user_seen_jobs (job_doc_id);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_seen_jobs_job_url",
            "ON user_seen_jobs (job_url);",
            "",
            "CREATE TABLE IF NOT EXISTS user_pipeline_artifacts (",
            "    artifact_id TEXT PRIMARY KEY,",
            "    owner_user_id TEXT NOT NULL REFERENCES auth_users(user_id) ON DELETE CASCADE,",
            "    run_id TEXT NOT NULL REFERENCES user_pipeline_runs(run_id) ON DELETE CASCADE,",
            "    artifact_kind TEXT NOT NULL,",
            "    artifact_name TEXT NOT NULL,",
            "    content_type TEXT NOT NULL DEFAULT 'application/json',",
            "    content_json JSONB,",
            "    content_text TEXT NOT NULL DEFAULT '',",
            "    content_bytes BYTEA,",
            "    created_at TIMESTAMPTZ NOT NULL",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_pipeline_artifacts_owner_run",
            "ON user_pipeline_artifacts (owner_user_id, run_id, artifact_kind);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_pipeline_artifacts_run_kind",
            "ON user_pipeline_artifacts (run_id, artifact_kind);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_user_pipeline_artifacts_owner_created",
            "ON user_pipeline_artifacts (owner_user_id, created_at DESC);",
        ]
    )


def user_pipeline_schema_sql_text(
    schema_path: Path = DEFAULT_USER_PIPELINE_SCHEMA_SQL_PATH,
) -> str:
    return _read_sql_artifact(schema_path, "user pipeline schema")


def user_pipeline_schema_sql_payload(
    schema_path: Path = DEFAULT_USER_PIPELINE_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    sql = user_pipeline_schema_sql_text(schema_path)
    return {
        "path": str(Path(schema_path)),
        "sql": sql,
    }


def user_pipeline_schema_sql_generation_payload(
    schema_path: Path = DEFAULT_USER_PIPELINE_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    generated_sql = render_user_pipeline_schema_sql()
    artifact_sql = user_pipeline_schema_sql_text(schema_path)

    return {
        "artifact_path": str(Path(schema_path)),
        "artifact_sql": artifact_sql,
        "generated_sql": generated_sql,
        "matches_artifact": generated_sql.strip() == artifact_sql.strip(),
    }


def user_pipeline_contract_health_payload() -> Dict[str, Any]:
    schema_generation = user_pipeline_schema_sql_generation_payload()

    return {
        "ok": True,
        "artifacts": {
            "schema_sql_path": str(DEFAULT_USER_PIPELINE_SCHEMA_SQL_PATH),
        },
        "checks": {
            "schema_sql_matches_artifact": bool(schema_generation["matches_artifact"]),
        },
        "all_checks_pass": bool(schema_generation["matches_artifact"]),
        "table_specs": user_pipeline_table_specs(),
    }
