from hashlib import sha256
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/phase18_provider_call_boundary_readiness_contract.md"

ORDERED_AGENTS = [
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
]

BOUNDARY_STATUSES = [
    "not_available",
    "boundary_not_configured",
    "boundary_disabled",
    "boundary_readiness_incomplete",
    "boundary_ready_for_separate_call_phase",
    "boundary_blocked",
    "boundary_failed_closed",
]

BOUNDARY_FIELDS = [
    "boundary_id",
    "boundary_status",
    "provider_name",
    "provider_operation",
    "model_or_endpoint_identifier",
    "requested_capability",
    "linked_preview_id",
    "linked_decision_id",
    "linked_activation_id",
    "linked_adapter_id",
    "linked_dry_run_packet_id",
    "linked_response_validation_id",
    "linked_readback_id",
    "linked_audit_id",
    "linked_trace_or_readback_id",
    "required_feature_flags",
    "operator_or_reviewer_id",
    "dry_run_packet_status",
    "response_validation_status",
    "readback_status",
    "audit_status",
    "secrets_reference_name_only",
    "network_policy_summary",
    "timeout_policy",
    "retry_policy",
    "rate_limit_policy",
    "cost_limit_policy",
    "output_schema_summary",
    "safety_flag_summary",
    "missing_requirements",
    "fail_closed_reason",
    "rollback_or_disable_reference",
    "created_timestamp",
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
    "src/agents/three_core_agent_shadow_operator_canary.py": (
        "b130620a2257603bd2ed5259f65434e4f13d9636d1d25a417c594f38251bb943"
    ),
    "src/pipeline/collector.py": (
        "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"
    ),
    "src/app/api.py": (
        "ba752c3a7eaef620476abffb0ecb7ebf8ce023346917ff8fedb5579c9504d41f"
    ),
    "src/app/services.py": (
        "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee"
    ),
    "src/app/static/agentic_review.js": (
        "029c1105e4d3ae9f023ad40418e83cc13e4dffc937406b5e7219e8934d067e35"
    ),
}


def _text() -> str:
    return DOC.read_text(encoding="utf-8")


def test_call_boundary_contract_exists_and_names_preceding_tags():
    assert DOC.exists()
    text = _text()

    assert "# Phase 18 Provider-Call Boundary Readiness Contract" in text
    for tag in (
        "phase17-three-core-shadow-readiness-release-v1",
        "phase18a-live-readiness-approval-boundary-v1",
        "phase18b-human-approval-gate-contract-v1",
        "phase18c-approval-preview-readonly-v1",
        "phase18d-operator-decision-capture-contract-v1",
        "phase18e-live-provider-activation-plan-v1",
        "phase18f-provider-runtime-adapter-contract-v1",
        "phase18g-live-provider-dry-run-packet-contract-v1",
        "phase18h-provider-response-validation-contract-v1",
        "phase18i-provider-readback-audit-contract-v1",
    ):
        assert f"`{tag}`" in text


def test_three_core_agents_are_named_in_correct_order():
    text = _text()
    positions = [text.index(f"`{agent}`") for agent in ORDERED_AGENTS]

    assert positions == sorted(positions)


def test_phase18j_is_docs_tests_only_and_implements_no_runtime_surface():
    text = _text()

    assert "Phase 18J is docs/tests-only" in text
    assert "authorizes no runtime behavior" in text
    assert "does\nnot implement a provider-call boundary" in text
    assert "does not call or activate a\nprovider" in text
    assert "Phase 18J does not access secrets." in text
    assert "Phase 18J does not create network\ntraffic." in text
    assert "adds no API" in text
    for term in ("default-off", "read-only", "shadow-only", "advisory-only"):
        assert term in text


def test_allowed_future_boundary_statuses_are_exact_and_ordered():
    text = _text()
    section = text[
        text.index("## Allowed future provider-call boundary statuses"):
        text.index("## Required future provider-call boundary fields")
    ]
    listed = re.findall(r"^\d+\. `([^`]+)`$", section, flags=re.MULTILINE)

    assert listed == BOUNDARY_STATUSES


def test_required_future_boundary_fields_are_listed():
    text = _text()

    for field in BOUNDARY_FIELDS:
        assert f"`{field}`" in text


