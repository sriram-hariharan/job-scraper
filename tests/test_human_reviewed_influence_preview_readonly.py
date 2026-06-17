from copy import deepcopy
from pathlib import Path

from src.agents import human_reviewed_influence_preview as preview


PREVIEW_FLAG = "APPLYLENS_AGENTIC_PIPELINE_HUMAN_REVIEWED_INFLUENCE_PREVIEW_ENABLED"
KILL_SWITCH = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"


def _enabled_config():
    return {PREVIEW_FLAG: True}


def _deterministic_score_context():
    return {
        "agent_name": "final_application_scoring_agent",
        "status": "completed",
        "deterministic_score": 0.91,
        "deterministic_decision": "qualified_priority_ready",
        "decision_counts": {"qualified": 4, "disqualified": 1},
    }


def _shadow_score_comparison_context():
    return {
        "comparison_status": "comparison_ready_with_fallback",
        "comparison_type": "shadow_sidecar_vs_deterministic_score",
        "deterministic_score": 0.91,
        "deterministic_decision": "qualified_priority_ready",
        "shadow_snapshot_status": "snapshot_ready_with_fallback",
        "shadow_agent_names": [
            "jd_intelligence",
            "tailoring_suggestion",
            "critic_guardrail",
        ],
        "shadow_risk_flag_count": 1,
        "shadow_blocking_finding_count": 0,
        "agreement_level": "needs_operator_review",
        "comparison_findings": [
            {
                "finding_code": "shadow_risk_flags_present",
                "severity": "warning",
                "read_only": True,
            }
        ],
        "operator_review_summary": {
            "summary_type": "shadow_sidecar_score_comparison",
            "operator_review_only": True,
            "recommended_review_focus": ["shadow_risk_flags_present"],
        },
    }


def _assert_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["advisory_only"] is True
    assert safety["human_review_required"] is True
    assert safety["approval_gate_required"] is True
    assert safety["influence_preview_only"] is True
    assert safety["provider_calls_disabled_in_tests"] is True
    assert safety["requires_live_database"] is False
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
    assert safety["service_wiring_added"] is False
    assert safety["ui_action_added"] is False
    assert safety["auto_apply_enabled"] is False
    assert safety["mutation_authorized"] is False


def test_default_environment_returns_preview_not_enabled():
    payload = preview.build_human_reviewed_influence_preview_payload(
        deterministic_score_context=_deterministic_score_context(),
        shadow_score_comparison_context=_shadow_score_comparison_context(),
        preview_config={},
    )

    assert payload["preview_status"] == "preview_not_enabled"
    assert payload["preview_enabled"] is False
    assert payload["preview_findings"] == []
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    _assert_safety(payload)


def test_kill_switch_blocks_preview():
    payload = preview.build_human_reviewed_influence_preview_payload(
        deterministic_score_context=_deterministic_score_context(),
        shadow_score_comparison_context=_shadow_score_comparison_context(),
        preview_config={**_enabled_config(), KILL_SWITCH: True},
    )

    assert payload["preview_status"] == "preview_blocked_by_kill_switch"
    assert payload["preview_enabled"] is False
    assert payload["preview_findings"] == []
    _assert_safety(payload)


def test_missing_deterministic_context_blocks_safely():
    payload = preview.build_human_reviewed_influence_preview_payload(
        deterministic_score_context={},
        shadow_score_comparison_context=_shadow_score_comparison_context(),
        preview_config=_enabled_config(),
    )

    assert payload["preview_status"] == "preview_blocked_missing_deterministic_context"
    assert payload["preview_enabled"] is False
    assert payload["deterministic_score_context"]["deterministic_score"] is None
    _assert_safety(payload)


def test_missing_shadow_comparison_context_blocks_safely():
    payload = preview.build_human_reviewed_influence_preview_payload(
        deterministic_score_context=_deterministic_score_context(),
        shadow_score_comparison_context={},
        preview_config=_enabled_config(),
    )

    assert payload["preview_status"] == "preview_blocked_missing_shadow_comparison"
    assert payload["preview_enabled"] is False
    assert payload["shadow_comparison_context"]["comparison_status"] == ""
    _assert_safety(payload)


