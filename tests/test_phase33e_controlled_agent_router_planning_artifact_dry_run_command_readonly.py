from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess

import pytest

import run_controlled_agent_router_planning_artifact_dry_run as dry_run


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = ROOT / "run_controlled_agent_router_planning_artifact_dry_run.py"
DOC_PATH = (
    ROOT
    / "docs/phase33_controlled_agent_router_planning_artifact_dry_run_command_readonly.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "read_only",
    "advisory_only",
    "dry_run_command_only",
    "planning_artifact_dry_run",
    "allowlisted_routing_only",
    "requires_manual_user_control",
    "planning_row_count",
    "mapper_result",
    "grouped_by_next_allowed_step",
    "next_step_counts",
    "dry_run_summary",
    "dry_run_key",
    "no_llm_calls",
    "llm_call_performed",
    "no_provider_calls",
    "provider_call_performed",
    "no_network_calls",
    "network_call_performed",
    "dispatch_performed",
    "stage_execution_performed",
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

TRUE_KEYS = {
    "default_off",
    "read_only",
    "advisory_only",
    "dry_run_command_only",
    "planning_artifact_dry_run",
    "allowlisted_routing_only",
    "requires_manual_user_control",
    "no_llm_calls",
    "no_provider_calls",
    "no_network_calls",
}

FALSE_KEYS = {
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "dispatch_performed",
    "stage_execution_performed",
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

FORBIDDEN_IMPORT_MARKERS = (
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
    "from src.rag",
    "import src.rag",
    "requests",
    "httpx",
    "openai",
    "anthropic",
    "psycopg",
    "sqlite",
    "subprocess.",
    "run_prefilter(",
    "score_resume_job_match(",
    "run_chat_completion",
    "_run_live_llm_tailoring",
    "provider_call(",
    "network_call(",
    "execute_application(",
    "submit_application(",
)

DOC_MARKERS = (
    "phase 33e controlled agent router planning artifact dry-run command read-only",
    "controlled agent router planning artifact dry-run command",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "reads a supplied planning artifact file",
    "supports json, jsonl, and csv planning-like row inputs",
    "calls the phase 33d planning artifact mapper",
    "prints grouped next-step router handoff json to stdout",
    "does not write output files",
    "does not run relevance prefilter",
    "does not run jd intelligence",
    "does not run final application scoring",
    "does not run tailoring opportunity check",
    "does not run manual generate ai tailoring preview preparation",
    "does not call llm",
    "does not call providers",
    "does not call network",
    "does not dispatch",
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
    "tailoring agent remains separate from final scoring",
    "final scoring remains deterministic and controlled by scoring logic",
    "llm calls are not introduced in this phase",
    "persistence is not introduced in this phase",
    "phase33d-controlled-agent-router-planning-artifact-mapper-readonly-v1",
    "phase33c-controlled-agent-router-batch-handoff-plan-readonly-v1",
    "phase33b-controlled-agent-router-workflow-state-adapter-readonly-v1",
    "phase33a-controlled-agent-router-readonly-v1",
    "phase32b-manual-generate-ai-tailoring-preview-normalized-response-preview-packet-api-readback-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/controlled_agent_router_readonly.py": "c1cac3d8d1858b5143d0c3ca0082f3b908410020a0e4220c1dea9531cbf3655d",
    "src/agents/controlled_agent_router_workflow_state_adapter_readonly.py": "4f01b4e58c8e517ec633331da44341ee5596d486ae7d40d38fdca4666d6fa47e",
    "src/agents/controlled_agent_router_batch_handoff_plan_readonly.py": "7824233cbb4c6efd75481a8097a041488adfbd53f7c97e4832c02b8822741834",
    "src/agents/controlled_agent_router_planning_artifact_mapper_readonly.py": "1966a4d95eaf57b735545efd00e28803bba077192c81668165e9b3f491491fe8",
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


def _assert_safe(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "33E"
    for key in TRUE_KEYS:
        assert payload[key] is True
    for key in FALSE_KEYS:
        assert payload[key] is False


def test_command_module_is_import_safe(capsys):
    importlib.reload(dry_run)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(dry_run.load_planning_rows_from_path)
    assert callable(dry_run.build_dry_run_payload)
    assert callable(dry_run.main)


def test_load_planning_rows_from_json_list(tmp_path):
    path = tmp_path / "rows.json"
    path.write_text(json.dumps([{"job_id": "j1"}, {"job_id": "j2"}]))
    assert dry_run.load_planning_rows_from_path(path) == [
        {"job_id": "j1"},
        {"job_id": "j2"},
    ]


def test_load_planning_rows_from_json_dictionary_with_planning_rows(tmp_path):
    path = tmp_path / "rows.json"
    path.write_text(json.dumps({"planning_rows": [{"job_id": "j1"}]}))
    assert dry_run.load_planning_rows_from_path(path) == [{"job_id": "j1"}]


def test_load_planning_rows_from_jsonl(tmp_path):
    path = tmp_path / "rows.jsonl"
    path.write_text('{"job_id":"j1"}\n\n{"job_id":"j2"}\n')
    assert dry_run.load_planning_rows_from_path(path) == [
        {"job_id": "j1"},
        {"job_id": "j2"},
    ]


def test_load_planning_rows_from_csv(tmp_path):
    path = tmp_path / "rows.csv"
    path.write_text("job_id,title\nj1,Engineer\n")
    assert dry_run.load_planning_rows_from_path(path) == [
        {"job_id": "j1", "title": "Engineer"}
    ]


def test_loader_rejects_unsupported_extension_and_invalid_json(tmp_path):
    unsupported = tmp_path / "rows.txt"
    unsupported.write_text("job_id=j1")
    with pytest.raises(dry_run.PlanningArtifactLoadError, match="unsupported"):
        dry_run.load_planning_rows_from_path(unsupported)

    invalid = tmp_path / "rows.json"
    invalid.write_text("{not-json")
    with pytest.raises(dry_run.PlanningArtifactLoadError, match="invalid JSON"):
        dry_run.load_planning_rows_from_path(invalid)


def test_build_dry_run_payload_calls_phase33d_mapper(monkeypatch):
    calls = []

    def fake_mapper(*, planning_rows=None, router_policy=None):
        calls.append({"planning_rows": planning_rows, "router_policy": router_policy})
        return {
            "mapped_items": [{"item_id": "j1"}],
            "unmapped_rows": [],
            "grouped_by_next_allowed_step": {"run_relevance_prefilter": []},
            "next_step_counts": {"run_relevance_prefilter": 1},
        }

    monkeypatch.setattr(
        dry_run,
        "build_controlled_agent_router_planning_artifact_mapper_readonly",
        fake_mapper,
    )

    payload = dry_run.build_dry_run_payload(
        planning_rows=[{"job_id": "j1"}],
        router_policy={"final_score_threshold": 75},
    )

    assert calls == [
        {
            "planning_rows": [{"job_id": "j1"}],
            "router_policy": {"final_score_threshold": 75},
        }
    ]
    _assert_safe(payload)
    assert payload["planning_row_count"] == 1
    assert payload["grouped_by_next_allowed_step"] == {"run_relevance_prefilter": []}
    assert payload["next_step_counts"] == {"run_relevance_prefilter": 1}
    assert payload["dry_run_summary"]["output_file_written"] is False


def test_main_prints_json_to_stdout_for_valid_input(tmp_path, capsys):
    path = tmp_path / "rows.json"
    path.write_text(json.dumps([{"job_id": "j1", "title": "Engineer"}]))

    before = {item.name for item in tmp_path.iterdir()}
    result = dry_run.main(["--input", str(path), "--score-threshold", "72"])
    after = {item.name for item in tmp_path.iterdir()}
    captured = capsys.readouterr()

    assert result == 0
    assert captured.err == ""
    payload = json.loads(captured.out)
    _assert_safe(payload)
    assert payload["planning_row_count"] == 1
    assert "grouped_by_next_allowed_step" in payload
    assert before == after


def test_main_returns_nonzero_for_missing_or_invalid_input(tmp_path, capsys):
    missing_result = dry_run.main([])
    missing_captured = capsys.readouterr()
    assert missing_result != 0
    assert "--input is required" in missing_captured.err
    assert missing_captured.out == ""

    invalid = tmp_path / "rows.txt"
    invalid.write_text("not supported")
    invalid_result = dry_run.main(["--input", str(invalid)])
    invalid_captured = capsys.readouterr()
    assert invalid_result != 0
    assert "unsupported" in invalid_captured.err
    assert invalid_captured.out == ""


def test_payload_excludes_generated_tailoring_text_and_real_output():
    payload = dry_run.build_dry_run_payload(
        planning_rows=[
            {
                "job_id": "j1",
                "manual_tailoring_preview": {
                    "preview_ready": True,
                    "generated_tailoring_text": "do not surface",
                    "real_tailoring_output": "do not surface",
                },
            }
        ]
    )
    rendered = json.dumps(payload).lower()
    assert "do not surface" not in rendered
    assert payload["real_tailoring_output_created"] is False


def test_source_has_no_forbidden_imports_or_runtime_calls():
    source = COMMAND_PATH.read_text(encoding="utf-8")
    assert "build_controlled_agent_router_planning_artifact_mapper_readonly" in source
    for marker in FORBIDDEN_IMPORT_MARKERS:
        assert marker not in source


def test_docs_contain_required_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged_by_hash():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_changed_files_are_limited_to_phase33e_surface_and_legacy_guards():
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    allowed = {
        "run_controlled_agent_router_planning_artifact_dry_run.py",
        "docs/phase33_controlled_agent_router_planning_artifact_dry_run_command_readonly.md",
        "tests/test_phase33e_controlled_agent_router_planning_artifact_dry_run_command_readonly.py",
        "src/agents/jd_intelligence_llm_signal_extractor_default_off.py",
        "docs/phase34_jd_intelligence_llm_signal_extractor_default_off.md",
        "tests/test_phase34a_jd_intelligence_llm_signal_extractor_default_off.py",
        "src/agents/jd_intelligence_planning_artifact_enricher_default_off.py",
        "docs/phase34_jd_intelligence_planning_artifact_enricher_default_off.md",
        "tests/test_phase34b_jd_intelligence_planning_artifact_enricher_default_off.py",
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
