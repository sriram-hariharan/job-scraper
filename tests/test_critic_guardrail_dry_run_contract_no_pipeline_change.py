from __future__ import annotations

from copy import deepcopy

from src.agents import critic_agent


def _jd(**overrides):
    payload = {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": [],
        "required_tools": ["Airflow"],
        "preferred_tools": [],
        "workflows": ["production data pipelines"],
        "business_contexts": ["finance partners"],
        "ownership_signals": [],
        "seniority_signals": [],
    }
    payload.update(overrides)
    return payload


def _resume(**overrides):
    payload = {
        "resume_id": "resume-a",
        "bullets": [
            "Built Python and SQL production data pipelines with Airflow for finance partners."
        ],
        "skills": ["Python", "SQL"],
        "tools": ["Airflow"],
        "business_contexts": ["finance partners"],
    }
    payload.update(overrides)
    return [payload]


def _patch_ready_suggestion(**overrides):
    payload = {
        "suggestion_id": "tailoring_dry_run_001",
        "source_bullet_id": "bullet-1",
        "original_text": "Built Python and SQL production data pipelines with Airflow for finance partners.",
        "suggested_text": "Built Python and SQL production data pipelines with Airflow for finance partners.",
        "reason": "Existing resume evidence directly supports JD signal: Python.",
        "evidence_spans": [
            "Built Python and SQL production data pipelines with Airflow for finance partners."
        ],
        "jd_signal_links": [{"field": "required_skills", "signal": "Python"}],
        "patch_ready": True,
        "projected_score_delta": 0.03,
        "risk_flags": [],
    }
    payload.update(overrides)
    return payload


def _tailoring_payload(**overrides):
    payload = {
        "suggestion_status": "patch_ready_available",
        "selected_resume_id": "resume-a",
        "patch_ready_suggestions": [_patch_ready_suggestion()],
        "guidance_only_suggestions": [],
        "rejected_suggestions": [],
        "missing_evidence": [],
        "unsupported_claim_risks": [],
        "projected_score_delta": 0.03,
        "source_fields_used": ["required_skills", "required_tools"],
    }
    payload.update(overrides)
    return payload


def _build(**overrides):
    kwargs = {
        "tailoring_suggestion_payload": _tailoring_payload(),
        "jd_intelligence": _jd(),
        "resume_evidence_rows": _resume(),
        "context_id": "ctx-1",
        "job_id": "job-1",
    }
    kwargs.update(overrides)
    return critic_agent.build_critic_guardrail_dry_run_payload(**kwargs)


def test_supported_patch_ready_suggestion_is_approved():
    payload = _build()

    assert payload["critic_status"] == "approved"
    assert payload["approved_suggestions"]
    decision = payload["approved_suggestions"][0]
    assert decision["suggestion_id"] == "tailoring_dry_run_001"
    assert decision["decision"] == "approve"
    assert decision["original_patch_ready"] is True
    assert decision["final_patch_ready"] is True
    assert decision["reason_codes"] == []
    assert payload["confidence"] > 0


def test_unsupported_tool_metric_or_domain_is_rejected():
    risky_suggestion = _patch_ready_suggestion(
        suggestion_id="tailoring_dry_run_unsupported",
        suggested_text="Built Kubernetes automation that reduced healthcare revenue latency by 40%.",
        evidence_spans=["Built Python APIs for internal operations."],
        jd_signal_links=[
            {"field": "required_tools", "signal": "Kubernetes"},
            {"field": "business_contexts", "signal": "healthcare revenue"},
            {"field": "required_skills", "signal": "reduced latency by 40%"},
        ],
        risk_flags=["unsupported_tool", "unsupported_metric", "unsupported_domain_or_context"],
    )
    payload = _build(
        tailoring_suggestion_payload=_tailoring_payload(
            patch_ready_suggestions=[risky_suggestion],
            unsupported_claim_risks=[
                {"field": "required_tools", "signal": "Kubernetes", "risk": "unsupported_tool"},
                {"field": "business_contexts", "signal": "healthcare revenue", "risk": "unsupported_domain_or_context"},
                {"field": "required_skills", "signal": "reduced latency by 40%", "risk": "unsupported_metric"},
            ],
        ),
        resume_evidence_rows=_resume(
            bullets=["Built Python APIs for internal operations."],
            tools=["Python"],
            business_contexts=["internal operations"],
        ),
    )

    assert payload["critic_status"] == "rejected"
    assert payload["rejected_suggestions"][0]["decision"] == "reject"
    assert "unsupported_claim" in payload["rejected_suggestions"][0]["reason_codes"]
    assert {"unsupported_tool", "unsupported_metric", "unsupported_domain_or_context"} <= set(payload["unsupported_claim_risks"])
    assert payload["rejected_suggestions"][0]["final_patch_ready"] is False


