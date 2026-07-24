"""Explicit synchronous PostgreSQL saver owner for LangGraph checkpoints.

Importing this module reads no environment and opens no connection. Callers
must provide an explicit target and opt in for each bounded resource scope.
Schema setup is owned by the separate administrative setup tool.
"""

from __future__ import annotations

from contextlib import contextmanager
import re
from typing import Any, Iterator
from urllib.parse import urlsplit

from langgraph.checkpoint.postgres import PostgresSaver
import psycopg
from psycopg.rows import dict_row


LANGGRAPH_POSTGRES_SCHEMA = "applylens_langgraph_checkpoint"
DEFAULT_CONNECT_TIMEOUT_SECONDS = 5
MAX_CONNECT_TIMEOUT_SECONDS = 30
DEFAULT_STATEMENT_TIMEOUT_MS = 5_000
MAX_STATEMENT_TIMEOUT_MS = 60_000
DEFAULT_APPLICATION_NAME = "applylens-langgraph-checkpointer"
MAX_APPLICATION_NAME_BYTES = 63
SUPPORTED_SSL_MODES = frozenset(
    {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
)


class LangGraphPostgresSaverError(RuntimeError):
    """Bounded saver configuration or connection error."""


def _bounded_positive_int(
    value: Any,
    *,
    field_name: str,
    maximum: int,
) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value < 1
        or value > maximum
    ):
        raise LangGraphPostgresSaverError(
            f"langgraph_postgres_saver:{field_name}_invalid"
        )
    return value


def _validated_database_url(value: Any) -> str:
    target = str(value or "").strip()
    if not target:
        raise LangGraphPostgresSaverError(
            "langgraph_postgres_saver:database_url_missing"
        )
    try:
        parsed = urlsplit(target)
        valid = (
            parsed.scheme.lower() in {"postgres", "postgresql"}
            and bool(parsed.hostname)
            and bool(parsed.path.strip("/"))
            and not parsed.fragment
        )
    except (TypeError, ValueError):
        valid = False
    if not valid:
        raise LangGraphPostgresSaverError(
            "langgraph_postgres_saver:database_url_invalid"
        )
    return target


def _validated_schema(value: Any) -> str:
    schema = str(value or "").strip()
    if schema != LANGGRAPH_POSTGRES_SCHEMA:
        raise LangGraphPostgresSaverError(
            "langgraph_postgres_saver:schema_unsupported"
        )
    return schema


def _validated_application_name(value: Any) -> str:
    application_name = str(value or "").strip()
    if (
        not application_name
        or "\x00" in application_name
        or len(application_name.encode("utf-8")) > MAX_APPLICATION_NAME_BYTES
    ):
        raise LangGraphPostgresSaverError(
            "langgraph_postgres_saver:application_name_invalid"
        )
    return application_name


def _validated_ssl_mode(value: Any) -> str | None:
    if value is None:
        return None
    ssl_mode = str(value).strip().lower()
    if ssl_mode not in SUPPORTED_SSL_MODES:
        raise LangGraphPostgresSaverError(
            "langgraph_postgres_saver:ssl_mode_invalid"
        )
    return ssl_mode


def _connection_options(
    *,
    schema: str,
    statement_timeout_ms: int,
) -> str:
    if re.fullmatch(r"[a-z][a-z0-9_]{0,62}", schema) is None:
        raise LangGraphPostgresSaverError(
            "langgraph_postgres_saver:schema_unsupported"
        )
    return (
        f"-c statement_timeout={statement_timeout_ms} "
        f"-c search_path={schema}"
    )


@contextmanager
def open_langgraph_postgres_connection(
    *,
    enabled: bool = False,
    database_url: str = "",
    schema: str = LANGGRAPH_POSTGRES_SCHEMA,
    connect_timeout_seconds: int = DEFAULT_CONNECT_TIMEOUT_SECONDS,
    statement_timeout_ms: int = DEFAULT_STATEMENT_TIMEOUT_MS,
    application_name: str = DEFAULT_APPLICATION_NAME,
    ssl_mode: str | None = None,
) -> Iterator[Any]:
    """Open one saver-compatible Psycopg connection in the dedicated schema."""

    if enabled is not True:
        raise LangGraphPostgresSaverError(
            "langgraph_postgres_saver:capability_disabled"
        )
    target = _validated_database_url(database_url)
    bounded_schema = _validated_schema(schema)
    connect_timeout = _bounded_positive_int(
        connect_timeout_seconds,
        field_name="connect_timeout",
        maximum=MAX_CONNECT_TIMEOUT_SECONDS,
    )
    statement_timeout = _bounded_positive_int(
        statement_timeout_ms,
        field_name="statement_timeout",
        maximum=MAX_STATEMENT_TIMEOUT_MS,
    )
    bounded_application_name = _validated_application_name(application_name)
    explicit_ssl_mode = _validated_ssl_mode(ssl_mode)
    options: dict[str, Any] = {
        "autocommit": True,
        "prepare_threshold": 0,
        "row_factory": dict_row,
        "connect_timeout": connect_timeout,
        "options": _connection_options(
            schema=bounded_schema,
            statement_timeout_ms=statement_timeout,
        ),
        "application_name": bounded_application_name,
    }
    if explicit_ssl_mode is not None:
        options["sslmode"] = explicit_ssl_mode

    connection = None
    try:
        connection = psycopg.connect(target, **options)
    except Exception:
        raise LangGraphPostgresSaverError(
            "langgraph_postgres_saver:connection_failed"
        ) from None
    try:
        yield connection
    finally:
        try:
            connection.close()
        except Exception:
            pass


@contextmanager
def open_langgraph_postgres_saver(
    *,
    enabled: bool = False,
    database_url: str = "",
    schema: str = LANGGRAPH_POSTGRES_SCHEMA,
    connect_timeout_seconds: int = DEFAULT_CONNECT_TIMEOUT_SECONDS,
    statement_timeout_ms: int = DEFAULT_STATEMENT_TIMEOUT_MS,
    application_name: str = DEFAULT_APPLICATION_NAME,
    ssl_mode: str | None = None,
) -> Iterator[PostgresSaver]:
    """Own one saver and its connection; never run setup or graph code."""

    with open_langgraph_postgres_connection(
        enabled=enabled,
        database_url=database_url,
        schema=schema,
        connect_timeout_seconds=connect_timeout_seconds,
        statement_timeout_ms=statement_timeout_ms,
        application_name=application_name,
        ssl_mode=ssl_mode,
    ) as connection:
        yield PostgresSaver(connection)


__all__ = [
    "DEFAULT_APPLICATION_NAME",
    "DEFAULT_CONNECT_TIMEOUT_SECONDS",
    "DEFAULT_STATEMENT_TIMEOUT_MS",
    "LANGGRAPH_POSTGRES_SCHEMA",
    "LangGraphPostgresSaverError",
    "MAX_APPLICATION_NAME_BYTES",
    "MAX_CONNECT_TIMEOUT_SECONDS",
    "MAX_STATEMENT_TIMEOUT_MS",
    "SUPPORTED_SSL_MODES",
    "open_langgraph_postgres_connection",
    "open_langgraph_postgres_saver",
]
