"""Default-off controlled provider benchmark execution harness.

This evaluation owner imports no provider SDK, reads no credential, opens no
network or database connection, creates no subprocess or thread, and writes no
artifact.  A narrow injected callable is the only execution seam.
"""

from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from hashlib import sha256
import json
import math
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, List, Mapping, Sequence

from src.evaluation.controlled_provider_benchmark_plan import (
    AUTHORIZATION_VERSION,
    CONTROLLED_PLAN_VERSION,
    build_controlled_provider_benchmark_plan,
    build_transmittable_request_packet,
    controlled_provider_benchmark_plan_sha256,
    validate_controlled_provider_benchmark_plan,
    validate_operator_authorization,
    validate_redacted_result_packet,
)
from src.evaluation.provider_benchmark_contract import (
    CONTRACT_VERSION as STEP8L_CONTRACT_VERSION,
    MODEL_ORDER,
    WORKLOAD_ORDER,
    provider_benchmark_contract_sha256,
)
from src.evaluation.provider_client_compatibility import (
    COMPATIBILITY_CONTRACT_VERSION,
    STEP8M_COMPATIBILITY_BASELINE_SHA256,
)
from src.evaluation.provider_fixture_benchmark import (
    FIXTURE_BENCHMARK_VERSION,
    fixture_case_corpus_sha256,
    grade_normalized_candidate_result,
    load_fixture_case_corpus,
    provider_fixture_benchmark_sha256,
    validate_fixture_case_corpus,
)


HARNESS_VERSION = "controlled-provider-benchmark-harness-v1"
PRICING_SCHEMA_VERSION = "controlled-provider-pricing-table-v1"
RESULT_ARTIFACT_VERSION = "controlled-provider-benchmark-result-v1"
SYNTHETIC_AUTHORIZATION_SOURCE = (
    "tests/fixtures/provider_benchmark/synthetic_authorization.json"
)
SYNTHETIC_PRICING_SOURCE = (
    "tests/fixtures/provider_benchmark/synthetic_pricing.json"
)
DEFAULT_AUTHORIZATION_PATH = (
    Path(__file__).resolve().parents[2] / SYNTHETIC_AUTHORIZATION_SOURCE
)
DEFAULT_PRICING_PATH = (
    Path(__file__).resolve().parents[2] / SYNTHETIC_PRICING_SOURCE
)
APPROVED_RESULT_DIRECTORY = Path("outputs/provider_benchmark")

