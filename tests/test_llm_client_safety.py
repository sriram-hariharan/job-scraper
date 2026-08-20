from __future__ import annotations

import inspect
import json
from pathlib import Path

import groq
import httpx
import pytest

from src.evaluation.provider_client_compatibility import (
    _FakeMessage,
    _FakeSdkClient,
    _isolated_shared_client,
)


ROOT = Path(__file__).resolve().parents[1]
CLIENT_PATH = ROOT / "src/ai/llm_client.py"
RUNTIME_OWNER_PATHS = (
    CLIENT_PATH,
    ROOT / "src/app/services.py",
    ROOT / "src/agents/llm_adjudicator_readback.py",
    ROOT / "src/pipeline/collector.py",
    ROOT / "src/app/static/planning.js",
)

KNOWN_PAIRS = (
    ("groq", "llama-3.1-8b-instant"),
    ("groq", "llama-3.3-70b-versatile"),
    ("groq", "openai/gpt-oss-20b"),
    ("groq", "openai/gpt-oss-120b"),
    ("openai", "gpt-5-mini"),
    ("openai", "gpt-5.1"),
)


@pytest.fixture
def client_module():
    with _isolated_shared_client() as (module, isolation):
        yield module, isolation


def _install_fake(module, provider, message):
    fake = _FakeSdkClient([message])
    setattr(module, f"_{provider}_client", fake)
    return fake


def _install_capturing_fake(module, provider, message):
    fake = _install_fake(module, provider, message)
    captured = []
    create = fake.chat.completions.create

    def capture_create(**kwargs):
        captured.append(kwargs)
        return create(**kwargs)

    fake.chat.completions.create = capture_create
    return captured


def _run_empty(module, provider, model, message):
    _install_fake(module, provider, message)
    runner = getattr(module, f"_run_{provider}_chat_completion")
    return runner(
        messages=[{"role": "user", "content": "bounded synthetic input"}],
        model=model,
        temperature=0,
        max_tokens=32,
        response_mime_type="application/json",
        response_schema={"type": "object"},
        return_parsed=True,
    )


@pytest.mark.parametrize(
    "model",
    (
        "gpt-5-mini",
        "gpt-5-mini-2025-08-07",
    ),
)
def test_gpt_5_mini_zero_budget_maps_to_minimal_reasoning_without_temperature(
    client_module,
    model,
):
    module, _ = client_module
    captured = _install_capturing_fake(
        module,
        "openai",
        _FakeMessage('{"status":"ok"}'),
    )
    module.reset_provider_metrics()
    messages = [{"role": "user", "content": "bounded"}]
    schema = {
        "type": "object",
        "properties": {"status": {"type": "string"}},
        "required": ["status"],
        "additionalProperties": False,
    }

    result = module._run_openai_chat_completion(
        messages=messages,
        model=model,
        temperature=0,
        max_tokens=520,
        response_mime_type="application/json",
        response_schema=schema,
        return_parsed=True,
        thinking_budget=0,
    )

    assert result == {"status": "ok"}
    assert len(captured) == 1
    request = captured[0]
    assert "temperature" not in request
    assert request["reasoning_effort"] == "minimal"
    assert request["model"] == model
    assert request["messages"] == messages
    assert request["max_completion_tokens"] == 520
    assert request["response_format"] == {
        "type": "json_schema",
        "json_schema": {
            "name": "structured_output",
            "strict": True,
            "schema": schema,
        },
    }
    assert module.get_provider_metrics() == {
        "primary_attempts": 0,
        "fallback_attempts": 0,
        "groq_calls": 0,
        "openai_calls": 1,
        "gemini_calls": 0,
        "fallback_successes": 0,
        "provider_failures": 0,
    }