def test_enabled_preview_builds_deterministic_operator_review_payload():
    deterministic = _deterministic_score_context()
    shadow = _shadow_score_comparison_context()
    before = deepcopy((deterministic, shadow))

    first = preview.build_human_reviewed_influence_preview_payload(
        deterministic_score_context=deterministic,
        shadow_score_comparison_context=shadow,
        preview_config=_enabled_config(),
    )
    second = preview.build_human_reviewed_influence_preview_payload(
        deterministic_score_context=deterministic,
        shadow_score_comparison_context=shadow,
        preview_config=_enabled_config(),
    )

    assert first == second
    assert (deterministic, shadow) == before
    assert first["preview_status"] == "preview_ready_with_fallback"
    assert first["preview_type"] == "human_reviewed_shadow_score_influence_preview"
    assert first["required_human_review"] is True
    assert first["approval_gate_required"] is True
    assert first["deterministic_score_context"]["deterministic_score"] == 0.91
    assert first["deterministic_score_context"]["deterministic_decision"] == (
        "qualified_priority_ready"
    )
    assert first["shadow_comparison_context"]["comparison_status"] == (
        "comparison_ready_with_fallback"
    )
    assert first["shadow_comparison_context"]["agreement_level"] == (
        "needs_operator_review"
    )
    assert first["proposed_influence_summary"]["summary_type"] == (
        "human_reviewed_influence_preview"
    )
    assert first["proposed_influence_summary"]["advisory_only"] is True
    assert first["proposed_score_adjustment_preview"]["proposed_score_delta"] == 0.0
    assert first["proposed_score_adjustment_preview"]["score_after_preview"] == 0.91
    assert first["proposed_score_adjustment_preview"]["did_mutate_scoring"] is False
    assert first["proposed_ranking_effect_preview"]["proposed_ranking_delta"] == 0
    assert first["proposed_ranking_effect_preview"]["ranking_after_preview"] == (
        "unchanged"
    )
    assert first["proposed_ranking_effect_preview"]["did_change_ranking"] is False
    assert first["operator_review_summary"]["operator_review_only"] is True
    assert first["operator_review_summary"]["approval_gate_required"] is True
    assert any(
        finding["finding_code"] == "human_review_and_approval_gate_required"
        for finding in first["preview_findings"]
    )
    assert first["provider_calls_disabled_in_tests"] is True
    assert first["requires_live_database"] is False
    assert first["live_provider_backed_automated_agents"] == 0
    assert first["mutation_authorized_agents"] == 0
    _assert_safety(first)


def test_preview_failure_is_non_blocking():
    def builder(**_kwargs):
        raise RuntimeError("preview boom")

    payload = preview.build_human_reviewed_influence_preview_payload(
        deterministic_score_context=_deterministic_score_context(),
        shadow_score_comparison_context=_shadow_score_comparison_context(),
        preview_config=_enabled_config(),
        preview_builder=builder,
    )

    assert payload["preview_status"] == "preview_failed_non_blocking"
    assert payload["preview_enabled"] is True
    assert payload["error_type"] == "RuntimeError"
    assert payload["operator_review_summary"]["review_status"] == "failed_non_blocking"
    _assert_safety(payload)


def test_source_has_no_provider_db_pipeline_api_service_ui_or_schema_wiring():
    source = Path("src/agents/human_reviewed_influence_preview.py").read_text(
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
        "record_approval_decision(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "update_ranking(",
        "mutate_queue(",
        "score_resume_job_match(",
    ]

    for marker in forbidden:
        assert marker not in source


def test_no_runtime_pipeline_or_schema_file_uses_preview_helper():
    helper_markers = [
        "human_reviewed_influence_preview",
        "build_human_reviewed_influence_preview_payload",
    ]
    protected_paths = [
        "src/pipeline/collector.py",
        "src/storage/agent_trace/schema.sql",
    ]

    for path in protected_paths:
        text = Path(path).read_text(encoding="utf-8")
        for marker in helper_markers:
            assert marker not in text
