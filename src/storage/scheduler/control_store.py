from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Callable, Dict, Iterator


SCHEDULER_AUTOMATION_AFFECTED_JOBS = (
    "agent_discovery",
    "live_pipeline",
)

# Two-key advisory-lock namespace reserved for scheduler automatic-start
# admission. Automatic starts take the shared variant; pause/resume mutations
# take the exclusive variant.
SCHEDULER_AUTOMATION_ADMISSION_LOCK_KEYS = (181, 1820)

_CURRENT_EVENT_SQL = """
SELECT
    revision,
    action,
    prior_paused,
    resulting_paused,
    changed_at,
    changed_by_user_id
FROM scheduler_automation_control_events
ORDER BY revision DESC
LIMIT 1
""".strip()

_INSERT_EVENT_SQL = """
INSERT INTO scheduler_automation_control_events (
    action,
    prior_paused,
    resulting_paused,
    changed_by_user_id
)
VALUES (%s, %s, %s, %s)
RETURNING
    revision,
    action,
    prior_paused,
    resulting_paused,
    changed_at,
    changed_by_user_id
""".strip()


class SchedulerAutomationControlUnavailable(RuntimeError):
    """Bounded failure when authoritative scheduler control cannot be verified."""


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _resolve_database_url(explicit_value: str, env_var_name: str) -> str:
    explicit = _clean_text(explicit_value)
    if explicit:
        return explicit

    env_name = _clean_text(env_var_name) or "DATABASE_URL"
    env_value = _clean_text(os.environ.get(env_name))
    if env_value:
        return env_value

    raise SchedulerAutomationControlUnavailable(
        "scheduler_automation_control_unavailable"
    )


def _default_connection_factory(database_url: str) -> Any:
    try:
        import psycopg  # type: ignore
    except ImportError as exc:
        raise SchedulerAutomationControlUnavailable(
            "scheduler_automation_control_unavailable"
        ) from exc
    return psycopg.connect(database_url)


def _timestamp_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    text = _clean_text(value)
    return text or None


def _default_state() -> Dict[str, Any]:
    return {
        "paused": False,
        "revision": 0,
        "updated_at": None,
        "updated_by_user_id": None,
        "paused_at": None,
        "paused_by_user_id": None,
        "affected_jobs": list(SCHEDULER_AUTOMATION_AFFECTED_JOBS),
        "manual_admin_runs_allowed": True,
    }


def _state_from_event(row: Any) -> Dict[str, Any]:
    if not row:
        return _default_state()

    if isinstance(row, dict):
        revision = row.get("revision")
        resulting_paused = row.get("resulting_paused")
        changed_at = row.get("changed_at")
        changed_by = row.get("changed_by_user_id")
    else:
        revision = row[0]
        resulting_paused = row[3]
        changed_at = row[4]
        changed_by = row[5]

    paused = bool(resulting_paused)
    changed_at_text = _timestamp_text(changed_at)
    changed_by_text = _clean_text(changed_by) or None
    return {
        "paused": paused,
        "revision": int(revision),
        "updated_at": changed_at_text,
        "updated_by_user_id": changed_by_text,
        "paused_at": changed_at_text if paused else None,
        "paused_by_user_id": changed_by_text if paused else None,
        "affected_jobs": list(SCHEDULER_AUTOMATION_AFFECTED_JOBS),
        "manual_admin_runs_allowed": True,
    }


def _read_current_state(cursor: Any) -> Dict[str, Any]:
    cursor.execute(_CURRENT_EVENT_SQL)
    return _state_from_event(cursor.fetchone())


def _close_connection(connection: Any) -> None:
    close = getattr(connection, "close", None)
    if callable(close):
        try:
            close()
        except Exception:
            pass


def read_scheduler_automation_control(
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    connection_factory: Callable[[str], Any] | None = None,
) -> Dict[str, Any]:
    resolved_url = _resolve_database_url(database_url, database_url_env)
    factory = connection_factory or _default_connection_factory
    connection = None
    try:
        connection = factory(resolved_url)
        with connection.cursor() as cursor:
            state = _read_current_state(cursor)
        rollback = getattr(connection, "rollback", None)
        if callable(rollback):
            rollback()
        return state
    except SchedulerAutomationControlUnavailable:
        raise
    except Exception as exc:
        raise SchedulerAutomationControlUnavailable(
            "scheduler_automation_control_unavailable"
        ) from exc
    finally:
        if connection is not None:
            _close_connection(connection)


def set_scheduler_automation_paused(
    paused: bool,
    *,
    changed_by_user_id: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    connection_factory: Callable[[str], Any] | None = None,
) -> Dict[str, Any]:
    if not isinstance(paused, bool):
        raise ValueError("paused must be a boolean.")
    actor_user_id = _clean_text(changed_by_user_id)
    if not actor_user_id:
        raise ValueError("changed_by_user_id is required.")

    resolved_url = _resolve_database_url(database_url, database_url_env)
    factory = connection_factory or _default_connection_factory
    connection = None
    try:
        connection = factory(resolved_url)
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT pg_advisory_xact_lock(%s, %s)",
                SCHEDULER_AUTOMATION_ADMISSION_LOCK_KEYS,
            )
            previous_state = _read_current_state(cursor)
            previous_paused = bool(previous_state["paused"])
            if previous_paused == paused:
                connection.commit()
                return {
                    "ok": True,
                    "changed": False,
                    "previous_paused": previous_paused,
                    "automation_control": previous_state,
                }

            cursor.execute(
                _INSERT_EVENT_SQL,
                (
                    "pause" if paused else "resume",
                    previous_paused,
                    paused,
                    actor_user_id,
                ),
            )
            inserted_state = _state_from_event(cursor.fetchone())
        connection.commit()
        return {
            "ok": True,
            "changed": True,
            "previous_paused": previous_paused,
            "automation_control": inserted_state,
        }
    except SchedulerAutomationControlUnavailable:
        raise
    except Exception as exc:
        if connection is not None:
            rollback = getattr(connection, "rollback", None)
            if callable(rollback):
                try:
                    rollback()
                except Exception:
                    pass
        raise SchedulerAutomationControlUnavailable(
            "scheduler_automation_control_unavailable"
        ) from exc
    finally:
        if connection is not None:
            _close_connection(connection)


@contextmanager
def automatic_scheduler_start_admission(
    *,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    connection_factory: Callable[[str], Any] | None = None,
) -> Iterator[Dict[str, Any]]:
    """Hold shared admission until the caller either skips or spawns its child."""
    resolved_url = _resolve_database_url(database_url, database_url_env)
    factory = connection_factory or _default_connection_factory
    connection = None
    try:
        connection = factory(resolved_url)
        cursor = connection.cursor()
        cursor.execute(
            "SELECT pg_advisory_xact_lock_shared(%s, %s)",
            SCHEDULER_AUTOMATION_ADMISSION_LOCK_KEYS,
        )
        state = _read_current_state(cursor)
    except SchedulerAutomationControlUnavailable:
        if connection is not None:
            _close_connection(connection)
        raise
    except Exception as exc:
        if connection is not None:
            _close_connection(connection)
        raise SchedulerAutomationControlUnavailable(
            "scheduler_automation_control_unavailable"
        ) from exc

    try:
        yield state
    finally:
        rollback = getattr(connection, "rollback", None)
        if callable(rollback):
            try:
                rollback()
            except Exception:
                pass
        try:
            cursor.close()
        except Exception:
            pass
        try:
            _close_connection(connection)
        except Exception:
            pass
