from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents import operator_decision_capture_readback_contract as contract


ROOT = Path(__file__).resolve().parents[1]

PROTECTED_HASHES = {
    "src/app/api.py": "4953e19b5b9914310d10ff758fd72eb4abed0ffb568a59fa43284ac17a4dce34",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "029c1105e4d3ae9f023ad40418e83cc13e4dffc937406b5e7219e8934d067e35",
    "src/app/static/app_redesign.css": "cbf6e94095f4ffcd932d31f163adde1c27f115dcbaa5ae4d0939398348f1e014",
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
    changed = set(tracked + untracked)
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
                    "4953e19b5b9914310d10ff758fd72eb4abed0ffb568a59fa43284ac17a4dce34",
                    "029c1105e4d3ae9f023ad40418e83cc13e4dffc937406b5e7219e8934d067e35",
                )
            )
        }

    assert changed <= allowed | legacy_guards
