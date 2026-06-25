from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents import three_core_approval_preview_runtime as preview_runtime
from src.agents import three_core_agent_shadow_runtime_readback


ROOT = Path(__file__).resolve().parents[1]

PROTECTED_HASHES = {
    "src/app/api.py": "4953e19b5b9914310d10ff758fd72eb4abed0ffb568a59fa43284ac17a4dce34",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "029c1105e4d3ae9f023ad40418e83cc13e4dffc937406b5e7219e8934d067e35",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/agents/relevance_prefilter.py": "5be6d21c27b720472daef6f85f813bc6561c90f9f8abfcfc09e88a5cd36a490b",
    "src/agents/jd_intelligence.py": "1f79df7e4349ce9ae7b1e5bad185a7958d86aa654d7c8bbd77634f59f529f81e",
    "src/agents/final_application_scoring.py": "eed7eed337b860345f38005c1f898732c8c809f6087e7fbbf33de6f4ad7ed2fd",
    "src/agents/three_core_agent_shadow_runtime_readback.py": "7a11a895ebb409b035cdd2851947f310df4b4fc7a58529794a3046fbbb6ac6b4",
    "src/agents/three_core_agent_shadow_pipeline_hook.py": "bdabd60eda23c115dfba27a3221a97d5b6782e61e13a62fd3c431b230c7428d8",
    "src/agents/three_core_agent_shadow_callable_adapters.py": "e7bfcf282a40d254ffbef99d2a8c92abdd2d43ac931741e7a39da1724dd8e37f",
}


def _enabled_config(**extra):
    return {
        preview_runtime.APPROVAL_PREVIEW_RUNTIME_FLAG: True,
        **extra,
    }


def _completed_readback():
    return {
        "readback_version": "phase-17g-three-core-shadow-runtime-readback-v1",
        "readback_status": (
            three_core_agent_shadow_runtime_readback.STATUS_COMPLETED
        ),
        "read_only": True,
        "shadow_only": True,
        "advisory_only": True,
        "ordered_core_agent_names": list(
            preview_runtime.ORDERED_CORE_AGENT_NAMES
        ),
        "mutation_authorized": False,
        "execution_authorized": False,
        "submission_authorized": False,
        "application_execution_authorized": False,
        "runtime_readback_summary": {
            "completion": True,
            "incomplete_checks": [],
        },
        "readback_context": {"trace_id": "trace-phase19a"},
    }


def test_default_off_returns_not_enabled():
    payload = preview_runtime.build_three_core_approval_preview_runtime_payload()

    assert payload["preview_status"] == preview_runtime.STATUS_NOT_ENABLED
    assert payload["preview_enabled"] is False


def test_missing_flag_returns_not_enabled():
    payload = preview_runtime.build_three_core_approval_preview_runtime_payload(
        enabled=True,
        shadow_runtime_readback_payload=_completed_readback(),
        preview_config={},
    )

    assert payload["preview_status"] == preview_runtime.STATUS_NOT_ENABLED


def test_kill_switch_blocks_preview():
    payload = preview_runtime.build_three_core_approval_preview_runtime_payload(
        enabled=True,
        shadow_runtime_readback_payload=_completed_readback(),
        preview_config=_enabled_config(kill_switch_enabled=True),
    )

    assert payload["preview_status"] == (
        preview_runtime.STATUS_BLOCKED_BY_KILL_SWITCH
    )


def test_missing_shadow_readback_fails_closed():
    payload = preview_runtime.build_three_core_approval_preview_runtime_payload(
        enabled=True,
        preview_config=_enabled_config(),
    )

    assert payload["preview_status"] == (
        preview_runtime.STATUS_BLOCKED_MISSING_SHADOW_READBACK
    )


def test_completed_three_core_readback_returns_ready():
    payload = preview_runtime.build_three_core_approval_preview_runtime_payload(
        enabled=True,
        shadow_runtime_readback_payload=_completed_readback(),
        preview_context={
            "requested_capability": "review_three_core_shadow_evidence",
            "target_context_summary": {"job_id": "job-19a"},
        },
        preview_config=_enabled_config(),
    )

    assert payload["preview_status"] == preview_runtime.STATUS_READY
    assert payload["linked_trace_or_readback_id"] == "trace-phase19a"
    assert payload["missing_requirements"] == []
    assert payload["fail_closed_reason"] == ""