_AUTHORIZATION_EXECUTION_FIELDS = {
    "approved_request_matrix",
    "maximum_requests_per_provider_model",
    "maximum_requests_per_case",
}
_PRICING_FIELDS = {
    "pricing_schema_version",
    "pricing_version",
    "valid_from_utc",
    "expires_at_utc",
    "prices",
    "currency",
    "operator_approved",
    "source_classification",
    "pricing_table_sha256",
}
_PRICE_FIELDS = {
    "provider",
    "model",
    "input_price_per_million_tokens",
    "output_price_per_million_tokens",
}
_SCHEDULE_FIELDS = {
    "schedule_key",
    "execution_order",
    "case_alias",
    "workload_id",
    "tier",
    "provider",
    "model",
    "timeout_seconds",
    "fallback",
    "harness_retry_limit",
}
_TRANSPORT_RESULT_FIELDS = {
    "normalized_output",
    "provider",
    "model",
    "latency_ms",
    "input_token_count",
    "output_token_count",
    "provider_outcome_category",
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
_CHECKPOINT_FIELDS = {
    "harness_version",
    "plan_sha256",
    "corpus_sha256",
    "authorization_sha256",
    "pricing_sha256",
    "completed_schedule_keys",
    "blocked_schedule_keys",
    "ambiguous_schedule_keys",
    "aggregate_usage",
    "grading_summaries",
    "stop_reason",
    "authority_invariants",
}
_AGGREGATE_FIELDS = {
    "transport_calls",
    "input_tokens",
    "output_tokens",
    "observed_cost",
    "latency_ms",
    "by_provider",
    "by_model",
    "by_case_alias",
    "by_schedule_key",
}
_GRADING_SUMMARY_FIELDS = {
    "schedule_key",
    "case_alias",
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
_PROHIBITED_CHECKPOINT_KEYS = {
    "credential",
    "environment",
    "header",
    "normalized_output",
    "prompt",
    "provider_error",
    "raw_response",
    "reasoning",
    "request_id",
    "request_packet",
    "response_envelope",
    "synthetic_input",
    "transport_log",
}
_STOP_REASONS = {
    None,
    "ambiguous_timeout",
    "application_action",
    "ats_action",
    "cost_ceiling_exceeded",
    "definitive_transport_failure",
    "duplicate_call_uncertainty",
    "fallback_attempted",
    "hard_safety_failure",
    "missing_usage_metadata",
    "provider_duration_exceeded",
    "provider_model_mismatch",
    "raw_response_persistence",
    "request_budget_exceeded",
    "retry_attempted",
    "run_duration_exceeded",
    "token_budget_exceeded",
    "unknown_provider_outcome",
}


class AmbiguousTransportTimeout(RuntimeError):
    """Injected transport reports that provider receipt is unknowable."""


class DefinitiveTransportFailure(RuntimeError):
    """Injected transport reports a definitive, non-retriable failure."""


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


def _normalized_key(value: Any) -> str:
    return _clean_text(value).lower().replace("-", "_").replace(" ", "_")


def _iter_keys(value: Any) -> Iterable[str]:
    if isinstance(value, dict):
        for key, item in value.items():
            yield _normalized_key(key)
            yield from _iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_keys(item)


def _contains_prohibited_checkpoint_field(value: Any) -> bool:
    return any(key in _PROHIBITED_CHECKPOINT_KEYS for key in _iter_keys(value))


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


def _number(value: Any, label: str, *, positive: bool = False) -> float:
    number = _decimal(value, label, positive=positive)
    return float(number)


def _schedule_key(
    *,
    plan_sha256: str,
    execution_order: int,
    case_alias: str,
    provider: str,
    model: str,
) -> str:
    material = (
        f"{HARNESS_VERSION}:{plan_sha256}:{execution_order}:"
        f"{case_alias}:{provider}:{model}"
    )
    return f"schedule_{sha256(material.encode('utf-8')).hexdigest()[:32]}"


def build_controlled_benchmark_harness_contract(
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    validate_controlled_provider_benchmark_plan(controlled_plan)
    contract = {
        "harness_version": HARNESS_VERSION,
        "contract_kind": "default_off_injected_transport_execution",
        "step8l_contract_version": STEP8L_CONTRACT_VERSION,
        "step8l_contract_sha256": provider_benchmark_contract_sha256(),
        "step8m_contract_version": COMPATIBILITY_CONTRACT_VERSION,
        "step8m_contract_sha256": STEP8M_COMPATIBILITY_BASELINE_SHA256,
        "step8o_contract_version": FIXTURE_BENCHMARK_VERSION,
        "step8o_engine_sha256": controlled_plan["step8o_engine_sha256"],
        "step8pa_plan_version": CONTROLLED_PLAN_VERSION,
        "step8pa_plan_sha256": controlled_provider_benchmark_plan_sha256(
            controlled_plan
        ),
        "candidate_definitions": deepcopy(
            controlled_plan["candidate_definitions"]
        ),
        "workload_order": list(WORKLOAD_ORDER),
        "schedule_count": controlled_plan["request_counts"][
            "maximum_total_requests"
        ],
        "schedule_counts": deepcopy(controlled_plan["request_counts"]),
        "controls": {
            "live_execution_default": False,
            "real_transport_authorized": False,
            "injected_fake_transport_only_in_tests": True,
            "serial_concurrency": 1,
            "fallback": False,
            "harness_retry_limit": 0,
            "automatic_persistence": False,
            "winner_selection_allowed": False,
            "production_activation_allowed": False,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
        },
    }
    validate_controlled_benchmark_harness_contract(contract, plan=controlled_plan)
    return deepcopy(contract)


def validate_controlled_benchmark_harness_contract(
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
    _require(isinstance(contract, dict), "harness contract must be an object")
    _require(
        contract.get("harness_version") == HARNESS_VERSION,
        "harness version mismatch",
    )
    _require(
        contract.get("step8pa_plan_sha256")
        == controlled_provider_benchmark_plan_sha256(controlled_plan),
        "harness plan digest mismatch",
    )
    _require(
        [
            (row.get("provider"), row.get("model"))
            for row in contract.get("candidate_definitions", [])
        ]
        == list(MODEL_ORDER),
        "harness candidate set mismatch",
    )
    _require(
        all(
            row.get("provider") != "gemini"
            for row in contract["candidate_definitions"]
        ),
        "Gemini is prohibited",
    )
    _require(
        contract.get("workload_order") == list(WORKLOAD_ORDER),
        "harness workload order mismatch",
    )
    _require(
        contract.get("schedule_count")
        == controlled_plan["request_counts"]["maximum_total_requests"]
        and contract.get("schedule_counts")
        == controlled_plan["request_counts"],
        "harness schedule bounds mismatch",
    )
    controls = contract.get("controls")
    _require(
        isinstance(controls, dict)
        and controls.get("live_execution_default") is False
        and controls.get("real_transport_authorized") is False
        and controls.get("injected_fake_transport_only_in_tests") is True
        and controls.get("serial_concurrency") == 1
        and controls.get("fallback") is False
        and controls.get("harness_retry_limit") == 0
        and controls.get("automatic_persistence") is False
        and controls.get("winner_selection_allowed") is False
        and controls.get("production_activation_allowed") is False
        and controls.get("mutation_count") == 0
        and controls.get("application_action_count") == 0
        and controls.get("ats_action_count") == 0,
        "harness controls are unsafe",
    )
    serialized = _canonical_json(contract).lower()
    for forbidden in (
        '"recommended_route"',
        '"selected_model"',
        '"selected_provider"',
        '"selected_winner"',
        '"winning_model"',
    ):
        _require(forbidden not in serialized, "model selection is prohibited")
    return True


def serialize_controlled_benchmark_harness_contract(
    contract: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_controlled_benchmark_harness_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_controlled_benchmark_harness_contract(payload)
    return _canonical_json(payload)


def controlled_benchmark_harness_sha256(
    contract: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_controlled_benchmark_harness_contract(contract).encode(
            "utf-8"
        )
    ).hexdigest()


def pricing_table_sha256(pricing: Dict[str, Any]) -> str:
    payload = deepcopy(pricing)
    payload.pop("pricing_table_sha256", None)
    return _sha256(payload)


def validate_operator_approved_pricing(
    pricing: Dict[str, Any] | None,
    *,
    execution_at_utc: str,
) -> bool:
    _require(isinstance(pricing, dict), "operator-approved pricing is required")
    _require(
        set(pricing) == _PRICING_FIELDS,
        "pricing table fields must match the exact schema",
    )
    _require(
        pricing.get("pricing_schema_version") == PRICING_SCHEMA_VERSION,
        "pricing schema version mismatch",
    )
    _require(
        bool(_clean_text(pricing.get("pricing_version"))),
        "pricing version is required",
    )
    _require(pricing.get("currency") == "USD", "pricing currency is unsupported")
    _require(
        pricing.get("operator_approved") is True,
        "pricing operator approval is required",
    )
    _require(
        pricing.get("source_classification")
        == "synthetic_non_current_test_only",
        "pricing source classification is invalid",
    )
    valid_from = _parse_utc(pricing.get("valid_from_utc"))
    expires_at = _parse_utc(pricing.get("expires_at_utc"))
    execution_at = _parse_utc(execution_at_utc)
    _require(valid_from < expires_at, "pricing validity window is invalid")
    _require(
        valid_from <= execution_at <= expires_at,
        "pricing is expired or not yet valid",
    )
    rows = pricing.get("prices")
    _require(isinstance(rows, list), "pricing rows are required")
    _require(
        all(isinstance(row, dict) and set(row) == _PRICE_FIELDS for row in rows),
        "pricing row fields must match the exact schema",
    )
    observed_pairs = [
        (_clean_text(row.get("provider")).lower(), _clean_text(row.get("model")))
        for row in rows
    ]
    _require(
        observed_pairs == list(MODEL_ORDER),
        "pricing provider/model set must be exact",
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
        "pricing table hash mismatch",
    )
    return True


def load_synthetic_pricing_fixture(
    path: str | Path | None = None,
    *,
    execution_at_utc: str = "2026-07-25T00:00:00Z",
) -> Dict[str, Any]:
    fixture_path = Path(path) if path is not None else DEFAULT_PRICING_PATH
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    validate_operator_approved_pricing(
        payload,
        execution_at_utc=execution_at_utc,
    )
    return deepcopy(payload)


def authorization_sha256(authorization: Dict[str, Any]) -> str:
    _require(isinstance(authorization, dict), "authorization must be an object")
    return _sha256(authorization)


def _exact_authorization_fields(plan: Mapping[str, Any]) -> set[str]:
    return (
        set(plan["authorization_schema"]["required_fields"])
        | _AUTHORIZATION_EXECUTION_FIELDS
    )


def validate_harness_operator_authorization(
    authorization: Dict[str, Any] | None,
    *,
    plan: Dict[str, Any],
    pricing: Dict[str, Any],
    execution_at_utc: str,
) -> bool:
    controlled_plan = deepcopy(plan)
    validate_controlled_provider_benchmark_plan(controlled_plan)
    _require(
        isinstance(authorization, dict),
        "operator authorization is required",
    )
    _require(
        set(authorization) == _exact_authorization_fields(controlled_plan),
        "operator authorization fields must match the exact harness schema",
    )
    validate_operator_authorization(
        authorization,
        plan=controlled_plan,
        execution_at_utc=execution_at_utc,
    )
    _require(
        authorization.get("pricing_table_version")
        == pricing.get("pricing_version"),
        "authorization pricing version mismatch",
    )
    _require(
        authorization.get("approved_request_matrix")
        == controlled_plan["staged_matrix"],
        "authorization request matrix mismatch",
    )
    _require(
        authorization.get("maximum_requests_per_provider_model")
        == controlled_plan["request_counts"]["maximum_requests_per_model"],
        "authorization provider/model request bounds mismatch",
    )
    _require(
        authorization.get("maximum_requests_per_case")
        == controlled_plan["request_counts"]["maximum_requests_per_case"],
        "authorization per-case request bound mismatch",
    )
    return True


def load_synthetic_authorization_fixture(
    path: str | Path | None = None,
    *,
    plan: Dict[str, Any] | None = None,
    pricing: Dict[str, Any] | None = None,
    execution_at_utc: str = "2026-07-25T00:00:00Z",
) -> Dict[str, Any]:
    fixture_path = Path(path) if path is not None else DEFAULT_AUTHORIZATION_PATH
    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    pricing_payload = (
        load_synthetic_pricing_fixture(execution_at_utc=execution_at_utc)
        if pricing is None
        else deepcopy(pricing)
    )
    payload = json.loads(fixture_path.read_text(encoding="utf-8"))
    validate_harness_operator_authorization(
        payload,
        plan=controlled_plan,
        pricing=pricing_payload,
        execution_at_utc=execution_at_utc,
    )
    return deepcopy(payload)


def _schedule_from_plan(plan: Mapping[str, Any]) -> List[Dict[str, Any]]:
    plan_digest = controlled_provider_benchmark_plan_sha256(dict(plan))
    timeout_seconds = plan["timeout_policy"]["timeout_seconds"]
    schedule = []
    for row in plan["staged_matrix"]:
        schedule.append(
            {
                "schedule_key": _schedule_key(
                    plan_sha256=plan_digest,
                    execution_order=row["execution_order"],
                    case_alias=row["case_alias"],
                    provider=row["provider"],
                    model=row["model"],
                ),
                "execution_order": row["execution_order"],
                "case_alias": row["case_alias"],
                "workload_id": row["workload_id"],
                "tier": row["tier"],
                "provider": row["provider"],
                "model": row["model"],
                "timeout_seconds": timeout_seconds,
                "fallback": False,
                "harness_retry_limit": 0,
            }
        )
    return schedule


def build_execution_schedule(
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
) -> List[Dict[str, Any]]:
    controlled_plan = deepcopy(plan)
    validate_controlled_provider_benchmark_plan(controlled_plan)
    _require(
        authorization.get("approved_request_matrix")
        == controlled_plan["staged_matrix"],
        "authorized matrix differs from the controlled plan",
    )
    schedule = _schedule_from_plan(controlled_plan)
    validate_execution_schedule(
        schedule,
        plan=controlled_plan,
        authorization=authorization,
    )
    return deepcopy(schedule)


def validate_execution_schedule(
    schedule: Sequence[Mapping[str, Any]],
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
) -> bool:
    controlled_plan = deepcopy(plan)
    validate_controlled_provider_benchmark_plan(controlled_plan)
    _require(
        isinstance(schedule, (list, tuple)),
        "execution schedule must be a sequence",
    )
    rows = [dict(row) for row in schedule]
    _require(
        all(set(row) == _SCHEDULE_FIELDS for row in rows),
        "execution schedule fields are invalid",
    )
    _require(
        rows == _schedule_from_plan(controlled_plan),
        "execution schedule differs from the controlled matrix",
    )
    _require(
        len(rows)
        == authorization.get("maximum_request_count")
        == controlled_plan["request_counts"]["maximum_total_requests"],
        "execution schedule request count mismatch",
    )
    keys = [row["schedule_key"] for row in rows]
    unique_requests = [
        (row["case_alias"], row["provider"], row["model"]) for row in rows
    ]
    _require(
        len(keys) == len(set(keys))
        and len(unique_requests) == len(set(unique_requests)),
        "duplicate execution schedule key",
    )
    _require(
        [row["execution_order"] for row in rows]
        == list(range(1, len(rows) + 1)),
        "execution schedule order is not deterministic",
    )
    _require(
        all(
            row["fallback"] is False
            and row["harness_retry_limit"] == 0
            and row["timeout_seconds"] == 30
            and (row["provider"], row["model"]) in MODEL_ORDER
            and row["provider"] != "gemini"
            for row in rows
        ),
        "execution schedule safety policy is invalid",
    )
    return True


def _case_maps(
    *,
    plan: Mapping[str, Any],
    corpus: Mapping[str, Any],
) -> tuple[Dict[str, Dict[str, Any]], Dict[str, str]]:
    reviews = plan["transmission_review"]
    cases = corpus["cases"]
    _require(
        len(reviews) == len(cases),
        "plan review and corpus case count mismatch",
    )
    by_alias: Dict[str, Dict[str, Any]] = {}
    case_id_by_alias: Dict[str, str] = {}
    for case, review in zip(cases, reviews):
        if not review["eligible_for_later_controlled_transmission"]:
            continue
        alias = review["case_alias"]
        by_alias[alias] = deepcopy(case)
        case_id_by_alias[alias] = case["case_id"]
    return by_alias, case_id_by_alias


def _pricing_map(pricing: Mapping[str, Any]) -> Dict[str, Dict[str, Decimal]]:
    return {
        f"{row['provider']}/{row['model']}": {
            "input": Decimal(str(row["input_price_per_million_tokens"])),
            "output": Decimal(str(row["output_price_per_million_tokens"])),
        }
        for row in pricing["prices"]
    }


def _observed_cost(
    *,
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    pricing: Mapping[str, Any],
) -> float:
    price = _pricing_map(pricing)[f"{provider}/{model}"]
    cost = (
        Decimal(input_tokens) * price["input"]
        + Decimal(output_tokens) * price["output"]
    ) / Decimal(1_000_000)
    return float(cost.quantize(Decimal("0.000000000001")))


def _empty_aggregate(plan: Mapping[str, Any]) -> Dict[str, Any]:
    eligible_aliases = sorted(
        row["case_alias"]
        for row in plan["transmission_review"]
        if row["eligible_for_later_controlled_transmission"]
    )
    return {
        "transport_calls": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "observed_cost": 0.0,
        "latency_ms": 0.0,
        "by_provider": {"groq": 0, "openai": 0},
        "by_model": {
            key: 0
            for key in plan["request_counts"]["maximum_requests_per_model"]
        },
        "by_case_alias": {alias: 0 for alias in eligible_aliases},
        "by_schedule_key": {},
    }


def build_empty_checkpoint(
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Dict[str, Any]:
    controlled_plan = deepcopy(plan)
    checkpoint = {
        "harness_version": HARNESS_VERSION,
        "plan_sha256": controlled_provider_benchmark_plan_sha256(
            controlled_plan
        ),
        "corpus_sha256": controlled_plan["step8o_case_corpus_sha256"],
        "authorization_sha256": authorization_sha256(authorization),
        "pricing_sha256": pricing_table_sha256(pricing),
        "completed_schedule_keys": [],
        "blocked_schedule_keys": [],
        "ambiguous_schedule_keys": [],
        "aggregate_usage": _empty_aggregate(controlled_plan),
        "grading_summaries": [],
        "stop_reason": None,
        "authority_invariants": {
            "provider_call_count": 0,
            "fallback_activation_count": 0,
            "retry_count": 0,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
            "raw_response_persisted_count": 0,
            "production_activation": False,
            "winner_selected": False,
        },
    }
    return checkpoint


def validate_checkpoint(
    checkpoint: Dict[str, Any],
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> bool:
    controlled_plan = deepcopy(plan)
    _require(isinstance(checkpoint, dict), "checkpoint must be an object")
    _require(
        set(checkpoint) == _CHECKPOINT_FIELDS,
        "checkpoint fields must match the exact schema",
    )
    _require(
        not _contains_prohibited_checkpoint_field(checkpoint),
        "checkpoint contains prohibited raw material",
    )
    _require(
        checkpoint.get("harness_version") == HARNESS_VERSION,
        "checkpoint harness version mismatch",
    )
    _require(
        checkpoint.get("plan_sha256")
        == controlled_provider_benchmark_plan_sha256(controlled_plan),
        "checkpoint plan hash mismatch",
    )
    _require(
        checkpoint.get("corpus_sha256")
        == controlled_plan["step8o_case_corpus_sha256"],
        "checkpoint corpus hash mismatch",
    )
    _require(
        checkpoint.get("authorization_sha256")
        == authorization_sha256(authorization),
        "checkpoint authorization hash mismatch",
    )
    _require(
        checkpoint.get("pricing_sha256") == pricing_table_sha256(pricing),
        "checkpoint pricing hash mismatch",
    )
    schedule = _schedule_from_plan(controlled_plan)
    schedule_by_key = {row["schedule_key"]: row for row in schedule}
    key_lists = []
    for field in (
        "completed_schedule_keys",
        "blocked_schedule_keys",
        "ambiguous_schedule_keys",
    ):
        values = checkpoint.get(field)
        _require(
            isinstance(values, list)
            and len(values) == len(set(values))
            and set(values).issubset(schedule_by_key),
            f"checkpoint {field} is invalid",
        )
        key_lists.append(set(values))
    _require(
        not (key_lists[0] & key_lists[1])
        and not (key_lists[0] & key_lists[2])
        and not (key_lists[1] & key_lists[2]),
        "checkpoint schedule key states overlap",
    )
    summaries = checkpoint.get("grading_summaries")
    _require(
        isinstance(summaries, list)
        and all(
            isinstance(row, dict)
            and set(row) == _GRADING_SUMMARY_FIELDS
            and row.get("schedule_key") in schedule_by_key
            and row.get("provider_call_count") == 1
            for row in summaries
        ),
        "checkpoint grading summaries are malformed",
    )
    summary_keys = [row["schedule_key"] for row in summaries]
    _require(
        len(summary_keys) == len(set(summary_keys)),
        "checkpoint contains duplicate grading evidence",
    )
    _require(
        set(checkpoint["completed_schedule_keys"]).issubset(summary_keys),
        "checkpoint is missing completed-key evidence",
    )
    aggregate = checkpoint.get("aggregate_usage")
    _require(
        isinstance(aggregate, dict)
        and set(aggregate) == _AGGREGATE_FIELDS,
        "checkpoint aggregate usage is malformed",
    )
    calls = aggregate.get("transport_calls")
    _require(
        isinstance(calls, int) and not isinstance(calls, bool) and calls >= 0,
        "checkpoint transport call count is invalid",
    )
    by_key = aggregate.get("by_schedule_key")
    _require(
        isinstance(by_key, dict)
        and set(by_key).issubset(schedule_by_key)
        and all(value == 1 for value in by_key.values())
        and sum(by_key.values()) == calls,
        "checkpoint schedule invocation counts are inconsistent",
    )
    invoked_keys = set(by_key)
    state_keys = set().union(*key_lists)
    _require(
        invoked_keys == state_keys,
        "checkpoint invocation evidence and key states are inconsistent",
    )
    expected_provider_counts = {"groq": 0, "openai": 0}
    expected_model_counts = {
        key: 0
        for key in controlled_plan["request_counts"][
            "maximum_requests_per_model"
        ]
    }
    expected_alias_counts = {
        alias: 0 for alias in _empty_aggregate(controlled_plan)["by_case_alias"]
    }
    for key in invoked_keys:
        row = schedule_by_key[key]
        expected_provider_counts[row["provider"]] += 1
        expected_model_counts[f"{row['provider']}/{row['model']}"] += 1
        expected_alias_counts[row["case_alias"]] += 1
    _require(
        aggregate.get("by_provider") == expected_provider_counts
        and aggregate.get("by_model") == expected_model_counts
        and aggregate.get("by_case_alias") == expected_alias_counts,
        "checkpoint aggregate invocation counts are inconsistent",
    )
    for field in (
        "input_tokens",
        "output_tokens",
        "observed_cost",
        "latency_ms",
    ):
        _decimal(aggregate.get(field), f"checkpoint {field}")
    _require(
        checkpoint.get("stop_reason") in _STOP_REASONS,
        "checkpoint stop reason is unsupported",
    )
    authority = checkpoint.get("authority_invariants")
    _require(
        authority
        == {
            "provider_call_count": calls,
            "fallback_activation_count": 0,
            "retry_count": 0,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
            "raw_response_persisted_count": 0,
            "production_activation": False,
            "winner_selected": False,
        },
        "checkpoint authority invariants changed",
    )
    return True


def serialize_checkpoint(
    checkpoint: Dict[str, Any],
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> str:
    payload = deepcopy(checkpoint)
    validate_checkpoint(
        payload,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    return _canonical_json(payload)


def checkpoint_sha256(
    checkpoint: Dict[str, Any],
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> str:
    return sha256(
        serialize_checkpoint(
            checkpoint,
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        ).encode("utf-8")
    ).hexdigest()


def _validate_transport_result(
    result: Dict[str, Any],
    *,
    scheduled: Mapping[str, Any],
) -> bool:
    _require(isinstance(result, dict), "transport result must be an object")
    _require(
        set(result) == _TRANSPORT_RESULT_FIELDS,
        "transport result fields must match the exact allowlist",
    )
    _require(
        result.get("provider_outcome_category") in _TRANSPORT_OUTCOMES,
        "transport provider outcome is unknown",
    )
    _require(
        _clean_text(result.get("provider")).lower() == scheduled["provider"]
        and _clean_text(result.get("model")) == scheduled["model"],
        "transport provider/model mismatch",
    )
    _require(
        isinstance(result.get("normalized_output"), dict),
        "transport normalized content must be an object",
    )
    _number(result.get("latency_ms"), "transport latency")
    for field in ("input_token_count", "output_token_count"):
        value = result.get(field)
        _require(
            isinstance(value, int)
            and not isinstance(value, bool)
            and value >= 0,
            f"transport {field} is missing or invalid",
        )
    return True


def _grading_projection(
    *,
    case_id: str,
    scheduled: Mapping[str, Any],
    normalized_output: Dict[str, Any],
    schema_valid: bool,
    latency_ms: float,
    input_tokens: int,
    output_tokens: int,
    observed_cost: float,
) -> Dict[str, Any]:
    # Step 8O is deliberately offline-only.  This bounded projection invokes
    # its deterministic schema/grader path while the harness separately owns
    # the one observed injected-transport call.
    return {
        "case_id": case_id,
        "workload_id": scheduled["workload_id"],
        "provider": scheduled["provider"],
        "model": scheduled["model"],
        "normalized_output": deepcopy(normalized_output),
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
        "estimated_cost": observed_cost,
    }


def _redacted_result_packet(
    *,
    scheduled: Mapping[str, Any],
    normalized_output: Dict[str, Any],
    schema_valid: bool,
    latency_ms: float,
    input_tokens: int,
    output_tokens: int,
    observed_cost: float,
    quality_gate_passed: bool,
    outcome: str,
) -> Dict[str, Any]:
    packet = {
        "case_alias": scheduled["case_alias"],
        "workload_id": scheduled["workload_id"],
        "provider": scheduled["provider"],
        "model": scheduled["model"],
        "normalized_output": deepcopy(normalized_output),
        "schema_valid": schema_valid,
        "normalization_succeeded": True,
        "latency_ms": latency_ms,
        "input_token_count": input_tokens,
        "output_token_count": output_tokens,
        "observed_cost": observed_cost,
        "provider_outcome_category": outcome,
        "fallback_used": False,
        "retry_count": 0,
        "redaction_status": "redacted_normalized_only",
        "hard_failure_status": (
            "none" if quality_gate_passed else "hard_safety_failure"
        ),
    }
    validate_redacted_result_packet(packet)
    return packet


def _grading_summary(
    *,
    scheduled: Mapping[str, Any],
    grade: Mapping[str, Any],
    schema_valid: bool,
    outcome: str,
    latency_ms: float,
    input_tokens: int,
    output_tokens: int,
    observed_cost: float,
) -> Dict[str, Any]:
    return {
        "schedule_key": scheduled["schedule_key"],
        "case_alias": scheduled["case_alias"],
        "workload_id": scheduled["workload_id"],
        "provider": scheduled["provider"],
        "model": scheduled["model"],
        "schema_valid": schema_valid,
        "normalization_succeeded": True,
        "quality_gate_passed": bool(grade["quality_gate_passed"]),
        "hard_failures": deepcopy(grade["hard_failures"]),
        "provider_outcome_category": outcome,
        "latency_ms": latency_ms,
        "input_token_count": input_tokens,
        "output_token_count": output_tokens,
        "observed_cost": observed_cost,
        "provider_call_count": 1,
    }


def _append_unique(target: List[str], key: str) -> None:
    _require(key not in target, "duplicate-call uncertainty")
    target.append(key)


def _mark_invocation(
    checkpoint: Dict[str, Any],
    scheduled: Mapping[str, Any],
) -> None:
    aggregate = checkpoint["aggregate_usage"]
    key = scheduled["schedule_key"]
    _require(
        key not in aggregate["by_schedule_key"],
        "duplicate-call uncertainty",
    )
    aggregate["transport_calls"] += 1
    aggregate["by_provider"][scheduled["provider"]] += 1
    model_key = f"{scheduled['provider']}/{scheduled['model']}"
    aggregate["by_model"][model_key] += 1
    aggregate["by_case_alias"][scheduled["case_alias"]] += 1
    aggregate["by_schedule_key"][key] = 1
    checkpoint["authority_invariants"]["provider_call_count"] += 1


def _stop(
    checkpoint: Dict[str, Any],
    scheduled: Mapping[str, Any] | None,
    reason: str,
    *,
    ambiguous: bool = False,
    blocked: bool = False,
) -> None:
    checkpoint["stop_reason"] = reason
    if scheduled is None:
        return
    key = scheduled["schedule_key"]
    if ambiguous:
        _append_unique(checkpoint["ambiguous_schedule_keys"], key)
    elif blocked:
        _append_unique(checkpoint["blocked_schedule_keys"], key)


def _pre_call_stop_reason(
    *,
    checkpoint: Mapping[str, Any],
    scheduled: Mapping[str, Any],
    plan: Mapping[str, Any],
    authorization: Mapping[str, Any],
) -> str | None:
    aggregate = checkpoint["aggregate_usage"]
    if aggregate["transport_calls"] >= authorization["maximum_request_count"]:
        return "request_budget_exceeded"
    model_key = f"{scheduled['provider']}/{scheduled['model']}"
    if (
        aggregate["by_model"][model_key]
        >= authorization["maximum_requests_per_provider_model"][model_key]
    ):
        return "request_budget_exceeded"
    if (
        aggregate["by_case_alias"][scheduled["case_alias"]]
        >= authorization["maximum_requests_per_case"]
    ):
        return "request_budget_exceeded"
    if (
        aggregate["input_tokens"]
        >= plan["token_budget_schema"]["maximum_total_observed_input_tokens"]
        or aggregate["output_tokens"]
        >= plan["token_budget_schema"]["maximum_total_observed_output_tokens"]
    ):
        return "token_budget_exceeded"
    if (
        Decimal(str(aggregate["observed_cost"]))
        >= Decimal(str(authorization["maximum_total_observed_cost"]))
    ):
        return "cost_ceiling_exceeded"
    if (
        aggregate["latency_ms"]
        >= plan["execution_policy"]["maximum_run_duration_seconds"] * 1000
    ):
        return "run_duration_exceeded"
    provider_latency = sum(
        Decimal(str(row["latency_ms"]))
        for row in checkpoint["grading_summaries"]
        if row["provider"] == scheduled["provider"]
    )
    if provider_latency >= (
        Decimal(
            plan["execution_policy"]["maximum_provider_duration_seconds"][
                scheduled["provider"]
            ]
        )
        * 1000
    ):
        return "provider_duration_exceeded"
    return None


def execute_schedule_with_fake_transport(
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    transport: Callable[[Dict[str, Any], int], Dict[str, Any]],
    execution_at_utc: str,
    prior_checkpoint: Dict[str, Any] | None = None,
    maximum_schedule_items: int | None = None,
) -> Dict[str, Any]:
    """Execute only an explicitly injected deterministic fake transport."""

    controlled_plan = deepcopy(plan)
    pricing_payload = deepcopy(pricing)
    authorization_payload = deepcopy(authorization)
    validate_controlled_provider_benchmark_plan(controlled_plan)
    validate_operator_approved_pricing(
        pricing_payload,
        execution_at_utc=execution_at_utc,
    )
    validate_harness_operator_authorization(
        authorization_payload,
        plan=controlled_plan,
        pricing=pricing_payload,
        execution_at_utc=execution_at_utc,
    )
    _require(callable(transport), "injected fake transport is required")
    schedule = build_execution_schedule(
        plan=controlled_plan,
        authorization=authorization_payload,
    )
    corpus = load_fixture_case_corpus()
    validate_fixture_case_corpus(corpus)
    _require(
        fixture_case_corpus_sha256(corpus)
        == controlled_plan["step8o_case_corpus_sha256"],
        "execution corpus digest mismatch",
    )
    cases_by_alias, case_ids_by_alias = _case_maps(
        plan=controlled_plan,
        corpus=corpus,
    )
    if prior_checkpoint is None:
        checkpoint = build_empty_checkpoint(
            plan=controlled_plan,
            authorization=authorization_payload,
            pricing=pricing_payload,
        )
    else:
        checkpoint = deepcopy(prior_checkpoint)
        validate_checkpoint(
            checkpoint,
            plan=controlled_plan,
            authorization=authorization_payload,
            pricing=pricing_payload,
        )
        checkpoint["stop_reason"] = None
    already_final = set(
        checkpoint["completed_schedule_keys"]
        + checkpoint["blocked_schedule_keys"]
        + checkpoint["ambiguous_schedule_keys"]
    )
    result_packets: List[Dict[str, Any]] = []
    processed = 0
    for scheduled in schedule:
        key = scheduled["schedule_key"]
        if key in already_final:
            continue
        if maximum_schedule_items is not None and processed >= maximum_schedule_items:
            break
        pre_call_stop = _pre_call_stop_reason(
            checkpoint=checkpoint,
            scheduled=scheduled,
            plan=controlled_plan,
            authorization=authorization_payload,
        )
        if pre_call_stop is not None:
            _stop(checkpoint, None, pre_call_stop)
            break
        request_packet = build_transmittable_request_packet(
            case_alias=scheduled["case_alias"],
            provider=scheduled["provider"],
            model=scheduled["model"],
            plan=controlled_plan,
            corpus=corpus,
            live_execution_requested=False,
        )
        _mark_invocation(checkpoint, scheduled)
        processed += 1
        try:
            transport_result = transport(
                deepcopy(request_packet),
                scheduled["timeout_seconds"],
            )
        except AmbiguousTransportTimeout:
            _stop(
                checkpoint,
                scheduled,
                "ambiguous_timeout",
                ambiguous=True,
            )
            break
        except DefinitiveTransportFailure:
            _stop(
                checkpoint,
                scheduled,
                "definitive_transport_failure",
                blocked=True,
            )
            break
        except Exception:
            _stop(
                checkpoint,
                scheduled,
                "unknown_provider_outcome",
                blocked=True,
            )
            break
        try:
            _validate_transport_result(transport_result, scheduled=scheduled)
        except ValueError as exc:
            bounded_error = str(exc)
            if "token_count" in bounded_error:
                stop_reason = "missing_usage_metadata"
            elif "provider/model" in bounded_error:
                stop_reason = "provider_model_mismatch"
            else:
                stop_reason = "unknown_provider_outcome"
            _stop(
                checkpoint,
                scheduled,
                stop_reason,
                blocked=True,
            )
            break
        outcome = transport_result["provider_outcome_category"]
        if outcome == "ambiguous_timeout":
            _stop(
                checkpoint,
                scheduled,
                "ambiguous_timeout",
                ambiguous=True,
            )
            break
        outcome_stop = {
            "definitive_failure": "definitive_transport_failure",
            "unknown_provider_outcome": "unknown_provider_outcome",
            "application_action": "application_action",
            "ats_action": "ats_action",
            "raw_response_persistence": "raw_response_persistence",
            "fallback_attempt": "fallback_attempted",
            "retry_attempt": "retry_attempted",
        }.get(outcome)
        if outcome_stop is not None:
            _stop(checkpoint, scheduled, outcome_stop, blocked=True)
            break
        latency_ms = _number(transport_result["latency_ms"], "latency")
        input_tokens = transport_result["input_token_count"]
        output_tokens = transport_result["output_token_count"]
        if latency_ms > scheduled["timeout_seconds"] * 1000:
            _stop(
                checkpoint,
                scheduled,
                "ambiguous_timeout",
                ambiguous=True,
            )
            break
        per_request_input = controlled_plan["token_budget_schema"][
            "maximum_input_tokens_per_request"
        ]
        per_request_output = controlled_plan["token_budget_schema"][
            "maximum_output_tokens_per_request"
        ]
        aggregate = checkpoint["aggregate_usage"]
        if (
            input_tokens > per_request_input
            or output_tokens > per_request_output
            or aggregate["input_tokens"] + input_tokens
            > controlled_plan["token_budget_schema"][
                "maximum_total_observed_input_tokens"
            ]
            or aggregate["output_tokens"] + output_tokens
            > controlled_plan["token_budget_schema"][
                "maximum_total_observed_output_tokens"
            ]
        ):
            aggregate["input_tokens"] += input_tokens
            aggregate["output_tokens"] += output_tokens
            aggregate["latency_ms"] += latency_ms
            _stop(
                checkpoint,
                scheduled,
                "token_budget_exceeded",
                blocked=True,
            )
            break
        cost = _observed_cost(
            provider=scheduled["provider"],
            model=scheduled["model"],
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            pricing=pricing_payload,
        )
        model_key = f"{scheduled['provider']}/{scheduled['model']}"
        model_cost_before = sum(
            Decimal(str(row["observed_cost"]))
            for row in checkpoint["grading_summaries"]
            if row["provider"] == scheduled["provider"]
            and row["model"] == scheduled["model"]
        )
        aggregate["input_tokens"] += input_tokens
        aggregate["output_tokens"] += output_tokens
        aggregate["latency_ms"] += latency_ms
        aggregate["observed_cost"] = float(
            Decimal(str(aggregate["observed_cost"])) + Decimal(str(cost))
        )
        if (
            model_cost_before + Decimal(str(cost))
            > Decimal(
                str(
                    authorization_payload[
                        "maximum_observed_cost_per_model"
                    ][model_key]
                )
            )
            or Decimal(str(aggregate["observed_cost"]))
            > Decimal(
                str(authorization_payload["maximum_total_observed_cost"])
            )
        ):
            _stop(
                checkpoint,
                scheduled,
                "cost_ceiling_exceeded",
                blocked=True,
            )
            break
        case = cases_by_alias[scheduled["case_alias"]]
        normalized_output = deepcopy(transport_result["normalized_output"])
        schema_valid = all(
            field in normalized_output and normalized_output[field] is not None
            for field in case["required_fields"]
        )
        projection = _grading_projection(
            case_id=case_ids_by_alias[scheduled["case_alias"]],
            scheduled=scheduled,
            normalized_output=normalized_output,
            schema_valid=schema_valid,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            observed_cost=cost,
        )
        grade = grade_normalized_candidate_result(
            projection,
            corpus=corpus,
        )
        summary = _grading_summary(
            scheduled=scheduled,
            grade=grade,
            schema_valid=schema_valid,
            outcome=outcome,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            observed_cost=cost,
        )
        checkpoint["grading_summaries"].append(summary)
        if not grade["quality_gate_passed"]:
            _stop(
                checkpoint,
                scheduled,
                "hard_safety_failure",
                blocked=True,
            )
            break
        redacted = _redacted_result_packet(
            scheduled=scheduled,
            normalized_output=normalized_output,
            schema_valid=schema_valid,
            latency_ms=latency_ms,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            observed_cost=cost,
            quality_gate_passed=True,
            outcome=outcome,
        )
        result_packets.append(redacted)
        _append_unique(checkpoint["completed_schedule_keys"], key)
    validate_checkpoint(
        checkpoint,
        plan=controlled_plan,
        authorization=authorization_payload,
        pricing=pricing_payload,
    )
    return {
        "harness_version": HARNESS_VERSION,
        "execution_mode": "injected_fake_transport_only",
        "checkpoint": deepcopy(checkpoint),
        "result_packets": deepcopy(result_packets),
        "transport_calls": checkpoint["aggregate_usage"]["transport_calls"],
        "live_execution": False,
        "winner_selected": False,
        "production_activation": False,
    }


def validate_ignored_result_path(
    path: str | Path,
    *,
    repository_root: str | Path,
) -> Path:
    root = Path(repository_root).resolve()
    approved_root = (root / APPROVED_RESULT_DIRECTORY).resolve()
    candidate = Path(path)
    _require(candidate.is_absolute(), "result path must be explicit and absolute")
    _require(".." not in candidate.parts, "result path traversal is prohibited")
    if candidate.exists() or candidate.is_symlink():
        _require(not candidate.is_symlink(), "result path symlink is prohibited")
        _require(False, "result artifact overwrite is prohibited")
    resolved = candidate.resolve(strict=False)
    _require(
        resolved != approved_root and approved_root in resolved.parents,
        "result path is outside the approved ignored benchmark directory",
    )
    current = root
    for part in candidate.relative_to(root).parts[:-1]:
        current = current / part
        if current.exists() or current.is_symlink():
            _require(
                not current.is_symlink(),
                "result path symlink escape is prohibited",
            )
    _require(
        candidate.suffix == ".json",
        "result artifact must use canonical JSON",
    )
    return candidate


def build_result_artifact(
    *,
    checkpoint: Dict[str, Any],
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> Dict[str, Any]:
    validate_checkpoint(
        checkpoint,
        plan=plan,
        authorization=authorization,
        pricing=pricing,
    )
    artifact = {
        "artifact_version": RESULT_ARTIFACT_VERSION,
        "harness_version": HARNESS_VERSION,
        "plan_sha256": controlled_provider_benchmark_plan_sha256(plan),
        "corpus_sha256": plan["step8o_case_corpus_sha256"],
        "authorization_sha256": authorization_sha256(authorization),
        "pricing_sha256": pricing_table_sha256(pricing),
        "checkpoint": deepcopy(checkpoint),
        "retention_policy": {
            "automatic_persistence": False,
            "ignored_artifact_only": True,
            "required_file_mode": "0600",
            "maximum_retention_days": 7,
            "operator_review_required": True,
            "deletion_required": True,
            "overwrite_allowed": False,
        },
        "authority_invariants": {
            "winner_selected": False,
            "production_activation": False,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
        },
    }
    _require(
        not _contains_prohibited_checkpoint_field(artifact),
        "result artifact contains prohibited raw material",
    )
    return artifact


def serialize_result_artifact(
    artifact: Dict[str, Any],
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
) -> str:
    payload = deepcopy(artifact)
    _require(
        payload
        == build_result_artifact(
            checkpoint=payload.get("checkpoint"),
            plan=plan,
            authorization=authorization,
            pricing=pricing,
        ),
        "result artifact schema mismatch",
    )
    return _canonical_json(payload)


def _dry_run_summary(
    *,
    plan: Mapping[str, Any],
    authorization: Mapping[str, Any],
    schedule: Sequence[Mapping[str, Any]],
) -> Dict[str, Any]:
    return {
        "harness_version": HARNESS_VERSION,
        "authorization_validation": "valid",
        "pricing_validation": "valid",
        "schedule_count": len(schedule),
        "count_by_provider_model": deepcopy(
            plan["request_counts"]["by_model"]
        ),
        "count_by_workload": deepcopy(plan["request_counts"]["by_workload"]),
        "serial_concurrency": 1,
        "timeout_policy": deepcopy(plan["timeout_policy"]),
        "retry_policy": deepcopy(plan["retry_policy"]),
        "fallback_policy": deepcopy(plan["fallback_policy"]),
        "token_ceilings": deepcopy(plan["token_budget_schema"]),
        "cost_ceilings": {
            "maximum_observed_cost_per_model": deepcopy(
                authorization["maximum_observed_cost_per_model"]
            ),
            "maximum_total_observed_cost": authorization[
                "maximum_total_observed_cost"
            ],
        },
        "transport_calls": 0,
        "live_execution": False,
        "winner_selected": False,
        "production_activation": False,
        "authority_invariants": {
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
        },
    }


def run_controlled_provider_benchmark(
    *,
    plan: Dict[str, Any],
    authorization: Dict[str, Any],
    pricing: Dict[str, Any],
    transport: Callable[[Dict[str, Any], int], Dict[str, Any]],
    execution_at_utc: str,
    prior_checkpoint: Dict[str, Any] | None = None,
    result_path: str | Path | None = None,
    repository_root: str | Path | None = None,
    live_execution: bool = False,
) -> Dict[str, Any]:
    """Validate an exact future run; default-off mode never enters transport."""

    controlled_plan = deepcopy(plan)
    pricing_payload = deepcopy(pricing)
    authorization_payload = deepcopy(authorization)
    validate_controlled_provider_benchmark_plan(controlled_plan)
    validate_operator_approved_pricing(
        pricing_payload,
        execution_at_utc=execution_at_utc,
    )
    validate_harness_operator_authorization(
        authorization_payload,
        plan=controlled_plan,
        pricing=pricing_payload,
        execution_at_utc=execution_at_utc,
    )
    _require(callable(transport), "explicit execution transport is required")
    schedule = build_execution_schedule(
        plan=controlled_plan,
        authorization=authorization_payload,
    )
    if prior_checkpoint is not None:
        validate_checkpoint(
            prior_checkpoint,
            plan=controlled_plan,
            authorization=authorization_payload,
            pricing=pricing_payload,
        )
    if result_path is not None:
        _require(
            repository_root is not None,
            "repository root is required for result path validation",
        )
        validate_ignored_result_path(
            result_path,
            repository_root=repository_root,
        )
    _require(
        live_execution is False,
        "live benchmark execution is not authorized by Step 8Q",
    )
    return _dry_run_summary(
        plan=controlled_plan,
        authorization=authorization_payload,
        schedule=schedule,
    )
