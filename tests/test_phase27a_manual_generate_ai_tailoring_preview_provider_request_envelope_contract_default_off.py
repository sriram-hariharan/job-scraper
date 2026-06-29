from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents.manual_generate_ai_tailoring_preview_provider_request_envelope_contract import (
    build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/manual_generate_ai_tailoring_preview_provider_request_envelope_contract.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_contract.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "provider_request_envelope_contract_only",
    "requires_user_trigger",
    "user_trigger_present",
    "operator_confirmation_required",
    "operator_confirmation_present",
    "manual_acceptance_required",
    "dispatch_boundary_required",
    "dispatch_boundary_accepted",
    "provider_configuration_required",
    "provider_configuration_present",
    "provider_request_envelope_ready",
    "provider_request_allowed",
    "blocked_reasons",
    "missing_inputs",
    "request_envelope",
    "deterministic_envelope_key",
    "no_provider_calls",
    "provider_call_performed",
    "no_network_calls",
    "network_call_performed",
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
    "provider_request_envelope_contract_only",
    "requires_user_trigger",
    "operator_confirmation_required",
    "manual_acceptance_required",
    "dispatch_boundary_required",
    "provider_configuration_required",
    "no_provider_calls",
    "no_network_calls",
}

FALSE_ACTION_KEYS = {
    "provider_call_performed",
    "network_call_performed",
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

REQUIRED_DOC_MARKERS = (
    "# Phase 27A Manual Generate AI Tailoring Preview Provider Request-Envelope Contract",
    "Provider request-envelope contract only",
    "Default-off",
    "Read-only",
    "Advisory-only",
    "Manual-review only",
    "User trigger required",
    "Operator confirmation required",
    "Manual acceptance required",
    "Dispatch boundary required",
    "Provider configuration required",
    "Does not dispatch",
    "Does not call network",
    "Does not call providers",
    "Does not generate AI tailoring",
    "Does not call tailoring runtime",
    "Does not create real tailoring output",
    "Does not create resume rewrites",
    "Does not overwrite resumes",
    "Does not mutate resumes",
    "Does not persist data",
    "Does not write to database",
    "Does not execute applications",
    "Does not submit applications",
    "No provider calls",
    "No network calls",
    "No database writes",
    "No persistence",
    "No mutation",
    "No resume mutation",
    "No application mutation",
    "No execution",
    "No submission",
    "No auto-apply",
    "No auto-submit",
    "No autonomous application execution",
    "No automatic job application submission",
    "Tailoring agent remains separate from final scoring",
    (
        "Generated tailoring suggestions must remain preview/manual-review "
        "only unless user accepts edits in a later phase"
    ),
    "This phase does not create real tailoring output",
    "This phase does not add a UI action control",
    "phase26-manual-generate-ai-tailoring-preview-dispatch-boundary-release-v1",
    (
        "phase26d-manual-generate-ai-tailoring-preview-dispatch-boundary-"
        "release-checkpoint-v1"
    ),
    (
        "phase26c-manual-generate-ai-tailoring-preview-dispatch-boundary-"
        "ui-readback-v1"
    ),
    (
        "phase26b-manual-generate-ai-tailoring-preview-dispatch-boundary-"
        "api-readback-v1"
    ),
    "phase26a-manual-generate-ai-tailoring-preview-dispatch-boundary-contract-v1",
    "phase25-manual-generate-ai-tailoring-preview-request-packet-release-v1",
    "phase24-manual-generate-ai-tailoring-preview-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _ready_inputs() -> dict[str, dict]:
    return {
        "phase26_dispatch_boundary_payload": {
            "contract_status": (
                "manual_generate_ai_tailoring_preview_dispatch_boundary_ready"
            ),
            "dispatch_ready": True,
            "dispatch_allowed": True,
            "provider_call_performed": False,
            "network_call_performed": False,
            "tailoring_runtime_call_performed": False,
            "ai_tailoring_generation_performed": False,
            "execution_performed": False,
            "submission_performed": False,
            "deterministic_dispatch_key": (
                "manual-generate-ai-tailoring-preview-dispatch-example"
            ),
        },
        "phase25_request_packet_payload": {
            "contract_status": (
                "manual_generate_ai_tailoring_preview_request_packet_ready"
            ),
            "preview_request_allowed": True,
            "request_packet": {
                "deterministic_request_key": (
                    "manual-generate-ai-tailoring-preview-request-example"
                ),
            },
        },
        "phase24_preview_contract_payload": {
            "contract_status": "manual_generate_ai_tailoring_preview_ready",
            "can_prepare_preview": True,
        },
        "user_trigger_metadata": {"explicit_user_trigger": True},
        "operator_confirmation_metadata": {
            "explicit_operator_confirmation": True
        },
        "provider_configuration_metadata": {
            "provider_configuration_present": True,
            "provider_name": "manual-review-provider-stub",
            "model": "manual-review-model-stub",
        },
    }


def _walk(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key), nested
            yield from _walk(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk(nested)


def _changed_files() -> set[str]:
    tracked = subprocess.check_output(
        ["git", "diff", "--name-only"], cwd=ROOT, text=True
    ).splitlines()
    untracked = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        text=True,
    ).splitlines()
    return set(tracked + untracked)


def test_helper_exists_and_returns_required_contract_keys():
    payload = (
        build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract()
    )

    assert HELPER_PATH.exists()
    assert callable(
        build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract
    )
    assert REQUIRED_KEYS.issubset(payload.keys())
    assert payload["phase"] == "27A"
    for key in TRUE_SAFETY_KEYS:
        assert payload[key] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_no_user_trigger_blocks_provider_request_envelope_readiness():
    inputs = _ready_inputs()
    inputs["user_trigger_metadata"] = {"explicit_user_trigger": False}

    payload = (
        build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract(
            **inputs
        )
    )

    assert payload["user_trigger_present"] is False
    assert payload["provider_request_envelope_ready"] is False
    assert payload["provider_request_allowed"] is False
    assert "explicit user trigger required" in payload["blocked_reasons"]
    assert "user_trigger_metadata" in payload["missing_inputs"]
    assert payload["next_safe_step"] == "require_explicit_user_trigger"
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_missing_operator_confirmation_blocks_provider_request_envelope():
    inputs = _ready_inputs()
    inputs["operator_confirmation_metadata"] = {}

    payload = (
        build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract(
            **inputs
        )
    )

    assert payload["operator_confirmation_present"] is False
    assert payload["provider_request_envelope_ready"] is False
    assert payload["provider_request_allowed"] is False
    assert "operator confirmation required" in payload["blocked_reasons"]
    assert "operator_confirmation_metadata" in payload["missing_inputs"]
    assert payload["next_safe_step"] == "require_operator_confirmation"
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_missing_or_blocked_dispatch_boundary_blocks_envelope_readiness():
    missing_payload = (
        build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract(
            phase25_request_packet_payload={"preview_request_allowed": True},
            phase24_preview_contract_payload={"can_prepare_preview": True},
            user_trigger_metadata={"explicit_user_trigger": True},
            operator_confirmation_metadata={
                "explicit_operator_confirmation": True
            },
            provider_configuration_metadata={
                "provider_configuration_present": True
            },
        )
    )

    assert missing_payload["dispatch_boundary_accepted"] is False
    assert (
        "phase26_dispatch_boundary_payload"
        in missing_payload["missing_inputs"]
    )
    assert (
        "phase26 dispatch-boundary payload required"
        in missing_payload["blocked_reasons"]
    )

    inputs = _ready_inputs()
    inputs["phase26_dispatch_boundary_payload"] = {
        "dispatch_ready": False,
        "dispatch_allowed": False,
    }
    blocked_payload = (
        build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract(
            **inputs
        )
    )

    assert blocked_payload["dispatch_boundary_accepted"] is False
    assert blocked_payload["provider_request_envelope_ready"] is False
    assert any(
        "dispatch boundary must be accepted" in reason
        for reason in blocked_payload["blocked_reasons"]
    )


def test_missing_provider_configuration_metadata_is_blocked():
    inputs = _ready_inputs()
    inputs["provider_configuration_metadata"] = {}

    payload = (
        build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract(
            **inputs
        )
    )

    assert payload["provider_configuration_present"] is False
    assert payload["provider_request_envelope_ready"] is False
    assert "provider_configuration_metadata" in payload["missing_inputs"]
    assert (
        "provider configuration metadata required"
        in payload["blocked_reasons"]
    )
    assert payload["next_safe_step"] == "provide_provider_configuration_metadata"


def test_ready_inputs_allow_envelope_readiness_without_any_action_flags():
    payload = (
        build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract(
            **_ready_inputs()
        )
    )

    assert payload["dispatch_boundary_accepted"] is True
    assert payload["provider_configuration_present"] is True
    assert payload["provider_request_envelope_ready"] is True
    assert payload["provider_request_allowed"] is True
    assert payload["blocked_reasons"] == []
    assert payload["missing_inputs"] == []
    assert payload["next_safe_step"] == (
        "manual_review_provider_request_envelope_without_dispatching"
    )
    assert payload["request_envelope"]["provider_request_allowed"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False
        assert payload["request_envelope"].get(key, False) is False


def test_deterministic_envelope_key_is_stable_and_input_sensitive():
    inputs = _ready_inputs()
    first = (
        build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract(
            **inputs
        )
    )
    second = (
        build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract(
            **deepcopy(inputs)
        )
    )

    mutated_inputs = deepcopy(inputs)
    mutated_inputs["provider_configuration_metadata"]["model"] = (
        "manual-review-model-stub-v2"
    )
    mutated = (
        build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract(
            **mutated_inputs
        )
    )

    assert first["deterministic_envelope_key"] == second[
        "deterministic_envelope_key"
    ]
    assert first["deterministic_envelope_key"] != mutated[
        "deterministic_envelope_key"
    ]


def test_helper_payload_does_not_include_generated_tailoring_text_or_output():
    payload = (
        build_manual_generate_ai_tailoring_preview_provider_request_envelope_contract(
            **_ready_inputs()
        )
    )

    forbidden_keys = {
        "generated_tailoring_text",
        "generated_resume_text",
        "tailored_resume_text",
        "tailoring_output",
        "real_tailoring_output",
        "generated_tailoring",
    }
    for key, nested in _walk(payload):
        assert key not in forbidden_keys
        if isinstance(nested, str):
            assert "generated_tailoring_text" not in nested
            assert "tailored_resume_text" not in nested
            assert "real_tailoring_output" not in nested


def test_helper_source_has_no_forbidden_runtime_provider_or_network_imports():
    source = HELPER_PATH.read_text(encoding="utf-8")

    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source


def test_doc_contains_required_safety_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8")

    assert text.startswith(
        "# Phase 27A Manual Generate AI Tailoring Preview Provider Request-Envelope Contract"
    )
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_phase27a_changes_only_helper_doc_test_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "src/agents/manual_generate_ai_tailoring_preview_provider_request_envelope_contract.py",
        "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_contract.md",
        "tests/test_phase27a_manual_generate_ai_tailoring_preview_provider_request_envelope_contract_default_off.py",
        "src/app/api.py",
        "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_api_readback.md",
        "tests/test_phase27b_manual_generate_ai_tailoring_preview_provider_request_envelope_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_ui_readback.md",
        "tests/test_phase27c_manual_generate_ai_tailoring_preview_provider_request_envelope_ui_readback_default_off.py",
        "docs/phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_release_checkpoint.md",
        "tests/test_phase27d_manual_generate_ai_tailoring_preview_provider_request_envelope_release_checkpoint_default_off.py",
        "src/agents/manual_generate_ai_tailoring_preview_provider_call_boundary_contract.py",
        "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_contract.md",
        "tests/test_phase28a_manual_generate_ai_tailoring_preview_provider_call_boundary_contract_default_off.py",
        "src/app/api.py",
        "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback.md",
        "tests/test_phase28b_manual_generate_ai_tailoring_preview_provider_call_boundary_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback.md",
        "tests/test_phase28c_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback_default_off.py",
        "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback 2.md",
        "tests/test_phase28c_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback_default_off 2.py",
        "docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_release_checkpoint.md",
        "tests/test_phase28d_manual_generate_ai_tailoring_preview_provider_call_boundary_release_checkpoint_default_off.py",
        "src/agents/manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.py",
        "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract.md",
        "tests/test_phase29a_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_contract_default_off.py",
        "src/app/api.py",
        "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_api_readback.md",
        "tests/test_phase29b_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_ui_readback.md",
        "tests/test_phase29c_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_ui_readback_default_off.py",
        "docs/phase29_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_release_checkpoint.md",
        "tests/test_phase29d_manual_generate_ai_tailoring_preview_provider_call_dry_run_packet_release_checkpoint_default_off.py",
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
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if path != Path(__file__).resolve()
        and any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "phase27a_manual_generate_ai_tailoring_preview_provider_request_envelope_contract",
                "phase27_manual_generate_ai_tailoring_preview_provider_request_envelope_contract",
                "changes_only",
            )
        )
    }

    assert changed <= allowed | legacy_guards
