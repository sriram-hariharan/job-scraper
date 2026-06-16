from pathlib import Path


DOC = Path("docs/phase5_shadow_sidecar_config_contract_no_runtime_change.md")


def _doc_text() -> str:
    assert DOC.exists()
    return DOC.read_text(encoding="utf-8")


def test_phase5_shadow_sidecar_config_contract_doc_exists():
    text = _doc_text()
    assert "Phase 5B Shadow Sidecar Config Contract" in text
    assert "No runtime behavior change is introduced." in text
    assert "Live agents connected to production pipeline remain zero." in text


def test_phase5_shadow_sidecar_config_contract_includes_global_default_off_flag():
    text = _doc_text()
    assert "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED=false" in text
    assert "global production pipeline shadow sidecar flag must be default-off" in text


def test_phase5_shadow_sidecar_config_contract_includes_per_agent_flags():
    text = _doc_text()
    required = [
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED=false",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED=false",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED=false",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_config_contract_includes_global_kill_switch():
    text = _doc_text()
    assert "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH=true" in text
    assert "kill switch must take precedence" in text


def test_phase5_shadow_sidecar_config_contract_provider_policy_is_default_safe():
    text = _doc_text()
    required = [
        "Provider calls disabled in tests.",
        "Provider calls must not run in tests.",
        "Provider calls disabled unless global sidecar flag and per-agent flag are enabled.",
        "Provider calls require both global and per-agent enablement.",
        "Deterministic fallback required",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_config_contract_blocks_runtime_mutations():
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


def test_phase5_shadow_sidecar_config_contract_observability_requirements():
    text = _doc_text()
    required = [
        "Trace bundle required.",
        "Evidence pack required.",
        "Readiness decision required.",
        "Health status required.",
        "Batch/run id required.",
        "Stage name required.",
        "Agent name required.",
        "Source deterministic pipeline decision must be preserved.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_config_contract_failure_behavior_is_safe():
    text = _doc_text()
    required = [
        "Sidecar failures must not fail deterministic pipeline by default.",
        "Failures must be logged into trace/evidence payload.",
        "Fallback output must be deterministic.",
        "No retry storm.",
    ]

    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_config_contract_testing_and_non_goals():
    text = _doc_text()
    required = [
        "No network/provider calls in tests.",
        "Deterministic fixtures only.",
        "Config contract tests only in this phase.",
        "No pipeline wiring.",
        "No real provider calls.",
        "No automated decisions.",
        "No human approval mutation.",
        "No application execution/submission.",
        "No queue writes.",
        "No runtime behavior change.",
    ]

    for phrase in required:
        assert phrase in text
