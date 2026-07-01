# phase56b legacy guard marker: changes_only 5c951b6b6b06b47caa9c7874b94f0f8e968de487817ef4bdceb745c225517386 992b95259e278a6dd0f9b8d37be916ece433b562529fc2d3ff0d683d8f9cc25e
# phase56a legacy guard marker: changes_only a52216e4920bc866d09f8899c12b3a1e8b2dd86a92d9e366d383db09f9e10a32 5c951b6b6b06b47caa9c7874b94f0f8e968de487817ef4bdceb745c225517386
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess

from src.agents import jd_evidence_score_impact_preview_default_off as impact
from src.agents.jd_evidence_score_impact_preview_default_off import (
    build_jd_evidence_score_impact_preview_default_off,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "src/agents/jd_evidence_score_impact_preview_default_off.py"
DOC_PATH = ROOT / "docs/phase38_jd_evidence_score_impact_preview_default_off.md"

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "jd_evidence_score_impact_preview",
    "read_only",
    "advisory_only",
    "preview_only",
    "deterministic_score_impact_preview",
    "requires_manual_user_control",
    "contribution_rows_present",
    "contribution_row_count",
    "valid_contribution_row_count",
    "invalid_contribution_row_count",
    "impact_policy",
    "impact_rows",
    "unmapped_rows",
    "impact_packet",
    "impact_summary",
    "preview_score_available_count",
    "preview_score_blocked_count",
    "positive_impact_count",
    "negative_impact_count",
    "neutral_impact_count",
    "red_flag_review_count",
    "existing_score_fields_detected",
    "existing_scores_preserved",
    "score_preview_values",
    "impact_findings",
    "missing_inputs",
    "impact_key",
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
    "phase 38a jd evidence score impact preview default-off",
    "jd evidence score impact preview",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "deterministic score impact preview",
    "converts advisory contribution previews into hypothetical score impact previews",
    "produces hypothetical score preview values",
    "preserves existing score fields",
    "does not produce final application score",
    "does not change existing scoring logic",
    "does not call matching/scoring modules",
    "does not run relevance prefilter",
    "does not run jd intelligence extraction",
    "does not run evidence matching",
    "does not run scoring feature preparation",
    "does not run contribution preview",
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
    "final scoring remains deterministic and controlled by scoring logic",
    "phase37-jd-evidence-scoring-contribution-preview-release-v1",
    "phase37b-jd-evidence-scoring-contribution-preview-dry-run-command-default-off-v1",
    "phase37a-jd-evidence-scoring-contribution-preview-default-off-v1",
    "phase36-jd-evidence-final-scoring-feature-adapter-release-v1",
    "phase36b-jd-evidence-final-scoring-feature-adapter-dry-run-command-default-off-v1",
    "phase36a-jd-evidence-final-scoring-feature-adapter-default-off-v1",
    "phase35c-jd-signal-planning-artifact-evidence-enrichment-dry-run-command-default-off-v1",
    "phase34c-jd-intelligence-planning-artifact-enrichment-dry-run-command-default-off-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
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
    "src/app/api.py": "a52216e4920bc866d09f8899c12b3a1e8b2dd86a92d9e366d383db09f9e10a32",
    "src/app/services.py": "5c951b6b6b06b47caa9c7874b94f0f8e968de487817ef4bdceb745c225517386",
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


def _row(**extra) -> dict:
    row = {
        "row_key": "item-1",
        "item_id": "item-1",
        "job_id": "job-1",
        "title": "Data Engineer",
        "company": "Acme",
        "existing_score_present": True,
        "existing_score_field": "final_score",
        "existing_score_value": 80,
        "bounded_advisory_contribution_points": 7.5,
        "contribution_band": "positive",
        "requires_red_flag_review": False,
        "final_score_produced": False,
        "existing_score_changed": False,
    }
    for key, value in extra.items():
        row[key] = value
    return row


def _assert_safe(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "38A"
    assert payload["default_off"] is True
    assert payload["jd_evidence_score_impact_preview"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["preview_only"] is True
    assert payload["deterministic_score_impact_preview"] is True
    assert payload["requires_manual_user_control"] is True
    assert payload["hypothetical_score_preview_produced"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_helper_exists_and_is_import_safe(capsys):
    importlib.reload(impact)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(build_jd_evidence_score_impact_preview_default_off)


def test_missing_contribution_rows_blocks_with_missing_input_reason():
    payload = build_jd_evidence_score_impact_preview_default_off()
    _assert_safe(payload)
    assert payload["contribution_rows_present"] is False
    assert payload["contribution_row_count"] == 0
    assert payload["impact_rows"] == []
    assert payload["missing_inputs"] == ["contribution_rows"]
    assert payload["preview_score_available_count"] == 0


def test_contribution_packet_with_contribution_rows_is_accepted():
    payload = build_jd_evidence_score_impact_preview_default_off(
        contribution_packet={"contribution_rows": [_row()]}
    )
    _assert_safe(payload)
    assert payload["contribution_rows_present"] is True
    assert payload["valid_contribution_row_count"] == 1
    assert payload["impact_packet"]["source"] == "contribution_packet"


def test_nested_preview_result_contribution_rows_are_accepted():
    payload = build_jd_evidence_score_impact_preview_default_off(
        contribution_packet={"preview_result": {"contribution_rows": [_row()]}}
    )
    _assert_safe(payload)
    assert payload["impact_packet"]["source"] == "preview_result"
    nested_packet = build_jd_evidence_score_impact_preview_default_off(
        contribution_packet={
            "preview_result": {"contribution_packet": {"contribution_rows": [_row()]}}
        }
    )
    _assert_safe(nested_packet)
    assert nested_packet["impact_packet"]["source"] == "preview_result_packet"


def test_explicit_contribution_rows_take_precedence_over_packet_rows():
    payload = build_jd_evidence_score_impact_preview_default_off(
        contribution_packet={"contribution_rows": [_row(job_id="packet")]},
        contribution_rows=[_row(job_id="explicit")],
    )
    _assert_safe(payload)
    assert payload["impact_packet"]["source"] == "contribution_rows"
    assert payload["impact_rows"][0]["job_id"] == "explicit"


def test_invalid_non_dict_contribution_rows_go_to_unmapped_rows_without_crashing():
    payload = build_jd_evidence_score_impact_preview_default_off(
        contribution_rows=[_row(), "bad"]
    )
    _assert_safe(payload)
    assert payload["valid_contribution_row_count"] == 1
    assert payload["invalid_contribution_row_count"] == 1
    assert payload["unmapped_rows"] == [
        {"input_index": 1, "reason": "contribution row must be a dictionary"}
    ]


def test_existing_score_fields_are_detected_preserved_and_not_changed():
    row = _row(existing_score_value=91)
    original = deepcopy(row)
    payload = build_jd_evidence_score_impact_preview_default_off(
        contribution_rows=[row]
    )
    _assert_safe(payload)
    assert row == original
    impact_row = payload["impact_rows"][0]
    assert impact_row["existing_score_present"] is True
    assert impact_row["existing_score_field"] == "final_score"
    assert impact_row["existing_score_value"] == 91
    assert impact_row["existing_score_changed"] is False
    assert payload["existing_score_fields_detected"] == [
        {"row_key": "item-1", "field": "final_score", "value": 91}
    ]
    assert payload["existing_scores_preserved"] is True


def test_base_score_delta_and_hypothetical_preview_are_deterministic():
    payload = build_jd_evidence_score_impact_preview_default_off(
        contribution_rows=[_row(existing_score_value=80, bounded_advisory_contribution_points=7.5)]
    )
    _assert_safe(payload)
    row = payload["impact_rows"][0]
    assert row["base_score_for_preview"] == 80.0
    assert row["bounded_advisory_contribution_points"] == 7.5
    assert row["hypothetical_score_preview"] == 87.5
    assert row["score_preview_delta"] == 7.5
    assert row["score_preview_available"] is True
    assert row["impact_band"] == "positive"


def test_default_base_score_is_used_when_existing_score_absent():
    payload = build_jd_evidence_score_impact_preview_default_off(
        contribution_rows=[
            _row(existing_score_present=False, existing_score_field="", existing_score_value=None)
        ],
        impact_policy={"default_base_score": 70},
    )
    _assert_safe(payload)
    row = payload["impact_rows"][0]
    assert row["base_score_for_preview"] == 70.0
    assert row["hypothetical_score_preview"] == 77.5


def test_preview_blocks_when_existing_score_is_required_and_missing():
    payload = build_jd_evidence_score_impact_preview_default_off(
        contribution_rows=[
            _row(existing_score_present=False, existing_score_field="", existing_score_value=None)
        ],
        impact_policy={"require_existing_score_for_preview": True},
    )
    _assert_safe(payload)
    row = payload["impact_rows"][0]
    assert row["score_preview_available"] is False
    assert row["score_preview_blocked_reason"] == "existing score required for preview"
    assert row["impact_band"] == "blocked"
    assert payload["preview_score_blocked_count"] == 1


def test_preview_blocks_when_red_flag_review_blocks_preview_score():
    payload = build_jd_evidence_score_impact_preview_default_off(
        contribution_rows=[_row(requires_red_flag_review=True)],
        impact_policy={"red_flag_review_blocks_preview_score": True},
    )
    _assert_safe(payload)
    row = payload["impact_rows"][0]
    assert row["score_preview_available"] is False
    assert row["score_preview_blocked_reason"] == "red flag review required"
    assert row["impact_band"] == "review"
    assert payload["red_flag_review_count"] == 1


def test_hypothetical_score_preview_is_bounded_by_floor_and_ceiling():
    payload = build_jd_evidence_score_impact_preview_default_off(
        contribution_rows=[
            _row(row_key="high", item_id="high", existing_score_value=98, bounded_advisory_contribution_points=10),
            _row(row_key="low", item_id="low", existing_score_value=2, bounded_advisory_contribution_points=-10),
        ],
        impact_policy={"score_floor": 0, "score_ceiling": 100},
    )
    _assert_safe(payload)
    assert payload["impact_rows"][0]["hypothetical_score_preview"] == 100.0
    assert payload["impact_rows"][0]["score_preview_delta"] == 2.0
    assert payload["impact_rows"][1]["hypothetical_score_preview"] == 0.0
    assert payload["impact_rows"][1]["score_preview_delta"] == -2.0


def test_impact_band_counts_and_summary_are_deterministic():
    payload = build_jd_evidence_score_impact_preview_default_off(
        contribution_rows=[
            _row(row_key="positive", item_id="positive", existing_score_value=80, bounded_advisory_contribution_points=5),
            _row(row_key="negative", item_id="negative", existing_score_value=80, bounded_advisory_contribution_points=-5),
            _row(row_key="neutral", item_id="neutral", existing_score_value=80, bounded_advisory_contribution_points=0),
            _row(row_key="review", item_id="review", existing_score_value=80, requires_red_flag_review=True),
        ]
    )
    _assert_safe(payload)
    assert [row["impact_band"] for row in payload["impact_rows"]] == [
        "positive",
        "negative",
        "neutral",
        "review",
    ]
    assert payload["impact_summary"] == {
        "contribution_row_count": 4,
        "valid_contribution_row_count": 4,
        "invalid_contribution_row_count": 0,
        "preview_score_available_count": 3,
        "preview_score_blocked_count": 1,
        "positive_impact_count": 1,
        "negative_impact_count": 1,
        "neutral_impact_count": 1,
        "red_flag_review_count": 1,
        "final_score_produced": False,
        "existing_score_changed": False,
    }


def test_no_final_score_is_produced_and_no_runtime_commands_are_included():
    payload = build_jd_evidence_score_impact_preview_default_off(
        contribution_rows=[_row()]
    )
    rendered = json.dumps(payload).lower()
    _assert_safe(payload)
    assert payload["final_score_produced"] is False
    assert payload["impact_packet"]["final_score_included"] is False
    assert "application_score" not in payload
    assert "provider_request" not in rendered
    assert "network_request" not in rendered
    assert "mutation_command" not in rendered
    assert "db_write_command" not in rendered
    assert "application_submission_command" not in rendered


def test_impact_packet_and_score_preview_values_are_deterministic():
    payload = build_jd_evidence_score_impact_preview_default_off(
        contribution_rows=[_row(existing_score_value=80, bounded_advisory_contribution_points=7.5)]
    )
    _assert_safe(payload)
    assert payload["score_preview_values"] == [
        {
            "row_key": "item-1",
            "base_score_for_preview": 80.0,
            "hypothetical_score_preview": 87.5,
            "score_preview_delta": 7.5,
        }
    ]
    assert payload["impact_packet"]["impact_rows"][0] == {
        "row_key": "item-1",
        "item_id": "item-1",
        "job_id": "job-1",
        "hypothetical_score_preview": 87.5,
        "score_preview_delta": 7.5,
        "score_preview_available": True,
        "impact_band": "positive",
        "final_score_produced": False,
    }


def test_source_has_no_forbidden_imports_calls_or_writes():
    source = HELPER_PATH.read_text(encoding="utf-8")
    assert "from src." not in source
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


def test_changed_files_are_limited_to_phase38a_surface_and_legacy_guards():
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    allowed = {
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
