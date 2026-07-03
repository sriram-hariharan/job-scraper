from hashlib import sha256
import importlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = (
    ROOT
    / "run_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase53_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run_command_default_off.md"
)
PROTECTED_HASHES = {
    "src/tailoring/llm.py": "44614b3b0ecf7b13514996b33ddc9d4346024e9cf031f77eaa135e8a0ab30ce8",
    "generate_tailoring_" + "suggestions" + ".py": "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28",
    "src/matching/scorer.py": "c3f0b1f4a938ca933b10991af1ddb0aca2790136c7c6b487a8ee79556ee5ceac",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_" + "queue" + ".py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
    "src/agents/controlled_exact_resume_change_set_approved_change_plan_packet_default_off.py": (
        "b9f11e4d95660a88a81d107b06f7cb3893d8b706bcf92c9513ccafb4143333b3"
    ),
    "src/agents/controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off.py": (
        "68ef42fd16c6299681641ad92bc93c648331c36e8fdd17971e387247e9c3e66a"
    ),
    "run_controlled_exact_resume_change_set_manual_decision_readback_adapter_dry_run.py": (
        "3defcb6db228936f4045bcfeb1695f4980d042d224be46e300980adb00ca361e"
    ),
}


def _command():
    return importlib.import_module(
        "run_controlled_exact_resume_change_set_approved_change_plan_packet_dry_run"
    )


def _write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _readback_payload() -> dict:
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


def _phase52_result() -> dict:
    return {
        "phase": "52A",
        "status": "completed",
        "readback_payload_created": True,
        "readback_payload": _readback_payload(),
    }


