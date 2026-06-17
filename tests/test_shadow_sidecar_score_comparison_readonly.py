from copy import deepcopy
from pathlib import Path

from src.agents import shadow_sidecar_score_comparison as comparison


GLOBAL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
COMPARISON_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SCORE_COMPARISON_ENABLED"
KILL_SWITCH = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"


def _enabled_config():
    return {
        GLOBAL_FLAG: True,
        COMPARISON_FLAG: True,
    }


def _deterministic_score_context():
    return {
        "agent_name": "final_application_scoring_agent",
        "status": "completed",
        "deterministic_score": 0.91,
        "deterministic_decision": "qualified_priority_ready",
        "score_summary": {
            "max_score": 0.91,
            "average_score": 0.72,
        },
        "decision_counts": {
            "qualified": 4,
            "disqualified": 1,
        },
    }


def _shadow_snapshot_payload():
    return {
        "snapshot_status": "snapshot_ready_with_fallback",
        "snapshot_type": "shadow_sidecar_evidence_snapshot",
        "source_hook_status": "hook_completed_with_fallback",
        "source_chain_status": "completed_with_fallback",
        "agent_names": [
            "jd_intelligence",
            "tailoring_suggestion",
            "critic_guardrail",
        ],
        "enabled_agent_count": 3,
        "fallback_count": 1,
        "risk_flag_count": 1,
        "blocking_finding_count": 0,
        "operator_review_summary": {
            "summary_type": "shadow_sidecar_evidence_snapshot",
            "operator_review_only": True,
            "recommended_review_focus": ["review_shadow_fallbacks"],
        },
    }


