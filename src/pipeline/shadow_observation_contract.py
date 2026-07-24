"""Strict, content-free contract for controlled shadow observations."""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from datetime import date
import json
import math
import re
from typing import Any, Mapping


OBSERVATION_CONTRACT_VERSION = "applylens-shadow-observation-v1"
OBSERVATION_MODE = "controlled_observation"
MAX_OBSERVATION_BYTES = 8 * 1024
MAX_COUNT = 1_000_000
MAX_LATENCY_MS = 3_600_000
_KEY_PATTERN = re.compile(r"[0-9a-f]{32}")
_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
_TERMINAL_CLASSIFICATIONS = {
    "shadow_completed",
    "parity_mismatch",
    "shadow_execution_failure",
    "shadow_timeout",
    "shadow_safety_violation",
    "shadow_projection_failed",
    "shadow_projection_skipped",
}
_JOB_COUNT_FIELDS = {
    "jobs_attempted",
    "jobs_completed",
    "jobs_skipped",
    "jobs_skipped_by_limit",
    "adapter_rejection_count",
    "graph_failure_count",
    "parity_processing_failure_count",
    "timeout_count",
}
_COUNT_FIELDS = {
    *_JOB_COUNT_FIELDS,
    "parity_mismatch_count",
    "safety_violation_count",
    "cleanup_failure_count",
    "process_liveness_failure_count",
    "exact_identity_total",
    "exact_identity_matched",
    "selected_resume_total",
    "selected_resume_matched",
    "ordered_parity_total",
    "ordered_parity_matched",
    "categorical_parity_total",
    "categorical_parity_matched",
    "intentionally_incomparable_count",
}
_LATENCY_FIELDS = {
    "shadow_latency_ms_total",
    "max_job_graph_latency_ms",
    "subprocess_wall_clock_ms",
}
_MATCH_PAIRS = (
    ("exact_identity_matched", "exact_identity_total"),
    ("selected_resume_matched", "selected_resume_total"),
    ("ordered_parity_matched", "ordered_parity_total"),
    ("categorical_parity_matched", "categorical_parity_total"),
)


class ObservationContractError(ValueError):
    """A bounded observation failed strict validation."""


@dataclass(frozen=True, slots=True)
class ShadowObservationRecord:
    contract_version: str
    observation_key: str
    observation_date_utc: str
    shadow_mode: str
    terminal_classification: str
    authoritative_run_succeeded: bool
    invocation_count: int
    jobs_attempted: int | None
    jobs_completed: int | None
    jobs_skipped: int | None
    jobs_skipped_by_limit: int | None
    adapter_rejection_count: int | None
    graph_failure_count: int | None
    parity_mismatch_count: int | None
    parity_processing_failure_count: int | None
    timeout_count: int | None
    safety_violation_count: int | None
    cleanup_failure_count: int | None
    process_liveness_failure_count: int | None
    exact_identity_total: int | None
    exact_identity_matched: int | None
    selected_resume_total: int | None
    selected_resume_matched: int | None
    ordered_parity_total: int | None
    ordered_parity_matched: int | None
    categorical_parity_total: int | None
    categorical_parity_matched: int | None
    intentionally_incomparable_count: int | None
    shadow_latency_ms_total: int | None
    max_job_graph_latency_ms: int | None
    subprocess_wall_clock_ms: int | None
    status_update_succeeded: bool | None
    aggregate_log_succeeded: bool | None
    flag_enabled_for_run: bool
    cleanup_complete: bool | None
    process_liveness_confirmed: bool | None

    def __post_init__(self) -> None:
        _validate_mapping(asdict(self))

    def to_mapping(self) -> dict[str, Any]:
        return asdict(self)

    def serialize(self) -> bytes:
        return serialize_observation(self)


OBSERVATION_FIELDS = tuple(field.name for field in fields(ShadowObservationRecord))
_OBSERVATION_FIELD_SET = frozenset(OBSERVATION_FIELDS)


def _strict_int(
    name: str, value: Any, *, maximum: int, nullable: bool = True
) -> None:
    if value is None and nullable:
        return
    if isinstance(value, bool) or not isinstance(value, int):
        raise ObservationContractError("observation_numeric_invalid")
    if value < 0 or value > maximum:
        raise ObservationContractError("observation_numeric_invalid")


def _strict_optional_bool(value: Any) -> None:
    if value is not None and not isinstance(value, bool):
        raise ObservationContractError("observation_boolean_invalid")


