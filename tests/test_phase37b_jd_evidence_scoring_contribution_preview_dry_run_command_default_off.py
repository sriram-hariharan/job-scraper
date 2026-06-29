from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess

import run_jd_evidence_scoring_contribution_preview_dry_run as command
from run_jd_evidence_scoring_contribution_preview_dry_run import (
    DryRunLoadError,
    build_dry_run_payload,
    load_feature_packet_from_path,
    load_scoring_feature_rows_from_path,
    main,
)


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = ROOT / "run_jd_evidence_scoring_contribution_preview_dry_run.py"
DOC_PATH = (
    ROOT
    / "docs/phase37_jd_evidence_scoring_contribution_preview_dry_run_command_default_off.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "jd_evidence_scoring_contribution_preview_dry_run",
    "dry_run_command_only",
    "read_only",
    "advisory_only",
    "deterministic_contribution_preview",
    "requires_manual_user_control",
    "feature_packet_present",
    "scoring_feature_rows_present",
    "contribution_policy",
    "preview_result",
    "contribution_packet",
    "contribution_rows",
    "contribution_summary",
    "positive_contribution_points_total",
    "negative_contribution_points_total",
    "bounded_contribution_points_total",
    "high_positive_contribution_count",
    "negative_contribution_count",
    "red_flag_review_count",
    "existing_score_fields_detected",
    "existing_scores_preserved",
    "preview_ready_count",
    "preview_blocked_count",
    "dry_run_summary",
    "dry_run_key",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
    "evidence_matching_performed",
    "scoring_feature_preparation_performed",
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
    "auto_apply_performed",
    "auto_submit_performed",
}

