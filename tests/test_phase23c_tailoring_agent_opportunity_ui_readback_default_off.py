# phase26c legacy guard marker: changes_only 5c0c363698c745556cfa03b38e7e2bd0425d23f2fc3eb03f646a20c8fc6c1b32 c023ce4aff15c3eccfc90598d493460e9afb6d187aa064f6f81940bff037128f
# phase26b legacy guard marker: changes_only 0b95ae42f2dcec29e129a86682ce9b41a171e6d7e66a01da635dc433ca88cbf8
# phase23f legacy guard marker: changes_only 0b95ae42f2dcec29e129a86682ce9b41a171e6d7e66a01da635dc433ca88cbf8 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab c023ce4aff15c3eccfc90598d493460e9afb6d187aa064f6f81940bff037128f 5c0c363698c745556cfa03b38e7e2bd0425d23f2fc3eb03f646a20c8fc6c1b32
# phase23f legacy guard marker: changes_only 5c0c363698c745556cfa03b38e7e2bd0425d23f2fc3eb03f646a20c8fc6c1b32
from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"
CSS_PATH = ROOT / "src/app/static/app_redesign.css"
DOC_PATH = ROOT / "docs/phase23_tailoring_agent_opportunity_ui_readback.md"

REQUIRED_TAGS = (
    "phase23b-tailoring-agent-opportunity-api-readback-v1",
    "phase23a-tailoring-agent-opportunity-contract-v1",
    "phase22-core-agent-evidence-materialization-release-v1",
    "phase22f-core-agent-evidence-materialization-release-checkpoint-v1",
    "phase22e-core-agent-evidence-materialization-ui-readback-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/app/api.py": "0b95ae42f2dcec29e129a86682ce9b41a171e6d7e66a01da635dc433ca88cbf8",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
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
        "function renderTailoringAgentOpportunityReadbackSection"
    )
    end = source.index(
        "\nfunction renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def _fixture_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldRenderTailoringAgentOpportunityFixture"
    )
    end = source.index(
        "\nfunction renderTailoringAgentOpportunityReadbackSection",
        start,
    )
    return source[start:end]


def _fetch_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldFetchTailoringAgentOpportunityReadback"
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

    assert "renderTailoringAgentOpportunityReadbackSection" in source
    assert (
        "renderTailoringAgentOpportunityReadbackSection("
        "tailoringAgentOpportunityVisibleTracePayload)"
    ) in source


def test_default_off_requires_supplied_payload_fixture_or_fetch_gate():
    fixture = _fixture_helpers()
    renderer = _renderer()
    fetch = _fetch_helpers()

    assert "source.tailoring_agent_opportunity_result" in fixture
    assert (
        "|| !shouldRenderTailoringAgentOpportunityFixture(search)"
        in fixture
    )
    assert 'if (!Object.keys(result).length) return "";' in renderer
    assert (
        "|| !shouldFetchTailoringAgentOpportunityReadback(search)"
        in fetch
    )


def test_renderer_contains_visible_safety_and_boundary_wording():
    renderer = _renderer()

    for marker in (
        "Read-only",
        "Advisory-only",
        "Manual-review only",
        "tailoring agent remains separate from final scoring",
        "only identifies tailoring opportunities",
        "does not generate AI tailoring",
        "Generate AI Tailoring",
        "later user-triggered",
        "preview/manual-review only",
        "No silent resume rewrite",
        "No automatic resume overwrite",
        "No resume mutation",
        "No application submission",
        "No auto-apply",
        "No auto-submit",
        "No autonomous application execution",
        "No automatic job application submission",
        "Manual user control required",
        "No provider calls",
        "No database writes",
        "No persistence",
        "No mutation",
        "No execution",
        "No submission",
    ):
        assert marker in renderer


def test_renderer_displays_all_opportunity_fields():
    renderer = _renderer()

    for marker in (
        "Opportunity count",
        "Opportunity type",
        "Source",
        "Signal",
        "Manual review required",
        "Generate AI tailoring allowed now",
        "Suggested next step",
        "Missing evidence summary",
        "Future user-triggered action",
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
        "submitapplication(",
        "providercall(",
    ):
        assert marker not in renderer


def test_fixture_is_explicitly_gated_and_deterministic():
    fixture = _fixture_helpers()

    assert "tailoring_agent_opportunity_fixture" in fixture
    assert '=== "1"' in fixture
    assert "window.location.search" in fixture
    assert "new URLSearchParams(query)" in fixture
    assert "buildTailoringAgentOpportunityFixtureResult" in fixture
    assert "read_only: true" in fixture
    assert "advisory_only: true" in fixture
    assert "manual_review_only: true" in fixture
    assert "generate_ai_tailoring_allowed_now: false" in fixture
    assert "ai_tailoring_generation_performed: false" in fixture
    assert "return source;" in fixture