def _assert_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["score_comparison_only"] is True
    assert safety["operator_review_only"] is True
    assert safety["did_read_database"] is False
    assert safety["did_write_database"] is False
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
    assert safety["api_route_added"] is False
    assert safety["ui_action_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False


def test_default_environment_returns_comparison_not_enabled():
    payload = comparison.build_shadow_sidecar_score_comparison_payload(
        deterministic_score_context=_deterministic_score_context(),
        shadow_evidence_snapshot_payload=_shadow_snapshot_payload(),
        sidecar_config={},
    )

    assert payload["comparison_status"] == "comparison_not_enabled"
    assert payload["comparison_enabled"] is False
    assert payload["comparison_findings"] == []
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    _assert_safety(payload)


def test_kill_switch_blocks_comparison():
    payload = comparison.build_shadow_sidecar_score_comparison_payload(
        deterministic_score_context=_deterministic_score_context(),
        shadow_evidence_snapshot_payload=_shadow_snapshot_payload(),
        sidecar_config={**_enabled_config(), KILL_SWITCH: True},
    )

    assert payload["comparison_status"] == "comparison_blocked_by_kill_switch"
    assert payload["comparison_enabled"] is False
    assert payload["comparison_findings"] == []
    _assert_safety(payload)


def test_missing_deterministic_score_context_blocks_safely():
    payload = comparison.build_shadow_sidecar_score_comparison_payload(
        deterministic_score_context={},
        shadow_evidence_snapshot_payload=_shadow_snapshot_payload(),
        sidecar_config=_enabled_config(),
    )

    assert payload["comparison_status"] == (
        "comparison_blocked_missing_deterministic_context"
    )
    assert payload["comparison_enabled"] is False
    assert payload["deterministic_score"] is None
    _assert_safety(payload)


def test_missing_shadow_snapshot_blocks_safely():
    payload = comparison.build_shadow_sidecar_score_comparison_payload(
        deterministic_score_context=_deterministic_score_context(),
        shadow_evidence_snapshot_payload={},
        sidecar_config=_enabled_config(),
    )

    assert payload["comparison_status"] == (
        "comparison_blocked_missing_shadow_snapshot"
    )
    assert payload["comparison_enabled"] is False
    assert payload["shadow_snapshot_status"] == ""
    _assert_safety(payload)


def test_enabled_comparison_builds_deterministic_operator_review_payload():
    deterministic = _deterministic_score_context()
    shadow = _shadow_snapshot_payload()
    before = deepcopy((deterministic, shadow))

    first = comparison.build_shadow_sidecar_score_comparison_payload(
        deterministic_score_context=deterministic,
        shadow_evidence_snapshot_payload=shadow,
        sidecar_config=_enabled_config(),
    )
    second = comparison.build_shadow_sidecar_score_comparison_payload(
        deterministic_score_context=deterministic,
        shadow_evidence_snapshot_payload=shadow,
        sidecar_config=_enabled_config(),
    )

    assert first == second
    assert (deterministic, shadow) == before
    assert first["comparison_status"] == "comparison_ready_with_fallback"
    assert first["comparison_type"] == "shadow_sidecar_vs_deterministic_score"
    assert first["deterministic_score"] == 0.91
    assert first["deterministic_decision"] == "qualified_priority_ready"
    assert first["shadow_snapshot_status"] == "snapshot_ready_with_fallback"
    assert first["shadow_agent_names"] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert first["shadow_risk_flag_count"] == 1
    assert first["shadow_blocking_finding_count"] == 0
    assert first["agreement_level"] == "needs_operator_review"
    assert first["comparison_findings"]
    assert any(
        finding["finding_code"] == "deterministic_score_preserved"
        for finding in first["comparison_findings"]
    )
    assert first["operator_review_summary"]["summary_type"] == (
        "shadow_sidecar_score_comparison"
    )
    assert first["operator_review_summary"]["operator_review_only"] is True
    assert first["source_deterministic_context"]["deterministic_score"] == 0.91
    assert first["source_shadow_snapshot_context"]["shadow_snapshot_status"] == (
        "snapshot_ready_with_fallback"
    )
    assert first["provider_calls_disabled_in_tests"] is True
    assert first["requires_live_database"] is False
    assert first["live_provider_backed_automated_agents"] == 0
    assert first["mutation_authorized_agents"] == 0
    _assert_safety(first)


def test_comparison_failure_is_non_blocking():
    def builder(**_kwargs):
        raise RuntimeError("comparison boom")

    payload = comparison.build_shadow_sidecar_score_comparison_payload(
        deterministic_score_context=_deterministic_score_context(),
        shadow_evidence_snapshot_payload=_shadow_snapshot_payload(),
        sidecar_config=_enabled_config(),
        comparison_builder=builder,
    )

    assert payload["comparison_status"] == "comparison_failed_non_blocking"
    assert payload["comparison_enabled"] is True
    assert payload["error_type"] == "RuntimeError"
    assert payload["operator_review_summary"]["review_status"] == (
        "failed_non_blocking"
    )
    _assert_safety(payload)


def test_source_has_no_provider_db_pipeline_api_service_ui_or_schema_wiring():
    source = Path("src/agents/shadow_sidecar_score_comparison.py").read_text(
        encoding="utf-8"
    )
    forbidden = [
        "src.pipeline",
        "src.app.api",
        "src.app.services",
        "agentic_review",
        "schema.sql",
        "build_live_jd_intelligence_dry_run_payload(",
        "build_live_tailoring_suggestion_provider_adapter(",
        "build_live_critic_guardrail_provider_adapter(",
        "create_agent_run(",
        "record_agent_step(",
        "complete_agent_run(",
        "create_approval_request(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "update_ranking(",
        "mutate_queue(",
    ]

    for marker in forbidden:
        assert marker not in source


def test_no_runtime_pipeline_or_schema_file_uses_comparison_helper():
    helper_markers = [
        "shadow_sidecar_score_comparison",
        "build_shadow_sidecar_score_comparison_payload",
    ]
    protected_paths = [
        "src/pipeline/collector.py",
        "src/storage/agent_trace/schema.sql",
    ]

    for path in protected_paths:
        text = Path(path).read_text(encoding="utf-8")
        for marker in helper_markers:
            assert marker not in text
