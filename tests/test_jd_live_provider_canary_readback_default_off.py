# phase56b legacy guard marker: changes_only f186703fecdda54458c468f9c2ed1de0517fa86942bb3d0fe0b522f0601fe5a8 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 f186703fecdda54458c468f9c2ed1de0517fa86942bb3d0fe0b522f0601fe5a8
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96
# phase23f legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from hashlib import sha256
from pathlib import Path

from src.agents import pipeline_agent_review_packet
from src.agents.jd_live_provider_canary_readback import (
    build_jd_live_provider_canary_readback,
)


ROOT = Path(__file__).resolve().parents[1]


def _llmops(**updates):
    payload = {
        "agent_name": "jd_intelligence",
        "agent_version": "jd-live-provider-canary-v1",
        "prompt_version": "jd-canary-prompt-v1",
        "runtime_version": "jd-canary-runtime-v1",
        "model_provider": "fixture-provider",
        "model_name": "fixture-model",
        "provider_call_attempted": True,
        "provider_call_made": True,
        "provider_call_succeeded": True,
        "fallback_used": False,
        "schema_validation_status": "valid",
        "error_type": "",
        "latency_ms": 15,
        "input_tokens": 20,
        "output_tokens": 8,
        "total_tokens": 28,
        "estimated_cost": 0.004,
    }
    payload.update(updates)
    return payload


def _direct(**updates):
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
        "llmops_metadata": _llmops(),
        "jd_intelligence_output": {
            "validation_status": "valid",
            "validation_errors": [],
            "fallback_used": False,
        },
        "safety_metadata": {
            "shadow_only": True,
            "did_mutate_scoring": False,
            "did_change_ranking": False,
            "did_mutate_queue": False,
            "did_mutate_resume": False,
            "did_execute_application": False,
            "did_submit_application": False,
        },
    }
    payload.update(updates)
    return payload


def _chain_result(*, trace=None, safety=None, output=None):
    return {
        "chain_payload": {
            "ordered_agent_results": [
                {
                    "agent_name": "jd_intelligence",
                    "llmops_trace_metadata": trace or {},
                    "safety_metadata": safety or {},
                    "agent_output_payload": output or {},
                }
            ]
        }
    }


def test_missing_metadata_returns_safe_default_off_and_no_data():
    skipped = build_jd_live_provider_canary_readback()
    no_data = build_jd_live_provider_canary_readback(enabled=True)

    assert skipped["readback_status"] == (
        "jd_live_canary_readback_skipped_default_off"
    )
    assert skipped["readback_enabled"] is False
    assert no_data["readback_status"] == (
        "jd_live_canary_readback_no_data"
    )
    assert no_data["canary_configured"] is False
    assert no_data["provider_call_attempted"] is False


def test_blocked_canary_reports_no_provider_call():
    payload = _direct(
        canary_status="jd_live_canary_blocked",
        canary_allowed=True,
        canary_attempted=False,
        provider_call_attempted=False,
        provider_call_succeeded=False,
        fallback_used=True,
        fallback_reason="missing_injected_provider_adapter",
        structured_output_validated=False,
        llmops_metadata=_llmops(
            provider_call_attempted=False,
            provider_call_made=False,
            provider_call_succeeded=False,
            fallback_used=True,
            schema_validation_status="not_executed_missing_adapter",
            error_type="MissingInjectedProviderAdapter",
        ),
    )
    readback = build_jd_live_provider_canary_readback(
        enabled=True,
        payload=payload,
    )

    assert readback["readback_status"] == (
        "jd_live_canary_readback_blocked"
    )
    assert readback["canary_configured"] is True
    assert readback["canary_attempted"] is False
    assert readback["provider_call_attempted"] is False
    assert readback["fallback_used"] is True
    assert readback["fallback_reason"] == (
        "missing_injected_provider_adapter"
    )


def test_fallback_canary_reports_reason_without_raising():
    payload = _direct(
        canary_status="jd_live_canary_fallback",
        provider_call_succeeded=False,
        provider_call_failed=True,
        fallback_used=True,
        fallback_reason="required_skills_not_list",
        structured_output_validated=False,
        llmops_metadata=_llmops(
            provider_call_succeeded=False,
            fallback_used=True,
            schema_validation_status="invalid",
            error_type="StructuredOutputValidationError",
        ),
        jd_intelligence_output={
            "validation_status": "fallback",
            "validation_errors": ["required_skills_not_list"],
            "fallback_used": True,
        },
    )
    readback = build_jd_live_provider_canary_readback(
        enabled=True,
        payload=payload,
    )

    assert readback["readback_status"] == (
        "jd_live_canary_readback_fallback"
    )
    assert readback["provider_call_attempted"] is True
    assert readback["provider_call_failed"] is True
    assert readback["fallback_reason"] == "required_skills_not_list"
    assert readback["structured_output_validated"] is False


