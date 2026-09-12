from __future__ import annotations

import argparse
import hashlib
import importlib
import json
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Sequence
from urllib.parse import parse_qs, unquote, urlsplit

REPO_ROOT = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class ProductionSchema:
    name: str
    relative_path: str
    reason: str
    contract_health_owner: str = ""


# Ordered, finite allowlist. New schema artifacts never become executable merely
# by being added to the repository.
PRODUCTION_SCHEMA_ALLOWLIST: Sequence[ProductionSchema] = (
    ProductionSchema(
        "user_pipeline",
        "src/storage/user_pipeline/schema.sql",
        "normal authenticated pipeline runs, seen jobs, and persisted artifacts",
        "src.storage.user_pipeline.store:user_pipeline_contract_health_payload",
    ),
    ProductionSchema(
        "profile_resumes",
        "src/storage/profile_resumes/schema.sql",
        "normal authenticated resume storage and role mappings",
    ),
    ProductionSchema(
        "onboarding_preferences",
        "src/storage/onboarding_preferences/schema.sql",
        "normal authenticated onboarding preferences",
    ),
    ProductionSchema(
        "user_ai_settings",
        "src/storage/user_ai_settings/schema.sql",
        "normal authenticated provider preferences and encrypted credentials",
    ),
    ProductionSchema(
        "notification_state",
        "src/storage/notification_state/schema.sql",
        "normal per-user notification state",
        "src.storage.notification_state.store:notification_state_contract_health_payload",
    ),
    ProductionSchema(
        "bulk_generation",
        "src/storage/bulk_generation/schema.sql",
        "normal persistent bulk-generation runs and items",
    ),
    ProductionSchema(
        "agent_feedback",
        "src/storage/agent_feedback/schema.sql",
        "current authenticated feedback API and summaries",
        "src.storage.agent_feedback.store:agent_feedback_contract_health_payload",
    ),
)

INTENTIONALLY_EXCLUDED_SCHEMAS: Mapping[str, str] = {
    "agent_state": "static/default-off agent-state artifact with incompatible experimental tables",
    "agent_trace": "default-off tracing capability",
    "agentic_approvals": "default-off static approval artifact",
    "durable_orchestration": "explicitly gated durable orchestration capability",
    "vector_evidence": "default-off pgvector capability; production has no vector extension",
}

_FORBIDDEN_SQL = re.compile(
    r"\b(?:DROP|TRUNCATE)\b|\bDELETE\s+FROM\b|\bUPDATE\b|"
    r"\bINSERT\s+INTO\b|\bCREATE\s+EXTENSION\b",
    re.IGNORECASE,
)


def _schema_path(schema: ProductionSchema) -> Path:
    path = REPO_ROOT / schema.relative_path
    if path.is_symlink() or not path.is_file():
        raise SystemExit(f"Production schema is missing or not a regular file: {schema.relative_path}")
    return path


def _load_contract_health(owner: str) -> Dict[str, Any]:
    module_name, separator, function_name = owner.partition(":")
    if not separator or not module_name or not function_name:
        raise SystemExit(f"Invalid contract-health owner: {owner!r}")
    module = importlib.import_module(module_name)
    function: Callable[[], Dict[str, Any]] = getattr(module, function_name)
    payload = function()
    if not payload.get("all_checks_pass", False):
        raise SystemExit(f"Schema contract health failed for {owner}")
    return payload


def _validate_additive_sql(schema: ProductionSchema, sql: str) -> None:
    if _FORBIDDEN_SQL.search(sql):
        raise SystemExit(
            f"Refusing non-additive production schema SQL: {schema.relative_path}"
        )

    for statement in (part.strip() for part in sql.split(";") if part.strip()):
        normalized = " ".join(statement.split()).upper()
        if normalized.startswith("CREATE TABLE IF NOT EXISTS "):
            continue
        if normalized.startswith("CREATE INDEX IF NOT EXISTS "):
            continue
        if normalized.startswith("CREATE UNIQUE INDEX IF NOT EXISTS "):
            continue
        if normalized.startswith("ALTER TABLE ") and " ADD COLUMN IF NOT EXISTS " in normalized:
            continue
        raise SystemExit(
            "Refusing production schema statement outside the additive allowlist: "
            f"{schema.relative_path}"
        )


def build_production_schema_plan() -> Dict[str, Any]:
    included: List[Dict[str, Any]] = []
    for position, schema in enumerate(PRODUCTION_SCHEMA_ALLOWLIST, start=1):
        path = _schema_path(schema)
        sql = path.read_text(encoding="utf-8")
        _validate_additive_sql(schema, sql)
        contract_health_checked = bool(schema.contract_health_owner)
        if contract_health_checked:
            _load_contract_health(schema.contract_health_owner)
        included.append(
            {
                "position": position,
                "name": schema.name,
                "path": schema.relative_path,
                "sha256": hashlib.sha256(sql.encode("utf-8")).hexdigest(),
                "reason": schema.reason,
                "contract_health_checked": contract_health_checked,
            }
        )

    return {
        "mode": "plan",
        "read_only": True,
        "transactional": True,
        "on_error_stop": True,
        "included": included,
        "excluded": dict(INTENTIONALLY_EXCLUDED_SCHEMAS),
    }


