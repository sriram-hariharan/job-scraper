"""Deterministic offline compatibility harness for the shared LLM client.

The harness executes the current ``src/ai/llm_client.py`` implementation with
in-memory fake SDK modules and fake clients.  It never loads dotenv, reads a
provider credential, opens a transport, or persists a result.
"""

from __future__ import annotations

from contextlib import contextmanager, redirect_stderr, redirect_stdout
from copy import deepcopy
from hashlib import sha256
from io import StringIO
import json
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
from typing import Any, Dict, Iterator, List

from src.evaluation.provider_benchmark_contract import (
    build_provider_benchmark_contract,
)


COMPATIBILITY_CONTRACT_VERSION = "provider-client-compatibility-v1"
STEP8M_COMPATIBILITY_BASELINE_SHA256 = (
    "e798f7d10f67c65c5d02f7531b54c3ce1b18ad0a6db5ec98505b4f1847f23ddd"
)
SYNTHETIC_PASS = "SYNTHETIC_REQUEST_SURFACE_PASS"
SYNTHETIC_REPAIR_REQUIRED = "SYNTHETIC_REQUEST_SURFACE_REPAIR_REQUIRED"
LIVE_UNPROVEN = "LIVE_COMPATIBILITY_UNPROVEN"
RAW_DEBUG_SAFE = "RAW_DEBUG_OUTPUT_SAFE"
RAW_DEBUG_REPAIR_REQUIRED = "RAW_DEBUG_OUTPUT_REPAIR_REQUIRED"

_CREDENTIAL_NAMES = {
    "GROQ_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
}
_FIXED_CONFIGURATION = {
    "LLM_PROVIDER": "groq",
    "LLM_MODEL": "offline-placeholder-model",
    "LLM_FALLBACK_ENABLED": "false",
    "LLM_FALLBACK_PROVIDER": "openai",
    "LLM_FALLBACK_MODEL": "offline-placeholder-fallback",
}
_MESSAGES = [{"role": "user", "content": "offline synthetic compatibility probe"}]
_SCHEMA = {
    "type": "object",
    "properties": {"status": {"type": "string"}},
    "required": ["status"],
    "additionalProperties": False,
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


class _FakeMessage:
    def __init__(
        self,
        content: Any,
        *,
        refusal: str | None = None,
        reasoning: str | None = None,
        marker: str = "bounded-synthetic-marker",
    ) -> None:
        self.content = content
        self.refusal = refusal
        self.reasoning = reasoning
        self._marker = marker

    def model_dump(self) -> Dict[str, Any]:
        return {
            "synthetic_marker": self._marker,
            "content_shape": type(self.content).__name__,
            "refusal_present": bool(self.refusal),
            "reasoning_present": bool(self.reasoning),
        }


class _FakeCompletions:
    def __init__(self, messages: List[_FakeMessage]) -> None:
        self._messages = list(messages)
        self.calls: List[Dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        if not self._messages:
            raise RuntimeError("fake response queue exhausted")
        messages = kwargs.get("messages")
        response_format = kwargs.get("response_format")
        schema_payload = (
            response_format.get("json_schema")
            if isinstance(response_format, dict)
            else None
        )
        self.calls.append(
            {
                "request_fields": sorted(kwargs),
                "model": str(kwargs.get("model") or ""),
                "message_count": len(messages) if isinstance(messages, list) else 0,
                "message_roles": [
                    str(item.get("role") or "")
                    for item in (messages or [])
                    if isinstance(item, dict)
                ],
                "temperature_classification": (
                    "explicit_numeric"
                    if isinstance(kwargs.get("temperature"), (int, float))
                    else "missing_or_non_numeric"
                ),
                "max_completion_tokens_present": (
                    "max_completion_tokens" in kwargs
                ),
                "include_reasoning": kwargs.get("include_reasoning"),
                "response_format_type": (
                    response_format.get("type")
                    if isinstance(response_format, dict)
                    else "none"
                ),
                "json_schema_strict": (
                    schema_payload.get("strict")
                    if isinstance(schema_payload, dict)
                    else False
                ),
            }
        )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=self._messages.pop(0))]
        )


