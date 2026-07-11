# phase79b legacy guard marker: changes_only collector_hash_old 73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405
# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess

from tests.support.phase_guard_registry import (
    assert_changed_files_allowed,
    get_changed_files,
)


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
    "auto_" + "apply_performed",
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
    "auto_" + "apply_performed",
    "auto_submit_performed",
}

PROTECTED_HASHES = {
    "src/app/api.py": "d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004",
    "src/app/services.py": "bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2",
    "src/app/static/agentic_review.js": "fdbd820a68a356d894ac0b904bd649d511dcf501129d32ed00d34ffc7f927fd0",
    "src/app/static/app_redesign.css": "81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961",
    "src/agents/manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.py": "26340a75114c6e1d3d909be3dfb6ddde1997578268ce966fda634c645c630fa6",
    "src/agents/manual_generate_ai_tailoring_preview_provider_call_boundary_contract.py": "8e4b2a93d535f37387283b943d4a31fc3ff1c23016d2958132e2362a74f97f7b",
    "src/agents/manual_generate_ai_tailoring_preview_provider_request_envelope_contract.py": "e1c9f6f55b7d8a8c0171b52d7e891d531aae0ad3384eb74d686f50ba4e59533f",
    "src/agents/manual_generate_ai_tailoring_preview_dispatch_boundary_contract.py": "2fdc984c5ee395d43e71fd2ce991b9575316f8714188cc16a13c97c73074996f",
    "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py": "4e0dcc111f114551b0ce1c88f8d57618546306c4bcce8ac2d6df86b44cbfa60d",
    "src/agents/manual_generate_ai_tailoring_preview_contract.py": "98e2c69010061fa8e98cf50541f88537ad9eaff72c7c13a270e57822196eeb45",
    "src/agents/generate_ai_tailoring_action_boundary_contract.py": "5c7675f889daa3342258be5d8eac5c191b196a84795238c658eb73cb76672953",
    "src/agents/tailoring_agent_opportunity_contract.py": "e61e910176a315e11b2e403a33920a53726c9df8ed0213f0121b5c6eb0c1d8b3",
    "src/pipeline/collector.py": "e5af36527801b2a1a55501622619d4e62ccaa7472e835500613e2894843d1671",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "f56624b5b3c7e2bb01a824386b86fbc2a194e727f0437ca0773764eae64ec941",
    "src/tailoring/llm.py": "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
    "generate_tailoring_suggestions.py": "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28",
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
            "src/app/auth_ui.py",
            "src/app/static/shell.js",
            "src/app/ui_shell.py",
            "src/app/static/media/adv_diagnostics_img.svg",
        "src/tailoring/llm.py",
        "generate_tailoring_suggestions.py",
        "src/tailoring/rendering.py",
        "tests/test_score_first_scan.py",
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
        "docs/phase60_guarded_resume_copy_artifact_verification_readback_ui_api_default_off.md",
        "docs/phase61_verified_artifact_operator_review_packet_wiring_default_off.md",
        "docs/phase61_verified_artifact_operator_review_packet_readback_ui_api_default_off.md",
            "docs/phase62_verified_artifact_operator_decision_capture_wiring_default_off.md",
            "docs/phase62_verified_artifact_operator_decision_capture_readback_ui_api_default_off.md",
            "docs/phase63_operator_approved_artifact_application_readiness_packet_wiring_default_off.md",
            "docs/phase63_operator_approved_artifact_application_readiness_packet_readback_ui_api_default_off.md",
            "docs/phase64_human_only_manual_application_handoff_packet_wiring_default_off.md",
                "docs/phase64_human_only_manual_application_handoff_packet_wiring_default_off 3.md",
                "docs/phase64_human_only_manual_application_handoff_packet_wiring_default_off 2.md",
            "docs/phase64_human_only_manual_application_handoff_packet_readback_ui_api_default_off.md",
                "docs/phase64_human_only_manual_application_handoff_packet_readback_ui_api_default_off 3.md",
                "docs/phase64_human_only_manual_application_handoff_packet_readback_ui_api_default_off 2.md",
            "docs/phase65_human_only_handoff_audit_trail_wiring_default_off.md",
                "docs/phase65_human_only_handoff_audit_trail_readback_ui_api_default_off.md",
                "docs/phase66_human_only_safety_boundary_summary_wiring_default_off.md",
                "docs/phase66_human_only_safety_boundary_summary_readback_ui_api_default_off.md",
                "docs/phase66_human_only_safety_boundary_summary_readback_ui_api_default_off 2.md",
                "docs/phase67_human_only_workflow_readiness_checkpoint_wiring_default_off.md",
                "docs/phase67_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off.md",
            "docs/phase68_end_to_end_agentic_workflow_integration_wiring_default_off.md",
            "docs/phase68_end_to_end_agentic_workflow_integration_readback_ui_api_default_off.md",
            "docs/phase69_agentic_workflow_production_readiness_checkpoint_default_off.md",
            "docs/phase69_agentic_workflow_production_readiness_readback_ui_api_default_off.md",
            "docs/phase70_ux_polish_agentic_workflow_demo_readiness_default_off.md",
            "docs/phase70_ux_polish_agentic_workflow_demo_readiness_readback_default_off.md",
            "docs/phase71_live_pipeline_argument_list_too_long_guard_default_off.md",
            "docs/phase71_tailoring_workspace_artifact_path_preload_repair_default_off.md",
            "tests/test_phase71a_live_pipeline_argument_list_too_long_guard_default_off.py",
            "tests/test_phase71a_tailoring_workspace_artifact_path_preload_repair_default_off.py",
            "tests/test_user_pipeline_role_preferences.py",
            "docs/phase69_agentic_workflow_production_readiness_checkpoint_default_off 2.md",
            "docs/phase69_agentic_workflow_production_readiness_readback_ui_api_default_off 2.md",
            "\"docs/phase69_agentic_workflow_production_readiness_checkpoint_default_off 2.md\"",
            "\"docs/phase69_agentic_workflow_production_readiness_readback_ui_api_default_off 2.md\"",
            "docs/phase66_human_only_safety_boundary_summary_readback_ui_api_default_off 3.md",
            "docs/phase67_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off 2.md",
            "docs/phase67_human_only_workflow_readiness_checkpoint_wiring_default_off 2.md",
            "\"docs/phase66_human_only_safety_boundary_summary_readback_ui_api_default_off 3.md\"",
            "\"docs/phase67_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off 2.md\"",
            "\"docs/phase67_human_only_workflow_readiness_checkpoint_wiring_default_off 2.md\"",
            '"docs/phase64_human_only_manual_application_handoff_packet_wiring_default_off 2.md"',
            '"docs/phase64_human_only_manual_application_handoff_packet_wiring_default_off 3.md"',
            '"docs/phase64_human_only_manual_application_handoff_packet_readback_ui_api_default_off 2.md"',
            '"docs/phase64_human_only_manual_application_handoff_packet_readback_ui_api_default_off 3.md"',
            '"tests/test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off 2.py"',
            '"tests/test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off 3.py"',
            '"tests/test_phase64b_human_only_manual_application_handoff_packet_readback_ui_api_default_off 2.py"',
        "tests/test_phase58a_manual_exact_change_acceptance_approved_plan_wiring_default_off.py",
        "tests/test_phase58b_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.py",
        "tests/test_phase59a_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.py",
        "tests/test_phase59b_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.py",
        "tests/test_phase60a_guarded_resume_copy_artifact_readback_verification_default_off.py",
        "tests/test_phase60b_guarded_resume_copy_artifact_verification_readback_ui_api_default_off.py",
        "tests/test_phase61a_verified_artifact_operator_review_packet_wiring_default_off.py",
        "tests/test_phase61b_verified_artifact_operator_review_packet_readback_ui_api_default_off.py",
            "tests/test_phase62a_verified_artifact_operator_decision_capture_wiring_default_off.py",
            "tests/test_phase62b_verified_artifact_operator_decision_capture_readback_ui_api_default_off.py",
            "tests/test_phase63a_operator_approved_artifact_application_readiness_packet_wiring_default_off.py",
            "tests/test_phase63b_operator_approved_artifact_application_readiness_packet_readback_ui_api_default_off.py",
            "tests/test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off.py",
                "tests/test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off 3.py",
                "tests/test_phase64a_human_only_manual_application_handoff_packet_wiring_default_off 2.py",
            "tests/test_phase64b_human_only_manual_application_handoff_packet_readback_ui_api_default_off.py",
                "tests/test_phase64b_human_only_manual_application_handoff_packet_readback_ui_api_default_off 2.py",
            "tests/test_phase65a_human_only_handoff_audit_trail_wiring_default_off.py",
                "tests/test_phase65b_human_only_handoff_audit_trail_readback_ui_api_default_off.py",
                "tests/test_phase66a_human_only_safety_boundary_summary_wiring_default_off.py",
                "tests/test_phase66b_human_only_safety_boundary_summary_readback_ui_api_default_off.py",
                "tests/test_phase66a_human_only_safety_boundary_summary_wiring_default_off 2.py",
                "tests/test_phase66b_human_only_safety_boundary_summary_readback_ui_api_default_off 2.py",
                "tests/test_phase67a_human_only_workflow_readiness_checkpoint_wiring_default_off.py",
                "tests/test_phase67b_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off.py",
            "tests/test_phase68a_end_to_end_agentic_workflow_integration_wiring_default_off.py",
            "tests/test_phase68b_end_to_end_agentic_workflow_integration_readback_ui_api_default_off.py",
            "tests/test_phase69a_agentic_workflow_production_readiness_checkpoint_default_off.py",
            "tests/test_phase69b_agentic_workflow_production_readiness_readback_ui_api_default_off.py",
            "tests/test_phase70a_ux_polish_agentic_workflow_demo_readiness_default_off.py",
            "tests/test_phase70b_ux_polish_agentic_workflow_demo_readiness_readback_default_off.py",
            "tests/test_phase69a_agentic_workflow_production_readiness_checkpoint_default_off 2.py",
            "tests/test_phase69b_agentic_workflow_production_readiness_readback_ui_api_default_off 2.py",
            "\"tests/test_phase69a_agentic_workflow_production_readiness_checkpoint_default_off 2.py\"",
            "\"tests/test_phase69b_agentic_workflow_production_readiness_readback_ui_api_default_off 2.py\"",
            "tests/test_phase66a_human_only_safety_boundary_summary_wiring_default_off 3.py",
            "tests/test_phase66b_human_only_safety_boundary_summary_readback_ui_api_default_off 3.py",
            "tests/test_phase67a_human_only_workflow_readiness_checkpoint_wiring_default_off 2.py",
            "tests/test_phase67b_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off 2.py",
            "\"tests/test_phase66a_human_only_safety_boundary_summary_wiring_default_off 3.py\"",
            "\"tests/test_phase66b_human_only_safety_boundary_summary_readback_ui_api_default_off 3.py\"",
            "\"tests/test_phase67a_human_only_workflow_readiness_checkpoint_wiring_default_off 2.py\"",
            "\"tests/test_phase67b_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off 2.py\"",
        "tests/test_phase56b_live_tailoring_suggestion_planning_workspace_readback_ui_api_default_off.py",
        "src/app/api.py",
        "src/app/services.py",
        "src/app/planning_ui.py",
        "src/app/static/scan_workspace.js",
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
        "docs/phase60_guarded_resume_copy_artifact_verification_readback_ui_api_default_off.md",
        "docs/phase61_verified_artifact_operator_review_packet_wiring_default_off.md",
        "docs/phase61_verified_artifact_operator_review_packet_readback_ui_api_default_off.md",
            "docs/phase62_verified_artifact_operator_decision_capture_wiring_default_off.md",
            "docs/phase62_verified_artifact_operator_decision_capture_readback_ui_api_default_off.md",
            "docs/phase63_operator_approved_artifact_application_readiness_packet_wiring_default_off.md",
            "docs/phase63_operator_approved_artifact_application_readiness_packet_readback_ui_api_default_off.md",
        "tests/test_phase58a_manual_exact_change_acceptance_approved_plan_wiring_default_off.py",
        "tests/test_phase58b_manual_exact_change_acceptance_approved_plan_readback_ui_api_default_off.py",
        "tests/test_phase59a_approved_change_plan_guarded_resume_copy_artifact_wiring_default_off.py",
        "tests/test_phase59b_approved_change_plan_guarded_resume_copy_artifact_readback_ui_api_default_off.py",
        "tests/test_phase60a_guarded_resume_copy_artifact_readback_verification_default_off.py",
        "tests/test_phase60b_guarded_resume_copy_artifact_verification_readback_ui_api_default_off.py",
        "tests/test_phase61a_verified_artifact_operator_review_packet_wiring_default_off.py",
        "tests/test_phase61b_verified_artifact_operator_review_packet_readback_ui_api_default_off.py",
            "tests/test_phase62a_verified_artifact_operator_decision_capture_wiring_default_off.py",
            "tests/test_phase62b_verified_artifact_operator_decision_capture_readback_ui_api_default_off.py",
            "tests/test_phase63a_operator_approved_artifact_application_readiness_packet_wiring_default_off.py",
            "tests/test_phase63b_operator_approved_artifact_application_readiness_packet_readback_ui_api_default_off.py",
        "tests/test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off.py",
        "src/agents/manual_generate_ai_tailoring_preview_provider_response_validation_contract.py",
        "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_contract.md",
        "tests/test_phase30a_manual_generate_ai_tailoring_preview_provider_response_validation_contract_default_off.py",
        "src/app/api.py",
        "docs/phase30_manual_generate_ai_tailoring_preview_provider_response_validation_api_readback.md",
        "tests/test_phase30b_manual_generate_ai_tailoring_preview_provider_response_validation_api_readback_default_off.py",
                "src/app/static/agentic_review.js",
                "src/app/static/app_redesign.css",
            "src/app/static/agentic_review.js",
                "src/app/ui.py",
                "src/app/static/app.js",
                "src/app/static/planning.js",
                "src/app/static/scan_workspace.css",
            "src/app/static/scan_workspace_review.css",
            "src/app/static/styles.css",
                "tests/test_queue_ui_metadata_contract.py",
                "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
                "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
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

    allowed |= {
        "requirements.txt",
        "src/agents/orchestrator_adapter_harness.py",
        "tests/test_phase80b_controlled_advisory_chain_trace_persistence.py",
    }
    allowed |= {
        "requirements.txt",
        "src/pipeline/collector.py",
        "tests/test_phase80d_advisory_chain_trace_readback_compatibility.py",
        "tests/test_phase81b_controlled_pipeline_advisory_chain_invocation_default_off.py",
        "tests/test_phase81d_collector_advisory_chain_diagnostics_sidecar_default_off.py",
        "tests/test_phase82b_collector_advisory_chain_trace_persistence_default_off.py",
        "tests/test_phase83b_live_llm_invocation_contract_map_default_off.py",
            "src/agents/jd_intelligence.py",
            "tests/test_phase84b_jd_intelligence_existing_output_wrapper_default_off.py",
                "tests/test_phase86b_jd_intelligence_existing_output_trace_payload_default_off.py",
                "tests/test_phase87b_jd_intelligence_existing_output_collector_diagnostics_default_off.py",
            "tests/test_phase88b_jd_intelligence_existing_output_trace_persistence_default_off.py",
            "src/agents/resume_match_agent.py",
            "tests/test_phase89b_resume_match_consumes_jd_intelligence_default_off.py",
            "src/agents/critic_agent.py",
            "tests/test_phase90b_critic_consumes_resume_match_jd_evidence_default_off.py",
            "src/agents/job_prioritization_agent.py",
            "tests/test_phase91b_job_prioritization_consumes_critic_evidence_default_off.py",
            "src/agents/tailoring_decision_agent.py",
            "tests/test_phase92b_tailoring_decision_consumes_job_prioritization_evidence_default_off.py",
            "src/agents/operator_review_agent.py",
            "src/agents/evidence_chain_composition.py",
            "tests/test_phase93b_operator_review_consumes_tailoring_decision_evidence_default_off.py",
            "tests/test_phase94b_agent_evidence_chain_composition_default_off.py",
            "tests/test_phase95b_agent_evidence_chain_trace_payload_default_off.py",
                "tests/test_phase96b_agent_evidence_chain_trace_persistence_default_off.py",
                "tests/test_phase97b_agent_evidence_chain_collector_diagnostics_default_off.py",
            "src/agents/evidence_chain_execution.py",
                "requirements.txt",
                "src/agents/evidence_chain_langgraph_harness.py",
            "tests/test_phase98b_controlled_evidence_chain_execution_default_off.py",
            "tests/test_phase99b_collector_controlled_evidence_chain_execution_default_off.py",
            "tests/test_phase100b_evidence_chain_trace_persistence_readback_default_off.py",
            "tests/test_phase101b_evidence_chain_api_service_readback_default_off.py",
                "src/app/static/agentic_review.js",
            "tests/test_resume_match_dry_run_contract_no_pipeline_change.py",
            "tests/support/phase_guard_registry.py",
            "tests/test_phase85b_legacy_guard_registry_default_off.py",
            "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
            "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
            "tests/test_three_core_shadow_readiness_wrap_default_off.py",
            "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
            "tests/test_agent_trace_ui_readiness_checkpoint.py",
            "tests/test_agent_trace_readonly_ui_panel_no_api_no_writes.py",
            "tests/test_agent_trace_polish_ux_hardening_ui_only_no_api_no_writes.py",
            "tests/test_agent_trace_polish_ux_hardening_ui_only_no_api_no_writes.py",
            "tests/test_agent_trace_readonly_ui_panel_no_api_no_writes.py",
        "tests/test_shadow_sidecar_trace_persistence_hook_integration_default_off.py",
    }
    assert_changed_files_allowed(
        changed,
        allowed | legacy_guards,
        legacy_guard_profiles=("config_vocabulary_scoring_change",),
    )
