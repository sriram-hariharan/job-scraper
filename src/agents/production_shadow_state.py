"""Bounded state contract for the artifact-only production shadow graph."""

from __future__ import annotations

from copy import deepcopy
import json
import re
from typing import Any, Dict, Mapping, TypedDict


PRODUCTION_SHADOW_STATE_VERSION = "production-shadow-artifact-state-v3"
_IDENTITY = re.compile(r"[A-Za-z0-9_.:@/-]{1,200}")
_PROHIBITED_KEYS = {
    "resume_text",
    "job_description",
    "job_description_text",
    "generated_tailoring",
    "generated_tailoring_content",
    "raw_provider_output",
    "normalized_provider_output",
    "prompt",
    "prompts",
    "reasoning",
    "credential",
    "credentials",
    "database_url",
    "application_state",
    "ats_state",
}
_ALLOWED_TOP_LEVEL = {
    "graph_state_schema_version",
    "owner_user_id",
    "pipeline_run_id",
    "context_id",
    "graph_invocation_id",
    "job_id",
    "job_index",
    "selected_resume_id",
    "authoritative_artifacts",
    "authoritative_projection",
    "queue_rank",
    "queue_action",
    "advisory_priority_facts",
    "tailoring_decision_facts",
    "operator_review_facts",
    "parity",
    "deterministic_owner_enabled",
    "deterministic_owner_invocation_attempted",
    "deterministic_owner_invocation_completed",
    "deterministic_owner_invocation_count",
    "deterministic_owner_invocation_latency_ms",
    "deterministic_owner_status",
    "deterministic_owner_failure_code",
    "rendered_priority_facts",
    "direct_owner_parity",
    "provider_metadata",
    "node_statuses",
    "node_latencies_ms",
    "reason_codes",
    "warnings",
    "current_node",
    "completed_nodes",
    "pending_node",
    "operator_review_required",
    "failure_classification",
    "read_only",
    "authoritative",
    "provider_calls_allowed",
    "mutation_authorized",
    "application_authorized",
    "ats_authorized",
    "provider_call_count",
    "production_write_count",
    "mutation_count",
    "application_count",
    "ats_count",
}


class ProductionShadowState(TypedDict):
    graph_state_schema_version: str
    owner_user_id: str
    pipeline_run_id: str
    context_id: str
    graph_invocation_id: str
    job_id: str
    job_index: int
    selected_resume_id: str
    authoritative_artifacts: Dict[str, Dict[str, str]]
    authoritative_projection: Dict[str, Any]
    queue_rank: int | None
    queue_action: str
    advisory_priority_facts: Dict[str, Any]
    tailoring_decision_facts: Dict[str, Any]
    operator_review_facts: Dict[str, Any]
    parity: Dict[str, Any]
    deterministic_owner_enabled: bool
    deterministic_owner_invocation_attempted: bool
    deterministic_owner_invocation_completed: bool
    deterministic_owner_invocation_count: int
    deterministic_owner_invocation_latency_ms: int
    deterministic_owner_status: str
    deterministic_owner_failure_code: str
    rendered_priority_facts: Dict[str, Any]
    direct_owner_parity: Dict[str, Any]
    provider_metadata: Dict[str, Any]
    node_statuses: Dict[str, str]
    node_latencies_ms: Dict[str, int]
    reason_codes: list[str]
    warnings: list[str]
    current_node: str
    completed_nodes: list[str]
    pending_node: str
    operator_review_required: bool
    failure_classification: str
    read_only: bool
    authoritative: bool
    provider_calls_allowed: bool
    mutation_authorized: bool
    application_authorized: bool
    ats_authorized: bool
    provider_call_count: int
    production_write_count: int
    mutation_count: int
    application_count: int
    ats_count: int


def _identity(value: Any, field: str) -> str:
    text = str(value or "").strip()
    if not _IDENTITY.fullmatch(text):
        raise ValueError(f"production_shadow_state_invalid:{field}")
    return text


def _bounded_codes(value: Any, field: str) -> list[str]:
    if not isinstance(value, list):
        raise ValueError(f"production_shadow_state_invalid:{field}")
    result: list[str] = []
    for item in value:
        text = str(item or "").strip()
        if text and not re.fullmatch(r"[a-z0-9_.-]{1,120}", text):
            raise ValueError(f"production_shadow_state_invalid:{field}")
        if text and text not in result:
            result.append(text)
    return result[:50]


