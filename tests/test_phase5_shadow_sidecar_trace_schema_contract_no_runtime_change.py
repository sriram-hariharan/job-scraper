from pathlib import Path


DOC = Path("docs/phase5_shadow_sidecar_trace_schema_contract_no_runtime_change.md")


def _doc_text() -> str:
    assert DOC.exists()
    return DOC.read_text(encoding="utf-8")


def test_phase5_shadow_sidecar_trace_schema_contract_doc_exists():
    text = _doc_text()
    assert "Phase 5C Shadow Sidecar Trace Schema Contract" in text
    assert "No runtime behavior change is introduced." in text
    assert "Live agents connected to production pipeline remain zero." in text


def test_phase5_shadow_sidecar_trace_schema_contract_includes_trace_envelope_fields():
    text = _doc_text()
    required = [
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
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_schema_contract_includes_source_decision_fields():
    text = _doc_text()
    required = [
        "source_deterministic_stage",
        "source_deterministic_status",
        "source_deterministic_score",
        "source_deterministic_decision",
        "source_deterministic_reason_codes",
        "source deterministic pipeline decision must be preserved",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_schema_contract_includes_agent_output_fields():
    text = _doc_text()
    required = [
        "agent_output_status",
        "agent_recommendation",
        "agent_confidence",
        "agent_reason_codes",
        "agent_evidence_refs",
        "agent_risk_flags",
        "agent_blocking_findings",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_schema_contract_includes_observability_fields():
    text = _doc_text()
    required = [
        "trace_bundle",
        "evidence_pack",
        "readiness_decision",
        "health_status",
        "fallback_used",
        "error_type",
        "error_message",
        "Trace bundle, evidence pack, readiness decision, and health status are required",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_schema_contract_includes_safety_metadata():
    text = _doc_text()
    required = [
        "read_only",
        "shadow_only",
        "manual_review_required",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_create_approval",
        "did_mutate_approval",
        "did_mutate_resume",
        "did_create_execution_request",
        "did_create_execution_launch_request",
        "did_execute_application",
        "did_submit_application",
        "pipeline_wiring_added",
        "auto_apply_enabled",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_schema_contract_includes_status_enum():
    text = _doc_text()
    required = [
        "not_enabled",
        "skipped_by_config",
        "completed_shadow",
        "completed_with_fallback",
        "blocked_by_kill_switch",
        "failed_non_blocking",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_schema_contract_lists_three_live_agents():
    text = _doc_text()
    required = [
        "JD Intelligence Agent",
        "Tailoring Suggestion Agent",
        "Critic / Guardrail Agent",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_schema_contract_failure_and_fallback_are_safe():
    text = _doc_text()
    required = [
        "Sidecar failures must not fail deterministic pipeline by default.",
        "Failures must emit trace/evidence payloads.",
        "Deterministic fallback required.",
        "No retry storm.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_schema_contract_blocks_mutation_and_provider_calls():
    text = _doc_text()
    required = [
        "No provider calls in tests.",
        "Deterministic fixtures only.",
        "No scoring mutation.",
        "No ranking mutation.",
        "No queue mutation.",
        "No approval mutation.",
        "No resume mutation.",
        "No execution request mutation.",
        "No execution launch request mutation.",
        "No application execution.",
        "No application submission.",
        "No pipeline wiring.",
        "No provider calls.",
        "No automated decisions.",
    ]

    for phrase in required:
        assert phrase in text
