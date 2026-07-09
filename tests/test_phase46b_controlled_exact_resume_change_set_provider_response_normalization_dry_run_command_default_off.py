# phase56b legacy guard marker: changes_only bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only d2e57ab788d69329f46cb31f6fb705ed46af2499ac57001222e1b738de27e004 bfa035faa8e89abd2b75095f68b45a282fb3b7fc8e5ff43e36c754db56ef12c2
from __future__ import annotations

import csv
from hashlib import sha256
import importlib
from io import StringIO
import json
from pathlib import Path
import subprocess

import pytest

import run_controlled_exact_resume_change_set_provider_response_normalization_dry_run as command


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = (
    ROOT
    / "run_controlled_exact_resume_change_set_provider_response_normalization_dry_run.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase46_controlled_exact_resume_change_set_provider_response_normalization_dry_run_command_default_off.md"
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
    "auto_" + "apply_performed",
    "auto_submit_performed",
}

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "controlled_exact_resume_change_set_provider_response_normalization_dry_run",
    "dry_run_command_only",
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
    "normalization_result",
    "provider_response_valid",
    "normalized_refined_change_proposals",
    "normalized_change_proposals_by_type",
    "normalized_change_set_summary",
    "normalization_errors",
    "normalization_warnings",
    "normalization_findings",
    "dry_run_summary",
    "dry_run_key",
    "provider_response_normalization_performed",
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
    "phase 46b controlled exact resume change-set provider response normalization dry-run command default-off",
    "controlled exact resume change-set provider response normalization dry-run command",
    "reads supplied validation result file",
    "reads supplied provider response file",
    "reads supplied original change proposals file",
    "calls the phase 46a controlled exact resume change-set provider response normalization helper",
    "prints provider response normalization json to stdout",
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
    'python run_controlled_exact_resume_change_set_provider_response_normalization_dry_run.py --input path/to/validation_result.json --original-change-proposals path/to/change_proposals.json',
    "phase46a-controlled-exact-resume-change-set-provider-response-normalization-default-off-v1",
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
    "src/agents/controlled_exact_resume_change_set_provider_response_normalization_default_off.py": "bf50f751e501db96bdc30308b3bf162ec61b79111fe79907a9efd126f823206f",
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
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _json(path: Path, payload) -> Path:
    return _write(path, json.dumps(payload))


def _jsonl(path: Path, rows: list[dict]) -> Path:
    return _write(path, "\n".join(json.dumps(row) for row in rows))


def _csv(path: Path, rows: list[dict]) -> Path:
    fieldnames = sorted({key for row in rows for key in row})
    handle = StringIO()
    writer = csv.DictWriter(handle, fieldnames=fieldnames)
    writer.writeheader()
    for row in rows:
        safe_row = {}
        for key in fieldnames:
            safe_row[key] = row.get(key, "")
        writer.writerow(safe_row)
    return _write(path, handle.getvalue())


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


def _provider_response(proposals=None):
    return {
        "refined_change_proposals": proposals if proposals is not None else [_proposal()],
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "application_submission_performed": False,
    }


def _validation_result(*, valid=True, proposals=None):
    response = _provider_response(proposals=proposals)
    return {
        "phase": "45A",
        "provider_response_valid": valid,
        "parsed_provider_response": response,
        "refined_change_proposals": (
            proposals if proposals is not None else response["refined_change_proposals"]
        ),
        "validation_errors": [] if valid else ["invalid"],
        "provider_response_validation_performed": True,
    }


