from __future__ import annotations

from copy import deepcopy

from src.agents import tailoring_decision_agent


def _jd_signals(**overrides):
    payload = {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": [],
        "required_tools": ["Airflow"],
        "preferred_tools": [],
        "workflows": ["production data pipelines"],
        "methods": [],
        "business_contexts": ["finance partners"],
        "stakeholder_contexts": [],
        "ownership_signals": [],
        "seniority_signals": [],
    }
    payload.update(overrides)
    return payload


def _resume_match_payload(**overrides):
    payload = {
        "match_status": "strong_match",
        "selected_resume_id": "resume-a",
        "matched_evidence": [
            {
                "resume_id": "resume-a",
                "dimension": "tools",
                "signal": "Airflow",
                "evidence": "Airflow",
            }
        ],
        "missing_evidence": ["seniority:jd_signals_missing"],
        "safety_metadata": {
            "dry_run_only": True,
            "did_call_llm": False,
        },
    }
    payload.update(overrides)
    return payload


def _resume_evidence(**overrides):
    payload = {
        "resume_id": "resume-a",
        "bullet_ids": ["bullet-1"],
        "bullets": [
            "Built Python and SQL production data pipelines with Airflow for finance partners."
        ],
        "skills": ["Python", "SQL"],
        "tools": ["Airflow"],
        "business_contexts": ["finance partners"],
    }
    payload.update(overrides)
    return [payload]


def _build(**overrides):
    kwargs = {
        "jd_intelligence": _jd_signals(),
        "resume_match_payload": _resume_match_payload(),
        "resume_evidence_rows": _resume_evidence(),
        "selected_resume_id": "resume-a",
        "context_id": "ctx-1",
        "job_id": "job-1",
    }
    kwargs.update(overrides)
    return tailoring_decision_agent.build_tailoring_suggestion_dry_run_payload(**kwargs)


def test_strong_supported_evidence_creates_patch_ready_suggestion():
    payload = _build()

    assert payload["suggestion_status"] == "patch_ready_available"
    assert payload["selected_resume_id"] == "resume-a"
    assert payload["projected_score_delta"] > 0
    suggestion = payload["patch_ready_suggestions"][0]
    assert suggestion["patch_ready"] is True
    assert suggestion["source_bullet_id"] == "bullet-1"
    assert "Airflow" in suggestion["original_text"] or "Python" in suggestion["original_text"]
    assert suggestion["suggested_text"] == suggestion["original_text"]
    assert suggestion["evidence_spans"] == [suggestion["original_text"]]
    assert suggestion["risk_flags"] == []
    assert "required_skills" in payload["source_fields_used"]


def test_missing_evidence_creates_guidance_or_rejected_suggestion():
    payload = _build(
        jd_intelligence=_jd_signals(
            required_skills=["Rust"],
            required_tools=[],
            workflows=[],
            business_contexts=[],
        ),
        resume_evidence_rows=_resume_evidence(
            bullets=["Built Python data pipelines for internal reporting."],
            skills=["Python"],
            tools=[],
            business_contexts=[],
        ),
    )

    assert payload["patch_ready_suggestions"] == []
    assert payload["suggestion_status"] in {"guidance_only", "rejected_unsupported_claims"}
    assert payload["guidance_only_suggestions"] or payload["rejected_suggestions"]
    assert any("Rust" in item for item in payload["missing_evidence"])


def test_unsupported_tool_metric_or_domain_is_not_patch_ready():
    payload = _build(
        jd_intelligence=_jd_signals(
            required_skills=["Reduced latency by 40%"],
            required_tools=["Kubernetes"],
            business_contexts=["healthcare revenue cycle"],
        ),
        resume_evidence_rows=_resume_evidence(
            bullets=["Built Python APIs for internal operations."],
            tools=["Python"],
            business_contexts=["internal operations"],
        ),
    )

    assert payload["patch_ready_suggestions"] == []
    rejected = payload["rejected_suggestions"]
    risks = {risk["risk"] for risk in payload["unsupported_claim_risks"]}
    assert rejected
    assert {"unsupported_tool", "unsupported_metric", "unsupported_domain_or_context"} <= risks
    assert all(item["patch_ready"] is False for item in rejected)


def test_missing_jd_or_resume_match_inputs_return_safe_fallback():
    payload = tailoring_decision_agent.build_tailoring_suggestion_dry_run_payload(
        jd_intelligence={},
        resume_match_payload={},
        resume_evidence_rows=[],
        selected_resume_id="resume-a",
    )

    assert payload["suggestion_status"] == "insufficient_evidence"
    assert payload["patch_ready_suggestions"] == []
    assert payload["guidance_only_suggestions"] == []
    assert payload["rejected_suggestions"] == []
    assert "jd_signals_missing" in payload["missing_evidence"]
    assert "resume_match_payload_missing" in payload["missing_evidence"]
    assert "resume_evidence_missing" in payload["missing_evidence"]


def test_tailoring_suggestion_dry_run_does_not_mutate_inputs_and_is_deterministic():
    jd = _jd_signals()
    match = _resume_match_payload()
    evidence = _resume_evidence()
    original_jd = deepcopy(jd)
    original_match = deepcopy(match)
    original_evidence = deepcopy(evidence)

    first = tailoring_decision_agent.build_tailoring_suggestion_dry_run_payload(
        jd_intelligence=jd,
        resume_match_payload=match,
        resume_evidence_rows=evidence,
        selected_resume_id="resume-a",
    )
    second = tailoring_decision_agent.build_tailoring_suggestion_dry_run_payload(
        jd_intelligence=jd,
        resume_match_payload=match,
        resume_evidence_rows=evidence,
        selected_resume_id="resume-a",
    )

    assert first == second
    assert jd == original_jd
    assert match == original_match
    assert evidence == original_evidence


def test_tailoring_suggestion_dry_run_safety_metadata_has_no_runtime_mutation():
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


def test_tailoring_suggestion_dry_run_helper_has_no_pipeline_or_storage_calls():
    source = tailoring_decision_agent.build_tailoring_suggestion_dry_run_payload.__code__.co_names

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
    assert forbidden.isdisjoint(set(source))
