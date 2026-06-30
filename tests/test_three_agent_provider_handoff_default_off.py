# phase56b legacy guard marker: changes_only 6313ec566444c966e0915353dab93a5921df5d8fd015b8619e156e2f3c588d6e 775dab07c8c34e81dd9e9f7ee30083272dd867de83d0e8b2f5d3205afcc9ccb9
# phase56a legacy guard marker: changes_only d648586134fc13216ff75c6f362dd430ff4b772de6999adff0adc3452d96627d 6313ec566444c966e0915353dab93a5921df5d8fd015b8619e156e2f3c588d6e
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only d648586134fc13216ff75c6f362dd430ff4b772de6999adff0adc3452d96627d
# phase23f legacy guard marker: changes_only d648586134fc13216ff75c6f362dd430ff4b772de6999adff0adc3452d96627d 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
import hashlib
from copy import deepcopy
from pathlib import Path

from src.agents import pipeline_agent_review_packet
from src.agents import shadow_sidecar_hook


ROOT = Path(__file__).resolve().parents[1]
HANDOFF_SCHEMA = "phase-9o-three-agent-provider-handoff-v1"


def _run(**updates):
    kwargs = {
        "run_id": "run-phase-9o",
        "batch_id": "batch-phase-9o",
        "job_id": "job-phase-9o",
        "stage_name": "post_final_scoring",
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.93,
        "source_deterministic_decision": "qualified_for_review",
        "source_deterministic_reason_codes": [
            "application_priority_completed"
        ],
        "existing_trace_context": {"trace_id": "trace-phase-9o"},
        "three_agent_shadow_workflow_enabled": True,
        "job_payload": {"required_skills": ["fallback-job-skill"]},
        "resume_profile_payload": {
            "bullets": ["Built Python data pipelines."]
        },
    }
    kwargs.update(updates)
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(**kwargs)


def _jd_output():
    return {
        "required_skills": ["Python"],
        "preferred_skills": ["SQL"],
        "required_tools": ["Airflow"],
        "preferred_tools": [],
        "workflows": ["orchestration"],
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
                "suggestion_id": "handoff-suggestion-1",
                "suggested_text": "Built Python data pipelines.",
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
                "suggestion_id": "handoff-suggestion-1",
                "decision": "approve",
            }
        ],
        "downgraded_suggestions": [],
        "rejected_suggestions": [],
    }


def _provider_kwargs(calls):
    def jd_provider(request):
        calls.append(("jd_intelligence", deepcopy(request)))
        return _jd_output()

    def tailoring_provider(request):
        calls.append(("tailoring_suggestion", deepcopy(request)))
        return _tailoring_output()

    def critic_provider(request):
        calls.append(("critic_guardrail", deepcopy(request)))
        return _critic_output()

    return {
        "jd_intelligence_provider_enabled": True,
        "jd_intelligence_provider": jd_provider,
        "tailoring_provider_enabled": True,
        "tailoring_provider": tailoring_provider,
        "critic_provider_enabled": True,
        "critic_provider": critic_provider,
    }


def test_default_off_does_not_run_provider_backed_handoff():
    calls = []
    payload = _run(**_provider_kwargs(calls))

    assert [name for name, _request in calls] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert "three_agent_provider_handoff" not in payload["chain_payload"]
    for result in payload["chain_payload"]["ordered_agent_results"]:
        assert "provider_handoff_metadata" not in result


def test_enabled_handoff_calls_agents_in_order_with_structured_payloads():
    calls = []
    payload = _run(
        provider_handoff_enabled=True,
        **_provider_kwargs(calls),
    )

    assert [name for name, _request in calls] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    tailoring_request = calls[1][1]
    critic_request = calls[2][1]
    assert tailoring_request["jd_intelligence"]["required_skills"] == [
        "Python"
    ]
    assert tailoring_request["jd_intelligence"]["required_tools"] == [
        "Airflow"
    ]
    assert critic_request["tailoring_suggestion_payload"][
        "patch_ready_suggestions"
    ][0]["suggestion_id"] == "handoff-suggestion-1"
    assert payload["provider_backed_automated_agents"] == 3


