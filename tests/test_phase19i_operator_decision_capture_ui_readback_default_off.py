from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"

PROTECTED_HASHES = {
    "src/app/api.py": "ba752c3a7eaef620476abffb0ecb7ebf8ce023346917ff8fedb5579c9504d41f",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/agents/operator_decision_capture_readback_contract.py": "4066b415b7ac84eca8e37df5b1b71cad208001fd49c76126bd928eab39992450",
}


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _readback_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldRenderOperatorDecisionCaptureReadbackFixture"
    )
    end = source.index(
        "\nfunction renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def _fetch_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldFetchOperatorDecisionCaptureReadback"
    )
    end = source.index(
        "\nfunction getAgenticReviewApprovalRequestId",
        start,
    )
    return source[start:end]


def test_renderer_and_fixture_gate_exist():
    snippet = _readback_helpers()

    assert "renderOperatorDecisionCaptureReadbackSection" in snippet
    assert "operator_decision_capture_readback_fixture" in snippet
    assert "window.location.search" in snippet
    assert "new URLSearchParams(query)" in snippet
    assert '=== "1"' in snippet


def test_optional_api_fetch_gate_exists_and_is_default_off():
    snippet = _fetch_helpers()

    assert "operator_decision_capture_api_fetch" in snippet
    assert "window.location.search" in snippet
    assert "new URLSearchParams(query)" in snippet
    assert '=== "1"' in snippet
    assert "|| !shouldFetchOperatorDecisionCaptureReadback(search)" in snippet


def test_default_off_requires_supplied_payload_fixture_or_fetch_gate():
    helpers = _readback_helpers()
    renderer_start = helpers.index(
        "function renderOperatorDecisionCaptureReadbackSection"
    )
    renderer = helpers[renderer_start:]

    assert "source.operator_decision_capture_readback_result" in helpers
    assert (
        "|| !shouldRenderOperatorDecisionCaptureReadbackFixture(search)"
        in helpers
    )
    assert 'if (!Object.keys(result).length) return "";' in renderer
    assert (
        "withOperatorDecisionCaptureReadbackApiFetch("
        in _source()
    )


def test_panel_title_and_required_readback_fields_exist():
    snippet = _readback_helpers()

    for marker in (
        "Operator Decision Capture Readback",
        "Capture status",
        "Selected action",
        "Selected resume / variant",
        "Operator note",
        "Validation errors",
        "Read only",
        "Shadow only",
        "Advisory only",
        "Decision persisted",
        "Approval created",
        "Execution authorized",
        "Submission authorized",
        "Mutation authorized",
        "Next safe step",
        "Safety metadata summary",
    ):
        assert marker in snippet


def test_fixture_payload_is_deterministic_read_only_and_non_authorizing():
    snippet = _readback_helpers()

    for marker in (
        "buildOperatorDecisionCaptureReadbackFixtureResult",
        '"operator_decision_capture_readback_ready"',
        'selected_action: "HOLD"',
        'selected_resume: "primary_resume"',
        'selected_variant: "baseline"',
        "read_only: true",
        "shadow_only: true",
        "advisory_only: true",
        "decision_persisted: false",
        "approval_created: false",
        "execution_authorized: false",
        "submission_authorized: false",
        "mutation_authorized: false",
    ):
        assert marker in snippet


def test_fixture_never_overwrites_supplied_or_fetched_payload():
    snippet = _readback_helpers()

    assert "source.operator_decision_capture_readback_result" in snippet
    assert "return source;" in snippet


def test_api_fetch_is_gated_post_only_and_targets_phase19h_endpoint():
    snippet = _fetch_helpers()
    gate_position = snippet.index(
        "!shouldFetchOperatorDecisionCaptureReadback(search)"
    )
    fetch_position = snippet.index("await fetchJson(")

    assert gate_position < fetch_position
    assert snippet.count(
        '"/api/operator-decision-capture-readback"'
    ) == 1
    assert 'method: "POST"' in snippet
    assert 'enabled: false' in snippet


def test_api_response_reuses_renderer_and_failure_is_fail_closed():
    source = _source()
    snippet = _fetch_helpers()

    assert "operator_decision_capture_readback_result: result" in snippet
    assert (
        "renderOperatorDecisionCaptureReadbackSection("
        "operatorDecisionCaptureVisibleTracePayload)"
        in source
    )
    assert "catch (error)" in snippet
    assert '"operator_decision_capture_readback_failed_closed"' in snippet
    assert "ui_api_fetch_failed: true" in snippet
    assert "read_only: true" in snippet
    assert "mutation_authorized: false" in snippet


def test_helpers_add_no_controls_storage_or_mutation_paths():
    snippet = (_readback_helpers() + _fetch_helpers()).lower()

    for marker in (
        "<button",
        "<input",
        "<form",
        "data-apply",
        "data-submit",
        "data-execute",
        "data-approval",
        "localstorage.setitem",
        "sessionstorage.setitem",
        "createapproval",
        "recordapproval",
        "persistdecision",
        "persistaudit",
        "executeapplication",
        "submitapplication",
        "mutatequeue",
        "updateranking",
        "mutatescoring",
        "mutateresume",
    ):
        assert marker not in snippet


def test_protected_backend_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase19i_changes_only_approved_files():
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
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase19_operator_decision_capture_ui_readback.md",
        "tests/test_phase19i_operator_decision_capture_ui_readback_default_off.py",
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
        "docs/no_auto_apply_safety_policy.md",
        "docs/phase20_no_auto_apply_safety_checkpoint.md",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "docs/phase20_provider_readiness_release_checkpoint.md",
        "tests/test_phase20e_provider_readiness_release_checkpoint_default_off.py",
        "docs/manual_review_workflow_boundary.md",
        "docs/phase21_manual_review_workflow_boundary.md",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "src/agents/manual_review_readiness_contract.py",
        "docs/phase21_manual_review_readiness_contract.md",
        "tests/test_phase21b_manual_review_readiness_contract_default_off.py",
        "src/app/api.py",
        "docs/phase21_manual_review_readiness_api_readback.md",
        "tests/test_phase21c_manual_review_readiness_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "docs/phase21_manual_review_readiness_ui_readback.md",
        "tests/test_phase21d_manual_review_readiness_ui_readback_default_off.py",
        "docs/phase21_manual_review_workflow_release_checkpoint.md",
        "tests/test_phase21e_manual_review_workflow_release_checkpoint_default_off.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "agentic_review.js",
                "ba752c3a7eaef620476abffb0ecb7ebf8ce023346917ff8fedb5579c9504d41f",
            )
        )
    }

    assert changed <= allowed | legacy_guards
