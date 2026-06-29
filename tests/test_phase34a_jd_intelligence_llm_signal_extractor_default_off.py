from __future__ import annotations

from hashlib import sha256
import importlib
import json
from pathlib import Path
import subprocess

from src.agents import jd_intelligence_llm_signal_extractor_default_off as extractor
from src.agents.jd_intelligence_llm_signal_extractor_default_off import (
    build_jd_intelligence_llm_signal_extractor_default_off,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "src/agents/jd_intelligence_llm_signal_extractor_default_off.py"
DOC_PATH = ROOT / "docs/phase34_jd_intelligence_llm_signal_extractor_default_off.md"

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "jd_intelligence_llm_signal_extractor",
    "llm_capable",
    "llm_enabled",
    "read_only",
    "advisory_only",
    "requires_manual_user_control",
    "jd_text_present",
    "job_record_present",
    "request_packet",
    "provider_response_present",
    "provider_callable_present",
    "provider_callable_invoked",
    "provider_response_parse_status",
    "jd_signals",
    "required_skills",
    "preferred_skills",
    "responsibilities",
    "seniority",
    "domain",
    "tools",
    "location_constraints",
    "visa_constraints",
    "red_flags",
    "resume_evidence_needed",
    "confidence",
    "extraction_ready",
    "extraction_source",
    "missing_inputs",
    "blocked_reasons",
    "extractor_findings",
    "extractor_key",
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
    "phase 34a jd intelligence llm signal extractor default-off",
    "jd intelligence llm signal extractor",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "llm-capable",
    "default-off",
    "requires explicit `enable_llm=true`",
    "supports an injected provider callable",
    "supports supplied provider response parsing",
    "builds structured jd intelligence signals",
    "required skills",
    "preferred skills",
    "responsibilities",
    "seniority",
    "domain",
    "tools",
    "location constraints",
    "visa constraints",
    "red flags",
    "resume evidence needed",
    "confidence",
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
    "phase33e-controlled-agent-router-planning-artifact-dry-run-command-readonly-v1",
    "phase33d-controlled-agent-router-planning-artifact-mapper-readonly-v1",
    "phase33c-controlled-agent-router-batch-handoff-plan-readonly-v1",
    "phase33b-controlled-agent-router-workflow-state-adapter-readonly-v1",
    "phase33a-controlled-agent-router-readonly-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/controlled_agent_router_readonly.py": "c1cac3d8d1858b5143d0c3ca0082f3b908410020a0e4220c1dea9531cbf3655d",
    "src/agents/controlled_agent_router_workflow_state_adapter_readonly.py": "4f01b4e58c8e517ec633331da44341ee5596d486ae7d40d38fdca4666d6fa47e",
    "src/agents/controlled_agent_router_batch_handoff_plan_readonly.py": "7824233cbb4c6efd75481a8097a041488adfbd53f7c97e4832c02b8822741834",
    "src/agents/controlled_agent_router_planning_artifact_mapper_readonly.py": "1966a4d95eaf57b735545efd00e28803bba077192c81668165e9b3f491491fe8",
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


def _assert_safe(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "34A"
    assert payload["default_off"] is True
    assert payload["jd_intelligence_llm_signal_extractor"] is True
    assert payload["llm_capable"] is True
    assert payload["read_only"] is True
    assert payload["advisory_only"] is True
    assert payload["requires_manual_user_control"] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def _sample_response() -> dict:
    return {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": ["Airflow"],
        "responsibilities": ["Own data workflows"],
        "seniority": "senior",
        "domain": "data platform",
        "tools": ["dbt"],
        "location_constraints": ["US remote"],
        "visa_constraints": ["No sponsorship"],
        "red_flags": ["Ambiguous on-call"],
        "resume_evidence_needed": ["Python pipeline ownership"],
        "confidence": 0.82,
    }


def test_helper_exists_and_is_import_safe(capsys):
    importlib.reload(extractor)
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    assert callable(build_jd_intelligence_llm_signal_extractor_default_off)


def test_missing_jd_text_blocks_with_missing_input_reason():
    payload = build_jd_intelligence_llm_signal_extractor_default_off(
        jd_text="",
        enable_llm=True,
        provider_response=_sample_response(),
    )
    _assert_safe(payload)
    assert payload["extraction_ready"] is False
    assert payload["missing_inputs"] == ["jd_text"]
    assert "jd_text is required" in payload["blocked_reasons"]
    assert payload["provider_callable_invoked"] is False


def test_default_off_does_not_call_provider_callable_and_returns_request_packet():
    calls = []

    def provider(_packet):
        calls.append(_packet)
        return _sample_response()

    payload = build_jd_intelligence_llm_signal_extractor_default_off(
        jd_text="Build Python data workflows.",
        job_record={"title": "Data Engineer"},
        enable_llm=False,
        provider_callable=provider,
    )
    _assert_safe(payload)
    assert calls == []
    assert payload["llm_enabled"] is False
    assert payload["provider_callable_present"] is True
    assert payload["provider_callable_invoked"] is False
    assert payload["request_packet"]["prompt_version"]
    assert "explicit LLM enable is required" in payload["blocked_reasons"]


def test_supplied_provider_response_dictionary_is_parsed_when_enabled():
    payload = build_jd_intelligence_llm_signal_extractor_default_off(
        jd_text="Build Python data workflows.",
        enable_llm=True,
        provider_response=_sample_response(),
    )
    _assert_safe(payload)
    assert payload["extraction_ready"] is True
    assert payload["extraction_source"] == "provider_response"
    assert payload["provider_response_parse_status"] == "parsed"
    assert payload["required_skills"] == ["Python", "SQL"]
    assert payload["preferred_skills"] == ["Airflow"]
    assert payload["responsibilities"] == ["Own data workflows"]
    assert payload["seniority"] == "senior"
    assert payload["domain"] == "data platform"
    assert payload["tools"] == ["dbt"]
    assert payload["location_constraints"] == ["US remote"]
    assert payload["visa_constraints"] == ["No sponsorship"]
    assert payload["red_flags"] == ["Ambiguous on-call"]
    assert payload["resume_evidence_needed"] == ["Python pipeline ownership"]
    assert payload["confidence"] == 0.82


def test_supplied_provider_response_json_string_is_parsed_when_enabled():
    payload = build_jd_intelligence_llm_signal_extractor_default_off(
        jd_text="Build Python data workflows.",
        enable_llm=True,
        provider_response=json.dumps(_sample_response()),
    )
    _assert_safe(payload)
    assert payload["provider_response_parse_status"] == "parsed"
    assert payload["required_skills"] == ["Python", "SQL"]


def test_supplied_provider_response_plain_text_containing_json_is_parsed_when_enabled():
    payload = build_jd_intelligence_llm_signal_extractor_default_off(
        jd_text="Build Python data workflows.",
        enable_llm=True,
        provider_response=f"Here is the JSON:\n{json.dumps(_sample_response())}\nDone.",
    )
    _assert_safe(payload)
    assert payload["provider_response_parse_status"] == "parsed"
    assert payload["tools"] == ["dbt"]


def test_provider_callable_is_called_exactly_once_when_enabled():
    calls = []

    def provider(packet):
        calls.append(packet)
        return _sample_response()

    payload = build_jd_intelligence_llm_signal_extractor_default_off(
        jd_text="Build Python data workflows.",
        job_record={"company": "ExampleCo"},
        enable_llm=True,
        provider_callable=provider,
        extraction_policy={"max_items_per_field": 8},
    )
    _assert_safe(payload)
    assert len(calls) == 1
    assert calls[0]["phase"] == "34A"
    assert calls[0]["job_record"] == {"company": "ExampleCo"}
    assert calls[0]["extraction_policy"] == {"max_items_per_field": 8}
    assert payload["provider_callable_invoked"] is True
    assert payload["extraction_source"] == "provider_callable"


def test_missing_fields_normalize_to_empty_lists_or_none_without_crashing():
    payload = build_jd_intelligence_llm_signal_extractor_default_off(
        jd_text="General role.",
        enable_llm=True,
        provider_response={"required_skills": "Python"},
    )
    _assert_safe(payload)
    assert payload["required_skills"] == ["Python"]
    assert payload["preferred_skills"] == []
    assert payload["responsibilities"] == []
    assert payload["seniority"] is None
    assert payload["domain"] is None
    assert payload["tools"] == []
    assert payload["location_constraints"] == []
    assert payload["visa_constraints"] == []
    assert payload["red_flags"] == []
    assert payload["resume_evidence_needed"] == []
    assert payload["confidence"] is None


def test_no_generated_tailoring_text_or_real_tailoring_output_appears():
    payload = build_jd_intelligence_llm_signal_extractor_default_off(
        jd_text="Role text.",
        enable_llm=True,
        provider_response={
            **_sample_response(),
            "generated_tailoring_text": "do not surface",
            "real_tailoring_output": "do not surface",
        },
    )
    rendered = json.dumps(payload).lower()
    assert "do not surface" not in rendered
    assert payload["real_tailoring_output_created"] is False
    assert payload["ai_tailoring_generation_performed"] is False


def test_source_has_no_forbidden_imports_or_runtime_calls():
    source = HELPER_PATH.read_text(encoding="utf-8").lower()
    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker.lower() not in source


def test_docs_contain_required_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_files_are_unchanged_by_hash():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected


def test_changed_files_are_limited_to_phase34a_surface_and_legacy_guards():
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    changed = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    allowed = {
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
