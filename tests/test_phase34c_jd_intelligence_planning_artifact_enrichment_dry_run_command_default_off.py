from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess

import pytest

import run_jd_intelligence_planning_artifact_enrichment_dry_run as dry_run


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = ROOT / "run_jd_intelligence_planning_artifact_enrichment_dry_run.py"
DOC_PATH = (
    ROOT
    / "docs/phase34_jd_intelligence_planning_artifact_enrichment_dry_run_command_default_off.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "jd_intelligence_planning_artifact_enrichment_dry_run",
    "dry_run_command_only",
    "llm_capable",
    "llm_enabled",
    "read_only",
    "advisory_only",
    "requires_manual_user_control",
    "planning_row_count",
    "provider_responses_present",
    "enricher_result",
    "grouped_by_next_allowed_step",
    "next_step_counts",
    "extraction_ready_count",
    "extraction_blocked_count",
    "dry_run_summary",
    "dry_run_key",
    "stage_execution_performed",
    "relevance_prefilter_performed",
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
    "stage_execution_performed",
    "relevance_prefilter_performed",
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
    "subprocess.",
    "requests",
    "httpx",
    "urllib",
    "openai",
    "anthropic",
    "run_chat_completion",
    "_run_live_llm_tailoring",
    "run_prefilter(",
    "score_resume_job_match(",
    "execute_application(",
    "submit_application(",
    "provider_call(",
    "network_call(",
)

FORBIDDEN_WRITE_MARKERS = (
    "write_text",
    "write_bytes",
    "mkdir",
    ".save(",
    ".insert(",
    ".update(",
)

