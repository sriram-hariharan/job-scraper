from copy import deepcopy
from pathlib import Path

from src.app import services


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
        "score_summary": {"max_score": 0.91, "average_score": 0.72},
    }


def _shadow_snapshot_payload():
    return {
        "snapshot_status": "snapshot_ready_with_fallback",
        "snapshot_type": "shadow_sidecar_evidence_snapshot",
        "agent_names": [
            "jd_intelligence",
            "tailoring_suggestion",
            "critic_guardrail",
        ],
        "fallback_count": 1,
        "risk_flag_count": 1,
        "blocking_finding_count": 0,
    }


def _assert_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["service_helper_only"] is True
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
    assert payload["service_helper_only"] is True
    assert payload["api_route_added"] is False
    assert payload["ui_action_added"] is False


def test_service_helper_default_environment_returns_comparison_not_enabled():
    payload = services.shadow_sidecar_score_comparison_service_payload(
        deterministic_score_context=_deterministic_score_context(),
        shadow_evidence_snapshot_payload=_shadow_snapshot_payload(),
        sidecar_config={},
    )

    assert payload["comparison_status"] == "comparison_not_enabled"
    assert payload["comparison_enabled"] is False
    assert payload["service_surface"] == "shadow_sidecar_score_comparison_service"
    assert payload["comparison_findings"] == []
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    _assert_safety(payload)


def test_service_helper_kill_switch_blocks_comparison():
    payload = services.shadow_sidecar_score_comparison_service_payload(
        deterministic_score_context=_deterministic_score_context(),
        shadow_evidence_snapshot_payload=_shadow_snapshot_payload(),
        sidecar_config={**_enabled_config(), KILL_SWITCH: True},
    )

    assert payload["comparison_status"] == "comparison_blocked_by_kill_switch"
    assert payload["comparison_enabled"] is False
    _assert_safety(payload)


def test_service_helper_missing_deterministic_context_blocks_safely():
    payload = services.shadow_sidecar_score_comparison_service_payload(
        deterministic_score_context={},
        shadow_evidence_snapshot_payload=_shadow_snapshot_payload(),
        sidecar_config=_enabled_config(),
    )

    assert payload["comparison_status"] == (
        "comparison_blocked_missing_deterministic_context"
    )
    assert payload["deterministic_score"] is None
    _assert_safety(payload)


def test_service_helper_missing_shadow_snapshot_blocks_safely():
    payload = services.shadow_sidecar_score_comparison_service_payload(
        deterministic_score_context=_deterministic_score_context(),
        shadow_evidence_snapshot_payload={},
        sidecar_config=_enabled_config(),
    )

    assert payload["comparison_status"] == (
        "comparison_blocked_missing_shadow_snapshot"
    )
    assert payload["shadow_snapshot_status"] == ""
    _assert_safety(payload)


def test_service_helper_enabled_comparison_builds_operator_review_payload():
    deterministic = _deterministic_score_context()
    shadow = _shadow_snapshot_payload()
    before = deepcopy((deterministic, shadow))

    first = services.shadow_sidecar_score_comparison_service_payload(
        deterministic_score_context=deterministic,
        shadow_evidence_snapshot_payload=shadow,
        sidecar_config=_enabled_config(),
    )
    second = services.shadow_sidecar_score_comparison_service_payload(
        deterministic_score_context=deterministic,
        shadow_evidence_snapshot_payload=shadow,
        sidecar_config=_enabled_config(),
    )

    assert first == second
    assert (deterministic, shadow) == before
    assert first["comparison_status"] == "comparison_ready_with_fallback"
    assert first["deterministic_score"] == 0.91
    assert first["deterministic_decision"] == "qualified_priority_ready"
    assert first["shadow_snapshot_status"] == "snapshot_ready_with_fallback"
    assert first["agreement_level"] == "needs_operator_review"
    assert first["comparison_findings"]
    assert first["operator_review_summary"]["operator_review_only"] is True
    assert first["provider_calls_disabled_in_tests"] is True
    assert first["requires_live_database"] is False
    assert first["live_provider_backed_automated_agents"] == 0
    assert first["mutation_authorized_agents"] == 0
    _assert_safety(first)


def test_service_helper_comparison_failure_is_non_blocking():
    def builder(**_kwargs):
        raise RuntimeError("comparison boom")

    payload = services.shadow_sidecar_score_comparison_service_payload(
        deterministic_score_context=_deterministic_score_context(),
        shadow_evidence_snapshot_payload=_shadow_snapshot_payload(),
        sidecar_config=_enabled_config(),
        comparison_builder=builder,
    )

    assert payload["comparison_status"] == "comparison_failed_non_blocking"
    assert payload["comparison_enabled"] is True
    assert payload["error_type"] == "RuntimeError"
    _assert_safety(payload)


def test_service_helper_slice_has_no_api_ui_storage_pipeline_or_mutation_calls():
    source = Path("src/app/services.py").read_text(encoding="utf-8")
    start = source.index("def shadow_sidecar_score_comparison_service_payload(")
    end = source.index("\ndef record_agent_feedback_payload(", start)
    helper_source = source[start:end]
    forbidden = [
        "@app.",
        "router.",
        "agentic_review",
        "src.pipeline",
        "schema.sql",
        "create_agent_run(",
        "record_agent_step(",
        "complete_agent_run(",
        "create_approval_request(",
        "create_execution_request(",
        "create_execution_launch_request(",
        "execute_application(",
        "submit_application(",
        "insert_application",
        "insert_patch",
        "insert_operator",
        "update_ranking(",
        "mutate_queue(",
        "score_resume_job_match(",
    ]

    for marker in forbidden:
        assert marker not in helper_source


def test_no_api_ui_pipeline_or_schema_file_uses_service_helper():
    helper_marker = "shadow_sidecar_score_comparison_service_payload"
    protected_paths = [
        "src/pipeline/collector.py",
        "src/app/api.py",
        "src/app/static/agentic_review.js",
        "src/storage/agent_trace/schema.sql",
    ]

    for path in protected_paths:
        assert helper_marker not in Path(path).read_text(encoding="utf-8")
