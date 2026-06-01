from __future__ import annotations

from typing import Any, Dict

from src.storage.agent_trace.store import (
    complete_agent_run_postgres_payload,
    complete_agent_step_postgres_payload,
    create_agent_run_postgres_payload,
    fail_agent_run_postgres_payload,
    fail_agent_step_postgres_payload,
    get_agent_run_postgres_payload,
    list_agent_runs_postgres_payload,
    list_agent_steps_postgres_payload,
    record_agent_step_postgres_payload,
)


def create_agent_run(**kwargs: Any) -> Dict[str, Any]:
    return create_agent_run_postgres_payload(**kwargs)


def complete_agent_run(**kwargs: Any) -> Dict[str, Any]:
    return complete_agent_run_postgres_payload(**kwargs)


def fail_agent_run(**kwargs: Any) -> Dict[str, Any]:
    return fail_agent_run_postgres_payload(**kwargs)


def record_agent_step(**kwargs: Any) -> Dict[str, Any]:
    return record_agent_step_postgres_payload(**kwargs)


def complete_agent_step(**kwargs: Any) -> Dict[str, Any]:
    return complete_agent_step_postgres_payload(**kwargs)


def fail_agent_step(**kwargs: Any) -> Dict[str, Any]:
    return fail_agent_step_postgres_payload(**kwargs)


def get_agent_run(**kwargs: Any) -> Dict[str, Any]:
    return get_agent_run_postgres_payload(**kwargs)


def list_agent_runs(**kwargs: Any) -> Dict[str, Any]:
    return list_agent_runs_postgres_payload(**kwargs)


def list_agent_steps(**kwargs: Any) -> Dict[str, Any]:
    return list_agent_steps_postgres_payload(**kwargs)
