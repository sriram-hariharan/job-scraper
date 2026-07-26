"""Offline identity and inactive authorization template for Groq run 003."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Dict, Iterable, Mapping

from src.evaluation.controlled_groq_canary_run_003_plan import (
    RUN_003_IDENTIFIER as PLAN_RUN_003_IDENTIFIER,
    RUN_003_PLAN_VERSION,
    TARGET_CASE_ALIAS,
    TARGET_MODEL,
    TARGET_PROVIDER,
    TARGET_WORKLOAD,
    build_run_003_plan_contract,
    run_003_plan_sha256,
    validate_run_003_plan_contract,
)


RUN_003_IDENTITY_VERSION = "controlled-groq-canary-run-003-identity-v1"
RUN_003_AUTHORIZATION_TEMPLATE_VERSION = (
    "controlled-groq-canary-run-003-authorization-template-v1"
)
RUN_003_IDENTIFIER = "phase11-groq-canary-003"
PLACEHOLDER = "OPERATOR_INPUT_REQUIRED"

RUN_003_ARTIFACT_PATHS = {
    "pricing": (
        "outputs/provider_benchmark/phase11_groq_canary_pricing_003.json"
    ),
    "authorization": (
        "outputs/provider_benchmark/"
        "phase11_groq_canary_authorization_003.json"
    ),
    "checkpoint": (
        "outputs/provider_benchmark/"
        "phase11_groq_canary_checkpoint_003.json"
    ),
    "result": (
        "outputs/provider_benchmark/phase11_groq_canary_result_003.json"
    ),
}
PROTECTED_RUN_001_ARTIFACT_PATHS = {
    "pricing": (
        "outputs/provider_benchmark/phase11_groq_canary_pricing_001.json"
    ),
    "authorization": (
        "outputs/provider_benchmark/"
        "phase11_groq_canary_authorization_001.json"
    ),
    "checkpoint": (
        "outputs/provider_benchmark/"
        "phase11_groq_canary_checkpoint_001.json"
    ),
    "result": (
        "outputs/provider_benchmark/phase11_groq_canary_result_001.json"
    ),
}
PROTECTED_RUN_002_ARTIFACT_PATHS = {
    "pricing": (
        "outputs/provider_benchmark/phase11_groq_canary_pricing_002.json"
    ),
    "authorization": (
        "outputs/provider_benchmark/"
        "phase11_groq_canary_authorization_002.json"
    ),
    "checkpoint": (
        "outputs/provider_benchmark/"
        "phase11_groq_canary_checkpoint_002.json"
    ),
    "result": (
        "outputs/provider_benchmark/phase11_groq_canary_result_002.json"
    ),
}

_PINNED_PLAN_SHA256 = (
    "5d63ef8bc8749645c19211184e8b7be16aa1909fbdb8a3682b9073af7270e9e8"
)
_PINNED_SCHEDULE_KEY = (
    "canary_run_003_"
    "0ba1bf8c9270b5bbe777b6a27c05342cb906ab2e0e25609714a81dde9cf4fb46"
)
_IDENTITY_FIELDS = {
    "run_003_identity_version",
    "run_identifier",
    "contract_kind",
    "run_003_plan_version",
    "run_003_plan_sha256",
    "target_case_alias",
    "target_workload",
    "target_provider",
    "target_model",
    "schedule",
    "request_bounds",
    "token_bounds",
    "stop_policy",
    "future_artifact_identities",
    "protected_prior_artifacts",
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
_AUTHORIZATION_TEMPLATE_FIELDS = {
    "authorization_template_version",
    "run_003_identity_version",
    "run_identifier",
    "run_003_identity_sha256",
    "run_003_plan_version",
    "run_003_plan_sha256",
    "candidate_provider_models",
    "approved_schedule_keys",
    "approved_case_aliases",
    "approved_workloads",
    "request_bounds",
    "token_ceilings",
    "reserved_artifact_paths",
    "maximum_observed_cost_per_model",
    "maximum_total_observed_cost",
    "pricing_table_sha256",
    "valid_from_utc",
    "expires_at_utc",
    "operator_approved",
    "live_execution_authorized",
    "fallback_allowed",
    "retry_count",
    "gemini_allowed",
    "openai_provider_allowed",
    "production_activation_allowed",
    "mutation_authority_allowed",
    "application_authority_allowed",
    "ats_authority_allowed",
    "run_001_resume_allowed",
    "run_001_key_replay_allowed",
    "run_002_resume_allowed",
    "run_002_key_replay_allowed",
}
_FORBIDDEN_EXACT_KEYS = {
    "api_key",
    "credential",
    "credentials",
    "normalized_output",
    "prompt",
    "raw_response",
    "reasoning",
    "request_id",
    "route",
    "secret",
    "selected_model",
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


def _contains_forbidden_key(value: Any) -> bool:
    return any(key in _FORBIDDEN_EXACT_KEYS for key in _iter_keys(value))


def _validated_plan() -> Dict[str, Any]:
    plan = build_run_003_plan_contract()
    validate_run_003_plan_contract(plan)
    _require(
        PLAN_RUN_003_IDENTIFIER == RUN_003_IDENTIFIER
        and plan["run_identifier"] == RUN_003_IDENTIFIER,
        "run-003 plan identifier changed",
    )
    _require(
        run_003_plan_sha256(plan) == _PINNED_PLAN_SHA256,
        "run-003 plan digest changed",
    )
    _require(
        len(plan["schedule"]) == 1
        and plan["schedule"][0]["schedule_key"] == _PINNED_SCHEDULE_KEY,
        "run-003 schedule ownership changed",
    )
    return deepcopy(plan)


def _expected_identity_contract() -> Dict[str, Any]:
    plan = _validated_plan()
    return {
        "run_003_identity_version": RUN_003_IDENTITY_VERSION,
        "run_identifier": RUN_003_IDENTIFIER,
        "contract_kind": (
            "offline-run-003-one-call-groq-120b-skill-extraction-identity"
        ),
        "run_003_plan_version": RUN_003_PLAN_VERSION,
        "run_003_plan_sha256": _PINNED_PLAN_SHA256,
        "target_case_alias": TARGET_CASE_ALIAS,
        "target_workload": TARGET_WORKLOAD,
        "target_provider": TARGET_PROVIDER,
        "target_model": TARGET_MODEL,
        "schedule": deepcopy(plan["schedule"]),
        "request_bounds": deepcopy(plan["request_bounds"]),
        "token_bounds": deepcopy(plan["token_bounds"]),
        "stop_policy": deepcopy(plan["stop_policy"]),
        "future_artifact_identities": deepcopy(RUN_003_ARTIFACT_PATHS),
        "protected_prior_artifacts": {
            "run_001": {
                "artifact_paths": deepcopy(
                    PROTECTED_RUN_001_ARTIFACT_PATHS
                ),
                "resume_allowed": False,
                "key_replay_allowed": False,
                "writes_allowed": False,
            },
            "run_002": {
                "artifact_paths": deepcopy(
                    PROTECTED_RUN_002_ARTIFACT_PATHS
                ),
                "resume_allowed": False,
                "key_replay_allowed": False,
                "writes_allowed": False,
                "checkpoint_as_run_003_initial_state_allowed": False,
                "result_as_run_003_initial_state_allowed": False,
            },
        },
        "authority_invariants": {
            "identity_only": True,
            "live_execution_authorized": False,
            "provider_calls_allowed": False,
            "full_benchmark_authorized": False,
            "fallback_allowed": False,
            "retry_count": 0,
            "openai_provider_allowed": False,
            "gemini_allowed": False,
            "winner_selected": False,
            "routing_change_allowed": False,
            "production_activation": False,
            "mutation_authority_allowed": False,
            "application_authority_allowed": False,
            "ats_authority_allowed": False,
            "run_001_resume_allowed": False,
            "run_001_key_replay_allowed": False,
            "run_002_resume_allowed": False,
            "run_002_key_replay_allowed": False,
        },
    }


def build_run_003_identity_contract() -> Dict[str, Any]:
    contract = _expected_identity_contract()
    validate_run_003_identity_contract(contract)
    return deepcopy(contract)


def validate_run_003_identity_contract(contract: Dict[str, Any]) -> bool:
    _require(
        isinstance(contract, dict) and set(contract) == _IDENTITY_FIELDS,
        "run-003 identity fields must match the exact schema",
    )
    schedule = contract.get("schedule")
    _require(
        isinstance(schedule, list)
        and len(schedule) == 1
        and isinstance(schedule[0], dict)
        and set(schedule[0]) == _SCHEDULE_FIELDS,
        "run-003 identity schedule must contain exactly one exact plan row",
    )
    _require(
        not _contains_forbidden_key(contract),
        "run-003 identity contains a forbidden field",
    )
    _require(
        contract == _expected_identity_contract(),
        "run-003 identity differs from the committed plan identity",
    )
    return True


def serialize_run_003_identity_contract(
    contract: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_run_003_identity_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_run_003_identity_contract(payload)
    return _canonical_json(payload)


def run_003_identity_sha256(
    contract: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_run_003_identity_contract(contract).encode("utf-8")
    ).hexdigest()


def _expected_authorization_template() -> Dict[str, Any]:
    identity = build_run_003_identity_contract()
    return {
        "authorization_template_version": (
            RUN_003_AUTHORIZATION_TEMPLATE_VERSION
        ),
        "run_003_identity_version": RUN_003_IDENTITY_VERSION,
        "run_identifier": RUN_003_IDENTIFIER,
        "run_003_identity_sha256": run_003_identity_sha256(identity),
        "run_003_plan_version": RUN_003_PLAN_VERSION,
        "run_003_plan_sha256": _PINNED_PLAN_SHA256,
        "candidate_provider_models": [
            {"provider": TARGET_PROVIDER, "model": TARGET_MODEL}
        ],
        "approved_schedule_keys": [_PINNED_SCHEDULE_KEY],
        "approved_case_aliases": [TARGET_CASE_ALIAS],
        "approved_workloads": [TARGET_WORKLOAD],
        "request_bounds": deepcopy(identity["request_bounds"]),
        "token_ceilings": deepcopy(identity["token_bounds"]),
        "reserved_artifact_paths": deepcopy(RUN_003_ARTIFACT_PATHS),
        "maximum_observed_cost_per_model": {
            f"{TARGET_PROVIDER}/{TARGET_MODEL}": PLACEHOLDER
        },
        "maximum_total_observed_cost": PLACEHOLDER,
        "pricing_table_sha256": PLACEHOLDER,
        "valid_from_utc": PLACEHOLDER,
        "expires_at_utc": PLACEHOLDER,
        "operator_approved": False,
        "live_execution_authorized": False,
        "fallback_allowed": False,
        "retry_count": 0,
        "gemini_allowed": False,
        "openai_provider_allowed": False,
        "production_activation_allowed": False,
        "mutation_authority_allowed": False,
        "application_authority_allowed": False,
        "ats_authority_allowed": False,
        "run_001_resume_allowed": False,
        "run_001_key_replay_allowed": False,
        "run_002_resume_allowed": False,
        "run_002_key_replay_allowed": False,
    }


def build_run_003_authorization_template() -> Dict[str, Any]:
    template = _expected_authorization_template()
    validate_run_003_authorization_template(template)
    return deepcopy(template)


def validate_run_003_authorization_template(
    template: Dict[str, Any],
) -> bool:
    _require(
        isinstance(template, dict)
        and set(template) == _AUTHORIZATION_TEMPLATE_FIELDS,
        "run-003 authorization template fields must match the exact schema",
    )
    _require(
        not _contains_forbidden_key(template),
        "run-003 authorization template contains a forbidden field",
    )
    _require(
        template == _expected_authorization_template(),
        "run-003 authorization template changed or gained authority",
    )
    return True


def serialize_run_003_authorization_template(
    template: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_run_003_authorization_template()
        if template is None
        else deepcopy(template)
    )
    validate_run_003_authorization_template(payload)
    return _canonical_json(payload)


def run_003_authorization_template_sha256(
    template: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_run_003_authorization_template(template).encode("utf-8")
    ).hexdigest()
