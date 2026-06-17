from pathlib import Path


DOC = Path("docs/phase6_human_reviewed_influence_preview_ui_readiness_audit.md")


def _doc_text() -> str:
    assert DOC.exists()
    return DOC.read_text(encoding="utf-8")


def test_phase6_human_reviewed_influence_preview_ui_readiness_doc_exists():
    text = _doc_text()

    assert "Phase 6J Human-reviewed Influence Preview UI Readiness Audit" in text
    assert "No UI code was added in this phase." in text
    assert "No runtime behavior changed in this phase." in text


def test_phase6_influence_preview_ui_readiness_audit_states_exact_inspected_files():
    text = _doc_text()
    required = [
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "src/app/api.py",
        "src/app/services.py",
        "src/agents/human_reviewed_influence_preview.py",
        "docs/phase6_human_reviewed_influence_preview_readiness_audit.md",
        "tests/test_human_reviewed_influence_preview_api_default_off_no_ui.py",
        "tests/test_human_reviewed_influence_preview_service_helper_no_api_ui.py",
        "tests/test_human_reviewed_influence_preview_readonly.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_influence_preview_ui_readiness_identifies_existing_ui_trace_review_files():
    text = _doc_text()
    required = [
        "Existing UI trace/review files discovered from the repo:",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "renderAgentTraceReadOnlyPanel",
        "renderAgentTraceReadOnlyDetails",
        "renderShadowSidecarTraceReadbackSection",
        "renderShadowSidecarScoreComparisonSection",
        "fetchAgentTraceReadOnlyPayload",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_influence_preview_ui_readiness_identifies_api_service_files():
    text = _doc_text()
    required = [
        "Existing API/service influence preview files available for future UI use:",
        "src/agents/human_reviewed_influence_preview.py",
        "src/app/services.py",
        "src/app/api.py",
        "POST /api/human-reviewed-influence-preview",
        "human_reviewed_influence_preview_service_payload",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_influence_preview_ui_readiness_names_future_insertion_point():
    text = _doc_text()

    assert "recommended future UI insertion point" in text
    assert "inside the existing Agent Trace panel" in text
    assert "near the manual shadow sidecar score comparison section" in text


def test_phase6_influence_preview_ui_readiness_states_no_behavior_changes():
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


def test_phase6_influence_preview_ui_readiness_states_safety_counts():
    text = _doc_text()
    required = [
        "Default-off pipeline hook call site exists: 1.",
        "Live provider-backed automated agents remain zero.",
        "Mutation-authorized agents remain zero.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_influence_preview_ui_readiness_blocks_mutation_and_execution():
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


def test_phase6_influence_preview_ui_readiness_requires_default_off_flag_and_kill_switch():
    text = _doc_text()
    required = [
        "APPLYLENS_AGENTIC_PIPELINE_HUMAN_REVIEWED_INFLUENCE_PREVIEW_ENABLED",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_KILL_SWITCH",
        "Required default-off influence preview flag",
        "Required kill switch",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_influence_preview_ui_readiness_requires_safe_states():
    text = _doc_text()
    required = [
        "safe empty/not-enabled state",
        "safe blocked-by-kill-switch state",
        "safe missing deterministic context state",
        "safe missing shadow comparison state",
        "safe preview failure state",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_influence_preview_ui_readiness_requires_human_review_and_approval_gate():
    text = _doc_text()
    required = [
        "human-review required",
        "approval-gate required before any later influence",
        "human-review requirement",
        "approval-gate requirement",
        "must require human review plus an approval gate before any later influence",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_influence_preview_ui_readiness_preserves_existing_operational_flow():
    text = _doc_text()
    required = [
        "Existing stage-level logging and metrics flow must be preserved.",
        "Existing retry, rate-limit, cache, deduplication, and ATS health checks must not be removed.",
        "Existing deterministic pipeline outputs must remain the source of truth.",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_influence_preview_ui_readiness_preserves_stage_separation():
    text = _doc_text()
    required = [
        "prefilter relevance stays separate from human-reviewed influence preview",
        "LLM evaluation stays separate from human-reviewed influence preview",
        "final application scoring stays separate from human-reviewed influence preview",
        "shadow score comparison stays separate from human-reviewed influence preview",
        "influence preview stays separate from deterministic final application scoring",
    ]
    for phrase in required:
        assert phrase in text


def test_phase6_influence_preview_ui_readiness_lists_next_sequence_and_non_goals():
    text = _doc_text()
    required = [
        "add UI-only influence preview panel behind existing trace/review surface",
        "fetch default-off influence preview API only when user opens the panel",
        "render deterministic score context, shadow comparison context, proposed influence summary, score adjustment preview, ranking effect preview, human-review requirement, approval-gate requirement, and no-mutation summary",
        "add UI tests",
        "only later add approval-gated influence request",
        "only later allow approved influence to affect downstream ranking/scoring",
        "only much later guarded automation",
        "no automated decisions",
        "no mutation",
    ]
    for phrase in required:
        assert phrase in text
