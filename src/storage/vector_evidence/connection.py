"""Explicit, default-off connection provider for vector evidence pgvector use.

Importing this module reads no environment and opens no connection. A caller
must explicitly build the provider, enable it, and supply usable database
configuration. No schema, query, write, commit, embedding, or provider call is
performed here.
"""

from __future__ import annotations

import importlib
import os
from typing import Any, Callable, Mapping


PGVECTOR_ENABLED_ENV = "APPLYLENS_VECTOR_EVIDENCE_PGVECTOR_ENABLED"
PGVECTOR_DATABASE_URL_ENV = "APPLYLENS_VECTOR_EVIDENCE_DATABASE_URL"
DEFAULT_DATABASE_URL_ENV = "DATABASE_URL"
CONNECTION_PROVIDER_VERSION = "phase-8r-pgvector-connection-provider-v1"

Connector = Callable[[str], Any]

_TRUE_VALUES = {"1", "true", "yes", "on", "enabled"}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _enabled_value(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return _clean_text(value).lower() in _TRUE_VALUES


def pgvector_connection_provider_safety_metadata(
    *,
    db_connection_opened: bool = False,
    db_executor_created: bool = False,
) -> dict[str, bool]:
    return {
        "read_only": True,
        "advisory_only": True,
        "pgvector_connection_provider": True,
        "default_off": True,
        "db_connection_opened": bool(db_connection_opened),
        "db_executor_created": bool(db_executor_created),
        "schema_setup_executed": False,
        "chunks_written": False,
        "embeddings_written": False,
        "retrieval_events_written": False,
        "embeddings_created": False,
        "provider_calls_made": False,
        "did_read_database": False,
        "did_write_database": False,
        "did_mutate_scoring": False,
        "did_change_ranking": False,
        "did_mutate_queue": False,
        "did_create_approval": False,
        "did_mutate_approval": False,
        "did_mutate_resume": False,
        "did_create_execution_request": False,
        "did_create_execution_launch_request": False,
        "did_execute_application": False,
        "did_submit_application": False,
        "pipeline_stage_added": False,
        "auto_apply_enabled": False,
        "mutation_authorized": False,
    }


def vector_evidence_pgvector_connection_config_from_env(
    *,
    environ: Mapping[str, str] | None = None,
    enabled: bool | None = None,
    database_url: str = "",
) -> dict[str, Any]:
    """Resolve explicit vector configuration without opening a connection."""

    source = os.environ if environ is None else environ
    enabled_value = (
        _enabled_value(source.get(PGVECTOR_ENABLED_ENV, ""))
        if enabled is None
        else bool(enabled)
    )
    explicit_url = _clean_text(database_url)
    namespaced_url = _clean_text(source.get(PGVECTOR_DATABASE_URL_ENV, ""))
    shared_url = _clean_text(source.get(DEFAULT_DATABASE_URL_ENV, ""))
    resolved_url = explicit_url or namespaced_url or shared_url
    if explicit_url:
        database_url_source = "explicit"
    elif namespaced_url:
        database_url_source = PGVECTOR_DATABASE_URL_ENV
    elif shared_url:
        database_url_source = DEFAULT_DATABASE_URL_ENV
    else:
        database_url_source = ""

    status = "pgvector_connection_provider_disabled"
    if enabled_value and not resolved_url:
        status = "pgvector_connection_provider_missing_config"
    elif enabled_value:
        status = "pgvector_connection_provider_configured"

    return {
        "provider_version": CONNECTION_PROVIDER_VERSION,
        "status": status,
        "enabled": enabled_value,
        "default_off": True,
        "database_url_configured": bool(resolved_url),
        "database_url_source": database_url_source,
        "database_url": resolved_url,
        "safety_metadata": pgvector_connection_provider_safety_metadata(),
    }


def _existing_postgres_connector() -> tuple[str, Connector] | None:
    """Load the repository's existing optional DB-API driver convention."""

    for driver_name in ("psycopg", "psycopg2"):
        try:
            driver = importlib.import_module(driver_name)
        except ImportError:
            continue
        connect = getattr(driver, "connect", None)
        if callable(connect):
            return driver_name, connect
    return None


def _provider_payload(
    *,
    status: str,
    config: dict[str, Any],
    driver: str = "",
    connection: Any = None,
    error: str = "",
) -> dict[str, Any]:
    opened = connection is not None
    return {
        "provider_version": CONNECTION_PROVIDER_VERSION,
        "status": status,
        "enabled": bool(config.get("enabled")),
        "default_off": True,
        "database_url_configured": bool(
            config.get("database_url_configured")
        ),
        "database_url_source": str(
            config.get("database_url_source", "") or ""
        ),
        "driver": driver,
        "connection": connection,
        "db_executor": connection,
        "db_connection_opened": opened,
        "db_executor_created": opened,
        "error": error,
        "provider_backed_automated_agents": 0,
        "live_provider_backed_automated_agents": 0,
        "mutation_authorized_agents": 0,
        "mutation_authorized_scoring_agents": 0,
        "mutation_authorized_ranking_agents": 0,
        "mutation_authorized_application_agents": 0,
        "safety_metadata": pgvector_connection_provider_safety_metadata(
            db_connection_opened=opened,
            db_executor_created=opened,
        ),
    }


def build_vector_evidence_db_executor(
    *,
    enabled: bool | None = None,
    database_url: str = "",
    environ: Mapping[str, str] | None = None,
    connector: Connector | None = None,
) -> dict[str, Any]:
    """Open one connection only when explicitly enabled and configured."""

    config = vector_evidence_pgvector_connection_config_from_env(
        environ=environ,
        enabled=enabled,
        database_url=database_url,
    )
    if not config["enabled"]:
        return _provider_payload(
            status="pgvector_connection_provider_disabled",
            config=config,
        )
    if not config["database_url_configured"]:
        return _provider_payload(
            status="pgvector_connection_provider_missing_config",
            config=config,
        )

    selected_connector = connector
    driver_name = "injected"
    if selected_connector is None:
        existing = _existing_postgres_connector()
        if existing is None:
            return _provider_payload(
                status="pgvector_connection_provider_driver_unavailable",
                config=config,
                error="psycopg_or_psycopg2_required",
            )
        driver_name, selected_connector = existing

    try:
        connection = selected_connector(config["database_url"])
    except Exception as exc:
        return _provider_payload(
            status="pgvector_connection_provider_failed_non_blocking",
            config=config,
            driver=driver_name,
            error=type(exc).__name__,
        )
    if connection is None:
        return _provider_payload(
            status="pgvector_connection_provider_failed_non_blocking",
            config=config,
            driver=driver_name,
            error="connector_returned_no_connection",
        )
    return _provider_payload(
        status="pgvector_connection_provider_ready",
        config=config,
        driver=driver_name,
        connection=connection,
    )
