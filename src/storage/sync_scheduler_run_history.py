from __future__ import annotations

import argparse
import csv
import json
import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple

from src.config.settings import SCHEDULER_RUN_HISTORY_PATH
from src.storage.scheduler_store import (
    scheduler_contract_health_payload,
    scheduler_run_history_db_row,
)

DEFAULT_HISTORY_PATH = Path(SCHEDULER_RUN_HISTORY_PATH)

RUN_HISTORY_HEADERS = [
    "run_id",
    "job_name",
    "job_description",
    "status",
    "started_at",
    "finished_at",
    "return_code",
    "command_text",
    "command_json",
    "options_json",
    "trigger_source",
    "error_text",
]


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


def _load_history_rows(history_path: Path) -> List[Dict[str, Any]]:
    if not history_path.exists() or not history_path.is_file():
        raise SystemExit(f"Scheduler history file not found: {history_path}")

    rows: List[Dict[str, Any]] = []

    with history_path.open("r", encoding="utf-8") as f:
        for line_number, raw_line in enumerate(f, start=1):
            line = raw_line.strip()
            if not line:
                continue

            try:
                payload = json.loads(line)
            except Exception as exc:
                raise SystemExit(
                    f"Invalid JSON in scheduler history at line {line_number}: {exc}"
                ) from exc

            if not isinstance(payload, dict):
                raise SystemExit(
                    f"Scheduler history line {line_number} is not a JSON object."
                )

            try:
                row = scheduler_run_history_db_row(payload)
            except Exception as exc:
                raise SystemExit(
                    f"Invalid scheduler history record at line {line_number}: {exc}"
                ) from exc

            rows.append(row)

    return rows


def _write_rows_csv(rows: List[Dict[str, Any]]) -> Path:
    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        newline="",
        suffix=".csv",
        delete=False,
    )
    tmp_path = Path(tmp.name)

    try:
        writer = csv.DictWriter(tmp, fieldnames=RUN_HISTORY_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in RUN_HISTORY_HEADERS})
    finally:
        tmp.close()

    return tmp_path


def _psql_copy_path_literal(path: Path) -> str:
    return str(path).replace("'", "''")


def _build_sync_sql(csv_path: Path) -> str:
    copy_path = _psql_copy_path_literal(csv_path)

    copy_cmd = (
        "\\copy _scheduler_run_history_stage "
        "(run_id, job_name, job_description, status, started_at, finished_at, "
        "return_code, command_text, command_json, options_json, trigger_source, error_text) "
        f"FROM '{copy_path}' WITH (FORMAT csv, HEADER true);"
    )

    return "\n".join(
        [
            "CREATE TEMP TABLE _scheduler_run_history_stage (",
            "    run_id TEXT,",
            "    job_name TEXT,",
            "    job_description TEXT,",
            "    status TEXT,",
            "    started_at TIMESTAMPTZ,",
            "    finished_at TIMESTAMPTZ,",
            "    return_code INTEGER,",
            "    command_text TEXT,",
            "    command_json JSONB,",
            "    options_json JSONB,",
            "    trigger_source TEXT,",
            "    error_text TEXT",
            ") ON COMMIT DROP;",
            "",
            copy_cmd,
            "",
            "WITH inserted AS (",
            "    INSERT INTO scheduler_run_history (",
            "        run_id,",
            "        job_name,",
            "        job_description,",
            "        status,",
            "        started_at,",
            "        finished_at,",
            "        return_code,",
            "        command_text,",
            "        command_json,",
            "        options_json,",
            "        trigger_source,",
            "        error_text",
            "    )",
            "    SELECT",
            "        run_id,",
            "        job_name,",
            "        job_description,",
            "        status,",
            "        started_at,",
            "        finished_at,",
            "        return_code,",
            "        COALESCE(command_text, ''),",
            "        command_json,",
            "        options_json,",
            "        COALESCE(trigger_source, 'external_scheduler_wrapper'),",
            "        COALESCE(error_text, '')",
            "    FROM _scheduler_run_history_stage",
            "    ON CONFLICT (run_id) DO NOTHING",
            "    RETURNING 1",
            ")",
            "SELECT COUNT(*) AS inserted_rows FROM inserted;",
        ]
    )

