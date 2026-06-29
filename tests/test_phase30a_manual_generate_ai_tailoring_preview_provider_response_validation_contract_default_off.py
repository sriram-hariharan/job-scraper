from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents.manual_generate_ai_tailoring_preview_provider_response_validation_contract import (
    build_manual_generate_ai_tailoring_preview_provider_response_validation_contract,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/manual_generate_ai_tailoring_preview_provider_response_validation_contract.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_contract.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "provider_response_validation_contract_only",
    "response_validation_only",
    "requires_user_trigger",
    "user_trigger_present",
    "operator_confirmation_required",
    "operator_confirmation_present",
    "manual_acceptance_required",
    "provider_call_dry_run_packet_required",
    "provider_call_dry_run_packet_accepted",
    "provider_request_envelope_required",
    "provider_request_envelope_accepted",
    "provider_response_candidate_required",
    "provider_response_candidate_present",
    "response_validation_policy_required",
    "response_validation_policy_present",
    "provider_configuration_required",
    "provider_configuration_present",
    "response_validation_ready",
    "provider_response_accepted_for_future_manual_preview",
    "blocked_reasons",
    "missing_inputs",
    "validation_findings",
    "provider_response_contract",
    "deterministic_response_validation_key",
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
    "auto_apply_performed",
    "auto_submit_performed",
    "next_safe_step",
}

TRUE_SAFETY_KEYS = {
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "provider_response_validation_contract_only",
    "response_validation_only",
    "requires_user_trigger",
    "operator_confirmation_required",
    "manual_acceptance_required",
    "provider_call_dry_run_packet_required",
    "provider_request_envelope_required",
    "provider_response_candidate_required",
    "response_validation_policy_required",
    "provider_configuration_required",
    "no_provider_calls",
    "no_network_calls",
}

FALSE_ACTION_KEYS = {
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
    "auto_apply_performed",
    "auto_submit_performed",
}

PROTECTED_HASHES = {
    "src/app/api.py": "dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
    "src/app/static/app_redesign.css": "62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c",
    "src/agents/manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.py": "26340a75114c6e1d3d909be3dfb6ddde1997578268ce966fda634c645c630fa6",
    "src/agents/manual_generate_ai_tailoring_preview_provider_call_boundary_contract.py": "8e4b2a93d535f37387283b943d4a31fc3ff1c23016d2958132e2362a74f97f7b",
    "src/agents/manual_generate_ai_tailoring_preview_provider_request_envelope_contract.py": "e1c9f6f55b7d8a8c0171b52d7e891d531aae0ad3384eb74d686f50ba4e59533f",
    "src/agents/manual_generate_ai_tailoring_preview_dispatch_boundary_contract.py": "2fdc984c5ee395d43e71fd2ce991b9575316f8714188cc16a13c97c73074996f",
    "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py": "4e0dcc111f114551b0ce1c88f8d57618546306c4bcce8ac2d6df86b44cbfa60d",
    "src/agents/manual_generate_ai_tailoring_preview_contract.py": "98e2c69010061fa8e98cf50541f88537ad9eaff72c7c13a270e57822196eeb45",
    "src/agents/generate_ai_tailoring_action_boundary_contract.py": "5c7675f889daa3342258be5d8eac5c191b196a84795238c658eb73cb76672953",
    "src/agents/tailoring_agent_opportunity_contract.py": "e61e910176a315e11b2e403a33920a53726c9df8ed0213f0121b5c6eb0c1d8b3",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_suggestions.py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
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
    "execute_application",
    "submit_application",
    "provider_call(",
    "network_call(",
)

