from __future__ import annotations

from dataclasses import replace
import json

import pytest

from src.pipeline.shadow_observation_contract import (
    MAX_OBSERVATION_BYTES,
    OBSERVATION_CONTRACT_VERSION,
    OBSERVATION_FIELDS,
    OBSERVATION_MODE,
    ObservationContractError,
    ShadowObservationRecord,
    parse_observation_json,
)


def valid_record(**overrides) -> ShadowObservationRecord:
    values = {
        "contract_version": OBSERVATION_CONTRACT_VERSION,
        "observation_key": "a" * 32,
        "observation_date_utc": "2026-07-24",
        "shadow_mode": OBSERVATION_MODE,
        "terminal_classification": "shadow_completed",
        "authoritative_run_succeeded": True,
        "invocation_count": 1,
        "jobs_attempted": 2,
        "jobs_completed": 2,
        "jobs_skipped": 0,
        "jobs_skipped_by_limit": 0,
        "adapter_rejection_count": 0,
        "graph_failure_count": 0,
        "parity_mismatch_count": 0,
        "parity_processing_failure_count": 0,
        "timeout_count": 0,
        "safety_violation_count": 0,
        "cleanup_failure_count": 0,
        "process_liveness_failure_count": 0,
        "exact_identity_total": 4,
        "exact_identity_matched": 4,
        "selected_resume_total": 2,
        "selected_resume_matched": 2,
        "ordered_parity_total": 2,
        "ordered_parity_matched": 2,
        "categorical_parity_total": None,
        "categorical_parity_matched": None,
        "intentionally_incomparable_count": 0,
        "shadow_latency_ms_total": 50,
        "max_job_graph_latency_ms": 10,
        "subprocess_wall_clock_ms": 40,
        "status_update_succeeded": None,
        "aggregate_log_succeeded": None,
        "flag_enabled_for_run": True,
        "cleanup_complete": True,
        "process_liveness_confirmed": True,
    }
    values.update(overrides)
    return ShadowObservationRecord(**values)


def test_complete_valid_record_is_deterministic_and_exactly_bounded():
    record = valid_record()
    assert record.serialize() == record.serialize()
    assert len(record.serialize()) <= MAX_OBSERVATION_BYTES
    payload = json.loads(record.serialize())
    assert tuple(payload) == OBSERVATION_FIELDS
    assert parse_observation_json(record.serialize()) == record


def test_every_key_is_required_and_unknown_or_prohibited_keys_are_rejected():
    payload = valid_record().to_mapping()
    payload.pop("jobs_completed")
    with pytest.raises(ObservationContractError):
        parse_observation_json(json.dumps(payload))
    for prohibited in (
        "owner_id",
        "pipeline_run_id",
        "context_id",
        "job_id",
        "selected_resume_id",
        "stdout",
        "stderr",
        "exception",
        "recommendation",
        "artifact_digest",
    ):
        payload = valid_record().to_mapping()
        payload[prohibited] = "SENSITIVE_MARKER"
        with pytest.raises(
            ObservationContractError, match="observation_fields_invalid"
        ):
            parse_observation_json(json.dumps(payload))


def test_duplicate_json_key_is_rejected():
    rendered = valid_record().serialize().decode().rstrip()
    duplicate = rendered[:-1] + ',"contract_version":"other"}'
    with pytest.raises(
        ObservationContractError, match="observation_duplicate_key"
    ):
        parse_observation_json(duplicate)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("observation_key", "A" * 32),
        ("observation_key", "a" * 31),
        ("observation_date_utc", "2026-7-24"),
        ("observation_date_utc", "2026-02-30"),
        ("shadow_mode", "canary"),
        ("terminal_classification", "free form failure"),
        ("invocation_count", 0),
        ("invocation_count", True),
        ("jobs_attempted", -1),
        ("jobs_attempted", 26),
        ("jobs_completed", True),
        ("shadow_latency_ms_total", 3_600_001),
        ("authoritative_run_succeeded", 1),
    ],
)
def test_format_enum_boolean_and_integer_bounds(field, value):
    with pytest.raises(ObservationContractError):
        valid_record(**{field: value})


@pytest.mark.parametrize("constant", ["NaN", "Infinity", "-Infinity"])
def test_non_finite_json_numbers_are_rejected(constant):
    rendered = valid_record().serialize().decode()
    rendered = rendered.replace('"shadow_latency_ms_total":50', f'"shadow_latency_ms_total":{constant}')
    with pytest.raises(
        ObservationContractError, match="observation_numeric_invalid"
    ):
        parse_observation_json(rendered)


def test_cross_field_relationships_are_strict():
    with pytest.raises(
        ObservationContractError, match="observation_job_counts_invalid"
    ):
        valid_record(jobs_attempted=1, jobs_completed=2)
    with pytest.raises(
        ObservationContractError, match="observation_match_counts_invalid"
    ):
        valid_record(selected_resume_total=1, selected_resume_matched=2)


def test_null_means_unknown_and_is_not_coerced_to_zero():
    record = valid_record(
        jobs_attempted=None,
        jobs_completed=None,
        exact_identity_total=None,
        exact_identity_matched=None,
    )
    payload = json.loads(record.serialize())
    assert payload["jobs_attempted"] is None
    assert payload["exact_identity_matched"] is None


def test_record_has_no_sensitive_names_values_or_free_form_error_channel():
    rendered = valid_record().serialize().decode()
    for marker in (
        "owner_id",
        "pipeline_run_id",
        "context_id",
        "job_id",
        "selected_resume_id",
        "stdout",
        "stderr",
        "path",
        "exception",
        "warning",
        "reason",
        "credential",
        "authorization",
        "database",
        "SENSITIVE_MARKER",
    ):
        assert marker not in rendered
    assert not any("error" in field or "reason" in field for field in OBSERVATION_FIELDS)


def test_dataclass_revalidation_prevents_oversized_or_unvalidated_replacement():
    with pytest.raises(ObservationContractError):
        replace(valid_record(), terminal_classification="x" * 9000)
