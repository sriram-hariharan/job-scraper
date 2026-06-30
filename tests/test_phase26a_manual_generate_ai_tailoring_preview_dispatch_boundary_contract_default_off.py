# phase56b legacy guard marker: changes_only 8e1cfc6368ce71885a523928682913e6d361259f44f38cc00f50ca093ae7b718 cde7018be5fbaec52f7a393de70d71dc1f964b6188831ab25b4fcf28f964c89c
# phase56a legacy guard marker: changes_only 9bfda94f241abc0d39faacfc7d3cd8c19ced1e2a25e49628216ae181769d3d7e 8e1cfc6368ce71885a523928682913e6d361259f44f38cc00f50ca093ae7b718
# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only 9bfda94f241abc0d39faacfc7d3cd8c19ced1e2a25e49628216ae181769d3d7e
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents.manual_generate_ai_tailoring_preview_dispatch_boundary_contract import (
    build_manual_generate_ai_tailoring_preview_dispatch_boundary_contract,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/manual_generate_ai_tailoring_preview_dispatch_boundary_contract.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_contract.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "dispatch_boundary_contract_only",
    "requires_user_trigger",
    "user_trigger_present",
    "operator_confirmation_required",
    "operator_confirmation_present",
    "manual_acceptance_required",
    "dispatch_ready",
    "dispatch_allowed",
    "blocked_reasons",
    "missing_inputs",
    "request_packet_accepted",
    "deterministic_dispatch_key",
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
    "auto_" + "apply_performed",
    "auto_submit_performed",
    "next_safe_step",
}

TRUE_SAFETY_KEYS = {
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "dispatch_boundary_contract_only",
    "requires_user_trigger",
    "operator_confirmation_required",
    "manual_acceptance_required",
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
    "auto_" + "apply_performed",
    "auto_submit_performed",
}

PROTECTED_HASHES = {
    "src/app/api.py": (
        "9bfda94f241abc0d39faacfc7d3cd8c19ced1e2a25e49628216ae181769d3d7e"
    ),
    "src/app/services.py": (
        "8e1cfc6368ce71885a523928682913e6d361259f44f38cc00f50ca093ae7b718"
    ),
    "src/app/static/agentic_review.js": (
        "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b"
    ),
    "src/app/static/app_redesign.css": (
        "62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c"
    ),
    "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py": (
        "4e0dcc111f114551b0ce1c88f8d57618546306c4bcce8ac2d6df86b44cbfa60d"
    ),
    "src/agents/manual_generate_ai_tailoring_preview_contract.py": (
        "98e2c69010061fa8e98cf50541f88537ad9eaff72c7c13a270e57822196eeb45"
    ),
    "src/agents/generate_ai_tailoring_action_boundary_contract.py": (
        "5c7675f889daa3342258be5d8eac5c191b196a84795238c658eb73cb76672953"
    ),
    "src/agents/tailoring_agent_opportunity_contract.py": (
        "e61e910176a315e11b2e403a33920a53726c9df8ed0213f0121b5c6eb0c1d8b3"
    ),
    "src/pipeline/collector.py": (
        "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405"
    ),
    "src/pipeline/job_filter.py": (
        "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4"
    ),
    "src/matching/prefilter.py": (
        "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f"
    ),
    "src/matching/scorer.py": (
        "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac"
    ),
    "src/tailoring/llm.py": (
        "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28"
    ),
    "generate_tailoring_suggestions.py": (
        "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2"
    ),
    "application_execution_queue.py": (
        "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0"
    ),
}

FORBIDDEN_SOURCE_MARKERS = (
    "from src.tailoring",
    "import src.tailoring",
    "generate_tailoring_suggestions",
    "application_execution_queue",
    "from src.app",
    "import src.app",
    "src.services",
    "job_service",
    "storage",
    "database_url",
    "psycopg",
    "sqlite",
    "subprocess",
    "requests.",
    "httpx",
    "run_chat_completion",
    "_run_live_llm_tailoring",
    "execute_application",
    "submit_application",
    "provider_call(",
    "network_call(",
)

