from hashlib import sha256
import importlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
COMMAND_PATH = (
    ROOT / "run_controlled_exact_resume_change_set_manual_decision_packet_dry_run.py"
)
DOC_PATH = (
    ROOT
    / "docs/phase51_controlled_exact_resume_change_set_manual_decision_packet_dry_run_command_default_off.md"
)
PROTECTED_HASHES = {
    "src/tailoring/llm.py": "6153c78e5f0eca7c78451f0d234609682e01990041deae7fccb0aa303c653920",
    "generate_tailoring_" + "suggestions" + ".py": "2422452d1c7a54777684b399730d02c11e58ce1ad6ac5658527ad71bb9050f28",
    "src/matching/scorer.py": "5a7fa4abf6adb353bbb8c3f8c3113279409de1250f99e61a36056c5d06503062",
    "src/matching/prefilter.py": "489d9461a0b6422d94be717dd3a54bfb2609660ad1f305e03eab20e7cec64a7f",
    "application_execution_" + "queue" + ".py": "c06438ad6a304780824e64f97fdcd35db08fa3a53b0538bca6244bb3fedb92e0",
    "src/agents/controlled_exact_resume_change_set_manual_decision_packet_default_off.py": (
        "0c54c837040007e0241aeedffabdf35375797d8f55bead5b0c6b73106d9867aa"
    ),
    "run_controlled_exact_resume_change_set_real_provider_response_handoff_pipeline_dry_run.py": (
        "596d17aff87a43db2b3b4cb2e1cbf036c7019736d458b2a4112289d6a892d5c6"
    ),
}


def _command():
    return importlib.import_module(
        "run_controlled_exact_resume_change_set_manual_decision_packet_dry_run"
    )


def _write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _readback_items() -> list[dict]:
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


def _phase50_output() -> dict:
    return {
        "phase": "50A",
        "status": "completed",
        "final_readback_payload": {
            "payload_type": "exact_resume_change_set_manual_review_readback",
            "readback_items": _readback_items(),
        },
    }


def _manual_review_output() -> dict:
    return {"manual_review_packets": _readback_items()}


def _decisions() -> list[dict]:
    return [
        {"proposal_id": "p1", "decision": "approve", "reason": "looks exact"},
        {"proposal_id": "p2", "decision": "reject", "reason": "not supported"},
        {
            "proposal_id": "p3",
            "decision": "needs_revision",
            "reason": "tighten wording",
        },
    ]


def test_command_module_is_import_safe_and_exposes_functions(capsys):
    module = _command()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""
    for name in (
        "load_readback_result_from_path",
        "load_manual_review_output_from_path",
        "load_manual_decisions_from_path",
        "build_dry_run_payload",
        "main",
    ):
        assert callable(getattr(module, name))


