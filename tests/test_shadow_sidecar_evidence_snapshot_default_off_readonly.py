from copy import deepcopy
from pathlib import Path

from src.agents import shadow_sidecar_evidence_snapshot as snapshot


GLOBAL_FLAG = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED"
SNAPSHOT_FLAG = (
    "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_EVIDENCE_SNAPSHOT_ENABLED"
)
KILL_SWITCH = "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH"


def _enabled_config():
    return {
        GLOBAL_FLAG: True,
        SNAPSHOT_FLAG: True,
    }


def _hook_payload():
    return {
        "hook_status": "hook_completed_with_fallback",
        "stage_name": "post_final_scoring",
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.87,
        "source_deterministic_decision": "priority_ready",
        "source_deterministic_reason_codes": ["deterministic_priority_ready"],
        "chain_payload": {
            "chain_status": "completed_with_fallback",
            "sidecar_chain_status": "completed_with_fallback",
            "stage_order": [
                "jd_intelligence",
                "tailoring_suggestion",
                "critic_guardrail",
            ],
            "stage_statuses": {
                "jd_intelligence": "completed_with_fallback",
                "tailoring_suggestion": "completed_with_fallback",
                "critic_guardrail": "completed_shadow",
            },
            "fallback_used": True,
            "evidence_pack": {
                "evidence_pack_type": "shadow_sidecar_chain_evidence_pack",
                "agent_evidence_refs": ["job_payload.required_skills"],
                "agent_risk_flags": ["provider_disabled_fallback"],
            },
            "readiness_decision": {
                "readiness_status": "blocked",
                "blocking_findings": ["provider_disabled_for_shadow_run"],
            },
        },
        "trace_persistence": {
            "trace_persistence_status": "trace_persistence_skipped_no_safe_sink"
        },
    }


def _trace_capture_payload():
    return {
        "trace_capture_status": "trace_capture_captured",
        "trace_capture_only": True,
        "hook_status": "hook_completed_with_fallback",
        "chain_summary": {
            "chain_status": "completed_with_fallback",
            "stage_order": [
                "jd_intelligence",
                "tailoring_suggestion",
                "critic_guardrail",
            ],
            "stage_statuses": {
                "jd_intelligence": "completed_with_fallback",
                "tailoring_suggestion": "completed_with_fallback",
                "critic_guardrail": "completed_shadow",
            },
            "fallback_used": True,
            "readiness_status": "blocked",
        },
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.87,
        "source_deterministic_decision": "priority_ready",
        "source_deterministic_reason_codes": ["deterministic_priority_ready"],
        "evidence_pack": {
            "agent_risk_flags": ["provider_disabled_fallback"],
        },
    }


def _trace_persistence_payload():
    return {
        "trace_persistence_status": "trace_persistence_skipped_no_safe_sink",
        "persistence_records": {},
    }


def _trace_readback_payload():
    return {
        "trace_readback_status": "trace_readback_ready",
        "trace_readback": {
            "agent_steps": [
                {"agent_name": "jd_intelligence", "status": "ready"},
                {"agent_name": "tailoring_suggestion", "status": "ready"},
                {"agent_name": "critic_guardrail", "status": "ready"},
            ]
        },
    }


def _assert_safety(payload):
    safety = payload["safety_metadata"]
    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["evidence_snapshot_only"] is True
    assert safety["operator_review_only"] is True
    assert safety["did_read_database"] is False
    assert safety["did_write_database"] is False
    assert safety["did_write_agent_trace_run"] is False
    assert safety["did_write_agent_trace_step"] is False
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


def test_default_config_keeps_evidence_snapshot_not_enabled():
    payload = snapshot.build_shadow_sidecar_evidence_snapshot_payload(
        hook_payload=_hook_payload(),
        sidecar_config={},
    )

    assert payload["snapshot_status"] == "snapshot_not_enabled"
    assert payload["snapshot_enabled"] is False
    assert payload["evidence_items"] == []
    assert payload["live_provider_backed_automated_agents"] == 0
    assert payload["mutation_authorized_agents"] == 0
    _assert_safety(payload)


def test_kill_switch_blocks_snapshot_work():
    payload = snapshot.build_shadow_sidecar_evidence_snapshot_payload(
        hook_payload=_hook_payload(),
        sidecar_config={**_enabled_config(), KILL_SWITCH: True},
    )

    assert payload["snapshot_status"] == "snapshot_blocked_by_kill_switch"
    assert payload["snapshot_enabled"] is False
    assert payload["evidence_items"] == []
    _assert_safety(payload)


