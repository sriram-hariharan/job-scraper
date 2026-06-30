# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only e658b1e05444d7cd2546d3d065cc325045a9d2bb1589b900c18d1aeea0fbd084
# phase23f legacy guard marker: changes_only e658b1e05444d7cd2546d3d065cc325045a9d2bb1589b900c18d1aeea0fbd084 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
import hashlib
from copy import deepcopy
from pathlib import Path

from src.agents import pipeline_agent_review_packet
from src.agents import shadow_sidecar_hook


ROOT = Path(__file__).resolve().parents[1]


def _run(**updates):
    kwargs = {
        "run_id": "run-phase-9m",
        "batch_id": "batch-phase-9m",
        "job_id": "job-phase-9m",
        "stage_name": "post_final_scoring",
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.92,
        "source_deterministic_decision": "qualified_for_review",
        "three_agent_shadow_workflow_enabled": True,
        "job_payload": {
            "title": "Senior Data Platform Engineer",
            "required_skills": ["Python", "SQL"],
            "preferred_tools": ["Airflow"],
        },
        "resume_profile_payload": {
            "resume_id": "resume-a",
            "bullets": [
                "Built Python and SQL data pipelines with Airflow."
            ],
        },
    }
    kwargs.update(updates)
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(**kwargs)


def _valid_tailoring_payload():
    evidence = "Built Python and SQL data pipelines with Airflow."
    return {
        "patch_ready_suggestions": [
            {
                "suggestion_id": "tailoring-provider-001",
                "source_bullet_id": "bullet-1",
                "original_text": evidence,
                "suggested_text": evidence,
                "reason": "Evidence supports alignment.",
                "evidence_spans": [evidence],
                "jd_signal_links": [
                    {"field": "required_skills", "signal": "Python"}
                ],
                "patch_ready": True,
                "projected_score_delta": 0.03,
                "risk_flags": [],
            }
        ],
        "guidance_only_suggestions": [],
        "rejected_suggestions": [],
        "missing_evidence": [],
        "unsupported_claim_risks": [],
        "projected_score_delta": 0.03,
        "rationale": "Evidence-backed suggestion plan.",
        "model_provider": "fake-tailoring-provider",
        "model_name": "fake-tailoring-model",
        "prompt_version": "fake-tailoring-prompt-v1",
        "token_usage": {
            "input_token_count": 14,
            "output_token_count": 9,
        },
        "cost": {"estimated_cost": 0.003},
        "latency_ms": 23,
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
        "model_provider": "fake-jd-provider",
        "model_name": "fake-jd-model",
    }


def _results(payload):
    return payload["chain_payload"]["ordered_agent_results"]


def test_default_off_keeps_deterministic_tailoring_and_does_not_call_provider():
    calls = []
    payload = _run(
        tailoring_provider=lambda request: calls.append(deepcopy(request))
    )

    assert calls == []
    tailoring = _results(payload)[1]
    assert tailoring["sidecar_stage_status"] == "completed_with_fallback"
    assert "agent_output_payload" not in tailoring
    assert payload["provider_backed_automated_agents"] == 0


def test_enabled_without_provider_falls_back_safely():
    payload = _run(tailoring_provider_enabled=True)
    tailoring = _results(payload)[1]
    provider_payload = tailoring["agent_output_payload"]

    assert tailoring["sidecar_stage_status"] == "completed_with_fallback"
    assert provider_payload["validation_status"] == "fallback"
    assert provider_payload["validation_errors"] == ["adapter_missing"]
    assert provider_payload["fallback_used"] is True
    assert tailoring["safety_metadata"]["tailoring_provider_enabled"] is True
    assert tailoring["safety_metadata"]["tailoring_provider_attempted"] is False
    assert payload["provider_backed_automated_agents"] == 0


