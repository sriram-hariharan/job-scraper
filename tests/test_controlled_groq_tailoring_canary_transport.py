from __future__ import annotations

import ast
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest

from src.evaluation import controlled_groq_canary_transport as generic
from src.evaluation import controlled_groq_tailoring_canary_transport as transport
from src.evaluation import controlled_tailoring_benchmark_request_adapter as adapter
from src.evaluation.controlled_groq_provider_canary import (
    build_controlled_groq_canary_contract,
)
from src.evaluation.controlled_provider_benchmark_harness import (
    DefinitiveTransportFailure,
    TRANSPORT_RESULT_FIELDS,
)
from src.evaluation.controlled_provider_benchmark_plan import (
    build_controlled_provider_benchmark_plan,
    build_transmittable_request_packet,
)


ROOT = Path(__file__).resolve().parents[1]
OWNER = (
    ROOT
    / "src/evaluation/controlled_groq_tailoring_canary_transport.py"
)
GENERIC_SHA = (
    "e27ad7f7eccf67837cde2b940c448042953abe16749378b0f353d6e503180209"
)
PROTECTED_FILE_SHAS = {
    "src/app/services.py": (
        "8fdd9eb765fef33d6855a2992c4a5e12aa48c97d055fd41b26076034833a98c6"
    ),
    "src/agents/tailoring_decision_agent.py": (
        "8937816651d96e6f5b475a4fc99285ff0a80443269dd1a0359b94fc6f599921e"
    ),
    "src/ai/llm_client.py": (
        "830866d616c8d2d5d6b2147cd6a17b19f049f8a064592d78c2b7170d4e49ffc2"
    ),
    "src/evaluation/controlled_groq_canary_transport.py": (
        "7df9dfcff70197c84a665a0d9f101b1ca4ce74322ea580c60f4e33a8cdf8a7d3"
    ),
}


def _plan():
    return build_controlled_provider_benchmark_plan()


def _scheduled():
    return next(
        deepcopy(row)
        for row in build_controlled_groq_canary_contract()["schedule"]
        if row["workload_id"] == "tailoring_generation"
        and row["provider"] == "groq"
        and row["model"] == "openai/gpt-oss-120b"
    )


def _packet():
    plan = _plan()
    row = _scheduled()
    return build_transmittable_request_packet(
        case_alias=row["case_alias"],
        provider=row["provider"],
        model=row["model"],
        plan=plan,
        live_execution_requested=False,
    )


def _valid_output():
    return {
        "suggestions": [
            {
                "suggestion_id": "suggestion_001",
                "source_bullet_id": "bullet_alpha",
                "claims": ["python"],
                "evidence_tokens": ["python"],
            }
        ],
        "human_review_required": True,
        "authority_mutated": False,
    }


