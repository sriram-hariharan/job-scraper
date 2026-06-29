from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
from pathlib import Path

from src.agents import exact_resume_change_set_proposal_builder_default_off as builder
from src.agents.exact_resume_change_set_proposal_builder_default_off import (
    build_exact_resume_change_set_proposal_builder_default_off,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = ROOT / "src/agents/exact_resume_change_set_proposal_builder_default_off.py"
DOC_PATH = ROOT / "docs/phase42_exact_resume_change_set_proposal_builder_default_off.md"

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "exact_resume_change_set_proposal_builder",
    "read_only",
    "advisory_only",
    "proposal_only",
    "exact_worthy_changes_only",
    "manual_review_required",
    "requires_manual_user_control",
    "review_queue_present",
    "review_queue_count",
    "valid_review_queue_item_count",
    "invalid_review_queue_item_count",
    "resume_context_present",
    "jd_context_present",
    "tailoring_context_present",
    "proposal_policy",
    "change_proposals",
    "change_proposals_by_type",
    "change_set_summary",
    "proposal_findings",
    "missing_inputs",
    "proposal_key",
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
    "review_packet_building_performed",
    "review_queue_building_performed",
    "final_scoring_performed",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "application_submission_performed",
    "submission_performed",
    "auto_apply_performed",
    "auto_submit_performed",
}

FALSE_ACTION_KEYS = {
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
    "review_packet_building_performed",
    "review_queue_building_performed",
    "final_scoring_performed",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "application_submission_performed",
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
    "run_chat_completion",
    "build_jd_evidence_score_impact_review_queue_builder_default_off(",
    "build_jd_evidence_score_impact_review_packet_builder_default_off(",
    "build_jd_evidence_score_impact_preview_default_off(",
    "build_jd_evidence_scoring_contribution_preview_default_off(",
    "build_final_replacement_plan(",
    "execute_application(",
    "submit_application(",
    "overwrite_resume(",
    "mutate_resume(",
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
    "phase 42a exact resume change-set proposal builder default-off",
    "exact resume change-set proposal builder",
    "starts the exact worthy resume change path after the review queue",
    "not another safety-wrapper chain",
    "produces exact worthy resume change proposals",
    "supplied review queue, resume context, jd context, and tailoring context",
    "proposal-only before/after changes",
    "does not produce a full resume",
    "does not overwrite resumes",
    "does not mutate resumes",
    "does not call llm",
    "does not call provider",
    "does not call network",
    "does not call tailoring runtime",
    "does not generate real tailoring output",
    "does not produce final application score",
    "does not change scoring logic",
    "does not call matching/scoring modules",
    "does not persist data",
    "does not write to database",
    "does not execute applications",
    "does not submit applications",
    "no auto-apply",
    "no auto-submit",
    "manual user control remains required",
    "existing ui/manual control remains the acceptance point",
    "exact worthy changes must be manually accepted by the user",
    "resume overwrite is not needed",
    "application execution is not needed",
    "phase41-jd-evidence-score-impact-review-queue-builder-release-v1",
    "phase41b-jd-evidence-score-impact-review-queue-builder-dry-run-command-default-off-v1",
    "phase41a-jd-evidence-score-impact-review-queue-builder-default-off-v1",
    "phase40-jd-evidence-score-impact-review-packet-builder-release-v1",
    "phase39-jd-evidence-score-impact-planning-artifact-annotator-release-v1",
    "phase38-jd-evidence-score-impact-preview-release-v1",
    "phase37-jd-evidence-scoring-contribution-preview-release-v1",
    "phase36-jd-evidence-final-scoring-feature-adapter-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/jd_evidence_score_impact_review_queue_builder_default_off.py": "c3080e881850ec75472e1e57727829db2866236139a84cc29a3ecd2ebe7ef6df",
    "run_jd_evidence_score_impact_review_queue_builder_dry_run.py": "77e2e06b1c99433f832c6b3a238f26c662ae8a382874500f33087aed8fdcdfab",
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
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_suggestions.py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _queue_item(**overrides):
    item = {
        "item_id": "queue-1",
        "job_id": "job-1",
        "title": "Senior Data Scientist",
        "company": "ExampleCo",
        "score_impact_review_recommendation": "manual_review",
    }
    for key, value in overrides.items():
        item[key] = value
    return item


def _resume_context():
    return {
        "profile_summary": "Data scientist with experimentation and SQL analytics experience.",
        "skills": ["Python", "SQL", "Experimentation"],
        "resume_bullets": [
            {
                "id": "b1",
                "text": "Built Python forecasting models and SQL dashboards for marketplace analytics.",
            },
            {
                "id": "b2",
                "text": "Designed experimentation readouts for product teams.",
            },
        ],
        "projects": [
            {
                "name": "Forecasting Lab",
                "description": "Python forecasting project with stakeholder reporting.",
            }
        ],
    }


def _jd_context():
    return {
        "required_skills": ["Python", "SQL"],
        "preferred_skills": ["Experimentation"],
        "tools": ["Tableau"],
        "responsibilities": ["forecasting"],
        "domain": "marketplace analytics",
    }


def _tailoring_context():
    return {
        "matched_required_skills": ["Python", "SQL"],
        "matched_tools": [],
        "missing_tools": ["Tableau"],
        "missing_required_skills": [],
        "evidence_matrix": [
            {"term": "Python", "evidence": "Python forecasting models"},
            {"term": "SQL", "evidence": "SQL dashboards"},
        ],
        "suggested_focus": ["forecasting"],
    }


def test_helper_exists_and_is_import_safe():
    module = importlib.reload(builder)
    assert callable(module.build_exact_resume_change_set_proposal_builder_default_off)


def test_missing_review_queue_blocks_with_missing_input_reason():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
    )

    assert REQUIRED_KEYS.issubset(payload)
    assert payload["phase"] == "42A"
    assert payload["review_queue_present"] is False
    assert "review_queue" in payload["missing_inputs"]
    assert payload["change_set_summary"]["proposal_blocked"] is True


