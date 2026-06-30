from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess

from src.agents import jd_intelligence_planning_artifact_enricher_default_off as enricher
from src.agents.jd_intelligence_planning_artifact_enricher_default_off import (
    build_jd_intelligence_planning_artifact_enricher_default_off,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "src/agents/jd_intelligence_planning_artifact_enricher_default_off.py"
DOC_PATH = ROOT / "docs/phase34_jd_intelligence_planning_artifact_enricher_default_off.md"

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "jd_intelligence_planning_artifact_enricher",
    "llm_capable",
    "llm_enabled",
    "read_only",
    "advisory_only",
    "requires_manual_user_control",
    "planning_row_count",
    "valid_planning_row_count",
    "invalid_planning_row_count",
    "enriched_rows",
    "unmapped_rows",
    "extraction_results",
    "extraction_ready_count",
    "extraction_blocked_count",
    "provider_callable_present",
    "provider_callable_invocation_count",
    "provider_responses_present",
    "mapper_result",
    "grouped_by_next_allowed_step",
    "next_step_counts",
    "enricher_findings",
    "missing_inputs",
    "enricher_key",
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
    "auto_" + "apply_performed",
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
    "build_live_jd_intelligence_dry_run_payload(",
    "execute_application(",
    "submit_application(",
    "provider_call(",
    "network_call(",
)

