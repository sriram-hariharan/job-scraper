from __future__ import annotations

from pathlib import Path

from src.agents import (
    agent_recommendation_overlay_readback as overlay_readback,
    shadow_sidecar_hook,
)


GLOBAL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
JD_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED"
AUTO_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_AGENT_RECOMMENDATION_OVERLAY_AUTO_GENERATE_ENABLED"
)
PERSISTENCE_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_PERSISTENCE_ENABLED"
)


def _hook_payload(*, include_preview: bool = True, **config):
    trace_context = {"trace_id": "trace_overlay_context"}
    if include_preview:
        trace_context["human_reviewed_influence_preview_result"] = {
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
        }
    return shadow_sidecar_hook.run_shadow_sidecar_pipeline_hook(
        run_id="run_overlay_context",
        batch_id="batch_overlay_context",
        job_id="job_overlay_context",
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
        },
        existing_trace_context=trace_context,
    )


def _enabled_config():
    return {
        GLOBAL_FLAG: True,
        JD_FLAG: True,
        AUTO_FLAG: True,
    }


def _assert_context_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["trace_context_only"] is True
    assert safety["advisory_only"] is True
    assert safety["pipeline_generated_overlay_context_propagation"] is True
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


def test_generated_overlay_is_present_in_hook_trace_context():
    hook = _hook_payload(**_enabled_config())
    context = hook["existing_trace_context"][
        "agent_recommendation_overlay_auto_generation"
    ]

    assert context["auto_generation_status"] in {"overlay_auto_generated", "overlay_auto_generated_partial"}
    assert context["overlay_generated"] is True
    assert context["agent_recommendation_overlay"]["overlay_status"] in {"overlay_ready", "overlay_partial_insufficient_context"}
    assert context["safety_metadata"]["automatic_generation"] is True
    _assert_context_safety(context)


def test_generated_overlay_is_present_in_trace_capture_context():
    hook = _hook_payload(**_enabled_config())
    context = hook["trace_capture"]["agent_recommendation_overlay_auto_generation"]

    assert context["auto_generation_status"] in {"overlay_auto_generated", "overlay_auto_generated_partial"}
    assert context["agent_recommendation_overlay"]["recommended_review_action"] in {
        "request_influence_approval",
        "review_agent_preview",
        "no_agent_action",
    }


def test_trace_persistence_disabled_still_carries_safe_overlay_source_context():
    hook = _hook_payload(**_enabled_config())
    persistence = hook["trace_persistence"]
    context = persistence["source_trace_context"][
        "agent_recommendation_overlay_auto_generation"
    ]

    assert persistence["trace_persistence_status"] == "trace_persistence_not_enabled"
    assert persistence["persistence_attempted"] is False
    assert context["auto_generation_status"] in {"overlay_auto_generated", "overlay_auto_generated_partial"}
    assert context["agent_recommendation_overlay"]["overlay_status"] in {"overlay_ready", "overlay_partial_insufficient_context"}
    _assert_context_safety(persistence["source_trace_context"])


def test_trace_persistence_records_carry_overlay_without_live_database():
    hook = _hook_payload(
        **{
            **_enabled_config(),
            PERSISTENCE_FLAG: True,
        }
    )
    persistence = hook["trace_persistence"]
    records = persistence["persistence_records"]
    step_output = records["agent_step_record"]["output_json"]

    assert persistence["trace_persistence_status"] == (
        "trace_persistence_skipped_no_safe_sink"
    )
    assert persistence["persistence_attempted"] is False
    assert step_output["agent_recommendation_overlay_auto_generation"][
        "auto_generation_status"
    ] in {"overlay_auto_generated", "overlay_auto_generated_partial"}
    assert records["source_trace_context"][
        "agent_recommendation_overlay_auto_generation"
    ]["overlay_generated"] is True
    _assert_context_safety(records["source_trace_context"])


def test_readback_recovers_overlay_from_trace_persistence_source_context():
    hook = _hook_payload(**_enabled_config())

    payload = overlay_readback.build_pipeline_generated_agent_recommendation_overlay_readback_payload(
        trace_persistence_payload={
            "source_trace_context": hook["trace_persistence"]["source_trace_context"]
        }
    )

    assert payload["readback_status"] == "pipeline_generated_overlay_readback_ready"
    assert payload["auto_generation_status"] in {"overlay_auto_generated", "overlay_auto_generated_partial"}
    assert payload["agent_recommendation_overlay"]["overlay_status"] in {"overlay_ready", "overlay_partial_insufficient_context"}


def test_readback_recovers_overlay_from_trace_readback_payload_shape():
    hook = _hook_payload(
        **{
            **_enabled_config(),
            PERSISTENCE_FLAG: True,
        }
    )
    step = hook["trace_persistence"]["persistence_records"]["agent_step_record"]

    payload = overlay_readback.build_pipeline_generated_agent_recommendation_overlay_readback_payload(
        trace_readback_payload={
            "trace_readback": {
                "agent_steps": [step],
            }
        }
    )

    assert payload["readback_status"] == "pipeline_generated_overlay_readback_ready"
    assert payload["auto_generation_status"] in {"overlay_auto_generated", "overlay_auto_generated_partial"}
    assert payload["pipeline_generated_overlay_found"] is True


def test_missing_overlay_still_returns_not_found():
    payload = overlay_readback.build_pipeline_generated_agent_recommendation_overlay_readback_payload(
        trace_persistence_payload={
            "source_trace_context": {
                "hook_status": "hook_completed_with_fallback",
            }
        }
    )

    assert payload["readback_status"] == "pipeline_generated_overlay_not_found"
    assert payload["pipeline_generated_overlay_found"] is False


def test_partial_overlay_remains_valid_in_trace_context_and_readback():
    hook = _hook_payload(
        include_preview=False,
        **{
            GLOBAL_FLAG: True,
            AUTO_FLAG: True,
        },
    )
    context = hook["trace_persistence"]["source_trace_context"][
        "agent_recommendation_overlay_auto_generation"
    ]
    payload = overlay_readback.build_pipeline_generated_agent_recommendation_overlay_readback_payload(
        trace_persistence_payload=hook["trace_persistence"]
    )

    assert context["auto_generation_status"] == "overlay_auto_generated_partial"
    assert context["agent_recommendation_overlay"]["overlay_status"] == (
        "overlay_partial_insufficient_context"
    )
    assert payload["readback_status"] == "pipeline_generated_overlay_readback_ready"
    assert payload["auto_generation_status"] == "overlay_auto_generated_partial"


def test_context_propagation_sources_have_no_provider_or_mutation_calls():
    paths = [
        Path("src/agents/shadow_sidecar_hook.py"),
        Path("src/agents/shadow_sidecar_trace_persistence.py"),
        Path("src/agents/agent_recommendation_overlay_readback.py"),
    ]
    combined = "\n".join(path.read_text(encoding="utf-8") for path in paths)

    forbidden = [
        "src.app.services",
        "src.app.api",
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
        assert marker not in combined


def test_no_storage_schema_change_or_new_pipeline_stage():
    schema_text = "\n".join(
        [
            Path("src/storage/agentic_approvals/schema.sql").read_text(encoding="utf-8"),
            Path("src/storage/agent_trace/schema.sql").read_text(encoding="utf-8"),
        ]
    )
    collector = Path("src/pipeline/collector.py").read_text(encoding="utf-8")

    assert "pipeline_generated_overlay_context_propagation" not in schema_text
    assert collector.count("run_shadow_sidecar_pipeline_hook(") == 1
    assert "pipeline_generated_overlay_context_propagation" not in collector
