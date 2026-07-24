"""Explicit Psycopg connection factory for durable orchestration.

Importing this module opens no connection and reads no environment. Callers
must supply an explicit target and enable the factory before use.
"""

from __future__ import annotations

from typing import Any, Callable
from urllib.parse import urlsplit

import psycopg
from psycopg.rows import dict_row


DEFAULT_CONNECT_TIMEOUT_SECONDS = 5
MAX_CONNECT_TIMEOUT_SECONDS = 30
DEFAULT_STATEMENT_TIMEOUT_MS = 5_000
MAX_STATEMENT_TIMEOUT_MS = 60_000
DEFAULT_APPLICATION_NAME = "applylens-durable-orchestration-runtime"
MAX_APPLICATION_NAME_BYTES = 63
SUPPORTED_SSL_MODES = frozenset(
    {"disable", "allow", "prefer", "require", "verify-ca", "verify-full"}
)

PostgresConnectionFactory = Callable[[], Any]


class PostgresConnectionFactoryError(RuntimeError):
    """Bounded configuration or connection failure without target details."""


def _bounded_positive_int(
    value: Any,
    *,
    field_name: str,
    maximum: int,
) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise PostgresConnectionFactoryError(
            f"durable_orchestration_postgres_connection:{field_name}_invalid"
        )
    if value < 1 or value > maximum:
        raise PostgresConnectionFactoryError(
            f"durable_orchestration_postgres_connection:{field_name}_invalid"
        )
    return value


def _validated_database_url(value: Any) -> str:
    target = str(value or "").strip()
    if not target:
        raise PostgresConnectionFactoryError(
            "durable_orchestration_postgres_connection:database_url_missing"
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
        raise PostgresConnectionFactoryError(
            "durable_orchestration_postgres_connection:database_url_invalid"
        )
    return target


def _validated_application_name(value: Any) -> str:
    application_name = str(value or "").strip()
    if (
        not application_name
        or "\x00" in application_name
        or len(application_name.encode("utf-8")) > MAX_APPLICATION_NAME_BYTES
    ):
        raise PostgresConnectionFactoryError(
            "durable_orchestration_postgres_connection:"
            "application_name_invalid"
        )
    return application_name


def _validated_ssl_mode(value: Any) -> str | None:
    if value is None:
        return None
    ssl_mode = str(value).strip().lower()
    if ssl_mode not in SUPPORTED_SSL_MODES:
        raise PostgresConnectionFactoryError(
            "durable_orchestration_postgres_connection:ssl_mode_invalid"
        )
    return ssl_mode


def build_postgres_connection_factory(
    *,
    enabled: bool = False,
    database_url: str = "",
    connect_timeout_seconds: int = DEFAULT_CONNECT_TIMEOUT_SECONDS,
    statement_timeout_ms: int = DEFAULT_STATEMENT_TIMEOUT_MS,
    application_name: str = DEFAULT_APPLICATION_NAME,
    ssl_mode: str | None = None,
) -> PostgresConnectionFactory:
    """Build a new-connection-per-call Psycopg factory."""

    if enabled is not True:
        raise PostgresConnectionFactoryError(
            "durable_orchestration_postgres_connection:capability_disabled"
        )
    target = _validated_database_url(database_url)
    connection_timeout = _bounded_positive_int(
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

    def connection_factory() -> Any:
        options = {
            "autocommit": False,
            "row_factory": dict_row,
            "connect_timeout": connection_timeout,
            "options": f"-c statement_timeout={statement_timeout}",
            "application_name": bounded_application_name,
        }
        if explicit_ssl_mode is not None:
            options["sslmode"] = explicit_ssl_mode
        try:
            return psycopg.connect(target, **options)
        except Exception:
            raise PostgresConnectionFactoryError(
                "durable_orchestration_postgres_connection:"
                "connection_failed"
            ) from None

    return connection_factory


__all__ = [
    "DEFAULT_APPLICATION_NAME",
    "DEFAULT_CONNECT_TIMEOUT_SECONDS",
    "DEFAULT_STATEMENT_TIMEOUT_MS",
    "MAX_APPLICATION_NAME_BYTES",
    "MAX_CONNECT_TIMEOUT_SECONDS",
    "MAX_STATEMENT_TIMEOUT_MS",
    "PostgresConnectionFactory",
    "PostgresConnectionFactoryError",
    "SUPPORTED_SSL_MODES",
    "build_postgres_connection_factory",
]
