from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
import json
import math
from pathlib import Path
import socket
import stat
from types import SimpleNamespace

import pytest

from src.evaluation import controlled_groq_canary_transport as transport
from src.evaluation import controlled_groq_canary_evidence_runtime as evidence
from src.evaluation import controlled_groq_provider_canary as canary
from src.evaluation import controlled_provider_benchmark_harness as harness
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    build_transmittable_request_packet,
)
from src.evaluation.provider_fixture_benchmark import (
    grade_normalized_candidate_result,
    load_fixture_case_corpus,
)


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = (
    ROOT / "src/evaluation/controlled_groq_canary_transport.py"
)
PRODUCTION_CLIENT_PATH = ROOT / "src/ai/llm_client.py"
PRICING_PATH = (
    ROOT
    / "outputs/provider_benchmark"
    / "phase11_groq_canary_pricing_001.json"
)
AUTHORIZATION_PATH = (
    ROOT
    / "outputs/provider_benchmark"
    / "phase11_groq_canary_authorization_001.json"
)
RESULT_PATH = (
    ROOT
    / "outputs/provider_benchmark"
    / "phase11_groq_canary_result_001.json"
)
CHECKPOINT_PATH = (
    ROOT
    / "outputs/provider_benchmark"
    / "phase11_groq_canary_checkpoint_001.json"
)
EXECUTION_TIME = "2026-07-25T08:58:57.094442Z"
FAKE_KEY = "synthetic-fake-key-test-memory-only"
CANARY_SHA256 = (
    "43241c341fe4d69c8cbeb2d6e95b6c56e68e67134b693c91396a932775a673bf"
)
HARNESS_SHA256 = (
    "eacf13521305689a0e7c7e3768c5e18c083308d30e6bb6b69f8d5cab1f125572"
)
PRODUCTION_CLIENT_SHA256 = (
    "830866d616c8d2d5d6b2147cd6a17b19f049f8a064592d78c2b7170d4e49ffc2"
)
PRICING_FILE_SHA256 = (
    "05a67642a30fd111ad8fb5f44dd0479595b8b8ab493d6868104ad67b20e767e7"
)
AUTHORIZATION_FILE_SHA256 = (
    "a3eef7c83614b9a11c58de56e1d2968d29ce46e8d15660040bd9b784aa6aa631"
)


def _plan():
    return build_controlled_provider_benchmark_plan()


def _canary():
    return canary.build_controlled_groq_canary_contract()


def _scheduled(index=0):
    return deepcopy(_canary()["schedule"][index])


def _packet(index=0):
    plan = _plan()
    scheduled = _scheduled(index)
    return build_transmittable_request_packet(
        case_alias=scheduled["case_alias"],
        provider=scheduled["provider"],
        model=scheduled["model"],
        plan=plan,
        live_execution_requested=False,
    )


def _case_maps():
    plan = _plan()
    corpus = load_fixture_case_corpus()
    cases_by_alias = {}
    for review, case in zip(
        plan["transmission_review"],
        corpus["cases"],
    ):
        if review["eligible_for_later_controlled_transmission"]:
            cases_by_alias[review["case_alias"]] = case
    return corpus, cases_by_alias


def _golden(index=0):
    _corpus, cases = _case_maps()
    return deepcopy(cases[_scheduled(index)["case_alias"]]["expected_output"])


