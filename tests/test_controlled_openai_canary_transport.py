from __future__ import annotations

import ast
from copy import deepcopy
import json
from pathlib import Path
import socket
from types import SimpleNamespace

import pytest

from src.evaluation import controlled_groq_canary_transport as groq_transport
from src.evaluation import controlled_groq_provider_canary as groq_canary
from src.evaluation import controlled_openai_canary_transport as transport
from src.evaluation import controlled_provider_benchmark_harness as harness
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    build_transmittable_request_packet,
)
from src.evaluation.controlled_production_parity_benchmark import (
    build_production_parity_request,
    validate_and_grade_production_parity_response,
)
from src.evaluation.provider_fixture_benchmark import load_fixture_case_corpus


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = ROOT / "src/evaluation/controlled_openai_canary_transport.py"
FAKE_KEY = "synthetic-openai-key-memory-only"
EXPECTED_MODEL_COUNTS = {
    "groq/openai/gpt-oss-20b": 12,
    "groq/openai/gpt-oss-120b": 10,
    "openai/gpt-5-mini": 12,
    "openai/gpt-5.1": 10,
}


def _plan():
    return build_controlled_provider_benchmark_plan()


def _scheduled(model="gpt-5-mini"):
    row = next(
        row
        for row in _plan()["staged_matrix"]
        if row["provider"] == "openai" and row["model"] == model
    )
    return {
        "schedule_key": f"synthetic-{model}",
        "execution_order": row["execution_order"],
        "case_alias": row["case_alias"],
        "workload_id": row["workload_id"],
        "tier": row["tier"],
        "provider": row["provider"],
        "model": row["model"],
        "timeout_seconds": 30,
        "fallback": False,
        "harness_retry_limit": 0,
    }


def _packet(model="gpt-5-mini"):
    scheduled = _scheduled(model)
    return build_transmittable_request_packet(
        case_alias=scheduled["case_alias"],
        provider=scheduled["provider"],
        model=scheduled["model"],
        plan=_plan(),
        live_execution_requested=False,
    )


def _expected_output(scheduled):
    corpus = load_fixture_case_corpus()
    plan = _plan()
    by_alias = {
        review["case_alias"]: case["expected_output"]
        for review, case in zip(plan["transmission_review"], corpus["cases"])
        if review["eligible_for_later_controlled_transmission"]
    }
    return deepcopy(by_alias[scheduled["case_alias"]])


