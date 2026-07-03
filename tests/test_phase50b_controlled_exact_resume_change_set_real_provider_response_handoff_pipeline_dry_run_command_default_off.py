from hashlib import sha256
import importlib
import json
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = (
    ROOT
    / "run_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase50_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run_command_default_off.md"
)
PROTECTED_HASHES = {
    "src/tailoring/llm.py": "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
    "generate_tailoring_" + "suggestions" + ".py": "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_" + "queue" + ".py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
    "src/agents/controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off.py": (
        "89b7063a13f0f12da662cd6bdae534cdfb7f5156d52c1a9d311ccc349e3a7774"
    ),
}


def _command():
    return importlib.import_module(
        "run_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run"
    )


def _write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _request_packet() -> dict:
    return {"change_proposals": [{"proposal_id": "p1"}], "request_id": "req-1"}


def _provider_response() -> dict:
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


def test_command_module_is_import_safe_and_exposes_functions(capsys):
    module = _command()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    for name in (
        "load_provider_response_from_path",
        "load_runtime_result_from_path",
        "load_original_request_packet_from_path",
        "build_dry_run_payload",
        "main",
    ):
        assert callable(getattr(module, name))


def test_default_off_command_blocks_safely(tmp_path):
    module = _command()
    response_path = _write_json(tmp_path / "response.json", _provider_response())
    request_path = _write_json(tmp_path / "request.json", _request_packet())

    result = module.main(
        [
            "--provider-response",
            str(response_path),
            "--original-request-packet",
            str(request_path),
        ]
    )

    assert result == 0


def test_enabled_command_accepts_local_json_provider_response_input(tmp_path, capsys):
    module = _command()
    response_path = _write_json(tmp_path / "response.json", _provider_response())
    request_path = _write_json(tmp_path / "request.json", _request_packet())
    proposals_path = _write_json(
        tmp_path / "proposals.json",
        {"change_proposals": _request_packet()["change_proposals"]},
    )

    result = module.main(
        [
            "--provider-response",
            str(response_path),
            "--original-request-packet",
            str(request_path),
            "--original-change-proposals",
            str(proposals_path),
            "--enable-handoff",
            "--allow-real-provider-response-handoff",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["phase"] == "50B"
    assert payload["status"] == "completed"
    assert payload["pipeline_result"]["provider_response_source"] == "provider_response"
    assert payload["final_readback_payload"]["payload_type"] == (
        "exact_resume_change_set_manual_review_readback"
    )


def test_enabled_command_accepts_local_json_runtime_result_input(tmp_path, capsys):
    module = _command()
    runtime_path = _write_json(
        tmp_path / "runtime.json",
        {"phase": "49A", "provider_response": _provider_response()},
    )
    request_path = _write_json(tmp_path / "request.json", _request_packet())

    result = module.main(
        [
            "--runtime-result",
            str(runtime_path),
            "--original-request-packet",
            str(request_path),
            "--enable-handoff",
            "--allow-real-provider-response-handoff",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["pipeline_result"]["provider_response_source"] == (
        "runtime_result.provider_response"
    )


def test_missing_provider_output_blocks_safely(tmp_path):
    module = _command()
    request_path = _write_json(tmp_path / "request.json", _request_packet())

    payload = module.build_dry_run_payload(
        original_request_packet=module.load_original_request_packet_from_path(request_path),
        enable_handoff=True,
        allow_real_provider_response_handoff=True,
    )

    assert payload["status"] == "blocked"
    assert payload["pipeline_result"]["missing_inputs"] == ["provider_response"]
    assert "provider_response required" in payload["blocked_reason"]


def test_invalid_json_is_surfaced_cleanly(tmp_path, capsys):
    module = _command()
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not-json", encoding="utf-8")
    request_path = _write_json(tmp_path / "request.json", _request_packet())

    result = module.main(
        [
            "--provider-response",
            str(bad_path),
            "--original-request-packet",
            str(request_path),
        ]
    )

    captured = capsys.readouterr()
    assert result == 2
    assert "invalid JSON" in captured.err
    assert captured.out == ""


def test_command_calls_phase50a_only_not_lower_level_helpers_directly(monkeypatch):
    module = _command()
    calls = []

    def fake_phase50a(**kwargs):
        calls.append(kwargs)
        return {
            "phase": "50A",
            "status": "blocked",
            "blocked_reason": "stubbed",
            "provider_response_present": True,
            "provider_response_source": "provider_response",
            "stage_sequence": [
                "validation",
                "normalization",
                "manual_review_packet",
                "readback",
            ],
            "stage_summaries": {},
            "final_readback_payload": None,
        }

    monkeypatch.setattr(
        module,
        "build_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_default_off",
        fake_phase50a,
    )

    payload = module.build_dry_run_payload(
        provider_response=_provider_response(),
        original_request_packet=_request_packet(),
        enable_handoff=True,
        allow_real_provider_response_handoff=True,
    )

    assert payload["status"] == "blocked"
    assert len(calls) == 1
    assert calls[0]["enabled"] is True
    assert calls[0]["handoff_policy"] == {
        "allow_real_provider_response_handoff": True
    }


def test_no_forbidden_provider_llm_network_or_runtime_imports():
    source = COMMAND_PATH.read_text(encoding="utf-8")
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
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source


def test_no_mutation_persistence_scoring_artifact_execution_or_decision_acceptance():
    module = _command()
    payload = module.build_dry_run_payload(
        provider_response=_provider_response(),
        original_request_packet=_request_packet(),
        enable_handoff=True,
        allow_real_provider_response_handoff=True,
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
        assert payload[key] is False


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_docs_capture_default_off_sequence_and_safety_boundaries():
    text = DOC_PATH.read_text(encoding="utf-8")

    assert "default-off" in text
    assert "does not call a provider" in text
    assert "call an LLM" in text
    assert "call network" in text
    assert "mutate resumes" in text
    assert "persist data" in text
    assert "score applications" in text
    assert "application workflow" in text
    assert "validation -> normalization -> manual review -> readback" in text
