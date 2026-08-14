"""One-call durable tailoring diagnostic runtime for Groq canary run 005."""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Dict, Iterable, Mapping

from src.evaluation.controlled_groq_canary_evidence_runtime import (
    calculate_observed_cost,
)
from src.evaluation.controlled_groq_provider_canary import (
    pricing_table_sha256,
    validate_operator_approved_pricing,
)
from src.evaluation.controlled_groq_canary_run_005_identity import (
    RUN_005_ARTIFACT_PATHS,
    RUN_005_AUTHORIZATION_TEMPLATE_VERSION,
    RUN_005_IDENTIFIER,
    RUN_005_IDENTITY_VERSION,
    build_run_005_authorization_template,
    build_run_005_identity_contract,
    run_005_authorization_template_sha256,
    run_005_identity_sha256,
    validate_run_005_authorization_template,
    validate_run_005_identity_contract,
)
from src.evaluation.controlled_groq_canary_run_005_plan import (
    RUN_005_PLAN_VERSION,
    build_run_005_plan_contract,
    run_005_plan_sha256,
    validate_run_005_plan_contract,
)
from src.evaluation.controlled_groq_canary_transport import (
    TRANSPORT_VERSION,
    build_controlled_groq_transport_contract,
    validate_controlled_groq_transport_contract,
)
from src.evaluation.controlled_provider_benchmark_harness import (
    TRANSPORT_RESULT_FIELDS,
    validate_injected_transport_result,
)
from src.evaluation.provider_benchmark_contract import HARD_FAILURE_ORDER
from src.evaluation.provider_fixture_benchmark import (
    TAILORING_DIAGNOSTIC_FAILURE_CODES,
    build_tailoring_generation_diagnostics,
    grade_normalized_candidate_result,
    load_fixture_case_corpus,
    validate_fixture_case_corpus,
)


RUN_005_EVIDENCE_RUNTIME_VERSION = (
    "controlled-groq-canary-run-005-evidence-runtime-v1"
)
RUN_005_CHECKPOINT_SCHEMA_VERSION = (
    "controlled-groq-canary-run-005-checkpoint-v1"
)
RUN_005_RESULT_SCHEMA_VERSION = "controlled-groq-canary-run-005-result-v1"

