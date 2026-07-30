"""Offline adapter for evidence-bound tailoring benchmark requests.

The adapter is evaluation-only.  It turns an existing transmission-approved
provider-neutral packet into deterministic tailoring-specific instructions and
a strict typed response schema.  It grants no execution or mutation authority.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Dict, Mapping

from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    build_transmittable_request_packet,
    validate_controlled_provider_benchmark_plan,
)


ADAPTER_VERSION = "controlled-tailoring-benchmark-request-adapter-v1"
TARGET_WORKLOAD = "tailoring_generation"
TARGET_PROVIDER = "groq"
TARGET_MODEL = "openai/gpt-oss-120b"
TASK_IDENTIFIER = "generate_evidence_bound_tailoring_suggestions"
SYSTEM_INSTRUCTION = (
    "Generate advisory, evidence-backed resume tailoring suggestions for human "
    "review only. Use only the supplied source-bullet IDs and evidence tokens. "
    "Do not invent claims, mutate a resume, change deterministic authority, "
    "score or rank candidates, alter queues or approvals, apply, or take ATS "
    "action. Return only JSON matching the supplied strict schema."
)

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
_SYNTHETIC_INPUT_FIELDS = {"source_bullet_ids", "evidence_tokens"}
_ADAPTED_REQUEST_FIELDS = {
    "adapter_version",
    "workload_id",
    "provider",
    "model",
    "system_instruction",
    "user_payload",
    "response_schema",
}
_USER_PAYLOAD_FIELDS = {
    "task_identifier",
    "source_bullet_ids",
    "evidence_tokens",
    "requirements",
}
_RESPONSE_FIELDS = {
    "suggestions",
    "human_review_required",
    "authority_mutated",
}
_SUGGESTION_FIELDS = {
    "suggestion_id",
    "source_bullet_id",
    "claims",
    "evidence_tokens",
}
_CONTRACT_FIELDS = {
    "adapter_version",
    "contract_kind",
    "canonical_semantic_owners",
    "request_contract",
    "response_contract",
    "authority_invariants",
}
_REQUIREMENTS = {
    "minimum_suggestions": 1,
    "source_bullet_ids_must_be_supplied": True,
    "claims_must_use_supplied_evidence_tokens": True,
    "suggestion_evidence_must_use_supplied_evidence_tokens": True,
    "human_review_required": True,
    "deterministic_authority_preserved": True,
    "resume_mutation_authorized": False,
    "score_or_ranking_mutation_authorized": False,
    "queue_or_approval_mutation_authorized": False,
    "application_authorized": False,
    "ats_action_authorized": False,
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


def _validate_unique_nonempty_strings(value: Any, label: str) -> list[str]:
    _require(isinstance(value, list) and bool(value), f"{label} are invalid")
    _require(
        all(isinstance(item, str) and bool(item.strip()) for item in value),
        f"{label} are invalid",
    )
    _require(len(value) == len(set(value)), f"{label} are invalid")
    return list(value)


def build_controlled_tailoring_request_adapter_contract() -> Dict[str, Any]:
    contract = {
        "adapter_version": ADAPTER_VERSION,
        "contract_kind": "evaluation_only_tailoring_request_adapter",
        "canonical_semantic_owners": {
            "manual_tailoring_response_schema": (
                "src/app/services.py:"
                "LIVE_TAILORING_SUGGESTION_DRY_RUN_RESPONSE_SCHEMA"
            ),
            "manual_tailoring_instruction": (
                "src/app/services.py:_live_tailoring_suggestion_prompt"
            ),
            "manual_only_authority_boundary": (
                "src/app/services.py:"
                "build_manual_tailoring_suggestion_dry_run_payload"
            ),
            "deterministic_evidence_and_source_identity": (
                "src/agents/tailoring_decision_agent.py:"
                "build_tailoring_suggestion_dry_run_payload"
            ),
            "deterministic_authority_preservation": (
                "src/agents/tailoring_decision_agent.py:"
                "_tailoring_suggestion_safety_metadata"
            ),
            "provider_neutral_packet": (
                "src/evaluation/controlled_provider_benchmark_plan.py:"
                "build_transmittable_request_packet"
            ),
            "deterministic_tailoring_grader": (
                "src/evaluation/provider_fixture_benchmark.py:"
                "build_tailoring_generation_diagnostics"
            ),
        },
        "request_contract": {
            "workload_id": TARGET_WORKLOAD,
            "provider": TARGET_PROVIDER,
            "model": TARGET_MODEL,
            "packet_fields": sorted(_PACKET_FIELDS),
            "synthetic_input_fields": sorted(_SYNTHETIC_INPUT_FIELDS),
            "task_identifier": TASK_IDENTIFIER,
            "tailoring_specific_system_instruction": True,
            "expected_or_golden_output_allowed": False,
            "provenance_allowed": False,
            "personal_or_private_content_allowed": False,
            "free_form_additions_allowed": False,
        },
        "response_contract": {
            "strict_typed_json_schema": True,
            "minimum_suggestions": 1,
            "supplied_source_ids_only": True,
            "supplied_evidence_tokens_only": True,
            "local_validation_required": True,
            "generated_content_retained_on_failure": False,
        },
        "authority_invariants": {
            "human_review_required": True,
            "deterministic_authority_mutated": False,
            "resume_mutation_allowed": False,
            "score_or_ranking_mutation_allowed": False,
            "queue_or_approval_mutation_allowed": False,
            "application_action_allowed": False,
            "ats_action_allowed": False,
            "production_activation": False,
        },
    }
    validate_controlled_tailoring_request_adapter_contract(contract)
    return deepcopy(contract)


def validate_controlled_tailoring_request_adapter_contract(
    contract: Dict[str, Any],
) -> bool:
    _require(isinstance(contract, dict), "adapter contract must be an object")
    _require(
        set(contract) == _CONTRACT_FIELDS,
        "adapter contract fields must match the exact schema",
    )
    _require(contract.get("adapter_version") == ADAPTER_VERSION, "adapter version mismatch")
    _require(
        contract.get("contract_kind")
        == "evaluation_only_tailoring_request_adapter",
        "adapter kind mismatch",
    )
    owners = contract.get("canonical_semantic_owners")
    _require(
        isinstance(owners, dict)
        and set(owners)
        == {
            "manual_tailoring_response_schema",
            "manual_tailoring_instruction",
            "manual_only_authority_boundary",
            "deterministic_evidence_and_source_identity",
            "deterministic_authority_preservation",
            "provider_neutral_packet",
            "deterministic_tailoring_grader",
        }
        and all(isinstance(value, str) and ":" in value for value in owners.values()),
        "canonical semantic-owner mapping is invalid",
    )
    request = contract.get("request_contract")
    _require(
        isinstance(request, dict)
        and request.get("workload_id") == TARGET_WORKLOAD
        and request.get("provider") == TARGET_PROVIDER
        and request.get("model") == TARGET_MODEL
        and request.get("packet_fields") == sorted(_PACKET_FIELDS)
        and request.get("synthetic_input_fields")
        == sorted(_SYNTHETIC_INPUT_FIELDS)
        and request.get("task_identifier") == TASK_IDENTIFIER
        and request.get("tailoring_specific_system_instruction") is True
        and all(
            request.get(field) is False
            for field in (
                "expected_or_golden_output_allowed",
                "provenance_allowed",
                "personal_or_private_content_allowed",
                "free_form_additions_allowed",
            )
        ),
        "adapter request contract is invalid",
    )
    response = contract.get("response_contract")
    _require(
        response
        == {
            "strict_typed_json_schema": True,
            "minimum_suggestions": 1,
            "supplied_source_ids_only": True,
            "supplied_evidence_tokens_only": True,
            "local_validation_required": True,
            "generated_content_retained_on_failure": False,
        },
        "adapter response contract is invalid",
    )
    authority = contract.get("authority_invariants")
    _require(
        isinstance(authority, dict)
        and authority.get("human_review_required") is True
        and authority.get("deterministic_authority_mutated") is False
        and authority.get("production_activation") is False
        and all(
            authority.get(field) is False
            for field in (
                "resume_mutation_allowed",
                "score_or_ranking_mutation_allowed",
                "queue_or_approval_mutation_allowed",
                "application_action_allowed",
                "ats_action_allowed",
            )
        ),
        "adapter authority contract is invalid",
    )
    return True


def serialize_controlled_tailoring_request_adapter_contract(
    contract: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_controlled_tailoring_request_adapter_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_controlled_tailoring_request_adapter_contract(payload)
    return _canonical_json(payload)


def controlled_tailoring_request_adapter_sha256(
    contract: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_controlled_tailoring_request_adapter_contract(contract).encode(
            "utf-8"
        )
    ).hexdigest()


def _validate_exact_provider_neutral_packet(
    packet: Dict[str, Any],
    *,
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    _require(isinstance(packet, dict), "provider-neutral packet is invalid")
    _require(
        set(packet) == _PACKET_FIELDS,
        "provider-neutral packet fields are invalid",
    )
    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    validate_controlled_provider_benchmark_plan(controlled_plan)
    _require(
        packet.get("workload_id") == TARGET_WORKLOAD
        and packet.get("provider") == TARGET_PROVIDER
        and packet.get("model") == TARGET_MODEL,
        "tailoring provider-neutral packet target is invalid",
    )
    expected = build_transmittable_request_packet(
        case_alias=packet.get("case_alias"),
        provider=TARGET_PROVIDER,
        model=TARGET_MODEL,
        plan=controlled_plan,
        live_execution_requested=False,
    )
    _require(packet == expected, "provider-neutral packet is not allowlisted")
    _require(
        packet.get("temperature") == 0
        and packet.get("maximum_completion_tokens") == 1024
        and packet.get("timeout_seconds") == 30
        and packet.get("fallback") is False
        and packet.get("live_execution_requested") is False,
        "provider-neutral packet bounds are invalid",
    )
    output_schema = packet.get("output_schema")
    _require(
        output_schema
        == {
            "schema_id": "tailoring_generation_result_v1",
            "required_fields": [
                "suggestions",
                "human_review_required",
                "authority_mutated",
            ],
        },
        "provider-neutral output schema is invalid",
    )
    synthetic = packet.get("synthetic_input")
    _require(
        isinstance(synthetic, dict)
        and set(synthetic) == _SYNTHETIC_INPUT_FIELDS,
        "synthetic tailoring input fields are invalid",
    )
    _validate_unique_nonempty_strings(
        synthetic.get("source_bullet_ids"), "source bullet IDs"
    )
    _validate_unique_nonempty_strings(
        synthetic.get("evidence_tokens"), "evidence tokens"
    )
    return controlled_plan


def _build_response_schema(
    *,
    source_bullet_ids: list[str],
    evidence_tokens: list[str],
) -> Dict[str, Any]:
    return {
        "type": "object",
        "properties": {
            "suggestions": {
                "type": "array",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "properties": {
                        "suggestion_id": {
                            "type": "string",
                            "minLength": 1,
                        },
                        "source_bullet_id": {
                            "type": "string",
                            "enum": list(source_bullet_ids),
                        },
                        "claims": {
                            "type": "array",
                            "minItems": 1,
                            "items": {
                                "type": "string",
                                "enum": list(evidence_tokens),
                            },
                        },
                        "evidence_tokens": {
                            "type": "array",
                            "minItems": 1,
                            "items": {
                                "type": "string",
                                "enum": list(evidence_tokens),
                            },
                        },
                    },
                    "required": sorted(_SUGGESTION_FIELDS),
                    "additionalProperties": False,
                },
            },
            "human_review_required": {
                "type": "boolean",
                "const": True,
            },
            "authority_mutated": {
                "type": "boolean",
                "const": False,
            },
        },
        "required": sorted(_RESPONSE_FIELDS),
        "additionalProperties": False,
    }


def build_adapted_tailoring_request_specification(
    *,
    packet: Dict[str, Any],
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    packet_copy = deepcopy(packet)
    _validate_exact_provider_neutral_packet(packet_copy, plan=plan)
    synthetic = packet_copy["synthetic_input"]
    source_bullet_ids = list(synthetic["source_bullet_ids"])
    evidence_tokens = list(synthetic["evidence_tokens"])
    adapted = {
        "adapter_version": ADAPTER_VERSION,
        "workload_id": TARGET_WORKLOAD,
        "provider": TARGET_PROVIDER,
        "model": TARGET_MODEL,
        "system_instruction": SYSTEM_INSTRUCTION,
        "user_payload": {
            "task_identifier": TASK_IDENTIFIER,
            "source_bullet_ids": source_bullet_ids,
            "evidence_tokens": evidence_tokens,
            "requirements": deepcopy(_REQUIREMENTS),
        },
        "response_schema": _build_response_schema(
            source_bullet_ids=source_bullet_ids,
            evidence_tokens=evidence_tokens,
        ),
    }
    validate_adapted_tailoring_request_specification(adapted)
    return deepcopy(adapted)


def validate_adapted_tailoring_request_specification(
    adapted: Dict[str, Any],
) -> bool:
    _require(isinstance(adapted, dict), "adapted tailoring request is invalid")
    _require(
        set(adapted) == _ADAPTED_REQUEST_FIELDS,
        "adapted tailoring request fields are invalid",
    )
    _require(
        adapted.get("adapter_version") == ADAPTER_VERSION
        and adapted.get("workload_id") == TARGET_WORKLOAD
        and adapted.get("provider") == TARGET_PROVIDER
        and adapted.get("model") == TARGET_MODEL
        and adapted.get("system_instruction") == SYSTEM_INSTRUCTION,
        "adapted tailoring request identity is invalid",
    )
    user = adapted.get("user_payload")
    _require(
        isinstance(user, dict) and set(user) == _USER_PAYLOAD_FIELDS,
        "tailoring user payload fields are invalid",
    )
    source_ids = _validate_unique_nonempty_strings(
        user.get("source_bullet_ids"), "source bullet IDs"
    )
    evidence_tokens = _validate_unique_nonempty_strings(
        user.get("evidence_tokens"), "evidence tokens"
    )
    _require(
        user.get("task_identifier") == TASK_IDENTIFIER
        and user.get("requirements") == _REQUIREMENTS,
        "tailoring user payload semantics are invalid",
    )
    _require(
        adapted.get("response_schema")
        == _build_response_schema(
            source_bullet_ids=source_ids,
            evidence_tokens=evidence_tokens,
        ),
        "typed tailoring response schema is invalid",
    )
    return True


def serialize_adapted_tailoring_request_specification(
    adapted: Dict[str, Any],
) -> str:
    payload = deepcopy(adapted)
    validate_adapted_tailoring_request_specification(payload)
    return _canonical_json(payload)


def validate_normalized_tailoring_response(
    normalized_output: Dict[str, Any],
    *,
    adapted_request: Dict[str, Any],
) -> bool:
    request_copy = deepcopy(adapted_request)
    validate_adapted_tailoring_request_specification(request_copy)
    _require(
        isinstance(normalized_output, dict)
        and set(normalized_output) == _RESPONSE_FIELDS,
        "tailoring response fields are invalid",
    )
    suggestions = normalized_output.get("suggestions")
    _require(
        isinstance(suggestions, list) and bool(suggestions),
        "tailoring suggestions are invalid",
    )
    allowed_sources = set(request_copy["user_payload"]["source_bullet_ids"])
    allowed_evidence = set(request_copy["user_payload"]["evidence_tokens"])
    for suggestion in suggestions:
        _require(
            isinstance(suggestion, dict)
            and set(suggestion) == _SUGGESTION_FIELDS,
            "tailoring suggestion fields are invalid",
        )
        suggestion_id = suggestion.get("suggestion_id")
        _require(
            isinstance(suggestion_id, str) and bool(suggestion_id.strip()),
            "tailoring suggestion identifier is invalid",
        )
        _require(
            isinstance(suggestion.get("source_bullet_id"), str)
            and suggestion["source_bullet_id"] in allowed_sources,
            "tailoring source bullet is unsupported",
        )
        for field in ("claims", "evidence_tokens"):
            values = suggestion.get(field)
            _require(
                isinstance(values, list)
                and bool(values)
                and all(
                    isinstance(value, str) and value in allowed_evidence
                    for value in values
                ),
                f"tailoring {field} are unsupported",
            )
    _require(
        normalized_output.get("human_review_required") is True,
        "tailoring response requires human review",
    )
    _require(
        normalized_output.get("authority_mutated") is False,
        "tailoring response mutated deterministic authority",
    )
    return True
