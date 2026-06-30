from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess

from src.agents import (
    controlled_exact_resume_change_set_provider_response_normalization_default_off
    as normalization,
)
from src.agents.controlled_exact_resume_change_set_provider_response_normalization_default_off import (
    build_controlled_exact_resume_change_set_provider_response_normalization_default_off,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/controlled_exact_resume_change_set_provider_response_normalization_default_off.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase46_controlled_exact_resume_change_set_provider_response_normalization_default_off.md"
)

FALSE_ACTION_KEYS = {
    "provider_response_validation_performed",
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
    "auto_apply_performed",
    "auto_submit_performed",
}

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "controlled_exact_resume_change_set_provider_response_normalization",
    "read_only",
    "advisory_only",
    "normalization_only",
    "proposal_only",
    "exact_worthy_changes_only",
    "manual_review_required",
    "requires_manual_user_control",
    "validation_result_present",
    "provider_response_present",
    "original_change_proposals_present",
    "normalization_policy",
    "provider_response_valid",
    "normalized_refined_change_proposals",
    "normalized_change_proposals_by_type",
    "normalized_change_set_summary",
    "normalization_errors",
    "normalization_warnings",
    "normalization_findings",
    "missing_inputs",
    "normalization_key",
    "provider_response_normalization_performed",
} | FALSE_ACTION_KEYS

NORMALIZED_PROPOSAL_KEYS = {
    "proposal_id",
    "change_type",
    "target_section",
    "target_identifier",
    "current_text",
    "proposed_text",
    "change_reason",
    "jd_terms_supported",
    "resume_evidence_used",
    "risk_flags",
    "manual_review_required",
    "requires_user_acceptance",
    "source_validation_status",
    "normalization_notes",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "application_submission_performed",
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

DOC_MARKERS = (
    "phase 46a controlled exact resume change-set provider response normalization default-off",
    "controlled exact resume change-set provider response normalization",
    "normalizes provider responses after phase 45 validation",
    "not a provider call phase",
    "not a validation phase",
    "normalizes validated refined change proposals",
    "preserves manual review and user acceptance requirements",
    "produces normalized proposal-only output",
    "does not create new proposal text",
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
    "ui/manual review readback comes in a later phase",
    "phase45-controlled-exact-resume-change-set-provider-response-validation-release-v1",
    "phase45b-controlled-exact-resume-change-set-provider-response-validation-dry-run-command-default-off-v1",
    "phase45a-controlled-exact-resume-change-set-provider-response-validation-default-off-v1",
    "phase44-controlled-exact-resume-change-set-provider-call-boundary-release-v1",
    "phase43-controlled-exact-resume-change-set-llm-request-packet-release-v1",
    "phase42-exact-resume-change-set-proposal-builder-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/controlled_exact_resume_change_set_provider_response_validation_default_off.py": "413ace0d64f8c1bd62726cf7ae32bc4fc8e4b88eca82826492362d9842f569ef",
    "run_controlled_exact_resume_change_set_provider_response_validation_dry_run.py": "52351a639821afc4a042be7350514be33bd4f8fa5fbb714eda9d19aa45c0f0d4",
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
        "current_text": " Built Python dashboards. ",
        "proposed_text": " Built Python and SQL dashboards. ",
        "change_reason": " Align with supplied JD terms. ",
        "jd_terms_supported": [" Python ", "SQL", "python"],
        "resume_evidence_used": [" Built Python dashboards. "],
        "risk_flags": ["manual_review"],
        "manual_review_required": True,
        "requires_user_acceptance": True,
    }
    for key, value in overrides.items():
        proposal[key] = value
    return proposal


def _provider_response(proposals=None, **overrides):
    response = {
        "refined_change_proposals": proposals if proposals is not None else [_proposal()],
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
    }
    for key, value in overrides.items():
        response[key] = value
    return response


def _validation_result(*, valid=True, proposals=None, **overrides):
    response = _provider_response(proposals=proposals)
    result = {
        "phase": "45A",
        "provider_response_valid": valid,
        "parsed_provider_response": response,
        "refined_change_proposals": (
            proposals if proposals is not None else response["refined_change_proposals"]
        ),
        "validation_errors": [] if valid else ["invalid"],
        "provider_response_validation_performed": True,
    }
    for key, value in overrides.items():
        result[key] = value
    return result


def _contains_callable(value) -> bool:
    if callable(value):
        return True
    if isinstance(value, dict):
        return any(_contains_callable(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_callable(item) for item in value)
    return False


def test_helper_exists_and_is_import_safe():
    module = importlib.reload(normalization)
    assert callable(
        module.build_controlled_exact_resume_change_set_provider_response_normalization_default_off
    )


def test_missing_validation_result_or_provider_response_blocks_with_missing_input_reason():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off()

    assert REQUIRED_KEYS.issubset(payload)
    assert payload["phase"] == "46A"
    assert payload["normalized_refined_change_proposals"] == []
    assert "validation_result_or_provider_response" in payload["missing_inputs"]
    assert "validation result or provider response required" in payload["normalization_errors"]


def test_phase45_validation_result_is_accepted():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(),
    )

    assert payload["validation_result_present"] is True
    assert payload["provider_response_valid"] is True
    assert payload["normalized_refined_change_proposals"][0]["proposal_id"] == "p1"


def test_phase45b_nested_validation_result_is_accepted():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result={"phase": "45B", "validation_result": _validation_result()},
    )

    assert payload["validation_result_present"] is True
    assert payload["normalized_refined_change_proposals"][0]["source_validation_status"] == "valid"


