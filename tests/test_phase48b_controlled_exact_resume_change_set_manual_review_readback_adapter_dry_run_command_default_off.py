from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = (
    ROOT
    / "run_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase48_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run_command_default_off.md"
)

PROTECTED_HASHES = {
    "src/agents/controlled_exact_resume_change_set_manual_review_readback_adapter_default_off.py": "cfeff0858be6f9177956a1e4b76af6d3ada1775f2833b7a1a1575a1f17aae03a",
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
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_suggestions.py": "559a66a7c7a1963d322a1e7b3f0fd3ede1ea161a9be2d176dcce0ef1016ea9ff",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}

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
    "auto_apply_performed",
    "auto_submit_performed",
}

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run",
    "dry_run_command_only",
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
    "readback_result",
    "readback_items",
    "readback_items_by_type",
    "readback_items_by_action",
    "readback_payload",
    "readback_summary",
    "readback_findings",
    "dry_run_summary",
    "dry_run_key",
    "manual_review_readback_payload_created",
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


def _command():
    return importlib.import_module(
        "run_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run"
    )


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _json(path: Path, payload) -> Path:
    return _write(path, json.dumps(payload))


def _packet(proposal_id: str = "proposal-1") -> dict:
    return {
        "review_packet_id": f"packet-{proposal_id}",
        "proposal_id": proposal_id,
        "change_type": "bullet_rewrite",
        "target_section": "experience",
        "target_identifier": "role-1-bullet-2",
        "current_text": "Built dashboards.",
        "proposed_text": "Built executive dashboards using revenue signals.",
        "recommended_operator_action": "review_change",
        "display_order": 1,
    }


def test_command_module_is_import_safe_and_exposes_functions(capsys):
    module = _command()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    for name in (
        "load_manual_review_packets_from_path",
        "load_review_packet_result_from_path",
        "load_readback_context_from_path",
        "build_dry_run_payload",
        "main",
    ):
        assert callable(getattr(module, name))


def test_manual_review_packet_loader_supports_json_jsonl_and_csv(tmp_path):
    module = _command()
    assert module.load_manual_review_packets_from_path(
        _json(tmp_path / "packets.json", [_packet("list")])
    )[0]["proposal_id"] == "list"
    for key in ("manual_review_packets", "readback_items", "rows", "items", "packets"):
        rows = module.load_manual_review_packets_from_path(
            _json(tmp_path / f"{key}.json", {key: [_packet(key)]})
        )
        assert rows[0]["proposal_id"] == key
    jsonl_path = _write(
        tmp_path / "packets.jsonl",
        json.dumps(_packet("jsonl-1")) + "\n" + json.dumps(_packet("jsonl-2")),
    )
    assert [row["proposal_id"] for row in module.load_manual_review_packets_from_path(jsonl_path)] == [
        "jsonl-1",
        "jsonl-2",
    ]
    csv_path = _write(
        tmp_path / "packets.csv",
        "proposal_id,change_type,current_text,proposed_text\ncsv-1,bullet,a,b\n",
    )
    assert module.load_manual_review_packets_from_path(csv_path)[0]["proposal_id"] == "csv-1"


def test_review_packet_result_loader_supports_required_shapes(tmp_path):
    module = _command()
    assert module.load_review_packet_result_from_path(
        _json(tmp_path / "full.json", {"manual_review_packets": [_packet("full")]})
    )["manual_review_packets"][0]["proposal_id"] == "full"
    assert module.load_review_packet_result_from_path(
        _json(
            tmp_path / "wrapper.json",
            {"review_packet_result": {"manual_review_packets": [_packet("wrapped")]}},
        )
    )["review_packet_result"]["manual_review_packets"][0]["proposal_id"] == "wrapped"
    assert module.load_review_packet_result_from_path(
        _json(tmp_path / "list.json", [_packet("list")])
    )["manual_review_packets"][0]["proposal_id"] == "list"
    assert "manual_review_packets_by_type" in module.load_review_packet_result_from_path(
        _json(
            tmp_path / "grouped.json",
            {"manual_review_packets_by_type": {"bullet": [_packet("grouped")]}},
        )
    )
    assert module.load_review_packet_result_from_path(
        _json(tmp_path / "rows.json", {"rows": [_packet("rows")]})
    )["manual_review_packets"][0]["proposal_id"] == "rows"
    assert module.load_review_packet_result_from_path(
        _json(tmp_path / "items.json", {"items": [_packet("items")]})
    )["manual_review_packets"][0]["proposal_id"] == "items"
    jsonl_path = _write(
        tmp_path / "result.jsonl",
        json.dumps({"manual_review_packets": [_packet("jsonl")]}),
    )
    assert module.load_review_packet_result_from_path(jsonl_path)["manual_review_packets"][0]["proposal_id"] == "jsonl"
    csv_path = _write(
        tmp_path / "result.csv",
        "proposal_id,change_type,current_text,proposed_text\ncsv,bullet,a,b\n",
    )
    assert module.load_review_packet_result_from_path(csv_path)["manual_review_packets"][0]["proposal_id"] == "csv"


