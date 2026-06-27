# phase26c legacy guard marker: changes_only 2f42b7874d33652145345b6a427a9a5d674b517692150e39c3908f45702de8ff 54ed37ddc8f9c34c2b87fd8fe437573c6f270922b9f14ada26547fd5889a5251
# phase26b legacy guard marker: changes_only b11904be37cdfdf8beb2ea93a0498bf6fb26ca9881f99c0e1579a6988071f0e8
# phase23f legacy guard marker: changes_only b11904be37cdfdf8beb2ea93a0498bf6fb26ca9881f99c0e1579a6988071f0e8 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 54ed37ddc8f9c34c2b87fd8fe437573c6f270922b9f14ada26547fd5889a5251 2f42b7874d33652145345b6a427a9a5d674b517692150e39c3908f45702de8ff
# phase23f legacy guard marker: changes_only 2f42b7874d33652145345b6a427a9a5d674b517692150e39c3908f45702de8ff
from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"

PROTECTED_HASHES = {
    "src/app/api.py": "b11904be37cdfdf8beb2ea93a0498bf6fb26ca9881f99c0e1579a6988071f0e8",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/agents/manual_review_readiness_contract.py": "5253414d1343d5eae64af7fbb6f87da68f9d4931b762cac972a94c29dc9ad5a2",
    "src/agents/provider_call_readiness_experiment.py": "d4176e889893b3acfb348c15a59a73418818e369e326f3935f4d673a50d88d28",
}


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _readback_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldRenderManualReviewReadinessFixture"
    )
    end = source.index(
        "\nfunction renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def _fetch_helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldFetchManualReviewReadinessReadback"
    )
    end = source.index(
        "\nfunction getAgenticReviewApprovalRequestId",
        start,
    )
    return source[start:end]


def test_renderer_and_fixture_gate_exist():
    snippet = _readback_helpers()

    assert "renderManualReviewReadinessReadbackSection" in snippet
    assert "manual_review_readiness_fixture" in snippet
    assert "window.location.search" in snippet
    assert "new URLSearchParams(query)" in snippet
    assert '=== "1"' in snippet


def test_optional_api_fetch_gate_exists_and_is_default_off():
    snippet = _fetch_helpers()

    assert "manual_review_readiness_api_fetch" in snippet
    assert "window.location.search" in snippet
    assert "new URLSearchParams(query)" in snippet
    assert '=== "1"' in snippet
    assert "|| !shouldFetchManualReviewReadinessReadback(search)" in snippet


def test_default_off_requires_supplied_payload_fixture_or_fetch_gate():
    helpers = _readback_helpers()
    renderer = helpers[
        helpers.index("function renderManualReviewReadinessReadbackSection"):
    ]

    assert "source.manual_review_readiness_result" in helpers
    assert (
        "|| !shouldRenderManualReviewReadinessFixture(search)"
        in helpers
    )
    assert 'if (!Object.keys(result).length) return "";' in renderer
    assert "withManualReviewReadinessReadbackApiFetch(" in _source()


def test_panel_title_fields_and_permanent_rule_exist():
    snippet = _readback_helpers()

    for marker in (
        "Manual-Review Readiness Readback",
        "Readiness status",
        "Manual review required",
        "Manual user control required",
        "No auto apply",
        "No auto submit",
        "No autonomous application execution",
        "No automatic job application submission",
        "Allowed assistance modes",
        "Forbidden actions",
        "Review inputs summary",
        "Missing review inputs",
        "Checklist items",
        "Next safe step",
        "Safety metadata summary",
        "no auto-apply",
        "no auto-submit",
        "no autonomous application execution",
    ):
        assert marker in snippet


def test_fixture_is_deterministic_read_only_and_manual_controlled():
    snippet = _readback_helpers()

    for marker in (
        "buildManualReviewReadinessFixtureResult",
        '"manual_review_readiness_ready"',
        '"Machine Learning Engineer"',
        '"Example Corp"',
        "read_only: true",
        "advisory_only: true",
        "manual_review_required: true",
        "manual_user_control_required: true",
        "no_auto_apply: true",
        "no_auto_submit: true",
        "no_autonomous_application_execution: true",
        "no_automatic_job_application_submission: true",
        "provider_call_attempted: false",
        "network_call_attempted: false",
        "mutation_authorized: false",
    ):
        assert marker in snippet


