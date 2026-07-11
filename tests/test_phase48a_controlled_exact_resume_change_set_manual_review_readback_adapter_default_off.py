# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
from pathlib import Path

from tests.support.phase_guard_registry import (
    assert_changed_files_allowed,
    get_changed_files,
)



ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase48_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.md"
)

PROTECTED_HASHES = {
    "src/agents/controlled_exact_resume_change_set_manual_review_packet_builder_default_off.py": "07f08a45bc0487f97c4de540947159f79fc41c3ab742b03f4e186c1285592d5e",
    "run_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run.py": "90a3eab155b98c293a9199cfa0707cf32bfa531d7503daef8a1656601d63bd22",
    "src/agents/controlled_exact_resume_change_set_provider_response_normalization_default_off.py": "bf50f751e501db96bdc30308b3bf162ec61b79111fe79907a9efd126f823206f",
    "run_controlled_exact_resume_change_set_provider_response_normalization_dry_run.py": "f298f42d602252b2314750593eab93573eed4dae8e3d90068e05f8a51e60dd9d",
    "src/agents/controlled_exact_resume_change_set_provider_response_validation_default_off.py": "413ace0d64f8c1bd62726cf7ae32bc4fc8e4b88eca82826492362d9842f569ef",
    "run_controlled_exact_resume_change_set_provider_response_validation_dry_run.py": "52351a639821afc4a042be7350514be33bd4f8fa5fbb714eda9d19aa45c0f0d4",
    "src/agents/controlled_exact_resume_change_set_provider_call_boundary_default_off.py": "ed065e62f8cfdc6cf3c89f5e9a5d953ba577050eb4088af23bfaeea8becc088d",
    "run_controlled_exact_resume_change_set_provider_call_boundary_dry_run.py": "20a65fe37de31883c56b38dcda537b2a4034d2a1868d1965f848c1568075f771",
    "src/agents/controlled_exact_resume_change_set_llm_request_packet_default_off.py": "acaf694a08f65a5e646d2cbcc7b83a394ea1d15416c7311e230c86536d0a6b0f",
    "run_controlled_exact_resume_change_set_llm_request_packet_dry_run.py": "8baca68f6d8ba882324d028a68372d0d618709413bebe47931c93da5ef6dc175",
    "src/agents/exact_resume_change_set_proposal_builder_default_off.py": "fd173ea8bf3f7d746ebbdb7d6b2af7ae7df1aeaea4e66acaca52ea4fda1a9dc4",
    "run_exact_resume_change_set_proposal_builder_dry_run.py": "a8ea3201f0e71e463e316abdcf813b8d08fa3a473cd3dddcee158b87f3442451",
    "src/tailoring/llm.py": "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
    "generate_tailoring_suggestions.py": "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28",
    "src/matching/scorer.py": "f56624b5b3c7e2bb01a824386b86fbc2a194e727f0437ca0773764eae64ec941",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}

FORBIDDEN_SOURCE_MARKERS = (
    "from src.pipeline",
    "import src.pipeline",
    "from src.matching",
    "import src.matching",
    "from src.tailoring",
    "import src.tailoring",
    "generate_tailoring_suggestions",
    "application_execution_queue",
    "from src.app",
    "import src.app",
    "from src.storage",
    "import src.storage",
    "requests",
    "httpx",
    "urllib",
    "openai",
    "anthropic",
    "psycopg",
    "sqlite",
    "subprocess",
    "run_prefilter(",
    "score_resume_job_match(",
    "run_chat_completion",
    "build_final_replacement_plan(",
    "submit_application(",
    "execute_application(",
    "overwrite_resume(",
    "mutate_resume(",
    "provider_call(",
    "network_call(",
)

FORBIDDEN_WRITE_MARKERS = (
    ".update(",
    "update(",
    ".write_text(",
    ".write_bytes(",
    ".mkdir(",
    ".save(",
    ".insert(",
)

FALSE_ACTION_KEYS = {
    "ui_route_added",
    "api_route_added",
    "ui_readback_performed",
    "api_readback_performed",
    "user_acceptance_performed",
    "resume_change_applied",
    "manual_review_packets_created",
    "resume_change_proposals_created",
    "provider_response_validation_performed",
    "provider_response_normalization_performed",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "application_submission_performed",
    "submission_performed",
    "auto_" + "apply_performed",
    "auto_submit_performed",
}

ITEM_FALSE_ACTION_KEYS = {
    "ui_route_added",
    "api_route_added",
    "ui_readback_performed",
    "api_readback_performed",
    "user_acceptance_performed",
    "resume_change_applied",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "application_submission_performed",
}

