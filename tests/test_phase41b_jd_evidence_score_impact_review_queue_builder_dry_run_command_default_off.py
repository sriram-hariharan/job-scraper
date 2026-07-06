# phase56b legacy guard marker: changes_only e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 e30180b352ebe8abca2ec34b4b34983fbaee61a32bdc0d511001c406703e392c
from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess
import sys

import pytest

import run_jd_evidence_score_impact_review_queue_builder_dry_run as command


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = ROOT / "run_jd_evidence_score_impact_review_queue_builder_dry_run.py"
DOC_PATH = (
    ROOT
    / "docs/phase41_jd_evidence_score_impact_review_queue_builder_dry_run_command_default_off.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "jd_evidence_score_impact_review_queue_builder_dry_run",
    "dry_run_command_only",
    "read_only",
    "advisory_only",
    "preview_only",
    "deterministic_review_queue_building",
    "manual_review_queue_only",
    "requires_manual_user_control",
    "review_packets_present",
    "builder_result_present",
    "queue_policy",
    "queue_result",
    "review_queue",
    "review_queue_by_priority",
    "review_queue_summary",
    "urgent_review_count",
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
    "review_packet_building_performed",
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
    "auto_" + "apply_performed",
    "auto_submit_performed",
}

FALSE_ACTION_KEYS = {
    "review_packet_building_performed",
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
    "build_jd_evidence_score_impact_review_packet_builder_default_off(",
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
    "phase 41b jd evidence score impact review queue builder dry-run command default-off",
    "jd evidence score impact review queue builder dry-run command",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "deterministic review queue building",
    "reads a supplied review packet file",
    "reads a supplied builder result file",
    "supports json, jsonl, and csv review packet inputs",
    "supports supplied builder results",
    "calling the phase 41a jd evidence score impact review queue builder",
    "prints prioritized operator review queue json to stdout",
    "does not write output files",
    "builds prioritized operator review queues from score impact review packets",
    "prioritizes red flag and blocked score preview rows",
    "preserves deterministic order for equal priorities",
    "manual-review queue only",
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
    "does not run review packet building",
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
    "review queue building remains separate from final scoring",
    'python run_jd_evidence_score_impact_review_queue_builder_dry_run.py --input path/to/review_packets.json',
    "phase41a-jd-evidence-score-impact-review-queue-builder-default-off-v1",
    "phase40-jd-evidence-score-impact-review-packet-builder-release-v1",
    "phase40b-jd-evidence-score-impact-review-packet-builder-dry-run-command-default-off-v1",
    "phase40a-jd-evidence-score-impact-review-packet-builder-default-off-v1",
    "phase39-jd-evidence-score-impact-planning-artifact-annotator-release-v1",
    "phase39b-jd-evidence-score-impact-planning-artifact-annotator-dry-run-command-default-off-v1",
    "phase38-jd-evidence-score-impact-preview-release-v1",
    "phase37-jd-evidence-scoring-contribution-preview-release-v1",
    "phase36-jd-evidence-final-scoring-feature-adapter-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/jd_evidence_score_impact_review_queue_builder_default_off.py": "c3080e881850ec75472e1e57727829db2866236139a84cc29a3ecd2ebe7ef6df",
    "src/agents/jd_evidence_score_impact_review_packet_builder_default_off.py": "daa472f00511e16d37975472dcf06fcd7ffcd3f353509d8524e949baae137f68",
    "run_jd_evidence_score_impact_review_packet_builder_dry_run.py": "87c9a0356e8e9d633062c0adcf387baebb721c6dd6331047f5190f1413de4dd8",
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


def _packet(**overrides):
    packet = {
        "item_id": "job-1",
        "title": "Data Scientist",
        "company": "Example",
        "score_impact_review_recommendation": "manual_review",
        "score_preview_available": True,
        "score_preview_delta": 0.12,
        "existing_score_present": True,
        "existing_score_field": "resolved_score",
        "existing_score_value": 0.76,
    }
    packet.update(overrides)
    return packet


def test_import_safe_and_exposes_required_functions():
    module = importlib.reload(command)
    assert callable(module.load_review_packets_from_path)
    assert callable(module.load_builder_result_from_path)
    assert callable(module.build_dry_run_payload)
    assert callable(module.main)


@pytest.mark.parametrize(
    "filename,payload",
    [
        ("packets.json", [_packet()]),
        ("packets_wrapped.json", {"review_packets": [_packet(item_id="job-2")]}),
        ("rows_wrapped.json", {"rows": [_packet(item_id="job-3")]}),
        ("items_wrapped.json", {"items": [_packet(item_id="job-4")]}),
        ("queue_wrapped.json", {"review_queue": [_packet(item_id="job-5")]}),
    ],
)
def test_load_review_packets_from_json_shapes(tmp_path, filename, payload):
    path = _json(tmp_path / filename, payload)
    rows = command.load_review_packets_from_path(path)
    assert len(rows) == 1
    assert isinstance(rows[0], dict)


def test_load_review_packets_from_jsonl_and_csv(tmp_path):
    rows = [_packet(item_id="job-1"), _packet(item_id="job-2")]
    assert len(command.load_review_packets_from_path(_jsonl(tmp_path / "x.jsonl", rows))) == 2
    assert len(command.load_review_packets_from_path(_csv(tmp_path / "x.csv", rows))) == 2


@pytest.mark.parametrize(
    "filename,payload",
    [
        ("builder.json", {"builder_result": {"review_packets": [_packet()]}}),
        ("packets.json", {"review_packets": [_packet(item_id="job-2")]}),
        ("rows.json", {"rows": [_packet(item_id="job-3")]}),
        ("items.json", {"items": [_packet(item_id="job-4")]}),
        ("list.json", [_packet(item_id="job-5")]),
    ],
)
def test_load_builder_result_from_json_shapes(tmp_path, filename, payload):
    path = _json(tmp_path / filename, payload)
    result = command.load_builder_result_from_path(path)
    assert isinstance(result, dict)
    assert "builder_result" in result or "review_packets" in result


def test_load_builder_result_from_jsonl_and_csv(tmp_path):
    rows = [_packet(item_id="job-1"), _packet(item_id="job-2")]
    assert "review_packets" in command.load_builder_result_from_path(
        _jsonl(tmp_path / "builder.jsonl", rows)
    )
    assert "review_packets" in command.load_builder_result_from_path(
        _csv(tmp_path / "builder.csv", rows)
    )


@pytest.mark.parametrize(
    "filename,writer,error",
    [
        ("packets.txt", lambda path: path.write_text("[]", encoding="utf-8"), "unsupported"),
        ("packets.json", lambda path: path.write_text("{", encoding="utf-8"), "invalid JSON"),
        ("packets.jsonl", lambda path: path.write_text("{", encoding="utf-8"), "invalid JSONL"),
        ("packets.json", lambda path: path.write_text(json.dumps({"review_packets": ["bad"]}), encoding="utf-8"), "row 0"),
    ],
)
def test_review_packet_loader_errors_are_deterministic(tmp_path, filename, writer, error):
    path = tmp_path / filename
    writer(path)
    with pytest.raises(command.DryRunLoadError, match=error):
        command.load_review_packets_from_path(path)


@pytest.mark.parametrize(
    "filename,writer,error",
    [
        ("builder.txt", lambda path: path.write_text("[]", encoding="utf-8"), "unsupported"),
        ("builder.json", lambda path: path.write_text("{", encoding="utf-8"), "invalid JSON"),
        ("builder.jsonl", lambda path: path.write_text("[1]", encoding="utf-8"), "line 1"),
        ("builder.json", lambda path: path.write_text(json.dumps({"not_rows": []}), encoding="utf-8"), "must include"),
    ],
)
def test_builder_result_loader_errors_are_deterministic(tmp_path, filename, writer, error):
    path = tmp_path / filename
    writer(path)
    with pytest.raises(command.DryRunLoadError, match=error):
        command.load_builder_result_from_path(path)


def test_build_dry_run_payload_exposes_queue_surfaces_and_false_actions():
    payload = command.build_dry_run_payload(
        review_packets=[
            _packet(item_id="red", requires_red_flag_review=True),
            _packet(item_id="blocked", score_preview_available=False),
            _packet(item_id="positive", score_impact_review_recommendation="positive_review"),
        ],
        queue_policy={"max_queue_items": 2},
    )

    assert REQUIRED_KEYS.issubset(payload)
    assert payload["phase"] == "41B"
    assert payload["default_off"] is True
    assert payload["review_packets_present"] is True
    assert payload["builder_result_present"] is False
    assert payload["queue_policy"]["max_queue_items"] == 2
    assert len(payload["review_queue"]) == 2
    assert payload["review_queue"][0]["item_id"] == "red"
    assert payload["urgent_review_count"] == 2
    assert payload["red_flag_review_count"] == 1
    assert payload["score_preview_blocked_count"] == 1
    assert payload["existing_score_fields_detected"]
    assert payload["existing_scores_preserved"] is True
    assert payload["hypothetical_score_preview_produced"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False
    assert payload["queue_result"]["jd_evidence_score_impact_review_queue_builder"] is True


def test_build_dry_run_payload_uses_builder_result_when_packets_absent():
    payload = command.build_dry_run_payload(
        builder_result={"review_packets": [_packet(item_id="from-builder")]},
    )

    assert payload["review_packets_present"] is False
    assert payload["builder_result_present"] is True
    assert payload["review_queue"][0]["item_id"] == "from-builder"


def test_cli_prints_json_to_stdout_and_respects_policy(tmp_path, capsys):
    path = _json(tmp_path / "packets.json", [_packet(item_id="first"), _packet(item_id="second")])

    code = command.main(
        [
            "--input",
            str(path),
            "--preserve-input-order-within-priority",
            "--max-queue-items",
            "1",
        ]
    )

    captured = capsys.readouterr()
    assert captured.err == ""
    assert code == 0
    payload = json.loads(captured.out)
    assert payload["queue_policy"]["sort_by_absolute_delta_within_priority"] is False
    assert payload["queue_policy"]["max_queue_items"] == 1
    assert len(payload["review_queue"]) == 1


def test_cli_returns_nonzero_for_invalid_or_missing_inputs(tmp_path, capsys):
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


def test_command_does_not_create_output_files(tmp_path):
    path = _json(tmp_path / "packets.json", [_packet()])
    before = sorted(item.name for item in tmp_path.iterdir())

    assert command.main(["--input", str(path)]) == 0

    after = sorted(item.name for item in tmp_path.iterdir())
    assert after == before


def test_source_has_only_allowed_imports_and_no_write_or_runtime_markers():
    source = COMMAND_PATH.read_text(encoding="utf-8")
    assert (
        "from src.agents.jd_evidence_score_impact_review_queue_builder_default_off import"
        in source
    )
    assert "build_jd_evidence_score_impact_review_queue_builder_default_off(" in source
    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source
    for marker in FORBIDDEN_WRITE_MARKERS:
        assert marker not in source


def test_docs_include_required_phase41b_markers():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_backend_and_runtime_hashes_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected, relative


def test_subprocess_cli_outputs_valid_json(tmp_path):
    path = _json(tmp_path / "packets.json", [_packet()])

    result = subprocess.run(
        [
            sys.executable,
            str(COMMAND_PATH),
            "--input",
            str(path),
        ],
        check=True,
        capture_output=True,
        text=True,
        cwd=ROOT,
    )

    payload = json.loads(result.stdout)
    assert result.stderr == ""
    assert payload["phase"] == "41B"
    assert payload["review_queue"]
