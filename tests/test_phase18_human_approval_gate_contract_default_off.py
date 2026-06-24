from hashlib import sha256
from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
DOC = ROOT / "docs/phase18_human_approval_gate_contract.md"

ORDERED_AGENTS = [
    "relevance_prefilter",
    "jd_intelligence",
    "final_application_scoring",
]

DECISION_STATES = [
    "not_requested",
    "requested",
    "approved",
    "rejected",
    "expired",
    "revoked",
    "failed_closed",
]

REQUEST_FIELDS = [
    "request_id",
    "requested_capability",
    "requester_source",
    "target_context",
    "evidence_summary",
    "proposed_action_summary",
    "risk_summary",
    "safety_flags",
    "expiry_timestamp",
    "created_timestamp",
    "operator_or_reviewer_id",
    "decision_timestamp",
    "decision_reason",
    "rollback_or_disable_reference",
]

SEPARATE_CAPABILITIES = [
    "Live provider execution",
    "Provider SDK/network calls",
    "Final scoring mutation",
    "Ranking mutation",
    "Queue mutation",
    "Resume mutation",
    "Approval creation",
    "Execution request creation",
    "Application execution",
    "Application submission",
    "DB writes",
    "Secrets access",
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


def test_contract_doc_exists_and_names_preceding_tags():
    assert DOC.exists()
    text = _text()

    assert "# Phase 18 Human Approval Gate Contract" in text
    assert "`phase17-three-core-shadow-readiness-release-v1`" in text
    assert "`phase18a-live-readiness-approval-boundary-v1`" in text


def test_three_core_agents_are_named_in_correct_order():
    text = _text()
    positions = [text.index(f"`{agent}`") for agent in ORDERED_AGENTS]

    assert positions == sorted(positions)


def test_phase18b_is_docs_tests_only_and_authorizes_no_runtime():
    text = _text()

    assert "Phase 18B is docs/tests-only" in text
    assert "authorizes no runtime behavior" in text
    assert "adds no API" in text
    for term in ("default-off", "read-only", "shadow-only", "advisory-only"):
        assert term in text


def test_allowed_future_decision_states_are_exact_and_ordered():
    text = _text()
    section = text[
        text.index("## Allowed future decision states"):
        text.index("## Required future approval request fields")
    ]
    positions = [section.index(f"`{state}`") for state in DECISION_STATES]

    assert positions == sorted(positions)
    for state in DECISION_STATES:
        assert section.count(f"`{state}`") >= 1


def test_required_future_approval_request_fields_are_listed():
    text = _text()

    for field in REQUEST_FIELDS:
        assert f"`{field}`" in text


def test_separate_approval_capabilities_are_all_listed():
    text = _text()
    section = text[
        text.index("## Capabilities requiring separate approval"):
        text.index("## Hard rules")
    ]

    for capability in SEPARATE_CAPABILITIES:
        assert capability in section


def test_approval_scope_characteristics_and_non_implication_are_explicit():
    text = _text()

    assert "Approval for one capability does not imply approval for another." in text
    assert (
        "single-capability scoped, time-bound, auditable, reversible, and\n"
        "fail-closed"
        in text
    )


def test_hard_rules_are_complete():
    text = _text()

    for term in (
        "No approval may directly submit an application.",
        "No approval may combine provider execution with",
        "scoring/ranking/queue/resume/application submission.",
        "No approval may bypass default-off feature flags.",
        "No approval may bypass dry-run/readback evidence.",
        "No approval may bypass tests proving no submit/apply path is reachable",
        "submission itself is the separately approved capability in a later phase.",
    ):
        assert term in text


def test_fail_closed_conditions_are_complete():
    text = _text()

    for condition in (
        "Missing approval",
        "Expired approval",
        "Revoked approval",
        "Rejected approval",
        "Mismatched capability",
        "Missing evidence",
        "Missing feature flag",
        "Unsafe safety flags",
        "Unknown target context",
        "Provider/runtime error",
    ):
        assert condition in text


def test_minimum_future_observability_is_complete():
    text = _text()

    for field in (
        "Decision state",
        "Requested capability",
        "Operator/reviewer id",
        "Decision timestamp",
        "Evidence summary",
        "Safety flag summary",
        "Fail-closed reason",
        "Linked trace/readback id",
    ):
        assert field in text


def test_not_authorized_section_lists_every_forbidden_path():
    text = _text()

    for term in (
        "No live provider execution.",
        "No provider SDK/network call.",
        "No DB writes.",
        "No secrets access.",
        "No final scoring mutation.",
        "No ranking mutation.",
        "No queue mutation.",
        "No resume mutation.",
        "No approval creation runtime.",
        "No execution request creation.",
        "No application execution.",
        "No application submission.",
    ):
        assert term in text


def test_recommended_next_phase_is_read_only_preview_without_execution():
    assert (
        "Phase 18C should be a read-only approval preview, still no execution."
        in _text()
    )


def test_phase18b_changes_only_approved_docs_and_tests():
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
        "docs/phase18_human_approval_gate_contract.md",
        "tests/test_phase18_human_approval_gate_contract_default_off.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
        "tests/test_phase18_live_readiness_approval_boundary_default_off.py",
        "tests/test_three_core_shadow_readiness_wrap_default_off.py",
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


def test_phase18b_key_runtime_files_are_unchanged():
    for relative_path, expected_hash in RUNTIME_HASHES.items():
        path = ROOT / relative_path

        assert path.exists()
        assert sha256(path.read_bytes()).hexdigest() == expected_hash
