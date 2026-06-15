from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from src.app import services


STAGE_ORDER = [
    "jd_intelligence",
    "resume_match",
    "tailoring_suggestion",
    "critic_guardrail",
    "strategy_recommendation",
]


def _jd() -> dict:
    return {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": [],
        "required_tools": ["Airflow"],
        "preferred_tools": [],
        "workflows": ["production data pipelines"],
        "methods": ["LLMOps evaluation"],
        "business_contexts": ["finance partners"],
        "stakeholder_contexts": ["finance stakeholders"],
        "ownership_signals": ["owned production workflows"],
        "seniority_signals": ["senior IC scope"],
    }


def _resume() -> dict:
    return {
        "resume_id": "resume-a",
        "bullet_ids": ["bullet-1"],
        "bullets": [
            "Senior IC scope owned production workflows for Python and SQL production data pipelines with Airflow, LLMOps evaluation, and finance stakeholders."
        ],
        "skills": ["Python", "SQL"],
        "tools": ["Airflow"],
        "methods": ["LLMOps evaluation"],
        "workflows": ["production data pipelines"],
        "business_contexts": ["finance partners"],
        "stakeholder_contexts": ["finance stakeholders"],
        "ownership_signals": ["owned production workflows"],
        "seniority_signals": ["senior IC scope"],
        "raw_text": (
            "Senior IC scope owned production workflows for Python and SQL production data "
            "pipelines with Airflow, LLMOps evaluation, finance partners, and finance stakeholders."
        ),
    }


def _request_payload() -> dict:
    return {
        "job_title": "Data Platform Engineer",
        "company": "ExampleCo",
        "location": "Remote",
        "job_description": "Python SQL Airflow production data pipelines for finance partners.",
        "jd_intelligence": _jd(),
        "resume_evidence_rows": [_resume()],
        "selected_resume_id": "resume-a",
        "user_preferences": {"risk_tolerance": "conservative"},
        "context_id": "ctx-1",
        "job_id": "job-1",
    }


def _valid_jd_provider_payload() -> dict:
    return {
        **_jd(),
        "risk_flags": [],
        "extraction_confidence": 0.92,
        "model_provider": "fake-jd-provider",
        "model_name": "fake-jd-model",
        "prompt_version": "fake-jd-prompt-v1",
        "token_usage": {"total_token_count": 31},
        "cost": {"estimated_cost": 0.01, "cost_currency": "USD"},
        "latency_ms": 44,
    }


def _valid_tailoring_provider_payload() -> dict:
    evidence = (
        "Senior IC scope owned production workflows for Python and SQL production data "
        "pipelines with Airflow, LLMOps evaluation, and finance stakeholders."
    )
    return {
        "patch_ready_suggestions": [
            {
                "suggestion_id": "live_tailoring_001",
                "source_bullet_id": "bullet-1",
                "original_text": evidence,
                "suggested_text": evidence,
                "reason": "Evidence directly supports Python and Airflow alignment.",
                "evidence_spans": [evidence],
                "jd_signal_links": [{"field": "required_skills", "signal": "Python"}],
                "patch_ready": True,
                "projected_score_delta": 0.04,
                "risk_flags": [],
            }
        ],
        "guidance_only_suggestions": [],
        "rejected_suggestions": [],
        "missing_evidence": [],
        "unsupported_claim_risks": [],
        "projected_score_delta": 0.04,
        "rationale": "Provider returned evidence-backed tailoring suggestions.",
        "model_provider": "fake-tailoring-provider",
        "model_name": "fake-tailoring-model",
        "prompt_version": "fake-tailoring-prompt-v1",
        "token_usage": {"total_token_count": 42},
        "cost": {"estimated_cost": 0.01, "cost_currency": "USD"},
        "latency_ms": 88,
    }