def _response(index=0, **overrides):
    scheduled = _scheduled(index)
    payload = {
        "model": scheduled["model"],
        "choices": [
            SimpleNamespace(
                message=SimpleNamespace(
                    content=json.dumps(
                        _golden(index),
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                )
            )
        ],
        "usage": SimpleNamespace(
            prompt_tokens=11,
            completion_tokens=7,
        ),
        "id": "synthetic-response-id-not-returned",
        "headers": {"synthetic": "not-returned"},
        "system_fingerprint": "not-returned",
    }
    payload.update(overrides)
    return SimpleNamespace(**payload)


class FakeCompletions:
    def __init__(self, outcome):
        self.outcome = outcome
        self.calls = []
        self.active = 0
        self.maximum_active = 0

    def create(self, **kwargs):
        self.active += 1
        self.maximum_active = max(self.maximum_active, self.active)
        self.calls.append(deepcopy(kwargs))
        try:
            if isinstance(self.outcome, BaseException):
                raise self.outcome
            return self.outcome
        finally:
            self.active -= 1


class FakeClient:
    def __init__(self, outcome):
        self.completions = FakeCompletions(outcome)
        self.chat = SimpleNamespace(completions=self.completions)


class FakeSDK:
    def __init__(self, outcomes=None):
        self.outcomes = list(outcomes or [])
        self.constructor_calls = []
        self.clients = []

    def Groq(self, **kwargs):
        self.constructor_calls.append(deepcopy(kwargs))
        outcome = self.outcomes.pop(0) if self.outcomes else _response()
        client = FakeClient(outcome)
        self.clients.append(client)
        return client


def _clock():
    values = iter((100.0, 100.125))
    return lambda: next(values)


def _execute(index=0, *, response=None):
    client = FakeClient(_response(index) if response is None else response)
    result = transport.execute_groq_chat_completion_once(
        client=client,
        packet=_packet(index),
        scheduled=_scheduled(index),
        monotonic_clock=_clock(),
        plan=_plan(),
    )
    return result, client


def _offline_grade(index, result):
    corpus, cases = _case_maps()
    scheduled = _scheduled(index)
    case = cases[scheduled["case_alias"]]
    packet = {
        "case_id": case["case_id"],
        "workload_id": scheduled["workload_id"],
        "provider": result["provider"],
        "model": result["model"],
        "normalized_output": deepcopy(result["normalized_output"]),
        "schema_valid": True,
        "normalization_succeeded": True,
        "fallback_used": False,
        "provider_call_count": 0,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
        "raw_response_persisted": False,
        "live_execution": False,
        "latency_ms": result["latency_ms"],
        "input_token_count": result["input_token_count"],
        "output_token_count": result["output_token_count"],
        "estimated_cost": 0,
    }
    return grade_normalized_candidate_result(packet, corpus=corpus)


def test_transport_version_is_exact():
    assert transport.build_controlled_groq_transport_contract()[
        "transport_version"
    ] == "controlled-groq-canary-transport-v1"


def test_candidates_are_consumed_from_step8r():
    contract = transport.build_controlled_groq_transport_contract()

    assert contract["candidate_provider_models"] == (
        _canary()["candidate_provider_models"]
    )
    assert contract["canary_sha256"] == canary.controlled_groq_canary_sha256()


def test_packet_schema_is_consumed_from_step8pa():
    scheduled = _scheduled()
    packet = _packet()

    assert canary.validate_canary_transport_request(
        packet,
        scheduled=scheduled,
        plan=_plan(),
    )


def test_result_schema_is_consumed_from_step8q():
    contract = transport.build_controlled_groq_transport_contract()

    assert contract["transport_result_fields"] == sorted(
        harness.TRANSPORT_RESULT_FIELDS
    )


def test_transport_owner_contains_no_duplicate_model_registry():
    source = OWNER_PATH.read_text(encoding="utf-8")

    assert "openai/gpt-oss-20b" not in source
    assert "openai/gpt-oss-120b" not in source


def test_contract_has_no_route_or_winner_field():
    serialized = transport.serialize_controlled_groq_transport_contract().lower()

    assert "winner" not in serialized
    assert "recommended_route" not in serialized
    assert "selected_model" not in serialized


def test_production_shared_client_is_byte_identical():
    assert sha256(PRODUCTION_CLIENT_PATH.read_bytes()).hexdigest() == (
        PRODUCTION_CLIENT_SHA256
    )


def test_module_import_does_not_import_real_groq():
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    top_level_imports = {
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
        and node.name == "create_live_groq_client"
    )
    lazy_groq_imports = [
        node
        for node in ast.walk(client_factory)
        if isinstance(node, ast.ImportFrom) and node.module == "groq"
    ]

    assert "groq" not in top_level_imports
    assert len(lazy_groq_imports) == 1


def test_module_import_reads_no_environment_or_dotenv():
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    imported_modules = {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.Import, ast.ImportFrom))
        for alias in node.names
    }
    accessed_names = {
        node.id for node in ast.walk(tree) if isinstance(node, ast.Name)
    }
    accessed_attributes = {
        node.attr for node in ast.walk(tree) if isinstance(node, ast.Attribute)
    }

    assert "os" not in imported_modules
    assert not any(name.startswith("dotenv") for name in imported_modules)
    assert "getenv" not in accessed_names | accessed_attributes
    assert "environ" not in accessed_names | accessed_attributes