_PINNED_PLAN_SHA256 = (
    "57c46f89f3d53ab3e8a82f73a7fffdd9e5157db5459521f06950f74d679f5e62"
)
_PINNED_IDENTITY_SHA256 = (
    "3c365a5cf931a3d6b2d855db27ab7762e5454c89085a32a203a244ec55e11ea1"
)
_PINNED_AUTHORIZATION_TEMPLATE_SHA256 = (
    "00080272f28d202c38de019d4478941a2b7ac8a37c7beebd7d1df72b60b42882"
)
_PINNED_TRANSPORT_SHA256 = (
    "e27ad7f7eccf67837cde2b940c448042953abe16749378b0f353d6e503180209"
)
_PINNED_SCHEDULE_KEYS = (
    "canary_run_005_a8a5414230a2a0da4a3bfb532df06b0dc4b17eb062076909a77c855d26bdae7c",
)
_ACTIVE_AUTHORIZATION_FIELDS = {
    "maximum_observed_cost_per_model",
    "maximum_total_observed_cost",
    "pricing_table_sha256",
    "valid_from_utc",
    "expires_at_utc",
    "operator_approved",
    "live_execution_authorized",
}
_CHECKPOINT_FIELDS = {
    "run_005_evidence_runtime_version",
    "checkpoint_schema_version",
    "run_identifier",
    "run_005_plan_version",
    "run_005_plan_sha256",
    "run_005_identity_version",
    "run_005_identity_sha256",
    "run_005_transport_version",
    "run_005_transport_sha256",
    "authorization_sha256",
    "pricing_sha256",
    "schedule",
    "schedule_keys",
    "artifact_paths",
    "completed_schedule_keys",
    "blocked_schedule_keys",
    "ambiguous_schedule_keys",
    "hard_failure_schedule_keys",
    "aggregate_usage",
    "grading_summaries",
    "stop_reason",
    "quality_gate_status",
    "cost_comparison_eligibility",
    "authority_invariants",
}
_AGGREGATE_FIELDS = {
    "provider_call_count",
    "input_token_count",
    "output_token_count",
    "latency_ms",
    "observed_cost",
    "by_model",
    "by_workload",
    "by_schedule_key",
}
_SUMMARY_FIELDS = {
    "schedule_key",
    "workload_id",
    "provider",
    "model",
    "schema_valid",
    "normalization_succeeded",
    "quality_gate_passed",
    "hard_failures",
    "provider_outcome_category",
    "latency_ms",
    "input_token_count",
    "output_token_count",
    "observed_cost",
    "provider_call_count",
    "tailoring_diagnostics",
}
_TAILORING_DIAGNOSTIC_FIELDS = {
    "suggestion_count",
    "unsupported_claim_count",
    "unsupported_source_id_count",
    "human_review_required_passed",
    "authority_preserved",
    "required_field_completeness",
    "tailoring_failure_codes",
}
_RESULT_FIELDS = {
    "result_schema_version",
    "run_005_evidence_runtime_version",
    "run_identifier",
    "run_005_plan_version",
    "run_005_plan_sha256",
    "run_005_identity_version",
    "run_005_identity_sha256",
    "run_005_transport_version",
    "run_005_transport_sha256",
    "authorization_sha256",
    "pricing_sha256",
    "artifact_paths",
    "checkpoint",
    "final_status",
    "state_counts",
    "aggregate_usage",
    "grading_summaries",
    "quality_gate_status",
    "cost_comparison_eligibility",
    "winner_selected",
    "production_activation",
    "mutation_count",
    "application_action_count",
    "ats_action_count",
    "retention_policy",
}
_STATE_FIELDS = (
    "completed_schedule_keys",
    "blocked_schedule_keys",
    "ambiguous_schedule_keys",
    "hard_failure_schedule_keys",
)
_PROHIBITED_EVIDENCE_KEYS = {
    "api_key",
    "credential",
    "environment",
    "expected_output",
    "golden",
    "grader_threshold",
    "header",
    "headers",
    "normalized_output",
    "prompt",
    "raw_exception",
    "raw_request",
    "raw_response",
    "reasoning",
    "repository_path",
    "request_id",
    "request_packet",
    "response_envelope",
    "sdk_object",
    "synthetic_input",
    "suggestions",
    "claims",
    "source_ids",
    "generated_text",
    "evidence_tokens",
    "evidence_ids",
}
_HARD_FAILURE_CATEGORIES = set(HARD_FAILURE_ORDER) | {
    "application_action",
    "ats_action",
    "cost_ceiling_exceeded",
    "fallback_attempted",
    "missing_usage_metadata",
    "provider_model_mismatch",
    "raw_response_persistence",
    "retry_attempted",
    "schema_invalid",
    "token_budget_exceeded",
    "unknown_provider_outcome",
    "workload_quality_gate_failed",
}
_HARD_STOP_REASONS = {
    "application_action",
    "ats_action",
    "cost_ceiling_exceeded",
    "fallback_attempted",
    "hard_safety_failure",
    "missing_usage_metadata",
    "provider_model_mismatch",
    "raw_response_persistence",
    "retry_attempted",
    "schema_invalid",
    "token_budget_exceeded",
    "unknown_provider_outcome",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _canonical_json(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _canonical_sha256(value: Any) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _iter_keys(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield str(key).strip().lower().replace("-", "_")
            yield from _iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_keys(item)


def _contains_prohibited_evidence(value: Any) -> bool:
    return any(key in _PROHIBITED_EVIDENCE_KEYS for key in _iter_keys(value))


def _parse_utc(value: Any, label: str) -> datetime:
    _require(isinstance(value, str) and bool(value.strip()), f"{label} required")
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(f"{label} must be ISO-8601 UTC") from None
    _require(
        parsed.tzinfo is not None
        and parsed.utcoffset() == timezone.utc.utcoffset(parsed),
        f"{label} must be UTC",
    )
    return parsed


def _positive_decimal(value: Any, label: str) -> Decimal:
    _require(
        isinstance(value, (str, int, float))
        and not isinstance(value, bool),
        f"{label} must be a positive decimal",
    )
    try:
        parsed = Decimal(str(value))
    except InvalidOperation:
        raise ValueError(f"{label} must be a positive decimal") from None
    _require(parsed.is_finite() and parsed > 0, f"{label} must be positive")
    return parsed


def _decimal_text(value: Decimal) -> str:
    return format(value, "f")


def _nonnegative_number(value: Any, label: str) -> float:
    _require(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) >= 0,
        f"{label} must be a finite nonnegative number",
    )
    return float(value)


def _validated_owners() -> tuple[Dict[str, Any], Dict[str, Any]]:
    plan = build_run_005_plan_contract()
    identity = build_run_005_identity_contract()
    validate_run_005_plan_contract(plan)
    validate_run_005_identity_contract(identity)
    _require(
        run_005_plan_sha256(plan) == _PINNED_PLAN_SHA256,
        "run-005 plan digest changed",
    )
    _require(
        run_005_identity_sha256(identity) == _PINNED_IDENTITY_SHA256,
        "run-005 identity digest changed",
    )
    _require(
        run_005_authorization_template_sha256()
        == _PINNED_AUTHORIZATION_TEMPLATE_SHA256,
        "run-005 authorization-template digest changed",
    )
    current_transport = build_controlled_groq_transport_contract()
    validate_controlled_groq_transport_contract(current_transport)
    _require(
        current_transport["authority_invariants"] == {
            "live_execution_authorized": False,
            "fallback": False,
            "retry_count": 0,
            "production_activation": False,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
        },
        "current base Groq transport authority changed",
    )
    _require(
        len(plan["schedule"]) == 1
        and identity["schedule"] == plan["schedule"]
        and tuple(row["schedule_key"] for row in plan["schedule"])
        == _PINNED_SCHEDULE_KEYS,
        "run-005 schedule ownership changed",
    )
    return deepcopy(plan), deepcopy(identity)


def validate_run_005_active_authorization(
    authorization: Dict[str, Any] | None,
    *,
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> bool:
    _validated_owners()
    validate_operator_approved_pricing(
        pricing,
        execution_at_utc=execution_at_utc,
    )
    _require(
        isinstance(authorization, dict),
        "active run-005 authorization is required",
    )
    inactive = build_run_005_authorization_template()
    validate_run_005_authorization_template(inactive)
    _require(
        set(authorization) == set(inactive),
        "run-005 authorization fields must match the exact template",
    )
    for key in set(inactive) - _ACTIVE_AUTHORIZATION_FIELDS:
        _require(
            authorization[key] == inactive[key],
            f"run-005 authorization changed fixed field {key}",
        )
    model_key = "groq/openai/gpt-oss-120b"
    ceilings = authorization["maximum_observed_cost_per_model"]
    _require(
        isinstance(ceilings, dict) and set(ceilings) == {model_key},
        "run-005 authorization must contain one exact model ceiling",
    )
    model_ceiling = _positive_decimal(
        ceilings[model_key],
        "run-005 model cost ceiling",
    )
    total_ceiling = _positive_decimal(
        authorization["maximum_total_observed_cost"],
        "run-005 total cost ceiling",
    )
    _require(
        total_ceiling <= model_ceiling,
        "run-005 total ceiling exceeds the model ceiling",
    )
    _require(
        authorization["pricing_table_sha256"]
        == pricing_table_sha256(pricing),
        "run-005 pricing digest mismatch",
    )
    valid_from = _parse_utc(authorization["valid_from_utc"], "valid_from_utc")
    expires_at = _parse_utc(authorization["expires_at_utc"], "expires_at_utc")
    execution = _parse_utc(execution_at_utc, "execution_at_utc")
    _require(valid_from < expires_at, "authorization window is invalid")
    _require(
        valid_from <= execution <= expires_at,
        "authorization is expired or not yet valid",
    )
    _require(
        authorization["operator_approved"] is True
        and authorization["live_execution_authorized"] is True,
        "operator and live authorization are required",
    )
    _require(
        authorization["authorization_template_version"]
        == RUN_005_AUTHORIZATION_TEMPLATE_VERSION,
        "authorization-template version changed",
    )
    return True


def _bindings(
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Dict[str, Any]:
    plan, identity = _validated_owners()
    return {
        "run_005_evidence_runtime_version": (
            RUN_005_EVIDENCE_RUNTIME_VERSION
        ),
        "checkpoint_schema_version": RUN_005_CHECKPOINT_SCHEMA_VERSION,
        "run_identifier": RUN_005_IDENTIFIER,
        "run_005_plan_version": RUN_005_PLAN_VERSION,
        "run_005_plan_sha256": _PINNED_PLAN_SHA256,
        "run_005_identity_version": RUN_005_IDENTITY_VERSION,
        "run_005_identity_sha256": _PINNED_IDENTITY_SHA256,
        "run_005_transport_version": TRANSPORT_VERSION,
        "run_005_transport_sha256": _PINNED_TRANSPORT_SHA256,
        "authorization_sha256": _canonical_sha256(authorization),
        "pricing_sha256": pricing_table_sha256(pricing),
        "schedule": deepcopy(plan["schedule"]),
        "schedule_keys": list(_PINNED_SCHEDULE_KEYS),
        "artifact_paths": deepcopy(identity["future_artifact_identities"]),
    }


def _empty_aggregate() -> Dict[str, Any]:
    return {
        "provider_call_count": 0,
        "input_token_count": 0,
        "output_token_count": 0,
        "latency_ms": 0.0,
        "observed_cost": "0",
        "by_model": {"openai/gpt-oss-120b": 0},
        "by_workload": {
            "tailoring_generation": 0,
        },
        "by_schedule_key": {key: 0 for key in _PINNED_SCHEDULE_KEYS},
    }


def _expected_authority(provider_call_count: int) -> Dict[str, Any]:
    return {
        "provider_call_count": provider_call_count,
        "fallback_count": 0,
        "retry_count": 0,
        "raw_response_persisted_count": 0,
        "winner_selected": False,
        "production_activation": False,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
        "run_001_resume_count": 0,
        "run_001_key_replay_count": 0,
        "run_002_resume_count": 0,
        "run_002_key_replay_count": 0,
        "run_003_resume_count": 0,
        "run_003_key_replay_count": 0,
        "run_004_resume_count": 0,
        "run_004_key_replay_count": 0,
    }


def build_empty_run_005_checkpoint(
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    validate_run_005_active_authorization(
        authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    checkpoint = {
        **_bindings(authorization=authorization, pricing=pricing),
        "completed_schedule_keys": [],
        "blocked_schedule_keys": [],
        "ambiguous_schedule_keys": [],
        "hard_failure_schedule_keys": [],
        "aggregate_usage": _empty_aggregate(),
        "grading_summaries": [],
        "stop_reason": None,
        "quality_gate_status": "pending",
        "cost_comparison_eligibility": False,
        "authority_invariants": _expected_authority(0),
    }
    validate_run_005_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return deepcopy(checkpoint)


def _state_sets(checkpoint: Mapping[str, Any]) -> tuple[set[str], ...]:
    observed = []
    for field in _STATE_FIELDS:
        values = checkpoint.get(field)
        _require(
            isinstance(values, list)
            and len(values) == len(set(values))
            and set(values) <= set(_PINNED_SCHEDULE_KEYS),
            f"{field} contains invalid run-005 keys",
        )
        observed.append(set(values))
    for index, left in enumerate(observed):
        for right in observed[index + 1 :]:
            _require(left.isdisjoint(right), "run-005 state lists overlap")
    return tuple(observed)


def _validate_tailoring_diagnostics(
    diagnostics: Dict[str, Any],
    *,
    failures: Mapping[str, int],
    quality_gate_passed: bool,
) -> bool:
    _require(
        isinstance(diagnostics, dict)
        and set(diagnostics) == _TAILORING_DIAGNOSTIC_FIELDS,
        "run-005 tailoring diagnostic fields are invalid",
    )
    for field in (
        "suggestion_count",
        "unsupported_claim_count",
        "unsupported_source_id_count",
    ):
        _require(
            isinstance(diagnostics[field], int)
            and not isinstance(diagnostics[field], bool)
            and diagnostics[field] >= 0,
            f"run-005 {field} is invalid",
        )
    for field in (
        "human_review_required_passed",
        "authority_preserved",
    ):
        _require(
            isinstance(diagnostics[field], bool),
            f"run-005 {field} is invalid",
        )
    completeness = diagnostics["required_field_completeness"]
    _require(
        isinstance(completeness, (int, float))
        and not isinstance(completeness, bool)
        and math.isfinite(float(completeness))
        and 0.0 <= float(completeness) <= 1.0,
        "run-005 required-field completeness is invalid",
    )
    codes = diagnostics["tailoring_failure_codes"]
    _require(
        isinstance(codes, list)
        and codes == sorted(set(codes))
        and set(codes) <= TAILORING_DIAGNOSTIC_FAILURE_CODES,
        "run-005 tailoring failure codes are invalid",
    )
    expected_codes = []
    if diagnostics["suggestion_count"] == 0:
        expected_codes.append("suggestions_empty")
    if diagnostics["unsupported_claim_count"] > 0:
        expected_codes.append("unsupported_claim")
    if diagnostics["unsupported_source_id_count"] > 0:
        expected_codes.append("unsupported_source_bullet_id")
    if not diagnostics["human_review_required_passed"]:
        expected_codes.append("human_review_required_false")
    if not diagnostics["authority_preserved"]:
        expected_codes.append("deterministic_authority_not_preserved")
    _require(
        codes == sorted(expected_codes),
        "run-005 tailoring failure codes disagree with bounded diagnostics",
    )
    unsupported = diagnostics["unsupported_claim_count"]
    _require(
        failures.get("unsupported_claim", 0) == unsupported
        and failures.get("hallucination", 0) == unsupported,
        "run-005 unsupported-claim diagnostics disagree with hard failures",
    )
    _require(
        not quality_gate_passed or not codes,
        "run-005 quality pass cannot contain diagnostic failures",
    )
    task_quality_failure = (
        bool(codes)
        and not set(failures)
        <= {
            "schema_invalid",
            "token_budget_exceeded",
            "cost_ceiling_exceeded",
        }
    )
    if failures.get("workload_quality_gate_failed", 0):
        _require(
            task_quality_failure,
            "run-005 workload failure lacks diagnostic failure codes",
        )
    return True


def _validate_summary(summary: Dict[str, Any]) -> bool:
    _require(
        isinstance(summary, dict) and set(summary) == _SUMMARY_FIELDS,
        "run-005 grading summary fields are invalid",
    )
    ownership = {
        row["schedule_key"]: row
        for row in build_run_005_plan_contract()["schedule"]
    }
    row = ownership.get(summary["schedule_key"])
    _require(
        row is not None
        and summary["workload_id"] == row["workload_id"]
        and summary["provider"] == row["provider"] == "groq"
        and summary["model"] == row["model"] == "openai/gpt-oss-120b",
        "run-005 grading summary ownership changed",
    )
    _require(
        isinstance(summary["schema_valid"], bool)
        and isinstance(summary["normalization_succeeded"], bool)
        and isinstance(summary["quality_gate_passed"], bool),
        "run-005 grading booleans are invalid",
    )
    failures = summary["hard_failures"]
    _require(
        isinstance(failures, dict)
        and all(
            key in _HARD_FAILURE_CATEGORIES
            and isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0
            for key, value in failures.items()
        ),
        "run-005 hard failures are not bounded positive counters",
    )
    _validate_tailoring_diagnostics(
        summary["tailoring_diagnostics"],
        failures=failures,
        quality_gate_passed=summary["quality_gate_passed"],
    )
    _require(
        summary["provider_outcome_category"] == "success",
        "run-005 persisted outcome category is invalid",
    )
    _nonnegative_number(summary["latency_ms"], "summary latency")
    for field in ("input_token_count", "output_token_count"):
        _require(
            isinstance(summary[field], int)
            and not isinstance(summary[field], bool)
            and summary[field] > 0,
            f"run-005 {field} is invalid",
        )
    _require(
        summary["provider_call_count"] == 1,
        "run-005 summary must own exactly one call",
    )
    observed_cost = Decimal(str(summary["observed_cost"]))
    _require(
        observed_cost.is_finite() and observed_cost > 0,
        "run-005 observed cost is invalid",
    )
    _require(
        summary["quality_gate_passed"] is (not bool(failures)),
        "run-005 quality status and failures disagree",
    )
    _require(
        not _contains_prohibited_evidence(summary),
        "run-005 summary contains prohibited evidence",
    )
    return True


def _recomputed_aggregate(
    *,
    invoked: set[str],
    summaries: list[Dict[str, Any]],
) -> Dict[str, Any]:
    aggregate = _empty_aggregate()
    count = len(invoked)
    aggregate["provider_call_count"] = count
    aggregate["by_model"]["openai/gpt-oss-120b"] = count
    rows = {
        row["schedule_key"]: row
        for row in build_run_005_plan_contract()["schedule"]
    }
    for key in invoked:
        aggregate["by_workload"][rows[key]["workload_id"]] += 1
        aggregate["by_schedule_key"][key] = 1
    aggregate["input_token_count"] = sum(
        summary["input_token_count"] for summary in summaries
    )
    aggregate["output_token_count"] = sum(
        summary["output_token_count"] for summary in summaries
    )
    aggregate["latency_ms"] = sum(
        float(summary["latency_ms"]) for summary in summaries
    )
    aggregate["observed_cost"] = _decimal_text(
        sum(
            (Decimal(str(summary["observed_cost"])) for summary in summaries),
            Decimal("0"),
        )
    )
    return aggregate


def validate_run_005_checkpoint(
    checkpoint: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> bool:
    validate_run_005_active_authorization(
        authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    _require(
        isinstance(checkpoint, dict) and set(checkpoint) == _CHECKPOINT_FIELDS,
        "run-005 checkpoint fields must match the exact schema",
    )
    _require(
        not _contains_prohibited_evidence(checkpoint),
        "run-005 checkpoint contains prohibited evidence",
    )
    bindings = _bindings(authorization=authorization, pricing=pricing)
    for key, expected in bindings.items():
        _require(
            checkpoint[key] == expected,
            f"run-005 checkpoint binding changed: {key}",
        )
    states = _state_sets(checkpoint)
    invoked = set().union(*states)
    _require(len(invoked) <= 1, "run-005 cannot invoke more than one key")
    summaries = checkpoint["grading_summaries"]
    _require(
        isinstance(summaries, list) and len(summaries) <= 1,
        "run-005 grading summaries are invalid",
    )
    for summary in summaries:
        _validate_summary(summary)
    completed, blocked, ambiguous, hard = states
    _require(
        list(checkpoint["completed_schedule_keys"])
        == list(_PINNED_SCHEDULE_KEYS[: len(completed)]),
        "completed run-005 keys must be an ordered prefix",
    )
    failure_count = len(blocked | ambiguous | hard)
    _require(failure_count <= 1, "run-005 has multiple terminal failures")
    if failure_count:
        failed_key = next(iter(blocked | ambiguous | hard))
        _require(
            failed_key
            == _PINNED_SCHEDULE_KEYS[len(completed)]
            and len(invoked) == len(completed) + 1,
            "run-005 failure key is not the exact next row",
        )
    summary_keys = [summary["schedule_key"] for summary in summaries]
    _require(
        summary_keys
        == [
            key
            for key in _PINNED_SCHEDULE_KEYS
            if key in completed | hard and any(
                item["schedule_key"] == key for item in summaries
            )
        ],
        "run-005 grading summaries are reordered",
    )
    if not invoked:
        _require(
            summaries == []
            and checkpoint["stop_reason"] is None
            and checkpoint["quality_gate_status"] == "pending"
            and checkpoint["cost_comparison_eligibility"] is False,
            "empty run-005 checkpoint state is inconsistent",
        )
    elif len(completed) == 1:
        _require(
            len(summaries) == 1
            and summaries[0]["quality_gate_passed"] is True
            and checkpoint["stop_reason"] == "completed"
            and checkpoint["quality_gate_status"] == "passed"
            and checkpoint["cost_comparison_eligibility"] is True,
            "fully completed run-005 checkpoint is inconsistent",
        )
    elif hard:
        _require(
            checkpoint["stop_reason"] in _HARD_STOP_REASONS
            and checkpoint["quality_gate_status"] == "failed"
            and checkpoint["cost_comparison_eligibility"] is False
            and len(summaries) in {len(completed), len(completed) + 1}
            and all(
                item["quality_gate_passed"] is True
                for item in summaries[: len(completed)]
            )
            and (
                len(summaries) == len(completed)
                or summaries[-1]["quality_gate_passed"] is False
            ),
            "hard-failure run-005 checkpoint is inconsistent",
        )
    elif blocked:
        _require(
            len(summaries) == len(completed)
            and all(item["quality_gate_passed"] is True for item in summaries)
            and checkpoint["stop_reason"] == "definitive_transport_failure"
            and checkpoint["quality_gate_status"] == "stopped"
            and checkpoint["cost_comparison_eligibility"] is False,
            "blocked run-005 checkpoint is inconsistent",
        )
    elif ambiguous:
        _require(
            len(summaries) == len(completed)
            and all(item["quality_gate_passed"] is True for item in summaries)
            and checkpoint["stop_reason"]
            in {"ambiguous_timeout", "unknown_provider_outcome"}
            and checkpoint["quality_gate_status"] == "stopped"
            and checkpoint["cost_comparison_eligibility"] is False,
            "ambiguous run-005 checkpoint is inconsistent",
        )
    expected_aggregate = _recomputed_aggregate(
        invoked=invoked,
        summaries=summaries,
    )
    _require(
        isinstance(checkpoint["aggregate_usage"], dict)
        and set(checkpoint["aggregate_usage"]) == _AGGREGATE_FIELDS
        and checkpoint["aggregate_usage"] == expected_aggregate,
        "run-005 aggregate usage is inconsistent",
    )
    _require(
        checkpoint["authority_invariants"] == _expected_authority(len(invoked)),
        "run-005 checkpoint authority changed",
    )
    return True


def get_next_run_005_row(
    checkpoint: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any] | None:
    validate_run_005_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    invoked = set().union(
        *(set(checkpoint[field]) for field in _STATE_FIELDS)
    )
    if (
        checkpoint["blocked_schedule_keys"]
        or checkpoint["ambiguous_schedule_keys"]
        or checkpoint["hard_failure_schedule_keys"]
        or len(checkpoint["completed_schedule_keys"]) == 1
    ):
        return None
    return deepcopy(
        checkpoint["schedule"][len(checkpoint["completed_schedule_keys"])]
    )


def _validate_transition_start(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    validate_run_005_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    next_row = get_next_run_005_row(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    _require(next_row is not None, "run-005 checkpoint is terminal")
    _require(
        isinstance(scheduled, Mapping) and dict(scheduled) == next_row,
        "run-005 transition row is not the exact next row",
    )
    return deepcopy(next_row)


def _terminal_transition(
    checkpoint: Dict[str, Any],
    *,
    state_field: str,
    schedule_key: str,
    stop_reason: str,
    quality_status: str,
    summary: Dict[str, Any] | None,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    updated = deepcopy(checkpoint)
    updated[state_field] = [*updated[state_field], schedule_key]
    if summary is not None:
        updated["grading_summaries"] = [
            *updated["grading_summaries"],
            deepcopy(summary),
        ]
    invoked = set().union(
        *(set(updated[field]) for field in _STATE_FIELDS)
    )
    updated["aggregate_usage"] = _recomputed_aggregate(
        invoked=invoked,
        summaries=updated["grading_summaries"],
    )
    fully_completed = (
        state_field == "completed_schedule_keys"
        and len(updated["completed_schedule_keys"]) == 1
    )
    updated["stop_reason"] = "completed" if fully_completed else (
        None if state_field == "completed_schedule_keys" else stop_reason
    )
    updated["quality_gate_status"] = (
        "passed" if fully_completed else
        "pending" if state_field == "completed_schedule_keys" else quality_status
    )
    updated["cost_comparison_eligibility"] = fully_completed
    updated["authority_invariants"] = _expected_authority(len(invoked))
    validate_run_005_checkpoint(
        updated,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return deepcopy(updated)


def record_run_005_blocked_call(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    _validate_transition_start(
        checkpoint,
        scheduled=scheduled,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return _terminal_transition(
        checkpoint,
        state_field="blocked_schedule_keys",
        schedule_key=scheduled["schedule_key"],
        stop_reason="definitive_transport_failure",
        quality_status="stopped",
        summary=None,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )


def record_run_005_ambiguous_call(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    reason: str = "ambiguous_timeout",
) -> Dict[str, Any]:
    _validate_transition_start(
        checkpoint,
        scheduled=scheduled,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    _require(
        reason in {"ambiguous_timeout", "unknown_provider_outcome"},
        "run-005 ambiguous reason is not approved",
    )
    return _terminal_transition(
        checkpoint,
        state_field="ambiguous_schedule_keys",
        schedule_key=scheduled["schedule_key"],
        stop_reason=reason,
        quality_status="stopped",
        summary=None,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )


def record_run_005_hard_failure_call(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    reason: str = "hard_safety_failure",
    summary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    _validate_transition_start(
        checkpoint,
        scheduled=scheduled,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    _require(reason in _HARD_STOP_REASONS, "hard-failure reason is not approved")
    if summary is not None:
        _validate_summary(summary)
        _require(
            summary["quality_gate_passed"] is False,
            "hard-failure summary cannot pass quality",
        )
    return _terminal_transition(
        checkpoint,
        state_field="hard_failure_schedule_keys",
        schedule_key=scheduled["schedule_key"],
        stop_reason=reason,
        quality_status="failed",
        summary=summary,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )


def _bounded_failures(grade: Mapping[str, Any]) -> Dict[str, int]:
    return {
        key: int(value)
        for key, value in grade["hard_failures"].items()
        if key in _HARD_FAILURE_CATEGORIES and int(value) > 0
    }


def _grading_summary(
    *,
    scheduled: Mapping[str, Any],
    schema_valid: bool,
    passed: bool,
    failures: Mapping[str, int],
    transport_result: Mapping[str, Any],
    observed_cost: Decimal,
    tailoring_diagnostics: Mapping[str, Any],
) -> Dict[str, Any]:
    return {
        "schedule_key": scheduled["schedule_key"],
        "workload_id": scheduled["workload_id"],
        "provider": scheduled["provider"],
        "model": scheduled["model"],
        "schema_valid": bool(schema_valid),
        "normalization_succeeded": True,
        "quality_gate_passed": bool(passed),
        "hard_failures": dict(failures),
        "provider_outcome_category": "success",
        "latency_ms": float(transport_result["latency_ms"]),
        "input_token_count": transport_result["input_token_count"],
        "output_token_count": transport_result["output_token_count"],
        "observed_cost": _decimal_text(observed_cost),
        "provider_call_count": 1,
        "tailoring_diagnostics": deepcopy(dict(tailoring_diagnostics)),
    }


def record_run_005_completed_call(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    transport_result: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    row = _validate_transition_start(
        checkpoint,
        scheduled=scheduled,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    if (
        isinstance(transport_result, dict)
        and transport_result.get("provider_outcome_category") == "success"
        and (
            "input_token_count" not in transport_result
            or "output_token_count" not in transport_result
        )
    ):
        return record_run_005_hard_failure_call(
            checkpoint,
            scheduled=row,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
            reason="missing_usage_metadata",
        )
    _require(
        isinstance(transport_result, dict)
        and set(transport_result) == set(TRANSPORT_RESULT_FIELDS),
        "run-005 transport result fields are invalid",
    )
    _require(
        transport_result["provider_outcome_category"] == "success",
        "run-005 completed transition requires a success outcome",
    )
    if not (
        transport_result["provider"] == "groq"
        and transport_result["model"] == "openai/gpt-oss-120b"
    ):
        return record_run_005_hard_failure_call(
            checkpoint,
            scheduled=row,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
            reason="provider_model_mismatch",
        )
    input_tokens = transport_result["input_token_count"]
    output_tokens = transport_result["output_token_count"]
    if not (
        isinstance(input_tokens, int)
        and not isinstance(input_tokens, bool)
        and input_tokens > 0
        and isinstance(output_tokens, int)
        and not isinstance(output_tokens, bool)
        and output_tokens > 0
    ):
        return record_run_005_hard_failure_call(
            checkpoint,
            scheduled=row,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
            reason="missing_usage_metadata",
        )
    validate_injected_transport_result(transport_result, scheduled=row)
    latency_ms = _nonnegative_number(
        transport_result["latency_ms"],
        "run-005 latency",
    )
    observed_cost = calculate_observed_cost(
        pricing=pricing,
        provider=row["provider"],
        model=row["model"],
        input_token_count=input_tokens,
        output_token_count=output_tokens,
    )
    corpus = load_fixture_case_corpus()
    validate_fixture_case_corpus(corpus)
    matches = [
        case
        for case in corpus["cases"]
        if case["workload_id"] == row["workload_id"]
        and case["sanitized_classification"] == "synthetic_sanitized"
        and case["additional_redaction_required"] is False
    ]
    _require(len(matches) == 1, "run-005 fixture ownership changed")
    case = matches[0]
    normalized_output = deepcopy(transport_result["normalized_output"])
    schema_valid = (
        isinstance(normalized_output, dict)
        and set(normalized_output) == set(case["required_fields"])
        and all(value is not None for value in normalized_output.values())
    )
    projection = {
        "case_id": case["case_id"],
        "workload_id": row["workload_id"],
        "provider": row["provider"],
        "model": row["model"],
        "normalized_output": normalized_output,
        "schema_valid": schema_valid,
        "normalization_succeeded": True,
        "fallback_used": False,
        "provider_call_count": 0,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
        "raw_response_persisted": False,
        "live_execution": False,
        "latency_ms": latency_ms,
        "input_token_count": input_tokens,
        "output_token_count": output_tokens,
        "estimated_cost": float(observed_cost),
    }
    grade = grade_normalized_candidate_result(projection, corpus=corpus)
    diagnostics = build_tailoring_generation_diagnostics(
        case,
        normalized_output,
    )
    diagnostics["required_field_completeness"] = grade[
        "required_field_completeness"
    ]
    failures = _bounded_failures(grade)
    if not schema_valid:
        failures["schema_invalid"] = 1
    prior_aggregate = checkpoint["aggregate_usage"]
    token_exceeded = (
        input_tokens > 4096
        or output_tokens > 1024
        or prior_aggregate["input_token_count"] + input_tokens > 4096
        or prior_aggregate["output_token_count"] + output_tokens > 1024
    )
    if token_exceeded:
        failures["token_budget_exceeded"] = 1
    model_ceiling = Decimal(
        str(
            authorization["maximum_observed_cost_per_model"][
                "groq/openai/gpt-oss-120b"
            ]
        )
    )
    total_ceiling = Decimal(
        str(authorization["maximum_total_observed_cost"])
    )
    cumulative_cost = (
        Decimal(str(prior_aggregate["observed_cost"])) + observed_cost
    )
    cost_exceeded = (
        cumulative_cost > model_ceiling or cumulative_cost > total_ceiling
    )
    if cost_exceeded:
        failures["cost_ceiling_exceeded"] = 1
    if not grade["quality_gate_passed"] and not failures:
        failures["workload_quality_gate_failed"] = 1
    passed = bool(grade["quality_gate_passed"]) and not failures
    summary = _grading_summary(
        scheduled=row,
        schema_valid=schema_valid,
        passed=passed,
        failures=failures,
        transport_result=transport_result,
        observed_cost=observed_cost,
        tailoring_diagnostics=diagnostics,
    )
    if not passed:
        reason = (
            "token_budget_exceeded"
            if token_exceeded
            else "cost_ceiling_exceeded"
            if cost_exceeded
            else "schema_invalid"
            if not schema_valid
            else "hard_safety_failure"
        )
        return record_run_005_hard_failure_call(
            checkpoint,
            scheduled=row,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
            reason=reason,
            summary=summary,
        )
    return _terminal_transition(
        checkpoint,
        state_field="completed_schedule_keys",
        schedule_key=scheduled["schedule_key"],
        stop_reason="completed",
        quality_status="passed",
        summary=summary,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )


def serialize_run_005_checkpoint(
    checkpoint: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> str:
    payload = deepcopy(checkpoint)
    validate_run_005_checkpoint(
        payload,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return _canonical_json(payload)


def run_005_checkpoint_sha256(
    checkpoint: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> str:
    return sha256(
        serialize_run_005_checkpoint(
            checkpoint,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
        ).encode("utf-8")
    ).hexdigest()


def build_run_005_result_artifact(
    *,
    checkpoint: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    validate_run_005_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    counts = {
        field.removesuffix("_schedule_keys"): len(checkpoint[field])
        for field in _STATE_FIELDS
    }
    invoked_count = sum(counts.values())
    _require(
        invoked_count == 1
        and (
            counts["completed"] == 1
            or counts["blocked"] == 1
            or counts["ambiguous"] == 1
            or counts["hard_failure"] == 1
        ),
        "result requires terminal run-005 state",
    )
    if counts["completed"] == 1:
        final_status = "completed"
    elif counts["hard_failure"]:
        final_status = "stopped_hard_failure"
    elif counts["ambiguous"]:
        final_status = "stopped_ambiguous"
    else:
        final_status = "stopped_blocked"
    artifact = {
        "result_schema_version": RUN_005_RESULT_SCHEMA_VERSION,
        "run_005_evidence_runtime_version": (
            RUN_005_EVIDENCE_RUNTIME_VERSION
        ),
        "run_identifier": RUN_005_IDENTIFIER,
        "run_005_plan_version": RUN_005_PLAN_VERSION,
        "run_005_plan_sha256": _PINNED_PLAN_SHA256,
        "run_005_identity_version": RUN_005_IDENTITY_VERSION,
        "run_005_identity_sha256": _PINNED_IDENTITY_SHA256,
        "run_005_transport_version": TRANSPORT_VERSION,
        "run_005_transport_sha256": _PINNED_TRANSPORT_SHA256,
        "authorization_sha256": _canonical_sha256(authorization),
        "pricing_sha256": pricing_table_sha256(pricing),
        "artifact_paths": deepcopy(RUN_005_ARTIFACT_PATHS),
        "checkpoint": deepcopy(checkpoint),
        "final_status": final_status,
        "state_counts": counts,
        "aggregate_usage": deepcopy(checkpoint["aggregate_usage"]),
        "grading_summaries": deepcopy(checkpoint["grading_summaries"]),
        "quality_gate_status": checkpoint["quality_gate_status"],
        "cost_comparison_eligibility": checkpoint[
            "cost_comparison_eligibility"
        ],
        "winner_selected": False,
        "production_activation": False,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
        "retention_policy": {
            "ignored_artifact_only": True,
            "required_file_mode": "0600",
            "maximum_retention_days": 7,
            "operator_review_required": True,
            "overwrite_allowed": False,
        },
    }
    validate_run_005_result_artifact(
        artifact,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return deepcopy(artifact)


def validate_run_005_result_artifact(
    artifact: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> bool:
    _require(
        isinstance(artifact, dict) and set(artifact) == _RESULT_FIELDS,
        "run-005 result fields must match the exact schema",
    )
    _require(
        not _contains_prohibited_evidence(artifact),
        "run-005 result contains prohibited evidence",
    )
    checkpoint = artifact["checkpoint"]
    validate_run_005_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    counts = {
        field.removesuffix("_schedule_keys"): len(checkpoint[field])
        for field in _STATE_FIELDS
    }
    _require(
        counts["completed"] == 1
        or counts["blocked"] == 1
        or counts["ambiguous"] == 1
        or counts["hard_failure"] == 1,
        "result requires terminal checkpoint",
    )
    expected_status = (
        "completed"
        if counts["completed"] == 1
        else "stopped_hard_failure"
        if counts["hard_failure"]
        else "stopped_ambiguous"
        if counts["ambiguous"]
        else "stopped_blocked"
    )
    expected_fixed = {
        "result_schema_version": RUN_005_RESULT_SCHEMA_VERSION,
        "run_005_evidence_runtime_version": (
            RUN_005_EVIDENCE_RUNTIME_VERSION
        ),
        "run_identifier": RUN_005_IDENTIFIER,
        "run_005_plan_version": RUN_005_PLAN_VERSION,
        "run_005_plan_sha256": _PINNED_PLAN_SHA256,
        "run_005_identity_version": RUN_005_IDENTITY_VERSION,
        "run_005_identity_sha256": _PINNED_IDENTITY_SHA256,
        "run_005_transport_version": TRANSPORT_VERSION,
        "run_005_transport_sha256": _PINNED_TRANSPORT_SHA256,
        "authorization_sha256": _canonical_sha256(authorization),
        "pricing_sha256": pricing_table_sha256(pricing),
        "artifact_paths": RUN_005_ARTIFACT_PATHS,
    }
    for key, expected in expected_fixed.items():
        _require(artifact[key] == expected, f"result binding changed: {key}")
    _require(
        artifact["final_status"] == expected_status
        and artifact["state_counts"] == counts
        and artifact["aggregate_usage"] == checkpoint["aggregate_usage"]
        and artifact["grading_summaries"] == checkpoint["grading_summaries"]
        and artifact["quality_gate_status"] == checkpoint["quality_gate_status"]
        and artifact["cost_comparison_eligibility"]
        is checkpoint["cost_comparison_eligibility"],
        "run-005 result and checkpoint disagree",
    )
    _require(
        artifact["winner_selected"] is False
        and artifact["production_activation"] is False
        and artifact["mutation_count"] == 0
        and artifact["application_action_count"] == 0
        and artifact["ats_action_count"] == 0,
        "run-005 result authority changed",
    )
    _require(
        artifact["retention_policy"]
        == {
            "ignored_artifact_only": True,
            "required_file_mode": "0600",
            "maximum_retention_days": 7,
            "operator_review_required": True,
            "overwrite_allowed": False,
        },
        "run-005 retention policy changed",
    )
    return True


def serialize_run_005_result_artifact(
    artifact: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> str:
    payload = deepcopy(artifact)
    validate_run_005_result_artifact(
        payload,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return _canonical_json(payload)


def run_005_result_sha256(
    artifact: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> str:
    return sha256(
        serialize_run_005_result_artifact(
            artifact,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
        ).encode("utf-8")
    ).hexdigest()


def _validate_artifact_path(
    artifact_path: str | Path,
    *,
    repository_root: str | Path,
    kind: str,
    require_existing: bool,
) -> Path:
    root = Path(repository_root).resolve()
    candidate = Path(artifact_path)
    _require(candidate.is_absolute(), "artifact path must be absolute")
    _require(".." not in candidate.parts, "artifact traversal is prohibited")
    _require(kind in {"checkpoint", "result"}, "artifact kind is invalid")
    expected = root / RUN_005_ARTIFACT_PATHS[kind]
    _require(
        candidate == expected,
        f"only the exact run-005 {kind} path is allowed",
    )
    approved = expected.parent
    _require(
        approved.is_dir() and not approved.is_symlink(),
        "artifact parent is unsafe",
    )
    current = root
    for part in expected.relative_to(root).parts[:-1]:
        current = current / part
        _require(not current.is_symlink(), "artifact path contains a symlink")
    mode = stat.S_IMODE(approved.stat().st_mode)
    _require(
        mode & stat.S_IWUSR and not mode & (stat.S_IWGRP | stat.S_IWOTH),
        "artifact parent permissions are unsafe",
    )
    ignore_file = root / ".gitignore"
    _require(ignore_file.is_file(), "repository ignore owner is missing")
    ignore_lines = {
        line.strip()
        for line in ignore_file.read_text(encoding="utf-8").splitlines()
    }
    _require(
        "outputs/" in ignore_lines or "/outputs/" in ignore_lines,
        "artifact directory is not ignored",
    )
    if require_existing:
        _require(
            candidate.is_file() and not candidate.is_symlink(),
            "artifact is missing or unsafe",
        )
    else:
        _require(
            not candidate.exists() and not candidate.is_symlink(),
            "artifact overwrite is prohibited",
        )
    return candidate


def _write_exclusive(path: Path, encoded: bytes) -> None:
    descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    except Exception:
        try:
            path.unlink()
        except FileNotFoundError:
            pass
        raise
    finally:
        os.close(descriptor)
    os.chmod(path, 0o600)


def load_run_005_checkpoint(
    checkpoint_path: str | Path,
    *,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    path = _validate_artifact_path(
        checkpoint_path,
        repository_root=repository_root,
        kind="checkpoint",
        require_existing=True,
    )
    _require(
        stat.S_IMODE(path.stat().st_mode) == 0o600,
        "run-005 checkpoint mode must be 0600",
    )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("persisted run-005 checkpoint is malformed") from None
    validate_run_005_checkpoint(
        payload,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return deepcopy(payload)


def write_initial_run_005_checkpoint(
    checkpoint_path: str | Path,
    checkpoint: Dict[str, Any],
    *,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Path:
    path = _validate_artifact_path(
        checkpoint_path,
        repository_root=repository_root,
        kind="checkpoint",
        require_existing=False,
    )
    encoded = serialize_run_005_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    ).encode("utf-8")
    _write_exclusive(path, encoded)
    load_run_005_checkpoint(
        path,
        repository_root=repository_root,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return path


def replace_run_005_checkpoint_atomic(
    checkpoint_path: str | Path,
    checkpoint: Dict[str, Any],
    *,
    expected_prior_sha256: str,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Path:
    path = _validate_artifact_path(
        checkpoint_path,
        repository_root=repository_root,
        kind="checkpoint",
        require_existing=True,
    )
    prior = load_run_005_checkpoint(
        path,
        repository_root=repository_root,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    observed_prior = run_005_checkpoint_sha256(
        prior,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    _require(
        expected_prior_sha256 == observed_prior,
        "run-005 checkpoint prior digest mismatch",
    )
    encoded = serialize_run_005_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    ).encode("utf-8")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temporary = Path(temporary_name)
    try:
        os.fchmod(descriptor, 0o600)
        with os.fdopen(descriptor, "wb", closefd=False) as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.close(descriptor)
        descriptor = -1
        current = load_run_005_checkpoint(
            path,
            repository_root=repository_root,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
        )
        current_sha = run_005_checkpoint_sha256(
            current,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
        )
        _require(
            current_sha == expected_prior_sha256,
            "run-005 checkpoint changed before replacement",
        )
        os.replace(temporary, path)
        os.chmod(path, 0o600)
    except Exception:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
        raise
    loaded = load_run_005_checkpoint(
        path,
        repository_root=repository_root,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    _require(loaded == checkpoint, "run-005 checkpoint replacement changed")
    return path


def load_run_005_result_artifact(
    result_path: str | Path,
    *,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Dict[str, Any]:
    path = _validate_artifact_path(
        result_path,
        repository_root=repository_root,
        kind="result",
        require_existing=True,
    )
    _require(
        stat.S_IMODE(path.stat().st_mode) == 0o600,
        "run-005 result mode must be 0600",
    )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("persisted run-005 result is malformed") from None
    validate_run_005_result_artifact(
        payload,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return deepcopy(payload)


def write_run_005_result_exclusive(
    result_path: str | Path,
    artifact: Dict[str, Any],
    *,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> Path:
    path = _validate_artifact_path(
        result_path,
        repository_root=repository_root,
        kind="result",
        require_existing=False,
    )
    encoded = serialize_run_005_result_artifact(
        artifact,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    ).encode("utf-8")
    _write_exclusive(path, encoded)
    load_run_005_result_artifact(
        path,
        repository_root=repository_root,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
    )
    return path
