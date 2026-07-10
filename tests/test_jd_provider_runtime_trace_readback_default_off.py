# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
# phase26c legacy guard marker: changes_only fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004
# phase23f legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0
# phase23f legacy guard marker: changes_only fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents import shadow_sidecar_hook
from src.agents.jd_provider_runtime_activation import (
    run_jd_provider_runtime_activation,
)
from src.agents.jd_provider_runtime_trace_readback import (
    build_jd_provider_runtime_trace_readback,
)


ROOT = Path(__file__).resolve().parents[1]


def _valid_output():
    return {
        "required_skills": ["Python", "SQL"],
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


def _hook(**updates):
    kwargs = {
        "run_id": "run-phase-12d",
        "batch_id": "batch-phase-12d",
        "job_id": "job-phase-12d",
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


def test_missing_payload_returns_safe_default_off_and_no_data():
    skipped = build_jd_provider_runtime_trace_readback()
    no_data = build_jd_provider_runtime_trace_readback(enabled=True)

    assert skipped["readback_status"] == (
        "jd_provider_runtime_readback_skipped_default_off"
    )
    assert skipped["readback_enabled"] is False
    assert no_data["readback_status"] == (
        "jd_provider_runtime_readback_no_data"
    )
    assert no_data["jd_provider_runtime_attempted"] is False
    assert no_data["provider_calls_allowed"] is False


def test_default_off_shadow_payload_reports_no_attempt():
    payload = _hook()
    readback = build_jd_provider_runtime_trace_readback(
        enabled=True,
        payload=payload,
    )

    assert readback["readback_status"] == (
        "jd_provider_runtime_readback_not_attempted"
    )
    assert readback["jd_provider_runtime_enabled"] is False
    assert readback["jd_provider_runtime_attempted"] is False
    assert readback["jd_provider_runtime_succeeded"] is False
    assert readback["shadow_only"] is True


def test_blocked_missing_client_reports_fallback():
    payload = _hook(jd_provider_runtime_activation_enabled=True)
    readback = build_jd_provider_runtime_trace_readback(
        enabled=True,
        payload=payload,
    )

    assert readback["readback_status"] == (
        "jd_provider_runtime_readback_blocked"
    )
    assert readback["jd_provider_runtime_enabled"] is True
    assert readback["jd_provider_runtime_attempted"] is False
    assert readback["fallback_used"] is True
    assert readback["fallback_reason"]


def test_valid_fake_provider_reports_success_validation_and_llmops():
    calls = []
    payload = _hook(
        jd_provider_runtime_activation_enabled=True,
        jd_provider_runtime_activation_client=lambda request: (
            calls.append(deepcopy(request)) or _response(_valid_output())
        ),
    )
    calls_before = deepcopy(calls)
    readback = build_jd_provider_runtime_trace_readback(
        enabled=True,
        payload=payload,
    )

    assert calls == calls_before
    assert readback["readback_status"] == (
        "jd_provider_runtime_readback_succeeded"
    )
    assert readback["jd_provider_runtime_attempted"] is True
    assert readback["jd_provider_runtime_succeeded"] is True
    assert readback["jd_provider_runtime_failed"] is False
    assert readback["structured_output_validated"] is True
    assert readback["llmops_metadata_present"] is True
    assert readback["configured_provider_name"] == "fixture-provider"
    assert readback["configured_model_name"] == "fixture-model"
    assert readback["shadow_only"] is True


def test_invalid_output_reports_validation_failure_and_fallback():
    payload = run_jd_provider_runtime_activation(
        enabled=True,
        provider_callable=lambda _request: _response(
            {"required_skills": {"invalid": "shape"}}
        ),
    )
    readback = build_jd_provider_runtime_trace_readback(
        enabled=True,
        payload=payload,
    )

    assert readback["readback_status"] == (
        "jd_provider_runtime_readback_validation_failed"
    )
    assert readback["jd_provider_runtime_attempted"] is True
    assert readback["jd_provider_runtime_succeeded"] is False
    assert readback["jd_provider_runtime_failed"] is True
    assert readback["structured_output_validated"] is False
    assert readback["fallback_used"] is True
    assert readback["fallback_reason"] == "required_skills_not_list"


def test_provider_exception_reports_failure_and_fallback():
    def failing_client(_request):
        raise RuntimeError("fixture failure")

    payload = run_jd_provider_runtime_activation(
        enabled=True,
        provider_client=failing_client,
    )
    readback = build_jd_provider_runtime_trace_readback(
        enabled=True,
        payload=payload,
    )

    assert readback["readback_status"] == (
        "jd_provider_runtime_readback_failed"
    )
    assert readback["jd_provider_runtime_attempted"] is True
    assert readback["jd_provider_runtime_failed"] is True
    assert readback["fallback_used"] is True
    assert readback["fallback_reason"] == "RuntimeError"


def test_readback_keeps_mutation_authority_zero_and_makes_no_calls():
    calls = []
    source = run_jd_provider_runtime_activation(
        enabled=True,
        provider_callable=lambda request: (
            calls.append(deepcopy(request)) or _response(_valid_output())
        ),
    )
    count_before = len(calls)
    readback = build_jd_provider_runtime_trace_readback(
        enabled=True,
        payload=source,
    )
    safety = readback["safety_metadata"]

    assert len(calls) == count_before
    assert readback["mutation_authorized"] is False
    assert readback["mutation_authorized_agent_count"] == 0
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


def test_helper_has_no_sdk_network_runtime_or_mutation_wiring():
    source = (
        ROOT / "src/agents/jd_provider_runtime_trace_readback.py"
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
        "run_provider_runtime_adapter(",
        "run_jd_provider_runtime_activation(",
        "provider_callable(",
        "provider_client",
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
        assert marker not in source


def test_api_ui_service_pipeline_and_dependencies_are_unchanged():
    expected = {
        "requirements.txt": ("5dc563901e19c10a0f59fe811ec6961ee47f837827a7448e3a669aed9f244cc6"),
        "src/app/api.py": ("d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004"),
        "src/app/services.py": ("bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2"),
        "src/app/static/agentic_review.js": ("fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0"),
        "src/pipeline/collector.py": ("e5af36527801b2a1a55501622619d4e62ccaa7472e835500613e2894843d1671"),
        "src/pipeline/application_scorer.py": ("e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b"),
        "src/pipeline/job_ranker.py": ("5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54"),
        "application_execution_queue.py": ("c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"),
    }
    for relative_path, expected_hash in expected.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
