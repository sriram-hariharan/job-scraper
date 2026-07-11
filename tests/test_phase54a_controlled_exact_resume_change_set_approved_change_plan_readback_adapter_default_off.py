from copy import deepcopy
from hashlib import sha256
import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase54_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off.md"
)
PROTECTED_HASHES = {
    "src/tailoring/llm.py": "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
    "generate_tailoring_" + "suggestions" + ".py": "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28",
    "src/matching/scorer.py": "f56624b5b3c7e2bb01a824386b86fbc2a194e727f0437ca0773764eae64ec941",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_" + "queue" + ".py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
    "src/agents/controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py": (
        "b9f11e4d95660a88a81d107b06f7cb3893d8b706bcf92c9513ccafb4143333b3"
    ),
    "run_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run.py": (
        "6f64d07abe2df6898a42c614c10db868170263a57e57d409ac076b635d47c054"
    ),
    "src/agents/controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py": (
        "68ef42fd16c6299681641ad92bc93c648331c36e8fdd17971e387247e9c3e66a"
    ),
}


def _module():
    return importlib.import_module(
        "src.agents.controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off"
    )


def _policy():
    return {"allow_approved_change_plan_readback": True}


def _approved_change_plan_packet() -> dict:
    return {
        "payload_type": "exact_resume_change_set_approved_change_plan_packet",
        "approved_change_plan_packet_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "source_manual_decision_readback": {
            "payload_type": "exact_resume_change_set_manual_decision_readback"
        },
        "decision_summary": {
            "decision_count": 3,
            "approved_count": 2,
            "rejected_count": 1,
            "needs_revision_count": 0,
        },
        "excluded_decision_summary": {
            "rejected_count": 1,
            "needs_revision_count": 0,
            "excluded_count": 1,
        },
        "approved_change_count": 2,
        "approved_changes": [
            {
                "plan_item_id": "approved-change-plan-p1",
                "proposal_id": "p1",
                "source_readback_item_id": "manual-decision-readback-p1",
                "manual_decision": "approve",
                "decision_reason": "looks exact",
                "change_type": "bullet_update",
                "section": "experience",
                "resume_change_applied": False,
                "resume_overwrite_performed": False,
                "resume_mutation_performed": False,
                "artifact_created": False,
                "application_execution_performed": False,
            },
            {
                "plan_item_id": "approved-change-plan-p2",
                "proposal_id": "p2",
                "source_readback_item_id": "manual-decision-readback-p2",
                "manual_decision": "approve",
                "decision_reason": "also exact",
                "change_type": "keyword_addition",
                "section": "skills",
                "resume_change_applied": False,
                "resume_overwrite_performed": False,
                "resume_mutation_performed": False,
                "artifact_created": False,
                "application_execution_performed": False,
            },
        ],
        "resume_change_applied": False,
        "resume_mutation_performed": False,
        "artifact_created": False,
        "application_execution_performed": False,
    }


def _phase53_result() -> dict:
    return {
        "phase": "53A",
        "status": "completed",
        "approved_change_plan_packet_created": True,
        "approved_change_plan_packet": _approved_change_plan_packet(),
    }


def _phase53b_result() -> dict:
    return {
        "phase": "53B",
        "status": "completed",
        "plan_result": _phase53_result(),
    }


def _raw_phase52_readback() -> dict:
    return {
        "payload_type": "exact_resume_change_set_manual_decision_readback",
        "readback_items": [{"proposal_id": "p1", "manual_decision": "approve"}],
    }


def _raw_phase51_packet() -> dict:
    return {
        "payload_type": "exact_resume_change_set_manual_decision_packet",
        "manual_decisions": [{"proposal_id": "p1", "manual_decision": "approve"}],
    }


def _raw_phase50_readback() -> dict:
    return {
        "phase": "50A",
        "final_readback_payload": {
            "payload_type": "exact_resume_change_set_manual_review_readback",
            "readback_items": [{"proposal_id": "p1"}],
        },
    }


def test_default_off_blocks():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off(
        approved_change_plan_packet_result=_phase53_result(),
    )

    assert result["status"] == "blocked"
    assert result["enabled"] is False
    assert "enabled must be true" in result["blocked_reason"]
    assert result["readback_payload_created"] is False


