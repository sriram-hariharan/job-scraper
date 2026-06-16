from pathlib import Path


DOC = Path("docs/phase5_shadow_agentic_pipeline_sidecar_readiness_audit.md")


def _doc_text() -> str:
    assert DOC.exists()
    return DOC.read_text(encoding="utf-8")


def test_phase5_shadow_agentic_pipeline_sidecar_readiness_doc_exists():
    text = _doc_text()
    assert "Phase 5A Shadow Agentic Pipeline Sidecar Readiness Audit" in text
    assert "No runtime behavior change is introduced." in text
    assert "No production pipeline behavior is changed." in text


def test_phase5_shadow_agentic_pipeline_sidecar_readiness_agent_counts():
    text = _doc_text()
    required_counts = [
        "| live LLM-capable agents coded | 3 |",
        "| live agents available in manual/shadow workflow | 3 |",
        "| live agents connected to production pipeline | 0 |",
        "| live agents allowed to automate mutations | 0 |",
    ]

    for phrase in required_counts:
        assert phrase in text


def test_phase5_shadow_agentic_pipeline_sidecar_readiness_lists_live_agents():
    text = _doc_text()
    for agent_name in [
        "JD Intelligence Agent",
        "Tailoring Suggestion Agent",
        "Critic / Guardrail Agent",
    ]:
        assert agent_name in text


def test_phase5_shadow_agentic_pipeline_sidecar_readiness_defines_workflows():
    text = _doc_text()
    required = [
        "Manual/shadow workflow means",
        "Production pipeline shadow sidecar means",
        "Automated workflow means",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_agentic_pipeline_sidecar_readiness_first_integration_is_readonly_sidecar():
    text = _doc_text()
    required = [
        "The safest first real-pipeline connection is a read-only shadow sidecar",
        "First integration is read-only shadow sidecar.",
        "Trace/evidence storage only.",
        "No scoring/ranking override.",
        "No automatic pipeline wiring in this phase.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_agentic_pipeline_sidecar_readiness_blocks_mutations():
    text = _doc_text()
    required = [
        "No scoring mutation.",
        "No ranking mutation.",
        "No queue mutation.",
        "No approval mutation.",
        "No resume mutation.",
        "No execution mutation.",
        "No submission mutation.",
        "No application execution.",
        "No application submission.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_agentic_pipeline_sidecar_readiness_requires_default_off_and_no_test_provider_calls():
    text = _doc_text()
    required = [
        "Feature flag default-off requirement.",
        "Provider-backed sidecar runs remain disabled unless explicitly enabled.",
        "Provider calls must not run in tests.",
        "No provider call in tests.",
        "Deterministic fallback",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_agentic_pipeline_sidecar_readiness_observability_requirements():
    text = _doc_text()
    required = [
        "Trace bundle emitted.",
        "Evidence pack emitted.",
        "Status/health/readiness checks emitted.",
        "Trace/evidence/readiness observability requirements documented and tested.",
        "Batch-level observability.",
        "Kill switch.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_agentic_pipeline_sidecar_readiness_non_goals_and_sequence():
    text = _doc_text()
    required = [
        "No auto-apply.",
        "No auto-submit.",
        "No LLM ranking override.",
        "No resume overwrite.",
        "Documentation/readiness audit.",
        "Shadow sidecar config contract.",
        "Sidecar trace schema contract.",
        "Pipeline-sidecar adapter default-off.",
        "Local deterministic test doubles only.",
        "Provider-backed shadow run default-off.",
        "Dashboard/readback.",
        "Human-approved influence path.",
        "Guarded automation only after validation.",
    ]

    for phrase in required:
        assert phrase in text
