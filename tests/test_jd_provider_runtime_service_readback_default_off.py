from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents import pipeline_agent_review_packet, shadow_sidecar_hook
from src.app.services import jd_provider_runtime_readback_service_payload


ROOT = Path(__file__).resolve().parents[1]


def _hook(**updates):
    kwargs = {
        "run_id": "run-phase-12f",
        "batch_id": "batch-phase-12f",
        "job_id": "job-phase-12f",
        "stage_name": "post_final_scoring",
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.9,
        "source_deterministic_decision": "qualified_for_review",
        "three_agent_shadow_workflow_enabled": True,
        "job_payload": {"job_description": "Build Python systems."},
    }
    kwargs.update(updates)
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(**kwargs)


def _valid_output():
    return {
        "required_skills": ["Python"],
        "preferred_skills": [],
        "required_tools": [],
        "preferred_tools": [],
        "workflows": ["data systems"],
        "methods": [],
        "business_contexts": [],
        "stakeholder_contexts": [],
        "ownership_signals": [],
        "seniority_signals": [],
        "risk_flags": [],
        "extraction_confidence": 0.9,
    }


def _response(output):
    return {
        "output": deepcopy(output),
        "provider_name": "fixture-provider",
        "model_name": "fixture-model",
        "schema_validation_status": "valid",
    }


def _assert_safe(payload):
    safety = payload["safety_metadata"]
    assert payload["service_surface"] == (
        "jd_provider_runtime_readback_service"
    )
    assert payload["service_helper_only"] is True
    assert payload["review_packet_compatible"] is True
    assert payload["mutation_authorized"] is False
    assert payload["mutation_authorized_agent_count"] == 0
    for key in (
        "read_only",
        "advisory_only",
        "readback_only",
        "shadow_only",
    ):
        assert safety[key] is True
    for key in (
        "provider_calls_made",
        "network_calls_made",
        "embeddings_created",
        "did_read_database",
        "did_write_database",
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


def test_service_default_off_returns_safe_skipped_summary():
    payload = jd_provider_runtime_readback_service_payload()

    assert payload["readback_status"] == (
        "jd_provider_runtime_readback_skipped_default_off"
    )
    assert payload["readback_enabled"] is False
    assert payload["default_off"] is True
    assert payload["jd_provider_runtime_attempted"] is False
    _assert_safe(payload)


def test_service_enabled_missing_payload_returns_safe_no_data():
    payload = jd_provider_runtime_readback_service_payload(enabled=True)

    assert payload["readback_status"] == (
        "jd_provider_runtime_readback_no_data"
    )
    assert payload["default_off"] is False
    assert payload["provider_calls_allowed"] is False
    _assert_safe(payload)


def test_service_summarizes_default_off_shadow_metadata():
    payload = jd_provider_runtime_readback_service_payload(
        enabled=True,
        payload=_hook(),
    )

    assert payload["readback_status"] == (
        "jd_provider_runtime_readback_not_attempted"
    )
    assert payload["jd_provider_runtime_enabled"] is False
    assert payload["jd_provider_runtime_attempted"] is False
    _assert_safe(payload)


def test_service_summarizes_blocked_fallback_metadata():
    payload = jd_provider_runtime_readback_service_payload(
        enabled=True,
        payload=_hook(jd_provider_runtime_activation_enabled=True),
    )

    assert payload["readback_status"] == (
        "jd_provider_runtime_readback_blocked"
    )
    assert payload["jd_provider_runtime_enabled"] is True
    assert payload["jd_provider_runtime_attempted"] is False
    assert payload["fallback_used"] is True
    assert payload["fallback_reason"]
    _assert_safe(payload)


def test_service_summarizes_successful_validated_metadata():
    calls = []
    hook = _hook(
        jd_provider_runtime_activation_enabled=True,
        jd_provider_runtime_activation_client=lambda request: (
            calls.append(deepcopy(request)) or _response(_valid_output())
        ),
    )
    before = deepcopy(calls)
    payload = jd_provider_runtime_readback_service_payload(
        enabled=True,
        payload=hook,
    )

    assert calls == before
    assert payload["readback_status"] == (
        "jd_provider_runtime_readback_succeeded"
    )
    assert payload["jd_provider_runtime_attempted"] is True
    assert payload["jd_provider_runtime_succeeded"] is True
    assert payload["structured_output_validated"] is True
    assert payload["llmops_metadata_present"] is True
    assert payload["configured_provider_name"] == "fixture-provider"
    assert payload["configured_model_name"] == "fixture-model"
    _assert_safe(payload)


def test_service_summarizes_invalid_and_failed_fallback_metadata():
    invalid = jd_provider_runtime_readback_service_payload(
        enabled=True,
        payload=_hook(
            jd_provider_runtime_activation_enabled=True,
            jd_provider_runtime_activation_provider=lambda _request: (
                _response({"required_skills": {"invalid": "shape"}})
            ),
        ),
    )

    def failing_client(_request):
        raise RuntimeError("fixture failure")

    failed = jd_provider_runtime_readback_service_payload(
        enabled=True,
        payload=_hook(
            jd_provider_runtime_activation_enabled=True,
            jd_provider_runtime_activation_client=failing_client,
        ),
    )

    assert invalid["readback_status"] == (
        "jd_provider_runtime_readback_validation_failed"
    )
    assert invalid["fallback_reason"] == "required_skills_not_list"
    assert invalid["fallback_used"] is True
    assert failed["readback_status"] == (
        "jd_provider_runtime_readback_failed"
    )
    assert failed["fallback_reason"] == "RuntimeError"
    assert failed["fallback_used"] is True
    _assert_safe(invalid)
    _assert_safe(failed)


def test_service_preserves_review_packet_compatible_summary():
    hook = _hook(
        jd_provider_runtime_activation_enabled=True,
        jd_provider_runtime_activation_client=lambda _request: (
            _response(_valid_output())
        ),
    )
    packet = (
        pipeline_agent_review_packet
        .build_pipeline_agent_review_packet_payload(hook_payload=hook)
    )
    before = deepcopy(packet)
    payload = jd_provider_runtime_readback_service_payload(
        enabled=True,
        review_packet_payload=packet,
    )

    assert packet == before
    assert payload["readback_status"] == packet[
        "jd_provider_runtime_readback"
    ]["readback_status"]
    assert payload["configured_provider_name"] == "fixture-provider"
    assert payload["review_packet_compatible"] is True
    _assert_safe(payload)


def test_service_does_not_call_activation_adapter_client_env_or_storage():
    source = (ROOT / "src/app/services.py").read_text(encoding="utf-8")
    start = source.index("def jd_provider_runtime_readback_service_payload(")
    end = source.index(
        "\ndef vector_evidence_readback_service_helper_payload(",
        start,
    )
    snippet = source[start:end].lower()

    assert "build_jd_provider_runtime_trace_readback" in snippet
    for marker in (
        "run_jd_provider_runtime_activation(",
        "run_provider_runtime_adapter(",
        "provider_client",
        "provider_callable",
        "from openai",
        "import openai",
        "anthropic",
        "langchain",
        "os.getenv",
        "os.environ",
        "requests.",
        "httpx",
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
            "7cd4cc3e4bb921542e6f6e4870fb4999e7546fb5db90ed3bc1aa07d17930c1b5"
        ),
        "src/app/static/agentic_review.js": (
            "17af3ca604e4a88a5f51bab37617888b1b4f66dc2f446b976cf211484f69cbe0"
        ),
        "src/pipeline/collector.py": (
            "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"
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
