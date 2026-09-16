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

_EFFECTIVE_EVENT_FOR_JOB_SQL = """
SELECT
    revision,
    action,
    prior_paused,
    resulting_paused,
    changed_at,
    changed_by_user_id,
    job_name
FROM scheduler_automation_control_events
WHERE job_name IS NULL OR job_name = %s
ORDER BY revision DESC
LIMIT 1
""".strip()

_EFFECTIVE_EVENTS_FOR_ALL_JOBS_SQL = """
WITH supported_jobs(job_name, sort_order) AS (
    VALUES
        ('agent_discovery', 1),
        ('live_pipeline', 2)
)
SELECT
    supported_jobs.job_name,
    event.revision,
    event.action,
    event.prior_paused,
    event.resulting_paused,
    event.changed_at,
    event.changed_by_user_id,
    event.job_name AS event_job_name
FROM supported_jobs
LEFT JOIN LATERAL (
    SELECT
        revision,
        action,
        prior_paused,
        resulting_paused,
        changed_at,
        changed_by_user_id,
        job_name
    FROM scheduler_automation_control_events
    WHERE job_name IS NULL OR job_name = supported_jobs.job_name
    ORDER BY revision DESC
    LIMIT 1
) AS event ON TRUE
ORDER BY supported_jobs.sort_order
""".strip()