def test_fake_provider_produces_validated_suggestion_plan_only():
    calls = []

    def provider(request):
        calls.append(deepcopy(request))
        return _valid_tailoring_payload()

    payload = _run(
        tailoring_provider_enabled=True,
        tailoring_provider=provider,
    )
    tailoring = _results(payload)[1]
    provider_payload = tailoring["agent_output_payload"]

    assert len(calls) == 1
    assert provider_payload["validation_status"] == "valid"
    assert provider_payload["patch_ready_suggestions"][0][
        "suggestion_id"
    ] == "tailoring-provider-001"
    assert provider_payload["fallback_used"] is False
    assert tailoring["sidecar_stage_status"] == "completed_shadow"
    assert tailoring["safety_metadata"]["tailoring_provider_attempted"] is True
    assert tailoring["safety_metadata"]["tailoring_provider_succeeded"] is True
    assert tailoring["safety_metadata"]["tailoring_schema_validated"] is True
    assert tailoring["safety_metadata"]["did_mutate_resume"] is False


def test_invalid_provider_response_falls_back_safely():
    payload = _run(
        tailoring_provider_enabled=True,
        tailoring_provider=lambda _request: {
            "patch_ready_suggestions": {"invalid": True}
        },
    )
    tailoring = _results(payload)[1]
    provider_payload = tailoring["agent_output_payload"]

    assert provider_payload["validation_status"] == "invalid"
    assert provider_payload["fallback_used"] is True
    assert "patch_ready_suggestions_not_list" in (
        provider_payload["validation_errors"]
    )
    assert tailoring["sidecar_stage_status"] == "completed_with_fallback"


def test_provider_exception_is_non_blocking_and_recorded():
    def provider(_request):
        raise RuntimeError("fixture tailoring provider failure")

    payload = _run(
        tailoring_provider_enabled=True,
        tailoring_provider=provider,
    )
    tailoring = _results(payload)[1]
    trace = tailoring["llmops_trace_metadata"]

    assert tailoring["sidecar_stage_status"] == "completed_with_fallback"
    assert trace["provider_call_made"] is True
    assert trace["fallback_used"] is True
    assert trace["schema_validation_status"] == "fallback"
    assert trace["error_type"] == "adapter_error:RuntimeError"


def test_jd_and_tailoring_are_provider_backed_but_critic_is_not():
    payload = _run(
        jd_intelligence_provider_enabled=True,
        jd_intelligence_provider=lambda _request: _valid_jd_payload(),
        tailoring_provider_enabled=True,
        tailoring_provider=lambda _request: _valid_tailoring_payload(),
    )
    results = _results(payload)
    traces = {
        result["agent_name"]: result["llmops_trace_metadata"]
        for result in results
    }

    assert traces["jd_intelligence"]["provider_call_made"] is True
    assert traces["tailoring_suggestion"]["provider_call_made"] is True
    assert traces["critic_guardrail"]["provider_call_made"] is False
    tailoring_trace = traces["tailoring_suggestion"]
    assert tailoring_trace["model_provider"] == "fake-tailoring-provider"
    assert tailoring_trace["model_name"] == "fake-tailoring-model"
    assert tailoring_trace["input_tokens"] == 14
    assert tailoring_trace["output_tokens"] == 9
    assert tailoring_trace["estimated_cost"] == 0.003
    assert tailoring_trace["latency_ms"] == 23
    assert tailoring_trace["fallback_used"] is False
    assert tailoring_trace["schema_validation_status"] == "valid"
    assert payload["provider_backed_automated_agents"] == 2
    contract = payload["chain_payload"]["three_agent_llmops_trace_contract"]
    assert contract["provider_backed_agent_count"] == 2
    assert contract["provider_backed_agent_names"] == [
        "jd_intelligence",
        "tailoring_suggestion",
    ]

    packet = pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
        hook_payload=payload
    )
    assert packet["provider_backed_automated_agents"] == 2
    assert packet["mutation_authorized_agents"] == 0


def test_no_database_api_ui_pipeline_dependency_or_mutation_wiring():
    sources = "\n".join(
        (ROOT / path).read_text(encoding="utf-8")
        for path in (
            "src/agents/tailoring_decision_agent.py",
            "src/agents/shadow_sidecar.py",
            "src/agents/shadow_sidecar_hook.py",
        )
    ).lower()
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
        assert marker not in sources

    expected = {
        "requirements.txt": "96146be2940c7333dba0f919dc4d9d21bed3db536bf3249684b03705991ede1f",
        "src/app/api.py": "e658b1e05444d7cd2546d3d065cc325045a9d2bb1589b900c18d1aeea0fbd084",
        "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
        "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