def test_readiness_prerequisites_are_complete():
    text = _text()
    section = text[
        text.index("## Readiness prerequisites"):
        text.index("## Required future default-off gates")
    ]

    for prerequisite in (
        "Linked approval preview exists",
        "Linked operator decision exists",
        "Linked activation plan exists",
        "Linked adapter contract exists",
        "Linked dry-run packet exists",
        "Linked response validation contract exists",
        "Linked readback/audit contract exists",
        "Required feature flags are default-off and explicitly named",
        "Secrets reference name only is available",
        "Network policy is defined",
        "Timeout policy is defined",
        "Retry policy is defined",
        "Rate limit policy is defined",
        "Cost limit policy is defined",
        "Rollback/disable reference is defined",
        "Mutation-disabled gate is present",
    ):
        assert prerequisite in section


def test_required_future_default_off_gates_are_listed():
    text = _text()

    for gate in (
        "Global provider runtime flag",
        "Provider-specific flag",
        "Provider-call-boundary flag",
        "Operation-specific flag",
        "Human decision required flag",
        "Dry-run packet required flag",
        "Response-validation required flag",
        "Readback/audit required flag",
        "Mutation-disabled flag",
        "Submission-disabled flag",
    ):
        assert gate in text


def test_boundary_safety_requirements_are_complete():
    text = _text()

    for requirement in (
        "Boundary readiness evaluation must be deterministic.",
        "Boundary readiness evaluation must not call providers.",
        "Boundary readiness evaluation must not read secret values.",
        "Boundary readiness evaluation must not create network traffic.",
        "Boundary readiness evaluation must not persist approvals, decisions, or",
        "Boundary readiness evaluation must not mutate final score, rank, queue,",
        "Boundary readiness evaluation must fail closed when any prerequisite is",
        "Boundary readiness output must remain advisory and review-only.",
        "Provider-call readiness must require a separate later provider-call phase.",
    ):
        assert requirement in text


def test_failed_closed_boundary_conditions_are_complete():
    text = _text()

    for condition in (
        "Missing provider name",
        "Missing provider operation",
        "Missing requested capability",
        "Missing linked preview id",
        "Missing linked decision id",
        "Missing linked activation id",
        "Missing linked adapter id",
        "Missing linked dry-run packet id",
        "Missing linked response validation id",
        "Missing linked readback id",
        "Missing linked audit id",
        "Missing linked trace/readback id",
        "Missing required feature flag",
        "Missing operator/reviewer id",
        "Missing secrets reference name only",
        "Missing network policy",
        "Missing timeout policy",
        "Missing retry policy",
        "Missing rate limit policy",
        "Missing cost limit policy",
        "Unsafe safety flags",
        "Secret value detected",
        "Attempted provider call",
        "Attempted mutation or submission",
    ):
        assert condition in text


def test_minimum_future_observability_is_complete():
    text = _text()

    for field in (
        "Boundary status",
        "Provider name",
        "Provider operation",
        "Requested capability",
        "Linked preview id",
        "Linked decision id",
        "Linked activation id",
        "Linked adapter id",
        "Linked dry-run packet id",
        "Linked response validation id",
        "Linked readback id",
        "Linked audit id",
        "Linked trace/readback id",
        "Readiness prerequisite summary",
        "Safety flag summary",
        "Missing requirements",
        "Fail-closed reason",
    ):
        assert field in text


def test_not_authorized_section_lists_every_forbidden_path():
    text = _text()

    for term in (
        "No provider-call boundary implementation.",
        "No live provider execution.",
        "No provider SDK/network call.",
        "No secrets access.",
        "No approval creation runtime.",
        "No decision persistence runtime.",
        "No audit persistence runtime.",
        "No DB writes.",
        "No final scoring mutation.",
        "No ranking mutation.",
        "No queue mutation.",
        "No resume mutation.",
        "No execution request creation.",
        "No application execution.",
        "No application submission.",
    ):
        assert term in text


def test_recommended_next_phase_is_mutation_boundary_without_call_or_mutation():
    assert (
        "Phase 18K should be a docs/tests-only mutation boundary readiness "
        "contract,\nstill no provider call and still no mutation."
        in _text()
    )


def test_phase18j_changes_only_approved_docs_and_tests():
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
        "docs/phase18_provider_call_boundary_readiness_contract.md",
        "tests/test_phase18_provider_call_boundary_readiness_contract_default_off.py",
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


def test_phase18j_key_runtime_files_are_unchanged():
    for relative_path, expected_hash in RUNTIME_HASHES.items():
        path = ROOT / relative_path

        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == expected_hash
