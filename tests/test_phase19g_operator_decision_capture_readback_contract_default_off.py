# phase23f legacy guard marker: changes_only f68ffa1e18343ffe85cbe4493064fb7e6af10edbc27efe3aa6459cd48088bc54 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 83bcc1e4f1c276e42e7306e30a2beb2a60a4f92bc0efe41f2525d4540d866167 898a88b49c765d59c099132a049aad79ea3c42774ad58912c0aac9b0d859d9a2
# phase23f legacy guard marker: changes_only 898a88b49c765d59c099132a049aad79ea3c42774ad58912c0aac9b0d859d9a2
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents import operator_decision_capture_readback_contract as contract


ROOT = Path(__file__).resolve().parents[1]

PROTECTED_HASHES = {
    "src/app/api.py": "f68ffa1e18343ffe85cbe4493064fb7e6af10edbc27efe3aa6459cd48088bc54",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "898a88b49c765d59c099132a049aad79ea3c42774ad58912c0aac9b0d859d9a2",
    "src/app/static/app_redesign.css": "83bcc1e4f1c276e42e7306e30a2beb2a60a4f92bc0efe41f2525d4540d866167",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/agents/three_core_approval_preview_runtime.py": "8dfe50739f22d42df97db0ea0f2a2dac70d93abf720bbcfe62ad3df205073bbc",
    "src/agents/three_core_approval_preview_service_readback.py": "aed9fc35ee7f0c72ddb46e5db87efde799e5bb5218be252db113e7ac7ab5c71c",
}


def _enabled_config(**extra):
    return {
        contract.OPERATOR_DECISION_CAPTURE_READBACK_FLAG: True,
        **extra,
    }


def test_default_off_returns_not_enabled():
    payload = contract.build_operator_decision_capture_readback_payload()

    assert payload["capture_status"] == contract.STATUS_NOT_ENABLED
    assert payload["enabled"] is False


def test_enabled_without_config_flag_returns_not_enabled():
    payload = contract.build_operator_decision_capture_readback_payload(
        enabled=True,
        selected_action="HOLD",
        config={},
    )

    assert payload["capture_status"] == contract.STATUS_NOT_ENABLED


def test_kill_switch_blocks_contract():
    payload = contract.build_operator_decision_capture_readback_payload(
        enabled=True,
        selected_action="HOLD",
        config=_enabled_config(kill_switch_enabled=True),
    )

    assert payload["capture_status"] == contract.STATUS_BLOCKED_BY_KILL_SWITCH


def test_shadow_kill_switch_flag_blocks_contract():
    payload = contract.build_operator_decision_capture_readback_payload(
        enabled=True,
        selected_action="HOLD",
        config=_enabled_config(
            **{contract.SHADOW_KILL_SWITCH_FLAG: True}
        ),
    )

    assert payload["capture_status"] == contract.STATUS_BLOCKED_BY_KILL_SWITCH


def test_missing_action_returns_validation_error():
    payload = contract.build_operator_decision_capture_readback_payload(
        enabled=True,
        config=_enabled_config(),
    )

    assert payload["capture_status"] == contract.STATUS_MISSING_ACTION
    assert payload["validation_errors"] == ["selected_action_is_required"]


def test_unknown_action_returns_validation_error():
    payload = contract.build_operator_decision_capture_readback_payload(
        enabled=True,
        selected_action="SEND_NOW",
        config=_enabled_config(),
    )

    assert payload["capture_status"] == contract.STATUS_INVALID_ACTION
    assert payload["validation_errors"] == [
        "selected_action_is_not_allowed"
    ]


def test_valid_action_returns_ready_with_supplied_metadata():
    payload = contract.build_operator_decision_capture_readback_payload(
        enabled=True,
        selected_action="maybe_tailor",
        selected_resume="resume-main",
        selected_variant="variant-a",
        operator_note="Review only",
        config=_enabled_config(),
    )

    assert payload["capture_status"] == contract.STATUS_READY
    assert payload["selected_action"] == "MAYBE_TAILOR"
    assert payload["selected_resume"] == "resume-main"
    assert payload["selected_variant"] == "variant-a"
    assert payload["operator_note"] == "Review only"
    assert payload["validation_errors"] == []


def test_allowed_actions_are_ordered_exactly():
    assert contract.ALLOWED_ACTIONS == (
        "APPLY",
        "APPLY_REVIEW_VARIANTS",
        "MAYBE_TAILOR",
        "SKIP_FOR_NOW",
        "HOLD",
    )


def test_output_is_deterministic_and_inputs_are_not_mutated():
    config = _enabled_config()
    before = deepcopy(config)

    first = contract.build_operator_decision_capture_readback_payload(
        enabled=True,
        selected_action="HOLD",
        config=config,
    )
    second = contract.build_operator_decision_capture_readback_helper_payload(
        enabled=True,
        selected_action="HOLD",
        config=config,
    )

    assert first == second
    assert config == before


def test_payload_proves_no_persistence_mutation_execution_or_submission():
    payload = contract.build_operator_decision_capture_readback_payload(
        enabled=True,
        selected_action="APPLY",
        config=_enabled_config(),
    )

    assert payload["read_only"] is True
    assert payload["shadow_only"] is True
    assert payload["advisory_only"] is True
    for key in (
        "decision_persisted",
        "approval_created",
        "audit_persisted",
        "execution_authorized",
        "submission_authorized",
        "mutation_authorized",
    ):
        assert payload[key] is False


def test_safety_metadata_keeps_every_forbidden_path_inactive():
    safety = contract.operator_decision_capture_readback_safety_metadata()

    for key in (
        "provider_call",
        "provider_sdk_import",
        "env_secret_read",
        "network_call",
        "did_read_database",
        "did_write_database",
        "did_read_file",
        "did_write_file",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_mutate_resume",
        "did_create_approval",
        "did_persist_decision",
        "did_persist_audit",
        "did_create_execution_request",
        "did_execute_application",
        "did_submit_application",
    ):
        assert safety[key] is False


def test_helper_source_has_no_forbidden_runtime_imports_or_io():
    source = (
        ROOT / "src/agents/operator_decision_capture_readback_contract.py"
    ).read_text(encoding="utf-8").lower()

    for marker in (
        "os.environ",
        "pathlib",
        "open(",
        "requests",
        "httpx",
        "openai",
        "anthropic",
        "boto3",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "src.app",
        "src.pipeline",
        "src.storage",
        "create_approval_request",
        "record_approval_decision",
        "create_execution_request",
        "execute_application",
        "submit_application",
    ):
        assert marker not in source


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase19g_changes_only_approved_files():
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
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback 2.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off 2.py",
        "docs/phase22_core_agent_evidence_materialization_api_readback 2.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off 2.py",
    }
    allowed = {
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
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if any(
                marker in path.read_text(encoding="utf-8")
                for marker in (
                    "test_phase19f_approval_preview_operator_decision_preview_default_off.py",
                    "f68ffa1e18343ffe85cbe4493064fb7e6af10edbc27efe3aa6459cd48088bc54",
                    "300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab",
                )
            )
        }

    assert changed <= allowed | legacy_guards