DOC_MARKERS = (
    "phase 34b jd intelligence planning artifact enricher default-off",
    "jd intelligence planning artifact enricher",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "llm-capable",
    "default-off",
    "requires explicit `enable_llm=true`",
    "calls the phase 34a jd intelligence llm signal extractor",
    "calls the phase 33d planning artifact mapper",
    "enriches planning-like rows with structured jd intelligence results",
    "supports supplied provider responses",
    "supports an injected provider callable through phase 34a",
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
    "src/agents/jd_intelligence_llm_signal_extractor_default_off.py": "a73124801ce6768aebb934e1c6a7e76d4f9888bbb7b0ca28eb93e882e06f4f6c",
    "src/agents/controlled_agent_router_planning_artifact_mapper_readonly.py": "1966a4d95eaf57b735545efd00e28803bba077192c81668165e9b3f491491fe8",
    "src/agents/controlled_agent_router_batch_handoff_plan_readonly.py": "7824233cbb4c6efd75481a8097a041488adfbd53f7c97e4832c02b8822741834",
    "src/agents/controlled_agent_router_workflow_state_adapter_readonly.py": "4f01b4e58c8e517ec633331da44341ee5596d486ae7d40d38fdca4666d6fa47e",
    "src/agents/controlled_agent_router_readonly.py": "c1cac3d8d1858b5143d0c3ca0082f3b908410020a0e4220c1dea9531cbf3655d",
    "run_controlled_agent_router_planning_artifact_dry_run.py": "1e49a69da5b306272319f2bef5e7162467f294aff4cbe37e8167125a56777dc4",
    "src/app/api.py": "e658b1e05444d7cd2546d3d065cc325045a9d2bb1589b900c18d1aeea0fbd084",
    "src/app/services.py": "4e3ca1a2d9c4e5ea8a459ef29b377ab25b41b8073239e05c2d1de37cd174ce24",
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
    return {
        "required_skills": ["Python"],
        "preferred_skills": ["Airflow"],
        "responsibilities": ["Own workflows"],
        "seniority": "senior",
        "domain": "data platform",
        "tools": ["dbt"],
        "location_constraints": ["Remote"],
        "visa_constraints": [],
        "red_flags": [],
        "resume_evidence_needed": ["Python pipelines"],
        "confidence": 0.9,
    }


def _assert_safe(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "34B"
    assert payload["default_off"] is True
    assert payload["jd_intelligence_planning_artifact_enricher"] is True
    assert payload["llm_capable"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["requires_manual_user_control"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_helper_exists_and_is_import_safe(capsys):
    importlib.reload(enricher)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(build_jd_intelligence_planning_artifact_enricher_default_off)


def test_helper_imports_only_phase34a_and_phase33d_helpers():
    source = HELPER_PATH.read_text(encoding="utf-8")
    assert "build_jd_intelligence_llm_signal_extractor_default_off" in source
    assert "build_controlled_agent_router_planning_artifact_mapper_readonly" in source
    assert "from src.agents.jd_intelligence_llm_signal_extractor_default_off import" in source
    assert "from src.agents.controlled_agent_router_planning_artifact_mapper_readonly import" in source
    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source


def test_missing_and_non_list_planning_rows_return_empty_blocked_result():
    for rows in (None, {"job_id": "j1"}):
        payload = build_jd_intelligence_planning_artifact_enricher_default_off(
            planning_rows=rows
        )
        _assert_safe(payload)
        assert payload["planning_row_count"] == 0
        assert payload["enriched_rows"] == []
        assert payload["missing_inputs"] == ["planning_rows"]
        assert payload["unmapped_rows"][0]["reason"] == (
            "planning_rows must be supplied as a list"
        )


def test_empty_planning_rows_returns_empty_enriched_rows_and_mapper_result():
    payload = build_jd_intelligence_planning_artifact_enricher_default_off(
        planning_rows=[]
    )
    _assert_safe(payload)
    assert payload["planning_row_count"] == 0
    assert payload["enriched_rows"] == []
    assert payload["mapper_result"]["mapped_items"] == []
    assert payload["next_step_counts"] == {}


def test_invalid_non_dict_row_goes_to_unmapped_rows_without_crashing():
    payload = build_jd_intelligence_planning_artifact_enricher_default_off(
        planning_rows=[{"job_id": "j1"}, "bad"]
    )
    _assert_safe(payload)
    assert payload["valid_planning_row_count"] == 1
    assert payload["invalid_planning_row_count"] == 1
    assert payload["unmapped_rows"] == [
        {"input_index": 1, "reason": "planning row must be a dictionary"}
    ]


def test_default_off_does_not_call_provider_callable_or_fake_jd_signals():
    calls = []

    def provider(_packet):
        calls.append(_packet)
        return _signals()

    payload = build_jd_intelligence_planning_artifact_enricher_default_off(
        planning_rows=[
            {
                "job_id": "j1",
                "title": "Data Engineer",
                "job_description": "Python pipelines",
                "relevant": True,
            }
        ],
        provider_callable=provider,
    )
    _assert_safe(payload)
    assert calls == []
    assert payload["provider_callable_invocation_count"] == 0
    assert payload["extraction_ready_count"] == 0
    assert payload["extraction_blocked_count"] == 1
    assert "jd_intelligence_result" not in payload["enriched_rows"][0]
    assert "explicit LLM enable is required" in payload["extraction_results"][0]["blocked_reasons"]
    assert payload["extraction_results"][0]["request_packet"]["jd_text"] == "Python pipelines"


def test_supplied_provider_response_dict_and_list_are_parsed_when_enabled():
    rows = [
        {"item_id": "a", "job_description": "Python", "relevant": True},
        {"job_id": "b", "description": "SQL", "relevant": True},
    ]
    as_dict = build_jd_intelligence_planning_artifact_enricher_default_off(
        planning_rows=rows,
        enable_llm=True,
        provider_responses={"a": _signals(), "b": json.dumps(_signals())},
    )
    as_list = build_jd_intelligence_planning_artifact_enricher_default_off(
        planning_rows=rows,
        enable_llm=True,
        provider_responses=[_signals(), json.dumps(_signals())],
    )
    for payload in (as_dict, as_list):
        _assert_safe(payload)
        assert payload["provider_responses_present"] is True
        assert payload["provider_callable_invocation_count"] == 0
        assert payload["extraction_ready_count"] == 2
        assert all("jd_intelligence_result" in row for row in payload["enriched_rows"])


def test_provider_callable_is_called_through_phase34a_only_when_enabled_and_needed():
    calls = []

    def provider(packet):
        calls.append(packet)
        return _signals()

    rows = [
        {"job_id": "with-response", "posting_text": "Python", "relevant": True},
        {"job_id": "needs-callable", "posting_text": "SQL", "relevant": True},
    ]
    payload = build_jd_intelligence_planning_artifact_enricher_default_off(
        planning_rows=rows,
        enable_llm=True,
        provider_callable=provider,
        provider_responses={"with-response": _signals()},
    )
    _assert_safe(payload)
    assert len(calls) == 1
    assert calls[0]["jd_text"] == "SQL"
    assert payload["provider_callable_invocation_count"] == 1
    assert payload["extraction_ready_count"] == 2


def test_extraction_ready_rows_route_through_phase33d_to_expected_group():
    payload = build_jd_intelligence_planning_artifact_enricher_default_off(
        planning_rows=[
            {
                "job_id": "j1",
                "job_description": "Python",
                "relevant": True,
            }
        ],
        enable_llm=True,
        provider_responses={"j1": _signals()},
    )
    _assert_safe(payload)
    row = payload["enriched_rows"][0]
    assert row["jd_intelligence_result"]["required_skills"] == ["Python"]
    assert row["jd_intelligence"] == row["jd_intelligence_result"]
    assert payload["next_step_counts"] == {"run_final_application_scoring": 1}
    assert "run_final_application_scoring" in payload["grouped_by_next_allowed_step"]


def test_extraction_blocked_rows_do_not_get_fake_jd_intelligence():
    payload = build_jd_intelligence_planning_artifact_enricher_default_off(
        planning_rows=[
            {"job_id": "j1", "job_description": "Python", "relevant": True}
        ],
        enable_llm=True,
    )
    _assert_safe(payload)
    assert payload["extraction_ready_count"] == 0
    assert payload["extraction_blocked_count"] == 1
    assert "jd_intelligence_result" not in payload["enriched_rows"][0]
    assert payload["next_step_counts"] == {"run_jd_intelligence": 1}


def test_input_rows_are_not_mutated():
    rows = [{"job_id": "j1", "job_description": "Python", "relevant": True}]
    before = deepcopy(rows)
    build_jd_intelligence_planning_artifact_enricher_default_off(
        planning_rows=rows,
        enable_llm=True,
        provider_responses={"j1": _signals()},
    )
    assert rows == before


def test_no_generated_tailoring_text_or_real_tailoring_output_appears():
    payload = build_jd_intelligence_planning_artifact_enricher_default_off(
        planning_rows=[
            {"job_id": "j1", "job_description": "Python", "relevant": True}
        ],
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
    assert payload["real_tailoring_output_created"] is False


def test_docs_contain_required_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged_by_hash():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_changed_files_are_limited_to_phase34b_surface_and_legacy_guards():
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    allowed = {
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
