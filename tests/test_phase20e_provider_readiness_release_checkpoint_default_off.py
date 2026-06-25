from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs/phase20_provider_readiness_release_checkpoint.md"

REQUIRED_TAGS = (
    "phase20a-provider-call-readiness-experiment-v1",
    "phase20b-provider-call-readiness-api-readback-v1",
    "phase20c-provider-call-readiness-ui-readback-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
    "phase19-readonly-approval-workflow-release-v1",
    "phase18-safety-wrap-release-v1",
)

REQUIRED_SAFETY_MARKERS = (
    "provider-readiness/preflight/readback only",
    "no live provider calls",
    "no network calls",
    "no database writes",
    "no approval creation",
    "no decision persistence",
    "no scoring mutation",
    "no ranking mutation",
    "no queue mutation",
    "no resume mutation",
    "no application mutation",
    "no execution",
    "no submission",
    "no auto-apply",
    "no auto-submit",
    "no autonomous application execution",
    "no automatic job application submission",
    "manual user control",
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


def _text() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_release_checkpoint_doc_exists():
    assert DOC_PATH.exists()
    assert _text().startswith(
        "# Phase 20E Provider Readiness Release Checkpoint"
    )


def test_checkpoint_references_all_release_tags():
    text = _text()

    for tag in REQUIRED_TAGS:
        assert tag in text


def test_checkpoint_contains_exact_safety_markers():
    text = _text().lower()

    for marker in REQUIRED_SAFETY_MARKERS:
        assert marker in text


def test_checkpoint_summarizes_phase20a_through_phase20d():
    text = _text()

    for phase in ("Phase 20A", "Phase 20B", "Phase 20C", "Phase 20D"):
        assert phase in text


def test_checkpoint_recommends_manual_review_phase21():
    text = _text()

    assert "Phase 21" in text
    assert "manual-review workflow hardening" in text
    assert "still with no auto-apply and no auto-submit" in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase20e_changes_only_docs_tests_and_legacy_guards():
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    changed = set(tracked + untracked)
    allowed = {
        "docs/phase20_provider_readiness_release_checkpoint.md",
        "tests/test_phase20e_provider_readiness_release_checkpoint_default_off.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if (
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py"
            in path.read_text(encoding="utf-8")
        )
    }

    assert changed <= allowed | legacy_guards