def test_readback_context_loader_supports_json_jsonl_and_csv(tmp_path):
    module = _command()
    assert module.load_readback_context_from_path(
        _json(tmp_path / "context.json", {"operator": "reviewer"})
    ) == {"operator": "reviewer"}
    jsonl_path = _write(
        tmp_path / "context.jsonl",
        json.dumps({"source": "one"}) + "\n" + json.dumps({"source": "two"}),
    )
    assert module.load_readback_context_from_path(jsonl_path) == {
        "source_format": "jsonl",
        "rows": [{"source": "one"}, {"source": "two"}],
    }
    csv_path = _write(tmp_path / "context.csv", "source\nspreadsheet\n")
    assert module.load_readback_context_from_path(csv_path) == {
        "source_format": "csv",
        "rows": [{"source": "spreadsheet"}],
    }


@pytest.mark.parametrize(
    ("loader_name", "filename", "contents", "message"),
    [
        ("load_manual_review_packets_from_path", "packets.txt", "{}", "unsupported"),
        ("load_manual_review_packets_from_path", "bad.json", "{", "invalid JSON"),
        ("load_manual_review_packets_from_path", "bad.jsonl", "[]", "must be a JSON object"),
        ("load_manual_review_packets_from_path", "bad.csv", "a,b\n1,2,3\n", "invalid CSV"),
        ("load_manual_review_packets_from_path", "shape.json", {"unexpected": []}, "manual review packets json"),
        ("load_review_packet_result_from_path", "shape.json", {"unexpected": []}, "review packet result input"),
        ("load_readback_context_from_path", "shape.json", [], "readback context json"),
    ],
)
def test_loaders_raise_deterministic_errors(tmp_path, loader_name, filename, contents, message):
    module = _command()
    path = tmp_path / filename
    if isinstance(contents, str):
        _write(path, contents)
    else:
        _json(path, contents)
    with pytest.raises(module.DryRunLoadError) as exc:
        getattr(module, loader_name)(path)
    assert message in str(exc.value)


def test_review_packet_result_jsonl_and_csv_reject_multiple_rows(tmp_path):
    module = _command()
    jsonl_path = _write(
        tmp_path / "two.jsonl",
        json.dumps({"manual_review_packets": []}) + "\n" + json.dumps({"manual_review_packets": []}),
    )
    with pytest.raises(module.DryRunLoadError, match="exactly one"):
        module.load_review_packet_result_from_path(jsonl_path)
    csv_path = _write(tmp_path / "two.csv", "proposal_id\none\ntwo\n")
    with pytest.raises(module.DryRunLoadError, match="exactly one"):
        module.load_review_packet_result_from_path(csv_path)


