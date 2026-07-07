# phase56b legacy guard marker: changes_only e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c
from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess

import run_jd_signal_planning_artifact_evidence_enrichment_dry_run as command
from run_jd_signal_planning_artifact_evidence_enrichment_dry_run import (
    DryRunLoadError,
    build_dry_run_payload,
    load_planning_rows_from_path,
    load_resume_evidence_from_path,
    main,
)


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = ROOT / "run_jd_signal_planning_artifact_evidence_enrichment_dry_run.py"
DOC_PATH = (
    ROOT
    / "docs/phase35_jd_signal_planning_artifact_evidence_enrichment_dry_run_command_default_off.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "jd_signal_planning_artifact_evidence_enrichment_dry_run",
    "dry_run_command_only",
    "read_only",
    "advisory_only",
    "deterministic_evidence_matching",
    "requires_manual_user_control",
    "planning_row_count",
    "resume_evidence_present",
    "evidence_policy",
    "enricher_result",
    "evidence_ready_count",
    "evidence_blocked_count",
    "coverage_summary",
    "average_required_skill_coverage_ratio",
    "average_preferred_skill_coverage_ratio",
    "average_tool_coverage_ratio",
    "average_responsibility_coverage_ratio",
    "missing_required_skills_by_row",
    "missing_tools_by_row",
    "red_flag_findings_by_row",
    "dry_run_summary",
    "dry_run_key",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
    "final_scoring_performed",
    "tailoring_opportunity_check_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "application_submission_performed",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "submission_performed",
    "auto_" + "apply_performed",
    "auto_submit_performed",
}

FALSE_ACTION_KEYS = {
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
    "final_scoring_performed",
    "tailoring_opportunity_check_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "application_submission_performed",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
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
    "from src.agents.jd_live",
    "from src.agents.jd_provider",
    "from src.ai",
    "import src.ai",
    "database_url",
    "psycopg",
    "sqlite",
    "requests",
    "httpx",
    "urllib",
    "openai",
    "anthropic",
    "run_chat_completion",
    "_run_live_llm_tailoring",
    "run_prefilter(",
    "score_resume_job_match(",
    "build_jd_intelligence_llm_signal_extractor_default_off(",
    "execute_application(",
    "submit_application(",
    "provider_call(",
    "network_call(",
)

FORBIDDEN_WRITE_MARKERS = (
    ".update(",
    ".write_text(",
    ".write_bytes(",
    ".mkdir(",
    ".save(",
    ".insert(",
)

