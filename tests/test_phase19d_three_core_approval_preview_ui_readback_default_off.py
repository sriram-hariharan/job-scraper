from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"
CSS_PATH = ROOT / "src/app/static/app_redesign.css"

PROTECTED_HASHES = {
    "src/app/api.py": "4953e19b5b9914310d10ff758fd72eb4abed0ffb568a59fa43284ac17a4dce34",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/agents/three_core_approval_preview_runtime.py": "8dfe50739f22d42df97db0ea0f2a2dac70d93abf720bbcfe62ad3df205073bbc",
    "src/agents/three_core_approval_preview_service_readback.py": "aed9fc35ee7f0c72ddb46e5db87efde799e5bb5218be252db113e7ac7ab5c71c",
}


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _snippet(start_marker: str, end_marker: str) -> str:
    source = _source()
    start = source.index(start_marker)
    end = source.index(end_marker, start)
    return source[start:end]


def _fixture_helpers() -> str:
    return _snippet(
        "function shouldRenderThreeCoreApprovalPreviewFixture",
        "\nfunction renderThreeCoreApprovalPreviewServiceReadbackSection",
    )


def _renderer() -> str:
    return _snippet(
        "function renderThreeCoreApprovalPreviewServiceReadbackSection",
        "\nfunction renderHumanReviewedInfluencePreviewSection",
    )


def test_ui_has_passive_approval_preview_readback_renderer():
    source = _source()
    snippet = _renderer()

    assert "renderThreeCoreApprovalPreviewServiceReadbackSection" in snippet
    assert "Three-Core Approval Preview Readback" in snippet
    assert "three_core_approval_preview_service_readback_result" in snippet
    assert (
        "renderThreeCoreApprovalPreviewServiceReadbackSection("
        "fixtureVisibleTracePayload)"
        in source
    )


def test_panel_renders_only_for_supplied_payload_or_fixture():
    snippet = _renderer()
    panel = _snippet(
        "function renderAgentTraceReadOnlyPanel",
        "\nfunction renderAgentTracePanel",
    )

    assert 'if (!Object.keys(result).length) return "";' in snippet
    assert "withThreeCoreApprovalPreviewServiceReadbackFixture" in panel


def test_fixture_query_gate_is_explicit_and_default_off():
    snippet = _fixture_helpers()

    assert "three_core_approval_preview_fixture" in snippet
    assert "window.location.search" in snippet
    assert "new URLSearchParams(query)" in snippet
    assert '=== "1"' in snippet
    assert "search = null" in snippet


def test_fixture_payload_is_deterministic_ready_and_safe():
    snippet = _fixture_helpers()

    for marker in (
        "buildThreeCoreApprovalPreviewServiceReadbackFixtureResult",
        '"approval_preview_service_readback_ready"',
        '"relevance_prefilter"',
        '"jd_intelligence"',
        '"final_application_scoring"',
        "read_only: true",
        "shadow_only: true",
        "advisory_only: true",
    ):
        assert marker in snippet


def test_fixture_does_not_overwrite_real_supplied_payload():
    snippet = _fixture_helpers()

    assert (
        "source.three_core_approval_preview_service_readback_result"
        in snippet
    )
    assert "return source;" in snippet
    assert (
        "three_core_approval_preview_service_readback_result:"
        in snippet
    )


def test_renderer_is_passive_and_has_no_action_controls_or_calls():
    snippet = _renderer().lower()

    for marker in (
        "<button",
        "<input",
        "<form",
        "fetch(",
        "fetchjson(",
        "/api/",
        "data-apply",
        "data-submit",
        "data-execute",
        "data-approval",
        "createapproval",
        "executeapplication",
        "submitapplication",
    ):
        assert marker not in snippet


def test_renderer_shows_required_readback_fields():
    snippet = _renderer()

    for marker in (
        "Service readback status",
        "Read only",
        "Shadow only",
        "Advisory only",
        "Ordered agents",
        "Requested capability",
        "Linked trace / readback id",
        "Next safe step",
        "Missing requirements",
        "Fail-closed reason",
        "Safety metadata",
    ):
        assert marker in snippet


