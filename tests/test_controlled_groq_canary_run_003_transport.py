from __future__ import annotations

import ast
from copy import deepcopy
import json
import os
from pathlib import Path
import socket
import subprocess
import sys

import pytest

from src.evaluation import controlled_groq_canary_run_003_identity as identity
from src.evaluation import controlled_groq_canary_run_003_plan as plan
from src.evaluation import controlled_groq_canary_run_003_transport as owner


ROOT = Path(__file__).resolve().parents[1]
OWNER_PATH = (
    ROOT / "src/evaluation/controlled_groq_canary_run_003_transport.py"
)
PLAN_SHA = (
    "5d63ef8bc8749645c19211184e8b7be16aa1909fbdb8a3682b9073af7270e9e8"
)
IDENTITY_SHA = (
    "db22f2add4075775747f3c90de89977f82f918adc655eda1f343ab5aeed44980"
)
def _packet():
    return plan.build_run_003_transmittable_request_packet()


def _row():
    return plan.build_run_003_plan_contract()["schedule"][0]


def _arguments():
    return owner.build_run_003_groq_chat_completion_arguments(
        packet=_packet(),
        scheduled=_row(),
    )


def _response(**overrides):
    packet = _packet()
    output = {
        field: []
        for field in packet["output_schema"]["required_fields"]
    }
    response = {
        "model": "openai/gpt-oss-120b",
        "choices": [
            {"message": {"content": json.dumps(output)}}
        ],
        "usage": {"prompt_tokens": 100, "completion_tokens": 50},
    }
    response.update(overrides)
    return response


class FakeCompletions:
    def __init__(self, response=None, error=None):
        self.response = _response() if response is None else response
        self.error = error
        self.calls = []

    def create(self, **kwargs):
        self.calls.append(deepcopy(kwargs))
        if self.error is not None:
            raise self.error
        return deepcopy(self.response)


class FakeClient:
    def __init__(self, response=None, error=None):
        self.chat = type("Chat", (), {})()
        self.chat.completions = FakeCompletions(response, error)


def _clock():
    values = iter((10.0, 10.125))
    return lambda: next(values)


def test_exact_version_and_contract_fields():
    assert owner.RUN_003_TRANSPORT_VERSION == (
        "controlled-groq-canary-run-003-transport-v1"
    )
    contract = owner.build_run_003_transport_contract()
    assert set(contract) == {
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


def test_contract_is_deterministic_canonical_and_deep_copy_contained():
    first = owner.build_run_003_transport_contract()
    second = owner.build_run_003_transport_contract()
    assert first == second
    assert owner.validate_run_003_transport_contract(first)
    assert owner.serialize_run_003_transport_contract(first) == json.dumps(
        first,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert owner.run_003_transport_sha256(first) == (
        owner.run_003_transport_sha256(second)
    )
    first["schedule"][0]["model"] = "tampered"
    assert owner.build_run_003_transport_contract()["schedule"][0][
        "model"
    ] == "openai/gpt-oss-120b"


def test_transport_digest_is_stable_in_fresh_process():
    command = (
        "from src.evaluation.controlled_groq_canary_run_003_transport "
        "import run_003_transport_sha256;"
        "print(run_003_transport_sha256())"
    )
    completed = subprocess.run(
        [sys.executable, "-c", command],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
        env={**os.environ, "PYTHONPATH": str(ROOT)},
    )
    assert completed.stderr == ""
    assert completed.stdout.strip() == owner.run_003_transport_sha256()


def test_exact_plan_identity_and_one_row_binding():
    contract = owner.build_run_003_transport_contract()
    assert contract["run_003_plan_sha256"] == PLAN_SHA
    assert contract["run_003_identity_sha256"] == IDENTITY_SHA
    assert contract["schedule"] == plan.build_run_003_plan_contract()[
        "schedule"
    ]
    assert len(contract["schedule"]) == 1
    assert contract["schedule"][0]["schedule_key"].startswith(
        "canary_run_003_"
    )
    assert contract["target"] == {
        "case_alias": "case_fb2b069aa9340571b60e1fb5",
        "workload_id": "skill_extraction",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
    }


def test_transport_contract_is_one_call_default_off():
    request = owner.build_run_003_transport_contract()["request_contract"]
    assert request["maximum_provider_calls"] == 1
    assert request["timeout_seconds"] == 30
    assert request["temperature"] == 0
    assert request["maximum_completion_tokens"] == 1024
    assert request["maximum_input_tokens"] == 4096
    assert request["stream"] is False
    assert request["n"] == 1
    assert request["retry_count"] == 0
    assert request["fallback"] is False


def test_chat_arguments_have_exact_fields_and_values():
    arguments = _arguments()
    assert set(arguments) == {
        "model",
        "messages",
        "temperature",
        "max_completion_tokens",
        "response_format",
        "stream",
        "n",
    }
    assert arguments["model"] == "openai/gpt-oss-120b"
    assert arguments["temperature"] == 0
    assert arguments["max_completion_tokens"] == 1024
    assert arguments["stream"] is False
    assert arguments["n"] == 1


def test_messages_are_exact_and_canonical():
    arguments = _arguments()
    assert arguments["messages"] == [
        {
            "role": "system",
            "content": (
                "Return only JSON matching the supplied strict schema."
            ),
        },
        {
            "role": "user",
            "content": json.dumps(
                _packet()["synthetic_input"],
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        },
    ]


def test_response_schema_is_strict_and_packet_derived():
    response_format = _arguments()["response_format"]
    schema = response_format["json_schema"]["schema"]
    required = _packet()["output_schema"]["required_fields"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    assert schema == {
        "type": "object",
        "properties": {field: {} for field in required},
        "required": required,
        "additionalProperties": False,
    }


def test_canonical_local_request_size_is_bounded():
    arguments = _arguments()
    assert owner.conservative_run_003_local_input_size_bytes(arguments) <= 4096
    assert owner.conservative_run_003_local_input_size_bytes(arguments) == (
        owner.conservative_run_003_local_input_size_bytes(deepcopy(arguments))
    )


@pytest.mark.parametrize(
    ("target", "field", "value"),
    [
        ("packet", "case_alias", "case_other"),
        ("packet", "workload_id", "jd_intelligence"),
        ("packet", "provider", "openai"),
        ("packet", "model", "openai/gpt-oss-20b"),
        ("packet", "live_execution_requested", True),
        ("packet", "fallback", True),
        ("row", "case_alias", "case_other"),
        ("row", "workload_id", "tailoring_generation"),
        ("row", "provider", "gemini"),
        ("row", "model", "openai/gpt-oss-20b"),
        ("row", "fallback", True),
        ("row", "harness_retry_limit", 1),
        ("row", "provider_sdk_retry_limit", 1),
    ],
)
def test_packet_or_row_scope_mutation_is_rejected(target, field, value):
    packet = _packet()
    row = _row()
    (packet if target == "packet" else row)[field] = value
    with pytest.raises(ValueError):
        owner.build_run_003_groq_chat_completion_arguments(
            packet=packet,
            scheduled=row,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("model", "openai/gpt-oss-20b"),
        ("messages", []),
        ("temperature", 1),
        ("max_completion_tokens", 2048),
        ("stream", True),
        ("n", 2),
        ("response_format", {}),
    ],
)
def test_chat_argument_mutation_is_rejected(field, value):
    arguments = _arguments()
    arguments[field] = value
    with pytest.raises(ValueError):
        owner.validate_run_003_groq_chat_completion_arguments(
            arguments,
            packet=_packet(),
            scheduled=_row(),
        )


@pytest.mark.parametrize(
    "field",
    [
        "tools",
        "mcp",
        "metadata",
        "request_id",
        "headers",
        "credential",
        "expected_output",
        "grader",
        "production_state",
        "application_state",
        "ats_state",
    ],
)
def test_extra_chat_fields_are_rejected(field):
    arguments = _arguments()
    arguments[field] = {}
    with pytest.raises(ValueError):
        owner.validate_run_003_groq_chat_completion_arguments(
            arguments,
            packet=_packet(),
            scheduled=_row(),
        )


def test_execute_requires_explicit_client_and_clock():
    with pytest.raises(ValueError):
        owner.execute_run_003_groq_chat_completion_once(
            client=None,
            packet=_packet(),
            scheduled=_row(),
            monotonic_clock=_clock(),
        )
    with pytest.raises(ValueError):
        owner.execute_run_003_groq_chat_completion_once(
            client=FakeClient(),
            packet=_packet(),
            scheduled=_row(),
            monotonic_clock=None,
        )


def test_execute_invokes_fake_sdk_exactly_once_and_reduces_response():
    client = FakeClient()
    result = owner.execute_run_003_groq_chat_completion_once(
        client=client,
        packet=_packet(),
        scheduled=_row(),
        monotonic_clock=_clock(),
    )
    assert len(client.chat.completions.calls) == 1
    assert client.chat.completions.calls[0] == _arguments()
    assert set(result) == {
        "normalized_output",
        "provider",
        "model",
        "latency_ms",
        "input_token_count",
        "output_token_count",
        "provider_outcome_category",
    }
    assert result["latency_ms"] == 125.0
    assert result["provider_outcome_category"] == "success"


def test_reduced_result_retains_no_raw_envelope_fields():
    result = owner.execute_run_003_groq_chat_completion_once(
        client=FakeClient(),
        packet=_packet(),
        scheduled=_row(),
        monotonic_clock=_clock(),
    )
    serialized = json.dumps(result).lower()
    for prohibited in (
        "choices",
        "usage",
        "request_id",
        "headers",
        "reasoning",
        "raw_response",
    ):
        assert prohibited not in serialized


class AuthenticationError(Exception):
    status_code = 401


class ConnectionErrorForTest(Exception):
    pass


class UnknownFailureForTest(Exception):
    pass


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (TimeoutError(), owner.AmbiguousTransportTimeout),
        (AuthenticationError(), owner.DefinitiveTransportFailure),
        (ConnectionErrorForTest(), owner.DefinitiveTransportFailure),
        (UnknownFailureForTest(), owner.UnknownProviderOutcome),
    ],
)
def test_fake_errors_preserve_bounded_exception_classes(error, expected):
    client = FakeClient(error=error)
    with pytest.raises(expected):
        owner.execute_run_003_groq_chat_completion_once(
            client=client,
            packet=_packet(),
            scheduled=_row(),
            monotonic_clock=_clock(),
        )
    assert len(client.chat.completions.calls) == 1


@pytest.mark.parametrize(
    "response",
    [
        {"model": "openai/gpt-oss-120b", "choices": [], "usage": {}},
        {
            "model": "openai/gpt-oss-20b",
            "choices": [{"message": {"content": "{}"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        },
        {
            "model": "openai/gpt-oss-120b",
            "choices": [{"message": {"content": "not-json"}}],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1},
        },
    ],
)
def test_malformed_fake_response_is_bounded_failure(response):
    with pytest.raises(owner.DefinitiveTransportFailure):
        owner.execute_run_003_groq_chat_completion_once(
            client=FakeClient(response=response),
            packet=_packet(),
            scheduled=_row(),
            monotonic_clock=_clock(),
        )


def test_contract_mutation_is_rejected():
    contract = owner.build_run_003_transport_contract()
    contract["authority_invariants"]["provider_calls_allowed"] = True
    with pytest.raises(ValueError):
        owner.validate_run_003_transport_contract(contract)


def test_import_owner_has_no_sdk_environment_network_database_or_write_reach():
    tree = ast.parse(OWNER_PATH.read_text(encoding="utf-8"))
    roots = set()
    calls = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            roots.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            calls.add(node.func.id)
    assert roots.isdisjoint(
        {
            "dotenv",
            "groq",
            "httpx",
            "openai",
            "os",
            "psycopg",
            "requests",
            "socket",
            "sqlalchemy",
            "subprocess",
            "threading",
            "urllib",
        }
    )
    assert calls.isdisjoint({"open", "Popen", "Thread", "Process"})


def test_fake_execution_reaches_no_environment_socket_or_write(monkeypatch):
    def fail(*_args, **_kwargs):
        raise AssertionError("environment, network, or write access prohibited")

    monkeypatch.setattr(os, "getenv", fail)
    monkeypatch.setattr(socket, "create_connection", fail)
    monkeypatch.setattr(socket.socket, "connect", fail)
    monkeypatch.setattr(Path, "write_text", fail)
    monkeypatch.setattr(Path, "write_bytes", fail)
    result = owner.execute_run_003_groq_chat_completion_once(
        client=FakeClient(),
        packet=_packet(),
        scheduled=_row(),
        monotonic_clock=_clock(),
    )
    assert result["provider_outcome_category"] == "success"


def test_pinned_owners_and_runtime_artifacts_are_hermetic():
    assert plan.run_003_plan_sha256() == PLAN_SHA
    assert identity.run_003_identity_sha256() == IDENTITY_SHA
    assert all(
        not (ROOT / relative_path).exists()
        for relative_path in identity.RUN_003_ARTIFACT_PATHS.values()
    )
