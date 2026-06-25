from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs/phase22_manual_review_ux_hardening.md"
JS_PATH = ROOT / "src/app/static/agentic_review.js"

REQUIRED_DOC_MARKERS = (
    "default-off",
    "read-only",
    "advisory-only",
    "manual-review only",
    "no auto-apply",
    "no auto-submit",
    "no autonomous application execution",
    "no automatic job application submission",
    "manual user control",
    "no backend",
    "no api",
    "no services",
    "no agent",
    "no pipeline",
    "no provider",
    "no db",
    "no persistence",
    "no mutation",
    "no execution",
    "no submission",
)

REQUIRED_TAGS = (
    "phase21-manual-review-workflow-release-v1",
    "phase21e-manual-review-workflow-release-checkpoint-v1",
    "phase21d-manual-review-readiness-ui-readback-v1",
    "phase20-provider-readiness-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
    "phase19-readonly-approval-workflow-release-v1",
    "phase18-safety-wrap-release-v1",
)

PROTECTED_HASHES = {
    "src/app/api.py": "bb4755cd3d74c72e7ed0af24de9d617c0ff568b61639b6d61e59c057348f424a",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/agents/manual_review_readiness_contract.py": "5253414d1343d5eae64af7fbb6f87da68f9d4931b762cac972a94c29dc9ad5a2",
    "src/agents/provider_call_readiness_experiment.py": "d4176e889893b3acfb348c15a59a73418818e369e326f3935f4d673a50d88d28",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
}


def _renderer() -> str:
    source = JS_PATH.read_text(encoding="utf-8")
    start = source.index(
        "function renderManualReviewReadinessReadbackSection"
    )
    end = source.index(
        "\nfunction renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def test_phase22a_doc_exists_with_exact_title():
    assert DOC_PATH.exists()
    assert DOC_PATH.read_text(encoding="utf-8").startswith(
        "# Phase 22A Manual-Review UX Hardening"
    )


def test_docs_contain_required_safety_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text


def test_docs_reference_required_release_tags():
    text = DOC_PATH.read_text(encoding="utf-8")

    for tag in REQUIRED_TAGS:
        assert tag in text


def test_ui_contains_visible_manual_review_safety_wording():
    renderer = _renderer()

    for marker in (
        "Manual review support only",
        "Manual user control required",
        "Read-only",
        "Advisory-only",
        "Manual-review only",
        "no auto-apply",
        "no auto-submit",
        "no autonomous application execution",
        "no automatic job application submission",
    ):
        assert marker in renderer


def test_renderer_adds_no_controls_or_storage_writes():
    renderer = _renderer().lower()

    for marker in (
        "<button",
        "<input",
        "<form",
        "data-apply",
        "data-submit",
        "data-approval",
        "data-provider",
        "data-execute",
        "data-autonomous",
        "localstorage.setitem",
        "sessionstorage.setitem",
    ):
        assert marker not in renderer


def test_phase22a_adds_no_endpoint_urls_or_fetch_changes():
    diff = subprocess.check_output(
        ["git", "diff", "--", "src/app/static/agentic_review.js"],
        cwd=ROOT,
        text=True,
    )
    added_lines = "\n".join(
        line[1:]
        for line in diff.splitlines()
        if line.startswith("+") and not line.startswith("+++")
    )

    endpoint_lines = [
        line for line in added_lines.splitlines() if '"/api/' in line
    ]
    assert endpoint_lines == [
        '      "/api/core-agent-evidence-materialization-preview",'
    ]
    assert "fetch(" not in added_lines
    assert added_lines.count("fetchJson(") == 1
    assert "manual_review_readiness_fixture" not in added_lines
    assert "manual_review_readiness_api_fetch" not in added_lines


def test_protected_backend_and_helper_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase22a_changes_only_static_docs_tests_and_legacy_guards():
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    changed = set(tracked + untracked) - {
        "docs/core_agent_automation_mutation_inventory.md",
        "docs/phase22_core_agent_automation_mutation_inventory.md",
        "src/agents/core_agent_evidence_materialization_preview.py",
        "docs/phase22_core_agent_evidence_materialization_preview.md",
        "tests/test_phase22c_core_agent_evidence_materialization_preview_default_off.py",
        "src/app/api.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase22_core_agent_evidence_materialization_ui_readback.md",
        "tests/test_phase22e_core_agent_evidence_materialization_ui_readback_default_off.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback 2.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off 2.py",
    }
    allowed = {
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase22_manual_review_ux_hardening.md",
        "tests/test_phase22a_manual_review_ux_hardening_default_off.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                    "tests/test_phase21e_manual_review_workflow_release_checkpoint_default_off.py",
                    "bb4755cd3d74c72e7ed0af24de9d617c0ff568b61639b6d61e59c057348f424a",
                    "f7cdf115e412f34094e80e71b18e86f94365715c6f5010faa8e2ba7fe41daeff",
                "962232082cf71e5c85150ff52de5466b11a791567692a45e768dae6d5d11c6ba",
            )
        )
    }

    assert changed <= allowed | legacy_guards
