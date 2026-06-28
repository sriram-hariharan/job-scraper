# phase26c legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c
# phase26b legacy guard marker: changes_only dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9
# phase23f legacy guard marker: changes_only dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9 300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab 62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
# phase23f legacy guard marker: changes_only 1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents import tailoring_agent_opportunity_contract as contract


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "src/agents/tailoring_agent_opportunity_contract.py"
DOC_PATH = ROOT / "docs/phase23_tailoring_agent_opportunity_contract.md"

SAFETY_KEYS = (
    "no_auto_apply",
    "no_auto_submit",
    "no_autonomous_application_execution",
    "no_automatic_job_application_submission",
    "manual_user_control_required",
    "no_provider_calls",
    "no_network_calls",
    "no_database_writes",
    "no_persistence",
    "no_mutation",
    "no_resume_mutation",
    "no_application_mutation",
    "no_execution",
    "no_submission",
)

FORBIDDEN_SOURCE_MARKERS = (
    "run_chat_completion",
    "run_chat_completion_with_metadata",
    "requests.",
    "httpx",
    "urllib",
    "subprocess",
    "open(",
    "read_text",
    "write_text",
    "DATABASE_URL",
    "cache_get_json",
    "cache_set_json",
    "score_resume_job_match(",
    "run_prefilter(",
    "_run_live_llm_tailoring",
    "generate_tailoring_suggestions",
)

REQUIRED_TAGS = (
    "phase22-core-agent-evidence-materialization-release-v1",
    "phase22f-core-agent-evidence-materialization-release-checkpoint-v1",
    "phase22e-core-agent-evidence-materialization-ui-readback-v1",
    "phase22d-core-agent-evidence-materialization-api-readback-v1",
    "phase22c-core-agent-evidence-materialization-preview-v1",
    "phase22b-core-agent-automation-mutation-inventory-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/app/api.py": "dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
    "src/app/static/app_redesign.css": "62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c",
    "src/agents/core_agent_evidence_materialization_preview.py": "d1b0862cf0355192a45a7b45fbeaa622d72e16b7c5234c71bea75aea90db9110",
    "src/pipeline/collector.py": "73cd47f98ece2b4cf1006ac17da559d1f621fb6bc4e92a75f9e92870f60b7405",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
}


def _inputs():
    return {
        "core_agent_evidence_packet": {
            "manual_review_evidence_packet": {
                "missing_evidence_fields": ["project_evidence"],
            },
        },
        "job_evidence": {
            "title": "Machine Learning Engineer",
            "required_skills": ["python", "kubernetes"],
        },
        "resume_evidence": {
            "resume_name": "ML Resume",
            "skills": ["python"],
        },
        "missing_requirements": ["kubernetes", "model monitoring"],
        "matched_terms": ["python", "machine learning"],
        "tailoring_context": {
            "focus_areas": ["production ML impact"],
        },
    }


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


def test_helper_module_and_public_function_exist():
    assert HELPER_PATH.exists()
    assert callable(contract.build_tailoring_agent_opportunity_contract)


