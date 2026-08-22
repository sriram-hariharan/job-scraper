"""Hermetic-ready OpenAI transport for controlled provider evaluation.

The module is evaluation infrastructure only. Importing it does not import the
OpenAI SDK, read environment configuration or user credentials, construct a
client, open a network connection, or persist an artifact.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import math
import re
from typing import Any, Callable, Dict, Mapping

from src.ai.provider_model_catalog import list_configurable_models
from src.evaluation.controlled_provider_benchmark_harness import (
    AmbiguousTransportTimeout,
    DefinitiveTransportFailure,
    TRANSPORT_RESULT_FIELDS,
    validate_injected_transport_result,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    validate_controlled_provider_benchmark_plan,
    validate_transmittable_request_packet,
)


TRANSPORT_VERSION = "controlled-openai-canary-transport-v1"
LOCAL_INPUT_SIZE_UNIT = "canonical_utf8_bytes"
MAXIMUM_LOCAL_INPUT_SIZE_BYTES = 4096
MAXIMUM_PRODUCTION_PARITY_LOCAL_INPUT_SIZE_BYTES = 16384
SYSTEM_MESSAGE = "Return only JSON matching the supplied strict schema."

_APPROVED_RESPONSE_MODEL_SNAPSHOTS = {
    "gpt-5-mini": frozenset({"gpt-5-mini-2025-08-07"}),
    "gpt-5.1": frozenset({"gpt-5.1-2025-11-13"}),
}

_BASE_CHAT_ARGUMENT_FIELDS = {
    "model",
    "messages",
    "max_completion_tokens",
    "response_format",
}
_CONTRACT_FIELDS = {
    "transport_version",
    "contract_kind",
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


def _qualification_openai_models() -> tuple[str, ...]:
    return tuple(
        row["model_id"]
        for row in list_configurable_models("openai")
        if row.get("configuration_status") == "configuration_eligible"
        and row.get("synthetic_compatibility_status")
        == "synthetic_compatibility_expected"
        and row.get("live_qualification_status")
        == "live_qualification_required"
        and row.get("eligible_benchmark_tiers")
    )


def _candidate_provider_models() -> list[Dict[str, str]]:
    return [
        {"provider": "openai", "model": model}
        for model in _qualification_openai_models()
    ]


def _is_gpt_5_mini(model: Any) -> bool:
    return str(model or "").strip() == "gpt-5-mini"


def _response_model_matches_scheduled(
    response_model: Any,
    scheduled_model: Any,
) -> bool:
    if response_model == scheduled_model:
        return True
    return response_model in _APPROVED_RESPONSE_MODEL_SNAPSHOTS.get(
        scheduled_model,
        (),
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


def build_controlled_openai_transport_contract() -> Dict[str, Any]:
    contract = {
        "transport_version": TRANSPORT_VERSION,
        "contract_kind": "isolated_lazy_openai_controlled_transport",
        "candidate_provider_models": _candidate_provider_models(),
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
            "user_credential_storage_allowed": False,
            "global_client_allowed": False,
            "cached_client_allowed": False,
            "fresh_client_per_invocation": True,
            "max_retries": 0,
            "timeout_seconds": 30.0,
        },
        "request_contract": {
            "provider": "openai",
            "temperature": 0,
            "maximum_completion_tokens": 1024,
            "response_format": "strict_json_schema",
            "gpt_5_mini_zero_temperature": "omitted",
            "gpt_5_mini_zero_thinking_reasoning_effort": "minimal",
            "other_catalog_model_zero_temperature": "explicit",
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
            "qualification_decision_allowed": False,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
        },
    }
    validate_controlled_openai_transport_contract(contract)
    return deepcopy(contract)


def validate_controlled_openai_transport_contract(
    contract: Dict[str, Any],
) -> bool:
    _require(isinstance(contract, dict), "transport contract must be an object")
    _require(
        set(contract) == _CONTRACT_FIELDS,
        "transport contract fields must match the exact schema",
    )
    _require(
        contract.get("transport_version") == TRANSPORT_VERSION
        and contract.get("contract_kind")
        == "isolated_lazy_openai_controlled_transport",
        "transport identity mismatch",
    )
    _require(
        contract.get("candidate_provider_models")
        == _candidate_provider_models(),
        "transport candidates differ from the canonical catalog",
    )
    _require(
        contract.get("transport_result_fields")
        == sorted(TRANSPORT_RESULT_FIELDS),
        "transport result schema differs from the generic harness",
    )
    client = contract.get("client_contract")
    _require(
        isinstance(client, dict)
        and client.get("lazy_sdk_import") is True
        and client.get("explicit_api_key_required") is True
        and client.get("environment_read_allowed") is False
        and client.get("user_credential_storage_allowed") is False
        and client.get("global_client_allowed") is False
        and client.get("cached_client_allowed") is False
        and client.get("fresh_client_per_invocation") is True
        and client.get("max_retries") == 0
        and client.get("timeout_seconds") == 30.0,
        "client safety contract changed",
    )
    request = contract.get("request_contract")
    _require(
        isinstance(request, dict)
        and request.get("provider") == "openai"
        and request.get("temperature") == 0
        and request.get("maximum_completion_tokens") == 1024
        and request.get("response_format") == "strict_json_schema"
        and request.get("gpt_5_mini_zero_temperature") == "omitted"
        and request.get("gpt_5_mini_zero_thinking_reasoning_effort")
        == "minimal"
        and request.get("other_catalog_model_zero_temperature") == "explicit"
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
        and authority.get("qualification_decision_allowed") is False
        and authority.get("mutation_count") == 0
        and authority.get("application_action_count") == 0
        and authority.get("ats_action_count") == 0,
        "transport authority changed",
    )
    return True


def serialize_controlled_openai_transport_contract(
    contract: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_controlled_openai_transport_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_controlled_openai_transport_contract(payload)
    return _canonical_json(payload)


def controlled_openai_transport_sha256(
    contract: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_controlled_openai_transport_contract(contract).encode(
            "utf-8"
        )
    ).hexdigest()


def classify_sdk_exception(exc: BaseException) -> str:
    """Map SDK failures to the established controlled-evaluation vocabulary."""

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


def create_live_openai_client(
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
        from openai import OpenAI

        factory = OpenAI
    else:
        factory = getattr(sdk_module, "OpenAI", None)
        _require(callable(factory), "injected SDK OpenAI factory is required")
    try:
        return factory(
            api_key=api_key,
            max_retries=0,
            timeout=30.0,
        )
    except Exception as exc:
        _raise_bounded_sdk_failure(exc)


def _validate_packet_and_schedule(
    *,
    packet: Dict[str, Any],
    scheduled: Mapping[str, Any],
    plan: Dict[str, Any],
) -> None:
    validate_controlled_provider_benchmark_plan(plan)
    validate_transmittable_request_packet(packet, plan=plan)
    _require(scheduled.get("provider") == "openai", "provider must be OpenAI")
    _require(
        packet.get("provider") == "openai"
        and packet.get("model") == scheduled.get("model")
        and packet.get("case_alias") == scheduled.get("case_alias")
        and packet.get("workload_id") == scheduled.get("workload_id"),
        "provider/model/case must match the scheduled row",
    )
    _require(
        scheduled.get("model") in _qualification_openai_models(),
        "model is not a catalog-authorized OpenAI qualification candidate",
    )
    _require(
        any(
            row["case_alias"] == scheduled.get("case_alias")
            and row["workload_id"] == scheduled.get("workload_id")
            and row["provider"] == scheduled.get("provider")
            and row["model"] == scheduled.get("model")
            for row in plan["staged_matrix"]
        ),
        "scheduled row is outside the controlled plan",
    )
    _require(
        scheduled.get("fallback") is False
        and packet.get("fallback") is False,
        "fallback is prohibited",
    )
    _require(
        scheduled.get("harness_retry_limit") == 0
        and scheduled.get("provider_sdk_retry_limit", 0) == 0,
        "retries are prohibited",
    )
    _require(
        scheduled.get("timeout_seconds") == 30
        and packet.get("timeout_seconds") == 30,
        "timeout must be exactly 30 seconds",
    )
    _require(
        packet.get("live_execution_requested") is False,
        "live execution is prohibited by the controlled plan",
    )
    _require(packet.get("temperature") == 0, "temperature must be zero")
    maximum_completion_tokens = packet.get("maximum_completion_tokens")
    _require(
        isinstance(maximum_completion_tokens, int)
        and not isinstance(maximum_completion_tokens, bool)
        and 0 < maximum_completion_tokens <= 1024,
        "maximum completion tokens exceed the controlled bound",
    )
    _require(
        isinstance(packet.get("synthetic_input"), dict),
        "synthetic input must be a bounded object",
    )


def build_openai_chat_completion_arguments(
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
    _validate_packet_and_schedule(
        packet=packet,
        scheduled=scheduled,
        plan=controlled_plan,
    )
    schema = _expected_json_schema(packet)
    arguments = {
        "model": scheduled["model"],
        "messages": [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {
                "role": "user",
                "content": _canonical_json(packet["synthetic_input"]),
            },
        ],
        "max_completion_tokens": packet["maximum_completion_tokens"],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": _schema_name(packet["workload_id"]),
                "strict": True,
                "schema": schema,
            },
        },
    }
    if _is_gpt_5_mini(scheduled["model"]):
        arguments["reasoning_effort"] = "minimal"
    else:
        arguments["temperature"] = 0
    validate_openai_chat_completion_arguments(
        arguments,
        packet=packet,
        scheduled=scheduled,
        plan=controlled_plan,
    )
    return deepcopy(arguments)


def build_openai_production_parity_chat_completion_arguments(
    *,
    parity_request: Dict[str, Any],
    scheduled: Mapping[str, Any],
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Adapt a validated production-parity request without prompt ownership."""

    from src.evaluation.controlled_production_parity_benchmark import (
        validate_production_parity_request,
    )

    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    validate_production_parity_request(parity_request, plan=controlled_plan)
    _require(
        scheduled.get("provider") == parity_request.get("provider") == "openai"
        and scheduled.get("model") == parity_request.get("model")
        and scheduled.get("case_alias") == parity_request.get("case_alias")
        and scheduled.get("workload_id") == parity_request.get("workload_id"),
        "production-parity schedule binding mismatch",
    )
    _require(
        scheduled.get("fallback") is False
        and scheduled.get("harness_retry_limit") == 0
        and scheduled.get("provider_sdk_retry_limit") == 0
        and parity_request.get("fallback") is False
        and parity_request.get("retry_limit") == 0,
        "production-parity retries or fallback are prohibited",
    )
    arguments = {
        "model": scheduled["model"],
        "messages": deepcopy(parity_request["messages"]),
        "max_completion_tokens": parity_request["task_parameters"]["max_tokens"],
    }
    response_contract = parity_request["response_contract"]
    response_mode = response_contract["mode"]
    if response_mode == "structured_json":
        arguments["response_format"] = {
            "type": "json_schema",
            "json_schema": {
                "name": response_contract["schema_name"],
                "strict": True,
                "schema": deepcopy(response_contract["schema"]),
            },
        }
    elif response_mode == "json_object":
        arguments["response_format"] = {"type": "json_object"}
    else:
        _require(
            response_mode in {"json_text", "plain_text"},
            "unsupported production-parity OpenAI response mode",
        )
    if _is_gpt_5_mini(scheduled["model"]):
        arguments["reasoning_effort"] = "minimal"
    else:
        arguments["temperature"] = parity_request["task_parameters"]["temperature"]
    validate_openai_production_parity_chat_completion_arguments(
        arguments,
        parity_request=parity_request,
        scheduled=scheduled,
        plan=controlled_plan,
    )
    return deepcopy(arguments)