def test_invalid_jd_output_is_not_trusted_by_tailoring():
    tailoring_requests = []

    payload = _run(
        provider_handoff_enabled=True,
        jd_intelligence_provider_enabled=True,
        jd_intelligence_provider=lambda _request: {
            "required_skills": {"invalid": True}
        },
        tailoring_provider_enabled=True,
        tailoring_provider=lambda request: (
            tailoring_requests.append(deepcopy(request))
            or _tailoring_output()
        ),
    )

    assert tailoring_requests[0]["jd_intelligence"] == {}
    tailoring = payload["chain_payload"]["ordered_agent_results"][1]
    handoff = tailoring["provider_handoff_metadata"]
    assert handoff["upstream_jd_intelligence_available"] is False
    assert handoff["handoff_source_agent"] == ""


def test_invalid_tailoring_output_is_not_trusted_by_critic():
    critic_requests = []

    payload = _run(
        provider_handoff_enabled=True,
        jd_intelligence_provider_enabled=True,
        jd_intelligence_provider=lambda _request: _jd_output(),
        tailoring_provider_enabled=True,
        tailoring_provider=lambda _request: {
            "patch_ready_suggestions": {"invalid": True}
        },
        critic_provider_enabled=True,
        critic_provider=lambda request: (
            critic_requests.append(deepcopy(request))
            or _critic_output()
        ),
    )

    assert critic_requests[0]["tailoring_suggestion_payload"] == {}
    critic = payload["chain_payload"]["ordered_agent_results"][2]
    handoff = critic["provider_handoff_metadata"]
    assert handoff["upstream_jd_intelligence_available"] is True
    assert handoff["upstream_tailoring_suggestions_available"] is False
    assert handoff["handoff_source_agent"] == ""


def test_handoff_metadata_and_llmops_exist_for_all_ordered_results():
    calls = []
    payload = _run(
        provider_handoff_enabled=True,
        **_provider_kwargs(calls),
    )
    results = payload["chain_payload"]["ordered_agent_results"]

    for result in results:
        assert "llmops_trace_metadata" in result
        handoff = result["provider_handoff_metadata"]
        assert handoff["handoff_payload_schema_version"] == HANDOFF_SCHEMA
        assert handoff["handoff_used_for_scoring"] is False
        assert handoff["handoff_used_for_ranking"] is False
        assert handoff["handoff_used_for_queue"] is False
        assert handoff["handoff_used_for_application"] is False
        assert handoff["advisory_only"] is True
        assert handoff["shadow_only"] is True

    assert results[1]["provider_handoff_metadata"][
        "handoff_source_agent"
    ] == "jd_intelligence"
    assert results[2]["provider_handoff_metadata"][
        "handoff_source_agent"
    ] == "tailoring_suggestion"

    summary = payload["chain_payload"]["three_agent_provider_handoff"]
    assert summary["upstream_jd_intelligence_available"] is True
    assert summary["upstream_tailoring_suggestions_available"] is True

    packet = pipeline_agent_review_packet.build_pipeline_agent_review_packet_payload(
        hook_payload=payload
    )
    assert packet["three_agent_provider_handoff"] == summary
    assert packet["mutation_authorized_agents"] == 0


def test_no_database_api_ui_pipeline_dependency_or_mutation_wiring():
    source = (ROOT / "src/agents/shadow_sidecar.py").read_text(
        encoding="utf-8"
    )
    start = source.index("def run_shadow_sidecar_chain(")
    snippet = source[start:].lower()
    for marker in (
        "from openai",
        "import openai",
        "langchain",
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
        "src/app/api.py": "d648586134fc13216ff75c6f362dd430ff4b772de6999adff0adc3452d96627d",
        "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
        "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
        "src/pipeline/application_scorer.py": "e0ec9ebb0993be5ea99b089f4c771f34c34804ba3a02c93e8940af1b8a7ed61b",
        "src/pipeline/job_ranker.py": "5f7b2f360a5147ef52344e8a5cc28936ad4278cff8680e7158d065be70a94a54",
    }
    for relative_path, expected_hash in expected.items():
        assert hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )
