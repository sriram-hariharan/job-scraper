from pathlib import Path


DOC = Path("docs/phase5_shadow_sidecar_trace_readback_readiness_audit.md")


def _doc_text() -> str:
    assert DOC.exists()
    return DOC.read_text(encoding="utf-8")


def test_phase5_shadow_sidecar_trace_readback_readiness_doc_exists():
    text = _doc_text()
    assert "Phase 5S Shadow Sidecar Trace Readback Readiness Audit" in text
    assert "No runtime behavior change is introduced." in text
    assert "No service/API/UI code was added." in text
    assert "No trace writes were added." in text


def test_phase5_shadow_sidecar_trace_readback_audit_states_exact_inspected_files():
    text = _doc_text()
    required = [
        "src/agents/shadow_sidecar_hook.py",
        "src/agents/shadow_sidecar_trace_persistence.py",
        "src/agents/shadow_sidecar.py",
        "src/storage/agent_trace/store.py",
        "src/agents/trace.py",
        "src/app/services.py",
        "src/app/api.py",
        "src/pipeline/collector.py",
        "docs/phase5_shadow_sidecar_trace_persistence_readiness_audit.md",
        "tests/test_shadow_sidecar_trace_persistence_hook_integration_default_off.py",
        "tests/test_shadow_sidecar_hook_trace_capture_default_off.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_audit_identifies_existing_readback_files():
    text = _doc_text()
    required = [
        "Existing trace readback service/API files discovered from the repo:",
        "src/app/services.py",
        "src/app/api.py",
        "src/storage/agent_trace/store.py",
        "src/agents/trace.py",
        "agent_trace_payload",
        "GET /profile/pipeline-runs/{run_id}/agent-trace",
        "GET /api/agentic-approvals/{approval_request_id}/agent-trace",
        "_agent_trace_readonly_payload",
        "_read_agent_trace_for_approval",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_audit_identifies_trace_helpers():
    text = _doc_text()
    required = [
        "get_agent_run_postgres_payload",
        "list_agent_runs_postgres_payload",
        "list_agent_steps_postgres_payload",
        "build_agent_trace_summary_payload",
        "build_stage_trace_bundle_payload",
        "evaluate_stage_trace_bundle_health",
        "build_stage_trace_readiness_decision",
        "build_agent_trace_evidence_pack",
        "trace_summary",
        "stage_trace_bundle",
        "stage_trace_health",
        "stage_trace_readiness",
        "trace_evidence_pack",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_audit_suitability_decision():
    text = _doc_text()
    required = [
        "Existing trace readback endpoints/services can support future shadow sidecar trace readback",
        "Future shadow sidecar trace readback should reuse existing agent trace concepts instead of adding a new readback architecture.",
        "No readback service was added.",
        "No readback API was added.",
        "No UI/dashboard was added.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_audit_requires_default_off_flags():
    text = _doc_text()
    required = [
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_READBACK_ENABLED",
        "The global sidecar flag remains default-off.",
        "The trace persistence flag remains default-off.",
        "The readback flag remains default-off.",
        "The kill switch disables trace capture/persistence/readback.",
        "Provider calls disabled in tests.",
        "Provider calls must not run in tests.",
        "Deterministic fallback is required.",
        "Readback failure must not fail deterministic pipeline.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_audit_blocks_runtime_wiring_and_schema():
    text = _doc_text()
    required = [
        "No runtime behavior change in this phase.",
        "No service/API/UI wiring in this phase.",
        "No UI wiring in this phase.",
        "No trace writes in this phase.",
        "No DB schema creation in this phase.",
        "No schema change.",
        "No service/API/UI code.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_audit_blocks_mutation():
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
        "No application execution/submission.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_audit_preserves_existing_pipeline_flow():
    text = _doc_text()
    required = [
        "Stage-level logging must be preserved.",
        "Existing metrics flow must be preserved.",
        "Existing retry/rate-limit/cache/dedup/ATS health checks must not be removed.",
        "Sidecar failures remain non-blocking.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_audit_counts_remain_zero():
    text = _doc_text()
    required = [
        "Default-off pipeline hook call site exists: 1.",
        "Live provider-backed automated agents remain zero.",
        "Mutation-authorized agents remain zero.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_audit_next_sequence_and_non_goals():
    text = _doc_text()
    required = [
        "Add default-off service/helper readback function, not API/UI.",
        "Add tests proving default-off and read-only behavior.",
        "Add read-only API endpoint behind explicit readback flag.",
        "Add UI/dashboard later.",
        "Only later allow human-approved influence.",
        "Only much later guarded automation.",
        "No automated decisions.",
        "No mutation.",
    ]
    for phrase in required:
        assert phrase in text
