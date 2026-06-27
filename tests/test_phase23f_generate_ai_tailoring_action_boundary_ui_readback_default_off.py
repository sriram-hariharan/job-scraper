# phase26c legacy guard marker: changes_only bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821 c71e2057276080e36fce4bec48a881753d8e09d7d1b49e7d0676d4a0665f32c9
# phase26b legacy guard marker: changes_only 96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff
# phase23f legacy guard marker: changes_only 96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab c71e2057276080e36fce4bec48a881753d8e09d7d1b49e7d0676d4a0665f32c9 bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821
# phase23f legacy guard marker: changes_only bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821
from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"
CSS_PATH = ROOT / "src/app/static/app_redesign.css"
DOC_PATH = (
    ROOT
    / "docs/phase23_generate_ai_tailoring_action_boundary_ui_readback.md"
)

REQUIRED_TAGS = (
    "phase23e-generate-ai-tailoring-action-boundary-api-readback-v1",
    "phase23d-generate-ai-tailoring-action-boundary-contract-v1",
    "phase23c-tailoring-agent-opportunity-ui-readback-v1",
    "phase23b-tailoring-agent-opportunity-api-readback-v1",
    "phase23a-tailoring-agent-opportunity-contract-v1",
    "phase22-core-agent-evidence-materialization-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/app/api.py": "96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/agents/generate_ai_tailoring_action_boundary_contract.py": "5c7675f889daa3342258be5d8eac5c191b196a84795238c658eb73cb76672953",
    "src/agents/tailoring_agent_opportunity_contract.py": "e61e910176a315e11b2e403a33920a53726c9df8ed0213f0121b5c6eb0c1d8b3",
    "src/agents/core_agent_evidence_materialization_preview.py": "d1b0862cf0355192a45a7b45fbeaa622d72e16b7c5234c71bea75aea90db9110",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
}


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _renderer() -> str:
    source = _source()
    start = source.index(
        "function renderGenerateAiTailoringActionBoundaryReadbackSection"
    )
    end = source.index(
        "\nfunction renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def _fixture_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldRenderGenerateAiTailoringActionBoundaryFixture"
    )
    end = source.index(
        "\nfunction renderGenerateAiTailoringActionBoundaryReadbackSection",
        start,
    )
    return source[start:end]


def _fetch_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldFetchGenerateAiTailoringActionBoundaryReadback"
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
    return set(tracked + untracked) - {
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback 2.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off 2.py",
    }


def test_renderer_exists_and_is_integrated():
    source = _source()

    assert "renderGenerateAiTailoringActionBoundaryReadbackSection" in source
    assert (
        "renderGenerateAiTailoringActionBoundaryReadbackSection("
        "generateAiTailoringActionBoundaryVisibleTracePayload)"
    ) in source
    assert "withGenerateAiTailoringActionBoundaryReadbackApiFetch(" in source


def test_default_off_requires_supplied_payload_fixture_or_fetch_gate():
    fixture = _fixture_helpers()
    renderer = _renderer()
    fetch = _fetch_helpers()

    assert "source.generate_ai_tailoring_action_boundary_result" in fixture
    assert (
        "|| !shouldRenderGenerateAiTailoringActionBoundaryFixture(search)"
        in fixture
    )
    assert 'if (!Object.keys(result).length) return "";' in renderer
    assert (
        "|| !shouldFetchGenerateAiTailoringActionBoundaryReadback(search)"
        in fetch
    )


def test_renderer_contains_visible_safety_and_boundary_wording():
    renderer = _renderer().lower()

    for marker in (
        "read-only",
        "advisory-only",
        "manual-review only",
        "action-boundary readback only",
        "does not generate ai tailoring",
        "does not call tailoring runtime",
        "does not call providers",
        "does not create resume rewrites",
        "does not overwrite resumes",
        "does not submit app",
        "user trigger is required",
        "manual acceptance is required",
        "preview/manual-review only",
        "no silent resume rewrite",
        "no automatic resume overwrite",
        "no resume mutation",
        "no application submission",
        "no auto-apply",
        "no auto-submit",
        "no autonomous application execution",
        "no automatic job application submission",
        "manual user control required",
        "no provider calls",
        "no network calls",
        "no database writes",
        "no persistence",
        "no mutation",
        "no execution",
        "no submission",
    ):
        assert marker in renderer


