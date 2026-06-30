from hashlib import sha256
import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/controlled_exact_resume_change_set_manual_decision_packet_default_off.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase51_controlled_exact_resume_change_set_manual_decision_packet_default_off.md"
)
PROTECTED_HASHES = {
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_" + "suggestions" + ".py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_" + "queue" + ".py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
    "src/agents/controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.py": (
        "89b7063a13f0f12da662cd6bdae534cdfb7f5156d52c1a9d311ccc349e3a7774"
    ),
    "run_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run.py": (
        "596d17aff87a43db2b3b4cb2e1cbf036c7019736d458b2a4112289d6a892d5c6"
    ),
}


def _module():
    return importlib.import_module(
        "src.agents.controlled_exact_resume_change_set_manual_decision_packet_default_off"
    )


def _policy():
    return {"allow_manual_decision_packet": True}


def _readback_items():
    return [
        {
            "readback_item_id": "rb-1",
            "review_packet_id": "pkt-1",
            "proposal_id": "p1",
            "change_type": "rewrite_bullet",
            "target_section": "experience",
            "target_identifier": "role-1-bullet-1",
            "current_text": "Built reporting workflows.",
            "proposed_text": "Built deterministic reporting workflows.",
            "manual_review_required": True,
            "requires_user_acceptance": True,
        },
        {
            "readback_item_id": "rb-2",
            "review_packet_id": "pkt-2",
            "proposal_id": "p2",
            "change_type": "skill_addition",
            "target_section": "skills",
            "target_identifier": "skills",
            "current_text": "Python",
            "proposed_text": "Python, deterministic testing",
            "manual_review_required": True,
            "requires_user_acceptance": True,
        },
        {
            "readback_item_id": "rb-3",
            "review_packet_id": "pkt-3",
            "proposal_id": "p3",
            "change_type": "summary_revision",
            "target_section": "summary",
            "target_identifier": "summary",
            "current_text": "Builder.",
            "proposed_text": "Builder of reliable automation.",
            "manual_review_required": True,
            "requires_user_acceptance": True,
        },
    ]


def _phase50_output():
    return {
        "phase": "50A",
        "status": "completed",
        "final_readback_payload": {
            "payload_type": "exact_resume_change_set_manual_review_readback",
            "readback_items": _readback_items(),
        },
    }


def _decisions():
    return [
        {"proposal_id": "p1", "decision": "approve", "reason": "looks exact"},
        {"proposal_id": "p2", "decision": "reject", "reason": "not supported"},
        {
            "proposal_id": "p3",
            "decision": "needs_revision",
            "reason": "tighten wording",
        },
    ]


def test_default_off_blocks():
    result = _module().build_controlled_exact_resume_change_set_manual_decision_packet_default_off(
        readback_result=_phase50_output(),
        manual_decisions=_decisions(),
    )

    assert result["status"] == "blocked"
    assert result["enabled"] is False
    assert "enabled must be true" in result["blocked_reason"]
    assert result["manual_decision_packet_created"] is False