def test_client_construction_requires_explicit_nonempty_key():
    sdk = FakeSDK()

    with pytest.raises(ValueError, match="nonempty"):
        transport.create_live_groq_client(api_key="", sdk_module=sdk)
    assert sdk.constructor_calls == []


@pytest.mark.parametrize("invalid", [None, " ", "\t"])
def test_invalid_key_is_rejected_before_factory(invalid):
    sdk = FakeSDK()

    with pytest.raises(ValueError, match="API key"):
        transport.create_live_groq_client(
            api_key=invalid,
            sdk_module=sdk,
        )
    assert sdk.constructor_calls == []


def test_fake_constructor_receives_exact_retry_timeout_and_key():
    sdk = FakeSDK()

    client = transport.create_live_groq_client(
        api_key=FAKE_KEY,
        sdk_module=sdk,
    )

    assert client is sdk.clients[0]
    assert sdk.constructor_calls == [
        {
            "api_key": FAKE_KEY,
            "max_retries": 0,
            "timeout": 30.0,
        }
    ]


def test_client_constructor_failure_does_not_expose_explicit_key():
    class RaisingSDK:
        @staticmethod
        def Groq(**kwargs):
            raise RuntimeError(kwargs["api_key"])

    with pytest.raises(transport.UnknownProviderOutcome) as caught:
        transport.create_live_groq_client(
            api_key=FAKE_KEY,
            sdk_module=RaisingSDK(),
        )

    assert str(caught.value) == "unknown_provider_outcome"
    assert FAKE_KEY not in str(caught.value)


def test_no_global_or_cached_client_owner_exists():
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    top_level_names = {
        target.id
        for node in tree.body
        if isinstance(node, (ast.Assign, ast.AnnAssign))
        for target in (
            node.targets
            if isinstance(node, ast.Assign)
            else [node.target]
        )
        if isinstance(target, ast.Name)
    }

    assert not any("client" in name.lower() for name in top_level_names)


def test_valid_request_builds_exact_chat_argument_allowlist():
    arguments = transport.build_groq_chat_completion_arguments(
        packet=_packet(),
        scheduled=_scheduled(),
        plan=_plan(),
    )

    assert set(arguments) == {
        "model",
        "messages",
        "temperature",
        "max_completion_tokens",
        "response_format",
        "stream",
        "n",
    }


@pytest.mark.parametrize(
    "mutation",
    [
        lambda packet: packet.update({"provider": "openai"}),
        lambda packet: packet.update({"provider": "gemini"}),
        lambda packet: packet.update({"model": "unknown-model"}),
        lambda packet: packet.update({"fallback": True}),
        lambda packet: packet.update({"temperature": 1}),
        lambda packet: packet.update({"maximum_completion_tokens": 1025}),
        lambda packet: packet.update({"timeout_seconds": 31}),
        lambda packet: packet.update({"extra": "blocked"}),
        lambda packet: packet.update({"request_id": "blocked"}),
    ],
)
def test_request_packet_mutation_is_rejected(mutation):
    packet = _packet()
    mutation(packet)

    with pytest.raises(ValueError):
        transport.build_groq_chat_completion_arguments(
            packet=packet,
            scheduled=_scheduled(),
            plan=_plan(),
        )


