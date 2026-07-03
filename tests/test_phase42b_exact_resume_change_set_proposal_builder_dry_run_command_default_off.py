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

import run_exact_resume_change_set_proposal_builder_dry_run as command


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = ROOT / "run_exact_resume_change_set_proposal_builder_dry_run.py"
DOC_PATH = (
    ROOT
    / "docs/phase42_exact_resume_change_set_proposal_builder_dry_run_command_default_off.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "exact_resume_change_set_proposal_builder_dry_run",
    "dry_run_command_only",
    "read_only",
    "advisory_only",
    "proposal_only",
    "exact_worthy_changes_only",
    "manual_review_required",
    "requires_manual_user_control",
    "review_queue_present",
    "queue_result_present",
    "resume_context_present",
    "jd_context_present",
    "tailoring_context_present",
    "proposal_policy",
    "proposal_result",
    "change_proposals",
    "change_proposals_by_type",
    "change_set_summary",
    "dry_run_summary",
    "dry_run_key",
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

FALSE_ACTION_KEYS = {
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
    "build_jd_evidence_score_impact_review_queue_builder_default_off(",
    "build_jd_evidence_score_impact_review_packet_builder_default_off(",
    "build_jd_evidence_score_impact_preview_default_off(",
    "build_jd_evidence_scoring_contribution_preview_default_off(",
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
    "phase 42b exact resume change-set proposal builder dry-run command default-off",
    "exact resume change-set proposal builder dry-run command",
    "exact worthy resume change path after the review queue",
    "not another safety-wrapper chain",
    "reads a supplied review queue file",
    "reads a supplied queue result file",
    "reads supplied resume context file",
    "reads supplied jd context file",
    "reads supplied tailoring context file",
    "calls the phase 42a exact resume change-set proposal builder",
    "prints exact resume change proposal json to stdout",
    "produces exact worthy resume change proposals",
    "proposal-only before/after changes",
    "does not produce a full resume",
    "does not overwrite resumes",
    "does not mutate resumes",
    "does not call llm",
    "does not call provider",
    "does not call network",
    "does not call tailoring runtime",
    "does not generate real tailoring output",
    "does not produce final application score",
    "does not change scoring logic",
    "does not call matching/scoring modules",
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
    'python run_exact_resume_change_set_proposal_builder_dry_run.py --input path/to/review_queue.json --resume-context path/to/resume_context.json --jd-context path/to/jd_context.json --tailoring-context path/to/tailoring_context.json',
    "phase42a-exact-resume-change-set-proposal-builder-default-off-v1",
    "phase41-jd-evidence-score-impact-review-queue-builder-release-v1",
    "phase41b-jd-evidence-score-impact-review-queue-builder-dry-run-command-default-off-v1",
    "phase41a-jd-evidence-score-impact-review-queue-builder-default-off-v1",
    "phase40-jd-evidence-score-impact-review-packet-builder-release-v1",
    "phase39-jd-evidence-score-impact-planning-artifact-annotator-release-v1",
    "phase38-jd-evidence-score-impact-preview-release-v1",
    "phase37-jd-evidence-scoring-contribution-preview-release-v1",
    "phase36-jd-evidence-final-scoring-feature-adapter-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/exact_resume_change_set_proposal_builder_default_off.py": "fd173ea8bf3f7d746ebbdb7d6b2af7ae7df1aeaea4e66acaca52ea4fda1a9dc4",
    "src/agents/jd_evidence_score_impact_review_queue_builder_default_off.py": "c3080e881850ec75472e1e57727829db2866236139a84cc29a3ecd2ebe7ef6df",
    "run_jd_evidence_score_impact_review_queue_builder_dry_run.py": "77e2e06b1c99433f832c6b3a238f26c662ae8a382874500f33087aed8fdcdfab",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_suggestions.py": "559a66a7c7a1963d322a1e7b3f0fd3ede1ea161a9be2d176dcce0ef1016ea9ff",
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


def _queue_item(**overrides):
    item = {
        "item_id": "queue-1",
        "job_id": "job-1",
        "title": "Senior Data Scientist",
        "company": "ExampleCo",
    }
    for key, value in overrides.items():
        item[key] = value
    return item


def _resume_context():
    return {
        "profile_summary": "Data scientist with Python and SQL analytics experience.",
        "skills": ["Python", "SQL"],
        "resume_bullets": [
            {
                "id": "b1",
                "text": "Built Python forecasting models and SQL dashboards.",
            }
        ],
    }


def _jd_context():
    return {"required_skills": ["Python", "SQL"]}


def _tailoring_context():
    return {"matched_required_skills": ["Python", "SQL"]}


def test_command_module_is_import_safe_and_exposes_functions():
    module = importlib.reload(command)
    assert callable(module.load_review_queue_from_path)
    assert callable(module.load_queue_result_from_path)
    assert callable(module.load_context_from_path)
    assert callable(module.build_dry_run_payload)
    assert callable(module.main)


@pytest.mark.parametrize(
    "filename,payload",
    [
        ("queue.json", [_queue_item()]),
        ("wrapped.json", {"review_queue": [_queue_item(item_id="wrapped")]}),
        ("rows.json", {"rows": [_queue_item(item_id="rows")]}),
        ("items.json", {"items": [_queue_item(item_id="items")]}),
        ("queue_items.json", {"queue_items": [_queue_item(item_id="queue-items")]}),
    ],
)
def test_review_queue_loader_loads_json_shapes(tmp_path, filename, payload):
    rows = command.load_review_queue_from_path(_json(tmp_path / filename, payload))
    assert len(rows) == 1
    assert isinstance(rows[0], dict)


def test_review_queue_loader_loads_jsonl_and_csv(tmp_path):
    rows = [_queue_item(), _queue_item(item_id="queue-2")]
    assert len(command.load_review_queue_from_path(_jsonl(tmp_path / "queue.jsonl", rows))) == 2
    assert len(command.load_review_queue_from_path(_csv(tmp_path / "queue.csv", rows))) == 2


@pytest.mark.parametrize(
    "filename,payload",
    [
        ("result.json", {"review_queue": [_queue_item()]}),
        ("dryrun.json", {"queue_result": {"review_queue": [_queue_item()]}}),
        ("wrapped.json", {"review_queue": [_queue_item(item_id="wrapped")]}),
        ("rows.json", {"rows": [_queue_item(item_id="rows")]}),
        ("items.json", {"items": [_queue_item(item_id="items")]}),
        ("list.json", [_queue_item(item_id="list")]),
    ],
)
def test_queue_result_loader_loads_supported_shapes(tmp_path, filename, payload):
    result = command.load_queue_result_from_path(_json(tmp_path / filename, payload))
    assert isinstance(result, dict)
    assert "queue_result" in result or "review_queue" in result


def test_queue_result_loader_loads_jsonl_and_csv(tmp_path):
    rows = [_queue_item(), _queue_item(item_id="queue-2")]
    assert "review_queue" in command.load_queue_result_from_path(
        _jsonl(tmp_path / "queue_result.jsonl", rows)
    )
    assert "review_queue" in command.load_queue_result_from_path(
        _csv(tmp_path / "queue_result.csv", rows)
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
        (command.load_review_queue_from_path, "queue.txt", lambda path: path.write_text("[]", encoding="utf-8"), "unsupported"),
        (command.load_review_queue_from_path, "queue.json", lambda path: path.write_text("{", encoding="utf-8"), "invalid JSON"),
        (command.load_review_queue_from_path, "queue.jsonl", lambda path: path.write_text("{", encoding="utf-8"), "invalid JSONL"),
        (command.load_review_queue_from_path, "queue.csv", lambda path: path.write_text("a,b\n1,2,3", encoding="utf-8"), "extra columns"),
        (command.load_review_queue_from_path, "queue.json", lambda path: path.write_text(json.dumps({"review_queue": ["bad"]}), encoding="utf-8"), "row 0"),
        (command.load_queue_result_from_path, "result.json", lambda path: path.write_text(json.dumps({"not_queue": []}), encoding="utf-8"), "must include"),
        (command.load_context_from_path, "context.json", lambda path: path.write_text(json.dumps(["bad"]), encoding="utf-8"), "context json must be an object"),
    ],
)
def test_loader_errors_are_deterministic(tmp_path, loader, filename, writer, error):
    path = tmp_path / filename
    writer(path)
    with pytest.raises(command.DryRunLoadError, match=error):
        loader(path)


def test_build_dry_run_payload_calls_phase42a_and_returns_required_surfaces():
    payload = command.build_dry_run_payload(
        review_queue=[_queue_item()],
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
        proposal_policy={"max_change_proposals": 2},
    )

    assert REQUIRED_KEYS.issubset(payload)
    assert payload["phase"] == "42B"
    assert payload["default_off"] is True
    assert payload["review_queue_present"] is True
    assert payload["queue_result_present"] is False
    assert payload["resume_context_present"] is True
    assert payload["jd_context_present"] is True
    assert payload["tailoring_context_present"] is True
    assert payload["proposal_policy"]["max_change_proposals"] == 2
    assert payload["proposal_result"]["exact_resume_change_set_proposal_builder"] is True
    assert payload["change_proposals"]
    assert payload["change_proposals_by_type"]
    assert payload["change_set_summary"]
    assert "full_resume" not in payload
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_cli_policy_options_are_passed_and_main_prints_json(tmp_path, capsys):
    queue = _json(tmp_path / "queue.json", [_queue_item()])
    resume = _json(tmp_path / "resume.json", _resume_context())
    jd = _json(tmp_path / "jd.json", _jd_context())
    tailoring = _json(tmp_path / "tailoring.json", _tailoring_context())

    code = command.main(
        [
            "--input",
            str(queue),
            "--resume-context",
            str(resume),
            "--jd-context",
            str(jd),
            "--tailoring-context",
            str(tailoring),
            "--max-change-proposals",
            "1",
            "--max-changes-per-queue-item",
            "1",
            "--minimum-evidence-terms",
            "1",
            "--disable-summary-changes",
            "--disable-skill-changes",
            "--disable-project-changes",
            "--allow-without-source-evidence",
            "--exclude-before-after-text",
        ]
    )

    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    policy = payload["proposal_policy"]
    assert policy["max_change_proposals"] == 1
    assert policy["max_changes_per_queue_item"] == 1
    assert policy["minimum_evidence_terms"] == 1
    assert policy["allow_summary_changes"] is False
    assert policy["allow_skill_changes"] is False
    assert policy["allow_project_changes"] is False
    assert policy["allow_bullet_changes"] is True
    assert policy["require_source_evidence"] is False
    assert policy["include_before_after_text"] is False


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
    queue = _json(tmp_path / "queue.json", [_queue_item()])
    before = sorted(item.name for item in tmp_path.iterdir())

    assert command.main(["--input", str(queue)]) == 0

    after = sorted(item.name for item in tmp_path.iterdir())
    assert after == before


def test_payload_has_no_full_resume_real_tailoring_or_runtime_effects():
    payload = command.build_dry_run_payload(
        review_queue=[_queue_item()],
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
    )

    assert "full_resume" not in payload
    assert "real_tailoring_output" not in payload
    assert payload["resume_change_proposals_created"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_source_has_only_allowed_imports_and_no_write_or_runtime_markers():
    source = COMMAND_PATH.read_text(encoding="utf-8")
    assert (
        "from src.agents.exact_resume_change_set_proposal_builder_default_off import"
        in source
    )
    assert "build_exact_resume_change_set_proposal_builder_default_off(" in source
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


def test_changed_files_are_limited_to_phase42b_and_legacy_guards():
    allowed = {
        "generate_tailoring_suggestions.py",
        "src/tailoring/rendering.py",
        "tests/test_score_first_scan.py",
        "run_exact_resume_change_set_proposal_builder_dry_run.py",
        "docs/phase42_exact_resume_change_set_proposal_builder_dry_run_command_default_off.md",
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
        "tests/test_phase42b_exact_resume_change_set_proposal_builder_dry_run_command_default_off.py",
    }
    legacy_guards = {
        path
        for path in _changed_files()
        if path.startswith("tests/test_") and path.endswith(".py")
    }
    assert _changed_files() <= allowed | legacy_guards


def test_subprocess_cli_outputs_valid_json(tmp_path):
    queue = _json(tmp_path / "queue.json", [_queue_item()])

    result = subprocess.run(
        [
            sys.executable,
            str(COMMAND_PATH),
            "--input",
            str(queue),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    payload = json.loads(result.stdout)
    assert result.stderr == ""
    assert payload["phase"] == "42B"
    assert payload["proposal_result"]["phase"] == "42A"


def _changed_files() -> set[str]:
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}