def test_missing_context_blocks_snapshot_safely():
    payload = snapshot.build_shadow_sidecar_evidence_snapshot_payload(
        sidecar_config=_enabled_config(),
    )

    assert payload["snapshot_status"] == "snapshot_blocked_missing_context"
    assert payload["snapshot_enabled"] is False
    assert payload["operator_review_summary"] == {}
    _assert_safety(payload)


def test_enabled_snapshot_builds_deterministic_operator_review_evidence():
    hook = _hook_payload()
    capture = _trace_capture_payload()
    persistence = _trace_persistence_payload()
    readback = _trace_readback_payload()
    before = deepcopy((hook, capture, persistence, readback))

    first = snapshot.build_shadow_sidecar_evidence_snapshot_payload(
        hook_payload=hook,
        trace_capture_payload=capture,
        trace_persistence_payload=persistence,
        trace_readback_payload=readback,
        sidecar_config=_enabled_config(),
    )
    second = snapshot.build_shadow_sidecar_evidence_snapshot_payload(
        hook_payload=hook,
        trace_capture_payload=capture,
        trace_persistence_payload=persistence,
        trace_readback_payload=readback,
        sidecar_config=_enabled_config(),
    )

    assert first == second
    assert (hook, capture, persistence, readback) == before
    assert first["snapshot_status"] == "snapshot_ready_with_fallback"
    assert first["snapshot_type"] == "shadow_sidecar_evidence_snapshot"
    assert first["source_hook_status"] == "hook_completed_with_fallback"
    assert first["source_chain_status"] == "completed_with_fallback"
    assert first["agent_names"] == [
        "jd_intelligence",
        "tailoring_suggestion",
        "critic_guardrail",
    ]
    assert first["enabled_agent_count"] == 3
    assert first["fallback_count"] >= 1
    assert first["risk_flag_count"] >= 1
    assert first["blocking_finding_count"] >= 1
    assert first["readback_status"] == "trace_readback_ready"
    assert first["trace_persistence_status"] == (
        "trace_persistence_skipped_no_safe_sink"
    )
    assert first["source_deterministic_context"] == {
        "source_deterministic_stage": "application_priority",
        "source_deterministic_status": "completed",
        "source_deterministic_score": 0.87,
        "source_deterministic_decision": "priority_ready",
        "source_deterministic_reason_codes": ["deterministic_priority_ready"],
    }
    assert first["operator_review_summary"]["summary_type"] == (
        "shadow_sidecar_evidence_snapshot"
    )
    assert first["operator_review_summary"]["operator_review_only"] is True
    assert "review_shadow_fallbacks" in first["operator_review_summary"][
        "recommended_review_focus"
    ]
    assert first["evidence_items"]
    assert first["provider_calls_disabled_in_tests"] is True
    assert first["requires_live_database"] is False
    _assert_safety(first)


def test_snapshot_builder_failure_is_non_blocking():
    def builder(**_kwargs):
        raise RuntimeError("snapshot boom")

    payload = snapshot.build_shadow_sidecar_evidence_snapshot_payload(
        hook_payload=_hook_payload(),
        sidecar_config=_enabled_config(),
        snapshot_builder=builder,
    )

    assert payload["snapshot_status"] == "snapshot_failed_non_blocking"
    assert payload["snapshot_enabled"] is True
    assert payload["error_type"] == "RuntimeError"
    assert payload["operator_review_summary"]["review_status"] == (
        "failed_non_blocking"
    )
    _assert_safety(payload)


def test_source_has_no_pipeline_api_service_ui_schema_provider_or_storage_wiring():
    source = Path("src/agents/shadow_sidecar_evidence_snapshot.py").read_text(
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
        "execute_application(",
        "submit_application(",
    ]

    for marker in forbidden:
        assert marker not in source


def test_no_runtime_or_ui_file_imports_or_calls_evidence_snapshot_helper():
    helper_markers = [
        "shadow_sidecar_evidence_snapshot",
        "build_shadow_sidecar_evidence_snapshot_payload",
    ]
    protected_paths = [
        "src/pipeline/collector.py",
        "src/app/api.py",
        "src/app/services.py",
        "src/app/static/agentic_review.js",
        "src/storage/agent_trace/schema.sql",
    ]

    for path in protected_paths:
        text = Path(path).read_text(encoding="utf-8")
        for marker in helper_markers:
            assert marker not in text