def test_fixture_safety_metadata_keeps_forbidden_paths_false():
    snippet = _fixture_helpers()

    for marker in (
        "provider_call: false",
        "network_call: false",
        "did_read_database: false",
        "did_write_database: false",
        "did_mutate_scoring: false",
        "did_change_ranking: false",
        "did_mutate_queue: false",
        "did_mutate_resume: false",
        "did_create_approval: false",
        "did_create_execution_request: false",
        "did_execute_application: false",
        "did_submit_application: false",
    ):
        assert marker in snippet


def test_css_additions_are_minimal_and_scoped_to_panel():
    source = CSS_PATH.read_text(encoding="utf-8")

    assert ".three-core-approval-preview-readback {" in source
    assert ".three-core-approval-preview-readback__metrics {" in source
    assert source.count("three-core-approval-preview-readback") == 2


def test_protected_backend_hashes_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase19d_changes_only_approved_files():
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
        "docs/phase19_approval_preview_ui_readback.md",
        "tests/test_phase19d_three_core_approval_preview_ui_readback_default_off.py",
        "docs/phase19_approval_preview_ui_api_fetch.md",
        "tests/test_phase19e_three_core_approval_preview_ui_api_fetch_default_off.py",
        "docs/phase19_approval_preview_operator_decision_preview.md",
        "tests/test_phase19f_approval_preview_operator_decision_preview_default_off.py",
        "src/agents/operator_decision_capture_readback_contract.py",
        "docs/phase19_operator_decision_capture_readback_contract.md",
        "tests/test_phase19g_operator_decision_capture_readback_contract_default_off.py",
        "src/app/api.py",
        "docs/phase19_operator_decision_capture_api_readback.md",
        "tests/test_phase19h_operator_decision_capture_api_readback_default_off.py",
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
        "tests/test_phase19c_three_core_approval_preview_api_readback_default_off.py",
        "tests/test_phase19b_three_core_approval_preview_service_readback_default_off.py",
        "tests/test_phase19a_three_core_approval_preview_runtime_readonly_default_off.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
        "tests/test_three_core_shadow_readiness_wrap_default_off.py",
        "tests/test_phase18_live_readiness_approval_boundary_default_off.py",
        "tests/test_phase18_human_approval_gate_contract_default_off.py",
        "tests/test_phase18_approval_preview_readonly_default_off.py",
        "tests/test_phase18_operator_decision_capture_contract_default_off.py",
        "tests/test_phase18_live_provider_activation_plan_default_off.py",
        "tests/test_phase18_provider_runtime_adapter_contract_default_off.py",
        "tests/test_phase18_live_provider_dry_run_packet_contract_default_off.py",
        "tests/test_phase18_provider_response_validation_contract_default_off.py",
        "tests/test_phase18_provider_readback_audit_contract_default_off.py",
        "tests/test_phase18_provider_call_boundary_readiness_contract_default_off.py",
        "tests/test_phase18_mutation_boundary_readiness_contract_default_off.py",
        "tests/test_phase18_safety_wrap_release_checkpoint_default_off.py",
    }

    legacy_static_hash_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if path.name == "test_three_core_agent_shadow_sidecar_bridge_default_off.py"
        or any(
                marker in path.read_text(encoding="utf-8")
                for marker in (
                    "c0c7a0a229a0cc9a1042c84c37a1728a33707e1035f6d604b6fe6aa74cc4b5e7",
                    "cbf6e94095f4ffcd932d31f163adde1c27f115dcbaa5ae4d0939398348f1e014",
                    "029c1105e4d3ae9f023ad40418e83cc13e4dffc937406b5e7219e8934d067e35",
                    "4953e19b5b9914310d10ff758fd72eb4abed0ffb568a59fa43284ac17a4dce34",
                )
            )
    }
    assert changed <= allowed | legacy_static_hash_guards
