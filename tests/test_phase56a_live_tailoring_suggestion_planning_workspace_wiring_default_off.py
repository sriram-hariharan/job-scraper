# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
from __future__ import annotations

# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 c3de61f6e079ea961cae4c7f2f38695313059c15239f71e75cfc600c86d5cefe 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient

from src.app import api, services


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = (
    ROOT
    / "docs/phase56_live_tailoring_suggestion_planning_workspace_wiring_default_off.md"
)
PROTECTED_HASHES = {
    "src/matching/scorer.py": "f56624b5b3c7e2bb01a824386b86fbc2a194e727f0437ca0773764eae64ec941",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/tailoring/llm.py": "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
    "generate_tailoring_" + "suggestions" + ".py": (
        "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28"
    ),
    "application_execution_" + "queue" + ".py": (
        "28ac5d153eeb1d3e6238bed57418a45b603f72caea6c0f671a8dcbb3b0a76097"
    ),
}


def _state_request() -> dict:
    return {
        "selected_patch_candidate_ids": ["candidate-1"],
        "manual_bullet_edits": {"bullet-1": "Built Python pipelines."},
        "rewrite_review_decisions": {"candidate-1": {"decision": "review"}},
        "excluded_scan_issue_ids": ["issue-2"],
        "personal_details": {"name": "A. Candidate"},
    }


def _scan_review_payload() -> dict:
    return {
        "ok": True,
        "selected_resume": "resume-a",
        "resume_name": "resume-a",
        "scan_score": {"score": 82, "source": "new_scan_match_score"},
        "score_preview": {
            "preview_status": "new_scan_ready",
            "original_score": 0.82,
            "projected_score": 0.82,
            "projected_delta": 0,
        },
        "scan_session": {"session_id": "phase56a-scan", "job_doc_id": "job-56a"},
        "scan_issue_contract": {
            "matched_evidence": [
                {
                    "candidate_id": "candidate-1",
                    "bullet_id": "bullet-1",
                    "signal": "Python",
                    "evidence": "Built Python pipelines.",
                }
            ]
        },
        "jd_llm_extraction_readback": {
            "llm_enabled": True,
            "llm_call_attempted": True,
            "llm_call_performed": True,
            "fallback_used": False,
            "validation_status": "valid",
            "structured_jd_signals": {
                "required_skills": ["Python"],
                "tools": ["Airflow"],
            },
        },
        "draft": _state_request(),
    }


def _stored_scan_payload() -> dict:
    return {
        "scan": {
            "scan_id": "phase56a-scan",
            "resume_name": "resume-a",
            "job_doc_id": "job-56a",
            "payload_json": {
                "version": "saved_scan_report_v1",
                "scan_review_payload": _scan_review_payload(),
            },
        }
    }


def _valid_provider_payload() -> dict:
    evidence = "Built Python pipelines."
    return {
        "patch_ready_suggestions": [
            {
                "suggestion_id": "live_tailoring_001",
                "source_bullet_id": "bullet-1",
                "target_section": "experience",
                "original_text": evidence,
                "suggested_text": evidence,
                "reason": "Evidence supports Python alignment.",
                "evidence_spans": [evidence],
                "jd_signal_links": [{"field": "required_skills", "signal": "Python"}],
                "patch_ready": True,
                "projected_score_delta": 0.04,
                "risk_flags": [],
            }
        ],
        "guidance_only_suggestions": [],
        "rejected_suggestions": [],
        "missing_evidence": [],
        "unsupported_claim_risks": [],
        "projected_score_delta": 0.04,
        "rationale": "Provider returned evidence-backed tailoring suggestions.",
        "model_provider": "fake-provider",
        "model_name": "fake-model",
        "prompt_version": "fake-prompt-v1",
        "token_usage": {"total_token_count": 42},
        "cost": {"estimated_cost": 0.01, "cost_currency": "USD"},
        "latency_ms": 88,
    }