def _response(model="gpt-5-mini", **overrides):
    scheduled = _scheduled(model)
    payload = {
        "model": model,
        "choices": [
            SimpleNamespace(
                message=SimpleNamespace(
                    content=json.dumps(
                        _expected_output(scheduled),
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                    reasoning="synthetic-reasoning-not-returned",
                )
            )
        ],
        "usage": SimpleNamespace(
            prompt_tokens=13,
            completion_tokens=8,
            completion_tokens_details={"reasoning_tokens": 2},
        ),
        "id": "synthetic-request-id-not-returned",
        "headers": {"synthetic": "not-returned"},
        "system_fingerprint": "not-returned",
    }
    payload.update(overrides)
    return SimpleNamespace(**payload)


class FakeCompletions:
    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        if isinstance(self.outcome, BaseException):
            raise self.outcome
        return self.outcome


class FakeClient:
    def __init__(self, outcome):
        self.completions = FakeCompletions(outcome)
        self.chat = SimpleNamespace(completions=self.completions)


class FakeSDK:
    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.constructor_calls = []
        self.clients = []

    def OpenAI(self, **kwargs):
        self.constructor_calls.append(deepcopy(kwargs))
        client = FakeClient(self.outcomes.pop(0))
        self.clients.append(client)
        return client


def _clock():
    values = iter((200.0, 200.075))
    return lambda: next(values)


def _execute(model="gpt-5-mini", *, response=None, api_key=FAKE_KEY):
    outcome = _response(model) if response is None else response
    sdk = FakeSDK([outcome])
    result = transport.execute_openai_chat_completion_once(
        api_key=api_key,
        sdk_module=sdk,
        packet=_packet(model),
        scheduled=_scheduled(model),
        monotonic_clock=_clock(),
        plan=_plan(),
    )
    return result, sdk


def _execute_production_parity(*, response_model):
    plan = _plan()
    scheduled = _scheduled("gpt-5-mini")
    scheduled["provider_sdk_retry_limit"] = 0
    parity_request = build_production_parity_request(
        _packet("gpt-5-mini"),
        plan=plan,
    )
    response = _response("gpt-5-mini")
    response.model = response_model
    sdk = FakeSDK([response])
    result = transport.execute_openai_production_parity_chat_completion_once(
        api_key=FAKE_KEY,
        parity_request=parity_request,
        scheduled=scheduled,
        parity_response_consumer=lambda content: (
            validate_and_grade_production_parity_response(
                parity_request,
                content,
                plan=plan,
            )
        ),
        monotonic_clock=_clock(),
        sdk_module=sdk,
        plan=plan,
    )
    return result, sdk


def test_transport_contract_reuses_generic_result_fields_and_catalog_models():
    contract = transport.build_controlled_openai_transport_contract()

    assert contract["transport_version"] == (
        "controlled-openai-canary-transport-v1"
    )
    assert contract["candidate_provider_models"] == [
        {"provider": "openai", "model": "gpt-5-mini"},
        {"provider": "openai", "model": "gpt-5.1"},
    ]
    assert contract["transport_result_fields"] == sorted(
        harness.TRANSPORT_RESULT_FIELDS
    )


def test_contract_is_deterministic_default_off_and_non_qualifying():
    first = transport.build_controlled_openai_transport_contract()
    second = transport.build_controlled_openai_transport_contract()

    assert first == second
    assert transport.controlled_openai_transport_sha256(first) == (
        transport.controlled_openai_transport_sha256(second)
    )
    assert first["authority_invariants"] == {
        "live_execution_authorized": False,
        "fallback": False,
        "retry_count": 0,
        "production_activation": False,
        "qualification_decision_allowed": False,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
    }


def test_import_is_lazy_and_has_no_environment_or_user_credential_reach():
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    top_level_modules = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom)
    } | {
        alias.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    client_factory = next(
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "create_live_openai_client"
    )
    lazy_imports = [
        node
        for node in ast.walk(client_factory)
        if isinstance(node, ast.ImportFrom) and node.module == "openai"
    ]

    assert "openai" not in top_level_modules
    assert len(lazy_imports) == 1
    for prohibited in (
        "os.getenv",
        "os.environ",
        "dotenv",
        "user_ai_settings",
        "user_provider_runtime",
        "OPENAI_API_KEY",
        "LLM_PROVIDER",
        "LLM_MODEL",
    ):
        assert prohibited not in source


@pytest.mark.parametrize("invalid", [None, "", " ", "\t"])
def test_explicit_nonempty_api_key_is_required_before_client_construction(invalid):
    sdk = FakeSDK([_response()])

    with pytest.raises(ValueError, match="API key"):
        transport.execute_openai_chat_completion_once(
            api_key=invalid,
            sdk_module=sdk,
            packet=_packet(),
            scheduled=_scheduled(),
            monotonic_clock=_clock(),
        )
    assert sdk.constructor_calls == []


def test_explicit_key_fresh_client_retry_and_timeout_boundary_is_exact(
    monkeypatch,
):
    monkeypatch.setenv("OPENAI_API_KEY", "environment-key-must-not-be-read")
    sdk = FakeSDK([_response(), _response()])

    for _ in range(2):
        transport.execute_openai_chat_completion_once(
            api_key=FAKE_KEY,
            sdk_module=sdk,
            packet=_packet(),
            scheduled=_scheduled(),
            monotonic_clock=_clock(),
        )

    assert len(sdk.clients) == 2
    assert sdk.clients[0] is not sdk.clients[1]
    assert sdk.constructor_calls == [
        {"api_key": FAKE_KEY, "max_retries": 0, "timeout": 30.0},
        {"api_key": FAKE_KEY, "max_retries": 0, "timeout": 30.0},
    ]


@pytest.mark.parametrize("model", ["gpt-5-mini", "gpt-5.1"])
def test_only_catalog_openai_models_execute_one_call(model):
    result, sdk = _execute(model)

    assert result["provider"] == "openai"
    assert result["model"] == model
    assert len(sdk.constructor_calls) == 1
    assert len(sdk.clients[0].completions.calls) == 1


@pytest.mark.parametrize(
    "mutation",
    [
        lambda packet, scheduled: packet.update({"model": "gpt-4o"}),
        lambda packet, scheduled: packet.update({"provider": "groq"}),
        lambda packet, scheduled: scheduled.update({"model": "gpt-4o"}),
        lambda packet, scheduled: scheduled.update({"provider": "groq"}),
        lambda packet, scheduled: scheduled.update({"timeout_seconds": 31}),
        lambda packet, scheduled: scheduled.update({"fallback": True}),
        lambda packet, scheduled: scheduled.update({"harness_retry_limit": 1}),
        lambda packet, scheduled: scheduled.update({"provider_sdk_retry_limit": 1}),
        lambda packet, scheduled: packet.update({"maximum_completion_tokens": 1025}),
    ],
)
def test_invalid_model_provider_or_bounds_fail_before_sdk_construction(mutation):
    packet = _packet()
    scheduled = _scheduled()
    mutation(packet, scheduled)
    sdk = FakeSDK([_response()])

    with pytest.raises(ValueError):
        transport.execute_openai_chat_completion_once(
            api_key=FAKE_KEY,
            sdk_module=sdk,
            packet=packet,
            scheduled=scheduled,
            monotonic_clock=_clock(),
        )
    assert sdk.constructor_calls == []


def test_gpt_5_mini_uses_proven_zero_thinking_request_shape():
    arguments = transport.build_openai_chat_completion_arguments(
        packet=_packet("gpt-5-mini"),
        scheduled=_scheduled("gpt-5-mini"),
    )

    assert "temperature" not in arguments
    assert arguments["reasoning_effort"] == "minimal"
    assert arguments["max_completion_tokens"] == 1024


def test_gpt_5_1_uses_proven_temperature_request_shape():
    arguments = transport.build_openai_chat_completion_arguments(
        packet=_packet("gpt-5.1"),
        scheduled=_scheduled("gpt-5.1"),
    )

    assert arguments["temperature"] == 0
    assert "reasoning_effort" not in arguments
    assert arguments["max_completion_tokens"] == 1024


@pytest.mark.parametrize("model", ["gpt-5-mini", "gpt-5.1"])
def test_request_is_strict_schema_bounded_and_contains_no_fallback_surface(model):
    arguments = transport.build_openai_chat_completion_arguments(
        packet=_packet(model),
        scheduled=_scheduled(model),
    )
    response_format = arguments["response_format"]
    schema = response_format["json_schema"]["schema"]

    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == set(schema["required"])
    assert transport.conservative_local_input_size_bytes(arguments) <= 4096
    for prohibited in (
        "fallback",
        "tools",
        "metadata",
        "request_id",
        "api_key",
    ):
        assert prohibited not in arguments


def test_success_result_uses_exact_generic_contract_usage_and_local_latency():
    result, _sdk = _execute()

    assert set(result) == set(harness.TRANSPORT_RESULT_FIELDS)
    assert harness.validate_injected_transport_result(
        result,
        scheduled=_scheduled(),
    )
    assert result["input_token_count"] == 13
    assert result["output_token_count"] == 8
    assert result["latency_ms"] == pytest.approx(75.0)
    assert result["provider_outcome_category"] == "success"


@pytest.mark.parametrize(
    ("scheduled_model", "response_model"),
    [
        ("gpt-5-mini", "gpt-5-mini"),
        ("gpt-5-mini", "gpt-5-mini-2025-08-07"),
        ("gpt-5.1", "gpt-5.1-2025-11-13"),
    ],
)
def test_exact_and_approved_snapshot_response_models_are_accepted(
    scheduled_model,
    response_model,
):
    response = _response(scheduled_model)
    response.model = response_model

    result, _sdk = _execute(scheduled_model, response=response)

    assert result["model"] == scheduled_model


@pytest.mark.parametrize(
    "response_model",
    [
        "gpt-5",
        "gpt-5-mini-2025-08-08",
        "gpt-5.1-2025-11-14",
        "gpt-5-mini-evil",
    ],
)
def test_unapproved_response_models_remain_rejected(response_model):
    response = _response("gpt-5-mini")
    response.model = response_model

    with pytest.raises(
        harness.DefinitiveTransportFailure,
        match="provider_model_mismatch",
    ):
        _execute("gpt-5-mini", response=response)


def test_production_parity_accepts_official_gpt_5_mini_snapshot():
    result, sdk = _execute_production_parity(
        response_model="gpt-5-mini-2025-08-07",
    )

    assert result["model"] == "gpt-5-mini"
    assert result["provider_outcome_category"] == "success"
    assert len(sdk.constructor_calls) == 1
    assert sdk.constructor_calls[0]["max_retries"] == 0
    assert len(sdk.clients[0].completions.calls) == 1
    serialized = json.dumps(result, sort_keys=True)
    for prohibited in (
        "synthetic-request-id-not-returned",
        "synthetic-reasoning-not-returned",
        "headers",
    ):
        assert prohibited not in serialized


def test_production_parity_rejects_unrelated_response_model():
    with pytest.raises(
        harness.DefinitiveTransportFailure,
        match="provider_model_mismatch",
    ):
        _execute_production_parity(response_model="gpt-5-mini-evil")


def test_unsupported_production_parity_mode_fails_before_sdk_construction():
    plan = _plan()
    scheduled = _scheduled("gpt-5-mini")
    scheduled["provider_sdk_retry_limit"] = 0
    parity_request = build_production_parity_request(
        _packet("gpt-5-mini"),
        plan=plan,
    )
    parity_request["response_contract"]["mode"] = "unsupported"
    sdk = FakeSDK([])

    with pytest.raises(ValueError, match="production response mode mismatch"):
        transport.execute_openai_production_parity_chat_completion_once(
            api_key=FAKE_KEY,
            parity_request=parity_request,
            scheduled=scheduled,
            parity_response_consumer=lambda _content: {},
            monotonic_clock=_clock(),
            sdk_module=sdk,
            plan=plan,
        )

    assert sdk.constructor_calls == []
    assert sdk.clients == []


@pytest.mark.parametrize(
    ("prompt_tokens", "completion_tokens"),
    [
        (None, 1),
        (1, None),
        ("1", 1),
        (1, "1"),
        (0, 1),
        (1, 0),
        (4097, 1),
        (1, 1025),
    ],
)
def test_missing_malformed_or_unbounded_usage_fails_closed(
    prompt_tokens,
    completion_tokens,
):
    response = _response(
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
    )

    with pytest.raises(harness.DefinitiveTransportFailure):
        _execute(response=response)


@pytest.mark.parametrize(
    "response",
    [
        SimpleNamespace(
            model="gpt-5-mini",
            choices=[],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1),
        ),
        SimpleNamespace(
            model="gpt-5-mini",
            choices=[SimpleNamespace(message=SimpleNamespace(content=""))],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1),
        ),
        SimpleNamespace(
            model="gpt-5-mini",
            choices=[
                SimpleNamespace(message=SimpleNamespace(content="{malformed"))
            ],
            usage=SimpleNamespace(prompt_tokens=1, completion_tokens=1),
        ),
    ],
)
def test_malformed_provider_content_fails_without_repair_call(response):
    sdk = FakeSDK([response])

    with pytest.raises(harness.DefinitiveTransportFailure):
        transport.execute_openai_chat_completion_once(
            api_key=FAKE_KEY,
            sdk_module=sdk,
            packet=_packet(),
            scheduled=_scheduled(),
            monotonic_clock=_clock(),
        )
    assert len(sdk.clients[0].completions.calls) == 1


