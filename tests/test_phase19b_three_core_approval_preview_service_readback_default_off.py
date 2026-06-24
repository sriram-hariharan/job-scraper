from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents import three_core_approval_preview_runtime as preview_runtime
from src.agents import three_core_approval_preview_service_readback as service_readback
from src.agents import three_core_agent_shadow_runtime_readback


ROOT = Path(__file__).resolve().parents[1]

PROTECTED_HASHES = {
    "src/app/api.py": "23e335987f08ddc484c8b0617608b6a742e58b780f7a932c14401e1ce5045766",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "3520143a71e59a3e4f225db746657c248f10d5317480b602de3881d8811abb97",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/agents/relevance_prefilter.py": "5be6d21c27b720472daef6f85f813bc6561c90f9f8abfcfc09e88a5cd36a490b",
    "src/agents/jd_intelligence.py": "1f79df7e4349ce9ae7b1e5bad185a7958d86aa654d7c8bbd77634f59f529f81e",
    "src/agents/final_application_scoring.py": "eed7eed337b860345f38005c1f898732c8c809f6087e7fbbf33de6f4ad7ed2fd",
    "src/agents/three_core_agent_shadow_runtime_readback.py": "7a11a895ebb409b035cdd2851947f310df4b4fc7a58529794a3046fbbb6ac6b4",
    "src/agents/three_core_agent_shadow_pipeline_hook.py": "bdabd60eda23c115dfba27a3221a97d5b6782e61e13a62fd3c431b230c7428d8",
    "src/agents/three_core_agent_shadow_callable_adapters.py": "e7bfcf282a40d254ffbef99d2a8c92abdd2d43ac931741e7a39da1724dd8e37f",
    "src/agents/three_core_approval_preview_runtime.py": "8dfe50739f22d42df97db0ea0f2a2dac70d93abf720bbcfe62ad3df205073bbc",
}


def _enabled_config(**extra):
    return {
        service_readback.APPROVAL_PREVIEW_SERVICE_READBACK_FLAG: True,
        **extra,
    }


def _ready_preview():
    return preview_runtime.build_three_core_approval_preview_runtime_payload(
        enabled=True,
        shadow_runtime_readback_payload=_completed_shadow_readback(),
        preview_context={
            "requested_capability": "review_three_core_shadow_evidence",
            "target_context_summary": {"job_id": "job-19b"},
        },
        preview_config={preview_runtime.APPROVAL_PREVIEW_RUNTIME_FLAG: True},
    )


def _completed_shadow_readback():
    return {
        "readback_version": "phase-17g-three-core-shadow-runtime-readback-v1",
        "readback_status": three_core_agent_shadow_runtime_readback.STATUS_COMPLETED,
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "ordered_core_agent_names": list(service_readback.ORDERED_CORE_AGENT_NAMES),
        "mutation_authorized": False,
        "execution_authorized": False,
        "submission_authorized": False,
        "application_execution_authorized": False,
        "runtime_readback_summary": {
            "completion": True,
            "incomplete_checks": [],
        },
        "readback_context": {"trace_id": "trace-phase19b"},
    }


def test_default_off_returns_not_enabled():
    payload = (
        service_readback
        .build_three_core_approval_preview_service_readback_payload()
    )

    assert payload["service_readback_status"] == service_readback.STATUS_NOT_ENABLED
    assert payload["service_readback_enabled"] is False


def test_missing_service_flag_returns_not_enabled():
    payload = (
        service_readback
        .build_three_core_approval_preview_service_readback_payload(
            enabled=True,
            approval_preview_runtime_payload=_ready_preview(),
            readback_config={},
        )
    )

    assert payload["service_readback_status"] == service_readback.STATUS_NOT_ENABLED


def test_kill_switch_blocks_service_readback():
    payload = (
        service_readback
        .build_three_core_approval_preview_service_readback_payload(
            enabled=True,
            approval_preview_runtime_payload=_ready_preview(),
            readback_config=_enabled_config(kill_switch_enabled=True),
        )
    )

    assert payload["service_readback_status"] == (
        service_readback.STATUS_BLOCKED_BY_KILL_SWITCH
    )


def test_missing_approval_preview_is_blocked():
    payload = (
        service_readback
        .build_three_core_approval_preview_service_readback_payload(
            enabled=True,
            readback_config=_enabled_config(),
        )
    )

    assert payload["service_readback_status"] == (
        service_readback.STATUS_BLOCKED_MISSING_PREVIEW
    )


def test_ready_phase19a_preview_returns_ready():
    payload = (
        service_readback
        .build_three_core_approval_preview_service_readback_payload(
            enabled=True,
            approval_preview_runtime_payload=_ready_preview(),
            readback_config=_enabled_config(),
        )
    )

    assert payload["service_readback_status"] == service_readback.STATUS_READY
    assert payload["target_context_summary"] == {"job_id": "job-19b"}
    assert payload["missing_requirements"] == []


def test_incomplete_phase19a_preview_is_blocked():
    preview = _ready_preview()
    preview["preview_status"] = preview_runtime.STATUS_BLOCKED_INCOMPLETE_SHADOW_READBACK
    preview["missing_requirements"] = ["completed_shadow_readback"]

    payload = (
        service_readback
        .build_three_core_approval_preview_service_readback_payload(
            enabled=True,
            approval_preview_runtime_payload=preview,
            readback_config=_enabled_config(),
        )
    )

    assert payload["service_readback_status"] == (
        service_readback.STATUS_BLOCKED_INCOMPLETE_PREVIEW
    )
    assert payload["missing_requirements"] == ["completed_shadow_readback"]