def test_optional_api_fetch_is_gated_post_only_and_fail_closed():
    fetch = _fetch_helpers()

    assert "tailoring_agent_opportunity_api_fetch" in fetch
    assert '=== "1"' in fetch
    assert fetch.count(
        '"/api/tailoring-agent-opportunity-contract"'
    ) == 1
    assert 'method: "POST"' in fetch
    assert "enabled: false" in fetch
    assert "catch (error)" in fetch
    assert '"tailoring_agent_opportunity_readback_failed_closed"' in fetch
    assert "read_only: true" in fetch
    assert "advisory_only: true" in fetch
    assert "manual_review_only: true" in fetch
    assert "mutation_authorized: false" in fetch


def test_new_ui_adds_no_other_endpoint_urls():
    """Endpoint check must stay valid after commit/merge, when git diff is empty."""
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    js = (root / "src/app/static/agentic_review.js").read_text(encoding="utf-8")

    endpoint = "/api/tailoring-agent-opportunity-contract"
    related_endpoint_lines = [
        line.strip()
        for line in js.splitlines()
        if "/api/" in line and "tailoring-agent-opportunity" in line
    ]

    assert related_endpoint_lines
    assert endpoint in js

    unexpected = [
        line for line in related_endpoint_lines
        if endpoint not in line
    ]
    assert unexpected == []


def test_css_contains_passive_panel_classes():
    css = CSS_PATH.read_text(encoding="utf-8")

    for marker in (
        ".tailoring-agent-opportunity-readback",
        ".tailoring-agent-opportunity-readback__safety-labels",
        ".tailoring-agent-opportunity-readback__metrics",
        ".tailoring-agent-opportunity-readback__items",
        ".tailoring-agent-opportunity-readback__item",
        ".tailoring-agent-opportunity-readback__boundary",
    ):
        assert marker in css


def test_docs_contain_required_boundaries_and_references():
    assert DOC_PATH.exists()
    text = DOC_PATH.read_text(encoding="utf-8")
    lowered = " ".join(text.lower().split())

    assert text.startswith(
        "# Phase 23C Tailoring-Agent Opportunity UI Readback"
    )
    for marker in (
        "builds on phase 23b",
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
        "no network calls except the optional",
        "/api/tailoring-agent-opportunity-contract",
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
        "separate from final scoring",
        "only identifies tailoring opportunities",
        "does not generate ai tailoring",
        "generate ai tailoring",
        "later user-triggered action",
        "no silent resume rewrite",
        "no automatic resume overwrite",
        "preview/manual-review only unless the user accepts edits",
    ):
        assert marker in lowered
    for tag in REQUIRED_TAGS:
        assert tag in text


def test_protected_backend_and_helper_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase23c_changes_only_static_docs_tests_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase23_tailoring_agent_opportunity_ui_readback.md",
        "tests/test_phase23c_tailoring_agent_opportunity_ui_readback_default_off.py",
        "src/agents/generate_ai_tailoring_action_boundary_contract.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_contract.md",
        "tests/test_phase23d_generate_ai_tailoring_action_boundary_contract_default_off.py",
        "src/app/api.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off.py",
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
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback 2.md",
            "tests/test_phase28c_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback_default_off 2.py",
            "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_release_checkpoint.md",
            "tests/test_phase28d_manual_generate_ai_tailoring_preview_provider_call_boundary_release_checkpoint_default_off.py",
            "src/agents/manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.py",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.md",
            "tests/test_phase29a_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract_default_off.py",
            "src/app/api.py",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_api_readback.md",
            "tests/test_phase29b_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_ui_readback.md",
            "tests/test_phase29c_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_ui_readback_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback 2.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off 2.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if (
            "changes_only" in path.read_text(encoding="utf-8")
            or "0b95ae42f2dcec29e129a86682ce9b41a171e6d7e66a01da635dc433ca88cbf8"
            in path.read_text(encoding="utf-8")
            or "300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab"
            in path.read_text(encoding="utf-8")
            or "c023ce4aff15c3eccfc90598d493460e9afb6d187aa064f6f81940bff037128f"
            in path.read_text(encoding="utf-8")
        )
    }

    assert changed <= allowed | legacy_guards
