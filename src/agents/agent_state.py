from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any


SAFETY_FLAGS: dict[str, bool] = {
    "did_persist_state": False,
    "did_write_agent_run": False,
    "did_write_agent_step": False,
    "did_schedule_background_work": False,
    "did_execute_scheduler": False,
    "did_execute_reporting_job": False,
    "did_export_files": False,
    "did_execute_application": False,
    "did_submit_application": False,
    "migration_required": False,
    "persistence_enabled": False,
}


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _plain_dict(value: Any) -> dict[str, Any]:
    return deepcopy(value) if isinstance(value, dict) else {}


def _plain_list(value: Any) -> list[Any]:
    return deepcopy(value) if isinstance(value, list) else []


def _deterministic_key(prefix: str, *parts: Any) -> str:
    cleaned_parts = [_clean_text(part) for part in parts]
    return ":".join([prefix, *cleaned_parts])


def safety_flags() -> dict[str, bool]:
    return dict(SAFETY_FLAGS)


@dataclass(frozen=True)
class JobApplicationContext:
    approval_request_id: str
    job_id: str
    candidate_key: str
    role_family: str
    run_mode: str
    observed_at_utc: str
    metadata: dict[str, Any] = field(default_factory=dict)
    context_id: str = ""

    @property
    def context_key(self) -> str:
        if _clean_text(self.context_id):
            return _clean_text(self.context_id)
        return _deterministic_key(
            "job_application_context",
            self.approval_request_id,
            self.job_id,
            self.candidate_key,
            self.run_mode,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "context_id": _clean_text(self.context_id),
            "context_key": self.context_key,
            "approval_request_id": _clean_text(self.approval_request_id),
            "job_id": _clean_text(self.job_id),
            "candidate_key": _clean_text(self.candidate_key),
            "role_family": _clean_text(self.role_family),
            "run_mode": _clean_text(self.run_mode),
            "observed_at_utc": _clean_text(self.observed_at_utc),
            "metadata": _plain_dict(self.metadata),
            **safety_flags(),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "JobApplicationContext":
        if not isinstance(payload, dict):
            raise ValueError("JobApplicationContext payload must be a dictionary.")
        return cls(
            approval_request_id=_clean_text(payload.get("approval_request_id")),
            job_id=_clean_text(payload.get("job_id")),
            candidate_key=_clean_text(
                payload.get("candidate_key") or payload.get("candidate_id")
            ),
            role_family=_clean_text(payload.get("role_family")),
            run_mode=_clean_text(payload.get("run_mode")),
            observed_at_utc=_clean_text(
                payload.get("observed_at_utc") or payload.get("created_at_utc")
            ),
            metadata=_plain_dict(payload.get("metadata")),
            context_id=_clean_text(payload.get("context_id")),
        )


def job_application_context_payload(**kwargs: Any) -> dict[str, Any]:
    return JobApplicationContext(**kwargs).to_dict()


def build_agent_run_snapshot(
    *,
    context: JobApplicationContext | dict[str, Any],
    agent_name: str,
    observed_at_utc: str,
    run_status: str = "ready",
    agent_run_id: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context_payload = (
        context.to_dict()
        if isinstance(context, JobApplicationContext)
        else JobApplicationContext.from_dict(context).to_dict()
    )
    run_key = _deterministic_key(
        "agent_run",
        context_payload["context_key"],
        agent_name,
        observed_at_utc,
    )
    resolved_run_id = _clean_text(agent_run_id) or run_key
    return {
        "agent_run_id": resolved_run_id,
        "agent_run_key": run_key,
        "context_key": context_payload["context_key"],
        "approval_request_id": context_payload["approval_request_id"],
        "job_id": context_payload["job_id"],
        "candidate_key": context_payload["candidate_key"],
        "agent_name": _clean_text(agent_name),
        "run_status": _clean_text(run_status),
        "observed_at_utc": _clean_text(observed_at_utc),
        "metadata": _plain_dict(metadata),
        **safety_flags(),
    }


def build_agent_step_snapshot(
    *,
    context: JobApplicationContext | dict[str, Any],
    agent_name: str,
    step_name: str,
    step_index: int,
    observed_at_utc: str,
    step_status: str = "ready",
    agent_run_id: str = "",
    agent_step_id: str = "",
    input_summary: dict[str, Any] | None = None,
    output_summary: dict[str, Any] | None = None,
    reason_codes: list[str] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    context_payload = (
        context.to_dict()
        if isinstance(context, JobApplicationContext)
        else JobApplicationContext.from_dict(context).to_dict()
    )
    run_id = _clean_text(agent_run_id) or _deterministic_key(
        "agent_run",
        context_payload["context_key"],
        agent_name,
        observed_at_utc,
    )
    step_key = _deterministic_key(
        "agent_step",
        context_payload["context_key"],
        agent_name,
        step_name,
        step_index,
    )
    return {
        "agent_step_id": _clean_text(agent_step_id) or step_key,
        "agent_step_key": step_key,
        "agent_run_id": run_id,
        "context_key": context_payload["context_key"],
        "approval_request_id": context_payload["approval_request_id"],
        "job_id": context_payload["job_id"],
        "candidate_key": context_payload["candidate_key"],
        "agent_name": _clean_text(agent_name),
        "step_name": _clean_text(step_name),
        "step_index": int(step_index),
        "step_status": _clean_text(step_status),
        "observed_at_utc": _clean_text(observed_at_utc),
        "input_summary": _plain_dict(input_summary),
        "output_summary": _plain_dict(output_summary),
        "reason_codes": _plain_list(reason_codes),
        "metadata": _plain_dict(metadata),
        **safety_flags(),
    }


def append_trace_step(
    trace_payload: dict[str, Any] | None,
    step_snapshot: dict[str, Any],
) -> dict[str, Any]:
    payload = _plain_dict(trace_payload)
    steps = _plain_list(payload.get("trace_steps"))
    steps.append(_plain_dict(step_snapshot))
    return {
        **payload,
        "trace_steps": steps,
        **safety_flags(),
    }