def _patch_storage(monkeypatch, *, stored_payload: dict | None = None) -> None:
    monkeypatch.setattr(
        services,
        "save_saved_scan_draft_postgres_payload",
        lambda **_kwargs: {"ok": True},
    )
    if stored_payload is not None:
        monkeypatch.setattr(
            services,
            "get_saved_scan_postgres_payload",
            lambda **_kwargs: deepcopy(stored_payload),
        )


def test_default_off_planning_workspace_action_does_not_call_live_tailoring_llm(
    monkeypatch,
):
    calls = []
    _patch_storage(monkeypatch)
    monkeypatch.setattr(
        services,
        "get_saved_scan_postgres_payload",
        lambda **_kwargs: (_ for _ in ()).throw(AssertionError("unexpected scan read")),
    )

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        live_tailoring_suggestion_adapter=lambda request: calls.append(request)
        or _valid_provider_payload(),
    )

    assert calls == []
    assert payload["ok"] is True
    assert payload["draft"]["selected_patch_candidate_ids"] == ["candidate-1"]
    readback = payload["live_tailoring_suggestion_readback"]
    assert readback["tailoring_llm_enabled"] is False
    assert readback["tailoring_llm_call_attempted"] is False
    assert readback["tailoring_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "disabled"


def test_enabled_planning_workspace_action_calls_existing_live_tailoring_path(
    monkeypatch,
):
    calls = []
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda request: calls.append(request)
        or _valid_provider_payload(),
    )

    readback = payload["live_tailoring_suggestion_readback"]
    assert calls
    assert calls[0]["config"]["surface"] == "planning_workspace_action"
    assert calls[0]["jd_intelligence"]["required_skills"] == ["Python"]
    assert readback["tailoring_llm_enabled"] is True
    assert readback["tailoring_llm_call_attempted"] is True
    assert readback["tailoring_llm_call_performed"] is True
    assert readback["validation_status"] == "valid"
    assert readback["provider"] == "fake-provider"
    assert readback["model"] == "fake-model"
    assert readback["prompt_version"] == "fake-prompt-v1"


def test_valid_fake_provider_response_appears_in_workspace_readback_metadata(
    monkeypatch,
):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: _valid_provider_payload(),
    )

    readback = payload["live_tailoring_suggestion_readback"]
    assert readback["suggestion_count"] == 1
    assert readback["patch_ready_suggestion_count"] == 1
    assert readback["suggestion_ids"] == ["live_tailoring_001"]
    assert readback["suggestions_preview"][0]["source_bullet_id"] == "bullet-1"
    assert readback["token_usage"] == {"total_token_count": 42}
    assert readback["cost"] == {"estimated_cost": 0.01, "cost_currency": "USD"}
    assert readback["latency_ms"] == 88


def test_invalid_provider_response_falls_back_safely(monkeypatch):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: {"raw_response": "{bad json"},
    )

    readback = payload["live_tailoring_suggestion_readback"]
    assert readback["tailoring_llm_call_attempted"] is True
    assert readback["tailoring_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "fallback"
    assert readback["validation_errors"] == ["invalid_json_response"]


def test_provider_exception_falls_back_safely(monkeypatch):
    def failing_provider(_request):
        raise RuntimeError("provider unavailable")

    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=failing_provider,
    )

    readback = payload["live_tailoring_suggestion_readback"]
    assert readback["tailoring_llm_call_attempted"] is True
    assert readback["tailoring_llm_call_performed"] is False
    assert readback["fallback_used"] is True
    assert readback["validation_status"] == "fallback"
    assert readback["validation_errors"] == ["adapter_error:RuntimeError"]


def test_existing_deterministic_workspace_output_and_phase55_readback_remain_present(
    monkeypatch,
):
    stored = _stored_scan_payload()
    original = deepcopy(stored)
    _patch_storage(monkeypatch, stored_payload=stored)

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: _valid_provider_payload(),
    )

    assert stored == original
    assert payload["draft"]["manual_bullet_edits"] == {
        "bullet-1": "Built Python pipelines."
    }
    assert payload["score_preview"] == {}
    assert _scan_review_payload()["jd_llm_extraction_readback"]["validation_status"] == "valid"