def _connection_environment(database_url: str) -> Dict[str, str]:
    parsed = urlsplit(database_url)
    if parsed.scheme not in {"postgres", "postgresql"}:
        raise SystemExit("DATABASE_URL must use the postgres or postgresql scheme.")
    if not parsed.hostname or not parsed.username or not parsed.path.strip("/"):
        raise SystemExit("DATABASE_URL must include host, user, and database name.")

    query = parse_qs(parsed.query, keep_blank_values=False)
    unsupported = sorted(set(query) - {"sslmode"})
    if unsupported:
        raise SystemExit(
            "DATABASE_URL contains unsupported connection options: " + ", ".join(unsupported)
        )

    env = dict(os.environ)
    env.update(
        {
            "PGHOST": parsed.hostname,
            "PGPORT": str(parsed.port or 5432),
            "PGUSER": unquote(parsed.username),
            "PGDATABASE": unquote(parsed.path.lstrip("/")),
        }
    )
    if parsed.password is not None:
        env["PGPASSWORD"] = unquote(parsed.password)
    if query.get("sslmode"):
        env["PGSSLMODE"] = query["sslmode"][-1]
    return env


def _combined_sql() -> str:
    parts = ["-- ApplyLens finite production schema upgrade allowlist"]
    for schema in PRODUCTION_SCHEMA_ALLOWLIST:
        sql = _schema_path(schema).read_text(encoding="utf-8")
        _validate_additive_sql(schema, sql)
        parts.extend([f"\n-- {schema.name}: {schema.relative_path}", sql.rstrip()])
    return "\n".join(parts) + "\n"


def apply_production_schema_upgrade(
    *,
    database_url: str,
    psql_bin: str = "psql",
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> Dict[str, Any]:
    plan = build_production_schema_plan()
    resolved_psql = shutil.which(psql_bin)
    if not resolved_psql:
        raise SystemExit(f"psql executable not found: {psql_bin!r}")

    connection_env = _connection_environment(database_url)
    descriptor, temp_name = tempfile.mkstemp(prefix="applylens_prod_schema_", suffix=".sql")
    sql_path = Path(temp_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(_combined_sql())

        command = [
            resolved_psql,
            "-X",
            "--set=ON_ERROR_STOP=1",
            "--single-transaction",
            "--file",
            str(sql_path),
        ]
        completed = runner(
            command,
            check=False,
            capture_output=True,
            text=True,
            env=connection_env,
        )
        if completed.returncode != 0:
            detail = str(completed.stderr or completed.stdout or "psql failed").strip()
            password = connection_env.get("PGPASSWORD", "")
            if password:
                detail = detail.replace(password, "[REDACTED]")
            detail = detail.replace(database_url, "[DATABASE_URL_REDACTED]")
            raise SystemExit(f"Production schema upgrade failed: {detail}")
    finally:
        sql_path.unlink(missing_ok=True)

    return {
        **plan,
        "mode": "apply",
        "read_only": False,
        "applied_schema_count": len(PRODUCTION_SCHEMA_ALLOWLIST),
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Plan or explicitly apply the finite production schema upgrade."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Explicitly apply the allowlisted additive schemas in one transaction.",
    )
    parser.add_argument(
        "--database-url-env",
        default="DATABASE_URL",
        help="Environment variable containing the Postgres URL (never printed).",
    )
    parser.add_argument("--psql-bin", default="psql")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.apply:
        database_url = str(os.environ.get(args.database_url_env, "") or "").strip()
        if not database_url:
            raise SystemExit(
                f"Explicit apply requires a non-empty {args.database_url_env} environment variable."
            )
        payload = apply_production_schema_upgrade(
            database_url=database_url,
            psql_bin=args.psql_bin,
        )
    else:
        payload = build_production_schema_plan()

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(f"mode={payload['mode']}")
        print(f"read_only={str(payload['read_only']).lower()}")
        for item in payload["included"]:
            print(
                f"include[{item['position']}]={item['name']} "
                f"sha256={item['sha256']} path={item['path']}"
            )
        for name, reason in payload["excluded"].items():
            print(f"exclude={name} reason={reason}")
        if payload["mode"] == "plan":
            print("No database connection was made. Pass --apply to execute.")
        else:
            print(f"applied_schema_count={payload['applied_schema_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
