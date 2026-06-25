from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents import provider_call_readiness_experiment as experiment


ROOT = Path(__file__).resolve().parents[1]

PROTECTED_HASHES = {
    "src/app/api.py": "65975190cebecd5cefc179be1d71c4cbe7b3214ed9c7b3691d6cc7877f7db6e3",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "ec19a732f5ad655e5252a986a0e52239549a1e6d435f21c79f6d80e2c8b43454",
    "src/app/static/app_redesign.css": "8fae431da8b4d0a8fcbd9dbe9778d334e84905ef0e2915fcbb67dcf20eb4cdef",
    "src/agents/operator_decision_capture_readback_contract.py": "4066b415b7ac84eca8e37df5b1b71cad208001fd49c76126bd928eab39992450",
    "src/agents/three_core_approval_preview_runtime.py": "8dfe50739f22d42df97db0ea0f2a2dac70d93abf720bbcfe62ad3df205073bbc",
    "src/agents/three_core_approval_preview_service_readback.py": "aed9fc35ee7f0c72ddb46e5db87efde799e5bb5218be252db113e7ac7ab5c71c",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
}


def _enabled_config(**extra):
    return {
        experiment.PROVIDER_CALL_READINESS_EXPERIMENT_FLAG: True,
        **extra,
    }


def _ready_payload(**extra):
    return experiment.build_provider_call_readiness_experiment_payload(
        enabled=True,
        requested_provider_capability="review_jd_intelligence_packet",
        provider_name="caller-supplied-provider",
        requested_model="caller-supplied-model",
        request_packet_summary={
            "packet_type": "provider_call_preflight",
            "input_fields": ["job_description"],
        },
        config=_enabled_config(),
        **extra,
    )


def test_default_off_returns_not_enabled():
    payload = experiment.build_provider_call_readiness_experiment_payload()

    assert payload["readiness_status"] == experiment.STATUS_NOT_ENABLED
    assert payload["enabled"] is False


def test_enabled_without_config_flag_returns_not_enabled():
    payload = experiment.build_provider_call_readiness_experiment_payload(
        enabled=True,
        requested_provider_capability="review_packet",
        request_packet_summary={"packet_type": "preflight"},
        config={},
    )

    assert payload["readiness_status"] == experiment.STATUS_NOT_ENABLED


def test_kill_switch_blocks_experiment():
    for config in (
        _enabled_config(kill_switch_enabled=True),
        _enabled_config(**{experiment.SHADOW_KILL_SWITCH_FLAG: True}),
    ):
        payload = (
            experiment.build_provider_call_readiness_experiment_payload(
                enabled=True,
                requested_provider_capability="review_packet",
                request_packet_summary={"packet_type": "preflight"},
                config=config,
            )
        )
        assert payload["readiness_status"] == (
            experiment.STATUS_BLOCKED_BY_KILL_SWITCH
        )


def test_missing_provider_capability_returns_validation_error():
    payload = experiment.build_provider_call_readiness_experiment_payload(
        enabled=True,
        request_packet_summary={"packet_type": "preflight"},
        config=_enabled_config(),
    )

    assert payload["readiness_status"] == (
        experiment.STATUS_MISSING_PROVIDER_CAPABILITY
    )
    assert payload["validation_errors"] == [
        "requested_provider_capability_is_required"
    ]


def test_missing_request_packet_returns_validation_error():
    payload = experiment.build_provider_call_readiness_experiment_payload(
        enabled=True,
        requested_provider_capability="review_packet",
        config=_enabled_config(),
    )

    assert payload["readiness_status"] == (
        experiment.STATUS_MISSING_REQUEST_PACKET
    )
    assert payload["validation_errors"] == [
        "request_packet_summary_is_required"
    ]


