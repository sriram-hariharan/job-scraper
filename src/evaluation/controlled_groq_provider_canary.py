"""Default-off preparation contract for a four-call Groq canary.

This evaluation owner performs no live execution.  It imports no provider SDK,
reads no environment configuration, constructs no client, opens no network or
database connection, starts no process or thread, and writes no artifact.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
from pathlib import Path
import stat
from typing import Any, Callable, Dict, Iterable, Mapping, Sequence

from src.evaluation.controlled_provider_benchmark_harness import (
    HARNESS_VERSION,
    RESULT_ARTIFACT_VERSION,
    TRANSPORT_RESULT_FIELDS,
    controlled_benchmark_harness_sha256,
    validate_ignored_result_path,
    validate_injected_transport_result,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    build_transmittable_request_packet,
    controlled_provider_benchmark_plan_sha256,
    validate_controlled_provider_benchmark_plan,
)
from src.evaluation.provider_benchmark_contract import (
    MODEL_ORDER,
    provider_benchmark_contract_sha256,
)
from src.evaluation.provider_fixture_benchmark import (
    provider_fixture_benchmark_sha256,
)


CANARY_VERSION = "controlled-groq-provider-canary-v1"
AUTHORIZATION_VERSION = "controlled-groq-provider-canary-authorization-v1"
PRICING_SCHEMA_VERSION = "controlled-groq-provider-canary-pricing-v1"
AUTHORIZATION_TEMPLATE_VERSION = (
    "controlled-groq-provider-canary-authorization-template-v1"
)
PRICING_TEMPLATE_VERSION = (
    "controlled-groq-provider-canary-pricing-template-v1"
)
EVIDENCE_CONTRACT_VERSION = (
    "controlled-groq-provider-canary-evidence-contract-v1"
)

AUTHORIZATION_TEMPLATE_SOURCE = (
    "tests/fixtures/provider_benchmark/"
    "groq_canary_authorization_template.json"
)
PRICING_TEMPLATE_SOURCE = (
    "tests/fixtures/provider_benchmark/groq_canary_pricing_template.json"
)
DEFAULT_AUTHORIZATION_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2] / AUTHORIZATION_TEMPLATE_SOURCE
)
DEFAULT_PRICING_TEMPLATE_PATH = (
    Path(__file__).resolve().parents[2] / PRICING_TEMPLATE_SOURCE
)
RECOVERY_006_STATUS_PATH = (
    Path("outputs/application_planning")
    / "phase11_controlled_priority_graph_verification_006_status.json"
)

_GROQ_CANDIDATES = tuple(
    pair for pair in MODEL_ORDER if pair[0] == "groq"
)
_CANARY_ASSIGNMENTS = (
    ("skill_extraction", 0),
    ("grounded_rag_answer", 0),
    ("jd_intelligence", 1),
    ("tailoring_generation", 1),
)
_SCHEDULE_FIELDS = {
    "schedule_key",
    "execution_order",
    "case_alias",
    "workload_id",
    "provider",
    "model",
    "timeout_seconds",
    "fallback",
    "harness_retry_limit",
    "provider_sdk_retry_limit",
}
_CONTRACT_FIELDS = {
    "canary_version",
    "contract_kind",
    "step8l_contract_sha256",
    "step8o_engine_sha256",
    "controlled_full_plan_sha256",
    "fixture_corpus_sha256",
    "harness_version",
    "harness_sha256",
    "candidate_provider_models",
    "schedule",
    "request_bounds",
    "token_bounds",
    "cost_policy",
    "stop_policy",
    "authority_invariants",
}
_AUTHORIZATION_FIELDS = {
    "authorization_version",
    "authorization_template_version",
    "canary_version",
    "canary_sha256",
    "controlled_full_plan_sha256",
    "fixture_corpus_sha256",
    "harness_sha256",
    "candidate_provider_models",
    "approved_schedule_keys",
    "approved_case_aliases",
    "request_counts",
    "token_ceilings",
    "maximum_observed_cost_per_model",
    "maximum_total_observed_cost",
    "valid_from_utc",
    "expires_at_utc",
    "pricing_table_sha256",
    "fallback_allowed",
    "retry_count",
    "gemini_allowed",
    "openai_allowed",
    "production_activation_allowed",
    "application_authority_allowed",
    "ats_authority_allowed",
    "operator_approved",
}
_PRICING_FIELDS = {
    "pricing_schema_version",
    "pricing_template_version",
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
_PRICE_FIELDS = {
    "provider",
    "model",
    "input_price_per_million_tokens",
    "output_price_per_million_tokens",
}
_FORBIDDEN_SELECTION_FIELDS = {
    "production_model_choice",
    "recommended_route",
    "selected_model",
    "selected_provider",
    "selected_winner",
    "winner",
    "winner_model",
    "winning_model",
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


def _sha256(value: Any) -> str:
    return sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _clean_text(value: Any) -> str:
    return str(value or "").strip()


def _parse_utc(value: Any) -> datetime:
    text = _clean_text(value)
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
    if positive:
        _require(number > 0, f"{label} must be positive")
    else:
        _require(number >= 0, f"{label} must be nonnegative")
    return number


def _iter_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key).strip().lower()
            yield from _iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_keys(item)


def _schedule_key(
    *,
    full_plan_sha256: str,
    execution_order: int,
    case_alias: str,
    provider: str,
    model: str,
) -> str:
    material = (
        f"{CANARY_VERSION}:{full_plan_sha256}:{execution_order}:"
        f"{case_alias}:{provider}:{model}"
    )
    return f"canary_{sha256(material.encode('utf-8')).hexdigest()[:32]}"


def _eligible_alias_by_workload(
    plan: Mapping[str, Any],
) -> Dict[str, str]:
    result: Dict[str, str] = {}
    for row in plan["transmission_review"]:
        if not row["eligible_for_later_controlled_transmission"]:
            continue
        workload_id = row["workload_id"]
        _require(
            workload_id not in result,
            "transmission-safe workload alias is ambiguous",
        )
        result[workload_id] = row["case_alias"]
    return result


def _build_schedule(plan: Mapping[str, Any]) -> list[Dict[str, Any]]:
    plan_sha = controlled_provider_benchmark_plan_sha256(dict(plan))
    aliases = _eligible_alias_by_workload(plan)
    schedule = []
    for execution_order, (workload_id, candidate_index) in enumerate(
        _CANARY_ASSIGNMENTS,
        start=1,
    ):
        provider, model = _GROQ_CANDIDATES[candidate_index]
        matching_rows = [
            row
            for row in plan["staged_matrix"]
            if row["workload_id"] == workload_id
            and row["provider"] == provider
            and row["model"] == model
        ]
        _require(
            len(matching_rows) == 1,
            "controlled plan does not own an exact canary assignment",
        )
        row = matching_rows[0]
        _require(
            aliases.get(workload_id) == row["case_alias"],
            "canary alias is not transmission eligible",
        )
        schedule.append(
            {
                "schedule_key": _schedule_key(
                    full_plan_sha256=plan_sha,
                    execution_order=execution_order,
                    case_alias=row["case_alias"],
                    provider=provider,
                    model=model,
                ),
                "execution_order": execution_order,
                "case_alias": row["case_alias"],
                "workload_id": workload_id,
                "provider": provider,
                "model": model,
                "timeout_seconds": plan["timeout_policy"]["timeout_seconds"],
                "fallback": False,
                "harness_retry_limit": 0,
                "provider_sdk_retry_limit": 0,
            }
        )
    return schedule


def build_controlled_groq_canary_contract(
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    validate_controlled_provider_benchmark_plan(controlled_plan)
    _require(
        len(_GROQ_CANDIDATES) == 2,
        "Step 8L Groq candidate set must contain exactly two models",
    )
    contract = {
        "canary_version": CANARY_VERSION,
        "contract_kind": "default_off_groq_live_canary_preparation",
        "step8l_contract_sha256": provider_benchmark_contract_sha256(),
        "step8o_engine_sha256": provider_fixture_benchmark_sha256(),
        "controlled_full_plan_sha256": (
            controlled_provider_benchmark_plan_sha256(controlled_plan)
        ),
        "fixture_corpus_sha256": controlled_plan[
            "step8o_case_corpus_sha256"
        ],
        "harness_version": HARNESS_VERSION,
        "harness_sha256": controlled_benchmark_harness_sha256(),
        "candidate_provider_models": [
            {"provider": provider, "model": model}
            for provider, model in _GROQ_CANDIDATES
        ],
        "schedule": _build_schedule(controlled_plan),
        "request_bounds": {
            "maximum_total_requests": 4,
            "maximum_requests_per_provider_model": {
                f"{provider}/{model}": 2
                for provider, model in _GROQ_CANDIDATES
            },
            "maximum_requests_per_case": 1,
            "serial_concurrency": 1,
            "automatic_expansion": False,
            "conditional_additional_calls": False,
        },
        "token_bounds": {
            "maximum_input_tokens_per_request": controlled_plan[
                "token_budget_schema"
            ]["maximum_input_tokens_per_request"],
            "maximum_output_tokens_per_request": controlled_plan[
                "token_budget_schema"
            ]["maximum_output_tokens_per_request"],
            "maximum_aggregate_input_tokens": 16384,
            "maximum_aggregate_output_tokens": 4096,
            "observed_usage_required": True,
            "missing_usage_estimation_allowed": False,
        },
        "cost_policy": {
            "positive_per_model_dollar_ceilings_required": True,
            "positive_total_dollar_ceiling_required": True,
            "total_ceiling_not_greater_than_per_model_sum": True,
            "validated_operator_approved_pricing_required": True,
            "observed_input_output_usage_only": True,
            "missing_usage_estimation_allowed": False,
            "stop_before_next_call_on_ceiling": True,
            "quality_gates_precede_cost_comparison": True,
        },
        "stop_policy": {
            "stop_on_first_hard_failure": True,
            "stop_on_missing_usage": True,
            "stop_on_provider_model_mismatch": True,
            "stop_on_unauthorized_transport_behavior": True,
            "ambiguous_timeout": "outcome_unknown_no_retry",
            "resume_ambiguous_key": False,
            "resume_completed_key": False,
            "resume_hard_failure_key": False,
            "fallback": False,
            "harness_retry_limit": 0,
            "provider_sdk_retry_limit": 0,
            "timeout_seconds": 30,
        },
        "authority_invariants": {
            "live_execution_authorized": False,
            "full_benchmark_authorized": False,
            "openai_allowed": False,
            "gemini_allowed": False,
            "production_activation": False,
            "routing_change_allowed": False,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
            "recovery_006_authorized": False,
        },
    }
    validate_controlled_groq_canary_contract(
        contract,
        plan=controlled_plan,
    )
    return deepcopy(contract)


def validate_controlled_groq_canary_contract(
    contract: Dict[str, Any],
    *,
    plan: Dict[str, Any] | None = None,
) -> bool:
    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    validate_controlled_provider_benchmark_plan(controlled_plan)
    _require(isinstance(contract, dict), "canary contract must be an object")
    _require(
        set(contract) == _CONTRACT_FIELDS,
        "canary contract fields must match the exact schema",
    )
    _require(
        contract.get("canary_version") == CANARY_VERSION,
        "canary version mismatch",
    )
    _require(
        contract.get("step8l_contract_sha256")
        == provider_benchmark_contract_sha256(),
        "Step 8L contract digest mismatch",
    )
    _require(
        contract.get("step8o_engine_sha256")
        == provider_fixture_benchmark_sha256(),
        "Step 8O engine digest mismatch",
    )
    _require(
        contract.get("controlled_full_plan_sha256")
        == controlled_provider_benchmark_plan_sha256(controlled_plan),
        "controlled full-plan digest mismatch",
    )
    _require(
        contract.get("fixture_corpus_sha256")
        == controlled_plan["step8o_case_corpus_sha256"],
        "fixture corpus digest mismatch",
    )
    _require(
        contract.get("harness_version") == HARNESS_VERSION
        and contract.get("harness_sha256")
        == controlled_benchmark_harness_sha256(),
        "Step 8Q harness contract mismatch",
    )
    expected_candidates = [
        {"provider": provider, "model": model}
        for provider, model in _GROQ_CANDIDATES
    ]
    _require(
        contract.get("candidate_provider_models") == expected_candidates,
        "canary candidate set must be exactly the two Groq models",
    )
    schedule = contract.get("schedule")
    _require(
        isinstance(schedule, list)
        and all(
            isinstance(row, dict) and set(row) == _SCHEDULE_FIELDS
            for row in schedule
        ),
        "canary schedule fields are invalid",
    )
    _require(
        schedule == _build_schedule(controlled_plan),
        "canary schedule differs from the controlled subset",
    )
    _require(
        len(schedule) == 4
        and [row["execution_order"] for row in schedule] == [1, 2, 3, 4]
        and len({row["schedule_key"] for row in schedule}) == 4
        and len({row["case_alias"] for row in schedule}) == 4,
        "canary schedule is not an exact deterministic four-key subset",
    )
    counts = {
        pair: sum(
            1
            for row in schedule
            if (row["provider"], row["model"]) == pair
        )
        for pair in _GROQ_CANDIDATES
    }
    _require(
        set(counts.values()) == {2},
        "canary schedule must contain two calls per Groq model",
    )
    _require(
        all(
            row["provider"] == "groq"
            and row["timeout_seconds"] == 30
            and row["fallback"] is False
            and row["harness_retry_limit"] == 0
            and row["provider_sdk_retry_limit"] == 0
            for row in schedule
        ),
        "canary schedule safety bounds changed",
    )
    request_bounds = contract.get("request_bounds")
    _require(
        request_bounds
        == {
            "maximum_total_requests": 4,
            "maximum_requests_per_provider_model": {
                f"{provider}/{model}": 2
                for provider, model in _GROQ_CANDIDATES
            },
            "maximum_requests_per_case": 1,
            "serial_concurrency": 1,
            "automatic_expansion": False,
            "conditional_additional_calls": False,
        },
        "canary request bounds changed",
    )
    token_bounds = contract.get("token_bounds")
    _require(
        token_bounds
        == {
            "maximum_input_tokens_per_request": 4096,
            "maximum_output_tokens_per_request": 1024,
            "maximum_aggregate_input_tokens": 16384,
            "maximum_aggregate_output_tokens": 4096,
            "observed_usage_required": True,
            "missing_usage_estimation_allowed": False,
        },
        "canary token bounds changed",
    )
    _require(
        contract.get("cost_policy")
        == {
            "positive_per_model_dollar_ceilings_required": True,
            "positive_total_dollar_ceiling_required": True,
            "total_ceiling_not_greater_than_per_model_sum": True,
            "validated_operator_approved_pricing_required": True,
            "observed_input_output_usage_only": True,
            "missing_usage_estimation_allowed": False,
            "stop_before_next_call_on_ceiling": True,
            "quality_gates_precede_cost_comparison": True,
        },
        "canary cost policy changed",
    )
    stop = contract.get("stop_policy")
    _require(
        isinstance(stop, dict)
        and stop.get("stop_on_first_hard_failure") is True
        and stop.get("stop_on_missing_usage") is True
        and stop.get("stop_on_provider_model_mismatch") is True
        and stop.get("stop_on_unauthorized_transport_behavior") is True
        and stop.get("ambiguous_timeout") == "outcome_unknown_no_retry"
        and stop.get("resume_ambiguous_key") is False
        and stop.get("resume_completed_key") is False
        and stop.get("resume_hard_failure_key") is False
        and stop.get("fallback") is False
        and stop.get("harness_retry_limit") == 0
        and stop.get("provider_sdk_retry_limit") == 0
        and stop.get("timeout_seconds") == 30,
        "canary stop policy changed",
    )
    authority = contract.get("authority_invariants")
    _require(
        isinstance(authority, dict)
        and all(
            authority.get(field) is False
            for field in (
                "live_execution_authorized",
                "full_benchmark_authorized",
                "openai_allowed",
                "gemini_allowed",
                "production_activation",
                "routing_change_allowed",
                "recovery_006_authorized",
            )
        )
        and authority.get("mutation_count") == 0
        and authority.get("application_action_count") == 0
        and authority.get("ats_action_count") == 0,
        "canary authority changed",
    )
    _require(
        not (_FORBIDDEN_SELECTION_FIELDS & set(_iter_keys(contract))),
        "model selection fields are prohibited",
    )
    return True


def serialize_controlled_groq_canary_contract(
    contract: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_controlled_groq_canary_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_controlled_groq_canary_contract(payload)
    return _canonical_json(payload)


def controlled_groq_canary_sha256(
    contract: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_controlled_groq_canary_contract(contract).encode("utf-8")
    ).hexdigest()


def build_operator_authorization_template(
    contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    canary = (
        build_controlled_groq_canary_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_controlled_groq_canary_contract(canary)
    schedule = canary["schedule"]
    return {
        "authorization_version": AUTHORIZATION_VERSION,
        "authorization_template_version": AUTHORIZATION_TEMPLATE_VERSION,
        "canary_version": CANARY_VERSION,
        "canary_sha256": controlled_groq_canary_sha256(canary),
        "controlled_full_plan_sha256": canary[
            "controlled_full_plan_sha256"
        ],
        "fixture_corpus_sha256": canary["fixture_corpus_sha256"],
        "harness_sha256": canary["harness_sha256"],
        "candidate_provider_models": deepcopy(
            canary["candidate_provider_models"]
        ),
        "approved_schedule_keys": [
            row["schedule_key"] for row in schedule
        ],
        "approved_case_aliases": [
            row["case_alias"] for row in schedule
        ],
        "request_counts": deepcopy(canary["request_bounds"]),
        "token_ceilings": deepcopy(canary["token_bounds"]),
        "maximum_observed_cost_per_model": {
            f"{provider}/{model}": None
            for provider, model in _GROQ_CANDIDATES
        },
        "maximum_total_observed_cost": None,
        "valid_from_utc": None,
        "expires_at_utc": None,
        "pricing_table_sha256": None,
        "fallback_allowed": False,
        "retry_count": 0,
        "gemini_allowed": False,
        "openai_allowed": False,
        "production_activation_allowed": False,
        "application_authority_allowed": False,
        "ats_authority_allowed": False,
        "operator_approved": False,
    }


def validate_operator_authorization(
    authorization: Dict[str, Any] | None,
    *,
    pricing: Dict[str, Any],
    execution_at_utc: str,
    contract: Dict[str, Any] | None = None,
) -> bool:
    canary = (
        build_controlled_groq_canary_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_controlled_groq_canary_contract(canary)
    validate_operator_approved_pricing(
        pricing,
        execution_at_utc=execution_at_utc,
    )
    _require(
        isinstance(authorization, dict),
        "operator authorization is required",
    )
    _require(
        set(authorization) == _AUTHORIZATION_FIELDS,
        "authorization fields must match the exact schema",
    )
    template = build_operator_authorization_template(canary)
    operator_fields = {
        "maximum_observed_cost_per_model",
        "maximum_total_observed_cost",
        "valid_from_utc",
        "expires_at_utc",
        "pricing_table_sha256",
        "operator_approved",
    }
    _require(
        all(
            authorization.get(field) == template[field]
            for field in _AUTHORIZATION_FIELDS - operator_fields
        ),
        "authorization scope differs from the exact canary",
    )
    _require(
        authorization.get("operator_approved") is True,
        "operator approval is required",
    )
    valid_from = _parse_utc(authorization.get("valid_from_utc"))
    expires_at = _parse_utc(authorization.get("expires_at_utc"))
    execution_at = _parse_utc(execution_at_utc)
    _require(valid_from < expires_at, "authorization validity is invalid")
    _require(
        valid_from <= execution_at <= expires_at,
        "authorization is expired or not yet valid",
    )
    per_model = authorization.get("maximum_observed_cost_per_model")
    expected_model_keys = {
        f"{provider}/{model}" for provider, model in _GROQ_CANDIDATES
    }
    _require(
        isinstance(per_model, dict) and set(per_model) == expected_model_keys,
        "authorization per-model dollar ceilings are incomplete",
    )
    per_model_values = [
        _decimal(value, "per-model dollar ceiling", positive=True)
        for value in per_model.values()
    ]
    total = _decimal(
        authorization.get("maximum_total_observed_cost"),
        "total dollar ceiling",
        positive=True,
    )
    _require(
        total <= sum(per_model_values, Decimal("0")),
        "total dollar ceiling exceeds per-model ceilings",
    )
    _require(
        authorization.get("pricing_table_sha256")
        == pricing_table_sha256(pricing),
        "authorization pricing digest mismatch",
    )
    return True


def load_authorization_template_fixture(
    path: str | Path | None = None,
) -> Dict[str, Any]:
    fixture_path = (
        Path(path)
        if path is not None
        else DEFAULT_AUTHORIZATION_TEMPLATE_PATH
    )
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    _require(
        payload == build_operator_authorization_template(),
        "authorization template fixture differs from its builder",
    )
    return deepcopy(payload)


def pricing_table_sha256(pricing: Dict[str, Any]) -> str:
    payload = deepcopy(pricing)
    payload.pop("pricing_table_sha256", None)
    return _sha256(payload)


def build_groq_pricing_template() -> Dict[str, Any]:
    return {
        "pricing_schema_version": PRICING_SCHEMA_VERSION,
        "pricing_template_version": PRICING_TEMPLATE_VERSION,
        "pricing_version": None,
        "source_classification": None,
        "source_effective_at_utc": None,
        "valid_from_utc": None,
        "expires_at_utc": None,
        "currency": None,
        "prices": [
            {
                "provider": provider,
                "model": model,
                "input_price_per_million_tokens": None,
                "output_price_per_million_tokens": None,
            }
            for provider, model in _GROQ_CANDIDATES
        ],
        "operator_approved": False,
        "pricing_table_sha256": None,
    }


def validate_operator_approved_pricing(
    pricing: Dict[str, Any] | None,
    *,
    execution_at_utc: str,
) -> bool:
    _require(
        isinstance(pricing, dict),
        "operator-approved Groq pricing is required",
    )
    _require(
        set(pricing) == _PRICING_FIELDS,
        "pricing fields must match the exact schema",
    )
    _require(
        pricing.get("pricing_schema_version") == PRICING_SCHEMA_VERSION,
        "pricing schema version mismatch",
    )
    _require(
        pricing.get("pricing_template_version") == PRICING_TEMPLATE_VERSION,
        "pricing template version mismatch",
    )
    _require(
        bool(_clean_text(pricing.get("pricing_version"))),
        "pricing version is required",
    )
    _require(
        bool(_clean_text(pricing.get("source_classification"))),
        "pricing source classification is required",
    )
    source_effective = _parse_utc(pricing.get("source_effective_at_utc"))
    valid_from = _parse_utc(pricing.get("valid_from_utc"))
    expires_at = _parse_utc(pricing.get("expires_at_utc"))
    execution_at = _parse_utc(execution_at_utc)
    _require(
        source_effective <= expires_at and valid_from < expires_at,
        "pricing validity window is invalid",
    )
    _require(
        valid_from <= execution_at <= expires_at,
        "pricing is expired or not yet valid",
    )
    _require(pricing.get("currency") == "USD", "pricing currency is unsupported")
    _require(
        pricing.get("operator_approved") is True,
        "pricing operator approval is required",
    )
    rows = pricing.get("prices")
    _require(
        isinstance(rows, list)
        and all(
            isinstance(row, dict) and set(row) == _PRICE_FIELDS
            for row in rows
        ),
        "pricing rows must match the exact schema",
    )
    _require(
        [
            (row.get("provider"), row.get("model"))
            for row in rows
        ]
        == list(_GROQ_CANDIDATES),
        "pricing must contain exactly the two Groq models",
    )
    for row in rows:
        _decimal(
            row.get("input_price_per_million_tokens"),
            "input price",
            positive=True,
        )
        _decimal(
            row.get("output_price_per_million_tokens"),
            "output price",
            positive=True,
        )
    _require(
        pricing.get("pricing_table_sha256") == pricing_table_sha256(pricing),
        "pricing digest mismatch",
    )
    return True


def load_pricing_template_fixture(
    path: str | Path | None = None,
) -> Dict[str, Any]:
    fixture_path = (
        Path(path) if path is not None else DEFAULT_PRICING_TEMPLATE_PATH
    )
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    _require(
        payload == build_groq_pricing_template(),
        "pricing template fixture differs from its builder",
    )
    return deepcopy(payload)


def _validate_parent_permissions(path: Path, root: Path) -> None:
    current = path.parent
    while not current.exists():
        _require(current != root.parent, "approved artifact parent is missing")
        current = current.parent
    _require(not current.is_symlink(), "artifact parent symlink is prohibited")
    mode = stat.S_IMODE(current.stat().st_mode)
    _require(mode & stat.S_IWUSR != 0, "artifact parent is not owner-writable")
    _require(
        mode & (stat.S_IWGRP | stat.S_IWOTH) == 0,
        "artifact parent permissions are too broad",
    )


def validate_live_canary_preflight(
    *,
    authorization: Dict[str, Any] | None,
    pricing: Dict[str, Any] | None,
    execution_at_utc: str,
    result_path: str | Path,
    checkpoint_path: str | Path,
    repository_root: str | Path,
    graph_verification_enabled: bool,
    recovery_006_present: bool,
    owned_process_count: int,
    prior_checkpoint: Dict[str, Any] | None,
    live_execution: bool = False,
) -> Dict[str, Any]:
    root = Path(repository_root).resolve()
    canary = build_controlled_groq_canary_contract()
    validate_operator_approved_pricing(
        pricing,
        execution_at_utc=execution_at_utc,
    )
    validate_operator_authorization(
        authorization,
        pricing=pricing,
        execution_at_utc=execution_at_utc,
        contract=canary,
    )
    result = validate_ignored_result_path(
        result_path,
        repository_root=root,
    )
    checkpoint = validate_ignored_result_path(
        checkpoint_path,
        repository_root=root,
    )
    _require(result != checkpoint, "result and checkpoint paths must differ")
    _validate_parent_permissions(result, root)
    _validate_parent_permissions(checkpoint, root)
    ignore_text = (root / ".gitignore").read_text(encoding="utf-8")
    _require(
        any(
            line.strip() in {"outputs/", "/outputs/"}
            for line in ignore_text.splitlines()
        ),
        "benchmark output directory is not ignored",
    )
    _require(
        graph_verification_enabled is False,
        "graph verification must remain disabled",
    )
    _require(
        recovery_006_present is False
        and not (root / RECOVERY_006_STATUS_PATH).exists(),
        "recovery 006 must remain absent",
    )
    _require(
        isinstance(owned_process_count, int)
        and not isinstance(owned_process_count, bool)
        and owned_process_count == 0,
        "an owned runtime process is active",
    )
    _require(
        prior_checkpoint is None,
        "prior checkpoint requires separate ambiguity review",
    )
    _require(
        live_execution is False,
        "live execution remains unauthorized during preparation",
    )
    return {
        "canary_version": CANARY_VERSION,
        "canary_sha256": controlled_groq_canary_sha256(canary),
        "authorization_validation": "valid",
        "pricing_validation": "valid",
        "schedule_count": 4,
        "result_path_validation": "approved_absent_ignored",
        "checkpoint_path_validation": "approved_absent_ignored",
        "parent_permissions": "acceptable",
        "graph_verification": False,
        "recovery_006": False,
        "owned_process_count": 0,
        "prior_ambiguous_checkpoint": False,
        "credential_configuration_presence": "not_checked_in_preparation",
        "live_transport_readiness": False,
        "execution_authorization": False,
        "live_execution": False,
    }


def build_future_live_transport_adapter_contract(
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    canary = build_controlled_groq_canary_contract(controlled_plan)
    first = canary["schedule"][0]
    packet = build_transmittable_request_packet(
        case_alias=first["case_alias"],
        provider=first["provider"],
        model=first["model"],
        plan=controlled_plan,
        live_execution_requested=False,
    )
    return {
        "contract_kind": "future_live_transport_adapter_default_off",
        "request_field_allowlist": sorted(packet),
        "result_field_allowlist": sorted(TRANSPORT_RESULT_FIELDS),
        "approved_provider_models": deepcopy(
            canary["candidate_provider_models"]
        ),
        "timeout_seconds": 30,
        "provider_sdk_retry_limit": 0,
        "provider_sdk_retry_readiness": (
            "requires_explicit_zero_in_future_adapter"
        ),
        "fallback": False,
        "normalization": "immediate",
        "raw_sdk_envelope_retained": False,
        "request_identifier_retained": False,
        "reasoning_trace_retained": False,
        "headers_retained": False,
        "raw_provider_error_retained": False,
        "bounded_provider_outcome_required": True,
        "observed_latency_required": True,
        "observed_input_tokens_required": True,
        "observed_output_tokens_required": True,
        "generic_fallback_router_allowed": False,
        "openai_allowed": False,
        "gemini_allowed": False,
        "live_execution_authorized": False,
    }


def validate_canary_transport_request(
    packet: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
    plan: Dict[str, Any] | None = None,
) -> bool:
    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    canary = build_controlled_groq_canary_contract(controlled_plan)
    _require(
        dict(scheduled) in canary["schedule"],
        "transport request schedule key is outside the canary",
    )
    expected = build_transmittable_request_packet(
        case_alias=scheduled["case_alias"],
        provider=scheduled["provider"],
        model=scheduled["model"],
        plan=controlled_plan,
        live_execution_requested=False,
    )
    _require(
        packet == expected,
        "transport request differs from the exact allowlisted packet",
    )
    return True


def verify_canary_with_injected_fake_transport(
    *,
    transport: Callable[[Dict[str, Any], int], Dict[str, Any]],
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    canary = build_controlled_groq_canary_contract(controlled_plan)
    _require(callable(transport), "injected fake transport is required")
    calls = 0
    for scheduled in canary["schedule"]:
        packet = build_transmittable_request_packet(
            case_alias=scheduled["case_alias"],
            provider=scheduled["provider"],
            model=scheduled["model"],
            plan=controlled_plan,
            live_execution_requested=False,
        )
        validate_canary_transport_request(
            packet,
            scheduled=scheduled,
            plan=controlled_plan,
        )
        _require(
            packet["provider"] == "groq"
            and packet["model"] == scheduled["model"]
            and packet["fallback"] is False
            and packet["timeout_seconds"] == 30
            and packet["live_execution_requested"] is False,
            "fake transport request differs from the canary contract",
        )
        result = transport(deepcopy(packet), 30)
        validate_injected_transport_result(
            result,
            scheduled=scheduled,
        )
        calls += 1
    return {
        "canary_version": CANARY_VERSION,
        "schedule_count": 4,
        "fake_transport_calls": calls,
        "maximum_calls_per_key": 1,
        "serial_concurrency": 1,
        "fallback_count": 0,
        "retry_count": 0,
        "live_provider_calls": 0,
        "winner_selected": False,
        "production_activation": False,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
    }


def build_canary_result_checkpoint_contract(
    contract: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    canary = (
        build_controlled_groq_canary_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_controlled_groq_canary_contract(canary)
    return {
        "evidence_contract_version": EVIDENCE_CONTRACT_VERSION,
        "canary_version": CANARY_VERSION,
        "canary_sha256": controlled_groq_canary_sha256(canary),
        "harness_version": HARNESS_VERSION,
        "step8q_result_artifact_version": RESULT_ARTIFACT_VERSION,
        "schedule_keys": [
            row["schedule_key"] for row in canary["schedule"]
        ],
        "required_metadata": [
            "authorization_sha256",
            "pricing_sha256",
            "bounded_observed_usage",
            "bounded_observed_cost",
            "redacted_normalized_grading_summaries",
            "completed_schedule_keys",
            "blocked_schedule_keys",
            "ambiguous_schedule_keys",
            "hard_failure_schedule_keys",
            "stop_reason",
            "quality_gate_status",
            "cost_comparison_eligibility",
        ],
        "resume_completed_key": False,
        "resume_ambiguous_key": False,
        "resume_hard_failure_key": False,
        "winner_selected": False,
        "production_activation": False,
        "automatic_persistence": False,
        "required_file_mode": "0600",
        "maximum_retention_days": 7,
    }