@pytest.mark.parametrize(
    "mutation",
    [
        lambda row: row.update({"provider": "openai"}),
        lambda row: row.update({"model": "unknown-model"}),
        lambda row: row.update({"fallback": True}),
        lambda row: row.update({"harness_retry_limit": 1}),
        lambda row: row.update({"provider_sdk_retry_limit": 1}),
        lambda row: row.update({"timeout_seconds": 31}),
        lambda row: row.update({"schedule_key": "not-approved"}),
    ],
)
def test_schedule_mutation_is_rejected(mutation):
    scheduled = _scheduled()
    mutation(scheduled)

    with pytest.raises(ValueError):
        transport.build_groq_chat_completion_arguments(
            packet=_packet(),
            scheduled=scheduled,
            plan=_plan(),
        )


def test_json_schema_request_is_strict_and_exact():
    arguments = transport.build_groq_chat_completion_arguments(
        packet=_packet(),
        scheduled=_scheduled(),
    )
    response_format = arguments["response_format"]
    schema = response_format["json_schema"]["schema"]

    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert schema["type"] == "object"
    assert schema["additionalProperties"] is False
    assert set(schema["properties"]) == set(schema["required"])


def test_chat_request_is_nonstreaming_single_choice_without_tools():
    arguments = transport.build_groq_chat_completion_arguments(
        packet=_packet(),
        scheduled=_scheduled(),
    )

    assert arguments["stream"] is False
    assert arguments["n"] == 1
    for prohibited in (
        "tools",
        "metadata",
        "reasoning",
        "fallback",
        "request_id",
    ):
        assert prohibited not in arguments


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("stream", True, "streaming"),
        ("n", 2, "one choice"),
        ("temperature", 1, "temperature"),
        ("tools", [], "allowlist"),
    ],
)
def test_chat_argument_mutation_is_rejected(field, value, message):
    packet = _packet()
    scheduled = _scheduled()
    arguments = transport.build_groq_chat_completion_arguments(
        packet=packet,
        scheduled=scheduled,
    )
    arguments[field] = value

    with pytest.raises(ValueError, match=message):
        transport.validate_groq_chat_completion_arguments(
            arguments,
            packet=packet,
            scheduled=scheduled,
        )


def test_message_roles_count_and_content_are_deterministic():
    first = transport.build_groq_chat_completion_arguments(
        packet=_packet(),
        scheduled=_scheduled(),
    )
    second = transport.build_groq_chat_completion_arguments(
        packet=_packet(),
        scheduled=_scheduled(),
    )

    assert first == second
    assert [row["role"] for row in first["messages"]] == ["system", "user"]
    assert len(first["messages"]) == 2


def test_schema_name_uses_workload_not_alias_or_schedule_key():
    scheduled = _scheduled()
    arguments = transport.build_groq_chat_completion_arguments(
        packet=_packet(),
        scheduled=scheduled,
    )
    name = arguments["response_format"]["json_schema"]["name"]

    assert scheduled["workload_id"] in name
    assert scheduled["case_alias"] not in name
    assert scheduled["schedule_key"] not in name


def test_conservative_local_size_is_bounded_and_not_observed_usage():
    arguments = transport.build_groq_chat_completion_arguments(
        packet=_packet(),
        scheduled=_scheduled(),
    )
    size = transport.conservative_local_input_size_bytes(arguments)
    contract = transport.build_controlled_groq_transport_contract()

    assert 0 < size <= transport.MAXIMUM_LOCAL_INPUT_SIZE_BYTES
    assert contract["request_contract"][
        "local_size_is_observed_tokens"
    ] is False


def test_conservative_local_size_excess_fails_closed(monkeypatch):
    packet = _packet()
    scheduled = _scheduled()
    monkeypatch.setattr(transport, "MAXIMUM_LOCAL_INPUT_SIZE_BYTES", 1)

    with pytest.raises(ValueError, match="local input-size"):
        transport.build_groq_chat_completion_arguments(
            packet=packet,
            scheduled=scheduled,
        )


def test_exactly_one_sdk_call_per_execute_once_invocation():
    result, client = _execute()

    assert len(client.completions.calls) == 1
    assert set(result) == set(harness.TRANSPORT_RESULT_FIELDS)


