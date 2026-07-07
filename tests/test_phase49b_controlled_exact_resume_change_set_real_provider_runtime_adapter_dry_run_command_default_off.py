# phase56b legacy guard marker: changes_only e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c
from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = (
    ROOT / "run_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase49_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run_command_default_off.md"
)

PROTECTED_HASHES = {
    "src/agents/controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py": "7e3cea001fb2ded35c1d998e22d156568492a4b76804a76d4142a329d18c5c97",
    "src/tailoring/llm.py": "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
    "generate_tailoring_suggestions.py": "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28",
    "src/agents/controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py": "cfeff0858be6f9177956a1e4b76af6d3ada1775f2833b7a1a1575a1f17aae03a",
    "run_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run.py": "07497f149c37d7e43068299c439f3dac29cd172cf95ec73c7bdb070f816fc32d",
    "src/agents/controlled_exact_resume_change_set_provider_response_validation_default_off.py": "413ace0d64f8c1bd62726cf7ae32bc4fc8e4b88eca82826492362d9842f569ef",
    "run_controlled_exact_resume_change_set_provider_response_validation_dry_run.py": "52351a639821afc4a042be7350514be33bd4f8fa5fbb714eda9d19aa45c0f0d4",
    "src/agents/controlled_exact_resume_change_set_provider_response_normalization_default_off.py": "bf50f751e501db96bdc30308b3bf162ec61b79111fe79907a9efd126f823206f",
    "run_controlled_exact_resume_change_set_provider_response_normalization_dry_run.py": "f298f42d602252b2314750593eab93573eed4dae8e3d90068e05f8a51e60dd9d",
    "src/agents/controlled_exact_resume_change_set_provider_call_boundary_default_off.py": "ed065e62f8cfdc6cf3c89f5e9a5d953ba577050eb4088af23bfaeea8becc088d",
    "run_controlled_exact_resume_change_set_provider_call_boundary_dry_run.py": "20a65fe37de31883c56b38dcda537b2a4034d2a1868d1965f848c1568075f771",
    "src/agents/controlled_exact_resume_change_set_llm_request_packet_default_off.py": "acaf694a08f65a5e646d2cbcc7b83a394ea1d15416c7311e230c86536d0a6b0f",
    "run_controlled_exact_resume_change_set_llm_request_packet_dry_run.py": "8baca68f6d8ba882324d028a68372d0d618709413bebe47931c93da5ef6dc175",
    "src/agents/exact_resume_change_set_proposal_builder_default_off.py": "fd173ea8bf3f7d746ebbdb7d6b2af7ae7df1aeaea4e66acaca52ea4fda1a9dc4",
    "run_exact_resume_change_set_proposal_builder_dry_run.py": "a8ea3201f0e71e463e316abdcf813b8d08fa3a473cd3dddcee158b87f3442451",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}

FALSE_KEYS = {
    "provider_response_validation_performed",
    "provider_response_normalization_performed",
    "manual_review_packets_created",
    "manual_review_readback_payload_created",
    "ui_route_added",
    "api_route_added",
    "ui_readback_performed",
    "api_readback_performed",
    "user_acceptance_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
    "resume_change_applied",
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
    "controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run",
    "dry_run_command_only",
    "real_provider_runtime_adapter_only",
    "read_only",
    "advisory_only",
    "provider_execution_boundary_only",
    "proposal_only",
    "exact_worthy_changes_only",
    "manual_review_required",
    "requires_manual_user_control",
    "request_packet_present",
    "request_result_present",
    "provider_policy",
    "runtime_result",
    "provider_callable_path_supplied",
    "provider_callable_path_allowed",
    "real_provider_call_allowed",
    "real_provider_call_blocked_reason",
    "real_provider_call_attempted",
    "real_provider_call_performed",
    "llm_call_performed",
    "provider_response",
    "provider_response_summary",
    "provider_runtime_error",
    "dry_run_summary",
    "dry_run_key",
    "manual_trigger_confirmed",
    "enable_real_provider_call",
    "tailoring_runtime_call_performed",
} | FALSE_KEYS