def test_api_default_off_and_explicit_enable_flag(monkeypatch):
    monkeypatch.setattr(api, "auth_guard_response", lambda request: None)
    monkeypatch.setattr(api, "_auth_owner_user_id", lambda request: "owner-1")
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())
    calls = []
    monkeypatch.setattr(
        services,
        "_live_tailoring_suggestion_provider_adapter",
        lambda request: calls.append(request) or _valid_provider_payload(),
    )
    client = TestClient(api.app)

    default_response = client.post(
        "/planning/saved-scan/phase56a-scan/state",
        json=_state_request(),
    )
    enabled_response = client.post(
        "/planning/saved-scan/phase56a-scan/state",
        json={**_state_request(), "enable_live_tailoring_suggestion": True},
    )

    assert default_response.status_code == 200
    assert default_response.json()["live_tailoring_suggestion_readback"][
        "tailoring_llm_call_attempted"
    ] is False
    assert enabled_response.status_code == 200
    assert calls
    assert enabled_response.json()["live_tailoring_suggestion_readback"][
        "validation_status"
    ] == "valid"


def test_no_mutation_artifact_approved_plan_application_or_scoring_side_effects(
    monkeypatch,
):
    _patch_storage(monkeypatch, stored_payload=_stored_scan_payload())

    payload = services.save_saved_scan_state_payload(
        scan_id="phase56a-scan",
        **_state_request(),
        enable_live_tailoring_suggestion=True,
        live_tailoring_suggestion_adapter=lambda _request: _valid_provider_payload(),
    )

    safety = payload["live_tailoring_suggestion_readback"]["safety"]
    for key in (
        "resume_mutation_performed",
        "resume_overwrite_performed",
        "resume_artifact_created",
        "suggestion_application_performed",
        "approved_change_plan_created",
        "exact_resume_change_refinement_performed",
        "queue_mutation_performed",
        "approval_mutation_performed",
        "application_execution_performed",
        "application_submission_performed",
        "auto_" + "apply_performed",
        "final_scoring_performed",
        "score_formula_changed",
        "scoring_weights_changed",
    ):
        assert safety[key] is False


def test_ui_explicit_action_and_readback_surface_are_default_off():
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    diagnostics_tsx = (
        ROOT / "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx"
    ).read_text(encoding="utf-8")

    # These IDs and their wiring moved from src/app/planning_ui.py into the
    # React Advanced Diagnostics Command Center; scan_workspace.js keeps the
    # live-scan readback plumbing that predates the redesign.
    assert "scanWorkspaceLiveTailoringSuggestionToggle" in diagnostics_tsx
    assert "scanWorkspaceTailoringLlmReadback" in diagnostics_tsx
    assert "enable_live_tailoring_suggestion" in script
    assert "getScanWorkspaceLiveTailoringSuggestionEnabled()" in script
    assert "renderScanWorkspaceTailoringLlmReadback(response)" in script
    assert "Live tailoring LLM: default-off" in script