@pytest.mark.parametrize(
    ("error", "expected_exception", "category"),
    [
        (
            TimeoutError("raw timeout secret"),
            harness.AmbiguousTransportTimeout,
            "ambiguous_timeout",
        ),
        (
            type("AuthenticationError", (Exception,), {})("raw auth secret"),
            harness.DefinitiveTransportFailure,
            "definitive_authentication_failure",
        ),
        (
            type("BadRequestError", (Exception,), {})("raw request secret"),
            harness.DefinitiveTransportFailure,
            "definitive_invalid_request",
        ),
        (
            type("ConfigurationError", (Exception,), {})(
                "raw configuration secret"
            ),
            harness.DefinitiveTransportFailure,
            "definitive_configuration_failure",
        ),
        (
            type(
                "RateLimitError",
                (Exception,),
                {"status_code": 429},
            )("raw rejection secret"),
            harness.DefinitiveTransportFailure,
            "definitive_provider_rejection",
        ),
        (
            ConnectionError("raw connection secret"),
            harness.DefinitiveTransportFailure,
            "definitive_connection_failure",
        ),
        (
            RuntimeError("raw unknown secret"),
            transport.UnknownProviderOutcome,
            "unknown_provider_outcome",
        ),
    ],
)
def test_sdk_errors_are_bounded_and_suppress_raw_exception_text(
    error,
    expected_exception,
    category,
):
    sdk = FakeSDK([error])

    with pytest.raises(expected_exception) as caught:
        transport.execute_openai_chat_completion_once(
            api_key=FAKE_KEY,
            sdk_module=sdk,
            packet=_packet(),
            scheduled=_scheduled(),
            monotonic_clock=_clock(),
        )
    assert str(caught.value) == category
    assert "secret" not in str(caught.value)
    assert len(sdk.clients[0].completions.calls) == 1