def test_default_off_command_blocks_safely(tmp_path, capsys):
    module = _command()
    readback_path = _write_json(tmp_path / "readback.json", _phase50_output())
    decisions_path = _write_json(tmp_path / "decisions.json", _decisions())

    result = module.main(
        [
            "--readback-result",
            str(readback_path),
            "--manual-decisions",
            str(decisions_path),
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["phase"] == "51B"
    assert payload["status"] == "blocked"
    assert "enabled must be true" in payload["blocked_reason"]
    assert payload["manual_decision_packet_created"] is False


def test_enabled_command_accepts_local_json_readback_and_decision_input(
    tmp_path,
    capsys,
):
    module = _command()
    readback_path = _write_json(tmp_path / "readback.json", _phase50_output())
    decisions_path = _write_json(
        tmp_path / "decisions.json",
        {"manual_decisions": _decisions()},
    )

    result = module.main(
        [
            "--readback-result",
            str(readback_path),
            "--manual-decisions",
            str(decisions_path),
            "--enable-manual-decision-packet",
            "--allow-manual-decision-packet",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["manual_decision_packet_created"] is True
    assert payload["manual_decision_packet"]["payload_type"] == (
        "exact_resume_change_set_manual_decision_packet"
    )
    assert payload["decision_result"]["manual_decision_packet_created"] is True


def test_enabled_command_accepts_local_json_manual_review_input(tmp_path, capsys):
    module = _command()
    review_path = _write_json(tmp_path / "review.json", _manual_review_output())
    decisions_path = _write_json(tmp_path / "decisions.json", _decisions())

    result = module.main(
        [
            "--manual-review-output",
            str(review_path),
            "--manual-decisions",
            str(decisions_path),
            "--enable-manual-decision-packet",
            "--allow-manual-decision-packet",
        ]
    )

    assert result == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["status"] == "completed"
    assert payload["manual_review_output_present"] is True
    assert payload["manual_decision_packet"]["decision_summary"]["approved_count"] == 1


def test_missing_readback_or_manual_review_input_blocks_safely():
    module = _command()
    payload = module.build_dry_run_payload(
        manual_decisions=_decisions(),
        enable_manual_decision_packet=True,
        allow_manual_decision_packet=True,
    )

    assert payload["status"] == "blocked"
    assert payload["decision_result"]["missing_inputs"] == [
        "readback_or_manual_review_output"
    ]
    assert "readback/manual review output required" in payload["blocked_reason"]


def test_missing_decision_input_blocks_safely():
    module = _command()
    payload = module.build_dry_run_payload(
        readback_result=_phase50_output(),
        enable_manual_decision_packet=True,
        allow_manual_decision_packet=True,
    )

    assert payload["status"] == "blocked"
    assert payload["decision_result"]["missing_inputs"] == ["manual_decisions"]
    assert "manual decisions required" in payload["blocked_reason"]


def test_invalid_json_is_surfaced_cleanly(tmp_path, capsys):
    module = _command()
    bad_path = tmp_path / "bad.json"
    bad_path.write_text("{not-json", encoding="utf-8")

    result = module.main(["--manual-decisions", str(bad_path)])

    captured = capsys.readouterr()
    assert result == 2
    assert "invalid JSON" in captured.err
    assert captured.out == ""


def test_invalid_decision_values_are_surfaced_safely():
    module = _command()
    payload = module.build_dry_run_payload(
        readback_result=_phase50_output(),
        manual_decisions=[{"proposal_id": "p1", "decision": "apply"}],
        enable_manual_decision_packet=True,
        allow_manual_decision_packet=True,
    )

    assert payload["status"] == "blocked"
    assert "invalid manual decisions present" in payload["blocked_reason"]
    invalid = payload["stage_results"]["decision_validation"]["invalid_decisions"]
    assert invalid[0]["reason"] == "invalid decision value"


def test_unknown_proposal_identifiers_are_surfaced_safely():
    module = _command()
    payload = module.build_dry_run_payload(
        readback_result=_phase50_output(),
        manual_decisions=[{"proposal_id": "unknown", "decision": "approve"}],
        enable_manual_decision_packet=True,
        allow_manual_decision_packet=True,
    )

    assert payload["status"] == "blocked"
    assert "unknown proposal identifiers present" in payload["blocked_reason"]
    assert payload["stage_results"]["decision_validation"]["unknown_identifiers"] == [
        "unknown"
    ]


def test_command_calls_phase51a_only_not_phase50_or_lower_helpers(monkeypatch):
    module = _command()
    calls = []

    def fake_phase51a(**kwargs):
        calls.append(kwargs)
        return {
            "phase": "51A",
            "status": "blocked",
            "blocked_reason": "stubbed",
            "manual_decision_packet_created": False,
            "manual_decision_packet_key": "",
            "stage_sequence": [
                "readback_resolution",
                "decision_validation",
                "manual_decision_packet",
            ],
            "stage_summaries": {},
            "stage_results": {},
            "manual_decision_packet": None,
        }

    monkeypatch.setattr(
        module,
        "build_controlled_exact_resume_change_set_manual_decision_packet_default_off",
        fake_phase51a,
    )

    payload = module.build_dry_run_payload(
        readback_result=_phase50_output(),
        manual_decisions=_decisions(),
        enable_manual_decision_packet=True,
        allow_manual_decision_packet=True,
    )

    assert payload["status"] == "blocked"
    assert len(calls) == 1
    assert calls[0]["enabled"] is True
    assert calls[0]["decision_policy"] == {
        "allow_manual_decision_packet": True,
        "require_all_readback_items_decided": False,
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
        readback_result=_phase50_output(),
        manual_decisions=_decisions(),
        enable_manual_decision_packet=True,
        allow_manual_decision_packet=True,
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


def test_docs_capture_default_off_decision_packet_only_and_safety_boundaries():
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
    assert "manual decision packet only" in text
