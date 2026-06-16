from pathlib import Path

from src.agents import shadow_sidecar


def _chain_input(**config):
    return shadow_sidecar.build_shadow_sidecar_input_payload(
        run_id="run_shadow_observability",
        batch_id="batch_shadow_observability",
        job_id="job_shadow_observability",
        stage_name="post_deterministic_evaluation_shadow_chain",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=0.87,
        source_deterministic_decision="qualified_for_review",
        source_deterministic_reason_codes=["score_above_review_threshold"],
        job_payload={
            "title": "Data Platform Engineer",
            "job_description": "Build SQL and Airflow data pipelines.",
            "required_skills": ["SQL"],
            "required_tools": ["Airflow"],
            "jd_evidence_refs": ["job_payload.required_skills"],
            "jd_reason_codes": ["jd_required_skills_present"],
            "jd_risk_flags": ["jd_validation_warning"],
            "tailoring_evidence_refs": ["resume_profile_payload.sql_airflow_bullet"],
            "tailoring_reason_codes": ["tailoring_gap_supported_by_resume"],
            "tailoring_risk_flags": ["unsupported_claim_review_required"],
            "critic_evidence_refs": ["existing_trace_context.approved_suggestions"],
            "critic_reason_codes": ["patch_supported_by_resume_evidence"],
            "critic_risk_flags": ["human_review_required"],
        },
        resume_profile_payload={
            "resume_id": "resume_primary",
            "evidence_refs": ["resume_profile_payload.sql_airflow_bullet"],
            "tailoring_reason_codes": ["resume_evidence_available"],
            "critic_reason_codes": ["resume_evidence_available"],
        },
        existing_trace_context={
            "jd_evidence_refs": ["existing_trace_context.jd_summary"],
            "tailoring_evidence_refs": ["existing_trace_context.resume_match_gap"],
            "critic_evidence_refs": ["existing_trace_context.critic_summary"],
            "critic_blocking_findings": ["no_real_workflow_block_applied"],
        },
        sidecar_config=config,
        agent_name="shadow_sidecar_chain",
        started_at_utc="2026-06-16T15:00:00Z",
        completed_at_utc="2026-06-16T15:00:01Z",
        duration_ms=1000,
    )


def _enabled_fallback_chain():
    return shadow_sidecar.run_shadow_sidecar_chain(
        sidecar_input=_chain_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED=True,
        )
    )


def _completed_shadow_chain():
    source = _chain_input(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED=True,
    )
    config = source["sidecar_config"]
    results = [
        shadow_sidecar.build_shadow_sidecar_trace_payload(
            sidecar_input=shadow_sidecar.build_shadow_sidecar_input_payload(
                run_id=source["run_id"],
                batch_id=source["batch_id"],
                job_id=source["job_id"],
                stage_name=f"{source['stage_name']}.{agent_name}",
                source_deterministic_stage=source["source_deterministic_stage"],
                source_deterministic_status=source["source_deterministic_status"],
                source_deterministic_score=source["source_deterministic_score"],
                source_deterministic_decision=source["source_deterministic_decision"],
                source_deterministic_reason_codes=source[
                    "source_deterministic_reason_codes"
                ],
                job_payload=source["job_payload"],
                resume_profile_payload=source["resume_profile_payload"],
                existing_trace_context=source["existing_trace_context"],
                sidecar_config=config,
                agent_name=agent_name,
                started_at_utc=source["started_at_utc"],
                completed_at_utc=source["completed_at_utc"],
                duration_ms=source["duration_ms"],
            ),
            sidecar_stage_status="completed_shadow",
            agent_output_status="completed_shadow",
            agent_recommendation="preserve_source_deterministic_decision",
            agent_confidence=0.1,
            agent_reason_codes=[f"{agent_name}_observed"],
            agent_evidence_refs=[f"{agent_name}.evidence"],
            agent_risk_flags=[],
            agent_blocking_findings=[],
            fallback_used=False,
        )
        for agent_name in ["jd_intelligence", "tailoring_suggestion", "critic_guardrail"]
    ]
    return shadow_sidecar.build_shadow_sidecar_chain_payload(
        sidecar_input=source,
        chain_status="completed_shadow_chain",
        agent_results=results,
    )


def _assert_no_mutation_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["observability_only"] is True
    assert safety["manual_review_required"] is True
    assert safety["did_mutate_scoring"] is False
    assert safety["did_change_ranking"] is False
    assert safety["did_mutate_queue"] is False
    assert safety["did_create_approval"] is False
    assert safety["did_mutate_approval"] is False
    assert safety["did_mutate_resume"] is False
    assert safety["did_create_execution_request"] is False
    assert safety["did_create_execution_launch_request"] is False
    assert safety["did_execute_application"] is False
    assert safety["did_submit_application"] is False
    assert safety["pipeline_wiring_added"] is False
    assert safety["auto_apply_enabled"] is False