def _command():
    return importlib.import_module(
        "run_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run"
    )


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _json(path: Path, payload: object) -> Path:
    return _write(path, json.dumps(payload))


def _packet(packet_id: str = "packet-1") -> dict:
    return {
        "request_type": "exact_resume_change_set_refinement",
        "request_id": packet_id,
        "messages": [{"role": "user", "content": "Refine one exact change."}],
    }


def test_command_module_is_import_safe_and_exposes_functions(capsys):
    module = _command()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    for name in (
        "load_request_packet_from_path",
        "load_request_result_from_path",
        "build_dry_run_payload",
        "main",
    ):
        assert callable(getattr(module, name))


def test_request_packet_loader_supports_json_wrappers_jsonl_and_csv(tmp_path):
    module = _command()
    assert module.load_request_packet_from_path(_json(tmp_path / "packet.json", _packet("plain")))["request_id"] == "plain"
    for key in ("request_packet", "llm_request_packet", "request_payload"):
        assert module.load_request_packet_from_path(
            _json(tmp_path / f"{key}.json", {key: _packet(key)})
        )["request_id"] == key
    jsonl_path = _write(tmp_path / "packet.jsonl", json.dumps(_packet("jsonl")))
    assert module.load_request_packet_from_path(jsonl_path)["request_id"] == "jsonl"
    csv_path = _write(
        tmp_path / "packet.csv",
        "request_type,request_id,prompt\nexact_resume_change_set_refinement,csv,hello\n",
    )
    assert module.load_request_packet_from_path(csv_path)["request_id"] == "csv"


def test_request_result_loader_supports_required_shapes(tmp_path):
    module = _command()
    assert module.load_request_result_from_path(
        _json(tmp_path / "result.json", {"phase": "43A", "request_packet": _packet("direct")})
    )["request_packet"]["request_id"] == "direct"
    assert module.load_request_result_from_path(
        _json(tmp_path / "wrapper.json", {"request_result": {"request_packet": _packet("wrapped")}})
    )["request_result"]["request_packet"]["request_id"] == "wrapped"
    assert module.load_request_result_from_path(
        _json(tmp_path / "packet.json", _packet("plain"))
    )["request_packet"]["request_id"] == "plain"
    assert module.load_request_result_from_path(
        _json(tmp_path / "llm.json", {"llm_request_packet": _packet("llm")})
    )["llm_request_packet"]["request_id"] == "llm"
    assert module.load_request_result_from_path(
        _json(tmp_path / "payload.json", {"request_payload": _packet("payload")})
    )["request_payload"]["request_id"] == "payload"
    jsonl_path = _write(tmp_path / "result.jsonl", json.dumps({"request_packet": _packet("jsonl")}))
    assert module.load_request_result_from_path(jsonl_path)["request_packet"]["request_id"] == "jsonl"
    csv_path = _write(
        tmp_path / "result.csv",
        "request_type,request_id,prompt\nexact_resume_change_set_refinement,csv,hello\n",
    )
    assert module.load_request_result_from_path(csv_path)["request_packet"]["request_id"] == "csv"


@pytest.mark.parametrize(
    ("loader", "filename", "contents", "message"),
    [
        ("load_request_packet_from_path", "bad.txt", "{}", "unsupported request packet extension"),
        ("load_request_packet_from_path", "bad.json", "{", "invalid JSON"),
        ("load_request_packet_from_path", "bad.jsonl", "[]", "must be a JSON object"),
        ("load_request_packet_from_path", "bad.csv", "a,b\n1,2,3\n", "invalid CSV"),
        ("load_request_packet_from_path", "shape.json", {"unexpected": True}, "request packet json"),
        ("load_request_result_from_path", "shape.json", {"unexpected": True}, "request result json"),
    ],
)
def test_loaders_raise_deterministic_errors(tmp_path, loader, filename, contents, message):
    module = _command()
    path = tmp_path / filename
    if isinstance(contents, str):
        _write(path, contents)
    else:
        _json(path, contents)
    with pytest.raises(module.DryRunLoadError) as exc:
        getattr(module, loader)(path)
    assert message in str(exc.value)