def test_client_constructor_error_suppresses_key_and_raw_text():
    class RaisingSDK:
        @staticmethod
        def OpenAI(**kwargs):
            raise RuntimeError(f"raw constructor {kwargs['api_key']}")

    with pytest.raises(transport.UnknownProviderOutcome) as caught:
        transport.execute_openai_chat_completion_once(
            api_key=FAKE_KEY,
            sdk_module=RaisingSDK(),
            packet=_packet(),
            scheduled=_scheduled(),
            monotonic_clock=_clock(),
        )
    assert str(caught.value) == "unknown_provider_outcome"
    assert FAKE_KEY not in str(caught.value)


def test_reduced_result_discards_raw_sdk_response_sensitive_fields():
    result, _sdk = _execute()

    serialized = json.dumps(result, sort_keys=True)
    for prohibited in (
        "synthetic-request-id-not-returned",
        "synthetic-reasoning-not-returned",
        "reasoning_tokens",
        "headers",
        "system_fingerprint",
        FAKE_KEY,
    ):
        assert prohibited not in serialized


def test_fake_groq_and_openai_success_share_the_generic_result_contract():
    openai_result, _sdk = _execute()
    groq_scheduled = deepcopy(groq_canary.build_controlled_groq_canary_contract()[
        "schedule"
    ][0])
    groq_packet = build_transmittable_request_packet(
        case_alias=groq_scheduled["case_alias"],
        provider=groq_scheduled["provider"],
        model=groq_scheduled["model"],
        plan=_plan(),
        live_execution_requested=False,
    )
    groq_response = SimpleNamespace(
        model=groq_scheduled["model"],
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content=json.dumps(_expected_output(groq_scheduled))
                )
            )
        ],
        usage=SimpleNamespace(prompt_tokens=13, completion_tokens=8),
    )
    groq_result = groq_transport.reduce_groq_sdk_response(
        groq_response,
        scheduled=groq_scheduled,
        packet=groq_packet,
        latency_ms=75.0,
        plan=_plan(),
    )

    assert set(openai_result) == set(groq_result) == set(
        harness.TRANSPORT_RESULT_FIELDS
    )
    assert openai_result["provider_outcome_category"] == (
        groq_result["provider_outcome_category"]
    )
    assert openai_result["input_token_count"] == groq_result["input_token_count"]
    assert openai_result["output_token_count"] == groq_result["output_token_count"]
    assert openai_result["latency_ms"] == pytest.approx(
        groq_result["latency_ms"]
    )


