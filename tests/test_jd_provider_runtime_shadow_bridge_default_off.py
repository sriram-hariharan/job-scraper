# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only e658b1e05444d7cd2546d3d065cc325045a9d2bb1589b900c18d1aeea0fbd084
# phase23f legacy guard marker: changes_only e658b1e05444d7cd2546d3d065cc325045a9d2bb1589b900c18d1aeea0fbd084 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents import shadow_sidecar_hook


ROOT = Path(__file__).resolve().parents[1]
ORDERED_AGENTS = [
    "jd_intelligence",
    "tailoring_suggestion",
    "critic_guardrail",
]


def _run(**updates):
    kwargs = {
        "run_id": "run-phase-12c",
        "batch_id": "batch-phase-12c",
        "job_id": "job-phase-12c",
        "stage_name": "post_final_scoring",
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.9,
        "source_deterministic_decision": "qualified_for_review",
        "three_agent_shadow_workflow_enabled": True,
        "job_payload": {
            "title": "Data Platform Engineer",
            "company": "Example Co",
            "location": "Remote",
            "job_description": "Build Python and SQL data systems.",
        },
    }
    kwargs.update(updates)
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(**kwargs)


def _valid_output():
    return {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": [],
        "required_tools": ["PostgreSQL"],
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


def _fake_response(output):
    return {
        "output": deepcopy(output),
        "provider_name": "fixture-runtime",
        "model_name": "fixture-jd-model",
        "latency_ms": 11,
        "token_usage": {
            "input_tokens": 8,
            "output_tokens": 3,
            "total_tokens": 11,
        },
        "cost": {"estimated_cost": 0.001},
        "schema_validation_status": "valid",
    }


def _results(payload):
    return payload["chain_payload"]["ordered_agent_results"]


def _jd(payload):
    return _results(payload)[0]


def test_shadow_workflow_default_off_does_not_call_activation_client():
    calls = []
    payload = _run(
        jd_provider_runtime_activation_client=lambda request: calls.append(
            deepcopy(request)
        )
    )

    assert calls == []
    assert _jd(payload)["sidecar_stage_status"] == (
        "completed_with_fallback"
    )
    assert payload["provider_backed_automated_agents"] == 0
    assert "jd_provider_runtime_activation_enabled" not in _jd(payload)[
        "safety_metadata"
    ]


def test_enabled_without_injected_client_blocks_safely():
    payload = _run(jd_provider_runtime_activation_enabled=True)
    jd = _jd(payload)

    assert jd["sidecar_stage_status"] == "completed_with_fallback"
    assert jd["agent_output_payload"]["validation_status"] == "fallback"
    assert jd["safety_metadata"][
        "jd_provider_runtime_activation_enabled"
    ] is True
    assert jd["safety_metadata"][
        "jd_provider_runtime_activation_attempted"
    ] is False
    assert jd["safety_metadata"][
        "jd_provider_runtime_activation_succeeded"
    ] is False
    assert jd["llmops_trace_metadata"]["provider_call_made"] is False
    assert payload["provider_backed_automated_agents"] == 0


def test_valid_fake_client_produces_jd_shadow_runtime_metadata():
    calls = []

    def client(request):
        calls.append(deepcopy(request))
        return _fake_response(_valid_output())

    payload = _run(
        jd_provider_runtime_activation_enabled=True,
        jd_provider_runtime_activation_client=client,
        provider_runtime_provider_name="fixture-runtime",
        provider_runtime_model_name="fixture-jd-model",
    )
    jd = _jd(payload)
    trace = jd["llmops_trace_metadata"]

    assert len(calls) == 1
    assert calls[0]["agent_name"] == "jd_intelligence"
    assert calls[0]["shadow_only"] is True
    assert jd["sidecar_stage_status"] == "completed_shadow"
    assert jd["agent_output_payload"]["validation_status"] == "valid"
    assert trace["provider_call_made"] is True
    assert trace["model_provider"] == "fixture-runtime"
    assert trace["model_name"] == "fixture-jd-model"
    assert trace["schema_validation_status"] == "valid"
    assert trace["fallback_used"] is False
    assert jd["safety_metadata"][
        "jd_provider_runtime_activation_succeeded"
    ] is True
    assert payload["provider_backed_automated_agents"] == 1


def test_invalid_fake_output_falls_back_deterministically():
    payload = _run(
        jd_provider_runtime_activation_enabled=True,
        jd_provider_runtime_activation_provider=lambda _request: (
            _fake_response({"required_skills": {"invalid": "shape"}})
        ),
    )
    jd = _jd(payload)
    trace = jd["llmops_trace_metadata"]

    assert jd["sidecar_stage_status"] == "completed_with_fallback"
    assert jd["agent_output_payload"]["validation_status"] == "invalid"
    assert "required_skills_not_list" in jd["agent_output_payload"][
        "validation_errors"
    ]
    assert trace["provider_call_made"] is True
    assert trace["provider_call_succeeded"] is False
    assert trace["fallback_used"] is True
    assert payload["provider_backed_automated_agents"] == 1


def test_provider_exception_falls_back_deterministically():
    def failing_client(_request):
        raise RuntimeError("fixture failure")

    payload = _run(
        jd_provider_runtime_activation_enabled=True,
        jd_provider_runtime_activation_client=failing_client,
    )
    jd = _jd(payload)
    trace = jd["llmops_trace_metadata"]

    assert jd["sidecar_stage_status"] == "completed_with_fallback"
    assert jd["agent_output_payload"]["validation_status"] == "fallback"
    assert trace["provider_call_made"] is True
    assert trace["provider_call_succeeded"] is False
    assert trace["fallback_used"] is True
    assert trace["error_type"] == "RuntimeError"


def test_only_jd_activation_runs_and_mutation_authority_stays_zero():
    calls = []
    payload = _run(
        jd_provider_runtime_activation_enabled=True,
        jd_provider_runtime_activation_client=lambda request: (
            calls.append(deepcopy(request))
            or _fake_response(_valid_output())
        ),
    )
    results = _results(payload)

    assert [call["agent_name"] for call in calls] == ["jd_intelligence"]
    assert [result["agent_name"] for result in results] == ORDERED_AGENTS
    assert results[1]["llmops_trace_metadata"][
        "provider_call_made"
    ] is False
    assert results[2]["llmops_trace_metadata"][
        "provider_call_made"
    ] is False
    assert results[1]["sidecar_stage_status"] == "completed_with_fallback"
    assert results[2]["sidecar_stage_status"] == "completed_with_fallback"
    assert payload["provider_backed_automated_agents"] == 1
    assert payload["mutation_authorized_agents"] == 0
    safety = results[0]["safety_metadata"]
    for key in (
        "did_write_database",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_create_approval",
        "did_mutate_resume",
        "did_execute_application",
        "did_submit_application",
    ):
        assert safety[key] is False


def test_bridge_has_no_sdk_network_storage_or_mutation_wiring():
    source = (ROOT / "src/agents/shadow_sidecar_hook.py").read_text(
        encoding="utf-8"
    )
    start = source.index("def run_shadow_sidecar_pipeline_hook(")
    snippet = source[start:].lower()
    for marker in (
        "from openai",
        "import openai",
        "anthropic",
        "langchain",
        "sentence_transformers",
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
        "record_approval_decision(",
        "mutate_resume(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in snippet


def test_api_ui_service_pipeline_and_dependencies_are_unchanged():
    expected = {
        "requirements.txt": ("96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f"),
        "src/app/api.py": ("e658b1e05444d7cd2546d3d065cc325045a9d2bb1589b900c18d1aeea0fbd084"),
        "src/app/services.py": ("c27f0c1a499398d423f8edd46165da784dabfea0309f2022ed88f9fc75d8df8f"),
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
