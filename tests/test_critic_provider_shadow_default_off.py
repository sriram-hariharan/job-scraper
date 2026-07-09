# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96
# phase23f legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
import hashlib
from copy import deepcopy
from pathlib import Path

from src.agents import pipeline_agent_review_packet
from src.agents import shadow_sidecar_hook


ROOT = Path(__file__).resolve().parents[1]


def _run(**updates):
    kwargs = {
        "run_id": "run-phase-9n",
        "batch_id": "batch-phase-9n",
        "job_id": "job-phase-9n",
        "stage_name": "post_final_scoring",
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.92,
        "source_deterministic_decision": "qualified_for_review",
        "source_deterministic_reason_codes": [
            "application_priority_completed"
        ],
        "existing_trace_context": {"trace_id": "trace-phase-9n"},
        "three_agent_shadow_workflow_enabled": True,
        "job_payload": {
            "required_skills": ["Python"],
            "preferred_tools": ["Airflow"],
        },
        "resume_profile_payload": {
            "bullets": ["Built Python data pipelines with Airflow."]
        },
    }
    kwargs.update(updates)
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(**kwargs)


def _valid_critic_payload():
    return {
        "critic_status": "approved",
        "approved_suggestions": [
            {
                "suggestion_id": "tailoring-provider-001",
                "decision": "approve",
                "confidence": 0.93,
                "reason_codes": [],
                "evidence_spans": ["Built Python data pipelines."],
                "notes": "Evidence-backed.",
                "original_patch_ready": True,
                "final_patch_ready": True,
            }
        ],
        "downgraded_suggestions": [],
        "rejected_suggestions": [],
        "reason_codes": [],
        "unsupported_claim_risks": [],
        "ats_risks": [],
        "readability_risks": [],
        "evidence_gaps": [],
        "confidence": 0.93,
        "rationale": "Approved evidence-backed suggestion.",
        "model_provider": "fake-critic-provider",
        "model_name": "fake-critic-model",
        "prompt_version": "fake-critic-prompt-v1",
        "token_usage": {
            "input_token_count": 16,
            "output_token_count": 7,
        },
        "cost": {"estimated_cost": 0.004},
        "latency_ms": 29,
    }


def _valid_jd_payload():
    return {
        "required_skills": ["Python"],
        "preferred_skills": [],
        "required_tools": [],
        "preferred_tools": [],
        "workflows": [],
        "methods": [],
        "business_contexts": [],
        "stakeholder_contexts": [],
        "ownership_signals": [],
        "seniority_signals": [],
        "risk_flags": [],
        "extraction_confidence": 0.8,
    }


def _valid_tailoring_payload():
    return {
        "patch_ready_suggestions": [
            {
                "suggestion_id": "tailoring-provider-001",
                "suggested_text": "Built Python data pipelines.",
                "patch_ready": True,
            }
        ],
        "guidance_only_suggestions": [],
        "rejected_suggestions": [],
    }


def _results(payload):
    return payload["chain_payload"]["ordered_agent_results"]


def test_default_off_keeps_deterministic_critic_and_does_not_call_provider():
    calls = []
    payload = _run(
        three_agent_shadow_workflow_enabled=True,
        critic_provider=lambda request: calls.append(deepcopy(request))
    )

    assert calls == []
    critic = _results(payload)[2]
    assert critic["sidecar_stage_status"] == "completed_with_fallback"
    assert "agent_output_payload" not in critic
    assert payload["provider_backed_automated_agents"] == 0


def test_enabled_without_provider_falls_back_safely():
    payload = _run(critic_provider_enabled=True)
    critic = _results(payload)[2]
    output = critic["agent_output_payload"]

    assert output["validation_status"] == "fallback"
    assert output["validation_errors"] == ["adapter_missing"]
    assert output["fallback_used"] is True
    assert critic["safety_metadata"]["critic_provider_enabled"] is True
    assert critic["safety_metadata"]["critic_provider_attempted"] is False
    assert payload["provider_backed_automated_agents"] == 0


