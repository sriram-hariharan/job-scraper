from hashlib import sha256
from pathlib import Path

import pytest

from src.agents import (
    controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off
    as phase50,
)


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    ROOT
    / "src/agents/controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase50_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.md"
)
PROTECTED_HASHES = {
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_" + "suggestions" + ".py": "559a66a7c7a1963d322a1e7b3f0fd3ede1ea161a9be2d176dcce0ef1016ea9ff",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_" + "queue" + ".py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
    "src/agents/controlled_exact_resume_change_set_real_provider_runtime_adapter_default_off.py": (
        "7e3cea001fb2ded35c1d998e22d156568492a4b76804a76d4142a329d18c5c97"
    ),
    "run_controlled_exact_resume_change_set_real_provider_runtime_adapter_dry_run.py": (
        "e98126542e3d5d83bb6dd2265631718edaffff7555d4b76cbeb3d9a3318b745d"
    ),
}


def _policy():
    return {"allow_real_provider_response_handoff": True}


def _request_packet():
    return {"change_proposals": [{"proposal_id": "p1"}]}


def _provider_response():
    return {
        "provider_call_performed": False,
        "llm_call_performed": False,
        "network_call_performed": False,
        "resume_overwrite_performed": False,
        "resume_mutation_performed": False,
        "persistence_performed": False,
        "final_score_produced": False,
        "application_submission_performed": False,
        "refined_change_proposals": [
            {
                "proposal_id": "p1",
                "change_type": "rewrite_bullet",
                "target_section": "experience",
                "target_identifier": "role-1-bullet-1",
                "current_text": "Built reporting workflows.",
                "proposed_text": "Built deterministic reporting workflows.",
                "change_reason": "Matches JD evidence.",
                "jd_terms_supported": ["deterministic"],
                "resume_evidence_used": ["reporting workflows"],
                "risk_flags": [],
                "manual_review_required": True,
                "requires_user_acceptance": True,
            }
        ],
    }


def _enabled_kwargs():
    return {
        "original_request_packet": _request_packet(),
        "original_change_proposals": _request_packet()["change_proposals"],
        "enabled": True,
        "handoff_policy": _policy(),
    }


def test_default_off_blocks_without_calling_stages(monkeypatch):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("stage helper should not run while default-off")

    monkeypatch.setattr(
        phase50,
        "build_controlled_exact_resume_change_set_provider_response_validation_default_off",
        forbidden,
    )

    result = phase50.build_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off(
        provider_response=_provider_response(),
    )

    assert result["status"] == "blocked"
    assert result["enabled"] is False
    assert "enabled must be true" in result["blocked_reason"]
    assert calls == []
    assert result["provider_call_performed"] is False
    assert result["resume_mutation_performed"] is False
    assert result["persistence_performed"] is False
    assert result["application_execution_performed"] is False


def test_missing_provider_output_blocks_safely():
    result = phase50.build_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off(
        enabled=True,
        handoff_policy=_policy(),
        original_request_packet=_request_packet(),
    )

    assert result["status"] == "blocked"
    assert result["provider_response_present"] is False
    assert result["missing_inputs"] == ["provider_response"]
    assert "provider_response required" in result["blocked_reason"]


def test_runtime_result_provider_response_extraction_works():
    result = phase50.build_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off(
        runtime_result={"phase": "49A", "provider_response": _provider_response()},
        **_enabled_kwargs(),
    )

    assert result["status"] == "completed"
    assert result["provider_response_source"] == "runtime_result.provider_response"
    assert result["final_readback_payload"]["payload_type"] == (
        "exact_resume_change_set_manual_review_readback"
    )


def test_direct_provider_response_input_works():
    result = phase50.build_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off(
        provider_response=_provider_response(),
        **_enabled_kwargs(),
    )

    assert result["status"] == "completed"
    assert result["provider_response_source"] == "provider_response"
    assert result["provider_response_validation_performed"] is True
    assert result["provider_response_normalization_performed"] is True
    assert result["manual_review_packets_created"] is True
    assert result["manual_review_readback_payload_created"] is True