REQUIRED_OUTPUT_KEYS = {
    "phase",
    "default_off",
    "controlled_exact_resume_change_set_manual_review_readback_adapter",
    "read_only",
    "advisory_only",
    "manual_review_readback_only",
    "ui_api_readback_payload_only",
    "proposal_only",
    "exact_worthy_changes_only",
    "manual_review_required",
    "requires_manual_user_control",
    "manual_review_packets_present",
    "review_packet_result_present",
    "readback_context_present",
    "readback_policy",
    "readback_items",
    "readback_items_by_type",
    "readback_items_by_action",
    "readback_payload",
    "readback_summary",
    "readback_findings",
    "missing_inputs",
    "readback_key",
    "manual_review_readback_payload_created",
} | FALSE_ACTION_KEYS


def _builder():
    module = importlib.import_module(
        "src.agents.controlled_exact_resume_change_set_manual_review_readback_adapter_default_off"
    )
    return (
        module.build_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off
    )


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _packet(
    proposal_id: str = "proposal-1",
    change_type: str = "bullet_rewrite",
    action: str = "review_change",
    display_order: int = 2,
) -> dict:
    return {
        "review_packet_id": f"packet-{proposal_id}",
        "proposal_id": proposal_id,
        "change_type": change_type,
        "target_section": "experience",
        "target_identifier": "role-1-bullet-2",
        "current_text": "Built dashboards.",
        "proposed_text": "Built executive dashboards using revenue signals.",
        "change_reason": "Aligns resume evidence with JD analytics language.",
        "jd_terms_supported": ["dashboards", "analytics"],
        "resume_evidence_used": ["Built dashboards"],
        "risk_flags": ["semantic_drift"],
        "source_validation_status": "valid",
        "normalization_notes": ["normalized casing"],
        "manual_review_required": True,
        "requires_user_acceptance": True,
        "recommended_operator_action": action,
        "review_reason": "Operator must inspect exact wording.",
        "display_order": display_order,
    }


def test_helper_import_safe_and_exposes_build_function():
    assert HELPER_PATH.exists()
    builder = _builder()
    assert callable(builder)


def test_missing_packets_blocks_with_missing_input_reason():
    result = _builder()()
    assert result["phase"] == "48A"
    assert result["default_off"] is True
    assert result["readback_findings"]["blocked"] is True
    assert result["missing_inputs"] == ["manual_review_packets"]
    assert result["readback_items"] == []
    assert result["manual_review_readback_payload_created"] is True


def test_accepts_phase47_result_phase47b_nested_and_grouped_sources():
    builder = _builder()
    direct = builder(review_packet_result={"manual_review_packets": [_packet("direct")]})
    nested = builder(
        review_packet_result={
            "review_packet_result": {"manual_review_packets": [_packet("nested")]}
        }
    )
    grouped = builder(
        review_packet_result={
            "manual_review_packets_by_type": {
                "summary": [_packet("grouped-2", "summary", display_order=2)],
                "bullet": [_packet("grouped-1", "bullet", display_order=1)],
            }
        }
    )
    nested_grouped = builder(
        review_packet_result={
            "review_packet_result": {
                "manual_review_packets_by_type": {
                    "skill": [_packet("nested-grouped", "skill")]
                }
            }
        }
    )
    assert direct["readback_items"][0]["proposal_id"] == "direct"
    assert nested["readback_items"][0]["proposal_id"] == "nested"
    assert [item["proposal_id"] for item in grouped["readback_items"]] == [
        "grouped-1",
        "grouped-2",
    ]
    assert nested_grouped["readback_items"][0]["proposal_id"] == "nested-grouped"


def test_explicit_packets_take_precedence_over_result_packets():
    result = _builder()(
        manual_review_packets=[_packet("explicit")],
        review_packet_result={"manual_review_packets": [_packet("ignored")]},
    )
    assert result["manual_review_packets_present"] is True
    assert result["review_packet_result_present"] is True
    assert result["readback_items"][0]["proposal_id"] == "explicit"
    assert result["readback_summary"]["packet_source"] == "manual_review_packets"


def test_valid_packets_create_required_readback_payload_and_safety_flags():
    result = _builder()(
        manual_review_packets=[_packet()],
        readback_context={"source": "unit-test"},
    )
    assert REQUIRED_OUTPUT_KEYS <= set(result)
    assert result["controlled_exact_resume_change_set_manual_review_readback_adapter"] is True
    assert result["read_only"] is True
    assert result["advisory_only"] is True
    assert result["manual_review_readback_only"] is True
    assert result["ui_api_readback_payload_only"] is True
    assert all(result[key] is False for key in FALSE_ACTION_KEYS)
    item = result["readback_items"][0]
    assert ITEM_FALSE_ACTION_KEYS <= set(item)
    assert all(item[key] is False for key in ITEM_FALSE_ACTION_KEYS)
    assert item["manual_review_required"] is True
    assert item["requires_user_acceptance"] is True
    assert item["current_text"] == "Built dashboards."
    assert item["proposed_text"] == "Built executive dashboards using revenue signals."
    assert item["readback_context"] == {"source": "unit-test"}
    payload = result["readback_payload"]
    assert payload["payload_type"] == "exact_resume_change_set_manual_review_readback"
    assert payload["manual_review_required"] is True
    assert payload["requires_manual_user_control"] is True
    assert payload["allowed_user_actions"] == ["preview", "inspect", "defer"]
    for blocked_action in (
        "apply",
        "overwrite_resume",
        "mutate_resume",
        "submit_application",
        "auto_" + "apply",
        "auto_submit",
    ):
        assert blocked_action in payload["blocked_user_actions"]


