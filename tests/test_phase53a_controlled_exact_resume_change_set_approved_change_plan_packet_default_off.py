from copy import deepcopy
from hashlib import sha256
import importlib
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
HELPER_PATH = (
    ROOT
    / "src/agents/controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase53_controlled_exact_resume_change_set_approved_change_plan_packet_default_off.md"
)
PROTECTED_HASHES = {
    "src/tailoring/llm.py": "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
    "generate_tailoring_" + "suggestions" + ".py": "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28",
    "src/matching/scorer.py": "5a7fa4abf6adb353bbb8c3f8c3113279409de1250f99e61a36056c5d06503062",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_" + "queue" + ".py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
    "src/agents/controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py": (
        "68ef42fd16c6299681641ad92bc93c648331c36e8fdd17971e387247e9c3e66a"
    ),
    "run_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run.py": (
        "3defcb6db228936f4045bcfeb1695f4980d042d224be46e300980adb00ca361e"
    ),
    "src/agents/controlled_exact_resume_change_set_manual_decision_packet_default_off.py": (
        "0c54c837040007e0241aeedffabdf35375797d8f55bead5b0c6b73106d9867aa"
    ),
}


def _module():
    return importlib.import_module(
        "src.agents.controlled_exact_resume_change_set_approved_change_plan_packet_default_off"
    )


def _policy():
    return {"allow_approved_change_plan_packet": True}


def _readback_payload():
    return {
        "payload_type": "exact_resume_change_set_manual_decision_readback",
        "manual_decision_readback_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "source_manual_decision_packet": {
            "payload_type": "exact_resume_change_set_manual_decision_packet"
        },
        "decision_summary": {
            "decision_count": 3,
            "approved_count": 1,
            "rejected_count": 1,
            "needs_revision_count": 1,
        },
        "readback_items": [
            {
                "readback_item_id": "manual-decision-readback-p1",
                "proposal_id": "p1",
                "manual_decision": "approve",
                "decision_reason": "looks exact",
                "resume_change_applied": False,
                "artifact_created": False,
                "application_execution_performed": False,
            },
            {
                "readback_item_id": "manual-decision-readback-p2",
                "proposal_id": "p2",
                "manual_decision": "reject",
                "decision_reason": "not supported",
                "resume_change_applied": False,
                "artifact_created": False,
                "application_execution_performed": False,
            },
            {
                "readback_item_id": "manual-decision-readback-p3",
                "proposal_id": "p3",
                "manual_decision": "needs_revision",
                "decision_reason": "tighten wording",
                "resume_change_applied": False,
                "artifact_created": False,
                "application_execution_performed": False,
            },
        ],
    }


def _phase52_result():
    return {
        "phase": "52A",
        "status": "completed",
        "readback_payload_created": True,
        "readback_payload": _readback_payload(),
    }


def _raw_phase51_packet():
    return {
        "payload_type": "exact_resume_change_set_manual_decision_packet",
        "manual_decisions": [{"proposal_id": "p1", "manual_decision": "approve"}],
    }


def _raw_phase50_readback():
    return {
        "phase": "50A",
        "final_readback_payload": {
            "payload_type": "exact_resume_change_set_manual_review_readback",
            "readback_items": [{"proposal_id": "p1"}],
        },
    }


def test_default_off_blocks():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_packet_default_off(
        manual_decision_readback_result=_phase52_result(),
    )

    assert result["status"] == "blocked"
    assert result["enabled"] is False
    assert "enabled must be true" in result["blocked_reason"]
    assert result["approved_change_plan_packet_created"] is False


