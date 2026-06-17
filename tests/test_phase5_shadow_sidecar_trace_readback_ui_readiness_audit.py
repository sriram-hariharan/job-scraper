from pathlib import Path


DOC = Path("docs/phase5_shadow_sidecar_trace_readback_ui_readiness_audit.md")


def _doc_text() -> str:
    assert DOC.exists()
    return DOC.read_text(encoding="utf-8")


def test_phase5_shadow_sidecar_trace_readback_ui_readiness_doc_exists():
    text = _doc_text()
    assert "Phase 5W Shadow Sidecar Trace Readback UI Readiness Audit" in text
    assert "No UI code was added in this phase." in text
    assert "No API/service behavior changed." in text
    assert "No runtime behavior change is introduced." in text


def test_phase5_shadow_sidecar_trace_readback_ui_audit_states_exact_inspected_files():
    text = _doc_text()
    required = [
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "src/app/api.py",
        "src/app/services.py",
        "docs/phase5_shadow_sidecar_trace_readback_readiness_audit.md",
        "tests/test_shadow_sidecar_trace_readback_api_default_off_no_ui.py",
        "tests/test_agent_trace_readonly_ui_panel_no_api_no_writes.py",
        "tests/test_agent_trace_polish_ux_hardening_ui_only_no_api_no_writes.py",
        "tests/test_agent_trace_ui_contract.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_ui_audit_identifies_ui_files():
    text = _doc_text()
    required = [
        "Existing UI trace/review files discovered from the repo:",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "renderAgentTraceReadOnlyPanel",
        "renderAgentTraceEvidencePackSection",
        "renderAgentTraceDetailedSections",
        "renderAgentTraceReadOnlyDetails",
        "fetchAgentTraceReadOnlyPayload",
        "fetchReadOnlyAgentTrace",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_ui_audit_identifies_api_service_files():
    text = _doc_text()
    required = [
        "Existing API/service readback files available for future UI use:",
        "src/app/api.py",
        "src/app/services.py",
        "src/agents/shadow_sidecar_trace_readback.py",
        "POST /api/shadow-sidecar/trace-readback",
        "shadow_sidecar_trace_readback_service_payload",
        "build_shadow_sidecar_trace_readback_payload",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_ui_audit_names_insertion_point():
    text = _doc_text()
    required = [
        "Recommended future UI insertion point:",
        "renderAgentTraceReadOnlyPanel",
        "renderAgentTraceEvidencePackSection(tracePayload?.trace_evidence_pack)",
        "before lower-level debug details",
        "instead of inventing a new dashboard architecture",
        "escapeHtml",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_ui_audit_requires_default_off_flag_and_kill_switch():
    text = _doc_text()
    required = [
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_READBACK_ENABLED",
        "The readback flag remains default-off.",
        "The global sidecar flag remains default-off.",
        "The trace persistence flag remains default-off.",
        "The kill switch disables trace capture/persistence/readback/UI readback.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_ui_audit_requires_safe_states():
    text = _doc_text()
    required = [
        "Safe empty/not-enabled state.",
        "Safe blocked-by-kill-switch state.",
        "Safe no-trace/no-source state.",
        "Safe invalid-context state.",
        "Safe failed-non-blocking state.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_ui_audit_blocks_mutation():
    text = _doc_text()
    required = [
        "Read-only display.",
        "No auto-refresh that calls providers.",
        "No mutation buttons.",
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


def test_phase5_shadow_sidecar_trace_readback_ui_audit_preserves_existing_flow():
    text = _doc_text()
    required = [
        "Stage-level logging must be preserved.",
        "Existing metrics flow must be preserved.",
        "Existing retry/rate-limit/cache/dedup/ATS health checks must not be removed.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_ui_audit_counts_remain_zero():
    text = _doc_text()
    required = [
        "Default-off pipeline hook call site exists: 1.",
        "Live provider-backed automated agents remain zero.",
        "Mutation-authorized agents remain zero.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_trace_readback_ui_audit_next_sequence_and_non_goals():
    text = _doc_text()
    required = [
        "Add UI-only readback panel behind existing trace/review surface.",
        "Fetch default-off readback API only when user opens the panel.",
        "Render status, source context, safety metadata, and no-mutation summary.",
        "Add UI tests.",
        "Only later add richer dashboard.",
        "Only later allow human-approved influence.",
        "Only much later guarded automation.",
        "No UI code in this phase.",
        "No API/service code in this phase.",
        "No automated decisions.",
        "No mutation.",
    ]
    for phrase in required:
        assert phrase in text
