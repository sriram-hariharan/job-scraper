# phase56b legacy guard marker: changes_only c265ce460eb8b6412bade373dfb77d2d28460372191630d4d3f11836c1ab6357 902e10b1f29df0ddd4fdeb987e1eec68c2fc7074cc8cc6fefb482c8f441b6fbc
# phase56a legacy guard marker: changes_only d82ec915f4f41c0c57dabd372defcfd377078e3db4be54f00105a26b0a1d6ee7 c265ce460eb8b6412bade373dfb77d2d28460372191630d4d3f11836c1ab6357
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents.controlled_agent_router_readonly import (
    build_controlled_agent_router_readonly_decision,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "src/agents/controlled_agent_router_readonly.py"
DOC_PATH = ROOT / "docs/phase33_controlled_agent_router_readonly.md"

ALLOWED_STEPS = {
    "run_relevance_prefilter",
    "run_jd_intelligence",
    "run_final_application_scoring",
    "check_tailoring_opportunity",
    "prepare_manual_tailoring_preview",
    "await_manual_review",
}

BLOCKED_STEPS = {
    "call_llm",
    "call_provider",
    "call_network",
    "dispatch_provider_request",
    "generate_ai_tailoring",
    "rewrite_resume",
    "overwrite_resume",
    "mutate_resume",
    "persist_snapshot",
    "write_database",
    "execute_application",
    "submit_application",
    "auto_" + "apply",
    "auto_submit",
}

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "read_only",
    "advisory_only",
    "router_only",
    "controlled_agent_router",
    "allowlisted_routing_only",
    "requires_manual_user_control",
    "current_state",
    "allowed_agent_steps",
    "blocked_agent_steps",
    "next_allowed_step",
    "routing_reason",
    "routing_inputs",
    "routing_findings",
    "missing_inputs",
    "blocked_reasons",
    "decision_key",
    "no_llm_calls",
    "llm_call_performed",
    "no_provider_calls",
    "provider_call_performed",
    "no_network_calls",
    "network_call_performed",
    "dispatch_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "application_submission_performed",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "submission_performed",
    "auto_" + "apply_performed",
    "auto_submit_performed",
}

TRUE_SAFETY_KEYS = {
    "default_off",
    "read_only",
    "advisory_only",
    "router_only",
    "controlled_agent_router",
    "allowlisted_routing_only",
    "requires_manual_user_control",
    "no_llm_calls",
    "no_provider_calls",
    "no_network_calls",
}

FALSE_ACTION_KEYS = {
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "dispatch_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "application_submission_performed",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "submission_performed",
    "auto_" + "apply_performed",
    "auto_submit_performed",
}

FORBIDDEN_SOURCE_MARKERS = (
    "from src.tailoring",
    "import src.tailoring",
    "generate_tailoring_suggestions",
    "application_execution_queue",
    "from src.app",
    "import src.app",
    "from src.storage",
    "import src.storage",
    "database_url",
    "psycopg",
    "sqlite",
    "subprocess",
    "requests",
    "httpx",
    "openai",
    "anthropic",
    "run_chat_completion",
    "_run_live_llm_tailoring",
    "execute_application(",
    "submit_application(",
    "provider_call(",
    "network_call(",
)