def test_stage_order_validation_normalization_manual_review_readback(monkeypatch):
    calls = []

    def validation(**kwargs):
        calls.append("validation")
        return {
            "phase": "45A",
            "provider_response_valid": True,
            "refined_change_proposals": _provider_response()["refined_change_proposals"],
            "validation_summary": {"provider_response_valid": True},
        }

    def normalization(**kwargs):
        calls.append("normalization")
        return {
            "phase": "46A",
            "normalized_refined_change_proposals": [
                {
                    "proposal_id": "p1",
                    "change_type": "rewrite_bullet",
                    "manual_review_required": True,
                    "requires_user_acceptance": True,
                }
            ],
            "normalization_summary": {"normalized_refined_change_proposal_count": 1},
        }

    def review(**kwargs):
        calls.append("manual_review_packet")
        return {
            "phase": "47A",
            "manual_review_packets": [
                {
                    "review_packet_id": "r1",
                    "proposal_id": "p1",
                    "recommended_operator_action": "review_change",
                }
            ],
            "manual_review_packet_summary": {"manual_review_packet_count": 1},
        }

    def readback(**kwargs):
        calls.append("readback")
        return {
            "phase": "48A",
            "readback_payload": {"readback_items": [{"proposal_id": "p1"}]},
            "readback_summary": {"readback_item_count": 1},
            "readback_findings": {"blocked": False},
        }

    monkeypatch.setattr(
        phase50,
        "build_controlled_exact_resume_change_set_provider_response_validation_default_off",
        validation,
    )
    monkeypatch.setattr(
        phase50,
        "build_controlled_exact_resume_change_set_provider_response_normalization_default_off",
        normalization,
    )
    monkeypatch.setattr(
        phase50,
        "build_controlled_exact_resume_change_set_manual_review_packet_builder_default_off",
        review,
    )
    monkeypatch.setattr(
        phase50,
        "build_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off",
        readback,
    )

    result = phase50.build_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off(
        provider_response=_provider_response(),
        **_enabled_kwargs(),
    )

    assert result["status"] == "completed"
    assert calls == ["validation", "normalization", "manual_review_packet", "readback"]
    assert result["stage_sequence"] == calls


@pytest.mark.parametrize(
    ("stage", "expected_status", "expected_calls"),
    [
        ("validation", "validation_failed", ["validation"]),
        ("normalization", "normalization_failed", ["validation", "normalization"]),
        (
            "manual_review_packet",
            "manual_review_packet_failed",
            ["validation", "normalization", "manual_review_packet"],
        ),
        (
            "readback",
            "readback_failed",
            ["validation", "normalization", "manual_review_packet", "readback"],
        ),
    ],
)
def test_stage_failures_stop_or_surface(monkeypatch, stage, expected_status, expected_calls):
    calls = []

    def validation(**kwargs):
        calls.append("validation")
        if stage == "validation":
            return {"status": "blocked", "provider_response_valid": False}
        return {
            "provider_response_valid": True,
            "refined_change_proposals": _provider_response()["refined_change_proposals"],
        }

    def normalization(**kwargs):
        calls.append("normalization")
        if stage == "normalization":
            return {"status": "blocked", "normalized_refined_change_proposals": []}
        return {
            "normalized_refined_change_proposals": [
                {
                    "proposal_id": "p1",
                    "change_type": "rewrite_bullet",
                    "manual_review_required": True,
                    "requires_user_acceptance": True,
                }
            ]
        }

    def review(**kwargs):
        calls.append("manual_review_packet")
        if stage == "manual_review_packet":
            return {"status": "blocked", "manual_review_packets": []}
        return {
            "manual_review_packets": [
                {
                    "review_packet_id": "r1",
                    "proposal_id": "p1",
                    "recommended_operator_action": "review_change",
                }
            ]
        }

    def readback(**kwargs):
        calls.append("readback")
        if stage == "readback":
            return {
                "status": "blocked",
                "readback_payload": {},
                "readback_findings": {"blocked": True},
            }
        return {
            "readback_payload": {"readback_items": [{"proposal_id": "p1"}]},
            "readback_findings": {"blocked": False},
        }

    monkeypatch.setattr(
        phase50,
        "build_controlled_exact_resume_change_set_provider_response_validation_default_off",
        validation,
    )
    monkeypatch.setattr(
        phase50,
        "build_controlled_exact_resume_change_set_provider_response_normalization_default_off",
        normalization,
    )
    monkeypatch.setattr(
        phase50,
        "build_controlled_exact_resume_change_set_manual_review_packet_builder_default_off",
        review,
    )
    monkeypatch.setattr(
        phase50,
        "build_controlled_exact_resume_change_set_manual_review_readback_adapter_default_off",
        readback,
    )

    result = phase50.build_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off(
        provider_response=_provider_response(),
        **_enabled_kwargs(),
    )

    assert result["status"] == expected_status
    assert calls == expected_calls


def test_no_forbidden_provider_llm_network_or_runtime_imports():
    source = MODULE_PATH.read_text(encoding="utf-8")
    forbidden_fragments = [
        "op" + "enai",
        "anth" + "ropic",
        "ht" + "tpx",
        "url" + "lib",
        "importlib",
        "src.tailoring." + "llm",
        "generate_tailoring_" + "suggestions",
        "src.matching.scorer",
        "src.matching.prefilter",
        "application_execution_" + "queue",
        "sock" + "et",
        "subprocess",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source


def test_no_mutation_persistence_scoring_artifact_execution_or_decision_acceptance():
    result = phase50.build_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off(
        provider_response=_provider_response(),
        **_enabled_kwargs(),
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
        "user_decision_accepted",
        "ui_route_added",
        "api_route_added",
    ):
        assert result[key] is False


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_docs_capture_default_off_sequence_and_safety_boundaries():
    text = DOC_PATH.read_text(encoding="utf-8")

    assert "default-off" in text
    assert "provider, call an LLM, call network" in text
    assert "mutate resumes, persist data, score applications" in text
    assert "application execution" in text
    assert "validation -> normalization -> manual review -> readback" in text
    assert "never executes Phase 49" in text