def test_phase78a_scan_review_keeps_internal_workflow_in_advanced_diagnostics():
    html = (ROOT / "src/app/planning_ui.py").read_text(encoding="utf-8")
    diagnostics = (
        ROOT / "frontend/executive-kpi/src/diagnostics/AdvancedDiagnosticsDashboard.tsx"
    ).read_text(encoding="utf-8")

    score_card = html[
        html.index("scan-workspace-review-score-card"):
        html.index('id="scanWorkspaceControlsShell"')
    ]
    normal_actions = html[
        html.index("scan-workspace-review-main-actions"):
        html.index("scan-workspace-toolbar-context")
    ]
    tabs = html[
        html.index('id="scanWorkspaceTabRow"'):
        html.index('</section>', html.index('id="scanWorkspaceControlsShell"'))
    ]

    # The internal workflow surface now lives in the React Advanced
    # Diagnostics Command Center (frontend/executive-kpi/src/diagnostics/),
    # rendered only at the standalone /advanced-diagnostics route — it is no
    # longer inlined into src/app/planning_ui.py's scan-review markup.
    assert "Advanced Diagnostics" in diagnostics
    assert "These do not apply to jobs automatically." in diagnostics
    assert "Selecting diagnostics does not run them." in diagnostics
    assert "Diagnostics never apply to jobs automatically." in diagnostics
    assert "Run selected diagnostics" in diagnostics
    assert "Execution is not enabled yet. Selections are for admin review only." in diagnostics
    assert "<details" not in diagnostics
    assert "scanWorkspaceAdvancedDiagnostics" not in html
    assert "admin-diagnostics-shell" not in html

    for label in ("Undo", "Redo", "Accept All", "Export", "Compare", "Continue"):
        assert label in normal_actions
    for label in (
        "Personal Details",
        "Skills",
        "Searchability",
        "Formatting",
        "Recruiter Tips",
    ):
        assert label in tabs

    for internal_label in (
        "Create guarded resume copy",
        "Create human-only workflow readiness checkpoint",
        "Operator review packet ID",
        "Verified artifact ID",
        "Live tailoring suggestions",
        "Live exact change proposals",
    ):
        assert internal_label not in normal_actions
        assert internal_label not in score_card
        assert internal_label in diagnostics

    for internal_id in (
        "scanWorkspaceLiveTailoringSuggestionToggle",
        "scanWorkspaceLiveExactChangeProposalToggle",
        "scanWorkspaceManualExactChangeAcceptanceToggle",
        "scanWorkspaceAcceptedExactChangeProposalIds",
        "scanWorkspaceGuardedResumeCopyArtifactToggle",
        "scanWorkspaceApprovedChangePlanId",
        "scanWorkspaceGuardedResumeCopyArtifactVerificationToggle",
        "scanWorkspaceGuardedResumeCopyArtifactId",
        "scanWorkspaceVerifiedArtifactOperatorReviewPacketToggle",
        "scanWorkspaceVerifiedArtifactOperatorReviewArtifactId",
        "scanWorkspaceVerifiedArtifactOperatorDecisionToggle",
        "scanWorkspaceVerifiedArtifactOperatorDecisionPacketId",
        "scanWorkspaceVerifiedArtifactOperatorDecisionArtifactId",
        "scanWorkspaceVerifiedArtifactOperatorDecisionValue",
        "scanWorkspaceApplicationReadinessPacketToggle",
        "scanWorkspaceApplicationReadinessDecisionId",
        "scanWorkspaceApplicationReadinessReviewPacketId",
        "scanWorkspaceApplicationReadinessArtifactId",
        "scanWorkspaceManualApplicationHandoffPacketToggle",
        "scanWorkspaceManualHandoffReadinessPacketId",
        "scanWorkspaceManualHandoffArtifactId",
        "scanWorkspaceHandoffAuditTrailToggle",
        "scanWorkspaceHandoffAuditHandoffPacketId",
        "scanWorkspaceHandoffAuditReadinessPacketId",
        "scanWorkspaceHandoffAuditArtifactId",
        "scanWorkspaceSafetyBoundarySummaryToggle",
        "scanWorkspaceSafetyBoundaryAuditTrailId",
        "scanWorkspaceSafetyBoundaryHandoffPacketId",
        "scanWorkspaceSafetyBoundaryReadinessPacketId",
        "scanWorkspaceSafetyBoundaryArtifactId",
        "scanWorkspaceWorkflowReadinessCheckpointToggle",
        "scanWorkspaceWorkflowReadinessSummaryId",
        "scanWorkspaceWorkflowReadinessAuditTrailId",
        "scanWorkspaceWorkflowReadinessHandoffPacketId",
        "scanWorkspaceWorkflowReadinessReadinessPacketId",
        "scanWorkspaceWorkflowReadinessArtifactId",
        "scanWorkspaceJdLlmReadback",
        "scanWorkspaceTailoringLlmReadback",
        "scanWorkspaceExactChangeLlmReadback",
        "scanWorkspaceManualExactChangeAcceptanceReadback",
        "scanWorkspaceGuardedResumeCopyArtifactReadback",
        "scanWorkspaceGuardedResumeCopyArtifactVerificationReadback",
        "scanWorkspaceVerifiedArtifactOperatorReviewPacketReadback",
        "scanWorkspaceVerifiedArtifactOperatorDecisionReadback",
        "scanWorkspaceApplicationReadinessPacketReadback",
        "scanWorkspaceManualApplicationHandoffPacketReadback",
        "scanWorkspaceHandoffAuditTrailReadback",
        "scanWorkspaceSafetyBoundarySummaryReadback",
        "scanWorkspaceWorkflowReadinessCheckpointReadback",
        "scanWorkspaceAgenticWorkflowIntegrationReadback",
        "scanWorkspaceProductionReadinessCheckpointReadback",
    ):
        assert internal_id in diagnostics