def test_explicit_validation_result_takes_precedence_over_provider_response():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(proposals=[_proposal(proposal_id="from-validation")]),
        provider_response=_provider_response(proposals=[_proposal(proposal_id="from-provider")]),
    )

    assert payload["normalized_refined_change_proposals"][0]["proposal_id"] == "from-validation"


def test_provider_response_can_normalize_only_when_require_valid_provider_response_is_false():
    blocked = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        provider_response=_provider_response(),
    )
    allowed = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        provider_response=_provider_response(),
        normalization_policy={"require_valid_provider_response": False},
    )

    assert blocked["normalized_refined_change_proposals"] == []
    assert "validated provider response required before normalization" in blocked["normalization_errors"]
    assert allowed["normalized_refined_change_proposals"][0]["source_validation_status"] == "unvalidated"


def test_invalid_validation_result_blocks_normalization_by_default():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(valid=False),
    )

    assert payload["provider_response_valid"] is False
    assert payload["normalized_refined_change_proposals"] == []
    assert "valid provider response required before normalization" in payload["normalization_errors"]


def test_valid_refined_change_proposals_are_normalized_with_required_fields_and_safety_flags():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(),
    )
    proposal = payload["normalized_refined_change_proposals"][0]

    assert NORMALIZED_PROPOSAL_KEYS.issubset(proposal)
    assert proposal["current_text"] == "Built Python dashboards."
    assert proposal["proposed_text"] == "Built Python and SQL dashboards."
    assert proposal["resume_overwrite_performed"] is False
    assert proposal["resume_mutation_performed"] is False
    assert proposal["application_submission_performed"] is False


def test_invalid_non_dict_proposals_are_counted_reported_and_excluded_by_default():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(proposals=["bad"]),
    )

    assert payload["normalized_refined_change_proposals"] == []
    assert payload["normalized_change_set_summary"]["invalid_refined_change_proposal_count"] == 1
    assert payload["normalized_change_set_summary"]["excluded_invalid_refined_change_proposal_count"] == 1


def test_include_invalid_proposals_policy_is_deterministic():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(proposals=["bad"]),
        normalization_policy={"include_invalid_proposals": True},
    )

    proposal = payload["normalized_refined_change_proposals"][0]
    assert proposal["proposal_id"] == "index:0"
    assert "proposal item was not a dictionary" in proposal["normalization_notes"]
    assert payload == build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(proposals=["bad"]),
        normalization_policy={"include_invalid_proposals": True},
    )


def test_max_normalized_change_proposals_truncates_deterministically():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(
            proposals=[_proposal(proposal_id="p1"), _proposal(proposal_id="p2")]
        ),
        normalization_policy={"max_normalized_change_proposals": 1},
    )

    assert [row["proposal_id"] for row in payload["normalized_refined_change_proposals"]] == ["p1"]
    assert payload["normalized_change_set_summary"]["truncated_by_policy_limit"] is True


def test_trim_text_policy_trims_strings():
    trimmed = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(),
    )
    untrimmed = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(),
        normalization_policy={"trim_text": False},
    )

    assert trimmed["normalized_refined_change_proposals"][0]["target_identifier"] == "b1"
    assert untrimmed["normalized_refined_change_proposals"][0]["current_text"].startswith(" ")