def test_fake_provider_produces_validated_guardrail_decision_only():
    calls = []

    def provider(request):
        calls.append(deepcopy(request))
        return _valid_critic_payload()

    payload = _run(
        three_agent_shadow_workflow_enabled=True,
        critic_provider_enabled=True,
        critic_provider=provider,
    )
    critic = _results(payload)[2]
    output = critic["agent_output_payload"]

    assert len(calls) == 1
    assert output["validation_status"] == "valid"
    assert output["critic_status"] == "approved"
    assert output["approved_suggestions"][0]["decision"] == "approve"
    assert output["guardrail_decision_only"] is True
    assert critic["sidecar_stage_status"] == "completed_shadow"
    assert critic["safety_metadata"]["critic_provider_attempted"] is True
    assert critic["safety_metadata"]["critic_provider_succeeded"] is True
    assert critic["safety_metadata"]["critic_schema_validated"] is True
    assert critic["safety_metadata"]["did_mutate_resume"] is False


def test_invalid_provider_response_falls_back_safely():
    payload = _run(
        three_agent_shadow_workflow_enabled=True,
        critic_provider_enabled=True,
        critic_provider=lambda _request: {
            "approved_suggestions": {"invalid": True}
        },
    )
    critic = _results(payload)[2]
    output = critic["agent_output_payload"]

    assert output["validation_status"] == "invalid"
    assert output["fallback_used"] is True
    assert "approved_suggestions_not_list" in output["validation_errors"]
    assert critic["sidecar_stage_status"] == "completed_with_fallback"


def test_provider_exception_is_non_blocking_and_recorded():
    def provider(_request):
        raise RuntimeError("fixture critic provider failure")

    payload = _run(
        three_agent_shadow_workflow_enabled=True,
        critic_provider_enabled=True,
        critic_provider=provider,
    )
    critic = _results(payload)[2]
    trace = critic["llmops_trace_metadata"]

    assert critic["sidecar_stage_status"] == "completed_with_fallback"
    assert trace["provider_call_made"] is True
    assert trace["fallback_used"] is True
    assert trace["schema_validation_status"] == "fallback"
    assert trace["error_type"] == "adapter_error:RuntimeError"


def test_all_three_agents_are_provider_backed_with_zero_mutation_authority():
    payload = _run(
        three_agent_shadow_workflow_enabled=True,
        jd_intelligence_provider_enabled=True,
        jd_intelligence_provider=lambda _request: _valid_jd_payload(),
        tailoring_provider_enabled=True,
        tailoring_provider=lambda _request: _valid_tailoring_payload(),
        critic_provider_enabled=True,
        critic_provider=lambda _request: _valid_critic_payload(),
    )
    results = _results(payload)
    traces = {
        result["agent_name"]: result["llmops_trace_metadata"]
        for result in results
    }

    assert all(trace["provider_call_made"] is True for trace in traces.values())
    critic_trace = traces["critic_guardrail"]
    assert critic_trace["model_provider"] == "fake-critic-provider"
    assert critic_trace["model_name"] == "fake-critic-model"
    assert critic_trace["input_tokens"] == 16
    assert critic_trace["output_tokens"] == 7
    assert critic_trace["estimated_cost"] == 0.004
    assert critic_trace["latency_ms"] == 29
    assert critic_trace["fallback_used"] is False
    assert critic_trace["schema_validation_status"] == "valid"
    assert payload["provider_backed_automated_agents"] == 3
    contract = payload["chain_payload"]["three_agent_llmops_trace_contract"]
    assert contract["provider_backed_agent_count"] == 3
    assert contract["provider_backed_agent_names"] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]

    packet = pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
        hook_payload=payload
    )
    assert packet["provider_backed_automated_agents"] == 3
    assert packet["mutation_authorized_agents"] == 0


def test_no_database_api_ui_pipeline_dependency_or_mutation_wiring():
    source = (ROOT / "src/agents/critic_agent.py").read_text(
        encoding="utf-8"
    )
    start = source.index("def build_live_critic_guardrail_shadow_payload(")
    snippet = source[start:].lower()
    for marker in (
        "from openai",
        "import openai",
        "langchain",
        "sentence_transformers",
        "create_embedding(",
        "database_url",
        "connect(",
        "score_jobs(",
        "rank_jobs(",
        "create_approval_request(",
        "record_approval_decision(",
        "mutate_resume(",
        "create_execution_request(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in snippet

    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96",
        "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
        "src/pipeline/collector.py": "3e5d429fe94cdd9d58d0c0a666563caee25f50865bc18a3824b6bac634a00971",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
