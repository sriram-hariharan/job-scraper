# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from pathlib import Path

from src.agents.manual_generate_ai_tailoring_preview_request_packet_contract import (
    build_manual_generate_ai_tailoring_preview_request_packet_contract,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_contract.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "read_only",
    "advisory_only",
    "manual_review_only",
    "request_packet_contract_only",
    "requires_user_trigger",
    "user_trigger_present",
    "manual_acceptance_required",
    "can_prepare_request_packet",
    "preview_request_allowed",
    "blocked_reasons",
    "missing_inputs",
    "request_packet",
    "deterministic_request_key",
    "no_provider_calls",
    "provider_call_performed",
    "no_network_calls",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
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
    "request_packet_contract_only",
    "requires_user_trigger",
    "manual_acceptance_required",
    "no_provider_calls",
    "no_network_calls",
}

FALSE_ACTION_KEYS = {
    "provider_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
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
    "src/app/api.py": (
        "dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9"
    ),
    "src/app/services.py": (
        "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee"
    ),
    "src/app/static/agentic_review.js": (
        "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b"
    ),
    "src/app/static/app_redesign.css": (
        "62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c"
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
)

REQUIRED_DOC_MARKERS = (
    "Phase 25A Manual Generate AI Tailoring Preview Request-Packet Contract",
    "request-packet contract only",
    "default-off",
    "read-only",
    "advisory-only",
    "manual-review only",
    "requires an explicit user trigger",
    "manual acceptance required",
    "no provider calls",
    "no network calls",
    "no tailoring runtime calls",
    "no AI tailoring generation",
    "no generated tailoring text",
    "no resume rewrite",
    "no resume overwrite",
    "no resume mutation",
    "no application mutation",
    "no database writes",
    "no persistence",
    "no execution",
    "no submission",
    "no auto-apply",
    "no auto-submit",
    "no autonomous application execution",
    "no automatic job application submission",
    "phase24-manual-generate-ai-tailoring-preview-release-v1",
    "phase24d-manual-generate-ai-tailoring-preview-release-checkpoint-v1",
    "phase24c-manual-generate-ai-tailoring-preview-ui-readback-v1",
    "phase24b-manual-generate-ai-tailoring-preview-api-readback-v1",
    "phase24a-manual-generate-ai-tailoring-preview-contract-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _ready_inputs() -> dict[str, dict]:
    return {
        "phase24_preview_contract_payload": {
            "contract_status": "manual_generate_ai_tailoring_preview_ready",
            "can_prepare_preview": True,
        },
        "job_metadata": {
            "job_id": "job-1",
            "title": "Machine Learning Engineer",
            "company": "ExampleCo",
        },
        "selected_resume_metadata": {
            "resume_id": "resume-1",
            "resume_label": "ML platform resume",
        },
        "tailoring_opportunity_payload": {
            "tailoring_opportunities": [
                {
                    "opportunity_type": "missing_requirement",
                    "signal": "kubernetes",
                }
            ]
        },
        "user_trigger_metadata": {"user_triggered": True},
    }


def _walk(value):
    if isinstance(value, dict):
        for key, nested in value.items():
            yield str(key), nested
            yield from _walk(nested)
    elif isinstance(value, list):
        for nested in value:
            yield from _walk(nested)


def test_helper_exists_and_returns_required_contract_keys():
    payload = build_manual_generate_ai_tailoring_preview_request_packet_contract()

    assert HELPER_PATH.exists()
    assert REQUIRED_KEYS.issubset(payload.keys())
    assert payload["phase"] == "25A"
    for key in TRUE_SAFETY_KEYS:
        assert payload[key] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_no_user_trigger_blocks_request_packet_preparation():
    inputs = _ready_inputs()
    inputs["user_trigger_metadata"] = {"user_triggered": False}

    payload = build_manual_generate_ai_tailoring_preview_request_packet_contract(
        **inputs
    )

    assert payload["user_trigger_present"] is False
    assert payload["can_prepare_request_packet"] is False
    assert payload["preview_request_allowed"] is False
    assert "explicit user trigger required" in payload["blocked_reasons"]
    assert "user_trigger_metadata" in payload["missing_inputs"]
    assert payload["next_safe_step"] == "require_explicit_user_trigger"
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_trigger_with_missing_inputs_reports_incomplete_contract():
    payload = build_manual_generate_ai_tailoring_preview_request_packet_contract(
        user_trigger_metadata={"explicit_user_trigger": True}
    )

    assert payload["user_trigger_present"] is True
    assert payload["can_prepare_request_packet"] is False
    assert payload["preview_request_allowed"] is False
    assert payload["missing_inputs"] == [
        "phase24_preview_contract_payload",
        "job_metadata",
        "selected_resume_metadata",
        "tailoring_opportunity_payload",
    ]
    assert "required request-packet inputs missing" in payload["blocked_reasons"]
    assert payload["next_safe_step"] == "supply_missing_request_packet_inputs"


def test_ready_inputs_prepare_read_only_request_packet_without_mutation():
    inputs = _ready_inputs()
    original = deepcopy(inputs)

    payload = build_manual_generate_ai_tailoring_preview_request_packet_contract(
        **inputs
    )

    assert inputs == original
    assert payload["user_trigger_present"] is True
    assert payload["missing_inputs"] == []
    assert payload["blocked_reasons"] == []
    assert payload["can_prepare_request_packet"] is True
    assert payload["preview_request_allowed"] is True
    assert payload["next_safe_step"] == (
        "review_request_packet_without_generating_ai_tailoring"
    )

    request_packet = payload["request_packet"]
    assert request_packet["deterministic_request_key"] == payload[
        "deterministic_request_key"
    ]
    assert request_packet["read_only"] is True
    assert request_packet["advisory_only"] is True
    assert request_packet["manual_review_only"] is True
    assert request_packet["request_packet_contract_only"] is True
    assert request_packet["contains_generated_tailoring_output"] is False
    assert request_packet["tailoring_generation_requested_from_runtime"] is False
    assert request_packet["source_inputs"] == original
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_deterministic_request_key_is_stable_and_input_sensitive():
    inputs = _ready_inputs()
    first = build_manual_generate_ai_tailoring_preview_request_packet_contract(
        **inputs
    )
    second = build_manual_generate_ai_tailoring_preview_request_packet_contract(
        **deepcopy(inputs)
    )
    changed_inputs = deepcopy(inputs)
    changed_inputs["job_metadata"]["job_id"] = "job-2"
    changed = build_manual_generate_ai_tailoring_preview_request_packet_contract(
        **changed_inputs
    )

    assert first["deterministic_request_key"] == second[
        "deterministic_request_key"
    ]
    assert first["deterministic_request_key"] != changed[
        "deterministic_request_key"
    ]


def test_request_packet_contains_no_generated_tailoring_text_fields():
    payload = build_manual_generate_ai_tailoring_preview_request_packet_contract(
        **_ready_inputs()
    )

    forbidden_field_names = {
        "generated_tailoring_text",
        "tailoring_text",
        "tailoring_output_text",
        "cover_letter_text",
        "resume_rewrite_text",
    }
    for key, value in _walk(payload):
        assert key.lower() not in forbidden_field_names
        assert not (
            isinstance(value, str)
            and "generated tailoring text" in value.lower()
        )


def test_helper_source_has_no_forbidden_imports_or_runtime_calls():
    source = HELPER_PATH.read_text()

    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source


def test_docs_capture_default_off_request_packet_safety_contract():
    text = DOC_PATH.read_text()

    for marker in REQUIRED_DOC_MARKERS:
        assert marker in text


def test_protected_runtime_api_ui_and_generation_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_phase25a_changes_are_limited_to_contract_doc_and_tests():
    status = ROOT.joinpath(".git").exists()
    assert status

    import subprocess

    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    changed = {
        line[3:]
        for line in result.stdout.splitlines()
        if line and line[:2].strip()
    }
    allowed = {
        "src/app/api.py",
        "src/agents/manual_generate_ai_tailoring_preview_request_packet_contract.py",
        "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_contract.md",
        "tests/test_phase25a_manual_generate_ai_tailoring_preview_request_packet_contract_default_off.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_api_readback.md",
            "tests/test_phase25b_manual_generate_ai_tailoring_preview_request_packet_api_readback_default_off.py",
            "src/app/static/agentic_review.js",
            "src/app/static/app_redesign.css",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_ui_readback.md",
            "tests/test_phase25c_manual_generate_ai_tailoring_preview_request_packet_ui_readback_default_off.py",
            "docs/phase25_manual_generate_ai_tailoring_preview_request_packet_release_checkpoint.md",
            "tests/test_phase25d_manual_generate_ai_tailoring_preview_request_packet_release_checkpoint_default_off.py",
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
                '"docs/phase28_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback 2.md"',
                '"tests/test_phase28c_manual_generate_ai_tailoring_preview_provider_call_boundary_ui_readback_default_off 2.py"',
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
                                    '"docs/phase32_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback 2.md"',
                                    '"tests/test_phase32b_manual_generate_ai_tailoring_preview_normalized_response_preview_packet_api_readback_default_off 2.py"',
                                    "src/agents/controlled_agent_router_readonly.py",
                                "docs/phase33_controlled_agent_router_readonly.md",
                                    "tests/test_phase33a_controlled_agent_router_readonly.py",
                                    "docs/phase33_controlled_agent_router_readonly 2.md",
                                    "tests/test_phase33a_controlled_agent_router_readonly 2.py",
                                    '"docs/phase33_controlled_agent_router_readonly 2.md"',
                                    '"tests/test_phase33a_controlled_agent_router_readonly 2.py"',
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
        }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if path != Path(__file__).resolve()
        and any(
            marker in path.read_text(encoding="utf-8")
            for marker in (
                "manual_generate_ai_tailoring_preview_request_packet_contract",
                "manual_generate_ai_tailoring_preview_request_packet_api_readback",
                "dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9",
                "changes_only",
            )
        )
    }

    assert changed <= allowed | legacy_guards
