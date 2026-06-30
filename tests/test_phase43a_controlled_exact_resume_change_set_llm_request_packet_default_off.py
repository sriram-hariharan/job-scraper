from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
import importlib
from pathlib import Path

from src.agents import (
    controlled_exact_resume_change_set_llm_request_packet_default_off as packet_builder,
)
from src.agents.controlled_exact_resume_change_set_llm_request_packet_default_off import (
    build_controlled_exact_resume_change_set_llm_request_packet_default_off,
)


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT / "src/agents/controlled_exact_resume_change_set_llm_request_packet_default_off.py"
)
DOC_PATH = (
    ROOT / "docs/phase43_controlled_exact_resume_change_set_llm_request_packet_default_off.md"
)

FALSE_ACTION_KEYS = {
    "llm_call_performed",
    "provider_call_performed",
    "network_call_performed",
    "tailoring_runtime_call_performed",
    "ai_tailoring_generation_performed",
    "real_tailoring_output_created",
    "resume_change_proposals_created",
    "resume_rewrite_performed",
    "resume_overwrite_performed",
    "resume_mutation_performed",
    "final_score_produced",
    "existing_score_changed",
    "matching_scoring_module_called",
    "database_write_performed",
    "persistence_performed",
    "execution_performed",
    "application_submission_performed",
    "submission_performed",
    "auto_apply_performed",
    "auto_submit_performed",
}

REQUIRED_KEYS = {
    "phase",
    "default_off",
    "controlled_exact_resume_change_set_llm_request_packet",
    "read_only",
    "advisory_only",
    "proposal_only",
    "llm_request_packet_only",
    "provider_request_packet_only",
    "exact_worthy_changes_only",
    "manual_review_required",
    "requires_manual_user_control",
    "manual_trigger_required",
    "change_proposals_present",
    "change_proposal_count",
    "valid_change_proposal_count",
    "invalid_change_proposal_count",
    "resume_context_present",
    "jd_context_present",
    "tailoring_context_present",
    "request_policy",
    "request_packet",
    "request_messages",
    "request_schema",
    "request_packet_summary",
    "request_findings",
    "missing_inputs",
    "request_key",
    "llm_request_packet_created",
    "provider_dispatch_ready",
} | FALSE_ACTION_KEYS

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
    "build_final_replacement_plan(",
    "submit_application(",
    "execute_application(",
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
    "phase 43a controlled exact resume change-set llm request packet default-off",
    "controlled exact resume change-set llm request packet",
    "first llm-facing step for exact worthy resume changes after phase 42",
    "not another review-only queue phase",
    "creates a provider-ready request packet",
    "does not call llm",
    "does not call provider",
    "does not call network",
    "does not call tailoring runtime",
    "does not generate real tailoring output",
    "does not produce a full resume",
    "does not overwrite resumes",
    "does not mutate resumes",
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
    "provider dispatch is prepared but not executed",
    "llm call comes in a later controlled provider-call phase",
    "phase42-exact-resume-change-set-proposal-builder-release-v1",
    "phase42b-exact-resume-change-set-proposal-builder-dry-run-command-default-off-v1",
    "phase42a-exact-resume-change-set-proposal-builder-default-off-v1",
    "phase41-jd-evidence-score-impact-review-queue-builder-release-v1",
    "phase40-jd-evidence-score-impact-review-packet-builder-release-v1",
    "phase23-tailoring-agent-workflow-release-v1",
    "phase20d-no-auto-apply-safety-checkpoint-v1",
)

PROTECTED_HASHES = {
    "src/agents/exact_resume_change_set_proposal_builder_default_off.py": "fd173ea8bf3f7d746ebbdb7d6b2af7ae7df1aeaea4e66acaca52ea4fda1a9dc4",
    "run_exact_resume_change_set_proposal_builder_dry_run.py": "a8ea3201f0e71e463e316abdcf813b8d08fa3a473cd3dddcee158b87f3442451",
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_suggestions.py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_queue.py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
}


def _sha256(path: Path) -> str:
    return sha256(path.read_bytes()).hexdigest()


