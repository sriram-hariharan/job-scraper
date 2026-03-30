from __future__ import annotations

import argparse
import csv
import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List

DEFAULT_NOTIFICATION_STATE_PATH = Path("outputs/scheduler_logs/notification_state.csv")

from src.storage.notification_state.store import (
    notification_state_db_row,
    notification_state_contract_health_payload,
)

NOTIFICATION_STATE_HEADERS = [
    "state_id",
    "state_timestamp",
    "notification_id",
    "is_read",
]


def _load_local_dotenv_if_present(dotenv_path: Path = Path(".env")) -> None:
    path = dotenv_path.expanduser()
    if not path.exists() or not path.is_file():
        return

    try:
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()

            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            if not key or key in os.environ:
                continue

            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                value = value[1:-1]

            os.environ[key] = value
    except Exception:
        return


_load_local_dotenv_if_present()


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


def _load_notification_state_rows(csv_path: Path) -> List[Dict[str, Any]]:
    if not csv_path.exists() or not csv_path.is_file():
        return []

    rows: List[Dict[str, Any]] = []

    with csv_path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)

        for line_number, raw_row in enumerate(reader, start=2):
            try:
                normalized = notification_state_db_row(dict(raw_row))
            except Exception as exc:
                raise SystemExit(
                    f"Invalid notification state row at CSV line {line_number}: {exc}"
                ) from exc

            rows.append(normalized)

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
        writer = csv.DictWriter(tmp, fieldnames=NOTIFICATION_STATE_HEADERS)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in NOTIFICATION_STATE_HEADERS})
    finally:
        tmp.close()

    return tmp_path


def _psql_copy_path_literal(path: Path) -> str:
    return str(path).replace("'", "''")


def _build_sync_sql(csv_path: Path) -> str:
    copy_path = _psql_copy_path_literal(csv_path)

    copy_cmd = (
        "\\copy _notification_state_stage "
        "(state_id, state_timestamp, notification_id, is_read) "
        f"FROM '{copy_path}' WITH (FORMAT csv, HEADER true);"
    )

    return "\n".join(
        [
            "CREATE TEMP TABLE _notification_state_stage (",
            "    state_id TEXT,",
            "    state_timestamp TIMESTAMPTZ,",
            "    notification_id TEXT,",
            "    is_read BOOLEAN",
            ") ON COMMIT DROP;",
            "",
            copy_cmd,
            "",
            "WITH inserted AS (",
            "    INSERT INTO notification_state_events (",
            "        state_id,",
            "        state_timestamp,",
            "        notification_id,",
            "        is_read",
            "    )",
            "    SELECT",
            "        state_id,",
            "        state_timestamp,",
            "        notification_id,",
            "        is_read",
            "    FROM _notification_state_stage",
            "    ON CONFLICT (state_id) DO NOTHING",
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


def sync_notification_state_to_postgres(
    *,
    csv_path: Path = DEFAULT_NOTIFICATION_STATE_PATH,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    psql_bin: str = "psql",
    print_only: bool = False,
    allow_contract_drift: bool = False,
) -> Dict[str, Any]:
    contract_health = notification_state_contract_health_payload()
    if not contract_health.get("all_checks_pass", False) and not allow_contract_drift:
        raise SystemExit(
            "Notification-state contract health check failed. Refusing to sync while artifacts are drifting. "
            "Fix the schema artifact mismatch first, or pass --allow-contract-drift if you intentionally want to override."
        )

    resolved_csv_path = Path(csv_path).expanduser()
    rows = _load_notification_state_rows(resolved_csv_path)

    payload: Dict[str, Any] = {
        "csv_path": str(resolved_csv_path),
        "contract_health_ok": bool(contract_health["all_checks_pass"]),
        "csv_row_count": len(rows),
        "staged_csv_path": "",
        "sql_path": "",
        "command": [],
        "command_text": "",
        "skipped": "",
    }

    if not rows:
        payload["skipped"] = "no_rows"
        return payload

    staged_csv_path = _write_rows_csv(rows)
    sql_path = _write_sync_sql(staged_csv_path)

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

        payload["staged_csv_path"] = str(staged_csv_path)
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
            staged_csv_path.unlink(missing_ok=True)
        except Exception:
            pass
        try:
            sql_path.unlink(missing_ok=True)
        except Exception:
            pass


def _parse_args():
    parser = argparse.ArgumentParser(
        description="Sync notification_state.csv into Postgres."
    )
    parser.add_argument(
        "--csv-path",
        default=str(DEFAULT_NOTIFICATION_STATE_PATH),
        help="Notification state CSV path.",
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
        help="Allow execution even if the schema artifact drift check fails.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    payload = sync_notification_state_to_postgres(
        csv_path=Path(args.csv_path).expanduser(),
        database_url=args.database_url,
        database_url_env=args.database_url_env,
        psql_bin=args.psql_bin,
        print_only=bool(args.print_only),
        allow_contract_drift=bool(args.allow_contract_drift),
    )

    print(f"csv_path={payload['csv_path']}")
    print(f"contract_health_ok={payload['contract_health_ok']}")
    print(f"csv_row_count={payload['csv_row_count']}")

    if payload.get("skipped") == "no_rows":
        print("No notification state rows to sync.")
        return 0

    print(f"staged_csv_path={payload['staged_csv_path']}")
    print(f"sql_path={payload['sql_path']}")
    print(f"command={payload['command_text']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())