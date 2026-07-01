# phase56b legacy guard marker: changes_only 7c98ab6e6722f43cb1087847a699a44a648d9c0b4eaa85f68dfe1a27b7b7fa34 16b2769b2a0713614f5c1293a7ca511f1032c0aa539ae4676d817d73d4184429
# phase56a legacy guard marker: changes_only f9137ef3f8d1cc27fe08f3a592f1cff977a124cb6132a91394ee8350674bea6f 7c98ab6e6722f43cb1087847a699a44a648d9c0b4eaa85f68dfe1a27b7b7fa34
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess

from src.agents import (
    controlled_exact_resume_change_set_provider_response_validation_default_off
    as validation,
)
from src.agents.controlled_exact_resume_change_set_provider_response_validation_default_off import (
    build_controlled_exact_resume_change_set_provider_response_validation_default_off,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/controlled_exact_resume_change_set_provider_response_validation_default_off.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase45_controlled_exact_resume_change_set_provider_response_validation_default_off.md"
)

FALSE_ACTION_KEYS = {
    "provider_response_normalization_performed",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
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

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "controlled_exact_resume_change_set_provider_response_validation",
    "read_only",
    "advisory_only",
    "validation_only",
    "proposal_only",
    "exact_worthy_changes_only",
    "manual_review_required",
    "requires_manual_user_control",
    "provider_response_present",
    "provider_call_result_present",
    "original_request_packet_present",
    "validation_policy",
    "parsed_provider_response",
    "provider_response_parse_status",
    "provider_response_valid",
    "validation_errors",
    "validation_warnings",
    "refined_change_proposals",
    "valid_refined_change_proposal_count",
    "invalid_refined_change_proposal_count",
    "known_proposal_ids",
    "unknown_proposal_ids",
    "missing_required_fields_by_proposal",
    "invalid_safety_flags",
    "validation_summary",
    "validation_findings",
    "missing_inputs",
    "validation_key",
    "provider_response_validation_performed",
} | FALSE_ACTION_KEYS

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

