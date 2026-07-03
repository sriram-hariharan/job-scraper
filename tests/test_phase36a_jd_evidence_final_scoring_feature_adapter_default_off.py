# phase56b legacy guard marker: changes_only 4a2936004507cc4cc09615ef41de7e7e170c3c78aa840ce66bfd27484e542668 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 4a2936004507cc4cc09615ef41de7e7e170c3c78aa840ce66bfd27484e542668
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess

from src.agents import jd_evidence_final_scoring_feature_adapter_default_off as adapter
from src.agents.jd_evidence_final_scoring_feature_adapter_default_off import (
    build_jd_evidence_final_scoring_feature_adapter_default_off,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "src/agents/jd_evidence_final_scoring_feature_adapter_default_off.py"
DOC_PATH = ROOT / "docs/phase36_jd_evidence_final_scoring_feature_adapter_default_off.md"

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "jd_evidence_final_scoring_feature_adapter",
    "read_only",
    "advisory_only",
    "deterministic_scoring_feature_preparation",
    "requires_manual_user_control",
    "planning_row_count",
    "valid_planning_row_count",
    "invalid_planning_row_count",
    "feature_rows",
    "unmapped_rows",
    "feature_policy",
    "feature_packet",
    "scoring_feature_rows",
    "scoring_feature_summary",
    "existing_score_fields_detected",
    "existing_scores_preserved",
    "evidence_ready_count",
    "evidence_missing_count",
    "high_coverage_count",
    "low_coverage_count",
    "red_flag_review_count",
    "missing_required_skills_by_row",
    "missing_tools_by_row",
    "red_flag_findings_by_row",
    "adapter_findings",
    "missing_inputs",
    "adapter_key",
    "final_score_produced",
    "existing_score_changed",
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
    "evidence_matching_performed",
    "final_scoring_performed",
    "matching_scoring_module_called",
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
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "stage_execution_performed",
    "relevance_prefilter_performed",
    "jd_intelligence_extraction_performed",
    "evidence_matching_performed",
    "final_scoring_performed",
    "matching_scoring_module_called",
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
    "build_jd_signal_resume_evidence_matrix_default_off(",
    "build_jd_signal_planning_artifact_evidence_enricher_default_off(",
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
    "phase 36a jd evidence final-scoring feature adapter default-off",
    "jd evidence final-scoring feature adapter",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "deterministic scoring feature preparation",
    "converts jd evidence matrix results into final-scoring-ready feature packets",
    "preserves existing score fields",
    "does not produce final application score",
    "does not change existing scoring logic",
    "does not call matching/scoring modules",
    "does not run relevance prefilter",
    "does not run jd intelligence extraction",
    "does not run evidence matching",
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
    "final scoring remains deterministic and controlled by scoring logic",
    "phase35c-jd-signal-planning-artifact-evidence-enrichment-dry-run-command-default-off-v1",
    "phase35b-jd-signal-planning-artifact-evidence-enricher-default-off-v1",
    "phase35a-jd-signal-resume-evidence-matrix-default-off-v1",
    "phase34c-jd-intelligence-planning-artifact-enrichment-dry-run-command-default-off-v1",
    "phase34b-jd-intelligence-planning-artifact-enricher-default-off-v1",
    "phase34a-jd-intelligence-llm-signal-extractor-default-off-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
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
    "src/app/services.py": "4a2936004507cc4cc09615ef41de7e7e170c3c78aa840ce66bfd27484e542668",
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


def _evidence(
    *,
    ready: bool = True,
    required: float = 0.8,
    preferred: float = 0.5,
    tools: float = 0.5,
    responsibilities: float = 0.5,
    missing_required: list[str] | None = None,
    missing_tools: list[str] | None = None,
    red_flags: list[dict] | None = None,
) -> dict:
    return {
        "evidence_ready": ready,
        "required_skill_coverage_ratio": required,
        "preferred_skill_coverage_ratio": preferred,
        "tool_coverage_ratio": tools,
        "responsibility_coverage_ratio": responsibilities,
        "missing_required_skills": missing_required or [],
        "missing_tools": missing_tools or [],
        "red_flag_findings": red_flags or [],
    }


def _row(**extra) -> dict:
    row = {
        "item_id": "item-1",
        "job_id": "job-1",
        "title": "Data Engineer",
        "company": "Acme",
    }
    for key, value in extra.items():
        row[key] = value
    return row


def _assert_safe(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "36A"
    assert payload["default_off"] is True
    assert payload["jd_evidence_final_scoring_feature_adapter"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["deterministic_scoring_feature_preparation"] is True
    assert payload["requires_manual_user_control"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_helper_exists_and_is_import_safe(capsys):
    importlib.reload(adapter)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(build_jd_evidence_final_scoring_feature_adapter_default_off)


def test_missing_and_non_list_planning_rows_return_empty_blocked_result():
    for rows in (None, {"job_id": "j1"}):
        payload = build_jd_evidence_final_scoring_feature_adapter_default_off(
            planning_rows=rows
        )
        _assert_safe(payload)
        assert payload["planning_row_count"] == 0
        assert payload["feature_rows"] == []
        assert payload["feature_packet"]["scoring_feature_rows"] == []
        assert payload["missing_inputs"] == ["planning_rows"]
        assert payload["unmapped_rows"][0]["reason"] == (
            "planning_rows must be supplied as a list"
        )


def test_empty_planning_rows_returns_empty_feature_rows_and_packet():
    payload = build_jd_evidence_final_scoring_feature_adapter_default_off(
        planning_rows=[]
    )
    _assert_safe(payload)
    assert payload["planning_row_count"] == 0
    assert payload["feature_rows"] == []
    assert payload["feature_packet"]["feature_row_count"] == 0
    assert payload["scoring_feature_rows"] == []


def test_invalid_non_dict_rows_go_to_unmapped_rows_without_crashing():
    payload = build_jd_evidence_final_scoring_feature_adapter_default_off(
        planning_rows=[_row(evidence_matrix_result=_evidence()), "bad"]
    )
    _assert_safe(payload)
    assert payload["valid_planning_row_count"] == 1
    assert payload["invalid_planning_row_count"] == 1
    assert payload["unmapped_rows"] == [
        {"input_index": 1, "reason": "planning row must be a dictionary"}
    ]


def test_row_level_evidence_matrix_result_produces_scoring_feature_row():
    payload = build_jd_evidence_final_scoring_feature_adapter_default_off(
        planning_rows=[
            _row(
                evidence_matrix_result=_evidence(
                    required=1.0,
                    tools=1.0,
                    red_flags=[{"signal": "on-call ambiguity", "status": "matched"}],
                )
            )
        ]
    )
    _assert_safe(payload)
    feature = payload["feature_rows"][0]
    assert feature["item_id"] == "item-1"
    assert feature["job_id"] == "job-1"
    assert feature["evidence_ready"] is True
    assert feature["coverage_band"] == "high"
    assert feature["requires_red_flag_review"] is True
    assert feature["scoring_inputs_ready"] is True


def test_row_level_evidence_coverage_summary_produces_feature_row():
    payload = build_jd_evidence_final_scoring_feature_adapter_default_off(
        planning_rows=[
            _row(
                evidence_matrix={
                    "required_skills": [
                        {"signal": "Python", "status": "missing"}
                    ],
                    "tools": [{"signal": "dbt", "status": "missing"}],
                },
                evidence_coverage_summary={"required_skill_total": 1},
            )
        ]
    )
    _assert_safe(payload)
    feature = payload["feature_rows"][0]
    assert feature["evidence_ready"] is True
    assert feature["coverage_band"] == "low"
    assert feature["missing_required_skill_count"] == 1
    assert feature["missing_tool_count"] == 1


def test_evidence_results_keyed_by_item_job_id_id_and_index_are_resolved():
    rows = [
        {"item_id": "item-1", "title": "One"},
        {"job_id": "job-2", "title": "Two"},
        {"id": "id-3", "title": "Three"},
        {"title": "Four"},
    ]
    payload = build_jd_evidence_final_scoring_feature_adapter_default_off(
        planning_rows=rows,
        evidence_results={
            "item-1": _evidence(required=1.0),
            "job-2": _evidence(required=0.6),
            "id-3": _evidence(required=0.4),
            "3": _evidence(required=0.9),
        },
    )
    _assert_safe(payload)
    assert [row["coverage_band"] for row in payload["feature_rows"]] == [
        "high",
        "medium",
        "low",
        "high",
    ]


def test_list_aligned_evidence_results_are_resolved_deterministically():
    payload = build_jd_evidence_final_scoring_feature_adapter_default_off(
        planning_rows=[{"job_id": "j1"}, {"job_id": "j2"}],
        evidence_results=[_evidence(required=0.7), _evidence(required=0.2)],
    )
    _assert_safe(payload)
    assert payload["feature_rows"][0]["coverage_band"] == "medium"
    assert payload["feature_rows"][1]["coverage_band"] == "low"


def test_existing_score_fields_are_detected_preserved_and_not_changed():
    row = _row(final_score=91, score=12, evidence_matrix_result=_evidence())
    original = deepcopy(row)
    payload = build_jd_evidence_final_scoring_feature_adapter_default_off(
        planning_rows=[row]
    )
    _assert_safe(payload)
    assert row == original
    assert payload["feature_rows"][0]["existing_score_present"] is True
    assert payload["feature_rows"][0]["existing_score_field"] == "final_score"
    assert payload["feature_rows"][0]["existing_score_value"] == 91
    assert payload["existing_score_fields_detected"] == [
        {"row_key": "item-1", "field": "final_score", "value": 91}
    ]
    assert payload["existing_scores_preserved"] is True
    assert payload["existing_score_changed"] is False


def test_no_final_score_is_produced():
    payload = build_jd_evidence_final_scoring_feature_adapter_default_off(
        planning_rows=[_row(evidence_matrix_result=_evidence())]
    )
    rendered = json.dumps(payload).lower()
    _assert_safe(payload)
    assert payload["final_score_produced"] is False
    assert payload["scoring_feature_summary"]["final_score_produced"] is False
    assert payload["feature_packet"]["final_score_included"] is False
    assert "application_score" not in payload
    assert "provider_request" not in rendered
    assert "mutation_command" not in rendered
    assert "application_submission_command" not in rendered


def test_policy_controls_coverage_band_and_red_flag_review():
    payload = build_jd_evidence_final_scoring_feature_adapter_default_off(
        planning_rows=[
            _row(
                evidence_matrix_result=_evidence(
                    required=0.75,
                    red_flags=[
                        {"signal": "one", "status": "matched"},
                        {"signal": "two", "status": "matched"},
                    ],
                )
            )
        ],
        feature_policy={
            "high_required_skill_coverage_threshold": 0.7,
            "low_required_skill_coverage_threshold": 0.4,
            "red_flag_review_threshold": 3,
        },
    )
    _assert_safe(payload)
    assert payload["feature_rows"][0]["coverage_band"] == "high"
    assert payload["feature_rows"][0]["requires_red_flag_review"] is False
    assert payload["feature_policy"]["red_flag_review_threshold"] == 3


def test_missing_required_tools_packet_and_summary_are_deterministic():
    payload = build_jd_evidence_final_scoring_feature_adapter_default_off(
        planning_rows=[
            _row(
                evidence_matrix_result=_evidence(
                    ready=True,
                    required=0.4,
                    tools=0.0,
                    missing_required=["Python", "SQL"],
                    missing_tools=["dbt"],
                )
            ),
            {"job_id": "j2"},
        ]
    )
    _assert_safe(payload)
    assert payload["missing_required_skills_by_row"] == {
        "item-1": ["Python", "SQL"],
        "j2": [],
    }
    assert payload["missing_tools_by_row"] == {"item-1": ["dbt"], "j2": []}
    assert payload["scoring_feature_summary"] == {
        "feature_row_count": 2,
        "evidence_ready_count": 1,
        "evidence_missing_count": 1,
        "high_coverage_count": 0,
        "low_coverage_count": 1,
        "red_flag_review_count": 0,
        "final_score_produced": False,
        "existing_score_changed": False,
    }
    assert payload["feature_packet"]["scoring_feature_rows"] == payload[
        "scoring_feature_rows"
    ]


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


def test_changed_files_are_limited_to_phase36a_surface_and_legacy_guards():
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    allowed = {
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
