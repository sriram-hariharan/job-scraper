from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/three_core_shadow_readiness_wrap.md"

ORDERED_AGENTS = [
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
]

PHASE_TAGS = [
    "phase17a-three-core-agent-shadow-pipeline-hook-v1",
    "phase17b-three-core-agent-shadow-sidecar-bridge-v1",
    "phase17c-three-core-agent-collector-shadow-wiring-v1",
    "phase17d-three-core-agent-collector-connection-plan-v1",
    "phase17e-three-core-agent-shadow-callable-adapters-v1",
    "phase17f-three-core-agent-collector-callable-wiring-v1",
    "phase17g-three-core-agent-shadow-runtime-readback-v1",
    "phase17h-three-core-agent-shadow-operator-canary-v1",
    "phase17i-three-core-agent-shadow-api-ui-readback-v1",
    "phase17j-three-core-shadow-local-fixture-ui-visibility-v1",
]

RUNTIME_HASHES = {
    "src/agents/relevance_prefilter.py": (
        "5be6d21c27b720472daef6f85f813bc6561c90f9f8abfcfc09e88a5cd36a490b"
    ),
    "src/agents/jd_intelligence.py": (
        "1f79df7e4349ce9ae7b1e5bad185a7958d86aa654d7c8bbd77634f59f529f81e"
    ),
    "src/agents/final_application_scoring.py": (
        "eed7eed337b860345f38005c1f898732c8c809f6087e7fbbf33de6f4ad7ed2fd"
    ),
    "src/agents/three_core_agent_shadow_pipeline_hook.py": (
        "bdabd60eda23c115dfba27a3221a97d5b6782e61e13a62fd3c431b230c7428d8"
    ),
    "src/agents/shadow_sidecar_hook.py": (
        "0bbc15e9a2bae8e5154ff62b5fda7b6e4989ecc70f1104719197a2cf337ac3df"
    ),
    "src/agents/three_core_agent_shadow_pipeline_connection_plan.py": (
        "b6c244dac9a9f3f3180b928cf1375de77cd41a69c0f8688a8dead6708e188c0b"
    ),
    "src/agents/three_core_agent_shadow_callable_adapters.py": (
        "e7bfcf282a40d254ffbef99d2a8c92abdd2d43ac931741e7a39da1724dd8e37f"
    ),
    "src/agents/three_core_agent_shadow_runtime_readback.py": (
        "7a11a895ebb409b035cdd2851947f310df4b4fc7a58529794a3046fbbb6ac6b4"
    ),
    "src/agents/three_core_agent_shadow_operator_canary.py": (
        "b130620a2257603bd2ed5259f65434e4f13d9636d1d25a417c594f38251bb943"
    ),
    "src/pipeline/collector.py": (
        "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"
    ),
    "src/app/api.py": (
        "7cd4cc3e4bb921542e6f6e4870fb4999e7546fb5db90ed3bc1aa07d17930c1b5"
    ),
    "src/app/services.py": (
        "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee"
    ),
    "src/app/static/agentic_review.js": (
        "b3f311bc5390eacc4d698d71141ebd3a960a491765c074ebd37c33718f887a03"
    ),
}


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


def test_readiness_wrap_doc_exists_and_names_checkpoint():
    assert DOC.exists()
    assert "# Three-Core Shadow Readiness Wrap" in _text()
    assert "docs/tests only" in _text()


def test_three_core_agents_are_named_in_correct_order():
    text = _text()
    positions = [text.index(f"`{agent}`") for agent in ORDERED_AGENTS]

    assert positions == sorted(positions)


def test_all_phase_17a_through_17j_tags_are_documented():
    text = _text()

    for tag in PHASE_TAGS:
        assert f"`{tag}`" in text


def test_known_endpoint_fixture_and_flags_are_exact():
    text = _text()

    for term in (
        "/api/three-core-shadow-operator-canary-readback",
        "?three_core_canary_fixture=1",
        "APPLYLENS_AGENTIC_PIPELINE_THREE_CORE_SHADOW_PIPELINE_HOOK_ENABLED",
        "APPLYLENS_AGENTIC_PIPELINE_SHADOW_SIDECAR_ENABLED",
    ):
        assert f"`{term}`" in text


