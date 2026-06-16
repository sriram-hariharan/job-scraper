from pathlib import Path

from src.agents import shadow_sidecar


def _hook_preview(**config):
    return shadow_sidecar.build_shadow_sidecar_pipeline_hook_preview_payload(
        run_id="run_hook_preview",
        batch_id="batch_hook_preview",
        job_id="job_hook_preview",
        stage_name="post_filter_evaluation",
        source_deterministic_stage="filter_evaluation",
        source_deterministic_status="completed",
        source_deterministic_score=0.81,
        source_deterministic_decision="qualified_for_review",
        source_deterministic_reason_codes=["deterministic_filter_passed"],
        sidecar_config=config,
        job_payload={"title": "Data Platform Engineer"},
        resume_profile_payload={"resume_id": "resume_primary"},
        existing_trace_context={"trace_id": "trace_hook_preview"},
    )


def _assert_no_mutation_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["hook_preview_only"] is True
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


def test_missing_context_blocks_safely():
    payload = shadow_sidecar.build_shadow_sidecar_pipeline_hook_preview_payload(
        sidecar_config={
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED": True,
        },
    )

    assert payload["hook_preview_status"] == "hook_blocked_missing_context"
    assert "run_id" in payload["missing_context_fields"]
    assert "stage_name" in payload["missing_context_fields"]
    assert payload["readiness_decision"]["readiness_status"] == "blocked"
    _assert_no_mutation_safety(payload)


def test_global_disabled_returns_hook_not_enabled():
    payload = _hook_preview(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
    )

    assert payload["hook_preview_status"] == "hook_not_enabled"
    assert payload["supported_stage"] is True
    assert payload["enabled_agent_names"] == ["jd_intelligence"]
    assert payload["next_safe_step"] == "enable_global_shadow_sidecar_flag_for_preview_only"
    _assert_no_mutation_safety(payload)


def test_kill_switch_returns_hook_blocked_by_kill_switch():
    payload = _hook_preview(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH=True,
    )

    assert payload["hook_preview_status"] == "hook_blocked_by_kill_switch"
    assert payload["readiness_decision"]["blocking_findings"] == [
        "keep_shadow_sidecar_disabled"
    ]
    _assert_no_mutation_safety(payload)


def test_unsupported_stage_blocks_safely():
    payload = shadow_sidecar.build_shadow_sidecar_pipeline_hook_preview_payload(
        run_id="run_hook_preview",
        batch_id="batch_hook_preview",
        job_id="job_hook_preview",
        stage_name="unsupported_stage",
        source_deterministic_stage="filter_evaluation",
        source_deterministic_status="completed",
        source_deterministic_score=0.81,
        source_deterministic_decision="qualified_for_review",
        source_deterministic_reason_codes=["deterministic_filter_passed"],
        sidecar_config={
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED": True,
            "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED": True,
        },
    )

    assert payload["hook_preview_status"] == "hook_blocked_unsupported_stage"
    assert payload["supported_stage"] is False
    assert payload["supported_stages"] == [
        "post_filter_evaluation",
        "post_final_scoring",
        "pre_human_review",
    ]
    _assert_no_mutation_safety(payload)


def test_supported_stage_with_no_enabled_agents_returns_skipped():
    payload = _hook_preview(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
    )

    assert payload["hook_preview_status"] == "hook_skipped_no_enabled_agents"
    assert payload["enabled_agent_names"] == []
    assert payload["disabled_agent_names"] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    _assert_no_mutation_safety(payload)


def test_supported_stage_with_jd_enabled_is_ready():
    payload = _hook_preview(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
    )

    assert payload["hook_preview_status"] == "hook_ready_for_shadow_sidecar"
    assert payload["enabled_agent_names"] == ["jd_intelligence"]
    assert payload["disabled_agent_names"] == [
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert payload["readiness_decision"]["readiness_status"] == "ready"
    _assert_no_mutation_safety(payload)


def test_supported_stage_with_all_three_enabled_is_ready():
    payload = _hook_preview(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED=True,
    )

    assert payload["hook_preview_status"] == "hook_ready_for_shadow_sidecar"
    assert payload["enabled_agent_names"] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert payload["disabled_agent_names"] == []
    assert payload["provider_calls_disabled_in_tests"] is True
    _assert_no_mutation_safety(payload)


def test_output_preserves_deterministic_source_decision_fields():
    payload = _hook_preview(
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
        APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
    )

    assert payload["source_deterministic_stage"] == "filter_evaluation"
    assert payload["source_deterministic_status"] == "completed"
    assert payload["source_deterministic_score"] == 0.81
    assert payload["source_deterministic_decision"] == "qualified_for_review"
    assert payload["source_deterministic_reason_codes"] == [
        "deterministic_filter_passed"
    ]
    assert payload["live_production_pipeline_connected_agents"] == 0
    assert payload["live_agents_allowed_to_automate_mutations"] == 0


def test_shadow_sidecar_hook_preview_has_no_pipeline_api_ui_service_or_storage_wiring():
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

    assert "build_shadow_sidecar_pipeline_hook_preview_payload" in source
    assert "pipeline_wiring_added" in source