def _write_sync_sql(csv_path: Path) -> Path:
    sql_text = _build_sync_sql(csv_path)

    tmp = tempfile.NamedTemporaryFile(
        mode="w",
        encoding="utf-8",
        suffix=".sql",
        delete=False,
    )
    tmp_path = Path(tmp.name)

    try:
        tmp.write(sql_text)
    finally:
        tmp.close()

    return tmp_path


def _build_psql_cmd(
    *,
    psql_bin: str,
    database_url: str,
    sql_path: Path,
) -> List[str]:
    return [
        psql_bin,
        database_url,
        "-X",
        "-v",
        "ON_ERROR_STOP=1",
        "-1",
        "-f",
        str(sql_path),
    ]


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Sync scheduler run history JSONL into Postgres."
    )
    parser.add_argument(
        "--history-path",
        default=str(DEFAULT_HISTORY_PATH),
        help="Scheduler run history JSONL path.",
    )
    parser.add_argument(
        "--database-url",
        default="",
        help="Explicit Postgres connection URL. If omitted, read from --database-url-env.",
    )
    parser.add_argument(
        "--database-url-env",
        default="DATABASE_URL",
        help="Environment variable name that holds the Postgres connection URL.",
    )
    parser.add_argument(
        "--psql-bin",
        default="psql",
        help="psql executable to use.",
    )
    parser.add_argument(
        "--print-only",
        action="store_true",
        help="Print the resolved psql sync command without executing it.",
    )
    parser.add_argument(
        "--allow-contract-drift",
        action="store_true",
        help="Allow execution even if scheduler SQL artifact drift checks fail.",
    )
    return parser.parse_args()

def sync_scheduler_run_history_to_postgres(
    *,
    history_path: Path = DEFAULT_HISTORY_PATH,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    allow_contract_drift: bool = False,
) -> Dict[str, Any]:
    contract_health = scheduler_contract_health_payload()
    if not contract_health.get("all_checks_pass", False) and not allow_contract_drift:
        raise SystemExit(
            "Scheduler contract health check failed. Refusing to sync scheduler run history while artifacts are drifting. "
            "Fix the scheduler contract drift first, or pass --allow-contract-drift if you intentionally want to override."
        )

    resolved_history_path = Path(history_path).expanduser()
    rows = _load_history_rows(resolved_history_path)

    payload: Dict[str, Any] = {
        "history_path": str(resolved_history_path),
        "contract_health_ok": bool(contract_health["all_checks_pass"]),
        "history_row_count": len(rows),
        "staged_csv_path": "",
        "sql_path": "",
        "command": [],
        "command_text": "",
        "skipped": "",
    }

    if not rows:
        payload["skipped"] = "no_rows"
        return payload

    csv_path = _write_rows_csv(rows)
    sql_path = _write_sync_sql(csv_path)

    try:
        database_url_value = _resolve_database_url(
            database_url,
            database_url_env,
            allow_placeholder=bool(print_only),
        )

        cmd = _build_psql_cmd(
            psql_bin=str(psql_bin),
            database_url=database_url_value,
            sql_path=sql_path,
        )

        payload["staged_csv_path"] = str(csv_path)
        payload["sql_path"] = str(sql_path)
        payload["command"] = cmd
        payload["command_text"] = shlex.join(cmd)

        if print_only:
            return payload

        if shutil.which(str(psql_bin)) is None:
            raise SystemExit(
                f"psql executable not found on PATH: {psql_bin!r}. "
                "Install psql or pass --psql-bin with the correct executable path."
            )

        subprocess.run(cmd, check=True)
        return payload
    finally:
        try:
            csv_path.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            sql_path.unlink(missing_ok=True)
        except Exception:
            pass

def main() -> int:
    args = _parse_args()

    payload = sync_scheduler_run_history_to_postgres(
        history_path=Path(args.history_path).expanduser(),
        database_url=args.database_url,
        database_url_env=args.database_url_env,
        psql_bin=args.psql_bin,
        print_only=bool(args.print_only),
        allow_contract_drift=bool(args.allow_contract_drift),
    )

    print(f"history_path={payload['history_path']}")
    print(f"contract_health_ok={payload['contract_health_ok']}")
    print(f"history_row_count={payload['history_row_count']}")

    if payload.get("skipped") == "no_rows":
        print("No scheduler history rows to sync.")
        return 0

    print(f"staged_csv_path={payload['staged_csv_path']}")
    print(f"sql_path={payload['sql_path']}")
    print(f"command={payload['command_text']}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())