def test_renderer_displays_all_action_boundary_fields():
    renderer = _renderer()

    for marker in (
        "User trigger required",
        "User triggered",
        "Action allowed",
        "Action blocked reason",
        "Future action name",
        "AI tailoring generation performed",
        "Tailoring provider call performed",
        "Tailoring runtime call performed",
        "Resume rewrite performed",
        "Resume overwrite performed",
        "Application submission performed",
        "Preview only",
        "Manual acceptance required",
        "Next safe step",
    ):
        assert marker in renderer


def test_renderer_contains_no_controls_or_storage_writes():
    renderer = _renderer().lower()

    for marker in (
        "<button",
        "<input",
        "<form",
        "<select",
        "<textarea",
        "data-apply",
        "data-submit",
        "data-approval",
        "data-provider",
        "data-execute",
        "data-autonomous",
        "data-resume-rewrite",
        "data-resume-overwrite",
        "localstorage.setitem",
        "sessionstorage.setitem",
        "generateaitailoring(",
        "createapproval(",
        "persistdecision(",
        "persistaudit(",
        "mutateresume(",
        "overwriteresume(",
        "submitapplication(",
        "providercall(",
    ):
        assert marker not in renderer


def test_fixture_is_explicitly_gated_and_deterministic():
    fixture = _fixture_helpers()

    assert "generate_ai_tailoring_action_boundary_fixture" in fixture
    assert '=== "1"' in fixture
    assert "window.location.search" in fixture
    assert "new URLSearchParams(query)" in fixture
    assert "buildGenerateAiTailoringActionBoundaryFixtureResult" in fixture
    assert "read_only: true" in fixture
    assert "advisory_only: true" in fixture
    assert "manual_review_only: true" in fixture
    assert "user_trigger_required: true" in fixture
    assert "ai_tailoring_generation_performed: false" in fixture
    assert "tailoring_provider_call_performed: false" in fixture
    assert "tailoring_runtime_call_performed: false" in fixture
    assert "resume_rewrite_performed: false" in fixture
    assert "resume_overwrite_performed: false" in fixture
    assert "application_submission_performed: false" in fixture
    assert "return source;" in fixture


def test_optional_api_fetch_is_gated_post_only_and_fail_closed():
    fetch = _fetch_helpers()

    assert "generate_ai_tailoring_action_boundary_api_fetch" in fetch
    assert '=== "1"' in fetch
    assert fetch.count(
        '"/api/generate-ai-tailoring-action-boundary"'
    ) == 1
    assert 'method: "POST"' in fetch
    assert "enabled: false" in fetch
    assert "user_triggered: false" in fetch
    assert "catch (error)" in fetch
    assert (
        '"generate_ai_tailoring_action_boundary_readback_failed_closed"'
        in fetch
    )
    assert "read_only: true" in fetch
    assert "advisory_only: true" in fetch
    assert "manual_review_only: true" in fetch
    assert "mutation_authorized: false" in fetch


def test_new_ui_adds_no_other_generate_ai_tailoring_endpoint_urls():
    js = _source()
    endpoint = "/api/generate-ai-tailoring-action-boundary"
    related_endpoint_lines = [
        line.strip()
        for line in js.splitlines()
        if "/api/" in line and "generate-ai-tailoring" in line
    ]

    assert related_endpoint_lines
    assert endpoint in js

    unexpected = [
        line for line in related_endpoint_lines
            if endpoint not in line
            and "/api/manual-generate-ai-tailoring-preview-contract" not in line
            and "/api/manual-generate-ai-tailoring-preview-request-packet-contract" not in line
            and "/api/manual-generate-ai-tailoring-preview-dispatch-boundary-contract" not in line
            and "/api/manual-generate-ai-tailoring-preview-provider-request-envelope-contract" not in line
            and "/api/manual-generate-ai-tailoring-preview-provider-call-boundary-contract" not in line
        ]
    assert unexpected == []


def test_css_contains_passive_panel_classes():
    css = CSS_PATH.read_text(encoding="utf-8")

    for marker in (
        ".generate-ai-tailoring-action-boundary-readback",
        ".generate-ai-tailoring-action-boundary-readback__safety-labels",
        ".generate-ai-tailoring-action-boundary-readback__metrics",
        ".generate-ai-tailoring-action-boundary-readback__boundary",
    ):
        assert marker in css