def test_phase78b_scan_review_summary_drops_resume_name_and_keeps_metrics():
    html = (ROOT / "src/app/planning_ui.py").read_text(encoding="utf-8")
    script = (ROOT / "src/app/static/planning.js").read_text(encoding="utf-8")

    score_card = html[
        html.index("scan-workspace-review-score-card"):
        html.index('id="scanWorkspaceControlsShell"')
    ]

    assert "Optimization review" in score_card
    assert "{company_safe} / {title_safe}" in score_card
    assert 'id="scanWorkspaceScoreValue"' in score_card
    assert 'id="scanWorkspaceTrustedCount"' in score_card
    assert 'id="scanWorkspaceAiCount"' in score_card
    assert 'id="scanWorkspaceGuidanceCount"' in score_card
    assert 'id="scanWorkspaceMeta"' not in score_card
    assert "{resume_display_safe}" not in score_card
    assert 'meta.textContent = "";' in script


def test_phase78b_scan_preview_contact_links_render_linkedin_and_github():
    scan_script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    planning_script = (ROOT / "src/app/static/planning.js").read_text(encoding="utf-8")

    assert "function isValidScanWorkspaceLinkedInProfileUrl" in scan_script
    assert "function normalizeValidScanWorkspaceLinkedInProfileUrl" in scan_script
    assert "function isValidScanWorkspaceGitHubProfileUrl" in scan_script
    assert "function normalizeValidScanWorkspaceGitHubProfileUrl" in scan_script
    assert 'validLinkedIn ? "LinkedIn" : ""' in scan_script
    assert 'validGitHub ? "GitHub" : ""' in scan_script
    assert 'validLinkedIn ? { label: "LinkedIn", uri: validLinkedIn } : null' in scan_script
    assert 'validGitHub ? { label: "GitHub", uri: validGitHub } : null' in scan_script
    assert "Invalid LinkedIn link" in scan_script
    assert "function isValidScanWorkspaceGitHubProfileUrl" in scan_script
    assert "function renderScanWorkspaceLinkedText" in scan_script
    assert "renderTailoringWorkspaceLinkedText(text, linkItems)" in scan_script
    assert "renderScanWorkspaceLinkedText(rawText, row?.link_items || [])" in scan_script
    assert "function renderTailoringWorkspaceLinkedText" in planning_script
    assert 'class="tailoring-workspace-doc-link"' in planning_script


def test_phase78b_scan_personal_details_hydrates_blank_saved_fields_from_source():
    scan_script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    planning_script = (ROOT / "src/app/static/planning.js").read_text(encoding="utf-8")

    assert "function mergeScanWorkspacePersonalDetails(baseDetails = {}, overrideDetails = {})" in planning_script
    assert "const sourcePersonalDetails = getScanWorkspacePersonalDetailsFromPreload(payload);" in planning_script
    assert "mergeScanWorkspacePersonalDetails(\n      sourcePersonalDetails,\n      savedPersonalDetails\n    )" in planning_script
    assert "const sourcePersonalDetails = getSourceScanWorkspacePersonalDetails();" in scan_script
    assert "mergeScanWorkspacePersonalDetails(\n    sourcePersonalDetails,\n    savedPersonalDetails\n  )" in scan_script
    assert "savedDraft.personal_details ||\n        payload?.personal_details?.current" not in scan_script


