from __future__ import annotations

from copy import deepcopy
from pathlib import Path

from src.agents import agent_recommendation_overlay_readiness as readiness


def _overlay_readback(
    *,
    readback_status: str = "pipeline_generated_overlay_readback_ready",
    auto_generation_status: str = "overlay_auto_generated",
    overlay_status: str = "overlay_ready",
    recommended_review_action: str = "request_influence_approval",
) -> dict:
    overlay = (
        {
            "overlay_status": overlay_status,
            "recommended_review_action": recommended_review_action,
            "safety_metadata": {
                "read_only": True,
                "did_mutate_scoring": False,
                "did_change_ranking": False,
            },
        }
        if overlay_status
        else {}
    )
    generated = (
        {
            "auto_generation_status": auto_generation_status,
            "overlay_generated": bool(overlay),
            "agent_recommendation_overlay": overlay,
        }
        if auto_generation_status
        else {}
    )
    return {
        "readback_status": readback_status,
        "pipeline_generated_overlay_found": bool(generated),
        "pipeline_generated_overlay": generated,
        "agent_recommendation_overlay": overlay,
        "auto_generation_status": auto_generation_status,
        "overlay_status": overlay_status,
        "recommended_review_action": recommended_review_action,
    }


def _assert_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["readiness_summary_only"] is True
    assert safety["advisory_only"] is True
    assert safety["pipeline_generated_overlay_readiness_summary"] is True
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
    assert payload["provider_calls_disabled_in_tests"] is True
    assert payload["requires_live_database"] is False
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0


def test_ready_overlay_returns_reviewable_ready_summary():
    payload = readiness.build_pipeline_generated_agent_recommendation_overlay_readiness_payload(
        overlay_readback_payload=_overlay_readback()
    )

    assert payload["readiness_status"] == "overlay_ready"
    assert payload["reviewable"] is True
    assert payload["partial"] is False
    assert payload["recommended_review_action"] == "request_influence_approval"
    assert payload["reason_codes"] == [
        "pipeline_generated_overlay_ready_for_operator_review"
    ]
    assert payload["blocking_findings"] == []
    assert payload["warning_findings"] == []
    _assert_safety(payload)


def test_partial_overlay_returns_reviewable_partial_summary():
    payload = readiness.build_pipeline_generated_agent_recommendation_overlay_readiness_payload(
        overlay_readback_payload=_overlay_readback(
            auto_generation_status="overlay_auto_generated_partial",
            overlay_status="overlay_partial_insufficient_context",
            recommended_review_action="review_agent_preview",
        )
    )

    assert payload["readiness_status"] == "overlay_partial_reviewable"
    assert payload["reviewable"] is True
    assert payload["partial"] is True
    assert payload["blocking_findings"] == []
    assert payload["warning_findings"] == ["overlay_context_incomplete"]
    _assert_safety(payload)


def test_missing_overlay_returns_safe_not_found_summary():
    payload = readiness.build_pipeline_generated_agent_recommendation_overlay_readiness_payload(
        overlay_readback_payload={
            "readback_status": "pipeline_generated_overlay_not_found",
            "pipeline_generated_overlay_found": False,
            "pipeline_generated_overlay": {},
            "agent_recommendation_overlay": {},
        }
    )

    assert payload["readiness_status"] == "overlay_not_found"
    assert payload["reviewable"] is False
    assert payload["partial"] is False
    assert payload["reason_codes"] == ["pipeline_generated_overlay_not_found"]
    _assert_safety(payload)


def test_blocked_overlay_returns_blocked_summary():
    payload = readiness.build_pipeline_generated_agent_recommendation_overlay_readiness_payload(
        overlay_readback_payload=_overlay_readback(
            auto_generation_status="overlay_auto_generation_blocked_by_kill_switch",
            overlay_status="",
            recommended_review_action="",
        )
    )

    assert payload["readiness_status"] == "overlay_blocked"
    assert payload["reviewable"] is False
    assert payload["blocking_findings"] == ["pipeline_generated_overlay_blocked"]
    _assert_safety(payload)


def test_failed_overlay_returns_non_blocking_failed_summary():
    payload = readiness.build_pipeline_generated_agent_recommendation_overlay_readiness_payload(
        overlay_readback_payload=_overlay_readback(
            readback_status="pipeline_generated_overlay_readback_failed_non_blocking",
            auto_generation_status="overlay_auto_generation_failed_non_blocking",
            overlay_status="",
            recommended_review_action="",
        )
    )

    assert payload["readiness_status"] == "overlay_failed_non_blocking"
    assert payload["reviewable"] is False
    assert payload["blocking_findings"] == []
    assert payload["warning_findings"] == ["retry_read_only_overlay_readback"]
    _assert_safety(payload)


def test_disabled_overlay_returns_disabled_summary():
    payload = readiness.build_pipeline_generated_agent_recommendation_overlay_readiness_payload(
        overlay_readback_payload=_overlay_readback(
            auto_generation_status="overlay_auto_generation_not_enabled",
            overlay_status="",
            recommended_review_action="",
        )
    )

    assert payload["readiness_status"] == "overlay_disabled"
    assert payload["reviewable"] is False
    assert payload["reason_codes"] == ["overlay_auto_generation_not_enabled"]
    _assert_safety(payload)


def test_helper_accepts_hook_and_trace_payloads_without_regenerating_overlay():
    hook_payload = {
        "agent_recommendation_overlay_auto_generation": {
            "auto_generation_status": "overlay_auto_generated_partial",
            "overlay_generated": True,
            "agent_recommendation_overlay": {
                "overlay_status": "overlay_partial_insufficient_context",
                "recommended_review_action": "review_agent_preview",
            },
        }
    }
    before = deepcopy(hook_payload)

    first = readiness.build_pipeline_generated_agent_recommendation_overlay_readiness_payload(
        hook_payload=hook_payload
    )
    second = readiness.build_pipeline_generated_agent_recommendation_overlay_readiness_payload(
        trace_persistence_payload={
            "source_trace_context": hook_payload,
        }
    )

    assert hook_payload == before
    assert first["readiness_status"] == "overlay_partial_reviewable"
    assert second["readiness_status"] == "overlay_partial_reviewable"
    assert first["source_overlay_summary"] == second["source_overlay_summary"]
    _assert_safety(first)
    _assert_safety(second)


def test_helper_source_has_no_regeneration_provider_storage_or_mutation_calls():
    source = Path("src/agents/agent_recommendation_overlay_readiness.py").read_text(
        encoding="utf-8"
    )
    forbidden = [
        "build_agent_recommendation_overlay_payload(",
        "create_agent_run(",
        "record_agent_step(",
        "complete_agent_run(",
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
        "src.app.services",
        "src.app.api",
        "src.pipeline",
    ]
    for marker in forbidden:
        assert marker not in source

    assert (
        "build_pipeline_generated_agent_recommendation_overlay_readback_payload("
        in source
    )


def test_no_schema_change_or_new_pipeline_stage():
    schema_text = "\n".join(
        [
            Path("src/storage/agentic_approvals/schema.sql").read_text(encoding="utf-8"),
            Path("src/storage/agent_trace/schema.sql").read_text(encoding="utf-8"),
        ]
    )
    collector = Path("src/pipeline/collector.py").read_text(encoding="utf-8")

    assert "pipeline_generated_overlay_readiness_summary" not in schema_text
    assert "agent_recommendation_overlay_readiness" not in collector
    assert collector.count("run_shadow_sidecar_pipeline_hook(") == 1