def _proposal(**overrides):
    proposal = {
        "proposal_id": "p1",
        "item_id": "queue-1",
        "job_id": "job-1",
        "title": "Senior Data Scientist",
        "company": "ExampleCo",
        "change_type": "bullet",
        "target_section": "experience",
        "target_identifier": "b1",
        "current_text": "Built Python dashboards.",
        "proposed_text": "Built Python and SQL dashboards.",
        "change_reason": "Align with supplied JD terms.",
        "jd_terms_supported": ["Python", "SQL"],
        "resume_evidence_used": ["Built Python dashboards."],
        "risk_flags": [],
        "manual_review_required": True,
        "requires_user_acceptance": True,
    }
    for key, value in overrides.items():
        proposal[key] = value
    return proposal


def _resume_context():
    return {"profile_summary": "Data scientist.", "skills": ["Python", "SQL"]}


def _jd_context():
    return {"required_skills": ["Python", "SQL"], "tools": ["Tableau"]}


def _tailoring_context():
    return {"matched_required_skills": ["Python", "SQL"], "missing_tools": ["Tableau"]}


def test_helper_exists_and_is_import_safe():
    module = importlib.reload(packet_builder)
    assert callable(
        module.build_controlled_exact_resume_change_set_llm_request_packet_default_off
    )


def test_missing_change_proposals_blocks_with_missing_input_reason():
    payload = build_controlled_exact_resume_change_set_llm_request_packet_default_off(
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
    )

    assert REQUIRED_KEYS.issubset(payload)
    assert payload["phase"] == "43A"
    assert payload["change_proposals_present"] is False
    assert "change_proposals" in payload["missing_inputs"]
    assert payload["request_packet_summary"]["request_blocked"] is True


def test_proposal_result_with_change_proposals_is_accepted():
    payload = build_controlled_exact_resume_change_set_llm_request_packet_default_off(
        proposal_result={"change_proposals": [_proposal()]},
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
    )

    assert payload["request_findings"]["change_proposals_source"] == "proposal_result.change_proposals"
    assert payload["request_packet"]["included_change_proposals"][0]["proposal_id"] == "p1"


def test_nested_proposal_result_change_proposals_is_accepted():
    payload = build_controlled_exact_resume_change_set_llm_request_packet_default_off(
        proposal_result={"proposal_result": {"change_proposals": [_proposal(proposal_id="nested")]}},
    )

    assert (
        payload["request_findings"]["change_proposals_source"]
        == "proposal_result.proposal_result.change_proposals"
    )
    assert payload["request_packet"]["included_change_proposals"][0]["proposal_id"] == "nested"


def test_flattened_change_proposals_by_type_is_accepted():
    payload = build_controlled_exact_resume_change_set_llm_request_packet_default_off(
        proposal_result={"change_proposals_by_type": {"bullet": [_proposal(proposal_id="flat")]}},
    )

    assert payload["request_findings"]["change_proposals_source"] == "proposal_result.change_proposals_by_type"
    assert payload["request_packet"]["included_change_proposals"][0]["proposal_id"] == "flat"


def test_explicit_change_proposals_take_precedence_over_proposal_result():
    payload = build_controlled_exact_resume_change_set_llm_request_packet_default_off(
        change_proposals=[_proposal(proposal_id="explicit")],
        proposal_result={"change_proposals": [_proposal(proposal_id="ignored")]},
    )

    assert payload["request_findings"]["change_proposals_source"] == "change_proposals"
    assert payload["request_packet"]["included_change_proposals"][0]["proposal_id"] == "explicit"


def test_invalid_non_dict_proposals_are_counted_without_crashing():
    payload = build_controlled_exact_resume_change_set_llm_request_packet_default_off(
        change_proposals=[_proposal(), "bad"],
    )

    assert payload["change_proposal_count"] == 2
    assert payload["valid_change_proposal_count"] == 1
    assert payload["invalid_change_proposal_count"] == 1
    assert payload["request_findings"]["invalid_change_proposals"][0]["input_index"] == 1


def test_inputs_are_not_mutated():
    proposals = [_proposal()]
    proposal_result = {"change_proposals": [_proposal(proposal_id="other")]}
    resume = _resume_context()
    jd = _jd_context()
    tailoring = _tailoring_context()
    snapshots = (
        deepcopy(proposals),
        deepcopy(proposal_result),
        deepcopy(resume),
        deepcopy(jd),
        deepcopy(tailoring),
    )

    build_controlled_exact_resume_change_set_llm_request_packet_default_off(
        change_proposals=proposals,
        proposal_result=proposal_result,
        resume_context=resume,
        jd_context=jd,
        tailoring_context=tailoring,
    )

    assert proposals == snapshots[0]
    assert proposal_result == snapshots[1]
    assert resume == snapshots[2]
    assert jd == snapshots[3]
    assert tailoring == snapshots[4]