@pytest.mark.parametrize(
    ("model", "temperature", "thinking_budget"),
    (
        ("gpt-5.1", 0.25, 0),
        ("gpt-5-mini", 1, None),
        ("gpt-5-mini", 1, 64),
    ),
)
def test_other_openai_reasoning_intents_and_supported_temperatures_are_unchanged(
    client_module,
    model,
    temperature,
    thinking_budget,
):
    module, _ = client_module
    captured = _install_capturing_fake(
        module,
        "openai",
        _FakeMessage("bounded success"),
    )

    result = module._run_openai_chat_completion(
        messages=[{"role": "user", "content": "bounded"}],
        model=model,
        temperature=temperature,
        max_tokens=32,
        thinking_budget=thinking_budget,
    )

    assert result == "bounded success"
    assert captured[0]["temperature"] == temperature
    assert "reasoning_effort" not in captured[0]


@pytest.mark.parametrize(
    ("provider", "model"),
    (
        ("groq", "openai/gpt-oss-20b"),
        ("openai", "gpt-5-mini"),
    ),
)
def test_empty_content_emits_no_output_or_raw_data(
    client_module,
    capsys,
    provider,
    model,
):
    module, _ = client_module
    message = _FakeMessage(
        None,
        refusal="bounded-refusal-body-must-not-appear",
        reasoning="bounded-reasoning-body-must-not-appear",
        marker="bounded-raw-marker-must-not-appear",
    )

    with pytest.raises(RuntimeError) as exc_info:
        _run_empty(module, provider, model, message)

    captured = capsys.readouterr()
    rendered = str(exc_info.value)
    assert captured.out == ""
    assert captured.err == ""
    assert "bounded-refusal-body-must-not-appear" not in rendered
    assert "bounded-reasoning-body-must-not-appear" not in rendered
    assert "bounded-raw-marker-must-not-appear" not in rendered
    assert "refusal_present=true" in rendered
    if provider == "groq":
        assert "reasoning_present=true" in rendered


def test_empty_response_owner_has_no_raw_dump_or_debug_print():
    source = CLIENT_PATH.read_text(encoding="utf-8")
    assert "raw message dump" not in source
    assert "message.model_dump()" not in source
    assert "[GROQ DEBUG]" not in source
    assert "[OPENAI DEBUG]" not in source


@pytest.mark.parametrize(("provider", "model"), KNOWN_PAIRS)
def test_every_known_matching_pair_passes(client_module, provider, model):
    module, _ = client_module
    assert module._normalize_and_validate_provider_model(provider, model) == (
        provider,
        model,
    )


@pytest.mark.parametrize(
    ("provider", "model"),
    (
        ("groq", "gpt-5-mini"),
        ("groq", "gpt-5.1"),
        ("openai", "openai/gpt-oss-20b"),
        ("openai", "openai/gpt-oss-120b"),
    ),
)
def test_known_provider_model_mismatches_fail_closed(
    client_module,
    provider,
    model,
):
    module, _ = client_module
    with pytest.raises(ValueError) as exc_info:
        module._normalize_and_validate_provider_model(provider, model)
    assert getattr(exc_info.value, "error_category") == "provider_model_mismatch"


@pytest.mark.parametrize(
    ("provider", "model", "category"),
    (
        ("", "gpt-5-mini", "unsupported_provider"),
        ("openai", "", "configuration"),
        ("unsupported", "custom-model", "unsupported_provider"),
        ("gemini", "custom-model", "unsupported_provider"),
    ),
)
def test_missing_or_unsupported_identity_fails_closed(
    client_module,
    provider,
    model,
    category,
):
    module, _ = client_module
    with pytest.raises(ValueError) as exc_info:
        module._normalize_and_validate_provider_model(provider, model)
    assert getattr(exc_info.value, "error_category") == category


@pytest.mark.parametrize("provider", ("groq", "openai"))
def test_unknown_custom_model_remains_supported(client_module, provider):
    module, _ = client_module
    assert module._normalize_and_validate_provider_model(
        provider,
        "operator-custom-model",
    ) == (provider, "operator-custom-model")


def test_rejected_primary_pair_prevents_metrics_clients_and_calls(client_module):
    module, isolation = client_module
    calls = []
    module._run_single_provider = lambda **kwargs: calls.append(kwargs)
    module.reset_provider_metrics()

    with pytest.raises(ValueError):
        module.run_chat_completion_with_metadata(
            messages=[],
            provider="groq",
            model="gpt-5-mini",
            fallback_enabled=False,
        )

    assert calls == []
    assert all(value == 0 for value in module.get_provider_metrics().values())
    assert sum(isolation["provider_client_constructions"].values()) == 0


