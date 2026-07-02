# phase56b legacy guard marker: changes_only 56d8d73b5891c88ba482fe8a28a634010b5664408ddf35aabcbc89c8aee5005f 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 56d8d73b5891c88ba482fe8a28a634010b5664408ddf35aabcbc89c8aee5005f
from __future__ import annotations

from hashlib import sha256
import csv
import importlib
from io import StringIO
import json
from pathlib import Path
import subprocess

import pytest

import run_controlled_exact_resume_change_set_provider_response_validation_dry_run as command


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = (
    ROOT
    / "run_controlled_exact_resume_change_set_provider_response_validation_dry_run.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase45_controlled_exact_resume_change_set_provider_response_validation_dry_run_command_default_off.md"
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
    "controlled_exact_resume_change_set_provider_response_validation_dry_run",
    "dry_run_command_only",
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
    "validation_result",
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
    "dry_run_summary",
    "dry_run_key",
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
    "phase 45b controlled exact resume change-set provider response validation dry-run command default-off",
    "controlled exact resume change-set provider response validation dry-run command",
    "reads supplied provider response file",
    "reads supplied provider call result file",
    "reads supplied original request packet file",
    "calls the phase 45a controlled exact resume change-set provider response validation helper",
    "prints provider response validation json to stdout",
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
    'python run_controlled_exact_resume_change_set_provider_response_validation_dry_run.py --input path/to/provider_response.json --original-request-packet path/to/request_packet.json',
    "phase45a-controlled-exact-resume-change-set-provider-response-validation-default-off-v1",
    "phase44-controlled-exact-resume-change-set-provider-call-boundary-release-v1",
    "phase44b-controlled-exact-resume-change-set-provider-call-boundary-dry-run-command-default-off-v1",
    "phase44a-controlled-exact-resume-change-set-provider-call-boundary-default-off-v1",
    "phase43-controlled-exact-resume-change-set-llm-request-packet-release-v1",
    "phase42-exact-resume-change-set-proposal-builder-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/controlled_exact_resume_change_set_provider_response_validation_default_off.py": "413ace0d64f8c1bd62726cf7ae32bc4fc8e4b88eca82826492362d9842f569ef",
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


def test_command_module_is_import_safe_and_exposes_functions():
    module = importlib.reload(command)

    assert callable(module.load_provider_response_from_path)
    assert callable(module.load_provider_call_result_from_path)
    assert callable(module.load_original_request_packet_from_path)
    assert callable(module.build_dry_run_payload)
    assert callable(module.main)


def test_provider_response_loader_loads_json_dictionary_and_json_string(tmp_path):
    response = command.load_provider_response_from_path(
        _json(tmp_path / "response.json", _provider_response())
    )
    string_response = command.load_provider_response_from_path(
        _json(tmp_path / "response_string.json", json.dumps(_provider_response()))
    )

    assert response["refined_change_proposals"][0]["proposal_id"] == "p1"
    assert isinstance(string_response, str)


def test_provider_response_loader_loads_raw_txt_jsonl_and_csv(tmp_path):
    txt = command.load_provider_response_from_path(
        _write(tmp_path / "response.txt", "raw response")
    )
    single_jsonl = command.load_provider_response_from_path(
        _jsonl(tmp_path / "single.jsonl", [_provider_response()])
    )
    multi_jsonl = command.load_provider_response_from_path(
        _jsonl(tmp_path / "multi.jsonl", [_proposal(), _proposal(proposal_id="p2")])
    )
    csv_payload = command.load_provider_response_from_path(
        _csv(tmp_path / "rows.csv", [_proposal()])
    )

    assert txt == "raw response"
    assert single_jsonl["refined_change_proposals"][0]["proposal_id"] == "p1"
    assert multi_jsonl["refined_change_proposals"][1]["proposal_id"] == "p2"
    assert csv_payload["refined_change_proposals"][0]["proposal_id"] == "p1"


@pytest.mark.parametrize(
    "payload",
    [
        {"provider_response": _provider_response()},
        {"provider_call_result": {"provider_response": _provider_response()}},
        {
            "phase": "44B",
            "provider_call_result": {"provider_response": _provider_response()},
        },
    ],
)
def test_provider_call_result_loader_loads_json_shapes(tmp_path, payload):
    result = command.load_provider_call_result_from_path(
        _json(tmp_path / "call.json", payload)
    )

    assert isinstance(result, dict)
    assert "provider_response" in result or "provider_call_result" in result


def test_provider_call_result_loader_loads_jsonl_single_row_and_csv_single_row(tmp_path):
    jsonl_result = command.load_provider_call_result_from_path(
        _jsonl(tmp_path / "call.jsonl", [{"provider_response": json.dumps(_provider_response())}])
    )
    csv_result = command.load_provider_call_result_from_path(
        _csv(tmp_path / "call.csv", [{"provider_response": json.dumps(_provider_response())}])
    )

    assert "provider_response" in jsonl_result
    assert "provider_response" in csv_result


@pytest.mark.parametrize(
    "payload",
    [
        _request_packet("p1"),
        {"original_request_packet": _request_packet("p1")},
        {"request_packet": _request_packet("p1")},
        {"request_result": {"request_packet": _request_packet("p1")}},
    ],
)
def test_original_request_packet_loader_loads_json_shapes(tmp_path, payload):
    packet = command.load_original_request_packet_from_path(
        _json(tmp_path / "packet.json", payload)
    )

    assert packet["request_type"] == "exact_resume_change_set_refinement"


def test_original_request_packet_loader_loads_jsonl_single_row_and_csv_single_row(tmp_path):
    assert command.load_original_request_packet_from_path(
        _jsonl(tmp_path / "packet.jsonl", [_request_packet("p1")])
    )["request_type"] == "exact_resume_change_set_refinement"
    assert command.load_original_request_packet_from_path(
        _csv(tmp_path / "packet.csv", [{"request_type": "exact_resume_change_set_refinement"}])
    )["request_type"] == "exact_resume_change_set_refinement"


def test_loader_errors_are_deterministic_for_unsupported_invalid_json_jsonl_and_csv(tmp_path):
    with pytest.raises(command.DryRunLoadError, match="unsupported provider response extension"):
        command.load_provider_response_from_path(_write(tmp_path / "response.yaml", "x"))
    with pytest.raises(command.DryRunLoadError, match="invalid JSON"):
        command.load_provider_response_from_path(_write(tmp_path / "bad.json", "{"))
    with pytest.raises(command.DryRunLoadError, match="invalid JSONL"):
        command.load_provider_response_from_path(_write(tmp_path / "bad.jsonl", "{"))
    with pytest.raises(command.DryRunLoadError, match="invalid CSV"):
        command.load_provider_response_from_path(_write(tmp_path / "bad.csv", "a\n1,2"))


def test_invalid_provider_call_result_and_request_packet_shapes_raise(tmp_path):
    with pytest.raises(command.DryRunLoadError, match="provider call result input"):
        command.load_provider_call_result_from_path(_json(tmp_path / "bad_call.json", {"x": 1}))
    with pytest.raises(command.DryRunLoadError, match="original request packet input"):
        command.load_original_request_packet_from_path(_json(tmp_path / "bad_packet.json", {"x": 1}))


def test_build_dry_run_payload_calls_phase45a_and_returns_required_keys():
    payload = command.build_dry_run_payload(
        provider_response=_provider_response(),
        original_request_packet=_request_packet("p1"),
    )

    assert REQUIRED_KEYS.issubset(payload)
    assert payload["phase"] == "45B"
    assert payload["validation_result"]["phase"] == "45A"
    assert payload["provider_response_valid"] is True
    assert payload["read_only"] is True
    assert payload["validation_only"] is True


def test_invalid_provider_response_returns_validation_payload_not_crash():
    payload = command.build_dry_run_payload(provider_response="raw non-json")

    assert payload["provider_response_valid"] is False
    assert payload["provider_response_parse_status"] == "invalid_json"
    assert payload["validation_errors"]
    assert payload["provider_response_validation_performed"] is True


def test_payload_exposes_validation_artifacts_counts_and_summary():
    payload = command.build_dry_run_payload(provider_response=_provider_response())

    assert isinstance(payload["validation_result"], dict)
    assert isinstance(payload["parsed_provider_response"], dict)
    assert payload["provider_response_parse_status"] == "dict"
    assert payload["validation_errors"] == []
    assert isinstance(payload["validation_warnings"], list)
    assert payload["valid_refined_change_proposal_count"] == 1
    assert payload["invalid_refined_change_proposal_count"] == 0
    assert payload["validation_summary"]["provider_response_valid"] is True


def test_cli_policy_options_are_passed_into_validation_policy(tmp_path, capsys):
    response_path = _json(
        tmp_path / "response.json",
        _provider_response(refined_change_proposals=[], extra="blocked"),
    )

    code = command.main(
        [
            "--input",
            str(response_path),
            "--allow-missing-refined-change-proposals",
            "--require-known-proposal-ids",
            "--disallow-extra-top-level-keys",
            "--allow-empty-refined-change-proposals",
            "--max-refined-change-proposals",
            "2",
            "--max-text-length",
            "10",
            "--skip-required-boolean-safety-flags",
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert code == 0
    assert payload["validation_policy"]["require_refined_change_proposals"] is False
    assert payload["validation_policy"]["require_known_proposal_ids"] is True
    assert payload["validation_policy"]["allow_extra_top_level_keys"] is False
    assert payload["validation_policy"]["allow_empty_refined_change_proposals"] is True
    assert payload["validation_policy"]["max_refined_change_proposals"] == 2
    assert payload["validation_policy"]["max_text_length"] == 10
    assert payload["validation_policy"]["required_boolean_safety_flags"] is False


def test_main_prints_json_to_stdout_for_valid_parsed_input(tmp_path, capsys):
    response_path = _json(tmp_path / "response.json", _provider_response())
    packet_path = _json(tmp_path / "packet.json", _request_packet("p1"))

    code = command.main(
        [
            "--input",
            str(response_path),
            "--original-request-packet",
            str(packet_path),
        ]
    )
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert code == 0
    assert captured.err == ""
    assert payload["provider_response_valid"] is True
    assert payload["known_proposal_ids"] == ["p1"]


def test_main_returns_zero_for_parsed_invalid_provider_response(tmp_path, capsys):
    response_path = _write(tmp_path / "response.txt", "raw non-json")

    code = command.main(["--input", str(response_path)])
    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert code == 0
    assert payload["provider_response_valid"] is False
    assert payload["provider_response_parse_status"] == "invalid_json"


def test_main_returns_nonzero_for_missing_unreadable_or_shape_invalid_input(tmp_path, capsys):
    missing_code = command.main(["--input", str(tmp_path / "missing.json")])
    bad_call = _json(tmp_path / "bad_call.json", {"x": 1})
    response = _json(tmp_path / "response.json", _provider_response())
    shape_code = command.main(
        ["--input", str(response), "--provider-call-result", str(bad_call)]
    )
    captured = capsys.readouterr()

    assert missing_code != 0
    assert shape_code != 0
    assert "error:" in captured.err


def test_command_does_not_write_output_files(tmp_path, capsys):
    before = {path.name for path in tmp_path.iterdir()}
    response_path = _json(tmp_path / "response.json", _provider_response())

    code = command.main(["--input", str(response_path)])
    after = {path.name for path in tmp_path.iterdir()}

    assert code == 0
    assert after == before | {"response.json"}
    assert json.loads(capsys.readouterr().out)["provider_response_valid"] is True


def test_payload_does_not_include_callbacks_function_pointers_or_full_resume():
    payload = command.build_dry_run_payload(provider_response=_provider_response())
    serialized = json.dumps(payload, sort_keys=True).lower()

    assert _contains_callable(payload) is False
    assert "callback" not in serialized
    assert "function_pointer" not in serialized
    assert "full_resume" not in serialized


def test_no_llm_provider_network_tailoring_resume_score_persistence_or_submission():
    payload = command.build_dry_run_payload(provider_response=_provider_response())

    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False
    assert payload["provider_response_validation_performed"] is True
    assert payload["provider_response_normalization_performed"] is False


def test_source_has_no_forbidden_imports_or_runtime_calls_except_phase45a_helper():
    source = COMMAND_PATH.read_text(encoding="utf-8").lower()

    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker.lower() not in source
    assert (
        "build_controlled_exact_resume_change_set_provider_response_validation_default_off"
        in source
    )


def test_source_has_no_forbidden_write_or_mutation_markers():
    source = COMMAND_PATH.read_text(encoding="utf-8")

    for marker in FORBIDDEN_WRITE_MARKERS:
        assert marker not in source


def test_docs_contain_required_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()

    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged_by_hash():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_changed_files_are_limited_to_phase45b_and_legacy_guard_tests():
    changed = {
        line[3:]
        for line in subprocess.run(
            ["git", "status", "--short"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        ).stdout.splitlines()
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
                "\"tests/test_phase66a_human_only_safety_boundary_summary_wiring_default_off 2.py\"",
                "\"tests/test_phase66b_human_only_safety_boundary_summary_readback_ui_api_default_off 2.py\"",
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