def test_missing_approved_change_plan_packet_blocks_safely():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off(
        enabled=True,
        readback_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert result["missing_inputs"] == ["approved_change_plan_packet"]
    assert "approved change plan packet required" in result["blocked_reason"]


def test_raw_phase52_manual_decision_readback_blocks_safely():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off(
        approved_change_plan_packet_result=_raw_phase52_readback(),
        enabled=True,
        readback_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert "raw phase52 manual decision readback is not accepted" in result[
        "blocked_reason"
    ]
    assert result["stage_summaries"]["approved_change_plan_packet_resolution"][
        "raw_phase52_manual_decision_readback_input"
    ] is True


def test_raw_phase51_manual_decision_packet_blocks_safely():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off(
        approved_change_plan_packet_result=_raw_phase51_packet(),
        enabled=True,
        readback_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert "raw manual decision packet is not accepted" in result["blocked_reason"]
    assert result["stage_summaries"]["approved_change_plan_packet_resolution"][
        "raw_phase51_manual_decision_packet_input"
    ] is True


def test_raw_phase50_readback_or_manual_review_input_blocks_safely():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off(
        approved_change_plan_packet_result=_raw_phase50_readback(),
        enabled=True,
        readback_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert "raw phase50 readback/manual review input is not accepted" in result[
        "blocked_reason"
    ]
    assert result["stage_summaries"]["approved_change_plan_packet_resolution"][
        "raw_phase50_readback_or_review_input"
    ] is True


def test_invalid_or_incomplete_approved_change_plan_packet_blocks_safely():
    packet = _approved_change_plan_packet()
    packet["approved_changes"] = [{"proposal_id": "p1", "manual_decision": "reject"}]

    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off(
        approved_change_plan_packet=packet,
        enabled=True,
        readback_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert "invalid approved change plan packet present" in result["blocked_reason"]
    assert result["stage_results"]["approved_change_plan_packet_validation"][
        "invalid_approved_changes"
    ][0]["reason"] == "approved change must have approve decision"


def test_valid_approved_change_plan_packet_produces_deterministic_readback():
    builder = (
        _module().build_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off
    )
    first = builder(
        approved_change_plan_packet_result=_phase53_result(),
        enabled=True,
        readback_policy=_policy(),
    )
    second = builder(
        approved_change_plan_packet_result=_phase53_result(),
        enabled=True,
        readback_policy=_policy(),
    )

    assert first == second
    assert first["status"] == "completed"
    assert first["readback_payload_created"] is True
    assert first["readback_payload"]["payload_type"] == (
        "exact_resume_change_set_approved_change_plan_readback"
    )
    assert first["stage_summaries"]["approved_change_plan_packet_resolution"][
        "source"
    ] == "phase53.approved_change_plan_packet"


def test_phase53b_wrapper_input_is_supported():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off(
        approved_change_plan_packet_result=_phase53b_result(),
        enabled=True,
        readback_policy=_policy(),
    )

    assert result["status"] == "completed"
    assert result["stage_summaries"]["approved_change_plan_packet_resolution"][
        "source"
    ] == "phase53b.plan_result.approved_change_plan_packet"


def test_approved_actionable_change_counts_are_correct():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off(
        approved_change_plan_packet=_approved_change_plan_packet(),
        enabled=True,
        readback_policy=_policy(),
    )

    summary = result["readback_payload"]["approved_change_summary"]
    assert summary["approved_change_count"] == 2
    assert summary["approved_change_count_by_type"] == {
        "bullet_update": 1,
        "keyword_addition": 1,
    }
    assert summary["approved_change_count_by_section"] == {
        "experience": 1,
        "skills": 1,
    }
    assert len(result["readback_payload"]["approved_changes_by_type"]["bullet_update"]) == 1
    assert len(result["readback_payload"]["approved_changes_by_section"]["skills"]) == 1


def test_original_approved_change_plan_packet_is_preserved_and_not_mutated():
    packet = _approved_change_plan_packet()
    original = deepcopy(packet)

    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off(
        approved_change_plan_packet=packet,
        enabled=True,
        readback_policy=_policy(),
    )

    assert packet == original
    assert result["readback_payload"]["source_approved_change_plan_packet"] == original
    result["readback_payload"]["source_approved_change_plan_packet"]["approved_changes"][
        0
    ]["proposal_id"] = "changed"
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
        "controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off",
        "controlled_exact_resume_change_set_approved_change_plan_packet_default_off",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source


def test_no_mutation_persistence_scoring_artifact_execution_ui_or_api_behavior():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_readback_adapter_default_off(
        approved_change_plan_packet=_approved_change_plan_packet(),
        enabled=True,
        readback_policy=_policy(),
    )

    for key in (
        "provider_call_performed",
        "llm_call_performed",
        "network_call_performed",
        "resume_artifact_created",
        "resume_change_applied",
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
        assert result["readback_payload"].get(key, False) is False


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_docs_capture_default_off_readback_only_and_safety_boundaries():
    text = DOC_PATH.read_text(encoding="utf-8")

    assert "default-off" in text
    assert "does not call a provider" in text
    assert "call an llm" in text
    assert "call network" in text
    assert "no mutation" in text
    assert "no persistence" in text
    assert "no scoring" in text
    assert "no artifact creation" in text
    assert "no application execution" in text
    assert "readback only" in text