def test_valid_caller_supplied_payload_returns_ready_deterministically():
    packet = {
        "packet_type": "provider_call_preflight",
        "input_fields": ["job_description"],
    }
    config = _enabled_config()
    packet_before = deepcopy(packet)
    config_before = deepcopy(config)

    first = experiment.build_provider_call_readiness_experiment_payload(
        enabled=True,
        requested_provider_capability="review_jd_intelligence_packet",
        provider_name="caller-supplied-provider",
        requested_model="caller-supplied-model",
        request_packet_summary=packet,
        config=config,
    )
    second = (
        experiment.build_provider_call_readiness_experiment_helper_payload(
            enabled=True,
            requested_provider_capability=(
                "review_jd_intelligence_packet"
            ),
            provider_name="caller-supplied-provider",
            requested_model="caller-supplied-model",
            request_packet_summary=packet,
            config=config,
        )
    )

    assert first == second
    assert first["readiness_status"] == experiment.STATUS_READY
    assert first["version"] == (
        experiment.PROVIDER_CALL_READINESS_EXPERIMENT_VERSION
    )
    assert first["schema_version"] == (
        experiment.PROVIDER_CALL_READINESS_EXPERIMENT_SCHEMA_VERSION
    )
    assert first["requested_provider_capability"] == (
        "review_jd_intelligence_packet"
    )
    assert first["provider_name"] == "caller-supplied-provider"
    assert first["requested_model"] == "caller-supplied-model"
    assert first["request_packet_summary"] == packet
    assert first["validation_errors"] == []
    assert packet == packet_before
    assert config == config_before
    assert first["request_packet_summary"] is not packet


def test_payload_is_read_only_and_never_authorizes_provider_or_mutation():
    payload = _ready_payload()

    assert payload["read_only"] is True
    assert payload["shadow_only"] is True
    assert payload["advisory_only"] is True
    for key in (
        "provider_call_attempted",
        "provider_call_authorized",
        "network_call_attempted",
        "decision_persisted",
        "approval_created",
        "audit_persisted",
        "execution_authorized",
        "submission_authorized",
        "mutation_authorized",
    ):
        assert payload[key] is False


def test_safety_metadata_proves_all_forbidden_paths_inactive():
    safety = (
        experiment.provider_call_readiness_experiment_safety_metadata()
    )

    assert safety["read_only"] is True
    assert safety["shadow_only"] is True
    assert safety["advisory_only"] is True
    for key in (
        "provider_call_attempted",
        "provider_call_authorized",
        "provider_sdk_imported",
        "network_call_attempted",
        "environment_read",
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
        "mutation_authorized",
        "execution_authorized",
        "submission_authorized",
    ):
        assert safety[key] is False


def test_helper_imports_no_runtime_wiring_sdk_storage_env_or_filesystem():
    source = (
        ROOT / "src/agents/provider_call_readiness_experiment.py"
    ).read_text(encoding="utf-8").lower()

    for marker in (
        "src.app",
        "src.pipeline",
        "src.storage",
        "openai",
        "anthropic",
        "boto3",
        "langchain",
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "os.getenv",
        "os.environ",
        "pathlib",
        "open(",
        "read_text(",
        "write_text(",
        "connect(",
        ".commit(",
        "provider_callable(",
        "provider_client",
        "score_jobs(",
        "rank_jobs(",
        "create_approval(",
        "persist_decision(",
        "persist_audit(",
        "execute_application(",
        "submit_application(",
    ):
        assert marker not in source


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_phase20a_changes_only_new_helper_doc_test_and_legacy_guards():
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
        "docs/phase22_core_agent_evidence_materialization_api_readback 2.md",
        "tests/test_phase22d_core_agent_evidence_materialization_api_readback_default_off 2.py",
    }
    allowed = {
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
                "docs/phase19_readonly_approval_workflow_release_checkpoint.md",
                "65975190cebecd5cefc179be1d71c4cbe7b3214ed9c7b3691d6cc7877f7db6e3",
                "ec19a732f5ad655e5252a986a0e52239549a1e6d435f21c79f6d80e2c8b43454",
            )
        )
    }

    assert changed <= allowed | legacy_guards
