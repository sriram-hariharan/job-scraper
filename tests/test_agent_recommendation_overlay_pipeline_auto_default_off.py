from __future__ import annotations

from pathlib import Path

from src.agents import agent_recommendation_overlay, shadow_sidecar_hook


GLOBAL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
JD_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED"
AUTO_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_AGENT_RECOMMENDATION_OVERLAY_AUTO_GENERATE_ENABLED"
)
KILL_SWITCH = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"


def _hook_payload(**config):
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(
        run_id="run_overlay_auto",
        batch_id="batch_overlay_auto",
        job_id="job_overlay_auto",
        stage_name="post_final_scoring",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=0.91,
        source_deterministic_decision="qualified_priority_ready",
        source_deterministic_reason_codes=["priority_score_above_threshold"],
        sidecar_config=config,
        job_payload={
            "title": "Data Platform Engineer",
            "job_description": "Build SQL and Airflow data pipelines.",
            "required_skills": ["SQL"],
            "jd_evidence_refs": ["job_payload.required_skills"],
        },
        resume_profile_payload={
            "resume_id": "resume_primary",
            "evidence_refs": ["resume_profile_payload.sql_airflow_bullet"],
        },
        existing_trace_context={
            "trace_id": "trace_overlay_auto",
            "human_reviewed_influence_preview_result": {
                "preview_status": "preview_ready_with_fallback",
                "preview_type": "human_reviewed_shadow_score_influence_preview",
                "proposed_score_adjustment_preview": {
                    "proposed_score_delta": 0.0,
                    "did_mutate_scoring": False,
                },
                "proposed_ranking_effect_preview": {
                    "proposed_ranking_delta": 0,
                    "did_change_ranking": False,
                },
            },
        },
    )


def _assert_no_mutation_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["overlay_only"] is True
    assert safety["pipeline_shadow_only"] is True
    assert safety["human_review_required"] is True
    assert safety["approval_gate_required_for_influence"] is True
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
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    assert payload["requires_live_database"] is False


def _overlay_auto(payload):
    return payload["agent_recommendation_overlay_auto_generation"]


def test_default_environment_does_not_generate_overlay():
    payload = _hook_payload(**{GLOBAL_FLAG: True, JD_FLAG: True})
    auto = _overlay_auto(payload)

    assert auto["auto_generation_status"] == "overlay_auto_generation_not_enabled"
    assert auto["overlay_generated"] is False
    assert auto["blocked_reason"] == (
        "agent_recommendation_overlay_auto_generation_flag_disabled"
    )
    assert auto["agent_recommendation_overlay"] == {}
    assert auto["safety_metadata"]["automatic_generation"] is False
    _assert_no_mutation_safety(auto)


def test_shadow_sidecar_disabled_does_not_generate_overlay():
    payload = _hook_payload(AUTO_FLAG=True, JD_FLAG=True)
    auto = _overlay_auto(payload)

    assert payload["hook_status"] == "hook_not_enabled"
    assert auto["auto_generation_status"] == "overlay_auto_generation_not_enabled"
    assert auto["overlay_generated"] is False
    assert auto["blocked_reason"] == "global_shadow_sidecar_not_enabled"
    _assert_no_mutation_safety(auto)


def test_kill_switch_blocks_overlay_generation_safely():
    payload = _hook_payload(
        **{GLOBAL_FLAG: True, JD_FLAG: True, AUTO_FLAG: True, KILL_SWITCH: True}
    )
    auto = _overlay_auto(payload)

    assert payload["hook_status"] == "hook_blocked_by_kill_switch"
    assert auto["auto_generation_status"] == "overlay_auto_generation_blocked_by_kill_switch"
    assert auto["overlay_generated"] is False
    assert auto["blocked_reason"] == "shadow_sidecar_kill_switch_enabled"
    assert auto["safety_metadata"]["automatic_generation"] is True
    _assert_no_mutation_safety(auto)


