from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"

PROTECTED_HASHES = {
    "src/app/api.py": "8ab44f7e97113f6d28e9a8f7d032affef2e1f8f891286986d9e95d581ff97fbf",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/agents/three_core_approval_preview_runtime.py": "8dfe50739f22d42df97db0ea0f2a2dac70d93abf720bbcfe62ad3df205073bbc",
    "src/agents/three_core_approval_preview_service_readback.py": "aed9fc35ee7f0c72ddb46e5db87efde799e5bb5218be252db113e7ac7ab5c71c",
}


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _fetch_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldFetchThreeCoreApprovalPreviewServiceReadback"
    )
    end = source.index(
        "\nfunction getAgenticReviewApprovalRequestId",
        start,
    )
    return source[start:end]


def test_api_fetch_gate_is_explicit_and_default_off():
    snippet = _fetch_helpers()

    assert "three_core_approval_preview_api_fetch" in snippet
    assert "window.location.search" in snippet
    assert "new URLSearchParams(query)" in snippet
    assert '=== "1"' in snippet
    assert (
        "|| !shouldFetchThreeCoreApprovalPreviewServiceReadback(search)"
        in snippet
    )


def test_fetch_occurs_only_after_gate_and_targets_phase19c_endpoint():
    snippet = _fetch_helpers()
    gate_position = snippet.index(
        "!shouldFetchThreeCoreApprovalPreviewServiceReadback(search)"
    )
    fetch_position = snippet.index("await fetchJson(")

    assert gate_position < fetch_position
    assert snippet.count(
        '"/api/three-core-approval-preview-service-readback"'
    ) == 1
    assert 'method: "POST"' in snippet


def test_default_request_is_deterministic_and_disabled():
    snippet = _fetch_helpers()

    assert "buildThreeCoreApprovalPreviewServiceReadbackRequest" in snippet
    assert "enabled: false" in snippet
    for key in (
        "approval_preview_runtime_payload: null",
        "shadow_runtime_readback_payload: null",
        "shadow_sidecar_hook_payload: null",
        "readback_context: null",
        "readback_config: null",
    ):
        assert key in snippet


def test_caller_supplied_request_payload_is_used_when_present():
    snippet = _fetch_helpers()

    assert (
        "three_core_approval_preview_service_readback_request_payload"
        in snippet
    )
    assert "if (Object.keys(supplied).length) return supplied;" in snippet


def test_api_result_reuses_existing_phase19d_renderer():
    source = _source()

    assert (
        "three_core_approval_preview_service_readback_result: result"
        in source
    )
    assert (
        "renderThreeCoreApprovalPreviewServiceReadbackSection("
        "fixtureVisibleTracePayload)"
        in source
    )
    assert (
        "withThreeCoreApprovalPreviewServiceReadbackApiFetch(tracePayload)"
        in source
    )


def test_fixture_does_not_overwrite_real_or_api_payload():
    source = _source()
    start = source.index(
        "function withThreeCoreApprovalPreviewServiceReadbackFixture"
    )
    end = source.index(
        "\nfunction shouldFetchThreeCoreApprovalPreviewServiceReadback",
        start,
    )
    snippet = source[start:end]

    assert (
        "source.three_core_approval_preview_service_readback_result"
        in snippet
    )
    assert "return source;" in snippet


def test_failure_is_non_blocking_read_only_and_fail_closed():
    snippet = _fetch_helpers()

    assert "catch (error)" in snippet
    assert '"approval_preview_service_readback_failed_closed"' in snippet
    assert "ui_api_fetch_failed: true" in snippet
    assert "read_only: true" in snippet
    assert "shadow_only: true" in snippet
    assert "advisory_only: true" in snippet


def test_fetch_helpers_add_no_controls_storage_or_mutation_paths():
    snippet = _fetch_helpers().lower()

    for marker in (
        "<button",
        "<input",
        "<form",
        "localstorage",
        "sessionstorage",
        "data-apply",
        "data-submit",
        "data-execute",
        "data-approval",
        "createapproval",
        "executeapplication",
        "submitapplication",
        "mutatequeue",
        "updateranking",
        "mutatescoring",
        "mutateresume",
    ):
        assert marker not in snippet


def test_backend_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase19e_changes_only_approved_files():
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
        "docs/phase19_approval_preview_ui_api_fetch.md",
        "tests/test_phase19e_three_core_approval_preview_ui_api_fetch_default_off.py",
        "docs/phase19_approval_preview_operator_decision_preview.md",
        "tests/test_phase19f_approval_preview_operator_decision_preview_default_off.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if "agentic_review.js" in path.read_text(encoding="utf-8")
    }

    assert changed <= allowed | legacy_guards