DOC_MARKERS = (
    "phase 34c jd intelligence planning artifact enrichment dry-run command default-off",
    "jd intelligence planning artifact enrichment dry-run command",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "llm-capable",
    "default-off",
    "requires explicit `--enable-llm`",
    "reads a supplied planning artifact file",
    "supports json, jsonl, and csv planning-like row inputs",
    "supports supplied provider responses",
    "calls the phase 34b jd intelligence planning artifact enricher",
    "prints grouped next-step routing and jd enrichment json to stdout",
    "does not write output files",
    "does not directly import provider sdks",
    "does not directly call network",
    "does not run relevance prefilter",
    "does not run final application scoring",
    "does not run matching/scoring",
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
    "final scoring remains deterministic and controlled by scoring logic",
    "phase34b-jd-intelligence-planning-artifact-enricher-default-off-v1",
    "phase34a-jd-intelligence-llm-signal-extractor-default-off-v1",
    "phase33e-controlled-agent-router-planning-artifact-dry-run-command-readonly-v1",
    "phase33d-controlled-agent-router-planning-artifact-mapper-readonly-v1",
    "phase33c-controlled-agent-router-batch-handoff-plan-readonly-v1",
    "phase33b-controlled-agent-router-workflow-state-adapter-readonly-v1",
    "phase33a-controlled-agent-router-readonly-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/jd_intelligence_planning_artifact_enricher_default_off.py": "f8e365ab51de647dc6b45ff0c99cce075273eec61e12fc96c744118e1ca68c53",
    "src/agents/jd_intelligence_llm_signal_extractor_default_off.py": "a73124801ce6768aebb934e1c6a7e76d4f9888bbb7b0ca28eb93e882e06f4f6c",
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


def _signals() -> dict:
    return {"required_skills": ["Python"], "confidence": 0.8}


def _assert_safe(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "34C"
    assert payload["default_off"] is True
    assert payload["jd_intelligence_planning_artifact_enrichment_dry_run"] is True
    assert payload["dry_run_command_only"] is True
    assert payload["llm_capable"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["requires_manual_user_control"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_command_module_is_import_safe(capsys):
    importlib.reload(dry_run)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(dry_run.load_planning_rows_from_path)
    assert callable(dry_run.load_provider_responses_from_path)
    assert callable(dry_run.build_dry_run_payload)
    assert callable(dry_run.main)


def test_planning_loader_loads_json_list_and_dictionary(tmp_path):
    list_path = tmp_path / "rows.json"
    list_path.write_text(json.dumps([{"job_id": "j1"}]))
    dict_path = tmp_path / "wrapped.json"
    dict_path.write_text(json.dumps({"planning_rows": [{"job_id": "j2"}]}))
    assert dry_run.load_planning_rows_from_path(list_path) == [{"job_id": "j1"}]
    assert dry_run.load_planning_rows_from_path(dict_path) == [{"job_id": "j2"}]


def test_planning_loader_loads_jsonl_and_csv(tmp_path):
    jsonl_path = tmp_path / "rows.jsonl"
    jsonl_path.write_text('{"job_id":"j1"}\n\n{"job_id":"j2"}\n')
    csv_path = tmp_path / "rows.csv"
    csv_path.write_text("job_id,title\nj3,Engineer\n")
    assert dry_run.load_planning_rows_from_path(jsonl_path) == [
        {"job_id": "j1"},
        {"job_id": "j2"},
    ]
    assert dry_run.load_planning_rows_from_path(csv_path) == [
        {"job_id": "j3", "title": "Engineer"}
    ]


def test_provider_response_loader_loads_json_list_dictionary_and_jsonl(tmp_path):
    list_path = tmp_path / "responses.json"
    list_path.write_text(json.dumps([_signals()]))
    dict_path = tmp_path / "wrapped.json"
    dict_path.write_text(json.dumps({"provider_responses": {"j1": _signals()}}))
    jsonl_path = tmp_path / "responses.jsonl"
    jsonl_path.write_text(json.dumps(_signals()) + "\n")
    assert dry_run.load_provider_responses_from_path(list_path) == [_signals()]
    assert dry_run.load_provider_responses_from_path(dict_path) == {"j1": _signals()}
    assert dry_run.load_provider_responses_from_path(jsonl_path) == [_signals()]


def test_loader_errors_are_deterministic(tmp_path):
    unsupported = tmp_path / "rows.txt"
    unsupported.write_text("x")
    with pytest.raises(dry_run.DryRunLoadError, match="unsupported"):
        dry_run.load_planning_rows_from_path(unsupported)

    invalid_json = tmp_path / "bad.json"
    invalid_json.write_text("{bad")
    with pytest.raises(dry_run.DryRunLoadError, match="invalid JSON"):
        dry_run.load_planning_rows_from_path(invalid_json)

    invalid_jsonl = tmp_path / "bad.jsonl"
    invalid_jsonl.write_text("{bad\n")
    with pytest.raises(dry_run.DryRunLoadError, match="invalid JSONL"):
        dry_run.load_planning_rows_from_path(invalid_jsonl)

    wrong_shape = tmp_path / "wrong.json"
    wrong_shape.write_text(json.dumps({"not_rows": []}))
    with pytest.raises(dry_run.DryRunLoadError, match="planning_rows"):
        dry_run.load_planning_rows_from_path(wrong_shape)

    invalid_provider = tmp_path / "provider.json"
    invalid_provider.write_text(json.dumps("bad"))
    with pytest.raises(dry_run.DryRunLoadError, match="provider responses json"):
        dry_run.load_provider_responses_from_path(invalid_provider)


def test_build_dry_run_payload_calls_phase34b_enricher(monkeypatch):
    calls = []

    def fake_enricher(**kwargs):
        calls.append(kwargs)
        return {
            "grouped_by_next_allowed_step": {"run_final_application_scoring": []},
            "next_step_counts": {"run_final_application_scoring": 1},
            "extraction_ready_count": 1,
            "extraction_blocked_count": 0,
        }

    monkeypatch.setattr(
        dry_run,
        "build_jd_intelligence_planning_artifact_enricher_default_off",
        fake_enricher,
    )
    payload = dry_run.build_dry_run_payload(
        planning_rows=[{"job_id": "j1"}],
        enable_llm=True,
        provider_responses={"j1": _signals()},
        extraction_policy={"max_items": 4},
        router_policy={"final_score_threshold": 70},
    )
    _assert_safe(payload)
    assert calls == [
        {
            "planning_rows": [{"job_id": "j1"}],
            "enable_llm": True,
            "provider_responses": {"j1": _signals()},
            "extraction_policy": {"max_items": 4},
            "router_policy": {"final_score_threshold": 70},
        }
    ]
    assert payload["grouped_by_next_allowed_step"] == {
        "run_final_application_scoring": []
    }
    assert payload["next_step_counts"] == {"run_final_application_scoring": 1}
    assert payload["extraction_ready_count"] == 1
    assert payload["extraction_blocked_count"] == 0


def test_default_off_and_provider_responses_passed_when_enabled():
    off = dry_run.build_dry_run_payload(
        planning_rows=[{"job_id": "j1", "job_description": "Python"}]
    )
    _assert_safe(off)
    assert off["llm_enabled"] is False
    assert off["extraction_ready_count"] == 0

    enabled = dry_run.build_dry_run_payload(
        planning_rows=[{"job_id": "j1", "job_description": "Python", "relevant": True}],
        enable_llm=True,
        provider_responses={"j1": _signals()},
    )
    _assert_safe(enabled)
    assert enabled["llm_enabled"] is True
    assert enabled["provider_responses_present"] is True
    assert enabled["extraction_ready_count"] == 1


def test_main_prints_json_to_stdout_for_valid_input(tmp_path, capsys):
    rows = tmp_path / "rows.json"
    rows.write_text(json.dumps([{"job_id": "j1", "job_description": "Python"}]))
    responses = tmp_path / "responses.json"
    responses.write_text(json.dumps({"j1": _signals()}))
    before = {item.name for item in tmp_path.iterdir()}

    result = dry_run.main(
        [
            "--input",
            str(rows),
            "--enable-llm",
            "--provider-responses",
            str(responses),
            "--score-threshold",
            "72",
        ]
    )
    after = {item.name for item in tmp_path.iterdir()}
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    _assert_safe(payload)
    assert payload["planning_row_count"] == 1
    assert before == after


def test_main_returns_nonzero_for_missing_or_invalid_input(tmp_path, capsys):
    missing = dry_run.main([])
    captured = capsys.readouterr()
    assert missing != 0
    assert "--input is required" in captured.err
    assert captured.out == ""

    bad = tmp_path / "bad.txt"
    bad.write_text("x")
    invalid = dry_run.main(["--input", str(bad)])
    captured = capsys.readouterr()
    assert invalid != 0
    assert "unsupported" in captured.err
    assert captured.out == ""


def test_payload_excludes_tailoring_output_and_all_action_flags_false():
    payload = dry_run.build_dry_run_payload(
        planning_rows=[{"job_id": "j1", "job_description": "Python", "relevant": True}],
        enable_llm=True,
        provider_responses={
            "j1": {
                **_signals(),
                "generated_tailoring_text": "do not surface",
                "real_tailoring_output": "do not surface",
            }
        },
    )
    rendered = json.dumps(payload).lower()
    assert "do not surface" not in rendered
    _assert_safe(payload)


def test_source_has_no_forbidden_imports_calls_or_writes():
    source = COMMAND_PATH.read_text(encoding="utf-8")
    assert "build_jd_intelligence_planning_artifact_enricher_default_off" in source
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


def test_changed_files_are_limited_to_phase34c_surface_and_legacy_guards():
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    allowed = {
        "run_jd_intelligence_planning_artifact_enrichment_dry_run.py",
        "docs/phase34_jd_intelligence_planning_artifact_enrichment_dry_run_command_default_off.md",
        "tests/test_phase34c_jd_intelligence_planning_artifact_enrichment_dry_run_command_default_off.py",
        "src/agents/jd_signal_resume_evidence_matrix_default_off.py",
        "docs/phase35_jd_signal_resume_evidence_matrix_default_off.md",
        "tests/test_phase35a_jd_signal_resume_evidence_matrix_default_off.py",
        "src/agents/jd_signal_planning_artifact_evidence_enricher_default_off.py",
        "docs/phase35_jd_signal_planning_artifact_evidence_enricher_default_off.md",
        "tests/test_phase35b_jd_signal_planning_artifact_evidence_enricher_default_off.py",
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