def validate_openai_production_parity_chat_completion_arguments(
    arguments: Dict[str, Any],
    *,
    parity_request: Dict[str, Any],
    scheduled: Mapping[str, Any],
    plan: Dict[str, Any] | None = None,
) -> bool:
    from src.evaluation.controlled_production_parity_benchmark import (
        validate_production_parity_request,
    )

    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    validate_production_parity_request(parity_request, plan=controlled_plan)
    response_contract = parity_request["response_contract"]
    response_mode = response_contract["mode"]
    _require(
        response_mode
        in {"structured_json", "json_object", "json_text", "plain_text"},
        "unsupported production-parity OpenAI response mode",
    )
    expected_fields = {"model", "messages", "max_completion_tokens"}
    if response_mode in {"structured_json", "json_object"}:
        expected_fields.add("response_format")
    if _is_gpt_5_mini(scheduled["model"]):
        expected_fields.add("reasoning_effort")
    else:
        expected_fields.add("temperature")
    _require(
        isinstance(arguments, dict) and set(arguments) == expected_fields,
        "production-parity OpenAI arguments differ from the allowlist",
    )
    _require(
        scheduled.get("provider") == "openai"
        and arguments.get("model") == scheduled.get("model")
        and parity_request.get("model") == scheduled.get("model"),
        "production-parity OpenAI model mismatch",
    )
    _require(
        arguments.get("messages") == parity_request.get("messages")
        and arguments.get("max_completion_tokens")
        == parity_request["task_parameters"]["max_tokens"],
        "production-parity OpenAI request semantics changed",
    )
    if _is_gpt_5_mini(scheduled["model"]):
        _require(
            "temperature" not in arguments
            and arguments.get("reasoning_effort") == "minimal",
            "production-parity GPT-5 Mini compatibility changed",
        )
    else:
        _require(
            arguments.get("temperature") == 0
            and "reasoning_effort" not in arguments,
            "production-parity OpenAI temperature compatibility changed",
        )
    if response_mode == "structured_json":
        _require(
            arguments.get("response_format")
            == {
                "type": "json_schema",
                "json_schema": {
                    "name": response_contract["schema_name"],
                    "strict": True,
                    "schema": response_contract["schema"],
                },
            },
            "production-parity OpenAI structured schema mismatch",
        )
    elif response_mode == "json_object":
        _require(
            arguments.get("response_format") == {"type": "json_object"},
            "production-parity OpenAI JSON object mode mismatch",
        )
        _require(
            response_contract.get("schema") is None
            and response_contract.get("schema_name") is None
            and response_contract.get("strict") is False,
            "JSON object mode must not transmit a provider schema",
        )
    else:
        _require(
            "response_format" not in arguments,
            "plain or JSON-text production task was forced into a schema",
        )
    _require(
        conservative_local_input_size_bytes(arguments)
        <= MAXIMUM_PRODUCTION_PARITY_LOCAL_INPUT_SIZE_BYTES,
        "production-parity OpenAI input-size bound exceeded",
    )
    return True