def _reject_prohibited(value: Any, field_path: str = "state") -> None:
    if isinstance(value, Mapping):
        for raw_key, child in value.items():
            if not isinstance(raw_key, str):
                raise ValueError("production_shadow_state_non_text_key")
            key = raw_key.strip().lower()
            if (
                key in _PROHIBITED_KEYS
                or key.endswith("_path")
                or key.endswith("_filepath")
                or key == "filesystem_path"
            ):
                raise ValueError(
                    f"production_shadow_state_prohibited_field:{field_path}.{raw_key}"
                )
            _reject_prohibited(child, f"{field_path}.{raw_key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _reject_prohibited(child, f"{field_path}[{index}]")
    elif value is not None and not isinstance(value, (str, bool, int, float)):
        raise ValueError(
            f"production_shadow_state_non_json_value:{field_path}"
        )


def validate_production_shadow_state(
    value: Mapping[str, Any],
) -> ProductionShadowState:
    """Validate and return a fully detached canonical state copy."""

    if not isinstance(value, Mapping):
        raise ValueError("production_shadow_state_not_mapping")
    unknown = sorted(set(value) - _ALLOWED_TOP_LEVEL)
    if unknown:
        raise ValueError(
            f"production_shadow_state_unknown_field:{unknown[0]}"
        )
    _reject_prohibited(value)
    try:
        detached = deepcopy(dict(value))
        json.dumps(
            detached,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("production_shadow_state_not_json_safe") from exc

    if detached.get("graph_state_schema_version") != PRODUCTION_SHADOW_STATE_VERSION:
        raise ValueError("production_shadow_state_version_invalid")
    for field in (
        "owner_user_id",
        "pipeline_run_id",
        "context_id",
        "graph_invocation_id",
        "job_id",
        "selected_resume_id",
    ):
        detached[field] = _identity(detached.get(field), field)
    job_index = detached.get("job_index")
    if isinstance(job_index, bool) or not isinstance(job_index, int) or job_index < 0:
        raise ValueError("production_shadow_state_invalid:job_index")
    for field, expected in (
        ("read_only", True),
        ("authoritative", False),
        ("provider_calls_allowed", False),
        ("mutation_authorized", False),
        ("application_authorized", False),
        ("ats_authorized", False),
    ):
        if detached.get(field) is not expected:
            raise ValueError(f"production_shadow_state_safety_invalid:{field}")
    for field in (
        "provider_call_count",
        "production_write_count",
        "mutation_count",
        "application_count",
        "ats_count",
    ):
        if detached.get(field) != 0 or isinstance(detached.get(field), bool):
            raise ValueError(f"production_shadow_state_safety_invalid:{field}")
    for field in (
        "authoritative_artifacts",
        "authoritative_projection",
        "advisory_priority_facts",
        "tailoring_decision_facts",
        "operator_review_facts",
        "parity",
        "rendered_priority_facts",
        "direct_owner_parity",
        "provider_metadata",
        "node_statuses",
        "node_latencies_ms",
    ):
        if not isinstance(detached.get(field), dict):
            raise ValueError(f"production_shadow_state_invalid:{field}")
    for field in ("completed_nodes", "reason_codes", "warnings"):
        if not isinstance(detached.get(field), list):
            raise ValueError(f"production_shadow_state_invalid:{field}")
    detached["reason_codes"] = _bounded_codes(
        detached["reason_codes"], "reason_codes"
    )
    detached["warnings"] = _bounded_codes(detached["warnings"], "warnings")
    if not isinstance(detached.get("operator_review_required"), bool):
        raise ValueError(
            "production_shadow_state_invalid:operator_review_required"
        )
    for field in (
        "deterministic_owner_enabled",
        "deterministic_owner_invocation_attempted",
        "deterministic_owner_invocation_completed",
    ):
        if not isinstance(detached.get(field), bool):
            raise ValueError(f"production_shadow_state_invalid:{field}")
    invocation_count = detached.get("deterministic_owner_invocation_count")
    latency_ms = detached.get("deterministic_owner_invocation_latency_ms")
    if (
        isinstance(invocation_count, bool)
        or not isinstance(invocation_count, int)
        or invocation_count not in {0, 1}
        or isinstance(latency_ms, bool)
        or not isinstance(latency_ms, int)
        or latency_ms < 0
        or latency_ms > 3_600_000
    ):
        raise ValueError("production_shadow_state_owner_metrics_invalid")
    for field in (
        "deterministic_owner_status",
        "deterministic_owner_failure_code",
    ):
        value = str(detached.get(field) or "")
        if not re.fullmatch(r"[a-z0-9_.-]{0,120}", value):
            raise ValueError(f"production_shadow_state_invalid:{field}")
    return detached  # type: ignore[return-value]


def build_initial_production_shadow_state(
    projection: Mapping[str, Any],
) -> ProductionShadowState:
    """Build the only accepted initial state shape from a bounded projection."""

    state: Dict[str, Any] = {
        "graph_state_schema_version": PRODUCTION_SHADOW_STATE_VERSION,
        "owner_user_id": projection.get("owner_user_id"),
        "pipeline_run_id": projection.get("pipeline_run_id"),
        "context_id": projection.get("context_id"),
        "graph_invocation_id": projection.get("graph_invocation_id"),
        "job_id": projection.get("job_id"),
        "job_index": projection.get("job_index"),
        "selected_resume_id": projection.get("selected_resume_id"),
        "authoritative_artifacts": deepcopy(
            projection.get("authoritative_artifacts")
        ),
        "authoritative_projection": deepcopy(dict(projection)),
        "queue_rank": None,
        "queue_action": "",
        "advisory_priority_facts": {},
        "tailoring_decision_facts": {},
        "operator_review_facts": {},
        "parity": {},
        "deterministic_owner_enabled": bool(
            projection.get("deterministic_owner_enabled")
        ),
        "deterministic_owner_invocation_attempted": False,
        "deterministic_owner_invocation_completed": False,
        "deterministic_owner_invocation_count": 0,
        "deterministic_owner_invocation_latency_ms": 0,
        "deterministic_owner_status": "owner_not_enabled",
        "deterministic_owner_failure_code": "",
        "rendered_priority_facts": {},
        "direct_owner_parity": {},
        "provider_metadata": {},
        "node_statuses": {},
        "node_latencies_ms": {},
        "reason_codes": [],
        "warnings": [],
        "current_node": "",
        "completed_nodes": [],
        "pending_node": "",
        "operator_review_required": True,
        "failure_classification": "",
        "read_only": True,
        "authoritative": False,
        "provider_calls_allowed": False,
        "mutation_authorized": False,
        "application_authorized": False,
        "ats_authorized": False,
        "provider_call_count": 0,
        "production_write_count": 0,
        "mutation_count": 0,
        "application_count": 0,
        "ats_count": 0,
    }
    return validate_production_shadow_state(state)
