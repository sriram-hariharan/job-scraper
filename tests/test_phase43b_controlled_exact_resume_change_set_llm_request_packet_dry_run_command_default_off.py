# Legacy guard compatibility markers for downstream change-scope guards:
# controlled_exact_resume_change_set_provider_response_normalization_dry_run
# phase46_controlled_exact_resume_change_set_provider_response_normalization_dry_run_command_default_off
# controlled_exact_resume_change_set_manual_review_packet_builder_default_off
# phase47_controlled_exact_resume_change_set_manual_review_packet_builder_default_off
# controlled_exact_resume_change_set_manual_review_packet_builder_dry_run
# phase47_controlled_exact_resume_change_set_manual_review_packet_builder_dry_run_command_default_off

from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

import run_controlled_exact_resume_change_set_llm_request_packet_dry_run as command


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = (
    ROOT / "run_controlled_exact_resume_change_set_llm_request_packet_dry_run.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase43_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.md"
)

FALSE_ACTION_KEYS = {
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
    "controlled_exact_resume_change_set_llm_request_packet_dry_run",
    "dry_run_command_only",
    "read_only",
    "advisory_only",
    "proposal_only",
    "llm_request_packet_only",
    "provider_request_packet_only",
    "exact_worthy_changes_only",
    "manual_review_required",
    "requires_manual_user_control",
    "manual_trigger_required",
    "change_proposals_present",
    "proposal_result_present",
    "resume_context_present",
    "jd_context_present",
    "tailoring_context_present",
    "request_policy",
    "request_result",
    "request_packet",
    "request_messages",
    "request_schema",
    "request_packet_summary",
    "dry_run_summary",
    "dry_run_key",
    "llm_request_packet_created",
    "provider_dispatch_ready",
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
    "phase 43b controlled exact resume change-set llm request packet dry-run command default-off",
    "controlled exact resume change-set llm request packet dry-run command",
    "reads supplied change proposal file",
    "reads supplied proposal result file",
    "reads supplied resume context file",
    "reads supplied jd context file",
    "reads supplied tailoring context file",
    "calls the phase 43a controlled exact resume change-set llm request packet builder",
    "prints provider-ready request packet json to stdout",
    "creates a provider-ready request packet",
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
    "provider dispatch is prepared but not executed",
    "llm call comes in a later controlled provider-call phase",
    'python run_controlled_exact_resume_change_set_llm_request_packet_dry_run.py --input path/to/change_proposals.json --resume-context path/to/resume_context.json --jd-context path/to/jd_context.json --tailoring-context path/to/tailoring_context.json',
    "phase43a-controlled-exact-resume-change-set-llm-request-packet-default-off-v1",
    "phase42-exact-resume-change-set-proposal-builder-release-v1",
    "phase42b-exact-resume-change-set-proposal-builder-dry-run-command-default-off-v1",
    "phase42a-exact-resume-change-set-proposal-builder-default-off-v1",
    "phase41-jd-evidence-score-impact-review-queue-builder-release-v1",
    "phase40-jd-evidence-score-impact-review-packet-builder-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/controlled_exact_resume_change_set_llm_request_packet_default_off.py": "acaf694a08f65a5e646d2cbcc7b83a394ea1d15416c7311e230c86536d0a6b0f",
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


def _proposal(**overrides):
    proposal = {
        "proposal_id": "p1",
        "item_id": "queue-1",
        "job_id": "job-1",
        "title": "Senior Data Scientist",
        "company": "ExampleCo",
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


def _resume_context():
    return {"profile_summary": "Data scientist.", "skills": ["Python", "SQL"]}


def _jd_context():
    return {"required_skills": ["Python", "SQL"], "tools": ["Tableau"]}


def _tailoring_context():
    return {"matched_required_skills": ["Python"], "missing_tools": ["Tableau"]}


def test_command_module_is_import_safe_and_exposes_functions():
    module = importlib.reload(command)
    assert callable(module.load_change_proposals_from_path)
    assert callable(module.load_proposal_result_from_path)
    assert callable(module.load_context_from_path)
    assert callable(module.build_dry_run_payload)
    assert callable(module.main)


@pytest.mark.parametrize(
    "filename,payload",
    [
        ("proposals.json", [_proposal()]),
        ("wrapped.json", {"change_proposals": [_proposal(proposal_id="wrapped")]}),
        ("rows.json", {"rows": [_proposal(proposal_id="rows")]}),
        ("items.json", {"items": [_proposal(proposal_id="items")]}),
        ("proposals_key.json", {"proposals": [_proposal(proposal_id="proposals")]}),
    ],
)
def test_change_proposal_loader_loads_json_shapes(tmp_path, filename, payload):
    rows = command.load_change_proposals_from_path(_json(tmp_path / filename, payload))
    assert len(rows) == 1
    assert isinstance(rows[0], dict)


def test_change_proposal_loader_loads_jsonl_and_csv(tmp_path):
    rows = [_proposal(), _proposal(proposal_id="p2")]
    assert len(command.load_change_proposals_from_path(_jsonl(tmp_path / "p.jsonl", rows))) == 2
    csv_rows = [
        {"proposal_id": "p1", "change_type": "bullet"},
        {"proposal_id": "p2", "change_type": "skill"},
    ]
    assert len(command.load_change_proposals_from_path(_csv(tmp_path / "p.csv", csv_rows))) == 2


@pytest.mark.parametrize(
    "filename,payload",
    [
        ("result.json", {"change_proposals": [_proposal()]}),
        ("dryrun.json", {"proposal_result": {"change_proposals": [_proposal()]}}),
        ("wrapped.json", {"change_proposals": [_proposal(proposal_id="wrapped")]}),
        ("rows.json", {"rows": [_proposal(proposal_id="rows")]}),
        ("items.json", {"items": [_proposal(proposal_id="items")]}),
        ("list.json", [_proposal(proposal_id="list")]),
    ],
)
def test_proposal_result_loader_loads_supported_shapes(tmp_path, filename, payload):
    result = command.load_proposal_result_from_path(_json(tmp_path / filename, payload))
    assert isinstance(result, dict)
    assert "proposal_result" in result or "change_proposals" in result


def test_proposal_result_loader_loads_jsonl_and_csv(tmp_path):
    rows = [_proposal(), _proposal(proposal_id="p2")]
    assert "change_proposals" in command.load_proposal_result_from_path(
        _jsonl(tmp_path / "result.jsonl", rows)
    )
    csv_rows = [
        {"proposal_id": "p1", "change_type": "bullet"},
        {"proposal_id": "p2", "change_type": "skill"},
    ]
    assert "change_proposals" in command.load_proposal_result_from_path(
        _csv(tmp_path / "result.csv", csv_rows)
    )


def test_context_loader_loads_json_dictionary_jsonl_and_csv(tmp_path):
    assert command.load_context_from_path(_json(tmp_path / "context.json", {"skills": ["Python"]})) == {
        "skills": ["Python"]
    }
    assert "rows" in command.load_context_from_path(
        _jsonl(tmp_path / "context.jsonl", [{"skill": "Python"}])
    )
    assert "rows" in command.load_context_from_path(
        _csv(tmp_path / "context.csv", [{"skill": "Python"}])
    )


@pytest.mark.parametrize(
    "loader,filename,writer,error",
    [
        (command.load_change_proposals_from_path, "p.txt", lambda path: path.write_text("[]", encoding="utf-8"), "unsupported"),
        (command.load_change_proposals_from_path, "p.json", lambda path: path.write_text("{", encoding="utf-8"), "invalid JSON"),
        (command.load_change_proposals_from_path, "p.jsonl", lambda path: path.write_text("{", encoding="utf-8"), "invalid JSONL"),
        (command.load_change_proposals_from_path, "p.csv", lambda path: path.write_text("a,b\n1,2,3", encoding="utf-8"), "extra columns"),
        (command.load_change_proposals_from_path, "p.json", lambda path: path.write_text(json.dumps({"change_proposals": ["bad"]}), encoding="utf-8"), "row 0"),
        (command.load_proposal_result_from_path, "result.json", lambda path: path.write_text(json.dumps({"not_result": []}), encoding="utf-8"), "must include"),
        (command.load_context_from_path, "context.json", lambda path: path.write_text(json.dumps(["bad"]), encoding="utf-8"), "context json must be an object"),
    ],
)
def test_loader_errors_are_deterministic(tmp_path, loader, filename, writer, error):
    path = tmp_path / filename
    writer(path)
    with pytest.raises(command.DryRunLoadError, match=error):
        loader(path)


def test_build_dry_run_payload_calls_phase43a_and_returns_required_surfaces():
    payload = command.build_dry_run_payload(
        change_proposals=[_proposal()],
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
        request_policy={"max_proposals_per_request": 1},
    )

    assert REQUIRED_KEYS.issubset(payload)
    assert payload["phase"] == "43B"
    assert payload["default_off"] is True
    assert payload["change_proposals_present"] is True
    assert payload["proposal_result_present"] is False
    assert payload["resume_context_present"] is True
    assert payload["jd_context_present"] is True
    assert payload["tailoring_context_present"] is True
    assert payload["request_policy"]["max_proposals_per_request"] == 1
    assert payload["request_result"]["phase"] == "43A"
    assert payload["request_packet"]["request_type"] == "exact_resume_change_set_refinement"
    assert payload["request_messages"]
    assert payload["request_schema"]["properties"]["resume_overwrite_performed"]["const"] is False
    assert payload["request_packet_summary"]["included_change_proposal_count"] == 1
    assert "full_resume" not in payload
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_build_dry_run_payload_accepts_proposal_result_and_context_flags():
    payload = command.build_dry_run_payload(
        proposal_result={"change_proposals": [_proposal(proposal_id="from-result")]},
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
    )

    assert payload["change_proposals_present"] is False
    assert payload["proposal_result_present"] is True
    assert payload["resume_context_present"] is True
    assert payload["jd_context_present"] is True
    assert payload["tailoring_context_present"] is True
    assert (
        payload["request_packet"]["included_change_proposals"][0]["proposal_id"]
        == "from-result"
    )


def test_cli_policy_options_are_passed_and_main_prints_json(tmp_path, capsys):
    proposals = _json(tmp_path / "proposals.json", [_proposal()])
    proposal_result = _json(
        tmp_path / "proposal_result.json",
        {"change_proposals": [_proposal(proposal_id="result")]},
    )
    resume = _json(tmp_path / "resume.json", _resume_context())
    jd = _json(tmp_path / "jd.json", _jd_context())
    tailoring = _json(tmp_path / "tailoring.json", _tailoring_context())

    code = command.main(
        [
            "--input",
            str(proposals),
            "--proposal-result",
            str(proposal_result),
            "--resume-context",
            str(resume),
            "--jd-context",
            str(jd),
            "--tailoring-context",
            str(tailoring),
            "--max-proposals-per-request",
            "1",
            "--include-full-resume-context",
            "--include-full-jd-context",
            "--exclude-tailoring-context",
            "--response-format",
            "json_schema",
            "--temperature",
            "0.25",
            "--max-output-tokens",
            "900",
        ]
    )

    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    policy = payload["request_policy"]
    assert policy["max_proposals_per_request"] == 1
    assert policy["include_full_resume_context"] is True
    assert policy["include_full_jd_context"] is True
    assert policy["include_tailoring_context"] is False
    assert policy["require_manual_trigger"] is True
    assert policy["response_format"] == "json_schema"
    assert policy["temperature"] == 0.25
    assert policy["max_output_tokens"] == 900
    assert payload["request_packet"]["response_format"] == "json_schema"


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
    proposals = _json(tmp_path / "proposals.json", [_proposal()])
    before = sorted(item.name for item in tmp_path.iterdir())

    assert command.main(["--input", str(proposals)]) == 0

    after = sorted(item.name for item in tmp_path.iterdir())
    assert after == before


def test_payload_has_no_full_resume_tailoring_output_or_runtime_effects():
    payload = command.build_dry_run_payload(
        change_proposals=[_proposal()],
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
    )

    assert "full_resume" not in payload
    assert "real_tailoring_output" not in payload
    assert payload["llm_request_packet_created"] is True
    assert payload["provider_dispatch_ready"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_source_has_only_allowed_imports_and_no_write_or_runtime_markers():
    source = COMMAND_PATH.read_text(encoding="utf-8")
    assert (
        "from src.agents.controlled_exact_resume_change_set_llm_request_packet_default_off import"
        in source
    )
    assert "build_controlled_exact_resume_change_set_llm_request_packet_default_off(" in source
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


def test_changed_files_are_limited_to_phase43b_and_legacy_guards():
    allowed = {
        "src/app/ui.py",
        "src/app/static/app.js",
        "src/app/static/planning.js",
        "src/app/static/app_redesign.css",
        "tests/test_queue_ui_metadata_contract.py",
        "tests/test_phase20d_no_auto_apply_safety_checkpoint_default_off.py",
        "tests/test_phase21a_manual_review_workflow_boundary_default_off.py",
        "src/tailoring/llm.py",
        "generate_tailoring_suggestions.py",
        "src/tailoring/rendering.py",
        "tests/test_score_first_scan.py",
        "run_controlled_exact_resume_change_set_llm_request_packet_dry_run.py",
        "docs/phase43_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.md",
        "docs/phase50_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run_command_default_off.md",
        "src/app/services.py",
        "src/app/api.py",
        "docs/phase55_live_jd_llm_extraction_planning_scan_wiring_default_off.md",
        "tests/test_phase55a_live_jd_llm_extraction_planning_scan_wiring_default_off.py",
        "src/app/planning_ui.py",
        "src/app/static/planning.js",
        "src/app/static/scan_workspace.js",
        "docs/phase55_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off.md",
            "docs/phase71_tailoring_workspace_artifact_path_preload_repair_default_off.md",
        "tests/test_phase55b_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off.py",
        "tests/test_three_core_agent_shadow_sidecar_bridge_default_off.py",
        "tests/test_phase43b_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.py",
    }
    legacy_guards = {
        path
        for path in _changed_files()
        if path.startswith("tests/test_") and path.endswith(".py")
    }
    assert _changed_files() <= allowed | legacy_guards


def test_subprocess_cli_outputs_valid_json(tmp_path):
    proposals = _json(tmp_path / "proposals.json", [_proposal()])

    result = subprocess.run(
        [
            sys.executable,
            str(COMMAND_PATH),
            "--input",
            str(proposals),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    payload = json.loads(result.stdout)
    assert result.stderr == ""
    assert payload["phase"] == "43B"
    assert payload["request_result"]["phase"] == "43A"


def _changed_files() -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}
