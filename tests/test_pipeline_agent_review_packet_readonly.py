from copy import deepcopy
from pathlib import Path

from src.agents import pipeline_agent_review_packet as review_packet


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
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["review_packet_only"] is True
    assert safety["pipeline_agent_review_packet"] is True
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
    assert safety["api_route_added"] is False
    assert safety["ui_action_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False
    assert payload["provider_calls_disabled_in_tests"] is True
    assert payload["requires_live_database"] is False
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0


def test_ready_overlay_creates_reviewable_packet():
    source = _overlay_readback()
    before = deepcopy(source)

    payload = review_packet.build_pipeline_agent_review_packet_payload(
        overlay_readback_payload=source,
        trace_context_payload={
            "trace_id": "trace_packet_ready",
            "source_deterministic_stage": "application_priority",
            "source_deterministic_score": 0.91,
            "source_deterministic_decision": "qualified_priority_ready",
        },
    )

    assert source == before
    assert payload["packet_status"] == "review_packet_ready"
    assert payload["overlay_found"] is True
    assert payload["overlay_readiness_status"] == "overlay_ready"
    assert payload["overlay_reviewability"] == {
        "reviewable": True,
        "partial": False,
    }
    assert payload["recommended_operator_action"] == "request_influence_approval"
    assert payload["evaluation_boundaries"] == {
        "prefilter_relevance": "upstream_deterministic_filter_preserved",
        "shadow_evaluation": "advisory_read_only",
        "final_application_scoring": "unchanged",
    }
    assert payload["trace_context_summary"]["trace_id"] == "trace_packet_ready"
    assert payload["trace_context_summary"]["source_deterministic_score"] == 0.91
    _assert_safety(payload)


def test_partial_overlay_creates_reviewable_partial_packet():
    payload = review_packet.build_pipeline_agent_review_packet_payload(
        overlay_readback_payload=_overlay_readback(
            auto_generation_status="overlay_auto_generated_partial",
            overlay_status="overlay_partial_insufficient_context",
            recommended_review_action="review_agent_preview",
        )
    )

    assert payload["packet_status"] == "review_packet_partial_reviewable"
    assert payload["overlay_readiness_status"] == "overlay_partial_reviewable"
    assert payload["overlay_reviewability"] == {
        "reviewable": True,
        "partial": True,
    }
    assert "review_partial_overlay_and_missing_context" in payload["review_focus"]
    assert "overlay_context_incomplete" in payload["review_focus"]
    _assert_safety(payload)


def test_packet_accepts_generated_container_and_inner_overlay_shapes():
    from_generated = review_packet.build_pipeline_agent_review_packet_payload(
        pipeline_generated_overlay_payload={
            "auto_generation_status": "overlay_auto_generated",
            "overlay_generated": True,
            "agent_recommendation_overlay": {
                "overlay_status": "overlay_ready",
                "recommended_review_action": "request_influence_approval",
            },
        }
    )
    from_overlay = review_packet.build_pipeline_agent_review_packet_payload(
        agent_recommendation_overlay_payload={
            "overlay_status": "overlay_partial_insufficient_context",
            "recommended_review_action": "review_agent_preview",
        }
    )

    assert from_generated["packet_status"] == "review_packet_ready"
    assert from_overlay["packet_status"] == "review_packet_partial_reviewable"
    _assert_safety(from_generated)
    _assert_safety(from_overlay)


def test_missing_overlay_creates_safe_not_found_packet():
    payload = review_packet.build_pipeline_agent_review_packet_payload(
        overlay_readback_payload={
            "readback_status": "pipeline_generated_overlay_not_found",
            "pipeline_generated_overlay_found": False,
            "pipeline_generated_overlay": {},
            "agent_recommendation_overlay": {},
        }
    )

    assert payload["packet_status"] == "review_packet_not_found"
    assert payload["overlay_found"] is False
    assert payload["overlay_readiness_status"] == "overlay_not_found"
    assert payload["overlay_reviewability"]["reviewable"] is False
    _assert_safety(payload)


def test_blocked_failed_and_disabled_overlays_create_safe_packets():
    cases = [
        (
            _overlay_readback(
                auto_generation_status=(
                    "overlay_auto_generation_blocked_by_kill_switch"
                ),
                overlay_status="",
                recommended_review_action="",
            ),
            "review_packet_blocked",
            "overlay_blocked",
        ),
        (
            _overlay_readback(
                readback_status=(
                    "pipeline_generated_overlay_readback_failed_non_blocking"
                ),
                auto_generation_status=(
                    "overlay_auto_generation_failed_non_blocking"
                ),
                overlay_status="",
                recommended_review_action="",
            ),
            "review_packet_failed_non_blocking",
            "overlay_failed_non_blocking",
        ),
        (
            _overlay_readback(
                auto_generation_status="overlay_auto_generation_not_enabled",
                overlay_status="",
                recommended_review_action="",
            ),
            "review_packet_disabled",
            "overlay_disabled",
        ),
    ]

    for source, packet_status, readiness_status in cases:
        payload = review_packet.build_pipeline_agent_review_packet_payload(
            overlay_readback_payload=source
        )
        assert payload["packet_status"] == packet_status
        assert payload["overlay_readiness_status"] == readiness_status
        assert payload["overlay_reviewability"]["reviewable"] is False
        assert payload["recommended_operator_action"]
        _assert_safety(payload)


def test_packet_uses_readback_and_readiness_helper_behavior(monkeypatch):
    calls = []
    real_readback = (
        review_packet.agent_recommendation_overlay_readback.build_pipeline_generated_agent_recommendation_overlay_readback_payload
    )
    real_readiness = (
        review_packet.agent_recommendation_overlay_readiness.build_pipeline_generated_agent_recommendation_overlay_readiness_payload
    )

    def recording_readback(**kwargs):
        calls.append(("readback", deepcopy(kwargs)))
        return real_readback(**kwargs)

    def recording_readiness(**kwargs):
        calls.append(("readiness", deepcopy(kwargs)))
        return real_readiness(**kwargs)

    monkeypatch.setattr(
        review_packet.agent_recommendation_overlay_readback,
        "build_pipeline_generated_agent_recommendation_overlay_readback_payload",
        recording_readback,
    )
    monkeypatch.setattr(
        review_packet.agent_recommendation_overlay_readiness,
        "build_pipeline_generated_agent_recommendation_overlay_readiness_payload",
        recording_readiness,
    )
    hook = {
        "agent_recommendation_overlay_auto_generation": {
            "auto_generation_status": "overlay_auto_generated_partial",
            "overlay_generated": True,
            "agent_recommendation_overlay": {
                "overlay_status": "overlay_partial_insufficient_context",
                "recommended_review_action": "review_agent_preview",
            },
        },
        "stage_name": "post_final_scoring",
        "source_deterministic_stage": "application_priority",
        "source_deterministic_decision": "qualified_priority_ready",
    }

    payload = review_packet.build_pipeline_agent_review_packet_payload(
        hook_payload=hook
    )

    assert [name for name, _kwargs in calls] == ["readback", "readiness"]
    assert payload["packet_status"] == "review_packet_partial_reviewable"
    assert payload["trace_context_summary"]["stage_name"] == "post_final_scoring"


def test_packet_source_has_no_regeneration_provider_storage_or_mutation_calls():
    source = Path("src/agents/pipeline_agent_review_packet.py").read_text(
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
        "insert_",
        "update_",
        "upsert_",
        "delete_",
        "run_chat_completion",
        "openai",
        "anthropic",
        "llm_client",
        "workflow_runner",
        "src.app.api",
        "src.app.services",
        "src.pipeline",
    ]
    for marker in forbidden:
        assert marker not in source

    assert (
        "build_pipeline_generated_agent_recommendation_overlay_readback_payload("
        in source
    )
    assert (
        "build_pipeline_generated_agent_recommendation_overlay_readiness_payload("
        in source
    )


def test_packet_adds_no_api_ui_schema_or_pipeline_wiring():
    marker = "pipeline_agent_review_packet"
    protected_paths = [
        Path("src/app/api.py"),
        Path("src/app/services.py"),
        Path("src/app/static/agentic_review.js"),
        Path("src/storage/agent_trace/schema.sql"),
        Path("src/storage/agentic_approvals/schema.sql"),
        Path("src/pipeline/collector.py"),
    ]

    for path in protected_paths:
        assert marker not in path.read_text(encoding="utf-8")

    collector = Path("src/pipeline/collector.py").read_text(encoding="utf-8")
    assert collector.count("run_shadow_sidecar_pipeline_hook(") == 1
