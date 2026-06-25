from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
POLICY_PATH = ROOT / "docs/no_auto_apply_safety_policy.md"
CHECKPOINT_PATH = ROOT / "docs/phase20_no_auto_apply_safety_checkpoint.md"

REQUIRED_MARKERS = (
    "no auto-apply",
    "no auto-submit",
    "no autonomous application execution",
    "no automatic job application submission",
    "manual user control",
    "provider-call readiness is preflight/readback only",
)

REQUIRED_TAGS = (
    "phase20a-provider-call-readiness-experiment-v1",
    "phase20b-provider-call-readiness-api-readback-v1",
    "phase20c-provider-call-readiness-ui-readback-v1",
    "phase19-readonly-approval-workflow-release-v1",
)

PROTECTED_HASHES = {
    "src/app/api.py": "4953e19b5b9914310d10ff758fd72eb4abed0ffb568a59fa43284ac17a4dce34",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "029c1105e4d3ae9f023ad40418e83cc13e4dffc937406b5e7219e8934d067e35",
    "src/app/static/app_redesign.css": "cbf6e94095f4ffcd932d31f163adde1c27f115dcbaa5ae4d0939398348f1e014",
    "src/agents/provider_call_readiness_experiment.py": "d4176e889893b3acfb348c15a59a73418818e369e326f3935f4d673a50d88d28",
    "src/agents/operator_decision_capture_readback_contract.py": "4066b415b7ac84eca8e37df5b1b71cad208001fd49c76126bd928eab39992450",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
}

FORBIDDEN_RUNTIME_MARKERS = (
    "autoApply",
    "autoSubmit",
    "autonomousApplicationExecution",
    "executeApplication",
    "submitApplication",
    "applicationSubmitter",
    "applyAutomatically",
    "submitAutomatically",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _changed_files() -> set[str]:
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    return set(tracked + untracked)


def test_policy_and_checkpoint_docs_exist():
    assert POLICY_PATH.exists()
    assert CHECKPOINT_PATH.exists()
    assert _text(POLICY_PATH).startswith("# No Auto-Apply Safety Policy")
    assert _text(CHECKPOINT_PATH).startswith(
        "# Phase 20D No Auto-Apply Safety Checkpoint"
    )


def test_both_docs_contain_exact_safety_markers():
    for path in (POLICY_PATH, CHECKPOINT_PATH):
        text = _text(path).lower()
        for marker in REQUIRED_MARKERS:
            assert marker in text


def test_docs_define_a_permanent_not_temporary_boundary():
    for path in (POLICY_PATH, CHECKPOINT_PATH):
        text = _text(path).lower()
        assert "not a temporary default-off feature" in text
        assert "permanent product boundary" in text


def test_docs_reference_phase20_lineage_and_phase19_release():
    for path in (POLICY_PATH, CHECKPOINT_PATH):
        text = _text(path)
        for tag in REQUIRED_TAGS:
            assert tag in text


def test_docs_confirm_phase20a_through_c_performed_no_live_actions():
    for path in (POLICY_PATH, CHECKPOINT_PATH):
        text = _text(path).lower()
        for marker in (
            "no provider calls",
            "network calls",
            "database writes",
            "persistence",
            "mutation",
            "execution",
            "submission",
        ):
            assert marker in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase20d_changes_only_docs_tests_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "docs/no_auto_apply_safety_policy.md",
        "docs/phase20_no_auto_apply_safety_checkpoint.md",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "docs/phase20_provider_readiness_release_checkpoint.md",
        "tests/test_phase20e_provider_readiness_release_checkpoint_default_off.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if (
            "docs/phase20_provider_call_readiness_ui_readback.md"
            in path.read_text(encoding="utf-8")
        )
    }

    assert changed <= allowed | legacy_guards


def test_no_changed_runtime_file_introduces_forbidden_automation_markers():
    runtime_suffixes = {".py", ".js", ".html", ".css"}
    changed_runtime_files = [
        ROOT / relative_path
        for relative_path in _changed_files()
        if relative_path.startswith("src/")
        and Path(relative_path).suffix in runtime_suffixes
    ]

    assert changed_runtime_files == []
    for path in changed_runtime_files:
        source = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            assert marker not in source