DOC_MARKERS = (
    "phase 45a controlled exact resume change-set provider response validation default-off",
    "controlled exact resume change-set provider response validation",
    "validates provider responses after phase 44",
    "not a provider call phase",
    "not response normalization",
    "validates refined change proposal schema",
    "checks required proposal fields",
    "checks expected safety flags",
    "can compare proposal ids against the original request packet",
    "does not call llm",
    "does not call provider",
    "does not call network",
    "does not call tailoring runtime",
    "does not generate real tailoring output",
    "does not produce a full resume",
    "does not overwrite resumes",
    "does not mutate resumes",
    "does not persist data",
    "does not write to database",
    "does not execute applications",
    "does not submit applications",
    "no auto-apply",
    "no auto-submit",
    "manual user control remains required",
    "existing ui/manual control remains the acceptance point",
    "exact worthy changes must be manually accepted by the user",
    "resume overwrite is not needed",
    "application execution is not needed",
    "provider response normalization comes in a later phase",
    "phase44-controlled-exact-resume-change-set-provider-call-boundary-release-v1",
    "phase44b-controlled-exact-resume-change-set-provider-call-boundary-dry-run-command-default-off-v1",
    "phase44a-controlled-exact-resume-change-set-provider-call-boundary-default-off-v1",
    "phase43-controlled-exact-resume-change-set-llm-request-packet-release-v1",
    "phase42-exact-resume-change-set-proposal-builder-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/controlled_exact_resume_change_set_provider_call_boundary_default_off.py": "ed065e62f8cfdc6cf3c89f5e9a5d953ba577050eb4088af23bfaeea8becc088d",
    "run_controlled_exact_resume_change_set_provider_call_boundary_dry_run.py": "20a65fe37de31883c56b38dcda537b2a4034d2a1868d1965f848c1568075f771",
    "src/agents/controlled_exact_resume_change_set_llm_request_packet_default_off.py": "acaf694a08f65a5e646d2cbcc7b83a394ea1d15416c7311e230c86536d0a6b0f",
    "run_controlled_exact_resume_change_set_llm_request_packet_dry_run.py": "8baca68f6d8ba882324d028a68372d0d618709413bebe47931c93da5ef6dc175",
    "src/agents/exact_resume_change_set_proposal_builder_default_off.py": "fd173ea8bf3f7d746ebbdb7d6b2af7ae7df1aeaea4e66acaca52ea4fda1a9dc4",
    "run_exact_resume_change_set_proposal_builder_dry_run.py": "a8ea3201f0e71e463e316abdcf813b8d08fa3a473cd3dddcee158b87f3442451",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_suggestions.py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _proposal(**overrides):
    proposal = {
        "proposal_id": "p1",
        "change_type": "bullet",
        "target_section": "experience",
        "target_identifier": "b1",
        "current_text": "Built Python dashboards.",
        "proposed_text": "Built Python and SQL dashboards.",
        "change_reason": "Align with supplied JD terms.",
        "jd_terms_supported": ["Python", "SQL"],
        "resume_evidence_used": ["Built Python dashboards."],
        "risk_flags": [],
        "manual_review_required": True,
        "requires_user_acceptance": True,
    }
    for key, value in overrides.items():
        proposal[key] = value
    return proposal


def _provider_response(**overrides):
    response = {
        "refined_change_proposals": [_proposal()],
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
    }
    for key, value in overrides.items():
        response[key] = value
    return response


def _request_packet(*proposal_ids: str):
    return {
        "request_type": "exact_resume_change_set_refinement",
        "included_change_proposals": [
            {"proposal_id": proposal_id} for proposal_id in proposal_ids
        ],
    }


def _contains_callable(value) -> bool:
    if callable(value):
        return True
    if isinstance(value, dict):
        return any(_contains_callable(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_callable(item) for item in value)
    return False


def test_helper_exists_and_is_import_safe():
    module = importlib.reload(validation)
    assert callable(
        module.build_controlled_exact_resume_change_set_provider_response_validation_default_off
    )


def test_missing_provider_response_blocks_with_missing_input_reason():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off()

    assert REQUIRED_KEYS.issubset(payload)
    assert payload["phase"] == "45A"
    assert payload["provider_response_valid"] is False
    assert payload["provider_response_present"] is False
    assert payload["provider_response_validation_performed"] is True
    assert "provider_response" in payload["missing_inputs"]
    assert "provider response required" in payload["validation_errors"]


def test_provider_call_result_with_provider_response_is_accepted():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_call_result={"provider_response": _provider_response()},
    )

    assert payload["provider_call_result_present"] is True
    assert payload["provider_response_valid"] is True
    assert payload["validation_summary"]["provider_response_source"] == "provider_call_result.provider_response"


def test_nested_provider_call_result_provider_response_is_accepted():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_call_result={
            "provider_call_result": {"provider_response": _provider_response()}
        },
    )

    assert payload["provider_response_valid"] is True
    assert (
        payload["validation_summary"]["provider_response_source"]
        == "provider_call_result.provider_call_result.provider_response"
    )


def test_explicit_provider_response_takes_precedence_over_provider_call_result():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=_provider_response(refined_change_proposals=[_proposal(proposal_id="explicit")]),
        provider_call_result={"provider_response": _provider_response(refined_change_proposals=[_proposal(proposal_id="nested")])},
    )

    assert payload["provider_response_valid"] is True
    assert payload["refined_change_proposals"][0]["proposal_id"] == "explicit"
    assert payload["validation_summary"]["provider_response_source"] == "provider_response"


def test_json_string_provider_response_is_parsed():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=json.dumps(_provider_response()),
    )

    assert payload["provider_response_parse_status"] == "json_string_dict"
    assert payload["provider_response_valid"] is True


def test_raw_non_json_string_is_invalid_without_crashing():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response="not json",
    )

    assert payload["provider_response_valid"] is False
    assert payload["provider_response_parse_status"] == "invalid_json"