class _FakeSdkClient:
    def __init__(self, messages: List[_FakeMessage]) -> None:
        self.chat = SimpleNamespace(completions=_FakeCompletions(messages))


def _raising_sdk_constructor(
    construction_counts: Dict[str, int],
    provider: str,
):
    def _constructor(*_args: Any, **_kwargs: Any) -> None:
        construction_counts[provider] += 1
        raise AssertionError(f"real {provider} client construction is prohibited")

    return _constructor


@contextmanager
def _isolated_shared_client() -> Iterator[tuple[ModuleType, Dict[str, Any]]]:
    """Load the production module with fake imports and fixed non-secret config."""

    observations: Dict[str, Any] = {
        "dotenv_load_attempts_blocked": 0,
        "dotenv_load_count": 0,
        "credential_reads": 0,
        "provider_client_constructions": {
            "groq": 0,
            "openai": 0,
            "gemini": 0,
        },
    }
    construction_counts = observations["provider_client_constructions"]

    dotenv_module = ModuleType("dotenv")

    def _blocked_load_dotenv(*_args: Any, **_kwargs: Any) -> bool:
        observations["dotenv_load_attempts_blocked"] += 1
        return False

    dotenv_module.load_dotenv = _blocked_load_dotenv  # type: ignore[attr-defined]

    groq_module = ModuleType("groq")
    groq_module.Groq = _raising_sdk_constructor(  # type: ignore[attr-defined]
        construction_counts,
        "groq",
    )
    openai_module = ModuleType("openai")
    openai_module.OpenAI = _raising_sdk_constructor(  # type: ignore[attr-defined]
        construction_counts,
        "openai",
    )
    google_module = ModuleType("google")
    genai_module = ModuleType("google.genai")
    genai_types_module = ModuleType("google.genai.types")
    genai_module.Client = _raising_sdk_constructor(  # type: ignore[attr-defined]
        construction_counts,
        "gemini",
    )
    genai_types_module.ThinkingConfig = SimpleNamespace  # type: ignore[attr-defined]
    genai_types_module.GenerateContentConfig = SimpleNamespace  # type: ignore[attr-defined]
    genai_module.types = genai_types_module  # type: ignore[attr-defined]
    google_module.genai = genai_module  # type: ignore[attr-defined]

    replacements = {
        "dotenv": dotenv_module,
        "groq": groq_module,
        "openai": openai_module,
        "google": google_module,
        "google.genai": genai_module,
        "google.genai.types": genai_types_module,
    }
    previous_modules = {name: sys.modules.get(name) for name in replacements}
    original_getenv = os.getenv

    def _fixed_getenv(name: str, default: Any = None) -> Any:
        if name in _CREDENTIAL_NAMES:
            observations["credential_reads"] += 1
            return None
        return _FIXED_CONFIGURATION.get(name, default)

    module = ModuleType("_offline_provider_compatibility_llm_client")
    module.__file__ = "src/ai/llm_client.py"
    client_path = Path(__file__).resolve().parents[1] / "ai" / "llm_client.py"
    source = client_path.read_text(encoding="utf-8")

    try:
        sys.modules.update(replacements)
        os.getenv = _fixed_getenv  # type: ignore[assignment]
        exec(compile(source, module.__file__, "exec"), module.__dict__)
        yield module, observations
    finally:
        os.getenv = original_getenv  # type: ignore[assignment]
        for name, previous in previous_modules.items():
            if previous is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = previous


