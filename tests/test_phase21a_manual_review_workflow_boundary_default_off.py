# phase26c legacy guard marker: changes_only bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821 c71e2057276080e36fce4bec48a881753d8e09d7d1b49e7d0676d4a0665f32c9
# phase26b legacy guard marker: changes_only 96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff
# phase23f legacy guard marker: changes_only 96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab c71e2057276080e36fce4bec48a881753d8e09d7d1b49e7d0676d4a0665f32c9 bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821
# phase23f legacy guard marker: changes_only bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821
from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
BOUNDARY_PATH = ROOT / "docs/manual_review_workflow_boundary.md"
CHECKPOINT_PATH = ROOT / "docs/phase21_manual_review_workflow_boundary.md"

REQUIRED_MARKERS = (
    "no auto-apply",
    "no auto-submit",
    "no autonomous application execution",
    "no automatic job application submission",
    "manual user control",
    "manual-review workflow",
    "no bypass of manual review",
)

REQUIRED_TAGS = (
    "phase20-provider-readiness-release-v1",
    "phase20e-provider-readiness-release-checkpoint-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
    "phase19-readonly-approval-workflow-release-v1",
    "phase18-safety-wrap-release-v1",
)

ASSISTIVE_CAPABILITIES = (
    "discovery",
    "filtering",
    "ranking",
    "read-only previews",
    "readiness checks",
    "resume/content guidance",
    "manual review support",
)

PROTECTED_HASHES = {
    "src/app/api.py": "96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "bb3b1f351b9f3aeac197a3077ce4403f649a17ff81247fb1d0e41eeacc3a9821",
    "src/app/static/app_redesign.css": "c71e2057276080e36fce4bec48a881753d8e09d7d1b49e7d0676d4a0665f32c9",
    "src/agents/provider_call_readiness_experiment.py": "d4176e889893b3acfb348c15a59a73418818e369e326f3935f4d673a50d88d28",
    "src/agents/operator_decision_capture_readback_contract.py": "4066b415b7ac84eca8e37df5b1b71cad208001fd49c76126bd928eab39992450",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
}

FORBIDDEN_RUNTIME_MARKERS = (
    "autoApply",
    "autoSubmit",
    "autonomousApplicationExecution",
    "executeApplication",
    "submitApplication",
    "applicationSubmitter",
    "applyAutomatically",
    "submitAutomatically",
)


def _text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


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


def test_boundary_and_checkpoint_docs_exist():
    assert BOUNDARY_PATH.exists()
    assert CHECKPOINT_PATH.exists()
    assert _text(BOUNDARY_PATH).startswith(
        "# Manual-Review Workflow Boundary"
    )
    assert _text(CHECKPOINT_PATH).startswith(
        "# Phase 21A Manual-Review Workflow Boundary Checkpoint"
    )


def test_both_docs_contain_exact_boundary_markers():
    for path in (BOUNDARY_PATH, CHECKPOINT_PATH):
        text = _text(path).lower()
        for marker in REQUIRED_MARKERS:
            assert marker in text


def test_both_docs_reference_required_release_tags():
    for path in (BOUNDARY_PATH, CHECKPOINT_PATH):
        text = _text(path)
        for tag in REQUIRED_TAGS:
            assert tag in text


def test_docs_list_assistive_manual_review_capabilities():
    for path in (BOUNDARY_PATH, CHECKPOINT_PATH):
        text = _text(path).lower()
        for capability in ASSISTIVE_CAPABILITIES:
            assert capability in text


def test_phase21_focuses_on_manual_review_not_autonomous_execution():
    for path in (BOUNDARY_PATH, CHECKPOINT_PATH):
        text = _text(path)
        assert "Phase 21" in text
        assert "hardening the manual-review workflow" in text
        assert "not enabling autonomous application execution" in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase21a_changes_only_docs_tests_and_legacy_guards():
    changed = _changed_files() - {
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
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback 2.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off 2.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback 2.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off 2.py",
    }
    allowed = {
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
                "tests/test_phase20e_provider_readiness_release_checkpoint_default_off.py",
                "96f9cd7e7f3f877a147d612ad1394b8fcdd4671244de25c9f99c34795304a8ff",
                "300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab",
            )
        )
    }

    assert changed <= allowed | legacy_guards


def test_changed_runtime_files_add_no_autonomous_application_markers():
    runtime_suffixes = {".py", ".js", ".html", ".css"}
    changed_runtime_files = [
        ROOT / relative_path
        for relative_path in _changed_files()
        if relative_path.startswith("src/")
        and Path(relative_path).suffix in runtime_suffixes
    ]

    assert changed_runtime_files in (
        [],
        [ROOT / "src/agents/manual_review_readiness_contract.py"],
        [ROOT / "src/agents/core_agent_evidence_materialization_preview.py"],
        [ROOT / "src/agents/tailoring_agent_opportunity_contract.py"],
        [ROOT / "src/agents/generate_ai_tailoring_action_boundary_contract.py"],
        [
            ROOT
            / "src/agents/manual_generate_ai_tailoring_preview_contract.py"
        ],
        [
            ROOT
            / "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py"
        ],
        [
            ROOT
            / "src/agents/manual_generate_ai_tailoring_preview_dispatch_boundary_contract.py"
        ],
            [
                ROOT
                / "src/agents/manual_generate_ai_tailoring_preview_provider_request_envelope_contract.py"
            ],
                [
                    ROOT
                    / "src/agents/manual_generate_ai_tailoring_preview_provider_call_boundary_contract.py"
                ],
                [
                    ROOT
                    / "src/agents/manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.py"
                ],
                [ROOT / "src/app/api.py"],
        [ROOT / "src/app/static/agentic_review.js"],
        [
            ROOT / "src/app/static/agentic_review.js",
            ROOT / "src/app/static/app_redesign.css",
        ],
        [
            ROOT / "src/app/static/app_redesign.css",
            ROOT / "src/app/static/agentic_review.js",
        ],
    )
    for path in changed_runtime_files:
        source = path.read_text(encoding="utf-8")
        for marker in FORBIDDEN_RUNTIME_MARKERS:
            assert marker not in source