def _contains_callable(value) -> bool:
    if callable(value):
        return True
    if isinstance(value, dict):
        return any(_contains_callable(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_callable(item) for item in value)
    return False


def test_command_module_is_import_safe_and_exposes_required_functions():
    reloaded = importlib.reload(command)

    for name in (
        "load_validation_result_from_path",
        "load_provider_response_from_path",
        "load_original_change_proposals_from_path",
        "build_dry_run_payload",
        "main",
    ):
        assert callable(getattr(reloaded, name))


def test_validation_result_loader_accepts_json_wrapper_refined_jsonl_and_csv(tmp_path):
    validation = _validation_result()

    assert command.load_validation_result_from_path(_json(tmp_path / "v.json", validation)) == validation
    wrapped = {"validation_result": validation, "phase": "45B"}
    assert command.load_validation_result_from_path(_json(tmp_path / "wrapped.json", wrapped)) == wrapped
    refined = {"refined_change_proposals": [_proposal()], "provider_response_valid": True}
    assert command.load_validation_result_from_path(_json(tmp_path / "refined.json", refined)) == refined
    assert command.load_validation_result_from_path(_jsonl(tmp_path / "v.jsonl", [validation])) == validation
    csv_row = {"provider_response_valid": "true", "refined_change_proposals": "[]"}
    assert command.load_validation_result_from_path(_csv(tmp_path / "v.csv", [csv_row])) == csv_row


def test_provider_response_loader_accepts_json_string_txt_jsonl_and_csv(tmp_path):
    response = _provider_response()

    assert command.load_provider_response_from_path(_json(tmp_path / "p.json", response)) == response
    assert command.load_provider_response_from_path(_json(tmp_path / "p_string.json", "raw")) == "raw"
    assert command.load_provider_response_from_path(_write(tmp_path / "p.txt", "raw text")) == "raw text"
    jsonl = command.load_provider_response_from_path(_jsonl(tmp_path / "p.jsonl", [_proposal()]))
    assert jsonl["refined_change_proposals"] == [_proposal()]
    csv_loaded = command.load_provider_response_from_path(_csv(tmp_path / "p.csv", [_proposal()]))
    assert csv_loaded["refined_change_proposals"][0]["proposal_id"] == "p1"


def test_original_change_proposals_loader_accepts_json_containers_jsonl_and_csv(tmp_path):
    rows = [_proposal()]

    assert command.load_original_change_proposals_from_path(_json(tmp_path / "rows.json", rows)) == rows
    assert command.load_original_change_proposals_from_path(
        _json(tmp_path / "wrapped.json", {"change_proposals": rows})
    ) == rows
    assert command.load_original_change_proposals_from_path(_jsonl(tmp_path / "rows.jsonl", rows)) == rows
    csv_loaded = command.load_original_change_proposals_from_path(_csv(tmp_path / "rows.csv", rows))
    assert csv_loaded[0]["proposal_id"] == "p1"


@pytest.mark.parametrize(
    "loader,filename,text",
    (
        (command.load_validation_result_from_path, "bad.yaml", "x"),
        (command.load_provider_response_from_path, "bad.yaml", "x"),
        (command.load_original_change_proposals_from_path, "bad.yaml", "x"),
    ),
)
def test_unsupported_extension_raises_deterministic_error(tmp_path, loader, filename, text):
    with pytest.raises(command.DryRunLoadError, match="unsupported"):
        loader(_write(tmp_path / filename, text))


def test_invalid_json_jsonl_csv_and_shapes_raise_deterministic_errors(tmp_path):
    with pytest.raises(command.DryRunLoadError, match="invalid JSON"):
        command.load_validation_result_from_path(_write(tmp_path / "bad.json", "{"))
    with pytest.raises(command.DryRunLoadError, match="invalid JSONL"):
        command.load_provider_response_from_path(_write(tmp_path / "bad.jsonl", "{"))
    with pytest.raises(command.DryRunLoadError, match="invalid CSV"):
        command.load_original_change_proposals_from_path(
            _write(tmp_path / "bad.csv", "a,b\n1,2,3\n")
        )
    with pytest.raises(command.DryRunLoadError, match="validation result input"):
        command.load_validation_result_from_path(_json(tmp_path / "bad_shape.json", ["x"]))
    with pytest.raises(command.DryRunLoadError, match="original change proposals"):
        command.load_original_change_proposals_from_path(_json(tmp_path / "bad_props.json", {"x": []}))
    with pytest.raises(command.DryRunLoadError, match="provider response jsonl"):
        command.load_provider_response_from_path(_write(tmp_path / "bad_provider.jsonl", "\"x\""))


def test_build_dry_run_payload_returns_required_keys_and_normalized_proposals():
    payload = command.build_dry_run_payload(
        validation_result=_validation_result(),
        original_change_proposals=[_proposal()],
    )

    assert REQUIRED_KEYS <= set(payload)
    assert payload["phase"] == "46B"
    assert payload["default_off"] is True
    assert payload["controlled_exact_resume_change_set_provider_response_normalization_dry_run"] is True
    assert payload["dry_run_command_only"] is True
    assert payload["provider_response_valid"] is True
    assert payload["normalized_refined_change_proposals"]
    assert payload["normalized_change_proposals_by_type"]["bullet"]
    assert payload["normalized_change_set_summary"]["normalized_refined_change_proposal_count"] == 1
    assert payload["normalization_result"]["phase"] == "46A"
    assert payload["dry_run_key"].startswith(
        "phase46b-provider-response-normalization-dry-run-"
    )


def test_invalid_validation_result_yields_blocked_payload_not_crash():
    payload = command.build_dry_run_payload(validation_result=_validation_result(valid=False))

    assert payload["provider_response_valid"] is False
    assert payload["normalization_errors"]
    assert payload["normalized_refined_change_proposals"] == []


def test_payload_safety_flags_and_no_callbacks_or_full_resume():
    payload = command.build_dry_run_payload(validation_result=_validation_result())

    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False
    assert payload["provider_response_validation_performed"] is False
    assert payload["provider_response_normalization_performed"] is True
    assert _contains_callable(payload) is False
    encoded = json.dumps(payload, sort_keys=True).lower()
    assert "full_resume" not in encoded
    assert "callback" not in encoded
    assert "function_pointer" not in encoded
    assert "mutation_command" not in encoded
    assert "db_write_command" not in encoded
    assert "network_request" not in encoded
    assert "application_submission_command" not in encoded


def test_cli_policy_options_are_passed_into_normalization_policy(tmp_path, capsys):
    validation_path = _json(tmp_path / "v.json", _validation_result(valid=False))
    exit_code = command.main(
        [
            "--input",
            str(validation_path),
            "--allow-unvalidated-provider-response",
            "--include-invalid-proposals",
            "--max-normalized-change-proposals",
            "2",
            "--no-trim-text",
            "--max-text-length",
            "10",
            "--drop-before-after-text",
            "--drop-risk-flags",
            "--default-manual-review-required-false",
            "--default-requires-user-acceptance-false",
        ]
    )
    output = capsys.readouterr()
    payload = json.loads(output.out)

    assert exit_code == 0
    assert output.err == ""
    assert payload["normalization_policy"] == {
        "require_valid_provider_response": False,
        "include_invalid_proposals": True,
        "max_normalized_change_proposals": 2,
        "trim_text": False,
        "max_text_length": 10,
        "preserve_before_after_text": False,
        "preserve_risk_flags": False,
        "default_manual_review_required": False,
        "default_requires_user_acceptance": False,
    }


def test_main_prints_json_and_returns_nonzero_for_bad_input(tmp_path, capsys):
    validation_path = _json(tmp_path / "v.json", _validation_result())

    assert command.main(["--input", str(validation_path)]) == 0
    output = capsys.readouterr()
    payload = json.loads(output.out)
    assert payload["phase"] == "46B"
    assert output.err == ""

    assert command.main(["--input", str(tmp_path / "missing.json")]) == 2
    error_output = capsys.readouterr()
    assert error_output.out == ""
    assert "error:" in error_output.err


def test_command_does_not_write_output_files(tmp_path):
    validation_path = _json(tmp_path / "v.json", _validation_result())
    before = {path.name for path in tmp_path.iterdir()}

    assert command.main(["--input", str(validation_path)]) == 0

    after = {path.name for path in tmp_path.iterdir()}
    assert after == before


def test_source_uses_only_phase46a_helper_and_has_no_forbidden_calls():
    source = COMMAND_PATH.read_text(encoding="utf-8").lower()

    assert (
        "build_controlled_exact_resume_change_set_provider_response_normalization_default_off"
        in source
    )
    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source
    for marker in FORBIDDEN_WRITE_MARKERS:
        assert marker not in source


def test_docs_contain_required_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged_by_hash():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_changed_files_are_limited_to_phase46b_and_legacy_guards():
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    changed |= {line.strip() for line in untracked.stdout.splitlines() if line.strip()}
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
    legacy_guards = {
        str(path.relative_to(ROOT))
        for path in (ROOT / "tests").glob("test_*.py")
    }

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
            "tests/test_phase98b_controlled_evidence_chain_execution_default_off.py",
            "tests/test_phase99b_collector_controlled_evidence_chain_execution_default_off.py",
            "tests/test_phase100b_evidence_chain_trace_persistence_readback_default_off.py",
            "tests/test_phase101b_evidence_chain_api_service_readback_default_off.py",
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
    assert changed <= allowed | legacy_guards