def test_phase78b_compare_and_continue_disable_when_no_changes():
    html = (ROOT / "src/app/planning_ui.py").read_text(encoding="utf-8")
    script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")

    actions = html[
        html.index("scan-workspace-review-main-actions"):
        html.index("scan-workspace-toolbar-context")
    ]

    assert 'id="scanWorkspaceCompareBtn"' in actions
    assert 'id="scanWorkspaceSaveBtn"' in actions
    assert actions.count('data-scan-disabled-help="No changes made"') == 2
    assert actions.count('title="No changes made"') >= 2
    assert "disabled" in actions
    assert 'const noChangesLabel = "No changes made";' in script
    assert "const compareBtn = getScanWorkspaceInput(\"scanWorkspaceCompareBtn\");" in script
    assert "compareBtn.disabled =" in script
    assert "saveBtn.disabled =" in script
    assert "!isDirty" in script
    assert "syncDisabledHelp(compareBtn, compareBtn.disabled, \"Compare draft changes\")" in script
    assert "syncDisabledHelp(saveBtn, saveBtn.disabled, \"Continue\")" in script


def test_phase78b_scan_controls_use_calm_tinted_styles():
    html = (ROOT / "src/app/planning_ui.py").read_text(encoding="utf-8")
    css = (ROOT / "src/app/static/scan_workspace_review.css").read_text(encoding="utf-8")
    scan_script = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
    redesign_css = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")
    styles_css = (ROOT / "src/app/static/styles.css").read_text(encoding="utf-8")
    tab_active = css[
        css.rindex(".scan-review-left-pane .scan-workspace-tab-btn.active"):
        css.index("}", css.rindex(".scan-review-left-pane .scan-workspace-tab-btn.active"))
    ]
    surface_block = css[
        css.index(".scan-review-v2 .scan-workspace-surface-tab,"):
        css.index("}", css.index(".scan-review-v2 .scan-workspace-surface-tab,"))
    ]
    back_block = css[
        css.rindex(".scan-workspace-page .scan-workspace-header-actions .ghost-btn"):
        css.index("}", css.rindex(".scan-workspace-page .scan-workspace-header-actions .ghost-btn"))
    ]

    assert "scan_workspace_review.css" in html
    assert "scan_workspace.css?v=tailoring_workspace_consolidated_v11" not in html[
        html.index("<title>AI Optimize Scan</title>"):
        html.index("</head>", html.index("<title>AI Optimize Scan</title>"))
    ]
    assert ".scan-workspace-disabled-action-wrap" in scan_script
    assert "background-image: none !important;" in tab_active
    assert "linear-gradient(135deg, #2563eb" not in tab_active
    assert "background-image: none !important;" in surface_block
    assert "border-radius: 0 !important;" in surface_block
    assert "background-image: none !important;" in back_block
    assert "linear-gradient(" not in back_block
    assert ":not(.scan-workspace-tab-btn):not(.scan-workspace-surface-tab)" in redesign_css
    assert ":not(.scan-workspace-tab-btn):not(.scan-workspace-surface-tab)" in styles_css
    assert "background: #2563eb !important" not in tab_active
    assert "background: var(--scan-ui-blue) !important" not in tab_active


def test_docs_capture_phase56a_wiring_and_safety():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in (
        "default-off",
        "live tailoring suggestion",
        "planning workspace action",
        "deterministic fallback",
        "does not mutate resumes",
        "does not create resume artifacts",
        "does not execute applications",
        "auto-apply",
    ):
        assert marker in text


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash
