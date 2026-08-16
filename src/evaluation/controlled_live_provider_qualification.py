"""Explicit, default-off gate for future controlled live qualification.

Importing and building this evaluation-only contract performs no credential
read, client construction, network call, registry mutation, or persistence.
Only ``execute_controlled_live_qualification`` can dispatch, and it requires
an exact live authorization, current pricing, an explicit schedule subset,
and caller-supplied operator evaluation credentials.
"""

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
from time import monotonic
from typing import Any, Callable, Dict, Iterable, Mapping, Sequence

from src.evaluation.controlled_production_parity_benchmark import (
    PRODUCTION_PARITY_BLOCKED_WORKLOADS,
    PRODUCTION_PARITY_RUNNABLE_WORKLOADS,
    build_production_parity_request,
    validate_and_grade_production_parity_response,
    validate_production_parity_request,
    validate_production_parity_result,
)
from src.evaluation.controlled_provider_benchmark_harness import (
    _schedule_from_plan,
)
from src.evaluation.controlled_provider_benchmark_human_review import (
    build_subjective_qualification_review_packet,
    canonical_human_review_requirements,
    write_subjective_qualification_review_packet_exclusive,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    build_transmittable_request_packet,
    controlled_provider_benchmark_plan_sha256,
    validate_controlled_provider_benchmark_plan,
)
from src.evaluation.production_task_contract_fingerprints import (
    build_all_production_task_contract_fingerprints,
)
from src.evaluation.provider_benchmark_contract import (
    MODEL_ORDER,
    WORKLOAD_ORDER,
    provider_benchmark_contract_sha256,
)


LIVE_QUALIFICATION_GATE_VERSION = "controlled-live-qualification-gate-v1"
LIVE_AUTHORIZATION_VERSION = "controlled-live-qualification-authorization-v1"
LIVE_PRICING_VERSION = "controlled-live-qualification-pricing-v1"
LIVE_EVIDENCE_VERSION = "controlled-live-qualification-evidence-v1"
LIVE_VALIDATION_CONTEXT_VERSION = (
    "controlled-live-qualification-validation-context-v1"
)
LIVE_PRICING_SOURCE_CLASSIFICATION = "operator_current_live_qualification"
APPROVED_EVIDENCE_DIRECTORY = Path("outputs/provider_qualification")

_PAIR_FIELDS = {"provider", "model"}
_PRICE_FIELDS = {
    "provider",
    "model",
    "input_price_per_million_tokens",
    "output_price_per_million_tokens",
}
_PRICING_FIELDS = {
    "pricing_schema_version",
    "pricing_version",
    "source_classification",
    "source_effective_at_utc",
    "valid_from_utc",
    "expires_at_utc",
    "currency",
    "prices",
    "operator_approved",
    "pricing_table_sha256",
}
_TOKEN_CEILING_FIELDS = {
    "maximum_input_tokens_per_request",
    "maximum_output_tokens_per_request",
    "maximum_total_observed_input_tokens",
    "maximum_total_observed_output_tokens",
}
_AUTHORIZATION_FIELDS = {
    "authorization_version",
    "benchmark_contract_sha256",
    "controlled_plan_sha256",
    "model_catalog_snapshot_sha256",
    "fixture_corpus_sha256",
    "approved_schedule_keys",
    "approved_provider_model_pairs",
    "approved_workload_ids",
    "production_task_contract_fingerprints",
    "valid_from_utc",
    "expires_at_utc",
    "maximum_request_count",
    "token_ceilings",
    "maximum_cost_per_provider_model",
    "maximum_total_cost",
    "pricing_table_sha256",
    "serial_execution_required",
    "fallback_allowed",
    "retry_limit",
    "production_activation_forbidden",
    "application_mutation_forbidden",
    "ats_mutation_forbidden",
    "automatic_persistence_allowed",
    "operator_approved",
}
_TRANSPORT_RESULT_FIELDS = {
    "parity_result",
    "provider",
    "model",
    "latency_ms",
    "input_token_count",
    "output_token_count",
    "provider_outcome_category",
}
_SUMMARY_FIELDS = {
    "schedule_key",
    "case_alias",
    "workload_id",
    "provider",
    "model",
    "production_task_contract_sha256",
    "production_contract_valid",
    "benchmark_quality_passed",
    "hard_failure_present",
    "human_review_required",
    "provider_outcome_category",
    "latency_ms",
    "input_token_count",
    "output_token_count",
    "observed_cost",
}
_EVIDENCE_FIELDS = {
    "evidence_version",
    "gate_version",
    "execution_mode",
    "execution_at_utc",
    "benchmark_contract_sha256",
    "controlled_plan_sha256",
    "model_catalog_snapshot_sha256",
    "fixture_corpus_sha256",
    "authorization_sha256",
    "pricing_sha256",
    "approved_schedule_keys",
    "requested_schedule_keys",
    "attempted_schedule_keys",
    "completed_schedule_keys",
    "blocked_schedule_keys",
    "ambiguous_schedule_keys",
    "execution_status",
    "stop_reason",
    "aggregate_usage",
    "grading_summaries",
    "retention_policy",
    "authority_invariants",
}
_VALIDATION_CONTEXT_FIELDS = {
    "context_version",
    "evidence_sha256",
    "authorization_sha256",
    "pricing_sha256",
    "live_authorization",
    "live_pricing",
}
_PROHIBITED_SERIALIZED_KEYS = {
    "api_key",
    "credential",
    "credentials",
    "environment",
    "header",
    "headers",
    "messages",
    "normalized_output",
    "operator_credentials",
    "prompt",
    "raw_exception",
    "raw_request",
    "raw_response",
    "reasoning",
    "request_id",
    "request_packet",
    "response_envelope",
    "sdk_object",
    "synthetic_input",
}
_BOUNDED_TRANSPORT_FAILURE_STOP_REASONS = frozenset(
    {
        "definitive_authentication_failure",
        "definitive_configuration_failure",
        "definitive_connection_failure",
        "definitive_invalid_request",
        "definitive_provider_rejection",
        "definitive_transport_failure",
        "input_usage_ceiling_exceeded",
        "invalid_latency_measurement",
        "malformed_choice_count",
        "malformed_empty_content",
        "malformed_json_content",
        "missing_input_usage",
        "missing_output_usage",
        "output_usage_ceiling_exceeded",
        "provider_model_mismatch",
        "schema_incompatible_content",
    }
)
_STOP_REASONS = {
    None,
    "ambiguous_timeout",
    "cost_ceiling_exceeded",
    "hard_safety_failure",
    "missing_usage_metadata",
    "request_budget_exceeded",
    "token_budget_exceeded",
    "unknown_provider_outcome",
} | _BOUNDED_TRANSPORT_FAILURE_STOP_REASONS


