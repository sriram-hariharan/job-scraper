from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.app.services import (
    jd_live_provider_canary_readback_service_payload,
)


ROOT = Path(__file__).resolve().parents[1]


def _successful_readback():
    return {
        "readback_enabled": True,
        "readback_status": "jd_live_canary_readback_succeeded",
        "canary_configured": True,
        "canary_allowed": True,
        "canary_attempted": True,
        "provider_call_attempted": True,
        "provider_call_succeeded": True,
        "provider_call_failed": False,
        "fallback_used": False,
        "fallback_reason": "",
        "structured_output_validated": True,
        "shadow_only": True,
        "provider_name": "fixture-provider",
        "model_name": "fixture-model",
        "prompt_version": "jd-canary-prompt-v1",
        "runtime_version": "jd-canary-runtime-v1",
        "llmops_metadata_present": True,
        "latency_ms": 15,
        "input_tokens": 20,
        "output_tokens": 8,
        "total_tokens": 28,
        "estimated_cost": 0.004,
        "mutation_authorized": False,
        "mutation_authorized_agent_count": 0,
        "influence_disabled": {
            "scoring": True,
            "ranking": True,
            "queue": True,
            "resume": True,
            "execution": True,
            "submission": True,
        },
        "next_safe_step": "audit_shadow_canary_before_any_expansion",
        "safety_metadata": {
            "read_only": True,
            "advisory_only": True,
            "readback_only": True,
            "shadow_only": True,
        },
    }


def _direct_canary(**updates):
    payload = {
        "canary_status": "jd_live_canary_succeeded_shadow_only",
        "canary_enabled": True,
        "canary_allowed": True,
        "canary_attempted": True,
        "provider_call_attempted": True,
        "provider_call_succeeded": True,
        "provider_call_failed": False,
        "fallback_used": False,
        "fallback_reason": "",
        "structured_output_validated": True,
        "shadow_only": True,
        "provider_name": "fixture-provider",
        "model_name": "fixture-model",
        "prompt_version": "jd-canary-prompt-v1",
        "runtime_version": "jd-canary-runtime-v1",
        "llmops_metadata": {
            "model_provider": "fixture-provider",
            "model_name": "fixture-model",
            "prompt_version": "jd-canary-prompt-v1",
            "runtime_version": "jd-canary-runtime-v1",
            "provider_call_attempted": True,
            "provider_call_made": True,
            "provider_call_succeeded": True,
            "fallback_used": False,
            "schema_validation_status": "valid",
            "latency_ms": 15,
            "input_tokens": 20,
            "output_tokens": 8,
            "total_tokens": 28,
            "estimated_cost": 0.004,
        },
        "jd_intelligence_output": {
            "validation_status": "valid",
            "validation_errors": [],
            "fallback_used": False,
        },
        "safety_metadata": {"shadow_only": True},
    }
    payload.update(updates)
    return payload


def _assert_safe(payload):
    safety = payload["safety_metadata"]
    assert payload["service_surface"] == (
        "jd_live_provider_canary_readback_service"
    )
    assert payload["service_helper_only"] is True
    assert payload["review_packet_compatible"] is True
    assert payload["mutation_authorized"] is False
    assert payload["mutation_authorized_agent_count"] == 0
    assert all(payload["influence_disabled"].values())
    for key in (
        "read_only",
        "advisory_only",
        "readback_only",
        "shadow_only",
        "service_helper_only",
    ):
        assert safety[key] is True
    for key in (
        "provider_calls_made",
        "network_calls_made",
        "environment_secrets_read",
        "embeddings_created",
        "did_read_database",
        "did_write_database",
        "did_write_files",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_create_approval",
        "did_mutate_resume",
        "did_create_execution_request",
        "did_execute_application",
        "did_submit_application",
    ):
        assert safety[key] is False


def test_missing_metadata_returns_default_off_service_readback():
    default = jd_live_provider_canary_readback_service_payload()
    no_data = jd_live_provider_canary_readback_service_payload(
        enabled=True
    )

    assert default["readback_status"] == (
        "jd_live_canary_readback_skipped_default_off"
    )
    assert default["default_off"] is True
    assert no_data["readback_status"] == (
        "jd_live_canary_readback_no_data"
    )
    assert no_data["default_off"] is False
    assert no_data["canary_configured"] is False
    _assert_safe(default)
    _assert_safe(no_data)


def test_existing_review_packet_canary_readback_is_surfaced_unchanged():
    summary = _successful_readback()
    packet = {"jd_live_provider_canary_readback": deepcopy(summary)}
    before = deepcopy(packet)

    result = jd_live_provider_canary_readback_service_payload(
        enabled=True,
        review_packet_payload=packet,
    )

    assert packet == before
    for key in (
        "readback_status",
        "canary_configured",
        "canary_attempted",
        "provider_call_succeeded",
        "structured_output_validated",
        "provider_name",
        "model_name",
        "prompt_version",
        "runtime_version",
        "latency_ms",
        "total_tokens",
        "estimated_cost",
        "next_safe_step",
    ):
        assert result[key] == summary[key]
    _assert_safe(result)