def test_missing_readback_input_blocks_safely():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_packet_default_off(
        enabled=True,
        plan_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert result["missing_inputs"] == ["manual_decision_readback"]
    assert "manual decision readback required" in result["blocked_reason"]


def test_raw_phase51_manual_decision_packet_blocks_safely():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_packet_default_off(
        manual_decision_readback_result=_raw_phase51_packet(),
        enabled=True,
        plan_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert "raw manual decision packet is not accepted" in result["blocked_reason"]
    assert result["stage_summaries"]["manual_decision_readback_resolution"][
        "raw_phase51_manual_decision_packet_input"
    ] is True


def test_raw_phase50_readback_or_manual_review_input_blocks_safely():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_packet_default_off(
        manual_decision_readback_result=_raw_phase50_readback(),
        enabled=True,
        plan_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert "raw phase50 readback/manual review input is not accepted" in result[
        "blocked_reason"
    ]
    assert result["stage_summaries"]["manual_decision_readback_resolution"][
        "raw_phase50_readback_or_review_input"
    ] is True


def test_invalid_or_incomplete_readback_blocks_safely():
    readback = _readback_payload()
    readback["readback_items"] = [{"proposal_id": "p1", "manual_decision": "apply"}]

    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_packet_default_off(
        readback_payload=readback,
        enabled=True,
        plan_policy=_policy(),
    )

    assert result["status"] == "blocked"
    assert "invalid manual decision readback present" in result["blocked_reason"]
    assert result["stage_results"]["manual_decision_readback_validation"][
        "invalid_readback_items"
    ][0]["reason"] == "invalid decision value"


def test_valid_readback_produces_deterministic_approved_change_plan_packet():
    builder = (
        _module().build_controlled_exact_resume_change_set_approved_change_plan_packet_default_off
    )
    first = builder(
        manual_decision_readback_result=_phase52_result(),
        enabled=True,
        plan_policy=_policy(),
    )
    second = builder(
        manual_decision_readback_result=_phase52_result(),
        enabled=True,
        plan_policy=_policy(),
    )

    assert first == second
    assert first["status"] == "completed"
    assert first["approved_change_plan_packet_created"] is True
    assert first["approved_change_plan_packet"]["payload_type"] == (
        "exact_resume_change_set_approved_change_plan_packet"
    )


def test_only_approved_decisions_are_actionable():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_packet_default_off(
        readback_payload=_readback_payload(),
        enabled=True,
        plan_policy=_policy(),
    )

    approved = result["approved_change_plan_packet"]["approved_changes"]
    assert [row["proposal_id"] for row in approved] == ["p1"]
    assert all(row["manual_decision"] == "approve" for row in approved)
    assert result["approved_change_plan_packet"]["excluded_decision_summary"] == {
        "rejected_count": 1,
        "needs_revision_count": 1,
        "excluded_count": 2,
    }


def test_decision_counts_are_correct():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_packet_default_off(
        readback_payload=_readback_payload(),
        enabled=True,
        plan_policy=_policy(),
    )

    summary = result["approved_change_plan_packet"]["decision_summary"]
    assert summary["decision_count"] == 3
    assert summary["approved_count"] == 1
    assert summary["rejected_count"] == 1
    assert summary["needs_revision_count"] == 1
    assert result["approved_change_plan_packet"]["approved_change_count"] == 1


def test_original_readback_input_is_preserved_and_not_mutated():
    readback = _readback_payload()
    original = deepcopy(readback)

    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_packet_default_off(
        readback_payload=readback,
        enabled=True,
        plan_policy=_policy(),
    )

    assert readback == original
    assert result["approved_change_plan_packet"]["source_manual_decision_readback"] == original
    result["approved_change_plan_packet"]["source_manual_decision_readback"][
        "readback_items"
    ][0]["manual_decision"] = "reject"
    assert readback == original


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
        "controlled_exact_resume_change_set_manual_decision_packet_default_off",
        "controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off",
        "controlled_exact_resume_change_set_provider_response_validation",
        "controlled_exact_resume_change_set_provider_response_normalization",
        "controlled_exact_resume_change_set_manual_review_readback_adapter",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source


def test_no_mutation_persistence_scoring_artifact_execution_ui_or_api_behavior():
    result = _module().build_controlled_exact_resume_change_set_approved_change_plan_packet_default_off(
        readback_payload=_readback_payload(),
        enabled=True,
        plan_policy=_policy(),
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
    for row in result["approved_change_plan_packet"]["approved_changes"]:
        assert row["resume_change_applied"] is False
        assert row["artifact_created"] is False
        assert row["application_execution_performed"] is False


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_docs_capture_default_off_plan_packet_only_and_safety_boundaries():
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
    assert "plan packet only" in text
