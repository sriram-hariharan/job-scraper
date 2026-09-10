import re
import xml.etree.ElementTree as ET
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_RED = (ROOT / "src/app/static/app_redesign.css").read_text(encoding="utf-8")
PLANNING = (ROOT / "src/app/planning_ui.py").read_text(encoding="utf-8")
SCAN_JS = (ROOT / "src/app/static/scan_workspace.js").read_text(encoding="utf-8")
SCAN_CSS = (ROOT / "src/app/static/scan_workspace_premium.css").read_text(encoding="utf-8")
SHELL_JS = (ROOT / "src/app/static/shell.js").read_text(encoding="utf-8")
SHELL = (ROOT / "src/app/ui_shell.py").read_text(encoding="utf-8")


def test_application_status_dialog_is_shared_without_changing_machine_values():
    owners = [
        ROOT / "src/app/ui.py",
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/decisions_ui.py",
    ]
    for owner in owners:
        source = owner.read_text(encoding="utf-8")
        assert 'id="applicationActionModal" role="dialog" aria-modal="true"' in source
        assert 'class="modal-card application-status-dialog"' in source
        assert 'id="closeApplicationModalBtn"' in source
        assert 'id="applicationModalMeta"' in source
        assert 'id="applicationModalCompany"' in source
        assert 'id="applicationModalTitle"' in source
        for value in ("APPLIED", "SAVED", "NOT_APPLIED", "DISMISSED"):
            assert source.count(f'data-status-action="{value}"') == 1

    assert "#applicationActionModal .application-status-dialog" in APP_RED
    assert "grid-template-columns: repeat(2, minmax(0, 1fr));" in APP_RED


def test_wordmark_contains_only_the_exact_original_vector_glyph_paths():
    original = ET.parse(ROOT / "src/app/static/media/app-logo.svg").getroot()
    wordmark = ET.parse(ROOT / "src/app/static/media/app-wordmark.svg").getroot()
    namespace = "{http://www.w3.org/2000/svg}path"

    original_glyphs = []
    for path in original.findall(namespace):
        match = re.search(r"M\s+([-0-9.]+)\s+([-0-9.]+)", path.attrib["d"])
        if match and float(match.group(2)) > 600:
            original_glyphs.append(path.attrib)

    wordmark_glyphs = [path.attrib for path in wordmark.findall(namespace)]
    assert len(original_glyphs) == len(wordmark_glyphs) == 11
    assert wordmark_glyphs == original_glyphs
    assert "/static/media/app-wordmark.svg?v=applylens_wordmark_r1" in SHELL
    assert "/static/media/app-logo.svg" not in SHELL


def test_bulk_guard_copy_distinguishes_checking_active_and_failed_states():
    assert 'const BULK_GENERATION_CHECKING_MESSAGE = "Checking Bulk Generate status…"' in SHELL_JS
    assert "Bulk Generate status could not be verified. Retry before starting this action." in SHELL_JS
    assert "bulkGenerationCanonicalState.verified && bulkGenerationCanonicalState.active" in SHELL_JS
    assert '{ verification: "failed" }' in SHELL_JS
    assert "if (!shouldBlock) hideBulkGenerationGuardTooltip();" in SHELL_JS
    assert "Checking Bulk Generate status…" in SHELL


def test_scan_draft_fields_are_safe_but_start_scan_remains_guarded():
    draft_ids = (
        "scanWorkspaceResumeSelect",
        "scanWorkspaceCompanyInput",
        "scanWorkspaceRoleInput",
        "scanWorkspaceJobUrlInput",
        "scanWorkspaceJobDescriptionInput",
    )
    for element_id in draft_ids:
        fragment = PLANNING.split(f'id="{element_id}"', 1)[1].split(">", 1)[0]
        assert 'data-bulk-safe="true"' in fragment

    start_fragment = PLANNING.split('id="scanWorkspaceStartScanBtn"', 1)[1].split(">", 1)[0]
    assert "data-bulk-safe" not in start_fragment


def test_scan_progress_is_stateful_truthful_and_has_no_fake_timing():
    progress = PLANNING.split('id="scanWorkspaceProcessingBar"', 1)[1].split(">", 1)[0]
    assert 'role="progressbar"' in progress
    assert 'aria-valuenow="0"' in progress
    assert 'data-progress-state="idle"' in progress

    assert "width: 12%;" not in SCAN_CSS
    assert "width: var(--scan-progress, 0%);" in SCAN_CSS
    assert '[data-progress-state="running"]' in SCAN_CSS
    assert '[data-progress-state="complete"]' in SCAN_CSS
    assert '[data-progress-state="error"]' in SCAN_CSS

    request_block = SCAN_JS.split("async function beginScanWorkspaceProcessing()", 1)[1].split(
        "function buildSavedScanRescanDraft", 1
    )[0]
    assert request_block.count('fetch("/planning/start-scan"') == 1
    assert "setTimeout" not in request_block
    assert 'progressValue = 100' in request_block
    assert 'status = "error"' in request_block
    assert 'currentStageKey = "resume"' not in request_block
    assert 'aria-valuetext", "Scan running; progress percentage unavailable"' in SCAN_JS


def test_new_scan_controls_use_compact_eucalyptus_contract():
    assert "Choose a saved profile resume and target job to generate an optimization review." in PLANNING
    assert "<h3>Target job</h3>" in PLANNING
    assert 'id="scanWorkspaceJobDescriptionCount"' in PLANNING
    assert "--scan-action-primary: var(--app-action-primary, #56746d);" in SCAN_CSS
    assert "min-height: 46px;" in SCAN_CSS
    assert "border-radius: 12px;" in SCAN_CSS
    assert "outline: 3px solid var(--scan-action-focus)" in SCAN_CSS
    assert 'class="scan-workspace-clear-btn"' in PLANNING
    clear_button = PLANNING.split('id="scanWorkspaceClearIntakeBtn"', 1)[1].split("</button>", 1)[0]
    assert "<svg" in clear_button
    assert "<span>Clear</span>" in clear_button


def test_changed_shared_and_scan_assets_have_additive_cache_busters():
    hosts = [
        ROOT / "src/app/ui.py",
        ROOT / "src/app/planning_ui.py",
        ROOT / "src/app/decisions_ui.py",
        ROOT / "src/app/application_hub_ui.py",
        ROOT / "src/app/profile_ui.py",
        ROOT / "src/app/onboarding_ui.py",
    ]
    for host in hosts:
        source = host.read_text(encoding="utf-8")
        if "/static/shell.js?v=" in source:
            assert source.count("shell.js?v=eucalyptus_primary_shell_r1&ui=runtime_truth_r1") == source.count(
                "/static/shell.js?v="
            )

    assert "app_redesign.css?v=eucalyptus_primary_shell_r1&ui=runtime_truth_r1" in PLANNING
    assert "scan_workspace_premium_r1&ui=truthful_scan_r1" in PLANNING
    assert "scan_workspace_rescan6_popover_phrase_scroll&ui=truthful_scan_r1" in PLANNING