def test_queue_result_with_review_queue_is_accepted():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        queue_result={"review_queue": [_queue_item()]},
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
    )

    assert payload["review_queue_present"] is True
    assert payload["proposal_findings"]["review_queue_source"] == "queue_result.review_queue"
    assert payload["change_proposals"]


def test_nested_queue_result_review_queue_is_accepted():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        queue_result={"queue_result": {"review_queue": [_queue_item(item_id="nested")]}},
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
    )

    assert payload["proposal_findings"]["review_queue_source"] == "queue_result.queue_result.review_queue"
    assert payload["change_proposals"][0]["item_id"] == "nested"


def test_flattened_review_queue_by_priority_is_accepted():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        queue_result={"review_queue_by_priority": {"90": [_queue_item(item_id="p90")]}},
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
    )

    assert payload["proposal_findings"]["review_queue_source"] == "queue_result.review_queue_by_priority"
    assert payload["change_proposals"][0]["item_id"] == "p90"


def test_explicit_review_queue_takes_precedence_over_queue_result():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=[_queue_item(item_id="explicit")],
        queue_result={"review_queue": [_queue_item(item_id="ignored")]},
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
    )

    assert payload["proposal_findings"]["review_queue_source"] == "review_queue"
    assert payload["change_proposals"][0]["item_id"] == "explicit"


def test_invalid_non_dict_queue_items_are_counted_without_crashing():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=[_queue_item(), "bad"],
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
    )

    assert payload["review_queue_count"] == 2
    assert payload["valid_review_queue_item_count"] == 1
    assert payload["invalid_review_queue_item_count"] == 1
    assert payload["proposal_findings"]["invalid_review_queue_items"][0]["input_index"] == 1


def test_inputs_are_not_mutated():
    queue = [_queue_item()]
    resume = _resume_context()
    jd = _jd_context()
    tailoring = _tailoring_context()
    snapshots = (deepcopy(queue), deepcopy(resume), deepcopy(jd), deepcopy(tailoring))

    build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=queue,
        resume_context=resume,
        jd_context=jd,
        tailoring_context=tailoring,
    )

    assert queue == snapshots[0]
    assert resume == snapshots[1]
    assert jd == snapshots[2]
    assert tailoring == snapshots[3]


def test_no_proposals_when_required_evidence_is_missing_and_no_missing_terms():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=[_queue_item()],
        resume_context={"skills": ["Python"]},
        jd_context={"required_skills": ["Kubernetes"]},
        tailoring_context={"matched_required_skills": []},
        proposal_policy={"require_source_evidence": True},
    )

    assert payload["change_proposals"] == []
    assert payload["change_set_summary"]["proposal_blocked"] is True


def test_evidence_note_created_for_missing_jd_terms_without_resume_evidence():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=[_queue_item()],
        resume_context={"skills": ["Python"]},
        jd_context={"tools": ["Tableau"]},
        tailoring_context={"missing_tools": ["Tableau"]},
    )

    proposal = payload["change_proposals"][0]
    assert proposal["change_type"] == "evidence_note"
    assert proposal["risk_flags"] == ["missing_source_evidence"]
    assert "Tableau" in proposal["proposed_text"]


def test_skill_proposals_are_created_only_when_resume_evidence_supports_skill():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=[_queue_item()],
        resume_context=_resume_context(),
        jd_context={"required_skills": ["Python"]},
        tailoring_context={"matched_required_skills": ["Python"]},
        proposal_policy={"allow_bullet_changes": False, "allow_summary_changes": False},
    )

    proposal = payload["change_proposals"][0]
    assert proposal["change_type"] == "skill"
    assert "Python" in proposal["jd_terms_supported"]
    assert proposal["resume_evidence_used"]


