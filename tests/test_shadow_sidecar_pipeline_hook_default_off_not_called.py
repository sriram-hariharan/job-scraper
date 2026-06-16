from pathlib import Path

from src.agents import shadow_sidecar_hook


def _hook_payload(**config):
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(
        run_id="run_hook",
        batch_id="batch_hook",
        job_id="job_hook",
        stage_name="post_final_scoring",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=0.86,
        source_deterministic_decision="qualified_for_review",
        source_deterministic_reason_codes=["priority_score_above_threshold"],
        sidecar_config=config,
        job_payload={
            "title": "Data Platform Engineer",
            "job_description": "Build SQL and Airflow data pipelines.",
            "required_skills": ["SQL"],
            "jd_evidence_refs": ["job_payload.required_skills"],
            "jd_reason_codes": ["jd_required_skills_present"],
        },
        resume_profile_payload={
            "resume_id": "resume_primary",
            "evidence_refs": ["resume_profile_payload.sql_airflow_bullet"],
        },
        existing_trace_context={
            "trace_id": "trace_hook",
            "critic_blocking_findings": ["no_real_workflow_block_applied"],
        },
    )


def _assert_no_mutation_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["pipeline_hook_available"] is True
    assert safety["pipeline_hook_called_by_pipeline"] is False
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


def test_hook_is_default_off_and_does_not_attempt_chain():
    payload = _hook_payload(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
    )

    assert payload["hook_status"] == "hook_not_enabled"
    assert payload["hook_called"] is True
    assert payload["chain_attempted"] is False
    assert payload["chain_payload"] == {}
    assert payload["source_deterministic_decision"] == "qualified_for_review"
    _assert_no_mutation_safety(payload)


def test_kill_switch_blocks_the_hook():
    payload = _hook_payload(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH=True,
    )

    assert payload["hook_status"] == "hook_blocked_by_kill_switch"
    assert payload["chain_attempted"] is False
    assert payload["next_safe_step"] == "keep_shadow_sidecar_disabled"
    _assert_no_mutation_safety(payload)


def test_missing_context_blocks_safely():
    payload = shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(
        sidecar_config={
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED": True,
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED": True,
        }
    )

    assert payload["hook_status"] == "hook_blocked_missing_context"
    assert payload["chain_attempted"] is False
    assert payload["readiness_decision"]["readiness_status"] == "blocked"
    _assert_no_mutation_safety(payload)


def test_unsupported_stage_blocks_safely():
    payload = shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(
        run_id="run_hook",
        batch_id="batch_hook",
        job_id="job_hook",
        stage_name="unsupported_stage",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=0.86,
        source_deterministic_decision="qualified_for_review",
        source_deterministic_reason_codes=["priority_score_above_threshold"],
        sidecar_config={
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED": True,
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED": True,
        },
    )

    assert payload["hook_status"] == "hook_blocked_unsupported_stage"
    assert payload["chain_attempted"] is False
    assert payload["supported_stage"] is False
    _assert_no_mutation_safety(payload)


def test_supported_stage_with_no_enabled_agents_skips_safely():
    payload = _hook_payload(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
    )

    assert payload["hook_status"] == "hook_skipped_no_enabled_agents"
    assert payload["chain_attempted"] is False
    assert payload["enabled_agent_names"] == []
    _assert_no_mutation_safety(payload)


def test_supported_stage_with_jd_enabled_calls_isolated_chain_runner_with_fallback():
    payload = _hook_payload(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
    )

    assert payload["hook_status"] == "hook_completed_with_fallback"
    assert payload["chain_attempted"] is True
    assert payload["chain_payload"]["chain_status"] == "completed_with_fallback"
    assert payload["chain_payload"]["stage_order"] == ["jd_intelligence"]
    assert payload["observability_payload"]["observability_status"] == (
        "observed_completed_with_fallback"
    )
    assert payload["readiness_decision"]["readiness_status"] == "blocked"
    _assert_no_mutation_safety(payload)


def test_provider_calls_are_not_made_in_tests():
    calls = []

    def provider(_payload):
        calls.append("called")
        return {"agent_recommendation": "should_not_run"}

    payload = _hook_payload(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
        provider_execution_allowed=True,
        shadow_agent=provider,
    )

    assert calls == []
    assert payload["hook_status"] == "hook_completed_with_fallback"
    assert payload["provider_calls_disabled_in_tests"] is True
    assert payload["chain_payload"]["ordered_agent_results"][0]["provider_mode"] == "disabled"
    _assert_no_mutation_safety(payload)


def test_output_preserves_deterministic_source_decision_fields():
    payload = _hook_payload(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
    )

    assert payload["source_deterministic_stage"] == "application_priority"
    assert payload["source_deterministic_status"] == "completed"
    assert payload["source_deterministic_score"] == 0.86
    assert payload["source_deterministic_decision"] == "qualified_for_review"
    assert payload["source_deterministic_reason_codes"] == [
        "priority_score_above_threshold"
    ]
    assert payload["live_production_pipeline_connected_agents"] == 0
    assert payload["live_agents_allowed_to_automate_mutations"] == 0


def test_exactly_one_default_off_production_pipeline_call_site_is_added():
    pipeline_files = sorted(Path("src/pipeline").glob("*.py"))
    assert pipeline_files
    call_sites = []
    for path in pipeline_files:
        text = path.read_text(encoding="utf-8")
        if "run_shadow_sidecar_pipeline_hook(" in text:
            call_sites.append(path.as_posix())

    assert call_sites == ["src/pipeline/collector.py"]


def test_shadow_sidecar_hook_has_no_api_ui_service_or_storage_wiring():
    source = Path("src/agents/shadow_sidecar_hook.py").read_text(encoding="utf-8")

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

    assert "pipeline_hook_called_by_pipeline" in source
    assert "pipeline_wiring_added" in source