def test_operator_action_label_maps_all_actions():
    result = _builder()(
        manual_review_packets=[
            _packet("risk", action="review_risk", display_order=1),
            _packet("change", action="review_change", display_order=2),
            _packet("reject", action="reject_invalid", display_order=3),
            _packet("inspect", action="custom_action", display_order=4),
            _packet("unknown", action="", display_order=5),
        ]
    )
    labels = {item["proposal_id"]: item["operator_action_label"] for item in result["readback_items"]}
    assert labels == {
        "risk": "Review risk before accepting",
        "change": "Review exact change",
        "reject": "Reject invalid proposal",
        "inspect": "Inspect unknown proposal",
        "unknown": "Inspect proposal",
    }


def test_invalid_non_dict_packets_counted_reported_and_excluded():
    result = _builder()(manual_review_packets=[_packet("valid"), "invalid", 7, None])
    assert [item["proposal_id"] for item in result["readback_items"]] == ["valid"]
    assert result["readback_findings"]["invalid_packet_count"] == 3
    assert result["readback_findings"]["excluded_invalid_packets"] == 3
    assert result["readback_summary"]["input_packet_count"] == 4
    assert result["readback_summary"]["valid_packet_count"] == 1


def test_max_readback_items_truncates_after_display_order_sort():
    packets = [
        _packet("third", display_order=3),
        _packet("first", display_order=1),
        _packet("second", display_order=2),
    ]
    result = _builder()(
        manual_review_packets=packets,
        readback_policy={"max_readback_items": 2},
    )
    assert [item["proposal_id"] for item in result["readback_items"]] == ["first", "second"]
    assert result["readback_summary"]["truncated_item_count"] == 1


def test_visibility_policy_can_blank_text_risk_evidence_and_labels():
    result = _builder()(
        manual_review_packets=[_packet()],
        readback_policy={
            "include_before_after_text": False,
            "include_risk_flags": False,
            "include_evidence": False,
            "include_action_labels": False,
        },
    )
    item = result["readback_items"][0]
    assert item["current_text"] == ""
    assert item["proposed_text"] == ""
    assert item["risk_flags"] == []
    assert item["jd_terms_supported"] == []
    assert item["resume_evidence_used"] == []
    assert item["operator_action_label"] == ""


def test_groups_by_type_and_action_and_can_disable_groups():
    result = _builder()(
        manual_review_packets=[
            _packet("bullet", "bullet_rewrite", "review_change", 1),
            _packet("summary", "summary_rewrite", "review_risk", 2),
        ]
    )
    assert sorted(result["readback_items_by_type"]) == ["bullet_rewrite", "summary_rewrite"]
    assert sorted(result["readback_items_by_action"]) == ["review_change", "review_risk"]
    disabled = _builder()(
        manual_review_packets=[_packet()],
        readback_policy={
            "group_by_change_type": False,
            "group_by_operator_action": False,
        },
    )
    assert disabled["readback_items_by_type"] == {}
    assert disabled["readback_items_by_action"] == {}


def test_sort_by_display_order_can_preserve_input_order():
    packets = [_packet("second", display_order=2), _packet("first", display_order=1)]
    result = _builder()(
        manual_review_packets=packets,
        readback_policy={"sort_by_display_order": False},
    )
    assert [item["proposal_id"] for item in result["readback_items"]] == ["second", "first"]


def test_input_packets_and_context_are_not_mutated():
    packets = [_packet()]
    context = {"source": {"nested": ["value"]}}
    original_packets = deepcopy(packets)
    original_context = deepcopy(context)
    result = _builder()(manual_review_packets=packets, readback_context=context)
    result["readback_items"][0]["readback_context"]["source"]["nested"].append("changed")
    assert packets == original_packets
    assert context == original_context