def test_fake_sdk_path_has_no_network_or_artifact_write(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("network or artifact reach prohibited")

    monkeypatch.setattr(socket, "socket", blocked)
    monkeypatch.setattr(Path, "write_text", blocked)
    monkeypatch.setattr(Path, "write_bytes", blocked)

    result, _sdk = _execute()
    assert result["provider_outcome_category"] == "success"


def test_owner_has_no_network_database_process_thread_or_write_surface():
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    imports = set()
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)

    assert imports.isdisjoint(
        {
            "httpx",
            "requests",
            "socket",
            "psycopg",
            "sqlalchemy",
            "subprocess",
            "threading",
        }
    )
    assert calls.isdisjoint(
        {"connect", "open", "write_bytes", "write_text", "Popen", "Thread"}
    )


def test_step9c1_plan_remains_exactly_44_cells_and_default_off():
    plan = _plan()

    assert plan["request_counts"]["maximum_total_requests"] == 44
    assert plan["request_counts"]["by_model"] == EXPECTED_MODEL_COUNTS
    assert plan["authority_invariants"]["live_execution_authorized"] is False
    assert plan["authority_invariants"]["provider_calls_allowed"] is False
    assert plan["authority_invariants"]["routing_change_allowed"] is False
    assert "qualified" not in json.dumps(plan).lower()


def test_no_production_source_imports_openai_transport_owner():
    references = []
    for path in (ROOT / "src").rglob("*.py"):
        if path == OWNER_PATH:
            continue
        if "controlled_openai_canary_transport" in path.read_text(
            encoding="utf-8"
        ):
            references.append(path.relative_to(ROOT).as_posix())

    assert references == [
        "src/evaluation/controlled_live_provider_qualification.py"
    ]