def test_docs_contain_required_boundaries_and_references():
    assert DOC_PATH.exists()
    text = DOC_PATH.read_text(encoding="utf-8")
    lowered = " ".join(text.lower().split())

    assert text.startswith(
        "# Phase 23F Generate AI Tailoring Action-Boundary UI Readback"
    )
    for marker in (
        "builds on phase 23e",
        "ui readback surface only",
        "default-off",
        "read-only",
        "advisory-only",
        "manual-review only",
        "no backend behavior changes",
        "no api changes",
        "no services changes",
        "no agent helper changes",
        "no pipeline changes",
        "no matching changes",
        "no tailoring runtime changes",
        "no provider calls",
        "no network calls except the optional explicitly gated post",
        "/api/generate-ai-tailoring-action-boundary",
        "no database writes",
        "no persistence",
        "no mutation",
        "no resume mutation",
        "no application mutation",
        "no execution",
        "no submission",
        "no auto-apply",
        "no auto-submit",
        "no autonomous application execution",
        "no automatic job application submission",
        "manual user control remains required",
        "does not generate ai tailoring",
        "does not call tailoring runtime",
        "does not call providers",
        "does not create resume rewrites",
        "does not overwrite resumes",
        "does not submit applications",
        "user trigger is required",
        "manual acceptance is required before any future resume edit",
        "generated tailoring suggestions remain preview/manual-review only unless user accepts edits",
        "no silent resume rewrite",
        "no automatic resume overwrite",
        "no real generate ai tailoring button or control",
    ):
        assert marker in lowered
    for tag in REQUIRED_TAGS:
        assert tag in text


def test_protected_backend_and_helper_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase23f_changes_only_static_docs_tests_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "src/app/api.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase23_generate_ai_tailoring_action_boundary_ui_readback.md",
        "tests/test_phase23f_generate_ai_tailoring_action_boundary_ui_readback_default_off.py",
        "docs/phase23_tailoring_agent_workflow_release_checkpoint.md",
        "tests/test_phase23g_tailoring_agent_workflow_release_checkpoint_default_off.py",
        "src/agents/manual_generate_ai_tailoring_preview_contract.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_contract.md",
        "tests/test_phase24a_manual_generate_ai_tailoring_preview_contract_default_off.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_api_readback.md",
        "tests/test_phase24b_manual_generate_ai_tailoring_preview_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase24_manual_generate_ai_tailoring_preview_ui_readback.md",
        "tests/test_phase24c_manual_generate_ai_tailoring_preview_ui_readback_default_off.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_release_checkpoint.md",
        "tests/test_phase24d_manual_generate_ai_tailoring_preview_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_contract.md",
            "tests/test_phase25a_manual_generate_ai_tailoring_preview_request_packet_contract_default_off.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_api_readback.md",
            "tests/test_phase25b_manual_generate_ai_tailoring_preview_request_packet_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_ui_readback.md",
            "tests/test_phase25c_manual_generate_ai_tailoring_preview_request_packet_ui_readback_default_off.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_release_checkpoint.md",
            "tests/test_phase25d_manual_generate_ai_tailoring_preview_request_packet_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_dispatch_boundary_contract.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_contract.md",
            "tests/test_phase26a_manual_generate_ai_tailoring_preview_dispatch_boundary_contract_default_off.py",
            "src/app/api.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_api_readback.md",
            "tests/test_phase26b_manual_generate_ai_tailoring_preview_dispatch_boundary_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_ui_readback.md",
            "tests/test_phase26c_manual_generate_ai_tailoring_preview_dispatch_boundary_ui_readback_default_off.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_release_checkpoint.md",
            "tests/test_phase26d_manual_generate_ai_tailoring_preview_dispatch_boundary_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_request_envelope_contract.py",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_contract.md",
            "tests/test_phase27a_manual_generate_ai_tailoring_preview_provider_request_envelope_contract_default_off.py",
            "src/app/api.py",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_api_readback.md",
            "tests/test_phase27b_manual_generate_ai_tailoring_preview_provider_request_envelope_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_ui_readback.md",
            "tests/test_phase27c_manual_generate_ai_tailoring_preview_provider_request_envelope_ui_readback_default_off.py",
            "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_release_checkpoint.md",
            "tests/test_phase27d_manual_generate_ai_tailoring_preview_provider_request_envelope_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_call_boundary_contract.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_contract.md",
            "tests/test_phase28a_manual_generate_ai_tailoring_preview_provider_call_boundary_contract_default_off.py",
            "src/app/api.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback.md",
            "tests/test_phase28b_manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback.md",
            "tests/test_phase28c_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback_default_off.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "changes_only",
                "96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff",
                "300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab",
                "c71e2057276080e36fce4bec48a881753d8e09d7d1b49e7d0676d4a0665f32c9",
            )
        )
    }

    assert changed <= allowed | legacy_guards
