from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import subprocess

from src.agents import (
    controlled_agent_router_batch_handoff_plan_readonly as batch_planner,
)
from src.agents.controlled_agent_router_batch_handoff_plan_readonly import (
    build_controlled_agent_router_batch_handoff_plan_readonly,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT / "src/agents/controlled_agent_router_batch_handoff_plan_readonly.py"
)
DOC_PATH = (
    ROOT / "docs/phase33_controlled_agent_router_batch_handoff_plan_readonly.md"
)

ALLOWED_STEPS = {
    "run_relevance_prefilter",
    "run_jd_intelligence",
    "run_final_application_scoring",
    "check_tailoring_opportunity",
    "prepare_manual_tailoring_preview",
    "await_manual_review",
}

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "read_only",
    "advisory_only",
    "batch_handoff_plan_only",
    "controlled_agent_router_batch_plan",
    "allowlisted_routing_only",
    "requires_manual_user_control",
    "item_count",
    "valid_item_count",
    "invalid_item_count",
    "batch_items",
    "handoff_plan",
    "grouped_by_next_allowed_step",
    "routing_summary",
    "next_step_counts",
    "blocked_items",
    "missing_inputs",
    "batch_plan_key",
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

TRUE_SAFETY_KEYS = {
    "default_off",
    "read_only",
    "advisory_only",
    "batch_handoff_plan_only",
    "controlled_agent_router_batch_plan",
    "allowlisted_routing_only",
    "requires_manual_user_control",
    "no_llm_calls",
    "no_provider_calls",
    "no_network_calls",
}