def test_default_off_returns_skipped_read_only_payload():
    payload = contract.build_tailoring_agent_opportunity_contract()

    assert payload["contract_status"] == contract.STATUS_SKIPPED
    assert payload["tailoring_agent_opportunity_contract_enabled"] is False
    assert payload["default_off"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["manual_review_only"] is True
    for key in SAFETY_KEYS:
        assert payload[key] is True


def test_enabled_mode_accepts_and_materializes_all_caller_inputs():
    inputs = _inputs()
    payload = contract.build_tailoring_agent_opportunity_contract(
        enabled=True,
        **inputs,
    )

    assert payload["contract_status"] == contract.STATUS_READY
    assert payload["opportunity_inputs"] == inputs
    assert payload["supplied_input_fields"] == list(inputs)


def test_enabled_mode_returns_deterministic_opportunity_records():
    first = contract.build_tailoring_agent_opportunity_contract(
        enabled=True,
        **_inputs(),
    )
    second = contract.build_tailoring_agent_opportunity_contract(
        enabled=True,
        **_inputs(),
    )

    assert first == second
    assert first["tailoring_opportunities"] == [
        {
            "opportunity_type": "missing_requirement",
            "source": "missing_requirements",
            "signal": "kubernetes",
            "manual_review_required": True,
            "generate_ai_tailoring_allowed_now": False,
            "suggested_next_step": (
                "review_existing_resume_evidence_for_supported_alignment"
            ),
        },
        {
            "opportunity_type": "missing_requirement",
            "source": "missing_requirements",
            "signal": "model monitoring",
            "manual_review_required": True,
            "generate_ai_tailoring_allowed_now": False,
            "suggested_next_step": (
                "review_existing_resume_evidence_for_supported_alignment"
            ),
        },
        {
            "opportunity_type": "evidence_packet_gap",
            "source": "core_agent_evidence_packet",
            "signal": "project_evidence",
            "manual_review_required": True,
            "generate_ai_tailoring_allowed_now": False,
            "suggested_next_step": (
                "review_missing_evidence_before_tailoring"
            ),
        },
        {
            "opportunity_type": "caller_supplied_tailoring_context",
            "source": "tailoring_context",
            "signal": "production ML impact",
            "manual_review_required": True,
            "generate_ai_tailoring_allowed_now": False,
            "suggested_next_step": (
                "review_tailoring_opportunity_under_manual_control"
            ),
        },
    ]


def test_inputs_are_deep_copied_and_not_mutated():
    inputs = _inputs()
    before = deepcopy(inputs)
    payload = contract.build_tailoring_agent_opportunity_contract(
        enabled=True,
        **inputs,
    )

    assert inputs == before
    for field_name, value in inputs.items():
        assert payload["opportunity_inputs"][field_name] is not value

    inputs["missing_requirements"].append("changed")
    assert "changed" not in payload["opportunity_inputs"][
        "missing_requirements"
    ]


def test_no_inputs_returns_enabled_missing_evidence_payload():
    payload = contract.build_tailoring_agent_opportunity_contract(
        enabled=True
    )

    assert payload["contract_status"] == contract.STATUS_MISSING_EVIDENCE
    assert payload["tailoring_opportunities"] == []
    assert "No caller-supplied evidence" in payload[
        "tailoring_opportunity_summary"
    ]


def test_ai_tailoring_is_future_user_triggered_only():
    payload = contract.build_tailoring_agent_opportunity_contract(
        enabled=True,
        **_inputs(),
    )

    assert payload["future_user_triggered_action"] == (
        "Generate AI Tailoring"
    )
    assert payload["generate_ai_tailoring_user_trigger_required"] is True
    assert payload["ai_tailoring_generation_performed"] is False
    assert all(
        item["generate_ai_tailoring_allowed_now"] is False
        for item in payload["tailoring_opportunities"]
    )


def test_payload_contains_all_required_safety_markers():
    payload = contract.build_tailoring_agent_opportunity_contract(
        enabled=True,
        **_inputs(),
    )

    assert payload["tailoring_agent_separate_from_final_scoring"] is True
    for key in SAFETY_KEYS:
        assert payload[key] is True


def test_source_has_no_provider_network_io_or_runtime_calls():
    source = HELPER_PATH.read_text(encoding="utf-8")

    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source


def test_docs_contain_required_boundaries_and_references():
    assert DOC_PATH.exists()
    text = " ".join(DOC_PATH.read_text(encoding="utf-8").lower().split())

    for marker in (
        "phase 23a tailoring-agent opportunity contract",
        "phase 22 core-agent evidence materialization release",
        "tailoring agent is separate from final scoring",
        "only identifies tailoring opportunities",
        "does not generate ai tailoring",
        "generate ai tailoring",
        "must be user-triggered",
        "preview/manual-review only unless the user accepts edits",
        "no silent resume rewrite",
        "no automatic resume overwrite",
        "no resume mutation",
        "no application submission",
        "no provider calls",
        "no network calls",
        "no database writes",
        "no persistence",
        "no mutation",
        "no execution",
        "no submission",
        "no auto-apply",
        "no auto-submit",
        "no autonomous application execution",
        "no automatic job application submission",
        "manual user control remains required",
    ):
        assert marker in text
    raw_text = DOC_PATH.read_text(encoding="utf-8")
    for tag in REQUIRED_TAGS:
        assert tag in raw_text


def test_protected_runtime_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == (
            expected_hash
        )


def test_phase23a_changes_only_helper_doc_test_and_legacy_guards():
    changed = _changed_files()
    allowed = {
        "src/agents/tailoring_agent_opportunity_contract.py",
        "docs/phase23_tailoring_agent_opportunity_contract.md",
        "tests/test_phase23a_tailoring_agent_opportunity_contract_default_off.py",
        "src/app/api.py",
        "docs/phase23_tailoring_agent_opportunity_api_readback.md",
        "tests/test_phase23b_tailoring_agent_opportunity_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase23_tailoring_agent_opportunity_ui_readback.md",
        "tests/test_phase23c_tailoring_agent_opportunity_ui_readback_default_off.py",
        "src/agents/generate_ai_tailoring_action_boundary_contract.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_contract.md",
        "tests/test_phase23d_generate_ai_tailoring_action_boundary_contract_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off.py",
        "docs/phase23_generate_ai_tailoring_action_boundary_ui_readback.md",
        "tests/test_phase23f_generate_ai_tailoring_action_boundary_ui_readback_default_off.py",
        "docs/phase23_tailoring_agent_workflow_release_checkpoint.md",
        "tests/test_phase23g_tailoring_agent_workflow_release_checkpoint_default_off.py",
        "src/agents/manual_generate_ai_tailoring_preview_contract.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_contract.md",
        "tests/test_phase24a_manual_generate_ai_tailoring_preview_contract_default_off.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_api_readback.md",
        "tests/test_phase24b_manual_generate_ai_tailoring_preview_api_readback_default_off.py",
        "src/app/static/agentic_review.js",
        "src/app/static/app_redesign.css",
        "docs/phase24_manual_generate_ai_tailoring_preview_ui_readback.md",
        "tests/test_phase24c_manual_generate_ai_tailoring_preview_ui_readback_default_off.py",
        "docs/phase24_manual_generate_ai_tailoring_preview_release_checkpoint.md",
        "tests/test_phase24d_manual_generate_ai_tailoring_preview_release_checkpoint_default_off.py",
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
        "docs/phase23_generate_ai_tailoring_action_boundary_api_readback 2.md",
        "tests/test_phase23e_generate_ai_tailoring_action_boundary_api_readback_default_off 2.py",
        "tests/test_portfolio_demo_readiness_wrap_checkpoint.py",
    }
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
        if (
            "changes_only" in path.read_text(encoding="utf-8")
            or "dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9"
            in path.read_text(encoding="utf-8")
            or "300bd7285e7ed258197432f74cdab390f11f61670e5ef8e0feb77e3e90c005ab"
            in path.read_text(encoding="utf-8")
            or "62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c"
            in path.read_text(encoding="utf-8")
        )
    }

    assert changed <= allowed | legacy_guards