def test_max_text_length_warnings_are_reported_and_text_is_truncated():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(
            proposals=[_proposal(proposed_text="x" * 10)]
        ),
        normalization_policy={"max_text_length": 5},
    )

    assert payload["normalized_refined_change_proposals"][0]["proposed_text"] == "xxxxx"
    assert any("proposed_text:truncated" in warning for warning in payload["normalization_warnings"])


def test_list_like_fields_are_normalized_deterministically():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(
            proposals=[
                _proposal(
                    jd_terms_supported={"b": [" SQL "], "a": "Python"},
                    resume_evidence_used=(" Evidence ", "Evidence"),
                    risk_flags=[" Risk ", "risk"],
                )
            ]
        ),
    )
    proposal = payload["normalized_refined_change_proposals"][0]

    assert proposal["jd_terms_supported"] == ["Python", "SQL"]
    assert proposal["resume_evidence_used"] == ["Evidence"]
    assert proposal["risk_flags"] == ["Risk"]


def test_normalized_change_proposals_by_type_groups_by_change_type():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(
            proposals=[
                _proposal(proposal_id="p1", change_type="bullet"),
                _proposal(proposal_id="p2", change_type="skill"),
            ]
        ),
    )

    assert list(payload["normalized_change_proposals_by_type"].keys()) == ["bullet", "skill"]
    assert payload["normalized_change_set_summary"]["counts_by_type"] == {"bullet": 1, "skill": 1}


def test_normalized_change_set_summary_includes_counts_and_safety_flags():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(),
        original_change_proposals={"change_proposals": [{"proposal_id": "p1"}]},
    )
    summary = payload["normalized_change_set_summary"]

    assert summary["normalized_refined_change_proposal_count"] == 1
    assert summary["known_original_change_proposal_ids"] == ["p1"]
    assert summary["resume_overwrite_performed"] is False
    assert summary["resume_mutation_performed"] is False
    assert summary["application_submission_performed"] is False


def test_manual_review_required_and_requires_user_acceptance_remain_true():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(
            proposals=[_proposal(manual_review_required=False, requires_user_acceptance=False)]
        ),
    )
    proposal = payload["normalized_refined_change_proposals"][0]

    assert proposal["manual_review_required"] is True
    assert proposal["requires_user_acceptance"] is True
    assert payload["manual_review_required"] is True
    assert payload["requires_manual_user_control"] is True


def test_inputs_are_not_mutated():
    validation_result = _validation_result()
    provider_response = _provider_response()
    original_change_proposals = [_proposal()]
    policy = {"max_text_length": 20}
    originals = deepcopy(
        (validation_result, provider_response, original_change_proposals, policy)
    )

    build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=validation_result,
        provider_response=provider_response,
        original_change_proposals=original_change_proposals,
        normalization_policy=policy,
    )

    assert (validation_result, provider_response, original_change_proposals, policy) == originals


def test_no_llm_provider_network_tailoring_or_generation_calls_are_performed():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(),
    )

    assert payload["provider_response_validation_performed"] is False
    assert payload["provider_response_normalization_performed"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_no_full_resume_score_persistence_execution_submission_auto_apply_or_auto_submit():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(),
    )

    assert payload["real_tailoring_output_created"] is False
    assert payload["resume_rewrite_performed"] is False
    assert payload["resume_overwrite_performed"] is False
    assert payload["resume_mutation_performed"] is False
    assert payload["final_score_produced"] is False
    assert payload["database_write_performed"] is False
    assert payload["persistence_performed"] is False
    assert payload["execution_performed"] is False
    assert payload["application_submission_performed"] is False
    assert payload["auto_apply_performed"] is False
    assert payload["auto_submit_performed"] is False
    assert "full_resume" not in json.dumps(payload, sort_keys=True).lower()


def test_returned_payload_does_not_include_executable_callbacks_or_function_pointers():
    payload = build_controlled_exact_resume_change_set_provider_response_normalization_default_off(
        validation_result=_validation_result(),
    )

    assert _contains_callable(payload) is False
    serialized = json.dumps(payload, sort_keys=True).lower()
    assert "callback" not in serialized
    assert "function_pointer" not in serialized


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


def test_changed_files_are_limited_to_phase46a_and_legacy_guard_tests():
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

    }
    disallowed = [
        path
        for path in changed
        if path not in allowed and not path.startswith("tests/test_")
    ]

    assert disallowed == []