def _phase52b_result() -> dict:
    return {
        "phase": "52B",
        "status": "completed",
        "readback_result": _phase52_result(),
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


def test_command_module_is_import_safe_and_exposes_functions(capsys):
    module = _command()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    for name in (
        "load_manual_decision_readback_from_path",
        "build_dry_run_payload",
        "main",
    ):
        assert callable(getattr(module, name))


def test_default_off_command_blocks_safely(tmp_path, capsys):
    module = _command()
    readback_path = _write_json(tmp_path / "readback.json", _phase52_result())

    result = module.main(["--manual-decision-readback", str(readback_path)])

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["phase"] == "53B"
    assert payload["status"] == "blocked"
    assert "enabled must be true" in payload["blocked_reason"]
    assert payload["approved_change_plan_packet_created"] is False


def test_enabled_command_accepts_local_json_phase52_readback_input(tmp_path, capsys):
    module = _command()
    readback_path = _write_json(tmp_path / "readback.json", _readback_payload())

    result = module.main(
        [
            "--manual-decision-readback",
            str(readback_path),
            "--enable-approved-change-plan-packet",
            "--allow-approved-change-plan-packet",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["approved_change_plan_packet_created"] is True
    packet = payload["approved_change_plan_packet"]
    assert packet["payload_type"] == "exact_resume_change_set_approved_change_plan_packet"
    assert [row["proposal_id"] for row in packet["approved_changes"]] == ["p1"]


def test_enabled_command_accepts_phase52_result_input(tmp_path, capsys):
    module = _command()
    readback_path = _write_json(tmp_path / "phase52.json", _phase52_result())

    result = module.main(
        [
            "--manual-decision-readback",
            str(readback_path),
            "--enable-approved-change-plan-packet",
            "--allow-approved-change-plan-packet",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["plan_result"]["stage_summaries"][
        "manual_decision_readback_resolution"
    ]["source"] == "phase52.readback_payload"


def test_enabled_command_accepts_phase52b_wrapper_input(tmp_path, capsys):
    module = _command()
    readback_path = _write_json(tmp_path / "phase52b.json", _phase52b_result())

    result = module.main(
        [
            "--manual-decision-readback",
            str(readback_path),
            "--enable-approved-change-plan-packet",
            "--allow-approved-change-plan-packet",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["plan_result"]["stage_summaries"][
        "manual_decision_readback_resolution"
    ]["source"] == "phase52b.readback_result.readback_payload"


def test_missing_readback_input_blocks_safely():
    module = _command()
    payload = module.build_dry_run_payload(
        enable_approved_change_plan_packet=True,
        allow_approved_change_plan_packet=True,
    )

    assert payload["status"] == "blocked"
    assert payload["plan_result"]["missing_inputs"] == ["manual_decision_readback"]
    assert "manual decision readback required" in payload["blocked_reason"]


def test_raw_phase51_manual_decision_packet_is_surfaced_safely():
    module = _command()
    payload = module.build_dry_run_payload(
        manual_decision_readback=_raw_phase51_packet(),
        enable_approved_change_plan_packet=True,
        allow_approved_change_plan_packet=True,
    )

    assert payload["status"] == "blocked"
    assert "raw manual decision packet is not accepted" in payload["blocked_reason"]
    assert payload["stage_summaries"]["manual_decision_readback_resolution"][
        "raw_phase51_manual_decision_packet_input"
    ] is True


def test_raw_phase50_readback_or_manual_review_input_is_surfaced_safely():
    module = _command()
    payload = module.build_dry_run_payload(
        manual_decision_readback=_raw_phase50_readback(),
        enable_approved_change_plan_packet=True,
        allow_approved_change_plan_packet=True,
    )

    assert payload["status"] == "blocked"
    assert "raw phase50 readback/manual review input is not accepted" in payload[
        "blocked_reason"
    ]
    assert payload["stage_summaries"]["manual_decision_readback_resolution"][
        "raw_phase50_readback_or_review_input"
    ] is True


def test_invalid_json_is_surfaced_cleanly(tmp_path, capsys):
    module = _command()
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not-json", encoding="utf-8")

    result = module.main(["--manual-decision-readback", str(bad_path)])

    captured = capsys.readouterr()
    assert result == 2
    assert "invalid JSON" in captured.err
    assert captured.out == ""


def test_invalid_or_incomplete_readback_is_surfaced_safely():
    module = _command()
    readback = _readback_payload()
    readback["readback_items"] = [{"proposal_id": "p1", "manual_decision": "apply"}]

    payload = module.build_dry_run_payload(
        manual_decision_readback=readback,
        enable_approved_change_plan_packet=True,
        allow_approved_change_plan_packet=True,
    )

    assert payload["status"] == "blocked"
    assert "invalid manual decision readback present" in payload["blocked_reason"]
    invalid = payload["stage_results"]["manual_decision_readback_validation"][
        "invalid_readback_items"
    ]
    assert invalid[0]["reason"] == "invalid decision value"


def test_command_calls_phase53a_only_not_phase52_or_lower_helpers(monkeypatch):
    module = _command()
    calls = []

    def fake_phase53a(**kwargs):
        calls.append(kwargs)
        return {
            "phase": "53A",
            "status": "blocked",
            "blocked_reason": "stubbed",
            "approved_change_plan_packet_created": False,
            "approved_change_plan_packet_key": "",
            "stage_sequence": [
                "manual_decision_readback_resolution",
                "manual_decision_readback_validation",
                "approved_change_plan_packet",
            ],
            "stage_summaries": {},
            "stage_results": {},
            "approved_change_plan_packet": None,
        }

    monkeypatch.setattr(
        module,
        "build_controlled_exact_resume_change_set_approved_change_plan_packet_default_off",
        fake_phase53a,
    )

    payload = module.build_dry_run_payload(
        manual_decision_readback=_readback_payload(),
        enable_approved_change_plan_packet=True,
        allow_approved_change_plan_packet=True,
    )

    assert payload["status"] == "blocked"
    assert len(calls) == 1
    assert calls[0]["enabled"] is True
    assert calls[0]["plan_policy"] == {"allow_approved_change_plan_packet": True}


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
        "controlled_exact_resume_change_set_manual_decision_readback_adapter_default_off",
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
        manual_decision_readback=_readback_payload(),
        enable_approved_change_plan_packet=True,
        allow_approved_change_plan_packet=True,
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


def test_docs_capture_default_off_plan_packet_only_and_safety_boundaries():
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
    assert "plan packet only" in text