class LiveQualificationAmbiguousTimeout(RuntimeError):
    """The provider may have received the single authorized request."""


class LiveQualificationDefinitiveFailure(RuntimeError):
    """The provider definitively rejected the single authorized request."""


class LiveQualificationUnknownOutcome(RuntimeError):
    """The provider outcome cannot be safely classified."""


class LiveQualificationPersistenceFailure(RuntimeError):
    """Evidence persisted, but its requested validation context did not."""


def _bounded_transport_failure_stop_reason(value: Any) -> str:
    category = str(value).strip()
    if category in _BOUNDED_TRANSPORT_FAILURE_STOP_REASONS:
        return category
    return "unknown_provider_outcome"


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


def _sha256(value: Any) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _parse_utc(value: Any) -> datetime:
    text = _clean(value)
    _require(bool(text), "bounded UTC timestamp is required")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("bounded UTC timestamp is malformed") from exc
    _require(parsed.tzinfo is not None, "UTC timestamp requires timezone")
    return parsed.astimezone(timezone.utc)


def _decimal(value: Any, label: str, *, positive: bool = False) -> Decimal:
    _require(not isinstance(value, bool), f"{label} must be numeric")
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{label} must be numeric") from exc
    _require(number.is_finite(), f"{label} must be finite")
    _require(number > 0 if positive else number >= 0, f"{label} is invalid")
    return number


def _iter_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield _clean(key).lower()
            yield from _iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_keys(item)


def _contains_prohibited_serialized_key(value: Any) -> bool:
    return any(key in _PROHIBITED_SERIALIZED_KEYS for key in _iter_keys(value))


