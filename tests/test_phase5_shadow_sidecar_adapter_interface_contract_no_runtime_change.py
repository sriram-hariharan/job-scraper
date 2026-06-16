from pathlib import Path


DOC = Path("docs/phase5_shadow_sidecar_adapter_interface_contract_no_runtime_change.md")


def _doc_text() -> str:
    assert DOC.exists()
    return DOC.read_text(encoding="utf-8")


def test_phase5_shadow_sidecar_adapter_interface_contract_doc_exists():
    text = _doc_text()
    assert "Phase 5D Shadow Sidecar Adapter Interface Contract" in text
    assert "No runtime behavior change is introduced." in text
    assert "Live agents connected to production pipeline remain zero." in text


def test_phase5_shadow_sidecar_adapter_interface_contract_defines_adapter_purpose():
    text = _doc_text()
    required = [
        "receive deterministic pipeline context",
        "optionally call a shadow agent under future default-off configuration",
        "normalize output into the Phase 5C trace schema",
        "return a read-only sidecar result",
        "Never override deterministic decisions.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_adapter_interface_contract_includes_input_fields():
    text = _doc_text()
    required = [
        "run_id",
        "batch_id",
        "job_id",
        "stage_name",
        "source_deterministic_stage",
        "source_deterministic_status",
        "source_deterministic_score",
        "source_deterministic_decision",
        "source_deterministic_reason_codes",
        "job_payload",
        "resume_profile_payload",
        "existing_trace_context",
        "sidecar_config",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_adapter_interface_contract_includes_output_fields():
    text = _doc_text()
    required = [
        "sidecar_stage_status",
        "agent_name",
        "agent_mode",
        "provider_mode",
        "agent_output_status",
        "agent_recommendation",
        "agent_confidence",
        "agent_reason_codes",
        "agent_evidence_refs",
        "agent_risk_flags",
        "trace_bundle",
        "evidence_pack",
        "readiness_decision",
        "health_status",
        "safety_metadata",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_adapter_interface_contract_lists_future_functions():
    text = _doc_text()
    required = [
        "build_shadow_sidecar_input_payload",
        "run_shadow_sidecar_agent",
        "build_shadow_sidecar_trace_payload",
        "build_shadow_sidecar_fallback_payload",
        "evaluate_shadow_sidecar_safety",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_adapter_interface_contract_maps_three_live_agents():
    text = _doc_text()
    required = [
        "JD Intelligence Agent maps to job description extraction and risk signals.",
        "Tailoring Suggestion Agent maps to resume/job tailoring advice.",
        "Critic / Guardrail Agent maps to risk review and blocking findings.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_adapter_interface_contract_config_is_default_safe():
    text = _doc_text()
    required = [
        "Global sidecar flag default-off.",
        "Per-agent flags default-off.",
        "Kill switch disables all sidecar work.",
        "Provider calls require global plus per-agent enablement.",
        "Provider calls are disabled in tests.",
        "Tests must not call providers.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_adapter_interface_contract_failure_behavior_is_safe():
    text = _doc_text()
    required = [
        "Sidecar failures must not fail deterministic pipeline by default.",
        "Fallback payload required.",
        "Trace/evidence required even on failure.",
        "No retry storm.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_adapter_interface_contract_blocks_mutations():
    text = _doc_text()
    required = [
        "No scoring mutation.",
        "No ranking mutation.",
        "No queue mutation.",
        "No approval mutation.",
        "No resume mutation.",
        "No execution request mutation.",
        "No execution launch request mutation.",
        "No application execution.",
        "No application submission.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_adapter_interface_contract_non_goals():
    text = _doc_text()
    required = [
        "No runtime adapter implementation.",
        "No pipeline wiring.",
        "No provider calls.",
        "No automated decisions.",
        "No queue writes.",
        "No application execution/submission.",
        "No runtime behavior change.",
    ]

    for phrase in required:
        assert phrase in text
