"""Durable, provider-free evidence ownership for the four-call Groq canary.

This evaluation-only module owns canary-specific checkpoint and result
contracts.  It never reads credentials, imports a provider SDK, calls a
provider, loads dotenv, opens a network or database connection, starts a
process or thread, or selects a production route.
"""

from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import stat
import tempfile
from typing import Any, Dict, Mapping

from src.evaluation.controlled_groq_canary_transport import (
    TRANSPORT_VERSION,
    controlled_groq_transport_sha256,
)
from src.evaluation.controlled_groq_provider_canary import (
    CANARY_VERSION,
    build_controlled_groq_canary_contract,
    controlled_groq_canary_sha256,
    pricing_table_sha256,
    validate_controlled_groq_canary_contract,
    validate_operator_approved_pricing,
    validate_operator_authorization,
)
from src.evaluation.controlled_provider_benchmark_harness import (
    TRANSPORT_RESULT_FIELDS,
    validate_injected_transport_result,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
)
from src.evaluation.provider_benchmark_contract import HARD_FAILURE_ORDER
from src.evaluation.provider_fixture_benchmark import (
    grade_normalized_candidate_result,
    load_fixture_case_corpus,
    validate_fixture_case_corpus,
)


EVIDENCE_RUNTIME_VERSION = "controlled-groq-canary-evidence-runtime-v1"
CHECKPOINT_SCHEMA_VERSION = "controlled-groq-canary-checkpoint-v1"
RESULT_SCHEMA_VERSION = "controlled-groq-canary-result-v1"
APPROVED_ARTIFACT_DIRECTORY = Path("outputs/provider_benchmark")