def test_no_parallelism_occurs():
    _result, client = _execute()

    assert client.completions.maximum_active == 1


@pytest.mark.parametrize("index", [0, 1, 2, 3])
def test_four_fake_call_order_and_models_are_exact(index):
    result, client = _execute(index)

    assert len(client.completions.calls) == 1
    assert result["model"] == _scheduled(index)["model"]
    assert client.completions.calls[0]["model"] == _scheduled(index)["model"]


def test_four_fake_executions_have_two_calls_per_model():
    observed = []
    for index in range(4):
        result, _client = _execute(index)
        observed.append(result["model"])
    candidates = _canary()["candidate_provider_models"]

    assert observed.count(candidates[0]["model"]) == 2
    assert observed.count(candidates[1]["model"]) == 2


def test_latency_uses_injected_monotonic_clock():
    result, _client = _execute()

    assert result["latency_ms"] == 125.0


@pytest.mark.parametrize(
    "latency",
    [float("nan"), float("inf"), -1],
)
def test_invalid_latency_is_rejected(latency):
    with pytest.raises(ValueError, match="latency"):
        transport.reduce_groq_sdk_response(
            _response(),
            scheduled=_scheduled(),
            packet=_packet(),
            latency_ms=latency,
        )


@pytest.mark.parametrize(
    "choices",
    [[], [SimpleNamespace(), SimpleNamespace()]],
)
def test_exactly_one_choice_is_required(choices):
    with pytest.raises(harness.DefinitiveTransportFailure):
        transport.reduce_groq_sdk_response(
            _response(choices=choices),
            scheduled=_scheduled(),
            packet=_packet(),
            latency_ms=1,
        )


@pytest.mark.parametrize("content", ["", " ", "{malformed"])
def test_empty_or_malformed_content_is_rejected(content):
    response = _response()
    response.choices[0].message.content = content

    with pytest.raises(harness.DefinitiveTransportFailure):
        transport.reduce_groq_sdk_response(
            response,
            scheduled=_scheduled(),
            packet=_packet(),
            latency_ms=1,
        )


@pytest.mark.parametrize(
    "payload",
    [{}, {"unexpected": True}, []],
)
def test_schema_incompatible_output_is_rejected(payload):
    response = _response()
    response.choices[0].message.content = json.dumps(payload)

    with pytest.raises(harness.DefinitiveTransportFailure):
        transport.reduce_groq_sdk_response(
            response,
            scheduled=_scheduled(),
            packet=_packet(),
            latency_ms=1,
        )


def test_response_model_mismatch_is_rejected():
    with pytest.raises(
        harness.DefinitiveTransportFailure,
        match="provider_model_mismatch",
    ):
        transport.reduce_groq_sdk_response(
            _response(model="unknown-model"),
            scheduled=_scheduled(),
            packet=_packet(),
            latency_ms=1,
        )


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
def test_missing_invalid_or_excess_usage_is_rejected(
    prompt_tokens, completion_tokens
):
    response = _response(
        usage=SimpleNamespace(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )
    )

    with pytest.raises(harness.DefinitiveTransportFailure):
        transport.reduce_groq_sdk_response(
            response,
            scheduled=_scheduled(),
            packet=_packet(),
            latency_ms=1,
        )


def test_observed_usage_is_extracted_exactly():
    result, _client = _execute()

    assert result["input_token_count"] == 11
    assert result["output_token_count"] == 7


def test_reduced_result_excludes_raw_sensitive_response_fields():
    result, _client = _execute()

    assert set(result) == set(harness.TRANSPORT_RESULT_FIELDS)
    for prohibited in (
        "id",
        "headers",
        "reasoning",
        "system_fingerprint",
        "usage",
        "choices",
        "request",
        "prompt",
    ):
        assert prohibited not in result


def test_reduced_result_passes_step8q_validation():
    result, _client = _execute()

    assert harness.validate_injected_transport_result(
        result,
        scheduled=_scheduled(),
    )


