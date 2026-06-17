from pathlib import Path


DOC = Path("docs/phase5_shadow_sidecar_end_to_end_readiness_audit.md")


def _doc_text() -> str:
    assert DOC.exists()
    return DOC.read_text(encoding="utf-8")


def test_phase5_shadow_sidecar_end_to_end_readiness_doc_exists():
    text = _doc_text()
    assert "Phase 5Y Shadow Sidecar End-to-End Readiness Audit" in text
    assert "No new runtime behavior is introduced in this audit." in text
    assert "No application execution/submission is added." in text


def test_phase5_shadow_sidecar_end_to_end_audit_states_exact_inspected_files():
    text = _doc_text()
    required = [
        "src/agents/shadow_sidecar.py",
        "src/agents/shadow_sidecar_hook.py",
        "src/agents/shadow_sidecar_trace_persistence.py",
        "src/agents/shadow_sidecar_trace_readback.py",
        "src/pipeline/collector.py",
        "src/app/services.py",
        "src/app/api.py",
        "src/app/static/agentic_review.js",
        "docs/phase5_shadow_sidecar_trace_readback_ui_readiness_audit.md",
        "tests/test_shadow_sidecar_trace_readback_ui_default_off.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_end_to_end_audit_identifies_components():
    text = _doc_text()
    required = [
        "Isolated adapter",
        "JD Intelligence shadow mapping",
        "Tailoring Suggestion shadow mapping",
        "Critic / Guardrail shadow mapping",
        "Isolated shadow sidecar chain runner",
        "Shadow sidecar chain observability/readiness summary",
        "Shadow sidecar pipeline hook preview",
        "Default-off pipeline hook helper",
        "First default-off pipeline call site",
        "Structured hook trace capture",
        "Trace persistence helper",
        "Trace persistence hook integration",
        "Trace readback helper",
        "Trace readback service helper",
        "Trace readback API route",
        "Trace readback UI surface",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_end_to_end_audit_states_safety_counts():
    text = _doc_text()
    required = [
        "Default-off pipeline hook call site exists: 1.",
        "Live provider-backed automated agents remain zero.",
        "Mutation-authorized agents remain zero.",
        "Scoring/ranking mutation: 0.",
        "Queue/approval/resume/execution/submission mutation: 0.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_end_to_end_audit_blocks_mutation():
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


def test_phase5_shadow_sidecar_end_to_end_audit_lists_required_flags():
    text = _doc_text()
    required = [
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_JD_INTELLIGENCE_ENABLED",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_TAILORING_SUGGESTION_ENABLED",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_CRITIC_GUARDRAIL_ENABLED",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_PERSISTENCE_ENABLED",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_TRACE_READBACK_ENABLED",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_end_to_end_audit_requires_kill_switch():
    text = _doc_text()
    required = [
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH",
        "Kill switch blocks sidecar work.",
        "Kill switch blocks trace capture/persistence/readback/UI readback.",
        "Kill switch behavior must remain non-mutating.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_end_to_end_audit_requires_non_blocking_failures():
    text = _doc_text()
    required = [
        "Sidecar failure must not fail deterministic pipeline.",
        "Trace capture failure must not fail deterministic pipeline.",
        "Persistence failure must not fail deterministic pipeline.",
        "Readback failure must not fail deterministic pipeline.",
        "Shadow sidecar failures remain advisory and non-blocking.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_end_to_end_audit_preserves_stage_boundaries():
    text = _doc_text()
    required = [
        "Prefilter relevance remains separate.",
        "LLM evaluation remains separate.",
        "Final application scoring remains separate.",
        "Sidecar output remains advisory only.",
        "Sidecar output does not override ranking/scoring.",
        "Sidecar output does not mutate queue/approval/resume/execution/submission.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase5_shadow_sidecar_end_to_end_audit_next_sequence_and_non_goals():
    text = _doc_text()
    required = [
        "Add a shadow run evidence snapshot for operator review.",
        "Add read-only comparison against deterministic final score.",
        "Add human-reviewed influence preview.",
        "Add approval-gated influence only after explicit user action.",
        "Only later guarded automation.",
        "No new runtime behavior in this audit.",
        "No provider automation.",
        "No autonomous decisions.",
        "No mutation.",
        "No application execution/submission.",
    ]
    for phrase in required:
        assert phrase in text
