from __future__ import annotations

import argparse
import os
import shlex
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List

from src.storage.notification_state.store import (
    notification_state_contract_health_payload,
    notification_state_schema_sql_payload,
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


def _build_psql_apply_cmd(
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
        description="Apply notification-state storage SQL artifact to Postgres through psql."
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
        help="Print the resolved psql command and exit without executing.",
    )
    parser.add_argument(
        "--allow-contract-drift",
        action="store_true",
        help="Allow execution even if the generated schema does not match the checked-in artifact.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()

    contract_health = notification_state_contract_health_payload()
    if not contract_health.get("all_checks_pass", False) and not args.allow_contract_drift:
        raise SystemExit(
            "Notification-state contract health check failed. Refusing to apply SQL while artifacts are drifting. "
            "Re-run after fixing the schema artifact mismatch, or pass --allow-contract-drift if you intentionally want to override."
        )

    sql_payload: Dict[str, str] = notification_state_schema_sql_payload()
    sql_path = Path(sql_payload["path"]).expanduser()

    if not sql_path.exists() or not sql_path.is_file():
        raise SystemExit(f"Resolved SQL artifact does not exist: {sql_path}")

    database_url = _resolve_database_url(
        args.database_url,
        args.database_url_env,
        allow_placeholder=bool(args.print_only),
    )

    cmd = _build_psql_apply_cmd(
        psql_bin=str(args.psql_bin),
        database_url=database_url,
        sql_path=sql_path,
    )

    print(f"sql_path={sql_path}")
    print(f"contract_health_ok={contract_health['all_checks_pass']}")
    print(f"command={shlex.join(cmd)}")

    if args.print_only:
        return 0

    if shutil.which(str(args.psql_bin)) is None:
        raise SystemExit(
            f"psql executable not found on PATH: {args.psql_bin!r}. "
            "Install psql or pass --psql-bin with the correct executable path."
        )

    subprocess.run(cmd, check=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())