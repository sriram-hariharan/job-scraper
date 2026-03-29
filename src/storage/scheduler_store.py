from __future__ import annotations

import json
from typing import Any, Dict, List
from pathlib import Path

from src.pipeline.scheduler import get_scheduled_job_definitions

DEFAULT_SCHEDULER_SCHEMA_SQL_PATH = Path("src/storage/scheduler_schema.sql")
DEFAULT_SCHEDULER_SEED_SQL_PATH = Path("src/storage/scheduler_seed.sql")

def _json_compact(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _clean_text(value: Any) -> str:
    return str(value or "").strip()

def _read_sql_artifact(path: Path, label: str) -> str:
    resolved = Path(path)

    if not resolved.exists():
        raise ValueError(f"Missing {label} SQL file: {resolved}")

    sql = resolved.read_text(encoding="utf-8")

    if not sql.strip():
        raise ValueError(f"{label.capitalize()} SQL file is empty: {resolved}")

    return sql

def _sql_quote_text(value: Any) -> str:
    text = str(value or "")
    return "'" + text.replace("'", "''") + "'"


def _sql_bool_literal(value: Any) -> str:
    if isinstance(value, bool):
        return "TRUE" if value else "FALSE"

    raw = str(value or "").strip().lower()
    if raw in {"true", "1", "yes", "y"}:
        return "TRUE"
    if raw in {"false", "0", "no", "n"}:
        return "FALSE"

    raise ValueError(f"Cannot coerce boolean SQL literal from value={value!r}")


def _seed_jsonb_value(value: Any) -> Any:
    if isinstance(value, str):
        raw = value.strip()
        if not raw:
            return {}
        return json.loads(raw)
    return value


def _sql_jsonb_literal(value: Any) -> str:
    return f"{_sql_quote_text(_json_compact(_seed_jsonb_value(value)))}::jsonb"

def scheduler_schema_sql_text(
    schema_path: Path = DEFAULT_SCHEDULER_SCHEMA_SQL_PATH,
) -> str:
    return _read_sql_artifact(schema_path, "scheduler schema")


def scheduler_schema_sql_payload(
    schema_path: Path = DEFAULT_SCHEDULER_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    sql = scheduler_schema_sql_text(schema_path)

    return {
        "path": str(Path(schema_path)),
        "sql": sql,
    }


def scheduler_seed_sql_text(
    seed_path: Path = DEFAULT_SCHEDULER_SEED_SQL_PATH,
) -> str:
    return _read_sql_artifact(seed_path, "scheduler seed")


def scheduler_seed_sql_payload(
    seed_path: Path = DEFAULT_SCHEDULER_SEED_SQL_PATH,
) -> Dict[str, Any]:
    sql = scheduler_seed_sql_text(seed_path)

    return {
        "path": str(Path(seed_path)),
        "sql": sql,
    }

def render_scheduler_seed_sql(rows: Any = None) -> str:
    seed_rows = rows if rows is not None else scheduler_job_definition_seed_rows()

    if not isinstance(seed_rows, list) or not seed_rows:
        raise ValueError("Seed rows must be a non-empty list.")

    value_blocks: List[str] = []

    for row in seed_rows:
        if not isinstance(row, dict):
            raise ValueError("Each seed row must be a dictionary.")

        value_blocks.append(
            "\n".join(
                [
                    "    (",
                    f"        {_sql_quote_text(row.get('job_name'))},",
                    f"        {_sql_quote_text(row.get('job_description'))},",
                    f"        {_sql_jsonb_literal(row.get('default_options_json'))},",
                    f"        {_sql_bool_literal(row.get('supports_planning_only'))},",
                    f"        {_sql_bool_literal(row.get('supports_application_planning'))},",
                    f"        {_sql_quote_text(row.get('trigger_source'))},",
                    f"        {_sql_bool_literal(row.get('is_active'))}",
                    "    )",
                ]
            )
        )

    values_sql = ",\n".join(value_blocks)

    return "\n".join(
        [
            "INSERT INTO scheduler_job_definitions (",
            "    job_name,",
            "    job_description,",
            "    default_options_json,",
            "    supports_planning_only,",
            "    supports_application_planning,",
            "    trigger_source,",
            "    is_active",
            ")",
            "VALUES",
            values_sql,
            "ON CONFLICT (job_name) DO UPDATE",
            "SET",
            "    job_description = EXCLUDED.job_description,",
            "    default_options_json = EXCLUDED.default_options_json,",
            "    supports_planning_only = EXCLUDED.supports_planning_only,",
            "    supports_application_planning = EXCLUDED.supports_application_planning,",
            "    trigger_source = EXCLUDED.trigger_source,",
            "    is_active = EXCLUDED.is_active;",
        ]
    )

def scheduler_seed_sql_generation_payload(
    seed_path: Path = DEFAULT_SCHEDULER_SEED_SQL_PATH,
    rows: Any = None,
) -> Dict[str, Any]:
    generated_sql = render_scheduler_seed_sql(rows=rows)
    artifact_sql = scheduler_seed_sql_text(seed_path)

    return {
        "artifact_path": str(Path(seed_path)),
        "artifact_sql": artifact_sql,
        "generated_sql": generated_sql,
        "matches_artifact": generated_sql == artifact_sql,
    }

def _default_job_options(job_name: str) -> Dict[str, Any]:
    normalized = _clean_text(job_name).lower()

    if normalized == "live_pipeline":
        return {
            "planning_only": False,
            "run_application_planning": True,
            "output_dir": "outputs/application_planning",
            "job_limit": 50,
            "job_packet_limit": 0,
            "llm_actions": "APPLY,APPLY_REVIEW_VARIANTS",
            "generate_tailoring": False,
            "generate_llm_tailoring": False,
            "refresh_llm_tailoring": False,
            "generate_llm_fallback": False,
            "delete_seen_data": "no",
        }

    return {}


def scheduler_postgres_table_specs() -> Dict[str, Any]:
    return {
        "scheduler_job_definitions": {
            "description": "Static catalog of supported scheduled jobs and their default runtime options.",
            "primary_key": ["job_name"],
            "columns": [
                {"name": "job_name", "type": "text", "nullable": False},
                {"name": "job_description", "type": "text", "nullable": False},
                {"name": "default_options_json", "type": "jsonb", "nullable": False},
                {"name": "supports_planning_only", "type": "boolean", "nullable": False},
                {"name": "supports_application_planning", "type": "boolean", "nullable": False},
                {"name": "trigger_source", "type": "text", "nullable": False},
                {"name": "is_active", "type": "boolean", "nullable": False},
            ],
            "indexes": [
                {"name": "idx_scheduler_job_definitions_active", "columns": ["is_active"]},
            ],
        },
        "scheduler_run_history": {
            "description": "Append-only execution history for externally scheduled wrapper runs.",
            "primary_key": ["run_id"],
            "columns": [
                {"name": "run_id", "type": "text", "nullable": False},
                {"name": "job_name", "type": "text", "nullable": False},
                {"name": "job_description", "type": "text", "nullable": False},
                {"name": "status", "type": "text", "nullable": False},
                {"name": "started_at", "type": "timestamptz", "nullable": False},
                {"name": "finished_at", "type": "timestamptz", "nullable": False},
                {"name": "return_code", "type": "integer", "nullable": False},
                {"name": "command_text", "type": "text", "nullable": False},
                {"name": "command_json", "type": "jsonb", "nullable": False},
                {"name": "options_json", "type": "jsonb", "nullable": False},
                {"name": "trigger_source", "type": "text", "nullable": False},
                {"name": "error_text", "type": "text", "nullable": False},
            ],
            "indexes": [
                {"name": "idx_scheduler_run_history_job_started", "columns": ["job_name", "started_at"]},
                {"name": "idx_scheduler_run_history_status_started", "columns": ["status", "started_at"]},
            ],
            "foreign_keys": [
                {
                    "column": "job_name",
                    "references": "scheduler_job_definitions.job_name",
                }
            ],
        },
    }


def scheduler_job_definition_seed_rows() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    for definition in get_scheduled_job_definitions():
        job_name = _clean_text(definition.get("name"))
        rows.append(
            {
                "job_name": job_name,
                "job_description": _clean_text(definition.get("description")),
                "default_options_json": _json_compact(_default_job_options(job_name)),
                "supports_planning_only": job_name == "live_pipeline",
                "supports_application_planning": job_name == "live_pipeline",
                "trigger_source": "external_scheduler_wrapper",
                "is_active": True,
            }
        )

    return rows


def scheduler_run_history_db_row(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Scheduler run history record must be a dictionary.")

    required_text_fields = [
        "run_id",
        "job_name",
        "job_description",
        "status",
        "started_at",
        "finished_at",
    ]
    missing_text_fields = [
        field for field in required_text_fields
        if not _clean_text(record.get(field))
    ]
    if missing_text_fields:
        raise ValueError(
            "Scheduler run history record is missing required fields: "
            + ", ".join(missing_text_fields)
        )

    if "return_code" not in record or record.get("return_code") is None:
        raise ValueError(
            "Scheduler run history record is missing required fields: return_code"
        )

    command = record.get("command", [])
    if not isinstance(command, list):
        raise ValueError("record['command'] must be a list.")

    options = record.get("options", {})
    if not isinstance(options, dict):
        raise ValueError("record['options'] must be a dictionary.")

    command_text = _clean_text(record.get("command_text"))
    if not command_text:
        command_text = " ".join(str(part) for part in command)

    return {
        "run_id": _clean_text(record.get("run_id")),
        "job_name": _clean_text(record.get("job_name")),
        "job_description": _clean_text(record.get("job_description")),
        "status": _clean_text(record.get("status")).lower(),
        "started_at": _clean_text(record.get("started_at")),
        "finished_at": _clean_text(record.get("finished_at")),
        "return_code": int(record.get("return_code")),
        "command_text": command_text,
        "command_json": _json_compact(command),
        "options_json": _json_compact(options),
        "trigger_source": _clean_text(record.get("trigger_source")) or "external_scheduler_wrapper",
        "error_text": _clean_text(record.get("error")),
    }