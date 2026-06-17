from pathlib import Path


DOC = Path("docs/phase6_shadow_score_comparison_ui_readiness_audit.md")


def _doc_text() -> str:
    assert DOC.exists()
    return DOC.read_text(encoding="utf-8")


def test_phase6_shadow_score_comparison_ui_readiness_doc_exists():
    text = _doc_text()

    assert "Phase 6D Shadow Score Comparison UI Readiness Audit" in text
    assert "No UI code was added in this phase." in text
    assert "No runtime behavior changed in this phase." in text


def test_phase6_ui_readiness_audit_states_exact_inspected_files():
    text = _doc_text()
    required = [
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "src/app/api.py",
        "src/app/services.py",
        "src/agents/shadow_sidecar_score_comparison.py",
        "tests/test_shadow_sidecar_score_comparison_api_default_off_no_ui.py",
        "tests/test_shadow_sidecar_score_comparison_service_helper_no_api_ui.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_ui_readiness_audit_identifies_existing_ui_trace_review_files():
    text = _doc_text()
    required = [
        "Existing UI trace/review files discovered from the repo:",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "renderAgentTraceReadOnlyPanel",
        "renderAgentTraceReadOnlyDetails",
        "renderShadowSidecarTraceReadbackSection",
        "fetchAgentTraceReadOnlyPayload",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_ui_readiness_audit_identifies_api_service_comparison_files():
    text = _doc_text()
    required = [
        "Existing API/service comparison files available for future UI use:",
        "src/agents/shadow_sidecar_score_comparison.py",
        "src/app/services.py",
        "src/app/api.py",
        "POST /api/shadow-sidecar/score-comparison",
        "shadow_sidecar_score_comparison_service_payload",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_ui_readiness_audit_names_future_insertion_point():
    text = _doc_text()

    assert "recommended future UI insertion point" in text
    assert "inside the existing Agent Trace panel" in text
    assert "near the manual shadow sidecar trace readback section" in text


def test_phase6_ui_readiness_audit_states_no_behavior_changes():
    text = _doc_text()
    required = [
        "No UI code was added in this phase.",
        "No API/service behavior changed in this phase.",
        "No runtime behavior changed in this phase.",
        "No production pipeline behavior changed in this phase.",
        "no UI code in this phase",
        "no API/service code in this phase",
        "no runtime behavior change",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_ui_readiness_audit_states_safety_counts():
    text = _doc_text()
    required = [
        "Default-off pipeline hook call site exists: 1.",
        "Live provider-backed automated agents remain zero.",
        "Mutation-authorized agents remain zero.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_ui_readiness_audit_blocks_mutation_and_execution():
    text = _doc_text()
    required = [
        "No scoring, ranking, queue, approval, resume, execution request, execution launch request, application execution, or application submission mutation was added.",
        "no scoring mutation",
        "no ranking mutation",
        "no queue mutation",
        "no approval mutation",
        "no resume mutation",
        "no execution request mutation",
        "no execution launch request mutation",
        "no application execution/submission",
        "no application execution",
        "no application submission",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_ui_readiness_audit_requires_default_off_flag_and_kill_switch():
    text = _doc_text()
    required = [
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SCORE_COMPARISON_ENABLED",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH",
        "Required default-off comparison flag",
        "Required kill switch",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_ui_readiness_audit_requires_safe_states():
    text = _doc_text()
    required = [
        "safe empty/not-enabled state",
        "safe blocked-by-kill-switch state",
        "safe missing deterministic context state",
        "safe missing shadow snapshot state",
        "safe comparison failure state",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_ui_readiness_audit_preserves_existing_operational_flow():
    text = _doc_text()
    required = [
        "Existing stage-level logging and metrics flow must be preserved.",
        "Existing retry, rate-limit, cache, deduplication, and ATS health checks must not be removed.",
        "Existing deterministic pipeline outputs must remain the source of truth.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_ui_readiness_audit_preserves_stage_separation():
    text = _doc_text()
    required = [
        "prefilter relevance stays separate from shadow score comparison",
        "LLM evaluation stays separate from shadow score comparison",
        "final application scoring stays separate from shadow score comparison",
        "shadow comparison stays separate from deterministic final application scoring",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_ui_readiness_audit_lists_next_sequence_and_non_goals():
    text = _doc_text()
    required = [
        "add UI-only comparison panel behind existing trace/review surface",
        "fetch default-off comparison API only when user opens the panel",
        "render deterministic score/decision, shadow snapshot status, agreement level, findings, and no-mutation summary",
        "add UI tests",
        "only later add human-reviewed influence preview",
        "only later add approval-gated influence",
        "only much later guarded automation",
        "no automated decisions",
        "no mutation",
    ]
    for phrase in required:
        assert phrase in text