FALSE_ACTION_KEYS = {
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
    "database_url",
    "psycopg",
    "sqlite",
    "subprocess",
    "requests",
    "httpx",
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

DOC_MARKERS = (
    "phase 33c controlled agent router batch handoff plan read-only",
    "controlled agent router batch handoff plan",
    "capability step on the revised path",
    "not another safety-wrapper chain",
    "accepts supplied job/workflow artifact bundles",
    "calls the phase 33b workflow state adapter for each valid item",
    "groups items by next allowed agent step",
    "returns a deterministic batch handoff plan",
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
    "phase33b-controlled-agent-router-workflow-state-adapter-readonly-v1",
    "phase33a-controlled-agent-router-readonly-v1",
    "phase32b-manual-generate-ai-tailoring-preview-normalized-response-preview-packet-api-readback-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/controlled_agent_router_readonly.py": "c1cac3d8d1858b5143d0c3ca0082f3b908410020a0e4220c1dea9531cbf3655d",
    "src/agents/controlled_agent_router_workflow_state_adapter_readonly.py": "4f01b4e58c8e517ec633331da44341ee5596d486ae7d40d38fdca4666d6fa47e",
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


def _assert_safe_payload(payload: dict) -> None:
    assert REQUIRED_KEYS <= payload.keys()
    assert payload["phase"] == "33C"
    for key in TRUE_SAFETY_KEYS:
        assert payload[key] is True
    for key in FALSE_ACTION_KEYS:
        assert payload[key] is False
    for planned in payload["handoff_plan"]:
        assert planned["next_allowed_step"] in ALLOWED_STEPS
        assert planned["non_executable"] is True
        assert planned["no_executable_callback"] is True
        assert planned["no_provider_request"] is True
        assert planned["no_network_request"] is True
        assert planned["no_mutation_command"] is True
        assert planned["no_database_write_command"] is True
        assert planned["no_application_submission_command"] is True


def _plan(items=None, policy=None) -> dict:
    payload = build_controlled_agent_router_batch_handoff_plan_readonly(
        items=items,
        router_policy=policy,
    )
    _assert_safe_payload(payload)
    return payload


def test_helper_exists_and_calls_phase33b_adapter(monkeypatch):
    calls = []

    def fake_adapter(**kwargs):
        calls.append(kwargs)
        return {
            "next_allowed_step": "run_relevance_prefilter",
            "handoff_reason": "fake adapter",
            "agent_handoff_packet": {
                "next_allowed_step": "run_relevance_prefilter",
                "allowed_agent_steps": ["run_relevance_prefilter"],
                "blocked_agent_steps": ["call_llm"],
                "non_executable": True,
            },
            "required_inputs_for_next_step": ["job_record"],
            "available_inputs_for_next_step": ["job_record"],
            "missing_inputs_for_next_step": [],
            "adapter_key": "fake",
        }

    monkeypatch.setattr(
        batch_planner,
        "build_controlled_agent_router_workflow_state_adapter_readonly",
        fake_adapter,
    )

    payload = _plan(
        items=[{"item_id": "a", "job_record": {"job_id": "job-1"}}],
        policy={"threshold": 80},
    )

    assert callable(build_controlled_agent_router_batch_handoff_plan_readonly)
    assert calls == [
        {
            "job_record": {"job_id": "job-1"},
            "relevance_result": None,
            "jd_intelligence_result": None,
            "final_score_result": None,
            "tailoring_opportunity_result": None,
            "manual_tailoring_preview_result": None,
            "router_policy": {"threshold": 80},
        }
    ]
    assert payload["next_step_counts"] == {"run_relevance_prefilter": 1}


def test_missing_items_returns_empty_plan_with_missing_reason():
    payload = _plan()

    assert payload["item_count"] == 0
    assert payload["valid_item_count"] == 0
    assert payload["missing_inputs"] == ["items"]
    assert payload["blocked_items"][0]["reason"] == (
        "items must be supplied as a list"
    )


def test_non_list_items_returns_empty_plan_with_missing_reason():
    payload = _plan(items={"job_record": {"job_id": "job-1"}})

    assert payload["item_count"] == 0
    assert payload["missing_inputs"] == ["items"]
    assert payload["handoff_plan"] == []


def test_empty_list_returns_empty_plan_with_zero_count():
    payload = _plan(items=[])

    assert payload["item_count"] == 0
    assert payload["valid_item_count"] == 0
    assert payload["invalid_item_count"] == 0
    assert payload["grouped_by_next_allowed_step"] == {}


def test_invalid_items_are_blocked_without_crashing():
    payload = _plan(items=[{"job_record": {"job_id": "job-1"}}, "bad", 42])

    assert payload["item_count"] == 3
    assert payload["valid_item_count"] == 1
    assert payload["invalid_item_count"] == 2
    assert [item["input_index"] for item in payload["blocked_items"]] == [1, 2]
    assert all(
        item["reason"] == "item must be a dictionary"
        for item in payload["blocked_items"]
    )


def test_routes_all_supported_next_steps_into_deterministic_groups():
    items = [
        {"item_id": "job-only", "job_record": {"job_id": "job-1"}},
        {
            "item_id": "needs-jd",
            "job_record": {"job_id": "job-2"},
            "relevance_result": {"relevant": True},
        },
        {
            "item_id": "needs-score",
            "job_record": {"job_id": "job-3"},
            "relevance_result": {"relevant": True},
            "jd_intelligence_result": {"signals": ["python"]},
        },
        {
            "item_id": "needs-tailoring-check",
            "job_record": {"job_id": "job-4"},
            "relevance_result": {"relevant": True},
            "jd_intelligence_result": {"signals": ["python"]},
            "final_score_result": {"score": 90},
        },
        {
            "item_id": "needs-preview",
            "job_record": {"job_id": "job-5"},
            "relevance_result": {"relevant": True},
            "jd_intelligence_result": {"signals": ["python"]},
            "final_score_result": {"score": 90},
            "tailoring_opportunity_result": {"tailoring_may_help": True},
        },
        {
            "item_id": "manual-review",
            "job_record": {"job_id": "job-6"},
            "relevance_result": {"relevant": True},
            "jd_intelligence_result": {"signals": ["python"]},
            "final_score_result": {"score": 90},
            "tailoring_opportunity_result": {"tailoring_does_not_help": True},
        },
    ]

    payload = _plan(items=items)

    assert payload["valid_item_count"] == 6
    assert list(payload["next_step_counts"]) == [
        "run_relevance_prefilter",
        "run_jd_intelligence",
        "run_final_application_scoring",
        "check_tailoring_opportunity",
        "prepare_manual_tailoring_preview",
        "await_manual_review",
    ]
    assert payload["next_step_counts"] == {
        "run_relevance_prefilter": 1,
        "run_jd_intelligence": 1,
        "run_final_application_scoring": 1,
        "check_tailoring_opportunity": 1,
        "prepare_manual_tailoring_preview": 1,
        "await_manual_review": 1,
    }
    assert [
        item["item_id"] for item in payload["grouped_by_next_allowed_step"][
            "run_relevance_prefilter"
        ]
    ] == ["job-only"]
    assert [
        item["item_id"] for item in payload["handoff_plan"]
    ] == [item["item_id"] for item in items]


def test_plan_excludes_generated_tailoring_text_and_real_outputs():
    payload = _plan(
        items=[
            {
                "item_id": "safe-preview",
                "job_record": {"job_id": "job-1"},
                "relevance_result": {"relevant": True},
                "jd_intelligence_result": {"signals": ["python"]},
                "final_score_result": {"score": 90},
                "tailoring_opportunity_result": {"tailoring_may_help": True},
                "manual_tailoring_preview_result": {
                    "preview_id": "preview-1",
                    "generated_tailoring_text": "generated secret text",
                    "real_tailoring_output": "real generated output",
                },
            }
        ]
    )

    rendered = str(payload).lower()
    assert "generated secret text" not in rendered
    assert "real generated output" not in rendered


def test_source_has_only_phase33b_adapter_import_and_no_forbidden_calls():
    source = HELPER_PATH.read_text(encoding="utf-8")

    assert "build_controlled_agent_router_workflow_state_adapter_readonly" in source
    for marker in FORBIDDEN_SOURCE_MARKERS:
        assert marker not in source


def test_docs_contain_required_markers_and_references():
    doc = DOC_PATH.read_text(encoding="utf-8").lower()

    for marker in DOC_MARKERS:
        assert marker in doc


def test_protected_runtime_files_are_unchanged_by_hash():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert _sha256(ROOT / relative_path) == expected_hash


def test_changed_files_are_limited_to_phase33c_surface_and_legacy_guards():
    result = subprocess.run(
        ["git", "status", "--short"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    allowed_changed = {
        "src/agents/controlled_agent_router_batch_handoff_plan_readonly.py",
        "docs/phase33_controlled_agent_router_batch_handoff_plan_readonly.md",
        "tests/test_phase33c_controlled_agent_router_batch_handoff_plan_readonly.py",
        "src/agents/controlled_agent_router_planning_artifact_mapper_readonly.py",
        "docs/phase33_controlled_agent_router_planning_artifact_mapper_readonly.md",
        "tests/test_phase33d_controlled_agent_router_planning_artifact_mapper_readonly.py",
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
        "tests/test_phase42a_exact_resume_change_set_proposal_builder_default_off.py",
        "run_jd_evidence_score_impact_review_queue_builder_dry_run.py",
        "docs/phase41_jd_evidence_score_impact_review_queue_builder_dry_run_command_default_off.md",
        "tests/test_phase41b_jd_evidence_score_impact_review_queue_builder_dry_run_command_default_off.py",
        "tests/test_phase41a_jd_evidence_score_impact_review_queue_builder_default_off.py",
    }
    for line in result.stdout.splitlines():
        path = line[3:].strip().strip('"')
        if path.startswith("tests/test_") and path.endswith(".py"):
            continue
        assert path in allowed_changed
