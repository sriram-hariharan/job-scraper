"""Offline-only identity ownership for a future Groq canary run 002.

This additive evaluation module derives bounded identity metadata from the
committed v1 canary, transport, and evidence-runtime contracts. It reads no
environment or credential, imports no provider SDK, performs no I/O, and
grants no execution authority.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Dict, Mapping

from src.evaluation.controlled_groq_canary_evidence_runtime import (
    EVIDENCE_RUNTIME_VERSION,
)
from src.evaluation.controlled_groq_canary_transport import (
    TRANSPORT_VERSION,
    controlled_groq_transport_sha256,
)
from src.evaluation.controlled_groq_provider_canary import (
    CANARY_VERSION,
    build_controlled_groq_canary_contract,
    controlled_groq_canary_sha256,
)


RUN_IDENTITY_VERSION = "controlled-groq-canary-run-identity-v1"
RUN_IDENTIFIER = "phase11-groq-canary-002"
AUTHORIZATION_TEMPLATE_VERSION = (
    "controlled-groq-canary-run-authorization-template-v1"
)
PLACEHOLDER = "OPERATOR_INPUT_REQUIRED"

RUN_002_ARTIFACT_PATHS = {
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
PROTECTED_RUN_001_ARTIFACTS = {
    "checkpoint": (
        "outputs/provider_benchmark/"
        "phase11_groq_canary_checkpoint_001.json"
    ),
    "result": (
        "outputs/provider_benchmark/phase11_groq_canary_result_001.json"
    ),
}

_IDENTITY_FIELDS = {
    "run_identity_version",
    "run_identifier",
    "contract_kind",
    "base_canary_version",
    "base_canary_sha256",
    "transport_version",
    "transport_sha256",
    "evidence_runtime_version",
    "candidate_provider_models",
    "schedule",
    "future_artifact_identities",
    "protected_prior_incident_artifacts",
    "request_bounds",
    "token_bounds",
    "stop_policy",
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
    "base_schedule_key",
    "run_schedule_key",
}
_TEMPLATE_FIELDS = {
    "authorization_template_version",
    "run_identity_version",
    "run_identifier",
    "run_identity_sha256",
    "base_canary_sha256",
    "transport_sha256",
    "candidate_provider_models",
    "run_schedule_keys",
    "approved_case_aliases",
    "request_bounds",
    "token_ceilings",
    "reserved_artifact_paths",
    "maximum_observed_cost_per_model",
    "maximum_total_observed_cost",
    "pricing_table_sha256",
    "valid_from_utc",
    "expires_at_utc",
    "operator_approved",
    "fallback_allowed",
    "retry_count",
    "gemini_allowed",
    "openai_provider_allowed",
    "live_execution_authorized",
    "production_activation_allowed",
    "mutation_authority_allowed",
    "application_authority_allowed",
    "ats_authority_allowed",
    "run_001_resume_allowed",
    "run_001_key_replay_allowed",
}
_FORBIDDEN_KEYS = {
    "api_key",
    "credential",
    "environment",
    "golden",
    "header",
    "normalized_output",
    "prompt",
    "raw_response",
    "reasoning",
    "request_id",
    "route",
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


def _iter_keys(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key).strip().lower()
            yield from _iter_keys(item)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_keys(item)


def _contains_forbidden_key(value: Any) -> bool:
    return any(key in _FORBIDDEN_KEYS for key in _iter_keys(value))


def _run_schedule_key(
    *,
    base_canary_sha256: str,
    base_schedule_key: str,
    execution_order: int,
) -> str:
    material = {
        "run_identity_version": RUN_IDENTITY_VERSION,
        "run_identifier": RUN_IDENTIFIER,
        "base_canary_sha256": base_canary_sha256,
        "base_schedule_key": base_schedule_key,
        "execution_order": execution_order,
    }
    digest = sha256(_canonical_json(material).encode("utf-8")).hexdigest()
    return f"canary_run_002_{digest[:32]}"


def _expected_identity_contract() -> Dict[str, Any]:
    canary = build_controlled_groq_canary_contract()
    canary_sha = controlled_groq_canary_sha256(canary)
    schedule = []
    for row in canary["schedule"]:
        schedule.append(
            {
                "execution_order": row["execution_order"],
                "case_alias": row["case_alias"],
                "workload_id": row["workload_id"],
                "provider": row["provider"],
                "model": row["model"],
                "timeout_seconds": row["timeout_seconds"],
                "fallback": row["fallback"],
                "harness_retry_limit": row["harness_retry_limit"],
                "provider_sdk_retry_limit": row[
                    "provider_sdk_retry_limit"
                ],
                "base_schedule_key": row["schedule_key"],
                "run_schedule_key": _run_schedule_key(
                    base_canary_sha256=canary_sha,
                    base_schedule_key=row["schedule_key"],
                    execution_order=row["execution_order"],
                ),
            }
        )
    return {
        "run_identity_version": RUN_IDENTITY_VERSION,
        "run_identifier": RUN_IDENTIFIER,
        "contract_kind": "offline_future_groq_canary_run_identity",
        "base_canary_version": CANARY_VERSION,
        "base_canary_sha256": canary_sha,
        "transport_version": TRANSPORT_VERSION,
        "transport_sha256": controlled_groq_transport_sha256(),
        "evidence_runtime_version": EVIDENCE_RUNTIME_VERSION,
        "candidate_provider_models": deepcopy(
            canary["candidate_provider_models"]
        ),
        "schedule": schedule,
        "future_artifact_identities": deepcopy(RUN_002_ARTIFACT_PATHS),
        "protected_prior_incident_artifacts": {
            **deepcopy(PROTECTED_RUN_001_ARTIFACTS),
            "checkpoint_immutable": True,
            "result_must_remain_absent": True,
            "resume_run_001_allowed": False,
            "use_checkpoint_001_as_initial_state": False,
            "write_to_run_001_paths_allowed": False,
        },
        "request_bounds": deepcopy(canary["request_bounds"]),
        "token_bounds": deepcopy(canary["token_bounds"]),
        "stop_policy": deepcopy(canary["stop_policy"]),
        "authority_invariants": {
            "identity_only": True,
            "live_execution_authorized": False,
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
        },
    }


def build_run_identity_contract() -> Dict[str, Any]:
    contract = _expected_identity_contract()
    validate_run_identity_contract(contract)
    return deepcopy(contract)


def validate_run_identity_contract(contract: Dict[str, Any]) -> bool:
    _require(
        isinstance(contract, dict) and set(contract) == _IDENTITY_FIELDS,
        "run identity fields must match the exact schema",
    )
    _require(
        not _contains_forbidden_key(contract),
        "run identity contains a forbidden field",
    )
    schedule = contract.get("schedule")
    _require(
        isinstance(schedule, list)
        and len(schedule) == 4
        and all(
            isinstance(row, dict) and set(row) == _SCHEDULE_FIELDS
            for row in schedule
        ),
        "run schedule schema is invalid",
    )
    keys = [row["run_schedule_key"] for row in schedule]
    _require(len(keys) == len(set(keys)), "run schedule keys must be unique")
    expected = _expected_identity_contract()
    _require(contract == expected, "run identity contract changed")
    return True


def serialize_run_identity_contract(
    contract: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_run_identity_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_run_identity_contract(payload)
    return _canonical_json(payload)


def run_identity_sha256(contract: Dict[str, Any] | None = None) -> str:
    return sha256(
        serialize_run_identity_contract(contract).encode("utf-8")
    ).hexdigest()


def _expected_authorization_template() -> Dict[str, Any]:
    identity = build_run_identity_contract()
    return {
        "authorization_template_version": AUTHORIZATION_TEMPLATE_VERSION,
        "run_identity_version": RUN_IDENTITY_VERSION,
        "run_identifier": RUN_IDENTIFIER,
        "run_identity_sha256": run_identity_sha256(identity),
        "base_canary_sha256": identity["base_canary_sha256"],
        "transport_sha256": identity["transport_sha256"],
        "candidate_provider_models": deepcopy(
            identity["candidate_provider_models"]
        ),
        "run_schedule_keys": [
            row["run_schedule_key"] for row in identity["schedule"]
        ],
        "approved_case_aliases": [
            row["case_alias"] for row in identity["schedule"]
        ],
        "request_bounds": deepcopy(identity["request_bounds"]),
        "token_ceilings": deepcopy(identity["token_bounds"]),
        "reserved_artifact_paths": deepcopy(RUN_002_ARTIFACT_PATHS),
        "maximum_observed_cost_per_model": {
            f"{row['provider']}/{row['model']}": PLACEHOLDER
            for row in identity["candidate_provider_models"]
        },
        "maximum_total_observed_cost": PLACEHOLDER,
        "pricing_table_sha256": PLACEHOLDER,
        "valid_from_utc": PLACEHOLDER,
        "expires_at_utc": PLACEHOLDER,
        "operator_approved": False,
        "fallback_allowed": False,
        "retry_count": 0,
        "gemini_allowed": False,
        "openai_provider_allowed": False,
        "live_execution_authorized": False,
        "production_activation_allowed": False,
        "mutation_authority_allowed": False,
        "application_authority_allowed": False,
        "ats_authority_allowed": False,
        "run_001_resume_allowed": False,
        "run_001_key_replay_allowed": False,
    }


def build_run_authorization_template() -> Dict[str, Any]:
    template = _expected_authorization_template()
    validate_run_authorization_template(template)
    return deepcopy(template)


def validate_run_authorization_template(template: Dict[str, Any]) -> bool:
    _require(
        isinstance(template, dict) and set(template) == _TEMPLATE_FIELDS,
        "authorization template fields must match the exact schema",
    )
    _require(
        not _contains_forbidden_key(template),
        "authorization template contains a forbidden field",
    )
    _require(
        template == _expected_authorization_template(),
        "authorization template changed or gained authority",
    )
    return True


def serialize_run_authorization_template(
    template: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_run_authorization_template()
        if template is None
        else deepcopy(template)
    )
    validate_run_authorization_template(payload)
    return _canonical_json(payload)


def run_authorization_template_sha256(
    template: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_run_authorization_template(template).encode("utf-8")
    ).hexdigest()