def test_build_dry_run_payload_calls_phase48a_and_returns_required_flags(monkeypatch):
    module = _command()
    calls = []

    def fake_adapter(**kwargs):
        calls.append(kwargs)
        return {
            "phase": "48A",
            "readback_policy": {"max_readback_items": 1},
            "readback_items": [{"proposal_id": "called"}],
            "readback_items_by_type": {"bullet": [{"proposal_id": "called"}]},
            "readback_items_by_action": {"review_change": [{"proposal_id": "called"}]},
            "readback_payload": {"payload_type": "exact_resume_change_set_manual_review_readback"},
            "readback_summary": {"readback_item_count": 1},
            "readback_findings": {"blocked": False},
            "missing_inputs": [],
            "readback_key": "phase48a-key",
        }

    monkeypatch.setattr(
        module,
        "build_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off",
        fake_adapter,
    )
    payload = module.build_dry_run_payload(
        manual_review_packets=[_packet("called")],
        readback_context={"source": "unit"},
        readback_policy={"max_readback_items": 1},
    )
    assert len(calls) == 1
    assert calls[0]["manual_review_packets"][0]["proposal_id"] == "called"
    assert calls[0]["readback_context"] == {"source": "unit"}
    assert calls[0]["readback_policy"] == {"max_readback_items": 1}
    assert REQUIRED_KEYS <= set(payload)
    assert payload["phase"] == "48B"
    assert payload["default_off"] is True
    assert payload["controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run"] is True
    assert payload["dry_run_command_only"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["manual_review_readback_only"] is True
    assert payload["ui_api_readback_payload_only"] is True
    assert payload["manual_review_readback_payload_created"] is True
    assert all(payload[key] is False for key in FALSE_ACTION_KEYS)
    assert payload["dry_run_key"].startswith("phase48b-manual-review-readback-dry-run-")


def test_valid_manual_review_packets_yield_items_payload_and_cli_json(tmp_path, capsys):
    module = _command()
    input_path = _json(tmp_path / "packets.json", [_packet("cli")])
    context_path = _json(tmp_path / "context.json", {"source": "cli-test"})
    exit_code = module.main(
        [
            "--input",
            str(input_path),
            "--readback-context",
            str(context_path),
            "--max-readback-items",
            "1",
            "--exclude-risk-flags",
            "--disable-group-by-operator-action",
        ]
    )
    captured = capsys.readouterr()
    assert exit_code == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    assert payload["phase"] == "48B"
    assert payload["readback_items"][0]["proposal_id"] == "cli"
    assert payload["readback_payload"]["payload_type"] == "exact_resume_change_set_manual_review_readback"
    assert payload["readback_policy"]["max_readback_items"] == 1
    assert payload["readback_policy"]["include_risk_flags"] is False
    assert payload["readback_policy"]["group_by_operator_action"] is False


def test_cli_returns_nonzero_for_load_errors_and_stderr_only(tmp_path, capsys):
    module = _command()
    bad_path = _write(tmp_path / "bad.json", "{")
    assert module.main(["--input", str(bad_path)]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error: invalid JSON" in captured.err


def test_cli_returns_zero_for_parsed_empty_packets_even_when_blocked(tmp_path, capsys):
    module = _command()
    empty_path = _json(tmp_path / "empty.json", [])
    assert module.main(["--input", str(empty_path)]) == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["readback_findings"]["blocked"] is True
    assert payload["readback_items"] == []


def test_command_source_has_no_forbidden_imports_calls_writes_or_dict_update():
    source = COMMAND_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker.lower() not in lowered
    for marker in FORBIDDEN_WRITE_MARKERS:
        assert marker not in source
    assert "build_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off" in source


def test_docs_include_required_phase48b_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    required_markers = (
        "phase 48b controlled exact resume change-set manual review readback adapter dry-run command default-off",
        "controlled exact resume change-set manual review readback adapter dry-run command",
        "reads supplied manual review packets file",
        "reads supplied review packet result file",
        "reads supplied readback context file",
        "calls the phase 48a controlled exact resume change-set manual review readback adapter",
        "prints manual review readback payload json to stdout",
        "adapts manual review packets after phase 47",
        "not a ui route phase",
        "not an api route phase",
        "prepares ui/api-readback-ready payloads",
        "does not modify ui files",
        "does not modify api/service files",
        "does not perform ui readback",
        "does not perform api readback",
        "preserves manual review and user acceptance requirements",
        "produces manual-review readback payload only",
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
        "ui/api readback wiring comes in a later phase",
        'python run_controlled_exact_resume_change_set_manual_review_readback_adapter_dry_run.py --input path/to/manual_review_packets.json --readback-context path/to/readback_context.json',
        "phase48a-controlled-exact-resume-change-set-manual-review-readback-adapter-default-off-v1",
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
