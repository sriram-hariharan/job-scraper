from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC_PATH = ROOT / "docs/phase19_readonly_approval_workflow_release_checkpoint.md"

PHASE19_TAGS = (
    "phase19a-approval-preview-runtime-readonly-v1",
    "phase19b-approval-preview-service-readback-v1",
    "phase19c-approval-preview-api-readback-v1",
    "phase19d-approval-preview-ui-readback-v1",
    "phase19e-approval-preview-ui-api-fetch-v1",
    "phase19f-approval-preview-operator-decision-preview-v1",
    "phase19g-operator-decision-capture-readback-contract-v1",
    "phase19h-operator-decision-capture-api-readback-v1",
    "phase19i-operator-decision-capture-ui-readback-v1",
)

PROTECTED_HASHES = {
    "src/app/api.py": "4953e19b5b9914310d10ff758fd72eb4abed0ffb568a59fa43284ac17a4dce34",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "029c1105e4d3ae9f023ad40418e83cc13e4dffc937406b5e7219e8934d067e35",
    "src/app/static/app_redesign.css": "cbf6e94095f4ffcd932d31f163adde1c27f115dcbaa5ae4d0939398348f1e014",
    "src/agents/operator_decision_capture_readback_contract.py": "4066b415b7ac84eca8e37df5b1b71cad208001fd49c76126bd928eab39992450",
    "src/agents/three_core_approval_preview_runtime.py": "8dfe50739f22d42df97db0ea0f2a2dac70d93abf720bbcfe62ad3df205073bbc",
    "src/agents/three_core_approval_preview_service_readback.py": "aed9fc35ee7f0c72ddb46e5db87efde799e5bb5218be252db113e7ac7ab5c71c",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
}


def _doc() -> str:
    return DOC_PATH.read_text(encoding="utf-8")


def test_checkpoint_doc_exists():
    assert DOC_PATH.exists()
    assert _doc().startswith(
        "# Phase 19J Read-Only Approval Workflow Release Checkpoint"
    )


def test_checkpoint_references_all_phase19_release_tags():
    text = _doc()

    for tag in PHASE19_TAGS:
        assert tag in text


def test_checkpoint_states_default_off_read_only_safety_posture():
    text = _doc().lower()

    for marker in (
        "default-off",
        "read-only",
        "shadow-only",
        "advisory-only",
        "not live automation",
    ):
        assert marker in text


def test_checkpoint_states_no_provider_storage_persistence_or_actions():
    text = _doc().lower()

    for marker in (
        "no provider calls",
        "no database writes",
        "no approval creation",
        "no decision persistence",
        "no scoring mutation",
        "no ranking mutation",
        "no queue mutation",
        "no resume mutation",
        "no execution",
        "no submission",
    ):
        assert marker in text


def test_checkpoint_defers_live_mutation_and_recommends_phase20a():
    text = _doc()

    assert "Live mutation is deferred to later phases" in text
    assert "separate approval and safety gates" in text
    assert "Phase 20A" in text
    assert "controlled provider-call readiness experiment" in text
    assert "remain default-off" in text
    assert "authorize no mutation" in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase19j_changes_only_docs_tests_and_legacy_guards():
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
        "docs/phase19_readonly_approval_workflow_release_checkpoint.md",
        "tests/test_phase19j_readonly_approval_workflow_release_checkpoint_default_off.py",
        "src/agents/provider_call_readiness_experiment.py",
        "docs/phase20_provider_call_readiness_experiment.md",
        "tests/test_phase20a_provider_call_readiness_experiment_default_off.py",
        "src/app/api.py",
        "docs/phase20_provider_call_readiness_api_readback.md",
        "tests/test_phase20b_provider_call_readiness_api_readback_default_off.py",
            "docs/phase20_provider_call_readiness_ui_readback.md",
            "tests/test_phase20c_provider_call_readiness_ui_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
        }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "docs/phase19_operator_decision_capture_ui_readback.md",
                "4953e19b5b9914310d10ff758fd72eb4abed0ffb568a59fa43284ac17a4dce34",
                "029c1105e4d3ae9f023ad40418e83cc13e4dffc937406b5e7219e8934d067e35",
            )
        )
    }

    assert changed <= allowed | legacy_guards