def test_fallback_metadata_is_normalized_and_surfaced():
    payload = _direct_canary(
        canary_status="jd_live_canary_fallback",
        provider_call_succeeded=False,
        provider_call_failed=True,
        fallback_used=True,
        fallback_reason="required_skills_not_list",
        structured_output_validated=False,
        llmops_metadata={
            "provider_call_attempted": True,
            "provider_call_made": True,
            "provider_call_succeeded": False,
            "fallback_used": True,
            "schema_validation_status": "invalid",
            "error_type": "StructuredOutputValidationError",
        },
        jd_intelligence_output={
            "validation_status": "fallback",
            "validation_errors": ["required_skills_not_list"],
            "fallback_used": True,
        },
    )

    result = jd_live_provider_canary_readback_service_payload(
        enabled=True,
        payload=payload,
    )

    assert result["readback_status"] == (
        "jd_live_canary_readback_fallback"
    )
    assert result["provider_call_attempted"] is True
    assert result["provider_call_failed"] is True
    assert result["fallback_used"] is True
    assert result["fallback_reason"] == "required_skills_not_list"
    _assert_safe(result)


def test_successful_canary_metadata_and_llmops_are_surfaced():
    result = jd_live_provider_canary_readback_service_payload(
        enabled=True,
        payload=_direct_canary(),
    )

    assert result["readback_status"] == (
        "jd_live_canary_readback_succeeded"
    )
    assert result["canary_configured"] is True
    assert result["canary_attempted"] is True
    assert result["provider_call_attempted"] is True
    assert result["provider_call_succeeded"] is True
    assert result["structured_output_validated"] is True
    assert result["shadow_only"] is True
    assert result["provider_name"] == "fixture-provider"
    assert result["model_name"] == "fixture-model"
    assert result["prompt_version"] == "jd-canary-prompt-v1"
    assert result["runtime_version"] == "jd-canary-runtime-v1"
    assert result["latency_ms"] == 15
    assert result["input_tokens"] == 20
    assert result["output_tokens"] == 8
    assert result["total_tokens"] == 28
    assert result["estimated_cost"] == 0.004
    _assert_safe(result)


def test_service_delegates_only_to_readback_builder_without_execution():
    calls = []
    source = {"already_existing": "metadata"}
    before = deepcopy(source)

    def builder(**kwargs):
        calls.append(deepcopy(kwargs))
        return _successful_readback()

    result = jd_live_provider_canary_readback_service_payload(
        enabled=True,
        payload=source,
        readback_builder=builder,
    )

    assert source == before
    assert calls == [{"payload": before, "enabled": True}]
    assert result["readback_status"] == (
        "jd_live_canary_readback_succeeded"
    )
    _assert_safe(result)


def test_service_helper_has_no_canary_adapter_env_network_or_mutation_calls():
    source = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
    start = source.index(
        "def jd_live_provider_canary_readback_service_payload("
    )
    end = source.index(
        "\ndef vector_evidence_readback_service_helper_payload(",
        start,
    )
    snippet = source[start:end].lower()

    assert "build_jd_live_provider_canary_readback" in snippet
    for marker in (
        "run_jd_live_provider_canary(",
        "run_provider_runtime_adapter(",
        "provider_adapter(",
        "provider_client(",
        "provider_client.invoke(",
        "from openai",
        "import openai",
        "anthropic",
        "langchain",
        "os.getenv",
        "os.environ",
        "requests.",
        "httpx",
        "urllib",
        "socket",
        "create_embedding(",
        "database_url",
        "connect(",
        "cursor.execute",
        ".commit(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in snippet


def test_api_ui_pipeline_and_dependencies_are_unchanged():
    expected = {
        "requirements.txt": (
            "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"
        ),
        "src/app/api.py": (
            "9fd96dad2edce8c1ff41f5d239801cbab071ed939104a55d7322a91a3526bbf3"
        ),
        "src/app/static/agentic_review.js": (
            "54980b376269262288c613d9048129b0e1192810870866852e89d391a50fea7f"
        ),
        "src/pipeline/collector.py": (
            "cbcd90f3d8d367ebe6f178c211406da909f340ce62681047b70efe4fb4a30fa7"
        ),
        "src/pipeline/application_scorer.py": (
            "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"
        ),
        "src/pipeline/job_ranker.py": (
            "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"
        ),
        "application_execution_queue.py": (
            "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"
        ),
    }

    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
