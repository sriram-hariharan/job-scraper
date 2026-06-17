from pathlib import Path


DOC = Path("docs/phase5_shadow_sidecar_trace_persistence_readiness_audit.md")


def _doc_text() -> str:
    assert DOC.exists()
    return DOC.read_text(encoding="utf-8")


def test_phase5_shadow_sidecar_trace_persistence_readiness_doc_exists():
    text = _doc_text()
    assert "Phase 5P Shadow Sidecar Trace Persistence Readiness Audit" in text
    assert "No runtime behavior change is introduced." in text
    assert "No trace writes were added." in text


def test_phase5_shadow_sidecar_trace_persistence_audit_states_exact_inspected_files():
    text = _doc_text()
    required = [
        "src/agents/shadow_sidecar_hook.py",
        "src/agents/shadow_sidecar.py",
        "src/storage/agent_trace/store.py",
        "src/storage/agent_trace/schema.sql",
        "src/app/services.py",
        "src/app/api.py",
        "src/pipeline/collector.py",
        "docs/phase5_shadow_sidecar_pipeline_integration_point_audit.md",
        "tests/test_shadow_sidecar_hook_trace_capture_default_off.py",
        "tests/test_shadow_sidecar_first_pipeline_callsite_default_off.py",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_persistence_audit_identifies_trace_helpers():
    text = _doc_text()
    required = [
        "src/storage/agent_trace/schema.sql",
        "src/storage/agent_trace/store.py",
        "src/agents/trace.py",
        "create_agent_run_postgres_payload",
        "record_agent_step_postgres_payload",
        "complete_agent_run_postgres_payload",
        "build_agent_trace_recording_payload",
        "execute_agent_trace_recording",
        "list_agent_runs_postgres_payload",
        "list_agent_steps_postgres_payload",
        "build_agent_trace_summary_payload",
        "trace_bundle",
        "evidence_pack",
        "trace_summary",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_persistence_audit_suitability_decision():
    text = _doc_text()
    required = [
        "`src/storage/agent_trace/store.py` is suitable as the future persistence home",
        "Future shadow sidecar persistence should reuse existing agent trace concepts instead of adding a new storage architecture.",
        "This phase does not add trace persistence.",
        "It does not create new tables, alter schema, create DB connections, write rows, or add API/UI/service wiring.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_persistence_audit_requires_default_off_flags():
    text = _doc_text()
    required = [
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_PERSISTENCE_ENABLED",
        "Global sidecar flag remains default-off.",
        "Per-agent flags remain default-off.",
        "Kill switch disables trace capture/persistence.",
        "Provider calls disabled in tests.",
        "Provider calls must not run in tests.",
        "Deterministic fallback is required.",
        "Persistence failure must not fail deterministic pipeline.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_persistence_audit_blocks_mutation():
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


def test_phase5_shadow_sidecar_trace_persistence_audit_blocks_wiring_and_schema():
    text = _doc_text()
    required = [
        "No runtime behavior change.",
        "No trace writes.",
        "No schema change.",
        "No DB schema creation.",
        "No API/UI/service changes.",
        "No API/UI/service wiring in this phase.",
        "No DB schema creation in this phase.",
        "No trace writes in this phase.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_persistence_audit_preserves_pipeline_flow():
    text = _doc_text()
    required = [
        "Stage-level logging must be preserved.",
        "Existing metrics flow must be preserved.",
        "Existing retry/rate-limit/cache/dedup/ATS health checks must not be removed.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_persistence_audit_counts_remain_zero():
    text = _doc_text()
    required = [
        "Default-off pipeline hook call site exists: 1.",
        "Live provider-backed automated agents remain zero.",
        "Mutation-authorized agents remain zero.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_persistence_audit_next_sequence_and_non_goals():
    text = _doc_text()
    required = [
        "Add default-off trace persistence helper, not called by pipeline.",
        "Add tests proving default-off and non-blocking behavior.",
        "Wire persistence into the existing hook only behind explicit trace persistence flag.",
        "Add service/API readback later.",
        "Add UI/dashboard later.",
        "Only later allow human-approved influence.",
        "Only much later guarded automation.",
        "No automated decisions.",
        "No mutation.",
    ]
    for phrase in required:
        assert phrase in text