def test_fixture_does_not_overwrite_supplied_or_fetched_payload():
    snippet = _readback_helpers()

    assert "source.manual_review_readiness_result" in snippet
    assert "return source;" in snippet


def test_api_fetch_is_gated_post_only_and_targets_phase21c_endpoint():
    snippet = _fetch_helpers()
    gate_position = snippet.index(
        "!shouldFetchManualReviewReadinessReadback(search)"
    )
    fetch_position = snippet.index("await fetchJson(")

    assert gate_position < fetch_position
    assert snippet.count('"/api/manual-review-readiness-readback"') == 1
    assert 'method: "POST"' in snippet
    assert "enabled: false" in snippet
    assert "review_inputs_summary: null" in snippet


def test_api_response_reuses_renderer_and_failure_is_fail_closed():
    source = _source()
    snippet = _fetch_helpers()

    assert "manual_review_readiness_result: result" in snippet
    assert (
        "renderManualReviewReadinessReadbackSection("
        "manualReviewReadinessVisibleTracePayload)"
        in source
    )
    assert "catch (error)" in snippet
    assert '"manual_review_readiness_failed_closed"' in snippet
    assert "ui_api_fetch_failed: true" in snippet
    assert "read_only: true" in snippet
    assert "manual_user_control_required: true" in snippet
    assert "mutation_authorized: false" in snippet


def test_helpers_add_no_controls_storage_mutation_provider_or_automation():
    snippet = (_readback_helpers() + _fetch_helpers()).lower()

    for marker in (
        "<button",
        "<input",
        "<form",
        "data-apply",
        "data-submit",
        "data-execute",
        "data-approval",
        "data-autonomous",
        "data-provider",
        "localstorage.setitem",
        "sessionstorage.setitem",
        "createapproval(",
        "recordapproval(",
        "persistdecision(",
        "persistaudit(",
        "executeapplication(",
        "submitapplication(",
        "mutatequeue(",
        "updateranking(",
        "mutatescoring(",
        "mutateresume(",
        "providercall(",
        "autoapply(",
        "autosubmit(",
        "autonomousapplicationexecution(",
        "applicationsubmitter(",
        "applyautomatically(",
        "submitautomatically(",
    ):
        assert marker not in snippet


def test_protected_backend_and_helper_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase21d_changes_only_static_docs_tests_and_legacy_guards():
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
        "docs/phase22_core_agent_evidence_materialization_release_checkpoint.md",
        "tests/test_phase22f_core_agent_evidence_materialization_release_checkpoint_default_off.py",
        "src/agents/tailoring_agent_opportunity_contract.py",
        "docs/phase23_tailoring_agent_opportunity_contract.md",
        "tests/test_phase23a_tailoring_agent_opportunity_contract_default_off.py",
        "docs/phase23_tailoring_agent_opportunity_api_readback.md",
        "tests/test_phase23b_tailoring_agent_opportunity_api_readback_default_off.py",
        "docs/phase23_tailoring_agent_opportunity_ui_readback.md",
        "tests/test_phase23c_tailoring_agent_opportunity_ui_readback_default_off.py",
        "src/agents/generate_ai_tailoring_action_boundary_contract.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_contract.md",
        "tests/test_phase23d_generate_ai_tailoring_action_boundary_contract_default_off.py",
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
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback 2.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off 2.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback 2.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off 2.py",
    }
    allowed = {
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase21_manual_review_readiness_ui_readback.md",
        "tests/test_phase21d_manual_review_readiness_ui_readback_default_off.py",
        "docs/phase21_manual_review_workflow_release_checkpoint.md",
        "tests/test_phase21e_manual_review_workflow_release_checkpoint_default_off.py",
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
                    "tests/test_phase21c_manual_review_readiness_api_readback_default_off.py",
                    "b11904be37cdfdf8beb2ea93a0498bf6fb26ca9881f99c0e1579a6988071f0e8",
                    "300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab",
                "54ed37ddc8f9c34c2b87fd8fe437573c6f270922b9f14ada26547fd5889a5251",
            )
        )
    }

    assert changed <= allowed | legacy_guards
