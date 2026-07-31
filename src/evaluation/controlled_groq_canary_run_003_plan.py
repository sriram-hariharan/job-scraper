"""Offline one-call plan for the run-003 Groq 120B follow-up canary."""

from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
from hashlib import sha256
import json
from typing import Any, Dict, Iterable, Mapping

from src.evaluation.controlled_provider_benchmark_plan import (
    CONTROLLED_PLAN_VERSION,
    build_controlled_provider_benchmark_plan,
    controlled_provider_benchmark_plan_sha256,
    load_run_plan_fixture,
    validate_controlled_provider_benchmark_plan,
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


RUN_003_PLAN_VERSION = "controlled-groq-canary-run-003-plan-v1"
RUN_003_IDENTIFIER = "phase11-groq-canary-003"
RUN_003_CONTRACT_KIND = (
    "offline-one-call-groq-120b-skill-extraction-follow-up-plan"
)

TARGET_CASE_ALIAS = "case_fb2b069aa9340571b60e1fb5"
TARGET_WORKLOAD = "skill_extraction"
TARGET_PROVIDER = "groq"
TARGET_MODEL = "openai/gpt-oss-120b"
RUN_003_SCHEDULE_KEY_PREFIX = "canary_run_003_"

_PLAN_FIELDS = {
    "run_003_plan_version",
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
    "target_case_alias",
    "target_workload",
    "target_provider",
    "target_model",
    "schedule",
    "request_bounds",
    "token_bounds",
    "stop_policy",
    "transmission_safety_assertions",
    "authority_invariants",
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

    reviews = controlled_plan["transmission_review"]
    cases = corpus["cases"]
    _require(
        len(reviews) == len(cases),
        "transmission review and fixture corpus disagree",
    )
    matches = [
        (review, case)
        for review, case in zip(reviews, cases)
        if review["workload_id"] == TARGET_WORKLOAD
        and review["eligible_for_later_controlled_transmission"] is True
    ]
    _require(
        len(matches) == 1,
        "run-003 requires exactly one eligible skill-extraction case",
    )
    review, case = matches[0]
    _require(
        review["case_alias"] == TARGET_CASE_ALIAS,
        "run-003 target case alias changed",
    )
    _require(
        review["wholly_synthetic"] is True
        and review["requires_additional_redaction"] is False
        and review["human_approval_required"] is True
        and review["eligibility_reasons"] == [],
        "run-003 target is not wholly synthetic and transmission safe",
    )
    _require(
        all(review[field] is False for field in _REVIEW_FALSE_FIELDS),
        "run-003 target contains prohibited transmission material",
    )
    _require(
        case["workload_id"] == TARGET_WORKLOAD
        and case["sanitized_classification"] == "synthetic_sanitized"
        and case["contains_personal_resume_content"] is False
        and case["additional_redaction_required"] is False,
        "run-003 fixture case ownership changed",
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
        "run-003 provider/model is not a committed benchmark candidate",
    )
    return (
        deepcopy(corpus),
        deepcopy(benchmark),
        deepcopy(controlled_plan),
        deepcopy(step8o),
        deepcopy(fixture),
        {"review": deepcopy(review), "case": deepcopy(case)},
    )


def _run_003_schedule_key(
    *,
    controlled_plan_sha256: str,
    fixture_corpus_sha256: str,
) -> str:
    material = {
        "run_003_plan_version": RUN_003_PLAN_VERSION,
        "run_identifier": RUN_003_IDENTIFIER,
        "controlled_plan_sha256": controlled_plan_sha256,
        "fixture_corpus_sha256": fixture_corpus_sha256,
        "case_alias": TARGET_CASE_ALIAS,
        "workload_id": TARGET_WORKLOAD,
        "provider": TARGET_PROVIDER,
        "model": TARGET_MODEL,
        "execution_order": 1,
    }
    return (
        RUN_003_SCHEDULE_KEY_PREFIX
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
        ownership,
    ) = _committed_ownership()
    plan_sha = controlled_provider_benchmark_plan_sha256(controlled_plan)
    corpus_sha = fixture_case_corpus_sha256(corpus)
    request_limits = fixture["request_limits"]
    maximum_input = controlled_plan["token_budget_schema"][
        "maximum_input_tokens_per_request"
    ]
    maximum_output = controlled_plan["token_budget_schema"][
        "maximum_output_tokens_per_request"
    ]
    review = ownership["review"]
    schedule = [
        {
            "execution_order": 1,
            "case_alias": TARGET_CASE_ALIAS,
            "workload_id": TARGET_WORKLOAD,
            "provider": TARGET_PROVIDER,
            "model": TARGET_MODEL,
            "timeout_seconds": request_limits["timeout_seconds"],
            "fallback": False,
            "harness_retry_limit": request_limits["harness_retry_limit"],
            "provider_sdk_retry_limit": 0,
            "schedule_key": _run_003_schedule_key(
                controlled_plan_sha256=plan_sha,
                fixture_corpus_sha256=corpus_sha,
            ),
        }
    ]
    return {
        "run_003_plan_version": RUN_003_PLAN_VERSION,
        "run_identifier": RUN_003_IDENTIFIER,
        "contract_kind": RUN_003_CONTRACT_KIND,
        "benchmark_contract_version": BENCHMARK_CONTRACT_VERSION,
        "benchmark_contract_sha256": provider_benchmark_contract_sha256(
            benchmark
        ),
        "controlled_plan_version": CONTROLLED_PLAN_VERSION,
        "controlled_plan_sha256": plan_sha,
        "fixture_corpus_version": CASE_CORPUS_VERSION,
        "fixture_corpus_sha256": corpus_sha,
        "step8o_engine_version": FIXTURE_BENCHMARK_VERSION,
        "step8o_engine_sha256": provider_fixture_benchmark_sha256(step8o),
        "target_case_alias": TARGET_CASE_ALIAS,
        "target_workload": TARGET_WORKLOAD,
        "target_provider": TARGET_PROVIDER,
        "target_model": TARGET_MODEL,
        "schedule": schedule,
        "request_bounds": {
            "maximum_total_requests": 1,
            "maximum_requests_per_provider_model": 1,
            "maximum_requests_per_case": 1,
            "serial_concurrency": 1,
            "automatic_expansion": False,
            "conditional_additional_calls": False,
        },
        "token_bounds": {
            "maximum_input_tokens_per_request": maximum_input,
            "maximum_output_tokens_per_request": maximum_output,
            "maximum_aggregate_input_tokens": maximum_input,
            "maximum_aggregate_output_tokens": maximum_output,
            "observed_usage_required": True,
            "missing_usage_estimation_allowed": False,
        },
        "stop_policy": {
            "stop_after_one_outcome": True,
            "stop_on_hard_failure": True,
            "stop_on_missing_usage": True,
            "stop_on_provider_model_mismatch": True,
            "stop_on_unauthorized_transport_behavior": True,
            "ambiguous_timeout": "outcome_unknown_no_retry",
            "completed_key_can_resume": False,
            "ambiguous_key_can_resume": False,
            "hard_failure_key_can_resume": False,
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
        },
    }


def build_run_003_plan_contract() -> Dict[str, Any]:
    contract = deepcopy(_expected_plan_contract())
    validate_run_003_plan_contract(contract)
    return contract


def validate_run_003_plan_contract(contract: Dict[str, Any]) -> bool:
    _require(
        isinstance(contract, dict) and set(contract) == _PLAN_FIELDS,
        "run-003 plan fields must match the exact schema",
    )
    schedule = contract.get("schedule")
    _require(
        isinstance(schedule, list)
        and len(schedule) == 1
        and isinstance(schedule[0], dict)
        and set(schedule[0]) == _SCHEDULE_FIELDS,
        "run-003 schedule must contain exactly one exact row",
    )
    _require(
        not _contains_forbidden_plan_key(contract),
        "run-003 plan contains model-selection or routing fields",
    )
    _require(
        contract == _expected_plan_contract(),
        "run-003 plan differs from the committed one-call contract",
    )
    return True


def serialize_run_003_plan_contract(
    contract: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_run_003_plan_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_run_003_plan_contract(payload)
    return _canonical_json(payload)


def run_003_plan_sha256(
    contract: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_run_003_plan_contract(contract).encode("utf-8")
    ).hexdigest()


@lru_cache(maxsize=1)
def _expected_request_packet() -> Dict[str, Any]:
    (
        _corpus,
        _benchmark,
        _controlled_plan,
        _step8o,
        fixture,
        ownership,
    ) = _committed_ownership()
    case = ownership["case"]
    request_limits = fixture["request_limits"]
    return {
        "benchmark_contract_version": BENCHMARK_CONTRACT_VERSION,
        "run_plan_version": RUN_003_PLAN_VERSION,
        "case_alias": TARGET_CASE_ALIAS,
        "workload_id": TARGET_WORKLOAD,
        "provider": TARGET_PROVIDER,
        "model": TARGET_MODEL,
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


def build_run_003_transmittable_request_packet(
    *,
    live_execution_requested: bool = False,
) -> Dict[str, Any]:
    _require(
        live_execution_requested is False,
        "run-003 request packet must remain default off",
    )
    packet = deepcopy(_expected_request_packet())
    validate_run_003_transmittable_request_packet(packet)
    return packet


def validate_run_003_transmittable_request_packet(
    packet: Dict[str, Any],
) -> bool:
    _require(
        isinstance(packet, dict) and set(packet) == _PACKET_FIELDS,
        "run-003 request packet fields must match the exact allowlist",
    )
    _require(
        not _contains_prohibited_packet_key(packet),
        "run-003 request packet contains prohibited material",
    )
    _require(
        packet == _expected_request_packet(),
        "run-003 request packet differs from the exact target packet",
    )
    return True