def test_missing_readback_or_manual_review_input_blocks_safely():
    result = _module().build_controlled_exact_resume_change_set_manual_decision_packet_default_off(
        manual_decisions=_decisions(),
        enabled=True,
        decision_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert result["missing_inputs"] == ["readback_or_manual_review_output"]
    assert "readback/manual review output required" in result["blocked_reason"]


def test_missing_decision_input_blocks_safely():
    result = _module().build_controlled_exact_resume_change_set_manual_decision_packet_default_off(
        readback_result=_phase50_output(),
        enabled=True,
        decision_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert result["missing_inputs"] == ["manual_decisions"]
    assert "manual decisions required" in result["blocked_reason"]


def test_invalid_decision_values_block_safely():
    result = _module().build_controlled_exact_resume_change_set_manual_decision_packet_default_off(
        readback_result=_phase50_output(),
        manual_decisions=[{"proposal_id": "p1", "decision": "apply"}],
        enabled=True,
        decision_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert "invalid manual decisions present" in result["blocked_reason"]
    assert result["stage_results"]["decision_validation"]["invalid_decisions"][0][
        "reason"
    ] == "invalid decision value"


def test_unknown_proposal_identifiers_block_safely():
    result = _module().build_controlled_exact_resume_change_set_manual_decision_packet_default_off(
        readback_result=_phase50_output(),
        manual_decisions=[{"proposal_id": "unknown", "decision": "approve"}],
        enabled=True,
        decision_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert "unknown proposal identifiers present" in result["blocked_reason"]
    assert result["stage_results"]["decision_validation"]["unknown_identifiers"] == [
        "unknown"
    ]


def test_valid_approve_reject_needs_revision_decisions_create_packet():
    result = _module().build_controlled_exact_resume_change_set_manual_decision_packet_default_off(
        readback_result=_phase50_output(),
        manual_decisions=_decisions(),
        enabled=True,
        decision_policy=_policy(),
    )

    assert result["status"] == "completed"
    assert result["manual_decision_packet_created"] is True
    packet = result["manual_decision_packet"]
    assert packet["payload_type"] == "exact_resume_change_set_manual_decision_packet"
    assert [row["manual_decision"] for row in packet["manual_decisions"]] == [
        "approve",
        "reject",
        "needs_revision",
    ]
    assert packet["decision_summary"]["approved_count"] == 1
    assert packet["decision_summary"]["rejected_count"] == 1
    assert packet["decision_summary"]["needs_revision_count"] == 1


def test_accepts_review_packet_alias_identifiers():
    result = _module().build_controlled_exact_resume_change_set_manual_decision_packet_default_off(
        readback_result=_phase50_output(),
        manual_decisions=[{"proposal_id": "pkt-1", "decision": "approve"}],
        enabled=True,
        decision_policy=_policy(),
    )

    assert result["status"] == "completed"
    assert result["manual_decision_packet"]["manual_decisions"][0]["proposal_id"] == "p1"


def test_output_is_deterministic_for_same_inputs():
    builder = _module().build_controlled_exact_resume_change_set_manual_decision_packet_default_off
    first = builder(
        readback_result=_phase50_output(),
        manual_decisions=_decisions(),
        enabled=True,
        decision_policy=_policy(),
    )
    second = builder(
        readback_result=_phase50_output(),
        manual_decisions=_decisions(),
        enabled=True,
        decision_policy=_policy(),
    )

    assert first == second


def test_no_forbidden_provider_llm_network_or_runtime_imports():
    source = HELPER_PATH.read_text(encoding="utf-8")
    forbidden_fragments = [
        "op" + "enai",
        "anth" + "ropic",
        "req" + "uests",
        "ht" + "tpx",
        "url" + "lib",
        "sock" + "et",
        "src.tailoring." + "llm",
        "generate_tailoring_" + "suggestions",
        "src.matching.scorer",
        "src.matching.prefilter",
        "application_execution_" + "queue",
        "subprocess",
        "controlled_exact_resume_change_set_real_provider_response_handoff_pipeline",
        "controlled_exact_resume_change_set_provider_response_validation",
        "controlled_exact_resume_change_set_provider_response_normalization",
        "controlled_exact_resume_change_set_manual_review_readback_adapter",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source


def test_no_mutation_persistence_scoring_artifact_execution_ui_or_api_behavior():
    result = _module().build_controlled_exact_resume_change_set_manual_decision_packet_default_off(
        readback_result=_phase50_output(),
        manual_decisions=_decisions(),
        enabled=True,
        decision_policy=_policy(),
    )

    for key in (
        "provider_call_performed",
        "llm_call_performed",
        "network_call_performed",
        "resume_artifact_created",
        "resume_mutation_performed",
        "resume_overwrite_performed",
        "persistence_performed",
        "database_" + "write_performed",
        "final_score_produced",
        "matching_scoring_module_called",
        "application_execution_performed",
        "application_submission_performed",
        "ui_route_added",
        "api_route_added",
    ):
        assert result[key] is False
    for row in result["manual_decision_packet"]["manual_decisions"]:
        assert row["resume_change_applied"] is False
        assert row["artifact_created"] is False
        assert row["application_execution_performed"] is False


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_docs_capture_default_off_packet_only_and_safety_boundaries():
    text = DOC_PATH.read_text(encoding="utf-8")

    assert "default-off" in text
    assert "no provider call" in text
    assert "no llm" in text
    assert "no network" in text
    assert "no mutation" in text
    assert "no persistence" in text
    assert "no scoring" in text
    assert "no artifact creation" in text
    assert "no application execution" in text
    assert "manual decision packet only" in text