@pytest.mark.parametrize("index", [0, 1, 2, 3])
def test_all_four_reduced_outputs_pass_step8o_grading(index):
    result, _client = _execute(index)
    grade = _offline_grade(index, result)

    assert grade["quality_gate_passed"] is True
    assert all(value == 0 for value in grade["hard_failures"].values())


@pytest.mark.parametrize(
    ("error", "expected_exception", "category"),
    [
        (
            TimeoutError("raw timeout marker"),
            harness.AmbiguousTransportTimeout,
            "ambiguous_timeout",
        ),
        (
            type("AuthenticationError", (Exception,), {})(
                "raw auth marker"
            ),
            harness.DefinitiveTransportFailure,
            "definitive_authentication_failure",
        ),
        (
            type("BadRequestError", (Exception,), {})(
                "raw invalid marker"
            ),
            harness.DefinitiveTransportFailure,
            "definitive_invalid_request",
        ),
        (
            ConnectionError("raw connection marker"),
            harness.DefinitiveTransportFailure,
            "definitive_connection_failure",
        ),
        (
            RuntimeError("raw unknown marker"),
            transport.UnknownProviderOutcome,
            "unknown_provider_outcome",
        ),
    ],
)
def test_sdk_errors_map_to_bounded_categories_without_raw_text(
    error, expected_exception, category
):
    client = FakeClient(error)

    with pytest.raises(expected_exception) as caught:
        transport.execute_groq_chat_completion_once(
            client=client,
            packet=_packet(),
            scheduled=_scheduled(),
            monotonic_clock=_clock(),
        )
    assert str(caught.value) == category
    assert len(client.completions.calls) == 1


def test_timeout_has_no_retry_or_fallback():
    client = FakeClient(TimeoutError("raw"))

    with pytest.raises(harness.AmbiguousTransportTimeout):
        transport.execute_groq_chat_completion_once(
            client=client,
            packet=_packet(),
            scheduled=_scheduled(),
            monotonic_clock=_clock(),
        )
    assert len(client.completions.calls) == 1


def test_failure_has_no_cross_provider_call_or_recursion():
    client = FakeClient(RuntimeError("raw"))

    with pytest.raises(transport.UnknownProviderOutcome):
        transport.execute_groq_chat_completion_once(
            client=client,
            packet=_packet(),
            scheduled=_scheduled(),
            monotonic_clock=_clock(),
        )
    assert len(client.completions.calls) == 1


def test_fake_key_never_appears_in_bounded_errors():
    sdk = FakeSDK([RuntimeError(FAKE_KEY)])
    client = transport.create_live_groq_client(
        api_key=FAKE_KEY,
        sdk_module=sdk,
    )

    with pytest.raises(transport.UnknownProviderOutcome) as caught:
        transport.execute_groq_chat_completion_once(
            client=client,
            packet=_packet(),
            scheduled=_scheduled(),
            monotonic_clock=_clock(),
        )
    assert FAKE_KEY not in str(caught.value)


def test_only_fake_sdk_objects_are_used_for_four_constructor_calls():
    sdk = FakeSDK([_response(index) for index in range(4)])
    results = []
    for index in range(4):
        client = transport.create_live_groq_client(
            api_key=FAKE_KEY,
            sdk_module=sdk,
        )
        results.append(
            transport.execute_groq_chat_completion_once(
                client=client,
                packet=_packet(index),
                scheduled=_scheduled(index),
                monotonic_clock=_clock(),
            )
        )

    assert len(sdk.constructor_calls) == 4
    assert len(results) == 4
    assert all(call["max_retries"] == 0 for call in sdk.constructor_calls)
    assert all(call["timeout"] == 30.0 for call in sdk.constructor_calls)