def test_bullet_proposals_are_created_only_from_supplied_existing_bullet_evidence():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=[_queue_item()],
        resume_context=_resume_context(),
        jd_context={"responsibilities": ["forecasting"]},
        tailoring_context={"suggested_focus": ["forecasting"]},
        proposal_policy={
            "allow_skill_changes": False,
            "allow_summary_changes": False,
            "allow_project_changes": False,
        },
    )

    proposal = payload["change_proposals"][0]
    assert proposal["change_type"] == "bullet"
    assert proposal["target_identifier"] == "b1"
    assert "Built Python forecasting models" in proposal["current_text"]


def test_summary_proposals_are_created_only_when_allowed():
    blocked = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=[_queue_item()],
        resume_context=_resume_context(),
        jd_context={"preferred_skills": ["experimentation"]},
        tailoring_context={"matched_required_skills": ["experimentation"]},
        proposal_policy={
            "allow_skill_changes": False,
            "allow_bullet_changes": False,
            "allow_summary_changes": False,
            "allow_project_changes": False,
        },
    )
    allowed = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=[_queue_item()],
        resume_context=_resume_context(),
        jd_context={"preferred_skills": ["experimentation"]},
        tailoring_context={"matched_required_skills": ["experimentation"]},
        proposal_policy={
            "allow_skill_changes": False,
            "allow_bullet_changes": False,
            "allow_project_changes": False,
        },
    )

    assert blocked["change_proposals"] == []
    assert allowed["change_proposals"][0]["change_type"] == "summary"


def test_project_proposals_are_created_only_when_allowed_and_supported():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=[_queue_item()],
        resume_context=_resume_context(),
        jd_context={"responsibilities": ["stakeholder reporting"]},
        tailoring_context={"suggested_focus": ["stakeholder reporting"]},
        proposal_policy={
            "allow_skill_changes": False,
            "allow_bullet_changes": False,
            "allow_summary_changes": False,
        },
    )

    assert payload["change_proposals"][0]["change_type"] == "project"
    assert payload["change_proposals"][0]["target_section"] == "projects"


def test_max_change_proposals_truncates_deterministically():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=[_queue_item(), _queue_item(item_id="queue-2")],
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
        proposal_policy={"max_change_proposals": 2},
    )

    assert len(payload["change_proposals"]) == 2
    assert [row["proposal_id"] for row in payload["change_proposals"]] == [
        "phase42a-001",
        "phase42a-002",
    ]


def test_max_changes_per_queue_item_is_respected():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=[_queue_item(), _queue_item(item_id="queue-2")],
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
        proposal_policy={"max_changes_per_queue_item": 1, "max_change_proposals": 10},
    )

    assert len(payload["change_proposals"]) == 2
    assert payload["change_proposals"][0]["item_id"] == "queue-1"
    assert payload["change_proposals"][1]["item_id"] == "queue-2"


def test_before_after_text_can_be_omitted_by_policy():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=[_queue_item()],
        resume_context=_resume_context(),
        jd_context={"required_skills": ["Python"]},
        tailoring_context={"matched_required_skills": ["Python"]},
        proposal_policy={"include_before_after_text": False},
    )

    proposal = payload["change_proposals"][0]
    assert proposal["current_text"] == ""
    assert proposal["proposed_text"] == ""


def test_proposals_require_manual_review_and_user_acceptance():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=[_queue_item()],
        resume_context=_resume_context(),
        jd_context={"required_skills": ["Python"]},
        tailoring_context={"matched_required_skills": ["Python"]},
    )

    for proposal in payload["change_proposals"]:
        assert proposal["manual_review_required"] is True
        assert proposal["requires_user_acceptance"] is True
        assert proposal["resume_overwrite_performed"] is False
        assert proposal["resume_mutation_performed"] is False
        assert proposal["application_submission_performed"] is False


def test_no_runtime_side_effect_flags_and_no_full_resume_output():
    payload = build_exact_resume_change_set_proposal_builder_default_off(
        review_queue=[_queue_item()],
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
    )

    assert payload["resume_change_proposals_created"] is True
    assert payload["change_set_summary"]["full_resume_produced"] is False
    assert "full_resume" not in payload
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False


def test_source_has_no_forbidden_imports_calls_or_writes():
    source = HELPER_PATH.read_text(encoding="utf-8")
    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source
    for marker in FORBIDDEN_WRITE_MARKERS:
        assert marker not in source


def test_docs_include_required_markers_and_references():
    text = DOC_PATH.read_text(encoding="utf-8").lower()
    for marker in DOC_MARKERS:
        assert marker in text


def test_protected_runtime_hashes_unchanged():
    for relative, expected in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative) == expected, relative


def test_changed_files_are_limited_to_phase42a_and_legacy_guards():
    allowed = {
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
    }
    legacy_guards = {
        path
        for path in _changed_files()
        if path.startswith("tests/test_") and path.endswith(".py")
    }
    assert _changed_files() <= allowed | legacy_guards


def _changed_files() -> set[str]:
    import subprocess

    result = subprocess.run(
        ["git", "diff", "--name-only"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}