def _validate_mapping(payload: Mapping[str, Any]) -> None:
    if set(payload) != _OBSERVATION_FIELD_SET or len(payload) != len(
        OBSERVATION_FIELDS
    ):
        raise ObservationContractError("observation_fields_invalid")
    if payload["contract_version"] != OBSERVATION_CONTRACT_VERSION:
        raise ObservationContractError("observation_contract_invalid")
    if (
        not isinstance(payload["observation_key"], str)
        or _KEY_PATTERN.fullmatch(payload["observation_key"]) is None
    ):
        raise ObservationContractError("observation_key_invalid")
    rendered_date = payload["observation_date_utc"]
    if (
        not isinstance(rendered_date, str)
        or _DATE_PATTERN.fullmatch(rendered_date) is None
    ):
        raise ObservationContractError("observation_date_invalid")
    try:
        parsed_date = date.fromisoformat(rendered_date)
    except ValueError as exc:
        raise ObservationContractError("observation_date_invalid") from exc
    if parsed_date.isoformat() != rendered_date:
        raise ObservationContractError("observation_date_invalid")
    if payload["shadow_mode"] != OBSERVATION_MODE:
        raise ObservationContractError("observation_mode_invalid")
    if payload["terminal_classification"] not in _TERMINAL_CLASSIFICATIONS:
        raise ObservationContractError("observation_classification_invalid")
    for name in (
        "authoritative_run_succeeded",
        "flag_enabled_for_run",
    ):
        if not isinstance(payload[name], bool):
            raise ObservationContractError("observation_boolean_invalid")
    for name in (
        "status_update_succeeded",
        "aggregate_log_succeeded",
        "cleanup_complete",
        "process_liveness_confirmed",
    ):
        _strict_optional_bool(payload[name])
    _strict_int(
        "invocation_count",
        payload["invocation_count"],
        maximum=1,
        nullable=False,
    )
    if payload["invocation_count"] != 1:
        raise ObservationContractError("observation_invocation_invalid")
    for name in _COUNT_FIELDS:
        maximum = 25 if name in _JOB_COUNT_FIELDS else MAX_COUNT
        _strict_int(name, payload[name], maximum=maximum)
    for name in _LATENCY_FIELDS:
        _strict_int(name, payload[name], maximum=MAX_LATENCY_MS)
    attempted = payload["jobs_attempted"]
    completed = payload["jobs_completed"]
    if attempted is not None and completed is not None and completed > attempted:
        raise ObservationContractError("observation_job_counts_invalid")
    for matched_name, total_name in _MATCH_PAIRS:
        matched = payload[matched_name]
        total = payload[total_name]
        if matched is not None and total is not None and matched > total:
            raise ObservationContractError("observation_match_counts_invalid")
    for value in payload.values():
        if isinstance(value, float) and not math.isfinite(value):
            raise ObservationContractError("observation_numeric_invalid")


def serialize_observation(record: ShadowObservationRecord) -> bytes:
    _validate_mapping(record.to_mapping())
    try:
        encoded = (
            json.dumps(
                record.to_mapping(),
                ensure_ascii=True,
                sort_keys=False,
                separators=(",", ":"),
                allow_nan=False,
            )
            + "\n"
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeError) as exc:
        raise ObservationContractError("observation_serialization_failed") from exc
    if len(encoded) > MAX_OBSERVATION_BYTES:
        raise ObservationContractError("observation_too_large")
    return encoded


def parse_observation_json(rendered: str | bytes) -> ShadowObservationRecord:
    try:
        text = rendered.decode("utf-8") if isinstance(rendered, bytes) else rendered
    except UnicodeError as exc:
        raise ObservationContractError("observation_json_invalid") from exc

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ObservationContractError("observation_duplicate_key")
            result[key] = value
        return result

    def reject_constant(_value: str) -> None:
        raise ObservationContractError("observation_numeric_invalid")

    try:
        payload = json.loads(
            text,
            object_pairs_hook=reject_duplicates,
            parse_constant=reject_constant,
        )
    except ObservationContractError:
        raise
    except (json.JSONDecodeError, TypeError, UnicodeError) as exc:
        raise ObservationContractError("observation_json_invalid") from exc
    if not isinstance(payload, Mapping):
        raise ObservationContractError("observation_json_invalid")
    try:
        return ShadowObservationRecord(**payload)
    except TypeError as exc:
        raise ObservationContractError("observation_fields_invalid") from exc
