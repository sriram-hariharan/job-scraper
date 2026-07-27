"""Offline-first transport adapter for the one-call Groq run 003."""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import json
import math
import re
from typing import Any, Callable, Dict, Iterable, Mapping

from src.evaluation.controlled_groq_canary_run_003_identity import (
    RUN_003_IDENTITY_VERSION,
    build_run_003_identity_contract,
    run_003_identity_sha256,
    validate_run_003_identity_contract,
)
from src.evaluation.controlled_groq_canary_run_003_plan import (
    RUN_003_PLAN_VERSION,
    build_run_003_plan_contract,
    build_run_003_transmittable_request_packet,
    run_003_plan_sha256,
    validate_run_003_plan_contract,
    validate_run_003_transmittable_request_packet,
)
from src.evaluation.controlled_groq_canary_transport import (
    SYSTEM_MESSAGE,
    UnknownProviderOutcome,
    classify_sdk_exception,
    create_live_groq_client,
    reduce_groq_sdk_response,
)
from src.evaluation.controlled_provider_benchmark_harness import (
    AmbiguousTransportTimeout,
    DefinitiveTransportFailure,
    TRANSPORT_RESULT_FIELDS,
)


RUN_003_TRANSPORT_VERSION = "controlled-groq-canary-run-003-transport-v1"
LOCAL_INPUT_SIZE_UNIT = "canonical_utf8_bytes"
MAXIMUM_LOCAL_INPUT_SIZE_BYTES = 4096

_PINNED_PLAN_SHA256 = (
    "5d63ef8bc8749645c19211184e8b7be16aa1909fbdb8a3682b9073af7270e9e8"
)
_PINNED_IDENTITY_SHA256 = (
    "db22f2add4075775747f3c90de89977f82f918adc655eda1f343ab5aeed44980"
)
_PINNED_SCHEDULE_KEY = (
    "canary_run_003_"
    "0ba1bf8c9270b5bbe777b6a27c05342cb906ab2e0e25609714a81dde9cf4fb46"
)
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
    "run_003_transport_version",
    "contract_kind",
    "run_003_plan_version",
    "run_003_plan_sha256",
    "run_003_identity_version",
    "run_003_identity_sha256",
    "schedule",
    "target",
    "request_contract",
    "transport_result_fields",
    "response_contract",
    "error_contract",
    "authority_invariants",
}
_PROHIBITED_ARGUMENT_KEYS = {
    "api_key",
    "application_state",
    "ats_state",
    "browser",
    "case_alias",
    "code_interpreter",
    "credential",
    "expected_output",
    "fallback",
    "golden_output",
    "grader",
    "header",
    "headers",
    "mcp",
    "metadata",
    "prompt",
    "production_state",
    "reasoning",
    "request_id",
    "retry",
    "schedule_key",
    "secret",
    "tool",
    "tools",
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


def _contains_prohibited_argument_key(value: Any) -> bool:
    return any(key in _PROHIBITED_ARGUMENT_KEYS for key in _iter_keys(value))


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
        "run-003 packet output schema is invalid",
    )
    required = source.get("required_fields")
    _require(
        isinstance(required, list)
        and bool(required)
        and all(isinstance(field, str) and field.strip() for field in required)
        and len(required) == len(set(required)),
        "run-003 required fields are invalid",
    )
    return {
        "type": "object",
        "properties": {field: {} for field in required},
        "required": list(required),
        "additionalProperties": False,
    }


def _validated_owners() -> tuple[Dict[str, Any], Dict[str, Any]]:
    plan = build_run_003_plan_contract()
    identity = build_run_003_identity_contract()
    validate_run_003_plan_contract(plan)
    validate_run_003_identity_contract(identity)
    _require(
        run_003_plan_sha256(plan) == _PINNED_PLAN_SHA256,
        "run-003 plan digest changed",
    )
    _require(
        run_003_identity_sha256(identity) == _PINNED_IDENTITY_SHA256,
        "run-003 identity digest changed",
    )
    _require(
        identity["schedule"] == plan["schedule"]
        and len(plan["schedule"]) == 1
        and plan["schedule"][0]["schedule_key"] == _PINNED_SCHEDULE_KEY,
        "run-003 schedule ownership changed",
    )
    return deepcopy(plan), deepcopy(identity)


