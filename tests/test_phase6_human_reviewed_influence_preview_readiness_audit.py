from pathlib import Path


DOC = Path("docs/phase6_human_reviewed_influence_preview_readiness_audit.md")


def _doc_text() -> str:
    assert DOC.exists()
    return DOC.read_text(encoding="utf-8")


def test_phase6_human_reviewed_influence_preview_readiness_doc_exists():
    text = _doc_text()
    assert "Phase 6F Human-reviewed Influence Preview Readiness Audit" in text
    assert "No runtime behavior changed in this phase." in text
    assert "No influence preview builder was added in this phase." in text


def test_phase6_human_reviewed_influence_preview_audit_states_exact_inspected_files():
    text = _doc_text()
    for expected in [
        "src/agents/shadow_sidecar_score_comparison.py",
        "src/agents/final_application_scoring.py",
        "src/pipeline/collector.py",
        "src/app/services.py",
        "src/app/api.py",
        "src/app/static/agentic_review.js",
        "src/agents/shadow_sidecar.py",
        "docs/phase5_shadow_sidecar_end_to_end_readiness_audit.md",
        "docs/phase6_shadow_score_comparison_ui_readiness_audit.md",
        "tests/test_shadow_sidecar_score_comparison_readonly.py",
        "tests/test_shadow_sidecar_score_comparison_service_helper_no_api_ui.py",
        "tests/test_shadow_sidecar_score_comparison_api_default_off_no_ui.py",
        "tests/test_shadow_sidecar_score_comparison_ui_default_off.py",
        "tests/test_phase6_shadow_score_comparison_ui_readiness_audit.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
    ]:
        assert expected in text


def test_phase6_human_reviewed_influence_audit_identifies_phase6a_to_6e_flow():
    text = _doc_text()
    for expected in [
        "Current implemented Phase 6A-6E shadow score comparison flow:",
        "Phase 6A added isolated score comparison helper: `src/agents/shadow_sidecar_score_comparison.py`.",
        "Phase 6B added read-only service helper: `shadow_sidecar_score_comparison_service_payload`.",
        "Phase 6C added default-off API route: `POST /api/shadow-sidecar/score-comparison`.",
        "Phase 6D added UI readiness audit: `docs/phase6_shadow_score_comparison_ui_readiness_audit.md`.",
        "Phase 6E added read-only UI panel: `renderShadowSidecarScoreComparisonSection`.",
    ]:
        assert expected in text


def test_phase6_human_reviewed_influence_audit_states_zero_mutation_counts():
    text = _doc_text()
    for expected in [
        "Live provider-backed automated agents remain zero.",
        "live provider-backed automated agents: 0",
        "Mutation-authorized agents remain zero.",
        "mutation-authorized agents: 0",
        "scoring/ranking mutation: 0",
        "queue/approval/resume/execution/submission mutation: 0",
    ]:
        assert expected in text


def test_phase6_human_reviewed_influence_audit_preserves_stage_boundaries():
    text = _doc_text()
    for expected in [
        "Prefilter relevance remains separate.",
        "LLM evaluation remains separate.",
        "Final application scoring remains separate.",
        "Shadow score comparison remains advisory only.",
        "Influence preview remains separate from deterministic final application scoring.",
    ]:
        assert expected in text


def test_phase6_human_reviewed_influence_audit_defines_future_preview_object():
    text = _doc_text()
    for expected in [
        "`preview_status`",
        "`preview_type`",
        "`deterministic_score_context`",
        "`shadow_comparison_context`",
        "`proposed_influence_summary`",
        "`proposed_score_adjustment_preview`",
        "`proposed_ranking_effect_preview`",
        "`required_human_review`",
        "`approval_gate_required`",
        "`no_mutation_safety_metadata`",
    ]:
        assert expected in text


def test_phase6_human_reviewed_influence_audit_requires_default_off_flag_and_kill_switch():
    text = _doc_text()
    assert "APPLYLENS_AGENTIC_PIPELINE_HUMAN_REVIEWED_INFLUENCE_PREVIEW_ENABLED" in text
    assert "The feature flag must default off." in text
    assert "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH" in text
    assert "Kill switch behavior must win over all enablement flags." in text


def test_phase6_human_reviewed_influence_audit_blocks_mutation_and_execution():
    text = _doc_text()
    for expected in [
        "read-only",
        "advisory only",
        "no score mutation",
        "no ranking mutation",
        "no queue mutation",
        "no approval mutation",
        "no resume mutation",
        "no execution request mutation",
        "no execution launch request mutation",
        "no application execution/submission",
        "no application execution",
        "no application submission",
    ]:
        assert expected in text


def test_phase6_human_reviewed_influence_audit_requires_human_review_and_approval_gate():
    text = _doc_text()
    assert "Explicit human review is required before any influence." in text
    assert "Approval gate is required before any influence." in text
    assert "No future influence preview may be applied automatically." in text


def test_phase6_human_reviewed_influence_audit_preserves_observability_and_operational_guards():
    text = _doc_text()
    for expected in [
        "Existing stage-level logging and metrics flow must be preserved.",
        "Existing retry, rate-limit, cache, deduplication, and ATS health checks must not be removed.",
        "Trace bundle context must remain available.",
        "Evidence pack context must remain available.",
        "Readiness status must remain visible.",
        "Health status must remain visible.",
        "Provider calls must not run in tests.",
    ]:
        assert expected in text


def test_phase6_human_reviewed_influence_audit_lists_next_sequence_and_non_goals():
    text = _doc_text()
    for expected in [
        "add isolated influence preview builder",
        "add service helper",
        "add default-off API readback",
        "add UI preview panel",
        "add approval-gated influence request",
        "only later allow approved influence to affect downstream ranking/scoring",
        "only much later guarded automation",
        "no runtime behavior in this audit",
        "no influence builder yet",
        "no UI/API/service changes",
        "no score/ranking mutation",
        "no approval-gated mutation yet",
        "no application execution/submission",
    ]:
        assert expected in text