FALSE_ACTION_KEYS = {
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
    "evidence_matching_performed",
    "scoring_feature_preparation_performed",
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
    "auto_apply_performed",
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
    "subprocess",
    "requests",
    "httpx",
    "urllib",
    "openai",
    "anthropic",
    "run_chat_completion",
    "_run_live_llm_tailoring",
    "run_prefilter(",
    "score_resume_job_match(",
    "build_jd_evidence_final_scoring_feature_adapter_default_off(",
    "execute_application(",
    "submit_application(",
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
    "phase 37b jd evidence scoring contribution preview dry-run command default-off",
    "jd evidence scoring contribution preview dry-run command",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "deterministic contribution preview",
    "reads supplied feature packet file",
    "supports json, jsonl, and csv scoring feature row inputs",
    "supports supplied scoring feature rows",
    "calls the phase 37a jd evidence scoring contribution preview helper",
    "prints advisory contribution preview json to stdout",
    "does not write output files",
    "produces bounded advisory contribution points",
    "preserves existing score fields",
    "does not produce final application score",
    "does not change existing scoring logic",
    "does not call matching/scoring modules",
    "does not run relevance prefilter",
    "does not run jd intelligence extraction",
    "does not run evidence matching",
    "does not run scoring feature preparation",
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
    "scoring feature preparation remains separate from final scoring",
    "contribution preview remains separate from final scoring",
    "final scoring remains deterministic and controlled by scoring logic",
    'python run_jd_evidence_scoring_contribution_preview_dry_run.py --input path/to/feature_packet.json',
    "phase37a-jd-evidence-scoring-contribution-preview-default-off-v1",
    "phase36-jd-evidence-final-scoring-feature-adapter-release-v1",
    "phase36b-jd-evidence-final-scoring-feature-adapter-dry-run-command-default-off-v1",
    "phase36a-jd-evidence-final-scoring-feature-adapter-default-off-v1",
    "phase35c-jd-signal-planning-artifact-evidence-enrichment-dry-run-command-default-off-v1",
    "phase35b-jd-signal-planning-artifact-evidence-enricher-default-off-v1",
    "phase35a-jd-signal-resume-evidence-matrix-default-off-v1",
    "phase34c-jd-intelligence-planning-artifact-enrichment-dry-run-command-default-off-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/jd_evidence_scoring_contribution_preview_default_off.py": "6bfd39eb1bc51e01b990ca0a44e13645187eb0a07cb6ac1e91f6c9456cd41fd8",
    "src/agents/jd_evidence_final_scoring_feature_adapter_default_off.py": "f7ec839c8810439f9ceb2fccd9938d34cbb2f623590f0c2c2bf80afeba6cc105",
    "run_jd_evidence_final_scoring_feature_adapter_dry_run.py": "1cae3e0cbefef29dcb176ce16df85d241d247411ab781eb5d838a21f9c425fad",
    "src/agents/jd_signal_planning_artifact_evidence_enricher_default_off.py": "0404ff9c89895b13cf5ccc55029820d2ff5b82fb2dbd3c0c1e426bd0e83335c8",
    "src/agents/jd_signal_resume_evidence_matrix_default_off.py": "1d0275337f4785730b27515f0e9830601fd9e3cc941fe21d2f7bb8257d64e9be",
    "run_jd_signal_planning_artifact_evidence_enrichment_dry_run.py": "9db84fca7407329f0b0f84f46fb030f4c975fef9db0197188f0429b435f3c7c3",
    "src/agents/jd_intelligence_planning_artifact_enricher_default_off.py": "f8e365ab51de647dc6b45ff0c99cce075273eec61e12fc96c744118e1ca68c53",
    "src/agents/jd_intelligence_llm_signal_extractor_default_off.py": "a73124801ce6768aebb934e1c6a7e76d4f9888bbb7b0ca28eb93e882e06f4f6c",
    "run_jd_intelligence_planning_artifact_enrichment_dry_run.py": "d3e45057168f4daabba13077f0d27b6eb89be4d2f443c4a43a42274557ef26bb",
    "src/agents/controlled_agent_router_planning_artifact_mapper_readonly.py": "1966a4d95eaf57b735545efd00e28803bba077192c81668165e9b3f491491fe8",
    "src/agents/controlled_agent_router_batch_handoff_plan_readonly.py": "7824233cbb4c6efd75481a8097a041488adfbd53f7c97e4832c02b8822741834",
    "src/agents/controlled_agent_router_workflow_state_adapter_readonly.py": "4f01b4e58c8e517ec633331da44341ee5596d486ae7d40d38fdca4666d6fa47e",
    "src/agents/controlled_agent_router_readonly.py": "c1cac3d8d1858b5143d0c3ca0082f3b908410020a0e4220c1dea9531cbf3655d",
    "run_controlled_agent_router_planning_artifact_dry_run.py": "1e49a69da5b306272319f2bef5e7162467f294aff4cbe37e8167125a56777dc4",
    "src/app/api.py": "dd69c4813e4e25f65f611a4dadea5094e524ecd1c3d2f250ff859673d24af2d9",
    "src/app/services.py": "2c67ab4d78299de8e54db6ef76ea77598f7e98c1d2f516df97cea4c014e7b6ee",
    "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
    "src/app/static/app_redesign.css": "62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_suggestions.py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def _row(**extra) -> dict:
    row = {
        "row_key": "item-1",
        "item_id": "item-1",
        "job_id": "job-1",
        "title": "Data Engineer",
        "company": "Acme",
        "existing_score_present": False,
        "existing_score_field": "",
        "existing_score_value": None,
        "evidence_ready": True,
        "scoring_inputs_ready": True,
        "required_skill_coverage_ratio": 1.0,
        "preferred_skill_coverage_ratio": 1.0,
        "tool_coverage_ratio": 1.0,
        "responsibility_coverage_ratio": 1.0,
        "missing_required_skill_count": 0,
        "missing_tool_count": 0,
        "red_flag_count": 0,
        "missing_required_skills": [],
        "missing_tools": [],
        "red_flag_findings": [],
        "requires_red_flag_review": False,
    }
    for key, value in extra.items():
        row[key] = value
    return row


def _packet(**extra) -> dict:
    packet = {
        "phase": "36A",
        "packet_type": "jd_evidence_final_scoring_features",
        "feature_row_count": 1,
        "scoring_feature_rows": [_row()],
        "final_score_included": False,
    }
    for key, value in extra.items():
        packet[key] = value
    return packet


def _assert_safe(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "37B"
    assert payload["default_off"] is True
    assert payload["jd_evidence_scoring_contribution_preview_dry_run"] is True
    assert payload["dry_run_command_only"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["deterministic_contribution_preview"] is True
    assert payload["requires_manual_user_control"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_command_module_is_import_safe(capsys):
    importlib.reload(command)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(load_feature_packet_from_path)
    assert callable(load_scoring_feature_rows_from_path)
    assert callable(build_dry_run_payload)
    assert callable(main)


def test_feature_packet_loader_loads_json_feature_packet_shapes(tmp_path):
    packet = _write(tmp_path / "packet.json", json.dumps(_packet()))
    wrapped = _write(tmp_path / "wrapped.json", json.dumps({"feature_packet": _packet()}))
    adapter = _write(
        tmp_path / "adapter.json",
        json.dumps({"adapter_result": {"feature_packet": _packet()}}),
    )
    rows = _write(tmp_path / "rows.json", json.dumps([_row()]))
    assert load_feature_packet_from_path(packet)["scoring_feature_rows"] == [_row()]
    assert load_feature_packet_from_path(wrapped)["scoring_feature_rows"] == [_row()]
    assert load_feature_packet_from_path(adapter)["scoring_feature_rows"] == [_row()]
    assert load_feature_packet_from_path(rows)["scoring_feature_rows"] == [_row()]


def test_feature_packet_loader_loads_wrapped_rows_jsonl_and_csv(tmp_path):
    for key in ("scoring_feature_rows", "feature_rows", "rows", "items"):
        wrapped = _write(tmp_path / f"{key}.json", json.dumps({key: [_row()]}))
        assert load_feature_packet_from_path(wrapped) == {
            "scoring_feature_rows": [_row()]
        }
    jsonl = _write(tmp_path / "rows.jsonl", json.dumps(_row()) + "\n")
    csv_path = _write(
        tmp_path / "rows.csv",
        "row_key,job_id,evidence_ready,scoring_inputs_ready,required_skill_coverage_ratio\nitem-1,job-1,true,true,1\n",
    )
    assert load_feature_packet_from_path(jsonl) == {"scoring_feature_rows": [_row()]}
    assert load_feature_packet_from_path(csv_path) == {
        "scoring_feature_rows": [
            {
                "row_key": "item-1",
                "job_id": "job-1",
                "evidence_ready": "true",
                "scoring_inputs_ready": "true",
                "required_skill_coverage_ratio": "1",
            }
        ]
    }


def test_scoring_feature_row_loader_loads_json_jsonl_and_csv(tmp_path):
    plain = _write(tmp_path / "rows.json", json.dumps([_row()]))
    wrapped = _write(
        tmp_path / "wrapped.json",
        json.dumps({"scoring_feature_rows": [_row()]}),
    )
    jsonl = _write(tmp_path / "rows.jsonl", json.dumps(_row()) + "\n")
    csv_path = _write(tmp_path / "rows.csv", "row_key,job_id\nitem-1,job-1\n")
    assert load_scoring_feature_rows_from_path(plain) == [_row()]
    assert load_scoring_feature_rows_from_path(wrapped) == [_row()]
    assert load_scoring_feature_rows_from_path(jsonl) == [_row()]
    assert load_scoring_feature_rows_from_path(csv_path) == [
        {"row_key": "item-1", "job_id": "job-1"}
    ]


def test_loader_error_paths_are_deterministic(tmp_path):
    unsupported = _write(tmp_path / "rows.yaml", "[]")
    invalid_json = _write(tmp_path / "bad.json", "{")
    invalid_jsonl = _write(tmp_path / "bad.jsonl", "[]\n")
    invalid_packet = _write(tmp_path / "badpacket.json", json.dumps({"foo": []}))
    invalid_rows = _write(tmp_path / "badrows.json", json.dumps({"foo": []}))
    for path in (unsupported, invalid_json, invalid_jsonl, invalid_packet):
        try:
            load_feature_packet_from_path(path)
        except ValueError as exc:
            assert str(exc)
        else:
            raise AssertionError(f"expected feature packet loader failure for {path}")
    try:
        load_scoring_feature_rows_from_path(invalid_rows)
    except ValueError as exc:
        assert "scoring_feature_rows" in str(exc)
    else:
        raise AssertionError("expected scoring feature row loader failure")


def test_build_dry_run_payload_returns_required_keys_and_preview_data():
    payload = build_dry_run_payload(feature_packet=_packet())
    _assert_safe(payload)
    assert payload["feature_packet_present"] is True
    assert payload["scoring_feature_rows_present"] is False
    assert payload["preview_result"]["phase"] == "37A"
    assert payload["contribution_packet"] == payload["preview_result"][
        "contribution_packet"
    ]
    assert payload["contribution_rows"] == payload["preview_result"][
        "contribution_rows"
    ]
    assert payload["contribution_summary"] == payload["preview_result"][
        "contribution_summary"
    ]
    assert payload["positive_contribution_points_total"] == 12.0
    assert payload["negative_contribution_points_total"] == 0
    assert payload["bounded_contribution_points_total"] == 12.0
    assert payload["preview_ready_count"] == 1
    assert payload["preview_blocked_count"] == 0


def test_explicit_scoring_feature_rows_take_precedence_and_preserve_scores():
    payload = build_dry_run_payload(
        feature_packet=_packet(scoring_feature_rows=[_row(job_id="packet")]),
        scoring_feature_rows=[
            _row(
                job_id="explicit",
                existing_score_present=True,
                existing_score_field="final_score",
                existing_score_value=91,
            )
        ],
    )
    _assert_safe(payload)
    assert payload["scoring_feature_rows_present"] is True
    assert payload["contribution_rows"][0]["job_id"] == "explicit"
    assert payload["existing_scores_preserved"] is True
    assert payload["existing_score_fields_detected"] == [
        {"row_key": "item-1", "field": "final_score", "value": 91}
    ]


def test_main_prints_json_to_stdout_for_valid_input(tmp_path, capsys):
    packet = _write(tmp_path / "packet.json", json.dumps(_packet()))
    code = main(["--input", str(packet)])
    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    _assert_safe(payload)
    assert payload["contribution_policy"]["max_positive_contribution_points"] == 12.0


def test_main_passes_contribution_policy_options(tmp_path, capsys):
    packet = _write(tmp_path / "packet.json", json.dumps(_packet()))
    code = main(
        [
            "--input",
            str(packet),
            "--max-positive-contribution-points",
            "5",
            "--max-negative-contribution-points",
            "-2",
            "--required-skill-weight",
            "4",
            "--preferred-skill-weight",
            "1",
            "--tool-weight",
            "1",
            "--responsibility-weight",
            "1",
            "--missing-required-skill-penalty",
            "-2",
            "--missing-tool-penalty",
            "-1",
            "--red-flag-penalty",
            "-4",
            "--red-flag-review-threshold",
            "2",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert code == 0
    assert payload["contribution_policy"] == {
        "max_positive_contribution_points": 5.0,
        "max_negative_contribution_points": -2.0,
        "required_skill_weight": 4.0,
        "preferred_skill_weight": 1.0,
        "tool_weight": 1.0,
        "responsibility_weight": 1.0,
        "missing_required_skill_penalty": -2.0,
        "missing_tool_penalty": -1.0,
        "red_flag_penalty": -4.0,
        "red_flag_review_threshold": 2,
    }


def test_main_returns_nonzero_for_missing_or_invalid_input(tmp_path, capsys):
    assert main([]) == 2
    missing = capsys.readouterr()
    assert "error: --input is required" in missing.err
    invalid = _write(tmp_path / "bad.json", "{")
    assert main(["--input", str(invalid)]) == 1
    bad = capsys.readouterr()
    assert "error: invalid JSON" in bad.err


def test_command_does_not_write_output_files(tmp_path, capsys):
    packet = _write(tmp_path / "packet.json", json.dumps(_packet()))
    before = sorted(path.name for path in tmp_path.iterdir())
    assert main(["--input", str(packet)]) == 0
    after = sorted(path.name for path in tmp_path.iterdir())
    assert before == after
    assert json.loads(capsys.readouterr().out)["dry_run_summary"][
        "output_file_written"
    ] is False


def test_payload_contains_no_tailoring_output_score_or_commands():
    payload = build_dry_run_payload(feature_packet=_packet())
    rendered = json.dumps(payload).lower()
    _assert_safe(payload)
    assert "generated_tailoring_text" not in rendered
    assert "provider_request" not in rendered
    assert "network_request" not in rendered
    assert "mutation_command" not in rendered
    assert "db_write_command" not in rendered
    assert "application_submission_command" not in rendered
    assert "application_score" not in payload
    assert payload["real_tailoring_output_created"] is False
    assert payload["final_score_produced"] is False
    assert payload["dry_run_summary"]["final_score_produced"] is False
    assert payload["dry_run_summary"]["existing_score_changed"] is False


def test_source_has_no_forbidden_imports_calls_or_writes():
    source = COMMAND_PATH.read_text(encoding="utf-8")
    assert "build_jd_evidence_scoring_contribution_preview_default_off" in source
    assert (
        "from src.agents.jd_evidence_scoring_contribution_preview_default_off import"
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


def test_changed_files_are_limited_to_phase37b_surface_and_legacy_guards():
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    allowed = {
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