def test_jsonl_and_csv_reject_multiple_rows(tmp_path):
    module = _command()
    jsonl_path = _write(tmp_path / "two.jsonl", json.dumps(_packet("one")) + "\n" + json.dumps(_packet("two")))
    with pytest.raises(module.DryRunLoadError, match="exactly one"):
        module.load_request_packet_from_path(jsonl_path)
    csv_path = _write(
        tmp_path / "two.csv",
        "request_type,request_id\nexact_resume_change_set_refinement,one\nexact_resume_change_set_refinement,two\n",
    )
    with pytest.raises(module.DryRunLoadError, match="exactly one"):
        module.load_request_result_from_path(csv_path)


def test_build_dry_run_payload_calls_phase49a_helper_and_returns_required_keys(monkeypatch):
    module = _command()
    calls = []

    def fake_helper(**kwargs):
        calls.append(kwargs)
        return {
            "phase": "49A",
            "request_packet_present": True,
            "request_result_present": False,
            "provider_policy": {"provider_callable_path": "pkg.fake"},
            "provider_callable_path_supplied": True,
            "provider_callable_path_allowed": True,
            "real_provider_call_allowed": False,
            "real_provider_call_blocked_reason": "blocked in fake",
            "real_provider_call_attempted": False,
            "real_provider_call_performed": False,
            "llm_call_performed": False,
            "provider_response": None,
            "provider_response_summary": {},
            "provider_runtime_error": "",
            "provider_runtime_key": "phase49a-key",
            "tailoring_runtime_call_performed": False,
        }

    monkeypatch.setattr(
        module,
        "build_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off",
        fake_helper,
    )
    payload = module.build_dry_run_payload(
        request_packet=_packet("called"),
        enable_real_provider_call=True,
        manual_trigger_confirmed=True,
        provider_policy={"provider_callable_path": "pkg.fake"},
    )
    assert len(calls) == 1
    assert calls[0]["request_packet"]["request_id"] == "called"
    assert calls[0]["provider_callable"] is None
    assert calls[0]["provider_policy"]["provider_callable_path"] == "pkg.fake"
    assert REQUIRED_KEYS <= set(payload)
    assert payload["phase"] == "49B"
    assert payload["dry_run_command_only"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    for key in FALSE_KEYS:
        assert payload[key] is False


def test_default_command_payload_blocks_provider_execution():
    payload = _command().build_dry_run_payload(request_packet=_packet())
    assert payload["real_provider_call_performed"] is False
    assert payload["real_provider_call_attempted"] is False
    assert "enable_real_provider_call must be true" in payload["real_provider_call_blocked_reason"]


def test_cli_policy_options_are_passed_to_phase49a(monkeypatch, tmp_path, capsys):
    module = _command()
    input_path = _json(tmp_path / "packet.json", _packet("cli"))
    calls = []

    def fake_helper(**kwargs):
        calls.append(kwargs)
        return {
            "phase": "49A",
            "request_packet_present": True,
            "request_result_present": False,
            "provider_policy": kwargs["provider_policy"],
            "provider_callable_path_supplied": True,
            "provider_callable_path_allowed": False,
            "real_provider_call_allowed": False,
            "real_provider_call_blocked_reason": "path blocked",
            "real_provider_call_attempted": False,
            "real_provider_call_performed": False,
            "llm_call_performed": False,
            "provider_response": None,
            "provider_response_summary": {},
            "provider_runtime_error": "",
            "provider_runtime_key": "phase49a-key",
            "tailoring_runtime_call_performed": False,
        }

    monkeypatch.setattr(
        module,
        "build_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off",
        fake_helper,
    )
    exit_code = module.main(
        [
            "--input",
            str(input_path),
            "--enable-real-provider-call",
            "--manual-trigger-confirmed",
            "--allow-real-provider-call",
            "--provider-callable-path",
            "fake.module.callable",
            "--allowed-provider-module-prefix",
            "fake.module",
            "--provider-name",
            "demo",
            "--model-name",
            "model",
            "--temperature",
            "0.2",
            "--max-output-tokens",
            "123",
            "--request-timeout-seconds",
            "30",
            "--max-response-chars",
            "99",
            "--no-capture-raw-response",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    payload = json.loads(captured.out)
    policy = calls[0]["provider_policy"]
    assert policy["allow_real_provider_call"] is True
    assert policy["provider_callable_path"] == "fake.module.callable"
    assert policy["allowed_provider_module_prefixes"] == ["fake.module"]
    assert policy["provider_name"] == "demo"
    assert policy["model_name"] == "model"
    assert policy["temperature"] == 0.2
    assert policy["max_output_tokens"] == 123
    assert policy["request_timeout_seconds"] == 30
    assert policy["max_response_chars"] == 99
    assert policy["capture_raw_response"] is False
    assert payload["provider_policy"]["provider_callable_path"] == "fake.module.callable"


def test_main_prints_json_and_returns_zero_when_blocked(tmp_path, capsys):
    module = _command()
    input_path = _json(tmp_path / "packet.json", _packet("blocked"))
    assert module.main(["--input", str(input_path)]) == 0
    captured = capsys.readouterr()
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["phase"] == "49B"
    assert payload["real_provider_call_performed"] is False


def test_main_returns_zero_when_phase49a_returns_runtime_error(monkeypatch, tmp_path, capsys):
    module = _command()
    input_path = _json(tmp_path / "packet.json", _packet("error"))

    def fake_helper(**kwargs):
        return {
            "phase": "49A",
            "request_packet_present": True,
            "request_result_present": False,
            "provider_policy": kwargs["provider_policy"],
            "provider_callable_path_supplied": True,
            "provider_callable_path_allowed": True,
            "real_provider_call_allowed": False,
            "real_provider_call_blocked_reason": "provider runtime raised error",
            "real_provider_call_attempted": True,
            "real_provider_call_performed": False,
            "llm_call_performed": False,
            "provider_response": None,
            "provider_response_summary": {},
            "provider_runtime_error": "RuntimeError: boom",
            "provider_runtime_key": "phase49a-key",
            "tailoring_runtime_call_performed": False,
        }

    monkeypatch.setattr(
        module,
        "build_controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off",
        fake_helper,
    )
    assert module.main(["--input", str(input_path), "--provider-callable-path", "fake.call"]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["provider_runtime_error"] == "RuntimeError: boom"


def test_main_returns_nonzero_for_invalid_input(tmp_path, capsys):
    module = _command()
    bad = _write(tmp_path / "bad.json", "{")
    assert module.main(["--input", str(bad)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error: invalid JSON" in captured.err


def test_payload_has_no_callbacks_full_resume_or_side_effects():
    payload = _command().build_dry_run_payload(request_packet=_packet())
    text = repr(payload).lower()
    assert "callback" not in text
    assert "function" not in text
    assert "full_resume" not in text
    assert "overwrite_resume(" not in text
    assert "mutate_resume(" not in text
    assert "submit_application(" not in text
    for key in FALSE_KEYS:
        assert payload[key] is False


def test_source_has_no_forbidden_imports_calls_writes_or_direct_tailoring_import():
    source = COMMAND_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden = (
        "openai",
        "anthropic",
        "requests",
        "httpx",
        "urllib",
        "import src.tailoring.llm",
        "from src.tailoring",
        "from src.app",
        "import src.app",
        "from src.storage",
        "import src.storage",
        "from src.pipeline",
        "import src.pipeline",
        "from src.matching",
        "import src.matching",
        "score_resume_job_match",
        "run_prefilter",
        "generate_tailoring_suggestions",
        "application_execution_queue",
        "submit_application(",
        "execute_application(",
        "overwrite_resume(",
        "mutate_resume(",
    )
    forbidden_writes = (
        ".update(",
        "update(",
        ".write_text(",
        ".write_bytes(",
        ".mkdir(",
        ".save(",
        ".insert(",
    )
    for marker in forbidden:
        assert marker not in lowered
    for marker in forbidden_writes:
        assert marker not in source
    assert (
        "from src.agents.controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off import"
        in source
    )


def test_docs_include_required_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    required = (
        "phase 49b controlled exact resume change-set real provider runtime adapter dry-run command default-off",
        "controlled exact resume change-set real provider runtime adapter dry-run command",
        "first cli phase capable of a real provider call for exact resume change-set refinement",
        "default-off",
        "manual trigger confirmation",
        "enable_real_provider_call",
        "allow_real_provider_call",
        "configured provider callable path",
        "calls the phase 49a controlled exact resume change-set real provider runtime adapter",
        "reads supplied request packet files",
        "reads supplied request result files",
        "pass a configured provider callable path to phase 49a",
        "does not import provider sdks directly",
        "does not directly import `src/tailoring/llm.py`",
        "does not add dependencies",
        "does not validate provider response",
        "does not normalize provider response",
        "does not create manual review packets",
        "does not create ui/api readback payload",
        "does not modify ui files",
        "does not modify api/service files",
        "does not persist data",
        "does not write to database",
        "does not create real tailoring output",
        "does not produce a full resume",
        "does not overwrite resumes",
        "does not mutate resumes",
        "does not execute applications",
        "does not submit applications",
        "no auto-apply",
        "no auto-submit",
        "manual user control remains required",
        "existing ui/manual control remains the acceptance point",
        "provider response validation happens in phase 45",
        "provider response normalization happens in phase 46",
        "manual review packets happen in phase 47",
        "manual review readback happens in phase 48",
        "resume overwrite is not needed",
        "application execution is not needed",
        "python run_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run.py --input path/to/request_packet.json --enable-real-provider-call --manual-trigger-confirmed --allow-real-provider-call --provider-callable-path src.tailoring.llm.some_existing_callable",
        "phase49a-controlled-exact-resume-change-set-real-provider-runtime-adapter-default-off-v1",
        "phase48-controlled-exact-resume-change-set-manual-review-readback-adapter-release-v1",
        "phase48b-controlled-exact-resume-change-set-manual-review-readback-adapter-dry-run-command-default-off-v1",
        "phase48a-controlled-exact-resume-change-set-manual-review-readback-adapter-default-off-v1",
        "phase47-controlled-exact-resume-change-set-manual-review-packet-builder-release-v1",
        "phase46-controlled-exact-resume-change-set-provider-response-normalization-release-v1",
        "phase45-controlled-exact-resume-change-set-provider-response-validation-release-v1",
        "phase44-controlled-exact-resume-change-set-provider-call-boundary-release-v1",
        "phase43-controlled-exact-resume-change-set-llm-request-packet-release-v1",
        "phase42-exact-resume-change-set-proposal-builder-release-v1",
        "phase23-tailoring-agent-workflow-release-v1",
        "phase20d-no-auto-apply-safety-checkpoint-v1",
    )
    for marker in required:
        assert marker in text


def test_protected_runtime_hashes_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_changed_files_limited_to_phase49b_surface_and_legacy_guards():
    import subprocess

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
    forbidden_roots = (
        "src/app/",
        "src/pipeline/",
        "src/matching/",
        "src/tailoring/",
        "generate_tailoring_suggestions.py",
        "application_execution_queue.py",
    )
    allowed |= {
        "src/agents/orchestrator_adapter_harness.py",
            "src/pipeline/collector.py",
            "tests/test_phase81d_collector_advisory_chain_diagnostics_sidecar_default_off.py",
        "tests/test_phase82b_collector_advisory_chain_trace_persistence_default_off.py",
            "tests/test_phase83b_live_llm_invocation_contract_map_default_off.py",
            "src/agents/jd_intelligence.py",
            "tests/test_phase84b_jd_intelligence_existing_output_wrapper_default_off.py",
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
    for path in changed:
        assert path in allowed or not any(
            path == root or path.startswith(root) for root in forbidden_roots
        )
        assert path in allowed or path.startswith("tests/test_")
