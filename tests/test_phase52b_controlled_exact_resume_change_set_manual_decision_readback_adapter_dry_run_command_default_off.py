from hashlib import sha256
import importlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = (
    ROOT
    / "run_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase52_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run_command_default_off.md"
)
PROTECTED_HASHES = {
    "src/tailoring/llm.py": "d47c5d84758ca185a2fd4d8e2062018b48498592a4b79e88182036c2c4edbc28",
    "generate_tailoring_" + "suggestions" + ".py": "a5e3dda138232fadc6d69bd9f2468459ce2759d961687bf1fa9ee9970c5490c2",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_" + "queue" + ".py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
    "src/agents/controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py": (
        "68ef42fd16c6299681641ad92bc93c648331c36e8fdd17971e387247e9c3e66a"
    ),
    "src/agents/controlled_exact_resume_change_set_manual_decision_packet_default_off.py": (
        "0c54c837040007e0241aeedffabdf35375797d8f55bead5b0c6b73106d9867aa"
    ),
    "run_controlled_exact_resume_change_set_manual_decision_packet_dry_run.py": (
        "bbb99d08196f97a59c7da1044d6780c275e6c88b50f2f6707cc9ba50b8697bc3"
    ),
}


def _command():
    return importlib.import_module(
        "run_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run"
    )


