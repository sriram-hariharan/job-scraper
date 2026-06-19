from copy import deepcopy
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
        "run_id": "run-phase-11c",
        "batch_id": "batch-phase-11c",
        "job_id": "job-phase-11c",
        "stage_name": "post_final_scoring",
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.91,
        "source_deterministic_decision": "qualified_for_review",
        "three_agent_shadow_workflow_enabled": True,
        "job_payload": {
            "title": "Data Platform Engineer",
            "job_description": "Build Python data platforms.",
            "required_skills": ["Python"],
        },
        "resume_profile_payload": {
            "bullets": ["Built Python data platforms."]
        },
    }
    kwargs.update(updates)
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(**kwargs)


def _jd_output():
    return {
        "required_skills": ["Python"],
        "preferred_skills": [],
        "required_tools": [],
        "preferred_tools": [],
        "workflows": ["data platforms"],
        "methods": [],
        "business_contexts": [],
        "stakeholder_contexts": [],
        "ownership_signals": [],
        "seniority_signals": [],
        "risk_flags": [],
        "extraction_confidence": 0.9,
    }


def _tailoring_output():
    return {
        "patch_ready_suggestions": [
            {
                "suggestion_id": "runtime-tailoring-1",
                "suggested_text": "Built Python data platforms.",
                "patch_ready": True,
            }
        ],
        "guidance_only_suggestions": [],
        "rejected_suggestions": [],
    }


def _critic_output():
    return {
        "critic_status": "approved",
        "approved_suggestions": [
            {
                "suggestion_id": "runtime-tailoring-1",
                "decision": "approve",
            }
        ],
        "downgraded_suggestions": [],
        "rejected_suggestions": [],
    }


def _runtime_client(calls):
    def client(request):
        calls.append(deepcopy(request))
        agent_name = request["agent_name"]
        output = {
            "jd_intelligence": _jd_output(),
            "tailoring_suggestion": _tailoring_output(),
            "critic_guardrail": _critic_output(),
        }[agent_name]
        return {
            "output": output,
            "provider_name": "fixture-runtime",
            "model_name": f"{agent_name}-model",
            "latency_ms": 10,
            "token_usage": {
                "input_tokens": 7,
                "output_tokens": 3,
                "total_tokens": 10,
            },
            "cost": {"estimated_cost": 0.001},
            "schema_validation_status": "valid",
        }

    return client


def _provider_flags():
    return {
        "jd_intelligence_provider_enabled": True,
        "tailoring_provider_enabled": True,
        "critic_provider_enabled": True,
    }


def test_default_off_bridge_does_not_call_injected_runtime_client():
    calls = []
    payload = _run(
        provider_runtime_adapter_client=_runtime_client(calls),
        **_provider_flags(),
    )

    assert calls == []
    assert payload["provider_backed_automated_agents"] == 0
    for result in payload["chain_payload"]["ordered_agent_results"]:
        assert result["sidecar_stage_status"] == "completed_with_fallback"
        assert "provider_runtime_adapter_enabled" not in (
            result["llmops_trace_metadata"]
        )


def test_existing_provider_callable_path_is_unchanged_when_bridge_disabled():
    calls = []

    def provider(request):
        calls.append(deepcopy(request))
        return _jd_output()

    payload = _run(
        jd_intelligence_provider_enabled=True,
        jd_intelligence_provider=provider,
    )
    jd = payload["chain_payload"]["ordered_agent_results"][0]

    assert len(calls) == 1
    assert "provider_request" not in calls[0]
    assert jd["agent_output_payload"]["validation_status"] == "valid"
    assert jd["llmops_trace_metadata"]["provider_call_made"] is True
    assert "provider_runtime_adapter_enabled" not in (
        jd["llmops_trace_metadata"]
    )


def test_enabled_bridge_calls_fake_client_through_runtime_adapter():
    calls = []
    payload = _run(
        provider_runtime_adapter_enabled=True,
        provider_runtime_adapter_client=_runtime_client(calls),
        provider_runtime_provider_name="fixture-runtime",
        provider_runtime_model_name="fixture-model",
        jd_intelligence_provider_enabled=True,
    )
    jd = payload["chain_payload"]["ordered_agent_results"][0]

    assert len(calls) == 1
    assert calls[0]["agent_name"] == "jd_intelligence"
    assert "provider_request" in calls[0]
    assert jd["agent_output_payload"]["validation_status"] == "valid"
    assert jd["llmops_trace_metadata"]["provider_call_made"] is True
    assert jd["llmops_trace_metadata"][
        "provider_runtime_adapter_enabled"
    ] is True
    assert jd["llmops_trace_metadata"][
        "provider_runtime_adapter_attempted"
    ] is True
    assert jd["llmops_trace_metadata"][
        "provider_runtime_adapter_succeeded"
    ] is True
    assert jd["llmops_trace_metadata"][
        "provider_runtime_adapter_blocked"
    ] is False


