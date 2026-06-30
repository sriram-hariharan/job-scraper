from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

import run_controlled_exact_resume_change_set_provider_call_boundary_dry_run as command


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = (
    ROOT / "run_controlled_exact_resume_change_set_provider_call_boundary_dry_run.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase44_controlled_exact_resume_change_set_provider_call_boundary_dry_run_command_default_off.md"
)

FALSE_ACTION_KEYS = {
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
    "controlled_exact_resume_change_set_provider_call_boundary_dry_run",
    "dry_run_command_only",
    "read_only",
    "advisory_only",
    "proposal_only",
    "provider_call_boundary_only",
    "exact_worthy_changes_only",
    "manual_review_required",
    "requires_manual_user_control",
    "manual_trigger_required",
    "manual_trigger_confirmed",
    "request_packet_present",
    "request_result_present",
    "provider_response_fixture_present",
    "simulated_provider_callable_available",
    "enable_provider_call",
    "provider_policy",
    "provider_call_result",
    "provider_response",
    "provider_response_present",
    "provider_response_type",
    "provider_response_summary",
    "provider_call_blocked_reason",
    "dry_run_summary",
    "dry_run_key",
    "provider_call_attempted",
    "provider_call_performed",
    "llm_call_performed",
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
    "phase 44b controlled exact resume change-set provider call boundary dry-run command default-off",
    "controlled exact resume change-set provider call boundary dry-run command",
    "reads supplied request packet file",
    "reads supplied request result file",
    "reads supplied provider response fixture file",
    "calls the phase 44a controlled exact resume change-set provider call boundary",
    "prints provider call boundary json to stdout",
    "default behavior does not call provider",
    "provider call is explicit/manual-triggered only",
    "simulated provider response fixture as an injected local callable",
    "simulated provider callable is not a real provider sdk call",
    "does not import provider sdks",
    "does not call network directly",
    "keeps network_call_performed false",
    "does not call tailoring runtime",
    "does not generate real tailoring output by itself",
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
    "provider response validation comes in a later phase",
    'python run_controlled_exact_resume_change_set_provider_call_boundary_dry_run.py --input path/to/request_packet.json',
    "phase44a-controlled-exact-resume-change-set-provider-call-boundary-default-off-v1",
    "phase43-controlled-exact-resume-change-set-llm-request-packet-release-v1",
    "phase43b-controlled-exact-resume-change-set-llm-request-packet-dry-run-command-default-off-v1",
    "phase43a-controlled-exact-resume-change-set-llm-request-packet-default-off-v1",
    "phase42-exact-resume-change-set-proposal-builder-release-v1",
    "phase42b-exact-resume-change-set-proposal-builder-dry-run-command-default-off-v1",
    "phase42a-exact-resume-change-set-proposal-builder-default-off-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/controlled_exact_resume_change_set_provider_call_boundary_default_off.py": "ed065e62f8cfdc6cf3c89f5e9a5d953ba577050eb4088af23bfaeea8becc088d",
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


def _json(path: Path, payload) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _jsonl(path: Path, rows: list[dict]) -> Path:
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    return path


def _csv(path: Path, rows: list[dict]) -> Path:
    fieldnames = sorted({key for row in rows for key in row})
    lines = [",".join(fieldnames)]
    for row in rows:
        lines.append(",".join(str(row.get(key, "")) for key in fieldnames))
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _request_packet(**overrides):
    packet = {
        "request_type": "exact_resume_change_set_refinement",
        "manual_trigger_required": True,
        "response_format": "json",
        "temperature": 0,
        "request_messages": [{"role": "user", "content": {"change_proposals": []}}],
        "request_schema": {"type": "object"},
        "provider_call_performed": False,
        "network_call_performed": False,
    }
    for key, value in overrides.items():
        packet[key] = value
    return packet


def test_command_module_is_import_safe_and_exposes_functions():
    module = importlib.reload(command)
    assert callable(module.load_request_packet_from_path)
    assert callable(module.load_request_result_from_path)
    assert callable(module.load_provider_response_fixture_from_path)
    assert callable(module.build_dry_run_payload)
    assert callable(module.main)


@pytest.mark.parametrize(
    "filename,payload",
    [
        ("packet.json", _request_packet()),
        ("wrapped.json", {"request_packet": _request_packet(request_id="wrapped")}),
        ("nested.json", {"request_result": {"request_packet": _request_packet(request_id="nested")}}),
    ],
)
def test_request_packet_loader_loads_json_shapes(tmp_path, filename, payload):
    packet = command.load_request_packet_from_path(_json(tmp_path / filename, payload))
    assert packet["request_type"] == "exact_resume_change_set_refinement"


def test_request_packet_loader_loads_jsonl_single_row_and_csv_single_row(tmp_path):
    assert command.load_request_packet_from_path(
        _jsonl(tmp_path / "packet.jsonl", [_request_packet()])
    )["request_type"] == "exact_resume_change_set_refinement"
    assert command.load_request_packet_from_path(
        _csv(tmp_path / "packet.csv", [{"request_type": "exact_resume_change_set_refinement"}])
    )["request_type"] == "exact_resume_change_set_refinement"


@pytest.mark.parametrize(
    "filename,payload",
    [
        ("result.json", {"request_packet": _request_packet()}),
        ("dryrun.json", {"request_result": {"request_packet": _request_packet()}}),
        ("packet.json", _request_packet()),
    ],
)
def test_request_result_loader_loads_json_shapes(tmp_path, filename, payload):
    result = command.load_request_result_from_path(_json(tmp_path / filename, payload))
    assert isinstance(result, dict)
    assert "request_packet" in result


def test_request_result_loader_loads_jsonl_single_row_and_csv_single_row(tmp_path):
    assert "request_packet" in command.load_request_result_from_path(
        _jsonl(tmp_path / "result.jsonl", [{"request_packet": _request_packet()}])
    )
    assert "request_packet" in command.load_request_result_from_path(
        _csv(tmp_path / "result.csv", [{"request_type": "exact_resume_change_set_refinement"}])
    )


def test_provider_response_fixture_loader_loads_json_jsonl_and_csv(tmp_path):
    assert command.load_provider_response_fixture_from_path(
        _json(tmp_path / "fixture.json", {"ok": True})
    ) == {"ok": True}
    assert command.load_provider_response_fixture_from_path(
        _json(tmp_path / "fixture-list.json", [{"ok": True}])
    ) == [{"ok": True}]
    assert "fixture_rows" in command.load_provider_response_fixture_from_path(
        _jsonl(tmp_path / "fixture.jsonl", [{"ok": True}, {"ok": False}])
    )
    assert "fixture_rows" in command.load_provider_response_fixture_from_path(
        _csv(tmp_path / "fixture.csv", [{"ok": "true"}])
    )


@pytest.mark.parametrize(
    "loader,filename,writer,error",
    [
        (command.load_request_packet_from_path, "packet.txt", lambda path: path.write_text("{}", encoding="utf-8"), "unsupported"),
        (command.load_request_packet_from_path, "packet.json", lambda path: path.write_text("{", encoding="utf-8"), "invalid JSON"),
        (command.load_request_packet_from_path, "packet.jsonl", lambda path: path.write_text("{", encoding="utf-8"), "invalid JSONL"),
        (command.load_request_packet_from_path, "packet.csv", lambda path: path.write_text("a,b\n1,2,3", encoding="utf-8"), "extra columns"),
        (command.load_request_packet_from_path, "packet.json", lambda path: path.write_text(json.dumps(["bad"]), encoding="utf-8"), "JSON object"),
        (command.load_request_result_from_path, "result.json", lambda path: path.write_text(json.dumps({"no_packet": True}), encoding="utf-8"), "request_result or request_packet"),
        (command.load_provider_response_fixture_from_path, "fixture.txt", lambda path: path.write_text("{}", encoding="utf-8"), "unsupported"),
        (command.load_provider_response_fixture_from_path, "fixture.jsonl", lambda path: path.write_text("[]", encoding="utf-8"), "JSON object"),
    ],
)
def test_loader_errors_are_deterministic(tmp_path, loader, filename, writer, error):
    path = tmp_path / filename
    writer(path)
    with pytest.raises(command.DryRunLoadError, match=error):
        loader(path)


def test_build_dry_run_payload_calls_phase44a_and_returns_required_flags():
    payload = command.build_dry_run_payload(request_packet=_request_packet())

    assert REQUIRED_KEYS.issubset(payload)
    assert payload["phase"] == "44B"
    assert payload["default_off"] is True
    assert payload["request_packet_present"] is True
    assert payload["request_result_present"] is False
    assert payload["provider_response_fixture_present"] is False
    assert payload["simulated_provider_callable_available"] is False
    assert payload["provider_call_performed"] is False
    assert payload["llm_call_performed"] is False
    assert payload["network_call_performed"] is False
    assert payload["provider_call_result"]["status"] == "provider_call_blocked"


def test_default_payload_does_not_call_provider_even_with_fixture():
    payload = command.build_dry_run_payload(
        request_packet=_request_packet(),
        provider_response_fixture={"ok": True},
    )

    assert payload["simulated_provider_callable_available"] is True
    assert payload["provider_response_present"] is False
    assert payload["provider_call_attempted"] is False
    assert payload["provider_call_performed"] is False


@pytest.mark.parametrize(
    "enable,confirmed,allowed",
    [
        (False, True, True),
        (True, False, True),
        (True, True, False),
    ],
)
def test_simulated_callable_not_called_unless_all_gates_pass(enable, confirmed, allowed):
    payload = command.build_dry_run_payload(
        request_packet=_request_packet(),
        provider_response_fixture={"ok": True},
        enable_provider_call=enable,
        manual_trigger_confirmed=confirmed,
        provider_policy={"allow_provider_call": allowed},
    )

    assert payload["provider_call_performed"] is False
    assert payload["llm_call_performed"] is False
    assert payload["provider_response_present"] is False
    assert payload["network_call_performed"] is False


def test_simulated_fixture_is_captured_only_when_all_gates_pass():
    fixture = {"refined_change_proposals": [{"proposal_id": "p1"}]}
    payload = command.build_dry_run_payload(
        request_packet=_request_packet(),
        provider_response_fixture=fixture,
        enable_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy={"allow_provider_call": True},
    )

    assert payload["provider_call_attempted"] is True
    assert payload["provider_call_performed"] is True
    assert payload["llm_call_performed"] is True
    assert payload["network_call_performed"] is False
    assert payload["provider_response"] == fixture
    assert payload["provider_response_summary"]["provider_response_validation_performed"] is False


def test_request_result_can_drive_boundary_when_packet_not_explicit():
    payload = command.build_dry_run_payload(
        request_result={"request_packet": _request_packet()},
        provider_response_fixture={"ok": True},
        enable_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy={"allow_provider_call": True},
    )

    assert payload["request_packet_present"] is False
    assert payload["request_result_present"] is True
    assert payload["provider_call_performed"] is True


def test_cli_policy_options_are_passed_into_provider_policy(tmp_path, capsys):
    packet = _json(tmp_path / "packet.json", _request_packet())
    fixture = _json(tmp_path / "fixture.json", {"ok": True})

    code = command.main(
        [
            "--input",
            str(packet),
            "--provider-response-fixture",
            str(fixture),
            "--enable-provider-call",
            "--manual-trigger-confirmed",
            "--allow-provider-call",
            "--no-capture-raw-response",
            "--max-response-chars",
            "100",
        ]
    )

    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["provider_policy"]["allow_provider_call"] is True
    assert payload["provider_policy"]["require_manual_trigger"] is True
    assert payload["provider_policy"]["capture_raw_response"] is False
    assert payload["provider_policy"]["max_response_chars"] == 100
    assert payload["provider_call_performed"] is True


def test_allow_missing_provider_callable_policy_is_passed(tmp_path, capsys):
    packet = _json(tmp_path / "packet.json", _request_packet())

    code = command.main(
        [
            "--input",
            str(packet),
            "--enable-provider-call",
            "--manual-trigger-confirmed",
            "--allow-provider-call",
            "--allow-missing-provider-callable",
        ]
    )

    captured = capsys.readouterr()
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["provider_policy"]["require_provider_callable"] is False
    assert payload["simulated_provider_callable_available"] is False
    assert payload["provider_call_performed"] is False


def test_main_returns_nonzero_for_missing_or_invalid_input(tmp_path, capsys):
    missing_code = command.main(["--input", str(tmp_path / "missing.json")])
    missing = capsys.readouterr()
    assert missing_code != 0
    assert missing.out == ""
    assert "error:" in missing.err

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{", encoding="utf-8")
    invalid_code = command.main(["--input", str(invalid)])
    captured = capsys.readouterr()
    assert invalid_code != 0
    assert captured.out == ""
    assert "invalid JSON" in captured.err


def test_command_does_not_write_output_files(tmp_path):
    packet = _json(tmp_path / "packet.json", _request_packet())
    before = sorted(item.name for item in tmp_path.iterdir())

    assert command.main(["--input", str(packet)]) == 0

    after = sorted(item.name for item in tmp_path.iterdir())
    assert after == before


def test_payload_has_no_callback_full_resume_mutation_persistence_or_submission():
    payload = command.build_dry_run_payload(
        request_packet=_request_packet(),
        provider_response_fixture={"ok": True},
        enable_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy={"allow_provider_call": True},
    )

    assert "provider_callable" not in payload
    assert "simulated_provider" not in payload
    assert "full_resume" not in payload
    assert "real_tailoring_output" not in payload
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_source_has_only_allowed_imports_and_no_write_or_runtime_markers():
    source = COMMAND_PATH.read_text(encoding="utf-8")
    assert (
        "from src.agents.controlled_exact_resume_change_set_provider_call_boundary_default_off import"
        in source
    )
    assert "build_controlled_exact_resume_change_set_provider_call_boundary_default_off(" in source
    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source
    for marker in FORBIDDEN_WRITE_MARKERS:
        assert marker not in source


def test_docs_include_required_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_hashes_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected, relative


def test_changed_files_are_limited_to_phase44b_and_legacy_guards():
    allowed = {
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

    }
    legacy_guards = {
        path
        for path in _changed_files()
        if path.startswith("tests/test_") and path.endswith(".py")
    }
    assert _changed_files() <= allowed | legacy_guards


def test_subprocess_cli_outputs_valid_json(tmp_path):
    packet = _json(tmp_path / "packet.json", _request_packet())

    result = subprocess.run(
        [
            sys.executable,
            str(COMMAND_PATH),
            "--input",
            str(packet),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    payload = json.loads(result.stdout)
    assert result.stderr == ""
    assert payload["phase"] == "44B"
    assert payload["provider_call_performed"] is False


def _changed_files() -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}