def test_incomplete_shadow_readback_is_blocked():
    source = _completed_readback()
    source["readback_status"] = (
        three_core_agent_shadow_runtime_readback.STATUS_INCOMPLETE
    )
    source["runtime_readback_summary"] = {
        "completion": False,
        "incomplete_checks": ["ordered_core_agent_names_match"],
    }

    payload = preview_runtime.build_three_core_approval_preview_runtime_payload(
        enabled=True,
        shadow_runtime_readback_payload=source,
        preview_config=_enabled_config(),
    )

    assert payload["preview_status"] == (
        preview_runtime.STATUS_BLOCKED_INCOMPLETE_SHADOW_READBACK
    )
    assert payload["missing_requirements"] == [
        "ordered_core_agent_names_match"
    ]


def test_sidecar_readback_exception_returns_failed_closed(monkeypatch):
    def raise_readback(**_kwargs):
        raise RuntimeError("readback failure")

    monkeypatch.setattr(
        three_core_agent_shadow_runtime_readback,
        "build_three_core_agent_shadow_runtime_readback",
        raise_readback,
    )
    payload = preview_runtime.build_three_core_approval_preview_runtime_payload(
        enabled=True,
        shadow_sidecar_hook_payload={"hook_status": "caller_supplied"},
        preview_config=_enabled_config(),
    )

    assert payload["preview_status"] == preview_runtime.STATUS_FAILED_CLOSED
    assert payload["fail_closed_reason"] == (
        "unexpected_approval_preview_runtime_failure"
    )


def test_output_is_deterministic_and_inputs_are_not_mutated():
    source = _completed_readback()
    context = {"target_context_summary": {"job_id": "job-19a"}}
    config = _enabled_config()
    before = deepcopy((source, context, config))

    first = preview_runtime.build_three_core_approval_preview_runtime_payload(
        enabled=True,
        shadow_runtime_readback_payload=source,
        preview_context=context,
        preview_config=config,
    )
    second = preview_runtime.build_three_core_approval_preview_runtime_helper_payload(
        enabled=True,
        shadow_runtime_readback_payload=source,
        preview_context=context,
        preview_config=config,
    )

    assert first == second
    assert (source, context, config) == before


def test_ordered_agents_and_review_metadata_are_complete():
    payload = preview_runtime.build_three_core_approval_preview_runtime_payload(
        enabled=True,
        shadow_runtime_readback_payload=_completed_readback(),
        preview_config=_enabled_config(),
    )

    assert payload["ordered_core_agent_names"] == [
        "relevance_prefilter",
        "jd_intelligence",
        "final_application_scoring",
    ]
    for field in (
        "approval_preview_metadata",
        "evidence_summary",
        "proposed_action_summary",
        "risk_summary",
        "safety_flag_summary",
    ):
        assert field in payload


def test_payload_and_safety_metadata_prove_forbidden_paths_are_inactive():
    payload = preview_runtime.build_three_core_approval_preview_runtime_payload(
        enabled=True,
        shadow_runtime_readback_payload=_completed_readback(),
        preview_config=_enabled_config(),
    )
    safety = payload["safety_metadata"]

    assert payload["read_only"] is True
    assert payload["shadow_only"] is True
    assert payload["advisory_only"] is True
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
        "did_persist_decision",
        "did_persist_audit",
        "did_create_execution_request",
        "did_execute_application",
        "did_submit_application",
        "api_route_added",
        "ui_action_added",
        "pipeline_wiring_added",
        "collector_wiring_added",
    ):
        assert safety[key] is False


