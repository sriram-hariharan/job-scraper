from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANNING = (ROOT / "src/app/planning_ui.py").read_text(encoding="utf-8")
SCAN_JS = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
SCAN_CSS = (ROOT / "src/app/static/scan_workspace_premium.css").read_text(
    encoding="utf-8"
)


def _function(name: str, next_name: str) -> str:
    return SCAN_JS.split(f"function {name}", 1)[1].split(
        f"function {next_name}", 1
    )[0]


def test_ready_screen_preserves_exact_six_stage_meanings():
    stages = SCAN_JS.split("const SCAN_WORKSPACE_PROCESSING_STAGES = [", 1)[1].split(
        "];", 1
    )[0]
    expected = (
        ("prepare", "Prepare request"),
        ("resume", "Load resume"),
        ("ai_analysis", "Analyze job with AI"),
        ("validate_score", "Validate and score match"),
        ("review_payload", "Build review payload"),
        ("persist", "Save report"),
    )

    assert stages.count("key:") == 6
    for key, title in expected:
        assert f'key: "{key}"' in stages
        assert f'title: "{title}"' in stages


def test_ready_progress_is_truthful_and_error_cannot_render_complete():
    renderer = _function(
        "updateScanWorkspaceProcessingView()", "readScanWorkspaceFileAsBase64"
    )
    request = SCAN_JS.split("async function beginScanWorkspaceProcessing()", 1)[1].split(
        "function buildSavedScanRescanDraft", 1
    )[0]

    assert 'progressLabel.textContent = isComplete\n      ? "100% complete"' in renderer
    assert 'progressBar.dataset.progressState = status' in renderer
    assert 'isComplete ? "Scan complete" : isError ? "Scan stopped before completion"' in renderer
    assert 'scanWorkspaceProcessingState.progressValue = 100' in request
    catch_block = request.split("} catch (err) {", 1)[1]
    assert 'scanWorkspaceProcessingState.status = "error"' in catch_block
    assert "progressValue = 100" not in catch_block
    assert "setTimeout" not in request
    assert request.count('fetch("/planning/start-scan"') == 1


def test_scan_summary_is_one_surface_with_primary_company_and_role():
    summary = _function(
        "buildScanWorkspaceProcessingSummaryHtml(draft)",
        "buildScanWorkspaceProcessingStepsHtml",
    )

    assert 'class="scan-workspace-processing-summary-surface"' in summary
    assert '<h2>Scan summary</h2>' in summary
    assert "scan-workspace-processing-summary-card" not in summary
    assert "const cards = [" not in summary
    assert 'className: "is-company"' in summary
    assert 'className: "is-role"' in summary
    assert "grid-template-columns: minmax(180px, 0.8fr) minmax(260px, 1.35fr);" in SCAN_CSS
    assert "-webkit-line-clamp: 2;" in SCAN_CSS


def test_secondary_summary_values_remain_derived_and_truthful():
    summary = _function(
        "buildScanWorkspaceProcessingSummaryHtml(draft)",
        "buildScanWorkspaceProcessingStepsHtml",
    )

    assert "Saved resume · ${draft.savedResumeName}" in summary
    assert 'title: resumeSource' in summary
    assert 'draft.jobDescriptionText.length.toLocaleString("en-US")' in summary
    assert 'draft.jobUrl ? "Provided" : "Not provided"' in summary
    assert 'scanWorkspaceProcessingState.resultMeta?.scanTimestamp' in summary
    assert "formatScanWorkspaceSavedAt(scanTimestamp)" in summary
    assert "new Date()" not in summary


def test_ai_status_and_provider_model_use_actual_response_metadata():
    presentation = _function(
        "getScanWorkspaceProcessingLlmPresentation()",
        "buildScanWorkspaceProcessingSummaryItemHtml",
    )
    request = SCAN_JS.split("async function beginScanWorkspaceProcessing()", 1)[1].split(
        "function buildSavedScanRescanDraft", 1
    )[0]

    assert 'String(data?.llm_analysis_status || "")' in request
    assert "data?.jd_llm_extraction_readback" in request
    assert "pendingPayload?.jd_llm_extraction_readback" in request
    assert 'llmReadback?.llm_call_attempted === true' in request
    assert 'provider: String(llmReadback?.provider || "")' in request
    assert 'model: String(llmReadback?.model || "")' in request
    assert 'label: "AI analysis succeeded"' in presentation
    assert 'label: "AI unavailable · deterministic fallback used"' in presentation
    assert 'label: "AI analysis disabled"' in presentation
    assert "gpt-5-mini" not in SCAN_JS
    assert "OpenAI /" not in SCAN_JS


def test_fallback_never_uses_ai_success_completion_copy():
    renderer = _function(
        "updateScanWorkspaceProcessingView()", "readScanWorkspaceFileAsBase64"
    )

    assert 'llmStatus === "succeeded"\n        ? "AI-assisted match report ready"\n        : "Match report ready"' in renderer
    assert 'llmStatus === "fallback"' in renderer
    assert "AI analysis was unavailable, so ApplyLens used deterministic fallback." in renderer
    assert '[data-llm-analysis-status="fallback"]' in SCAN_CSS


def test_existing_report_transition_is_reused_by_view_report():
    markup = PLANNING.split('id="scanWorkspaceProcessingComplete"', 1)[1].split(
        "</div>\n        </div>\n      </section>", 1
    )[0]
    handler = _function(
        "bindScanWorkspaceProcessingShell()", "normalizeScanWorkspaceAnnotationDecision"
    )

    assert 'id="scanWorkspaceProcessingOkBtn"' in markup
    assert "<span>View Report</span>" in markup
    assert 'href="/profile/saved-scans"' in markup
    assert "<span>Go to Saved Scans</span>" in markup
    assert "applyNewScanWorkspaceReviewPayload(scanWorkspaceProcessingState.pendingReviewPayload)" in handler
    assert "fetch(" not in handler
    assert 'href="/profile/saved-scans"' not in SCAN_JS


def test_premium_timeline_completion_and_dark_mode_styles_are_present():
    assert ".scan-workspace-processing-step-icon" in SCAN_CSS
    assert ".scan-workspace-processing-step.is-complete .scan-workspace-processing-step-pill" in SCAN_CSS
    assert "background: var(--scan-action-soft);" in SCAN_CSS
    assert ".scan-workspace-processing-complete-actions" in SCAN_CSS
    assert "html[data-theme=\"dark\"] .scan-workspace-processing-summary-surface" in SCAN_CSS
    assert "@media (max-width: 900px)" in SCAN_CSS
    assert "@media (max-width: 620px)" in SCAN_CSS


def test_changed_scan_assets_have_additive_cache_markers():
    assert "scan_workspace_premium_r1&ui=truthful_scan_r1&ready=summary_r1" in PLANNING
    assert "llm=default_on_r1&ready=summary_r1" in PLANNING