def test_weak_useful_suggestion_is_downgraded_to_guidance():
    guidance = _patch_ready_suggestion(
        suggestion_id="tailoring_dry_run_guidance",
        suggested_text="Emphasize Python data pipeline work for this role.",
        evidence_spans=["Built Python and SQL production data pipelines with Airflow for finance partners."],
        patch_ready=False,
        projected_score_delta=0.0,
    )
    payload = _build(
        tailoring_suggestion_payload=_tailoring_payload(
            patch_ready_suggestions=[],
            guidance_only_suggestions=[guidance],
        )
    )

    assert payload["critic_status"] == "needs_guidance"
    decision = payload["downgraded_suggestions"][0]
    assert decision["decision"] == "downgrade_to_guidance"
    assert decision["original_patch_ready"] is False
    assert decision["final_patch_ready"] is False


def test_missing_evidence_is_rejected_or_downgraded():
    missing = _patch_ready_suggestion(
        suggestion_id="tailoring_dry_run_missing",
        suggested_text="Built Rust services for healthcare platforms.",
        evidence_spans=[],
        jd_signal_links=[{"field": "required_skills", "signal": "Rust"}],
        patch_ready=True,
        projected_score_delta=0.02,
    )
    payload = _build(
        tailoring_suggestion_payload=_tailoring_payload(
            patch_ready_suggestions=[missing],
            missing_evidence=["required_skills:Rust:resume_evidence_missing"],
        )
    )

    decisions = payload["rejected_suggestions"] + payload["downgraded_suggestions"]
    assert decisions
    assert decisions[0]["decision"] in {"reject", "downgrade_to_guidance"}
    assert "missing_evidence" in decisions[0]["reason_codes"]
    assert decisions[0]["final_patch_ready"] is False


def test_missing_tailoring_payload_returns_safe_fallback():
    payload = critic_agent.build_critic_guardrail_dry_run_payload(
        tailoring_suggestion_payload={},
        jd_intelligence={},
        resume_evidence_rows=[],
    )

    assert payload["critic_status"] == "insufficient_evidence"
    assert payload["approved_suggestions"] == []
    assert payload["downgraded_suggestions"] == []
    assert payload["rejected_suggestions"] == []
    assert "tailoring_payload_missing" in payload["reason_codes"]
    assert "tailoring_suggestions_missing" in payload["evidence_gaps"]


def test_critic_guardrail_dry_run_does_not_mutate_inputs_and_is_deterministic():
    tailoring = _tailoring_payload()
    jd = _jd()
    resume = _resume()
    original_tailoring = deepcopy(tailoring)
    original_jd = deepcopy(jd)
    original_resume = deepcopy(resume)

    first = critic_agent.build_critic_guardrail_dry_run_payload(
        tailoring_suggestion_payload=tailoring,
        jd_intelligence=jd,
        resume_evidence_rows=resume,
    )
    second = critic_agent.build_critic_guardrail_dry_run_payload(
        tailoring_suggestion_payload=tailoring,
        jd_intelligence=jd,
        resume_evidence_rows=resume,
    )

    assert first == second
    assert tailoring == original_tailoring
    assert jd == original_jd
    assert resume == original_resume


def test_critic_guardrail_dry_run_safety_metadata_has_no_runtime_mutation():
    payload = _build()

    safety = payload["safety_metadata"]
    assert safety["dry_run_only"] is True
    assert safety["deterministic_only"] is True
    assert safety["did_call_llm"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False


def test_critic_guardrail_dry_run_helper_has_no_pipeline_or_storage_calls():
    source_names = set(critic_agent.build_critic_guardrail_dry_run_payload.__code__.co_names)

    forbidden = {
        "create_agent_run",
        "record_agent_step",
        "complete_agent_run",
        "complete_agent_step",
        "score_resume_job_match",
        "run_agentic_workflow_dry_run",
        "execute_application",
        "submit_application",
    }
    assert forbidden.isdisjoint(source_names)