def conservative_run_003_local_input_size_bytes(
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


def build_run_003_groq_chat_completion_arguments(
    *,
    packet: Dict[str, Any],
    scheduled: Mapping[str, Any],
) -> Dict[str, Any]:
    plan, _identity = _validated_owners()
    validate_run_003_transmittable_request_packet(packet)
    _require(
        isinstance(scheduled, Mapping)
        and dict(scheduled) == plan["schedule"][0],
        "scheduled row must equal the exact run-003 plan row",
    )
    _require(
        packet == build_run_003_transmittable_request_packet(),
        "packet must equal the exact run-003 packet",
    )
    _require(
        packet["provider"] == "groq"
        and scheduled["provider"] == "groq"
        and packet["model"] == "openai/gpt-oss-120b"
        and scheduled["model"] == "openai/gpt-oss-120b",
        "run-003 provider/model mismatch",
    )
    _require(
        packet["fallback"] is False
        and scheduled["fallback"] is False
        and scheduled["harness_retry_limit"] == 0
        and scheduled["provider_sdk_retry_limit"] == 0,
        "run-003 fallback and retries are prohibited",
    )
    _require(
        packet["live_execution_requested"] is False,
        "run-003 packet must remain default off",
    )
    maximum_tokens = packet["maximum_completion_tokens"]
    _require(
        isinstance(maximum_tokens, int)
        and not isinstance(maximum_tokens, bool)
        and 0 < maximum_tokens <= 1024,
        "run-003 completion token bound is invalid",
    )
    arguments = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {
                "role": "user",
                "content": _canonical_json(packet["synthetic_input"]),
            },
        ],
        "temperature": 0,
        "max_completion_tokens": maximum_tokens,
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": _schema_name(packet["workload_id"]),
                "strict": True,
                "schema": _expected_json_schema(packet),
            },
        },
        "stream": False,
        "n": 1,
    }
    validate_run_003_groq_chat_completion_arguments(
        arguments,
        packet=packet,
        scheduled=scheduled,
    )
    return deepcopy(arguments)


def validate_run_003_groq_chat_completion_arguments(
    arguments: Dict[str, Any],
    *,
    packet: Dict[str, Any],
    scheduled: Mapping[str, Any],
) -> bool:
    plan, _identity = _validated_owners()
    validate_run_003_transmittable_request_packet(packet)
    _require(
        isinstance(scheduled, Mapping)
        and dict(scheduled) == plan["schedule"][0],
        "scheduled row must equal the exact run-003 plan row",
    )
    _require(
        packet == build_run_003_transmittable_request_packet(),
        "packet must equal the exact run-003 packet",
    )
    _require(
        isinstance(arguments, dict)
        and set(arguments) == _CHAT_ARGUMENT_FIELDS,
        "run-003 chat fields must match the exact allowlist",
    )
    expected = {
        "model": "openai/gpt-oss-120b",
        "messages": [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {
                "role": "user",
                "content": _canonical_json(packet["synthetic_input"]),
            },
        ],
        "temperature": 0,
        "max_completion_tokens": packet["maximum_completion_tokens"],
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": _schema_name(packet["workload_id"]),
                "strict": True,
                "schema": _expected_json_schema(packet),
            },
        },
        "stream": False,
        "n": 1,
    }
    _require(arguments == expected, "run-003 chat arguments changed")
    _require(
        arguments["max_completion_tokens"] <= 1024,
        "run-003 completion token ceiling exceeded",
    )
    _require(
        not _contains_prohibited_argument_key(arguments),
        "run-003 chat arguments contain a prohibited field",
    )
    _require(
        conservative_run_003_local_input_size_bytes(arguments)
        <= MAXIMUM_LOCAL_INPUT_SIZE_BYTES,
        "run-003 canonical local request size exceeded",
    )
    return True


def _raise_bounded_failure(exc: BaseException) -> None:
    category = classify_sdk_exception(exc)
    if category == "ambiguous_timeout":
        raise AmbiguousTransportTimeout("ambiguous_timeout") from None
    if category.startswith("definitive_"):
        raise DefinitiveTransportFailure(category) from None
    raise UnknownProviderOutcome("unknown_provider_outcome") from None


def execute_run_003_groq_chat_completion_once(
    *,
    client: Any,
    packet: Dict[str, Any],
    scheduled: Mapping[str, Any],
    monotonic_clock: Callable[[], float],
) -> Dict[str, Any]:
    """Execute exactly one injected-client call and discard the raw envelope."""

    _require(client is not None, "one caller-supplied client is required")
    _require(callable(monotonic_clock), "caller-supplied clock is required")
    arguments = build_run_003_groq_chat_completion_arguments(
        packet=packet,
        scheduled=scheduled,
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
    _require(
        math.isfinite(latency_ms) and latency_ms >= 0,
        "measured latency is invalid",
    )
    return reduce_groq_sdk_response(
        response,
        scheduled=scheduled,
        packet=packet,
        latency_ms=latency_ms,
    )


def _expected_transport_contract() -> Dict[str, Any]:
    plan, identity = _validated_owners()
    return {
        "run_003_transport_version": RUN_003_TRANSPORT_VERSION,
        "contract_kind": (
            "offline-injected-one-call-groq-run-003-transport"
        ),
        "run_003_plan_version": RUN_003_PLAN_VERSION,
        "run_003_plan_sha256": _PINNED_PLAN_SHA256,
        "run_003_identity_version": RUN_003_IDENTITY_VERSION,
        "run_003_identity_sha256": _PINNED_IDENTITY_SHA256,
        "schedule": deepcopy(plan["schedule"]),
        "target": {
            "case_alias": plan["target_case_alias"],
            "workload_id": plan["target_workload"],
            "provider": plan["target_provider"],
            "model": plan["target_model"],
        },
        "request_contract": {
            "maximum_provider_calls": 1,
            "timeout_seconds": 30,
            "temperature": 0,
            "maximum_completion_tokens": 1024,
            "maximum_input_tokens": 4096,
            "stream": False,
            "n": 1,
            "message_roles": ["system", "user"],
            "response_format": "strict_json_schema",
            "local_input_size_unit": LOCAL_INPUT_SIZE_UNIT,
            "maximum_local_input_size": MAXIMUM_LOCAL_INPUT_SIZE_BYTES,
            "fallback": False,
            "retry_count": 0,
        },
        "transport_result_fields": sorted(TRANSPORT_RESULT_FIELDS),
        "response_contract": {
            "bounded_reducer_reused": True,
            "raw_response_retained": False,
            "request_identifier_retained": False,
            "headers_retained": False,
            "reasoning_retained": False,
        },
        "error_contract": {
            "definitive_failure": "bounded_terminal_failure",
            "ambiguous_timeout": "bounded_terminal_ambiguous",
            "unknown_outcome": "bounded_terminal_unknown",
            "retry_count": 0,
            "fallback": False,
        },
        "authority_invariants": {
            "live_execution_authorized": False,
            "provider_calls_allowed": False,
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


def build_run_003_transport_contract() -> Dict[str, Any]:
    contract = _expected_transport_contract()
    validate_run_003_transport_contract(contract)
    return deepcopy(contract)


def validate_run_003_transport_contract(contract: Dict[str, Any]) -> bool:
    _require(
        isinstance(contract, dict) and set(contract) == _CONTRACT_FIELDS,
        "run-003 transport fields must match the exact schema",
    )
    _require(
        contract == _expected_transport_contract(),
        "run-003 transport contract changed or gained authority",
    )
    return True


def serialize_run_003_transport_contract(
    contract: Dict[str, Any] | None = None,
) -> str:
    payload = (
        build_run_003_transport_contract()
        if contract is None
        else deepcopy(contract)
    )
    validate_run_003_transport_contract(payload)
    return _canonical_json(payload)


def run_003_transport_sha256(
    contract: Dict[str, Any] | None = None,
) -> str:
    return sha256(
        serialize_run_003_transport_contract(contract).encode("utf-8")
    ).hexdigest()


__all__ = [
    "AmbiguousTransportTimeout",
    "DefinitiveTransportFailure",
    "UnknownProviderOutcome",
    "RUN_003_TRANSPORT_VERSION",
    "build_run_003_groq_chat_completion_arguments",
    "validate_run_003_groq_chat_completion_arguments",
    "execute_run_003_groq_chat_completion_once",
    "build_run_003_transport_contract",
    "validate_run_003_transport_contract",
    "serialize_run_003_transport_contract",
    "run_003_transport_sha256",
    "create_live_groq_client",
]