def test_no_network_socket_reach_with_fake_sdk(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("network reach prohibited")

    monkeypatch.setattr(socket, "socket", blocked)

    result, _client = _execute()
    assert result["provider_outcome_category"] == "success"


def test_owner_has_no_database_subprocess_thread_or_artifact_write_reach():
    source = OWNER_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    prohibited_imports = {
        "psycopg",
        "sqlalchemy",
        "subprocess",
        "threading",
    }
    imports = set()
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                calls.add(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                calls.add(node.func.attr)

    assert imports.isdisjoint(prohibited_imports)
    assert calls.isdisjoint(
        {
            "Popen",
            "Thread",
            "connect",
            "open",
            "write_bytes",
            "write_text",
        }
    )


def test_no_result_or_checkpoint_artifact_is_written():
    assert not RESULT_PATH.exists()
    incident_bytes = (
        CHECKPOINT_PATH.read_bytes() if CHECKPOINT_PATH.exists() else None
    )
    if incident_bytes is not None:
        assert CHECKPOINT_PATH.is_file()
        assert not CHECKPOINT_PATH.is_symlink()
        assert stat.S_IMODE(CHECKPOINT_PATH.stat().st_mode) == 0o600
        pricing = json.loads(PRICING_PATH.read_text(encoding="utf-8"))
        authorization = json.loads(
            AUTHORIZATION_PATH.read_text(encoding="utf-8")
        )
        checkpoint = evidence.load_checkpoint(
            CHECKPOINT_PATH,
            repository_root=ROOT,
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        )
        assert checkpoint == evidence.build_empty_checkpoint(
            authorization=authorization,
            pricing=pricing,
            execution_at_utc=EXECUTION_TIME,
            canary=_canary(),
        )

    _execute()

    assert not RESULT_PATH.exists()
    if incident_bytes is None:
        assert not CHECKPOINT_PATH.exists()
    else:
        assert CHECKPOINT_PATH.read_bytes() == incident_bytes
        assert stat.S_IMODE(CHECKPOINT_PATH.stat().st_mode) == 0o600


def test_operator_inputs_are_unchanged_and_still_validate():
    assert sha256(PRICING_PATH.read_bytes()).hexdigest() == (
        PRICING_FILE_SHA256
    )
    assert sha256(AUTHORIZATION_PATH.read_bytes()).hexdigest() == (
        AUTHORIZATION_FILE_SHA256
    )
    pricing = json.loads(PRICING_PATH.read_text(encoding="utf-8"))
    authorization = json.loads(
        AUTHORIZATION_PATH.read_text(encoding="utf-8")
    )

    assert canary.validate_operator_approved_pricing(
        pricing,
        execution_at_utc=EXECUTION_TIME,
    )
    assert canary.validate_operator_authorization(
        authorization,
        pricing=pricing,
        execution_at_utc=EXECUTION_TIME,
    )


def test_canary_and_harness_digests_are_unchanged():
    assert canary.controlled_groq_canary_sha256() == CANARY_SHA256
    assert harness.controlled_benchmark_harness_sha256() == HARNESS_SHA256


def test_recovery_006_remains_absent():
    assert not (ROOT / canary.RECOVERY_006_STATUS_PATH).exists()


def test_no_production_source_imports_the_transport_owner():
    references = []
    for path in (ROOT / "src").rglob("*.py"):
        if path == OWNER_PATH:
            continue
        if "controlled_groq_canary_transport" in path.read_text(
            encoding="utf-8"
        ):
            references.append(path.relative_to(ROOT).as_posix())

    assert references == [
        "src/evaluation/controlled_groq_canary_run_identity.py",
        "src/evaluation/controlled_groq_canary_run_003_transport.py",
        "src/evaluation/controlled_groq_canary_evidence_runtime.py",
        "src/evaluation/controlled_groq_canary_run_004_evidence_runtime.py",
        "src/evaluation/controlled_groq_canary_run_005_evidence_runtime.py",
    ]


def test_authority_application_and_ats_actions_remain_zero():
    contract = transport.build_controlled_groq_transport_contract()
    authority = contract["authority_invariants"]

    assert authority["mutation_count"] == 0
    assert authority["application_action_count"] == 0
    assert authority["ats_action_count"] == 0
    assert authority["production_activation"] is False
    assert authority["live_execution_authorized"] is False
