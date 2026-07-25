"""Isolated Groq canary transport with a lazy, explicit client boundary.

The module is evaluation infrastructure only. Importing it does not import the
Groq SDK, read environment configuration, construct a client, open a network or
database connection, create a process or thread, or write an artifact.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import math
import re
from typing import Any, Callable, Dict, Mapping

from src.evaluation.controlled_groq_provider_canary import (
    CANARY_VERSION,
    build_controlled_groq_canary_contract,
    controlled_groq_canary_sha256,
    validate_canary_transport_request,
)
from src.evaluation.controlled_provider_benchmark_harness import (
    AmbiguousTransportTimeout,
    DefinitiveTransportFailure,
    TRANSPORT_RESULT_FIELDS,
    validate_injected_transport_result,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    validate_controlled_provider_benchmark_plan,
)


TRANSPORT_VERSION = "controlled-groq-canary-transport-v1"
LOCAL_INPUT_SIZE_UNIT = "canonical_utf8_bytes"
MAXIMUM_LOCAL_INPUT_SIZE_BYTES = 4096
SYSTEM_MESSAGE = "Return only JSON matching the supplied strict schema."

_CHAT_ARGUMENT_FIELDS = {
    "model",
    "messages",
    "temperature",
    "max_completion_tokens",
    "response_format",
    "stream",
    "n",
}
_PROHIBITED_REQUEST_KEY_PARTS = {
    "api_key",
    "application_state",
    "ats_state",
    "browser",
    "case_alias",
    "code_interpreter",
    "credential",
    "fallback",
    "golden",
    "grader",
    "header",
    "metadata",
    "mcp",
    "production_run",
    "provenance",
    "reasoning",
    "repository",
    "request_id",
    "schedule_key",
    "threshold",
    "tool",
    "user_id",
}
_CONTRACT_FIELDS = {
    "transport_version",
    "contract_kind",
    "canary_version",
    "canary_sha256",
    "candidate_provider_models",
    "request_packet_owner",
    "transport_result_owner",
    "transport_result_fields",
    "client_contract",
    "request_contract",
    "response_contract",
    "error_contract",
    "authority_invariants",
}


class UnknownProviderOutcome(RuntimeError):
    """A bounded unknown provider outcome requiring immediate stop."""


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


def _has_prohibited_request_key(value: Any) -> bool:
    return any(
        any(part in key for part in _PROHIBITED_REQUEST_KEY_PARTS)
        for key in _iter_keys(value)
    )


def _schema_name(workload_id: str) -> str:
    normalized = re.sub(r"[^a-z0-9_]+", "_", workload_id.strip().lower())
    normalized = normalized.strip("_")
    _require(bool(normalized), "workload schema name is invalid")
    return f"applylens_{normalized}_v1"


def _expected_json_schema(packet: Mapping[str, Any]) -> Dict[str, Any]:
    source = packet.get("output_schema")
    _require(
        isinstance(source, dict)
        and set(source) == {"schema_id", "required_fields"},
        "packet output schema is invalid",
    )
    required = source.get("required_fields")
    _require(
        isinstance(required, list)
        and bool(required)
        and all(isinstance(field, str) and field.strip() for field in required)
        and len(required) == len(set(required)),
        "packet required fields are invalid",
    )
    return {
        "type": "object",
        "properties": {field: {} for field in required},
        "required": list(required),
        "additionalProperties": False,
    }


def build_controlled_groq_transport_contract() -> Dict[str, Any]:
    canary = build_controlled_groq_canary_contract()
    contract = {
        "transport_version": TRANSPORT_VERSION,
        "contract_kind": "isolated_lazy_groq_canary_transport",
        "canary_version": CANARY_VERSION,
        "canary_sha256": controlled_groq_canary_sha256(canary),
        "candidate_provider_models": deepcopy(
            canary["candidate_provider_models"]
        ),
        "request_packet_owner": (
            "src/evaluation/controlled_provider_benchmark_plan.py"
        ),
        "transport_result_owner": (
            "src/evaluation/controlled_provider_benchmark_harness.py"
        ),
        "transport_result_fields": sorted(TRANSPORT_RESULT_FIELDS),
        "client_contract": {
            "lazy_sdk_import": True,
            "explicit_api_key_required": True,
            "environment_read_allowed": False,
            "global_client_allowed": False,
            "cached_client_allowed": False,
            "async_client_allowed": False,
            "max_retries": 0,
            "timeout_seconds": 30.0,
        },
        "request_contract": {
            "provider": "groq",
            "temperature": 0,
            "maximum_completion_tokens": 1024,
            "stream": False,
            "n": 1,
            "message_roles": ["system", "user"],
            "response_format": "strict_json_schema",
            "local_input_size_unit": LOCAL_INPUT_SIZE_UNIT,
            "maximum_local_input_size": MAXIMUM_LOCAL_INPUT_SIZE_BYTES,
            "local_size_is_observed_tokens": False,
        },
        "response_contract": {
            "choice_count": 1,
            "nonempty_json_content_required": True,
            "response_model_must_match": True,
            "positive_observed_input_tokens_required": True,
            "positive_observed_output_tokens_required": True,
            "raw_response_retained": False,
            "request_identifier_retained": False,
            "headers_retained": False,
            "reasoning_retained": False,
        },
        "error_contract": {
            "timeout": "ambiguous_timeout",
            "authentication": "definitive_authentication_failure",
            "configuration": "definitive_configuration_failure",
            "invalid_request": "definitive_invalid_request",
            "provider_rejection": "definitive_provider_rejection",
            "connection": "definitive_connection_failure",
            "unknown": "unknown_provider_outcome",
            "raw_exception_text_retained": False,
        },
        "authority_invariants": {
            "live_execution_authorized": False,
            "fallback": False,
            "retry_count": 0,
            "production_activation": False,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
        },
    }
    validate_controlled_groq_transport_contract(contract)
    return deepcopy(contract)


def validate_controlled_groq_transport_contract(
    contract: Dict[str, Any],
) -> bool:
    _require(isinstance(contract, dict), "transport contract must be an object")
    _require(
        set(contract) == _CONTRACT_FIELDS,
        "transport contract fields must match the exact schema",
    )
    canary = build_controlled_groq_canary_contract()
    _require(
        contract.get("transport_version") == TRANSPORT_VERSION,
        "transport version mismatch",
    )
    _require(
        contract.get("canary_version") == CANARY_VERSION
        and contract.get("canary_sha256")
        == controlled_groq_canary_sha256(canary),
        "canary contract mismatch",
    )
    _require(
        contract.get("candidate_provider_models")
        == canary["candidate_provider_models"],
        "transport candidates differ from the canary",
    )
    _require(
        contract.get("transport_result_fields")
        == sorted(TRANSPORT_RESULT_FIELDS),
        "transport result schema differs from Step 8Q",
    )
    client = contract.get("client_contract")
    _require(
        isinstance(client, dict)
        and client.get("lazy_sdk_import") is True
        and client.get("explicit_api_key_required") is True
        and client.get("environment_read_allowed") is False
        and client.get("global_client_allowed") is False
        and client.get("cached_client_allowed") is False
        and client.get("async_client_allowed") is False
        and client.get("max_retries") == 0
        and client.get("timeout_seconds") == 30.0,
        "client safety contract changed",
    )
    request = contract.get("request_contract")
    _require(
        isinstance(request, dict)
        and request.get("provider") == "groq"
        and request.get("temperature") == 0
        and request.get("maximum_completion_tokens") == 1024
        and request.get("stream") is False
        and request.get("n") == 1
        and request.get("message_roles") == ["system", "user"]
        and request.get("response_format") == "strict_json_schema"
        and request.get("local_input_size_unit") == LOCAL_INPUT_SIZE_UNIT
        and request.get("maximum_local_input_size")
        == MAXIMUM_LOCAL_INPUT_SIZE_BYTES
        and request.get("local_size_is_observed_tokens") is False,
        "request safety contract changed",
    )
    authority = contract.get("authority_invariants")
    _require(
        isinstance(authority, dict)
        and authority.get("live_execution_authorized") is False
        and authority.get("fallback") is False
        and authority.get("retry_count") == 0
        and authority.get("production_activation") is False
        and authority.get("mutation_count") == 0
        and authority.get("application_action_count") == 0
        and authority.get("ats_action_count") == 0,
        "transport authority changed",
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


def serialize_controlled_groq_transport_contract(
    contract: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_controlled_groq_transport_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_controlled_groq_transport_contract(payload)
    return _canonical_json(payload)


def controlled_groq_transport_sha256(
    contract: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_controlled_groq_transport_contract(contract).encode("utf-8")
    ).hexdigest()


def create_live_groq_client(
    *,
    api_key: str,
    sdk_module: Any | None = None,
) -> Any:
    """Construct one uncached client from an explicit caller-supplied key."""

    _require(
        isinstance(api_key, str) and bool(api_key.strip()),
        "explicit nonempty API key is required",
    )
    if sdk_module is None:
        from groq import Groq

        factory = Groq
    else:
        factory = getattr(sdk_module, "Groq", None)
        _require(callable(factory), "injected SDK Groq factory is required")
    try:
        return factory(
            api_key=api_key,
            max_retries=0,
            timeout=30.0,
        )
    except Exception as exc:
        _raise_bounded_sdk_failure(exc)


def build_groq_chat_completion_arguments(
    *,
    packet: Dict[str, Any],
    scheduled: Mapping[str, Any],
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    validate_controlled_provider_benchmark_plan(controlled_plan)
    validate_canary_transport_request(
        packet,
        scheduled=scheduled,
        plan=controlled_plan,
    )
    _require(scheduled.get("provider") == "groq", "provider must be Groq")
    _require(
        packet.get("provider") == "groq"
        and packet.get("model") == scheduled.get("model"),
        "provider/model must match the scheduled canary row",
    )
    _require(
        scheduled.get("fallback") is False
        and packet.get("fallback") is False,
        "fallback is prohibited",
    )
    _require(
        scheduled.get("harness_retry_limit") == 0
        and scheduled.get("provider_sdk_retry_limit") == 0,
        "retries are prohibited",
    )
    _require(
        scheduled.get("timeout_seconds") == 30
        and packet.get("timeout_seconds") == 30,
        "timeout must be exactly 30 seconds",
    )
    _require(
        packet.get("live_execution_requested") is False,
        "Step 8T live execution is prohibited",
    )
    _require(packet.get("temperature") == 0, "temperature must be zero")
    maximum_completion_tokens = packet.get("maximum_completion_tokens")
    _require(
        isinstance(maximum_completion_tokens, int)
        and not isinstance(maximum_completion_tokens, bool)
        and 0 < maximum_completion_tokens <= 1024,
        "maximum completion tokens exceed the canary bound",
    )
    synthetic_input = packet.get("synthetic_input")
    _require(
        isinstance(synthetic_input, dict),
        "synthetic input must be a bounded object",
    )
    schema = _expected_json_schema(packet)
    messages = [
        {"role": "system", "content": SYSTEM_MESSAGE},
        {"role": "user", "content": _canonical_json(synthetic_input)},
    ]
    arguments = {
        "model": scheduled["model"],
        "messages": messages,
        "temperature": 0,
        "max_completion_tokens": maximum_completion_tokens,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": _schema_name(packet["workload_id"]),
                "strict": True,
                "schema": schema,
            },
        },
        "stream": False,
        "n": 1,
    }
    validate_groq_chat_completion_arguments(
        arguments,
        packet=packet,
        scheduled=scheduled,
        plan=controlled_plan,
    )
    return deepcopy(arguments)


def conservative_local_input_size_bytes(
    arguments: Mapping[str, Any],
) -> int:
    material = {
        "messages": arguments.get("messages"),
        "response_format": arguments.get("response_format"),
        "model": arguments.get("model"),
        "temperature": arguments.get("temperature"),
        "max_completion_tokens": arguments.get("max_completion_tokens"),
        "stream": arguments.get("stream"),
        "n": arguments.get("n"),
    }
    return len(_canonical_json(material).encode("utf-8"))


def validate_groq_chat_completion_arguments(
    arguments: Dict[str, Any],
    *,
    packet: Dict[str, Any],
    scheduled: Mapping[str, Any],
    plan: Dict[str, Any] | None = None,
) -> bool:
    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    validate_canary_transport_request(
        packet,
        scheduled=scheduled,
        plan=controlled_plan,
    )
    _require(
        isinstance(arguments, dict)
        and set(arguments) == _CHAT_ARGUMENT_FIELDS,
        "chat request fields must match the exact allowlist",
    )
    expected_schema = _expected_json_schema(packet)
    _require(
        arguments.get("model") == scheduled.get("model")
        and scheduled.get("provider") == "groq",
        "chat request provider/model mismatch",
    )
    _require(arguments.get("temperature") == 0, "temperature must be zero")
    _require(
        arguments.get("max_completion_tokens")
        == packet.get("maximum_completion_tokens")
        and 0 < arguments["max_completion_tokens"] <= 1024,
        "maximum completion tokens exceed the canary bound",
    )
    _require(arguments.get("stream") is False, "streaming is prohibited")
    _require(arguments.get("n") == 1, "exactly one choice is required")
    messages = arguments.get("messages")
    _require(
        isinstance(messages, list)
        and len(messages) == 2
        and [message.get("role") for message in messages]
        == ["system", "user"]
        and all(
            isinstance(message, dict)
            and set(message) == {"role", "content"}
            and isinstance(message["content"], str)
            and bool(message["content"])
            for message in messages
        ),
        "chat messages differ from the bounded allowlist",
    )
    _require(
        messages[0]["content"] == SYSTEM_MESSAGE
        and messages[1]["content"]
        == _canonical_json(packet["synthetic_input"]),
        "chat message content is not deterministic",
    )
    response_format = arguments.get("response_format")
    _require(
        response_format
        == {
            "type": "json_schema",
            "json_schema": {
                "name": _schema_name(packet["workload_id"]),
                "strict": True,
                "schema": expected_schema,
            },
        },
        "strict JSON-schema response format mismatch",
    )
    _require(
        expected_schema.get("type") == "object"
        and expected_schema.get("additionalProperties") is False,
        "strict output schema is unsafe",
    )
    _require(
        not _has_prohibited_request_key(arguments),
        "chat request contains a prohibited field",
    )
    local_size = conservative_local_input_size_bytes(arguments)
    _require(
        local_size <= MAXIMUM_LOCAL_INPUT_SIZE_BYTES,
        "conservative local input-size bound exceeded",
    )
    return True


def _read_attr(value: Any, name: str) -> Any:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def classify_sdk_exception(exc: BaseException) -> str:
    class_name = exc.__class__.__name__.strip().lower()
    status_code = getattr(exc, "status_code", None)
    try:
        status_code = int(status_code)
    except (TypeError, ValueError):
        status_code = None
    if isinstance(exc, TimeoutError) or "timeout" in class_name:
        return "ambiguous_timeout"
    if status_code in {401, 403} or any(
        marker in class_name
        for marker in ("authentication", "permission", "authorization")
    ):
        return "definitive_authentication_failure"
    if "configuration" in class_name:
        return "definitive_configuration_failure"
    if status_code in {400, 404, 405, 409, 422} or any(
        marker in class_name
        for marker in ("badrequest", "invalidrequest", "unprocessable")
    ):
        return "definitive_invalid_request"
    if status_code is not None and 400 <= status_code <= 499:
        return "definitive_provider_rejection"
    if any(
        marker in class_name
        for marker in ("connection", "connecterror", "network")
    ):
        return "definitive_connection_failure"
    return "unknown_provider_outcome"


def _raise_bounded_sdk_failure(exc: BaseException) -> None:
    category = classify_sdk_exception(exc)
    if category == "ambiguous_timeout":
        raise AmbiguousTransportTimeout("ambiguous_timeout") from None
    if category.startswith("definitive_"):
        raise DefinitiveTransportFailure(category) from None
    raise UnknownProviderOutcome("unknown_provider_outcome") from None


def reduce_groq_sdk_response(
    response: Any,
    *,
    scheduled: Mapping[str, Any],
    packet: Dict[str, Any],
    latency_ms: float,
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    _require(
        isinstance(latency_ms, (int, float))
        and not isinstance(latency_ms, bool)
        and math.isfinite(float(latency_ms))
        and latency_ms >= 0,
        "measured latency is invalid",
    )
    choices = _read_attr(response, "choices")
    if not isinstance(choices, (list, tuple)) or len(choices) != 1:
        raise DefinitiveTransportFailure("malformed_choice_count")
    response_model = _read_attr(response, "model")
    if response_model != scheduled.get("model"):
        raise DefinitiveTransportFailure("provider_model_mismatch")
    message = _read_attr(choices[0], "message")
    content = _read_attr(message, "content")
    if not isinstance(content, str) or not content.strip():
        raise DefinitiveTransportFailure("malformed_empty_content")
    try:
        normalized_output = json.loads(content)
    except (TypeError, ValueError):
        raise DefinitiveTransportFailure("malformed_json_content") from None
    expected_schema = _expected_json_schema(packet)
    required = set(expected_schema["required"])
    if (
        not isinstance(normalized_output, dict)
        or set(normalized_output) != required
    ):
        raise DefinitiveTransportFailure("schema_incompatible_content")
    usage = _read_attr(response, "usage")
    input_tokens = _read_attr(usage, "prompt_tokens")
    output_tokens = _read_attr(usage, "completion_tokens")
    for value, label, ceiling in (
        (input_tokens, "input", 4096),
        (output_tokens, "output", 1024),
    ):
        if (
            not isinstance(value, int)
            or isinstance(value, bool)
            or value <= 0
        ):
            raise DefinitiveTransportFailure(f"missing_{label}_usage")
        if value > ceiling:
            raise DefinitiveTransportFailure(f"{label}_usage_ceiling_exceeded")
    result = {
        "normalized_output": normalized_output,
        "provider": "groq",
        "model": scheduled["model"],
        "latency_ms": float(latency_ms),
        "input_token_count": input_tokens,
        "output_token_count": output_tokens,
        "provider_outcome_category": "success",
    }
    validate_injected_transport_result(result, scheduled=scheduled)
    return deepcopy(result)


def execute_groq_chat_completion_once(
    *,
    client: Any,
    packet: Dict[str, Any],
    scheduled: Mapping[str, Any],
    monotonic_clock: Callable[[], float],
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Execute one synchronous call and immediately discard the raw envelope."""

    _require(client is not None, "one explicit client is required")
    _require(callable(monotonic_clock), "monotonic clock is required")
    arguments = build_groq_chat_completion_arguments(
        packet=packet,
        scheduled=scheduled,
        plan=plan,
    )
    try:
        started = monotonic_clock()
        response = client.chat.completions.create(**deepcopy(arguments))
        finished = monotonic_clock()
    except Exception as exc:
        _raise_bounded_sdk_failure(exc)
    try:
        latency_ms = (float(finished) - float(started)) * 1000.0
    except (TypeError, ValueError, OverflowError):
        raise DefinitiveTransportFailure("invalid_latency_measurement") from None
    return reduce_groq_sdk_response(
        response,
        scheduled=scheduled,
        packet=packet,
        latency_ms=latency_ms,
        plan=plan,
    )