DOC_MARKERS = (
    "phase 30a manual generate ai tailoring preview provider response validation contract",
    "provider response validation contract only",
    "response validation only",
    "default-off",
    "read-only",
    "advisory-only",
    "manual-review only",
    "user trigger required",
    "operator confirmation required",
    "manual acceptance required",
    "provider-call dry-run packet required",
    "provider request-envelope required",
    "provider response candidate required",
    "response validation policy required",
    "provider configuration required",
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
    "no provider calls",
    "no network calls",
    "no database writes",
    "no persistence",
    "no mutation",
    "no resume mutation",
    "no application mutation",
    "no execution",
    "no submission",
    "no auto-apply",
    "no auto-submit",
    "no autonomous application execution",
    "no automatic job application submission",
    "tailoring agent remains separate from final scoring",
    "generated tailoring suggestions must remain preview/manual-review only unless user accepts edits in a later phase",
    "this phase does not create real tailoring output",
    "this phase does not add a ui action control",
    "phase29-manual-generate-ai-tailoring-preview-provider-call-dry-run-packet-release-v1",
    "phase29d-manual-generate-ai-tailoring-preview-provider-call-dry-run-packet-release-checkpoint-v1",
    "phase29c-manual-generate-ai-tailoring-preview-provider-call-dry-run-packet-ui-readback-v1",
    "phase29b-manual-generate-ai-tailoring-preview-provider-call-dry-run-packet-api-readback-v1",
    "phase29a-manual-generate-ai-tailoring-preview-provider-call-dry-run-packet-contract-v1",
    "phase28-manual-generate-ai-tailoring-preview-provider-call-boundary-release-v1",
    "phase27-manual-generate-ai-tailoring-preview-provider-request-envelope-release-v1",
    "phase26-manual-generate-ai-tailoring-preview-dispatch-boundary-release-v1",
    "phase25-manual-generate-ai-tailoring-preview-request-packet-release-v1",
    "phase24-manual-generate-ai-tailoring-preview-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _ready_inputs() -> dict[str, dict]:
    return {
        "provider_response_candidate_payload": {
            "response_id": "manual-review-response-stub",
            "status": "sample_response_shape",
            "choices_present": True,
        },
        "phase29_provider_call_dry_run_packet_payload": {
            "dry_run_packet_ready": True,
            "provider_call_allowed_for_future_manual_preview": True,
            "provider_call_performed": False,
            "network_call_performed": False,
            "dispatch_performed": False,
            "tailoring_runtime_call_performed": False,
            "ai_tailoring_generation_performed": False,
            "real_tailoring_output_created": False,
            "execution_performed": False,
            "submission_performed": False,
            "dry_run_packet": {
                "dry_run_packet_ready": True,
                "deterministic_dry_run_packet_key": (
                    "manual-generate-ai-tailoring-preview-provider-dry-run-example"
                ),
            },
        },
        "phase28_provider_call_boundary_payload": {
            "provider_call_boundary_ready": True,
            "provider_call_allowed": True,
        },
        "phase27_provider_request_envelope_payload": {
            "provider_request_envelope_ready": True,
            "provider_request_allowed": True,
            "provider_call_performed": False,
            "network_call_performed": False,
            "tailoring_runtime_call_performed": False,
            "ai_tailoring_generation_performed": False,
            "real_tailoring_output_created": False,
            "execution_performed": False,
            "submission_performed": False,
        },
        "user_trigger_metadata": {
            "user_triggered": True,
            "generate_ai_tailoring_requested": True,
        },
        "operator_confirmation_metadata": {
            "operator_confirmed": True,
            "provider_response_validation_confirmed": True,
        },
        "response_validation_policy_metadata": {
            "response_validation_policy_present": True,
            "response_validation_policy_id": "manual-review-response-policy",
        },
        "provider_configuration_metadata": {
            "provider_configuration_present": True,
            "provider_name": "manual-review-provider-stub",
            "model": "manual-review-model-stub",
        },
    }


def test_helper_exists_and_returns_required_keys():
    result = (
        build_manual_generate_ai_tailoring_preview_provider_response_validation_contract()
    )

    assert result["phase"] == "30A"
    assert REQUIRED_KEYS <= result.keys()
    for key in TRUE_SAFETY_KEYS:
        assert result[key] is True
    for key in FALSE_ACTION_KEYS:
        assert result[key] is False
    assert result["response_validation_ready"] is False
    assert result["provider_response_accepted_for_future_manual_preview"] is False


def test_no_user_trigger_blocks_response_validation():
    inputs = _ready_inputs()
    inputs["user_trigger_metadata"] = {}

    result = (
        build_manual_generate_ai_tailoring_preview_provider_response_validation_contract(
            **inputs
        )
    )

    assert result["response_validation_ready"] is False
    assert "user_trigger_metadata" in result["missing_inputs"]
    assert "explicit user trigger required" in result["blocked_reasons"]
    assert result["next_safe_step"] == "require_explicit_user_trigger"


def test_missing_operator_confirmation_blocks_response_validation():
    inputs = _ready_inputs()
    inputs["operator_confirmation_metadata"] = {}

    result = (
        build_manual_generate_ai_tailoring_preview_provider_response_validation_contract(
            **inputs
        )
    )

    assert result["response_validation_ready"] is False
    assert "operator_confirmation_metadata" in result["missing_inputs"]
    assert "operator confirmation required" in result["blocked_reasons"]
    assert result["next_safe_step"] == "require_operator_confirmation"


def test_missing_or_blocked_dry_run_packet_blocks_response_validation():
    missing = (
        build_manual_generate_ai_tailoring_preview_provider_response_validation_contract(
            **{
                **_ready_inputs(),
                "phase29_provider_call_dry_run_packet_payload": {},
            }
        )
    )
    blocked = (
        build_manual_generate_ai_tailoring_preview_provider_response_validation_contract(
            **{
                **_ready_inputs(),
                "phase29_provider_call_dry_run_packet_payload": {
                    "dry_run_packet_ready": False,
                    "provider_call_allowed_for_future_manual_preview": False,
                },
            }
        )
    )

    assert missing["response_validation_ready"] is False
    assert "phase29_provider_call_dry_run_packet_payload" in missing[
        "missing_inputs"
    ]
    assert "phase29 provider-call dry-run packet required" in missing[
        "blocked_reasons"
    ]
    assert blocked["response_validation_ready"] is False
    assert (
        "provider-call dry-run packet must be accepted before response validation"
        in blocked["blocked_reasons"]
    )


def test_missing_or_unaccepted_provider_request_envelope_blocks_validation():
    missing = (
        build_manual_generate_ai_tailoring_preview_provider_response_validation_contract(
            **{
                **_ready_inputs(),
                "phase27_provider_request_envelope_payload": {},
            }
        )
    )
    blocked = (
        build_manual_generate_ai_tailoring_preview_provider_response_validation_contract(
            **{
                **_ready_inputs(),
                "phase27_provider_request_envelope_payload": {
                    "provider_request_envelope_ready": False,
                    "provider_request_allowed": False,
                },
            }
        )
    )

    assert missing["response_validation_ready"] is False
    assert "phase27_provider_request_envelope_payload" in missing[
        "missing_inputs"
    ]
    assert "phase27 provider request-envelope payload required" in missing[
        "blocked_reasons"
    ]
    assert blocked["response_validation_ready"] is False
    assert (
        "provider request-envelope must be accepted before response validation"
        in blocked["blocked_reasons"]
    )


def test_missing_candidate_policy_and_configuration_are_blocked():
    missing_candidate = (
        build_manual_generate_ai_tailoring_preview_provider_response_validation_contract(
            **{
                **_ready_inputs(),
                "provider_response_candidate_payload": {},
            }
        )
    )
    missing_policy = (
        build_manual_generate_ai_tailoring_preview_provider_response_validation_contract(
            **{
                **_ready_inputs(),
                "response_validation_policy_metadata": {},
            }
        )
    )
    missing_configuration = (
        build_manual_generate_ai_tailoring_preview_provider_response_validation_contract(
            **{
                **_ready_inputs(),
                "provider_configuration_metadata": {},
            }
        )
    )

    assert missing_candidate["response_validation_ready"] is False
    assert "provider_response_candidate_payload" in missing_candidate[
        "missing_inputs"
    ]
    assert "provider response candidate payload required" in missing_candidate[
        "blocked_reasons"
    ]
    assert missing_policy["response_validation_ready"] is False
    assert "response_validation_policy_metadata" in missing_policy[
        "missing_inputs"
    ]
    assert "response validation policy metadata required" in missing_policy[
        "blocked_reasons"
    ]
    assert missing_configuration["response_validation_ready"] is False
    assert "provider_configuration_metadata" in missing_configuration[
        "missing_inputs"
    ]
    assert "provider configuration metadata required" in missing_configuration[
        "blocked_reasons"
    ]


def test_ready_stubs_mark_validation_ready_without_side_effects():
    first = (
        build_manual_generate_ai_tailoring_preview_provider_response_validation_contract(
            **_ready_inputs()
        )
    )
    second = (
        build_manual_generate_ai_tailoring_preview_provider_response_validation_contract(
            **_ready_inputs()
        )
    )

    assert first == second
    assert first["response_validation_ready"] is True
    assert first["provider_response_accepted_for_future_manual_preview"] is True
    assert first["blocked_reasons"] == []
    assert first["missing_inputs"] == []
    assert first["provider_response_contract"]["response_validation_ready"] is True
    assert first["provider_response_contract"][
        "contains_generated_tailoring_text"
    ] is False
    assert first["provider_response_contract"][
        "contains_real_tailoring_output"
    ] is False
    assert "generated_tailoring_text" not in first["provider_response_contract"]
    assert "real_tailoring_output" not in first["provider_response_contract"]
    for key in FALSE_ACTION_KEYS:
        assert first[key] is False
    for marker in (
        "provider_call_performed",
        "network_call_performed",
        "dispatch_performed",
        "tailoring_runtime_call_performed",
        "ai_tailoring_generation_performed",
        "real_tailoring_output_created",
    ):
        assert first["provider_response_contract"][marker] is False


def test_candidate_with_tailoring_output_is_blocked_and_not_copied():
    result = (
        build_manual_generate_ai_tailoring_preview_provider_response_validation_contract(
            **{
                **_ready_inputs(),
                "provider_response_candidate_payload": {
                    "response_id": "unsafe-sample",
                    "generated_tailoring_text": "do not copy this",
                },
            }
        )
    )

    assert result["response_validation_ready"] is False
    assert (
        "provider response candidate must not include generated tailoring output"
        in result["blocked_reasons"]
    )
    assert "do not copy this" not in str(result["provider_response_contract"])


def test_helper_source_has_no_forbidden_imports_or_calls():
    source = HELPER_PATH.read_text(encoding="utf-8").lower()

    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source


def test_doc_contains_required_safety_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_phase30a_changes_only_helper_doc_test_and_legacy_guards():
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
        "src/agents/manual_generate_ai_tailoring_preview_provider_response_validation_contract.py",
        "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_contract.md",
        "tests/test_phase30a_manual_generate_ai_tailoring_preview_provider_response_validation_contract_default_off.py",
        "src/app/api.py",
        "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_api_readback.md",
        "tests/test_phase30b_manual_generate_ai_tailoring_preview_provider_response_validation_api_readback_default_off.py",
                "src/app/static/agentic_review.js",
                "src/app/static/app_redesign.css",
                "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_ui_readback.md",
                "tests/test_phase30c_manual_generate_ai_tailoring_preview_provider_response_validation_ui_readback_default_off.py",
                    "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_release_checkpoint.md",
                    "tests/test_phase30d_manual_generate_ai_tailoring_preview_provider_response_validation_release_checkpoint_default_off.py",
                        "src/agents/manual_generate_ai_tailoring_preview_provider_response_normalization_contract.py",
                        "docs/phase31_manual_generate_ai_tailoring_preview_provider_response_normalization_contract.md",
                        "tests/test_phase31a_manual_generate_ai_tailoring_preview_provider_response_normalization_contract_default_off.py",
                        "src/app/api.py",
                        "docs/phase31_manual_generate_ai_tailoring_preview_provider_response_normalization_api_readback.md",
                        "tests/test_phase31b_manual_generate_ai_tailoring_preview_provider_response_normalization_api_readback_default_off.py",
                            "docs/phase31_manual_generate_ai_tailoring_preview_provider_response_normalization_ui_readback.md",
                            "tests/test_phase31c_manual_generate_ai_tailoring_preview_provider_response_normalization_ui_readback_default_off.py",
                                "docs/phase31_manual_generate_ai_tailoring_preview_provider_response_normalization_release_checkpoint.md",
                                "tests/test_phase31d_manual_generate_ai_tailoring_preview_provider_response_normalization_release_checkpoint_default_off.py",
                                "src/agents/manual_generate_ai_tailoring_preview_normalized_response_preview_packet_contract.py",
                                "docs/phase32_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_contract.md",
                                "tests/test_phase32a_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_contract_default_off.py",
                                "src/app/api.py",
                                "docs/phase32_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback.md",
                                "tests/test_phase32b_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback_default_off.py",
                                "docs/phase32_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback 2.md",
                                "tests/test_phase32b_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback_default_off 2.py",
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
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if path != Path(__file__).resolve()
        and any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "phase30a_manual_generate_ai_tailoring_preview_provider_response_validation_contract",
                "phase30_manual_generate_ai_tailoring_preview_provider_response_validation_contract",
                "changes_only",
            )
        )
    }

    assert changed <= allowed | legacy_guards