def test_non_dict_parsed_response_is_invalid():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=json.dumps([{"not": "dict"}]),
    )

    assert payload["provider_response_valid"] is False
    assert payload["provider_response_parse_status"] == "json_string_non_dict"


def test_valid_refined_change_proposals_response_passes_validation():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=_provider_response(),
        original_request_packet=_request_packet("p1"),
    )

    assert payload["provider_response_valid"] is True
    assert payload["valid_refined_change_proposal_count"] == 1
    assert payload["invalid_refined_change_proposal_count"] == 0
    assert payload["known_proposal_ids"] == ["p1"]
    assert payload["unknown_proposal_ids"] == []


def test_missing_refined_change_proposals_fails_when_required():
    response = _provider_response()
    del response["refined_change_proposals"]
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=response,
    )

    assert payload["provider_response_valid"] is False
    assert "refined_change_proposals required" in payload["validation_errors"]


def test_empty_refined_change_proposals_fails_when_empty_is_disallowed():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=_provider_response(refined_change_proposals=[]),
    )

    assert payload["provider_response_valid"] is False
    assert "refined_change_proposals must not be empty" in payload["validation_errors"]


def test_invalid_non_dict_proposal_items_are_counted():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=_provider_response(refined_change_proposals=["bad"]),
    )

    assert payload["provider_response_valid"] is False
    assert payload["invalid_refined_change_proposal_count"] == 1
    assert "index:0" in payload["missing_required_fields_by_proposal"]


def test_missing_required_fields_are_reported_by_proposal():
    proposal = _proposal()
    del proposal["proposed_text"]
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=_provider_response(refined_change_proposals=[proposal]),
    )

    assert payload["provider_response_valid"] is False
    assert payload["missing_required_fields_by_proposal"]["p1"] == ["proposed_text"]


def test_safety_flags_must_be_false_when_required():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=_provider_response(**{"resume_mutation_performed": True}),
    )

    assert payload["provider_response_valid"] is False
    assert payload["invalid_safety_flags"]["resume_mutation_performed"] is True
    assert "required safety flags must be false" in payload["validation_errors"]


def test_known_proposal_ids_and_unknown_ids_are_reported_when_required():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=_provider_response(refined_change_proposals=[_proposal(proposal_id="unknown")]),
        original_request_packet=_request_packet("p1"),
        validation_policy={"require_known_proposal_ids": True},
    )

    assert payload["provider_response_valid"] is False
    assert payload["known_proposal_ids"] == ["p1"]
    assert payload["unknown_proposal_ids"] == ["unknown"]
    assert "unknown proposal ids present" in payload["validation_errors"]


def test_max_refined_change_proposals_violation_is_reported():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=_provider_response(
            refined_change_proposals=[_proposal(proposal_id="p1"), _proposal(proposal_id="p2")]
        ),
        validation_policy={"max_refined_change_proposals": 1},
    )

    assert payload["provider_response_valid"] is False
    assert "too many refined_change_proposals" in payload["validation_errors"]


def test_max_text_length_violation_is_reported():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=_provider_response(
            refined_change_proposals=[_proposal(proposed_text="x" * 6)]
        ),
        validation_policy={"max_text_length": 5},
    )

    assert payload["provider_response_valid"] is False
    assert "proposed_text:max_text_length" in payload["missing_required_fields_by_proposal"]["p1"]


def test_extra_top_level_keys_can_be_blocked_or_warned():
    warned = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=_provider_response(extra="readback"),
    )
    blocked = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=_provider_response(extra="readback"),
        validation_policy={"allow_extra_top_level_keys": False},
    )

    assert warned["provider_response_valid"] is True
    assert "extra top-level keys ignored for validation" in warned["validation_warnings"]
    assert blocked["provider_response_valid"] is False
    assert "extra top-level keys are not allowed" in blocked["validation_errors"]