def test_missing_chain_payload_returns_safe_fallback():
    payload = shadow_sidecar.build_shadow_sidecar_chain_observability_payload(None)

    assert payload["observability_status"] == "observed_missing_source"
    assert payload["enabled_agent_count"] == 0
    assert payload["readiness_decision"]["readiness_status"] == "blocked"
    assert "missing_chain_payload" in payload["readiness_decision"][
        "decision_reason_codes"
    ]
    _assert_no_mutation_safety(payload)


def test_disabled_chain_returns_observed_not_enabled():
    chain = shadow_sidecar.run_shadow_sidecar_chain(sidecar_input=_chain_input())

    payload = shadow_sidecar.build_shadow_sidecar_chain_observability_payload(chain)

    assert payload["observability_status"] == "observed_not_enabled"
    assert payload["source_chain_status"] == "not_enabled"
    assert payload["enabled_agent_count"] == 0
    assert payload["health_status"] == "warning"
    _assert_no_mutation_safety(payload)


def test_kill_switch_chain_returns_observed_blocked_by_kill_switch():
    chain = shadow_sidecar.run_shadow_sidecar_chain(
        sidecar_input=_chain_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH=True,
        )
    )

    payload = shadow_sidecar.build_shadow_sidecar_chain_observability_payload(chain)

    assert payload["observability_status"] == "observed_blocked_by_kill_switch"
    assert payload["source_chain_status"] == "blocked_by_kill_switch"
    assert payload["readiness_decision"]["readiness_status"] == "blocked"
    _assert_no_mutation_safety(payload)


def test_completed_chain_returns_observed_completed_shadow_chain():
    payload = shadow_sidecar.build_shadow_sidecar_chain_observability_payload(
        _completed_shadow_chain()
    )

    assert payload["observability_status"] == "observed_completed_shadow_chain"
    assert payload["source_chain_status"] == "completed_shadow_chain"
    assert payload["enabled_agent_count"] == 3
    assert payload["fallback_count"] == 0
    assert payload["readiness_decision"]["readiness_status"] == "ready"
    assert payload["health_status"] == "healthy"
    _assert_no_mutation_safety(payload)


def test_fallback_chain_returns_observed_completed_with_fallback():
    payload = shadow_sidecar.build_shadow_sidecar_chain_observability_payload(
        _enabled_fallback_chain()
    )

    assert payload["observability_status"] == "observed_completed_with_fallback"
    assert payload["source_chain_status"] == "completed_with_fallback"
    assert payload["enabled_agent_count"] == 3
    assert payload["ordered_agent_names"] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert payload["fallback_count"] == 3
    assert payload["risk_flag_count"] == 3
    assert payload["blocking_finding_count"] == 1
    _assert_no_mutation_safety(payload)


def test_observability_output_includes_evidence_summary_and_counts():
    payload = shadow_sidecar.build_shadow_sidecar_chain_observability_payload(
        _enabled_fallback_chain()
    )

    summary = payload["evidence_summary"]
    assert summary["evidence_summary_type"] == "shadow_sidecar_chain_evidence_summary"
    assert summary["evidence_ref_count"] >= 3
    assert summary["risk_flag_count"] == payload["risk_flag_count"]
    assert summary["blocking_finding_count"] == payload["blocking_finding_count"]
    assert "job_payload.required_skills" in summary["agent_evidence_refs"]
    assert "human_review_required" in summary["agent_risk_flags"]
    assert "no_real_workflow_block_applied" in summary["blocking_findings"]


def test_invalid_chain_payload_returns_observed_invalid_source():
    payload = shadow_sidecar.build_shadow_sidecar_chain_observability_payload(
        {"chain_status": "not_a_real_status"}
    )

    assert payload["observability_status"] == "observed_invalid_source"
    assert payload["readiness_decision"]["readiness_status"] == "blocked"
    assert "invalid_chain_payload" in payload["readiness_decision"][
        "decision_reason_codes"
    ]
    _assert_no_mutation_safety(payload)


def test_shadow_sidecar_observability_has_no_pipeline_api_ui_service_or_storage_wiring():
    source = Path("src/agents/shadow_sidecar.py").read_text(encoding="utf-8")

    forbidden = [
        "from src.pipeline",
        "import src.pipeline",
        "src.app.services",
        "src.app.api",
        "agentic_review.js",
        "create_approval_request(",
        "submit_application(",
        "execute_application(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "upsert_",
        "record_agent_step",
        "create_agent_run",
        "complete_agent_run",
    ]
    for marker in forbidden:
        assert marker not in source

    assert "build_shadow_sidecar_chain_observability_payload" in source
    assert "pipeline_wiring_added" in source