def test_gemini_primary_is_rejected_before_provider_invocation(client_module):
    module, isolation = client_module
    calls = []
    module._run_single_provider = lambda **kwargs: calls.append(kwargs)
    module.reset_provider_metrics()

    with pytest.raises(ValueError) as exc_info:
        module.run_chat_completion_with_metadata(
            messages=[],
            provider="gemini",
            model="operator-model",
            fallback_enabled=False,
        )

    assert getattr(exc_info.value, "error_category") == "unsupported_provider"
    assert calls == []
    assert all(value == 0 for value in module.get_provider_metrics().values())
    assert sum(isolation["provider_client_constructions"].values()) == 0


def test_rejected_fallback_pair_prevents_primary_and_fallback_calls(client_module):
    module, isolation = client_module
    calls = []
    module._run_single_provider = lambda **kwargs: calls.append(kwargs)
    module.reset_provider_metrics()

    with pytest.raises(ValueError):
        module.run_chat_completion_with_metadata(
            messages=[],
            provider="groq",
            model="openai/gpt-oss-20b",
            fallback_enabled=True,
            fallback_provider="openai",
            fallback_model="openai/gpt-oss-120b",
        )

    assert calls == []
    assert all(value == 0 for value in module.get_provider_metrics().values())
    assert sum(isolation["provider_client_constructions"].values()) == 0


def test_gemini_fallback_is_rejected_before_primary_invocation(client_module):
    module, isolation = client_module
    calls = []
    module._run_single_provider = lambda **kwargs: calls.append(kwargs)
    module.reset_provider_metrics()

    with pytest.raises(ValueError) as exc_info:
        module.run_chat_completion_with_metadata(
            messages=[],
            provider="groq",
            model="openai/gpt-oss-20b",
            fallback_enabled=True,
            fallback_provider="gemini",
            fallback_model="operator-model",
        )

    assert getattr(exc_info.value, "error_category") == "unsupported_provider"
    assert calls == []
    assert all(value == 0 for value in module.get_provider_metrics().values())
    assert sum(isolation["provider_client_constructions"].values()) == 0


class _StatusError(RuntimeError):
    def __init__(self, status_code):
        self.status_code = status_code
        super().__init__("bounded synthetic status")


class _CategoryError(RuntimeError):
    def __init__(self, category):
        self.error_category = category
        super().__init__("bounded synthetic category")


def _groq_bad_request(body, *, raw_message="raw provider body must not appear"):
    request = httpx.Request(
        "POST",
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"authorization": "Bearer sk-test-must-not-appear"},
    )
    response = httpx.Response(400, request=request)
    return groq.BadRequestError(raw_message, response=response, body=body)


@pytest.mark.parametrize(
    ("error", "category"),
    (
        (TimeoutError("bounded"), "timeout"),
        (ConnectionError("bounded"), "connection"),
        (_StatusError(429), "rate_limit"),
        (_StatusError(503), "provider_5xx"),
        (_StatusError(401), "authentication"),
        (_StatusError(403), "authorization"),
        (RuntimeError("missing credential"), "configuration"),
        (_StatusError(400), "invalid_request"),
        (_CategoryError("provider_model_mismatch"), "provider_model_mismatch"),
        (json.JSONDecodeError("bounded", "", 0), "schema_or_parse"),
        (_CategoryError("refusal_or_empty_content"), "refusal_or_empty_content"),
        (_CategoryError("safety"), "safety"),
        (RuntimeError("bounded unknown"), "unknown"),
    ),
)
def test_error_taxonomy_is_exact(client_module, error, category):
    module, _ = client_module
    assert module._classify_provider_error(error) == category