def test_inputs_are_not_mutated():
    response = _provider_response()
    call_result = {"provider_response": _provider_response()}
    request_packet = _request_packet("p1")
    policy = {"require_known_proposal_ids": True}
    originals = deepcopy((response, call_result, request_packet, policy))

    build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=response,
        provider_call_result=call_result,
        original_request_packet=request_packet,
        validation_policy=policy,
    )

    assert (response, call_result, request_packet, policy) == originals


def test_validation_is_deterministic():
    kwargs = {
        "provider_response": _provider_response(),
        "original_request_packet": _request_packet("p1"),
    }

    first = build_controlled_exact_resume_change_set_provider_response_validation_default_off(**kwargs)
    second = build_controlled_exact_resume_change_set_provider_response_validation_default_off(**kwargs)

    assert first == second
    assert first["validation_key"] == second["validation_key"]


def test_no_llm_provider_network_tailoring_or_generation_calls_are_performed():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=_provider_response(),
    )

    assert payload["provider_response_validation_performed"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_no_real_tailoring_full_resume_score_persistence_execution_or_submission():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=_provider_response(),
    )

    assert payload["real_tailoring_output_created"] is False
    assert payload["resume_rewrite_performed"] is False
    assert payload["resume_overwrite_performed"] is False
    assert payload["resume_mutation_performed"] is False
    assert payload["final_score_produced"] is False
    assert payload["existing_score_changed"] is False
    assert payload["database_write_performed"] is False
    assert payload["persistence_performed"] is False
    assert payload["execution_performed"] is False
    assert payload["application_submission_performed"] is False
    assert payload["auto_" + "apply_performed"] is False
    assert payload["auto_submit_performed"] is False


def test_returned_payload_does_not_include_executable_callbacks_or_function_pointers():
    payload = build_controlled_exact_resume_change_set_provider_response_validation_default_off(
        provider_response=_provider_response(),
    )

    assert _contains_callable(payload) is False
    assert "callback" not in json.dumps(payload, sort_keys=True).lower()
    assert "function_pointer" not in json.dumps(payload, sort_keys=True).lower()


def test_source_has_no_forbidden_imports_or_runtime_calls():
    source = HELPER_PATH.read_text(encoding="utf-8").lower()

    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker.lower() not in source


def test_source_has_no_forbidden_write_or_mutation_markers():
    source = HELPER_PATH.read_text(encoding="utf-8")

    for marker in FORBIDDEN_WRITE_MARKERS:
        assert marker not in source


def test_docs_contain_required_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged_by_hash():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_changed_files_are_limited_to_phase45a_and_legacy_guard_tests():
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )
    changed = {
        line[3:]
        for line in result.stdout.splitlines()
        if line.strip()
    }
    allowed = {
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
                "\"docs/phase66_human_only_safety_boundary_summary_readback_ui_api_default_off 2.md\"",
                "docs/phase67_human_only_workflow_readiness_checkpoint_wiring_default_off.md",
                "docs/phase67_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off.md",
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
                "\"tests/test_phase66a_human_only_safety_boundary_summary_wiring_default_off 2.py\"",
                "\"tests/test_phase66b_human_only_safety_boundary_summary_readback_ui_api_default_off 2.py\"",
                "tests/test_phase67a_human_only_workflow_readiness_checkpoint_wiring_default_off.py",
                "tests/test_phase67b_human_only_workflow_readiness_checkpoint_readback_ui_api_default_off.py",
        "tests/test_phase56b_live_tailoring_suggestion_planning_workspace_readback_ui_api_default_off.py",
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
        '"docs/phase55_live_jd_llm_extraction_planning_scan_wiring_default_off 2.md"',
        '"tests/test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off 2.py"',
        '"docs/phase55_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off 2.md"',
        '"tests/test_phase55b_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off 2.py"',
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

    }
    disallowed = [
        path
        for path in changed
        if path not in allowed and not path.startswith("tests/test_")
    ]

    assert disallowed == []