def _write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _manual_decision_packet() -> dict:
    return {
        "payload_type": "exact_resume_change_set_manual_decision_packet",
        "manual_decision_packet_only": True,
        "manual_review_required": True,
        "requires_manual_user_control": True,
        "allowed_decision_values": ["approve", "reject", "needs_revision"],
        "manual_decisions": [
            {
                "proposal_id": "p1",
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
                "manual_decision": "needs_revision",
                "decision_reason": "tighten wording",
                "resume_change_applied": False,
                "resume_overwrite_performed": False,
                "resume_mutation_performed": False,
                "artifact_created": False,
                "application_execution_performed": False,
            },
        ],
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


def _phase51_result() -> dict:
    return {
        "phase": "51A",
        "status": "completed",
        "manual_decision_packet_created": True,
        "manual_decision_packet": _manual_decision_packet(),
    }


def _phase50_readback() -> dict:
    return {
        "phase": "50A",
        "status": "completed",
        "final_readback_payload": {
            "payload_type": "exact_resume_change_set_manual_review_readback",
            "readback_items": [{"proposal_id": "p1"}],
        },
    }


def test_command_module_is_import_safe_and_exposes_functions(capsys):
    module = _command()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    for name in (
        "load_manual_decision_packet_from_path",
        "build_dry_run_payload",
        "main",
    ):
        assert callable(getattr(module, name))


def test_default_off_command_blocks_safely(tmp_path, capsys):
    module = _command()
    packet_path = _write_json(tmp_path / "packet.json", _phase51_result())

    result = module.main(["--manual-decision-packet", str(packet_path)])

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["phase"] == "52B"
    assert payload["status"] == "blocked"
    assert "enabled must be true" in payload["blocked_reason"]
    assert payload["readback_payload_created"] is False


def test_enabled_command_accepts_local_json_manual_decision_packet_input(
    tmp_path,
    capsys,
):
    module = _command()
    packet_path = _write_json(tmp_path / "packet.json", _manual_decision_packet())

    result = module.main(
        [
            "--manual-decision-packet",
            str(packet_path),
            "--enable-manual-decision-readback",
            "--allow-manual-decision-readback",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["readback_payload_created"] is True
    assert payload["readback_payload"]["payload_type"] == (
        "exact_resume_change_set_manual_decision_readback"
    )
    assert payload["readback_payload"]["decision_summary"]["approved_count"] == 1


def test_enabled_command_accepts_phase51_result_input(tmp_path, capsys):
    module = _command()
    packet_path = _write_json(tmp_path / "phase51.json", _phase51_result())

    result = module.main(
        [
            "--manual-decision-packet",
            str(packet_path),
            "--enable-manual-decision-readback",
            "--allow-manual-decision-readback",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["readback_result"]["stage_summaries"][
        "manual_decision_packet_resolution"
    ]["source"] == "phase51.manual_decision_packet"


def test_missing_manual_decision_packet_input_blocks_safely():
    module = _command()
    payload = module.build_dry_run_payload(
        enable_manual_decision_readback=True,
        allow_manual_decision_readback=True,
    )

    assert payload["status"] == "blocked"
    assert payload["readback_result"]["missing_inputs"] == ["manual_decision_packet"]
    assert "manual decision packet required" in payload["blocked_reason"]


def test_raw_phase50_readback_or_manual_review_input_is_surfaced_safely():
    module = _command()
    payload = module.build_dry_run_payload(
        manual_decision_packet=_phase50_readback(),
        enable_manual_decision_readback=True,
        allow_manual_decision_readback=True,
    )

    assert payload["status"] == "blocked"
    assert "raw readback/manual review input is not accepted" in payload[
        "blocked_reason"
    ]
    assert payload["stage_summaries"]["manual_decision_packet_resolution"][
        "raw_review_or_readback_input"
    ] is True


def test_invalid_json_is_surfaced_cleanly(tmp_path, capsys):
    module = _command()
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not-json", encoding="utf-8")

    result = module.main(["--manual-decision-packet", str(bad_path)])

    captured = capsys.readouterr()
    assert result == 2
    assert "invalid JSON" in captured.err
    assert captured.out == ""


def test_invalid_or_incomplete_decision_packet_is_surfaced_safely():
    module = _command()
    packet = _manual_decision_packet()
    packet["manual_decisions"] = [{"proposal_id": "p1", "manual_decision": "apply"}]

    payload = module.build_dry_run_payload(
        manual_decision_packet=packet,
        enable_manual_decision_readback=True,
        allow_manual_decision_readback=True,
    )

    assert payload["status"] == "blocked"
    assert "invalid manual decision packet present" in payload["blocked_reason"]
    invalid = payload["stage_results"]["manual_decision_packet_validation"][
        "invalid_decisions"
    ]
    assert invalid[0]["reason"] == "invalid decision value"


def test_command_calls_phase52a_only_not_phase51_or_lower_helpers(monkeypatch):
    module = _command()
    calls = []

    def fake_phase52a(**kwargs):
        calls.append(kwargs)
        return {
            "phase": "52A",
            "status": "blocked",
            "blocked_reason": "stubbed",
            "readback_payload_created": False,
            "readback_payload_key": "",
            "stage_sequence": [
                "manual_decision_packet_resolution",
                "manual_decision_packet_validation",
                "manual_decision_readback",
            ],
            "stage_summaries": {},
            "stage_results": {},
            "readback_payload": None,
        }

    monkeypatch.setattr(
        module,
        "build_controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off",
        fake_phase52a,
    )

    payload = module.build_dry_run_payload(
        manual_decision_packet=_manual_decision_packet(),
        enable_manual_decision_readback=True,
        allow_manual_decision_readback=True,
    )

    assert payload["status"] == "blocked"
    assert len(calls) == 1
    assert calls[0]["enabled"] is True
    assert calls[0]["readback_policy"] == {
        "allow_manual_decision_readback": True
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
        "controlled_exact_resume_change_set_manual_decision_packet_default_off",
        "controlled_exact_resume_change_set_real_provider_response_handoff_pipeline",
        "controlled_exact_resume_change_set_provider_response_validation",
        "controlled_exact_resume_change_set_provider_response_normalization",
        "controlled_exact_resume_change_set_manual_review_readback_adapter",
    ]

    for fragment in forbidden_fragments:
        assert fragment not in source


def test_no_mutation_persistence_scoring_artifact_execution_or_decision_application():
    module = _command()
    payload = module.build_dry_run_payload(
        manual_decision_packet=_manual_decision_packet(),
        enable_manual_decision_readback=True,
        allow_manual_decision_readback=True,
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
        assert payload[key] is False


def test_protected_files_are_unchanged():
    for relative_path, expected_hash in PROTECTED_HASHES.items():
        assert sha256((ROOT / relative_path).read_bytes()).hexdigest() == expected_hash


def test_docs_capture_default_off_readback_only_and_safety_boundaries():
    text = DOC_PATH.read_text(encoding="utf-8")

    assert "default-off" in text
    assert "does not call a provider" in text
    assert "call an LLM" in text
    assert "call network" in text
    assert "no mutation" in text
    assert "no persistence" in text
    assert "no scoring" in text
    assert "no artifact creation" in text
    assert "no application execution" in text
    assert "readback only" in text
