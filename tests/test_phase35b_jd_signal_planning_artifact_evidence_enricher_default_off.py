# phase56b legacy guard marker: changes_only f186703fecdda54458c468f9c2ed1de0517fa86942bb3d0fe0b522f0601fe5a8 1ff2a73993300f391aa1fb8151a4d225e803b6c5d499e311faa5058efc4b965c
# phase56a legacy guard marker: changes_only 85bd669060be60c275c785fefdb4438dc567b6f1c40a3b2a134d1c885db4ee96 f186703fecdda54458c468f9c2ed1de0517fa86942bb3d0fe0b522f0601fe5a8
from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess

from src.agents import (
    jd_signal_planning_artifact_evidence_enricher_default_off as enricher,
)
from src.agents.jd_signal_planning_artifact_evidence_enricher_default_off import (
    build_jd_signal_planning_artifact_evidence_enricher_default_off,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT / "src/agents/jd_signal_planning_artifact_evidence_enricher_default_off.py"
)
DOC_PATH = (
    ROOT / "docs/phase35_jd_signal_planning_artifact_evidence_enricher_default_off.md"
)

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "jd_signal_planning_artifact_evidence_enricher",
    "read_only",
    "advisory_only",
    "deterministic_evidence_matching",
    "requires_manual_user_control",
    "planning_row_count",
    "valid_planning_row_count",
    "invalid_planning_row_count",
    "enriched_rows",
    "unmapped_rows",
    "evidence_results",
    "evidence_ready_count",
    "evidence_blocked_count",
    "resume_evidence_present",
    "field_mapping_summary",
    "coverage_summary",
    "average_required_skill_coverage_ratio",
    "average_preferred_skill_coverage_ratio",
    "average_tool_coverage_ratio",
    "average_responsibility_coverage_ratio",
    "missing_required_skills_by_row",
    "missing_tools_by_row",
    "red_flag_findings_by_row",
    "enricher_findings",
    "missing_inputs",
    "enricher_key",
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
    "phase 35b jd signal planning artifact evidence enricher default-off",
    "jd signal planning artifact evidence enricher",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "deterministic evidence matching",
    "calls the phase 35a jd signal resume evidence matrix helper",
    "enriches copied planning-like rows with evidence matrix results",
    "supports row-level resume evidence",
    "supports shared resume/profile evidence",
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
    "phase35a-jd-signal-resume-evidence-matrix-default-off-v1",
    "phase34c-jd-intelligence-planning-artifact-enrichment-dry-run-command-default-off-v1",
    "phase34b-jd-intelligence-planning-artifact-enricher-default-off-v1",
    "phase34a-jd-intelligence-llm-signal-extractor-default-off-v1",
    "phase33e-controlled-agent-router-planning-artifact-dry-run-command-readonly-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
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
    "src/app/services.py": "f186703fecdda54458c468f9c2ed1de0517fa86942bb3d0fe0b522f0601fe5a8",
    "src/app/static/agentic_review.js": "1dfa42f640a639b82ce8f22e652b91e92f25f8087ecafe817c97a05b48018e0b",
    "src/app/static/app_redesign.css": "62429a0e1466a93869e303023b6ee9a23108db6dddfd3b2c2247b2d31062169c",
    "src/pipeline/job_filter.py": "6931bbb67ec7a5aa68c9ddaf52bb28c56cd007f4ca30de18245fabdc959689b4",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/tailoring/llm.py": "44614b3b0ecf7b13514996b33ddc9d4346024e9cf031f77eaa135e8a0ab30ce8",
    "generate_tailoring_suggestions.py": "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _signals(required: list[str] | None = None) -> dict:
    return {
        "required_skills": required or ["Python", "SQL", "Kubernetes"],
        "preferred_skills": ["Airflow", "Scala"],
        "responsibilities": ["Own data pipelines", "Mentor engineers"],
        "tools": ["dbt", "Snowflake"],
        "domain": "data platform",
        "seniority": "senior",
        "location_constraints": ["Remote US"],
        "visa_constraints": ["No sponsorship"],
        "resume_evidence_needed": ["Python pipelines"],
        "red_flags": ["on-call ambiguity"],
    }


