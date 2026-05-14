from __future__ import annotations

import hashlib
import json
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Any, Dict, List
from urllib.parse import urlsplit, urlunsplit

DEFAULT_PATCH_SELECTIONS_SCHEMA_SQL_PATH = Path("src/storage/patch_selections/schema.sql")


def _json_compact(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _normalize_job_name(value: Any) -> str:
    text = _clean_text(value).lower()
    return text.replace("-", "_").replace(" ", "_")


def _normalize_selected_patch_candidate_ids(value: Any) -> List[str]:
    if isinstance(value, list):
        raw_items = value
    else:
        raw_text = _clean_text(value)
        if not raw_text:
            raw_items = []
        else:
            try:
                parsed = json.loads(raw_text)
                raw_items = parsed if isinstance(parsed, list) else [raw_text]
            except Exception:
                raw_items = [part.strip() for part in raw_text.split(",") if part.strip()]

    normalized: List[str] = []
    seen = set()

    for item in raw_items:
        candidate_id = _clean_text(item)
        if not candidate_id or candidate_id in seen:
            continue
        seen.add(candidate_id)
        normalized.append(candidate_id)

    return normalized


def _serialize_selected_patch_candidate_ids(value: Any) -> str:
    return json.dumps(
        _normalize_selected_patch_candidate_ids(value),
        ensure_ascii=False,
        sort_keys=False,
    )


def _resolve_database_url(
    explicit_value: str,
    env_var_name: str,
    *,
    allow_placeholder: bool,
) -> str:
    explicit = str(explicit_value or "").strip()
    if explicit:
        return explicit

    env_name = str(env_var_name or "").strip() or "DATABASE_URL"
    env_value = str(os.environ.get(env_name, "") or "").strip()
    if env_value:
        return env_value

    if allow_placeholder:
        return f"${env_name}"

    raise SystemExit(
        f"Database URL is required. Pass --database-url or set {env_name} in the environment."
    )


def _redact_database_url(value: str) -> str:
    raw = str(value or "").strip()
    if not raw:
        return raw

    parts = urlsplit(raw)
    if "@" not in parts.netloc:
        return raw

    userinfo, hostinfo = parts.netloc.rsplit("@", 1)

    if ":" in userinfo:
        username, _password = userinfo.split(":", 1)
        redacted_userinfo = f"{username}:***"
    else:
        redacted_userinfo = "***"

    return urlunsplit(
        (
            parts.scheme,
            f"{redacted_userinfo}@{hostinfo}",
            parts.path,
            parts.query,
            parts.fragment,
        )
    )


def _sql_quote_text(value: Any) -> str:
    text = str(value or "")
    return "'" + text.replace("'", "''") + "'"


def _read_sql_artifact(path: Path, label: str) -> str:
    resolved = Path(path)
    if not resolved.exists():
        raise ValueError(f"Missing {label} SQL file: {resolved}")

    sql = resolved.read_text(encoding="utf-8")
    if not sql.strip():
        raise ValueError(f"{label.capitalize()} SQL file is empty: {resolved}")

    return sql


def _build_selection_id(normalized_row: Dict[str, Any]) -> str:
    signature_payload = {
        "selection_timestamp": normalized_row["selection_timestamp"],
        "tailoring_json_path": normalized_row["tailoring_json_path"],
        "artifact_signature": normalized_row["artifact_signature"],
        "selected_resume": normalized_row["selected_resume"],
        "selected_candidate_ids_json": normalized_row["selected_candidate_ids_json"],
        "note": normalized_row["note"],
    }
    blob = _json_compact(signature_payload)
    return hashlib.sha1(blob.encode("utf-8")).hexdigest()


def patch_selection_db_row(record: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(record, dict):
        raise ValueError("Patch selection record must be a dictionary.")

    selection_timestamp = _clean_text(record.get("selection_timestamp"))
    if not selection_timestamp:
        raise ValueError("Patch selection record is missing required field: selection_timestamp")

    tailoring_json_path = _clean_text(record.get("tailoring_json_path"))
    if not tailoring_json_path:
        raise ValueError("Patch selection record is missing required field: tailoring_json_path")

    artifact_signature = _clean_text(record.get("artifact_signature"))
    if not artifact_signature:
        raise ValueError("Patch selection record is missing required field: artifact_signature")

    selected_resume = _clean_text(record.get("selected_resume"))
    if not selected_resume:
        raise ValueError("Patch selection record is missing required field: selected_resume")

    normalized_row = {
        "selection_timestamp": selection_timestamp,
        "owner_user_id": _clean_text(record.get("owner_user_id")),
        "job_doc_id": _clean_text(record.get("job_doc_id")),
        "queue_rank": _clean_text(record.get("queue_rank")),
        "job_company": _clean_text(record.get("job_company")),
        "job_title": _clean_text(record.get("job_title")),
        "selected_resume": selected_resume,
        "tailoring_json_path": tailoring_json_path,
        "artifact_signature": artifact_signature,
        "selected_candidate_ids_json": _serialize_selected_patch_candidate_ids(
            record.get("selected_candidate_ids_json", "")
        ),
        "note": _clean_text(record.get("note")),
    }

    normalized_row["selection_id"] = _build_selection_id(normalized_row)
    return normalized_row


def patch_selections_table_specs() -> Dict[str, Any]:
    return {
        "patch_selections": {
            "description": "Append-only operational history of manual patch selections for tailoring artifacts.",
            "primary_key": ["selection_id"],
            "columns": [
                {"name": "selection_id", "type": "text", "nullable": False},
                {"name": "selection_timestamp", "type": "timestamptz", "nullable": False},
                {"name": "owner_user_id", "type": "text", "nullable": False},
                {"name": "job_doc_id", "type": "text", "nullable": False},
                {"name": "queue_rank", "type": "text", "nullable": False},
                {"name": "job_company", "type": "text", "nullable": False},
                {"name": "job_title", "type": "text", "nullable": False},
                {"name": "selected_resume", "type": "text", "nullable": False},
                {"name": "tailoring_json_path", "type": "text", "nullable": False},
                {"name": "artifact_signature", "type": "text", "nullable": False},
                {"name": "selected_candidate_ids_json", "type": "jsonb", "nullable": False},
                {"name": "note", "type": "text", "nullable": False},
            ],
            "indexes": [
                {"name": "idx_patch_selections_path_timestamp", "columns": ["tailoring_json_path", "selection_timestamp"]},
                {"name": "idx_patch_selections_job_doc_id", "columns": ["job_doc_id"]},
                {"name": "idx_patch_selections_queue_rank", "columns": ["queue_rank"]},
                {"name": "idx_patch_selections_owner_timestamp", "columns": ["owner_user_id", "selection_timestamp"]},
                {"name": "idx_patch_selections_owner_job_doc_id", "columns": ["owner_user_id", "job_doc_id"]},
            ],
        }
    }


def render_patch_selections_schema_sql() -> str:
    return "\n".join(
        [
            "CREATE TABLE IF NOT EXISTS patch_selections (",
            "    selection_id TEXT PRIMARY KEY,",
            "    selection_timestamp TIMESTAMPTZ NOT NULL,",
            "    owner_user_id TEXT NOT NULL DEFAULT '',",
            "    job_doc_id TEXT NOT NULL,",
            "    queue_rank TEXT NOT NULL,",
            "    job_company TEXT NOT NULL,",
            "    job_title TEXT NOT NULL,",
            "    selected_resume TEXT NOT NULL,",
            "    tailoring_json_path TEXT NOT NULL,",
            "    artifact_signature TEXT NOT NULL,",
            "    selected_candidate_ids_json JSONB NOT NULL,",
            "    note TEXT NOT NULL",
            ");",
            "",
            "CREATE INDEX IF NOT EXISTS idx_patch_selections_path_timestamp",
            "ON patch_selections (tailoring_json_path, selection_timestamp DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_patch_selections_job_doc_id",
            "ON patch_selections (job_doc_id);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_patch_selections_queue_rank",
            "ON patch_selections (queue_rank);",
            "",
            "ALTER TABLE patch_selections",
            "ADD COLUMN IF NOT EXISTS owner_user_id TEXT NOT NULL DEFAULT '';",
            "",
            "CREATE INDEX IF NOT EXISTS idx_patch_selections_owner_timestamp",
            "ON patch_selections (owner_user_id, selection_timestamp DESC);",
            "",
            "CREATE INDEX IF NOT EXISTS idx_patch_selections_owner_job_doc_id",
            "ON patch_selections (owner_user_id, job_doc_id);",
        ]
    )


def patch_selections_schema_sql_text(
    schema_path: Path = DEFAULT_PATCH_SELECTIONS_SCHEMA_SQL_PATH,
) -> str:
    return _read_sql_artifact(schema_path, "patch selections schema")


def patch_selections_schema_sql_payload(
    schema_path: Path = DEFAULT_PATCH_SELECTIONS_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    sql = patch_selections_schema_sql_text(schema_path)
    return {
        "path": str(Path(schema_path)),
        "sql": sql,
    }


def patch_selections_schema_sql_generation_payload(
    schema_path: Path = DEFAULT_PATCH_SELECTIONS_SCHEMA_SQL_PATH,
) -> Dict[str, Any]:
    generated_sql = render_patch_selections_schema_sql()
    artifact_sql = patch_selections_schema_sql_text(schema_path)

    return {
        "artifact_path": str(Path(schema_path)),
        "artifact_sql": artifact_sql,
        "generated_sql": generated_sql,
        "matches_artifact": generated_sql.strip() == artifact_sql.strip(),
    }


def patch_selections_contract_health_payload() -> Dict[str, Any]:
    schema_generation = patch_selections_schema_sql_generation_payload()

    return {
        "ok": True,
        "artifacts": {
            "schema_sql_path": str(DEFAULT_PATCH_SELECTIONS_SCHEMA_SQL_PATH),
        },
        "checks": {
            "schema_sql_matches_artifact": bool(schema_generation["matches_artifact"]),
        },
        "all_checks_pass": bool(schema_generation["matches_artifact"]),
    }


def _build_insert_sql(row: Dict[str, Any]) -> str:
    return "\n".join(
        [
            "INSERT INTO patch_selections (",
            "    selection_id,",
            "    selection_timestamp,",
            "    owner_user_id,",
            "    job_doc_id,",
            "    queue_rank,",
            "    job_company,",
            "    job_title,",
            "    selected_resume,",
            "    tailoring_json_path,",
            "    artifact_signature,",
            "    selected_candidate_ids_json,",
            "    note",
            ")",
            "VALUES (",
            f"    {_sql_quote_text(row['selection_id'])},",
            f"    {_sql_quote_text(row['selection_timestamp'])}::timestamptz,",
            f"    {_sql_quote_text(row['owner_user_id'])},",
            f"    {_sql_quote_text(row['job_doc_id'])},",
            f"    {_sql_quote_text(row['queue_rank'])},",
            f"    {_sql_quote_text(row['job_company'])},",
            f"    {_sql_quote_text(row['job_title'])},",
            f"    {_sql_quote_text(row['selected_resume'])},",
            f"    {_sql_quote_text(row['tailoring_json_path'])},",
            f"    {_sql_quote_text(row['artifact_signature'])},",
            f"    {_sql_quote_text(row['selected_candidate_ids_json'])}::jsonb,",
            f"    {_sql_quote_text(row['note'])}",
            ")",
            "ON CONFLICT (selection_id) DO NOTHING;",
        ]
    )


def insert_patch_selection_row_to_postgres(
    *,
    record: Dict[str, Any],
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    allow_contract_drift: bool = False,
) -> Dict[str, Any]:
    contract_health = patch_selections_contract_health_payload()
    if not contract_health.get("all_checks_pass", False) and not allow_contract_drift:
        raise SystemExit(
            "Patch-selections contract health check failed. Refusing Postgres insert while artifacts are drifting. "
            "Fix the schema artifact mismatch first, or pass --allow-contract-drift if you intentionally want to override."
        )

    row = patch_selection_db_row(record)
    sql = _build_insert_sql(row)

    database_url_value = _resolve_database_url(
        database_url,
        database_url_env,
        allow_placeholder=bool(print_only),
    )

    cmd: List[str] = [
        str(psql_bin),
        database_url_value,
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-c",
        sql,
    ]

    redacted_cmd = list(cmd)
    redacted_cmd[1] = _redact_database_url(redacted_cmd[1])

    payload: Dict[str, Any] = {
        "ok": True,
        "contract_health_ok": bool(contract_health["all_checks_pass"]),
        "row": row,
        "command": redacted_cmd,
        "command_text": shlex.join(redacted_cmd),
        "table_name": "patch_selections",
    }

    if print_only:
        return payload

    if shutil.which(str(psql_bin)) is None:
        raise SystemExit(
            f"psql executable not found on PATH: {psql_bin!r}. "
            "Install psql or pass --psql-bin with the correct executable path."
        )

    subprocess.run(cmd, check=True)
    return payload