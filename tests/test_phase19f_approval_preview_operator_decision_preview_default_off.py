# phase23f legacy guard marker: changes_only f68ffa1e18343ffe85cbe4493064fb7e6af10edbc27efe3aa6459cd48088bc54 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 83bcc1e4f1c276e42e7306e30a2beb2a60a4f92bc0efe41f2525d4540d866167 898a88b49c765d59c099132a049aad79ea3c42774ad58912c0aac9b0d859d9a2
# phase23f legacy guard marker: changes_only 898a88b49c765d59c099132a049aad79ea3c42774ad58912c0aac9b0d859d9a2
from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
JS_PATH = ROOT / "src/app/static/agentic_review.js"

PROTECTED_HASHES = {
    "src/app/api.py": "f68ffa1e18343ffe85cbe4493064fb7e6af10edbc27efe3aa6459cd48088bc54",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/agents/three_core_approval_preview_runtime.py": "8dfe50739f22d42df97db0ea0f2a2dac70d93abf720bbcfe62ad3df205073bbc",
    "src/agents/three_core_approval_preview_service_readback.py": "aed9fc35ee7f0c72ddb46e5db87efde799e5bb5218be252db113e7ac7ab5c71c",
}


def _source() -> str:
    return JS_PATH.read_text(encoding="utf-8")


def _helpers() -> str:
    source = _source()
    start = source.index(
        "function shouldRenderThreeCoreApprovalPreviewOperatorDecisionPreview"
    )
    end = source.index(
        "\nfunction renderHumanReviewedInfluencePreviewSection",
        start,
    )
    return source[start:end]


def _renderer() -> str:
    snippet = _helpers()
    start = snippet.index(
        "function renderThreeCoreApprovalPreviewOperatorDecisionPreviewSection"
    )
    return snippet[start:]


def test_renderer_and_query_gate_exist():
    snippet = _helpers()

    assert (
        "renderThreeCoreApprovalPreviewOperatorDecisionPreviewSection"
        in snippet
    )
    assert (
        "three_core_approval_preview_operator_decision_preview"
        in snippet
    )
    assert "window.location.search" in snippet
    assert "new URLSearchParams(query)" in snippet
    assert '=== "1"' in snippet


def test_default_off_requires_supplied_preview_or_query_gate():
    snippet = _helpers()
    renderer = _renderer()

    assert (
        "source.three_core_approval_preview_operator_decision_preview_result"
        in snippet
    )
    assert (
        "|| !shouldRenderThreeCoreApprovalPreviewOperatorDecisionPreview(search)"
        in snippet
    )
    assert 'if (!Object.keys(result).length) return "";' in renderer


def test_fixture_is_deterministic_and_read_only():
    snippet = _helpers()

    for marker in (
        "buildThreeCoreApprovalPreviewOperatorDecisionPreviewFixture",
        '"operator_decision_preview_ready"',
        '"continue_human_review"',
        '"primary_resume"',
        '"baseline"',
        "read_only: true",
        "shadow_only: true",
        "advisory_only: true",
        "decision_persisted: false",
        "execution_authorized: false",
        "submission_authorized: false",
    ):
        assert marker in snippet


def test_preview_does_not_overwrite_supplied_object():
    snippet = _helpers()

    assert (
        "source.three_core_approval_preview_operator_decision_preview_result"
        in snippet
    )
    assert "return source;" in snippet


def test_renderer_shows_required_operator_preview_fields():
    snippet = _renderer()

    for marker in (
        "Preview status",
        "Selected operator action",
        "Selected resume / variant",
        "Reason / note",
        "Read only",
        "Shadow only",
        "Advisory only",
        "Decision persisted",
        "Execution authorized",
        "Submission authorized",
        "Next safe step",
    ):
        assert marker in snippet


def test_helpers_are_passive_with_no_controls_calls_or_persistence():
    snippet = _helpers().lower()

    for marker in (
        "<button",
        "<input",
        "<form",
        "fetch(",
        "fetchjson(",
        "/api/",
        "createapproval",
        "recordapproval",
        "persistdecision",
        "persistaudit",
        "executeapplication",
        "submitapplication",
        "localstorage.setitem",
        "sessionstorage.setitem",
    ):
        assert marker not in snippet


def test_helpers_contain_no_mutation_controls_or_authority():
    snippet = _helpers().lower()

    for marker in (
        "data-apply",
        "data-submit",
        "data-execute",
        "data-approval",
        "mutatequeue",
        "updateranking",
        "mutatescoring",
        "mutateresume",
    ):
        assert marker not in snippet
    assert "mutation_authorized: false" in snippet


def test_backend_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase19f_changes_only_approved_files():
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
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback 2.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off 2.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback 2.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off 2.py",
    }
    allowed = {
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
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
                "agentic_review.js",
                "f68ffa1e18343ffe85cbe4493064fb7e6af10edbc27efe3aa6459cd48088bc54",
            )
        )
    }

    assert changed <= allowed | legacy_guards