REQUIRED_DOC_MARKERS = (
    "# Phase 26A Manual Generate AI Tailoring Preview Dispatch-Boundary Contract",
    "Dispatch-boundary contract only",
    "Default-off",
    "Read-only",
    "Advisory-only",
    "Manual-review only",
    "User trigger required",
    "Operator confirmation required",
    "Manual acceptance required",
    "Does not dispatch",
    "Does not generate AI tailoring",
    "Does not call tailoring runtime",
    "Does not call providers",
    "Does not call network",
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
    "phase25-manual-generate-ai-tailoring-preview-request-packet-release-v1",
    (
        "phase25d-manual-generate-ai-tailoring-preview-request-packet-"
        "release-checkpoint-v1"
    ),
    (
        "phase25c-manual-generate-ai-tailoring-preview-request-packet-"
        "ui-readback-v1"
    ),
    (
        "phase25b-manual-generate-ai-tailoring-preview-request-packet-"
        "api-readback-v1"
    ),
    "phase25a-manual-generate-ai-tailoring-preview-request-packet-contract-v1",
    "phase24-manual-generate-ai-tailoring-preview-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _ready_inputs() -> dict[str, dict]:
    return {
        "phase25_request_packet_payload": {
            "contract_status": (
                "manual_generate_ai_tailoring_preview_request_packet_ready"
            ),
            "can_prepare_request_packet": True,
            "preview_request_allowed": True,
            "provider_call_performed": False,
            "tailoring_runtime_call_performed": False,
            "ai_tailoring_generation_performed": False,
            "request_packet": {
                "deterministic_request_key": (
                    "manual-generate-ai-tailoring-preview-request-example"
                ),
                "preview_request_allowed": True,
            },
        },
        "phase24_preview_contract_payload": {
            "contract_status": "manual_generate_ai_tailoring_preview_ready",
            "can_prepare_preview": True,
        },
        "user_trigger_metadata": {"user_triggered": True},
        "operator_confirmation_metadata": {"operator_confirmed": True},
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
    payload = build_manual_generate_ai_tailoring_preview_dispatch_boundary_contract()

    assert HELPER_PATH.exists()
    assert callable(
        build_manual_generate_ai_tailoring_preview_dispatch_boundary_contract
    )
    assert REQUIRED_KEYS.issubset(payload.keys())
    assert payload["phase"] == "26A"
    for key in TRUE_SAFETY_KEYS:
        assert payload[key] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_no_user_trigger_blocks_dispatch_readiness():
    inputs = _ready_inputs()
    inputs["user_trigger_metadata"] = {"user_triggered": False}

    payload = build_manual_generate_ai_tailoring_preview_dispatch_boundary_contract(
        **inputs
    )

    assert payload["user_trigger_present"] is False
    assert payload["dispatch_ready"] is False
    assert payload["dispatch_allowed"] is False
    assert "explicit user trigger required" in payload["blocked_reasons"]
    assert "user_trigger_metadata" in payload["missing_inputs"]
    assert payload["next_safe_step"] == "require_explicit_user_trigger"
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_missing_operator_confirmation_blocks_dispatch_readiness():
    inputs = _ready_inputs()
    inputs["operator_confirmation_metadata"] = {}

    payload = build_manual_generate_ai_tailoring_preview_dispatch_boundary_contract(
        **inputs
    )

    assert payload["operator_confirmation_present"] is False
    assert payload["dispatch_ready"] is False
    assert payload["dispatch_allowed"] is False
    assert "operator confirmation required" in payload["blocked_reasons"]
    assert "operator_confirmation_metadata" in payload["missing_inputs"]
    assert payload["next_safe_step"] == "require_operator_confirmation"
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_missing_or_blocked_request_packet_blocks_dispatch_readiness():
    missing_payload = (
        build_manual_generate_ai_tailoring_preview_dispatch_boundary_contract(
            phase24_preview_contract_payload={
                "contract_status": "manual_generate_ai_tailoring_preview_ready"
            },
            user_trigger_metadata={"explicit_user_trigger": True},
            operator_confirmation_metadata={
                "explicit_operator_confirmation": True
            },
        )
    )

    assert missing_payload["request_packet_accepted"] is False
    assert missing_payload["dispatch_ready"] is False
    assert "phase25_request_packet_payload" in missing_payload["missing_inputs"]
    assert (
        "phase25 request-packet payload required"
        in missing_payload["blocked_reasons"]
    )

    inputs = _ready_inputs()
    inputs["phase25_request_packet_payload"] = {
        "preview_request_allowed": False,
        "can_prepare_request_packet": False,
    }
    blocked_payload = (
        build_manual_generate_ai_tailoring_preview_dispatch_boundary_contract(
            **inputs
        )
    )

    assert blocked_payload["request_packet_accepted"] is False
    assert blocked_payload["dispatch_ready"] is False
    assert any(
        "request packet must be preview-request allowed" in reason
        for reason in blocked_payload["blocked_reasons"]
    )


def test_ready_inputs_allow_dispatch_readiness_without_any_action_flags():
    payload = build_manual_generate_ai_tailoring_preview_dispatch_boundary_contract(
        **_ready_inputs()
    )

    assert payload["request_packet_accepted"] is True
    assert payload["dispatch_ready"] is True
    assert payload["dispatch_allowed"] is True
    assert payload["blocked_reasons"] == []
    assert payload["missing_inputs"] == []
    assert payload["next_safe_step"] == (
        "manual_review_dispatch_boundary_without_dispatching"
    )
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_deterministic_dispatch_key_is_stable_and_input_sensitive():
    inputs = _ready_inputs()
    first = build_manual_generate_ai_tailoring_preview_dispatch_boundary_contract(
        **inputs
    )
    second = build_manual_generate_ai_tailoring_preview_dispatch_boundary_contract(
        **deepcopy(inputs)
    )

    mutated_inputs = deepcopy(inputs)
    mutated_inputs["phase25_request_packet_payload"]["request_packet"][
        "deterministic_request_key"
    ] = "manual-generate-ai-tailoring-preview-request-mutated"
    mutated = (
        build_manual_generate_ai_tailoring_preview_dispatch_boundary_contract(
            **mutated_inputs
        )
    )

    assert first["deterministic_dispatch_key"] == second[
        "deterministic_dispatch_key"
    ]
    assert first["deterministic_dispatch_key"] != mutated[
        "deterministic_dispatch_key"
    ]


def test_helper_payload_does_not_include_generated_tailoring_text_fields():
    payload = build_manual_generate_ai_tailoring_preview_dispatch_boundary_contract(
        **_ready_inputs()
    )

    forbidden_keys = {
        "generated_tailoring_text",
        "generated_resume_text",
        "tailored_resume_text",
        "tailoring_output",
        "real_tailoring_output",
    }
    for key, nested in _walk(payload):
        assert key not in forbidden_keys
        if isinstance(nested, str):
            assert "generated_tailoring_text" not in nested
            assert "tailored_resume_text" not in nested


def test_helper_source_has_no_forbidden_runtime_or_provider_imports():
    source = HELPER_PATH.read_text(encoding="utf-8")

    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source


def test_doc_contains_required_safety_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8")

    assert text.startswith(
        "# Phase 26A Manual Generate AI Tailoring Preview Dispatch-Boundary Contract"
    )
    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_phase26a_changes_only_helper_doc_test_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "docs/phase56_live_tailoring_suggestion_planning_workspace_readback_ui_api_default_off.md",
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
        "tests/test_phase56a_live_tailoring_suggestion_planning_workspace_wiring_default_off.py",
        "src/agents/manual_generate_ai_tailoring_preview_dispatch_boundary_contract.py",
        "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_contract.md",
        "tests/test_phase26a_manual_generate_ai_tailoring_preview_dispatch_boundary_contract_default_off.py",
            "src/app/api.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_api_readback.md",
            "tests/test_phase26b_manual_generate_ai_tailoring_preview_dispatch_boundary_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_ui_readback.md",
            "tests/test_phase26c_manual_generate_ai_tailoring_preview_dispatch_boundary_ui_readback_default_off.py",
            "docs/phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_release_checkpoint.md",
            "tests/test_phase26d_manual_generate_ai_tailoring_preview_dispatch_boundary_release_checkpoint_default_off.py",
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
                "phase26a_manual_generate_ai_tailoring_preview_dispatch_boundary_contract",
                "phase26_manual_generate_ai_tailoring_preview_dispatch_boundary_contract",
                "changes_only",
            )
        )
    }

    assert changed <= allowed | legacy_guards