_INSERT_EVENT_SQL = """
INSERT INTO scheduler_automation_control_events (
    job_name,
    action,
    prior_paused,
    resulting_paused,
    changed_by_user_id
)
VALUES (%s, %s, %s, %s, %s)
RETURNING
    revision,
    action,
    prior_paused,
    resulting_paused,
    changed_at,
    changed_by_user_id,
    job_name
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


def _validate_job_name(job_name: Any) -> str:
    if not isinstance(job_name, str) or job_name not in SCHEDULER_AUTOMATION_AFFECTED_JOBS:
        raise ValueError("Unsupported scheduler job name.")
    return job_name


def _default_job_state(job_name: str) -> Dict[str, Any]:
    return {
        "job_name": job_name,
        "paused": False,
        "revision": 0,
        "updated_at": None,
        "updated_by_user_id": None,
        "paused_at": None,
        "paused_by_user_id": None,
        "effective_scope": "default",
    }


def _job_state_from_event(row: Any, job_name: str) -> Dict[str, Any]:
    if not row:
        return _default_job_state(job_name)

    if isinstance(row, dict):
        revision = row.get("revision")
        resulting_paused = row.get("resulting_paused")
        changed_at = row.get("changed_at")
        changed_by = row.get("changed_by_user_id")
        event_job_name = row.get("job_name", row.get("event_job_name"))
    else:
        revision = row[0]
        resulting_paused = row[3]
        changed_at = row[4]
        changed_by = row[5]
        event_job_name = row[6]

    paused = bool(resulting_paused)
    changed_at_text = _timestamp_text(changed_at)
    changed_by_text = _clean_text(changed_by) or None
    return {
        "job_name": job_name,
        "paused": paused,
        "revision": int(revision),
        "updated_at": changed_at_text,
        "updated_by_user_id": changed_by_text,
        "paused_at": changed_at_text if paused else None,
        "paused_by_user_id": changed_by_text if paused else None,
        "effective_scope": "global" if event_job_name is None else "job",
    }


def _aggregate_control_state(job_states: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    ordered_states = [job_states[name] for name in SCHEDULER_AUTOMATION_AFFECTED_JOBS]
    paused_count = sum(1 for state in ordered_states if state["paused"])
    aggregate_state = (
        "running"
        if paused_count == 0
        else "paused"
        if paused_count == len(ordered_states)
        else "partially_paused"
    )
    latest_state = ordered_states[0]
    for state in ordered_states[1:]:
        if state["revision"] > latest_state["revision"]:
            latest_state = state

    fully_paused = aggregate_state == "paused"
    return {
        "aggregate_state": aggregate_state,
        "manual_admin_runs_allowed": True,
        "affected_jobs": list(SCHEDULER_AUTOMATION_AFFECTED_JOBS),
        "jobs": {name: dict(job_states[name]) for name in SCHEDULER_AUTOMATION_AFFECTED_JOBS},
        "paused": fully_paused,
        "revision": latest_state["revision"],
        "updated_at": latest_state["updated_at"],
        "updated_by_user_id": latest_state["updated_by_user_id"],
        "paused_at": latest_state["paused_at"] if fully_paused else None,
        "paused_by_user_id": latest_state["paused_by_user_id"] if fully_paused else None,
    }


def _read_effective_state_for_job(cursor: Any, job_name: str) -> Dict[str, Any]:
    canonical_job_name = _validate_job_name(job_name)
    cursor.execute(_EFFECTIVE_EVENT_FOR_JOB_SQL, (canonical_job_name,))
    return _job_state_from_event(cursor.fetchone(), canonical_job_name)


def _read_all_states(cursor: Any) -> Dict[str, Any]:
    cursor.execute(_EFFECTIVE_EVENTS_FOR_ALL_JOBS_SQL)
    rows = cursor.fetchall()
    row_by_job: Dict[str, Any] = {}
    for row in rows:
        if isinstance(row, dict):
            job_name = row.get("job_name")
            event_row = {
                "revision": row.get("revision"),
                "resulting_paused": row.get("resulting_paused"),
                "changed_at": row.get("changed_at"),
                "changed_by_user_id": row.get("changed_by_user_id"),
                "event_job_name": row.get("event_job_name"),
            }
        else:
            job_name = row[0]
            event_row = None if row[1] is None else row[1:]
        if job_name in SCHEDULER_AUTOMATION_AFFECTED_JOBS:
            row_by_job[job_name] = event_row

    return _aggregate_control_state({
        job_name: _job_state_from_event(row_by_job.get(job_name), job_name)
        for job_name in SCHEDULER_AUTOMATION_AFFECTED_JOBS
    })


def _insert_named_event(
    cursor: Any,
    *,
    job_name: str,
    paused: bool,
    prior_paused: bool,
    actor_user_id: str,
) -> None:
    cursor.execute(
        _INSERT_EVENT_SQL,
        (
            job_name,
            "pause" if paused else "resume",
            prior_paused,
            paused,
            actor_user_id,
        ),
    )
    cursor.fetchone()


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
            state = _read_all_states(cursor)
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
            previous_state = _read_all_states(cursor)
            previous_paused = bool(previous_state["paused"])
            changed_jobs = [
                job_name
                for job_name in SCHEDULER_AUTOMATION_AFFECTED_JOBS
                if bool(previous_state["jobs"][job_name]["paused"]) != paused
            ]
            if not changed_jobs:
                connection.commit()
                return {
                    "ok": True,
                    "changed": False,
                    "previous_paused": previous_paused,
                    "automation_control": previous_state,
                }

            for job_name in changed_jobs:
                _insert_named_event(
                    cursor,
                    job_name=job_name,
                    paused=paused,
                    prior_paused=bool(previous_state["jobs"][job_name]["paused"]),
                    actor_user_id=actor_user_id,
                )
            inserted_state = _read_all_states(cursor)
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


def set_scheduler_job_automation_paused(
    job_name: str,
    paused: bool,
    *,
    changed_by_user_id: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    connection_factory: Callable[[str], Any] | None = None,
) -> Dict[str, Any]:
    canonical_job_name = _validate_job_name(job_name)
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
            previous_state = _read_effective_state_for_job(cursor, canonical_job_name)
            previous_paused = bool(previous_state["paused"])
            if previous_paused != paused:
                _insert_named_event(
                    cursor,
                    job_name=canonical_job_name,
                    paused=paused,
                    prior_paused=previous_paused,
                    actor_user_id=actor_user_id,
                )
            authoritative_state = _read_all_states(cursor)
        connection.commit()
        return {
            "ok": True,
            "changed": previous_paused != paused,
            "job_name": canonical_job_name,
            "previous_paused": previous_paused,
            "automation_control": authoritative_state,
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
    job_name: str,
    database_url: str = "",
    database_url_env: str = "DATABASE_URL",
    connection_factory: Callable[[str], Any] | None = None,
) -> Iterator[Dict[str, Any]]:
    """Hold shared admission until the caller either skips or spawns its child."""
    canonical_job_name = _validate_job_name(job_name)
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
        state = _read_effective_state_for_job(cursor, canonical_job_name)
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