def test_successful_canary_metadata_and_llmops_are_normalized():
    readback = build_jd_live_provider_canary_readback(
        enabled=True,
        payload=_direct(),
    )

    assert readback["readback_status"] == (
        "jd_live_canary_readback_succeeded"
    )
    assert readback["canary_configured"] is True
    assert readback["canary_allowed"] is True
    assert readback["canary_attempted"] is True
    assert readback["provider_call_succeeded"] is True
    assert readback["structured_output_validated"] is True
    assert readback["shadow_only"] is True
    assert readback["provider_name"] == "fixture-provider"
    assert readback["model_name"] == "fixture-model"
    assert readback["prompt_version"] == "jd-canary-prompt-v1"
    assert readback["runtime_version"] == "jd-canary-runtime-v1"
    assert readback["llmops_metadata_present"] is True
    assert readback["latency_ms"] == 15
    assert readback["input_tokens"] == 20
    assert readback["output_tokens"] == 8
    assert readback["total_tokens"] == 28
    assert readback["estimated_cost"] == 0.004


def test_partial_failed_chain_metadata_is_normalized_without_raising():
    payload = _chain_result(
        trace={
            "jd_live_provider_canary_enabled": True,
            "jd_live_provider_canary_status": "jd_live_canary_fallback",
            "jd_live_provider_canary_allowed": True,
            "jd_live_provider_canary_attempted": True,
            "provider_call_made": True,
            "provider_call_succeeded": False,
            "fallback_used": True,
            "error_type": "RuntimeError",
        },
        safety={
            "shadow_only": True,
            "jd_live_provider_canary_enabled": True,
            "jd_live_provider_canary_allowed": True,
            "jd_live_provider_canary_attempted": True,
            "jd_live_provider_canary_succeeded": False,
            "jd_live_provider_canary_fallback": True,
            "jd_live_provider_canary_fallback_reason": (
                "provider_adapter_error:RuntimeError"
            ),
        },
        output={"validation_status": "fallback", "fallback_used": True},
    )
    readback = build_jd_live_provider_canary_readback(
        enabled=True,
        payload=payload,
    )

    assert readback["readback_status"] == (
        "jd_live_canary_readback_fallback"
    )
    assert readback["provider_call_attempted"] is True
    assert readback["provider_call_failed"] is True
    assert readback["fallback_used"] is True
    assert readback["fallback_reason"] == (
        "provider_adapter_error:RuntimeError"
    )


def test_review_packet_exposes_parallel_canary_readback_section():
    packet = (
        pipeline_agent_review_packet
        .build_pipeline_agent_review_packet_payload(
            hook_payload=_chain_result(
                trace={
                    **_llmops(),
                    "jd_live_provider_canary_enabled": True,
                    "jd_live_provider_canary_status": (
                        "jd_live_canary_succeeded_shadow_only"
                    ),
                    "jd_live_provider_canary_allowed": True,
                    "jd_live_provider_canary_attempted": True,
                },
                safety={
                    "shadow_only": True,
                    "jd_live_provider_canary_enabled": True,
                    "jd_live_provider_canary_allowed": True,
                    "jd_live_provider_canary_attempted": True,
                    "jd_live_provider_canary_succeeded": True,
                    "jd_live_provider_canary_fallback": False,
                },
                output={
                    "validation_status": "valid",
                    "fallback_used": False,
                },
            )
        )
    )
    readback = packet["jd_live_provider_canary_readback"]

    assert readback["readback_status"] == (
        "jd_live_canary_readback_succeeded"
    )
    assert readback["provider_call_succeeded"] is True
    assert packet["jd_provider_runtime_readback"][
        "readback_status"
    ] == "jd_provider_runtime_readback_no_data"


def test_readback_keeps_mutation_and_decision_influence_disabled():
    readback = build_jd_live_provider_canary_readback(
        enabled=True,
        payload=_direct(),
    )

    assert readback["mutation_authorized"] is False
    assert readback["mutation_authorized_agent_count"] == 0
    assert all(readback["influence_disabled"].values())
    for key in (
        "provider_calls_made",
        "network_calls_made",
        "environment_secrets_read",
        "provider_client_constructed",
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
        assert readback["safety_metadata"][key] is False


def test_helper_has_no_sdk_env_network_adapter_or_mutation_wiring():
    source = (
        ROOT / "src/agents/jd_live_provider_canary_readback.py"
    ).read_text(encoding="utf-8").lower()
    for marker in (
        "from openai",
        "import openai",
        "anthropic",
        "langchain",
        "sentence_transformers",
        "requests.",
        "httpx",
        "urllib",
        "socket",
        "os.getenv",
        "os.environ",
        "run_jd_live_provider_canary(",
        "provider_adapter(",
        "provider_client(",
        "provider_client.invoke(",
        "create_embedding(",
        "database_url",
        "connect(",
        "cursor.execute",
        ".commit(",
        "open(",
        "write_text(",
        "write_bytes(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in source


def test_api_ui_service_pipeline_and_dependencies_are_unchanged():
    expected = {
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/app/api.py": ("85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96"),
        "src/app/services.py": ("f186703fecdda54458c468f9c2ed1de0517fa86942bb3d0fe0b522f0601fe5a8"),
        "src/app/static/agentic_review.js": ("1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b"),
        "src/pipeline/collector.py": ("73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
    }

    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
