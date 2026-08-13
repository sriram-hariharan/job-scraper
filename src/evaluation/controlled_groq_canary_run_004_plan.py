"""Offline two-case plan for the run-004 Groq 120B follow-up canary."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
import json
from typing import Any, Dict, Iterable, Mapping

from src.evaluation.controlled_provider_benchmark_plan import (
    CONTROLLED_PLAN_VERSION,
    build_controlled_provider_benchmark_plan,
    load_run_plan_fixture,
    validate_controlled_provider_benchmark_plan,
)
from src.evaluation.controlled_groq_provider_canary import (
    build_controlled_groq_canary_contract,
    validate_controlled_groq_canary_contract,
)
from src.evaluation.provider_benchmark_contract import (
    CONTRACT_VERSION as BENCHMARK_CONTRACT_VERSION,
    build_provider_benchmark_contract,
    provider_benchmark_contract_sha256,
    validate_provider_benchmark_contract,
)
from src.evaluation.provider_fixture_benchmark import (
    CASE_CORPUS_VERSION,
    FIXTURE_BENCHMARK_VERSION,
    build_provider_fixture_benchmark_contract,
    fixture_case_corpus_sha256,
    load_fixture_case_corpus,
    provider_fixture_benchmark_sha256,
    validate_fixture_case_corpus,
    validate_provider_fixture_benchmark_contract,
)


RUN_004_PLAN_VERSION = "controlled-groq-canary-run-004-plan-v1"
RUN_004_IDENTIFIER = "phase11-groq-canary-004"
RUN_004_CONTRACT_KIND = (
    "offline-two-case-groq-120b-quality-confirmation-plan"
)

TARGET_WORKLOADS = ("jd_intelligence", "tailoring_generation")
TARGET_PROVIDER = "groq"
TARGET_MODEL = "openai/gpt-oss-120b"
RUN_004_SCHEDULE_KEY_PREFIX = "canary_run_004_"
HISTORICAL_TARGET_ALIASES = {
    "jd_intelligence": "case_db0a584dd7f8653ca842281f",
    "tailoring_generation": "case_ece85e9411ca52b579359fb8",
}
CURRENT_TARGET_OWNERSHIP = {
    "jd_intelligence": {
        "case_alias": "case_c4f73240ce6ff98809579b5d",
        "case_id": "jd_intelligence_signals_v1",
        "schema_id": "jd_intelligence_result_v1",
    },
    "tailoring_generation": {
        "case_alias": "case_3dddc5f43be918e0932d3bb2",
        "case_id": "tailoring_generation_evidence_bound_v1",
        "schema_id": "tailoring_generation_result_v1",
    },
}
_HISTORICAL_BENCHMARK_CONTRACT_SHA256 = (
    "ba4e817f4e82f9df967011709a42bc7d2f22998f176f555cfee9dfc9e0071b98"
)
_HISTORICAL_CONTROLLED_PLAN_SHA256 = (
    "a3ef53ff992a2d1daf43f8fa9b0556202268d34e21f7611eb5de4d26e9abe6b6"
)
_HISTORICAL_FIXTURE_CORPUS_SHA256 = (
    "0ddc82e62745856c0d5d4d3f0efbe3fc86bd4e84e5da070f54f4ea635e74b05c"
)
_HISTORICAL_STEP8O_ENGINE_SHA256 = (
    "7a6463fc465d963633f82a18de0b067daab31dc387680b1d004e706c61a55c15"
)
_HISTORICAL_RUN_004_SCHEDULE_KEYS = {
    "jd_intelligence": "canary_run_004_db0b880f7fdc091fd113a70d6e277b5890770f2d9e8301de5e750b821bb8c3b9",
    "tailoring_generation": "canary_run_004_c2f21c6c570b6361605978732fcdc603f2884c2764194e66b541a84ca4438b69",
}
_HISTORICAL_BASE_TRANSPORT_ROWS = {
    "jd_intelligence": {
        "execution_order": 3,
        "case_alias": "case_db0a584dd7f8653ca842281f",
        "workload_id": "jd_intelligence",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "timeout_seconds": 30,
        "fallback": False,
        "harness_retry_limit": 0,
        "provider_sdk_retry_limit": 0,
        "schedule_key": "canary_8b167323a8667845ab0e26083b5294f5",
    },
    "tailoring_generation": {
        "execution_order": 4,
        "case_alias": "case_ece85e9411ca52b579359fb8",
        "workload_id": "tailoring_generation",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
        "timeout_seconds": 30,
        "fallback": False,
        "harness_retry_limit": 0,
        "provider_sdk_retry_limit": 0,
        "schedule_key": "canary_969374f055f6d3a74a60a3e4ce6ee440",
    },
}
EXPECTED_CANONICAL_REQUEST_SIZES = {
    "jd_intelligence": 768,
    "tailoring_generation": 641,
}

_PLAN_FIELDS = {
    "run_004_plan_version",
    "run_identifier",
    "contract_kind",
    "benchmark_contract_version",
    "benchmark_contract_sha256",
    "controlled_plan_version",
    "controlled_plan_sha256",
    "fixture_corpus_version",
    "fixture_corpus_sha256",
    "step8o_engine_version",
    "step8o_engine_sha256",
    "target_case_aliases",
    "target_workloads",
    "target_provider",
    "target_model",
    "schedule",
    "base_transport_mapping",
    "request_bounds",
    "token_bounds",
    "stop_policy",
    "transmission_safety_assertions",
    "authority_invariants",
}
_MAPPING_FIELDS = {
    "execution_order",
    "run_004_schedule_key",
    "workload_id",
    "base_schedule_key",
    "base_transport_row",
}
_SCHEDULE_FIELDS = {
    "execution_order",
    "case_alias",
    "workload_id",
    "provider",
    "model",
    "timeout_seconds",
    "fallback",
    "harness_retry_limit",
    "provider_sdk_retry_limit",
    "schedule_key",
}
_PACKET_FIELDS = {
    "benchmark_contract_version",
    "run_plan_version",
    "case_alias",
    "workload_id",
    "provider",
    "model",
    "synthetic_input",
    "output_schema",
    "temperature",
    "maximum_completion_tokens",
    "timeout_seconds",
    "fallback",
    "live_execution_requested",
}
_REVIEW_FALSE_FIELDS = {
    "contains_personal_data",
    "contains_runtime_derived_data",
    "contains_employer_or_company_identity",
    "contains_person_name",
    "contains_resume_derived_text",
    "contains_private_job_description_text",
    "contains_credentials_or_secrets",
    "contains_internal_paths",
    "contains_request_identifiers",
    "contains_database_information",
    "contains_proprietary_application_state",
    "contains_unsupported_free_form_text",
}
_FORBIDDEN_EXACT_KEYS = {
    "recommended_route",
    "selected_model",
    "selected_provider",
    "selected_winner",
    "winning_model",
}
_PROHIBITED_PACKET_KEY_PARTS = {
    "application_state",
    "ats",
    "credential",
    "database",
    "environment",
    "expected",
    "golden",
    "grader",
    "header",
    "owner_id",
    "prompt",
    "provenance",
    "raw_provider",
    "raw_response",
    "reasoning",
    "repository_path",
    "request_id",
    "request_payload",
    "resume_content",
    "route",
    "secret",
    "threshold",
    "tool_output",
    "transport_log",
    "user_name",
    "winner",
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


def _normalized_key(value: Any) -> str:
    return str(value).strip().lower().replace("-", "_").replace(" ", "_")


def _iter_keys(value: Any) -> Iterable[str]:
    if isinstance(value, Mapping):
        for key, item in value.items():
            yield _normalized_key(key)
            yield from _iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_keys(item)


def _contains_forbidden_plan_key(value: Any) -> bool:
    return any(key in _FORBIDDEN_EXACT_KEYS for key in _iter_keys(value))


def _contains_prohibited_packet_key(value: Any) -> bool:
    return any(
        any(part in key for part in _PROHIBITED_PACKET_KEY_PARTS)
        for key in _iter_keys(value)
    )


@lru_cache(maxsize=1)
def _committed_ownership() -> tuple[
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    Dict[str, Any],
    list[Dict[str, Any]],
    Dict[str, Any],
]:
    corpus = load_fixture_case_corpus()
    validate_fixture_case_corpus(corpus)
    benchmark = build_provider_benchmark_contract()
    validate_provider_benchmark_contract(benchmark)
    controlled_plan = build_controlled_provider_benchmark_plan(corpus=corpus)
    validate_controlled_provider_benchmark_plan(controlled_plan)
    step8o = build_provider_fixture_benchmark_contract(corpus)
    validate_provider_fixture_benchmark_contract(step8o)
    fixture = load_run_plan_fixture()
    canary = build_controlled_groq_canary_contract(controlled_plan)
    validate_controlled_groq_canary_contract(canary)

    reviews = controlled_plan["transmission_review"]
    cases = corpus["cases"]
    _require(
        len(reviews) == len(cases),
        "transmission review and fixture corpus disagree",
    )
    ownership = []
    for execution_order, workload in enumerate(TARGET_WORKLOADS, 1):
        matches = [
            (review, case)
            for review, case in zip(reviews, cases)
            if review["workload_id"] == workload
            and review["eligible_for_later_controlled_transmission"] is True
        ]
        _require(
            len(matches) == 1,
            f"run-004 requires exactly one eligible {workload} case",
        )
        review, case = matches[0]
        current_target = CURRENT_TARGET_OWNERSHIP[workload]
        _require(
            review["case_alias"] == current_target["case_alias"],
            f"current {workload} case alias changed",
        )
        _require(
            review["wholly_synthetic"] is True
            and review["requires_additional_redaction"] is False
            and review["human_approval_required"] is True
            and review["eligibility_reasons"] == [],
            "run-004 target is not wholly synthetic and transmission safe",
        )
        _require(
            all(review[field] is False for field in _REVIEW_FALSE_FIELDS),
            "run-004 target contains prohibited transmission material",
        )
        _require(
            case["case_id"] == current_target["case_id"]
            and case["workload_id"] == workload
            and case["schema_id"] == current_target["schema_id"]
            and case["sanitized_classification"] == "synthetic_sanitized"
            and case["contains_personal_resume_content"] is False
            and case["additional_redaction_required"] is False,
            "run-004 fixture case ownership changed",
        )
        base_rows = [
            row
            for row in canary["schedule"]
            if row["workload_id"] == workload
            and row["provider"] == TARGET_PROVIDER
            and row["model"] == TARGET_MODEL
        ]
        _require(
            len(base_rows) == 1,
            "run-004 target must map to one exact base transport row",
        )
        ownership.append(
            {
                "execution_order": execution_order,
                "review": deepcopy(review),
                "case": deepcopy(case),
                "base_transport_row": deepcopy(base_rows[0]),
            }
        )
    target_pair = (TARGET_PROVIDER, TARGET_MODEL)
    _require(
        target_pair
        in {
            (row["provider"], row["model"])
            for row in benchmark["candidate_definitions"]
        }
        and target_pair
        in {
            (row["provider"], row["model"])
            for row in controlled_plan["candidate_definitions"]
        },
        "run-004 provider/model is not a committed benchmark candidate",
    )
    return (
        deepcopy(corpus),
        deepcopy(benchmark),
        deepcopy(controlled_plan),
        deepcopy(step8o),
        deepcopy(fixture),
        deepcopy(ownership),
        deepcopy(canary),
    )


def _run_004_schedule_key(
    *,
    controlled_plan_sha256: str,
    fixture_corpus_sha256: str,
    workload_id: str,
    case_alias: str,
    execution_order: int,
) -> str:
    material = {
        "run_004_plan_version": RUN_004_PLAN_VERSION,
        "run_identifier": RUN_004_IDENTIFIER,
        "controlled_plan_sha256": controlled_plan_sha256,
        "fixture_corpus_sha256": fixture_corpus_sha256,
        "case_alias": case_alias,
        "workload_id": workload_id,
        "provider": TARGET_PROVIDER,
        "model": TARGET_MODEL,
        "execution_order": execution_order,
    }
    return (
        RUN_004_SCHEDULE_KEY_PREFIX
        + sha256(_canonical_json(material).encode("utf-8")).hexdigest()
    )


@lru_cache(maxsize=1)
def _expected_plan_contract() -> Dict[str, Any]:
    (
        corpus,
        benchmark,
        controlled_plan,
        step8o,
        fixture,
        ownership_rows,
        _canary,
    ) = _committed_ownership()
    plan_sha = _HISTORICAL_CONTROLLED_PLAN_SHA256
    corpus_sha = _HISTORICAL_FIXTURE_CORPUS_SHA256
    request_limits = fixture["request_limits"]
    maximum_input = controlled_plan["token_budget_schema"][
        "maximum_input_tokens_per_request"
    ]
    maximum_output = controlled_plan["token_budget_schema"][
        "maximum_output_tokens_per_request"
    ]
    schedule = []
    mapping = []
    for owned in ownership_rows:
        review = owned["review"]
        workload = review["workload_id"]
        case_alias = HISTORICAL_TARGET_ALIASES[workload]
        base_row = _HISTORICAL_BASE_TRANSPORT_ROWS[workload]
        execution_order = owned["execution_order"]
        run_key = _HISTORICAL_RUN_004_SCHEDULE_KEYS[workload]
        schedule.append({
            "execution_order": execution_order,
            "case_alias": case_alias,
            "workload_id": workload,
            "provider": TARGET_PROVIDER,
            "model": TARGET_MODEL,
            "timeout_seconds": request_limits["timeout_seconds"],
            "fallback": False,
            "harness_retry_limit": request_limits["harness_retry_limit"],
            "provider_sdk_retry_limit": 0,
            "schedule_key": run_key,
        })
        mapping.append({
            "execution_order": execution_order,
            "run_004_schedule_key": run_key,
            "workload_id": workload,
            "base_schedule_key": base_row["schedule_key"],
            "base_transport_row": deepcopy(base_row),
        })
    return {
        "run_004_plan_version": RUN_004_PLAN_VERSION,
        "run_identifier": RUN_004_IDENTIFIER,
        "contract_kind": RUN_004_CONTRACT_KIND,
        "benchmark_contract_version": BENCHMARK_CONTRACT_VERSION,
        "benchmark_contract_sha256": _HISTORICAL_BENCHMARK_CONTRACT_SHA256,
        "controlled_plan_version": CONTROLLED_PLAN_VERSION,
        "controlled_plan_sha256": plan_sha,
        "fixture_corpus_version": CASE_CORPUS_VERSION,
        "fixture_corpus_sha256": corpus_sha,
        "step8o_engine_version": FIXTURE_BENCHMARK_VERSION,
        "step8o_engine_sha256": _HISTORICAL_STEP8O_ENGINE_SHA256,
        "target_case_aliases": [row["case_alias"] for row in schedule],
        "target_workloads": list(TARGET_WORKLOADS),
        "target_provider": TARGET_PROVIDER,
        "target_model": TARGET_MODEL,
        "schedule": schedule,
        "base_transport_mapping": mapping,
        "request_bounds": {
            "maximum_total_requests": 2,
            "maximum_requests_per_provider_model": 2,
            "maximum_requests_per_case": 1,
            "serial_concurrency": 1,
            "automatic_expansion": False,
            "conditional_additional_calls": False,
        },
        "token_bounds": {
            "maximum_input_tokens_per_request": maximum_input,
            "maximum_output_tokens_per_request": maximum_output,
            "maximum_aggregate_input_tokens": maximum_input * 2,
            "maximum_aggregate_output_tokens": maximum_output * 2,
            "observed_usage_required": True,
            "missing_usage_estimation_allowed": False,
        },
        "stop_policy": {
            "stop_after_one_outcome": False,
            "stop_after_two_successes": True,
            "stop_on_hard_failure": True,
            "stop_on_ambiguous_outcome": True,
            "stop_on_missing_usage": True,
            "stop_on_provider_model_mismatch": True,
            "stop_on_unauthorized_transport_behavior": True,
            "ambiguous_timeout": "outcome_unknown_no_retry",
            "completed_key_can_resume": False,
            "ambiguous_key_can_resume": False,
            "hard_failure_key_can_resume": False,
            "failed_key_can_replay": False,
            "ambiguous_key_can_replay": False,
            "completed_key_can_replay": False,
            "terminal_result_can_resume": False,
            "fallback": False,
            "harness_retry_limit": 0,
            "provider_sdk_retry_limit": 0,
            "timeout_seconds": 30,
        },
        "transmission_safety_assertions": {
            "wholly_synthetic": review["wholly_synthetic"],
            "eligible_for_controlled_transmission": review[
                "eligible_for_later_controlled_transmission"
            ],
            "requires_additional_redaction": review[
                "requires_additional_redaction"
            ],
            **{
                field: review[field]
                for field in sorted(_REVIEW_FALSE_FIELDS)
            },
            "synthetic_input_only": True,
            "expected_output_transmission_allowed": False,
            "golden_output_transmission_allowed": False,
            "provenance_transmission_allowed": False,
        },
        "authority_invariants": {
            "live_execution_authorized": False,
            "provider_calls_allowed": False,
            "full_benchmark_authorized": False,
            "openai_provider_allowed": False,
            "gemini_allowed": False,
            "winner_selected": False,
            "routing_change_allowed": False,
            "production_activation": False,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
            "run_001_resume_allowed": False,
            "run_001_key_replay_allowed": False,
            "run_002_resume_allowed": False,
            "run_002_key_replay_allowed": False,
            "run_003_resume_allowed": False,
            "run_003_key_replay_allowed": False,
        },
    }


def build_run_004_plan_contract() -> Dict[str, Any]:
    contract = deepcopy(_expected_plan_contract())
    validate_run_004_plan_contract(contract)
    return contract


def validate_run_004_plan_contract(contract: Dict[str, Any]) -> bool:
    _require(
        isinstance(contract, dict) and set(contract) == _PLAN_FIELDS,
        "run-004 plan fields must match the exact schema",
    )
    schedule = contract.get("schedule")
    _require(
        isinstance(schedule, list)
        and len(schedule) == 2
        and all(
            isinstance(row, dict) and set(row) == _SCHEDULE_FIELDS
            for row in schedule
        ),
        "run-004 schedule must contain exactly two exact rows",
    )
    mapping = contract.get("base_transport_mapping")
    _require(
        isinstance(mapping, list)
        and len(mapping) == 2
        and all(
            isinstance(row, dict) and set(row) == _MAPPING_FIELDS
            for row in mapping
        ),
        "run-004 base transport mapping must contain two exact rows",
    )
    _require(
        not _contains_forbidden_plan_key(contract),
        "run-004 plan contains model-selection or routing fields",
    )
    _require(
        contract == _expected_plan_contract(),
        "run-004 plan differs from the committed two-case contract",
    )
    return True


def serialize_run_004_plan_contract(
    contract: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_run_004_plan_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_run_004_plan_contract(payload)
    return _canonical_json(payload)


def run_004_plan_sha256(
    contract: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_run_004_plan_contract(contract).encode("utf-8")
    ).hexdigest()


def _historical_packet_for_row(row: Dict[str, Any]) -> Dict[str, Any]:
    ownership_rows = _committed_ownership()[5]
    owned = next(
        item
        for item in ownership_rows
        if item["review"]["workload_id"] == row["workload_id"]
    )
    case = owned["case"]
    request_limits = _committed_ownership()[4]["request_limits"]
    return {
        "benchmark_contract_version": BENCHMARK_CONTRACT_VERSION,
        "run_plan_version": RUN_004_PLAN_VERSION,
        "case_alias": row["case_alias"],
        "workload_id": row["workload_id"],
        "provider": row["provider"],
        "model": row["model"],
        "synthetic_input": deepcopy(case["normalized_input_packet"]),
        "output_schema": {
            "schema_id": case["schema_id"],
            "required_fields": deepcopy(case["required_fields"]),
        },
        "temperature": request_limits["temperature"],
        "maximum_completion_tokens": request_limits[
            "maximum_completion_tokens_per_request"
        ],
        "timeout_seconds": request_limits["timeout_seconds"],
        "fallback": False,
        "live_execution_requested": False,
    }


def build_run_004_transmittable_request_packet(
    *,
    schedule_key: str,
    live_execution_requested: bool = False,
) -> Dict[str, Any]:
    _require(
        live_execution_requested is False,
        "run-004 request packet must remain default off",
    )
    plan = build_run_004_plan_contract()
    row = next(
        (item for item in plan["schedule"] if item["schedule_key"] == schedule_key),
        None,
    )
    _require(row is not None, "unknown run-004 schedule key")
    packet = _historical_packet_for_row(row)
    validate_run_004_transmittable_request_packet(
        packet,
        schedule_key=schedule_key,
    )
    return packet


def validate_run_004_transmittable_request_packet(
    packet: Dict[str, Any],
    *,
    schedule_key: str,
) -> bool:
    _require(
        isinstance(packet, dict) and set(packet) == _PACKET_FIELDS,
        "run-004 request packet fields must match the exact allowlist",
    )
    _require(
        not _contains_prohibited_packet_key(packet),
        "run-004 request packet contains prohibited material",
    )
    row, _base_row, expected = resolve_run_004_transport_inputs(
        schedule_key,
        include_packet=False,
    )
    expected = _historical_packet_for_row(row)
    _require(packet == expected, "run-004 request packet differs")
    return True


def resolve_run_004_transport_inputs(
    schedule_key: str,
    *,
    include_packet: bool = True,
) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any] | None]:
    plan = build_run_004_plan_contract()
    rows = [
        row for row in plan["schedule"] if row["schedule_key"] == schedule_key
    ]
    mappings = [
        row
        for row in plan["base_transport_mapping"]
        if row["run_004_schedule_key"] == schedule_key
    ]
    _require(
        len(rows) == 1 and len(mappings) == 1,
        "run-004 schedule key mapping is unknown or ambiguous",
    )
    row = rows[0]
    mapping = mappings[0]
    _require(
        mapping["execution_order"] == row["execution_order"]
        and mapping["workload_id"] == row["workload_id"],
        "run-004 mapping workload or order mismatch",
    )
    base_row = mapping["base_transport_row"]
    _require(
        base_row["schedule_key"] == mapping["base_schedule_key"]
        and base_row["workload_id"] == row["workload_id"]
        and base_row["case_alias"] == row["case_alias"]
        and base_row["provider"] == row["provider"] == TARGET_PROVIDER
        and base_row["model"] == row["model"] == TARGET_MODEL,
        "run-004 mapping differs from the exact base transport row",
    )
    packet = None
    if include_packet:
        packet = _historical_packet_for_row(row)
    return deepcopy(row), deepcopy(base_row), deepcopy(packet)
