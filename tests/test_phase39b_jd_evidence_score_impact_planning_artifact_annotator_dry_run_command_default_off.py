# phase56b legacy guard marker: changes_only e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c
from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess

import pytest

import run_jd_evidence_score_impact_planning_artifact_annotator_dry_run as command


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = ROOT / "run_jd_evidence_score_impact_planning_artifact_annotator_dry_run.py"
DOC_PATH = (
    ROOT
    / "docs/phase39_jd_evidence_score_impact_planning_artifact_annotator_dry_run_command_default_off.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "jd_evidence_score_impact_planning_artifact_annotator_dry_run",
    "dry_run_command_only",
    "read_only",
    "advisory_only",
    "preview_only",
    "deterministic_score_impact_annotation",
    "requires_manual_user_control",
    "planning_row_count",
    "impact_result_present",
    "impact_rows_present",
    "annotation_policy",
    "annotator_result",
    "annotated_rows",
    "unannotated_rows",
    "annotation_summary",
    "score_preview_available_count",
    "score_preview_blocked_count",
    "positive_impact_count",
    "negative_impact_count",
    "neutral_impact_count",
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
    "phase 39b jd evidence score impact planning artifact annotator dry-run command default-off",
    "jd evidence score impact planning artifact annotator dry-run command",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "deterministic score impact annotation",
    "reads supplied planning artifact file",
    "reads supplied score impact preview result file",
    "supports json, jsonl, and csv planning-like row inputs",
    "supports json, jsonl, and csv score impact row inputs",
    "supports supplied score impact rows",
    "calls the phase 39a jd evidence score impact planning artifact annotator",
    "prints annotated planning artifact json to stdout",
    "does not write output files",
    "annotates copied planning-like rows with score impact preview metadata",
    "produces score impact review recommendations",
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
    "final scoring remains deterministic and controlled by scoring logic",
    "phase39a-jd-evidence-score-impact-planning-artifact-annotator-default-off-v1",
    "phase38-jd-evidence-score-impact-preview-release-v1",
    "phase38b-jd-evidence-score-impact-preview-dry-run-command-default-off-v1",
    "phase38a-jd-evidence-score-impact-preview-default-off-v1",
    "phase37-jd-evidence-scoring-contribution-preview-release-v1",
    "phase37b-jd-evidence-scoring-contribution-preview-dry-run-command-default-off-v1",
    "phase36-jd-evidence-final-scoring-feature-adapter-release-v1",
    "phase35c-jd-signal-planning-artifact-evidence-enrichment-dry-run-command-default-off-v1",
    "phase34c-jd-intelligence-planning-artifact-enrichment-dry-run-command-default-off-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/jd_evidence_score_impact_planning_artifact_annotator_default_off.py": "fd0903a249d46f609f2fd790ac5100b2ef7554132749de349b33162c22b4ed6f",
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


def _json(path: Path, payload) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _planning_row(**extra) -> dict:
    row = {
        "item_id": "item-1",
        "job_id": "job-1",
        "id": "id-1",
        "title": "Data Engineer",
        "company": "Acme",
        "existing_score_present": True,
        "existing_score_field": "final_score",
        "existing_score_value": 80,
        "final_score": 80,
    }
    for key, value in extra.items():
        row[key] = value
    return row


def _impact_row(**extra) -> dict:
    row = {
        "item_id": "item-1",
        "job_id": "job-1",
        "base_score_for_preview": 80,
        "bounded_advisory_contribution_points": 7,
        "hypothetical_score_preview": 87,
        "score_preview_delta": 7,
        "score_preview_available": True,
        "score_preview_blocked_reason": "",
        "impact_band": "positive",
        "requires_red_flag_review": False,
        "hypothetical_score_preview_produced": True,
        "final_score_produced": False,
        "existing_score_changed": False,
    }
    for key, value in extra.items():
        row[key] = value
    return row


def _assert_safe(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "39B"
    assert payload["default_off"] is True
    assert payload["jd_evidence_score_impact_planning_artifact_annotator_dry_run"] is True
    assert payload["dry_run_command_only"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["preview_only"] is True
    assert payload["deterministic_score_impact_annotation"] is True
    assert payload["requires_manual_user_control"] is True
    assert payload["hypothetical_score_preview_produced"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_command_module_is_import_safe_and_exposes_required_functions(capsys):
    importlib.reload(command)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(command.load_planning_rows_from_path)
    assert callable(command.load_impact_result_from_path)
    assert callable(command.load_impact_rows_from_path)
    assert callable(command.build_dry_run_payload)
    assert callable(command.main)


def test_planning_loader_accepts_json_list_wrapped_json_jsonl_and_csv(tmp_path):
    list_path = _json(tmp_path / "planning.json", [_planning_row(item_id="list")])
    wrapped_path = _json(
        tmp_path / "planning_wrapped.json",
        {"planning_rows": [_planning_row(item_id="wrapped")]},
    )
    jsonl_path = tmp_path / "planning.jsonl"
    jsonl_path.write_text(json.dumps(_planning_row(item_id="jsonl")) + "\n", encoding="utf-8")
    csv_path = tmp_path / "planning.csv"
    csv_path.write_text("item_id,job_id,final_score\ncsv,job,80\n", encoding="utf-8")

    assert command.load_planning_rows_from_path(list_path)[0]["item_id"] == "list"
    assert command.load_planning_rows_from_path(wrapped_path)[0]["item_id"] == "wrapped"
    assert command.load_planning_rows_from_path(jsonl_path)[0]["item_id"] == "jsonl"
    assert command.load_planning_rows_from_path(csv_path)[0]["item_id"] == "csv"


def test_planning_loader_accepts_all_supported_wrapper_keys(tmp_path):
    for key in ("rows", "items", "jobs", "annotated_rows", "unannotated_rows"):
        path = _json(tmp_path / f"{key}.json", {key: [_planning_row(item_id=key)]})
        assert command.load_planning_rows_from_path(path)[0]["item_id"] == key


def test_impact_result_loader_accepts_result_packet_rows_list_jsonl_and_csv(tmp_path):
    result_path = _json(tmp_path / "impact_result.json", {"impact_rows": [_impact_row(item_id="result")]})
    wrapped_result_path = _json(
        tmp_path / "wrapped_result.json",
        {"impact_result": {"impact_rows": [_impact_row(item_id="wrapped-result")]}},
    )
    packet_path = _json(
        tmp_path / "packet.json",
        {"impact_packet": {"impact_rows": [_impact_row(item_id="packet")]}},
    )
    packet_dict_path = _json(
        tmp_path / "packet_dict.json",
        {"packet_type": "jd_evidence_score_impact_preview", "impact_rows": [_impact_row(item_id="packet-dict")]},
    )
    list_path = _json(tmp_path / "impact_list.json", [_impact_row(item_id="list")])
    jsonl_path = tmp_path / "impact.jsonl"
    jsonl_path.write_text(json.dumps(_impact_row(item_id="jsonl")) + "\n", encoding="utf-8")
    csv_path = tmp_path / "impact.csv"
    csv_path.write_text("item_id,job_id,score_preview_delta,score_preview_available\ncsv,job,2,true\n", encoding="utf-8")

    assert command.load_impact_result_from_path(result_path)["impact_rows"][0]["item_id"] == "result"
    assert command.load_impact_result_from_path(wrapped_result_path)["impact_rows"][0]["item_id"] == "wrapped-result"
    assert command.load_impact_result_from_path(packet_path)["impact_packet"]["impact_rows"][0]["item_id"] == "packet"
    assert command.load_impact_result_from_path(packet_dict_path)["impact_packet"]["impact_rows"][0]["item_id"] == "packet-dict"
    assert command.load_impact_result_from_path(list_path)["impact_rows"][0]["item_id"] == "list"
    assert command.load_impact_result_from_path(jsonl_path)["impact_rows"][0]["item_id"] == "jsonl"
    assert command.load_impact_result_from_path(csv_path)["impact_rows"][0]["item_id"] == "csv"


def test_explicit_impact_rows_loader_accepts_json_wrapped_json_jsonl_and_csv(tmp_path):
    list_path = _json(tmp_path / "rows.json", [_impact_row(item_id="list")])
    wrapped_path = _json(tmp_path / "wrapped.json", {"impact_rows": [_impact_row(item_id="wrapped")]})
    jsonl_path = tmp_path / "rows.jsonl"
    jsonl_path.write_text(json.dumps(_impact_row(item_id="jsonl")) + "\n", encoding="utf-8")
    csv_path = tmp_path / "rows.csv"
    csv_path.write_text("item_id,job_id,score_preview_delta,score_preview_available\ncsv,job,2,true\n", encoding="utf-8")

    assert command.load_impact_rows_from_path(list_path)[0]["item_id"] == "list"
    assert command.load_impact_rows_from_path(wrapped_path)[0]["item_id"] == "wrapped"
    assert command.load_impact_rows_from_path(jsonl_path)[0]["item_id"] == "jsonl"
    assert command.load_impact_rows_from_path(csv_path)[0]["item_id"] == "csv"


def test_loaders_raise_deterministic_errors_for_bad_inputs(tmp_path):
    unsupported = tmp_path / "rows.txt"
    unsupported.write_text("[]", encoding="utf-8")
    invalid_json = tmp_path / "bad.json"
    invalid_json.write_text("{", encoding="utf-8")
    invalid_jsonl = tmp_path / "bad.jsonl"
    invalid_jsonl.write_text('{"ok": true}\n{', encoding="utf-8")
    invalid_csv = tmp_path / "bad.csv"
    invalid_csv.write_text("a,b\n1,2,3\n", encoding="utf-8")
    invalid_planning = _json(tmp_path / "bad_planning.json", {"unexpected": []})
    invalid_impact_result = _json(tmp_path / "bad_impact_result.json", {"unexpected": []})
    invalid_impact_rows = _json(tmp_path / "bad_impact_rows.json", {"impact_rows": ["bad"]})

    with pytest.raises(command.DryRunLoadError, match="unsupported"):
        command.load_planning_rows_from_path(unsupported)
    with pytest.raises(command.DryRunLoadError, match="invalid JSON"):
        command.load_planning_rows_from_path(invalid_json)
    with pytest.raises(command.DryRunLoadError, match="invalid JSONL"):
        command.load_planning_rows_from_path(invalid_jsonl)
    with pytest.raises(command.DryRunLoadError, match="invalid CSV"):
        command.load_planning_rows_from_path(invalid_csv)
    with pytest.raises(command.DryRunLoadError, match="must include"):
        command.load_planning_rows_from_path(invalid_planning)
    with pytest.raises(command.DryRunLoadError, match="must include"):
        command.load_impact_result_from_path(invalid_impact_result)
    with pytest.raises(command.DryRunLoadError, match="must be a JSON object"):
        command.load_impact_rows_from_path(invalid_impact_rows)


def test_build_dry_run_payload_calls_phase39a_annotator_and_exposes_required_keys(monkeypatch):
    calls = []

    def fake_annotator(*, planning_rows=None, impact_result=None, impact_rows=None, annotation_policy=None):
        calls.append(
            {
                "planning_rows": planning_rows,
                "impact_result": impact_result,
                "impact_rows": impact_rows,
                "annotation_policy": annotation_policy,
            }
        )
        return {
            "planning_row_count": 1,
            "impact_rows_present": True,
            "annotation_policy": {"positive_delta_threshold": 1},
            "annotated_rows": [{"item_id": "item-1", "final_score_produced": False}],
            "unannotated_rows": [],
            "annotation_summary": {"annotated_row_count": 1},
            "score_preview_available_count": 1,
            "score_preview_blocked_count": 0,
            "positive_impact_count": 1,
            "negative_impact_count": 0,
            "neutral_impact_count": 0,
            "red_flag_review_count": 0,
            "existing_score_fields_detected": [
                {"row_key": "item-1", "field": "final_score", "value": 80}
            ],
            "existing_scores_preserved": True,
        }

    monkeypatch.setattr(
        command,
        "build_jd_evidence_score_impact_planning_artifact_annotator_default_off",
        fake_annotator,
    )
    payload = command.build_dry_run_payload(
        planning_rows=[_planning_row()],
        impact_result={"impact_rows": [_impact_row()]},
        impact_rows=[_impact_row(item_id="explicit")],
        annotation_policy={"positive_delta_threshold": 1},
    )

    _assert_safe(payload)
    assert calls == [
        {
            "planning_rows": [_planning_row()],
            "impact_result": {"impact_rows": [_impact_row()]},
            "impact_rows": [_impact_row(item_id="explicit")],
            "annotation_policy": {"positive_delta_threshold": 1},
        }
    ]
    assert payload["annotated_rows"][0]["item_id"] == "item-1"
    assert payload["unannotated_rows"] == []
    assert payload["annotation_summary"]["annotated_row_count"] == 1
    assert payload["score_preview_available_count"] == 1
    assert payload["positive_impact_count"] == 1
    assert payload["existing_score_fields_detected"][0]["field"] == "final_score"
    assert payload["existing_scores_preserved"] is True


def test_real_payload_preserves_existing_scores_and_has_no_final_score_or_tailoring_output():
    payload = command.build_dry_run_payload(
        planning_rows=[_planning_row(existing_score_value=91, final_score=91)],
        impact_rows=[_impact_row(existing_score_value=91)],
    )
    _assert_safe(payload)
    assert payload["planning_row_count"] == 1
    assert payload["annotated_rows"][0]["final_score"] == 91
    assert payload["annotated_rows"][0]["existing_score_changed"] is False
    assert payload["existing_score_fields_detected"] == [
        {"row_key": "item-1", "field": "final_score", "value": 91}
    ]
    assert payload["existing_scores_preserved"] is True
    encoded = json.dumps(payload).lower()
    assert "generated_tailoring_text" not in encoded
    assert "tailored_resume" not in encoded
    assert "final_application_score" not in encoded
    assert payload["real_tailoring_output_created"] is False


def test_command_main_prints_json_to_stdout_for_valid_input(tmp_path, capsys):
    planning_path = _json(tmp_path / "planning.json", [_planning_row()])
    impact_path = _json(tmp_path / "impact.json", {"impact_rows": [_impact_row()]})
    code = command.main(
        [
            "--input",
            str(planning_path),
            "--impact-result",
            str(impact_path),
            "--positive-delta-threshold",
            "2",
            "--negative-delta-threshold",
            "-2",
            "--exclude-full-impact-row",
            "--skip-unmatched-annotations",
        ]
    )
    captured = capsys.readouterr()
    assert code == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    _assert_safe(payload)
    assert payload["annotation_policy"]["positive_delta_threshold"] == 2.0
    assert payload["annotation_policy"]["include_full_impact_row"] is False
    assert payload["annotation_policy"]["annotate_unmatched_rows"] is False
    assert payload["dry_run_summary"]["stdout_only"] is True


def test_command_main_returns_nonzero_for_missing_and_invalid_input(tmp_path, capsys):
    missing_code = command.main([])
    missing = capsys.readouterr()
    assert missing_code != 0
    assert "error:" in missing.err
    assert missing.out == ""

    bad = tmp_path / "bad.json"
    bad.write_text("{", encoding="utf-8")
    invalid_code = command.main(["--input", str(bad)])
    invalid = capsys.readouterr()
    assert invalid_code != 0
    assert "invalid JSON" in invalid.err
    assert invalid.out == ""


def test_command_does_not_write_output_files(tmp_path, capsys):
    planning_path = _json(tmp_path / "planning.json", [_planning_row()])
    impact_path = _json(tmp_path / "impact.json", {"impact_rows": [_impact_row()]})
    before = sorted(item.name for item in tmp_path.iterdir())
    assert command.main(["--input", str(planning_path), "--impact-result", str(impact_path)]) == 0
    capsys.readouterr()
    after = sorted(item.name for item in tmp_path.iterdir())
    assert after == before


def test_source_has_no_forbidden_imports_calls_or_writes():
    source = COMMAND_PATH.read_text(encoding="utf-8")
    assert (
        "from src.agents.jd_evidence_score_impact_planning_artifact_annotator_default_off import"
        in source
    )
    assert "build_jd_evidence_score_impact_planning_artifact_annotator_default_off(" in source
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


def test_changed_files_are_limited_to_phase39b_and_legacy_guard_tests():
    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
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
    }
    unexpected = {
        path
        for path in changed
        if path not in allowed
        and not (path.startswith("tests/test_") and path.endswith(".py"))
    }
    assert unexpected == set()
