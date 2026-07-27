"""Additive, default-off Groq transport for the tailoring benchmark adapter."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
from typing import Any, Callable, Dict, Mapping

from src.evaluation.controlled_groq_canary_transport import (
    MAXIMUM_LOCAL_INPUT_SIZE_BYTES,
    TRANSPORT_VERSION as GENERIC_TRANSPORT_VERSION,
    UnknownProviderOutcome,
    classify_sdk_exception,
    conservative_local_input_size_bytes,
    controlled_groq_transport_sha256,
    reduce_groq_sdk_response,
)
from src.evaluation.controlled_groq_provider_canary import (
    validate_canary_transport_request,
)
from src.evaluation.controlled_provider_benchmark_harness import (
    AmbiguousTransportTimeout,
    DefinitiveTransportFailure,
    TRANSPORT_RESULT_FIELDS,
    validate_injected_transport_result,
)
from src.evaluation.controlled_tailoring_benchmark_request_adapter import (
    ADAPTER_VERSION,
    TARGET_MODEL,
    TARGET_PROVIDER,
    TARGET_WORKLOAD,
    build_adapted_tailoring_request_specification,
    controlled_tailoring_request_adapter_sha256,
    validate_adapted_tailoring_request_specification,
    validate_normalized_tailoring_response,
)


TAILORING_TRANSPORT_VERSION = "controlled-groq-tailoring-canary-transport-v1"
TAILORING_SCHEMA_NAME = "applylens_tailoring_generation_evidence_bound_v1"

_CHAT_ARGUMENT_FIELDS = {
    "model",
    "messages",
    "temperature",
    "max_completion_tokens",
    "response_format",
    "stream",
    "n",
}
_CONTRACT_FIELDS = {
    "transport_version",
    "contract_kind",
    "tailoring_adapter",
    "generic_transport",
    "target",
    "client_contract",
    "request_contract",
    "response_contract",
    "authority_invariants",
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


def build_controlled_groq_tailoring_transport_contract() -> Dict[str, Any]:
    contract = {
        "transport_version": TAILORING_TRANSPORT_VERSION,
        "contract_kind": "additive_evaluation_only_tailoring_transport",
        "tailoring_adapter": {
            "version": ADAPTER_VERSION,
            "sha256": controlled_tailoring_request_adapter_sha256(),
        },
        "generic_transport": {
            "version": GENERIC_TRANSPORT_VERSION,
            "sha256": controlled_groq_transport_sha256(),
        },
        "target": {
            "workload_id": TARGET_WORKLOAD,
            "provider": TARGET_PROVIDER,
            "model": TARGET_MODEL,
        },
        "client_contract": {
            "explicit_caller_supplied_client_required": True,
            "environment_read_allowed": False,
            "sdk_import_during_module_import_allowed": False,
            "client_construction_allowed": False,
            "global_client_allowed": False,
            "cached_client_allowed": False,
            "synchronous_call_count": 1,
        },
        "request_contract": {
            "temperature": 0,
            "maximum_completion_tokens": 1024,
            "timeout_seconds": 30,
            "stream": False,
            "n": 1,
            "serial_concurrency": 1,
            "retry_count": 0,
            "fallback": False,
            "maximum_local_input_size_bytes": (
                MAXIMUM_LOCAL_INPUT_SIZE_BYTES
            ),
            "typed_tailoring_schema_required": True,
            "tailoring_specific_messages_required": True,
        },
        "response_contract": {
            "transport_result_fields": sorted(TRANSPORT_RESULT_FIELDS),
            "local_tailoring_validation_required": True,
            "raw_sdk_envelope_retained": False,
            "generated_text_retained": False,
            "messages_retained": False,
            "request_identifier_retained": False,
            "headers_retained": False,
            "reasoning_retained": False,
            "exception_text_retained": False,
        },
        "authority_invariants": {
            "live_execution_authorized": False,
            "production_activation": False,
            "routing_authority": False,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
            "automatic_runner": False,
        },
    }
    validate_controlled_groq_tailoring_transport_contract(contract)
    return deepcopy(contract)


def validate_controlled_groq_tailoring_transport_contract(
    contract: Dict[str, Any],
) -> bool:
    _require(
        isinstance(contract, dict) and set(contract) == _CONTRACT_FIELDS,
        "tailoring transport contract fields are invalid",
    )
    _require(
        contract.get("transport_version") == TAILORING_TRANSPORT_VERSION
        and contract.get("contract_kind")
        == "additive_evaluation_only_tailoring_transport",
        "tailoring transport identity is invalid",
    )
    _require(
        contract.get("tailoring_adapter")
        == {
            "version": ADAPTER_VERSION,
            "sha256": controlled_tailoring_request_adapter_sha256(),
        },
        "tailoring adapter binding is invalid",
    )
    _require(
        contract.get("generic_transport")
        == {
            "version": GENERIC_TRANSPORT_VERSION,
            "sha256": controlled_groq_transport_sha256(),
        },
        "generic transport binding is invalid",
    )
    _require(
        contract.get("target")
        == {
            "workload_id": TARGET_WORKLOAD,
            "provider": TARGET_PROVIDER,
            "model": TARGET_MODEL,
        },
        "tailoring transport target is invalid",
    )
    _require(
        contract.get("client_contract")
        == {
            "explicit_caller_supplied_client_required": True,
            "environment_read_allowed": False,
            "sdk_import_during_module_import_allowed": False,
            "client_construction_allowed": False,
            "global_client_allowed": False,
            "cached_client_allowed": False,
            "synchronous_call_count": 1,
        },
        "tailoring client boundary is invalid",
    )
    _require(
        contract.get("request_contract")
        == {
            "temperature": 0,
            "maximum_completion_tokens": 1024,
            "timeout_seconds": 30,
            "stream": False,
            "n": 1,
            "serial_concurrency": 1,
            "retry_count": 0,
            "fallback": False,
            "maximum_local_input_size_bytes": (
                MAXIMUM_LOCAL_INPUT_SIZE_BYTES
            ),
            "typed_tailoring_schema_required": True,
            "tailoring_specific_messages_required": True,
        },
        "tailoring request bounds are invalid",
    )
    response = contract.get("response_contract")
    _require(
        isinstance(response, dict)
        and response.get("transport_result_fields")
        == sorted(TRANSPORT_RESULT_FIELDS)
        and response.get("local_tailoring_validation_required") is True
        and all(
            response.get(field) is False
            for field in (
                "raw_sdk_envelope_retained",
                "generated_text_retained",
                "messages_retained",
                "request_identifier_retained",
                "headers_retained",
                "reasoning_retained",
                "exception_text_retained",
            )
        ),
        "tailoring response boundary is invalid",
    )
    _require(
        contract.get("authority_invariants")
        == {
            "live_execution_authorized": False,
            "production_activation": False,
            "routing_authority": False,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
            "automatic_runner": False,
        },
        "tailoring transport authority is invalid",
    )
    return True


def serialize_controlled_groq_tailoring_transport_contract(
    contract: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_controlled_groq_tailoring_transport_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_controlled_groq_tailoring_transport_contract(payload)
    return _canonical_json(payload)


def controlled_groq_tailoring_transport_sha256(
    contract: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_controlled_groq_tailoring_transport_contract(contract).encode(
            "utf-8"
        )
    ).hexdigest()


def build_groq_tailoring_chat_completion_arguments(
    *,
    packet: Dict[str, Any],
    scheduled: Mapping[str, Any],
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    packet_copy = deepcopy(packet)
    schedule_copy = deepcopy(dict(scheduled))
    validate_canary_transport_request(
        packet_copy,
        scheduled=schedule_copy,
        plan=plan,
    )
    _require(
        schedule_copy.get("workload_id") == TARGET_WORKLOAD
        and schedule_copy.get("provider") == TARGET_PROVIDER
        and schedule_copy.get("model") == TARGET_MODEL,
        "tailoring schedule target is invalid",
    )
    _require(
        schedule_copy.get("timeout_seconds") == 30
        and schedule_copy.get("fallback") is False
        and schedule_copy.get("harness_retry_limit") == 0
        and schedule_copy.get("provider_sdk_retry_limit") == 0,
        "tailoring schedule bounds are invalid",
    )
    adapted = build_adapted_tailoring_request_specification(
        packet=packet_copy,
        plan=plan,
    )
    arguments = {
        "model": TARGET_MODEL,
        "messages": [
            {
                "role": "system",
                "content": adapted["system_instruction"],
            },
            {
                "role": "user",
                "content": _canonical_json(adapted["user_payload"]),
            },
        ],
        "temperature": 0,
        "max_completion_tokens": 1024,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": TAILORING_SCHEMA_NAME,
                "strict": True,
                "schema": deepcopy(adapted["response_schema"]),
            },
        },
        "stream": False,
        "n": 1,
    }
    validate_groq_tailoring_chat_completion_arguments(
        arguments,
        packet=packet_copy,
        scheduled=schedule_copy,
        plan=plan,
    )
    return deepcopy(arguments)


def validate_groq_tailoring_chat_completion_arguments(
    arguments: Dict[str, Any],
    *,
    packet: Dict[str, Any],
    scheduled: Mapping[str, Any],
    plan: Dict[str, Any] | None = None,
) -> bool:
    _require(
        isinstance(arguments, dict)
        and set(arguments) == _CHAT_ARGUMENT_FIELDS,
        "tailoring chat argument fields are invalid",
    )
    adapted = build_adapted_tailoring_request_specification(
        packet=deepcopy(packet),
        plan=plan,
    )
    validate_adapted_tailoring_request_specification(adapted)
    _require(
        scheduled.get("workload_id") == TARGET_WORKLOAD
        and scheduled.get("provider") == TARGET_PROVIDER
        and scheduled.get("model") == TARGET_MODEL,
        "tailoring chat target is invalid",
    )
    _require(
        arguments.get("model") == TARGET_MODEL
        and arguments.get("temperature") == 0
        and arguments.get("max_completion_tokens") == 1024
        and arguments.get("stream") is False
        and arguments.get("n") == 1,
        "tailoring chat bounds are invalid",
    )
    _require(
        arguments.get("messages")
        == [
            {
                "role": "system",
                "content": adapted["system_instruction"],
            },
            {
                "role": "user",
                "content": _canonical_json(adapted["user_payload"]),
            },
        ],
        "tailoring chat messages are invalid",
    )
    _require(
        arguments.get("response_format")
        == {
            "type": "json_schema",
            "json_schema": {
                "name": TAILORING_SCHEMA_NAME,
                "strict": True,
                "schema": adapted["response_schema"],
            },
        },
        "tailoring typed response format is invalid",
    )
    _require(
        conservative_local_input_size_bytes(arguments)
        <= MAXIMUM_LOCAL_INPUT_SIZE_BYTES,
        "tailoring local request-size bound exceeded",
    )
    return True


def _raise_bounded_failure(exc: BaseException) -> None:
    category = classify_sdk_exception(exc)
    if category == "ambiguous_timeout":
        raise AmbiguousTransportTimeout("ambiguous_timeout") from None
    if category.startswith("definitive_"):
        raise DefinitiveTransportFailure(category) from None
    raise UnknownProviderOutcome("unknown_provider_outcome") from None


def execute_groq_tailoring_chat_completion_once(
    *,
    client: Any,
    packet: Dict[str, Any],
    scheduled: Mapping[str, Any],
    monotonic_clock: Callable[[], float],
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Execute exactly one injected synchronous call and return bounded fields."""

    _require(client is not None, "one explicit client is required")
    _require(callable(monotonic_clock), "monotonic clock is required")
    packet_copy = deepcopy(packet)
    schedule_copy = deepcopy(dict(scheduled))
    adapted = build_adapted_tailoring_request_specification(
        packet=packet_copy,
        plan=plan,
    )
    arguments = build_groq_tailoring_chat_completion_arguments(
        packet=packet_copy,
        scheduled=schedule_copy,
        plan=plan,
    )
    try:
        started = monotonic_clock()
        response = client.chat.completions.create(**deepcopy(arguments))
        finished = monotonic_clock()
    except Exception as exc:
        _raise_bounded_failure(exc)
    try:
        latency_ms = (float(finished) - float(started)) * 1000.0
    except (TypeError, ValueError, OverflowError):
        raise DefinitiveTransportFailure("invalid_latency_measurement") from None
    result = reduce_groq_sdk_response(
        response,
        scheduled=schedule_copy,
        packet=packet_copy,
        latency_ms=latency_ms,
        plan=plan,
    )
    try:
        validate_normalized_tailoring_response(
            result["normalized_output"],
            adapted_request=adapted,
        )
    except ValueError:
        raise DefinitiveTransportFailure(
            "tailoring_response_contract_invalid"
        ) from None
    validate_injected_transport_result(result, scheduled=schedule_copy)
    return deepcopy(result)