def test_adapter_metadata_is_attached_to_agent_safety():
    calls = []
    payload = _run(
        provider_runtime_adapter_enabled=True,
        provider_runtime_adapter_client=_runtime_client(calls),
        jd_intelligence_provider_enabled=True,
    )
    safety = payload["chain_payload"]["ordered_agent_results"][0][
        "safety_metadata"
    ]

    assert safety["provider_runtime_adapter_enabled"] is True
    assert safety["provider_runtime_adapter_attempted"] is True
    assert safety["provider_runtime_adapter_succeeded"] is True
    assert safety["provider_runtime_adapter_blocked"] is False
    assert safety["provider_calls_made"] is True
    assert safety["embeddings_created"] is False
    assert safety["did_write_database"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_create_execution_request"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False


def test_missing_runtime_client_falls_back_safely():
    payload = _run(
        provider_runtime_adapter_enabled=True,
        jd_intelligence_provider_enabled=True,
    )
    jd = payload["chain_payload"]["ordered_agent_results"][0]

    assert jd["sidecar_stage_status"] == "completed_with_fallback"
    assert jd["llmops_trace_metadata"][
        "provider_runtime_adapter_attempted"
    ] is False
    assert jd["llmops_trace_metadata"][
        "provider_runtime_adapter_succeeded"
    ] is False
    assert jd["llmops_trace_metadata"][
        "provider_runtime_adapter_blocked"
    ] is True
    assert jd["llmops_trace_metadata"]["provider_call_made"] is False
    assert jd["safety_metadata"]["provider_calls_made"] is False
    assert payload["provider_backed_automated_agents"] == 0


def test_runtime_client_exception_falls_back_safely():
    def failing_client(_request):
        raise RuntimeError("fixture runtime failure")

    payload = _run(
        provider_runtime_adapter_enabled=True,
        provider_runtime_adapter_client=failing_client,
        jd_intelligence_provider_enabled=True,
    )
    jd = payload["chain_payload"]["ordered_agent_results"][0]

    assert jd["sidecar_stage_status"] == "completed_with_fallback"
    assert jd["llmops_trace_metadata"][
        "provider_runtime_adapter_attempted"
    ] is True
    assert jd["llmops_trace_metadata"][
        "provider_runtime_adapter_succeeded"
    ] is False
    assert jd["llmops_trace_metadata"][
        "provider_runtime_adapter_blocked"
    ] is False
    assert jd["safety_metadata"]["provider_calls_made"] is True


def test_all_three_agents_run_through_adapter_backed_shadow_path():
    calls = []
    payload = _run(
        provider_runtime_adapter_enabled=True,
        provider_runtime_adapter_client=_runtime_client(calls),
        provider_runtime_provider_name="fixture-runtime",
        provider_runtime_model_name="fixture-model",
        provider_handoff_enabled=True,
        **_provider_flags(),
    )
    results = payload["chain_payload"]["ordered_agent_results"]

    assert [call["agent_name"] for call in calls] == ORDERED_AGENTS
    assert [result["agent_name"] for result in results] == ORDERED_AGENTS
    assert all(
        result["sidecar_stage_status"] == "completed_shadow"
        for result in results
    )
    assert all(
        result["llmops_trace_metadata"][
            "provider_runtime_adapter_succeeded"
        ]
        is True
        for result in results
    )
    assert payload["provider_backed_automated_agents"] == 3
    assert payload["mutation_authorized_agents"] == 0


def test_bridge_has_no_sdk_storage_or_mutation_wiring():
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


def test_no_service_api_ui_pipeline_or_dependency_wiring():
    paths = (
        "src/app/api.py",
        "src/pipeline/collector.py",
        "requirements.txt",
    )
    for path in paths:
        source = (ROOT / path).read_text(encoding="utf-8")
        assert "provider_runtime_adapter_enabled" not in source
        assert "provider_runtime_adapter_client" not in source