def _assert_safe(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "35B"
    assert payload["default_off"] is True
    assert payload["jd_signal_planning_artifact_evidence_enricher"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["deterministic_evidence_matching"] is True
    assert payload["requires_manual_user_control"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_helper_exists_and_is_import_safe(capsys):
    importlib.reload(enricher)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(build_jd_signal_planning_artifact_evidence_enricher_default_off)


def test_helper_imports_and_calls_phase35a_helper_only():
    source = HELPER_PATH.read_text(encoding="utf-8")
    assert "build_jd_signal_resume_evidence_matrix_default_off" in source
    assert "from src.agents.jd_signal_resume_evidence_matrix_default_off import" in source
    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source
    for marker in FORBIDDEN_WRITE_MARKERS:
        assert marker not in source


def test_missing_and_non_list_planning_rows_return_empty_blocked_result():
    for rows in (None, {"job_id": "j1"}):
        payload = build_jd_signal_planning_artifact_evidence_enricher_default_off(
            planning_rows=rows
        )
        _assert_safe(payload)
        assert payload["planning_row_count"] == 0
        assert payload["enriched_rows"] == []
        assert payload["evidence_results"] == []
        assert payload["missing_inputs"] == ["planning_rows"]
        assert payload["unmapped_rows"][0]["reason"] == (
            "planning_rows must be supplied as a list"
        )


def test_empty_planning_rows_returns_empty_enriched_rows_and_evidence_summaries():
    payload = build_jd_signal_planning_artifact_evidence_enricher_default_off(
        planning_rows=[]
    )
    _assert_safe(payload)
    assert payload["planning_row_count"] == 0
    assert payload["enriched_rows"] == []
    assert payload["evidence_results"] == []
    assert payload["missing_required_skills_by_row"] == {}
    assert payload["missing_tools_by_row"] == {}
    assert payload["red_flag_findings_by_row"] == {}


def test_invalid_non_dict_rows_go_to_unmapped_rows_without_crashing():
    payload = build_jd_signal_planning_artifact_evidence_enricher_default_off(
        planning_rows=[{"job_id": "j1", "jd_signals": _signals()}, "bad"],
        resume_evidence="Python SQL",
    )
    _assert_safe(payload)
    assert payload["valid_planning_row_count"] == 1
    assert payload["invalid_planning_row_count"] == 1
    assert payload["unmapped_rows"] == [
        {"input_index": 1, "reason": "planning row must be a dictionary"}
    ]


def test_row_level_jd_signals_and_row_level_resume_evidence_enrich_ready_row():
    row = {
        "item_id": "a1",
        "jd_signals": _signals(),
        "resume_evidence": "Python SQL Airflow dbt Own data pipelines",
    }
    original = deepcopy(row)
    payload = build_jd_signal_planning_artifact_evidence_enricher_default_off(
        planning_rows=[row],
    )
    _assert_safe(payload)
    assert row == original
    assert payload["evidence_ready_count"] == 1
    enriched = payload["enriched_rows"][0]
    assert enriched is not row
    assert "evidence_matrix_result" in enriched
    assert "evidence_matrix" in enriched
    assert "evidence_coverage_summary" in enriched
    assert enriched["evidence_matrix_result"]["evidence_ready"] is True
    assert payload["missing_required_skills_by_row"] == {"a1": ["Kubernetes"]}


def test_top_level_shared_resume_evidence_is_used_when_row_level_absent():
    payload = build_jd_signal_planning_artifact_evidence_enricher_default_off(
        planning_rows=[{"job_id": "j1", "jd_intelligence": _signals()}],
        resume_evidence="Senior data platform engineer with Python SQL dbt",
    )
    _assert_safe(payload)
    assert payload["evidence_ready_count"] == 1
    assert payload["enriched_rows"][0]["evidence_matrix_result"]["matched_tools"] == ["dbt"]


def test_top_level_keyed_resume_evidence_resolves_by_item_job_id_id_and_index():
    rows = [
        {"item_id": "item-1", "jd_signals": _signals(["Python"])},
        {"job_id": "job-2", "jd_signals": _signals(["SQL"])},
        {"id": "id-3", "jd_signals": _signals(["Airflow"])},
        {"jd_signals": _signals(["dbt"])},
    ]
    payload = build_jd_signal_planning_artifact_evidence_enricher_default_off(
        planning_rows=rows,
        resume_evidence={
            "item-1": "Python",
            "job-2": "SQL",
            "id-3": "Airflow",
            "3": "dbt",
        },
    )
    _assert_safe(payload)
    assert payload["evidence_ready_count"] == 4
    assert payload["missing_required_skills_by_row"] == {
        "item-1": [],
        "job-2": [],
        "id-3": [],
        "3": [],
    }


def test_list_aligned_top_level_resume_evidence_is_deterministic():
    payload = build_jd_signal_planning_artifact_evidence_enricher_default_off(
        planning_rows=[
            {"job_id": "j1", "jd_intelligence_result": _signals(["Python"])},
            {"job_id": "j2", "jd_intelligence_result": _signals(["Snowflake"])},
        ],
        resume_evidence=["Python", "Snowflake"],
    )
    _assert_safe(payload)
    assert payload["evidence_ready_count"] == 2
    assert payload["missing_required_skills_by_row"] == {"j1": [], "j2": []}


def test_blocked_rows_do_not_get_fake_evidence():
    payload = build_jd_signal_planning_artifact_evidence_enricher_default_off(
        planning_rows=[{"job_id": "j1", "jd_signals": _signals()}],
        resume_evidence="",
    )
    _assert_safe(payload)
    assert payload["evidence_ready_count"] == 0
    assert payload["evidence_blocked_count"] == 1
    assert "evidence_matrix_result" not in payload["enriched_rows"][0]
    assert "resume_evidence" in payload["evidence_results"][0]["missing_inputs"]


def test_average_coverage_ratios_use_ready_rows_only():
    payload = build_jd_signal_planning_artifact_evidence_enricher_default_off(
        planning_rows=[
            {"job_id": "j1", "jd_signals": _signals(["Python", "SQL"])},
            {"job_id": "j2", "jd_signals": _signals(["Kubernetes"])},
            {"job_id": "j3", "jd_signals": _signals(["Scala"])},
        ],
        resume_evidence={
            "j1": "Python",
            "j2": "Kubernetes Airflow dbt Own data pipelines",
        },
    )
    _assert_safe(payload)
    assert payload["evidence_ready_count"] == 2
    assert payload["evidence_blocked_count"] == 1
    assert payload["average_required_skill_coverage_ratio"] == 0.75
    assert payload["average_preferred_skill_coverage_ratio"] == 0.25
    assert payload["average_tool_coverage_ratio"] == 0.25
    assert payload["average_responsibility_coverage_ratio"] == 0.25


def test_missing_tools_and_red_flags_by_row_are_deterministic():
    payload = build_jd_signal_planning_artifact_evidence_enricher_default_off(
        planning_rows=[{"job_id": "j1", "jd_signals": _signals()}],
        resume_evidence="Python SQL on-call ambiguity",
    )
    _assert_safe(payload)
    assert payload["missing_tools_by_row"] == {"j1": ["dbt", "Snowflake"]}
    assert payload["red_flag_findings_by_row"]["j1"][0]["status"] == "matched"


def test_no_final_score_is_produced_and_existing_score_is_not_changed():
    row = {
        "job_id": "j1",
        "jd_signals": _signals(),
        "existing_score": 44,
        "final_score": 99,
    }
    payload = build_jd_signal_planning_artifact_evidence_enricher_default_off(
        planning_rows=[row],
        resume_evidence="Python SQL",
    )
    rendered = json.dumps(payload).lower()
    _assert_safe(payload)
    assert payload["enriched_rows"][0]["existing_score"] == 44
    assert payload["enriched_rows"][0]["final_score"] == 99
    assert payload["coverage_summary"]["final_application_score_created"] is False
    assert payload["coverage_summary"]["existing_score_changed"] is False
    assert "application_score" not in payload
    assert "provider_request" not in rendered
    assert "mutation_command" not in rendered
    assert "submission_command" not in rendered


def test_docs_contain_required_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged_by_hash():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_changed_files_are_limited_to_phase35b_surface_and_legacy_guards():
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    allowed = {
        "src/tailoring/llm.py",
        "generate_tailoring_suggestions.py",
        "src/tailoring/rendering.py",
        "tests/test_score_first_scan.py",
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