def test_request_packet_is_deterministic():
    kwargs = {
        "change_proposals": [_proposal()],
        "resume_context": _resume_context(),
        "jd_context": _jd_context(),
        "tailoring_context": _tailoring_context(),
    }

    assert (
        build_controlled_exact_resume_change_set_llm_request_packet_default_off(**kwargs)
        == build_controlled_exact_resume_change_set_llm_request_packet_default_off(**kwargs)
    )


def test_max_proposals_truncates_and_reports_excluded():
    payload = build_controlled_exact_resume_change_set_llm_request_packet_default_off(
        change_proposals=[
            _proposal(proposal_id="p1"),
            _proposal(proposal_id="p2"),
            _proposal(proposal_id="p3"),
        ],
        request_policy={"max_proposals_per_request": 2},
    )

    assert [row["proposal_id"] for row in payload["request_packet"]["included_change_proposals"]] == [
        "p1",
        "p2",
    ]
    assert [row["proposal_id"] for row in payload["request_packet"]["excluded_change_proposals"]] == [
        "p3"
    ]
    assert payload["request_packet_summary"]["excluded_change_proposal_count"] == 1
    assert payload["request_findings"]["excluded_change_proposals"][0]["proposal_id"] == "p3"


def test_messages_include_system_and_user_payload_and_required_prohibitions():
    payload = build_controlled_exact_resume_change_set_llm_request_packet_default_off(
        change_proposals=[_proposal()],
        resume_context=_resume_context(),
        jd_context=_jd_context(),
        tailoring_context=_tailoring_context(),
    )
    messages = payload["request_messages"]
    text = str(messages).lower()

    assert messages[0]["role"] == "system"
    assert messages[1]["role"] == "user"
    for marker in (
        "refine exact resume change proposals only",
        "do not generate a full resume",
        "unsupported claims",
        "overwrite",
        "mutate",
        "execute",
        "submit",
        "auto-apply",
        "auto-submit",
    ):
        assert marker in text


def test_schema_and_packet_include_required_contracts():
    payload = build_controlled_exact_resume_change_set_llm_request_packet_default_off(
        change_proposals=[_proposal()],
    )
    schema = payload["request_schema"]
    packet = payload["request_packet"]
    proposal_props = schema["properties"]["refined_change_proposals"]["items"]["properties"]

    assert "refined_change_proposals" in schema["properties"]
    for field in (
        "proposal_id",
        "change_type",
        "target_section",
        "target_identifier",
        "current_text",
        "proposed_text",
        "change_reason",
        "jd_terms_supported",
        "resume_evidence_used",
        "risk_flags",
        "manual_review_required",
        "requires_user_acceptance",
    ):
        assert field in proposal_props
    assert schema["properties"]["resume_overwrite_performed"]["const"] is False
    assert schema["properties"]["resume_mutation_performed"]["const"] is False
    assert schema["properties"]["application_submission_performed"]["const"] is False
    assert packet["safety_constraints"]
    assert packet["evidence_constraints"]
    assert packet["output_constraints"]
    assert packet["provider_call_performed"] is False
    assert packet["network_call_performed"] is False


def test_provider_dispatch_ready_but_no_provider_or_runtime_effects():
    payload = build_controlled_exact_resume_change_set_llm_request_packet_default_off(
        change_proposals=[_proposal()],
    )

    assert payload["provider_dispatch_ready"] is True
    assert payload["llm_request_packet_created"] is True
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


def test_changed_files_are_limited_to_phase43a_and_legacy_guards():
    allowed = {
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

        "tests/test_phase44a_controlled_exact_resume_change_set_provider_call_boundary_default_off.py",
        "run_controlled_exact_resume_change_set_llm_request_packet_dry_run.py",
        "docs/phase43_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.md",
        "tests/test_phase43b_controlled_exact_resume_change_set_llm_request_packet_dry_run_command_default_off.py",
        "tests/test_phase43a_controlled_exact_resume_change_set_llm_request_packet_default_off.py",
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