def _valid_critic_provider_payload() -> dict:
    evidence = (
        "Senior IC scope owned production workflows for Python and SQL production data "
        "pipelines with Airflow, LLMOps evaluation, and finance stakeholders."
    )
    return {
        "critic_status": "approved",
        "approved_suggestions": [
            {
                "suggestion_id": "live_tailoring_001",
                "decision": "approve",
                "confidence": 0.91,
                "reason_codes": [],
                "evidence_spans": [evidence],
                "notes": "Evidence-backed suggestion.",
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
        "confidence": 0.91,
        "rationale": "Provider approved evidence-backed tailoring suggestions.",
        "model_provider": "fake-critic-provider",
        "model_name": "fake-critic-model",
        "prompt_version": "fake-critic-prompt-v1",
        "token_usage": {"total_token_count": 38},
        "cost": {"estimated_cost": 0.01, "cost_currency": "USD"},
        "latency_ms": 77,
    }


def _assert_shadow_safety(payload: dict, *, did_call_llm: bool = False) -> None:
    safety = payload["safety_metadata"]
    assert payload["read_only"] is True
    assert payload["manual_surface"] is True
    assert payload["dry_run_only"] is True
    assert safety["dry_run_only"] is True
    assert safety["shadow_mode"] is True
    assert safety["manual_or_service_only"] is True
    assert safety["did_call_llm"] is did_call_llm
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["advisory_only"] is True


def test_chain_returns_all_stages_in_order():
    payload = services.build_shadow_agentic_workflow_chain_dry_run_payload(**_request_payload())

    assert payload["service_surface"] == "shadow_agentic_workflow_chain_dry_run"
    assert payload["stage_order"] == STAGE_ORDER
    assert list(payload["stages"].keys()) == STAGE_ORDER
    assert set(payload["stage_statuses"].keys()) == set(STAGE_ORDER)
    assert payload["stages"]["resume_match"]["match_status"] == "strong_match"
    assert payload["stages"]["tailoring_suggestion"]["suggestion_status"] == "patch_ready_available"
    assert payload["stages"]["critic_guardrail"]["critic_status"] == "approved"
    assert payload["recommendation_action"] in {"apply_now", "tailor_first"}
    _assert_shadow_safety(payload)


def test_missing_inputs_produce_safe_fallback():
    payload = services.build_shadow_agentic_workflow_chain_dry_run_payload()

    assert payload["shadow_chain_status"] == "completed_with_blockers"
    assert payload["stage_order"] == STAGE_ORDER
    assert list(payload["stages"].keys()) == STAGE_ORDER
    assert payload["recommendation_action"] == "insufficient_information"
    assert "resume_match_payload_missing" in payload["blocking_risks"]
    assert "critic_guardrail_payload_missing" in payload["blocking_risks"]
    _assert_shadow_safety(payload)


def test_default_off_path_does_not_call_live_providers():
    calls: list[str] = []

    def fake_jd_adapter(_payload):
        calls.append("jd")
        return _valid_jd_provider_payload()

    def fake_tailoring_adapter(_payload):
        calls.append("tailoring")
        return _valid_tailoring_provider_payload()

    def fake_critic_adapter(_payload):
        calls.append("critic")
        return _valid_critic_provider_payload()

    payload = services.build_shadow_agentic_workflow_chain_dry_run_payload(
        **_request_payload(),
        jd_adapter=fake_jd_adapter,
        tailoring_adapter=fake_tailoring_adapter,
        critic_adapter=fake_critic_adapter,
    )

    assert calls == []
    assert payload["stages"]["jd_intelligence"]["validation_status"] == "disabled"
    assert payload["stages"]["tailoring_suggestion"]["validation_status"] == "disabled"
    assert payload["stages"]["critic_guardrail"]["validation_status"] == "disabled"
    _assert_shadow_safety(payload, did_call_llm=False)


def test_optional_fake_adapters_can_be_injected_and_metadata_is_preserved():
    calls: list[str] = []

    def fake_jd_adapter(_payload):
        calls.append("jd")
        return _valid_jd_provider_payload()

    def fake_tailoring_adapter(_payload):
        calls.append("tailoring")
        return _valid_tailoring_provider_payload()

    def fake_critic_adapter(_payload):
        calls.append("critic")
        return _valid_critic_provider_payload()

    payload = services.build_shadow_agentic_workflow_chain_dry_run_payload(
        **_request_payload(),
        jd_adapter=fake_jd_adapter,
        jd_feature_enabled=True,
        tailoring_adapter=fake_tailoring_adapter,
        tailoring_feature_enabled=True,
        critic_adapter=fake_critic_adapter,
        critic_feature_enabled=True,
    )

    assert calls == ["jd", "tailoring", "critic"]
    assert payload["stages"]["jd_intelligence"]["model_provider"] == "fake-jd-provider"
    assert payload["stages"]["tailoring_suggestion"]["model_provider"] == "fake-tailoring-provider"
    assert payload["stages"]["critic_guardrail"]["model_provider"] == "fake-critic-provider"
    assert payload["stages"]["strategy_recommendation"]["recommendation_action"] in {"apply_now", "tailor_first"}
    _assert_shadow_safety(payload, did_call_llm=True)


def test_strategy_consumes_prior_stage_outputs():
    payload = services.build_shadow_agentic_workflow_chain_dry_run_payload(**_request_payload())
    strategy = payload["stages"]["strategy_recommendation"]

    assert "resume_match_payload" in strategy["source_fields_used"]
    assert "tailoring_suggestion_payload" in strategy["source_fields_used"]
    assert "critic_guardrail_payload" in strategy["source_fields_used"]
    assert strategy["recommendation_action"] == payload["recommendation_action"]


def test_inputs_are_not_mutated():
    source = _request_payload()
    original = deepcopy(source)

    first = services.build_shadow_agentic_workflow_chain_dry_run_payload(**source)
    second = services.build_shadow_agentic_workflow_chain_dry_run_payload(**source)

    assert first == second
    assert source == original


def test_no_storage_scoring_ranking_queue_approval_execution_submission_or_pipeline_wiring():
    source = Path("src/app/services.py").read_text()
    start = source.index("def build_shadow_agentic_workflow_chain_dry_run_payload")
    end = source.index("def _artifact_row_by_name")
    snippet = source[start:end]

    forbidden_markers = [
        "insert_",
        "get_rag_job_documents",
        "cursor.execute",
        ".commit(",
        "subprocess",
        "requests.",
        "httpx.",
        "run_chat_completion",
        "score_resume_job_match",
        "mutate_ranking",
        "update_ranking",
        "application_execution_queue",
        "execute_application(",
        "submit_application(",
        "workflow_runner",
        "create_agent_run",
        "record_agent_step",
    ]
    for marker in forbidden_markers:
        assert marker not in snippet