def _response(output=None, **overrides):
    payload = {
        "model": "openai/gpt-oss-120b",
        "choices": [
            SimpleNamespace(
                message=SimpleNamespace(
                    content=json.dumps(
                        _valid_output() if output is None else output,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                )
            )
        ],
        "usage": SimpleNamespace(prompt_tokens=31, completion_tokens=17),
        "id": "raw-id-not-returned",
        "headers": {"raw": "not-returned"},
        "reasoning": "not-returned",
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


def _clock():
    values = iter((10.0, 10.125))
    return lambda: next(values)


def _execute(output=None):
    client = FakeClient(_response(output))
    packet = _packet()
    scheduled = _scheduled()
    result = transport.execute_groq_tailoring_chat_completion_once(
        client=client,
        packet=packet,
        scheduled=scheduled,
        monotonic_clock=_clock(),
        plan=_plan(),
    )
    return result, client


def test_transport_contract_version_fields_bindings_target_and_authority_are_exact():
    contract = transport.build_controlled_groq_tailoring_transport_contract()

    assert contract["transport_version"] == (
        "controlled-groq-tailoring-canary-transport-v1"
    )
    assert set(contract) == {
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
    assert contract["tailoring_adapter"] == {
        "version": adapter.ADAPTER_VERSION,
        "sha256": adapter.controlled_tailoring_request_adapter_sha256(),
    }
    assert contract["generic_transport"] == {
        "version": generic.TRANSPORT_VERSION,
        "sha256": GENERIC_SHA,
    }
    assert contract["target"] == {
        "workload_id": "tailoring_generation",
        "provider": "groq",
        "model": "openai/gpt-oss-120b",
    }
    assert contract["authority_invariants"] == {
        "live_execution_authorized": False,
        "production_activation": False,
        "routing_authority": False,
        "mutation_count": 0,
        "application_action_count": 0,
        "ats_action_count": 0,
        "automatic_runner": False,
    }


def test_transport_digest_is_deterministic_deep_copy_contained_and_fresh_process_stable():
    contract = transport.build_controlled_groq_tailoring_transport_contract()
    original = deepcopy(contract)
    digest = transport.controlled_groq_tailoring_transport_sha256(contract)

    assert transport.controlled_groq_tailoring_transport_sha256(contract) == digest
    assert contract == original
    contract["authority_invariants"]["production_activation"] = True
    assert (
        transport.build_controlled_groq_tailoring_transport_contract()
        == original
    )
    code = (
        "from src.evaluation."
        "controlled_groq_tailoring_canary_transport import "
        "controlled_groq_tailoring_transport_sha256;"
        "print(controlled_groq_tailoring_transport_sha256())"
    )
    completed = subprocess.run(
        [sys.executable, "-c", code],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert completed.stdout.strip() == digest


def test_generic_transport_digest_remains_pinned():
    assert generic.controlled_groq_transport_sha256() == GENERIC_SHA


def test_chat_arguments_are_exact_typed_tailoring_specific_and_bounded():
    arguments = transport.build_groq_tailoring_chat_completion_arguments(
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
    assert arguments["model"] == "openai/gpt-oss-120b"
    assert arguments["temperature"] == 0
    assert arguments["max_completion_tokens"] == 1024
    assert arguments["stream"] is False
    assert arguments["n"] == 1
    assert [item["role"] for item in arguments["messages"]] == [
        "system",
        "user",
    ]
    assert "evidence-backed" in arguments["messages"][0]["content"]
    user = json.loads(arguments["messages"][1]["content"])
    assert set(user) == {
        "task_identifier",
        "source_bullet_ids",
        "evidence_tokens",
        "requirements",
    }
    response_format = arguments["response_format"]
    assert response_format["type"] == "json_schema"
    assert response_format["json_schema"]["strict"] is True
    schema = response_format["json_schema"]["schema"]
    assert schema["properties"]["suggestions"]["minItems"] == 1
    assert (
        generic.conservative_local_input_size_bytes(arguments) <= 4096
    )


def test_contract_pins_zero_retry_fallback_and_exact_timeout_serial_bounds():
    request = transport.build_controlled_groq_tailoring_transport_contract()[
        "request_contract"
    ]

    assert request["timeout_seconds"] == 30
    assert request["serial_concurrency"] == 1
    assert request["retry_count"] == 0
    assert request["fallback"] is False


def test_explicit_injected_client_and_clock_are_required():
    with pytest.raises(ValueError, match="explicit client"):
        transport.execute_groq_tailoring_chat_completion_once(
            client=None,
            packet=_packet(),
            scheduled=_scheduled(),
            monotonic_clock=_clock(),
            plan=_plan(),
        )
    with pytest.raises(ValueError, match="clock"):
        transport.execute_groq_tailoring_chat_completion_once(
            client=FakeClient(_response()),
            packet=_packet(),
            scheduled=_scheduled(),
            monotonic_clock=None,
            plan=_plan(),
        )


def test_fake_client_is_called_once_and_returns_only_bounded_fields():
    result, client = _execute()

    assert len(client.completions.calls) == 1
    assert set(result) == set(TRANSPORT_RESULT_FIELDS)
    assert result["normalized_output"] == _valid_output()
    assert result["provider"] == "groq"
    assert result["model"] == "openai/gpt-oss-120b"
    assert result["latency_ms"] == 125.0
    assert result["input_token_count"] == 31
    assert result["output_token_count"] == 17
    serialized = json.dumps(result, sort_keys=True)
    for raw_value in ("raw-id-not-returned", "not-returned"):
        assert raw_value not in serialized


@pytest.mark.parametrize(
    "mutation",
    [
        lambda output: output.update(suggestions=[]),
        lambda output: output.update(human_review_required=False),
        lambda output: output.update(authority_mutated=True),
        lambda output: output["suggestions"][0].update(
            source_bullet_id="invented_source"
        ),
        lambda output: output["suggestions"][0].update(
            claims=["invented_claim"]
        ),
        lambda output: output["suggestions"][0].update(
            evidence_tokens=["invented_evidence"]
        ),
    ],
)
def test_semantically_invalid_fake_responses_are_rejected(mutation):
    output = _valid_output()
    mutation(output)
    client = FakeClient(_response(output))

    with pytest.raises(
        DefinitiveTransportFailure,
        match="^tailoring_response_contract_invalid$",
    ) as exc_info:
        transport.execute_groq_tailoring_chat_completion_once(
            client=client,
            packet=_packet(),
            scheduled=_scheduled(),
            monotonic_clock=_clock(),
            plan=_plan(),
        )

    assert len(client.completions.calls) == 1
    assert "invented_" not in str(exc_info.value)


@pytest.mark.parametrize(
    ("response", "category"),
    [
        (
            SimpleNamespace(
                model="openai/gpt-oss-120b",
                choices=[],
                usage=SimpleNamespace(
                    prompt_tokens=1,
                    completion_tokens=1,
                ),
            ),
            "malformed_choice_count",
        ),
        (
            SimpleNamespace(
                model="openai/gpt-oss-120b",
                choices=[
                    SimpleNamespace(
                        message=SimpleNamespace(content="{not-json")
                    )
                ],
                usage=SimpleNamespace(
                    prompt_tokens=1,
                    completion_tokens=1,
                ),
            ),
            "malformed_json_content",
        ),
    ],
)
def test_malformed_response_outcomes_remain_bounded(response, category):
    client = FakeClient(response)

    with pytest.raises(DefinitiveTransportFailure, match=f"^{category}$"):
        transport.execute_groq_tailoring_chat_completion_once(
            client=client,
            packet=_packet(),
            scheduled=_scheduled(),
            monotonic_clock=_clock(),
            plan=_plan(),
        )


def test_exception_text_is_not_retained_and_classifier_is_reused():
    class BadRequestError(RuntimeError):
        status_code = 400

    client = FakeClient(BadRequestError("secret generated detail"))
    with pytest.raises(
        DefinitiveTransportFailure,
        match="^definitive_invalid_request$",
    ) as exc_info:
        transport.execute_groq_tailoring_chat_completion_once(
            client=client,
            packet=_packet(),
            scheduled=_scheduled(),
            monotonic_clock=_clock(),
            plan=_plan(),
        )

    assert "secret generated detail" not in str(exc_info.value)
    assert (
        generic.classify_sdk_exception(BadRequestError("ignored"))
        == "definitive_invalid_request"
    )


def test_arguments_packet_and_schedule_are_not_mutated():
    packet = _packet()
    scheduled = _scheduled()
    plan = _plan()
    packet_before = deepcopy(packet)
    scheduled_before = deepcopy(scheduled)
    plan_before = deepcopy(plan)

    arguments = transport.build_groq_tailoring_chat_completion_arguments(
        packet=packet,
        scheduled=scheduled,
        plan=plan,
    )
    arguments_before = deepcopy(arguments)
    result, _client = _execute()

    assert packet == packet_before
    assert scheduled == scheduled_before
    assert plan == plan_before
    assert arguments == arguments_before
    assert set(result) == set(TRANSPORT_RESULT_FIELDS)


def test_module_has_no_sdk_environment_process_thread_network_database_or_write_boundary():
    tree = ast.parse(OWNER.read_text(encoding="utf-8"))
    imports = {
        node.module
        for node in tree.body
        if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name
        for node in tree.body
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    source = OWNER.read_text(encoding="utf-8")

    assert not any(
        name.startswith(
            (
                "groq",
                "dotenv",
                "os",
                "socket",
                "subprocess",
                "threading",
                "multiprocessing",
                "src.app",
                "src.ai",
                "src.storage",
            )
        )
        for name in imports
    )
    for prohibited in (
        "getenv",
        "os.environ",
        "open(",
        "write_text",
        "write_bytes",
        "mkdir(",
        "create_live_groq_client",
    ):
        assert prohibited not in source


def test_no_future_run_owner_or_artifact_and_protected_behavior_is_unchanged():
    future_marker = "00" + "6"
    tracked = [
        path.relative_to(ROOT).as_posix()
        for base in (ROOT / "src", ROOT / "tests")
        for path in base.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    ]
    outputs = [
        path.name
        for path in (ROOT / "outputs/provider_benchmark").glob("*")
        if path.is_file()
    ]

    assert not any(future_marker in path for path in tracked)
    assert not any(future_marker in name for name in outputs)
    for relative, expected in PROTECTED_FILE_SHAS.items():
        assert sha256((ROOT / relative).read_bytes()).hexdigest() == expected