def _iter_strings(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for item in value.values():
            yield from _iter_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_strings(item)
    elif isinstance(value, str):
        yield value


def _contains_secret_like_serialized_value(value: Any) -> bool:
    markers = ("gsk_", "sk-", "bearer ")
    return any(
        marker in text.strip().lower()
        for text in _iter_strings(value)
        for marker in markers
    )


def _ordered_unique(values: Iterable[Any]) -> list[Any]:
    result: list[Any] = []
    for value in values:
        if value not in result:
            result.append(value)
    return result


def build_live_qualification_universe(
    plan: Dict[str, Any] | None = None,
) -> list[Dict[str, Any]]:
    """Derive all 44 historical rows and their current live eligibility."""

    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    validate_controlled_provider_benchmark_plan(controlled_plan)
    fingerprints = build_all_production_task_contract_fingerprints()
    rows = []
    for scheduled in _schedule_from_plan(controlled_plan):
        workload_id = scheduled["workload_id"]
        fingerprint = fingerprints[workload_id]
        eligible = (
            workload_id in PRODUCTION_PARITY_RUNNABLE_WORKLOADS
            and fingerprint is not None
        )
        rows.append(
            {
                **deepcopy(scheduled),
                "provider_sdk_retry_limit": 0,
                "production_task_contract_sha256": fingerprint,
                "live_qualification_eligible": eligible,
                "live_block_reason": (
                    None if eligible else "production_parity_contract_missing"
                ),
            }
        )
    _require(len(rows) == 44, "canonical historical plan size changed")
    _require(
        sum(row["live_qualification_eligible"] for row in rows) == 44,
        "production-qualifiable universe size changed",
    )
    _require(
        {
            row["workload_id"]
            for row in rows
            if not row["live_qualification_eligible"]
        }
        == set(PRODUCTION_PARITY_BLOCKED_WORKLOADS),
        "live-blocked workload set changed",
    )
    return deepcopy(rows)


def _eligible_rows_by_key(plan: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {
        row["schedule_key"]: row
        for row in build_live_qualification_universe(plan)
        if row["live_qualification_eligible"]
    }


def build_live_authorization_template(
    *,
    approved_schedule_keys: Sequence[str],
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Build a safe, unapproved, zero-authority authorization template."""

    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    eligible = _eligible_rows_by_key(controlled_plan)
    keys = list(approved_schedule_keys)
    _require(bool(keys) and len(keys) == len(set(keys)), "approved schedule keys are invalid")
    _require(set(keys).issubset(eligible), "live-blocked schedule key is prohibited")
    canonical_order = [row["schedule_key"] for row in eligible.values() if row["schedule_key"] in keys]
    _require(keys == canonical_order, "approved schedule keys must use canonical order")
    rows = [eligible[key] for key in keys]
    pairs = _ordered_unique(
        (row["provider"], row["model"])
        for row in rows
    )
    workloads = _ordered_unique(row["workload_id"] for row in rows)
    fingerprints = build_all_production_task_contract_fingerprints()
    return {
        "authorization_version": LIVE_AUTHORIZATION_VERSION,
        "benchmark_contract_sha256": provider_benchmark_contract_sha256(),
        "controlled_plan_sha256": controlled_provider_benchmark_plan_sha256(
            controlled_plan
        ),
        "model_catalog_snapshot_sha256": controlled_plan[
            "model_catalog_snapshot_sha256"
        ],
        "fixture_corpus_sha256": controlled_plan[
            "step8o_case_corpus_sha256"
        ],
        "approved_schedule_keys": keys,
        "approved_provider_model_pairs": [
            {"provider": provider, "model": model}
            for provider, model in pairs
        ],
        "approved_workload_ids": workloads,
        "production_task_contract_fingerprints": {
            workload_id: fingerprints[workload_id]
            for workload_id in workloads
        },
        "valid_from_utc": None,
        "expires_at_utc": None,
        "maximum_request_count": 0,
        "token_ceilings": {
            field: 0 for field in sorted(_TOKEN_CEILING_FIELDS)
        },
        "maximum_cost_per_provider_model": {
            f"{provider}/{model}": 0 for provider, model in pairs
        },
        "maximum_total_cost": 0,
        "pricing_table_sha256": None,
        "serial_execution_required": True,
        "fallback_allowed": False,
        "retry_limit": 0,
        "production_activation_forbidden": True,
        "application_mutation_forbidden": True,
        "ats_mutation_forbidden": True,
        "automatic_persistence_allowed": False,
        "operator_approved": False,
    }


def live_authorization_sha256(authorization: Dict[str, Any]) -> str:
    _require(
        isinstance(authorization, dict)
        and set(authorization) == _AUTHORIZATION_FIELDS,
        "live authorization fields must match the exact schema",
    )
    _require(
        not _contains_prohibited_serialized_key(authorization),
        "live authorization contains prohibited secret material",
    )
    return _sha256(authorization)


def build_live_pricing_template(
    *,
    approved_provider_model_pairs: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    pairs = [
        (_clean(row.get("provider")).lower(), _clean(row.get("model")))
        for row in approved_provider_model_pairs
        if isinstance(row, Mapping) and set(row) == _PAIR_FIELDS
    ]
    _require(
        len(pairs) == len(approved_provider_model_pairs)
        and bool(pairs)
        and len(pairs) == len(set(pairs))
        and all(pair in MODEL_ORDER for pair in pairs),
        "pricing provider/model scope is invalid",
    )
    pricing = {
        "pricing_schema_version": LIVE_PRICING_VERSION,
        "pricing_version": None,
        "source_classification": None,
        "source_effective_at_utc": None,
        "valid_from_utc": None,
        "expires_at_utc": None,
        "currency": "USD",
        "prices": [
            {
                "provider": provider,
                "model": model,
                "input_price_per_million_tokens": 0,
                "output_price_per_million_tokens": 0,
            }
            for provider, model in pairs
        ],
        "operator_approved": False,
        "pricing_table_sha256": None,
    }
    pricing["pricing_table_sha256"] = live_pricing_sha256(pricing)
    return pricing


def live_pricing_sha256(pricing: Dict[str, Any]) -> str:
    _require(isinstance(pricing, dict), "live pricing must be an object")
    material = deepcopy(pricing)
    material.pop("pricing_table_sha256", None)
    return _sha256(material)


def validate_live_pricing(
    pricing: Dict[str, Any] | None,
    *,
    authorization: Dict[str, Any],
    execution_at_utc: str,
) -> bool:
    _require(isinstance(pricing, dict), "current live pricing is required")
    _require(set(pricing) == _PRICING_FIELDS, "live pricing fields are invalid")
    _require(
        pricing.get("pricing_schema_version") == LIVE_PRICING_VERSION,
        "live pricing schema version mismatch",
    )
    _require(bool(_clean(pricing.get("pricing_version"))), "live pricing version is required")
    _require(
        pricing.get("source_classification") == LIVE_PRICING_SOURCE_CLASSIFICATION,
        "synthetic or non-current pricing is prohibited",
    )
    source_effective = _parse_utc(pricing.get("source_effective_at_utc"))
    valid_from = _parse_utc(pricing.get("valid_from_utc"))
    expires_at = _parse_utc(pricing.get("expires_at_utc"))
    execution_at = _parse_utc(execution_at_utc)
    _require(
        source_effective <= execution_at and valid_from < expires_at,
        "live pricing validity window is invalid",
    )
    _require(
        valid_from <= execution_at <= expires_at,
        "live pricing is expired or not yet valid",
    )
    _require(pricing.get("currency") == "USD", "live pricing currency is unsupported")
    _require(pricing.get("operator_approved") is True, "live pricing approval is required")
    expected_pairs = [
        (row["provider"], row["model"])
        for row in authorization["approved_provider_model_pairs"]
    ]
    rows = pricing.get("prices")
    _require(
        isinstance(rows, list)
        and all(isinstance(row, dict) and set(row) == _PRICE_FIELDS for row in rows),
        "live pricing rows are invalid",
    )
    observed_pairs = [
        (_clean(row.get("provider")).lower(), _clean(row.get("model")))
        for row in rows
    ]
    _require(observed_pairs == expected_pairs, "live pricing provider/model scope mismatch")
    for row in rows:
        _decimal(row["input_price_per_million_tokens"], "live input price", positive=True)
        _decimal(row["output_price_per_million_tokens"], "live output price", positive=True)
    _require(
        pricing.get("pricing_table_sha256") == live_pricing_sha256(pricing),
        "live pricing digest mismatch",
    )
    return True


def validate_live_authorization(
    authorization: Dict[str, Any] | None,
    *,
    plan: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> bool:
    controlled_plan = deepcopy(plan)
    validate_controlled_provider_benchmark_plan(controlled_plan)
    _require(isinstance(authorization, dict), "live authorization is required")
    live_authorization_sha256(authorization)
    keys = authorization["approved_schedule_keys"]
    _require(isinstance(keys, list) and bool(keys), "approved schedule keys are required")
    template = build_live_authorization_template(
        approved_schedule_keys=keys,
        plan=controlled_plan,
    )
    operator_fields = {
        "valid_from_utc",
        "expires_at_utc",
        "maximum_request_count",
        "token_ceilings",
        "maximum_cost_per_provider_model",
        "maximum_total_cost",
        "pricing_table_sha256",
        "operator_approved",
    }
    _require(
        all(
            authorization[field] == template[field]
            for field in _AUTHORIZATION_FIELDS - operator_fields
        ),
        "live authorization identity or authority binding mismatch",
    )
    _require(authorization["operator_approved"] is True, "operator approval is required")
    valid_from = _parse_utc(authorization["valid_from_utc"])
    expires_at = _parse_utc(authorization["expires_at_utc"])
    execution_at = _parse_utc(execution_at_utc)
    _require(valid_from < expires_at, "live authorization validity window is invalid")
    _require(
        valid_from <= execution_at <= expires_at,
        "live authorization is expired or not yet valid",
    )
    _require(
        authorization["maximum_request_count"] == len(keys),
        "live authorization request count must equal its exact schedule scope",
    )
    ceilings = authorization["token_ceilings"]
    plan_ceilings = controlled_plan["token_budget_schema"]
    _require(
        isinstance(ceilings, dict) and set(ceilings) == _TOKEN_CEILING_FIELDS,
        "live token ceilings are incomplete",
    )
    for field in _TOKEN_CEILING_FIELDS:
        value = ceilings[field]
        _require(
            isinstance(value, int)
            and not isinstance(value, bool)
            and 0 < value <= plan_ceilings[field],
            "live token ceiling is invalid",
        )
    _require(
        ceilings["maximum_total_observed_input_tokens"]
        >= ceilings["maximum_input_tokens_per_request"]
        and ceilings["maximum_total_observed_output_tokens"]
        >= ceilings["maximum_output_tokens_per_request"],
        "live total token ceilings are too small",
    )
    per_model = authorization["maximum_cost_per_provider_model"]
    expected_model_keys = {
        f"{row['provider']}/{row['model']}"
        for row in authorization["approved_provider_model_pairs"]
    }
    _require(
        isinstance(per_model, dict) and set(per_model) == expected_model_keys,
        "live per-model cost ceilings are incomplete",
    )
    per_model_values = [
        _decimal(value, "live per-model cost ceiling", positive=True)
        for value in per_model.values()
    ]
    total = _decimal(authorization["maximum_total_cost"], "live total cost ceiling", positive=True)
    _require(total <= sum(per_model_values, Decimal("0")), "live total cost ceiling is unbounded")
    validate_live_pricing(
        pricing,
        authorization=authorization,
        execution_at_utc=execution_at_utc,
    )
    _require(
        authorization["pricing_table_sha256"] == live_pricing_sha256(pricing),
        "live authorization pricing binding mismatch",
    )
    return True


def _pricing_map(pricing: Mapping[str, Any]) -> Dict[str, tuple[Decimal, Decimal]]:
    return {
        f"{row['provider']}/{row['model']}": (
            _decimal(row["input_price_per_million_tokens"], "input price", positive=True),
            _decimal(row["output_price_per_million_tokens"], "output price", positive=True),
        )
        for row in pricing["prices"]
    }


def _cost(input_tokens: int, output_tokens: int, prices: tuple[Decimal, Decimal]) -> Decimal:
    return (
        Decimal(input_tokens) * prices[0]
        + Decimal(output_tokens) * prices[1]
    ) / Decimal("1000000")


def _default_dispatch(
    *,
    provider: str,
    api_key: str,
    parity_request: Dict[str, Any],
    scheduled: Mapping[str, Any],
    plan: Dict[str, Any],
    monotonic_clock: Callable[[], float],
) -> Dict[str, Any]:
    consumer = lambda response: validate_and_grade_production_parity_response(
        parity_request,
        response,
        plan=plan,
    )
    try:
        if provider == "groq":
            from src.evaluation import controlled_groq_canary_transport as transport

            return transport.execute_groq_production_parity_chat_completion_once(
                api_key=api_key,
                parity_request=parity_request,
                scheduled=scheduled,
                parity_response_consumer=consumer,
                monotonic_clock=monotonic_clock,
                plan=plan,
            )
        if provider == "openai":
            from src.evaluation import controlled_openai_canary_transport as transport

            return transport.execute_openai_production_parity_chat_completion_once(
                api_key=api_key,
                parity_request=parity_request,
                scheduled=scheduled,
                parity_response_consumer=consumer,
                monotonic_clock=monotonic_clock,
                plan=plan,
            )
    except Exception as exc:
        name = exc.__class__.__name__
        if name == "AmbiguousTransportTimeout":
            raise LiveQualificationAmbiguousTimeout("ambiguous_timeout") from None
        if name == "DefinitiveTransportFailure":
            category = _bounded_transport_failure_stop_reason(exc)
            if category == "unknown_provider_outcome":
                raise LiveQualificationUnknownOutcome(category) from None
            raise LiveQualificationDefinitiveFailure(category) from None
        if name == "UnknownProviderOutcome":
            raise LiveQualificationUnknownOutcome("unknown_provider_outcome") from None
        raise
    raise LiveQualificationDefinitiveFailure("unsupported_provider")


def _empty_evidence(
    *,
    execution_at_utc: str,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    requested_schedule_keys: list[str],
) -> Dict[str, Any]:
    return {
        "evidence_version": LIVE_EVIDENCE_VERSION,
        "gate_version": LIVE_QUALIFICATION_GATE_VERSION,
        "execution_mode": "controlled_live_operator_qualification",
        "execution_at_utc": execution_at_utc,
        "benchmark_contract_sha256": provider_benchmark_contract_sha256(),
        "controlled_plan_sha256": controlled_provider_benchmark_plan_sha256(plan),
        "model_catalog_snapshot_sha256": plan["model_catalog_snapshot_sha256"],
        "fixture_corpus_sha256": plan["step8o_case_corpus_sha256"],
        "authorization_sha256": live_authorization_sha256(authorization),
        "pricing_sha256": live_pricing_sha256(pricing),
        "approved_schedule_keys": deepcopy(authorization["approved_schedule_keys"]),
        "requested_schedule_keys": deepcopy(requested_schedule_keys),
        "attempted_schedule_keys": [],
        "completed_schedule_keys": [],
        "blocked_schedule_keys": [],
        "ambiguous_schedule_keys": [],
        "execution_status": "stopped",
        "stop_reason": None,
        "aggregate_usage": {
            "provider_call_count": 0,
            "input_token_count": 0,
            "output_token_count": 0,
            "observed_cost": 0.0,
            "observed_cost_by_provider_model": {
                key: 0.0
                for key in authorization["maximum_cost_per_provider_model"]
            },
        },
        "grading_summaries": [],
        "retention_policy": {
            "automatic_persistence": False,
            "explicit_persistence_required": True,
            "required_file_mode": "0600",
            "overwrite_allowed": False,
        },
        "authority_invariants": {
            "fallback_activation_count": 0,
            "retry_count": 0,
            "registry_mutation_count": 0,
            "human_review_fabricated_count": 0,
            "qualification_promotion_count": 0,
            "recommendation_count": 0,
            "routing_change_count": 0,
            "application_mutation_count": 0,
            "ats_mutation_count": 0,
            "raw_response_persisted_count": 0,
            "raw_request_persisted_count": 0,
        },
    }


def validate_live_qualification_evidence(
    evidence: Dict[str, Any],
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> bool:
    _require(isinstance(evidence, dict) and set(evidence) == _EVIDENCE_FIELDS, "live evidence fields are invalid")
    _require(not _contains_prohibited_serialized_key(evidence), "live evidence contains prohibited material")
    _require(evidence["evidence_version"] == LIVE_EVIDENCE_VERSION, "live evidence version mismatch")
    _require(evidence["gate_version"] == LIVE_QUALIFICATION_GATE_VERSION, "live gate version mismatch")
    _require(evidence["execution_mode"] == "controlled_live_operator_qualification", "live execution mode mismatch")
    validate_live_authorization(
        authorization,
        plan=plan,
        pricing=pricing,
        execution_at_utc=evidence["execution_at_utc"],
    )
    _require(evidence["benchmark_contract_sha256"] == provider_benchmark_contract_sha256(), "live evidence benchmark binding mismatch")
    _require(evidence["controlled_plan_sha256"] == controlled_provider_benchmark_plan_sha256(plan), "live evidence plan binding mismatch")
    _require(evidence["model_catalog_snapshot_sha256"] == plan["model_catalog_snapshot_sha256"], "live evidence catalog binding mismatch")
    _require(evidence["fixture_corpus_sha256"] == plan["step8o_case_corpus_sha256"], "live evidence corpus binding mismatch")
    _require(evidence["authorization_sha256"] == live_authorization_sha256(authorization), "live evidence authorization binding mismatch")
    _require(evidence["pricing_sha256"] == live_pricing_sha256(pricing), "live evidence pricing binding mismatch")
    approved = authorization["approved_schedule_keys"]
    requested = evidence["requested_schedule_keys"]
    _require(evidence["approved_schedule_keys"] == approved, "live evidence approved scope mismatch")
    _require(isinstance(requested, list) and bool(requested) and set(requested).issubset(approved), "live evidence requested scope mismatch")
    attempted = evidence["attempted_schedule_keys"]
    completed = evidence["completed_schedule_keys"]
    blocked = evidence["blocked_schedule_keys"]
    ambiguous = evidence["ambiguous_schedule_keys"]
    _require(
        all(isinstance(value, list) and len(value) == len(set(value)) for value in (attempted, completed, blocked, ambiguous)),
        "live evidence schedule states are invalid",
    )
    _require(set(attempted).issubset(requested), "live evidence attempted scope expanded")
    _require(not (set(completed) & set(blocked) or set(completed) & set(ambiguous) or set(blocked) & set(ambiguous)), "live evidence schedule states overlap")
    _require(set(completed) | set(blocked) | set(ambiguous) == set(attempted), "live evidence final states are incomplete")
    _require(evidence["stop_reason"] in _STOP_REASONS, "live evidence stop reason is invalid")
    _require(evidence["execution_status"] in {"completed", "stopped"}, "live evidence status is invalid")
    aggregate = evidence["aggregate_usage"]
    _require(
        isinstance(aggregate, dict)
        and set(aggregate)
        == {
            "provider_call_count",
            "input_token_count",
            "output_token_count",
            "observed_cost",
            "observed_cost_by_provider_model",
        }
        and aggregate["provider_call_count"] == len(attempted),
        "live evidence aggregate is invalid",
    )
    for field in ("input_token_count", "output_token_count"):
        _require(isinstance(aggregate[field], int) and aggregate[field] >= 0, "live evidence usage is invalid")
    _decimal(aggregate["observed_cost"], "live evidence cost")
    _require(set(aggregate["observed_cost_by_provider_model"]) == set(authorization["maximum_cost_per_provider_model"]), "live evidence per-model cost scope mismatch")
    summaries = evidence["grading_summaries"]
    _require(
        isinstance(summaries, list)
        and all(
            isinstance(row, dict) and set(row) == _SUMMARY_FIELDS
            for row in summaries
        ),
        "live evidence grading summaries are invalid",
    )
    summary_keys = [row["schedule_key"] for row in summaries]
    _require(
        len(summary_keys) == len(set(summary_keys))
        and set(summary_keys).issubset(set(attempted)),
        "live evidence grading summary scope is invalid",
    )
    universe = {
        row["schedule_key"]: row
        for row in build_live_qualification_universe(plan)
    }
    review_requirements = canonical_human_review_requirements()
    for summary in summaries:
        scheduled = universe[summary["schedule_key"]]
        for field in ("case_alias", "workload_id", "provider", "model"):
            _require(
                summary[field] == scheduled[field],
                "live evidence grading identity mismatch",
            )
        _require(
            summary["production_task_contract_sha256"]
            == scheduled["production_task_contract_sha256"],
            "live evidence task fingerprint mismatch",
        )
        _require(
            isinstance(summary["production_contract_valid"], bool)
            and isinstance(summary["benchmark_quality_passed"], bool)
            and isinstance(summary["hard_failure_present"], bool)
            and summary["human_review_required"]
            is review_requirements[summary["workload_id"]]
            and summary["provider_outcome_category"] == "success",
            "live evidence grading state is invalid",
        )
        _require(
            isinstance(summary["input_token_count"], int)
            and summary["input_token_count"] > 0
            and isinstance(summary["output_token_count"], int)
            and summary["output_token_count"] > 0,
            "live evidence observed usage is invalid",
        )
        _decimal(summary["latency_ms"], "live evidence latency")
        _decimal(summary["observed_cost"], "live evidence observed cost")
    _require(
        set(completed).issubset(summary_keys),
        "completed live cells require grading evidence",
    )
    _require(
        aggregate["input_token_count"]
        == sum(row["input_token_count"] for row in summaries)
        and aggregate["output_token_count"]
        == sum(row["output_token_count"] for row in summaries),
        "live evidence aggregate usage is inconsistent",
    )
    summary_cost = sum(
        (Decimal(str(row["observed_cost"])) for row in summaries),
        Decimal("0"),
    )
    _require(
        Decimal(str(aggregate["observed_cost"])) == summary_cost,
        "live evidence aggregate cost is inconsistent",
    )
    expected_model_cost = {
        key: Decimal("0")
        for key in authorization["maximum_cost_per_provider_model"]
    }
    for summary in summaries:
        key = f"{summary['provider']}/{summary['model']}"
        expected_model_cost[key] += Decimal(str(summary["observed_cost"]))
    _require(
        all(
            Decimal(str(aggregate["observed_cost_by_provider_model"][key]))
            == value
            for key, value in expected_model_cost.items()
        ),
        "live evidence per-model cost is inconsistent",
    )
    _require(
        (
            evidence["execution_status"] == "completed"
            and evidence["stop_reason"] is None
            and completed == requested
        )
        or (
            evidence["execution_status"] == "stopped"
            and (evidence["stop_reason"] is not None or completed != requested)
        ),
        "live evidence completion state is inconsistent",
    )
    _require(
        evidence["retention_policy"]
        == {
            "automatic_persistence": False,
            "explicit_persistence_required": True,
            "required_file_mode": "0600",
            "overwrite_allowed": False,
        },
        "live evidence retention policy changed",
    )
    _require(
        evidence["authority_invariants"]
        == {
            "fallback_activation_count": 0,
            "retry_count": 0,
            "registry_mutation_count": 0,
            "human_review_fabricated_count": 0,
            "qualification_promotion_count": 0,
            "recommendation_count": 0,
            "routing_change_count": 0,
            "application_mutation_count": 0,
            "ats_mutation_count": 0,
            "raw_response_persisted_count": 0,
            "raw_request_persisted_count": 0,
        },
        "live evidence authority changed",
    )
    return True


def _validate_transport_result(
    result: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    parity_request: Dict[str, Any],
    plan: Dict[str, Any],
) -> bool:
    _require(isinstance(result, dict), "live transport result is required")
    missing_usage = _TRANSPORT_RESULT_FIELDS - set(result)
    if missing_usage & {"input_token_count", "output_token_count"}:
        raise ValueError("observed usage metadata is missing")
    _require(set(result) == _TRANSPORT_RESULT_FIELDS, "live transport result fields are invalid")
    _require(
        result["provider"] == scheduled["provider"]
        and result["model"] == scheduled["model"],
        "live transport provider/model mismatch",
    )
    _require(result["provider_outcome_category"] == "success", "live provider outcome is unknown")
    for field in ("input_token_count", "output_token_count"):
        _require(isinstance(result[field], int) and not isinstance(result[field], bool) and result[field] > 0, "observed usage metadata is missing")
    _require(isinstance(result["latency_ms"], (int, float)) and not isinstance(result["latency_ms"], bool) and math.isfinite(float(result["latency_ms"])) and result["latency_ms"] >= 0, "live transport latency is invalid")
    validate_production_parity_result(
        result["parity_result"],
        request=parity_request,
        plan=plan,
    )
    return True


def execute_controlled_live_qualification(
    *,
    plan: Dict[str, Any],
    live_authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    requested_schedule_keys: Sequence[str],
    operator_credentials: Mapping[str, str],
    execution_time_source: Callable[[], str],
    transport_dispatchers: Mapping[str, Callable[..., Dict[str, Any]]] | None = None,
    monotonic_clock: Callable[[], float] = monotonic,
    evidence_target: str | Path | None = None,
    validation_context_target: str | Path | None = None,
    review_packet_target: str | Path | None = None,
    repository_root: str | Path | None = None,
) -> Dict[str, Any]:
    """Execute an explicitly authorized serial subset; never update registry."""

    _require(callable(execution_time_source), "execution timestamp source is required")
    _require(callable(monotonic_clock), "monotonic clock is required")
    _require(
        validation_context_target is None or evidence_target is not None,
        "live validation context persistence requires matching evidence persistence",
    )
    _require(
        review_packet_target is None
        or (evidence_target is not None and validation_context_target is not None),
        "review packet persistence requires evidence and validation context persistence",
    )
    _require(
        (
            evidence_target is None
            and validation_context_target is None
            and review_packet_target is None
        )
        or repository_root is not None,
        "repository root is required for explicit persistence",
    )
    if validation_context_target is not None:
        _require(
            Path(validation_context_target) != Path(evidence_target),
            "live evidence and validation context targets must be distinct",
        )
    if review_packet_target is not None:
        _require(
            Path(review_packet_target)
            not in {Path(evidence_target), Path(validation_context_target)},
            "review packet target must be distinct from live evidence artifacts",
        )
    execution_at_utc = execution_time_source()
    controlled_plan = deepcopy(plan)
    authorization = deepcopy(live_authorization)
    pricing_payload = deepcopy(pricing)
    validate_live_authorization(
        authorization,
        plan=controlled_plan,
        pricing=pricing_payload,
        execution_at_utc=execution_at_utc,
    )
    eligible = _eligible_rows_by_key(controlled_plan)
    requested = list(requested_schedule_keys)
    _require(bool(requested) and len(requested) == len(set(requested)), "requested schedule subset is invalid")
    _require(set(requested).issubset(authorization["approved_schedule_keys"]), "requested schedule expands live authorization")
    expected_requested_order = [key for key in authorization["approved_schedule_keys"] if key in requested]
    _require(requested == expected_requested_order, "requested schedule subset must remain serial")
    rows = [eligible[key] for key in requested]
    review_requirements = canonical_human_review_requirements()
    if review_packet_target is not None:
        _require(
            len(rows) == 1
            and review_requirements[rows[0]["workload_id"]] is True,
            "review packet persistence requires exactly one subjective workload",
        )
    required_providers = {row["provider"] for row in rows}
    _require(
        isinstance(operator_credentials, Mapping)
        and set(operator_credentials) == required_providers
        and all(isinstance(operator_credentials[key], str) and bool(operator_credentials[key].strip()) for key in required_providers),
        "exact explicit operator evaluation credentials are required",
    )
    dispatchers = (
        {"groq": _default_dispatch, "openai": _default_dispatch}
        if transport_dispatchers is None
        else dict(transport_dispatchers)
    )
    _require(set(dispatchers) == {"groq", "openai"} and all(callable(value) for value in dispatchers.values()), "controlled provider dispatchers are invalid")
    evidence = _empty_evidence(
        execution_at_utc=execution_at_utc,
        plan=controlled_plan,
        authorization=authorization,
        pricing=pricing_payload,
        requested_schedule_keys=requested,
    )
    prices = _pricing_map(pricing_payload)
    review_parity_result = None
    ceilings = authorization["token_ceilings"]
    fingerprints = authorization["production_task_contract_fingerprints"]
    for scheduled in rows:
        aggregate = evidence["aggregate_usage"]
        if aggregate["provider_call_count"] >= authorization["maximum_request_count"]:
            evidence["stop_reason"] = "request_budget_exceeded"
            break
        packet = build_transmittable_request_packet(
            case_alias=scheduled["case_alias"],
            provider=scheduled["provider"],
            model=scheduled["model"],
            plan=controlled_plan,
            live_execution_requested=False,
        )
        parity_request = build_production_parity_request(
            packet,
            plan=controlled_plan,
            expected_task_contract_sha256=fingerprints[scheduled["workload_id"]],
        )
        validate_production_parity_request(parity_request, plan=controlled_plan)
        _require(
            parity_request["task_parameters"]["max_tokens"]
            <= ceilings["maximum_output_tokens_per_request"],
            "production task exceeds authorized output-token ceiling",
        )
        model_key = f"{scheduled['provider']}/{scheduled['model']}"
        worst_case_cost = _cost(
            ceilings["maximum_input_tokens_per_request"],
            parity_request["task_parameters"]["max_tokens"],
            prices[model_key],
        )
        model_spend = Decimal(str(aggregate["observed_cost_by_provider_model"][model_key]))
        total_spend = Decimal(str(aggregate["observed_cost"]))
        if (
            model_spend + worst_case_cost
            > Decimal(str(authorization["maximum_cost_per_provider_model"][model_key]))
            or total_spend + worst_case_cost
            > Decimal(str(authorization["maximum_total_cost"]))
        ):
            evidence["stop_reason"] = "cost_ceiling_exceeded"
            break
        if (
            aggregate["input_token_count"] + ceilings["maximum_input_tokens_per_request"]
            > ceilings["maximum_total_observed_input_tokens"]
            or aggregate["output_token_count"] + parity_request["task_parameters"]["max_tokens"]
            > ceilings["maximum_total_observed_output_tokens"]
        ):
            evidence["stop_reason"] = "token_budget_exceeded"
            break
        key = scheduled["schedule_key"]
        evidence["attempted_schedule_keys"].append(key)
        aggregate["provider_call_count"] += 1
        dispatcher = dispatchers[scheduled["provider"]]
        try:
            result = dispatcher(
                provider=scheduled["provider"],
                api_key=operator_credentials[scheduled["provider"]],
                parity_request=deepcopy(parity_request),
                scheduled=deepcopy(scheduled),
                plan=deepcopy(controlled_plan),
                monotonic_clock=monotonic_clock,
            )
        except LiveQualificationAmbiguousTimeout:
            evidence["ambiguous_schedule_keys"].append(key)
            evidence["stop_reason"] = "ambiguous_timeout"
            break
        except LiveQualificationDefinitiveFailure as exc:
            evidence["blocked_schedule_keys"].append(key)
            evidence["stop_reason"] = _bounded_transport_failure_stop_reason(exc)
            break
        except Exception:
            evidence["blocked_schedule_keys"].append(key)
            evidence["stop_reason"] = "unknown_provider_outcome"
            break
        try:
            _validate_transport_result(
                result,
                scheduled=scheduled,
                parity_request=parity_request,
                plan=controlled_plan,
            )
        except ValueError as exc:
            evidence["blocked_schedule_keys"].append(key)
            evidence["stop_reason"] = (
                "missing_usage_metadata"
                if "usage" in str(exc)
                else "unknown_provider_outcome"
            )
            break
        input_tokens = result["input_token_count"]
        output_tokens = result["output_token_count"]
        observed_cost = _cost(input_tokens, output_tokens, prices[model_key])
        aggregate["input_token_count"] += input_tokens
        aggregate["output_token_count"] += output_tokens
        aggregate["observed_cost"] = float(total_spend + observed_cost)
        aggregate["observed_cost_by_provider_model"][model_key] = float(
            model_spend + observed_cost
        )
        parity_result = result["parity_result"]
        hard_failures = parity_result["benchmark_quality"]["hard_failures"]
        hard_failure_present = any(hard_failures.values())
        quality_passed = parity_result["benchmark_quality"]["quality_gate_passed"]
        production_valid = parity_result["production_contract_valid"]
        evidence["grading_summaries"].append(
            {
                "schedule_key": key,
                "case_alias": scheduled["case_alias"],
                "workload_id": scheduled["workload_id"],
                "provider": scheduled["provider"],
                "model": scheduled["model"],
                "production_task_contract_sha256": scheduled[
                    "production_task_contract_sha256"
                ],
                "production_contract_valid": production_valid,
                "benchmark_quality_passed": quality_passed,
                "hard_failure_present": hard_failure_present,
                "human_review_required": review_requirements[
                    scheduled["workload_id"]
                ],
                "provider_outcome_category": result[
                    "provider_outcome_category"
                ],
                "latency_ms": float(result["latency_ms"]),
                "input_token_count": input_tokens,
                "output_token_count": output_tokens,
                "observed_cost": float(observed_cost),
            }
        )
        if (
            input_tokens > ceilings["maximum_input_tokens_per_request"]
            or output_tokens > ceilings["maximum_output_tokens_per_request"]
            or aggregate["input_token_count"]
            > ceilings["maximum_total_observed_input_tokens"]
            or aggregate["output_token_count"]
            > ceilings["maximum_total_observed_output_tokens"]
        ):
            evidence["blocked_schedule_keys"].append(key)
            evidence["stop_reason"] = "token_budget_exceeded"
            break
        if (
            model_spend + observed_cost
            > Decimal(str(authorization["maximum_cost_per_provider_model"][model_key]))
            or total_spend + observed_cost
            > Decimal(str(authorization["maximum_total_cost"]))
        ):
            evidence["blocked_schedule_keys"].append(key)
            evidence["stop_reason"] = "cost_ceiling_exceeded"
            break
        if not production_valid or not quality_passed or hard_failure_present:
            evidence["blocked_schedule_keys"].append(key)
            evidence["stop_reason"] = "hard_safety_failure"
            break
        evidence["completed_schedule_keys"].append(key)
        if review_packet_target is not None:
            review_parity_result = deepcopy(parity_result)
    if (
        evidence["stop_reason"] is None
        and evidence["completed_schedule_keys"] == requested
    ):
        evidence["execution_status"] = "completed"
    validate_live_qualification_evidence(
        evidence,
        plan=controlled_plan,
        authorization=authorization,
        pricing=pricing_payload,
    )
    validation_context = None
    if validation_context_target is not None:
        validation_context = build_live_qualification_validation_context(
            evidence,
            plan=controlled_plan,
            authorization=authorization,
            pricing=pricing_payload,
        )
    if evidence_target is not None:
        write_live_qualification_evidence_exclusive(
            evidence_target,
            evidence,
            repository_root=repository_root,
            plan=controlled_plan,
            authorization=authorization,
            pricing=pricing_payload,
        )
    if validation_context_target is not None:
        _require(
            validation_context is not None,
            "live validation context was not prepared",
        )
        try:
            write_live_qualification_validation_context_exclusive(
                validation_context_target,
                validation_context,
                evidence=evidence,
                repository_root=repository_root,
                plan=controlled_plan,
            )
        except (OSError, ValueError):
            raise LiveQualificationPersistenceFailure(
                "live validation context persistence failed after live evidence "
                "persistence"
            ) from None
    if review_packet_target is not None and evidence["completed_schedule_keys"]:
        _require(
            review_parity_result is not None,
            "review packet production result was not retained",
        )
        review_packet = build_subjective_qualification_review_packet(
            evidence=evidence,
            schedule_key=requested[0],
            production_parity_result=review_parity_result,
            plan=controlled_plan,
            authorization=authorization,
            pricing=pricing_payload,
        )
        try:
            write_subjective_qualification_review_packet_exclusive(
                review_packet_target,
                review_packet,
                repository_root=repository_root,
                evidence=evidence,
                plan=controlled_plan,
                authorization=authorization,
                pricing=pricing_payload,
            )
        except (OSError, ValueError):
            raise LiveQualificationPersistenceFailure(
                "subjective review packet persistence failed after live evidence "
                "persistence"
            ) from None
    return deepcopy(evidence)


def serialize_live_qualification_evidence(
    evidence: Dict[str, Any],
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> str:
    payload = deepcopy(evidence)
    validate_live_qualification_evidence(
        payload,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    return _canonical_json(payload)


def live_qualification_evidence_sha256(
    evidence: Dict[str, Any],
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> str:
    return sha256(
        serialize_live_qualification_evidence(
            evidence,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        ).encode("utf-8")
    ).hexdigest()


def build_live_qualification_validation_context(
    evidence: Dict[str, Any],
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Dict[str, Any]:
    """Bind exact non-secret live validation inputs to one evidence digest."""

    evidence_payload = deepcopy(evidence)
    authorization_payload = deepcopy(authorization)
    pricing_payload = deepcopy(pricing)
    validate_live_qualification_evidence(
        evidence_payload,
        plan=plan,
        authorization=authorization_payload,
        pricing=pricing_payload,
    )
    context = {
        "context_version": LIVE_VALIDATION_CONTEXT_VERSION,
        "evidence_sha256": live_qualification_evidence_sha256(
            evidence_payload,
            plan=plan,
            authorization=authorization_payload,
            pricing=pricing_payload,
        ),
        "authorization_sha256": live_authorization_sha256(
            authorization_payload
        ),
        "pricing_sha256": live_pricing_sha256(pricing_payload),
        "live_authorization": authorization_payload,
        "live_pricing": pricing_payload,
    }
    validate_live_qualification_validation_context(
        context,
        evidence=evidence_payload,
        plan=plan,
    )
    return deepcopy(context)


def validate_live_qualification_validation_context(
    context: Dict[str, Any],
    *,
    evidence: Dict[str, Any],
    plan: Dict[str, Any],
) -> bool:
    """Revalidate one durable context through the native live owners."""

    _require(
        isinstance(context, dict)
        and set(context) == _VALIDATION_CONTEXT_FIELDS,
        "live validation context fields must match the exact schema",
    )
    _require(
        context.get("context_version") == LIVE_VALIDATION_CONTEXT_VERSION,
        "live validation context version mismatch",
    )
    _require(
        not _contains_prohibited_serialized_key(context)
        and not _contains_secret_like_serialized_value(context),
        "live validation context contains prohibited secret or provider material",
    )
    authorization = deepcopy(context["live_authorization"])
    pricing = deepcopy(context["live_pricing"])
    evidence_payload = deepcopy(evidence)
    validate_live_qualification_evidence(
        evidence_payload,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    evidence_digest = live_qualification_evidence_sha256(
        evidence_payload,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    authorization_digest = live_authorization_sha256(authorization)
    pricing_digest = live_pricing_sha256(pricing)
    _require(
        context["evidence_sha256"] == evidence_digest,
        "live validation context evidence digest mismatch",
    )
    _require(
        context["authorization_sha256"] == authorization_digest
        and evidence_payload["authorization_sha256"] == authorization_digest,
        "live validation context authorization digest mismatch",
    )
    _require(
        context["pricing_sha256"] == pricing_digest
        and evidence_payload["pricing_sha256"] == pricing_digest,
        "live validation context pricing digest mismatch",
    )
    return True


def serialize_live_qualification_validation_context(
    context: Dict[str, Any],
    *,
    evidence: Dict[str, Any],
    plan: Dict[str, Any],
) -> str:
    payload = deepcopy(context)
    validate_live_qualification_validation_context(
        payload,
        evidence=evidence,
        plan=plan,
    )
    return _canonical_json(payload)


def load_live_qualification_validation_context(
    context: Dict[str, Any],
    *,
    evidence: Dict[str, Any],
    plan: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """Return exact validated authorization/pricing inputs without side effects."""

    payload = deepcopy(context)
    evidence_payload = deepcopy(evidence)
    plan_payload = deepcopy(plan)
    validate_live_qualification_validation_context(
        payload,
        evidence=evidence_payload,
        plan=plan_payload,
    )
    return {
        "authorization": deepcopy(payload["live_authorization"]),
        "pricing": deepcopy(payload["live_pricing"]),
    }


def _prepare_evidence_path(
    artifact_path: str | Path,
    *,
    repository_root: str | Path,
) -> Path:
    supplied_root = Path(repository_root)
    _require(
        supplied_root.is_dir() and not supplied_root.is_symlink(),
        "repository root is unsafe",
    )
    root = supplied_root.resolve()
    candidate = Path(artifact_path)
    _require(candidate.is_absolute(), "live evidence path must be absolute")
    _require(".." not in candidate.parts, "live evidence path traversal is prohibited")
    approved = root / APPROVED_EVIDENCE_DIRECTORY
    _require(
        candidate.parent == approved
        and candidate.suffix == ".json"
        and candidate.name not in {"", ".json"},
        "live evidence path is outside the approved namespace",
    )
    current = root
    for part in APPROVED_EVIDENCE_DIRECTORY.parts:
        current = current / part
        if current.exists() or current.is_symlink():
            _require(current.is_dir() and not current.is_symlink(), "live evidence parent path is unsafe")
        else:
            current.mkdir(mode=0o700)
        _require(
            not stat.S_IMODE(current.stat().st_mode) & (stat.S_IWGRP | stat.S_IWOTH),
            "live evidence parent permissions are unsafe",
        )
    _require(not candidate.exists() and not candidate.is_symlink(), "live evidence overwrite is prohibited")
    return candidate


def _prepare_validation_context_path(
    artifact_path: str | Path,
    *,
    repository_root: str | Path,
) -> Path:
    candidate = Path(artifact_path)
    _require(
        candidate.name.endswith(".validation-context.json")
        and candidate.name != ".validation-context.json",
        "live validation context filename is invalid",
    )
    return _prepare_evidence_path(
        candidate,
        repository_root=repository_root,
    )


def write_live_qualification_evidence_exclusive(
    artifact_path: str | Path,
    evidence: Dict[str, Any],
    *,
    repository_root: str | Path,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Path:
    """Persist explicitly requested bounded live evidence with mode 0600."""

    encoded = serialize_live_qualification_evidence(
        evidence,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    ).encode("utf-8")
    path = _prepare_evidence_path(artifact_path, repository_root=repository_root)
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
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
    _require(stat.S_IMODE(path.stat().st_mode) == 0o600, "live evidence mode must be 0600")
    persisted = json.loads(path.read_text(encoding="utf-8"))
    _require(persisted == evidence, "persisted live evidence verification failed")
    return path


def write_live_qualification_validation_context_exclusive(
    artifact_path: str | Path,
    context: Dict[str, Any],
    *,
    evidence: Dict[str, Any],
    repository_root: str | Path,
    plan: Dict[str, Any],
) -> Path:
    """Persist explicitly requested validation context with mode 0600."""

    encoded = serialize_live_qualification_validation_context(
        context,
        evidence=evidence,
        plan=plan,
    ).encode("utf-8")
    path = _prepare_validation_context_path(
        artifact_path,
        repository_root=repository_root,
    )
    flags = os.O_CREAT | os.O_EXCL | os.O_WRONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
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
    _require(
        stat.S_IMODE(path.stat().st_mode) == 0o600,
        "live validation context mode must be 0600",
    )
    persisted_bytes = path.read_bytes()
    _require(
        persisted_bytes == encoded,
        "persisted live validation context bytes differ",
    )
    persisted = json.loads(persisted_bytes.decode("utf-8"))
    _require(
        persisted == context,
        "persisted live validation context verification failed",
    )
    validate_live_qualification_validation_context(
        persisted,
        evidence=evidence,
        plan=plan,
    )
    return path
