from copy import deepcopy
from pathlib import Path

from src.agents import shadow_sidecar


def _chain_input(**config):
    return shadow_sidecar.build_shadow_sidecar_input_payload(
        run_id="run_shadow_chain",
        batch_id="batch_shadow_chain",
        job_id="job_shadow_chain",
        stage_name="post_deterministic_evaluation_shadow_chain",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=0.89,
        source_deterministic_decision="qualified_for_review",
        source_deterministic_reason_codes=["score_above_review_threshold"],
        job_payload={
            "title": "Data Platform Engineer",
            "job_description": "Build SQL and Airflow data pipelines.",
            "required_skills": ["SQL"],
            "required_tools": ["Airflow"],
            "jd_evidence_refs": ["job_payload.required_skills"],
            "jd_reason_codes": ["jd_required_skills_present"],
            "tailoring_evidence_refs": ["resume_profile_payload.sql_airflow_bullet"],
            "tailoring_reason_codes": ["tailoring_gap_supported_by_resume"],
            "critic_evidence_refs": ["existing_trace_context.approved_suggestions"],
            "critic_reason_codes": ["patch_supported_by_resume_evidence"],
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
        started_at_utc="2026-06-16T14:00:00Z",
        completed_at_utc="2026-06-16T14:00:01Z",
        duration_ms=1000,
    )


def _assert_no_mutation_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
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


def test_chain_remains_not_enabled_when_global_sidecar_is_disabled():
    source = _chain_input(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED=True,
    )
    original = deepcopy(source)

    payload = shadow_sidecar.run_shadow_sidecar_chain(sidecar_input=source)

    assert payload["chain_status"] == "not_enabled"
    assert payload["ordered_agent_results"] == []
    assert payload["source_deterministic_decision"] == "qualified_for_review"
    assert "global_sidecar_flag_disabled" in payload["readiness_decision"][
        "decision_reason_codes"
    ]
    assert source == original
    _assert_no_mutation_safety(payload)


def test_kill_switch_blocks_the_chain():
    payload = shadow_sidecar.run_shadow_sidecar_chain(
        sidecar_input=_chain_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH=True,
        )
    )

    assert payload["chain_status"] == "blocked_by_kill_switch"
    assert payload["ordered_agent_results"] == []
    assert payload["readiness_decision"]["readiness_status"] == "blocked"
    assert "blocked_by_kill_switch" in payload["readiness_decision"][
        "decision_reason_codes"
    ]
    _assert_no_mutation_safety(payload)


def test_provider_calls_are_not_made_by_the_chain_runner():
    calls = []

    def provider(_payload):
        calls.append("called")
        return {"agent_recommendation": "should_not_run"}

    payload = shadow_sidecar.run_shadow_sidecar_chain(
        sidecar_input=_chain_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
            provider_execution_allowed=True,
            shadow_agent=provider,
        )
    )

    assert calls == []
    assert payload["chain_status"] == "completed_with_fallback"
    assert payload["ordered_agent_results"][0]["provider_mode"] == "disabled"
    assert payload["sidecar_config"]["provider_calls_disabled_in_tests"] is True
    _assert_no_mutation_safety(payload)


def test_chain_runs_only_enabled_per_agent_mappings():
    payload = shadow_sidecar.run_shadow_sidecar_chain(
        sidecar_input=_chain_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED=True,
        )
    )

    assert payload["chain_status"] == "completed_with_fallback"
    assert payload["stage_order"] == ["jd_intelligence", "critic_guardrail"]
    assert set(payload["stage_statuses"]) == {"jd_intelligence", "critic_guardrail"}
    assert "tailoring_suggestion" not in payload["stage_statuses"]
    _assert_no_mutation_safety(payload)


def test_chain_runs_all_three_mappings_in_deterministic_order():
    payload = shadow_sidecar.run_shadow_sidecar_chain(
        sidecar_input=_chain_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED=True,
        )
    )

    assert payload["chain_status"] == "completed_with_fallback"
    assert payload["stage_order"] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert [result["agent_name"] for result in payload["ordered_agent_results"]] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert all(
        result["sidecar_stage_status"] == "completed_with_fallback"
        for result in payload["ordered_agent_results"]
    )
    _assert_no_mutation_safety(payload)


def test_chain_output_includes_aggregate_trace_evidence_readiness_and_health():
    payload = shadow_sidecar.run_shadow_sidecar_chain(
        sidecar_input=_chain_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED=True,
        )
    )

    assert payload["trace_bundle"]["bundle_type"] == "shadow_sidecar_chain_trace_bundle"
    assert payload["evidence_pack"]["evidence_pack_type"] == (
        "shadow_sidecar_chain_evidence_pack"
    )
    assert payload["readiness_decision"]["readiness_status"] == "blocked"
    assert payload["health_status"] == "warning"
    assert "job_payload.required_skills" in payload["evidence_pack"][
        "agent_evidence_refs"
    ]
    assert "resume_profile_payload.sql_airflow_bullet" in payload["evidence_pack"][
        "agent_evidence_refs"
    ]
    assert "no_real_workflow_block_applied" in payload["readiness_decision"][
        "blocking_findings"
    ]


def test_chain_preserves_deterministic_source_decision_fields():
    payload = shadow_sidecar.run_shadow_sidecar_chain(
        sidecar_input=_chain_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
        )
    )

    assert payload["source_deterministic_stage"] == "application_priority"
    assert payload["source_deterministic_status"] == "completed"
    assert payload["source_deterministic_score"] == 0.89
    assert payload["source_deterministic_decision"] == "qualified_for_review"
    assert payload["source_deterministic_reason_codes"] == [
        "score_above_review_threshold"
    ]
    assert payload["live_production_pipeline_connected_agents"] == 0
    assert payload["live_agents_allowed_to_automate_mutations"] == 0


def test_shadow_sidecar_chain_has_no_pipeline_api_ui_service_or_storage_wiring():
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

    assert "run_shadow_sidecar_chain" in source
    assert "pipeline_wiring_added" in source