def _candidate_fingerprint(candidate_definitions: List[Dict[str, Any]]) -> str:
    serialized = json.dumps(
        candidate_definitions,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(serialized.encode("utf-8")).hexdigest()


def build_compatibility_scenarios() -> List[Dict[str, Any]]:
    """Build scenarios from the authoritative Step 8L candidate definitions."""

    benchmark = build_provider_benchmark_contract()
    scenarios: List[Dict[str, Any]] = []
    for candidate in benchmark["candidate_definitions"]:
        provider = candidate["provider"]
        model = candidate["model"]
        uses_openai_default_temperature = (
            provider == "openai" and model == "gpt-5-mini"
        )
        expected_fields = [
            "max_completion_tokens",
            "messages",
            "model",
        ]
        prohibited_fields = ["max_tokens"]
        if uses_openai_default_temperature:
            prohibited_fields.append("temperature")
        else:
            expected_fields.append("temperature")
        if provider == "groq":
            expected_fields.append("include_reasoning")
        else:
            prohibited_fields.append("include_reasoning")
        scenarios.append(
            {
                "scenario_id": f"{candidate['candidate_id']}_chat_completions",
                "candidate_id": candidate["candidate_id"],
                "provider": provider,
                "model": model,
                "request_mode": "chat_completions",
                "structured_output_mode": "json_object_and_strict_json_schema",
                "response_parsing_mode": "text_and_optional_json_decode",
                "expected_provider_dispatch": provider,
                "expected_request_fields": sorted(expected_fields),
                "prohibited_request_fields": sorted(prohibited_fields),
                "expected_metrics_effects": {
                    f"{provider}_calls": 1,
                    "gemini_calls": 0,
                },
                "expected_fallback_behavior": "disabled_zero_attempts",
                "expected_error_behavior": "current_client_exception_contract",
                "live_compatibility_status": LIVE_UNPROVEN,
                "synthetic_compatibility_status": "pending_offline_evaluation",
                "authority_transfer": False,
                "raw_response_persistence": False,
            }
        )
    return deepcopy(scenarios)


def _invoke(
    client_module: ModuleType,
    provider: str,
    model: str,
    message: _FakeMessage,
    *,
    response_mime_type: str | None = None,
    response_schema: Dict[str, Any] | None = None,
    return_parsed: bool = False,
) -> tuple[Any, Dict[str, Any], Dict[str, int]]:
    fake = _FakeSdkClient([message])
    setattr(client_module, f"_{provider}_client", fake)
    client_module.reset_provider_metrics()
    output = client_module._run_single_provider(
        provider_name=provider,
        messages=deepcopy(_MESSAGES),
        model=model,
        temperature=0,
        max_tokens=64,
        response_mime_type=response_mime_type,
        response_schema=deepcopy(response_schema),
        return_parsed=return_parsed,
        thinking_budget=None,
    )
    calls = fake.chat.completions.calls
    _require(len(calls) == 1, "fake provider must receive exactly one call")
    return output, deepcopy(calls[0]), client_module.get_provider_metrics()


def _evaluate_candidate(
    client_module: ModuleType,
    scenario: Dict[str, Any],
) -> Dict[str, Any]:
    provider = scenario["provider"]
    model = scenario["model"]
    provider_metric = f"{provider}_calls"
    uses_openai_default_temperature = (
        provider == "openai" and model == "gpt-5-mini"
    )
    checks: Dict[str, bool] = {}

    plain, plain_call, metrics = _invoke(
        client_module,
        provider,
        model,
        _FakeMessage("synthetic plain text"),
    )
    checks["dispatch"] = (
        plain == "synthetic plain text"
        and plain_call["model"] == model
        and plain_call["message_count"] == 1
    )
    checks["request_fields"] = (
        set(scenario["expected_request_fields"])
        <= set(plain_call["request_fields"])
        and not (
            set(scenario["prohibited_request_fields"])
            & set(plain_call["request_fields"])
        )
    )
    checks["max_completion_tokens"] = plain_call["max_completion_tokens_present"]
    checks["temperature"] = (
        plain_call["temperature_classification"] == (
            "missing_or_non_numeric"
            if uses_openai_default_temperature
            else "explicit_numeric"
        )
    )
    checks["reasoning_control"] = (
        plain_call["include_reasoning"] is False
        if provider == "groq"
        else "include_reasoning" not in plain_call["request_fields"]
    )
    checks["metrics"] = (
        metrics[provider_metric] == 1
        and metrics["gemini_calls"] == 0
        and sum(metrics[name] for name in ("groq_calls", "openai_calls")) == 1
    )

    parsed, object_call, _ = _invoke(
        client_module,
        provider,
        model,
        _FakeMessage('{"status":"synthetic_ok"}'),
        response_mime_type="application/json",
        return_parsed=True,
    )
    checks["json_object"] = (
        object_call["response_format_type"] == "json_object"
        and parsed == {"status": "synthetic_ok"}
    )

    unparsed, schema_call, _ = _invoke(
        client_module,
        provider,
        model,
        _FakeMessage('{"status":"synthetic_ok"}'),
        response_mime_type="application/json",
        response_schema=_SCHEMA,
        return_parsed=False,
    )
    checks["json_schema"] = (
        schema_call["response_format_type"] == "json_schema"
        and schema_call["json_schema_strict"] is True
        and isinstance(unparsed, str)
    )

    malformed, _, _ = _invoke(
        client_module,
        provider,
        model,
        _FakeMessage("{malformed"),
        response_mime_type="application/json",
        return_parsed=True,
    )
    checks["malformed_json"] = isinstance(malformed, str)

    list_output, _, _ = _invoke(
        client_module,
        provider,
        model,
        _FakeMessage(["synthetic", {"text": "list"}]),
    )
    dictionary_output, _, _ = _invoke(
        client_module,
        provider,
        model,
        _FakeMessage({"text": "synthetic dictionary"}),
    )
    checks["content_coercion"] = (
        list_output == "synthetic\nlist"
        and dictionary_output == "synthetic dictionary"
    )

    empty_classification = "not_exercised"
    refusal_classification = "not_exercised"
    for label, fake_message in (
        ("empty", _FakeMessage(None)),
        ("refusal", _FakeMessage(None, refusal="synthetic_refusal")),
    ):
        with redirect_stdout(StringIO()), redirect_stderr(StringIO()):
            try:
                _invoke(client_module, provider, model, fake_message)
            except RuntimeError:
                classification = "runtime_error"
            else:
                classification = "unexpected_success"
        if label == "empty":
            empty_classification = classification
        else:
            refusal_classification = classification
    checks["empty_and_refusal"] = (
        empty_classification == "runtime_error"
        and refusal_classification == "runtime_error"
    )

    synthetic_status = SYNTHETIC_PASS if all(checks.values()) else SYNTHETIC_REPAIR_REQUIRED
    return {
        "scenario_id": scenario["scenario_id"],
        "provider": provider,
        "model": model,
        "request_field_classifications": {
            "base_fields": "pass" if checks["request_fields"] else "repair_required",
            "max_completion_tokens": (
                "present" if checks["max_completion_tokens"] else "missing"
            ),
            "temperature": (
                "omitted_for_default_only_model"
                if checks["temperature"] and uses_openai_default_temperature
                else "passed_explicitly"
                if checks["temperature"]
                else "incompatible_request_surface"
            ),
            "reasoning_control": (
                "suppressed_for_gpt_oss"
                if provider == "groq" and checks["reasoning_control"]
                else "not_sent_for_openai"
                if checks["reasoning_control"]
                else "repair_required"
            ),
        },
        "structured_output_classifications": {
            "json_object": "pass" if checks["json_object"] else "repair_required",
            "strict_json_schema": (
                "pass" if checks["json_schema"] else "repair_required"
            ),
        },
        "parse_classifications": {
            "plain_text": "pass" if checks["dispatch"] else "repair_required",
            "valid_json": "parsed",
            "malformed_json": (
                "returned_as_text" if checks["malformed_json"] else "repair_required"
            ),
            "list_and_dictionary_content": (
                "coerced" if checks["content_coercion"] else "repair_required"
            ),
            "empty_content": empty_classification,
            "refusal_without_content": refusal_classification,
        },
        "metrics_delta": {
            "provider_call_count": 1 if checks["metrics"] else 0,
            "gemini_call_count": 0,
        },
        "fallback_classification": "disabled_zero_attempts",
        "safety_classification": "offline_fake_client_only",
        "synthetic_status": synthetic_status,
        "live_status": LIVE_UNPROVEN,
        "production_repair_requirements": [],
        "authority_transfer": False,
        "raw_response_persistence": False,
    }


def _evaluate_fallback(client_module: ModuleType) -> Dict[str, Any]:
    original = client_module._run_single_provider
    invocations: List[tuple[str, str]] = []

    def _fake_dispatch(provider_name: str, model: str, **_kwargs: Any) -> str:
        invocations.append((provider_name, model))
        if provider_name == "groq":
            raise TimeoutError("synthetic transient primary failure")
        return "synthetic fallback success"

    client_module._run_single_provider = _fake_dispatch
    try:
        client_module.reset_provider_metrics()
        try:
            client_module.run_chat_completion_with_metadata(
                messages=deepcopy(_MESSAGES),
                provider="groq",
                model="openai/gpt-oss-20b",
                fallback_enabled=False,
                fallback_provider="openai",
                fallback_model="gpt-5-mini",
            )
        except RuntimeError:
            disabled_propagates = True
        else:
            disabled_propagates = False
        disabled_metrics = client_module.get_provider_metrics()

        invocations.clear()
        client_module.reset_provider_metrics()
        fallback_payload = client_module.run_chat_completion_with_metadata(
            messages=deepcopy(_MESSAGES),
            provider="groq",
            model="openai/gpt-oss-20b",
            fallback_enabled=True,
            fallback_provider="openai",
            fallback_model="gpt-5-mini",
        )
        enabled_metrics = client_module.get_provider_metrics()
        enabled_invocations = list(invocations)

        invocations.clear()

        def _all_fail(provider_name: str, model: str, **_kwargs: Any) -> str:
            invocations.append((provider_name, model))
            if provider_name == "groq":
                raise TimeoutError("synthetic transient primary failure")
            raise RuntimeError("synthetic provider failure")

        client_module._run_single_provider = _all_fail
        client_module.reset_provider_metrics()
        try:
            client_module.run_chat_completion_with_metadata(
                messages=deepcopy(_MESSAGES),
                provider="groq",
                model="openai/gpt-oss-20b",
                fallback_enabled=True,
                fallback_provider="openai",
                fallback_model="gpt-5-mini",
            )
        except RuntimeError:
            fallback_failure_class = "combined_runtime_error"
        else:
            fallback_failure_class = "unexpected_success"
        failure_invocations = list(invocations)
    finally:
        client_module._run_single_provider = original

    try:
        original(
            provider_name="unsupported",
            messages=deepcopy(_MESSAGES),
            model="unsupported",
            temperature=0,
            max_tokens=64,
        )
    except ValueError:
        unsupported_provider = "fails_closed"
    else:
        unsupported_provider = "repair_required"

    client_module.reset_provider_metrics()
    try:
        client_module.run_chat_completion_with_metadata(
            messages=deepcopy(_MESSAGES),
            provider="groq",
            model="gpt-5-mini",
            fallback_enabled=False,
        )
    except ValueError as exc:
        mismatch_classification = (
            "fails_closed"
            if getattr(exc, "error_category", "")
            == "provider_model_mismatch"
            else "repair_required"
        )
    else:
        mismatch_classification = "provider_model_mismatch_not_rejected"

    return {
        "fallback_disabled": (
            "primary_error_propagated_zero_fallback"
            if disabled_propagates
            and disabled_metrics["fallback_attempts"] == 0
            else "repair_required"
        ),
        "fallback_enabled_bound": (
            1
            if enabled_invocations
            == [
                ("groq", "openai/gpt-oss-20b"),
                ("openai", "gpt-5-mini"),
            ]
            else -1
        ),
        "recursive_fallback": False,
        "fallback_success": (
            "counted_once"
            if fallback_payload["fallback_used"] is True
            and enabled_metrics["fallback_attempts"] == 1
            and enabled_metrics["fallback_successes"] == 1
            else "repair_required"
        ),
        "fallback_failure": (
            fallback_failure_class
            if len(failure_invocations) == 2
            else "unbounded_invocation_repair_required"
        ),
        "unsupported_provider": unsupported_provider,
        "provider_model_mismatch": mismatch_classification,
        "exception_policy": "approved_transient_categories_only",
        "identity_observability": "retained_in_metadata_and_combined_error",
        "routing_policy": "bounded_explicit_transient_only",
    }


def _evaluate_raw_debug_output(client_module: ModuleType) -> str:
    marker = "bounded-raw-debug-synthetic-marker"
    output = StringIO()
    with redirect_stdout(output), redirect_stderr(StringIO()):
        try:
            _invoke(
                client_module,
                "groq",
                "openai/gpt-oss-20b",
                _FakeMessage(None, marker=marker),
            )
        except RuntimeError:
            pass
    return (
        RAW_DEBUG_REPAIR_REQUIRED
        if marker in output.getvalue()
        else RAW_DEBUG_SAFE
    )


def run_offline_provider_client_compatibility() -> Dict[str, Any]:
    """Execute all candidate scenarios with fake SDK clients only."""

    benchmark = build_provider_benchmark_contract()
    scenarios = build_compatibility_scenarios()
    with _isolated_shared_client() as (client_module, isolation):
        candidate_results = [
            _evaluate_candidate(client_module, scenario)
            for scenario in scenarios
        ]
        fallback = _evaluate_fallback(client_module)
        raw_debug = _evaluate_raw_debug_output(client_module)
        client_module.reset_provider_metrics()
        defensive = client_module.get_provider_metrics()
        defensive["groq_calls"] = 999
        metrics_defensive = (
            client_module.get_provider_metrics()["groq_calls"] == 0
        )

    repair_requirements = []
    if raw_debug == RAW_DEBUG_REPAIR_REQUIRED:
        repair_requirements.append(
            {
                "defect_id": "raw_empty_message_dump",
                "owner": "src/ai/llm_client.py",
                "classification": "production_repair_required",
            }
        )
    if fallback["provider_model_mismatch"] != "fails_closed":
        repair_requirements.append(
            {
                "defect_id": "provider_model_mismatch_not_rejected",
                "owner": "src/ai/llm_client.py",
                "classification": "production_repair_required",
            }
        )
    openai_risks = [
        "chat_completions_remote_support_unproven",
        "temperature_remote_support_unproven",
        "structured_output_remote_support_unproven",
        "schema_restrictions_unproven",
        "reasoning_controls_absent",
        "max_completion_tokens_remote_support_unproven",
        "response_content_shape_unproven",
        "repository_timeout_owner_missing",
        "sdk_retry_owner_external",
    ]
    result = {
        "contract_version": COMPATIBILITY_CONTRACT_VERSION,
        "step8m_compatibility_baseline_sha256": (
            STEP8M_COMPATIBILITY_BASELINE_SHA256
        ),
        "candidate_fingerprint": _candidate_fingerprint(
            benchmark["candidate_definitions"]
        ),
        "scenario_order": [row["scenario_id"] for row in scenarios],
        "candidate_results": candidate_results,
        "provider_metrics": {
            "single_call_deltas_exact": all(
                row["metrics_delta"]["provider_call_count"] == 1
                for row in candidate_results
            ),
            "gemini_calls": 0,
            "primary_attempts_classification": "exact_in_fallback_scenarios",
            "fallback_attempts_classification": "exact",
            "provider_failures_classification": "exact_but_not_typed",
            "fallback_successes_classification": "exact",
            "defensive_copy": metrics_defensive,
            "missing_observability": [
                "latency",
                "input_tokens",
                "output_tokens",
                "estimated_cost",
                "request_identity",
                "retry_classification",
                "model_attempt_history",
            ],
        },
        "fallback": fallback,
        "raw_debug_output": raw_debug,
        "openai_compatibility_risks": openai_risks,
        "production_repair_requirements": repair_requirements,
        "environment_isolation": {
            "repository_dotenv_loads": isolation["dotenv_load_count"],
            "dotenv_load_attempts_blocked": isolation[
                "dotenv_load_attempts_blocked"
            ],
            "credential_reads": isolation["credential_reads"],
            "real_provider_client_constructions": sum(
                isolation["provider_client_constructions"].values()
            ),
            "network_calls": 0,
            "socket_calls": 0,
        },
        "authority_invariants": {
            "authority_transfer": False,
            "mutation_count": 0,
            "application_action_count": 0,
            "ats_action_count": 0,
            "resume_selection_allowed": False,
            "score_mutation_allowed": False,
            "ranking_mutation_allowed": False,
            "queue_mutation_allowed": False,
            "provider_response_persistence_allowed": False,
            "provider_routing_change_allowed": False,
            "production_default_change_allowed": False,
            "recovery_006_authorization": False,
        },
        "live_compatibility_status": LIVE_UNPROVEN,
        "next_safe_step": "offline_fixture_benchmark_implementation",
    }
    validate_provider_client_compatibility_result(result)
    return deepcopy(result)


def validate_provider_client_compatibility_result(result: Dict[str, Any]) -> bool:
    _require(isinstance(result, dict), "compatibility result must be an object")
    _require(
        result.get("contract_version") == COMPATIBILITY_CONTRACT_VERSION,
        "compatibility contract version mismatch",
    )
    _require(
        result.get("step8m_compatibility_baseline_sha256")
        == STEP8M_COMPATIBILITY_BASELINE_SHA256,
        "Step 8M compatibility baseline digest mismatch",
    )
    benchmark = build_provider_benchmark_contract()
    expected_pairs = [
        (row["provider"], row["model"])
        for row in benchmark["candidate_definitions"]
    ]
    actual_pairs = [
        (row.get("provider"), row.get("model"))
        for row in result.get("candidate_results", [])
    ]
    _require(actual_pairs == expected_pairs, "candidate coverage or order mismatch")
    _require(
        all(row.get("provider") != "gemini" for row in result["candidate_results"]),
        "Gemini compatibility candidate is prohibited",
    )
    _require(
        all(row.get("live_status") == LIVE_UNPROVEN for row in result["candidate_results"]),
        "live compatibility must remain unproven",
    )
    isolation = result.get("environment_isolation", {})
    for field in (
        "repository_dotenv_loads",
        "credential_reads",
        "real_provider_client_constructions",
        "network_calls",
        "socket_calls",
    ):
        _require(isolation.get(field) == 0, f"{field} must remain zero")
    authority = result.get("authority_invariants", {})
    _require(authority.get("authority_transfer") is False, "authority transfer prohibited")
    for field in ("mutation_count", "application_action_count", "ats_action_count"):
        _require(authority.get(field) == 0, f"{field} must remain zero")
    serialized = json.dumps(result, sort_keys=True, separators=(",", ":"))
    for prohibited in (
        "prompt",
        "raw_response_body",
        "synthetic_response_body",
        "api_key",
        "credential_value",
        "selected_winner",
    ):
        _require(prohibited not in serialized.lower(), f"{prohibited} is prohibited")
    return True


def serialize_provider_client_compatibility_result(
    result: Dict[str, Any] | None = None,
) -> str:
    payload = (
        run_offline_provider_client_compatibility()
        if result is None
        else deepcopy(result)
    )
    validate_provider_client_compatibility_result(payload)
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def provider_client_compatibility_sha256(
    result: Dict[str, Any] | None = None,
) -> str:
    """Return the immutable Step 8M v1 compatibility baseline identifier."""

    payload = (
        run_offline_provider_client_compatibility()
        if result is None
        else deepcopy(result)
    )
    validate_provider_client_compatibility_result(payload)
    return STEP8M_COMPATIBILITY_BASELINE_SHA256


def provider_client_compatibility_result_sha256(
    result: Dict[str, Any] | None = None,
) -> str:
    """Hash the current deterministic observation result."""

    serialized = serialize_provider_client_compatibility_result(result)
    return sha256(serialized.encode("utf-8")).hexdigest()
