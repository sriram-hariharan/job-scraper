from copy import deepcopy
from pathlib import Path

from src.agents import shadow_sidecar


def _sidecar_input(**config):
    return shadow_sidecar.build_shadow_sidecar_input_payload(
        run_id="run_shadow_1",
        batch_id="batch_shadow_1",
        job_id="job_shadow_1",
        stage_name="post_deterministic_evaluation_shadow_sidecar",
        source_deterministic_stage="application_priority",
        source_deterministic_status="completed",
        source_deterministic_score=0.82,
        source_deterministic_decision="qualified",
        source_deterministic_reason_codes=["score_above_threshold"],
        job_payload={"title": "Data Platform Engineer"},
        resume_profile_payload={"resume_id": "resume_main"},
        existing_trace_context={"trace_id": "trace_shadow_1"},
        sidecar_config=config,
        agent_name="JD Intelligence Agent",
        started_at_utc="2026-06-16T10:00:00Z",
        completed_at_utc="2026-06-16T10:00:01Z",
        duration_ms=1000,
    )


def _assert_safety(payload):
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


def test_default_config_returns_not_enabled_and_preserves_source_decision():
    source = _sidecar_input()
    original = deepcopy(source)

    payload = shadow_sidecar.run_shadow_sidecar_agent(sidecar_input=source)

    assert payload["sidecar_stage_status"] == "not_enabled"
    assert payload["fallback_used"] is True
    assert payload["agent_recommendation"] == "preserve_source_deterministic_decision"
    assert payload["source_deterministic_decision"] == "qualified"
    assert payload["source_deterministic_score"] == 0.82
    assert source == original
    _assert_safety(payload)


def test_kill_switch_returns_blocked_by_kill_switch():
    payload = shadow_sidecar.run_shadow_sidecar_agent(
        sidecar_input=_sidecar_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH=True,
        )
    )

    assert payload["sidecar_stage_status"] == "blocked_by_kill_switch"
    assert payload["agent_reason_codes"] == ["blocked_by_kill_switch"]
    assert payload["readiness_decision"]["readiness_status"] == "blocked"
    _assert_safety(payload)


def test_provider_calls_are_not_made_when_provider_execution_is_disallowed():
    calls = []

    def provider(_payload):
        calls.append("called")
        return {"agent_recommendation": "should_not_appear"}

    payload = shadow_sidecar.run_shadow_sidecar_agent(
        sidecar_input=_sidecar_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=True,
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=True,
        ),
        shadow_agent=provider,
    )

    assert calls == []
    assert payload["sidecar_stage_status"] == "completed_with_fallback"
    assert payload["agent_reason_codes"] == [
        "provider_execution_unavailable_or_disallowed"
    ]
    assert payload["sidecar_config"]["provider_calls_disabled_in_tests"] is True
    _assert_safety(payload)


def test_enabled_without_provider_returns_deterministic_fallback():
    payload = shadow_sidecar.run_shadow_sidecar_agent(
        sidecar_input=_sidecar_input(
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED="true",
            APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED="true",
            provider_execution_allowed=False,
        )
    )

    assert payload["sidecar_stage_status"] == "completed_with_fallback"
    assert payload["fallback_used"] is True
    assert payload["health_status"] == "warning"
    assert payload["readiness_decision"]["readiness_status"] == "blocked"
    _assert_safety(payload)


def test_output_includes_phase5c_trace_envelope_fields():
    payload = shadow_sidecar.run_shadow_sidecar_agent(sidecar_input=_sidecar_input())

    for field in [
        "schema_version",
        "run_id",
        "batch_id",
        "job_id",
        "stage_name",
        "agent_name",
        "agent_mode",
        "provider_mode",
        "sidecar_enabled",
        "sidecar_stage_status",
        "started_at_utc",
        "completed_at_utc",
        "duration_ms",
    ]:
        assert field in payload


def test_output_includes_source_and_agent_fields():
    payload = shadow_sidecar.run_shadow_sidecar_agent(sidecar_input=_sidecar_input())

    for field in [
        "source_deterministic_stage",
        "source_deterministic_status",
        "source_deterministic_score",
        "source_deterministic_decision",
        "source_deterministic_reason_codes",
        "agent_output_status",
        "agent_recommendation",
        "agent_confidence",
        "agent_reason_codes",
        "agent_evidence_refs",
        "agent_risk_flags",
        "agent_blocking_findings",
    ]:
        assert field in payload


def test_output_includes_trace_evidence_readiness_and_health_placeholders():
    payload = shadow_sidecar.run_shadow_sidecar_agent(sidecar_input=_sidecar_input())

    assert payload["trace_bundle"]["bundle_type"] == "shadow_sidecar_trace_bundle"
    assert payload["evidence_pack"]["evidence_pack_type"] == "shadow_sidecar_evidence_pack"
    assert payload["readiness_decision"]["readiness_status"] == "blocked"
    assert payload["health_status"] == "warning"
    assert payload["trace_bundle"]["source_deterministic_decision"] == "qualified"
    assert payload["evidence_pack"]["source_deterministic_decision"] == "qualified"


def test_config_contract_flag_names_are_represented():
    source = _sidecar_input()
    config = source["sidecar_config"]

    assert config["global_flag_name"] == (
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
    )
    assert config["jd_intelligence_flag_name"] == (
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED"
    )
    assert config["tailoring_suggestion_flag_name"] == (
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED"
    )
    assert config["critic_guardrail_flag_name"] == (
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED"
    )
    assert config["kill_switch_flag_name"] == (
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"
    )


def test_source_has_no_pipeline_api_ui_service_or_storage_wiring():
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

    assert "pipeline_wiring_added" in source
    assert "LIVE_AGENT_CONNECTED_TO_PRODUCTION_PIPELINE" not in source

