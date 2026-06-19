from copy import deepcopy
from pathlib import Path

from src.app import services


HELPER_NAME = "pipeline_generated_overlay_review_packet_service_payload"


def _overlay_readback(
    *,
    auto_generation_status: str = "overlay_auto_generated",
    overlay_status: str = "overlay_ready",
    recommended_review_action: str = "request_influence_approval",
) -> dict:
    overlay = {
        "overlay_status": overlay_status,
        "recommended_review_action": recommended_review_action,
    }
    return {
        "readback_status": "pipeline_generated_overlay_readback_ready",
        "pipeline_generated_overlay_found": True,
        "pipeline_generated_overlay": {
            "auto_generation_status": auto_generation_status,
            "overlay_generated": True,
            "agent_recommendation_overlay": overlay,
        },
        "agent_recommendation_overlay": overlay,
        "auto_generation_status": auto_generation_status,
        "overlay_status": overlay_status,
        "recommended_review_action": recommended_review_action,
    }


def _assert_service_safety(payload: dict) -> None:
    safety = payload["safety_metadata"]
    assert payload["service_surface"] == (
        "pipeline_generated_overlay_review_packet_service"
    )
    assert payload["service_helper_only"] is True
    assert payload["api_route_added"] is False
    assert payload["ui_action_added"] is False
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["review_packet_only"] is True
    assert safety["read_only"] is True
    assert safety["service_helper_only"] is True
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


def test_service_helper_returns_review_packet_for_ready_overlay():
    source = _overlay_readback()
    before = deepcopy(source)

    payload = getattr(services, HELPER_NAME)(
        overlay_readback_payload=source,
        trace_context_payload={
            "trace_id": "trace_service_packet",
            "source_deterministic_stage": "application_priority",
        },
    )

    assert source == before
    assert payload["packet_status"] == "review_packet_ready"
    assert payload["overlay_readiness_status"] == "overlay_ready"
    assert payload["overlay_reviewability"] == {
        "reviewable": True,
        "partial": False,
    }
    assert payload["trace_context_summary"]["trace_id"] == "trace_service_packet"
    _assert_service_safety(payload)


def test_service_helper_returns_reviewable_partial_packet():
    payload = getattr(services, HELPER_NAME)(
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
    _assert_service_safety(payload)


def test_service_helper_returns_safe_not_found_packet():
    payload = getattr(services, HELPER_NAME)(
        overlay_readback_payload={
            "readback_status": "pipeline_generated_overlay_not_found",
            "pipeline_generated_overlay_found": False,
            "pipeline_generated_overlay": {},
            "agent_recommendation_overlay": {},
        }
    )

    assert payload["packet_status"] == "review_packet_not_found"
    assert payload["overlay_found"] is False
    assert payload["overlay_reviewability"]["reviewable"] is False
    _assert_service_safety(payload)


def test_service_helper_accepts_hook_trace_and_overlay_shapes():
    from_hook = getattr(services, HELPER_NAME)(
        hook_payload={
            "agent_recommendation_overlay_auto_generation": {
                "auto_generation_status": "overlay_auto_generated_partial",
                "overlay_generated": True,
                "agent_recommendation_overlay": {
                    "overlay_status": "overlay_partial_insufficient_context",
                    "recommended_review_action": "review_agent_preview",
                },
            }
        }
    )
    from_overlay = getattr(services, HELPER_NAME)(
        agent_recommendation_overlay_payload={
            "overlay_status": "overlay_ready",
            "recommended_review_action": "request_influence_approval",
        }
    )

    assert from_hook["packet_status"] == "review_packet_partial_reviewable"
    assert from_overlay["packet_status"] == "review_packet_ready"
    _assert_service_safety(from_hook)
    _assert_service_safety(from_overlay)


def test_service_helper_slice_has_no_provider_storage_or_mutation_calls():
    source = Path("src/app/services.py").read_text(encoding="utf-8")
    start = source.index(f"def {HELPER_NAME}(")
    next_function = source.find("\ndef ", start + 1)
    if next_function == -1:
        next_function = len(source)
    helper_source = source[start:next_function]
    forbidden = [
        "@app.",
        "router.",
        "src.pipeline",
        "schema.sql",
        "build_agent_recommendation_overlay_payload(",
        "score_resume_job_match(",
        "ranking_update",
        "ranking_mutation",
        "application_execution_queue",
        "create_approval_request(",
        "record_approval_decision(",
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
    ]
    for marker in forbidden:
        assert marker not in helper_source

    assert "packet_builder(" in helper_source


def test_service_helper_boundary_remains_read_only_when_api_is_added_later():
    api_source = Path("src/app/api.py").read_text(encoding="utf-8")
    ui_source = Path("src/app/static/agentic_review.js").read_text(encoding="utf-8")
    schema_text = "\n".join(
        [
            Path("src/storage/agentic_approvals/schema.sql").read_text(
                encoding="utf-8"
            ),
            Path("src/storage/agent_trace/schema.sql").read_text(encoding="utf-8"),
        ]
    )
    collector = Path("src/pipeline/collector.py").read_text(encoding="utf-8")

    assert api_source.count(HELPER_NAME) == 1
    assert HELPER_NAME not in ui_source
    assert HELPER_NAME not in schema_text
    assert HELPER_NAME not in collector
    assert collector.count("run_shadow_sidecar_pipeline_hook(") == 1


def test_service_helper_keeps_automated_and_mutation_agents_at_zero():
    payload = getattr(services, HELPER_NAME)(
        pipeline_generated_overlay_payload={
            "auto_generation_status": "overlay_auto_generated",
            "overlay_generated": True,
            "agent_recommendation_overlay": {
                "overlay_status": "overlay_ready",
                "recommended_review_action": "request_influence_approval",
            },
        }
    )

    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    _assert_service_safety(payload)
