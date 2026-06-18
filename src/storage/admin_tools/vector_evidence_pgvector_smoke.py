from __future__ import annotations

"""Run manually with:

APPLYLENS_VECTOR_EVIDENCE_PGVECTOR_ENABLED=true \
APPLYLENS_VECTOR_EVIDENCE_DATABASE_URL="$DATABASE_URL" \
python -m src.storage.admin_tools.vector_evidence_pgvector_smoke \
  --owner-user-id "<existing-auth-user-id>"
"""

import argparse
import json
import os
from typing import Any, Mapping

from src.storage.vector_evidence import connection, smoke


OWNER_USER_ID_ENV = "APPLYLENS_VECTOR_EVIDENCE_OWNER_USER_ID"


def _command_payload(
    *,
    status: str,
    provider_status: str,
    smoke_payload: dict[str, Any] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    result = smoke_payload if isinstance(smoke_payload, dict) else {}
    safety_metadata = dict(result.get("safety_metadata", {}) or {})
    if not safety_metadata:
        safety_metadata = smoke.pgvector_local_smoke_safety_metadata()
    return {
        "status": status,
        "connection_provider_status": provider_status,
        "schema_setup_status": (
            "executed"
            if result.get("schema_setup_executed") is True
            else "not_executed"
        ),
        "chunk_insert_status": (
            "executed"
            if result.get("chunk_insert_executed") is True
            else "not_executed"
        ),
        "retrieval_event_insert_status": (
            "executed"
            if result.get("retrieval_event_insert_executed") is True
            else "not_executed"
        ),
        "errors": list(errors or result.get("errors", []) or []),
        "safety_metadata": safety_metadata,
        "smoke_payload": result,
    }


def run_pgvector_real_local_smoke_command(
    *,
    owner_user_id: str = "",
    database_url: str = "",
    environ: Mapping[str, str] | None = None,
    connector: Any = None,
) -> dict[str, Any]:
    """Preflight configuration and explicitly invoke the local smoke helper."""

    source = os.environ if environ is None else environ
    config = connection.vector_evidence_pgvector_connection_config_from_env(
        environ=source,
        database_url=database_url,
    )
    if config["enabled"] is not True:
        skipped = smoke.run_vector_evidence_pgvector_smoke(enabled=False)
        return _command_payload(
            status="pgvector_real_local_smoke_skipped_default_off",
            provider_status=str(config["status"]),
            smoke_payload=skipped,
        )
    if config["database_url_configured"] is not True:
        return _command_payload(
            status="pgvector_real_local_smoke_missing_config",
            provider_status=str(config["status"]),
            errors=["database_url_required"],
        )

    safe_owner_user_id = (
        str(owner_user_id or "").strip()
        or str(source.get(OWNER_USER_ID_ENV, "") or "").strip()
    )
    if not safe_owner_user_id:
        return _command_payload(
            status="pgvector_real_local_smoke_missing_owner",
            provider_status=str(config["status"]),
            errors=["owner_user_id_required"],
        )

    selected_connector = connector
    if selected_connector is None:
        existing = connection._existing_postgres_connector()
        if existing is None:
            return _command_payload(
                status="pgvector_real_local_smoke_driver_unavailable",
                provider_status=(
                    "pgvector_connection_provider_driver_unavailable"
                ),
                errors=["psycopg_or_psycopg2_required"],
            )
        _, selected_connector = existing

    result = smoke.run_vector_evidence_pgvector_smoke(
        enabled=True,
        owner_user_id=safe_owner_user_id,
        database_url=str(config["database_url"]),
        environ=source,
        connector=selected_connector,
    )
    provider_status = (
        "pgvector_connection_provider_ready"
        if result.get("db_connection_opened") is True
        else str(config["status"])
    )
    return _command_payload(
        status=str(result.get("status", "") or "pgvector_real_local_smoke_failed"),
        provider_status=provider_status,
        smoke_payload=result,
    )


def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Explicitly run the local vector-evidence pgvector smoke. "
            "Disabled unless APPLYLENS_VECTOR_EVIDENCE_PGVECTOR_ENABLED=true."
        )
    )
    parser.add_argument(
        "--owner-user-id",
        default="",
        help=(
            "Existing auth_users.user_id. Falls back to "
            f"{OWNER_USER_ID_ENV}."
        ),
    )
    parser.add_argument(
        "--database-url",
        default="",
        help=(
            "Explicit Postgres URL. Otherwise use "
            "APPLYLENS_VECTOR_EVIDENCE_DATABASE_URL or DATABASE_URL."
        ),
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv)
    payload = run_pgvector_real_local_smoke_command(
        owner_user_id=args.owner_user_id,
        database_url=args.database_url,
    )
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))
    return 0 if payload["status"] in {
        "pgvector_real_local_smoke_skipped_default_off",
        "pgvector_real_local_smoke_missing_config",
        "pgvector_real_local_smoke_missing_owner",
        "pgvector_local_smoke_completed",
    } else 1


if __name__ == "__main__":
    raise SystemExit(main())