def test_payload_has_no_callbacks_full_resume_or_side_effect_commands():
    result = _builder()(manual_review_packets=[_packet()])
    payload_text = repr(result["readback_payload"]).lower()
    forbidden_payload_markers = (
        "callback",
        "function",
        "full_resume",
        "resume_document",
        "overwrite_resume",
        "mutate_resume",
        "submit_application(",
        "database_write",
        "network_request",
        "provider_call(",
    )
    assert "blocked_user_actions" in result["readback_payload"]
    for marker in forbidden_payload_markers:
        if marker == "overwrite_resume" or marker == "mutate_resume":
            assert marker in result["readback_payload"]["blocked_user_actions"]
        else:
            assert marker not in payload_text


def test_helper_source_has_no_forbidden_imports_calls_or_writes():
    source = HELPER_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker.lower() not in lowered
    for marker in FORBIDDEN_WRITE_MARKERS:
        assert marker not in source


def test_docs_include_required_phase_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    required_markers = (
        "phase 48a controlled exact resume change-set manual review readback adapter default-off",
        "controlled exact resume change-set manual review readback adapter",
        "ui api readback payload only",
        "manual review readback only",
        "not a provider call phase",
        "not an llm request phase",
        "not a validation phase",
        "not a normalization phase",
        "not a manual review packet creation phase",
        "not a ui route phase",
        "not an api route phase",
        "does not call llm",
        "does not call provider",
        "does not call network",
        "does not call tailoring runtime",
        "does not create new proposal text",
        "does not create manual review packets",
        "does not overwrite resumes",
        "does not mutate resumes",
        "does not persist data",
        "does not write to database",
        "does not execute applications",
        "does not submit applications",
        "does not add ui routes",
        "does not add api routes",
        "does not perform user acceptance",
        "no auto-apply",
        "no auto-submit",
        "manual user control remains required",
        "phase47-controlled-exact-resume-change-set-manual-review-packet-builder-release-v1",
        "phase47b-controlled-exact-resume-change-set-manual-review-packet-builder-dry-run-command-default-off-v1",
        "phase47a-controlled-exact-resume-change-set-manual-review-packet-builder-default-off-v1",
        "phase46-controlled-exact-resume-change-set-provider-response-normalization-release-v1",
        "phase45-controlled-exact-resume-change-set-provider-response-validation-release-v1",
        "phase44-controlled-exact-resume-change-set-provider-call-boundary-release-v1",
        "phase43-controlled-exact-resume-change-set-llm-request-packet-release-v1",
        "phase42-exact-resume-change-set-proposal-builder-release-v1",
        "phase23-tailoring-agent-workflow-release-v1",
        "phase20d-no-auto-apply-safety-checkpoint-v1",
    )
    for marker in required_markers:
        assert marker in text


def test_protected_runtime_hashes_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_changed_files_are_limited_to_phase48a_contract_surface():
    allowed = {
            "src/app/auth_ui.py",
            "src/app/static/shell.js",
            "src/app/ui_shell.py",
            "src/app/static/media/adv_diagnostics_img.svg",
        "src/app/ui.py",
        "src/app/static/app.js",
        "src/app/static/planning.js",
        "src/app/static/scan_workspace.css",
            "src/app/static/scan_workspace_review.css",
            "src/app/static/styles.css",
        "src/app/static/app_redesign.css",
            "src/app/static/agentic_review.js",
        "tests/test_queue_ui_metadata_contract.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
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

    }
    forbidden_roots = (
        "src/app/api.py",
        "src/app/services.py",
        "src/app/static/",
        "src/pipeline/",
        "src/tailoring/",
        "src/matching/",
        "generate_tailoring_suggestions.py",
        "application_execution_queue.py",
    )
    import subprocess

    completed = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    changed = set(filter(None, completed.stdout.splitlines()))
    changed |= set(filter(None, untracked.stdout.splitlines()))
    allowed |= {
        "src/agents/orchestrator_adapter_harness.py",
            "src/pipeline/collector.py",
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
        "tests/test_phase80b_controlled_advisory_chain_trace_persistence.py",
        }
    profile_allowed_changed_files = {
        "src/config/consts.py",
        "tests/test_phase116a_applied_ai_scoring_fix.py",
        "src/matching/clearance_requirements.py",
        "tests/test_phase117b_ts_clearance_diagnostic.py",
        "jd_resume_diff_helper.py",
        "tests/test_phase118b_ts_clearance_packet_diagnostic.py",
        "src/matching/semantic_similarity.py",
        "tests/test_phase120b_semantic_similarity_diagnostic.py",
            "src/matching/scorer.py",
            "tests/test_phase121b_semantic_alignment_dimension_default_off.py",
    }
    allowed |= profile_allowed_changed_files

    for changed_path in changed:
        if changed_path == "requirements.txt":
            continue
        assert not changed_path.endswith(("requirements.txt", "pyproject.toml", "poetry.lock"))
        assert changed_path in allowed or not any(
            changed_path == root or changed_path.startswith(root)
            for root in forbidden_roots
        )
        assert changed_path in allowed or changed_path.startswith("tests/test_")
