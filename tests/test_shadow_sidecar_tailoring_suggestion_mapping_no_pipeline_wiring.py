from pathlib import Path

from src.agents import shadow_sidecar


def _tailoring_sidecar_input(**config):
    return shadow_sidecar.build_shadow_sidecar_input_payload(
        run_id="run_tailoring_shadow",
        batch_id="batch_tailoring_shadow",
        job_id="job_tailoring_shadow",
        stage_name="tailoring_suggestion_shadow_sidecar",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=0.88,
        source_deterministic_decision="tailor_first",
        source_deterministic_reason_codes=["credible_match_with_tailoring_gap"],
        job_payload={
            "title": "Data Platform Engineer",
            "tailoring_evidence_refs": [
                "resume_profile_payload.bullet_analytics_platform",
            ],
            "tailoring_reason_codes": ["tailoring_gap_supported_by_resume"],
            "tailoring_risk_flags": ["unsupported_claim_review_required"],
        },
        resume_profile_payload={
            "resume_id": "resume_primary",
            "evidence_refs": ["resume_profile_payload.sql_airflow_bullet"],
            "tailoring_reason_codes": ["resume_evidence_available"],
        },
        existing_trace_context={
            "tailoring_evidence_refs": ["existing_trace_context.resume_match_gap"],
            "tailoring_reason_codes": ["existing_trace_tailoring_context"],
            "unsupported_claim_risks": ["metric_requires_evidence"],
        },
        sidecar_config=config,
        agent_name="tailoring_suggestion",
        started_at_utc="2026-06-16T12:00:00Z",
        completed_at_utc="2026-06-16T12:00:01Z",
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


def test_tailoring_mapping_is_not_enabled_when_global_sidecar_flag_is_disabled():
    payload = shadow_sidecar.run_shadow_sidecar_agent(
        sidecar_input=_tailoring_sidecar_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=True,
        )
    )

    assert payload["sidecar_stage_status"] == "not_enabled"
    assert payload["agent_name"] == "tailoring_suggestion"
    assert payload["source_deterministic_decision"] == "tailor_first"
    assert "global_sidecar_flag_disabled" in payload["agent_reason_codes"]
    _assert_no_mutation_safety(payload)


def test_tailoring_mapping_is_skipped_when_per_agent_flag_is_disabled():
    payload = shadow_sidecar.run_shadow_sidecar_agent(
        sidecar_input=_tailoring_sidecar_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        )
    )

    assert payload["sidecar_stage_status"] == "skipped_by_config"
    assert "per_agent_sidecar_flag_disabled" in payload["agent_reason_codes"]
    assert payload["source_deterministic_score"] == 0.88
    _assert_no_mutation_safety(payload)


def test_kill_switch_blocks_tailoring_sidecar_work():
    payload = shadow_sidecar.run_shadow_sidecar_agent(
        sidecar_input=_tailoring_sidecar_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH=True,
        )
    )

    assert payload["sidecar_stage_status"] == "blocked_by_kill_switch"
    assert payload["readiness_decision"]["readiness_status"] == "blocked"
    assert "blocked_by_kill_switch" in payload["agent_reason_codes"]
    _assert_no_mutation_safety(payload)


def test_provider_calls_are_not_made_for_tailoring_mapping_in_tests():
    calls = []

    def provider(_payload):
        calls.append("called")
        return {"agent_recommendation": "should_not_run"}

    payload = shadow_sidecar.run_shadow_sidecar_agent(
        sidecar_input=_tailoring_sidecar_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=True,
        ),
        shadow_agent=provider,
    )

    assert calls == []
    assert payload["sidecar_stage_status"] == "completed_with_fallback"
    assert "provider_execution_unavailable_or_disallowed" in payload["agent_reason_codes"]
    assert payload["provider_mode"] == "disabled"
    assert payload["sidecar_config"]["provider_calls_disabled_in_tests"] is True
    _assert_no_mutation_safety(payload)


def test_tailoring_mapping_returns_deterministic_fallback_with_evidence_hints():
    payload = shadow_sidecar.run_shadow_sidecar_agent(
        sidecar_input=_tailoring_sidecar_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=True,
            provider_execution_allowed=False,
        )
    )

    assert payload["sidecar_stage_status"] == "completed_with_fallback"
    assert payload["fallback_used"] is True
    assert payload["agent_mode"] == "shadow_sidecar"
    assert payload["provider_mode"] == "disabled"
    assert payload["agent_recommendation"] == "preserve_source_deterministic_decision"
    assert "tailoring_gap_supported_by_resume" in payload["agent_reason_codes"]
    assert "resume_evidence_available" in payload["agent_reason_codes"]
    assert "existing_trace_tailoring_context" in payload["agent_reason_codes"]
    assert "tailoring_shadow_signals_observed" in payload["agent_reason_codes"]
    assert "resume_profile_payload.bullet_analytics_platform" in payload["agent_evidence_refs"]
    assert "existing_trace_context.resume_match_gap" in payload["agent_evidence_refs"]
    assert "unsupported_claim_review_required" in payload["agent_risk_flags"]
    assert "metric_requires_evidence" in payload["agent_risk_flags"]
    _assert_no_mutation_safety(payload)


def test_tailoring_mapping_preserves_source_decision_and_trace_sections():
    payload = shadow_sidecar.run_shadow_sidecar_agent(
        sidecar_input=_tailoring_sidecar_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=True,
        )
    )

    assert payload["source_deterministic_stage"] == "application_priority"
    assert payload["source_deterministic_status"] == "completed"
    assert payload["source_deterministic_score"] == 0.88
    assert payload["source_deterministic_decision"] == "tailor_first"
    assert payload["source_deterministic_reason_codes"] == [
        "credible_match_with_tailoring_gap"
    ]
    assert payload["trace_bundle"]["bundle_type"] == "shadow_sidecar_trace_bundle"
    assert payload["evidence_pack"]["evidence_pack_type"] == "shadow_sidecar_evidence_pack"
    assert payload["readiness_decision"]["readiness_status"] == "blocked"
    assert payload["health_status"] == "warning"


def test_tailoring_mapping_does_not_generate_or_mutate_resume_content():
    payload = shadow_sidecar.run_shadow_sidecar_agent(
        sidecar_input=_tailoring_sidecar_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=True,
        )
    )

    assert "suggested_text" not in payload
    assert "patch_ready_suggestions" not in payload
    assert payload["safety_metadata"]["did_mutate_resume"] is False
    assert payload["agent_recommendation"] == "preserve_source_deterministic_decision"


def test_shadow_sidecar_has_no_pipeline_api_ui_service_or_tailoring_provider_wiring():
    source = Path("src/agents/shadow_sidecar.py").read_text(encoding="utf-8")

    forbidden = [
        "from src.pipeline",
        "import src.pipeline",
        "src.app.services",
        "src.app.api",
        "agentic_review.js",
        "build_tailoring_suggestion_dry_run_payload",
        "create_approval_request(",
        "submit_application(",
        "execute_application(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "record_agent_step",
        "create_agent_run",
        "complete_agent_run",
    ]
    for marker in forbidden:
        assert marker not in source

    assert "APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED" in source
    assert "pipeline_wiring_added" in source