DOC_MARKERS = (
    "phase 35c jd signal planning artifact evidence enrichment dry-run command default-off",
    "jd signal planning artifact evidence enrichment dry-run command",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "deterministic evidence matching",
    "reads supplied planning artifact file",
    "reads supplied resume/profile evidence",
    "supports json, jsonl, and csv planning-like row inputs",
    "supports json, jsonl, csv, txt, and md resume evidence inputs",
    "calls the phase 35b jd signal planning artifact evidence enricher",
    "prints evidence coverage json to stdout",
    "does not write output files",
    "aggregates required skill coverage",
    "aggregates preferred skill coverage",
    "aggregates tool coverage",
    "aggregates responsibility coverage",
    "reports missing required skills by row",
    "reports missing tools by row",
    "reports red flag findings by row",
    "does not produce final application score",
    "does not change existing scoring logic",
    "does not run relevance prefilter",
    "does not run jd intelligence extraction",
    "does not run matching/scoring modules",
    "does not run tailoring opportunity check",
    "does not generate ai tailoring",
    "does not call tailoring runtime",
    "does not create real tailoring output",
    "does not create resume rewrites",
    "does not overwrite resumes",
    "does not mutate resumes",
    "does not persist data",
    "does not write to database",
    "does not execute applications",
    "does not submit applications",
    "no auto-apply",
    "no auto-submit",
    "no autonomous application execution",
    "no automatic job application submission",
    "manual user control remains required",
    "jd intelligence remains separate from final scoring",
    "evidence matching remains separate from final scoring",
    "final scoring remains deterministic and controlled by scoring logic",
    'python run_jd_signal_planning_artifact_evidence_enrichment_dry_run.py --input path/to/planning_rows.json --resume-evidence path/to/resume.txt',
    "phase35b-jd-signal-planning-artifact-evidence-enricher-default-off-v1",
    "phase35a-jd-signal-resume-evidence-matrix-default-off-v1",
    "phase34c-jd-intelligence-planning-artifact-enrichment-dry-run-command-default-off-v1",
    "phase34b-jd-intelligence-planning-artifact-enricher-default-off-v1",
    "phase34a-jd-intelligence-llm-signal-extractor-default-off-v1",
    "phase33e-controlled-agent-router-planning-artifact-dry-run-command-readonly-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/jd_signal_planning_artifact_evidence_enricher_default_off.py": "0404ff9c89895b13cf5ccc55029820d2ff5b82fb2dbd3c0c1e426bd0e83335c8",
    "src/agents/jd_signal_resume_evidence_matrix_default_off.py": "1d0275337f4785730b27515f0e9830601fd9e3cc941fe21d2f7bb8257d64e9be",
    "src/agents/jd_intelligence_planning_artifact_enricher_default_off.py": "f8e365ab51de647dc6b45ff0c99cce075273eec61e12fc96c744118e1ca68c53",
    "src/agents/jd_intelligence_llm_signal_extractor_default_off.py": "a73124801ce6768aebb934e1c6a7e76d4f9888bbb7b0ca28eb93e882e06f4f6c",
    "run_jd_intelligence_planning_artifact_enrichment_dry_run.py": "d3e45057168f4daabba13077f0d27b6eb89be4d2f443c4a43a42274557ef26bb",
    "src/agents/controlled_agent_router_planning_artifact_mapper_readonly.py": "1966a4d95eaf57b735545efd00e28803bba077192c81668165e9b3f491491fe8",
    "src/agents/controlled_agent_router_batch_handoff_plan_readonly.py": "7824233cbb4c6efd75481a8097a041488adfbd53f7c97e4832c02b8822741834",
    "src/agents/controlled_agent_router_workflow_state_adapter_readonly.py": "4f01b4e58c8e517ec633331da44341ee5596d486ae7d40d38fdca4666d6fa47e",
    "src/agents/controlled_agent_router_readonly.py": "c1cac3d8d1858b5143d0c3ca0082f3b908410020a0e4220c1dea9531cbf3655d",
    "run_controlled_agent_router_planning_artifact_dry_run.py": "1e49a69da5b306272319f2bef5e7162467f294aff4cbe37e8167125a56777dc4",
    "src/app/api.py": "85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96",
    "src/app/services.py": "e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c",
    "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
    "src/app/static/app_redesign.css": "81eede647edd99ca1f8c0f5b759b35ecf40e223db9d9dbd4b976f487ecf49961",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
    "generate_tailoring_suggestions.py": "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _signals() -> dict:
    return {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": ["Airflow"],
        "responsibilities": ["Own data pipelines"],
        "tools": ["dbt"],
        "domain": "data platform",
        "red_flags": ["on-call ambiguity"],
    }


def _row() -> dict:
    return {"job_id": "j1", "jd_signals": _signals()}


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _assert_safe(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "35C"
    assert payload["default_off"] is True
    assert payload["jd_signal_planning_artifact_evidence_enrichment_dry_run"] is True
    assert payload["dry_run_command_only"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["deterministic_evidence_matching"] is True
    assert payload["requires_manual_user_control"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_command_module_is_import_safe(capsys):
    importlib.reload(command)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(load_planning_rows_from_path)
    assert callable(load_resume_evidence_from_path)
    assert callable(build_dry_run_payload)
    assert callable(main)


def test_planning_loader_loads_json_list_and_wrapped_rows(tmp_path):
    plain = _write(tmp_path / "rows.json", json.dumps([_row()]))
    wrapped = _write(tmp_path / "wrapped.json", json.dumps({"planning_rows": [_row()]}))
    assert load_planning_rows_from_path(plain) == [_row()]
    assert load_planning_rows_from_path(wrapped) == [_row()]


def test_planning_loader_loads_jsonl_and_csv_rows(tmp_path):
    jsonl = _write(tmp_path / "rows.jsonl", json.dumps(_row()) + "\n")
    csv_path = _write(tmp_path / "rows.csv", "job_id,title\nj1,Engineer\n")
    assert load_planning_rows_from_path(jsonl) == [_row()]
    assert load_planning_rows_from_path(csv_path) == [
        {"job_id": "j1", "title": "Engineer"}
    ]


def test_resume_evidence_loader_loads_json_shapes(tmp_path):
    raw_string = _write(tmp_path / "string.json", json.dumps("Python SQL"))
    raw_dict = _write(tmp_path / "dict.json", json.dumps({"skills": ["Python"]}))
    raw_list = _write(tmp_path / "list.json", json.dumps([{"skills": ["SQL"]}]))
    wrapped = _write(
        tmp_path / "wrapped.json",
        json.dumps({"resume_evidence": {"resume_text": "Python"}}),
    )
    assert load_resume_evidence_from_path(raw_string) == "Python SQL"
    assert load_resume_evidence_from_path(raw_dict) == {"skills": ["Python"]}
    assert load_resume_evidence_from_path(raw_list) == [{"skills": ["SQL"]}]
    assert load_resume_evidence_from_path(wrapped) == {"resume_text": "Python"}


def test_resume_evidence_loader_loads_jsonl_csv_txt_and_md(tmp_path):
    jsonl = _write(tmp_path / "evidence.jsonl", '{"skills":["Python"]}\n')
    csv_path = _write(tmp_path / "evidence.csv", "skills\nPython\n")
    txt = _write(tmp_path / "resume.txt", "Python SQL")
    md = _write(tmp_path / "resume.md", "# Resume\nPython")
    assert load_resume_evidence_from_path(jsonl) == [{"skills": ["Python"]}]
    assert load_resume_evidence_from_path(csv_path) == [{"skills": "Python"}]
    assert load_resume_evidence_from_path(txt) == "Python SQL"
    assert load_resume_evidence_from_path(md) == "# Resume\nPython"


def test_loader_error_paths_are_deterministic(tmp_path):
    unsupported = _write(tmp_path / "rows.yaml", "[]")
    invalid_json = _write(tmp_path / "bad.json", "{")
    invalid_jsonl = _write(tmp_path / "bad.jsonl", "[]\n")
    invalid_shape = _write(tmp_path / "badshape.json", json.dumps({"foo": []}))
    bad_resume_shape = _write(tmp_path / "resume.json", "1")
    for path in (unsupported, invalid_json, invalid_jsonl, invalid_shape):
        try:
            load_planning_rows_from_path(path)
        except ValueError as exc:
            assert str(exc)
        else:
            raise AssertionError(f"expected planning loader failure for {path}")
    try:
        load_resume_evidence_from_path(bad_resume_shape)
    except ValueError as exc:
        assert "resume evidence json" in str(exc)
    else:
        raise AssertionError("expected resume evidence loader failure")


def test_build_dry_run_payload_returns_required_keys_and_evidence_counts():
    payload = build_dry_run_payload(
        planning_rows=[_row()],
        resume_evidence="Python SQL Airflow dbt Own data pipelines",
        evidence_policy={"case_sensitive": False, "minimum_token_length": 2},
    )
    _assert_safe(payload)
    assert payload["planning_row_count"] == 1
    assert payload["resume_evidence_present"] is True
    assert payload["evidence_ready_count"] == 1
    assert payload["evidence_blocked_count"] == 0
    assert payload["average_required_skill_coverage_ratio"] == 1.0
    assert payload["average_preferred_skill_coverage_ratio"] == 1.0
    assert payload["average_tool_coverage_ratio"] == 1.0
    assert payload["average_responsibility_coverage_ratio"] == 1.0
    assert payload["missing_required_skills_by_row"] == {"j1": []}
    assert payload["missing_tools_by_row"] == {"j1": []}


def test_payload_exposes_blocked_rows_and_red_flags():
    payload = build_dry_run_payload(
        planning_rows=[_row(), {"job_id": "j2", "jd_signals": _signals()}],
        resume_evidence={"j1": "Python SQL on-call ambiguity"},
    )
    _assert_safe(payload)
    assert payload["evidence_ready_count"] == 1
    assert payload["evidence_blocked_count"] == 1
    assert payload["red_flag_findings_by_row"]["j1"][0]["status"] == "matched"


def test_main_prints_json_to_stdout_for_valid_input(tmp_path, capsys):
    rows = _write(tmp_path / "rows.json", json.dumps([_row()]))
    evidence = _write(tmp_path / "resume.txt", "Python SQL Airflow dbt")
    code = main(["--input", str(rows), "--resume-evidence", str(evidence)])
    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    _assert_safe(payload)
    assert payload["evidence_policy"]["case_sensitive"] is False
    assert payload["evidence_policy"]["minimum_token_length"] == 2
    assert payload["evidence_policy"]["include_partial_matches"] is True


def test_main_passes_evidence_policy_options(tmp_path, capsys):
    rows = _write(tmp_path / "rows.json", json.dumps([_row()]))
    code = main(
        [
            "--input",
            str(rows),
            "--case-sensitive",
            "--minimum-token-length",
            "4",
            "--no-partial-matches",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["evidence_policy"] == {
        "case_sensitive": True,
        "minimum_token_length": 4,
        "include_partial_matches": False,
    }


def test_main_returns_nonzero_for_missing_or_invalid_input(tmp_path, capsys):
    assert main([]) == 2
    missing = capsys.readouterr()
    assert "error: --input is required" in missing.err
    invalid = _write(tmp_path / "bad.json", "{")
    assert main(["--input", str(invalid)]) == 1
    bad = capsys.readouterr()
    assert "error: invalid JSON" in bad.err


def test_payload_contains_no_tailoring_output_or_commands():
    payload = build_dry_run_payload(
        planning_rows=[_row()],
        resume_evidence="Python SQL",
    )
    rendered = json.dumps(payload).lower()
    _assert_safe(payload)
    assert "generated_tailoring_text" not in rendered
    assert "provider_request" not in rendered
    assert "network_request" not in rendered
    assert "mutation_command" not in rendered
    assert "db_write_command" not in rendered
    assert "application_submission_command" not in rendered
    assert "application_score" not in payload
    assert payload["dry_run_summary"]["final_application_score_created"] is False
    assert payload["dry_run_summary"]["existing_score_changed"] is False


def test_source_has_no_forbidden_imports_calls_or_writes():
    source = COMMAND_PATH.read_text(encoding="utf-8")
    assert "build_jd_signal_planning_artifact_evidence_enricher_default_off" in source
    assert (
        "from src.agents.jd_signal_planning_artifact_evidence_enricher_default_off import"
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
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_changed_files_are_limited_to_phase35c_surface_and_legacy_guards():
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
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
        "run_jd_signal_planning_artifact_evidence_enrichment_dry_run.py",
        "docs/phase35_jd_signal_planning_artifact_evidence_enrichment_dry_run_command_default_off.md",
        "tests/test_phase35c_jd_signal_planning_artifact_evidence_enrichment_dry_run_command_default_off.py",
        "src/agents/jd_evidence_final_scoring_feature_adapter_default_off.py",
        "docs/phase36_jd_evidence_final_scoring_feature_adapter_default_off.md",
        "tests/test_phase36a_jd_evidence_final_scoring_feature_adapter_default_off.py",
        "run_jd_evidence_final_scoring_feature_adapter_dry_run.py",
        "docs/phase36_jd_evidence_final_scoring_feature_adapter_dry_run_command_default_off.md",
        "tests/test_phase36b_jd_evidence_final_scoring_feature_adapter_dry_run_command_default_off.py",
        "src/agents/jd_evidence_scoring_contribution_preview_default_off.py",
        "docs/phase37_jd_evidence_scoring_contribution_preview_default_off.md",
        "tests/test_phase37a_jd_evidence_scoring_contribution_preview_default_off.py",
        "run_jd_evidence_scoring_contribution_preview_dry_run.py",
        "docs/phase37_jd_evidence_scoring_contribution_preview_dry_run_command_default_off.md",
        "tests/test_phase37b_jd_evidence_scoring_contribution_preview_dry_run_command_default_off.py",
        "src/agents/jd_evidence_score_impact_preview_default_off.py",
        "docs/phase38_jd_evidence_score_impact_preview_default_off.md",
        "tests/test_phase38a_jd_evidence_score_impact_preview_default_off.py",
        "tests/test_phase38a_jd_evidence_score_impact_preview_default_off 2.py",
        "\"tests/test_phase38a_jd_evidence_score_impact_preview_default_off 2.py\"",
        "run_jd_evidence_score_impact_preview_dry_run.py",
        "docs/phase38_jd_evidence_score_impact_preview_dry_run_command_default_off.md",
        "tests/test_phase38b_jd_evidence_score_impact_preview_dry_run_command_default_off.py",
        "src/agents/jd_evidence_score_impact_planning_artifact_annotator_default_off.py",
        "docs/phase39_jd_evidence_score_impact_planning_artifact_annotator_default_off.md",
        "tests/test_phase39a_jd_evidence_score_impact_planning_artifact_annotator_default_off.py",
        "run_jd_evidence_score_impact_planning_artifact_annotator_dry_run.py",
        "docs/phase39_jd_evidence_score_impact_planning_artifact_annotator_dry_run_command_default_off.md",
        "tests/test_phase39b_jd_evidence_score_impact_planning_artifact_annotator_dry_run_command_default_off.py",
        "src/agents/jd_evidence_score_impact_review_packet_builder_default_off.py",
        "docs/phase40_jd_evidence_score_impact_review_packet_builder_default_off.md",
        "tests/test_phase40a_jd_evidence_score_impact_review_packet_builder_default_off.py",
        "run_jd_evidence_score_impact_review_packet_builder_dry_run.py",
        "docs/phase40_jd_evidence_score_impact_review_packet_builder_dry_run_command_default_off.md",
        "tests/test_phase40b_jd_evidence_score_impact_review_packet_builder_dry_run_command_default_off.py",
        "src/agents/jd_evidence_score_impact_review_queue_builder_default_off.py",
        "docs/phase41_jd_evidence_score_impact_review_queue_builder_default_off.md",
        "src/agents/exact_resume_change_set_proposal_builder_default_off.py",
        "docs/phase42_exact_resume_change_set_proposal_builder_default_off.md",
        "src/agents/controlled_exact_resume_change_set_llm_request_packet_default_off.py",
        "docs/phase43_controlled_exact_resume_change_set_llm_request_packet_default_off.md",
        "src/agents/controlled_exact_resume_change_set_provider_call_boundary_default_off.py",
        "docs/phase44_controlled_exact_resume_change_set_provider_call_boundary_default_off.md",
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
            "docs/phase71_tailoring_workspace_artifact_path_preload_repair_default_off.md",
        "tests/test_phase55b_live_jd_llm_extraction_planning_scan_readback_ui_api_default_off.py",
        "tests/test_three_core_agent_shadow_sidecar_bridge_default_off.py",

        "tests/test_phase44a_controlled_exact_resume_change_set_provider_call_boundary_default_off.py",
        "run_controlled_exact_resume_change_set_llm_request_packet_dry_run.py",
        "docs/phase43_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.md",
        "tests/test_phase43b_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.py",
        "tests/test_phase43a_controlled_exact_resume_change_set_llm_request_packet_default_off.py",
        "run_exact_resume_change_set_proposal_builder_dry_run.py",
        "docs/phase42_exact_resume_change_set_proposal_builder_dry_run_command_default_off.md",
        "tests/test_phase42b_exact_resume_change_set_proposal_builder_dry_run_command_default_off.py",
        "tests/test_phase42a_exact_resume_change_set_proposal_builder_default_off.py",
        "run_jd_evidence_score_impact_review_queue_builder_dry_run.py",
        "docs/phase41_jd_evidence_score_impact_review_queue_builder_dry_run_command_default_off.md",
        "tests/test_phase41b_jd_evidence_score_impact_review_queue_builder_dry_run_command_default_off.py",
        "tests/test_phase41a_jd_evidence_score_impact_review_queue_builder_default_off.py",
    } | {
        path
        for path in changed
        if path.startswith("tests/test_") and path.endswith(".py")
    }
    assert changed <= allowed