_CHECKPOINT_FIELDS = {
    "evidence_runtime_version",
    "checkpoint_schema_version",
    "canary_version",
    "canary_sha256",
    "transport_version",
    "transport_sha256",
    "authorization_sha256",
    "pricing_sha256",
    "schedule_count",
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
_GRADING_SUMMARY_FIELDS = {
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
}
_RESULT_FIELDS = {
    "result_schema_version",
    "evidence_runtime_version",
    "canary_version",
    "canary_sha256",
    "transport_version",
    "transport_sha256",
    "authorization_sha256",
    "pricing_sha256",
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
    "golden",
    "grader_threshold",
    "header",
    "normalized_output",
    "prompt",
    "raw_exception",
    "raw_provider",
    "raw_request",
    "raw_response",
    "reasoning",
    "repository_path",
    "request_id",
    "request_packet",
    "response_envelope",
    "sdk_object",
    "synthetic_input",
}
_TRANSPORT_OUTCOMES = {
    "success",
    "ambiguous_timeout",
    "definitive_failure",
    "unknown_provider_outcome",
    "application_action",
    "ats_action",
    "raw_response_persistence",
    "fallback_attempt",
    "retry_attempt",
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
_STOP_REASONS = {
    None,
    "ambiguous_timeout",
    "completed",
    "cost_ceiling_exceeded",
    "definitive_transport_failure",
    "fallback_attempted",
    "hard_safety_failure",
    "missing_usage_metadata",
    "provider_model_mismatch",
    "raw_response_persistence",
    "retry_attempted",
    "schema_invalid",
    "token_budget_exceeded",
    "unknown_provider_outcome",
    "application_action",
    "ats_action",
}
_FAILURE_OUTCOME_TO_REASON = {
    "ambiguous_timeout": "ambiguous_timeout",
    "definitive_failure": "definitive_transport_failure",
    "unknown_provider_outcome": "unknown_provider_outcome",
    "application_action": "application_action",
    "ats_action": "ats_action",
    "raw_response_persistence": "raw_response_persistence",
    "fallback_attempt": "fallback_attempted",
    "retry_attempt": "retry_attempted",
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


def _decimal(value: Any, label: str, *, positive: bool = False) -> Decimal:
    _require(not isinstance(value, bool), f"{label} must be numeric")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    _require(number.is_finite(), f"{label} must be finite")
    _require(number > 0 if positive else number >= 0, f"{label} is invalid")
    return number


def _decimal_text(value: Decimal) -> str:
    return format(value.quantize(Decimal("0.000000000001")), "f")


def _number(value: Any, label: str) -> float:
    _require(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(float(value))
        and float(value) >= 0,
        f"{label} must be finite and nonnegative",
    )
    return float(value)


def _iter_keys(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key).strip().lower()
            yield from _iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_keys(item)


def _contains_prohibited_evidence(value: Any) -> bool:
    return any(key in _PROHIBITED_EVIDENCE_KEYS for key in _iter_keys(value))


def _validated_inputs(
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    controlled_canary = (
        build_controlled_groq_canary_contract()
        if canary is None
        else deepcopy(canary)
    )
    validate_controlled_groq_canary_contract(controlled_canary)
    validate_operator_approved_pricing(
        pricing,
        execution_at_utc=execution_at_utc,
    )
    validate_operator_authorization(
        authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        contract=controlled_canary,
    )
    return controlled_canary


def _schedule_maps(
    canary: Mapping[str, Any],
) -> tuple[list[Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    schedule = [deepcopy(row) for row in canary["schedule"]]
    return schedule, {row["schedule_key"]: row for row in schedule}


def _case_maps() -> tuple[Dict[str, Dict[str, Any]], Dict[str, str]]:
    plan = build_controlled_provider_benchmark_plan()
    corpus = load_fixture_case_corpus()
    validate_fixture_case_corpus(corpus)
    by_alias: Dict[str, Dict[str, Any]] = {}
    case_id_by_alias: Dict[str, str] = {}
    for case, review in zip(corpus["cases"], plan["transmission_review"]):
        if not review["eligible_for_later_controlled_transmission"]:
            continue
        by_alias[review["case_alias"]] = deepcopy(case)
        case_id_by_alias[review["case_alias"]] = case["case_id"]
    return by_alias, case_id_by_alias


def _pricing_map(pricing: Mapping[str, Any]) -> Dict[str, Dict[str, Decimal]]:
    return {
        f"{row['provider']}/{row['model']}": {
            "input": Decimal(str(row["input_price_per_million_tokens"])),
            "output": Decimal(str(row["output_price_per_million_tokens"])),
        }
        for row in pricing["prices"]
    }


def calculate_observed_cost(
    *,
    pricing: Dict[str, Any],
    provider: str,
    model: str,
    input_token_count: int,
    output_token_count: int,
) -> Decimal:
    _require(
        isinstance(input_token_count, int)
        and not isinstance(input_token_count, bool)
        and input_token_count > 0,
        "observed input usage is required",
    )
    _require(
        isinstance(output_token_count, int)
        and not isinstance(output_token_count, bool)
        and output_token_count > 0,
        "observed output usage is required",
    )
    prices = _pricing_map(pricing)
    model_key = f"{provider}/{model}"
    _require(model_key in prices, "provider/model pricing is unavailable")
    price = prices[model_key]
    return (
        Decimal(input_token_count) * price["input"]
        + Decimal(output_token_count) * price["output"]
    ) / Decimal(1_000_000)


def _empty_aggregate(canary: Mapping[str, Any]) -> Dict[str, Any]:
    schedule = canary["schedule"]
    return {
        "provider_call_count": 0,
        "input_token_count": 0,
        "output_token_count": 0,
        "latency_ms": 0.0,
        "observed_cost": _decimal_text(Decimal("0")),
        "by_model": {
            row["model"]: 0
            for row in canary["candidate_provider_models"]
        },
        "by_workload": {
            workload: 0
            for workload in sorted({row["workload_id"] for row in schedule})
        },
        "by_schedule_key": {},
    }


def _expected_authority(provider_call_count: int) -> Dict[str, Any]:
    return {
        "provider_call_count": provider_call_count,
        "fallback_count": 0,
        "retry_count": 0,
        "raw_response_persisted_count": 0,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
        "production_activation": False,
        "winner_selected": False,
    }


def build_empty_checkpoint(
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    controlled_canary = _validated_inputs(
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    checkpoint = {
        "evidence_runtime_version": EVIDENCE_RUNTIME_VERSION,
        "checkpoint_schema_version": CHECKPOINT_SCHEMA_VERSION,
        "canary_version": CANARY_VERSION,
        "canary_sha256": controlled_groq_canary_sha256(controlled_canary),
        "transport_version": TRANSPORT_VERSION,
        "transport_sha256": controlled_groq_transport_sha256(),
        "authorization_sha256": _canonical_sha256(authorization),
        "pricing_sha256": pricing_table_sha256(pricing),
        "schedule_count": len(controlled_canary["schedule"]),
        "completed_schedule_keys": [],
        "blocked_schedule_keys": [],
        "ambiguous_schedule_keys": [],
        "hard_failure_schedule_keys": [],
        "aggregate_usage": _empty_aggregate(controlled_canary),
        "grading_summaries": [],
        "stop_reason": None,
        "quality_gate_status": "not_evaluated",
        "cost_comparison_eligibility": False,
        "authority_invariants": _expected_authority(0),
    }
    validate_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=controlled_canary,
    )
    return deepcopy(checkpoint)


def _state_sets(
    checkpoint: Mapping[str, Any],
    accepted_keys: set[str],
) -> tuple[list[set[str]], set[str]]:
    sets: list[set[str]] = []
    for field in _STATE_FIELDS:
        values = checkpoint.get(field)
        _require(
            isinstance(values, list)
            and len(values) == len(set(values))
            and set(values).issubset(accepted_keys),
            f"{field} is invalid",
        )
        sets.append(set(values))
    for index, left in enumerate(sets):
        for right in sets[index + 1 :]:
            _require(not (left & right), "checkpoint state lists overlap")
    return sets, set().union(*sets)


def _validate_summary(
    summary: Mapping[str, Any],
    *,
    scheduled: Mapping[str, Any],
) -> None:
    _require(
        isinstance(summary, dict)
        and set(summary) == _GRADING_SUMMARY_FIELDS,
        "grading summary fields are invalid",
    )
    _require(
        summary["schedule_key"] == scheduled["schedule_key"]
        and summary["workload_id"] == scheduled["workload_id"]
        and summary["provider"] == "groq"
        and summary["provider"] == scheduled["provider"]
        and summary["model"] == scheduled["model"],
        "grading summary schedule identity mismatch",
    )
    _require(
        isinstance(summary["schema_valid"], bool)
        and isinstance(summary["normalization_succeeded"], bool)
        and isinstance(summary["quality_gate_passed"], bool),
        "grading summary booleans are invalid",
    )
    _require(
        summary["provider_outcome_category"] in _TRANSPORT_OUTCOMES,
        "grading summary provider outcome is invalid",
    )
    _number(summary["latency_ms"], "grading latency")
    for field in ("input_token_count", "output_token_count"):
        value = summary[field]
        _require(
            isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0,
            f"grading {field} is missing",
        )
    _decimal(summary["observed_cost"], "grading observed cost")
    _require(
        summary["provider_call_count"] == 1,
        "grading summary must own exactly one provider call",
    )
    failures = summary["hard_failures"]
    _require(
        isinstance(failures, dict)
        and set(failures).issubset(_HARD_FAILURE_CATEGORIES)
        and all(
            isinstance(value, int)
            and not isinstance(value, bool)
            and value > 0
            for value in failures.values()
        ),
        "grading hard-failure categories are invalid",
    )
    _require(
        summary["quality_gate_passed"] is (not failures),
        "grading quality and hard failures disagree",
    )


def _recomputed_aggregate(
    *,
    invoked_keys: set[str],
    summaries: list[Mapping[str, Any]],
    canary: Mapping[str, Any],
) -> Dict[str, Any]:
    schedule, schedule_by_key = _schedule_maps(canary)
    aggregate = _empty_aggregate(canary)
    ordered_invoked = [
        row["schedule_key"]
        for row in schedule
        if row["schedule_key"] in invoked_keys
    ]
    aggregate["provider_call_count"] = len(ordered_invoked)
    for key in ordered_invoked:
        row = schedule_by_key[key]
        aggregate["by_model"][row["model"]] += 1
        aggregate["by_workload"][row["workload_id"]] += 1
        aggregate["by_schedule_key"][key] = 1
    cost = Decimal("0")
    for summary in summaries:
        aggregate["input_token_count"] += summary["input_token_count"]
        aggregate["output_token_count"] += summary["output_token_count"]
        aggregate["latency_ms"] += float(summary["latency_ms"])
        cost += Decimal(str(summary["observed_cost"]))
    aggregate["observed_cost"] = _decimal_text(cost)
    aggregate["latency_ms"] = float(aggregate["latency_ms"])
    return aggregate


def _expected_quality_status(
    checkpoint: Mapping[str, Any],
    invoked_keys: set[str],
) -> tuple[str, bool]:
    if not invoked_keys:
        return "not_evaluated", False
    if checkpoint["hard_failure_schedule_keys"]:
        return "failed", False
    if checkpoint["blocked_schedule_keys"] or checkpoint["ambiguous_schedule_keys"]:
        return "stopped", False
    if len(checkpoint["completed_schedule_keys"]) == 4:
        return "passed", True
    return "partial", False


def validate_checkpoint(
    checkpoint: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> bool:
    controlled_canary = _validated_inputs(
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    _require(
        isinstance(checkpoint, dict) and set(checkpoint) == _CHECKPOINT_FIELDS,
        "checkpoint fields must match the exact schema",
    )
    _require(
        not _contains_prohibited_evidence(checkpoint),
        "checkpoint contains prohibited evidence",
    )
    _require(
        checkpoint["evidence_runtime_version"] == EVIDENCE_RUNTIME_VERSION
        and checkpoint["checkpoint_schema_version"]
        == CHECKPOINT_SCHEMA_VERSION
        and checkpoint["canary_version"] == CANARY_VERSION
        and checkpoint["canary_sha256"]
        == controlled_groq_canary_sha256(controlled_canary)
        and checkpoint["transport_version"] == TRANSPORT_VERSION
        and checkpoint["transport_sha256"]
        == controlled_groq_transport_sha256()
        and checkpoint["authorization_sha256"]
        == _canonical_sha256(authorization)
        and checkpoint["pricing_sha256"] == pricing_table_sha256(pricing)
        and checkpoint["schedule_count"] == 4,
        "checkpoint ownership identifiers changed",
    )
    schedule, schedule_by_key = _schedule_maps(controlled_canary)
    accepted_keys = set(schedule_by_key)
    _require(
        len(accepted_keys) == 4
        and all(
            row["provider"] == "groq"
            and row["fallback"] is False
            and row["harness_retry_limit"] == 0
            and row["provider_sdk_retry_limit"] == 0
            and row["timeout_seconds"] == 30
            for row in schedule
        ),
        "canary schedule safety changed",
    )
    state_sets, invoked_keys = _state_sets(checkpoint, accepted_keys)
    ordered_keys = [row["schedule_key"] for row in schedule]
    ordered_invoked = [key for key in ordered_keys if key in invoked_keys]
    _require(
        ordered_invoked == ordered_keys[: len(ordered_invoked)],
        "checkpoint invocation order is not deterministic",
    )
    _require(len(invoked_keys) <= 4, "canary invocation count exceeded")
    summaries = checkpoint["grading_summaries"]
    _require(isinstance(summaries, list), "grading summaries must be a list")
    summary_keys: list[str] = []
    for summary in summaries:
        key = summary.get("schedule_key") if isinstance(summary, dict) else None
        _require(key in schedule_by_key, "grading summary key is unknown")
        _validate_summary(summary, scheduled=schedule_by_key[key])
        summary_keys.append(key)
    _require(
        len(summary_keys) == len(set(summary_keys)),
        "duplicate grading summary key",
    )
    _require(
        set(summary_keys).issubset(
            state_sets[0] | state_sets[3]
        )
        and state_sets[0].issubset(summary_keys),
        "grading summaries and final states disagree",
    )
    for key in state_sets[0]:
        summary = next(row for row in summaries if row["schedule_key"] == key)
        _require(
            summary["quality_gate_passed"] is True,
            "completed key did not pass its quality gate",
        )
    for key in state_sets[3] & set(summary_keys):
        summary = next(row for row in summaries if row["schedule_key"] == key)
        _require(
            summary["quality_gate_passed"] is False,
            "hard-failure key incorrectly passed its quality gate",
        )
    recomputed = _recomputed_aggregate(
        invoked_keys=invoked_keys,
        summaries=summaries,
        canary=controlled_canary,
    )
    _require(
        isinstance(checkpoint["aggregate_usage"], dict)
        and set(checkpoint["aggregate_usage"]) == _AGGREGATE_FIELDS
        and checkpoint["aggregate_usage"] == recomputed,
        "checkpoint aggregates do not reconcile",
    )
    model_counts = recomputed["by_model"]
    _require(
        all(value <= 2 for value in model_counts.values())
        and all(value <= 1 for value in recomputed["by_workload"].values())
        and all(value == 1 for value in recomputed["by_schedule_key"].values()),
        "checkpoint invocation bounds exceeded",
    )
    token_bounds = controlled_canary["token_bounds"]
    token_ceiling_exceeded = (
        recomputed["input_token_count"]
        > token_bounds["maximum_aggregate_input_tokens"]
        or recomputed["output_token_count"]
        > token_bounds["maximum_aggregate_output_tokens"]
        or any(
            summary["input_token_count"]
            > token_bounds["maximum_input_tokens_per_request"]
            or summary["output_token_count"]
            > token_bounds["maximum_output_tokens_per_request"]
            for summary in summaries
        )
    )
    _require(
        not token_ceiling_exceeded
        or (
            checkpoint["stop_reason"] == "token_budget_exceeded"
            and bool(checkpoint["hard_failure_schedule_keys"])
        ),
        "checkpoint token ceiling breach was not stopped",
    )
    any_model_cost_exceeded = False
    for candidate in controlled_canary["candidate_provider_models"]:
        model = candidate["model"]
        model_cost = sum(
            (
                Decimal(str(row["observed_cost"]))
                for row in summaries
                if row["model"] == model
            ),
            Decimal("0"),
        )
        ceiling = authorization["maximum_observed_cost_per_model"][
            f"groq/{model}"
        ]
        any_model_cost_exceeded = (
            any_model_cost_exceeded
            or model_cost > Decimal(str(ceiling))
        )
    total_cost_exceeded = (
        Decimal(recomputed["observed_cost"])
        > Decimal(str(authorization["maximum_total_observed_cost"]))
    )
    _require(
        not (any_model_cost_exceeded or total_cost_exceeded)
        or (
            checkpoint["stop_reason"] == "cost_ceiling_exceeded"
            and bool(checkpoint["hard_failure_schedule_keys"])
        ),
        "checkpoint cost ceiling breach was not stopped",
    )
    expected_status, expected_cost_eligibility = _expected_quality_status(
        checkpoint,
        invoked_keys,
    )
    _require(
        checkpoint["quality_gate_status"] == expected_status
        and checkpoint["cost_comparison_eligibility"]
        is expected_cost_eligibility,
        "checkpoint quality or cost eligibility changed",
    )
    _require(
        checkpoint["stop_reason"] in _STOP_REASONS,
        "checkpoint stop reason is unsupported",
    )
    if not invoked_keys or expected_status == "partial":
        _require(
            checkpoint["stop_reason"] is None,
            "nonterminal checkpoint has a stop reason",
        )
    elif expected_status == "passed":
        _require(
            checkpoint["stop_reason"] == "completed",
            "completed checkpoint stop reason is invalid",
        )
    else:
        _require(
            checkpoint["stop_reason"] is not None,
            "stopped checkpoint is missing a reason",
        )
    _require(
        checkpoint["authority_invariants"]
        == _expected_authority(len(invoked_keys)),
        "checkpoint authority invariants changed",
    )
    return True


def serialize_checkpoint(
    checkpoint: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> str:
    payload = deepcopy(checkpoint)
    validate_checkpoint(
        payload,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    return _canonical_json(payload)


def checkpoint_sha256(
    checkpoint: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_checkpoint(
            checkpoint,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
            canary=canary,
        ).encode("utf-8")
    ).hexdigest()


def _next_schedule_row(
    checkpoint: Mapping[str, Any],
    scheduled: Mapping[str, Any],
    canary: Mapping[str, Any],
) -> Dict[str, Any]:
    schedule = canary["schedule"]
    exact = [row for row in schedule if row == dict(scheduled)]
    _require(len(exact) == 1, "schedule row is outside the canary")
    invoked = set().union(
        *(set(checkpoint[field]) for field in _STATE_FIELDS)
    )
    _require(
        not checkpoint["blocked_schedule_keys"]
        and not checkpoint["ambiguous_schedule_keys"]
        and not checkpoint["hard_failure_schedule_keys"]
        and checkpoint["stop_reason"] is None,
        "terminal canary key cannot be resumed",
    )
    _require(
        scheduled["schedule_key"] not in invoked,
        "canary schedule key was already invoked",
    )
    _require(
        scheduled == schedule[len(invoked)],
        "canary transition order is invalid",
    )
    return deepcopy(exact[0])


def _bounded_grade_failures(grade: Mapping[str, Any]) -> Dict[str, int]:
    return {
        key: int(value)
        for key, value in grade["hard_failures"].items()
        if key in _HARD_FAILURE_CATEGORIES and int(value) > 0
    }


def _summary(
    *,
    scheduled: Mapping[str, Any],
    schema_valid: bool,
    quality_gate_passed: bool,
    hard_failures: Mapping[str, int],
    outcome: str,
    latency_ms: float,
    input_tokens: int,
    output_tokens: int,
    observed_cost: Decimal,
) -> Dict[str, Any]:
    return {
        "schedule_key": scheduled["schedule_key"],
        "workload_id": scheduled["workload_id"],
        "provider": scheduled["provider"],
        "model": scheduled["model"],
        "schema_valid": bool(schema_valid),
        "normalization_succeeded": True,
        "quality_gate_passed": bool(quality_gate_passed),
        "hard_failures": dict(hard_failures),
        "provider_outcome_category": outcome,
        "latency_ms": float(latency_ms),
        "input_token_count": input_tokens,
        "output_token_count": output_tokens,
        "observed_cost": _decimal_text(observed_cost),
        "provider_call_count": 1,
    }


def _apply_final_state(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    state_field: str,
    stop_reason: str | None,
    summary: Dict[str, Any] | None,
    canary: Mapping[str, Any],
) -> Dict[str, Any]:
    updated = deepcopy(checkpoint)
    updated[state_field].append(scheduled["schedule_key"])
    if summary is not None:
        updated["grading_summaries"].append(deepcopy(summary))
    invoked = set().union(*(set(updated[field]) for field in _STATE_FIELDS))
    updated["aggregate_usage"] = _recomputed_aggregate(
        invoked_keys=invoked,
        summaries=updated["grading_summaries"],
        canary=canary,
    )
    status, eligible = _expected_quality_status(updated, invoked)
    updated["quality_gate_status"] = status
    updated["cost_comparison_eligibility"] = eligible
    if status == "passed":
        updated["stop_reason"] = "completed"
    elif status in {"stopped", "failed"}:
        updated["stop_reason"] = stop_reason
    else:
        updated["stop_reason"] = None
    updated["authority_invariants"] = _expected_authority(len(invoked))
    return updated


def _validate_transition_start(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    controlled_canary = _validated_inputs(
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    validate_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=controlled_canary,
    )
    row = _next_schedule_row(checkpoint, scheduled, controlled_canary)
    return controlled_canary, row


def record_blocked_call(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    reason: str = "definitive_transport_failure",
    canary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    _require(
        reason in {
            "definitive_transport_failure",
            "provider_model_mismatch",
            "unknown_provider_outcome",
        },
        "blocked reason is unsupported",
    )
    controlled_canary, row = _validate_transition_start(
        checkpoint,
        scheduled=scheduled,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    updated = _apply_final_state(
        checkpoint,
        scheduled=row,
        state_field="blocked_schedule_keys",
        stop_reason=reason,
        summary=None,
        canary=controlled_canary,
    )
    validate_checkpoint(
        updated,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=controlled_canary,
    )
    return deepcopy(updated)


def record_ambiguous_call(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    controlled_canary, row = _validate_transition_start(
        checkpoint,
        scheduled=scheduled,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    updated = _apply_final_state(
        checkpoint,
        scheduled=row,
        state_field="ambiguous_schedule_keys",
        stop_reason="ambiguous_timeout",
        summary=None,
        canary=controlled_canary,
    )
    validate_checkpoint(
        updated,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=controlled_canary,
    )
    return deepcopy(updated)


def record_hard_failure_call(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    reason: str,
    summary: Dict[str, Any] | None = None,
    canary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    _require(
        reason in _STOP_REASONS
        and reason
        not in {None, "completed", "ambiguous_timeout", "definitive_transport_failure"},
        "hard-failure reason is unsupported",
    )
    controlled_canary, row = _validate_transition_start(
        checkpoint,
        scheduled=scheduled,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    if summary is not None:
        _validate_summary(summary, scheduled=row)
        _require(
            summary["quality_gate_passed"] is False,
            "hard-failure summary passed its quality gate",
        )
    updated = _apply_final_state(
        checkpoint,
        scheduled=row,
        state_field="hard_failure_schedule_keys",
        stop_reason=reason,
        summary=summary,
        canary=controlled_canary,
    )
    validate_checkpoint(
        updated,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=controlled_canary,
    )
    return deepcopy(updated)


def _hard_failure_from_invalid_transport(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    reason: str,
    canary: Dict[str, Any],
) -> Dict[str, Any]:
    return record_hard_failure_call(
        checkpoint,
        scheduled=scheduled,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        reason=reason,
        canary=canary,
    )


def record_completed_call(
    checkpoint: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    transport_result: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    controlled_canary, row = _validate_transition_start(
        checkpoint,
        scheduled=scheduled,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    if not isinstance(transport_result, dict) or set(transport_result) != set(
        TRANSPORT_RESULT_FIELDS
    ):
        return _hard_failure_from_invalid_transport(
            checkpoint,
            scheduled=row,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
            reason="unknown_provider_outcome",
            canary=controlled_canary,
        )
    outcome = transport_result.get("provider_outcome_category")
    if outcome != "success":
        reason = _FAILURE_OUTCOME_TO_REASON.get(
            outcome,
            "unknown_provider_outcome",
        )
        if reason == "ambiguous_timeout":
            return record_ambiguous_call(
                checkpoint,
                scheduled=row,
                authorization=authorization,
                pricing=pricing,
                execution_at_utc=execution_at_utc,
                canary=controlled_canary,
            )
        if reason == "definitive_transport_failure":
            return record_blocked_call(
                checkpoint,
                scheduled=row,
                authorization=authorization,
                pricing=pricing,
                execution_at_utc=execution_at_utc,
                canary=controlled_canary,
            )
        return _hard_failure_from_invalid_transport(
            checkpoint,
            scheduled=row,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
            reason=reason,
            canary=controlled_canary,
        )
    try:
        validate_injected_transport_result(transport_result, scheduled=row)
    except ValueError:
        input_value = transport_result.get("input_token_count")
        output_value = transport_result.get("output_token_count")
        if (
            not isinstance(input_value, int)
            or isinstance(input_value, bool)
            or input_value <= 0
            or not isinstance(output_value, int)
            or isinstance(output_value, bool)
            or output_value <= 0
        ):
            reason = "missing_usage_metadata"
        elif (
            transport_result.get("provider") != row["provider"]
            or transport_result.get("model") != row["model"]
        ):
            reason = "provider_model_mismatch"
        else:
            reason = "unknown_provider_outcome"
        return _hard_failure_from_invalid_transport(
            checkpoint,
            scheduled=row,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
            reason=reason,
            canary=controlled_canary,
        )
    input_tokens = transport_result.get("input_token_count")
    output_tokens = transport_result.get("output_token_count")
    if (
        not isinstance(input_tokens, int)
        or isinstance(input_tokens, bool)
        or input_tokens <= 0
        or not isinstance(output_tokens, int)
        or isinstance(output_tokens, bool)
        or output_tokens <= 0
    ):
        return _hard_failure_from_invalid_transport(
            checkpoint,
            scheduled=row,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
            reason="missing_usage_metadata",
            canary=controlled_canary,
        )
    latency_ms = _number(transport_result["latency_ms"], "observed latency")
    token_bounds = controlled_canary["token_bounds"]
    aggregate = checkpoint["aggregate_usage"]
    token_exceeded = (
        input_tokens > token_bounds["maximum_input_tokens_per_request"]
        or output_tokens > token_bounds["maximum_output_tokens_per_request"]
        or aggregate["input_token_count"] + input_tokens
        > token_bounds["maximum_aggregate_input_tokens"]
        or aggregate["output_token_count"] + output_tokens
        > token_bounds["maximum_aggregate_output_tokens"]
    )
    observed_cost = calculate_observed_cost(
        pricing=pricing,
        provider=row["provider"],
        model=row["model"],
        input_token_count=input_tokens,
        output_token_count=output_tokens,
    )
    cases_by_alias, case_ids = _case_maps()
    case = cases_by_alias[row["case_alias"]]
    normalized_output = deepcopy(transport_result["normalized_output"])
    schema_valid = (
        isinstance(normalized_output, dict)
        and all(
            field in normalized_output and normalized_output[field] is not None
            for field in case["required_fields"]
        )
    )
    projection = {
        "case_id": case_ids[row["case_alias"]],
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
    grade = grade_normalized_candidate_result(
        projection,
        corpus=load_fixture_case_corpus(),
    )
    failures = _bounded_grade_failures(grade)
    if not schema_valid:
        failures["schema_invalid"] = 1
    if token_exceeded:
        failures["token_budget_exceeded"] = 1
    model_key = f"{row['provider']}/{row['model']}"
    model_cost = sum(
        (
            Decimal(str(summary["observed_cost"]))
            for summary in checkpoint["grading_summaries"]
            if summary["model"] == row["model"]
        ),
        Decimal("0"),
    ) + observed_cost
    total_cost = (
        Decimal(str(aggregate["observed_cost"])) + observed_cost
    )
    cost_exceeded = (
        model_cost
        > Decimal(
            str(
                authorization["maximum_observed_cost_per_model"][model_key]
            )
        )
        or total_cost
        > Decimal(str(authorization["maximum_total_observed_cost"]))
    )
    if cost_exceeded:
        failures["cost_ceiling_exceeded"] = 1
    if not grade["quality_gate_passed"] and not failures:
        failures["workload_quality_gate_failed"] = 1
    passed = bool(grade["quality_gate_passed"]) and not failures
    summary = _summary(
        scheduled=row,
        schema_valid=schema_valid,
        quality_gate_passed=passed,
        hard_failures=failures,
        outcome="success",
        latency_ms=latency_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        observed_cost=observed_cost,
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
        return record_hard_failure_call(
            checkpoint,
            scheduled=row,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
            reason=reason,
            summary=summary,
            canary=controlled_canary,
        )
    updated = _apply_final_state(
        checkpoint,
        scheduled=row,
        state_field="completed_schedule_keys",
        stop_reason=None,
        summary=summary,
        canary=controlled_canary,
    )
    validate_checkpoint(
        updated,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=controlled_canary,
    )
    return deepcopy(updated)


def _validate_artifact_path(
    artifact_path: str | Path,
    *,
    repository_root: str | Path,
    require_existing: bool | None,
) -> Path:
    root = Path(repository_root).resolve()
    candidate = Path(artifact_path)
    _require(candidate.is_absolute(), "artifact path must be absolute")
    _require(".." not in candidate.parts, "artifact path traversal is prohibited")
    approved = root / APPROVED_ARTIFACT_DIRECTORY
    _require(approved.exists(), "approved artifact directory is missing")
    _require(
        approved.is_dir() and not approved.is_symlink(),
        "approved artifact directory is unsafe",
    )
    _require(
        candidate.parent == approved and candidate.suffix == ".json",
        "artifact path is outside the approved ignored directory",
    )
    current = root
    for part in candidate.relative_to(root).parts[:-1]:
        current = current / part
        _require(
            not current.is_symlink(),
            "artifact path contains a symlink component",
        )
    mode = stat.S_IMODE(approved.stat().st_mode)
    _require(
        mode & stat.S_IWUSR
        and not (mode & (stat.S_IWGRP | stat.S_IWOTH)),
        "artifact parent permissions are unsafe",
    )
    ignore_file = root / ".gitignore"
    _require(ignore_file.is_file(), "repository ignore owner is missing")
    ignore_lines = {
        line.strip() for line in ignore_file.read_text(encoding="utf-8").splitlines()
    }
    _require(
        "outputs/" in ignore_lines or "/outputs/" in ignore_lines,
        "artifact directory is not ignored",
    )
    if require_existing is True:
        _require(
            candidate.is_file() and not candidate.is_symlink(),
            "artifact file is missing or unsafe",
        )
    elif require_existing is False:
        _require(
            not candidate.exists() and not candidate.is_symlink(),
            "artifact overwrite is prohibited",
        )
    return candidate


def _write_exclusive_bytes(path: Path, encoded: bytes) -> None:
    descriptor = os.open(
        path,
        os.O_CREAT | os.O_EXCL | os.O_WRONLY,
        0o600,
    )
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


def load_checkpoint(
    checkpoint_path: str | Path,
    *,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    path = _validate_artifact_path(
        checkpoint_path,
        repository_root=repository_root,
        require_existing=True,
    )
    _require(
        stat.S_IMODE(path.stat().st_mode) == 0o600,
        "checkpoint mode must be 0600",
    )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("persisted checkpoint is malformed") from None
    validate_checkpoint(
        payload,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    return deepcopy(payload)


def write_initial_checkpoint(
    checkpoint_path: str | Path,
    checkpoint: Dict[str, Any],
    *,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> Path:
    path = _validate_artifact_path(
        checkpoint_path,
        repository_root=repository_root,
        require_existing=False,
    )
    encoded = serialize_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    ).encode("utf-8")
    _write_exclusive_bytes(path, encoded)
    load_checkpoint(
        path,
        repository_root=repository_root,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    return path


def replace_checkpoint_atomic(
    checkpoint_path: str | Path,
    checkpoint: Dict[str, Any],
    *,
    expected_prior_sha256: str,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> Path:
    path = _validate_artifact_path(
        checkpoint_path,
        repository_root=repository_root,
        require_existing=True,
    )
    prior = load_checkpoint(
        path,
        repository_root=repository_root,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    observed_prior = checkpoint_sha256(
        prior,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    _require(
        isinstance(expected_prior_sha256, str)
        and expected_prior_sha256 == observed_prior,
        "checkpoint prior digest mismatch",
    )
    encoded = serialize_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
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
        current = load_checkpoint(
            path,
            repository_root=repository_root,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
            canary=canary,
        )
        current_sha = checkpoint_sha256(
            current,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
            canary=canary,
        )
        _require(
            current_sha == expected_prior_sha256,
            "checkpoint changed before atomic replacement",
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
    loaded = load_checkpoint(
        path,
        repository_root=repository_root,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    _require(
        loaded == checkpoint,
        "atomic checkpoint replacement did not persist exact state",
    )
    return path


def build_result_artifact(
    *,
    checkpoint: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    controlled_canary = _validated_inputs(
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    validate_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=controlled_canary,
    )
    state_counts = {
        field.removesuffix("_schedule_keys"): len(checkpoint[field])
        for field in _STATE_FIELDS
    }
    _require(
        sum(state_counts.values()) == 4
        or checkpoint["stop_reason"] is not None,
        "result requires a terminal checkpoint",
    )
    if state_counts["completed"] == 4:
        final_status = "completed"
    elif state_counts["ambiguous"]:
        final_status = "stopped_ambiguous"
    elif state_counts["hard_failure"]:
        final_status = "stopped_hard_failure"
    else:
        final_status = "stopped_blocked"
    artifact = {
        "result_schema_version": RESULT_SCHEMA_VERSION,
        "evidence_runtime_version": EVIDENCE_RUNTIME_VERSION,
        "canary_version": CANARY_VERSION,
        "canary_sha256": controlled_groq_canary_sha256(controlled_canary),
        "transport_version": TRANSPORT_VERSION,
        "transport_sha256": controlled_groq_transport_sha256(),
        "authorization_sha256": _canonical_sha256(authorization),
        "pricing_sha256": pricing_table_sha256(pricing),
        "checkpoint": deepcopy(checkpoint),
        "final_status": final_status,
        "state_counts": state_counts,
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
    validate_result_artifact(
        artifact,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=controlled_canary,
    )
    return deepcopy(artifact)


def validate_result_artifact(
    artifact: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> bool:
    controlled_canary = _validated_inputs(
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    _require(
        isinstance(artifact, dict) and set(artifact) == _RESULT_FIELDS,
        "result fields must match the exact schema",
    )
    _require(
        not _contains_prohibited_evidence(artifact),
        "result contains prohibited evidence",
    )
    checkpoint = artifact["checkpoint"]
    validate_checkpoint(
        checkpoint,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=controlled_canary,
    )
    _require(
        artifact["result_schema_version"] == RESULT_SCHEMA_VERSION
        and artifact["evidence_runtime_version"] == EVIDENCE_RUNTIME_VERSION
        and artifact["canary_version"] == CANARY_VERSION
        and artifact["canary_sha256"]
        == controlled_groq_canary_sha256(controlled_canary)
        and artifact["transport_version"] == TRANSPORT_VERSION
        and artifact["transport_sha256"] == controlled_groq_transport_sha256()
        and artifact["authorization_sha256"]
        == _canonical_sha256(authorization)
        and artifact["pricing_sha256"] == pricing_table_sha256(pricing),
        "result ownership identifiers changed",
    )
    expected_counts = {
        field.removesuffix("_schedule_keys"): len(checkpoint[field])
        for field in _STATE_FIELDS
    }
    if expected_counts["completed"] == 4:
        expected_status = "completed"
    elif expected_counts["ambiguous"]:
        expected_status = "stopped_ambiguous"
    elif expected_counts["hard_failure"]:
        expected_status = "stopped_hard_failure"
    else:
        expected_status = "stopped_blocked"
    _require(
        artifact["state_counts"] == expected_counts
        and artifact["final_status"] == expected_status
        and artifact["aggregate_usage"] == checkpoint["aggregate_usage"]
        and artifact["grading_summaries"] == checkpoint["grading_summaries"]
        and artifact["quality_gate_status"] == checkpoint["quality_gate_status"]
        and artifact["cost_comparison_eligibility"]
        is checkpoint["cost_comparison_eligibility"],
        "result and checkpoint evidence disagree",
    )
    _require(
        artifact["winner_selected"] is False
        and artifact["production_activation"] is False
        and artifact["mutation_count"] == 0
        and artifact["application_action_count"] == 0
        and artifact["ats_action_count"] == 0,
        "result authority changed",
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
        "result retention policy changed",
    )
    return True


def serialize_result_artifact(
    artifact: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> str:
    payload = deepcopy(artifact)
    validate_result_artifact(
        payload,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    return _canonical_json(payload)


def result_sha256(
    artifact: Dict[str, Any],
    *,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_result_artifact(
            artifact,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=execution_at_utc,
            canary=canary,
        ).encode("utf-8")
    ).hexdigest()


def load_result_artifact(
    result_path: str | Path,
    *,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    path = _validate_artifact_path(
        result_path,
        repository_root=repository_root,
        require_existing=True,
    )
    _require(
        stat.S_IMODE(path.stat().st_mode) == 0o600,
        "result mode must be 0600",
    )
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        raise ValueError("persisted result is malformed") from None
    validate_result_artifact(
        payload,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    return deepcopy(payload)


def write_result_exclusive(
    result_path: str | Path,
    artifact: Dict[str, Any],
    *,
    repository_root: str | Path,
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
    canary: Dict[str, Any] | None = None,
) -> Path:
    path = _validate_artifact_path(
        result_path,
        repository_root=repository_root,
        require_existing=False,
    )
    encoded = serialize_result_artifact(
        artifact,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    ).encode("utf-8")
    _write_exclusive_bytes(path, encoded)
    load_result_artifact(
        path,
        repository_root=repository_root,
        authorization=authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        canary=canary,
    )
    return path