def conservative_local_input_size_bytes(arguments: Mapping[str, Any]) -> int:
    material = {
        key: arguments.get(key)
        for key in sorted(
            _BASE_CHAT_ARGUMENT_FIELDS | {"temperature", "reasoning_effort"}
        )
        if key in arguments
    }
    return len(_canonical_json(material).encode("utf-8"))


def validate_openai_chat_completion_arguments(
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
    _validate_packet_and_schedule(
        packet=packet,
        scheduled=scheduled,
        plan=controlled_plan,
    )
    expected_fields = set(_BASE_CHAT_ARGUMENT_FIELDS)
    if _is_gpt_5_mini(scheduled["model"]):
        expected_fields.add("reasoning_effort")
    else:
        expected_fields.add("temperature")
    _require(
        isinstance(arguments, dict) and set(arguments) == expected_fields,
        "chat request fields must match the exact compatibility allowlist",
    )
    _require(
        arguments.get("model") == scheduled.get("model"),
        "chat request provider/model mismatch",
    )
    if _is_gpt_5_mini(scheduled["model"]):
        _require(
            "temperature" not in arguments
            and arguments.get("reasoning_effort") == "minimal",
            "GPT-5 Mini zero-thinking compatibility changed",
        )
    else:
        _require(
            arguments.get("temperature") == 0
            and "reasoning_effort" not in arguments,
            "OpenAI temperature/reasoning compatibility changed",
        )
    _require(
        arguments.get("max_completion_tokens")
        == packet.get("maximum_completion_tokens")
        and 0 < arguments["max_completion_tokens"] <= 1024,
        "maximum completion tokens exceed the controlled bound",
    )
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
    expected_schema = _expected_json_schema(packet)
    _require(
        arguments.get("response_format")
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
        conservative_local_input_size_bytes(arguments)
        <= MAXIMUM_LOCAL_INPUT_SIZE_BYTES,
        "conservative local input-size bound exceeded",
    )
    return True


def _read_attr(value: Any, name: str) -> Any:
    if isinstance(value, dict):
        return value.get(name)
    return getattr(value, name, None)


def reduce_openai_sdk_response(
    response: Any,
    *,
    scheduled: Mapping[str, Any],
    packet: Dict[str, Any],
    latency_ms: float,
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
    if not _response_model_matches_scheduled(
        _read_attr(response, "model"),
        scheduled.get("model"),
    ):
        raise DefinitiveTransportFailure("provider_model_mismatch")
    message = _read_attr(choices[0], "message")
    content = _read_attr(message, "content")
    if not isinstance(content, str) or not content.strip():
        raise DefinitiveTransportFailure("malformed_empty_content")
    try:
        normalized_output = json.loads(content)
    except (TypeError, ValueError):
        raise DefinitiveTransportFailure("malformed_json_content") from None
    required = set(_expected_json_schema(packet)["required"])
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
            raise DefinitiveTransportFailure(
                f"{label}_usage_ceiling_exceeded"
            )
    result = {
        "normalized_output": normalized_output,
        "provider": "openai",
        "model": scheduled["model"],
        "latency_ms": float(latency_ms),
        "input_token_count": input_tokens,
        "output_token_count": output_tokens,
        "provider_outcome_category": "success",
    }
    validate_injected_transport_result(result, scheduled=scheduled)
    return deepcopy(result)


def execute_openai_chat_completion_once(
    *,
    api_key: str,
    packet: Dict[str, Any],
    scheduled: Mapping[str, Any],
    monotonic_clock: Callable[[], float],
    sdk_module: Any | None = None,
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Construct one fresh client, call once, and discard the raw envelope."""

    _require(callable(monotonic_clock), "monotonic clock is required")
    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    arguments = build_openai_chat_completion_arguments(
        packet=packet,
        scheduled=scheduled,
        plan=controlled_plan,
    )
    client = create_live_openai_client(
        api_key=api_key,
        sdk_module=sdk_module,
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
    return reduce_openai_sdk_response(
        response,
        scheduled=scheduled,
        packet=packet,
        latency_ms=latency_ms,
    )


def execute_openai_production_parity_chat_completion_once(
    *,
    api_key: str,
    parity_request: Dict[str, Any],
    scheduled: Mapping[str, Any],
    parity_response_consumer: Callable[[Any], Dict[str, Any]],
    monotonic_clock: Callable[[], float],
    sdk_module: Any | None = None,
    plan: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Execute one explicit OpenAI parity call and discard its raw envelope."""

    _require(callable(parity_response_consumer), "parity consumer is required")
    _require(callable(monotonic_clock), "monotonic clock is required")
    controlled_plan = (
        build_controlled_provider_benchmark_plan()
        if plan is None
        else deepcopy(plan)
    )
    arguments = build_openai_production_parity_chat_completion_arguments(
        parity_request=parity_request,
        scheduled=scheduled,
        plan=controlled_plan,
    )
    client = create_live_openai_client(api_key=api_key, sdk_module=sdk_module)
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
    choices = _read_attr(response, "choices")
    if not isinstance(choices, (list, tuple)) or len(choices) != 1:
        raise DefinitiveTransportFailure("malformed_choice_count")
    if not _response_model_matches_scheduled(
        _read_attr(response, "model"),
        scheduled.get("model"),
    ):
        raise DefinitiveTransportFailure("provider_model_mismatch")
    content = _read_attr(_read_attr(choices[0], "message"), "content")
    if not isinstance(content, str) or not content.strip():
        raise DefinitiveTransportFailure("malformed_empty_content")
    usage = _read_attr(response, "usage")
    input_tokens = _read_attr(usage, "prompt_tokens")
    output_tokens = _read_attr(usage, "completion_tokens")
    for value, label, ceiling in (
        (input_tokens, "input", 4096),
        (output_tokens, "output", 1024),
    ):
        if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
            raise DefinitiveTransportFailure(f"missing_{label}_usage")
        if value > ceiling:
            raise DefinitiveTransportFailure(f"{label}_usage_ceiling_exceeded")
    parity_result = parity_response_consumer(content)
    _require(isinstance(parity_result, dict), "parity result is invalid")
    return {
        "parity_result": deepcopy(parity_result),
        "provider": "openai",
        "model": scheduled["model"],
        "latency_ms": float(latency_ms),
        "input_token_count": input_tokens,
        "output_token_count": output_tokens,
        "provider_outcome_category": "success",
    }