def test_module_source_has_no_forbidden_runtime_markers():
    source = (
        ROOT / "src/agents/three_core_approval_preview_runtime.py"
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
        assert "three_core_approval_preview_runtime" not in (
            ROOT / relative_path
        ).read_text(encoding="utf-8")


def test_phase19a_changes_only_approved_files():
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
        "src/agents/three_core_approval_preview_runtime.py",
        "tests/test_phase19a_three_core_approval_preview_runtime_readonly_default_off.py",
        "docs/phase19_approval_preview_runtime_readonly.md",
        "src/agents/three_core_approval_preview_service_readback.py",
        "docs/phase19_approval_preview_service_readback.md",
        "tests/test_phase19b_three_core_approval_preview_service_readback_default_off.py",
        "src/app/api.py",
        "docs/phase19_approval_preview_api_readback.md",
        "tests/test_phase19c_three_core_approval_preview_api_readback_default_off.py",
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
            "tests/test_jd_provider_runtime_review_packet_default_off.py",
        "tests/test_jd_provider_runtime_service_readback_default_off.py",
        "tests/test_jd_provider_runtime_shadow_bridge_default_off.py",
        "tests/test_jd_provider_runtime_trace_readback_default_off.py",
        "tests/test_jd_provider_runtime_ui_readback_default_off.py",
        "tests/test_pgvector_connection_provider_default_off.py",
        "tests/test_pgvector_extension_probe_contract_no_schema.py",
        "tests/test_pgvector_extension_probe_ui_no_schema_readonly.py",
        "tests/test_pgvector_local_smoke_default_off.py",
        "tests/test_pgvector_real_local_smoke_command_default_off.py",
        "tests/test_pgvector_schema_store_adapter_default_off.py",
        "tests/test_pgvector_smoke_readback_verification_default_off.py",
        "tests/test_pgvector_store_db_executor_default_off.py",
        "tests/test_pipeline_embedding_retrieval_hook_default_off.py",
        "tests/test_pipeline_runtime_embedding_bridge_default_off.py",
        "tests/test_pipeline_vector_evidence_hook_default_off.py",
        "tests/test_provider_live_activation_safety_plan_default_off.py",
        "tests/test_provider_live_config_gate_default_off.py",
        "tests/test_provider_runtime_ui_readback_default_off.py",
        "tests/test_semantic_evidence_quality_gate_default_off.py",
        "tests/test_shadow_agent_vector_evidence_input_default_off.py",
        "tests/test_shadow_semantic_evidence_agent_input_default_off.py",
        "tests/test_shadow_vector_evidence_context_default_off.py",
        "tests/test_tailoring_provider_shadow_default_off.py",
        "tests/test_three_agent_llmops_aggregate_default_off.py",
        "tests/test_three_agent_llmops_observability_readback_default_off.py",
        "tests/test_three_agent_llmops_observability_service_bridge_default_off.py",
        "tests/test_three_agent_llmops_observability_ui_default_off.py",
        "tests/test_three_agent_llmops_trace_contract_default_off.py",
        "tests/test_three_agent_provider_handoff_default_off.py",
        "tests/test_three_agent_shadow_workflow_default_off.py",
        "tests/test_three_agent_workflow_readiness_default_off.py",
        "tests/test_vector_evidence_embedding_indexing_helper_default_off.py",
        "tests/test_vector_evidence_embedding_provider_contract_default_off.py",
        "tests/test_vector_evidence_embedding_retrieval_helper_default_off.py",
        "tests/test_vector_evidence_embedding_runtime_adapter_default_off.py",
        "tests/test_vector_evidence_embedding_runtime_service_bridge_default_off.py",
        "tests/test_vector_evidence_readback_service_helper_default_off.py",
        "tests/test_vector_evidence_readback_ui_default_off.py",
        "tests/test_vector_evidence_service_connection_provider_bridge_default_off.py",
        "tests/test_vector_evidence_service_db_executor_bridge_default_off.py",
        "tests/test_vector_evidence_service_pgvector_store_flagged_default_off.py",
        "tests/test_vector_evidence_ui_no_db_readonly.py",
        "tests/test_agent_trace_ui_readiness_checkpoint.py",
        "tests/test_agentic_review_ui_compaction_polish_no_backend_change.py",
        "tests/test_agentic_review_ui_portfolio_polish_no_backend_change.py",
        "tests/test_critic_provider_shadow_default_off.py",
        "tests/test_jd_intelligence_provider_shadow_default_off.py",
        "tests/test_jd_live_provider_canary_command_default_off.py",
        "tests/test_jd_live_provider_canary_default_off.py",
        "tests/test_jd_live_provider_canary_readback_default_off.py",
        "tests/test_jd_live_provider_canary_readiness_checkpoint_default_off.py",
        "tests/test_jd_live_provider_canary_runbook_default_off.py",
        "tests/test_jd_live_provider_canary_service_readback_default_off.py",
        "tests/test_jd_live_provider_canary_shadow_bridge_default_off.py",
        "tests/test_jd_live_provider_canary_ui_readback_default_off.py",
        "tests/test_jd_live_provider_external_adapter_default_off.py",
        "tests/test_jd_manual_live_canary_readiness_checkpoint_default_off.py",
        "tests/test_jd_provider_runtime_activation_default_off.py",
        "tests/test_jd_provider_runtime_readiness_checkpoint_default_off.py",
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
            )
        )
    }
    assert changed <= allowed | legacy_static_hash_guards


def test_protected_runtime_hashes_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        path = ROOT / relative_path

        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == expected_hash
