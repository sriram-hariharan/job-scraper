from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess

import pytest

import run_jd_evidence_score_impact_review_packet_builder_dry_run as command


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = ROOT / "run_jd_evidence_score_impact_review_packet_builder_dry_run.py"
DOC_PATH = (
    ROOT
    / "docs/phase40_jd_evidence_score_impact_review_packet_builder_dry_run_command_default_off.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "jd_evidence_score_impact_review_packet_builder_dry_run",
    "dry_run_command_only",
    "read_only",
    "advisory_only",
    "preview_only",
    "deterministic_review_packet_building",
    "manual_review_packet_only",
    "requires_manual_user_control",
    "annotated_rows_present",
    "annotator_result_present",
    "review_policy",
    "builder_result",
    "review_packets",
    "review_packets_by_recommendation",
    "review_packet_summary",
    "manual_review_count",
    "positive_review_count",
    "negative_review_count",
    "neutral_review_count",
    "unmatched_count",
    "unknown_review_count",
    "score_preview_available_count",
    "score_preview_blocked_count",
    "red_flag_review_count",
    "existing_score_fields_detected",
    "existing_scores_preserved",
    "dry_run_summary",
    "dry_run_key",
    "hypothetical_score_preview_produced",
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
    "contribution_preview_performed",
    "score_impact_preview_performed",
    "planning_annotation_performed",
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
    "contribution_preview_performed",
    "score_impact_preview_performed",
    "planning_annotation_performed",
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
    "build_jd_evidence_score_impact_preview_default_off(",
    "build_jd_evidence_scoring_contribution_preview_default_off(",
    "build_jd_evidence_score_impact_planning_artifact_annotator_default_off(",
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
    "phase 40b jd evidence score impact review packet builder dry-run command default-off",
    "jd evidence score impact review packet builder dry-run command",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "deterministic review packet building",
    "reads supplied annotated planning row file",
    "reads supplied annotator result file",
    "supports json, jsonl, and csv annotated planning row inputs",
    "supports supplied annotator results",
    "calls the phase 40a jd evidence score impact review packet builder",
    "prints operator review packet json to stdout",
    "does not write output files",
    "builds operator review packets from score impact annotated planning rows",
    "groups review packets by score impact review recommendation",
    "produces manual-review packet only output",
    "preserves existing score fields",
    "does not produce final application score",
    "does not change existing scoring logic",
    "does not call matching/scoring modules",
    "does not run relevance prefilter",
    "does not run jd intelligence extraction",
    "does not run evidence matching",
    "does not run scoring feature preparation",
    "does not run contribution preview",
    "does not run score impact preview",
    "does not run planning annotation",
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
    "score impact preview remains separate from final scoring",
    "planning annotation remains separate from final scoring",
    "review packet building remains separate from final scoring",
    "final scoring remains deterministic and controlled by scoring logic",
    "phase40a-jd-evidence-score-impact-review-packet-builder-default-off-v1",
    "phase39-jd-evidence-score-impact-planning-artifact-annotator-release-v1",
    "phase39b-jd-evidence-score-impact-planning-artifact-annotator-dry-run-command-default-off-v1",
    "phase39a-jd-evidence-score-impact-planning-artifact-annotator-default-off-v1",
    "phase38-jd-evidence-score-impact-preview-release-v1",
    "phase38b-jd-evidence-score-impact-preview-dry-run-command-default-off-v1",
    "phase38a-jd-evidence-score-impact-preview-default-off-v1",
    "phase37-jd-evidence-scoring-contribution-preview-release-v1",
    "phase36-jd-evidence-final-scoring-feature-adapter-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/jd_evidence_score_impact_review_packet_builder_default_off.py": "daa472f00511e16d37975472dcf06fcd7ffcd3f353509d8524e949baae137f68",
    "src/agents/jd_evidence_score_impact_planning_artifact_annotator_default_off.py": "fd0903a249d46f609f2fd790ac5100b2ef7554132749de349b33162c22b4ed6f",
    "run_jd_evidence_score_impact_planning_artifact_annotator_dry_run.py": "61401301966d5e7957e9aabacd485d42b663e3ca8f2f1bc3d774ee407aeaabce",
    "src/agents/jd_evidence_score_impact_preview_default_off.py": "94799582377fabd147fb134746d5b17a88b500589a6241e91a263356f1678ef1",
    "run_jd_evidence_score_impact_preview_dry_run.py": "73c27a8c1e86a880a02766e9a64917b5c699ebacac5e127c6330c51b3c1a6bbb",
    "src/agents/jd_evidence_scoring_contribution_preview_default_off.py": "6bfd39eb1bc51e01b990ca0a44e13645187eb0a07cb6ac1e91f6c9456cd41fd8",
    "run_jd_evidence_scoring_contribution_preview_dry_run.py": "3890723174effc02370619c563ca33f41101f55318bd4c54796a9a03408aeae5",
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


def _json(path: Path, payload) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _jsonl(path: Path, rows: list[dict]) -> Path:
    path.write_text("\n".join(json.dumps(row) for row in rows), encoding="utf-8")
    return path


def _csv(path: Path, rows: list[dict]) -> Path:
    fields = list(rows[0].keys())
    lines = [",".join(fields)]
    for row in rows:
        lines.append(",".join(str(row.get(field, "")) for field in fields))
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def _annotated_row(**extra) -> dict:
    row = {
        "item_id": "item-1",
        "job_id": "job-1",
        "id": "row-1",
        "title": "Data Engineer",
        "company": "Acme",
        "location": "Remote",
        "source_url": "https://example.test/job",
        "existing_score_present": True,
        "existing_score_field": "final_score",
        "existing_score_value": 80,
        "score_impact_preview_result": {"matched": True},
        "score_impact_preview": {
            "hypothetical_score_preview": 87,
            "score_preview_delta": 7,
            "score_preview_available": True,
            "score_preview_blocked_reason": "",
            "impact_band": "positive",
            "requires_red_flag_review": False,
        },
        "score_impact_review_recommendation": "positive_review",
        "score_impact_annotation_ready": True,
        "score_impact_annotation_source": "impact_rows",
        "final_score_produced": False,
        "existing_score_changed": False,
    }
    for key, value in extra.items():
        row[key] = value
    return row


def _assert_safe(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "40B"
    assert payload["default_off"] is True
    assert payload["jd_evidence_score_impact_review_packet_builder_dry_run"] is True
    assert payload["dry_run_command_only"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["preview_only"] is True
    assert payload["deterministic_review_packet_building"] is True
    assert payload["manual_review_packet_only"] is True
    assert payload["requires_manual_user_control"] is True
    assert payload["hypothetical_score_preview_produced"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_command_module_is_import_safe_and_exposes_required_functions(capsys):
    importlib.reload(command)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(command.load_annotated_rows_from_path)
    assert callable(command.load_annotator_result_from_path)
    assert callable(command.build_dry_run_payload)
    assert callable(command.main)


def test_annotated_row_loader_loads_json_jsonl_and_csv_shapes(tmp_path):
    row = _annotated_row()
    assert command.load_annotated_rows_from_path(_json(tmp_path / "rows.json", [row])) == [row]
    assert command.load_annotated_rows_from_path(
        _json(tmp_path / "wrapped.json", {"annotated_rows": [row]})
    ) == [row]
    assert command.load_annotated_rows_from_path(
        _json(tmp_path / "items.json", {"items": [row]})
    ) == [row]
    assert command.load_annotated_rows_from_path(
        _jsonl(tmp_path / "rows.jsonl", [row])
    ) == [row]
    csv_rows = command.load_annotated_rows_from_path(
        _csv(tmp_path / "rows.csv", [{"item_id": "csv", "score_impact_review_recommendation": "unmatched"}])
    )
    assert csv_rows == [
        {"item_id": "csv", "score_impact_review_recommendation": "unmatched"}
    ]


def test_annotator_result_loader_loads_supported_shapes(tmp_path):
    row = _annotated_row()
    assert command.load_annotator_result_from_path(
        _json(tmp_path / "result.json", {"annotated_rows": [row]})
    ) == {"annotated_rows": [row]}
    wrapped = {"annotator_result": {"annotated_rows": [row]}}
    assert command.load_annotator_result_from_path(
        _json(tmp_path / "wrapped.json", wrapped)
    ) == wrapped
    assert command.load_annotator_result_from_path(
        _json(tmp_path / "list.json", [row])
    ) == {"annotated_rows": [row]}
    assert command.load_annotator_result_from_path(
        _jsonl(tmp_path / "rows.jsonl", [row])
    ) == {"annotated_rows": [row]}
    assert command.load_annotator_result_from_path(
        _csv(tmp_path / "rows.csv", [{"item_id": "csv", "score_impact_review_recommendation": "unknown"}])
    ) == {"annotated_rows": [{"item_id": "csv", "score_impact_review_recommendation": "unknown"}]}


def test_loaders_raise_deterministic_errors_for_bad_inputs(tmp_path):
    with pytest.raises(command.DryRunLoadError, match="unsupported annotated rows extension"):
        command.load_annotated_rows_from_path(tmp_path / "rows.txt")
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("{", encoding="utf-8")
    with pytest.raises(command.DryRunLoadError, match="invalid JSON"):
        command.load_annotated_rows_from_path(bad_json)
    bad_jsonl = tmp_path / "bad.jsonl"
    bad_jsonl.write_text("[]", encoding="utf-8")
    with pytest.raises(command.DryRunLoadError, match="must be a JSON object"):
        command.load_annotated_rows_from_path(bad_jsonl)
    with pytest.raises(command.DryRunLoadError, match="row 0 must be a JSON object"):
        command.load_annotated_rows_from_path(_json(tmp_path / "bad_rows.json", ["bad"]))
    with pytest.raises(command.DryRunLoadError, match="annotated rows json must"):
        command.load_annotated_rows_from_path(_json(tmp_path / "bad_shape.json", "bad"))
    with pytest.raises(command.DryRunLoadError, match="annotator result json must include"):
        command.load_annotator_result_from_path(_json(tmp_path / "bad_result.json", {"phase": "39A"}))


def test_build_dry_run_payload_calls_builder_and_exposes_review_packet_surfaces():
    rows = [
        _annotated_row(item_id="manual", score_impact_review_recommendation="manual_review"),
        _annotated_row(item_id="positive", score_impact_review_recommendation="positive_review"),
        _annotated_row(
            item_id="negative",
            score_impact_review_recommendation="negative_review",
            score_impact_preview={
                "hypothetical_score_preview": 70,
                "score_preview_delta": -10,
                "score_preview_available": True,
                "score_preview_blocked_reason": "",
                "impact_band": "negative",
                "requires_red_flag_review": True,
            },
        ),
        _annotated_row(item_id="neutral", score_impact_review_recommendation="neutral_review"),
        _annotated_row(item_id="unmatched", score_impact_review_recommendation="unmatched"),
        _annotated_row(item_id="unknown", score_impact_review_recommendation=""),
    ]
    payload = command.build_dry_run_payload(
        annotated_rows=rows,
        review_policy={
            "include_full_annotated_row": True,
            "include_score_impact_preview_result": False,
            "max_missing_reason_items": 3,
        },
    )
    _assert_safe(payload)
    assert payload["annotated_rows_present"] is True
    assert payload["annotator_result_present"] is False
    assert payload["builder_result"]["phase"] == "40A"
    assert len(payload["review_packets"]) == 6
    assert set(payload["review_packets_by_recommendation"]) >= {
        "manual_review",
        "positive_review",
        "negative_review",
        "neutral_review",
        "unmatched",
        "unknown",
    }
    assert payload["manual_review_count"] == 1
    assert payload["positive_review_count"] == 1
    assert payload["negative_review_count"] == 1
    assert payload["neutral_review_count"] == 1
    assert payload["unmatched_count"] == 1
    assert payload["unknown_review_count"] == 1
    assert payload["score_preview_available_count"] == 6
    assert payload["score_preview_blocked_count"] == 0
    assert payload["red_flag_review_count"] == 1
    assert payload["existing_score_fields_detected"][0]["field"] == "final_score"
    assert payload["existing_scores_preserved"] is True
    assert payload["review_packets"][0]["final_score_produced"] is False
    assert payload["review_packets"][0]["existing_score_changed"] is False
    assert "generated_tailoring_text" not in str(payload).lower()
    assert payload["real_tailoring_output_created"] is False
    assert "final_application_score" not in str(payload).lower()


def test_build_dry_run_payload_accepts_annotator_result_when_rows_are_absent():
    payload = command.build_dry_run_payload(
        annotator_result={"annotated_rows": [_annotated_row(item_id="from-result")]}
    )
    _assert_safe(payload)
    assert payload["annotated_rows_present"] is False
    assert payload["annotator_result_present"] is True
    assert payload["review_packets"][0]["item_id"] == "from-result"


def test_main_prints_json_to_stdout_for_valid_input_and_errors_to_stderr(tmp_path, capsys):
    valid = _json(tmp_path / "rows.json", [_annotated_row()])
    assert command.main(["--input", str(valid), "--exclude-score-impact-preview-result"]) == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert payload["phase"] == "40B"
    assert payload["review_packets"][0]["item_id"] == "item-1"
    assert "score_impact_preview_result" not in payload["review_packets"][0]
    assert captured.err == ""

    assert command.main(["--input", str(tmp_path / "missing.json")]) == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "error:" in captured.err
    assert command.main([]) != 0


def test_command_does_not_write_output_files(tmp_path):
    before = {path.name for path in tmp_path.iterdir()}
    valid = _json(tmp_path / "rows.json", [_annotated_row()])
    assert command.main(["--input", str(valid)]) == 0
    after = {path.name for path in tmp_path.iterdir()}
    assert after == before | {"rows.json"}


def test_source_has_no_forbidden_imports_calls_or_writes():
    source = COMMAND_PATH.read_text(encoding="utf-8")
    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source
    for marker in FORBIDDEN_WRITE_MARKERS:
        assert marker not in source
    assert "build_jd_evidence_score_impact_review_packet_builder_default_off" in source


def test_docs_contain_required_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged_by_hash():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_changed_files_are_limited_to_phase40b_and_legacy_guard_tests():
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    allowed = {
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
    }
    unexpected = {
        path
        for path in changed
        if path not in allowed
        and not (path.startswith("tests/test_") and path.endswith(".py"))
    }
    assert unexpected == set()