def test_enabled_auto_generation_adds_overlay_payload_to_existing_hook_result():
    payload = _hook_payload(**{GLOBAL_FLAG: True, JD_FLAG: True, AUTO_FLAG: True})
    auto = _overlay_auto(payload)
    overlay = auto["agent_recommendation_overlay"]

    assert payload["hook_status"] == "hook_completed_with_fallback"
    assert payload["source_deterministic_score"] == 0.91
    assert payload["source_deterministic_decision"] == "qualified_priority_ready"
    assert auto["auto_generation_status"] in {"overlay_auto_generated", "overlay_auto_generated_partial"}
    assert auto["overlay_generated"] is True
    assert overlay["overlay_status"] in {"overlay_ready", "overlay_partial_insufficient_context"}
    assert overlay["deterministic_decision_context"]["deterministic_score"] == 0.91
    assert overlay["shadow_score_comparison"]["comparison_status"] == (
        "comparison_ready_with_fallback"
    )
    assert overlay["human_reviewed_influence_preview"].get("preview_status", "") in {
        "preview_ready_with_fallback",
        "",
    }
    assert overlay["recommended_review_action"] in {
        "request_influence_approval",
        "review_agent_preview",
        "no_agent_action",
    }
    _assert_no_mutation_safety(auto)


def test_missing_score_comparison_or_influence_preview_context_is_safe_partial():
    payload = shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(
        run_id="run_overlay_partial",
        batch_id="batch_overlay_partial",
        job_id="job_overlay_partial",
        stage_name="post_final_scoring",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=0.64,
        source_deterministic_decision="needs_review",
        sidecar_config={GLOBAL_FLAG: True, AUTO_FLAG: True},
        existing_trace_context={},
    )
    auto = _overlay_auto(payload)
    overlay = auto["agent_recommendation_overlay"]

    assert payload["hook_status"] == "hook_skipped_no_enabled_agents"
    assert auto["auto_generation_status"] == "overlay_auto_generated_partial"
    assert auto["overlay_generated"] is True
    assert overlay["overlay_status"] == "overlay_partial_insufficient_context"
    assert overlay["recommended_review_action"] == "insufficient_context"
    assert "shadow_score_comparison_missing" in {
        finding["finding_code"] for finding in overlay["overlay_findings"]
    }
    assert "human_reviewed_influence_preview_missing" in {
        finding["finding_code"] for finding in overlay["overlay_findings"]
    }
    _assert_no_mutation_safety(auto)


def test_overlay_failure_is_non_blocking(monkeypatch):
    def fail_overlay(**_kwargs):
        raise RuntimeError("overlay boom")

    monkeypatch.setattr(
        agent_recommendation_overlay,
        "build_agent_recommendation_overlay_payload",
        fail_overlay,
    )

    payload = _hook_payload(**{GLOBAL_FLAG: True, JD_FLAG: True, AUTO_FLAG: True})
    auto = _overlay_auto(payload)

    assert payload["hook_status"] == "hook_completed_with_fallback"
    assert auto["auto_generation_status"] == "overlay_auto_generation_failed_non_blocking"
    assert auto["overlay_generated"] is False
    assert auto["error_type"] == "RuntimeError"
    _assert_no_mutation_safety(auto)


def test_collector_passes_auto_overlay_flag_without_new_pipeline_stage():
    source = Path("src/pipeline/collector.py").read_text(encoding="utf-8")

    assert AUTO_FLAG in source
    assert source.count("run_shadow_sidecar_pipeline_hook(") == 1
    assert "agent_recommendation_overlay" not in source
    assert "score_jobs(ai_jobs)" in source
    assert "_maybe_run_shadow_sidecar_after_application_priority(scored_jobs)" in source


def test_hook_overlay_path_has_no_provider_api_service_storage_or_mutation_calls():
    source = Path("src/agents/shadow_sidecar_hook.py").read_text(encoding="utf-8")
    start = source.index("AGENT_RECOMMENDATION_OVERLAY_AUTO_GENERATE_FLAG")
    end = source.index("def run_shadow_sidecar_pipeline_hook")
    snippet = source[start:end]

    forbidden = [
        "src.app.services",
        "src.app.api",
        "agentic_review.js",
        "create_approval_request(",
        "record_approval_decision(",
        "score_resume_job_match",
        "ranking_update",
        "ranking_mutation",
        "application_execution_queue",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "run_chat_completion",
        "openai",
        "anthropic",
        "llm_client",
    ]
    for marker in forbidden:
        assert marker not in snippet

    assert "automatic_generation" in snippet
    assert "pipeline_shadow_only" in snippet


def test_no_schema_change_required_for_auto_overlay():
    combined = "\n".join(
        [
            Path("src/storage/agentic_approvals/schema.sql").read_text(encoding="utf-8"),
            Path("src/storage/agent_trace/schema.sql").read_text(encoding="utf-8"),
        ]
    )

    assert "agent_recommendation_overlay_auto_generation" not in combined
    assert AUTO_FLAG not in combined
