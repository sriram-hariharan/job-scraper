from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLANNING_JS = ROOT / "src/app/static/planning.js"
SCAN_CSS = ROOT / "src/app/static/scan_workspace_review.css"
SERVICES_PY = ROOT / "src/app/services.py"


def _function_block(source: str, name: str) -> str:
    start = source.index(f"function {name}")
    brace = source.index("{", start)
    depth = 0
    for index in range(brace, len(source)):
        if source[index] == "{":
            depth += 1
        elif source[index] == "}":
            depth -= 1
            if depth == 0:
                return source[start : index + 1]
    raise AssertionError(f"Could not locate function body for {name}")


def test_scan_workspace_reads_packet_hard_requirement_diagnostics_from_artifact():
    source = PLANNING_JS.read_text(encoding="utf-8")
    readback_block = _function_block(source, "loadScanWorkspaceHardRequirementDiagnostics")

    assert "getTailoringWorkspaceBasePacketKey(context)" in readback_block
    assert 'loadArtifact(packetKey, context?.planningOutputDir || "")' in readback_block
    assert "packet?.summary?.hard_requirement_diagnostics" in readback_block
    assert "scanWorkspaceState.hardRequirementDiagnosticsStatus = \"failed\"" in readback_block
    assert "throw" not in readback_block


def test_scan_workspace_warning_renders_only_when_diagnostics_exist():
    source = PLANNING_JS.read_text(encoding="utf-8")
    banner_block = _function_block(source, "renderScanWorkspaceHardRequirementDiagnosticsBanner")
    render_block = _function_block(source, "renderScanWorkspaceView")

    assert 'if (!diagnostics.length) return "";' in banner_block
    assert (
        "Hard requirement gap: Active TS/Top Secret clearance was required but not found in the selected resume."
        in banner_block
    )
    assert "scan-workspace-hard-requirement-warning" in banner_block
    assert "renderScanWorkspaceHardRequirementDiagnosticsBanner()" in render_block
    assert "renderScanWorkspaceTaxonomyPanel(activePanel)" in render_block


def test_scan_workspace_warning_does_not_change_scores_or_missing_counts():
    source = PLANNING_JS.read_text(encoding="utf-8")
    readback_block = _function_block(source, "loadScanWorkspaceHardRequirementDiagnostics")
    banner_block = _function_block(source, "renderScanWorkspaceHardRequirementDiagnosticsBanner")
    generate_block = _function_block(source, "buildGenerateSuggestionsPayload")

    for block in (readback_block, banner_block, generate_block):
        assert "missing_requirement_count" not in block
        assert "final_score" not in block
        assert "score" not in block

    assert "hard_requirement_diagnostics" not in generate_block


def test_scan_workspace_warning_is_frontend_only_no_service_readback_change():
    services_source = SERVICES_PY.read_text(encoding="utf-8")

    assert "scan-workspace-hard-requirement-warning" not in services_source
    assert "missing_active_ts_clearance" not in services_source
    assert "hard_requirement_diagnostics" not in services_source


def test_scan_workspace_warning_has_compact_css_only_for_interactive_summary():
    source = SCAN_CSS.read_text(encoding="utf-8")
    warning_block = source.split(
        "#scanWorkspaceInteractiveSummary .scan-workspace-hard-requirement-warning",
        1,
    )[1].split("/* scan_review_v2_58", 1)[0]

    assert "#scanWorkspaceInteractiveSummary .scan-workspace-hard-requirement-warning" in source
    assert "border-radius: 8px !important;" in warning_block
    assert "html[data-theme=\"dark\"] #scanWorkspaceInteractiveSummary" in warning_block
    assert ".planning-table" not in warning_block