@pytest.mark.parametrize(
    ("error_metadata", "expected_reason", "expected_keyword"),
    (
        (
            {"message": "Schema keyword anyOf is not supported"},
            "unsupported_schema_keyword",
            "anyOf",
        ),
        (
            {"message": "Invalid response_format configuration"},
            "response_format",
            "",
        ),
        (
            {"message": "Invalid JSON schema configuration"},
            "response_schema",
            "",
        ),
        (
            {"message": "include_reasoning is not supported"},
            "reasoning_parameter",
            "",
        ),
        (
            {"message": "max_completion_tokens exceeds the token limit"},
            "token_limit",
            "",
        ),
        (
            {"message": "private unrecognized provider detail"},
            "other_invalid_request",
            "",
        ),
    ),
)
def test_structured_groq_invalid_request_reason_classification_is_allowlisted(
    client_module,
    error_metadata,
    expected_reason,
    expected_keyword,
):
    module, _ = client_module
    body = {"error": error_metadata}

    reason, keyword = module._classify_invalid_request_reason(
        error_metadata,
        body,
    )

    assert reason == expected_reason
    assert keyword == expected_keyword


def test_structured_groq_400_metadata_is_bounded_without_raw_provider_data(
    client_module,
):
    module, _ = client_module
    raw_markers = (
        "raw provider body must not appear",
        "private prompt must not appear",
        "private failed generation must not appear",
        "sk-test-must-not-appear",
    )
    provider_error = _groq_bad_request(
        {
            "error": {
                "message": (
                    "Schema keyword anyOf is not supported; "
                    "private prompt must not appear"
                ),
                "type": "invalid_request_error",
                "code": "json_validate_failed",
                "param": "response_format",
                "failed_generation_detail": (
                    "private failed generation must not appear"
                ),
            },
            "request_payload": "private prompt must not appear",
            "api_key": "sk-test-must-not-appear",
        }
    )
    calls = []

    def dispatch(provider_name, **_kwargs):
        calls.append(provider_name)
        raise provider_error

    module._run_single_provider = dispatch
    module.reset_provider_metrics()
    with pytest.raises(RuntimeError) as exc_info:
        module.run_chat_completion_with_metadata(
            messages=[
                {"role": "user", "content": "private prompt must not appear"}
            ],
            provider="groq",
            model="openai/gpt-oss-120b",
            fallback_enabled=False,
        )

    rendered = str(exc_info.value)
    assert calls == ["groq"]
    assert rendered == (
        "LLM provider invocation failed "
        "(stage=primary, category=invalid_request, provider=groq, "
        "model=openai/gpt-oss-120b, "
        "invalid_request_reason=unsupported_schema_keyword, "
        "error_type=invalid_request_error, error_code=json_validate_failed, "
        "error_param=response_format, schema_keyword=anyOf)"
    )
    for raw_marker in raw_markers:
        assert raw_marker not in rendered
    metrics = module.get_provider_metrics()
    assert metrics["primary_attempts"] == 1
    assert metrics["fallback_attempts"] == 0
    assert metrics["provider_failures"] == 1


def test_unknown_groq_400_and_non_400_diagnostics_remain_generic(client_module):
    module, _ = client_module
    private_token = "sk-private-structured-token"
    unknown_400 = _groq_bad_request(
        {
            "error": {
                "message": f"unrecognized detail {private_token}",
                "type": private_token,
                "code": private_token,
                "param": private_token,
            }
        },
        raw_message=f"raw exception {private_token}",
    )

    diagnostic = module._bounded_invalid_request_diagnostic(
        unknown_400,
        "invalid_request",
        "groq",
    )

    assert diagnostic == {"invalid_request_reason": "other_invalid_request"}
    assert private_token not in str(diagnostic)
    assert (
        module._bounded_invalid_request_diagnostic(
            _StatusError(422),
            "invalid_request",
            "groq",
        )
        == {}
    )
    assert (
        module._bounded_invalid_request_diagnostic(
            _StatusError(503),
            "provider_5xx",
            "groq",
        )
        == {}
    )


@pytest.mark.parametrize(
    "error",
    (
        TimeoutError("bounded"),
        ConnectionError("bounded"),
        _StatusError(429),
        _StatusError(503),
    ),
)
def test_only_transient_errors_permit_one_fallback(client_module, error):
    module, _ = client_module
    calls = []

    def dispatch(provider_name, **_kwargs):
        calls.append(provider_name)
        if provider_name == "groq":
            raise error
        return "bounded fallback success"

    module._run_single_provider = dispatch
    module.reset_provider_metrics()
    payload = module.run_chat_completion_with_metadata(
        messages=[],
        provider="groq",
        model="openai/gpt-oss-20b",
        fallback_enabled=True,
        fallback_provider="openai",
        fallback_model="gpt-5-mini",
    )

    assert calls == ["groq", "openai"]
    assert payload == {
        "content": "bounded fallback success",
        "provider": "openai",
        "model": "gpt-5-mini",
        "fallback_used": True,
    }
    metrics = module.get_provider_metrics()
    assert metrics["primary_attempts"] == 1
    assert metrics["fallback_attempts"] == 1
    assert metrics["fallback_successes"] == 1
    assert metrics["provider_failures"] == 0


@pytest.mark.parametrize(
    "error",
    (
        _StatusError(401),
        _StatusError(403),
        RuntimeError("missing credential"),
        _StatusError(400),
        _CategoryError("provider_model_mismatch"),
        json.JSONDecodeError("bounded", "", 0),
        _CategoryError("refusal_or_empty_content"),
        _CategoryError("safety"),
        RuntimeError("bounded unknown"),
    ),
)
def test_non_transient_errors_make_zero_fallback_calls(client_module, error):
    module, _ = client_module
    calls = []

    def dispatch(provider_name, **_kwargs):
        calls.append(provider_name)
        raise error

    module._run_single_provider = dispatch
    module.reset_provider_metrics()
    with pytest.raises(RuntimeError) as exc_info:
        module.run_chat_completion_with_metadata(
            messages=[],
            provider="groq",
            model="openai/gpt-oss-20b",
            fallback_enabled=True,
            fallback_provider="openai",
            fallback_model="gpt-5-mini",
        )

    assert calls == ["groq"]
    assert "bounded unknown" not in str(exc_info.value)
    metrics = module.get_provider_metrics()
    assert metrics["primary_attempts"] == 1
    assert metrics["fallback_attempts"] == 0
    assert metrics["fallback_successes"] == 0
    assert metrics["provider_failures"] == 1


def test_fallback_disabled_always_makes_zero_fallback_calls(client_module):
    module, _ = client_module
    calls = []

    def dispatch(provider_name, **_kwargs):
        calls.append(provider_name)
        raise TimeoutError("bounded")

    module._run_single_provider = dispatch
    module.reset_provider_metrics()
    with pytest.raises(RuntimeError):
        module.run_chat_completion_with_metadata(
            messages=[],
            provider="groq",
            model="openai/gpt-oss-20b",
            fallback_enabled=False,
            fallback_provider="openai",
            fallback_model="gpt-5-mini",
        )
    assert calls == ["groq"]
    assert module.get_provider_metrics()["fallback_attempts"] == 0


def test_primary_success_makes_zero_fallback_calls(client_module):
    module, _ = client_module
    calls = []

    def dispatch(provider_name, **_kwargs):
        calls.append(provider_name)
        return "bounded primary success"

    module._run_single_provider = dispatch
    module.reset_provider_metrics()
    payload = module.run_chat_completion_with_metadata(
        messages=[],
        provider="groq",
        model="openai/gpt-oss-20b",
        fallback_enabled=True,
        fallback_provider="openai",
        fallback_model="gpt-5-mini",
    )
    assert calls == ["groq"]
    assert payload["fallback_used"] is False
    assert module.get_provider_metrics()["fallback_attempts"] == 0


def test_fallback_failure_is_bounded_and_non_recursive(client_module):
    module, _ = client_module
    calls = []

    def dispatch(provider_name, **_kwargs):
        calls.append(provider_name)
        if provider_name == "groq":
            raise TimeoutError("primary-body-must-not-appear")
        raise RuntimeError("fallback-body-must-not-appear")

    module._run_single_provider = dispatch
    module.reset_provider_metrics()
    with pytest.raises(RuntimeError) as exc_info:
        module.run_chat_completion_with_metadata(
            messages=[],
            provider="groq",
            model="openai/gpt-oss-20b",
            fallback_enabled=True,
            fallback_provider="openai",
            fallback_model="gpt-5-mini",
        )

    assert calls == ["groq", "openai"]
    rendered = str(exc_info.value)
    assert "primary-body-must-not-appear" not in rendered
    assert "fallback-body-must-not-appear" not in rendered
    metrics = module.get_provider_metrics()
    assert metrics["fallback_attempts"] == 1
    assert metrics["fallback_successes"] == 0
    assert metrics["provider_failures"] == 1


@pytest.mark.parametrize(
    ("provider", "model"),
    (
        ("groq", "openai/gpt-oss-20b"),
        ("openai", "gpt-5-mini"),
    ),
)
def test_successful_provider_parsing_and_metrics_remain_compatible(
    client_module,
    provider,
    model,
):
    module, _ = client_module
    _install_fake(module, provider, _FakeMessage('{"status":"ok"}'))
    module.reset_provider_metrics()
    payload = module.run_chat_completion_with_metadata(
        messages=[{"role": "user", "content": "bounded"}],
        provider=provider,
        model=model,
        response_mime_type="application/json",
        return_parsed=True,
        fallback_enabled=False,
    )
    assert payload == {
        "content": {"status": "ok"},
        "provider": provider,
        "model": model,
        "fallback_used": False,
    }
    metrics = module.get_provider_metrics()
    assert metrics["primary_attempts"] == 1
    assert metrics[f"{provider}_calls"] == 1
    assert metrics["fallback_attempts"] == 0
    assert metrics["provider_failures"] == 0


def test_public_signatures_remain_compatible_with_appended_provider_client(
    client_module,
):
    module, _ = client_module
    expected = [
        "messages",
        "model",
        "temperature",
        "max_tokens",
        "provider",
        "response_mime_type",
        "response_schema",
        "return_parsed",
        "thinking_budget",
        "fallback_enabled",
        "fallback_provider",
        "fallback_model",
        "provider_client",
    ]
    assert list(inspect.signature(module.run_chat_completion).parameters) == expected
    assert list(
        inspect.signature(module.run_chat_completion_with_metadata).parameters
    ) == expected
    assert module.DEFAULT_PROVIDER == "groq"
    assert module.DEFAULT_MODEL == "offline-placeholder-model"
    assert module.FALLBACK_ENABLED is False
    assert module.FALLBACK_PROVIDER == "openai"
    assert module.FALLBACK_MODEL == "offline-placeholder-fallback"


def test_production_runtime_has_no_callable_gemini_or_dependency():
    client_source = CLIENT_PATH.read_text(encoding="utf-8")
    runtime_source = "\n".join(
        path.read_text(encoding="utf-8") for path in RUNTIME_OWNER_PATHS
    )
    requirements = (ROOT / "requirements.txt").read_text(encoding="utf-8")

    assert '_SUPPORTED_PROVIDERS = {"groq", "openai"}' in client_source
    assert 'os.getenv("LLM_PROVIDER", "groq")' in client_source
    assert 'os.getenv("LLM_FALLBACK_PROVIDER", "openai")' in client_source
    assert 'os.getenv("LLM_FALLBACK_MODEL", "gpt-5-mini")' in client_source
    for forbidden in (
        "from google import genai",
        "from google.genai import",
        "get_gemini_client",
        "_run_gemini_chat_completion",
        "GEMINI_API_KEY",
        "gemini-2.5-flash",
    ):
        assert forbidden not in runtime_source
    assert "google-genai" not in requirements


def test_isolated_safety_tests_reach_no_external_boundary(client_module):
    _, isolation = client_module
    assert isolation["dotenv_load_count"] == 0
    assert isolation["credential_reads"] == 0
    assert sum(isolation["provider_client_constructions"].values()) == 0


def test_client_has_no_database_planning_graph_application_or_ats_wiring():
    source = CLIENT_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "database_url",
        "psycopg",
        "run_application_planning",
        "langgraph",
        "execute_application",
        "submit_application",
        "ats_action",
    ):
        assert marker not in source
