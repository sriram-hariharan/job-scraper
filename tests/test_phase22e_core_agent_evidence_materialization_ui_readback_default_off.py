from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"
DOC_PATH = (
    ROOT / "docs/phase22_core_agent_evidence_materialization_ui_readback.md"
)

PROTECTED_HASHES = {
    "src/app/api.py": "bb4755cd3d74c72e7ed0af24de9d617c0ff568b61639b6d61e59c057348f424a",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/agents/core_agent_evidence_materialization_preview.py": "d1b0862cf0355192a45a7b45fbeaa622d72e16b7c5234c71bea75aea90db9110",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
}

REQUIRED_TAGS = (
    "phase22d-core-agent-evidence-materialization-api-readback-v1",
    "phase22c-core-agent-evidence-materialization-preview-v1",
    "phase22b-core-agent-automation-mutation-inventory-v1",
    "phase22a-manual-review-ux-hardening-v1",
    "phase21-manual-review-workflow-release-v1",
    "phase20-provider-readiness-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
    "phase19-readonly-approval-workflow-release-v1",
    "phase18-safety-wrap-release-v1",
    "phase17-three-core-shadow-readiness-release-v1",
)


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _renderer() -> str:
    source = _source()
    start = source.index(
        "function renderCoreAgentEvidenceMaterializationReadbackSection"
    )
    end = source.index(
        "\nfunction renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def _fixture_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldRenderCoreAgentEvidenceMaterializationFixture"
    )
    end = source.index(
        "\nfunction renderCoreAgentEvidenceMaterializationReadbackSection",
        start,
    )
    return source[start:end]


def _fetch_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldFetchCoreAgentEvidenceMaterializationReadback"
    )
    end = source.index(
        "\nfunction getAgenticReviewApprovalRequestId",
        start,
    )
    return source[start:end]


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


def test_renderer_exists_and_is_integrated():
    source = _source()

    assert "renderCoreAgentEvidenceMaterializationReadbackSection" in source
    assert (
        "renderCoreAgentEvidenceMaterializationReadbackSection("
        "coreAgentEvidenceMaterializationVisibleTracePayload)"
    ) in source


def test_renderer_contains_core_agent_sequence_and_evidence_fields():
    renderer = _renderer()

    for marker in (
        "Core-agent sequence",
        "relevance_prefilter",
        "jd_intelligence",
        "final_application_scoring",
        "Relevance evidence supplied",
        "JD intelligence evidence supplied",
        "Final scoring evidence supplied",
        "Tailoring opportunity evidence supplied",
        "Manual review context supplied",
        "Suggested manual review status",
        "Why the job is worth reviewing",
        "Missing evidence fields",
        "Tailoring opportunity summary",
        "Future user-triggered action",
    ):
        assert marker in renderer or marker in _fixture_helpers()


def test_renderer_contains_visible_safety_and_tailoring_boundary_wording():
    renderer = _renderer()

    for marker in (
        "Read-only",
        "Advisory-only",
        "Manual-review only",
        "no auto-apply",
        "no auto-submit",
        "no autonomous application execution",
        "no automatic job application submission",
        "Manual user control required",
        "tailoring agent remains separate from final scoring",
        "Generate AI Tailoring",
        "preview/manual-review only",
        "unless the user accepts edits",
    ):
        assert marker in renderer


def test_renderer_contains_no_controls_storage_writes_or_actions():
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
        "createapproval(",
        "persistdecision(",
        "persistaudit(",
        "executeapplication(",
        "submitapplication(",
        "generateaitailoring(",
        "providercall(",
    ):
        assert marker not in renderer


def test_fixture_is_explicitly_gated_and_does_not_overwrite_payload():
    snippet = _fixture_helpers()

    assert "core_agent_evidence_materialization_fixture" in snippet
    assert '=== "1"' in snippet
    assert "window.location.search" in snippet
    assert "new URLSearchParams(query)" in snippet
    assert "source.core_agent_evidence_materialization_result" in snippet
    assert "return source;" in snippet


def test_optional_api_fetch_is_explicitly_gated_post_only_and_fail_closed():
    snippet = _fetch_helpers()

    assert "core_agent_evidence_materialization_api_fetch" in snippet
    assert '=== "1"' in snippet
    assert (
        "|| !shouldFetchCoreAgentEvidenceMaterializationReadback(search)"
        in snippet
    )
    assert (
        snippet.count(
            '"/api/core-agent-evidence-materialization-preview"'
        )
        == 1
    )
    assert 'method: "POST"' in snippet
    assert "enabled: false" in snippet
    assert "catch (error)" in snippet
    assert '"core_agent_evidence_preview_failed_closed"' in snippet
    assert "read_only: true" in snippet
    assert "advisory_only: true" in snippet
    assert "manual_review_only: true" in snippet
    assert "mutation_authorized: false" in snippet


def test_new_ui_adds_no_other_endpoint_urls():
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


def test_docs_contain_required_markers_and_references():
    assert DOC_PATH.exists()
    text = " ".join(DOC_PATH.read_text(encoding="utf-8").lower().split())

    for marker in (
        "phase 22e core-agent evidence materialization ui readback",
        "phase 22d",
        "ui readback surface only",
        "default-off",
        "read-only",
        "advisory-only",
        "manual-review only",
        "no backend behavior changes",
        "no api changes",
        "no services changes",
        "no agent changes",
        "no pipeline changes",
        "no matching changes",
        "no tailoring runtime changes",
        "no provider calls",
        "no network calls except the optional explicitly gated post",
        "/api/core-agent-evidence-materialization-preview",
        "no database writes",
        "no persistence",
        "no mutation",
        "no execution",
        "no submission",
        "no auto-apply",
        "no auto-submit",
        "no autonomous application execution",
        "no automatic job application submission",
        "manual user control remains required",
        "generate ai tailoring",
        "later user-triggered action",
        "preview/manual-review only unless the user accepts edits",
    ):
        assert marker in text
    raw_text = DOC_PATH.read_text(encoding="utf-8")
    for tag in REQUIRED_TAGS:
        assert tag in raw_text


def test_protected_backend_and_helper_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase22e_changes_only_static_docs_tests_and_legacy_guards():
    changed = _changed_files() - {
        "docs/phase22_core_agent_evidence_materialization_api_readback 2.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off 2.py",
    }
    allowed = {
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase22_core_agent_evidence_materialization_ui_readback.md",
        "tests/test_phase22e_core_agent_evidence_materialization_ui_readback_default_off.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "changes_only",
                "f7cdf115e412f34094e80e71b18e86f94365715c6f5010faa8e2ba7fe41daeff",
                "962232082cf71e5c85150ff52de5466b11a791567692a45e768dae6d5d11c6ba",
            )
        )
    }

    assert changed <= allowed | legacy_guards
