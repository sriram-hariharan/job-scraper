from copy import deepcopy
from hashlib import sha256
import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase52_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.md"
)
PROTECTED_HASHES = {
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_" + "suggestions" + ".py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_" + "queue" + ".py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
    "src/agents/controlled_exact_resume_change_set_manual_decision_packet_default_off.py": (
        "0c54c837040007e0241aeedffabdf35375797d8f55bead5b0c6b73106d9867aa"
    ),
    "run_controlled_exact_resume_change_set_manual_decision_packet_dry_run.py": (
        "bbb99d08196f97a59c7da1044d6780c275e6c88b50f2f6707cc9ba50b8697bc3"
    ),
}


def _module():
    return importlib.import_module(
        "src.agents.controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off"
    )


def _policy():
    return {"allow_manual_decision_readback": True}


def _manual_decision_packet():
    return {
        "payload_type": "exact_resume_change_set_manual_decision_packet",
        "manual_decision_packet_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "allowed_decision_values": ["approve", "reject", "needs_revision"],
        "manual_decisions": [
            {
                "proposal_id": "p1",
                "input_identifier": "p1",
                "manual_decision": "approve",
                "decision_reason": "looks exact",
                "resume_change_applied": False,
                "resume_overwrite_performed": False,
                "resume_mutation_performed": False,
                "artifact_created": False,
                "application_execution_performed": False,
            },
            {
                "proposal_id": "p2",
                "input_identifier": "p2",
                "manual_decision": "reject",
                "decision_reason": "not supported",
                "resume_change_applied": False,
                "resume_overwrite_performed": False,
                "resume_mutation_performed": False,
                "artifact_created": False,
                "application_execution_performed": False,
            },
            {
                "proposal_id": "p3",
                "input_identifier": "p3",
                "manual_decision": "needs_revision",
                "decision_reason": "tighten wording",
                "resume_change_applied": False,
                "resume_overwrite_performed": False,
                "resume_mutation_performed": False,
                "artifact_created": False,
                "application_execution_performed": False,
            },
        ],
        "manual_decisions_by_proposal_id": {},
        "decision_summary": {
            "decision_count": 3,
            "approved_count": 1,
            "rejected_count": 1,
            "needs_revision_count": 1,
            "resume_change_applied": False,
            "resume_mutation_performed": False,
            "artifact_created": False,
            "application_execution_performed": False,
        },
    }


def _phase51_result():
    return {
        "phase": "51A",
        "status": "completed",
        "manual_decision_packet_created": True,
        "manual_decision_packet": _manual_decision_packet(),
    }


def _phase50_readback():
    return {
        "phase": "50A",
        "status": "completed",
        "final_readback_payload": {
            "payload_type": "exact_resume_change_set_manual_review_readback",
            "readback_items": [{"proposal_id": "p1"}],
        },
    }


def test_default_off_blocks():
    result = _module().build_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off(
        manual_decision_packet_result=_phase51_result(),
    )

    assert result["status"] == "blocked"
    assert result["enabled"] is False
    assert "enabled must be true" in result["blocked_reason"]
    assert result["readback_payload_created"] is False


def test_missing_manual_decision_packet_blocks_safely():
    result = _module().build_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off(
        enabled=True,
        readback_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert result["missing_inputs"] == ["manual_decision_packet"]
    assert "manual decision packet required" in result["blocked_reason"]


def test_raw_phase50_readback_or_manual_review_input_blocks_safely():
    result = _module().build_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off(
        manual_decision_packet_result=_phase50_readback(),
        enabled=True,
        readback_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert "raw readback/manual review input is not accepted" in result["blocked_reason"]
    assert result["stage_summaries"]["manual_decision_packet_resolution"][
        "raw_review_or_readback_input"
    ] is True


def test_invalid_or_incomplete_decision_packet_blocks_safely():
    packet = _manual_decision_packet()
    packet["manual_decisions"] = [{"proposal_id": "p1", "manual_decision": "apply"}]

    result = _module().build_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off(
        manual_decision_packet=packet,
        enabled=True,
        readback_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert "invalid manual decision packet present" in result["blocked_reason"]
    assert result["stage_results"]["manual_decision_packet_validation"][
        "invalid_decisions"
    ][0]["reason"] == "invalid decision value"


def test_valid_decision_packet_produces_deterministic_readback():
    builder = (
        _module().build_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off
    )
    first = builder(
        manual_decision_packet_result=_phase51_result(),
        enabled=True,
        readback_policy=_policy(),
    )
    second = builder(
        manual_decision_packet_result=_phase51_result(),
        enabled=True,
        readback_policy=_policy(),
    )

    assert first == second
    assert first["status"] == "completed"
    assert first["readback_payload_created"] is True
    assert first["readback_payload"]["payload_type"] == (
        "exact_resume_change_set_manual_decision_readback"
    )


def test_decision_counts_are_correct():
    result = _module().build_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off(
        manual_decision_packet=_manual_decision_packet(),
        enabled=True,
        readback_policy=_policy(),
    )

    summary = result["readback_payload"]["decision_summary"]
    assert summary["decision_count"] == 3
    assert summary["approved_count"] == 1
    assert summary["rejected_count"] == 1
    assert summary["needs_revision_count"] == 1
    assert len(result["readback_payload"]["decisions_by_status"]["approve"]) == 1
    assert len(result["readback_payload"]["decisions_by_status"]["reject"]) == 1
    assert len(result["readback_payload"]["decisions_by_status"]["needs_revision"]) == 1


def test_original_decision_packet_is_preserved_and_not_mutated():
    packet = _manual_decision_packet()
    original = deepcopy(packet)

    result = _module().build_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off(
        manual_decision_packet=packet,
        enabled=True,
        readback_policy=_policy(),
    )

    assert packet == original
    assert result["readback_payload"]["source_manual_decision_packet"] == original
    result["readback_payload"]["source_manual_decision_packet"]["manual_decisions"][0][
        "manual_decision"
    ] = "reject"
    assert packet == original


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
    result = _module().build_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off(
        manual_decision_packet=_manual_decision_packet(),
        enabled=True,
        readback_policy=_policy(),
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
        "user_decision_applied",
        "ui_route_added",
        "api_route_added",
    ):
        assert result[key] is False
    for row in result["readback_payload"]["readback_items"]:
        assert row["resume_change_applied"] is False
        assert row["artifact_created"] is False
        assert row["application_execution_performed"] is False


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_docs_capture_default_off_readback_only_and_safety_boundaries():
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
    assert "readback only" in text