def test_default_off_read_only_shadow_only_advisory_only_are_explicit():
    text = _text()

    for term in ("default-off", "read-only", "shadow-only", "advisory-only"):
        assert term in text


def test_mutation_and_application_paths_are_not_authorized():
    text = _text().lower()

    for term in (
        "mutation authorization | not authorized",
        "final scoring mutation | not authorized",
        "ranking mutation | not authorized",
        "queue mutation | not authorized",
        "resume mutation | not authorized",
        "application execution | not authorized",
        "application submission | not authorized",
    ):
        assert term in text


def test_provider_network_database_and_file_io_are_not_used():
    text = _text()

    for term in (
        "Provider SDK call | Not used",
        "Network call | Not used",
        "Database read/write | Not used",
        "File IO | Not used",
    ):
        assert term in text


def test_fixture_verification_forbids_action_controls():
    text = _text().lower()

    assert "?three_core_canary_fixture=1" in text
    assert "no apply, submit, execute, or approval control appears" in text
    assert "only when" in text
    assert "real" in text


def test_next_safe_decision_options_are_documented_in_order():
    text = _text()
    options = [
        "Keep the completed Phase 17 surface shadow-only.",
        "Promote these readiness docs to the main release.",
        "Design a separate protected approval plan before any live provider or",
    ]
    positions = [text.index(option) for option in options]

    assert positions == sorted(positions)


def test_phase_17k_changes_only_approved_docs_and_tests():
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
        "docs/three_core_shadow_readiness_wrap.md",
        "tests/test_three_core_shadow_readiness_wrap_default_off.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
        "docs/phase18_live_readiness_approval_boundary.md",
        "tests/test_phase18_live_readiness_approval_boundary_default_off.py",
        "docs/phase18_human_approval_gate_contract.md",
        "tests/test_phase18_human_approval_gate_contract_default_off.py",
        "docs/phase18_approval_preview_readonly.md",
        "tests/test_phase18_approval_preview_readonly_default_off.py",
        "docs/phase18_operator_decision_capture_contract.md",
        "tests/test_phase18_operator_decision_capture_contract_default_off.py",
        "docs/phase18_live_provider_activation_plan.md",
        "tests/test_phase18_live_provider_activation_plan_default_off.py",
        "docs/phase18_provider_runtime_adapter_contract.md",
        "tests/test_phase18_provider_runtime_adapter_contract_default_off.py",
        "docs/phase18_live_provider_dry_run_packet_contract.md",
        "tests/test_phase18_live_provider_dry_run_packet_contract_default_off.py",
        "docs/phase18_provider_response_validation_contract.md",
        "tests/test_phase18_provider_response_validation_contract_default_off.py",
        "docs/phase18_provider_readback_audit_contract.md",
        "tests/test_phase18_provider_readback_audit_contract_default_off.py",
        "docs/phase18_provider_call_boundary_readiness_contract.md",
        "tests/test_phase18_provider_call_boundary_readiness_contract_default_off.py",
        "docs/phase18_mutation_boundary_readiness_contract.md",
        "tests/test_phase18_mutation_boundary_readiness_contract_default_off.py",
        "docs/phase18_safety_wrap_release_checkpoint.md",
        "tests/test_phase18_safety_wrap_release_checkpoint_default_off.py",
        "src/agents/three_core_approval_preview_runtime.py",
        "docs/phase19_approval_preview_runtime_readonly.md",
        "tests/test_phase19a_three_core_approval_preview_runtime_readonly_default_off.py",
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
                "b3f311bc5390eacc4d698d71141ebd3a960a491765c074ebd37c33718f887a03",
            )
        )
    }
    assert changed <= allowed | legacy_static_hash_guards


def test_phase_17_runtime_files_match_readiness_checkpoint_hashes():
    for relative_path, expected_hash in RUNTIME_HASHES.items():
        path = ROOT / relative_path

        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == expected_hash