def test_shadow_readback_is_converted_through_phase19a_and_summarized():
    payload = (
        service_readback
        .build_three_core_approval_preview_service_readback_payload(
            enabled=True,
            shadow_runtime_readback_payload=_completed_shadow_readback(),
            readback_context={"trace_id": "trace-phase19b"},
            readback_config=_enabled_config(),
        )
    )

    assert payload["service_readback_status"] == service_readback.STATUS_READY
    assert payload["linked_trace_or_readback_id"] == "trace-phase19b"
    assert payload["source_approval_preview_runtime_summary"][
        "preview_status"
    ] == preview_runtime.STATUS_READY


def test_phase19a_builder_exception_returns_failed_closed(monkeypatch):
    def raise_preview(**_kwargs):
        raise RuntimeError("preview failure")

    monkeypatch.setattr(
        preview_runtime,
        "build_three_core_approval_preview_runtime_payload",
        raise_preview,
    )
    payload = (
        service_readback
        .build_three_core_approval_preview_service_readback_payload(
            enabled=True,
            shadow_runtime_readback_payload={"readback_status": "supplied"},
            readback_config=_enabled_config(),
        )
    )

    assert payload["service_readback_status"] == (
        service_readback.STATUS_FAILED_CLOSED
    )
    assert payload["fail_closed_reason"] == "unexpected_service_readback_failure"


def test_output_is_deterministic_and_inputs_are_not_mutated():
    preview = _ready_preview()
    context = {"target_context_summary": {"job_id": "job-19b"}}
    config = _enabled_config()
    before = deepcopy((preview, context, config))

    first = (
        service_readback
        .build_three_core_approval_preview_service_readback_payload(
            enabled=True,
            approval_preview_runtime_payload=preview,
            readback_context=context,
            readback_config=config,
        )
    )
    second = (
        service_readback
        .build_three_core_approval_preview_service_readback_helper_payload(
            enabled=True,
            approval_preview_runtime_payload=preview,
            readback_context=context,
            readback_config=config,
        )
    )

    assert first == second
    assert (preview, context, config) == before


def test_ordered_agents_and_service_review_metadata_are_complete():
    payload = (
        service_readback
        .build_three_core_approval_preview_service_readback_payload(
            enabled=True,
            approval_preview_runtime_payload=_ready_preview(),
            readback_config=_enabled_config(),
        )
    )

    assert payload["ordered_core_agent_names"] == [
        "relevance_prefilter",
        "jd_intelligence",
        "final_application_scoring",
    ]
    for field in (
        "service_readback_metadata",
        "operator_review_summary",
        "evidence_summary",
        "proposed_action_summary",
        "risk_summary",
        "safety_flag_summary",
    ):
        assert field in payload


def test_safety_metadata_proves_forbidden_paths_are_inactive():
    payload = (
        service_readback
        .build_three_core_approval_preview_service_readback_payload(
            enabled=True,
            approval_preview_runtime_payload=_ready_preview(),
            readback_config=_enabled_config(),
        )
    )
    safety = payload["safety_metadata"]

    assert payload["read_only"] is True
    assert payload["shadow_only"] is True
    assert payload["advisory_only"] is True
    assert payload["service_readback_only"] is True
    for key in (
        "provider_call",
        "provider_sdk_import",
        "env_secret_read",
        "network_call",
        "did_read_database",
        "did_write_database",
        "did_write_file",
        "did_mutate_scoring",
        "did_change_ranking",
        "did_mutate_queue",
        "did_mutate_resume",
        "did_create_approval",
        "did_mutate_approval",
        "did_persist_decision",
        "did_persist_audit",
        "did_create_execution_request",
        "did_execute_application",
        "did_submit_application",
        "api_route_added",
        "ui_action_added",
        "app_service_wiring_added",
        "pipeline_wiring_added",
        "collector_wiring_added",
    ):
        assert safety[key] is False


def test_module_source_has_no_forbidden_runtime_markers():
    source = (
        ROOT / "src/agents/three_core_approval_preview_service_readback.py"
    ).read_text(encoding="utf-8").lower()

    for marker in (
        "os.environ",
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
        "create_approval_request",
        "record_approval_decision",
        "create_execution_request",
        "execute_application",
        "submit_application",
        "update_ranking",
        "mutate_queue",
    ):
        assert marker not in source


def test_protected_runtime_surfaces_do_not_reference_new_helper():
    for relative_path in (
        "src/app/api.py",
        "src/app/services.py",
        "src/app/static/agentic_review.js",
        "src/pipeline/collector.py",
    ):
        assert "three_core_approval_preview_service_readback" not in (
            ROOT / relative_path
        ).read_text(encoding="utf-8")


def test_phase19b_changes_only_approved_files():
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
        "src/agents/three_core_approval_preview_service_readback.py",
        "tests/test_phase19b_three_core_approval_preview_service_readback_default_off.py",
        "docs/phase19_approval_preview_service_readback.md",
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

    assert changed <= allowed


def test_protected_runtime_hashes_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        path = ROOT / relative_path

        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == expected_hash
