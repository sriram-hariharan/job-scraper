# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
# phase23f legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents import pipeline_agent_review_packet
from src.agents import shadow_sidecar_hook


ROOT = Path(__file__).resolve().parents[1]


def _hook(**updates):
    kwargs = {
        "run_id": "run-phase-12e",
        "batch_id": "batch-phase-12e",
        "job_id": "job-phase-12e",
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


def _packet(hook_payload=None):
    return pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
        hook_payload=hook_payload or {},
    )


def test_missing_runtime_metadata_gives_safe_no_data_section():
    readback = _packet()["jd_provider_runtime_readback"]

    assert readback["readback_status"] == (
        "jd_provider_runtime_readback_no_data"
    )
    assert readback["jd_provider_runtime_enabled"] is False
    assert readback["jd_provider_runtime_attempted"] is False
    assert readback["provider_calls_allowed"] is False
    assert readback["mutation_authorized"] is False
    assert readback["mutation_authorized_agent_count"] == 0


def test_default_off_shadow_payload_is_no_provider_attempt():
    readback = _packet(_hook())["jd_provider_runtime_readback"]

    assert readback["readback_status"] == (
        "jd_provider_runtime_readback_no_data"
    )
    assert readback["jd_provider_runtime_attempted"] is False
    assert readback["fallback_used"] is False
    assert readback["shadow_only"] is True


def test_blocked_missing_client_is_summarized_with_fallback():
    readback = _packet(
        _hook(jd_provider_runtime_activation_enabled=True)
    )["jd_provider_runtime_readback"]

    assert readback["readback_status"] == (
        "jd_provider_runtime_readback_blocked"
    )
    assert readback["jd_provider_runtime_enabled"] is True
    assert readback["jd_provider_runtime_attempted"] is False
    assert readback["fallback_used"] is True
    assert readback["fallback_reason"]


def test_valid_fake_provider_is_summarized_as_validated_shadow_success():
    calls = []
    hook = _hook(
        jd_provider_runtime_activation_enabled=True,
        jd_provider_runtime_activation_client=lambda request: (
            calls.append(deepcopy(request)) or _response(_valid_output())
        ),
    )
    before = deepcopy(calls)
    readback = _packet(hook)["jd_provider_runtime_readback"]

    assert calls == before
    assert readback["readback_status"] == (
        "jd_provider_runtime_readback_succeeded"
    )
    assert readback["jd_provider_runtime_attempted"] is True
    assert readback["jd_provider_runtime_succeeded"] is True
    assert readback["structured_output_validated"] is True
    assert readback["llmops_metadata_present"] is True
    assert readback["configured_provider_name"] == "fixture-provider"
    assert readback["configured_model_name"] == "fixture-model"
    assert readback["shadow_only"] is True


def test_invalid_output_is_summarized_as_validation_failure():
    readback = _packet(
        _hook(
            jd_provider_runtime_activation_enabled=True,
            jd_provider_runtime_activation_provider=lambda _request: (
                _response({"required_skills": {"invalid": "shape"}})
            ),
        )
    )["jd_provider_runtime_readback"]

    assert readback["readback_status"] == (
        "jd_provider_runtime_readback_validation_failed"
    )
    assert readback["jd_provider_runtime_failed"] is True
    assert readback["structured_output_validated"] is False
    assert readback["fallback_used"] is True
    assert readback["fallback_reason"] == "required_skills_not_list"


def test_provider_exception_is_summarized_as_failed_fallback():
    def failing_client(_request):
        raise RuntimeError("fixture failure")

    readback = _packet(
        _hook(
            jd_provider_runtime_activation_enabled=True,
            jd_provider_runtime_activation_client=failing_client,
        )
    )["jd_provider_runtime_readback"]

    assert readback["readback_status"] == (
        "jd_provider_runtime_readback_failed"
    )
    assert readback["jd_provider_runtime_failed"] is True
    assert readback["fallback_used"] is True
    assert readback["fallback_reason"] == "RuntimeError"


def test_packet_readback_does_not_call_activation_or_provider_runtime():
    source = (
        ROOT / "src/agents/pipeline_agent_review_packet.py"
    ).read_text(encoding="utf-8")
    start = source.index("def _jd_provider_runtime_readback(")
    end = source.index("\ndef _review_focus(", start)
    snippet = source[start:end].lower()

    assert "build_jd_provider_runtime_trace_readback(" in snippet
    for marker in (
        "run_jd_provider_runtime_activation(",
        "run_provider_runtime_adapter(",
        "provider_client",
        "provider_callable",
        "from openai",
        "import openai",
        "anthropic",
        "langchain",
        "create_embedding(",
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


def test_packet_and_runtime_readback_keep_mutation_authority_zero():
    packet = _packet(
        _hook(
            jd_provider_runtime_activation_enabled=True,
            jd_provider_runtime_activation_client=lambda _request: (
                _response(_valid_output())
            ),
        )
    )
    readback = packet["jd_provider_runtime_readback"]

    assert packet["mutation_authorized_agents"] == 0
    assert readback["mutation_authorized"] is False
    assert readback["mutation_authorized_agent_count"] == 0
    for key in (
        "provider_calls_made",
        "network_calls_made",
        "embeddings_created",
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
        assert readback["safety_metadata"][key] is False


def test_api_ui_service_pipeline_and_dependencies_are_unchanged():
    expected = {
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/app/api.py": ("d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004"),
        "src/app/services.py": ("bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2"),
        "src/app/static/agentic_review.js": ("1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b"),
        "src/pipeline/collector.py": ("1d35d00e54d1d858134b2e524955887bd7adbbce3a01e53d1782debc4584490a"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
    }
    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