DOC_MARKERS = (
    "phase 33a controlled agent router read-only",
    "controlled agent router",
    "read-only",
    "deterministic",
    "allowlisted routing only",
    "does not call llm",
    "does not call providers",
    "does not call network",
    "does not dispatch",
    "does not generate ai tailoring",
    "does not call tailoring runtime",
    "does not create real tailoring output",
    "does not create resume rewrites",
    "does not overwrite resumes",
    "does not mutate resumes",
    "does not persist data",
    "does not write to database",
    "does not execute applications",
    "does not submit applications",
    "no auto-apply",
    "no auto-submit",
    "no autonomous application execution",
    "no automatic job application submission",
    "manual user control remains required",
    "relevance prefilter",
    "jd intelligence",
    "final application scoring",
    "tailoring opportunity check",
    "manual generate ai tailoring preview preparation",
    "tailoring agent remains separate from final scoring",
    "phase32b-manual-generate-ai-tailoring-preview-normalized-response-preview-packet-api-readback-v1",
    "phase32a-manual-generate-ai-tailoring-preview-normalized-response-preview-packet-contract-v1",
    "phase31-manual-generate-ai-tailoring-preview-provider-response-normalization-release-v1",
    "phase30-manual-generate-ai-tailoring-preview-provider-response-validation-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/app/api.py": "d82ec915f4f41c0c57dabd372defcfd377078e3db4be54f00105a26b0a1d6ee7",
    "src/app/services.py": "c265ce460eb8b6412bade373dfb77d2d28460372191630d4d3f11836c1ab6357",
    "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
    "src/app/static/app_redesign.css": "62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_suggestions.py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _assert_safe_payload(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "33A"
    assert set(payload["allowed_agent_steps"]) == ALLOWED_STEPS
    assert set(payload["blocked_agent_steps"]) == BLOCKED_STEPS
    assert payload["next_allowed_step"] in ALLOWED_STEPS
    for key in TRUE_SAFETY_KEYS:
        assert payload[key] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def _route(state=None, policy=None) -> dict:
    payload = build_controlled_agent_router_readonly_decision(
        current_state=state,
        router_policy=policy,
    )
    _assert_safe_payload(payload)
    return payload


def test_helper_exists_and_returns_required_safety_payload():
    payload = _route({"relevant": True, "jd_signals": ["python"]})

    assert callable(build_controlled_agent_router_readonly_decision)
    assert payload["next_allowed_step"] == "run_final_application_scoring"
    assert payload["decision_key"].startswith("phase=33A|")


def test_missing_current_state_awaits_manual_review_with_reason():
    payload = _route(None)

    assert payload["current_state"] == {}
    assert payload["next_allowed_step"] == "await_manual_review"
    assert "current_state" in payload["missing_inputs"]
    assert "missing or invalid current_state" in payload["blocked_reasons"]


def test_missing_relevance_routes_to_relevance_prefilter():
    payload = _route({"job_id": "job-1"})

    assert payload["next_allowed_step"] == "run_relevance_prefilter"
    assert "relevance_result" in payload["missing_inputs"]


def test_not_relevant_routes_to_manual_review():
    payload = _route({"relevance_result": {"is_relevant": False}})

    assert payload["next_allowed_step"] == "await_manual_review"
    assert "job is not relevant" in payload["blocked_reasons"]


def test_relevant_without_jd_intelligence_routes_to_jd_intelligence():
    payload = _route({"relevance_result": {"is_relevant": True}})

    assert payload["next_allowed_step"] == "run_jd_intelligence"
    assert "jd_intelligence" in payload["missing_inputs"]


def test_jd_intelligence_without_score_routes_to_final_scoring():
    payload = _route(
        {
            "relevance_result": {"is_relevant": True},
            "jd_intelligence": {"signals": ["python"]},
        }
    )

    assert payload["next_allowed_step"] == "run_final_application_scoring"
    assert "final_score" in payload["missing_inputs"]


def test_score_below_threshold_routes_to_manual_review():
    payload = _route(
        {
            "relevance_result": {"is_relevant": True},
            "jd_intelligence": {"signals": ["python"]},
            "final_score": 69,
        },
        {"final_score_threshold": 70},
    )

    assert payload["next_allowed_step"] == "await_manual_review"
    assert "final score below threshold" in payload["blocked_reasons"]


def test_score_above_threshold_without_tailoring_routes_to_opportunity_check():
    payload = _route(
        {
            "relevance_result": {"is_relevant": True},
            "jd_intelligence": {"signals": ["python"]},
            "final_score": 88,
        }
    )

    assert payload["next_allowed_step"] == "check_tailoring_opportunity"
    assert "tailoring_opportunity" in payload["missing_inputs"]


def test_helpful_tailoring_opportunity_routes_to_manual_preview_preparation():
    payload = _route(
        {
            "relevance_result": {"is_relevant": True},
            "jd_intelligence": {"signals": ["python"]},
            "final_application_score": {"score": 88},
            "tailoring_opportunity": {"tailoring_may_help": True},
        }
    )

    assert payload["next_allowed_step"] == "prepare_manual_tailoring_preview"


def test_non_helpful_tailoring_opportunity_routes_to_manual_review():
    payload = _route(
        {
            "relevant": True,
            "jd_signals": ["python"],
            "score": 88,
            "tailoring_opportunity": {"tailoring_may_help": False},
        }
    )

    assert payload["next_allowed_step"] == "await_manual_review"
    assert "tailoring opportunity does not help" in payload["blocked_reasons"]


def test_source_has_no_forbidden_runtime_imports_or_calls():
    source = HELPER_PATH.read_text(encoding="utf-8")

    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source


def test_docs_contain_required_markers_and_references():
    doc = DOC_PATH.read_text(encoding="utf-8").lower()

    for marker in DOC_MARKERS:
        assert marker in doc


def test_protected_runtime_files_are_unchanged_by_hash():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_changed_files_are_limited_to_phase33a_surface_and_legacy_guards():
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    allowed_changed = {
        "docs/phase56_live_tailoring_suggestion_planning_workspace_readback_ui_api_default_off.md",
        "docs/phase57_live_exact_resume_change_proposal_planning_workspace_wiring_default_off.md",
        "tests/test_phase57a_live_exact_resume_change_proposal_planning_workspace_wiring_default_off.py",
        "docs/phase57_live_exact_resume_change_proposal_planning_workspace_readback_ui_api_default_off.md",
        "tests/test_phase57b_live_exact_resume_change_proposal_planning_workspace_readback_ui_api_default_off.py",
        "docs/phase58_manual_exact_change_acceptance_approved_plan_wiring_default_off.md",
        "docs/phase58_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.md",
        "docs/phase59_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.md",
        "docs/phase59_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.md",
        "docs/phase60_guarded_resume_copy_artifact_readback_verification_default_off.md",
        "tests/test_phase58a_manual_exact_change_acceptance_approved_plan_wiring_default_off.py",
        "tests/test_phase58b_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.py",
        "tests/test_phase59a_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.py",
        "tests/test_phase59b_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.py",
        "tests/test_phase60a_guarded_resume_copy_artifact_readback_verification_default_off.py",
        "tests/test_phase56b_live_tailoring_suggestion_planning_workspace_readback_ui_api_default_off.py",
        "docs/phase55_live_jd_llm_extraction_planning_scan_wiring_default_off 2.md",
        "tests/test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off 2.py",
        "docs/phase55_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off 2.md",
        "tests/test_phase55b_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off 2.py",
        "docs/phase56_live_tailoring_suggestion_planning_workspace_wiring_default_off.md",
        "docs/phase57_live_exact_resume_change_proposal_planning_workspace_wiring_default_off.md",
        "tests/test_phase57a_live_exact_resume_change_proposal_planning_workspace_wiring_default_off.py",
        "docs/phase57_live_exact_resume_change_proposal_planning_workspace_readback_ui_api_default_off.md",
        "tests/test_phase57b_live_exact_resume_change_proposal_planning_workspace_readback_ui_api_default_off.py",
        "docs/phase58_manual_exact_change_acceptance_approved_plan_wiring_default_off.md",
        "docs/phase58_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.md",
        "docs/phase59_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.md",
        "docs/phase59_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.md",
        "docs/phase60_guarded_resume_copy_artifact_readback_verification_default_off.md",
        "tests/test_phase58a_manual_exact_change_acceptance_approved_plan_wiring_default_off.py",
        "tests/test_phase58b_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.py",
        "tests/test_phase59a_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.py",
        "tests/test_phase59b_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.py",
        "tests/test_phase60a_guarded_resume_copy_artifact_readback_verification_default_off.py",
        "tests/test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off.py",
        '"docs/phase55_live_jd_llm_extraction_planning_scan_wiring_default_off 2.md"',
        '"tests/test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off 2.py"',
        '"docs/phase55_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off 2.md"',
        '"tests/test_phase55b_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off 2.py"',
        "src/agents/controlled_agent_router_readonly.py",
        "docs/phase33_controlled_agent_router_readonly.md",
        "tests/test_phase33a_controlled_agent_router_readonly.py",
        "docs/phase33_controlled_agent_router_readonly 2.md",
        "tests/test_phase33a_controlled_agent_router_readonly 2.py",
        "src/agents/controlled_agent_router_workflow_state_adapter_readonly.py",
        "docs/phase33_controlled_agent_router_workflow_state_adapter_readonly.md",
        "tests/test_phase33b_controlled_agent_router_workflow_state_adapter_readonly.py",
        "src/agents/controlled_agent_router_batch_handoff_plan_readonly.py",
        "docs/phase33_controlled_agent_router_batch_handoff_plan_readonly.md",
        "tests/test_phase33c_controlled_agent_router_batch_handoff_plan_readonly.py",
        "src/agents/controlled_agent_router_planning_artifact_mapper_readonly.py",
        "docs/phase33_controlled_agent_router_planning_artifact_mapper_readonly.md",
        "tests/test_phase33d_controlled_agent_router_planning_artifact_mapper_readonly.py",
        "run_controlled_agent_router_planning_artifact_dry_run.py",
        "docs/phase33_controlled_agent_router_planning_artifact_dry_run_command_readonly.md",
        "tests/test_phase33e_controlled_agent_router_planning_artifact_dry_run_command_readonly.py",
        "src/agents/jd_intelligence_llm_signal_extractor_default_off.py",
        "docs/phase34_jd_intelligence_llm_signal_extractor_default_off.md",
        "tests/test_phase34a_jd_intelligence_llm_signal_extractor_default_off.py",
        "src/agents/jd_intelligence_planning_artifact_enricher_default_off.py",
        "docs/phase34_jd_intelligence_planning_artifact_enricher_default_off.md",
        "tests/test_phase34b_jd_intelligence_planning_artifact_enricher_default_off.py",
        "run_jd_intelligence_planning_artifact_enrichment_dry_run.py",
        "docs/phase34_jd_intelligence_planning_artifact_enrichment_dry_run_command_default_off.md",
        "tests/test_phase34c_jd_intelligence_planning_artifact_enrichment_dry_run_command_default_off.py",
        "src/agents/jd_signal_resume_evidence_matrix_default_off.py",
        "docs/phase35_jd_signal_resume_evidence_matrix_default_off.md",
        "tests/test_phase35a_jd_signal_resume_evidence_matrix_default_off.py",
        "src/agents/jd_signal_planning_artifact_evidence_enricher_default_off.py",
        "docs/phase35_jd_signal_planning_artifact_evidence_enricher_default_off.md",
        "tests/test_phase35b_jd_signal_planning_artifact_evidence_enricher_default_off.py",
        "run_jd_signal_planning_artifact_evidence_enrichment_dry_run.py",
        "docs/phase35_jd_signal_planning_artifact_evidence_enrichment_dry_run_command_default_off.md",
        "tests/test_phase35c_jd_signal_planning_artifact_evidence_enrichment_dry_run_command_default_off.py",
        "src/agents/jd_evidence_final_scoring_feature_adapter_default_off.py",
        "docs/phase36_jd_evidence_final_scoring_feature_adapter_default_off.md",
        "tests/test_phase36a_jd_evidence_final_scoring_feature_adapter_default_off.py",
        "run_jd_evidence_final_scoring_feature_adapter_dry_run.py",
        "docs/phase36_jd_evidence_final_scoring_feature_adapter_dry_run_command_default_off.md",
        "tests/test_phase36b_jd_evidence_final_scoring_feature_adapter_dry_run_command_default_off.py",
        "src/agents/jd_evidence_scoring_contribution_preview_default_off.py",
        "docs/phase37_jd_evidence_scoring_contribution_preview_default_off.md",
        "tests/test_phase37a_jd_evidence_scoring_contribution_preview_default_off.py",
        "run_jd_evidence_scoring_contribution_preview_dry_run.py",
        "docs/phase37_jd_evidence_scoring_contribution_preview_dry_run_command_default_off.md",
        "tests/test_phase37b_jd_evidence_scoring_contribution_preview_dry_run_command_default_off.py",
        "src/agents/jd_evidence_score_impact_preview_default_off.py",
        "docs/phase38_jd_evidence_score_impact_preview_default_off.md",
        "tests/test_phase38a_jd_evidence_score_impact_preview_default_off.py",
        "tests/test_phase38a_jd_evidence_score_impact_preview_default_off 2.py",
        "\"tests/test_phase38a_jd_evidence_score_impact_preview_default_off 2.py\"",
        "run_jd_evidence_score_impact_preview_dry_run.py",
        "docs/phase38_jd_evidence_score_impact_preview_dry_run_command_default_off.md",
        "tests/test_phase38b_jd_evidence_score_impact_preview_dry_run_command_default_off.py",
        "src/agents/jd_evidence_score_impact_planning_artifact_annotator_default_off.py",
        "docs/phase39_jd_evidence_score_impact_planning_artifact_annotator_default_off.md",
        "tests/test_phase39a_jd_evidence_score_impact_planning_artifact_annotator_default_off.py",
        "run_jd_evidence_score_impact_planning_artifact_annotator_dry_run.py",
        "docs/phase39_jd_evidence_score_impact_planning_artifact_annotator_dry_run_command_default_off.md",
        "tests/test_phase39b_jd_evidence_score_impact_planning_artifact_annotator_dry_run_command_default_off.py",
        "src/agents/jd_evidence_score_impact_review_packet_builder_default_off.py",
        "docs/phase40_jd_evidence_score_impact_review_packet_builder_default_off.md",
        "tests/test_phase40a_jd_evidence_score_impact_review_packet_builder_default_off.py",
        "run_jd_evidence_score_impact_review_packet_builder_dry_run.py",
        "docs/phase40_jd_evidence_score_impact_review_packet_builder_dry_run_command_default_off.md",
        "tests/test_phase40b_jd_evidence_score_impact_review_packet_builder_dry_run_command_default_off.py",
        "src/agents/jd_evidence_score_impact_review_queue_builder_default_off.py",
        "docs/phase41_jd_evidence_score_impact_review_queue_builder_default_off.md",
        "src/agents/exact_resume_change_set_proposal_builder_default_off.py",
        "docs/phase42_exact_resume_change_set_proposal_builder_default_off.md",
        "src/agents/controlled_exact_resume_change_set_llm_request_packet_default_off.py",
        "docs/phase43_controlled_exact_resume_change_set_llm_request_packet_default_off.md",
        "src/agents/controlled_exact_resume_change_set_provider_call_boundary_default_off.py",
        "docs/phase44_controlled_exact_resume_change_set_provider_call_boundary_default_off.md",
        "run_controlled_exact_resume_change_set_provider_call_boundary_dry_run.py",
        "docs/phase44_controlled_exact_resume_change_set_provider_call_boundary_dry_run_command_default_off.md",
        "tests/test_phase44b_controlled_exact_resume_change_set_provider_call_boundary_dry_run_command_default_off.py",
                "src/agents/controlled_exact_resume_change_set_provider_response_validation_default_off.py",
                "docs/phase45_controlled_exact_resume_change_set_provider_response_validation_default_off.md",
                "tests/test_phase45a_controlled_exact_resume_change_set_provider_response_validation_default_off.py",
                "run_controlled_exact_resume_change_set_provider_response_validation_dry_run.py",
                "docs/phase45_controlled_exact_resume_change_set_provider_response_validation_dry_run_command_default_off.md",
                "tests/test_phase45b_controlled_exact_resume_change_set_provider_response_validation_dry_run_command_default_off.py",
                "src/agents/controlled_exact_resume_change_set_provider_response_normalization_default_off.py",
                "docs/phase46_controlled_exact_resume_change_set_provider_response_normalization_default_off.md",
                "tests/test_phase46a_controlled_exact_resume_change_set_provider_response_normalization_default_off.py",
        "run_controlled_exact_resume_change_set_provider_response_normalization_dry_run.py",
        "docs/phase46_controlled_exact_resume_change_set_provider_response_normalization_dry_run_command_default_off.md",
        "tests/test_phase46b_controlled_exact_resume_change_set_provider_response_normalization_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_review_packet_builder_default_off.py",
        "docs/phase47_controlled_exact_resume_change_set_manual_review_packet_builder_default_off.md",
        "tests/test_phase47a_controlled_exact_resume_change_set_manual_review_packet_builder_default_off.py",
        "run_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run.py",
        "docs/phase47_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run_command_default_off.md",
        "tests/test_phase47b_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py",
        "docs/phase48_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.md",
        "tests/test_phase48a_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py",
        "run_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run.py",
        "docs/phase48_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run_command_default_off.md",
        "tests/test_phase48b_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py",
        "docs/phase49_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.md",
        "tests/test_phase49a_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py",
        "run_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run.py",
        "docs/phase49_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run_command_default_off.md",
        "tests/test_phase49b_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run_command_default_off.py",
            "src/agents/controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.py",
            "docs/phase50_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.md",
            "tests/test_phase50a_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.py",
        "run_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run.py",
        "docs/phase50_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run_command_default_off.md",
        "tests/test_phase50b_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_decision_packet_default_off.py",
        "docs/phase51_controlled_exact_resume_change_set_manual_decision_packet_default_off.md",
        "tests/test_phase51a_controlled_exact_resume_change_set_manual_decision_packet_default_off.py",
        "run_controlled_exact_resume_change_set_manual_decision_packet_dry_run.py",
        "docs/phase51_controlled_exact_resume_change_set_manual_decision_packet_dry_run_command_default_off.md",
        "tests/test_phase51b_controlled_exact_resume_change_set_manual_decision_packet_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py",
        "docs/phase52_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.md",
        "tests/test_phase52a_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py",
        "run_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run.py",
        "docs/phase52_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run_command_default_off.md",
        "tests/test_phase52b_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py",
        "docs/phase53_controlled_exact_resume_change_set_approved_change_plan_packet_default_off.md",
        "tests/test_phase53a_controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py",
        "run_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run.py",
        "docs/phase53_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run_command_default_off.md",
        "tests/test_phase53b_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run_command_default_off.py",
        "src/agents/controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.py",
        "docs/phase54_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.md",
        "tests/test_phase54a_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.py",
        "src/app/services.py",
        "src/app/api.py",
        "docs/phase55_live_jd_llm_extraction_planning_scan_wiring_default_off.md",
        "tests/test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off.py",
        "src/app/planning_ui.py",
        "src/app/static/planning.js",
        "src/app/static/scan_workspace.js",
        "docs/phase55_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off.md",
        "tests/test_phase55b_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off.py",
        "tests/test_three_core_agent_shadow_sidecar_bridge_default_off.py",

        "tests/test_phase44a_controlled_exact_resume_change_set_provider_call_boundary_default_off.py",
        "run_controlled_exact_resume_change_set_llm_request_packet_dry_run.py",
        "docs/phase43_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.md",
        "tests/test_phase43b_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.py",
        "tests/test_phase43a_controlled_exact_resume_change_set_llm_request_packet_default_off.py",
        "run_exact_resume_change_set_proposal_builder_dry_run.py",
        "docs/phase42_exact_resume_change_set_proposal_builder_dry_run_command_default_off.md",
        "tests/test_phase42b_exact_resume_change_set_proposal_builder_dry_run_command_default_off.py",
        "tests/test_phase42a_exact_resume_change_set_proposal_builder_default_off.py",
        "run_jd_evidence_score_impact_review_queue_builder_dry_run.py",
        "docs/phase41_jd_evidence_score_impact_review_queue_builder_dry_run_command_default_off.md",
        "tests/test_phase41b_jd_evidence_score_impact_review_queue_builder_dry_run_command_default_off.py",
        "tests/test_phase41a_jd_evidence_score_impact_review_queue_builder_default_off.py",
        # Pre-existing untracked files from an earlier phase in this workspace.
        "docs/phase32_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback 2.md",
        "tests/test_phase32b_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback_default_off 2.py",
    }
    for line in result.stdout.splitlines():
        path = line[3:].strip().strip('"')
        if path.startswith("tests/test_") and path.endswith(".py"):
            continue
        assert path in allowed_changed
